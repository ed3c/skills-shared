#!/usr/bin/env python3
"""Publish overlap-aware source-skill contribution accounting (#233).

Exit codes:
  0   generated, or the committed outputs match a fresh generation exactly
  2   the committed outputs have drifted from what the inputs generate
  64  missing, unreadable, or self-contradicting input

Two failure shapes this exists to make impossible:

  1. A hand-maintained percentage table that drifts from `evals/contract.json`.
     Every Layer A number here is derived, so the table cannot disagree with the
     contract it claims to summarise.
  2. A Layer B state promoted by editing a word. A supported live state is
     refused unless `evals/live-evidence-state.json` names the qualifying pairs
     and their receipt files exist with matching digests.

Source Skills overlap: several sources map to one retained rule, and one source
claim can carry several obligations. So this reports three denominators side by
side -- unique retained rules, unique semantic claims, and source mappings --
and never adds two sources' fractions together.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

CONTRACT_SCHEMA = "repository-capability-audit-eval-contract/v1"
STATE_SCHEMA = "rca-live-evidence-state/v1"
REPORT_SCHEMA = "rca-live-source-contribution/v1"
OVERLAP_SCHEMA = "rca-rule-to-source-overlap/v1"
INDEX_SCHEMA = "rca-receipt-index/v1"

DRIFT = 2
INVALID = 64

LAYER_A_STATES = ("RUNTIME_SUPPORTED", "UNPROVEN_FOR_CORE", "NOT_MAPPED_TO_CORE")
LAYER_B_STATES = (
    "LIVE_SUPPORTED_MAPPING",
    "CONTEXT_DEPENDENT",
    "LIVE_NOT_SUPPORTED",
    "INSUFFICIENT_SAMPLE",
    "NOT_EXERCISED",
    "UNPROVEN_FOR_CORE",
)
RULE_LIVE_STATES = (
    "NOT_EXERCISED",
    "INSUFFICIENT_SAMPLE",
    "INVALID_EXPERIMENT",
    "LIVE_MODEL_NOT_SUPPORTED",
    "LIVE_MODEL_SUPPORTED",
    "CONTEXT_DEPENDENT",
)
# Only these assert that a model's behaviour changed. They are the ones that
# must be paid for with receipts.
RULE_STATES_REQUIRING_PAIRS = ("LIVE_MODEL_SUPPORTED", "LIVE_MODEL_NOT_SUPPORTED", "CONTEXT_DEPENDENT")

GENERATED = (
    "evals/live-source-contribution.json",
    "evals/live-source-contribution.md",
    "evals/rule-to-source-overlap.json",
    "evals/receipt-index.json",
)
# Authored, not generated, but published as part of the same packet, so its bytes
# are pinned by the same SHA256SUMS.
PINNED = ("modules/measurement-limits.md",)
SUMS_PATH = "evals/SHA256SUMS"

NON_CLAIMS = [
    "a source fraction is the share of that source's semantic claims with qualifying mapped evidence in this audit niche; it is not a Shapley value, a percentage of prose effectiveness, or a model-weight attribution",
    "source fractions overlap and must never be summed into a total contribution",
    "a Layer A deciding delta shows a procedure is necessary for the committed fixtures; it does not show a model read the text",
    "behaviour already present in the matched no_skill arm is not credited to any Skill source",
    "no word, token, or mention count appears in any number here",
    "a claim with no retained rule cannot reach a live state, because there is nothing to ablate",
]


class Invalid(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Invalid(f"absent-input: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Invalid(f"unreadable-input: {path}: {exc}") from exc


def digest_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def validate_state(state: dict, retained_ids: list[str], root: Path) -> None:
    """Refuse a state file that claims more than its receipts pay for."""
    if state.get("schema") != STATE_SCHEMA:
        raise Invalid(f"schema-mismatch: {state.get('schema')!r} != {STATE_SCHEMA!r}")

    rules = state.get("rules")
    if not isinstance(rules, dict):
        raise Invalid("malformed-state: rules must be an object")
    declared = sorted(rules)
    if declared != sorted(retained_ids):
        missing = sorted(set(retained_ids) - set(declared))
        extra = sorted(set(declared) - set(retained_ids))
        raise Invalid(f"rule-set-mismatch: missing={missing} extra={extra}")

    required_pairs = state["lanes"]["230_rule_ablation"].get("required_pairs_per_rule", 2)
    for rule_id in declared:
        entry = rules[rule_id]
        live = entry.get("live_state")
        if live not in RULE_LIVE_STATES:
            raise Invalid(f"unknown-live-state: {rule_id} {live!r}")
        pairs = entry.get("pairs", [])
        if not isinstance(pairs, list):
            raise Invalid(f"malformed-pairs: {rule_id}")
        if live in RULE_STATES_REQUIRING_PAIRS and len(pairs) < required_pairs:
            raise Invalid(
                f"unpaid-live-state: {rule_id} declares {live} with {len(pairs)} matched "
                f"pair(s); {required_pairs} are required"
            )
        for pair in pairs:
            receipt = root / pair.get("receipt", "")
            if not receipt.is_file():
                raise Invalid(f"absent-pair-receipt: {rule_id} {pair.get('receipt')!r}")
            actual = digest_file(receipt)
            if pair.get("sha256") and pair["sha256"] != actual:
                raise Invalid(f"pair-receipt-digest-mismatch: {rule_id} {pair['receipt']}")

    lane = state["lanes"]["233_source_contribution"].get("state")
    any_live = any(
        rules[rule_id]["live_state"] == "LIVE_MODEL_SUPPORTED" for rule_id in declared
    )
    expected_lane = "LIVE_PARTIAL" if any_live else "LAYER_A_ONLY"
    if lane != expected_lane:
        raise Invalid(f"lane-state-mismatch: 233 declares {lane!r} but rules imply {expected_lane!r}")

    for receipt in state.get("receipts", []):
        if not (root / receipt["path"]).is_file():
            raise Invalid(f"absent-receipt: {receipt['path']}")


def layer_a_state(claim: str, retained: set[str], unproven: set[str]) -> str:
    if claim in retained:
        return "RUNTIME_SUPPORTED"
    if claim in unproven:
        return "UNPROVEN_FOR_CORE"
    return "NOT_MAPPED_TO_CORE"


def layer_b_state(mapped: list[str], rules: dict, matrix_state: str) -> str:
    if not mapped:
        return "UNPROVEN_FOR_CORE"
    live = {rules[rule_id]["live_state"] for rule_id in mapped}
    if live == {"LIVE_MODEL_SUPPORTED"}:
        return "LIVE_SUPPORTED_MAPPING"
    if "LIVE_MODEL_NOT_SUPPORTED" in live:
        return "LIVE_NOT_SUPPORTED"
    if "CONTEXT_DEPENDENT" in live:
        return "CONTEXT_DEPENDENT"
    if "INSUFFICIENT_SAMPLE" in live or matrix_state == "INSUFFICIENT_SAMPLE":
        return "INSUFFICIENT_SAMPLE"
    return "NOT_EXERCISED"


def build(contract: dict, state: dict) -> dict[str, str]:
    retained_ids = [rule["id"] for rule in contract["retained"]]
    retained = set(retained_ids)
    unproven = {rule["id"] for rule in contract["unproven_for_core"]}
    source_claims: dict[str, list[str]] = contract["source_claims"]
    rules = state["rules"]
    matrix_state = state["lanes"]["228_matrix"]["state"]

    # Which sources name each claim. This is the overlap, and it is why no two
    # source fractions may be added.
    namers: dict[str, list[str]] = {}
    for source, claims in source_claims.items():
        for claim in claims:
            namers.setdefault(claim, []).append(source)
    for claim in namers:
        namers[claim].sort()

    overlap_rules = {}
    for rule_id in retained_ids:
        sources = namers.get(rule_id, [])
        overlap_rules[rule_id] = {
            "sources": sources,
            "source_count": len(sources),
            "overlap_group": "+".join(sources) if sources else "UNMAPPED",
            "layer_a_state": "RUNTIME_SUPPORTED",
            "layer_b_state": _rule_layer_b(rules[rule_id]["live_state"]),
        }
    groups: dict[str, dict] = {}
    for rule_id, entry in overlap_rules.items():
        group = groups.setdefault(
            entry["overlap_group"], {"sources": entry["sources"], "rules": []}
        )
        group["rules"].append(rule_id)
    for group in groups.values():
        group["rules"].sort()
        group["rule_count"] = len(group["rules"])

    sources_out = {}
    for source in sorted(source_claims):
        claims_out = []
        for claim in sorted(source_claims[source]):
            mapped = [claim] if claim in retained else []
            shared_with = [other for other in namers[claim] if other != source]
            claims_out.append(
                {
                    "claim_id": claim,
                    "mapped_rule_ids": mapped,
                    "overlap_group": "+".join(namers[claim]),
                    "shared_with_sources": shared_with,
                    "isolable": not shared_with,
                    "layer_a_state": layer_a_state(claim, retained, unproven),
                    "layer_b_state": layer_b_state(mapped, rules, matrix_state),
                }
            )
        supported = [c for c in claims_out if c["layer_a_state"] == "RUNTIME_SUPPORTED"]
        isolated = [c for c in supported if c["isolable"]]
        sources_out[source] = {
            "claims": claims_out,
            "candidate_claims": len(claims_out),
            "layer_a_supported_claims": len(supported),
            "layer_a_fraction": _fraction(len(supported), len(claims_out)),
            "layer_a_isolable_lower_bound": len(isolated),
            "layer_a_upper_bound": len(supported),
            "bound_reason": (
                "lower bound counts only supported claims no other source names; upper "
                "bound counts every supported claim including shared ones. Isolating the "
                "difference needs grouped or factorial ablations that have not run."
            ),
            "layer_b_supported_claims": len(
                [c for c in claims_out if c["layer_b_state"] == "LIVE_SUPPORTED_MAPPING"]
            ),
            "layer_b_fraction": _fraction(
                len([c for c in claims_out if c["layer_b_state"] == "LIVE_SUPPORTED_MAPPING"]),
                len(claims_out),
            ),
        }

    dependency_sources = [s for s in sorted(source_claims) if s != "current-system-prompt"]
    denominators = {
        "unique_retained_rules": len(retained_ids),
        "unique_semantic_claims": len(namers),
        "source_mappings": sum(len(v) for v in source_claims.values()),
        "dependency_source_mappings": sum(len(source_claims[s]) for s in dependency_sources),
        "dependency_supported_mappings": sum(
            sources_out[s]["layer_a_supported_claims"] for s in dependency_sources
        ),
        "_rule": "These four are different questions with different answers. None of them may be substituted for another, and none is a total of the per-source fractions.",
    }

    report = {
        "schema": REPORT_SCHEMA,
        "denominators": denominators,
        "layer_b_lane_states": {
            key: value["state"] for key, value in sorted(state["lanes"].items())
        },
        "non_claims": NON_CLAIMS,
        "sources": sources_out,
    }
    overlap = {
        "schema": OVERLAP_SCHEMA,
        "groups": dict(sorted(groups.items())),
        "rules": overlap_rules,
        "_rule": "A rule named by several sources cannot have its credit split by this file. The group is the unit that the current evidence can address.",
    }
    index = {
        "schema": INDEX_SCHEMA,
        "github_hosted_execution": state["github_hosted_execution"],
        "receipts": state["receipts"],
    }
    return {
        "evals/live-source-contribution.json": dumps(report),
        "evals/rule-to-source-overlap.json": dumps(overlap),
        "evals/receipt-index.json": dumps(index),
        "evals/live-source-contribution.md": render_markdown(report, state),
    }


def _rule_layer_b(live: str) -> str:
    return "LIVE_SUPPORTED_MAPPING" if live == "LIVE_MODEL_SUPPORTED" else live


def _fraction(numerator: int, denominator: int) -> str:
    """A string, so nothing downstream can average or sum these."""
    if denominator == 0:
        return "0/0 UNDEFINED"
    return f"{numerator}/{denominator}"


def render_markdown(report: dict, state: dict) -> str:
    lines = [
        "# Live source contribution",
        "",
        "Generated by `scripts/publish_source_contribution.py`. Do not edit: the suite",
        "regenerates this and fails on drift.",
        "",
        "## Denominators, kept apart",
        "",
        "| Denominator | Count |",
        "|---|---:|",
    ]
    for key, value in report["denominators"].items():
        if key.startswith("_"):
            continue
        lines.append(f"| {key.replace('_', ' ')} | {value} |")
    lines += [
        "",
        report["denominators"]["_rule"],
        "",
        "## Per source",
        "",
        "| Source | Claims | Layer A supported | Layer A fraction | Isolable lower bound | Layer B supported |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for source, entry in report["sources"].items():
        lines.append(
            f"| {source} | {entry['candidate_claims']} | {entry['layer_a_supported_claims']} "
            f"| {entry['layer_a_fraction']} | {entry['layer_a_isolable_lower_bound']} "
            f"| {entry['layer_b_supported_claims']} |"
        )
    lines += [
        "",
        "The Layer A fraction is a count of semantic claims, printed as a ratio so it",
        "cannot be averaged with another source's. The isolable lower bound counts only",
        "claims no other source names; everything between it and the supported count is",
        "shared credit this evidence cannot split.",
        "",
        "## Layer B lane states",
        "",
        "| Lane | Issue | State |",
        "|---|---|---|",
    ]
    for key, lane in sorted(state["lanes"].items()):
        lines.append(f"| {key} | {lane['issue']} | {lane['state']} |")
    lines += ["", "## Non-claims", ""]
    lines += [f"- {claim};" for claim in report["non_claims"][:-1]]
    lines.append(f"- {report['non_claims'][-1]}.")
    lines.append("")
    lines.append("Measurement limits: [`../modules/measurement-limits.md`](../modules/measurement-limits.md).")
    lines.append("")
    return "\n".join(lines)


def sums_text(root: Path, generated: dict[str, str]) -> str:
    rows = []
    for name in sorted(generated) + list(PINNED):
        if name in generated:
            payload = generated[name].encode("utf-8")
        else:
            path = root / name
            if not path.is_file():
                raise Invalid(f"absent-pinned-file: {name}")
            payload = path.read_bytes()
        rows.append(f"{hashlib.sha256(payload).hexdigest()}  {name}\n")
    return "".join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", required=True, type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate in memory and exit 2 if the committed outputs differ",
    )
    args = parser.parse_args(argv)
    root: Path = args.skill_root

    try:
        contract = load_json(root / "evals/contract.json")
        if contract.get("schema") != CONTRACT_SCHEMA:
            raise Invalid(f"schema-mismatch: {contract.get('schema')!r}")
        state = load_json(root / "evals/live-evidence-state.json")
        validate_state(state, [rule["id"] for rule in contract["retained"]], root)
        generated = build(contract, state)
        generated[SUMS_PATH] = sums_text(root, generated)
    except Invalid as exc:
        print(f"SOURCE-CONTRIBUTION-INVALID {exc}", file=sys.stderr)
        return INVALID
    except KeyError as exc:
        print(f"SOURCE-CONTRIBUTION-INVALID missing-field: {exc}", file=sys.stderr)
        return INVALID

    if args.check:
        drifted = []
        for name, text in sorted(generated.items()):
            path = root / name
            if not path.is_file():
                drifted.append(f"absent: {name}")
            elif path.read_text(encoding="utf-8") != text:
                drifted.append(f"stale: {name}")
        if drifted:
            for problem in drifted:
                print(f"SOURCE-CONTRIBUTION-RED {problem}", file=sys.stderr)
            return DRIFT
        print(
            f"SOURCE-CONTRIBUTION-GREEN files={len(generated)} "
            f"rules={len(contract['retained'])} "
            f"sources={len(contract['source_claims'])} committed outputs match"
        )
        return 0

    for name, text in sorted(generated.items()):
        (root / name).write_text(text, encoding="utf-8")
    print(f"SOURCE-CONTRIBUTION-WRITTEN files={len(generated)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
