#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AGENT_CONTRACT = ROOT / "evals" / "agent-effectiveness-contract.json"
PROCEDURE_CONTRACT = ROOT / "evals" / "contract.json"
MAIN_PROFILES = (
    "no_skill",
    "current_full_composition",
    "candidate_trimmed_skill",
)


class ExperimentError(RuntimeError):
    pass


def canonical_digest(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def get_path(value: dict[str, Any], dotted: str) -> Any:
    current: Any = value
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ExperimentError(
                f"receipt is missing matching field {dotted}"
            )
        current = current[part]
    return current


def validate_digest(value: Any, name: str, length: int = 64) -> None:
    if (
        not isinstance(value, str)
        or len(value) != length
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ExperimentError(
            f"{name} must be lowercase hexadecimal with length {length}"
        )


def validate_receipt(
    receipt: Any,
    contract: dict[str, Any],
    source: Path,
) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ExperimentError(f"{source}: receipt must be a JSON object")
    required_top = {
        "schema",
        "receipt_id",
        "receipt_digest",
        "agent_class",
        "profile",
        "case_id",
        "repository_id",
        "repository_subject",
        "repetition",
        "arm_order",
        "task_digest",
        "treatment_digest",
        "evaluator_digest",
        "agent",
        "runtime",
        "budgets",
        "evaluator",
        "agent_run",
        "evaluator_run",
        "metrics",
        "artifacts",
    }
    missing = sorted(required_top - set(receipt))
    if missing:
        raise ExperimentError(
            f"{source}: missing top-level fields {missing}"
        )
    if receipt["schema"] != "repository-capability-audit-agent-run/v1":
        raise ExperimentError(f"{source}: unsupported receipt schema")
    if receipt["agent_class"] not in contract["agent_classes"]:
        raise ExperimentError(f"{source}: unsupported agent_class")
    if not isinstance(receipt["repetition"], int) or receipt["repetition"] < 1:
        raise ExperimentError(
            f"{source}: repetition must be a positive integer"
        )
    if not isinstance(receipt["arm_order"], int) or receipt["arm_order"] < 0:
        raise ExperimentError(
            f"{source}: arm_order must be a non-negative integer"
        )
    validate_digest(receipt["task_digest"], f"{source}: task_digest")
    validate_digest(
        receipt["treatment_digest"],
        f"{source}: treatment_digest",
    )
    validate_digest(
        receipt["evaluator_digest"],
        f"{source}: evaluator_digest",
    )
    validate_digest(
        receipt["runtime"].get("toolset_digest"),
        f"{source}: toolset_digest",
    )
    validate_digest(
        receipt["repository_subject"].get("commit"),
        f"{source}: commit",
        40,
    )
    validate_digest(
        receipt["repository_subject"].get("tree"),
        f"{source}: tree",
        40,
    )
    if receipt["evaluator"].get("owner") != "independent":
        raise ExperimentError(
            f"{source}: evaluator must be independently owned"
        )
    if receipt["evaluator_run"].get("exit_code") != 0:
        raise ExperimentError(
            f"{source}: evaluator command did not exit zero"
        )
    required_metrics = set(contract["required_metrics"])
    metrics = receipt["metrics"]
    if not isinstance(metrics, dict) or set(metrics) != required_metrics:
        missing_metrics = (
            sorted(required_metrics - set(metrics))
            if isinstance(metrics, dict)
            else sorted(required_metrics)
        )
        extra_metrics = (
            sorted(set(metrics) - required_metrics)
            if isinstance(metrics, dict)
            else []
        )
        raise ExperimentError(
            f"{source}: metrics fields differ: "
            f"missing={missing_metrics} extra={extra_metrics}"
        )
    expected = canonical_digest(
        {key: value for key, value in receipt.items() if key != "receipt_digest"}
    )
    if receipt["receipt_digest"] != expected:
        raise ExperimentError(f"{source}: receipt digest mismatch")
    if not isinstance(receipt["artifacts"], list) or not receipt["artifacts"]:
        raise ExperimentError(f"{source}: artifact manifest is absent")
    seen_paths: set[str] = set()
    for item in receipt["artifacts"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "sha256", "bytes"}
        ):
            raise ExperimentError(
                f"{source}: invalid artifact manifest entry"
            )
        if item["path"] in seen_paths:
            raise ExperimentError(f"{source}: duplicate artifact path")
        seen_paths.add(item["path"])
        validate_digest(item["sha256"], f"{source}: artifact digest")
        if not isinstance(item["bytes"], int) or item["bytes"] < 0:
            raise ExperimentError(
                f"{source}: artifact bytes must be non-negative"
            )
    return receipt


def quality_components(metrics: dict[str, Any]) -> dict[str, float]:
    defects_total = metrics["material_defects_total"]
    false_pass_total = metrics["false_pass_opportunities"]
    return {
        "task_success": 1.0 if metrics["task_success"] else 0.0,
        "defect_recall": (
            metrics["material_defects_found"] / defects_total
            if defects_total
            else 1.0
        ),
        "false_pass_avoidance": (
            1.0 - metrics["false_pass_count"] / false_pass_total
            if false_pass_total
            else 1.0
        ),
        "evidence_packet_complete": (
            1.0 if metrics["evidence_packet_complete"] else 0.0
        ),
        "exact_subject_continuity": (
            1.0 if metrics["exact_subject_continuity"] else 0.0
        ),
        "negative_control_valid": (
            1.0 if metrics["negative_control_valid"] else 0.0
        ),
        "explicit_non_claim_accuracy": (
            1.0 if metrics["explicit_non_claim_accuracy"] else 0.0
        ),
        "trigger_correct": 1.0 if metrics["trigger_correct"] else 0.0,
    }


def quality_score(
    metrics: dict[str, Any],
    weights: dict[str, float],
) -> float:
    components = quality_components(metrics)
    return round(
        sum(components[name] * weight for name, weight in weights.items()),
        9,
    )


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def paired_bootstrap(
    differences: list[float],
    *,
    samples: int,
    seed: int,
) -> dict[str, float]:
    if not differences:
        raise ExperimentError(
            "paired comparison has no matched differences"
        )
    rng = random.Random(seed)
    means = []
    for _ in range(samples):
        draw = [
            differences[rng.randrange(len(differences))]
            for _ in differences
        ]
        means.append(statistics.fmean(draw))
    return {
        "pairs": len(differences),
        "mean": round(statistics.fmean(differences), 9),
        "ci95_low": round(percentile(means, 0.025), 9),
        "ci95_high": round(percentile(means, 0.975), 9),
    }


def profile_metrics(
    receipts: list[dict[str, Any]],
    weights: dict[str, float],
) -> dict[str, Any]:
    metrics = [item["metrics"] for item in receipts]
    components = [quality_components(value) for value in metrics]
    return {
        "runs": len(receipts),
        "quality_score": round(
            statistics.fmean(
                quality_score(value, weights) for value in metrics
            ),
            9,
        ),
        "task_success_rate": round(
            statistics.fmean(
                1.0 if value["task_success"] else 0.0
                for value in metrics
            ),
            9,
        ),
        "defect_recall": round(
            sum(value["material_defects_found"] for value in metrics)
            / max(
                1,
                sum(value["material_defects_total"] for value in metrics),
            ),
            9,
        ),
        "false_pass_count": sum(
            value["false_pass_count"] for value in metrics
        ),
        "false_pass_opportunities": sum(
            value["false_pass_opportunities"] for value in metrics
        ),
        "evidence_packet_complete_rate": round(
            statistics.fmean(
                value["evidence_packet_complete"] for value in metrics
            ),
            9,
        ),
        "exact_subject_continuity_rate": round(
            statistics.fmean(
                value["exact_subject_continuity"] for value in metrics
            ),
            9,
        ),
        "negative_control_valid_rate": round(
            statistics.fmean(
                value["negative_control_valid"] for value in metrics
            ),
            9,
        ),
        "explicit_non_claim_accuracy_rate": round(
            statistics.fmean(
                value["explicit_non_claim_accuracy"] for value in metrics
            ),
            9,
        ),
        "trigger_precision": round(
            statistics.fmean(
                value["trigger_correct"] for value in metrics
            ),
            9,
        ),
        "mean_tool_calls": round(
            statistics.fmean(value["tool_calls"] for value in metrics),
            3,
        ),
        "mean_input_tokens": round(
            statistics.fmean(value["input_tokens"] for value in metrics),
            3,
        ),
        "mean_output_tokens": round(
            statistics.fmean(value["output_tokens"] for value in metrics),
            3,
        ),
        "mean_duration_ms": round(
            statistics.fmean(value["duration_ms"] for value in metrics),
            3,
        ),
        "mean_cost_usd": round(
            statistics.fmean(float(value["cost_usd"]) for value in metrics),
            9,
        ),
        "component_means": {
            name: round(
                statistics.fmean(item[name] for item in components),
                9,
            )
            for name in sorted(components[0])
        },
    }


def cell_key(
    receipt: dict[str, Any],
    matching_fields: list[str],
) -> tuple[Any, ...]:
    return tuple(get_path(receipt, name) for name in matching_fields)


def base_cell_key(
    receipt: dict[str, Any],
    matching_fields: list[str],
) -> tuple[Any, ...]:
    return tuple(
        get_path(receipt, name)
        for name in matching_fields
        if name != "repetition"
    )


def source_effectiveness(
    procedure_contract: dict[str, Any],
    supported_rules: set[str],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    dependency_supported = 0
    dependency_total = 0
    for source, claims in procedure_contract["source_claims"].items():
        supported = sum(claim in supported_rules for claim in claims)
        total = len(claims)
        result[source] = {
            "live_supported": supported,
            "candidate_claims": total,
            "live_supported_fraction": round(supported / total, 6),
        }
        if source != "current-system-prompt":
            dependency_supported += supported
            dependency_total += total
    result["dependency_aggregate"] = {
        "live_supported": dependency_supported,
        "candidate_claims": dependency_total,
        "live_supported_fraction": round(
            dependency_supported / dependency_total,
            6,
        ),
    }
    return result


def score_live(
    receipts: list[dict[str, Any]],
    contract: dict[str, Any],
    procedure_contract: dict[str, Any],
) -> dict[str, Any]:
    weights = contract["quality_weights"]
    acceptance = contract["acceptance"]
    matching_fields = contract["matching_fields"]
    by_cell: dict[
        tuple[Any, ...],
        dict[str, dict[str, Any]],
    ] = defaultdict(dict)
    treatment_digests: dict[str, set[str]] = defaultdict(set)
    for receipt in receipts:
        key = cell_key(receipt, matching_fields)
        profile = receipt["profile"]
        if profile in by_cell[key]:
            raise ExperimentError(
                f"duplicate profile {profile!r} in a matched cell"
            )
        by_cell[key][profile] = receipt
        treatment_digests[profile].add(receipt["treatment_digest"])
    for profile, digests in treatment_digests.items():
        if len(digests) != 1:
            raise ExperimentError(
                f"profile {profile!r} changed treatment digest "
                "inside the experiment"
            )

    main_cells: list[dict[str, dict[str, Any]]] = []
    for key, profiles in by_cell.items():
        main_present = [profile in profiles for profile in MAIN_PROFILES]
        if any(main_present) and not all(main_present):
            raise ExperimentError(
                f"matched cell is missing a main treatment arm: {key}"
            )
        if all(main_present):
            main_cells.append(profiles)
    if not main_cells:
        raise ExperimentError(
            "no complete no-skill/full/trimmed matched cells"
        )

    by_base: dict[tuple[Any, ...], set[int]] = defaultdict(set)
    for receipt in receipts:
        if receipt["profile"] in MAIN_PROFILES:
            by_base[
                base_cell_key(receipt, matching_fields)
            ].add(receipt["repetition"])
    repetitions_ok = all(
        len(values) >= acceptance["minimum_repetitions_per_cell"]
        for values in by_base.values()
    )
    families = {receipt["agent"]["family"] for receipt in receipts}
    repositories = {receipt["repository_id"] for receipt in receipts}
    sample_ok = (
        repetitions_ok
        and len(families) >= acceptance["minimum_model_families"]
        and len(repositories)
        >= acceptance["minimum_held_out_repositories"]
    )

    by_profile: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for receipt in receipts:
        by_profile[receipt["profile"]].append(receipt)
    profile_report = {
        profile: profile_metrics(values, weights)
        for profile, values in sorted(by_profile.items())
    }

    candidate_no_skill = [
        quality_score(
            cell["candidate_trimmed_skill"]["metrics"],
            weights,
        )
        - quality_score(cell["no_skill"]["metrics"], weights)
        for cell in main_cells
    ]
    candidate_full = [
        quality_score(
            cell["candidate_trimmed_skill"]["metrics"],
            weights,
        )
        - quality_score(
            cell["current_full_composition"]["metrics"],
            weights,
        )
        for cell in main_cells
    ]
    samples = acceptance["bootstrap_samples"]
    seed = acceptance["bootstrap_seed"]
    uplift = paired_bootstrap(
        candidate_no_skill,
        samples=samples,
        seed=seed,
    )
    equivalence = paired_bootstrap(
        candidate_full,
        samples=samples,
        seed=seed + 1,
    )

    uplift_policy = acceptance["candidate_vs_no_skill"]
    candidate_false_passes = profile_report[
        "candidate_trimmed_skill"
    ]["false_pass_count"]
    baseline_false_passes = profile_report["no_skill"][
        "false_pass_count"
    ]
    uplift_pass = (
        uplift["mean"]
        >= uplift_policy["minimum_mean_quality_uplift"]
    )
    if uplift_policy["require_positive_ci_lower_bound"]:
        uplift_pass = uplift_pass and uplift["ci95_low"] > 0
    if uplift_policy["false_passes_must_not_increase"]:
        uplift_pass = (
            uplift_pass
            and candidate_false_passes <= baseline_false_passes
        )

    margin = acceptance["candidate_vs_full"]["equivalence_margin"]
    equivalence_pass = (
        equivalence["ci95_low"] >= -margin
        and equivalence["ci95_high"] <= margin
    )

    retained_rules = [
        item["id"] for item in procedure_contract["retained"]
    ]
    rule_policy = acceptance["rule_retention"]
    rules: dict[str, Any] = {}
    live_supported: set[str] = set()
    for index, rule_id in enumerate(retained_rules):
        ablation_profile = f"candidate_minus_{rule_id}"
        differences = []
        for profiles in by_cell.values():
            if (
                "candidate_trimmed_skill" in profiles
                and ablation_profile in profiles
            ):
                differences.append(
                    quality_score(
                        profiles["candidate_trimmed_skill"]["metrics"],
                        weights,
                    )
                    - quality_score(
                        profiles[ablation_profile]["metrics"],
                        weights,
                    )
                )
        if not differences:
            rules[rule_id] = {
                "state": "NOT_EXERCISED",
                "matched_pairs": 0,
            }
            continue
        comparison = paired_bootstrap(
            differences,
            samples=samples,
            seed=seed + 100 + index,
        )
        enough = (
            comparison["pairs"]
            >= rule_policy["minimum_matched_pairs"]
        )
        supported = (
            enough
            and comparison["mean"]
            >= rule_policy["minimum_mean_quality_delta"]
        )
        if rule_policy["require_positive_ci_lower_bound"]:
            supported = supported and comparison["ci95_low"] > 0
        state = (
            "SUPPORTED"
            if supported
            else (
                "INSUFFICIENT_SAMPLE"
                if not enough
                else "NOT_SUPPORTED"
            )
        )
        rules[rule_id] = {"state": state, **comparison}
        if supported:
            live_supported.add(rule_id)

    if not sample_ok:
        admission_state = "INSUFFICIENT_SAMPLE"
    elif uplift_pass and equivalence_pass:
        admission_state = "SUPPORTED"
    else:
        admission_state = "NOT_SUPPORTED"

    return {
        "admission_state": admission_state,
        "sample_gate": {
            "passed": sample_ok,
            "model_families": sorted(families),
            "held_out_repositories": sorted(repositories),
            "base_cells": len(by_base),
            "minimum_repetitions_per_cell": acceptance[
                "minimum_repetitions_per_cell"
            ],
            "repetitions_gate_passed": repetitions_ok,
        },
        "profiles": profile_report,
        "comparisons": {
            "candidate_vs_no_skill": {
                **uplift,
                "passed": uplift_pass,
                "minimum_mean_quality_uplift": uplift_policy[
                    "minimum_mean_quality_uplift"
                ],
                "candidate_false_passes": candidate_false_passes,
                "no_skill_false_passes": baseline_false_passes,
            },
            "candidate_vs_full": {
                **equivalence,
                "passed": equivalence_pass,
                "equivalence_margin": margin,
            },
        },
        "rule_effectiveness": rules,
        "live_supported_rules": sorted(live_supported),
        "source_effectiveness": source_effectiveness(
            procedure_contract,
            live_supported,
        ),
        "treatment_digests": {
            profile: sorted(values)[0]
            for profile, values in sorted(treatment_digests.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score matched held-out Agent A/B receipts"
    )
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    contract = read_json(AGENT_CONTRACT)
    procedure_contract = read_json(PROCEDURE_CONTRACT)
    receipt_paths = (
        sorted(args.receipts.rglob("*.json"))
        if args.receipts.exists()
        else []
    )
    base_report: dict[str, Any] = {
        "schema": "repository-capability-audit-agent-effectiveness/v1",
        "contract_digest": canonical_digest(contract),
        "procedure_contract_digest": canonical_digest(
            procedure_contract
        ),
        "receipt_count": len(receipt_paths),
        "limitations": [
            "Deterministic fixture Agents validate only the harness.",
            "Live support is bounded to matched held-out repositories, models, runtimes and budgets in the receipts.",
            "Semantic procedure overlap prevents source percentages from being interpreted as additive causality.",
        ],
    }
    if not receipt_paths:
        report = {
            **base_report,
            "admission_state": "NOT_EXERCISED",
            "fixture_receipts": 0,
            "live_receipts": 0,
        }
        write_json(args.output, report)
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0

    failures: list[str] = []
    receipts: list[dict[str, Any]] = []
    for path in receipt_paths:
        try:
            receipts.append(
                validate_receipt(read_json(path), contract, path)
            )
        except (
            ExperimentError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            failures.append(str(exc))
    if failures:
        report = {
            **base_report,
            "admission_state": "INVALID_EXPERIMENT",
            "validation_failures": failures,
        }
        write_json(args.output, report)
        print(json.dumps(report, sort_keys=True, indent=2))
        return 2

    fixture = [
        item
        for item in receipts
        if item["agent_class"] == "deterministic_fixture"
    ]
    live = [
        item
        for item in receipts
        if item["agent_class"] == "language_model_agent"
    ]
    if not live:
        report = {
            **base_report,
            "admission_state": "HARNESS_SELFTEST_ONLY",
            "fixture_receipts": len(fixture),
            "live_receipts": 0,
            "fixture_profiles": sorted(
                {item["profile"] for item in fixture}
            ),
        }
        write_json(args.output, report)
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0

    try:
        live_report = score_live(
            live,
            contract,
            procedure_contract,
        )
        report = {
            **base_report,
            **live_report,
            "fixture_receipts": len(fixture),
            "live_receipts": len(live),
        }
        write_json(args.output, report)
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0 if report["admission_state"] == "SUPPORTED" else 3
    except ExperimentError as exc:
        report = {
            **base_report,
            "admission_state": "INVALID_EXPERIMENT",
            "fixture_receipts": len(fixture),
            "live_receipts": len(live),
            "validation_failures": [str(exc)],
        }
        write_json(args.output, report)
        print(json.dumps(report, sort_keys=True, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
