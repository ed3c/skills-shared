#!/usr/bin/env python3
"""Verify that every required subagent is terminal and preserved in one join receipt."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from portfolio_control_lib import assert_digest, bind_digest, duplicate_values, load_json, TERMINAL_AGENT_STATES


def verify(join: dict[str, Any], results: list[dict[str, Any]], schema: dict[str, Any] | None = None) -> None:
    if schema is not None:
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(join))
        if errors:
            raise ValueError("shape: " + "; ".join(error.message for error in errors))
    assert_digest(join, label="subagent-join")

    required = join["required_dispatch_digests"]
    if duplicate_values(required):
        raise ValueError("required dispatch denominator contains duplicates")
    required_set = set(required)

    result_by_digest: dict[str, dict[str, Any]] = {}
    for result in results:
        assert_digest(result, label="subagent-result")
        if result["digest"] in result_by_digest:
            raise ValueError(f"duplicate result digest {result['digest']}")
        if result["state"] not in TERMINAL_AGENT_STATES:
            raise ValueError(f"nonterminal result state {result['state']}")
        result_by_digest[result["digest"]] = result

    rows = join["results"]
    row_dispatches = [row["dispatch_digest"] for row in rows]
    row_result_digests = [row["result_digest"] for row in rows]
    if duplicate_values(row_dispatches):
        raise ValueError("join contains duplicate dispatch result")
    if duplicate_values(row_result_digests):
        raise ValueError("join reuses one result for multiple dispatches")

    observed_dispatches = set(row_dispatches)
    expected_missing = sorted(required_set - observed_dispatches)
    if sorted(join["missing"]) != expected_missing:
        raise ValueError(f"missing denominator mismatch: expected {expected_missing}")
    extras = observed_dispatches - required_set
    if extras:
        raise ValueError(f"join contains unrequested dispatches: {sorted(extras)}")

    for row in rows:
        result = result_by_digest.get(row["result_digest"])
        if result is None:
            raise ValueError(f"join references absent result {row['result_digest']}")
        if result["dispatch_digest"] != row["dispatch_digest"]:
            raise ValueError("result dispatch identity mismatch")
        if result["state"] != row["state"]:
            raise ValueError("result terminal state mismatch")

    all_pass = all(row["state"] == "PASS" for row in rows)
    expected_verdict = (
        "JOIN_INCOMPLETE"
        if expected_missing
        else "PASS"
        if all_pass and not join["contradictions"]
        else "REJECT"
    )
    if join["verdict"] != expected_verdict:
        raise ValueError(f"verdict mismatch: expected {expected_verdict}, observed {join['verdict']}")
    if join["verdict"] == "PASS" and len(rows) != len(required):
        raise ValueError("PASS before complete join")


def result(dispatch: str, state: str, suffix: str) -> dict[str, Any]:
    packet = {
        "schema": "subagent-result/v1",
        "dispatch_digest": dispatch,
        "state": state,
        "observed_base": {"repository": "ed3c/skills-shared", "commit": "1" * 40, "tree": "2" * 40},
        "result_subject": {"repository": "ed3c/skills-shared", "commit": "1" * 40, "tree": "2" * 40},
        "changed_paths": [],
        "commands": [],
        "lease_readback": {"exclusive_paths_respected": True, "forbidden_paths_untouched": True, "dirty_state": "CLEAN"},
        "findings": [suffix],
        "output_digests": [],
        "cleanup": {"processes": "NOT_APPLICABLE", "worktree": "NOT_APPLICABLE", "leases": "RELEASED", "residue": []},
        "claims_not_proven": ["live model quality"],
    }
    return bind_digest(packet)


def make_join(dispatches: list[str], results: list[dict[str, Any]], *, contradictions: list[str] | None = None, verdict: str = "PASS") -> dict[str, Any]:
    packet = {
        "schema": "subagent-join-receipt/v1",
        "epoch_digest": "9" * 64,
        "required_dispatch_digests": dispatches,
        "results": [
            {"dispatch_digest": item["dispatch_digest"], "result_digest": item["digest"], "state": item["state"]}
            for item in results
        ],
        "missing": sorted(set(dispatches) - {item["dispatch_digest"] for item in results}),
        "contradictions": contradictions or [],
        "dissent": [],
        "verdict": verdict,
        "consolidated_findings_digest": "8" * 64,
        "claims_not_proven": ["merge and release"],
    }
    return bind_digest(packet)


def selftest(schema: dict[str, Any] | None) -> None:
    d1, d2 = "1" * 64, "2" * 64
    r1, r2 = result(d1, "PASS", "explorer complete"), result(d2, "PASS", "auditor complete")
    positive = make_join([d1, d2], [r1, r2])
    verify(positive, [r1, r2], schema)

    mutations: list[tuple[str, dict[str, Any], list[dict[str, Any]]]] = []
    early = make_join([d1, d2], [r1], verdict="PASS")
    early["missing"] = [d2]
    mutations.append(("SUBAGENT_RESULT_ACCEPTED_BEFORE_JOIN", bind_digest(early), [r1]))

    dropped = make_join([d1, d2], [r1], verdict="PASS")
    dropped["missing"] = []
    mutations.append(("FAILED_OR_CANCELLED_AGENT_DROPPED_FROM_DENOMINATOR", bind_digest(dropped), [r1]))

    duplicate = copy.deepcopy(positive)
    duplicate["results"].append(copy.deepcopy(duplicate["results"][0]))
    mutations.append(("DUPLICATE_RESULT", bind_digest(duplicate), [r1, r2]))

    failed = result(d2, "FAIL", "first red")
    false_pass = make_join([d1, d2], [r1, failed], verdict="PASS")
    mutations.append(("FAILED_AGENT_OUTVOTED", false_pass, [r1, failed]))

    contradiction = make_join([d1, d2], [r1, r2], contradictions=["oracles disagree"], verdict="PASS")
    mutations.append(("CONTRADICTION_DROPPED", contradiction, [r1, r2]))

    wrong_state = copy.deepcopy(positive)
    wrong_state["results"][1]["state"] = "FAIL"
    mutations.append(("RESULT_STATE_MISMATCH", bind_digest(wrong_state), [r1, r2]))

    for name, packet, packet_results in mutations:
        try:
            verify(packet, packet_results, schema)
        except ValueError:
            print(f"REFUSED {name}")
        else:
            raise AssertionError(f"mutation passed: {name}")
    print(f"SUBAGENT-JOIN-GREEN positives=1 mutations={len(mutations)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--join")
    parser.add_argument("--result", action="append", default=[])
    parser.add_argument("--schema")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    schema_path = args.schema or str(Path(__file__).resolve().parents[1] / "references/contracts/subagent-join-receipt.schema.json")
    schema = load_json(schema_path)
    if args.selftest:
        selftest(schema)
        return 0
    if not args.join or not args.result:
        parser.error("--join and at least one --result are required")
    verify(load_json(args.join), [load_json(path) for path in args.result], schema)
    print("SUBAGENT-JOIN-PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
