#!/usr/bin/env python3
"""Run the #229 held-out evaluation across two real Agent stacks.

#225 measured one stack and found the candidate ineligible. One stack cannot say
whether that is a property of the prompt or of the harness, which is what this
run is for: the same frozen cases, the same three arms, on Claude Code and Codex
CLI.

The two stacks do not carry a prompt the same way, and that is not fixable here.
Claude Code takes the bytes through a system-prompt channel; Codex CLI has no
such channel and takes them as instruction text. Any cross-stack difference is
therefore confounded with carrier, and the receipt says so rather than reporting
a clean stack comparison.

Ground truth comes from `check_multi_agent_runtime.py` and is computed by
`build_crossstack_cases.py`, never by the model under test, which never sees a
checker verdict.

Usage:
  run_prompt_crossstack.py --preregistration P --cases C --output DIR
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parent.parent
SCHEMA = "v2-1-crossstack-result/v1"
INVALID = 64

OUTPUT_SHAPE = """
Write your answer to agent-output.json in the working directory, shaped exactly:

{"judgements": [{"case_id": "...", "verdict": "ADMIT|REFUSE", "violated_rule": "..."}]}

Use violated_rule only when the verdict is REFUSE; a few words naming the single
rule broken. Write the file and stop.
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def portable(text: str) -> str:
    text = text.replace(str(Path.home()), "<HOME>")
    return re.sub(r"/(?:private/)?(?:var/folders|tmp)/[A-Za-z0-9._/+-]*", "<TMPDIR>", text)


def git_show(commit: str, path: str) -> bytes:
    result = subprocess.run(["git", "-C", str(SKILL.parents[1]), "show", f"{commit}:{path}"],
                            capture_output=True, check=True)
    return result.stdout


def build_task(cases: list[dict[str, Any]]) -> str:
    documents = "\n\n".join(
        f"----- case {case['case_id']} -----\n"
        f"{json.dumps(case['contract'], indent=2, sort_keys=True)}"
        for case in cases)
    return (
        "You are reviewing repository-multi-agent-runtime/v1 contract documents.\n"
        "For each case below, decide whether the contract should be ADMITTED or REFUSED, "
        "and when refusing, name the single rule it violates in a few words.\n\n"
        f"{documents}\n\n{OUTPUT_SHAPE}\n"
        "Judge every case. Do not run any checker; decide from the documents themselves."
    )


def arm_prompt(arm: dict[str, Any], prompt_path: str) -> bytes:
    if arm["arm"] == "NO_PROMPT":
        return b""
    return git_show(arm["prompt_commit"], prompt_path)


def run_claude(model: str, prompt_bytes: bytes, task: str, workspace: Path,
               timeout: int) -> dict[str, Any]:
    argv = ["claude", "-p", task, "--allowedTools", "Write,Read", "--model", model,
            "--output-format", "json"]
    prompt_file = None
    if prompt_bytes:
        prompt_file = workspace / ".arm-prompt.md"
        prompt_file.write_bytes(prompt_bytes)
        argv += ["--append-system-prompt-file", str(prompt_file)]
    started = time.time()
    process = subprocess.run(argv, cwd=workspace, capture_output=True, text=True,
                             check=False, timeout=timeout, stdin=subprocess.DEVNULL)
    duration = int((time.time() - started) * 1000)
    if prompt_file is not None:
        prompt_file.unlink()
    usage = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
             "cost_observed": False, "duration_ms": duration, "turns": 0}
    try:
        payload = json.loads(process.stdout)
        counts = payload.get("usage", {})
        usage.update({
            "input_tokens": int(counts.get("input_tokens", 0))
            + int(counts.get("cache_read_input_tokens", 0)),
            "output_tokens": int(counts.get("output_tokens", 0)),
            "cost_usd": float(payload.get("total_cost_usd", 0.0)),
            "cost_observed": "total_cost_usd" in payload,
            "turns": int(payload.get("num_turns", 0)),
        })
    except Exception:
        pass
    return {"exit_code": process.returncode, "usage": usage,
            "stderr": portable(process.stderr)[-1500:]}


def run_codex(model: str, prompt_bytes: bytes, task: str, workspace: Path,
              timeout: int) -> dict[str, Any]:
    """Codex has no system-prompt channel, so the bytes go in front of the task.

    That difference is the carrier confound this receipt declares. Pretending the
    two hosts received the prompt identically would be the cleaner-looking lie.
    """
    if prompt_bytes:
        instruction = (prompt_bytes.decode("utf-8", errors="replace")
                       + "\n\n---\n\n" + task)
    else:
        instruction = task
    argv = ["codex", "exec", "-m", model, "--sandbox", "workspace-write",
            "--skip-git-repo-check", "-C", str(workspace), instruction]
    started = time.time()
    process = subprocess.run(argv, cwd=workspace, capture_output=True, text=True,
                             check=False, timeout=timeout, stdin=subprocess.DEVNULL)
    duration = int((time.time() - started) * 1000)
    tokens = 0
    matched = re.search(r"tokens used\s*\n?\s*([\d,]+)", process.stdout)
    if matched:
        tokens = int(matched.group(1).replace(",", ""))
    return {"exit_code": process.returncode,
            "usage": {"input_tokens": 0, "output_tokens": tokens, "cost_usd": 0.0,
                      "cost_observed": False, "duration_ms": duration, "turns": 0},
            "stderr": portable(process.stderr)[-1500:]}


