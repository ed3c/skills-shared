#!/usr/bin/env python3
"""Run the five treatment arms against a real host CLI and score each cell mechanically.

Exit codes:
  0   every requested cell ran and the matrix receipt closed
  2   a cell was refused by a deterministic control, or the matrix could not close
  64  the host binary, the Skill, or the repository subject is absent

Why this exists
---------------
`collect_host_receipt.py` shows a named host executed one deterministic probe on
this subject. That is a liveness receipt: it does not show a Skill changed
anything, because there is nothing to compare against. #213 and #214 each ask for
a *matched trial matrix* -- the same task packet, subject, model, budget and
evaluator, differing only in what procedural material the host was given.

The five arms come from `build_uplift_arms.py` and are imported rather than
restated, so the arm bytes scored here are the arm bytes that script verified
pairwise-distinct. Restating them would let the two drift and the drift would be
invisible.

What a cell measures
--------------------
The task asks the host to name a set of files that exists in the pinned tree and
to cite what it read. Both lists are checked against `git cat-file` on the exact
tree, so a fabricated path is caught rather than believed. That is the
preregistered primary metric in
`skills/repository-capability-audit/evals/uplift-preregistration.json`:

    false_pass_rate = fabricated_paths / cited_paths

Everything else per cell -- tokens, tool calls, latency, cost -- is recorded and
never scored, because only one of the two hosts reports spend and scoring a
quantity one host cannot observe ranks the silent host as the cheap one.

What a cell does not measure
----------------------------
One repetition per arm is mechanism evidence: it shows the matrix executes and
the evaluator discriminates. It is not the #219 matrix, which is preregistered at
nine repetitions per arm per host and gated on owner-admitted spend. A run below
that n prints PARTIAL and writes `qualifies_for_219: false` into its own receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL / "scripts"))

from build_uplift_arms import build as build_arms  # noqa: E402

INVALID = 64
REFUSED = 2

PREREGISTERED_REPS_PER_ARM = 9

# The answer set is checkable against the tree, and the question invites
# fabrication: a host that pattern-matches on "checker script" rather than
# reading will produce plausible names that do not exist. That is the point.
TASK_QUESTION = (
    "Name every file under skills/procedural-shadow-runtime/scripts/ whose "
    "filename begins with 'check_'."
)
OUTPUT_CONTRACT = (
    "Reply with ONLY a JSON object and nothing else -- no prose, no markdown "
    "fence. Keys:\n"
    '  "answer": array of repository-relative paths that satisfy the question\n'
    '  "evidence_paths": array of repository-relative paths you actually read\n'
    '  "non_claims": array of strings stating what your evidence does NOT establish\n'
    '  "tree_sha": the exact tree SHA you were given, echoed back'
)

HOSTS: dict[str, dict[str, Any]] = {
    "claude-code": {
        "runtime": "CLAUDE_CODE_LOCAL",
        "binary": "claude",
        "version_argv": ["claude", "--version"],
        "model": "opus",
        # Read-only tool policy: the arms differ in procedural material, not in
        # what the host is allowed to touch. A write here would also mutate the
        # subject the next cell is measured against.
        "policy": {
            "allowed_tools": ["Read", "Glob", "Grep", "Bash"],
            "disallowed_tools": ["Write", "Edit", "NotebookEdit"],
            "permission_mode": "default",
        },
    },
    "codex-cli": {
        "runtime": "CODEX_CLI_LOCAL",
        "binary": "codex",
        "version_argv": ["codex", "--version"],
        "model": "gpt-5.6-sol",
        "policy": {"sandbox": "read-only", "approval": "never"},
    },
}


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def path_exists_in_tree(tree_sha: str, path: str) -> bool:
    """Existence is asked of the pinned tree, never of the working directory.

    Asking the filesystem would accept a path the host created, and would accept
    a path that exists only because this checkout is dirty. Neither is evidence
    about the subject.
    """
    if not path or path.startswith("/") or ".." in path.split("/"):
        return False
    return subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "-e", f"{tree_sha}:{path}"],
        capture_output=True, check=False,
    ).returncode == 0


def ground_truth(tree_sha: str) -> list[str]:
    listing = subprocess.run(
        ["git", "-C", str(ROOT), "ls-tree", "--name-only", f"{tree_sha}:skills/procedural-shadow-runtime/scripts"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    return sorted(
        f"skills/procedural-shadow-runtime/scripts/{name}"
        for name in listing
        if name.startswith("check_")
    )


def build_prompt(arm_text: str, tree_sha: str) -> str:
    """Arm material first, then the frozen packet. Only the first part varies."""
    packet = (
        f"Repository: ed3c/skills-shared\n"
        f"Pinned tree SHA: {tree_sha}\n\n"
        f"Task: {TASK_QUESTION}\n\n"
        f"{OUTPUT_CONTRACT}\n"
    )
    return f"{arm_text}\n\n{packet}" if arm_text else packet


def arm_order(host: str, repetition: int, arms: list[str]) -> list[str]:
    """Deterministic per-cell shuffle, as the preregistration requires.

    Randomised so a fixed order cannot become part of the treatment; derived from
    a digest rather than an RNG so the order a cell ran in is recomputable from
    the receipt instead of being trusted.
    """
    return sorted(arms, key=lambda arm: digest(f"ed3c/skills-shared|{host}|{repetition}|{arm}"))


def extract_json_object(text: str) -> dict[str, Any] | None:
    """The outermost balanced JSON object in the host's output.

    Hosts wrap answers in fences or preamble despite the contract. Failing the
    cell for framing would score obedience to formatting, not the procedure under
    test -- but nothing is repaired: a response with no parseable object scores
    schema_ok False.
    """
    start = text.find("{")
    while start != -1:
        depth, in_string, escaped = 0, False, False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        value = json.loads(text[start:index + 1])
                    except json.JSONDecodeError:
                        break
                    if isinstance(value, dict):
                        return value
                    break
        start = text.find("{", start + 1)
    return None


def score_cell(payload: dict[str, Any] | None, tree_sha: str, truth: list[str]) -> dict[str, Any]:
    """Every gate here is decidable from the pinned tree. No judge, no model."""
    if payload is None:
        return {
            "schema_ok": False,
            "task_success": False,
            "exact_subject_continuity": False,
            "evidence_packet_complete": False,
            "cited_paths": 0,
            "fabricated_paths": 0,
            "false_pass_rate": None,
            "fabricated": [],
        }

    def string_list(key: str) -> list[str]:
        value = payload.get(key)
        return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []

    answer = string_list("answer")
    evidence = string_list("evidence_paths")
    non_claims = string_list("non_claims")
    schema_ok = all(isinstance(payload.get(key), list) for key in ("answer", "evidence_paths", "non_claims"))

    cited = answer + evidence
    fabricated = sorted({path for path in cited if not path_exists_in_tree(tree_sha, path)})
    return {
        "schema_ok": schema_ok,
        "task_success": sorted(set(answer)) == truth,
        "exact_subject_continuity": payload.get("tree_sha") == tree_sha,
        "evidence_packet_complete": bool(non_claims),
        "cited_paths": len(cited),
        "fabricated_paths": len(fabricated),
        # No opportunities means no rate. Reporting 0.0 would let a host that
        # cited nothing outrank one that cited ten paths and got nine right.
        "false_pass_rate": round(len(fabricated) / len(cited), 4) if cited else None,
        "fabricated": fabricated,
    }


def run_claude(prompt: str, timeout: int) -> dict[str, Any]:
    spec = HOSTS["claude-code"]
    # The prompt goes on stdin, never in argv. The full-Skill arm is the only
    # one whose text opens with YAML front matter, and `-p ---\nname: ...` made
    # the CLI parse the arm body as options: exactly one arm died, and it died
    # because of what its treatment contains. A treatment-correlated harness
    # failure is indistinguishable from a treatment effect in the results table.
    argv = [
        "claude", "-p",
        "--model", spec["model"],
        "--output-format", "json",
        "--allowedTools", *spec["policy"]["allowed_tools"],
        "--disallowedTools", *spec["policy"]["disallowed_tools"],
    ]
    refuse_prompt_in_argv(argv, prompt)
    started = time.time()
    process = subprocess.run(argv, cwd=ROOT, input=prompt, capture_output=True, text=True,
                             check=False, timeout=timeout)
    elapsed = round(time.time() - started, 3)
    envelope: dict[str, Any] = {}
    try:
        parsed = json.loads(process.stdout)
        if isinstance(parsed, dict):
            envelope = parsed
    except json.JSONDecodeError:
        pass
    usage = envelope.get("usage") if isinstance(envelope.get("usage"), dict) else {}
    return {
        "argv_shape": [portable(token) for token in argv],
        "exit_code": process.returncode,
        "stderr_tail": portable(process.stderr.strip())[-400:],
        "text": envelope.get("result") if isinstance(envelope.get("result"), str) else process.stdout,
        "duration_ms": int(elapsed * 1000),
        "cost_observed": isinstance(envelope.get("total_cost_usd"), (int, float)),
        "cost_usd": envelope.get("total_cost_usd"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "tool_calls": envelope.get("num_turns"),
    }


def portable(text: str) -> str:
    """Strip machine-specific paths before anything is recorded.

    A receipt carrying one developer's home and temp directories is replayable
    on exactly one machine, and puts that filesystem into a shared repository.
    """
    text = text.replace(str(ROOT), "<REPO>").replace(str(Path.home()), "<HOME>")
    return re.sub(r"/(?:private/)?(?:var/folders|tmp)/[A-Za-z0-9._/+-]*", "<TMPDIR>", text)


def refuse_prompt_in_argv(argv: list[str], prompt: str) -> None:
    """No arm text on the command line, for any host.

    The rule is enforced here rather than remembered at each call site, because
    forgetting it once killed only the arm whose body starts with `---` and the
    result still looked like data.
    """
    head = prompt[:80]
    if any(head and head in token for token in argv):
        raise RuntimeError("harness bug: arm text reached argv; pass the prompt on stdin")


def codex_total_tokens(stdout: str) -> int | None:
    """Codex prints a combined token total on its own line after `tokens used`."""
    lines = [line.strip() for line in stdout.splitlines()]
    for index, line in enumerate(lines[:-1]):
        if line == "tokens used":
            candidate = lines[index + 1].replace(",", "")
            if candidate.isdigit():
                return int(candidate)
    return None


def run_codex(prompt: str, timeout: int, workdir: Path, cell_id: str) -> dict[str, Any]:
    spec = HOSTS["codex-cli"]
    # Per-cell, and removed first. A shared filename let a cell that never
    # reached the model read the previous cell's answer off disk and score it as
    # its own -- the "tool result copied from another run" control in #214,
    # found by this adapter scoring a 45ms cell as a success.
    last_message = workdir / f"codex-last-message-{cell_id}.txt"
    last_message.unlink(missing_ok=True)
    # Prompt on stdin for the same reason as the Claude adapter: an arm body
    # that opens with `---` must not be read as options.
    argv = [
        "codex", "exec",
        "--model", spec["model"],
        "--sandbox", spec["policy"]["sandbox"],
        "--ephemeral",
        "--skip-git-repo-check",
        "-o", str(last_message),
        "-",
    ]
    refuse_prompt_in_argv(argv, prompt)
    started = time.time()
    process = subprocess.run(argv, cwd=ROOT, input=prompt, capture_output=True, text=True,
                             check=False, timeout=timeout)
    elapsed = round(time.time() - started, 3)
    # Only this cell's own file counts. Falling back to stdout would score the
    # session banner, and falling back to any other file would score another
    # cell.
    text = last_message.read_text(encoding="utf-8") if last_message.is_file() else ""
    return {
        "argv_shape": [portable(token) for token in argv],
        "exit_code": process.returncode,
        "stderr_tail": portable(process.stderr.strip())[-400:],
        "text": text,
        "duration_ms": int(elapsed * 1000),
        # Recorded as unobservable rather than as zero: codex exec reports a
        # token total but no spend, and a zero would make the silent host look
        # free.
        "cost_observed": False,
        "cost_usd": None,
        # Codex reports one combined total, not an input/output split. Putting
        # it in input_tokens would make it comparable to a Claude figure that
        # means something narrower.
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": codex_total_tokens(process.stdout),
        "tool_calls": None,
    }


def run_cell(host: str, prompt: str, timeout: int, workdir: Path, cell_id: str) -> dict[str, Any]:
    observation = (run_claude(prompt, timeout) if host == "claude-code"
                   else run_codex(prompt, timeout, workdir, cell_id))
    # A host that exited non-zero or said nothing did not answer badly -- it did
    # not answer. Scoring that as a wrong answer would credit the treatment for
    # a provider outage, and #213 asks specifically that provider failure stay
    # distinguishable from a repository result.
    observation["cell_state"] = (
        "SCORED" if observation["exit_code"] == 0 and observation["text"].strip() else "HOST_ERROR"
    )
    return observation


def host_version(host: str) -> str:
    return subprocess.run(
        HOSTS[host]["version_argv"], capture_output=True, text=True, check=False, timeout=60
    ).stdout.strip()


def build_matrix_receipt(host: str, subject: dict[str, Any], cells: list[dict[str, Any]],
                         reps: int, bindings: dict[str, Any]) -> dict[str, Any]:
    procedure = "procedural-shadow-runtime.matched-arm-trial"
    ran_all_arms = {cell["arm"] for cell in cells} == set(build_arms())
    host_errors = [cell["arm"] for cell in cells if cell.get("cell_state") == "HOST_ERROR"]
    scored = [cell for cell in cells if cell.get("cell_state") != "HOST_ERROR"]
    every_cell_scored = bool(scored) and all(cell["score"]["schema_ok"] for cell in scored)
    # Separation is asked of the arms that actually answered. A host outage is
    # not a treatment difference.
    discriminated = len({
        (cell["score"]["false_pass_rate"], cell["score"]["task_success"], cell["score"]["cited_paths"])
        for cell in scored
    }) > 1

    assertions = [
        {"assertion_id": "every-arm-executed-on-exact-subject", "procedure_id": procedure,
         "result": "PASS" if ran_all_arms else "FAIL"},
        {"assertion_id": "no-cell-failed-for-a-host-reason", "procedure_id": procedure,
         "result": "PASS" if not host_errors else "FAIL"},
        {"assertion_id": "every-cell-returned-a-scorable-packet", "procedure_id": procedure,
         "result": "PASS" if every_cell_scored else "FAIL"},
        # Not a quality claim. If every arm scores identically the evaluator has
        # not been shown to separate anything, and the matrix cannot support a
        # comparison whatever the numbers say.
        {"assertion_id": "evaluator-separated-at-least-two-arms", "procedure_id": procedure,
         "result": "PASS" if discriminated else "FAIL"},
    ]
    passed = all(item["result"] == "PASS" for item in assertions)
    return {
        "schema": "procedural-shadow-runtime-receipt/v1",
        "receipt_id": f"arm-trials-{host}-{subject['current_sha'][:12]}",
        "checkpoint": "BEFORE_PR_OR_PUBLICATION",
        "subject": subject,
        "action": {
            "class": "MATCHED_ARM_TRIAL_MATRIX",
            "side_effecting": False,
            "intent_digest": digest({"task": TASK_QUESTION, "contract": OUTPUT_CONTRACT}),
        },
        "applicable_procedures": [{
            "procedure_id": procedure,
            "criticality": "must",
            "source": {
                "repository": "ed3c/skills-shared",
                "ref": subject["current_sha"],
                "path": "skills/procedural-shadow-runtime/SKILL.md",
                "content_sha256": bindings["skill_digest"],
            },
        }],
        "assertions": assertions,
        "evidence": [{
            "evidence_id": f"arm-cells-{host}",
            "procedure_id": procedure,
            "kind": "COMMAND",
            "artifact_sha256": digest([
                {"arm": cell["arm"], "repetition": cell["repetition"], "score": cell["score"]}
                for cell in cells
            ]),
            "exact_subject": True,
        }],
        "dispositions": [{"procedure_id": procedure, "state": "VERIFIED" if passed else "FAILED"}],
        "close_state": "PASS" if passed else "FAIL",
        "trial_matrix": {
            "host": host,
            "runtime": HOSTS[host]["runtime"],
            "repetitions_per_arm": reps,
            "preregistered_repetitions_per_arm": PREREGISTERED_REPS_PER_ARM,
            "host_error_arms": host_errors,
            # An underpowered run that calls itself the qualifying matrix is how
            # a pilot becomes a finding. The receipt says so in a field a checker
            # can read, not only in prose.
            "qualifies_for_219": reps >= PREREGISTERED_REPS_PER_ARM,
            "bindings": bindings,
            "cells": cells,
        },
    }


def selftest() -> int:
    """Score fixed packets against a real tree; no host, no network, no spend."""
    tree_sha = git("rev-parse", "HEAD^{tree}")
    truth = ground_truth(tree_sha)
    if len(truth) < 2:
        print(f"SELFTEST RED: expected several check_ scripts in the tree, found {truth}", file=sys.stderr)
        return 1

    perfect = score_cell(
        {"answer": truth, "evidence_paths": truth[:1], "non_claims": ["single tree only"], "tree_sha": tree_sha},
        tree_sha, truth,
    )
    if not (perfect["task_success"] and perfect["exact_subject_continuity"]
            and perfect["evidence_packet_complete"] and perfect["false_pass_rate"] == 0.0):
        print(f"SELFTEST RED: a correct packet did not score clean: {perfect}", file=sys.stderr)
        return 1

    fabricating = score_cell(
        {"answer": truth + ["skills/procedural-shadow-runtime/scripts/check_imaginary.py"],
         "evidence_paths": [], "non_claims": ["x"], "tree_sha": tree_sha},
        tree_sha, truth,
    )
    if fabricating["fabricated_paths"] != 1 or fabricating["task_success"]:
        print(f"SELFTEST RED: a fabricated path was not caught: {fabricating}", file=sys.stderr)
        return 1

    # A path that exists on disk but not in the pinned tree must not count as
    # cited evidence; otherwise a dirty checkout silently launders a false pass.
    untracked = ROOT / "arm-trials-selftest-untracked.txt"
    untracked.write_text("scratch\n", encoding="utf-8")
    try:
        dirty = score_cell(
            {"answer": [], "evidence_paths": [untracked.name], "non_claims": ["x"], "tree_sha": tree_sha},
            tree_sha, truth,
        )
    finally:
        untracked.unlink()
    if dirty["fabricated_paths"] != 1:
        print("SELFTEST RED: a path present only in the working tree scored as real", file=sys.stderr)
        return 1

    escaping = score_cell(
        {"answer": ["../../../etc/passwd", "/etc/passwd"], "evidence_paths": [],
         "non_claims": ["x"], "tree_sha": tree_sha},
        tree_sha, truth,
    )
    if escaping["fabricated_paths"] != 2:
        print("SELFTEST RED: paths escaping the repository were treated as real", file=sys.stderr)
        return 1

    stale = score_cell({"answer": truth, "evidence_paths": [], "non_claims": ["x"], "tree_sha": "0" * 40},
                       tree_sha, truth)
    if stale["exact_subject_continuity"]:
        print("SELFTEST RED: a packet bound to another tree claimed continuity", file=sys.stderr)
        return 1

    silent = score_cell({"answer": truth, "evidence_paths": [], "non_claims": [], "tree_sha": tree_sha},
                        tree_sha, truth)
    if silent["evidence_packet_complete"]:
        print("SELFTEST RED: an empty non_claims list scored as a complete packet", file=sys.stderr)
        return 1

    if score_cell(None, tree_sha, truth)["schema_ok"]:
        print("SELFTEST RED: an unparseable response scored as schema-ok", file=sys.stderr)
        return 1

    for stdout, expected in [
        ("codex\nok\ntokens used\n12,198\n", 12198),
        ("tokens used\n7\n", 7),
        ("tokens used\nnot-a-number\n", None),
        ("no total here\n", None),
        ("tokens used", None),
    ]:
        if codex_total_tokens(stdout) != expected:
            print(f"SELFTEST RED: codex_total_tokens({stdout!r}) != {expected}", file=sys.stderr)
            return 1

    for text, expected in [
        ('{"a": 1}', {"a": 1}),
        ('```json\n{"a": 1}\n```', {"a": 1}),
        ('here you go:\n{"a": {"b": 2}}\ndone', {"a": {"b": 2}}),
        ('{"a": "}"}', {"a": "}"}),
        ("no object here", None),
        ("{unbalanced", None),
    ]:
        if extract_json_object(text) != expected:
            print(f"SELFTEST RED: extract_json_object({text!r}) != {expected}", file=sys.stderr)
            return 1

    leaky = f"wrote {ROOT}/out.json from {Path.home()}/x and /var/folders/ab/cd/T/tmpq"
    cleaned = portable(leaky)
    if str(ROOT) in cleaned or str(Path.home()) in cleaned or "/var/folders/" in cleaned:
        print(f"SELFTEST RED: machine paths survived redaction: {cleaned!r}", file=sys.stderr)
        return 1

    full_body = build_arms()["C_FULL_SKILL"]
    try:
        refuse_prompt_in_argv(["claude", "-p", build_prompt(full_body, "0" * 40)], build_prompt(full_body, "0" * 40))
    except RuntimeError:
        pass
    else:
        print("SELFTEST RED: arm text on the command line was not refused", file=sys.stderr)
        return 1
    refuse_prompt_in_argv(["claude", "-p", "--model", "opus"], build_prompt(full_body, "0" * 40))

    arms = sorted(build_arms())
    if arm_order("claude-code", 0, arms) == arm_order("codex-cli", 0, arms):
        print("SELFTEST RED: two hosts received the same arm order", file=sys.stderr)
        return 1
    if sorted(arm_order("claude-code", 0, arms)) != arms:
        print("SELFTEST RED: the shuffle dropped or duplicated an arm", file=sys.stderr)
        return 1

    subject = {"repository": "ed3c/skills-shared", "base_sha": "a" * 40, "current_sha": "a" * 40,
               "runtime": "CLAUDE_CODE_LOCAL", "context_digest": "b" * 64}
    bindings = {"skill_digest": "c" * 64}
    def cell(arm: str, rate: float | None, state: str = "SCORED", success: bool = True) -> dict[str, Any]:
        return {"arm": arm, "repetition": 0, "cell_state": state,
                "score": {"schema_ok": True, "false_pass_rate": rate,
                          "task_success": success, "cited_paths": 5}}

    separated = [cell(arm, rate) for arm, rate in zip(sorted(build_arms()), [0.0, 0.5, 0.0, 0.0, 0.0])]
    if build_matrix_receipt("claude-code", subject, separated, 1, bindings)["close_state"] != "PASS":
        print("SELFTEST RED: a complete separated matrix did not close PASS", file=sys.stderr)
        return 1

    flat = [cell(arm, 0.0) for arm in sorted(build_arms())]
    if build_matrix_receipt("claude-code", subject, flat, 1, bindings)["close_state"] != "FAIL":
        print("SELFTEST RED: a matrix where no arm differed still closed PASS", file=sys.stderr)
        return 1

    # A host outage must fail the matrix on its own assertion, and must not be
    # laundered into a treatment difference by the separation gate.
    with_outage = [cell(arm, 0.0) for arm in sorted(build_arms())[:-1]]
    with_outage.append(cell(sorted(build_arms())[-1], None, state="HOST_ERROR", success=False))
    outage_receipt = build_matrix_receipt("claude-code", subject, with_outage, 1, bindings)
    outage_results = {item["assertion_id"]: item["result"] for item in outage_receipt["assertions"]}
    if outage_results["no-cell-failed-for-a-host-reason"] != "FAIL":
        print("SELFTEST RED: a host outage did not fail its own assertion", file=sys.stderr)
        return 1
    if outage_results["evaluator-separated-at-least-two-arms"] != "FAIL":
        print("SELFTEST RED: a host outage was counted as arm separation", file=sys.stderr)
        return 1
    if outage_receipt["trial_matrix"]["host_error_arms"] != [sorted(build_arms())[-1]]:
        print("SELFTEST RED: the outaged arm was not named in the receipt", file=sys.stderr)
        return 1

    short = build_matrix_receipt("claude-code", subject, separated, 1, bindings)
    full = build_matrix_receipt("claude-code", subject, separated, PREREGISTERED_REPS_PER_ARM, bindings)
    if short["trial_matrix"]["qualifies_for_219"] or not full["trial_matrix"]["qualifies_for_219"]:
        print("SELFTEST RED: the #219 power gate did not track the repetition count", file=sys.stderr)
        return 1

    print(
        f"SELFTEST GREEN: {len(truth)} ground-truth paths resolved from the pinned tree; "
        "fabricated, working-tree-only and repository-escaping paths each score as false passes; "
        "a stale tree_sha, an empty non_claims list and an unparseable response each fail their gate; "
        "arm order differs per host and preserves the arm set; "
        "an undifferentiated matrix and a sub-preregistration n are both refused"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="resolve every binding and print the cell plan without invoking a host")
    parser.add_argument("--host", choices=sorted(HOSTS))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if not args.host or not args.output:
        print("ARM-TRIALS-INVALID: --host and --output are required unless --selftest",
              file=sys.stderr)
        return INVALID

    skill_path = SKILL / "SKILL.md"
    if not skill_path.is_file():
        print(f"ARM-TRIALS-INVALID absent-skill: {skill_path}", file=sys.stderr)
        return INVALID
    if not args.dry_run and shutil.which(HOSTS[args.host]["binary"]) is None:
        print(f"ARM-TRIALS-INVALID absent-binary: {HOSTS[args.host]['binary']}", file=sys.stderr)
        return INVALID

    head = git("rev-parse", "HEAD")
    tree_sha = git("rev-parse", "HEAD^{tree}")
    truth = ground_truth(tree_sha)
    arms = build_arms()

    bindings = {
        "skill_digest": digest(skill_path.read_bytes()),
        "arm_digests": {name: digest(text.encode()) for name, text in sorted(arms.items())},
        "evaluator_digest": digest(Path(__file__).read_bytes()),
        "task_packet_digest": digest({"question": TASK_QUESTION, "contract": OUTPUT_CONTRACT}),
        "ground_truth_digest": digest(truth),
        "host_version": "DRY_RUN" if args.dry_run else host_version(args.host),
        "model": HOSTS[args.host]["model"],
        "policy": HOSTS[args.host]["policy"],
        "tree_sha": tree_sha,
        "timeout_seconds": args.timeout,
        "retries_permitted": 0,
    }
    subject = {
        "repository": "ed3c/skills-shared",
        "base_sha": head,
        "current_sha": head,
        "runtime": HOSTS[args.host]["runtime"],
        "context_digest": digest({"task": TASK_QUESTION, "tree": tree_sha, "skill": bindings["skill_digest"]}),
    }

    args.output.mkdir(parents=True, exist_ok=True)
    cells: list[dict[str, Any]] = []
    for repetition in range(args.repetitions):
        for arm in arm_order(args.host, repetition, sorted(arms)):
            prompt = build_prompt(arms[arm], tree_sha)
            if args.dry_run:
                print(f"PLAN {args.host} rep={repetition} arm={arm} prompt_bytes={len(prompt.encode())}")
                continue
            cell_id = f"{repetition}-{arm}"
            observation = run_cell(args.host, prompt, args.timeout, args.output, cell_id)
            score = score_cell(extract_json_object(observation["text"]), tree_sha, truth)
            cell = {
                "arm": arm,
                "repetition": repetition,
                "cell_state": observation["cell_state"],
                "prompt_digest": digest(prompt.encode()),
                "response_digest": digest(observation["text"].encode()),
                "observation": {k: v for k, v in observation.items() if k != "text"},
                "score": score,
            }
            cells.append(cell)
            (args.output / f"cell-{args.host}-{cell_id}.json").write_text(
                json.dumps({**cell, "response": observation["text"]}, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            if cell["cell_state"] == "HOST_ERROR":
                print(f"CELL {args.host} rep={repetition} {arm:<28} HOST_ERROR "
                      f"exit={observation['exit_code']} {observation['duration_ms']}ms "
                      f"stderr={observation['stderr_tail'][:120]!r}")
                continue
            rate = score["false_pass_rate"]
            print(f"CELL {args.host} rep={repetition} {arm:<28} "
                  f"success={score['task_success']} "
                  f"false_pass={'n/a' if rate is None else rate} "
                  f"cited={score['cited_paths']} {observation['duration_ms']}ms")

    if args.dry_run:
        print(f"DRY-RUN GREEN {args.repetitions * len(arms)} cells planned, "
              f"{len(truth)} ground-truth paths, no host invoked")
        return 0

    receipt = build_matrix_receipt(args.host, subject, cells, args.repetitions, bindings)
    (args.output / f"arm-trials-{args.host}.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    status = "COMPLETE" if receipt["trial_matrix"]["qualifies_for_219"] else "PARTIAL"
    print(f"ARM-TRIALS {status} host={args.host} cells={len(cells)} close={receipt['close_state']}")
    if status == "PARTIAL":
        print(f"  reps={args.repetitions} < preregistered {PREREGISTERED_REPS_PER_ARM}: "
              "mechanism evidence only, not the #219 matrix")
    return 0 if receipt["close_state"] == "PASS" else REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
