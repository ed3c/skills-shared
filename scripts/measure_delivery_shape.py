#!/usr/bin/env python3
"""Compare a monolithic delivery against a contract-first stack, or refuse to.

The question #109 asks is whether splitting a change into a contract
foundation, true children and path-disjoint siblings improves correctness,
reviewability, failure isolation and rollback scope — without spending an
unacceptable amount of CI and rebase churn.

Almost every way of answering it cheaply is wrong in the same direction:

    B produced more pull requests        -> so B was better decomposed
    B's diffs were smaller per unit      -> so B was more reviewable
    B's arm ran with a newer evaluator   -> so B found more defects
    B's arm was allowed more retries     -> so B converged
    a reviewer scored B higher           -> so B passed

Each is a well-formed number and none of them is the claim. PR count is a
property of how the work was cut, not of whether it was cut well; and the
issue says so directly: "PR count alone is not a success metric."

So this module does two separable things, and keeps them separable:

  `measure`  reads a delivery record and reports observable shape. It never
             compares, because a single arm has nothing to be better than.
  `compare`  requires a paired experiment, refuses unfair pairings before
             computing anything, and refuses to unlock the default on a
             single task however good the numbers are.
  `plan`     reads a pre-registered task pair — the treatment and the controls
             fixed before either arm runs — and refuses any outcome field in
             it. A pre-registration that already knows how it turned out is a
             record wearing a plan's name, and the difference is the whole
             value of registering it first.

Exits: 0 done, 2 refused or gate failed, 64 unusable input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

MEASUREMENT_SCHEMA = "delivery-shape-measurement/v1"
EXPERIMENT_SCHEMA = "delivery-shape-experiment/v1"
TASK_PAIR_SCHEMA = "delivery-shape-task-pair/v1"

# Fields that must be identical across arms. A difference in any of them makes
# the branch graph one variable among several, and the comparison answers a
# question nobody asked.
CONTROLLED_FIELDS = (
    "requirement_digest",
    "implementation_target",
    "evaluator_identities",
    "carrier",
    "fixture_commit",
    "reviewer_rubric_digest",
    "budget",
)

# A pre-registration declares the treatment and nothing about the outcome, so
# its fields are allowlisted rather than denylisted: a metric added to the
# measurement schema later would arrive here by default under a denylist, and
# the first person to notice would be whoever read a fabricated number as data.
PAIR_FIELDS = frozenset({"schema_version", "pair_id", "execution_state",
                         "declared_budget", "arms", "_meta"})
ARM_PLAN_FIELDS = frozenset(CONTROLLED_FIELDS) | {
    "shape", "requirement_text", "reviewer_rubric", "planned_units"}
UNIT_PLAN_FIELDS = frozenset({"id", "kind", "parent", "consumes_parent_paths",
                              "paths", "prerequisites", "purpose"})


class Refused(Exception):
    """Read, and cannot support the comparison."""


class Unusable(Exception):
    """Could not be read."""


def load(path: Path, label: str) -> dict[str, Any]:
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise Unusable(f"{label}: unreadable {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise Unusable(f"{label}: unparseable {path}: {error}") from error
    if not isinstance(body, dict):
        raise Unusable(f"{label}: root must be an object")
    return body


def key(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def check_units(arm: dict[str, Any], label: str, *,
                field: str = "review_units", require_merged: bool = True) -> None:
    """Structural rules a delivery record must satisfy to be measurable.

    The same rules describe a branch graph that has been executed and one that
    has only been planned, so `field` selects which the arm declares. Only the
    merged-prerequisite rule differs: nothing is merged in a plan yet, and
    demanding it there would make every honest pre-registration unwritable.
    """
    noun = "planned unit" if field == "planned_units" else "review unit"
    units = arm.get(field)
    if not isinstance(units, list) or not units:
        raise Refused(f"{label} declares no {noun}s")

    seen_ids: set[str] = set()
    for unit in units:
        unit_id = unit.get("id")
        if not unit_id:
            raise Refused(f"{label}: a {noun} has no id")
        if unit_id in seen_ids:
            raise Refused(f"{label}: {noun} {unit_id!r} is declared twice")
        seen_ids.add(unit_id)

        parent = unit.get("parent")
        if parent is not None:
            if parent not in seen_ids and parent not in {u.get("id") for u in units}:
                raise Refused(
                    f"{label}: unit {unit_id!r} names parent {parent!r}, which is "
                    f"not a unit of this arm"
                )
            # A serial child that consumes none of its parent's bytes is not a
            # child. Declaring it one inflates the depth of the stack without
            # any dependency existing, which is the cheapest way to make B look
            # decomposed.
            if not unit.get("consumes_parent_paths"):
                raise Refused(
                    f"{label}: unit {unit_id!r} is declared a child of "
                    f"{parent!r} but consumes none of its paths; a serial stack "
                    f"with no consumed parent bytes is not a stack"
                )
            parent_unit = next(u for u in units if u.get("id") == parent)
            outside = sorted(
                set(unit["consumes_parent_paths"]) - set(parent_unit.get("paths") or []))
            if outside:
                raise Refused(
                    f"{label}: unit {unit_id!r} claims to consume paths its "
                    f"parent never touched: {', '.join(outside)}"
                )

    # Siblings must hold disjoint path leases, or they are not siblings and
    # merging them independently is what produces add/add conflicts.
    by_parent: dict[Any, list[dict[str, Any]]] = {}
    for unit in units:
        by_parent.setdefault(unit.get("parent"), []).append(unit)
    for parent, group in by_parent.items():
        for index, first in enumerate(group):
            for second in group[index + 1:]:
                overlap = sorted(set(first.get("paths") or []) & set(second.get("paths") or []))
                if overlap:
                    raise Refused(
                        f"{label}: siblings {first['id']!r} and {second['id']!r} "
                        f"share path lease(s) {', '.join(overlap)}; independent "
                        f"merge would collide"
                    )

    convergence = [u for u in units if u.get("kind") == "convergence"]
    for unit in convergence:
        prerequisites = unit.get("prerequisites") or []
        if not prerequisites:
            raise Refused(f"{label}: convergence unit {unit['id']!r} names no prerequisites")
        for required in prerequisites:
            source = next((u for u in units if u.get("id") == required), None)
            if source is None:
                raise Refused(
                    f"{label}: convergence unit {unit['id']!r} requires {required!r}, "
                    f"which is not a unit of this arm"
                )
            if require_merged and not source.get("merged"):
                raise Refused(
                    f"{label}: convergence unit {unit['id']!r} exists while "
                    f"prerequisite {required!r} is unmerged"
                )


def measure(arm: dict[str, Any], label: str) -> dict[str, Any]:
    check_units(arm, label)
    units = arm["review_units"]
    sizes = [int(u.get("changed_files", 0)) for u in units]
    diffs = [int(u.get("added", 0)) + int(u.get("deleted", 0)) for u in units]
    rollback = [len(u.get("paths") or []) for u in units]

    first_defect_layers = [u.get("first_defect_layer") for u in units
                           if u.get("first_defect_layer")]
    return {
        "review_units": len(units),
        "changed_files_total": sum(sizes),
        "changed_files_max_per_unit": max(sizes) if sizes else 0,
        "changed_files_median_per_unit": sorted(sizes)[len(sizes) // 2] if sizes else 0,
        "diff_lines_total": sum(diffs),
        "diff_lines_max_per_unit": max(diffs) if diffs else 0,
        "path_lease_violations": int(arm.get("path_lease_violations", 0)),
        "first_defect_layers": sorted(set(first_defect_layers)),
        "false_pass_count": int(arm.get("false_pass_count", 0)),
        "old_sha_pass_count": int(arm.get("old_sha_pass_count", 0)),
        "stale_receipt_invalidations": int(arm.get("stale_receipt_invalidations", 0)),
        "child_revalidations": int(arm.get("child_revalidations", 0)),
        "semantic_conflicts": int(arm.get("semantic_conflicts", 0)),
        "workflow_runs": int(arm.get("workflow_runs", 0)),
        "ci_minutes": float(arm.get("ci_minutes", 0)),
        "first_red_to_green_minutes": arm.get("first_red_to_green_minutes"),
        "reviewer_findings": int(arm.get("reviewer_findings", 0)),
        "review_latency_minutes": arm.get("review_latency_minutes"),
        "rollback_blast_radius_max_paths": max(rollback) if rollback else 0,
        "tokens_observed": arm.get("tokens_observed"),
        "human_admit_evidence_gaps": sorted(arm.get("human_admit_evidence_gaps") or []),
    }


def check_two_arms(body: dict[str, Any]) -> dict[str, Any]:
    arms = body.get("arms")
    if not isinstance(arms, dict) or set(arms) != {"A", "B"}:
        raise Refused("an experiment has exactly two arms, A and B")
    return arms


def check_controlled(arms: dict[str, Any]) -> None:
    """Every field that must be held identical, and actually declared."""
    for field in CONTROLLED_FIELDS:
        values = {name: key(arm.get(field)) for name, arm in arms.items()}
        if len(set(values.values())) != 1:
            raise Refused(
                f"{field} differs between arms; the branch graph is the "
                f"treatment, and anything else differing is a confounder"
            )
        if arms["A"].get(field) in (None, "", [], {}):
            raise Refused(f"{field} is undeclared, so it cannot be shown identical")


def check_shapes(arms: dict[str, Any]) -> None:
    if arms["A"].get("shape") != "monolithic" or arms["B"].get("shape") != "contract_first_stack":
        raise Refused("arm A must be monolithic and arm B a contract-first stack")


def check_pairing(experiment: dict[str, Any]) -> None:
    if experiment.get("schema_version") != EXPERIMENT_SCHEMA:
        raise Refused(f"schema_version is not {EXPERIMENT_SCHEMA}")
    arms = check_two_arms(experiment)
    check_controlled(arms)

    for name, arm in arms.items():
        observed = arm.get("observed_budget")
        declared = arms["A"]["budget"]
        if not isinstance(observed, dict):
            raise Refused(f"arm {name} declares no observed_budget")
        for budget_field, ceiling in declared.items():
            if not isinstance(ceiling, (int, float)):
                continue
            if observed.get(budget_field, 0) > ceiling:
                raise Refused(
                    f"arm {name} used {observed.get(budget_field)} {budget_field} "
                    f"against a declared ceiling of {ceiling}; an arm with more "
                    f"attempts is not a better method"
                )

    check_shapes(arms)


def digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_plan(pair: dict[str, Any]) -> dict[str, Any]:
    """Validate a task pair registered before either arm runs.

    Two arms only answer the branch-graph question if the requirement, target,
    evaluator, carrier, base commit, rubric and budget were fixed before anyone
    saw a result. Fixing them afterwards is indistinguishable, in the file, from
    fixing them before — so they are fixed here, in a document whose defining
    property is that it contains no outcome at all.
    """
    if pair.get("schema_version") != TASK_PAIR_SCHEMA:
        raise Refused(f"schema_version is not {TASK_PAIR_SCHEMA}")
    unknown = sorted(set(pair) - PAIR_FIELDS)
    if unknown:
        raise Refused(
            f"a task pair carries no outcome, and these are not plan fields: "
            f"{', '.join(unknown)}"
        )
    if pair.get("execution_state") != "NOT_EXERCISED":
        raise Refused(
            "execution_state must be NOT_EXERCISED; a pair that has run is a "
            "record, and records go through `compare`"
        )

    arms = check_two_arms(pair)
    check_controlled(arms)
    check_shapes(arms)

    for name, arm in arms.items():
        label = f"arm {name}"
        stray = sorted(set(arm) - ARM_PLAN_FIELDS)
        if stray:
            raise Refused(
                f"{label} declares outcome-bearing field(s) before running: "
                f"{', '.join(stray)}"
            )
        # The controlled digests are the pre-registration's only falsifiable
        # part: without the text beside them, "identical requirement" is a claim
        # about two hex strings nobody can check.
        for text_field, digest_field in (("requirement_text", "requirement_digest"),
                                         ("reviewer_rubric", "reviewer_rubric_digest")):
            text = arm.get(text_field)
            if not isinstance(text, str) or not text.strip():
                raise Refused(f"{label} declares no {text_field}")
            if arm[digest_field] != digest(text):
                raise Refused(
                    f"{label}: {digest_field} does not digest its own "
                    f"{text_field}, so the field it controls is unverifiable"
                )
        check_units(arm, label, field="planned_units", require_merged=False)
        for unit in arm["planned_units"]:
            leaked = sorted(set(unit) - UNIT_PLAN_FIELDS)
            if leaked:
                raise Refused(
                    f"{label}: planned unit {unit['id']!r} declares measured "
                    f"field(s) {', '.join(leaked)}; nothing has been measured yet"
                )

    # Two arms of one task end at the same tree. If B plans to touch files A
    # does not, the arms are not the same work cut two ways, and the comparison
    # would be reading a scope difference as a shape difference.
    paths = {name: {p for u in arm["planned_units"] for p in (u.get("paths") or [])}
             for name, arm in arms.items()}
    if paths["A"] != paths["B"]:
        raise Refused(
            "the arms plan different files: "
            f"A-only {sorted(paths['A'] - paths['B']) or '[]'}, "
            f"B-only {sorted(paths['B'] - paths['A']) or '[]'}; two arms of one "
            f"task must deliver the same tree"
        )

    return {
        "schema_version": "delivery-shape-task-pair-receipt/v1",
        "pair_id": pair.get("pair_id"),
        "execution_state": "NOT_EXERCISED",
        "planned_units": {name: len(arm["planned_units"]) for name, arm in arms.items()},
        "planned_paths": len(paths["A"]),
        "comparative_claim": "NONE — neither arm has run, so there is no outcome",
        "canonical_default_unlock": "BLOCKED",
        "status": "PRE_REGISTERED",
    }


def compare(experiment: dict[str, Any]) -> dict[str, Any]:
    check_pairing(experiment)
    arms = experiment["arms"]
    measured = {name: measure(arm, f"arm {name}") for name, arm in arms.items()}

    a, b = measured["A"], measured["B"]

    # Deterministic outcome first. A reviewer's advisory score never overturns
    # it, and a defect that reached a later layer is not a better outcome.
    deterministic_regressions: list[str] = []
    for field, worse_is in (("false_pass_count", "higher"),
                            ("old_sha_pass_count", "higher"),
                            ("path_lease_violations", "higher"),
                            ("semantic_conflicts", "higher")):
        if b[field] > a[field]:
            deterministic_regressions.append(
                f"{field}: A={a[field]} B={b[field]}")

    budget = experiment.get("declared_budget") or {}
    budget_breaches: list[str] = []
    for field in ("workflow_runs", "ci_minutes"):
        ceiling = budget.get(f"max_{field}")
        if isinstance(ceiling, (int, float)) and b[field] > ceiling:
            budget_breaches.append(
                f"{field}: B={b[field]} exceeds declared ceiling {ceiling}")

    # Two kinds of improvement, kept apart because one of them can be produced
    # by cutting the work into more pieces without cutting it better.
    reviewability = {
        "max_files_per_unit": a["changed_files_max_per_unit"] - b["changed_files_max_per_unit"],
        "max_diff_per_unit": a["diff_lines_max_per_unit"] - b["diff_lines_max_per_unit"],
    }
    outcomes = {
        "false_pass": a["false_pass_count"] - b["false_pass_count"],
        "old_sha_pass": a["old_sha_pass_count"] - b["old_sha_pass_count"],
        "semantic_conflicts": a["semantic_conflicts"] - b["semantic_conflicts"],
        "path_lease_violations": a["path_lease_violations"] - b["path_lease_violations"],
    }
    # Rollback radius falls automatically as units get smaller, so it covaries
    # with how finely the work was split and is not independent evidence. It is
    # reported, and it counts only alongside a reviewability or outcome gain.
    covarying = {
        "rollback_blast_radius": a["rollback_blast_radius_max_paths"] - b["rollback_blast_radius_max_paths"],
    }
    improvements = {**reviewability, **outcomes}

    # The admission rule, stated as a refusal rather than a score. A single
    # hand-selected task pair is mechanism evidence; it cannot establish that
    # one shape is generally better, so the default stays where it is.
    task_pairs = int(experiment.get("task_pairs", 1))
    admission_blockers: list[str] = []
    if deterministic_regressions:
        admission_blockers.append(
            "B regressed on a deterministic outcome: " + "; ".join(deterministic_regressions))
    if budget_breaches:
        admission_blockers.append("B exceeded the declared budget: " + "; ".join(budget_breaches))
    if task_pairs < 2:
        admission_blockers.append(
            f"{task_pairs} task pair(s): a single hand-selected pair is mechanism "
            f"evidence, not comparative outcome evidence"
        )
    if not any(value > 0 for value in improvements.values()):
        if any(value > 0 for value in covarying.values()):
            admission_blockers.append(
                "B improved only rollback blast radius, which falls automatically "
                "as units get smaller; that is a measure of how finely the work "
                "was split, not of whether it was split well"
            )
        else:
            admission_blockers.append("B improved nothing measurable")

    return {
        "schema_version": "delivery-shape-comparison/v1",
        "experiment_id": experiment.get("experiment_id"),
        "task_pairs": task_pairs,
        "arms": measured,
        "improvements_b_over_a": improvements,
        "covarying_with_split_granularity": covarying,
        "deterministic_regressions": deterministic_regressions,
        "budget_breaches": budget_breaches,
        "pr_count_note": (
            "review_units is reported and deliberately excluded from the admission "
            "rule: it is a property of how the work was cut, not of whether it was "
            "cut well"
        ),
        "canonical_default_unlock": "BLOCKED" if admission_blockers else "ELIGIBLE_FOR_HUMAN_ADMIT",
        "admission_blockers": admission_blockers,
        "status": "PASS",
    }


def _selftest() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from delivery_shape_selftest import run_selftest
    return run_selftest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("measure", "compare", "plan", "selftest"))
    parser.add_argument("subject", type=Path, nargs="?")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    if args.mode == "selftest":
        return _selftest()
    if args.subject is None:
        parser.error("a subject path is required")

    try:
        body = load(args.subject, args.mode)
        if args.mode == "measure":
            if body.get("schema_version") != MEASUREMENT_SCHEMA:
                raise Refused(f"schema_version is not {MEASUREMENT_SCHEMA}")
            result = {"schema_version": "delivery-shape-measurement-receipt/v1",
                      "arm": body.get("arm_id"),
                      "shape": body.get("shape"),
                      "measured": measure(body, "arm"),
                      "comparative_claim": "NONE — a single arm has nothing to be better than"}
        elif args.mode == "plan":
            result = check_plan(body)
        else:
            result = compare(body)
    except Unusable as error:
        print(f"FATAL delivery-shape: {error}", file=sys.stderr)
        return 64
    except Refused as error:
        print(f"DELIVERY SHAPE RED: {error}", file=sys.stderr)
        return 2

    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
