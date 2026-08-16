#!/usr/bin/env python3
"""Execute the frozen #225 prompt baseline: three arms, five repetitions, one runtime.

Exit codes:
  0   every cell completed and was scored
  2   at least one cell failed; failures stay in the denominator with a reason
  64  the preregistration, case set, prompt blob, or host binary is absent

Each cell is a fresh session in an empty workspace, judging the same six frozen
contract documents. The only thing that differs between arms is which prompt bytes
are carried. Ground truth comes from the repository's own checker, so the agent's
self-report is never the verifier.

There are no retries: the preregistration forbids them, so a failed cell is
reported rather than repeated.
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

ROOT = Path(__file__).resolve().parents[3]
SKILL = Path(__file__).resolve().parents[1]
PREREG = SKILL / "evals" / "prompt-baseline-preregistration.json"
CASES = SKILL / "evals" / "prompt-baseline-cases.json"

INVALID = 64
CELL_FAILURE = 2

OUTPUT_SHAPE = (
    'Write your answers to agent-output.json in the current working directory with '
    'exactly this shape: {"judgements": [{"case_id": "<id>", "verdict": "ADMIT" or '
    '"REFUSE", "violated_rule": "<short rule name, or null when you admit>"}]}'
)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def portable(text: str) -> str:
    text = text.replace(str(Path.home()), "<HOME>")
    return re.sub(r"/(?:private/)?(?:var/folders|tmp)/[A-Za-z0-9._/+-]*", "<TMPDIR>", text)


def git_show(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
        capture_output=True, check=True,
    ).stdout


def arm_prompt(arm: dict[str, Any], prompt_path: str) -> bytes:
    if arm["arm"] == "NO_PROMPT":
        return b""
    return git_show(arm["prompt_commit"], prompt_path)


def build_task(cases: list[dict[str, Any]]) -> str:
    documents = "\n\n".join(
        f"----- case {case['case_id']} -----\n{json.dumps(case['contract'], indent=2, sort_keys=True)}"
        for case in cases
    )
    return (
        "You are reviewing repository-multi-agent-runtime/v1 contract documents.\n"
        "For each case below, decide whether the contract should be ADMITTED or REFUSED, "
        "and when refusing, name the single rule it violates in a few words.\n\n"
        f"{documents}\n\n{OUTPUT_SHAPE}\n"
        "Judge every case. Do not run any checker; decide from the documents themselves."
    )


def run_cell(model: str, prompt_bytes: bytes, task: str, workspace: Path,
             timeout: int) -> dict[str, Any]:
    argv = ["claude", "-p", task, "--allowedTools", "Write,Read", "--model", model,
            "--output-format", "json"]
    prompt_file = None
    if prompt_bytes:
        prompt_file = workspace / ".arm-prompt.md"
        prompt_file.write_bytes(prompt_bytes)
        argv += ["--append-system-prompt-file", str(prompt_file)]
    started = time.time()
    process = subprocess.run(
        argv, cwd=workspace, capture_output=True, text=True, check=False,
        timeout=timeout, stdin=subprocess.DEVNULL,
    )
    duration_ms = int((time.time() - started) * 1000)
    if prompt_file is not None:
        prompt_file.unlink()  # keep it out of the workspace manifest
    usage: dict[str, Any] = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
                             "duration_ms": duration_ms, "turns": 0}
    try:
        payload = json.loads(process.stdout)
        u = payload.get("usage", {})
        usage.update({
            "input_tokens": int(u.get("input_tokens", 0)) + int(u.get("cache_read_input_tokens", 0)),
            "output_tokens": int(u.get("output_tokens", 0)),
            "cost_usd": float(payload.get("total_cost_usd", 0.0)),
            "turns": int(payload.get("num_turns", 0)),
        })
    except Exception:
        pass
    return {"exit_code": process.returncode, "usage": usage,
            "stderr": portable(process.stderr)[-1500:]}


def score(workspace: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    truth = {c["case_id"]: c["ground_truth"] for c in cases}
    try:
        output = json.loads((workspace / "agent-output.json").read_text(encoding="utf-8"))
        judgements = output.get("judgements")
        parsed = isinstance(judgements, list)
    except Exception:
        judgements, parsed = None, False
    if not parsed:
        return {"parsed": False, "answered": 0, "verdict_correct": 0, "rule_correct": 0,
                "total": len(cases)}

    seen: dict[str, dict[str, Any]] = {}
    for item in judgements:
        if isinstance(item, dict) and isinstance(item.get("case_id"), str):
            seen.setdefault(item["case_id"], item)

    verdict_correct = 0
    rule_correct = 0
    for case_id, expected in truth.items():
        got = seen.get(case_id)
        if not got:
            continue
        if str(got.get("verdict", "")).upper() == expected["verdict"]:
            verdict_correct += 1
            if expected["verdict"] == "REFUSE" and expected["violated_rule"]:
                # Loose match on purpose: the agent is asked for a short rule name,
                # not for the checker's internal marker string.
                stated = str(got.get("violated_rule") or "").lower().replace("_", "-")
                tokens = [t for t in expected["violated_rule"].split("-") if len(t) > 3]
                if tokens and sum(t in stated for t in tokens) >= max(1, len(tokens) // 2):
                    rule_correct += 1
    return {"parsed": True, "answered": len(seen), "verdict_correct": verdict_correct,
            "rule_correct": rule_correct, "total": len(cases)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=0, help="override for smoke use only")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    for required in (PREREG, CASES):
        if not required.is_file():
            print(f"BASELINE-INVALID absent-input: {required}", file=sys.stderr)
            return INVALID
    if shutil.which("claude") is None:
        print("BASELINE-INVALID absent-binary: claude", file=sys.stderr)
        return INVALID

    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    case_set = json.loads(CASES.read_text(encoding="utf-8"))
    cases = case_set["cases"]
    if case_set["set_digest"][:12] != prereg["case_set"]["set_digest"]:
        print("BASELINE-INVALID case-set-drift: frozen digest does not match the case file",
              file=sys.stderr)
        return INVALID

    model = prereg["runtime"]["model"]
    prompt_path = prereg["subject"]["prompt_path"]
    repetitions = args.repetitions or prereg["design"]["repetitions_per_arm"]
    task = build_task(cases)

    args.output.mkdir(parents=True, exist_ok=True)
    cells: list[dict[str, Any]] = []
    failures = 0
    total = len(prereg["arms"]) * repetitions
    index = 0

    for repetition in range(1, repetitions + 1):
        # Arm order derived from the cell identity, per the frozen design.
        ordered = sorted(
            prereg["arms"],
            key=lambda a: hashlib.sha256(f"{a['arm']}|{repetition}".encode()).hexdigest(),
        )
        for arm in ordered:
            index += 1
            cell_id = f"{arm['arm']}__rep{repetition}"
            workspace = args.output / "cells" / cell_id
            if workspace.exists():
                shutil.rmtree(workspace)
            workspace.mkdir(parents=True)

            prompt_bytes = arm_prompt(arm, prompt_path)
            if arm["arm"] != "NO_PROMPT":
                expected = arm.get("prompt_sha256", "")
                actual = sha256_bytes(prompt_bytes)
                if not actual.startswith(expected.rstrip("…")[:12]):
                    print(f"BASELINE-INVALID prompt-drift for {arm['arm']}: {actual[:12]}",
                          file=sys.stderr)
                    return INVALID

            result = run_cell(model, prompt_bytes, task, workspace, args.timeout)
            scored = score(workspace, cases)
            ok = result["exit_code"] == 0 and scored["parsed"]
            if not ok:
                failures += 1
            cells.append({
                "cell_id": cell_id,
                "arm": arm["arm"],
                "repetition": repetition,
                "arm_order_index": index,
                "prompt_sha256": sha256_bytes(prompt_bytes) if prompt_bytes else None,
                "prompt_bytes": len(prompt_bytes),
                "exit_code": result["exit_code"],
                "scored": ok,
                "failure_reason": None if ok else (result["stderr"][-200:] or "no parsable output"),
                "metrics": scored,
                "usage": result["usage"],
            })
            print(f"cell {index}/{total} {cell_id} scored={ok} "
                  f"verdict={scored['verdict_correct']}/{scored['total']} "
                  f"rule={scored['rule_correct']}")

    report = {
        "schema": "v2-1-prompt-baseline-result/v1",
        "preregistration_id": prereg["preregistration_id"],
        "runtime": prereg["runtime"]["identity"],
        "model": model,
        "case_set_id": case_set["case_set_id"],
        "cells": cells,
        "cell_count": len(cells),
        "failed_cells": failures,
        "known_confounds": prereg["known_confounds"],
        "declared_non_claims": prereg["declared_non_claims"],
    }
    (args.output / "baseline-result.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"BASELINE COMPLETE cells={len(cells)} failed={failures}")
    return 0 if failures == 0 else CELL_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
