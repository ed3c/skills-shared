#!/usr/bin/env python3
"""Verify exact-head, non-empty, one-ready-transition GitHub Actions evidence."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from portfolio_control_lib import assert_digest, bind_digest, load_json


def verify(packet: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    if schema is not None:
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(packet))
        if errors:
            raise ValueError("shape: " + "; ".join(error.message for error in errors))
    assert_digest(packet, label="one-shot-ci-epoch")

    if packet["verdict"] == "PASS":
        publication = packet["publication"]
        if publication["ready_transition_count"] != 1:
            raise ValueError("PASS requires exactly one ready-for-review transition")
        if publication["code_push_count_after_ready"] != 0:
            raise ValueError("PASS forbids code movement after ready-for-review")
        if not packet["workflow_runs"]:
            raise ValueError("PASS requires at least one workflow run")
        for run in packet["workflow_runs"]:
            if run["head_sha"] != packet["candidate_head"]:
                raise ValueError(f"old or wrong workflow head: {run['head_sha']}")
            if run["status"] != "completed" or run["conclusion"] != "success":
                raise ValueError(f"workflow {run['run_id']} is not completed success")
            if not run["jobs_non_empty"] or not run["steps_non_empty"]:
                raise ValueError(f"workflow {run['run_id']} has empty jobs or steps")
        for rerun in packet["reruns"]:
            if rerun["classification"] != "INFRASTRUCTURE_FLAKE" or not rerun["source_unchanged"]:
                raise ValueError("blind or code-failure rerun is not admissible")


def positive_fixture() -> dict[str, Any]:
    packet = {
        "schema": "one-shot-ci-epoch/v1",
        "repository": "ed3c/skills-shared",
        "pull_request": 560,
        "candidate_head": "1" * 40,
        "candidate_tree": "2" * 40,
        "local_join_digest": "3" * 64,
        "publication": {
          "draft_created_at": "2026-08-21T00:00:00Z",
          "ready_transition_count": 1,
          "code_push_count_after_ready": 0
        },
        "workflow_runs": [{
          "run_id": 1,
          "workflow": "Repository Portfolio Control",
          "head_sha": "1" * 40,
          "status": "completed",
          "conclusion": "success",
          "jobs_non_empty": True,
          "steps_non_empty": True,
          "artifact_digests": ["4" * 64]
        }],
        "reruns": [],
        "verdict": "PASS",
        "claims_not_proven": ["semantic acceptance, merge, release and production"]
    }
    return bind_digest(packet)


def selftest(schema: dict[str, Any] | None) -> None:
    base = positive_fixture()
    verify(base, schema)
    mutations: list[tuple[str, dict[str, Any]]] = []

    twice_ready = copy.deepcopy(base)
    twice_ready["publication"]["ready_transition_count"] = 2
    mutations.append(("DRAFT_OR_SYNCHRONIZE_CI_SPAM", bind_digest(twice_ready)))

    moved = copy.deepcopy(base)
    moved["publication"]["code_push_count_after_ready"] = 1
    mutations.append(("CODE_PUSH_AFTER_READY", bind_digest(moved)))

    old_head = copy.deepcopy(base)
    old_head["workflow_runs"][0]["head_sha"] = "9" * 40
    mutations.append(("OLD_HEAD_WORKFLOW_RECEIPT_REUSED", bind_digest(old_head)))

    empty = copy.deepcopy(base)
    empty["workflow_runs"][0]["steps_non_empty"] = False
    mutations.append(("EMPTY_WORKFLOW_PROMOTED_TO_PASS", bind_digest(empty)))

    skipped = copy.deepcopy(base)
    skipped["workflow_runs"][0]["conclusion"] = "skipped"
    mutations.append(("SKIPPED_WORKFLOW_PROMOTED_TO_PASS", bind_digest(skipped)))

    blind = copy.deepcopy(base)
    blind["reruns"] = [{"run_id": 1, "classification": "CODE_OR_TEST_FAILURE", "source_unchanged": True}]
    mutations.append(("BLIND_RERUN_AFTER_CODE_FAILURE", bind_digest(blind)))

    for name, mutation in mutations:
        try:
            verify(mutation, schema)
        except ValueError:
            print(f"REFUSED {name}")
        else:
            raise AssertionError(f"mutation passed: {name}")
    print(f"ONE-SHOT-CI-GREEN positives=1 mutations={len(mutations)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epoch")
    parser.add_argument("--schema")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    schema_path = args.schema or str(Path(__file__).resolve().parents[1] / "references/contracts/one-shot-ci-epoch.schema.json")
    schema = load_json(schema_path)
    if args.selftest:
        selftest(schema)
        return 0
    if not args.epoch:
        parser.error("--epoch is required without --selftest")
    verify(load_json(args.epoch), schema)
    print("ONE-SHOT-CI-PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
