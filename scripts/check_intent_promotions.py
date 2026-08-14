#!/usr/bin/env python3
"""Intent promotion lifecycle and writeback gate.

The schemas prove a contract and a receipt are shaped correctly. They cannot
prove the promotion is legitimate, and every failure this module exists to catch
is shaped exactly like a well-formed receipt:

    a PR was opened            -> so the intent is durable
    CI went green              -> so the intent is verified
    a flag was passed          -> so a human approved
    prose said the same thing  -> so the old record can be overwritten

None of those four inferences is licensed by the evidence that triggered it.
This gate refuses each one.

Exits: 0 admitted, 2 refused, 64 usage or unreadable input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

STATE_ORDER = (
    "HYPOTHESIS",
    "CANDIDATE",
    "PROPOSED",
    "VERIFIED",
    "ADMITTED",
    "CANONICAL",
)
NON_AUTHORITATIVE = ("HYPOTHESIS", "CANDIDATE")
TERMINAL = ("SUPERSEDED", "REVOKED")


class Refused(Exception):
    pass


def load(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise Refused(f"unreadable: {path}: {error}") from error
    try:
        body = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise Refused(f"unparseable: {path}: {error}") from error
    if not isinstance(body, dict):
        raise Refused(f"{path}: top level must be an object")
    return body, raw


def digest_of(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def rank(state: str) -> int:
    return STATE_ORDER.index(state) if state in STATE_ORDER else -1


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "intent-promotion-contract/v1":
        raise Refused("contract schema_version is not intent-promotion-contract/v1")

    lifecycle = contract["lifecycle"]
    states = set(lifecycle["states"])
    for required in STATE_ORDER + TERMINAL:
        if required not in states:
            raise Refused(f"lifecycle omits state {required}")

    declared_non_auth = set(lifecycle["non_authoritative_states"])
    if declared_non_auth != set(NON_AUTHORITATIVE):
        raise Refused(
            f"non_authoritative_states must be exactly {sorted(NON_AUTHORITATIVE)}; "
            f"found {sorted(declared_non_auth)}. Widening it would let a "
            f"hypothesis write durable memory"
        )
    if set(lifecycle["terminal_states"]) != set(TERMINAL):
        raise Refused(f"terminal_states must be exactly {sorted(TERMINAL)}")

    for transition in lifecycle["transitions"]:
        source, target = transition["from"], transition["to"]
        if source not in states or target not in states:
            raise Refused(f"transition {source}->{target} names an undeclared state")
        requires = set(transition["requires"])
        if target == "PROPOSED" and "EXACT_SUBJECT" not in requires:
            raise Refused("PROPOSED must require EXACT_SUBJECT")
        if target == "VERIFIED" and "OWNING_EVALUATOR_RECEIPT" not in requires:
            raise Refused("VERIFIED must require OWNING_EVALUATOR_RECEIPT")
        if target == "ADMITTED" and "ADMITTED_MERGE_SUBJECT" not in requires:
            raise Refused("ADMITTED must require ADMITTED_MERGE_SUBJECT")
        if target == "CANONICAL" and "HUMAN_APPROVAL" not in requires:
            raise Refused("CANONICAL must require HUMAN_APPROVAL")
        if target == "SUPERSEDED" and "SUPERSESSION_TARGET" not in requires:
            raise Refused("SUPERSEDED must require SUPERSESSION_TARGET")

    writeback = contract["writeback_policy"]
    for destination in writeback["declared_destinations"]:
        if destination["scope"] == "ROOT_GLOBAL":
            if destination["minimum_state"] != "CANONICAL":
                raise Refused(
                    f"root/global destination {destination['destination_id']!r} "
                    f"admits state {destination['minimum_state']}; only CANONICAL "
                    f"may reach a root invariant"
                )
            if destination["human_owned"] is not True:
                raise Refused(
                    f"root/global destination {destination['destination_id']!r} "
                    f"must be human_owned"
                )

    if contract.get("private_reasoning_persistence", "FORBIDDEN") != "FORBIDDEN":
        raise Refused("private reasoning persistence must remain FORBIDDEN")


def validate_receipt(
    receipt: dict[str, Any],
    contract: dict[str, Any],
    contract_raw: bytes,
) -> None:
    if receipt.get("schema_version") != "intent-promotion-receipt/v1":
        raise Refused("receipt schema_version is not intent-promotion-receipt/v1")

    if receipt["contract_id"] != contract["contract_id"]:
        raise Refused(
            f"receipt contract_id {receipt['contract_id']!r} does not name the "
            f"contract it was checked against ({contract['contract_id']!r})"
        )
    expected_digest = digest_of(contract_raw)
    if receipt["contract_digest"] != expected_digest:
        raise Refused(
            f"contract_digest {receipt['contract_digest']} does not match the "
            f"contract bytes ({expected_digest}); the receipt was issued under "
            f"different rules than the ones being applied"
        )

    subject = receipt["subject"]
    if subject["repository"] != contract["subject_identity"]["repository"]:
        raise Refused("receipt subject repository differs from the contract's")

    source, target = receipt["from_state"], receipt["to_state"]
    lifecycle = contract["lifecycle"]
    legal = {(item["from"], item["to"]) for item in lifecycle["transitions"]}
    if (source, target) not in legal:
        raise Refused(f"transition {source}->{target} is not declared by the contract")

    requires = set()
    for item in lifecycle["transitions"]:
        if (item["from"], item["to"]) == (source, target):
            requires = set(item["requires"])
            break

    runs = receipt["evaluator_receipts"]

    if "EXACT_SUBJECT" in requires:
        if not subject.get("branch") and subject.get("pull_request") is None:
            raise Refused(
                f"{target} requires an exact subject, but the receipt names "
                f"neither a branch nor a pull request"
            )

    if "OWNING_EVALUATOR_RECEIPT" in requires:
        if not runs:
            raise Refused(
                f"{target} requires an owning evaluator receipt and none is present. "
                f"A green pipeline elsewhere is not evidence about this subject"
            )
        for run in runs:
            if run["subject_commit_sha"] != subject["commit_sha"]:
                raise Refused(
                    f"evaluator {run['evaluator_id']!r} ran against "
                    f"{run['subject_commit_sha'][:12]} but the receipt subject is "
                    f"{subject['commit_sha'][:12]}; an old receipt does not carry "
                    f"forward to a new commit"
                )
            if run["status"] != "PASS":
                raise Refused(
                    f"{target} requires passing owning evaluators; "
                    f"{run['evaluator_id']!r} is {run['status']}"
                )

    if "ADMITTED_MERGE_SUBJECT" in requires:
        merge = receipt.get("merge_subject")
        if not merge:
            raise Refused(f"{target} requires an admitted merge subject and none is present")

    if "HUMAN_APPROVAL" in requires:
        approval = receipt.get("approval")
        if not approval:
            raise Refused(f"{target} requires human approval and none is recorded")
        if approval["approver_kind"] != "HUMAN":
            raise Refused(
                f"approval was created by {approval['approver_kind']}; an agent "
                f"cannot manufacture the approval that authorises it"
            )
        if approval["approval_subject_commit_sha"] != subject["commit_sha"]:
            raise Refused(
                "approval was given for a different commit than the one being promoted"
            )

    if "SUPERSESSION_TARGET" in requires and not receipt.get("supersedes"):
        raise Refused(f"{target} requires a supersession target and none is named")

    # A caller flag can ask for approval. It cannot be the approval.
    flags = receipt.get("caller_flags") or []
    if flags and not receipt.get("approval"):
        for flag in flags:
            if "override" in flag.lower() or "approve" in flag.lower():
                raise Refused(
                    f"caller flag {flag!r} is present with no human approval "
                    f"receipt; a flag requests approval, it does not create it"
                )

    # Writeback destinations must be declared, and reachable from this state.
    declared = {
        item["destination_id"]: item
        for item in contract["writeback_policy"]["declared_destinations"]
    }
    for writeback in receipt["writebacks"]:
        destination = declared.get(writeback["destination_id"])
        if destination is None:
            raise Refused(
                f"writeback destination {writeback['destination_id']!r} is not "
                f"declared by the contract"
            )
        if writeback["scope"] != destination["scope"]:
            raise Refused(
                f"writeback to {writeback['destination_id']!r} claims scope "
                f"{writeback['scope']} but the contract declares {destination['scope']}"
            )
        if source in NON_AUTHORITATIVE and target in NON_AUTHORITATIVE:
            raise Refused(
                f"{target} is non-authoritative and cannot write to "
                f"{writeback['destination_id']!r}"
            )
        if rank(target) < rank(destination["minimum_state"]):
            raise Refused(
                f"destination {writeback['destination_id']!r} requires at least "
                f"{destination['minimum_state']}, receipt reaches {target}"
            )
        if writeback["mode"] == "SUPERSEDE" and not receipt.get("supersedes"):
            raise Refused(
                f"writeback to {writeback['destination_id']!r} supersedes without "
                f"naming what it replaces; replacement is by lineage, not by "
                f"resemblance"
            )

    if target in TERMINAL and receipt["writebacks"]:
        raise Refused(
            f"{target} intents may not project a writeback; a revoked or "
            f"superseded intent presented as current is the failure this state exists to prevent"
        )


def _fixtures() -> tuple[dict[str, Any], dict[str, Any]]:
    contract = {
        "schema_version": "intent-promotion-contract/v1",
        "contract_id": "skills-shared-intent-promotion",
        "contract_version": "1.0.0",
        "subject_identity": {
            "repository": "ed3c/skills-shared",
            "commit_sha": "a" * 40,
        },
        "lifecycle": {
            "states": list(STATE_ORDER) + list(TERMINAL),
            "transitions": [
                {"from": "HYPOTHESIS", "to": "CANDIDATE", "requires": []},
                {"from": "CANDIDATE", "to": "PROPOSED", "requires": ["EXACT_SUBJECT"]},
                {"from": "PROPOSED", "to": "VERIFIED",
                 "requires": ["EXACT_SUBJECT", "OWNING_EVALUATOR_RECEIPT"]},
                {"from": "VERIFIED", "to": "ADMITTED",
                 "requires": ["EXACT_SUBJECT", "OWNING_EVALUATOR_RECEIPT", "ADMITTED_MERGE_SUBJECT"]},
                {"from": "ADMITTED", "to": "CANONICAL",
                 "requires": ["EXACT_SUBJECT", "ADMITTED_MERGE_SUBJECT", "HUMAN_APPROVAL"]},
                {"from": "CANONICAL", "to": "SUPERSEDED", "requires": ["SUPERSESSION_TARGET"]},
                {"from": "CANONICAL", "to": "REVOKED", "requires": ["HUMAN_APPROVAL"]},
            ],
            "non_authoritative_states": list(NON_AUTHORITATIVE),
            "terminal_states": list(TERMINAL),
        },
        "writeback_policy": {
            "append_only": True,
            "similarity_overwrite_allowed": False,
            "declared_destinations": [
                {"destination_id": "module-notes", "scope": "MODULE",
                 "minimum_state": "VERIFIED", "human_owned": False},
                {"destination_id": "project-context", "scope": "PROJECT",
                 "minimum_state": "ADMITTED", "human_owned": False},
                {"destination_id": "root-context", "scope": "ROOT_GLOBAL",
                 "minimum_state": "CANONICAL", "human_owned": True},
            ],
        },
        "approval_policy": {
            "agent_may_create_approval": False,
            "caller_flag_may_request": True,
            "caller_flag_may_grant": False,
            "required_approver_identity": "HUMAN_IDENTITY_REQUIRED",
        },
        "supersession_policy": {
            "replacement_requires_supersedes": True,
            "revoked_projection_allowed": False,
        },
        "private_reasoning_persistence": "FORBIDDEN",
    }
    receipt = {
        "schema_version": "intent-promotion-receipt/v1",
        "receipt_id": "IPR-FIXTURE-001",
        "intent_id": "MI-CTL-EVIDENCE",
        "contract_id": "skills-shared-intent-promotion",
        "contract_digest": "sha256:" + "0" * 64,
        "subject": {
            "repository": "ed3c/skills-shared",
            "commit_sha": "b" * 40,
            "tree_sha": "c" * 40,
            "branch": "ctl/04-intent-promotion",
            "pull_request": 120,
        },
        "from_state": "PROPOSED",
        "to_state": "VERIFIED",
        "evaluator_receipts": [
            {
                "evaluator_id": "skill-eval-contract",
                "subject_commit_sha": "b" * 40,
                "status": "PASS",
                "output_digest": "sha256:" + "d" * 64,
            }
        ],
        "merge_subject": None,
        "writebacks": [
            {"destination_id": "module-notes", "scope": "MODULE", "mode": "APPEND"}
        ],
        "approval": None,
        "supersedes": None,
        "caller_flags": [],
    }
    return contract, receipt


def _selftest() -> int:
    import copy

    contract, receipt = _fixtures()
    contract_raw = (json.dumps(contract, indent=2, sort_keys=True) + "\n").encode("utf-8")
    receipt["contract_digest"] = digest_of(contract_raw)

    try:
        validate_contract(contract)
        validate_receipt(receipt, contract, contract_raw)
    except Refused as error:
        print(f"SELFTEST RED: canonical fixtures refused: {error}", file=sys.stderr)
        return 2

    survived: list[str] = []

    contract_mutations: list[tuple[str, Any]] = [
        ("root destination reachable below CANONICAL",
         lambda c: c["writeback_policy"]["declared_destinations"][2].__setitem__("minimum_state", "ADMITTED")),
        ("root destination not human owned",
         lambda c: c["writeback_policy"]["declared_destinations"][2].__setitem__("human_owned", False)),
        ("PROPOSED no longer needs an exact subject",
         lambda c: c["lifecycle"]["transitions"][1].__setitem__("requires", [])),
        ("VERIFIED no longer needs an owning receipt",
         lambda c: c["lifecycle"]["transitions"][2].__setitem__("requires", ["EXACT_SUBJECT"])),
        ("CANONICAL no longer needs human approval",
         lambda c: c["lifecycle"]["transitions"][4].__setitem__("requires", ["EXACT_SUBJECT"])),
        ("PROPOSED declared non-authoritative-safe",
         lambda c: c["lifecycle"]["non_authoritative_states"].append("PROPOSED")),
        ("private reasoning persisted",
         lambda c: c.__setitem__("private_reasoning_persistence", "ALLOWED")),
    ]
    for name, apply in contract_mutations:
        body = copy.deepcopy(contract)
        apply(body)
        try:
            validate_contract(body)
        except Refused:
            continue
        survived.append(f"contract: {name}")

    def receipt_case(name: str, apply: Any) -> None:
        body = copy.deepcopy(receipt)
        apply(body)
        try:
            validate_receipt(body, contract, contract_raw)
        except Refused:
            return
        survived.append(f"receipt: {name}")

    receipt_case("PR opened promoted straight to a project writeback",
                 lambda r: (r.__setitem__("from_state", "CANDIDATE"),
                            r.__setitem__("to_state", "PROPOSED"),
                            r.__setitem__("evaluator_receipts", []),
                            r.__setitem__("writebacks", [
                                {"destination_id": "project-context", "scope": "PROJECT", "mode": "APPEND"}])))
    receipt_case("CI green without an owning exact-head receipt",
                 lambda r: r.__setitem__("evaluator_receipts", []))
    receipt_case("old receipt applied to a new commit",
                 lambda r: r["evaluator_receipts"][0].__setitem__("subject_commit_sha", "e" * 40))
    receipt_case("failing evaluator inside a promotion",
                 lambda r: r["evaluator_receipts"][0].__setitem__("status", "FAIL"))
    receipt_case("root write reached from VERIFIED",
                 lambda r: r.__setitem__("writebacks", [
                     {"destination_id": "root-context", "scope": "ROOT_GLOBAL", "mode": "APPEND"}]))
    receipt_case("root override flag with no human approval",
                 lambda r: r.__setitem__("caller_flags", ["--allow-root-override"]))
    receipt_case("agent-created approval",
                 lambda r: (r.__setitem__("from_state", "ADMITTED"),
                            r.__setitem__("to_state", "CANONICAL"),
                            r.__setitem__("merge_subject", {"merge_commit_sha": "f" * 40, "admitted_by": "bot"}),
                            r.__setitem__("approval", {
                                "approver_identity": "release-bot",
                                "approver_kind": "AGENT",
                                "approval_subject_commit_sha": "b" * 40,
                                "approval_receipt_digest": "sha256:" + "1" * 64})))
    receipt_case("approval for a different commit",
                 lambda r: (r.__setitem__("from_state", "ADMITTED"),
                            r.__setitem__("to_state", "CANONICAL"),
                            r.__setitem__("merge_subject", {"merge_commit_sha": "f" * 40, "admitted_by": "ed3c"}),
                            r.__setitem__("approval", {
                                "approver_identity": "ed3c",
                                "approver_kind": "HUMAN",
                                "approval_subject_commit_sha": "9" * 40,
                                "approval_receipt_digest": "sha256:" + "1" * 64})))
    receipt_case("canonical promotion with no approval at all",
                 lambda r: (r.__setitem__("from_state", "ADMITTED"),
                            r.__setitem__("to_state", "CANONICAL"),
                            r.__setitem__("merge_subject", {"merge_commit_sha": "f" * 40, "admitted_by": "ed3c"})))
    receipt_case("supersede without naming what it replaces",
                 lambda r: r["writebacks"][0].__setitem__("mode", "SUPERSEDE"))
    receipt_case("undeclared writeback destination",
                 lambda r: r.__setitem__("writebacks", [
                     {"destination_id": "somewhere-else", "scope": "MODULE", "mode": "APPEND"}]))
    receipt_case("destination scope claimed differently than declared",
                 lambda r: r.__setitem__("writebacks", [
                     {"destination_id": "module-notes", "scope": "PROJECT", "mode": "APPEND"}]))
    receipt_case("revoked intent still projected",
                 lambda r: (r.__setitem__("from_state", "CANONICAL"),
                            r.__setitem__("to_state", "REVOKED"),
                            r.__setitem__("approval", {
                                "approver_identity": "ed3c",
                                "approver_kind": "HUMAN",
                                "approval_subject_commit_sha": "b" * 40,
                                "approval_receipt_digest": "sha256:" + "1" * 64}),
                            r.__setitem__("writebacks", [
                                {"destination_id": "module-notes", "scope": "MODULE", "mode": "APPEND"}])))
    receipt_case("superseded transition without a target",
                 lambda r: (r.__setitem__("from_state", "CANONICAL"),
                            r.__setitem__("to_state", "SUPERSEDED"),
                            r.__setitem__("writebacks", [])))
    receipt_case("undeclared transition",
                 lambda r: (r.__setitem__("from_state", "HYPOTHESIS"),
                            r.__setitem__("to_state", "CANONICAL")))
    receipt_case("receipt issued under different contract bytes",
                 lambda r: r.__setitem__("contract_digest", "sha256:" + "2" * 64))
    receipt_case("receipt naming a different contract",
                 lambda r: r.__setitem__("contract_id", "some-other-contract"))

    if survived:
        for name in survived:
            print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
        return 2

    total = len(contract_mutations) + 17
    print(f"SELFTEST GREEN: canonical promotion admitted; {total} mutations refused")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("contract", "receipt", "selftest"))
    parser.add_argument("subject", type=Path, nargs="?")
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args(argv)

    if args.kind == "selftest":
        return _selftest()
    if args.subject is None:
        parser.error("a subject path is required")

    try:
        if args.kind == "contract":
            contract, _ = load(args.subject)
            validate_contract(contract)
        else:
            if args.contract is None:
                parser.error("receipt validation requires --contract")
            contract, contract_raw = load(args.contract)
            validate_contract(contract)
            receipt, _ = load(args.subject)
            validate_receipt(receipt, contract, contract_raw)
    except Refused as error:
        print(f"INTENT PROMOTION RED: {error}", file=sys.stderr)
        return 2

    print(f"INTENT PROMOTION GREEN: {args.kind} verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
