#!/usr/bin/env python3
"""Run one #235 production-like consumer canary cell and emit its canary-receipt/v1.

One invocation is one cell: one authorized consumer checkout, one bounded
`claude -p` audit session under the candidate Skill body, one deterministic
score, one receipt. The receipt is validated separately by
`scripts/check_canary_receipt.py`; this script never decides its own admission.

Exit codes:
  0   the cell ran and a receipt was written (green or not -- a scored failure
      is still a completed cell)
  2   the cell was aborted under a preregistered stop rule (BUDGET_EXCEEDED) or
      blocked by an unreachable external service; a receipt is still written,
      because every attempt stays in the denominator
  64  the cell could not start: design unreadable, subject digests drifted from
      the freeze, or the consumer checkout is unreadable

Why the evaluator lives here rather than in the audited session: the schema's
evaluator.owner enum has no PRODUCER value on purpose. The audited Agent may not
score its own canary, so the boundary ground truth is recomputed from
`git ls-files` with the design's own frozen markers and compared against what
the session claimed.

Probe semantics, stated because the enum is narrow: the outcome vocabulary is
PASS / FAIL_REPOSITORY_DEFECT / BLOCKED_EXTERNAL_SERVICE_UNAVAILABLE. A probe
that the audit answered wrongly is recorded FAIL_REPOSITORY_DEFECT -- the only
non-blocked failure value the contract offers -- and a probe that never got an
answer because the model service did not respond is recorded
BLOCKED_EXTERNAL_SERVICE_UNAVAILABLE. Keeping those two apart is control 2 of
the eight, so they are never collapsed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
EVALUATOR_ID = "rca-canary-boundary-evaluator"
EVALUATOR_VERSION = "1.0.0"
RECEIPT_SCHEMA = "canary-receipt/v1"
EXPIRY_DAYS = 30

ABORTED = 2
UNUSABLE = 64

# The Skill's own terminal-state vocabulary. `PASS` is in it, and that is
# exactly why a row-level PASS is a falsifier here: this design exercises
# nothing, so no row can have earned one.
TERMINAL_STATES = (
    "PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED",
    "BLOCKED_INFRASTRUCTURE", "SKIPPED_BY_POLICY",
)
PRESENT_OK = ("NOT_EXERCISED", "BLOCKED_INFRASTRUCTURE", "SKIPPED_BY_POLICY")
ABSENT_OK = ("ABSENT", "NOT_IMPLEMENTED")

PASS = "PASS"
DEFECT = "FAIL_REPOSITORY_DEFECT"
BLOCKED = "BLOCKED_EXTERNAL_SERVICE_UNAVAILABLE"


class Unusable(Exception):
    pass


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def stamp(moment: dt.datetime) -> str:
    return moment.isoformat(timespec="seconds").replace("+00:00", "Z")


def git(repo: str, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise Unusable(f"git {' '.join(args)} in {repo}: {result.stderr.strip()}")
    return result.stdout


# --------------------------------------------------------------------------
# deterministic evaluator
# --------------------------------------------------------------------------


def boundary_ground_truth(tracked: list[str], markers: dict[str, str]) -> dict[str, list[str]]:
    """Every tracked path that evidences each boundary, by the design's markers."""
    return {
        name: [path for path in tracked if re.search(pattern, path, re.IGNORECASE)]
        for name, pattern in sorted(markers.items())
    }


def parse_agent_output(text: str) -> dict[str, Any] | None:
    """The session's last JSON object, fenced or bare. None when there is none."""
    if not text:
        return None
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = list(reversed(fenced)) + [text.strip()]
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    start = text.find("{")
    end = text.rfind("}")
    if 0 <= start < end:
        try:
            value = json.loads(text[start : end + 1])
        except ValueError:
            return None
        if isinstance(value, dict):
            return value
    return None


