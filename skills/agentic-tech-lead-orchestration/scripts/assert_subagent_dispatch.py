#!/usr/bin/env python3
"""Fail closed on unresolved model aliases, egress, or invalid role leases."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from portfolio_control_lib import assert_digest, bind_digest, load_json, TERMINAL_AGENT_STATES

READ_ONLY_ROLES = {
    "portfolio-explorer",
    "acceptance-adversary",
    "dependency-auditor",
    "runtime-admission-auditor",
    "consolidation-verifier",
    "release-auditor",
}


def verify(packet: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    if schema is not None:
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(packet))
        if errors:
            raise ValueError("shape: " + "; ".join(error.message for error in errors))
    assert_digest(packet, label="subagent-dispatch")
    model = packet["model"]
    unresolved = {"UNKNOWN", "UNRESOLVED", "${MODEL_ID}", model["alias"]}
    if model["model_id"] in unresolved or "${" in model["model_id"]:
        raise ValueError("MODEL_ALIAS_REPORTED_AS_EXACT_IDENTITY")
    if model["egress_state"] != "PASS":
        raise ValueError("PRIVATE_REPO_DISPATCH_WITHOUT_EGRESS_ADMISSION")
    exclusive = packet["leases"]["exclusive"]
    if packet["role"] in READ_ONLY_ROLES and exclusive:
        raise ValueError("READ_ONLY_AGENT_HAS_WRITE_LEASE")
    if packet["role"] == "implementation-worker" and not exclusive:
        raise ValueError("IMPLEMENTATION_WORKER_WITHOUT_EXCLUSIVE_LEASE")
    if set(packet["terminal_states"]) != TERMINAL_AGENT_STATES:
        raise ValueError("TERMINAL_DENOMINATOR_INCOMPLETE")


def positive_fixture() -> dict[str, Any]:
    packet = {
        "schema": "subagent-dispatch/v1",
        "coordinator_instruction": "Use subagents. Wait for all agents and consolidate their findings.",
        "dispatch_id": "dispatch-1",
        "epoch_digest": "1" * 64,
        "task_id": "task-1",
        "attempt_id": "attempt-1",
        "role": "portfolio-explorer",
        "agent_config_digest": "2" * 64,
        "host": "codex-cli",
        "model": {
            "alias": "FABLE_5",
            "provider": "provider-observed",
            "carrier": "codex-cli",
            "model_id": "exact-model-id",
            "version": "2026-08-21",
            "config_digest": "3" * 64,
            "egress_state": "PASS"
        },
        "base": {"repository": "ed3c/skills-shared", "commit": "4" * 40, "tree": "5" * 40},
        "leases": {"exclusive": [], "read_only": ["**"], "forbidden": ["secrets/**"]},
        "commands": [["git", "status", "--short"]],
        "expected_outputs": ["repository-portfolio-snapshot/v1"],
        "terminal_states": sorted(TERMINAL_AGENT_STATES),
        "budgets": {"wall_seconds": 600, "max_processes": 4, "max_output_bytes": 1000000, "max_retries": 0}
    }
    return bind_digest(packet)


def selftest(schema: dict[str, Any] | None) -> None:
    base = positive_fixture()
    verify(base, schema)
    mutations: list[tuple[str, dict[str, Any]]] = []

    alias = copy.deepcopy(base)
    alias["model"]["model_id"] = alias["model"]["alias"]
    mutations.append(("MODEL_ALIAS_REPORTED_AS_EXACT_IDENTITY", bind_digest(alias)))

    egress = copy.deepcopy(base)
    egress["model"]["egress_state"] = "NOT_EXERCISED"
    mutations.append(("PRIVATE_REPO_DISPATCH_WITHOUT_EGRESS_ADMISSION", bind_digest(egress)))

    write = copy.deepcopy(base)
    write["leases"]["exclusive"] = ["src/**"]
    mutations.append(("READ_ONLY_AGENT_HAS_WRITE_LEASE", bind_digest(write)))

    worker = copy.deepcopy(base)
    worker["role"] = "implementation-worker"
    mutations.append(("IMPLEMENTATION_WORKER_WITHOUT_EXCLUSIVE_LEASE", bind_digest(worker)))

    terminals = copy.deepcopy(base)
    terminals["terminal_states"].remove("TIMEOUT")
    mutations.append(("TERMINAL_DENOMINATOR_INCOMPLETE", bind_digest(terminals)))

    stale = copy.deepcopy(base)
    stale["task_id"] = "moved"
    mutations.append(("STALE_DIGEST", stale))

    for name, mutation in mutations:
        try:
            verify(mutation, schema)
        except ValueError:
            print(f"REFUSED {name}")
        else:
            raise AssertionError(f"mutation passed: {name}")
    print(f"SUBAGENT-DISPATCH-GREEN positives=1 mutations={len(mutations)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dispatch")
    parser.add_argument("--schema")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    schema_path = args.schema or str(Path(__file__).resolve().parents[1] / "references/contracts/subagent-dispatch.schema.json")
    schema = load_json(schema_path)
    if args.selftest:
        selftest(schema)
        return 0
    if not args.dispatch:
        parser.error("--dispatch is required without --selftest")
    verify(load_json(args.dispatch), schema)
    print("SUBAGENT-DISPATCH-PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
