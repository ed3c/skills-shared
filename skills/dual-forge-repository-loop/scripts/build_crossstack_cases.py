#!/usr/bin/env python3
"""Generate the #229 held-out case set and take its ground truth from the checker.

Ground truth is never authored here. Each case is one mutation of a known-good
contract, and the label is whatever `check_multi_agent_runtime.py` actually
returns for it. If a mutation does not produce the rule family it was aimed at,
the case is refused rather than relabelled -- a case whose answer was adjusted to
match the generator is a case that measures the generator.

The rule families are deliberately disjoint from the #225 set. Reusing those
would measure recall of a committed case file rather than judgement about
contracts.

Usage:
  build_crossstack_cases.py --out evals/prompt-crossstack-cases.json
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parent.parent
BASELINE = SKILL / "evals" / "prompt-baseline-cases.json"
CHECKER = SKILL / "scripts" / "check_multi_agent_runtime.py"

CASE_SET_ID = "v2-1-crossstack-heldout-cases-2026-08"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(body: Any) -> str:
    return sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode())


def base_contract() -> dict[str, Any]:
    cases = json.loads(BASELINE.read_text(encoding="utf-8"))["cases"]
    positive = next(c for c in cases if c["case_id"] == "positive")
    return copy.deepcopy(positive["contract"])


# Each mutation names the rule family it targets. The target is an expectation
# about the checker, and the checker gets the last word.
def mutate_unknown_runtime(contract: dict[str, Any]) -> None:
    contract["runtime"]["identity"] = "UNKNOWN"


def mutate_self_dependency(contract: dict[str, Any]) -> None:
    task = contract["tasks"][0]
    task["dependencies"] = [task["task_id"]]


def mutate_shadow_overclaim(contract: dict[str, Any]) -> None:
    # An L3 checkpoint outcome with the enforcement state left at anything but
    # PASS: the Shadow says stop and nothing enforced it.
    contract["shadow"]["checkpoint_outcome"] = "BLOCKED_AT_MATERIAL_BOUNDARY_L3"
    contract["shadow"]["enforcement_state"] = "NOT_EXERCISED"


def mutate_parallelism_admission(contract: dict[str, Any]) -> None:
    contract["admission"]["disjoint_path_and_resource_leases"] = False


def mutate_subject_base(contract: dict[str, Any]) -> None:
    contract["repository"]["base_sha"] = "1" * 40



def mutate_cardinality(contract: dict[str, Any]) -> None:
    contract["topology"] = "SINGLE_BUILDER"


MUTATIONS: list[tuple[str, str, Any]] = [
    ("unknown-runtime-published", "unknown-runtime", mutate_unknown_runtime),
    ("self-dependency", "self-dependency", mutate_self_dependency),
    ("shadow-l3-unenforced", "shadow-l3-unenforced", mutate_shadow_overclaim),
    ("subject-base-not-admitted", "unadmitted-base", mutate_subject_base),
    ("parallelism-not-admitted", "parallelism-not-admitted", mutate_parallelism_admission),
    ("single-builder-cardinality", "topology-cardinality", mutate_cardinality),
]


def run_checker(contract: dict[str, Any]) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(contract, handle)
        path = Path(handle.name)
    try:
        result = subprocess.run([sys.executable, str(CHECKER), str(path)],
                                capture_output=True, text=True, check=False)
        return result.returncode, (result.stdout + result.stderr)
    finally:
        path.unlink(missing_ok=True)


def rule_from_output(output: str, target: str) -> str | None:
    """Return the checker's own marker, not the target the generator aimed at.

    The target only decides whether the mutation hit; the label is whatever the
    checker printed. Storing the target instead would let a vague aim ("budget")
    become the answer a model is scored against, when the checker actually said
    something specific.
    """
    for line in output.splitlines():
        if target not in line:
            continue
        for token in re.findall(r"\b[a-z][a-z0-9]*(?:-[a-z0-9]+)+\b", line):
            if target in token:
                return token
        return target
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    base = base_contract()
    positive_exit, positive_output = run_checker(base)
    if positive_exit != 0:
        print(f"the known-good base does not pass the checker (exit {positive_exit}); "
              f"every derived case would be measuring that instead:\n{positive_output}",
              file=sys.stderr)
        return 2

    cases: list[dict[str, Any]] = [{
        "case_id": "heldout-positive",
        "contract": base,
        "ground_truth": {"checker_exit_code": 0, "verdict": "ADMIT",
                         "violated_rule": None},
        "case_digest": digest(base),
    }]

    refused = []
    for target, case_id, mutation in MUTATIONS:
        contract = copy.deepcopy(base)
        mutation(contract)
        exit_code, output = run_checker(contract)
        if exit_code == 0:
            refused.append(f"{case_id}: mutation aimed at {target} still passes")
            continue
        found = rule_from_output(output, target)
        if found is None:
            refused.append(f"{case_id}: checker refused but not for {target}; got "
                           f"{output.strip().splitlines()[:1]}")
            continue
        cases.append({
            "case_id": case_id,
            "contract": contract,
            "ground_truth": {"checker_exit_code": exit_code, "verdict": "REFUSE",
                             "violated_rule": target},
            "case_digest": digest(contract),
        })

    if refused:
        print("cases refused rather than relabelled:", file=sys.stderr)
        for line in refused:
            print(f"  {line}", file=sys.stderr)

    if len(cases) < 6:
        print(f"only {len(cases)} usable cases; #229 requires at least six held-out "
              f"cases and a short set is not one that can be topped up by loosening "
              f"a label", file=sys.stderr)
        return 2

    body = {
        "schema": "v2-1-crossstack-cases/v1",
        "case_set_id": CASE_SET_ID,
        "case_count": len(cases),
        "cases": cases,
        "checker": "skills/dual-forge-repository-loop/scripts/check_multi_agent_runtime.py",
        "checker_sha256": sha256(CHECKER.read_bytes()),
        "ground_truth_authority": "DETERMINISTIC_CHECKER",
        "_meta": {
            "held_out_policy": (
                "These contracts did not exist in any committed file before this run. "
                "They are derived from the #225 positive contract, whose shape is public, "
                "by one mutation each -- the shape is not the answer, the defect is. Every "
                "rule family here is disjoint from the #225 set, so a model that memorised "
                "that file gains nothing. Once committed they stop being held out, and a "
                "later run needs a new set."),
            "why_the_checker_labels": (
                "The generator states which family each mutation targets and the checker "
                "decides whether it hit. A mutation that misses is dropped, never "
                "relabelled to whatever it happened to trigger."),
            "agent_never_sees": "checker output, exit codes, or violated-rule markers",
        },
    }
    body["set_digest"] = digest(body["cases"])

    args.out.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"out": str(args.out), "cases": len(cases),
                      "set_digest": body["set_digest"][:12],
                      "families": [c["ground_truth"]["violated_rule"] for c in cases]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