RUNNERS = {"claude-code": run_claude, "codex-cli": run_codex}


def score(workspace: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    truth = {c["case_id"]: c["ground_truth"] for c in cases}
    try:
        output = json.loads((workspace / "agent-output.json").read_text(encoding="utf-8"))
        judgements = output.get("judgements")
        parsed = isinstance(judgements, list)
    except Exception:
        judgements, parsed = None, False
    if not parsed:
        return {"parsed": False, "answered": 0, "verdict_correct": 0,
                "rule_correct": 0, "total": len(cases)}

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
                stated = str(got.get("violated_rule") or "").lower().replace("_", "-")
                tokens = [t for t in expected["violated_rule"].split("-") if len(t) > 3]
                if tokens and sum(t in stated for t in tokens) >= max(1, len(tokens) // 2):
                    rule_correct += 1
    return {"parsed": True, "answered": len(seen), "verdict_correct": verdict_correct,
            "rule_correct": rule_correct, "total": len(cases)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    case_set = json.loads(args.cases.read_text(encoding="utf-8"))
    cases = case_set["cases"]

    if not case_set["set_digest"].startswith(prereg["case_set"]["set_digest"]):
        print("CROSSSTACK-INVALID case-set-drift: frozen digest does not match the file",
              file=sys.stderr)
        return INVALID
    for stack in prereg["stacks"]:
        if shutil.which(stack["binary"]) is None:
            print(f"CROSSSTACK-INVALID absent-binary: {stack['binary']}", file=sys.stderr)
            return INVALID

    prompt_path = prereg["subject"]["prompt_path"]
    repetitions = args.repetitions or prereg["design"]["repetitions_per_arm"]
    task = build_task(cases)
    args.output.mkdir(parents=True, exist_ok=True)

    cells: list[dict[str, Any]] = []
    failures = 0
    index = 0
    for stack in prereg["stacks"]:
        runner = RUNNERS[stack["harness"]]
        for repetition in range(1, repetitions + 1):
            ordered = sorted(prereg["arms"], key=lambda a: hashlib.sha256(
                f"{stack['stack_id']}|{a['arm']}|{repetition}".encode()).hexdigest())
            for arm in ordered:
                index += 1
                cell_id = f"{stack['stack_id']}__{arm['arm']}__rep{repetition}"
                workspace = args.output / "cells" / cell_id
                if workspace.exists():
                    shutil.rmtree(workspace)
                workspace.mkdir(parents=True)

                prompt_bytes = arm_prompt(arm, prompt_path)
                if arm["arm"] != "NO_PROMPT":
                    expected = arm.get("prompt_sha256", "")
                    actual = sha256(prompt_bytes)
                    if not actual.startswith(expected.rstrip("…")[:12]):
                        print(f"CROSSSTACK-INVALID prompt-drift {arm['arm']}: "
                              f"{actual[:12]}", file=sys.stderr)
                        return INVALID

                result = runner(stack["model"], prompt_bytes, task, workspace,
                                args.timeout)
                scored = score(workspace, cases)
                ok = result["exit_code"] == 0 and scored["parsed"]
                if not ok:
                    failures += 1
                cells.append({
                    "cell_id": cell_id,
                    "stack_id": stack["stack_id"],
                    "harness": stack["harness"],
                    "model": stack["model"],
                    "arm": arm["arm"],
                    "repetition": repetition,
                    "arm_order_index": index,
                    "prompt_bytes": len(prompt_bytes),
                    "prompt_sha256": sha256(prompt_bytes) if prompt_bytes else None,
                    "exit_code": result["exit_code"],
                    "scored": ok,
                    "failure_reason": None if ok else (
                        "nonzero-exit" if result["exit_code"] != 0 else "unparsed-output"),
                    "metrics": scored,
                    "usage": result["usage"],
                })
                print(f"  {cell_id:52} verdict={scored['verdict_correct']}/"
                      f"{scored['total']} rule={scored['rule_correct']} "
                      f"{'' if ok else result['stderr'][-120:]}", file=sys.stderr)

    by_stack_arm: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for cell in cells:
        by_stack_arm.setdefault((cell["stack_id"], cell["arm"]), []).append(cell)

    def mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    summary = {}
    for (stack_id, arm), group in sorted(by_stack_arm.items()):
        summary.setdefault(stack_id, {})[arm] = {
            "n": len(group),
            "verdict_accuracy": mean([c["metrics"]["verdict_correct"] for c in group]),
            "rule_accuracy": mean([c["metrics"]["rule_correct"] for c in group]),
            "scored_cells": sum(1 for c in group if c["scored"]),
        }

    receipt = {
        "schema": SCHEMA,
        "issue": 229,
        "preregistration_id": prereg["preregistration_id"],
        "case_set_id": case_set["case_set_id"],
        "case_count": len(cases),
        "cell_count": len(cells),
        "failed_cells": failures,
        "cells": cells,
        "per_stack": summary,
        "known_confounds": prereg["known_confounds"],
        "declared_non_claims": prereg["declared_non_claims"],
    }
    target = args.output / "crossstack-result.json"
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({"result": str(target), "cells": len(cells),
                      "failed": failures, "per_stack": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
