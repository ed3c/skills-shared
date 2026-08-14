"""Mutation-sensitive selftest for the promotion gate."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from .common import PolicyRefusal, canonical_sha256, git_blob_sha
from .contract import validate_contract
from .fixtures import build_fixture_contract, build_fixture_receipt
from .receipt import validate_receipt

def selftest(script_path: Path) -> int:
    import copy
    import tempfile

    script_raw = script_path.read_bytes()
    implementation_digest = canonical_sha256(script_raw)

    with tempfile.TemporaryDirectory() as raw:
        repo = Path(raw)
        bound_path = repo / "evals/fixtures/controlled-language/intent-contract.json"
        bound_path.parent.mkdir(parents=True)
        bound_body = {
            "schema_version": "intent-bound-constraint/v1",
            "contract_id": "controlled-language-foundation",
            "contract_version": "1.0.0",
            "subject_identity": {"repository": "ed3c/skills-shared"},
        }
        bound_raw = (json.dumps(bound_body, sort_keys=True) + "\n").encode()
        bound_path.write_bytes(bound_raw)
        script_copy = repo / "scripts/check_intent_promotions.py"
        script_copy.parent.mkdir(parents=True)
        script_copy.write_bytes(script_raw)

        contract = build_fixture_contract(
            implementation_digest=implementation_digest,
            bound_blob_sha=git_blob_sha(bound_raw),
        )
        contract_raw = (
            json.dumps(contract, indent=2, sort_keys=True) + "\n"
        ).encode()
        receipt = build_fixture_receipt(contract, contract_raw, target="VERIFIED")

        try:
            validate_contract(
                contract,
                repository_root=repo,
                verify_external_bindings=True,
            )
            validate_receipt(receipt, contract, contract_raw)
        except PolicyRefusal as error:
            print(f"SELFTEST RED: positive fixture refused: {error}", file=sys.stderr)
            return 2

        mutations: list[tuple[str, str, Any]] = []

        def contract_case(name: str, mutate: Any) -> None:
            mutations.append(("contract", name, mutate))

        def receipt_case(name: str, mutate: Any) -> None:
            mutations.append(("receipt", name, mutate))

        contract_case(
            "widen non-durable state",
            lambda value: value["lifecycle"]["non_durable_states"].remove("VERIFIED"),
        )
        contract_case(
            "durable destination before ADMITTED",
            lambda value: value["writeback_policy"]["declared_destinations"][3][
                "allowed_states"
            ].append("VERIFIED"),
        )
        contract_case(
            "similarity overwrite allowed",
            lambda value: value["writeback_policy"].__setitem__(
                "similarity_overwrite_allowed", True
            ),
        )
        contract_case(
            "owning evaluator no longer owning",
            lambda value: value["evaluator_registry"][1].__setitem__("owning", False),
        )
        contract_case(
            "VERIFIED drops owning receipt requirement",
            lambda value: value["lifecycle"]["transitions"][2].__setitem__(
                "requires", ["LOCAL_EVALUATOR_RECEIPT", "EXACT_PR_SUBJECT"]
            ),
        )
        contract_case(
            "root destination not Human-owned",
            lambda value: value["writeback_policy"]["declared_destinations"][5].__setitem__(
                "human_owned", False
            ),
        )
        contract_case(
            "bound IBC blob stale",
            lambda value: value["intent_bound_contract"].__setitem__(
                "git_blob_sha", "8" * 40
            ),
        )
        contract_case(
            "private reasoning enabled",
            lambda value: value.__setitem__("private_reasoning_persistence", "ALLOWED"),
        )

        receipt_case(
            "PR-open promoted to durable module writeback",
            lambda value: (
                value.__setitem__("from_state", "CANDIDATE"),
                value.__setitem__("to_state", "PROPOSED"),
                value.__setitem__(
                    "writebacks",
                    [
                        {
                            "destination_id": "module-context",
                            "scope": "MODULE",
                            "durability": "DURABLE",
                            "locator": "skills/controlled-technical-language-harness/README.md",
                            "mode": "APPEND",
                            "content_digest": "sha256:" + "1" * 64,
                            "authority_subject": "b" * 40,
                            "current_projection": True,
                        }
                    ],
                ),
            ),
        )
        receipt_case(
            "missing owning CI receipt",
            lambda value: value.__setitem__(
                "evaluator_receipts",
                [
                    run
                    for run in value["evaluator_receipts"]
                    if run["authority"] != "OWNING_CI"
                ],
            ),
        )
        receipt_case(
            "foreign green evaluator",
            lambda value: value["evaluator_receipts"][1].__setitem__(
                "evaluator_id", "some-other-green-job"
            ),
        )
        receipt_case(
            "stale evaluator implementation",
            lambda value: value["evaluator_receipts"][1].__setitem__(
                "implementation_digest", "sha256:" + "0" * 64
            ),
        )
        receipt_case(
            "old evaluator receipt",
            lambda value: value["evaluator_receipts"][0].__setitem__(
                "subject_commit_sha", "1" * 40
            ),
        )
        receipt_case(
            "requested lane not exercised",
            lambda value: value["evaluator_receipts"][1].__setitem__(
                "status", "NOT_EXERCISED"
            ),
        )
        receipt_case(
            "stale PR head",
            lambda value: value["pr_subject"].__setitem__("head_sha", "1" * 40),
        )
        receipt_case(
            "stale evidence marked PASS",
            lambda value: value.__setitem__("evidence_fresh", False),
        )
        receipt_case(
            "caller flag grants root override",
            lambda value: (
                value.__setitem__("from_state", "ADMITTED"),
                value.__setitem__("to_state", "CANONICAL"),
                value.__setitem__("caller_flags", ["--allow-root-override"]),
                value.__setitem__("human_approval", None),
            ),
        )
        receipt_case(
            "Agent-created Human approval",
            lambda value: (
                value.__setitem__("from_state", "ADMITTED"),
                value.__setitem__("to_state", "CANONICAL"),
                value.__setitem__(
                    "admitted_subject",
                    {
                        "kind": "MERGE_COMMIT",
                        "repository": "ed3c/skills-shared",
                        "source_head_sha": "b" * 40,
                        "admitted_identity": "f" * 40,
                        "status": "ADMITTED",
                        "receipt_digest": "sha256:" + "4" * 64,
                    },
                ),
                value.__setitem__(
                    "human_approval",
                    {
                        "approver_identity": "agent",
                        "approver_kind": "AGENT",
                        "approval_state": "ADMITTED",
                        "approval_subject": "f" * 40,
                        "allowed_actions": [
                            "PROMOTE_CANONICAL",
                            "WRITE:root-context",
                        ],
                        "receipt_digest": "sha256:" + "6" * 64,
                    },
                ),
            ),
        )
        receipt_case(
            "approval for another admitted subject",
            lambda value: (
                value.__setitem__("from_state", "ADMITTED"),
                value.__setitem__("to_state", "CANONICAL"),
                value.__setitem__(
                    "admitted_subject",
                    {
                        "kind": "MERGE_COMMIT",
                        "repository": "ed3c/skills-shared",
                        "source_head_sha": "b" * 40,
                        "admitted_identity": "f" * 40,
                        "status": "ADMITTED",
                        "receipt_digest": "sha256:" + "4" * 64,
                    },
                ),
                value.__setitem__(
                    "human_approval",
                    {
                        "approver_identity": "ed3c",
                        "approver_kind": "HUMAN",
                        "approval_state": "ADMITTED",
                        "approval_subject": "1" * 40,
                        "allowed_actions": [
                            "PROMOTE_CANONICAL",
                            "WRITE:root-context",
                        ],
                        "receipt_digest": "sha256:" + "6" * 64,
                    },
                ),
            ),
        )
        receipt_case(
            "admitted subject from another head",
            lambda value: (
                value.__setitem__("from_state", "VERIFIED"),
                value.__setitem__("to_state", "ADMITTED"),
                value.__setitem__(
                    "admitted_subject",
                    {
                        "kind": "MERGE_COMMIT",
                        "repository": "ed3c/skills-shared",
                        "source_head_sha": "1" * 40,
                        "admitted_identity": "f" * 40,
                        "status": "ADMITTED",
                        "receipt_digest": "sha256:" + "4" * 64,
                    },
                ),
            ),
        )
        receipt_case(
            "durable locator outside destination",
            lambda value: (
                value.__setitem__("from_state", "VERIFIED"),
                value.__setitem__("to_state", "ADMITTED"),
                value.__setitem__(
                    "admitted_subject",
                    {
                        "kind": "MERGE_COMMIT",
                        "repository": "ed3c/skills-shared",
                        "source_head_sha": "b" * 40,
                        "admitted_identity": "f" * 40,
                        "status": "ADMITTED",
                        "receipt_digest": "sha256:" + "4" * 64,
                    },
                ),
                value.__setitem__(
                    "writebacks",
                    [
                        {
                            "destination_id": "module-context",
                            "scope": "MODULE",
                            "durability": "DURABLE",
                            "locator": "CONTEXT.md#wrong-scope",
                            "mode": "APPEND",
                            "content_digest": "sha256:" + "5" * 64,
                            "authority_subject": "f" * 40,
                            "current_projection": True,
                        }
                    ],
                ),
            ),
        )
        receipt_case(
            "similarity-style overwrite with no lineage",
            lambda value: value["writebacks"][0].__setitem__("mode", "SUPERSEDE"),
        )
        receipt_case(
            "contract digest changed",
            lambda value: value["contract_identity"].__setitem__(
                "contract_digest", "sha256:" + "1" * 64
            ),
        )
        receipt_case(
            "IBC identity changed",
            lambda value: value["intent_bound_contract_identity"].__setitem__(
                "git_blob_sha", "1" * 40
            ),
        )
        receipt_case(
            "private reasoning persisted",
            lambda value: value.__setitem__("reasoning_trace", ["hidden"]),
        )

        survived: list[str] = []
        for kind, name, mutate in mutations:
            contract_copy = copy.deepcopy(contract)
            receipt_copy = copy.deepcopy(receipt)
            try:
                if kind == "contract":
                    mutate(contract_copy)
                    validate_contract(
                        contract_copy,
                        repository_root=repo,
                        verify_external_bindings=True,
                    )
                else:
                    mutate(receipt_copy)
                    validate_receipt(receipt_copy, contract, contract_raw)
            except PolicyRefusal:
                continue
            survived.append(f"{kind}: {name}")

        if survived:
            for name in survived:
                print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
            return 2

        print(
            f"SELFTEST GREEN: positive transition admitted; "
            f"{len(mutations)} mutations refused"
        )
        return 0
