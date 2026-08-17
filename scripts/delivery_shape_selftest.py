#!/usr/bin/env python3
"""Controls for the delivery-shape comparison.

The controls #109 names are all ways to make arm B look better without B being
better, so each is planted here and must be refused. The admission rule gets a
control of its own: a single task pair must not unlock the default however
favourable the numbers are, because that is the inference the issue's evidence
boundary rules out.

The pre-registered task pairs on disk get the same treatment. Their whole value
is that they were written before either arm ran, and the only mechanical proof
of that is that they contain no outcome field at all — so every way of smuggling
one in is planted here too.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_delivery_shape import Refused, check_plan, compare, measure  # noqa: E402

PAIR_DIR = Path(__file__).resolve().parents[1] / "evals" / "fixtures" / "delivery-shape"

SHARED = {
    "requirement_digest": "sha256:" + "a" * 64,
    "implementation_target": "skills/fixture-target",
    "evaluator_identities": [{"id": "fixture-eval", "version": "1.0.0"}],
    "carrier": {"model": "fixture-model", "harness": "fixture-harness"},
    "fixture_commit": "b" * 40,
    "reviewer_rubric_digest": "sha256:" + "c" * 64,
    "budget": {"max_model_calls": 10, "max_retries": 2},
}


def unit(uid: str, *, files: int, added: int, paths: list[str],
         parent: str | None = None, consumes: list[str] | None = None,
         kind: str = "leaf", merged: bool = True,
         prerequisites: list[str] | None = None) -> dict[str, Any]:
    body = {
        "id": uid, "changed_files": files, "added": added, "deleted": 0,
        "paths": paths, "kind": kind, "merged": merged,
    }
    if parent:
        body["parent"] = parent
        body["consumes_parent_paths"] = consumes or []
    if prerequisites:
        body["prerequisites"] = prerequisites
    return body


def arm_a() -> dict[str, Any]:
    return {
        **copy.deepcopy(SHARED),
        "shape": "monolithic",
        "observed_budget": {"max_model_calls": 8, "max_retries": 1},
        "review_units": [
            unit("A1", files=24, added=2400,
                 paths=["skills/fixture-target/a", "skills/fixture-target/b",
                        "skills/fixture-target/c"]),
        ],
        "false_pass_count": 1,
        "old_sha_pass_count": 1,
        "path_lease_violations": 0,
        "semantic_conflicts": 2,
        "workflow_runs": 6,
        "ci_minutes": 12.0,
        "reviewer_findings": 3,
    }


def arm_b() -> dict[str, Any]:
    return {
        **copy.deepcopy(SHARED),
        "shape": "contract_first_stack",
        "observed_budget": {"max_model_calls": 8, "max_retries": 1},
        "review_units": [
            unit("B1", files=9, added=900, paths=["skills/fixture-target/a"],
                 kind="contract"),
            unit("B2", files=6, added=500, paths=["skills/fixture-target/b"],
                 parent="B1", consumes=["skills/fixture-target/a"]),
            unit("B3", files=5, added=400, paths=["skills/fixture-target/c"],
                 parent="B1", consumes=["skills/fixture-target/a"]),
            unit("B4", files=3, added=200, paths=["docs/fixture-index.md"],
                 kind="convergence", prerequisites=["B1", "B2", "B3"]),
        ],
        "false_pass_count": 0,
        "old_sha_pass_count": 0,
        "path_lease_violations": 0,
        "semantic_conflicts": 1,
        "workflow_runs": 9,
        "ci_minutes": 18.0,
        "reviewer_findings": 5,
    }


def experiment(**overrides: Any) -> dict[str, Any]:
    body = {
        "schema_version": "delivery-shape-experiment/v1",
        "experiment_id": "fixture-shape-comparison",
        "task_pairs": 1,
        "declared_budget": {"max_workflow_runs": 12, "max_ci_minutes": 30.0},
        "arms": {"A": arm_a(), "B": arm_b()},
    }
    body.update(overrides)
    return body


def run_selftest() -> int:
    failures: list[str] = []
    survived: list[str] = []

    def expect(condition: bool, label: str) -> None:
        if not condition:
            failures.append(label)

    # A well-formed pairing is measurable, and still does not unlock anything.
    try:
        result = compare(experiment())
    except Refused as error:
        print(f"SELFTEST RED: canonical experiment refused: {error}", file=sys.stderr)
        return 2
    expect(result["status"] == "PASS", "canonical experiment did not complete")
    expect(result["canonical_default_unlock"] == "BLOCKED",
           "a single task pair unlocked the default")
    expect(any("single hand-selected pair" in b for b in result["admission_blockers"]),
           "the single-pair blocker was not reported")
    expect(result["improvements_b_over_a"]["max_files_per_unit"] > 0,
           "B's smaller review units were not measured as an improvement")
    expect("rollback_blast_radius" in result["covarying_with_split_granularity"],
           "rollback radius was not reported as covarying with split granularity")
    expect("rollback_blast_radius" not in result["improvements_b_over_a"],
           "rollback radius leaked into the admission-bearing improvement set")

    refused: list[str] = []

    def case(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        body = experiment()
        mutate(body)
        try:
            compare(body)
        except Refused:
            refused.append(name)
            return
        survived.append(name)

    # Every control #109 names.
    case("fake serial stack with no consumed parent bytes",
         lambda e: e["arms"]["B"]["review_units"][1].__setitem__("consumes_parent_paths", []))
    case("child consuming paths its parent never touched",
         lambda e: e["arms"]["B"]["review_units"][1].__setitem__(
             "consumes_parent_paths", ["skills/fixture-target/never"]))
    case("overlapping sibling path leases",
         lambda e: e["arms"]["B"]["review_units"][2].__setitem__(
             "paths", ["skills/fixture-target/b"]))
    case("changed evaluator between arms",
         lambda e: e["arms"]["B"].__setitem__(
             "evaluator_identities", [{"id": "other-eval", "version": "2.0.0"}]))
    case("different requirement text between arms",
         lambda e: e["arms"]["B"].__setitem__("requirement_digest", "sha256:" + "9" * 64))
    case("different carrier between arms",
         lambda e: e["arms"]["B"]["carrier"].__setitem__("model", "a-bigger-model"))
    case("different fixture commit between arms",
         lambda e: e["arms"]["B"].__setitem__("fixture_commit", "9" * 40))
    case("different reviewer rubric between arms",
         lambda e: e["arms"]["B"].__setitem__("reviewer_rubric_digest", "sha256:" + "9" * 64))
    case("one arm given more model calls",
         lambda e: e["arms"]["B"]["observed_budget"].__setitem__("max_model_calls", 99))
    case("one arm given more retries",
         lambda e: e["arms"]["B"]["observed_budget"].__setitem__("max_retries", 9))
    case("convergence created before its prerequisites merged",
         lambda e: e["arms"]["B"]["review_units"][1].__setitem__("merged", False))
    case("convergence naming no prerequisites",
         lambda e: e["arms"]["B"]["review_units"][3].__setitem__("prerequisites", []))
    case("convergence requiring a unit of another arm",
         lambda e: e["arms"]["B"]["review_units"][3].__setitem__("prerequisites", ["A1"]))
    case("duplicate review unit id",
         lambda e: e["arms"]["B"]["review_units"].append(
             copy.deepcopy(e["arms"]["B"]["review_units"][0])))
    case("arm shapes swapped",
         lambda e: (e["arms"]["A"].__setitem__("shape", "contract_first_stack"),
                    e["arms"]["B"].__setitem__("shape", "monolithic")))
    case("an arm with no review units",
         lambda e: e["arms"]["B"].__setitem__("review_units", []))
    case("a controlled field left undeclared",
         lambda e: (e["arms"]["A"].__setitem__("reviewer_rubric_digest", None),
                    e["arms"]["B"].__setitem__("reviewer_rubric_digest", None)))

    # The admission rule itself, as refusals rather than a score.
    regressed = experiment(task_pairs=4)
    regressed["arms"]["B"]["false_pass_count"] = 3
    outcome = compare(regressed)
    expect(outcome["canonical_default_unlock"] == "BLOCKED",
           "a deterministic regression did not block the unlock")
    expect(any("regressed on a deterministic outcome" in b
               for b in outcome["admission_blockers"]),
           "the deterministic regression was not named")

    over_budget = experiment(task_pairs=4)
    over_budget["arms"]["B"]["ci_minutes"] = 99.0
    outcome = compare(over_budget)
    expect(outcome["canonical_default_unlock"] == "BLOCKED",
           "exceeding the declared CI budget did not block the unlock")

    # More PRs alone must not be an improvement.
    pr_only = experiment(task_pairs=4)
    # Every outcome held identical to A, so the only thing that can move is the
    # rollback radius -- which falls purely because the units are smaller.
    for field in ("false_pass_count", "old_sha_pass_count",
                  "path_lease_violations", "semantic_conflicts"):
        pr_only["arms"]["B"][field] = pr_only["arms"]["A"][field]
    b_units = pr_only["arms"]["B"]["review_units"]
    for index, item in enumerate(b_units[:3]):
        item["changed_files"] = 24
        item["added"] = 2400
        item["paths"] = [f"skills/fixture-target/only-{index}"]
        if "consumes_parent_paths" in item:
            item["consumes_parent_paths"] = ["skills/fixture-target/only-0"]
    b_units[0]["paths"] = ["skills/fixture-target/only-0"]
    outcome = compare(pr_only)
    expect(outcome["canonical_default_unlock"] == "BLOCKED",
           "more review units alone unlocked the default")
    expect("review_units" not in str(outcome["improvements_b_over_a"]),
           "review unit count leaked into the improvement set")
    expect(any("rollback blast radius" in b for b in outcome["admission_blockers"]),
           "a rollback-radius-only gain was not named as insufficient")

    # A single arm is measurable and carries no comparative claim.
    single = measure(arm_b(), "arm B")
    expect(single["review_units"] == 4, "single-arm measurement failed")

    # The pre-registered pairs that actually ship. An empty directory is its own
    # state: it means the pairs are ABSENT, not that they passed.
    pair_files = sorted(PAIR_DIR.glob("task-pair-*.json"))
    if len(pair_files) < 2:
        print(f"SELFTEST RED: {len(pair_files)} pre-registered task pair(s) under "
              f"{PAIR_DIR}; the admission rule needs at least two", file=sys.stderr)
        return 2

    pairs: list[dict[str, Any]] = []
    for path in pair_files:
        body = json.loads(path.read_text(encoding="utf-8"))
        try:
            receipt = check_plan(body)
        except Refused as error:
            failures.append(f"committed pair {path.name} refused: {error}")
            continue
        pairs.append(body)
        expect(receipt["status"] == "PRE_REGISTERED",
               f"{path.name} did not read as a pre-registration")
        expect(receipt["canonical_default_unlock"] == "BLOCKED",
               f"{path.name} unlocked the default without running")
        # A plan and a record must not be interchangeable in either direction.
        try:
            compare(copy.deepcopy(body))
        except Refused:
            pass
        else:
            failures.append(f"{path.name} was accepted as an executed experiment")

    def plan_case(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        if not pairs:
            return
        body = copy.deepcopy(pairs[0])
        mutate(body)
        try:
            check_plan(body)
        except Refused:
            plan_refusals.append(name)
            return
        survived.append(name)

    plan_refusals: list[str] = []
    # Every way an outcome can reach a document defined by having none.
    plan_case("an outcome count on the pair",
              lambda p: p.__setitem__("task_pairs", 2))
    plan_case("an outcome count on an arm",
              lambda p: p["arms"]["B"].__setitem__("false_pass_count", 0))
    plan_case("CI minutes recorded before running",
              lambda p: p["arms"]["B"].__setitem__("ci_minutes", 4.0))
    plan_case("a measured size on a planned unit",
              lambda p: p["arms"]["B"]["planned_units"][0].__setitem__("changed_files", 9))
    plan_case("a planned unit already declared merged",
              lambda p: p["arms"]["B"]["planned_units"][0].__setitem__("merged", True))
    plan_case("an executed pair filed as a plan",
              lambda p: p.__setitem__("execution_state", "EXERCISED"))
    plan_case("a record's schema wearing a plan's name",
              lambda p: p.__setitem__("schema_version", "delivery-shape-experiment/v1"))
    # The controls carry over, because a pre-registration that is unfair on
    # paper produces an unfair experiment when it runs.
    plan_case("requirement digest that does not digest its own text",
              lambda p: p["arms"]["A"].__setitem__("requirement_text", "something else"))
    plan_case("reviewer rubric digest that does not digest its own text",
              lambda p: (p["arms"]["A"].__setitem__("reviewer_rubric", "lenient"),
                         p["arms"]["B"].__setitem__("reviewer_rubric", "lenient")))
    plan_case("different carrier between arms",
              lambda p: p["arms"]["B"]["carrier"].__setitem__("model", "a-bigger-model"))
    plan_case("different base commit between arms",
              lambda p: p["arms"]["B"].__setitem__("fixture_commit", "9" * 40))
    plan_case("arm shapes swapped",
              lambda p: (p["arms"]["A"].__setitem__("shape", "contract_first_stack"),
                         p["arms"]["B"].__setitem__("shape", "monolithic")))
    plan_case("arms planning different files",
              lambda p: p["arms"]["A"]["planned_units"][0]["paths"].append("docs/extra.md"))
    plan_case("fake serial stack with no consumed parent bytes",
              lambda p: p["arms"]["B"]["planned_units"][1].__setitem__(
                  "consumes_parent_paths", []))
    plan_case("child consuming paths its parent never touched",
              lambda p: p["arms"]["B"]["planned_units"][1].__setitem__(
                  "consumes_parent_paths", ["skills/never-touched"]))
    plan_case("overlapping sibling path leases",
              lambda p: p["arms"]["B"]["planned_units"][2].__setitem__(
                  "paths", list(p["arms"]["B"]["planned_units"][1]["paths"])))
    plan_case("convergence naming no prerequisites",
              lambda p: p["arms"]["B"]["planned_units"][3].__setitem__("prerequisites", []))
    plan_case("an arm planning no units",
              lambda p: p["arms"]["B"].__setitem__("planned_units", []))

    if survived:
        for name in survived:
            failures.append(f"mutation survived: {name}")
    if failures:
        for item in failures:
            print(f"SELFTEST RED: {item}", file=sys.stderr)
        return 2
    print(f"SELFTEST GREEN: paired experiment measured; {len(refused)} unfairness "
          f"controls refused; {len(pairs)} pre-registered task pairs validated with "
          f"{len(plan_refusals)} outcome-leak controls refused; the default stays "
          f"blocked on a single pair")
    return 0
