#!/usr/bin/env python3
"""Score an integrated controlled-language A/B run, and refuse an unfair one.

Most of this file is not scoring. Scoring an A/B comparison is arithmetic; the
hard part is that an unfair comparison produces exactly the same shape of
numbers as a fair one, and reads better.

    a different evaluator per arm       -> the candidate is graded more kindly
    a larger budget for one arm         -> the candidate had more attempts
    the baseline given skill content    -> both arms are the candidate
    failed conditions dropped           -> the denominator flatters the rate
    a semantic PASS over a hard failure -> a deterministic breach disappears

Every one of those yields a well-formed bundle and a plausible improvement.
So the validity checks run first, and no metric is emitted for a bundle that
fails them: a number computed from an invalid experiment is worse than no
number, because it looks like evidence.

Exits: 0 scored, 2 invalid experiment or failed gate, 64 unusable input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA = "controlled-language-ab-run/v1"
BASELINE_ARMS = ("no_skill", "prompt_only_baseline")
REQUIRED_CONDITIONS = (
    "no_skill",
    "prompt_only_baseline",
    "candidate_skill",
    "wrong_profile",
    "stale_termbase",
    "missing_human_review",
    "restricted_external_attempt",
    "lossy_document_rewrite",
)
# Conditions that must NOT reach a passing outcome: each is a planted defect in
# the experiment itself, and a green result there means the Harness missed it.
NEGATIVE_CONDITIONS = (
    "wrong_profile",
    "stale_termbase",
    "missing_human_review",
    "restricted_external_attempt",
    "lossy_document_rewrite",
)
BUDGET_FIELDS = ("max_model_calls", "max_tool_calls", "max_retries", "seed")


class Invalid(Exception):
    """The experiment cannot support a comparison."""


class Unusable(Exception):
    """The input could not be read. Not the same event as an invalid one."""


def load(path: Path) -> dict[str, Any]:
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise Unusable(f"unreadable: {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise Unusable(f"unparseable: {path}: {error}") from error
    if not isinstance(body, dict):
        raise Unusable(f"{path}: root must be an object")
    return body


def identity_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def check_validity(bundle: dict[str, Any]) -> None:
    if bundle.get("schema_version") != SCHEMA:
        raise Invalid(f"schema_version is not {SCHEMA}")

    conditions = bundle.get("conditions")
    if not isinstance(conditions, list) or not conditions:
        raise Invalid("conditions must be a non-empty array")

    names = [item.get("name") for item in conditions]
    if len(names) != len(set(names)):
        raise Invalid("a condition name is repeated")
    missing = [name for name in REQUIRED_CONDITIONS if name not in names]
    if missing:
        raise Invalid(
            f"conditions absent: {', '.join(missing)}. A comparison that drops "
            f"an arm is not the declared experiment, and the arms most likely "
            f"to be dropped are the ones that failed"
        )

    # One identity for the whole experiment. If any of these differ per arm,
    # the arms were not measured against the same thing.
    for field in ("fixture_identity", "profile_identity", "termbase_identity",
                  "model_identity", "harness_identity", "environment_identity"):
        if field not in bundle:
            raise Invalid(f"{field} is absent; the arms share no declared {field}")
        seen = {
            identity_key(item.get(field))
            for item in conditions
            if field in item
        }
        if seen and seen != {identity_key(bundle[field])}:
            raise Invalid(
                f"{field} differs between conditions; the arms were not "
                f"measured against the same subject"
            )

    evaluators = identity_key(bundle.get("evaluator_identities"))
    if not bundle.get("evaluator_identities"):
        raise Invalid("evaluator_identities is absent")
    for item in conditions:
        if "evaluator_identities" in item and identity_key(item["evaluator_identities"]) != evaluators:
            raise Invalid(
                f"condition {item['name']!r} was graded by different evaluators; "
                f"a comparison against a different grader is not a comparison"
            )

    budget = bundle.get("budget")
    if not isinstance(budget, dict) or any(field not in budget for field in BUDGET_FIELDS):
        raise Invalid(f"budget must declare {', '.join(BUDGET_FIELDS)}")
    for item in conditions:
        observed = item.get("observed_budget")
        if not isinstance(observed, dict):
            raise Invalid(f"condition {item['name']!r} has no observed_budget")
        for field in ("max_model_calls", "max_tool_calls", "max_retries"):
            if observed.get(field, 0) > budget[field]:
                raise Invalid(
                    f"condition {item['name']!r} used {observed.get(field)} "
                    f"{field} against a declared budget of {budget[field]}; one "
                    f"arm having more attempts is not a better method"
                )
        if observed.get("seed") != budget["seed"]:
            raise Invalid(f"condition {item['name']!r} ran on a different seed")

    for item in conditions:
        if item["name"] in BASELINE_ARMS and item.get("skill_content_included") is not False:
            raise Invalid(
                f"baseline arm {item['name']!r} declares skill content included; "
                f"a baseline given the candidate's content is the candidate"
            )
        if item["name"] == "candidate_skill" and item.get("skill_content_included") is not True:
            raise Invalid("candidate_skill arm does not include the skill content")

    # Every arm reports the same case set, or the rates have different
    # denominators and are not comparable.
    case_sets = {
        item["name"]: sorted(result.get("case_id") for result in item.get("results", []))
        for item in conditions
    }
    reference = case_sets[conditions[0]["name"]]
    if not reference:
        raise Invalid("conditions carry no case results")
    for name, cases in case_sets.items():
        if cases != reference:
            missing_cases = sorted(set(reference) - set(cases))
            raise Invalid(
                f"condition {name!r} reports a different case set"
                + (f"; absent: {', '.join(missing_cases)}" if missing_cases else "")
                + ". Dropping a case from one arm changes its denominator"
            )

    declared_total = bundle.get("declared_case_count")
    if declared_total is not None and declared_total != len(reference):
        raise Invalid(
            f"declared_case_count is {declared_total} but {len(reference)} cases "
            f"are reported; a shrinking denominator flatters every rate"
        )

    physical = bundle.get("physical_runs", 0)
    if bundle.get("generalization_claimed") and physical < 2:
        raise Invalid(
            f"generalization is claimed from {physical} physical run(s); a "
            f"single run establishes only the subject it ran on"
        )

    if bundle.get("compliance_claim") not in (None, "NONE", "HUMAN_ADMIT_REQUIRED"):
        raise Invalid(
            f"bundle asserts a compliance claim {bundle['compliance_claim']!r}; "
            f"the profile here is proposal-derived and no compliance claim is "
            f"available to it"
        )


def check_results(bundle: dict[str, Any]) -> list[str]:
    """Per-case rules that no arm may violate, whatever its aggregate looks like."""
    failures: list[str] = []
    for condition in bundle["conditions"]:
        for result in condition.get("results", []):
            where = f"{condition['name']}/{result.get('case_id')}"
            if result.get("deterministic_status") == "FAIL" and result.get("final_status") == "PASS":
                failures.append(
                    f"{where}: final PASS over a deterministic FAIL"
                )
            if (result.get("warnings_preserved") is False
                    or result.get("step_order_preserved") is False):
                if result.get("final_status") == "PASS":
                    failures.append(
                        f"{where}: final PASS while a warning or step order was "
                        f"lost; a high similarity score does not restore them"
                    )
            if result.get("restricted") and result.get("execution_lane") != "LOCAL_ONLY":
                failures.append(
                    f"{where}: restricted text left the local lane via "
                    f"{result.get('execution_lane')!r}"
                )
            review = result.get("human_review")
            if review and review.get("generated_by_agent") is not False:
                failures.append(f"{where}: human review was generated by an agent")
            if result.get("span_valid") is False and result.get("final_status") == "PASS":
                failures.append(f"{where}: final PASS with an invalid source span")

    for condition in bundle["conditions"]:
        if condition["name"] not in NEGATIVE_CONDITIONS:
            continue
        passing = [
            result.get("case_id") for result in condition.get("results", [])
            if result.get("final_status") == "PASS"
        ]
        if passing:
            failures.append(
                f"{condition['name']}: planted defect condition passed on "
                f"{len(passing)} case(s); the Harness did not detect what the "
                f"arm exists to plant"
            )
    return failures


def score(bundle: dict[str, Any]) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for condition in bundle["conditions"]:
        results = condition.get("results", [])
        total = len(results)
        if total == 0:
            continue

        def rate(predicate: Any) -> float:
            return sum(1 for item in results if predicate(item)) / total

        expected = sum(len(item.get("expected_violations", [])) for item in results)
        found = sum(
            len(set(item.get("violations_found", [])) & set(item.get("expected_violations", [])))
            for item in results
        )
        spurious = sum(
            len(set(item.get("violations_found", [])) - set(item.get("expected_violations", [])))
            for item in results
        )
        repairs = [item for item in results if item.get("repair_attempts", 0) > 0]

        metrics[condition["name"]] = {
            "cases": total,
            "deterministic_hard_gate_pass_rate": rate(
                lambda item: item.get("deterministic_status") == "PASS"),
            "violation_recall": (found / expected) if expected else None,
            "violation_false_positive_count": spurious,
            "tn_tv_false_rejection_rate": rate(
                lambda item: item.get("tn_tv_false_rejection") is True),
            "tn_tv_unsupported_admission_rate": rate(
                lambda item: item.get("tn_tv_unsupported_admission") is True),
            "source_span_validity_rate": rate(lambda item: item.get("span_valid") is True),
            "warning_preservation_rate": rate(
                lambda item: item.get("warnings_preserved") is True),
            "step_order_preservation_rate": rate(
                lambda item: item.get("step_order_preserved") is True),
            "semantic_meaning_preservation_score": (
                sum(item.get("meaning_preservation_score", 0.0) for item in results) / total),
            "repair_convergence_rate": (
                sum(1 for item in repairs if item.get("repair_converged")) / len(repairs)
                if repairs else None),
            "repair_no_improvement_stop_rate": (
                sum(1 for item in repairs if item.get("repair_stopped_no_improvement")) / len(repairs)
                if repairs else None),
            "human_override_rate": rate(lambda item: item.get("human_override") is True),
            "unsupported_compliance_claim_count": sum(
                1 for item in results if item.get("compliance_claim_made")),
            "tokens_in": sum(item.get("tokens_in", 0) for item in results),
            "tokens_out": sum(item.get("tokens_out", 0) for item in results),
            "latency_ms_total": sum(item.get("latency_ms", 0) for item in results),
            "tool_calls": sum(item.get("tool_calls", 0) for item in results),
            "evaluator_calls": sum(item.get("evaluator_calls", 0) for item in results),
            "provider_calls": sum(item.get("provider_calls", 0) for item in results),
        }
    return metrics


def evaluate(bundle: dict[str, Any]) -> dict[str, Any]:
    check_validity(bundle)
    failures = check_results(bundle)
    metrics = score(bundle)
    return {
        "schema_version": "controlled-language-ab-receipt/v1",
        "experiment_id": bundle.get("experiment_id"),
        "fixture_identity": bundle.get("fixture_identity"),
        "profile_identity": bundle.get("profile_identity"),
        "evidence_class": "OFFLINE_FIXTURE" if not bundle.get("physical_runs")
                          else "PHYSICAL_RUN",
        "physical_runs": bundle.get("physical_runs", 0),
        "generalization_claimed": bool(bundle.get("generalization_claimed")),
        "compliance_claim": "HUMAN_ADMIT_REQUIRED",
        "metrics": metrics,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
        "exit_code": 0 if not failures else 2,
    }


def _canonical() -> dict[str, Any]:
    identities = {
        "fixture_identity": {"corpus_id": "ctl-ab-fixture", "artifact_digest": "sha256:" + "a" * 64},
        "profile_identity": {"pack_id": "ste-proposal-derived", "edition": "0.1-proposal-derived",
                             "pack_digest": "sha256:" + "b" * 64},
        "termbase_identity": {"artifact_digest": "sha256:" + "c" * 64},
        "model_identity": {"id": "fixture-model", "version": "1.0.0"},
        "harness_identity": {"id": "fixture-harness", "version": "1.0.0"},
        "environment_identity": {"id": "fixture-env", "version": "1.0.0"},
    }

    def result(case_id: str, *, passing: bool, **overrides: Any) -> dict[str, Any]:
        base = {
            "case_id": case_id,
            "deterministic_status": "PASS" if passing else "FAIL",
            "final_status": "PASS" if passing else "FAIL",
            "violations_found": [] if passing else ["V-BUDGET"],
            "expected_violations": [] if passing else ["V-BUDGET"],
            "span_valid": True,
            "warnings_preserved": True,
            "step_order_preserved": True,
            "meaning_preservation_score": 1.0 if passing else 0.5,
            "repair_attempts": 0,
            "repair_converged": False,
            "repair_stopped_no_improvement": False,
            "human_override": False,
            "human_review": {"generated_by_agent": False},
            "restricted": False,
            "execution_lane": "LOCAL_ONLY",
            "compliance_claim_made": False,
            "tokens_in": 100, "tokens_out": 50, "latency_ms": 10,
            "tool_calls": 1, "evaluator_calls": 2, "provider_calls": 0,
        }
        base.update(overrides)
        return base

    cases = ["procedural-budget", "descriptive-budget", "multiword-tn", "forbidden-token"]
    conditions = []
    for name in REQUIRED_CONDITIONS:
        # Negative arms must fail: they carry a planted defect.
        passing = name not in NEGATIVE_CONDITIONS
        results = []
        for case_id in cases:
            overrides: dict[str, Any] = {}
            if name == "restricted_external_attempt":
                overrides = {"restricted": True, "execution_lane": "LOCAL_ONLY"}
            if name == "lossy_document_rewrite":
                overrides = {"warnings_preserved": False, "step_order_preserved": False}
            if name == "missing_human_review":
                overrides = {"human_review": None}
            results.append(result(case_id, passing=passing, **overrides))
        conditions.append({
            "name": name,
            "skill_content_included": name == "candidate_skill" or name not in BASELINE_ARMS,
            "observed_budget": {"max_model_calls": 2, "max_tool_calls": 2,
                                "max_retries": 1, "seed": 7},
            "results": results,
        })

    return {
        "schema_version": SCHEMA,
        "experiment_id": "ctl-06-offline-canary",
        **identities,
        "evaluator_identities": [
            {"id": "check_exact_evidence", "version": "1.0.0",
             "artifact_digest": "sha256:" + "d" * 64}
        ],
        "budget": {"max_model_calls": 2, "max_tool_calls": 2, "max_retries": 1, "seed": 7},
        "declared_case_count": len(cases),
        "physical_runs": 0,
        "generalization_claimed": False,
        "compliance_claim": "HUMAN_ADMIT_REQUIRED",
        "conditions": conditions,
    }


def _selftest() -> int:
    import copy

    bundle = _canonical()
    try:
        receipt = evaluate(bundle)
    except Invalid as error:
        print(f"SELFTEST RED: canonical bundle refused: {error}", file=sys.stderr)
        return 2
    if receipt["status"] != "PASS":
        print(f"SELFTEST RED: canonical bundle failed: {receipt['failures']}", file=sys.stderr)
        return 2

    survived: list[str] = []

    def case(name: str, apply: Any) -> None:
        body = copy.deepcopy(_canonical())
        apply(body)
        try:
            result = evaluate(body)
        except Invalid:
            return
        if result["status"] != "PASS":
            return
        survived.append(name)

    def condition(body: dict[str, Any], name: str) -> dict[str, Any]:
        return next(item for item in body["conditions"] if item["name"] == name)

    case("evaluator changed between arms",
         lambda b: condition(b, "candidate_skill").__setitem__(
             "evaluator_identities", [{"id": "kinder", "version": "9.9.9",
                                       "artifact_digest": "sha256:" + "e" * 64}]))
    case("one arm given a larger budget",
         lambda b: condition(b, "candidate_skill")["observed_budget"].__setitem__(
             "max_retries", 5))
    case("one arm given more model calls",
         lambda b: condition(b, "candidate_skill")["observed_budget"].__setitem__(
             "max_model_calls", 9))
    case("one arm run on a different seed",
         lambda b: condition(b, "candidate_skill")["observed_budget"].__setitem__("seed", 99))
    case("prompt-only baseline given skill content",
         lambda b: condition(b, "prompt_only_baseline").__setitem__(
             "skill_content_included", True))
    case("no_skill baseline given skill content",
         lambda b: condition(b, "no_skill").__setitem__("skill_content_included", True))
    case("candidate arm without the skill content",
         lambda b: condition(b, "candidate_skill").__setitem__(
             "skill_content_included", False))
    case("failed condition dropped from the experiment",
         lambda b: b.__setitem__("conditions",
                                 [c for c in b["conditions"] if c["name"] != "wrong_profile"]))
    case("a case dropped from one arm",
         lambda b: condition(b, "candidate_skill")["results"].pop())
    case("declared case count larger than what was reported",
         lambda b: b.__setitem__("declared_case_count", 99))
    case("profile identity differing per arm",
         lambda b: condition(b, "candidate_skill").__setitem__(
             "profile_identity", {"pack_id": "other", "edition": "9",
                                  "pack_digest": "sha256:" + "f" * 64}))
    case("stale fixture identity in one arm",
         lambda b: condition(b, "no_skill").__setitem__(
             "fixture_identity", {"corpus_id": "old", "artifact_digest": "sha256:" + "9" * 64}))
    case("wrong profile arm passing anyway",
         lambda b: [r.update({"deterministic_status": "PASS", "final_status": "PASS"})
                    for r in condition(b, "wrong_profile")["results"]])
    case("stale termbase arm passing anyway",
         lambda b: [r.update({"deterministic_status": "PASS", "final_status": "PASS"})
                    for r in condition(b, "stale_termbase")["results"]])
    case("deterministic failure hidden by a final PASS",
         lambda b: condition(b, "candidate_skill")["results"][0].update(
             {"deterministic_status": "FAIL", "final_status": "PASS"}))
    case("warning loss hidden by a final PASS",
         lambda b: condition(b, "candidate_skill")["results"][0].update(
             {"warnings_preserved": False, "final_status": "PASS"}))
    case("step-order loss hidden by a final PASS",
         lambda b: condition(b, "candidate_skill")["results"][0].update(
             {"step_order_preserved": False, "final_status": "PASS"}))
    case("invalid source span with a final PASS",
         lambda b: condition(b, "candidate_skill")["results"][0].update(
             {"span_valid": False, "final_status": "PASS"}))
    case("restricted text sent externally",
         lambda b: condition(b, "restricted_external_attempt")["results"][0].update(
             {"restricted": True, "execution_lane": "EXTERNAL_APPROVED"}))
    case("human review fabricated by the agent",
         lambda b: condition(b, "candidate_skill")["results"][0].update(
             {"human_review": {"generated_by_agent": True}}))
    case("generalization claimed from a single run",
         lambda b: (b.__setitem__("generalization_claimed", True),
                    b.__setitem__("physical_runs", 1)))
    case("generalization claimed from no physical run",
         lambda b: b.__setitem__("generalization_claimed", True))
    case("compliance claimed for a proposal-derived profile",
         lambda b: b.__setitem__("compliance_claim", "ASD-STE100 Issue 9 compliant"))
    case("duplicate condition name",
         lambda b: b["conditions"].append(copy.deepcopy(b["conditions"][0])))
    case("evaluator identities absent",
         lambda b: b.__setitem__("evaluator_identities", []))
    case("budget missing a declared field",
         lambda b: b["budget"].pop("max_retries"))

    if survived:
        for name in survived:
            print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
        return 2

    print(f"SELFTEST GREEN: canonical A/B bundle scored; 26 experiment-validity "
          f"and result mutations refused")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    if args.selftest:
        return _selftest()
    if args.bundle is None:
        parser.error("--bundle or --selftest is required")

    try:
        bundle = load(args.bundle)
        receipt = evaluate(bundle)
    except Unusable as error:
        print(f"FATAL A/B input: {error}", file=sys.stderr)
        return 64
    except Invalid as error:
        # No metric is emitted: a number from an invalid experiment reads as
        # evidence and is worse than no number.
        print(f"AB EXPERIMENT INVALID: {error}", file=sys.stderr)
        return 2

    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    if receipt["failures"]:
        for failure in receipt["failures"]:
            print(f"AB GATE RED: {failure}", file=sys.stderr)
    return receipt["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
