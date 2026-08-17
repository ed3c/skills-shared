#!/usr/bin/env python3
"""Generate a #229 held-out case set and take its ground truth from the checker.

Ground truth is never authored here. Each case is one mutation of a known-good
contract, and the label is whatever `check_multi_agent_runtime.py` actually
returns for it. If a mutation does not produce the rule family it was aimed at,
the case is refused rather than relabelled -- a case whose answer was adjusted to
match the generator is a case that measures the generator.

The rule families are deliberately disjoint from the #225 set. Reusing those
would measure recall of a committed case file rather than judgement about
contracts.

Two generations exist, and both are buildable so both stay replayable.

  --generation 1  reproduces the case set the 2026-08 cross-stack run executed.
                  Its metric was later shown to be unusable: every arm judged
                  every case correctly (a ceiling), and the only score
                  separation came from token overlap with the checker's own
                  marker vocabulary, which the 36KB candidate prompt carries and
                  the 4.6KB baseline does not.

  --generation 2  is the repair. Every refusal family gains a near-miss sibling
                  the checker admits, so no constant verdict can score well and
                  "this field was touched" stops being a winning heuristic; and
                  every refusal case carries a paraphrase rubric with executed
                  accept/reject examples, so a correct answer in the model's own
                  words scores and a bare marker echo does not.

Generation 2 refuses to emit a set that fails its own design gates: a set a
constant answer could win, a near-miss with no refusal sibling in its field
family, or a rubric whose declared examples it cannot separate.

Usage:
  build_crossstack_cases.py --generation 2 --out evals/prompt-crossstack-v2-cases.json
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

from crossstack_rubric import validate_rubric

SKILL = Path(__file__).resolve().parent.parent
BASELINE = SKILL / "evals" / "prompt-baseline-cases.json"
CHECKER = SKILL / "scripts" / "check_multi_agent_runtime.py"

CASE_SET_IDS = {
    1: "v2-1-crossstack-heldout-cases-2026-08",
    2: "v2-1-crossstack-heldout-cases-gen2-2026-08",
}


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


def mutate_shadow_overclaim_only(contract: dict[str, Any]) -> None:
    """Generation 2: the same defect without dragging `shadow-l3-bypassed` along.

    Generation 1 left delivery unblocked as well, so the contract broke two rules
    and a model naming the other one scored zero for being right about a
    different true thing.
    """
    mutate_shadow_overclaim(contract)
    contract["states"]["delivery_state"] = "BLOCKED"


def mutate_parallelism_admission(contract: dict[str, Any]) -> None:
    contract["admission"]["disjoint_path_and_resource_leases"] = False


def mutate_subject_base(contract: dict[str, Any]) -> None:
    contract["repository"]["base_sha"] = "1" * 40


def mutate_cardinality(contract: dict[str, Any]) -> None:
    contract["topology"] = "SINGLE_BUILDER"


GEN1_MUTATIONS: list[tuple[str, str, Any]] = [
    ("unknown-runtime-published", "unknown-runtime", mutate_unknown_runtime),
    ("self-dependency", "self-dependency", mutate_self_dependency),
    ("shadow-l3-unenforced", "shadow-l3-unenforced", mutate_shadow_overclaim),
    ("subject-base-not-admitted", "unadmitted-base", mutate_subject_base),
    ("parallelism-not-admitted", "parallelism-not-admitted", mutate_parallelism_admission),
    ("single-builder-cardinality", "topology-cardinality", mutate_cardinality),
]


# ---------------------------------------------------------------------------
# Generation 2: near misses.
#
# A near miss touches the same region of the contract as a refusal case and is
# still admitted. Without them the set is answerable by "something in this field
# changed, so refuse", which is what a ceiling of 6/6 in every arm looks like
# from the inside.
def collapse_to_single_builder(contract: dict[str, Any]) -> None:
    """One logical slice, with the budget and worker ledgers kept consistent."""
    contract["topology"] = "SINGLE_BUILDER"
    contract["tasks"] = contract["tasks"][:1]
    contract["results"] = contract["results"][:1]
    contract["budget"]["consumed"].update(contract["results"][0]["budget_consumed"])
    contract["budget"]["consumed"]["active_workers"] = 1
    contract["budget"]["consumed"]["total_workers"] = 1


def near_unknown_runtime_blocked(contract: dict[str, Any]) -> None:
    contract["runtime"]["identity"] = "UNKNOWN"
    contract["states"]["delivery_state"] = "BLOCKED"


def near_cross_task_dependency(contract: dict[str, Any]) -> None:
    contract["tasks"][0]["dependencies"] = [contract["tasks"][1]["task_id"]]


def near_shadow_l3_enforced(contract: dict[str, Any]) -> None:
    contract["shadow"]["checkpoint_outcome"] = "BLOCKED_AT_MATERIAL_BOUNDARY_L3"
    contract["shadow"]["enforcement_state"] = "PASS"
    contract["states"]["delivery_state"] = "BLOCKED"


def near_base_moved_within_admitted(contract: dict[str, Any]) -> None:
    contract["repository"]["base_sha"] = contract["repository"]["admitted_subjects"][1]


def near_admission_false_single_builder(contract: dict[str, Any]) -> None:
    collapse_to_single_builder(contract)
    contract["admission"]["disjoint_path_and_resource_leases"] = False


FIELD_FAMILIES = {
    "unknown-runtime-published": "runtime-identity",
    "self-dependency": "task-dependencies",
    "shadow-l3-unenforced": "shadow-enforcement",
    "subject-base-not-admitted": "repository-subjects",
    "parallelism-not-admitted": "parallelism-admission",
    "single-builder-cardinality": "topology-cardinality",
}

GEN2_MUTATIONS: list[tuple[str, str, Any]] = [
    ("unknown-runtime-published", "unknown-runtime", mutate_unknown_runtime),
    ("self-dependency", "self-dependency", mutate_self_dependency),
    ("shadow-l3-unenforced", "shadow-l3-unenforced", mutate_shadow_overclaim_only),
    ("subject-base-not-admitted", "unadmitted-base", mutate_subject_base),
    ("parallelism-not-admitted", "parallelism-not-admitted", mutate_parallelism_admission),
    ("single-builder-cardinality", "topology-cardinality", mutate_cardinality),
]

# (case_id, field_family, why_it_looks_wrong, mutation)
GEN2_NEAR_MISSES: list[tuple[str, str, str, Any]] = [
    ("nearmiss-unknown-runtime-blocked", "runtime-identity",
     "The runtime really is UNKNOWN. UNKNOWN is only fatal once the contract also "
     "claims a publication state; failing closed into BLOCKED delivery is exactly "
     "where an unclassified runtime is supposed to end up.",
     near_unknown_runtime_blocked),
    ("nearmiss-cross-task-dependency", "task-dependencies",
     "A dependency edge appears where the refusal case has one. This edge points at "
     "the sibling slice, not at itself, and an ordered pair of slices is the shape "
     "dependency-ordered handoff is made of.",
     near_cross_task_dependency),
    ("nearmiss-shadow-l3-enforced", "shadow-enforcement",
     "The Shadow blocked at the material boundary, which reads as alarming. It was "
     "enforced and delivery is BLOCKED, so this is the compliant L3 shape rather "
     "than an overclaim.",
     near_shadow_l3_enforced),
    ("nearmiss-base-moved-within-admitted", "repository-subjects",
     "The base subject moved, which is the same edit the refusal case makes. It "
     "moved to another sha that is already in admitted_subjects.",
     near_base_moved_within_admitted),
    ("nearmiss-admission-false-single-builder", "parallelism-admission",
     "A parallelism admission gate is false, exactly as in the refusal case. The "
     "contract is SINGLE_BUILDER, and admission gates bind fan-out; a lone builder "
     "is not running in parallel for them to bind.",
     near_admission_false_single_builder),
    ("nearmiss-single-builder-one-task", "topology-cardinality",
     "The topology is SINGLE_BUILDER, the same declaration the refusal case carries. "
     "Here it carries exactly one logical slice, which is what SINGLE_BUILDER means.",
     collapse_to_single_builder),
]

# Rubrics score the rule a model named, in whatever words it used. Each accept
# path is a conjunction of concept groups; an answer scores when one path is
# fully matched. The examples are executed at build time, not decoration.
GEN2_RUBRICS: dict[str, dict[str, Any]] = {
    "unknown-runtime-published": {
        "accept_any": [[
            ["runtime", "host", "execution environment", "environment", "platform",
             "harness"],
            ["unknown", "unclassified", "unidentified", "undetermined", "unresolved",
             "not classified", "never classified", "cannot be classified", "unbound"],
            ["publish", "commit", "pull request", "merge", "delivery", "deliver",
             "pushed", "push", "release"],
        ]],
        "examples": {
            "accept": [
                "the execution environment was never classified yet the change already "
                "reached a pull request",
                "unknown runtime published",
                "the host is unidentified but the work is already committed",
            ],
            "reject": [
                "runtime",
                "the runtime identity is recorded and the delivery state is a pull request",
            ],
        },
    },
    "self-dependency": {
        "accept_any": [[
            ["task", "slice", "worker", "node", "step", "item", "unit"],
            ["itself", "its own", "self", "circular", "cycle", "cyclic", "loops back",
             "own identifier", "same task"],
            ["depend", "prerequisite", "predecessor", "blocked by", "waits on",
             "wait on", "ordering", "requires", "upstream"],
        ]],
        "examples": {
            "accept": [
                "a slice waits on itself",
                "self-dependency: the task lists itself as a prerequisite",
                "the worker declares its own identifier as a predecessor",
                "dependency cycle at worker-a",
            ],
            "reject": [
                "dependency",
                "the task depends on another slice",
            ],
        },
    },
    "shadow-l3-unenforced": {
        "accept_any": [[
            ["shadow", "reviewer", "overseer", "supervisor", "independent check",
             "second checker", "guard", "l3"],
            ["block", "stop", "halt", "refus", "material boundary", "escalat"],
            ["unenforced", "not enforced", "no enforcement", "never enforced",
             "nothing enforced", "not exercised", "never exercised", "ignored",
             "without enforcement", "enforcement missing"],
        ]],
        "examples": {
            "accept": [
                "the overseer halted at the material boundary and nothing enforced it",
                "shadow blocked at l3 but the enforcement state was never exercised",
                "the independent check stopped the run yet no enforcement followed",
            ],
            "reject": [
                "shadow",
                "the shadow reviewed the change and passed",
            ],
        },
    },
    "subject-base-not-admitted": {
        "accept_any": [[
            ["base", "starting commit", "parent commit", "start point", "origin commit",
             "branched from", "started from", "from which"],
            ["admitted", "allowed", "permitted", "approved", "authoris", "authoriz",
             "declared subjects", "known subjects", "accepted list", "sanctioned"],
            ["not", "outside", "absent", "missing", "unlisted", "never", "no", "none",
             "without", "excluded", "foreign"],
        ]],
        "examples": {
            "accept": [
                "the starting commit lies outside the approved list of shas",
                "the base sha is not among the admitted subjects",
                "work started from a commit that was never sanctioned",
            ],
            "reject": [
                "admitted",
                "the base sha is listed among the admitted subjects",
            ],
        },
    },
    "parallelism-not-admitted": {
        "accept_any": [[
            ["parallel", "concurren", "fan out", "fanout", "multi worker",
             "multiple workers", "several workers", "two workers", "simultaneous"],
            ["admit", "admission", "gate", "precondition", "criteri", "requirement",
             "authoris", "authoriz", "approved", "eligib", "entry condition"],
            ["not", "false", "unmet", "fail", "missing", "without", "absent", "denied",
             "never", "no", "none", "violat"],
        ]],
        "examples": {
            "accept": [
                "concurrent work was allowed although its entry conditions are unmet",
                "parallelism was not admitted",
                "several workers ran without the admission gate passing",
            ],
            "reject": [
                "admitted",
                "the parallel workers were admitted correctly",
            ],
        },
    },
    "single-builder-cardinality": {
        "accept_any": [[
            ["single builder", "one builder", "solo", "one worker", "sole builder",
             "topology"],
            ["two", "three", "more than one", "multiple", "several", "many", "plural"],
        ]],
        "examples": {
            "accept": [
                "the topology says solo work while two logical tasks are present",
                "declared single builder but carries multiple slices",
                "one builder is declared and there are two tasks",
            ],
            "reject": [
                "cardinality",
                "single builder topology with exactly one task",
            ],
        },
    },
}

# A constant answer must not be a good strategy. Generation 1 is exempt because
# reproducing it is the point of keeping it: 6 refusals against 1 admit means
# "refuse everything" scores 0.857, and that ceiling is the defect generation 2
# exists to remove, not something to retrofit onto the executed run.
MAX_CONSTANT_VERDICT_SHARE = {1: None, 2: 0.60}


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


def reported_markers(output: str) -> list[str]:
    """Every rule marker the checker printed, so co-reported rules stay visible."""
    markers = []
    for line in output.splitlines():
        if "RUNTIME-CONTRACT-RED" not in line:
            continue
        match = re.search(r"RUNTIME-CONTRACT-RED\s+([a-z][a-z0-9]*(?:-[a-z0-9]+)+)", line)
        if match:
            markers.append(match.group(1))
    return sorted(set(markers))


def refusal_cases(base: dict[str, Any], mutations: list[tuple[str, str, Any]],
                  generation: int, refused: list[str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for target, case_id, mutation in mutations:
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
        ground_truth: dict[str, Any] = {"checker_exit_code": exit_code,
                                        "verdict": "REFUSE", "violated_rule": target}
        case: dict[str, Any] = {"case_id": case_id, "contract": contract,
                                "ground_truth": ground_truth,
                                "case_digest": digest(contract)}
        if generation >= 2:
            ground_truth["co_reported_rules"] = [m for m in reported_markers(output)
                                                 if m != target]
            case["field_family"] = FIELD_FAMILIES[target]
            case["rule_rubric"] = GEN2_RUBRICS[target]
        cases.append(case)
    return cases


def near_miss_cases(base: dict[str, Any], refused: list[str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for case_id, family, why, mutation in GEN2_NEAR_MISSES:
        contract = copy.deepcopy(base)
        mutation(contract)
        exit_code, output = run_checker(contract)
        if exit_code != 0:
            refused.append(f"{case_id}: near miss was refused (exit {exit_code}), so it "
                           f"is a defect and not a near miss: "
                           f"{output.strip().splitlines()[:1]}")
            continue
        cases.append({
            "case_id": case_id,
            "contract": contract,
            "ground_truth": {"checker_exit_code": 0, "verdict": "ADMIT",
                             "violated_rule": None},
            "case_digest": digest(contract),
            "field_family": family,
            "why_it_looks_wrong": why,
        })
    return cases


def design_gates(cases: list[dict[str, Any]], generation: int) -> list[str]:
    """Reasons this set may not be used to score a run. Empty means usable."""
    problems: list[str] = []
    ceiling = MAX_CONSTANT_VERDICT_SHARE[generation]
    if ceiling is not None:
        verdicts = [c["ground_truth"]["verdict"] for c in cases]
        share = max(verdicts.count("ADMIT"), verdicts.count("REFUSE")) / len(verdicts)
        if share > ceiling:
            problems.append(
                f"a constant verdict scores {share:.2f} of the set against a frozen "
                f"ceiling of {ceiling:.2f}; a set one word can answer measures nothing")

    if generation < 2:
        return problems

    refusal_families = {c["field_family"] for c in cases
                        if c["ground_truth"]["verdict"] == "REFUSE"}
    for case in cases:
        if case["ground_truth"]["verdict"] != "ADMIT" or "field_family" not in case:
            continue
        if case["field_family"] not in refusal_families:
            problems.append(f"{case['case_id']}: near miss in field family "
                            f"{case['field_family']} has no refusal sibling, so nothing "
                            f"about it is near")

    for case in cases:
        marker = case["ground_truth"]["violated_rule"]
        if not marker:
            continue
        problems.extend(validate_rubric(marker, case.get("rule_rubric")))
        rubric = case.get("rule_rubric") or {}
        accepted = (rubric.get("examples") or {}).get("accept") or []
        for co_reported in case["ground_truth"].get("co_reported_rules", []):
            if not any(co_reported.replace("-", " ") in " ".join(
                    example.lower().replace("-", " ").split()) for example in accepted):
                problems.append(
                    f"{case['case_id']}: the same edit also reports {co_reported}, and no "
                    f"accepted phrasing names it; a model right about that rule would "
                    f"score zero")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--generation", type=int, required=True, choices=[1, 2])
    args = parser.parse_args()

    generation = args.generation
    base = base_contract()
    positive_exit, positive_output = run_checker(base)
    if positive_exit != 0:
        print(f"the known-good base does not pass the checker (exit {positive_exit}); "
              f"every derived case would be measuring that instead:\n{positive_output}",
              file=sys.stderr)
        return 2

    positive: dict[str, Any] = {
        "case_id": "heldout-positive",
        "contract": base,
        "ground_truth": {"checker_exit_code": 0, "verdict": "ADMIT",
                         "violated_rule": None},
        "case_digest": digest(base),
    }

    refused: list[str] = []
    if generation == 1:
        cases = [positive] + refusal_cases(base, GEN1_MUTATIONS, generation, refused)
    else:
        cases = ([positive]
                 + refusal_cases(base, GEN2_MUTATIONS, generation, refused)
                 + near_miss_cases(base, refused))

    if refused:
        print("cases refused rather than relabelled:", file=sys.stderr)
        for line in refused:
            print(f"  {line}", file=sys.stderr)

    if len(cases) < 6:
        print(f"only {len(cases)} usable cases; #229 requires at least six held-out "
              f"cases and a short set is not one that can be topped up by loosening "
              f"a label", file=sys.stderr)
        return 2

    problems = design_gates(cases, generation)
    if problems:
        print("case set refused by its own design gates:", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        return 2

    body: dict[str, Any] = {
        "schema": "v2-1-crossstack-cases/v1",
        "case_set_id": CASE_SET_IDS[generation],
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
    if generation >= 2:
        body["rule_metric"] = "PARAPHRASE_RUBRIC"
        body["max_constant_verdict_share"] = MAX_CONSTANT_VERDICT_SHARE[generation]
        body["_meta"]["why_near_misses"] = (
            "Generation 1 scored 6/6 verdicts in every arm, which is not a measurement. "
            "Every refusal family here has a sibling that touches the same fields and is "
            "admitted, so 'this field changed, therefore refuse' loses, and a constant "
            "verdict cannot beat the frozen share.")
        body["_meta"]["why_rubrics"] = (
            "Generation 1 scored rule naming by token overlap with the checker's marker "
            "string, which the 36KB candidate prompt carries and the 4.6KB baseline does "
            "not. A rubric scores the concepts an answer states in whatever words it uses, "
            "and its own accept/reject examples are executed here rather than asserted.")
    body["set_digest"] = digest(body["cases"])

    args.out.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"out": str(args.out), "generation": generation,
                      "cases": len(cases),
                      "admits": sum(1 for c in cases
                                    if c["ground_truth"]["verdict"] == "ADMIT"),
                      "refusals": sum(1 for c in cases
                                      if c["ground_truth"]["verdict"] == "REFUSE"),
                      "set_digest": body["set_digest"][:12],
                      "families": [c["ground_truth"]["violated_rule"] for c in cases]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
