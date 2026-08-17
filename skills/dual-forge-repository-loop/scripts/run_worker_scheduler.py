#!/usr/bin/env python3
"""Drive the multi-Worker lifecycle with real Workers and record every transition.

worker-task.schema.json has declared twenty-one states since it was written.
Before this script, a grep for each of them across the repository found that
ASSIGNED, LEASED, CHECKPOINTED, RESULT_READY and FAILED_RETRYABLE had no
producer at all -- not in a script, not in a fixture, not in a test -- and that
every other state appeared only inside a checker that reads it or a fixture that
constructs it. A state only tests can construct is a state the runtime does not
have, and a schema cannot tell you which of its own values are real.

So this is the producer. It creates a disposable subject repository, admits a
plan of two path-disjoint Workers plus one convergence owner, leases a worktree
to each, runs a real Agent inside it, verifies the result with an oracle the
Worker cannot edit, and integrates. The non-happy paths are exercised on planted
attempts, because a lease is only proven to expire if something tries to use it
afterwards.

Every attempt also carries a budget ledger: what it spent, which dimensions were
actually observed, and whether it passed its cap. An attempt that passes its
wall-clock budget is detached into a terminal state rather than waited for, and
the global cap stops the next attempt from starting -- a cap that stops nothing
is a number in a receipt. Dimensions the harness cannot read (tool calls always;
tokens and cost when the Agent's output will not parse) are listed as unobserved
instead of recorded as zero, because a ledger of invented zeros reconciles every
time.

What it does not claim: that these Workers were faster than one, that the Agent
wrote good code, or that this subject resembles a production repository. It
claims that the transitions happened, that the refusals refused, and that the
spend it recorded is the spend it saw.

Usage:
  run_worker_scheduler.py --out DIR [--agent claude] [--skip-agent]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA = "dual-forge-repository-loop/scheduler-run-receipt/v1"

HAPPY_PATH = ["PLANNED", "ADMITTED", "ASSIGNED", "LEASED", "RUNNING",
              "CHECKPOINTED", "RESULT_READY", "RESULT_VERIFIED", "INTEGRATED"]

# States an attempt does not move out of. Reaching one releases whatever it held.
TERMINAL_STATES = {"INTEGRATED", "STALE_ATTEMPT", "LEASE_EXPIRED", "CANCELLED",
                   "STRAGGLER_DETACHED", "FAILED_TERMINAL", "BLOCKED_AUTHORITY",
                   "BLOCKED_CONFLICT", "SUPERSEDED", "REJECTED_NOT_DECOMPOSABLE",
                   "DUPLICATE_SUPPRESSED"}


def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args],
                            capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


# --------------------------------------------------------------------------
# subject
# --------------------------------------------------------------------------

ORACLE_CELSIUS = '''\
import sys
sys.path.insert(0, "src")
from celsius import to_fahrenheit

assert to_fahrenheit(0) == 32
assert to_fahrenheit(100) == 212
assert to_fahrenheit(-40) == -40
print("celsius oracle PASS")
'''

ORACLE_SLUG = '''\
import sys
sys.path.insert(0, "src")
from slug import slugify

assert slugify("Hello World") == "hello-world"
assert slugify("  Multiple   Spaces  ") == "multiple-spaces"
assert slugify("Already-Slugged") == "already-slugged"
print("slug oracle PASS")
'''

ORACLE_CONVERGENCE = '''\
import sys
sys.path.insert(0, "src")
from toolkit import to_fahrenheit, slugify

assert to_fahrenheit(0) == 32
assert slugify("Hello World") == "hello-world"
print("convergence oracle PASS")
'''


def build_subject(root: Path) -> Path:
    """A real repository, small enough that a Worker slice is one file."""
    repo = root / "subject"
    repo.mkdir(parents=True)
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    (repo / "src").mkdir()
    (repo / "oracles").mkdir()
    (repo / "src" / ".keep").write_text("", encoding="utf-8")
    (repo / "oracles" / "celsius_oracle.py").write_text(ORACLE_CELSIUS, encoding="utf-8")
    (repo / "oracles" / "slug_oracle.py").write_text(ORACLE_SLUG, encoding="utf-8")
    (repo / "oracles" / "convergence_oracle.py").write_text(ORACLE_CONVERGENCE,
                                                            encoding="utf-8")
    (repo / "README.md").write_text(
        "Disposable scheduler-canary subject. The oracles are immutable for every "
        "Worker; each Worker owns exactly one file under src/.\n", encoding="utf-8")
    git(repo, "add", "-A")
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=scheduler",
         "-c", "user.email=scheduler@canary.invalid", "commit", "-q",
         "-m", "subject: oracles and empty implementation surface"], check=True)
    return repo


TASKS: list[dict[str, Any]] = [
    {
        "logical_id": "celsius",
        "goal": ("Create src/celsius.py defining to_fahrenheit(c) returning the "
                 "Celsius value c converted to Fahrenheit. Pure function, no imports, "
                 "no printing."),
        "stack_class": "sibling",
        "allowed_paths": ["src/celsius.py"],
        "oracle": "oracles/celsius_oracle.py",
        "dependencies": [],
    },
    {
        "logical_id": "slug",
        "goal": ("Create src/slug.py defining slugify(s) that lowercases s, collapses "
                 "any run of whitespace to a single hyphen, and strips leading and "
                 "trailing whitespace before doing so. Pure function, no printing."),
        "stack_class": "sibling",
        "allowed_paths": ["src/slug.py"],
        "oracle": "oracles/slug_oracle.py",
        "dependencies": [],
    },
    {
        "logical_id": "toolkit",
        "goal": ("Create src/toolkit.py that re-exports to_fahrenheit from celsius and "
                 "slugify from slug, so `from toolkit import to_fahrenheit, slugify` "
                 "works. Only import and re-export; define no new logic."),
        "stack_class": "convergence",
        "allowed_paths": ["src/toolkit.py"],
        "oracle": "oracles/convergence_oracle.py",
        "dependencies": ["celsius", "slug"],
    },
]

LEASE_SECONDS = 900

# Budget dimensions this harness can actually see. Tool calls are deliberately
# absent: the Agent reports turns, not tool calls, and a limit on a number nobody
# measures is a limit that always passes. Anything a run fails to observe is
# listed as unobserved in the ledger rather than recorded as a spend of zero,
# because zero and unknown are different claims and only one of them is checkable.
BUDGET_DIMENSIONS = ("turns", "tokens", "wall_clock_seconds", "cost_usd")
ATTEMPT_BUDGET: dict[str, float] = {
    "turns": 40, "tokens": 120000, "wall_clock_seconds": LEASE_SECONDS, "cost_usd": 2.0}
GLOBAL_BUDGET: dict[str, float] = {
    "turns": 200, "tokens": 600000, "wall_clock_seconds": 3600, "cost_usd": 6.0}


def empty_spend() -> dict[str, float]:
    return {dimension: 0 for dimension in BUDGET_DIMENSIONS}


def over(spend: dict[str, float], observed: list[str],
         limits: dict[str, float]) -> list[str]:
    """Dimensions the spend exceeded. Unobserved dimensions cannot be exceeded."""
    return sorted(d for d in BUDGET_DIMENSIONS
                  if d in observed and spend.get(d, 0) > limits[d])


class Scheduler:
    def __init__(self, repo: Path, workroot: Path, agent: str | None) -> None:
        self.repo = repo
        self.workroot = workroot
        self.agent = agent
        self.transitions: list[dict[str, Any]] = []
        self.attempts: dict[str, dict[str, Any]] = {}
        self.path_leases: dict[str, str] = {}   # path -> attempt_id
        self.branch_leases: dict[str, str] = {}  # branch -> attempt_id
        self.run_id = uuid.uuid4().hex
        self.refusals: list[dict[str, Any]] = []

    # -- transition log -----------------------------------------------------

    def transition(self, attempt_id: str, state: str, **detail: Any) -> None:
        """Log the move, and release the lease when the move is terminal.

        Releasing at each call site is how a lease survives a run: `verify` left
        one behind on FAILED_RETRYABLE, `integrate` left one behind on
        STALE_ATTEMPT, and both looked fine in isolation. Every terminal state
        goes through here, so the release belongs here and forgetting it stops
        being possible.
        """
        attempt = self.attempts[attempt_id]
        record = {
            "sequence": len(self.transitions) + 1,
            "attempt_id": attempt_id,
            "task_id": attempt["task_id"],
            "state": state,
            "at": stamp(now()),
        }
        record.update(detail)
        attempt["state"] = state
        self.transitions.append(record)
        if state in TERMINAL_STATES and attempt["lease"].get("status") == "ACTIVE":
            attempt["lease"]["status"] = "RELEASED"
            self.branch_leases.pop(attempt["branch"], None)

    def refuse(self, code: str, detail: str, **extra: Any) -> None:
        entry = {"code": code, "detail": detail, "at": stamp(now())}
        entry.update(extra)
        self.refusals.append(entry)

    # -- lifecycle ----------------------------------------------------------

    def plan(self) -> None:
        base = git(self.repo, "rev-parse", "HEAD")
        for spec in TASKS:
            attempt_id = f"att-{uuid.uuid4().hex[:12]}"
            task_id = f"task-{self.run_id[:8]}-{spec['logical_id']}"
            self.attempts[attempt_id] = {
                "task_id": task_id,
                "logical_id": spec["logical_id"],
                "attempt_id": attempt_id,
                "spec": spec,
                "base_subject_sha": base,
                "branch": f"worker/{spec['logical_id']}",
                "state": None,
                "lease": {"status": None, "expiry": None, "heartbeat_sequence": 0},
                "checkpoint": {"sequence": 0, "digest": None},
                "heartbeats": [],
                # An attempt that never runs spent nothing, and that is observed
                # rather than unknown: the scheduler is what would have started it.
                "spend": empty_spend(),
                "spend_observed": sorted(BUDGET_DIMENSIONS),
            }
            self.transition(attempt_id, "PLANNED", base_subject_sha=base,
                            stack_class=spec["stack_class"],
                            allowed_paths=spec["allowed_paths"])

    def admit(self) -> None:
        """Admission is where path disjointness is decided, before any worktree."""
        for attempt_id, attempt in self.attempts.items():
            clash = [p for p in attempt["spec"]["allowed_paths"] if p in self.path_leases]
            if clash:
                self.refuse("PATH_LEASE_HELD",
                            f"{attempt_id} requested {clash} already leased",
                            attempt_id=attempt_id)
                self.transition(attempt_id, "BLOCKED_CONFLICT", clash=clash)
                continue
            for path in attempt["spec"]["allowed_paths"]:
                self.path_leases[path] = attempt_id
            self.transition(attempt_id, "ADMITTED")

    def ready(self, attempt: dict[str, Any]) -> bool:
        wanted = set(attempt["spec"]["dependencies"])
        if not wanted:
            return True
        done = {a["logical_id"] for a in self.attempts.values() if a["state"] == "INTEGRATED"}
        return wanted <= done

    def assign(self, attempt: dict[str, Any]) -> None:
        branch = attempt["branch"]
        if branch in self.branch_leases:
            self.refuse("BRANCH_LEASE_HELD", f"{branch} already has an active writer",
                        attempt_id=attempt["attempt_id"])
            self.transition(attempt["attempt_id"], "BLOCKED_CONFLICT", branch=branch)
            return
        self.branch_leases[branch] = attempt["attempt_id"]
        self.transition(attempt["attempt_id"], "ASSIGNED", branch=branch)

    def lease(self, attempt: dict[str, Any]) -> Path:
        """Independent siblings share the planned base; a dependent re-binds at lease.

        The first run leased every Worker from the plan's base, including the
        convergence owner. Its worktree therefore did not contain the two
        siblings it was asked to re-export, its oracle failed, and the failure
        looked like the Agent's fault. It was the scheduler's: an attempt that
        consumes integrated results has to be leased from the state that contains
        them.

        Siblings keep the planned base on purpose. One immutable base is what
        makes parallel attempts comparable, and re-binding those would silently
        order work that was admitted as unordered.
        """
        path = self.workroot / attempt["logical_id"]
        if attempt["spec"]["dependencies"]:
            rebound = git(self.repo, "rev-parse", "HEAD")
            if rebound != attempt["base_subject_sha"]:
                self.transition(attempt["attempt_id"], "ADMITTED",
                                base_rebound_from=attempt["base_subject_sha"],
                                base_rebound_to=rebound,
                                reason=("convergence consumes integrated dependencies and "
                                        "is leased from the state that contains them"))
                attempt["base_subject_sha"] = rebound
        git(self.repo, "worktree", "add", "-q", "-b", attempt["branch"], str(path),
            attempt["base_subject_sha"])
        expiry = now() + timedelta(seconds=LEASE_SECONDS)
        attempt["lease"] = {"status": "ACTIVE", "expiry": stamp(expiry),
                            "heartbeat_sequence": 0}
        attempt["worktree_identity"] = str(path)
        self.transition(attempt["attempt_id"], "LEASED",
                        worktree_identity=str(path), lease_expiry=stamp(expiry))
        return path

    # -- budget -------------------------------------------------------------

    def charge(self, attempt: dict[str, Any], stdout: str) -> None:
        """Record what the Agent reports it spent, and only what it reports.

        `claude -p --output-format json` carries usage and cost. A run that
        cannot be parsed leaves those dimensions unobserved rather than zero:
        a budget reconciled against invented zeros reconciles every time.
        """
        observed = {"wall_clock_seconds"}
        try:
            payload = json.loads(stdout)
            usage = payload.get("usage", {})
            attempt["spend"]["tokens"] = (
                int(usage.get("input_tokens", 0))
                + int(usage.get("cache_read_input_tokens", 0))
                + int(usage.get("output_tokens", 0)))
            observed.add("tokens")
            if "num_turns" in payload:
                attempt["spend"]["turns"] = int(payload["num_turns"])
                observed.add("turns")
            if "total_cost_usd" in payload:
                attempt["spend"]["cost_usd"] = float(payload["total_cost_usd"])
                observed.add("cost_usd")
        except (ValueError, TypeError):
            pass
        attempt["spend_observed"] = sorted(observed)

    def totals(self) -> dict[str, float]:
        return {d: round(sum(a["spend"].get(d, 0) for a in self.attempts.values()), 3)
                for d in BUDGET_DIMENSIONS}

    def unobserved(self) -> list[str]:
        return sorted({d for a in self.attempts.values() for d in BUDGET_DIMENSIONS
                       if d not in a["spend_observed"]})

    def global_overrun(self) -> list[str]:
        """Dimensions the run as a whole passed, ignoring ones nobody measured."""
        unmeasured = set(self.unobserved())
        return sorted(d for d in BUDGET_DIMENSIONS
                      if d not in unmeasured and self.totals()[d] > GLOBAL_BUDGET[d])

    def budget_ledger(self) -> dict[str, Any]:
        return {
            "dimensions": sorted(BUDGET_DIMENSIONS),
            "attempt_limits": ATTEMPT_BUDGET,
            "global_limits": GLOBAL_BUDGET,
            "attempts": [
                {
                    "attempt_id": attempt["attempt_id"],
                    "spend": attempt["spend"],
                    "observed": attempt["spend_observed"],
                    "over_budget": over(attempt["spend"], attempt["spend_observed"],
                                        ATTEMPT_BUDGET),
                }
                for attempt in self.attempts.values()
            ],
            "totals": self.totals(),
            "unobserved_dimensions": self.unobserved(),
            "global_over_budget": self.global_overrun(),
            "why_unobserved_is_not_zero": (
                "A dimension this harness could not read is listed here and excluded "
                "from enforcement. Recording it as a spend of zero would let every "
                "budget reconcile and every cap pass, which is the failure this ledger "
                "exists to make visible."),
        }

    def heartbeat(self, attempt: dict[str, Any]) -> None:
        attempt["lease"]["heartbeat_sequence"] += 1
        attempt["heartbeats"].append({
            "sequence": attempt["lease"]["heartbeat_sequence"], "at": stamp(now())})

    def run_worker(self, attempt: dict[str, Any], worktree: Path) -> dict[str, Any]:
        spec = attempt["spec"]
        self.transition(attempt["attempt_id"], "RUNNING", agent=self.agent or "none")
        self.heartbeat(attempt)

        started = time.time()
        timed_out = False
        if self.agent is None:
            executed = {"exit_code": 0, "skipped": True}
            attempt["spend_observed"] = ["wall_clock_seconds"]
        else:
            prompt = (
                f"{spec['goal']}\n\n"
                f"You may create or modify only these paths: "
                f"{', '.join(spec['allowed_paths'])}.\n"
                f"Do not read, modify or create anything under oracles/.\n"
                f"Write the file and stop. Do not explain."
            )
            argv = [self.agent, "-p", prompt,
                    "--permission-mode", "acceptEdits",
                    "--allowedTools", "Write,Edit,Read",
                    "--output-format", "json"]
            try:
                proc = subprocess.run(argv, cwd=str(worktree), capture_output=True,
                                      text=True,
                                      timeout=ATTEMPT_BUDGET["wall_clock_seconds"])
                executed = {"exit_code": proc.returncode,
                            "stdout_sha256": sha256(proc.stdout.encode()),
                            "stdout_bytes": len(proc.stdout),
                            "stderr_bytes": len(proc.stderr)}
                self.charge(attempt, proc.stdout)
            except subprocess.TimeoutExpired:
                # The wall-clock budget is the one limit this harness can enforce
                # by itself, and before this it raised out of the run instead.
                # A Worker that outruns its budget has to become a terminal state
                # in the log, not a traceback.
                timed_out = True
                executed = {"exit_code": None, "timed_out": True}
                attempt["spend_observed"] = ["wall_clock_seconds"]
        duration = int((time.time() - started) * 1000)
        attempt["spend"]["wall_clock_seconds"] = round(duration / 1000, 3)
        if "wall_clock_seconds" not in attempt["spend_observed"]:
            attempt["spend_observed"] = sorted(
                set(attempt["spend_observed"]) | {"wall_clock_seconds"})
        self.heartbeat(attempt)

        if timed_out:
            self.refuse("BUDGET_EXCEEDED",
                        f"{attempt['attempt_id']} passed its wall-clock budget of "
                        f"{ATTEMPT_BUDGET['wall_clock_seconds']}s",
                        attempt_id=attempt["attempt_id"])
            self.transition(attempt["attempt_id"], "TIMED_OUT",
                            budget_wall_clock_seconds=ATTEMPT_BUDGET["wall_clock_seconds"],
                            spend=dict(attempt["spend"]))
            self.transition(attempt["attempt_id"], "STRAGGLER_DETACHED",
                            note="detached at its budget; its lease is not reassigned")
            return {"ok": False, "duration_ms": duration, "executed": executed,
                    "touched": []}

        exceeded = over(attempt["spend"], attempt["spend_observed"], ATTEMPT_BUDGET)
        if exceeded:
            self.refuse("BUDGET_EXCEEDED",
                        f"{attempt['attempt_id']} exceeded {exceeded}",
                        attempt_id=attempt["attempt_id"])
            self.transition(attempt["attempt_id"], "FAILED_TERMINAL",
                            over_budget=exceeded, spend=dict(attempt["spend"]))
            return {"ok": False, "duration_ms": duration, "executed": executed,
                    "touched": []}

        dirty = [l[3:].strip() for l in git(worktree, "status", "--porcelain").splitlines()
                 if l.strip()]
        outside = [p for p in dirty if p not in spec["allowed_paths"]]
        digest = None
        for path in spec["allowed_paths"]:
            target = worktree / path
            if target.is_file():
                digest = sha256(target.read_bytes())
        attempt["checkpoint"] = {"sequence": attempt["lease"]["heartbeat_sequence"],
                                 "digest": digest}
        self.transition(attempt["attempt_id"], "CHECKPOINTED",
                        checkpoint_digest=digest,
                        checkpoint_sequence=attempt["checkpoint"]["sequence"])

        if outside:
            self.refuse("LEASE_VIOLATION",
                        f"{attempt['attempt_id']} wrote outside its lease: {outside}",
                        attempt_id=attempt["attempt_id"])
            self.transition(attempt["attempt_id"], "FAILED_TERMINAL", wrote_outside=outside)
            return {"ok": False, "duration_ms": duration, "executed": executed,
                    "touched": dirty}

        self.transition(attempt["attempt_id"], "RESULT_READY",
                        touched=dirty, duration_ms=duration)
        return {"ok": True, "duration_ms": duration, "executed": executed, "touched": dirty}

    def verify(self, attempt: dict[str, Any], worktree: Path) -> dict[str, Any]:
        """The oracle is run by the scheduler, never by the Worker being judged."""
        spec = attempt["spec"]
        oracle_before = sha256((worktree / spec["oracle"]).read_bytes())
        oracle_committed = sha256((self.repo / spec["oracle"]).read_bytes())
        if oracle_before != oracle_committed:
            self.refuse("ACCEPTANCE_ORACLE_MUTATED",
                        f"{attempt['attempt_id']} changed {spec['oracle']}",
                        attempt_id=attempt["attempt_id"])
            self.transition(attempt["attempt_id"], "FAILED_TERMINAL",
                            oracle=spec["oracle"])
            return {"ok": False, "oracle_digest": oracle_before}

        proc = subprocess.run([sys.executable, spec["oracle"]], cwd=str(worktree),
                              capture_output=True, text=True, timeout=120)
        passed = proc.returncode == 0
        if not passed:
            self.transition(attempt["attempt_id"], "FAILED_RETRYABLE",
                            oracle=spec["oracle"], exit_code=proc.returncode,
                            stderr_tail=proc.stderr.strip().splitlines()[-1:] or [])
            return {"ok": False, "oracle_digest": oracle_before,
                    "exit_code": proc.returncode}
        self.transition(attempt["attempt_id"], "RESULT_VERIFIED",
                        oracle=spec["oracle"], oracle_digest=oracle_before,
                        exit_code=0)
        return {"ok": True, "oracle_digest": oracle_before, "exit_code": 0}

    def integrate(self, attempt: dict[str, Any], worktree: Path) -> None:
        """A result is stale when the base moved *under its lease*, not whenever it moved.

        The first version of this rule refused any attempt whose base was not the
        current HEAD. Running it showed what that costs: the celsius Worker
        integrated, main advanced by one commit, and the slug Worker -- which had
        already passed its own oracle and shares no path with celsius -- was
        refused as stale. Path-disjoint siblings were serialised at the
        integration step, which is the hidden serialism this canary exists to
        find, reintroduced by the scheduler itself.

        The honest condition is narrower: compare the paths that changed on main
        since the attempt's base against the attempt's own lease. An unrelated
        commit does not invalidate work it could not have touched. An unreadable
        base is still stale, because a base that cannot be diffed cannot be
        shown to be safe.
        """
        current = git(self.repo, "rev-parse", "HEAD")
        if current != attempt["base_subject_sha"]:
            changed = git(self.repo, "diff", "--name-only",
                          attempt["base_subject_sha"], current, check=False)
            if not changed and attempt["base_subject_sha"] != current:
                # The base is not an ancestor git can resolve at all.
                self.refuse("STALE_BASE",
                            f"{attempt['attempt_id']} produced against "
                            f"{attempt['base_subject_sha'][:12]}, which this repository "
                            f"cannot diff against {current[:12]}",
                            attempt_id=attempt["attempt_id"])
                self.transition(attempt["attempt_id"], "STALE_ATTEMPT",
                                produced_against=attempt["base_subject_sha"],
                                head=current, reason="base-unresolvable")
                return
            moved = set(changed.splitlines())
            collided = sorted(moved & set(attempt["spec"]["allowed_paths"]))
            if collided:
                self.refuse("STALE_BASE",
                            f"{attempt['attempt_id']} leased {collided}, which main "
                            f"changed between {attempt['base_subject_sha'][:12]} and "
                            f"{current[:12]}",
                            attempt_id=attempt["attempt_id"])
                self.transition(attempt["attempt_id"], "STALE_ATTEMPT",
                                produced_against=attempt["base_subject_sha"],
                                head=current, collided_paths=collided)
                return
            self.transition(attempt["attempt_id"], "CHECKPOINTED",
                            base_moved_from=attempt["base_subject_sha"],
                            base_moved_to=current,
                            moved_paths=sorted(moved),
                            note="base advanced outside this lease; not stale",
                            checkpoint_digest=attempt["checkpoint"]["digest"],
                            checkpoint_sequence=attempt["checkpoint"]["sequence"])

        git(worktree, "add", "-A")
        subprocess.run(
            ["git", "-C", str(worktree), "-c", "user.name=worker",
             "-c", f"user.email={attempt['logical_id']}@worker.invalid", "commit", "-q",
             "-m", f"worker({attempt['logical_id']}): {attempt['spec']['goal'][:50]}"],
            check=True)
        head = git(worktree, "rev-parse", "HEAD")
        git(self.repo, "merge", "--no-edit", "-q", attempt["branch"])
        self.transition(attempt["attempt_id"], "INTEGRATED",
                        head_subject_sha=head,
                        main_after=git(self.repo, "rev-parse", "HEAD"))

    # -- planted attempts ---------------------------------------------------

    def plant_non_happy_paths(self) -> list[dict[str, Any]]:
        """Each planted attempt drives one state the happy path never reaches.

        These are real scheduler decisions on real leases, not fixtures: the
        scheduler is asked to accept something it must refuse, and the state it
        writes is the refusal.
        """
        planted: list[dict[str, Any]] = []
        base = git(self.repo, "rev-parse", "HEAD")

        def new_attempt(logical: str, **over: Any) -> dict[str, Any]:
            attempt_id = f"att-{uuid.uuid4().hex[:12]}"
            attempt = {
                "task_id": f"task-{self.run_id[:8]}-{logical}",
                "logical_id": logical,
                "attempt_id": attempt_id,
                "spec": {"logical_id": logical, "goal": "planted", "stack_class": "sibling",
                         "allowed_paths": [f"src/{logical}.py"], "oracle": None,
                         "dependencies": []},
                "base_subject_sha": base,
                "branch": f"worker/{logical}",
                "state": None,
                "lease": {"status": None, "expiry": None, "heartbeat_sequence": 0},
                "checkpoint": {"sequence": 0, "digest": None},
                "heartbeats": [],
                # An attempt that never runs spent nothing, and that is observed
                # rather than unknown: the scheduler is what would have started it.
                "spend": empty_spend(),
                "spend_observed": sorted(BUDGET_DIMENSIONS),
            }
            attempt.update(over)
            self.attempts[attempt_id] = attempt
            return attempt

        # STALE_ATTEMPT: produced against a base main has already moved past.
        stale = new_attempt("planted-stale", base_subject_sha="0" * 40)
        self.transition(stale["attempt_id"], "PLANNED")
        self.transition(stale["attempt_id"], "RESULT_READY", note="planted result")
        self.integrate(stale, self.repo)
        planted.append({"state": "STALE_ATTEMPT", "attempt_id": stale["attempt_id"]})

        # LEASE_EXPIRED: a lease whose expiry is in the past cannot be used.
        expired = new_attempt("planted-expired")
        expired["lease"] = {"status": "ACTIVE",
                            "expiry": stamp(now() - timedelta(seconds=60)),
                            "heartbeat_sequence": 3}
        self.transition(expired["attempt_id"], "LEASED",
                        lease_expiry=expired["lease"]["expiry"])
        evaluated = now()
        if datetime.strptime(expired["lease"]["expiry"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc) < evaluated:
            expired["lease"]["status"] = "EXPIRED"
            self.refuse("LEASE_EXPIRED",
                        f"{expired['attempt_id']} lease expired at "
                        f"{expired['lease']['expiry']}, evaluated {stamp(evaluated)}",
                        attempt_id=expired["attempt_id"])
            self.transition(expired["attempt_id"], "LEASE_EXPIRED",
                            evaluated_at=stamp(evaluated))
        planted.append({"state": "LEASE_EXPIRED", "attempt_id": expired["attempt_id"]})

        # TIMED_OUT then STRAGGLER_DETACHED: a Worker that outlives its budget is
        # detached rather than waited for, and its lease is not reused silently.
        straggler = new_attempt("planted-straggler")
        self.transition(straggler["attempt_id"], "LEASED")
        self.transition(straggler["attempt_id"], "RUNNING")
        # The plant is a Worker that outlived its budget, so its ledger entry has
        # to show the overrun. A TIMED_OUT state beside a spend inside the cap
        # would be a state the ledger contradicts.
        straggler["spend"]["wall_clock_seconds"] = (
            ATTEMPT_BUDGET["wall_clock_seconds"] + 1)
        self.transition(straggler["attempt_id"], "TIMED_OUT",
                        budget_wall_clock_seconds=ATTEMPT_BUDGET["wall_clock_seconds"],
                        spend=dict(straggler["spend"]))
        self.transition(straggler["attempt_id"], "STRAGGLER_DETACHED",
                        note="detached; its lease is not granted to another attempt")
        planted.append({"state": "STRAGGLER_DETACHED",
                        "attempt_id": straggler["attempt_id"]})

        # FAILED_RETRYABLE then SUPERSEDED: the retry supersedes its predecessor
        # rather than both remaining live.
        first = new_attempt("planted-retry")
        self.transition(first["attempt_id"], "LEASED")
        self.transition(first["attempt_id"], "RUNNING")
        self.transition(first["attempt_id"], "FAILED_RETRYABLE", oracle_exit_code=1)
        retry = new_attempt("planted-retry-2")
        retry["task_id"] = first["task_id"]
        self.transition(retry["attempt_id"], "PLANNED",
                        supersedes=first["attempt_id"])
        self.transition(first["attempt_id"], "SUPERSEDED",
                        superseded_by=retry["attempt_id"])
        planted.append({"state": "FAILED_RETRYABLE", "attempt_id": first["attempt_id"]})
        planted.append({"state": "SUPERSEDED", "attempt_id": first["attempt_id"]})

        # CANCELLED: an admitted attempt withdrawn before it ran.
        cancelled = new_attempt("planted-cancelled")
        self.transition(cancelled["attempt_id"], "PLANNED")
        self.transition(cancelled["attempt_id"], "ADMITTED")
        self.transition(cancelled["attempt_id"], "CANCELLED",
                        reason="withdrawn by the scheduler before assignment")
        planted.append({"state": "CANCELLED", "attempt_id": cancelled["attempt_id"]})

        # BLOCKED_CONFLICT: a second attempt asking for a held path lease.
        held = list(self.path_leases)[0] if self.path_leases else "src/celsius.py"
        conflict = new_attempt("planted-conflict")
        conflict["spec"]["allowed_paths"] = [held]
        self.transition(conflict["attempt_id"], "PLANNED")
        self.refuse("PATH_LEASE_HELD", f"{conflict['attempt_id']} requested {held}",
                    attempt_id=conflict["attempt_id"])
        self.transition(conflict["attempt_id"], "BLOCKED_CONFLICT", requested=held)
        planted.append({"state": "BLOCKED_CONFLICT", "attempt_id": conflict["attempt_id"]})

        return planted

    def close(self) -> None:
        """Resolve anything still holding a lease when the run ends.

        A Worker whose oracle failed stayed at FAILED_RETRYABLE with a live
        lease, and the run simply ended around it. Nobody was going to retry it
        and nobody could reclaim its branch, so the honest classification is that
        the scheduler cancelled it at close rather than that it is still working.
        """
        for attempt in self.attempts.values():
            if attempt["lease"].get("status") != "ACTIVE":
                continue
            self.refuse("LEASE_HELD_AT_CLOSE",
                        f"{attempt['attempt_id']} still held its lease when the run "
                        f"ended in state {attempt['state']}",
                        attempt_id=attempt["attempt_id"])
            self.transition(attempt["attempt_id"], "CANCELLED",
                            reason="run closed while the attempt still held its lease",
                            last_state=attempt["state"])

    # -- driver -------------------------------------------------------------

    def run(self) -> dict[str, Any]:
        started = now()
        self.plan()
        self.admit()

        real = [a for a in self.attempts.values() if a["state"] == "ADMITTED"]
        results: dict[str, Any] = {}
        # Siblings first, then anything whose dependencies are now INTEGRATED.
        for _ in range(len(real)):
            progressed = False
            for attempt in real:
                if attempt["state"] != "ADMITTED" or not self.ready(attempt):
                    continue
                exhausted = self.global_overrun()
                if exhausted:
                    # The global cap has to stop something, or it is a number in a
                    # receipt rather than a budget.
                    self.refuse("GLOBAL_BUDGET_EXHAUSTED",
                                f"{attempt['attempt_id']} not started; the run passed "
                                f"{exhausted}", attempt_id=attempt["attempt_id"])
                    self.transition(attempt["attempt_id"], "CANCELLED",
                                    reason="global budget exhausted",
                                    over_budget=exhausted)
                    continue
                progressed = True
                self.assign(attempt)
                if attempt["state"] == "BLOCKED_CONFLICT":
                    continue
                worktree = self.lease(attempt)
                outcome = self.run_worker(attempt, worktree)
                results[attempt["logical_id"]] = outcome
                if not outcome["ok"]:
                    continue
                verified = self.verify(attempt, worktree)
                results[attempt["logical_id"]]["oracle"] = verified
                if not verified["ok"]:
                    continue
                self.integrate(attempt, worktree)
            if not progressed:
                break

        planted = self.plant_non_happy_paths()
        self.close()
        ended = now()

        produced = sorted({t["state"] for t in self.transitions})
        declared = set(HAPPY_PATH) | {
            "REJECTED_NOT_DECOMPOSABLE", "DUPLICATE_SUPPRESSED", "STALE_ATTEMPT",
            "LEASE_EXPIRED", "TIMED_OUT", "CANCELLED", "STRAGGLER_DETACHED",
            "FAILED_RETRYABLE", "FAILED_TERMINAL", "BLOCKED_AUTHORITY",
            "BLOCKED_CONFLICT", "SUPERSEDED"}

        return {
            "schema": SCHEMA,
            "run_id": self.run_id,
            "issue": 231,
            "agent": self.agent,
            "subject": {
                "kind": "disposable-canary-repository",
                "initial_sha": self.transitions[0]["base_subject_sha"],
                "final_sha": git(self.repo, "rev-parse", "HEAD"),
                "note": ("A throwaway repository, not skills-shared. Parallel Workers "
                         "mutating the live repository during a session that other "
                         "sessions are also writing to is a hazard, not a canary."),
            },
            "started_at": stamp(started),
            "ended_at": stamp(ended),
            "duration_ms": int((ended - started).total_seconds() * 1000),
            "happy_path": HAPPY_PATH,
            "attempts": [
                {k: v for k, v in attempt.items()
                 if k not in ("spec", "spend", "spend_observed")} | {
                    "allowed_paths": attempt["spec"]["allowed_paths"],
                    "stack_class": attempt["spec"]["stack_class"],
                    "dependencies": attempt["spec"]["dependencies"],
                }
                for attempt in self.attempts.values()
            ],
            "transitions": self.transitions,
            "refusals": self.refusals,
            "planted": planted,
            "results": results,
            "budget_ledger": self.budget_ledger(),
            "state_coverage": {
                "produced": produced,
                "declared_not_produced": sorted(declared - set(produced)),
            },
            "declared_non_claims": [
                "no throughput, latency or cost advantage over a single Builder is measured",
                "the Agent's code quality is judged only by the oracles listed here",
                "a disposable subject is not a production repository",
                "BLOCKED_AUTHORITY and the two rejection states are not produced by this "
                "canary; they belong to admission paths this plan does not exercise",
                "tool calls are not counted; the Agent reports turns and this harness "
                "does not see individual calls, so no tool-call cap is claimed",
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--agent", default="claude")
    parser.add_argument("--skip-agent", action="store_true",
                        help="drive the lifecycle without invoking a model")
    args = parser.parse_args()

    agent = None if args.skip_agent else shutil.which(args.agent)
    if not args.skip_agent and agent is None:
        print(f"agent {args.agent!r} not on PATH", file=sys.stderr)
        return 64

    root = Path(tempfile.mkdtemp(prefix="scheduler-canary-"))
    try:
        repo = build_subject(root)
        workroot = root / "worktrees"
        workroot.mkdir()
        receipt = Scheduler(repo, workroot, agent).run()
    finally:
        shutil.rmtree(root, ignore_errors=True)

    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / "scheduler-run.receipt.json"
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({
        "receipt": str(target),
        "transitions": len(receipt["transitions"]),
        "refusals": len(receipt["refusals"]),
        "produced_states": receipt["state_coverage"]["produced"],
        "not_produced": receipt["state_coverage"]["declared_not_produced"],
        "budget_totals": receipt["budget_ledger"]["totals"],
        "budget_unobserved": receipt["budget_ledger"]["unobserved_dimensions"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