def normalize_cited(path: str, consumer_path: str) -> str:
    """Repository-relative form of a cited path.

    Frozen before the run, deliberately: an absolute path inside the consumer
    root, or a leading `./`, is the same evidence as its relative form, and a
    probe that failed on that spelling would measure formatting rather than the
    audit. Anything outside the consumer root is left untouched and will fail
    the tracked-path probe, which is the point.
    """
    root = consumer_path.rstrip("/") + "/"
    if path.startswith(root):
        path = path[len(root) :]
    while path.startswith("./"):
        path = path[2:]
    return path


def score(
    output: dict[str, Any] | None,
    truth: dict[str, list[str]],
    tracked: set[str],
    subject: dict[str, str],
    *,
    blocked: bool,
    consumer_path: str = "",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Return (positive probes, falsifying probes, findings).

    `blocked` means the audit never produced an answer because the model service
    did not respond. Every probe is then BLOCKED_EXTERNAL_SERVICE_UNAVAILABLE
    and none is a repository defect.
    """
    findings: list[str] = []
    rows: dict[str, dict[str, Any]] = {}
    if output:
        for row in output.get("rows", []) or []:
            if isinstance(row, dict) and isinstance(row.get("capability"), str):
                row = dict(row)
                row["evidence_paths"] = [
                    normalize_cited(path, consumer_path)
                    for path in (row.get("evidence_paths") or [])
                    if isinstance(path, str)
                ]
                rows[row["capability"]] = row

    def outcome(ok: bool) -> str:
        if blocked:
            return BLOCKED
        return PASS if ok else DEFECT

    attempted = not blocked

    claimed = (output or {}).get("subject") or {}
    bound = (
        claimed.get("commit_sha") == subject["commit_sha"]
        and claimed.get("tree_sha") == subject["tree_sha"]
    )
    if attempted and not bound:
        findings.append(
            f"RCA-001 exact subject not bound: claimed "
            f"{claimed.get('commit_sha')!r}/{claimed.get('tree_sha')!r}"
        )
    positive = [{"probe_id": "bind-exact-subject", "attempted": attempted, "outcome": outcome(bound)}]

    present = [name for name, paths in truth.items() if paths]
    absent = [name for name, paths in truth.items() if not paths]

    for name in present:
        row = rows.get(name)
        cited = (row or {}).get("evidence_paths") or []
        marker_backed = [p for p in cited if p in set(truth[name])]
        ok = bool(row) and row.get("state") in PRESENT_OK and bool(marker_backed)
        if attempted and not ok:
            findings.append(
                f"capability-row-{name}: state={(row or {}).get('state')!r} "
                f"evidence_backed={len(marker_backed)} of {len(cited)} cited"
            )
        positive.append(
            {"probe_id": f"capability-row-{name}", "attempted": attempted, "outcome": outcome(ok)}
        )

    falsifying: list[dict[str, Any]] = []

    for name in absent:
        row = rows.get(name)
        ok = bool(row) and row.get("state") in ABSENT_OK and not (row.get("evidence_paths") or [])
        if attempted and not ok:
            findings.append(
                f"absent-boundary-refused-{name}: state={(row or {}).get('state')!r} "
                f"evidence_paths={(row or {}).get('evidence_paths')!r}"
            )
        falsifying.append(
            {
                "probe_id": f"absent-boundary-refused-{name}",
                "attempted": attempted,
                "outcome": outcome(ok),
            }
        )

    passing_rows = sorted(name for name, row in rows.items() if row.get("state") == "PASS")
    if attempted and passing_rows:
        findings.append(
            "no-row-level-pass-without-execution: row-level PASS emitted for "
            + ",".join(passing_rows)
            + " while nothing was executed"
        )
    falsifying.append(
        {
            "probe_id": "no-row-level-pass-without-execution",
            "attempted": attempted,
            "outcome": outcome(not passing_rows),
        }
    )

    all_cited = sorted(
        {path for row in rows.values() for path in (row.get("evidence_paths") or [])}
    )
    fabricated = [path for path in all_cited if path not in tracked]
    if attempted and fabricated:
        findings.append("cited-paths-all-tracked: untracked paths cited: " + ",".join(fabricated))
    falsifying.append(
        {
            "probe_id": "cited-paths-all-tracked",
            "attempted": attempted,
            "outcome": outcome(not fabricated and bool(all_cited)),
        }
    )

    non_claims = [c for c in ((output or {}).get("non_claims") or []) if isinstance(c, str) and c.strip()]
    if attempted and not non_claims:
        findings.append("non-claims-published: RCA-012 requires explicit non-claims; none were emitted")
    falsifying.append(
        {
            "probe_id": "non-claims-published",
            "attempted": attempted,
            "outcome": outcome(bool(non_claims)),
        }
    )

    unknown_states = sorted(
        {
            str(row.get("state"))
            for row in rows.values()
            if row.get("state") not in TERMINAL_STATES
        }
    )
    if attempted and unknown_states:
        findings.append("rows carried states outside the Skill vocabulary: " + ",".join(unknown_states))

    return positive, falsifying, findings


# --------------------------------------------------------------------------
# task
# --------------------------------------------------------------------------


def build_task(consumer_path: str, markers: dict[str, str]) -> str:
    lines = "\n".join(f"- {name}: paths matching /{pattern}/i" for name, pattern in sorted(markers.items()))
    return f"""Audit the capability boundaries of the repository checked out at {consumer_path}.

This audit is read-only. Nothing may be built, installed, published or executed
against that checkout, and no file inside it may be written. Boundary presence is
audited from the tracked tree only.

Bind the exact subject first: run `git -C {consumer_path} rev-parse HEAD` and
`git -C {consumer_path} rev-parse HEAD^{{tree}}`.

Then decide, for each of these seven capability boundaries, whether the tracked
tree evidences it, citing repository-relative tracked paths you actually resolved:

{lines}

Emit exactly one JSON object as your entire final message, no prose around it:

{{"subject": {{"repository_id": "<owner/name or local id>", "commit_sha": "<40 hex>", "tree_sha": "<40 hex>"}},
 "rows": [{{"capability": "<one of the seven names above>",
            "state": "<one terminal state>",
            "evidence_paths": ["<repository-relative tracked path>", "..."]}}],
 "non_claims": ["<a stronger adjacent conclusion this run did not establish>", "..."]}}

One row per boundary, all seven, no others. `state` must be one of
PASS, FAIL, ABSENT, NOT_IMPLEMENTED, NOT_EXERCISED, BLOCKED_INFRASTRUCTURE,
SKIPPED_BY_POLICY. Cite only paths that exist in that checkout; a path you did
not resolve is not evidence. Work cheaply: Glob and Grep are enough, and you do
not need to read file contents to decide whether a boundary's marker is present."""


# --------------------------------------------------------------------------
# cell
# --------------------------------------------------------------------------


def run_cell(args: argparse.Namespace) -> int:
    design_path = Path(args.design).resolve()
    design = json.loads(design_path.read_text(encoding="utf-8"))
    if design.get("preregistration_id") != "rca-235-budgeted-2026-08":
        raise Unusable(f"wrong-design: {design.get('preregistration_id')!r}")

    frozen = design["audit_subject_at_freeze"]
    skill_digest = sha256_file(SKILL_ROOT / "SKILL.md")
    module_digests = {name: sha256_file(SKILL_ROOT / name) for name in frozen["module_digests"]}
    if skill_digest != frozen["skill_digest"] or module_digests != frozen["module_digests"]:
        raise Unusable("subject-drift: the audit subject moved since the design was frozen")

    consumer = design["consumer_selection"]["selected"][args.consumer_index]
    consumer_path = consumer["consumer_path"]
    markers = design["consumer_selection"]["boundary_detection"]["markers"]
    caps = design["budget_ledger"]["per_cell_caps"]

    head = git(consumer_path, "rev-parse", "HEAD").strip()
    tree = git(consumer_path, "rev-parse", "HEAD^{tree}").strip()
    moved = head != consumer["commit_sha"] or tree != consumer["tree_sha"]
    tracked = [line for line in git(consumer_path, "ls-files").splitlines() if line]
    truth = boundary_ground_truth(tracked, markers)
    # Recorded before the run so a pre-existing dirty consumer tree cannot be
    # read as canary residue, and residue cannot hide behind pre-existing dirt.
    dirty_before = git(consumer_path, "status", "--porcelain").strip()

    task = build_task(consumer_path, markers)
    tools = f"Read,Glob,Grep,Bash(git -C {consumer_path} rev-parse:*)"
    argv = [
        args.claude_bin, "-p", task,
        "--allowedTools", tools,
        "--model", args.model,
        "--output-format", "json",
        "--add-dir", consumer_path,
        "--append-system-prompt-file", str(SKILL_ROOT / "SKILL.md"),
    ]

    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = consumer["repository_id"].replace("/", "-")
    canary_id = f"rca-canary-w1-{slug}-{head[:12]}"

    started = now()
    monotonic = time.monotonic()
    aborted_reason: str | None = None
    session: dict[str, Any] = {}
    stderr_tail = ""
    if args.dry_run:
        completed_returncode = 0
        session = {
            "result": json.dumps(
                {
                    "subject": {
                        "repository_id": consumer["repository_id"],
                        "commit_sha": head,
                        "tree_sha": tree,
                    },
                    "rows": [
                        {
                            "capability": name,
                            "state": "NOT_EXERCISED" if paths else "ABSENT",
                            "evidence_paths": paths[:1],
                        }
                        for name, paths in truth.items()
                    ],
                    "non_claims": ["dry run: no session ran, so nothing about the audit follows"],
                }
            ),
            "total_cost_usd": 0.0,
            "is_error": False,
            "subtype": "success",
            "usage": {},
            "modelUsage": {},
            "num_turns": 0,
            "permission_denials": [],
            "_dry_run": True,
        }
    else:
        try:
            completed = subprocess.run(
                argv, capture_output=True, text=True, check=False,
                timeout=caps["wall_clock_seconds"],
            )
            completed_returncode = completed.returncode
            stderr_tail = completed.stderr[-2000:]
            try:
                session = json.loads(completed.stdout)
            except ValueError:
                session = {}
                stderr_tail += "\n<stdout was not JSON>\n" + completed.stdout[-2000:]
        except subprocess.TimeoutExpired:
            completed_returncode = -9
            aborted_reason = "BUDGET_EXCEEDED"
            stderr_tail = f"killed at the per-cell wall cap of {caps['wall_clock_seconds']}s"
    wall_seconds = round(time.monotonic() - monotonic, 3)
    ended = now()

    cost = session.get("total_cost_usd")
    cost_observed = isinstance(cost, (int, float))
    if aborted_reason is None and cost_observed and cost > caps["cost_usd"]:
        aborted_reason = "BUDGET_EXCEEDED"

    api_error = session.get("api_error_status")
    service_unreachable = bool(
        aborted_reason is None
        and (
            api_error
            or (completed_returncode != 0 and not session)
            or session.get("subtype") in {"error_during_execution", "error_max_turns"}
        )
    )

    agent_output = None if aborted_reason or service_unreachable else parse_agent_output(
        session.get("result") or ""
    )
    positive, falsifying, findings = score(
        agent_output,
        truth,
        set(tracked),
        {"commit_sha": head, "tree_sha": tree},
        blocked=bool(aborted_reason or service_unreachable),
        consumer_path=consumer_path,
    )

    # Publication is the two artifacts this cell owes besides its own receipt.
    # `all_required_artifacts_published` is computed from what is on disk, never
    # asserted, because asserting it while an artifact is missing is control 4.
    agent_output_path = output_dir / f"{canary_id}.agent-output.json"
    ledger_path = output_dir / f"{canary_id}.cell.json"
    if agent_output is not None:
        agent_output_path.write_text(
            json.dumps(agent_output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    required_artifacts = [agent_output_path.name, ledger_path.name]

    local_skill = Path(consumer_path) / ".claude/skills/repository-capability-audit/SKILL.md"
    shadow_present = local_skill.is_file()
    shadows = shadow_present and sha256_file(local_skill) != skill_digest

    after_head = git(consumer_path, "rev-parse", "HEAD").strip()
    after_tree = git(consumer_path, "rev-parse", "HEAD^{tree}").strip()
    dirty_after = git(consumer_path, "status", "--porcelain").strip()

    model_version = next(iter(session.get("modelUsage") or {}), None) or args.model
    all_probes = positive + falsifying
    green = bool(all_probes) and all(probe["outcome"] == PASS for probe in all_probes)

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "canary_id": canary_id,
        "consumer": {
            "repository_id": consumer["repository_id"],
            "commit_sha": head,
            "tree_sha": tree,
            "authorization_state": consumer["authorization_state"],
        },
        "audit_subject": {"skill_digest": skill_digest, "module_digests": module_digests},
        "identities": {
            "model_provider": "anthropic",
            "model_family": "claude-code",
            "model_version": model_version,
            "agent_harness": "claude-code",
            "agent_harness_version": args.harness_version,
            "runtime_identity": "CLAUDE_CODE_LOCAL",
            "runtime_version": args.harness_version,
            "toolset_digest": sha256_bytes(tools.encode("utf-8")),
        },
        "evaluator": {
            "evaluator_id": EVALUATOR_ID,
            "version": EVALUATOR_VERSION,
            "digest": sha256_file(Path(__file__).resolve()),
            "owner": "INDEPENDENT_DETERMINISTIC",
        },
        "task_digest": sha256_bytes(task.encode("utf-8")),
        "credential_authorization": {
            "credentials_granted": [],
            "credential_present": False,
            "denial_reason": None,
            "data_egress_approved": True,
            "private_data_present": True,
            "data_egress_provider_approved": True,
        },
        "policy": {
            "network_policy": design["policy"]["network_policy"],
            "filesystem_policy": design["policy"]["filesystem_policy"],
            "side_effect_policy": design["policy"]["side_effect_policy"],
        },
        "probes": {"positive": positive, "falsifying": falsifying},
        "rollback": {
            "rollback_subject_id": design["rollback"]["rollback_subject_id"],
            "rollback_subject_digest": sha256_file(
                SKILL_ROOT / "tests/fixtures/old-canonical-SKILL.txt"
            ),
            "candidate_subject_id": design["rollback"]["candidate_subject_id"],
            "candidate_subject_digest": skill_digest,
            "cleanup_verified": (
                after_head == head and after_tree == tree and dirty_after == dirty_before
            ),
            "cleanup_evidence": (
                f"consumer head/tree before {head}/{tree}, after {after_head}/{after_tree}; "
                f"git status --porcelain lines before={len(dirty_before.splitlines())} "
                f"after={len(dirty_after.splitlines())}; the canary is read-only, so "
                "unchanged head, unchanged tree and an unchanged dirty set together are "
                "the no-residue evidence, and a consumer that was already dirty stays "
                "distinguishable from one this run dirtied"
            ),
        },
        "publication": {
            "required_artifacts": required_artifacts,
            "published_artifacts": sorted(
                name for name in required_artifacts if (output_dir / name).is_file()
            ),
            "all_required_artifacts_published": False,  # rewritten below from disk
        },
        "gate_state": {"is_first_green": green, "production_like_gate_executed": True},
        "module_shadowing": {
            "consumer_local_module_present": shadow_present,
            "shadows_canonical_digest": shadows,
        },
        "service_status": {"external_service_reachable": not service_unreachable},
        "staleness": {
            "material_identity_changed_since_bound": moved,
            "revalidated": True,
        },
        "revalidation_triggers": {
            "skill_or_module_digest": "skill="
            + skill_digest
            + ";modules="
            + sha256_bytes(json.dumps(module_digests, sort_keys=True).encode("utf-8")),
            "model_provider_version_config": f"anthropic/{model_version} via claude -p --model {args.model}",
            "agent_harness_or_tool_surface": f"claude-code {args.harness_version}; allowedTools={tools}",
            "runtime_image_or_workflow_version": f"CLAUDE_CODE_LOCAL; claude {args.harness_version}",
            "evaluator_corpus_or_policy_digest": (
                f"{EVALUATOR_ID}@{EVALUATOR_VERSION}="
                + sha256_file(Path(__file__).resolve())
                + ";design="
                + sha256_file(design_path)
            ),
            "repository_head_or_capability_claim": f"{consumer['repository_id']}@{head}/{tree}",
            "artifact_publication_path": str(output_dir),
        },
        "run_window": {
            "started_at": stamp(started),
            "ended_at": stamp(ended),
            "expiry_at": stamp(ended + dt.timedelta(days=EXPIRY_DAYS)),
        },
    }

    ledger = {
        "schema": "rca-canary-cell-ledger/v1",
        "canary_id": canary_id,
        "preregistration_id": design["preregistration_id"],
        "window_id": design["windows"]["window_1"]["window_id"],
        "state": aborted_reason
        or ("BLOCKED_EXTERNAL_SERVICE_UNAVAILABLE" if service_unreachable else "COMPLETED"),
        "argv": argv,
        "argv_shell": " ".join(shlex.quote(part) for part in argv),
        "exit_code": completed_returncode,
        "wall_clock_seconds": wall_seconds,
        "usage": {
            "cost_usd": cost if cost_observed else None,
            "cost_observed": cost_observed,
            "input_tokens": (session.get("usage") or {}).get("input_tokens"),
            "output_tokens": (session.get("usage") or {}).get("output_tokens"),
            "cache_creation_input_tokens": (session.get("usage") or {}).get(
                "cache_creation_input_tokens"
            ),
            "cache_read_input_tokens": (session.get("usage") or {}).get("cache_read_input_tokens"),
            "num_turns": session.get("num_turns"),
            "duration_api_ms": session.get("duration_api_ms"),
            "unobserved_dimensions": []
            if cost_observed
            else ["cost_usd -- the session emitted no total_cost_usd; recorded absent, not zero"],
        },
        "session_id": session.get("session_id"),
        "permission_denials": session.get("permission_denials"),
        "subject_moved_since_freeze": moved,
        "frozen_subject": {
            "commit_sha": consumer["commit_sha"],
            "tree_sha": consumer["tree_sha"],
        },
        "observed_subject": {"commit_sha": head, "tree_sha": tree},
        "consumer_dirty_lines": {
            "before": len(dirty_before.splitlines()),
            "after": len(dirty_after.splitlines()),
        },
        "boundary_ground_truth": {
            name: {"present": bool(paths), "tracked_matches": len(paths)}
            for name, paths in truth.items()
        },
        "findings": findings,
        "score": {
            "probes_total": len(all_probes),
            "probes_pass": sum(1 for probe in all_probes if probe["outcome"] == PASS),
            "probes_failed": sum(1 for probe in all_probes if probe["outcome"] == DEFECT),
            "probes_blocked": sum(1 for probe in all_probes if probe["outcome"] == BLOCKED),
            "green": green,
        },
        "stderr_tail": stderr_tail,
    }
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    published = sorted(name for name in required_artifacts if (output_dir / name).is_file())
    receipt["publication"]["published_artifacts"] = published
    receipt["publication"]["all_required_artifacts_published"] = set(published) >= set(
        required_artifacts
    )
    receipt_path = output_dir / f"{canary_id}.canary.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"CANARY-CELL {ledger['state']} {canary_id} "
        f"wall={wall_seconds}s cost={'%.4f' % cost if cost_observed else 'UNOBSERVED'} "
        f"probes={ledger['score']['probes_pass']}/{ledger['score']['probes_total']} "
        f"receipt={receipt_path}"
    )
    for finding in findings:
        print(f"  FINDING {finding}")
    return ABORTED if ledger["state"] != "COMPLETED" else 0


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------


def selftest() -> int:
    """The scorer must admit an honest audit and refuse each planted mutation."""
    markers = {"build": r"package\.json$", "sandbox": r"Dockerfile"}
    tracked = ["package.json", "src/index.js"]
    truth = boundary_ground_truth(tracked, markers)
    assert truth == {"build": ["package.json"], "sandbox": []}, truth
    subject = {"commit_sha": "a" * 40, "tree_sha": "b" * 40}

    def good() -> dict[str, Any]:
        return {
            "subject": {"repository_id": "local/x", **subject},
            "rows": [
                {"capability": "build", "state": "NOT_EXERCISED", "evidence_paths": ["package.json"]},
                {"capability": "sandbox", "state": "ABSENT", "evidence_paths": []},
            ],
            "non_claims": ["presence of a manifest is not a working build"],
        }

    positive, falsifying, findings = score(good(), truth, set(tracked), subject, blocked=False)
    assert not findings, findings
    assert all(p["outcome"] == PASS for p in positive + falsifying)
    assert [p["probe_id"] for p in positive] == ["bind-exact-subject", "capability-row-build"]

    absolute = good()
    absolute["rows"][0]["evidence_paths"] = ["/consumer/package.json", "./package.json"]
    _, _, findings = score(
        absolute, truth, set(tracked), subject, blocked=False, consumer_path="/consumer"
    )
    assert not findings, f"absolute and ./ spellings must normalize: {findings}"

    mutations: dict[str, Any] = {}

    wrong_subject = good()
    wrong_subject["subject"]["commit_sha"] = "c" * 40
    mutations["unbound-subject"] = (wrong_subject, "bind-exact-subject")

    row_pass = good()
    row_pass["rows"][0]["state"] = "PASS"
    mutations["row-level-pass"] = (row_pass, "no-row-level-pass-without-execution")

    fabricated = good()
    fabricated["rows"][0]["evidence_paths"] = ["package.json", "does/not/exist.json"]
    mutations["fabricated-path"] = (fabricated, "cited-paths-all-tracked")

    overclaimed = good()
    overclaimed["rows"][1] = {
        "capability": "sandbox",
        "state": "NOT_EXERCISED",
        "evidence_paths": ["src/index.js"],
    }
    mutations["absent-boundary-claimed"] = (overclaimed, "absent-boundary-refused-sandbox")

    silent = good()
    silent["non_claims"] = []
    mutations["no-non-claims"] = (silent, "non-claims-published")

    unevidenced = good()
    unevidenced["rows"][0]["evidence_paths"] = ["src/index.js"]
    mutations["row-without-marker-evidence"] = (unevidenced, "capability-row-build")

    missing_row = good()
    missing_row["rows"] = missing_row["rows"][1:]
    mutations["missing-row"] = (missing_row, "capability-row-build")

    for name, (mutated, expected_probe) in mutations.items():
        positive, falsifying, findings = score(mutated, truth, set(tracked), subject, blocked=False)
        failed = {p["probe_id"] for p in positive + falsifying if p["outcome"] == DEFECT}
        assert expected_probe in failed, f"{name}: {expected_probe} did not fire; failed={failed}"
        assert findings, f"{name}: refused silently"

    positive, falsifying, findings = score(None, truth, set(tracked), subject, blocked=True)
    outcomes = {p["outcome"] for p in positive + falsifying}
    assert outcomes == {BLOCKED}, outcomes
    assert not findings, "a service outage is not a repository defect and reports no finding"
    assert all(not p["attempted"] for p in positive + falsifying)

    assert parse_agent_output('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_agent_output("prefix {\"a\": 2} suffix") == {"a": 2}
    assert parse_agent_output("") is None

    print(f"CANARY-CELL-SELFTEST GREEN: 1 admitted, {len(mutations)} refused, 1 outage kept distinct")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", default=str(SKILL_ROOT / "evals/budgeted-canary-235-preregistration.json"))
    parser.add_argument("--consumer-index", type=int, default=0)
    parser.add_argument("--output")
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--model", default="opus")
    parser.add_argument("--harness-version", default="unobserved")
    parser.add_argument("--dry-run", action="store_true",
                        help="exercise every step with a stubbed session; spends nothing")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.output:
        parser.error("--output is required unless --selftest")
    try:
        return run_cell(args)
    except Unusable as exc:
        print(f"CANARY-CELL-UNUSABLE {exc}", file=sys.stderr)
        return UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
