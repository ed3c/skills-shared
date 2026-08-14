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


class Unusable(Exception):
    """The input could not be evaluated. Distinct from a refused promotion.

    Collapsing these two means a typo in a path reads as a policy failure, and
    a policy failure reads as a broken invocation. They exit differently.
    """


MUTABLE_VERSIONS = ("latest", "current", "head", "dev", "")
FORBIDDEN_FIELDS = ("chain_of_thought", "reasoning", "scratchpad",
                    "private_notes", "thinking")


def load(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise Unusable(f"unreadable: {path}: {error}") from error
    try:
        body = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise Unusable(f"unparseable: {path}: {error}") from error
    if not isinstance(body, dict):
        raise Unusable(f"{path}: top level must be an object")
    return body, raw


def reject_private_reasoning(body: Any, where: str = "receipt") -> None:
    """No free-form private reasoning is persisted, at any nesting depth."""
    if isinstance(body, dict):
        for key, value in body.items():
            if str(key).lower() in FORBIDDEN_FIELDS:
                raise Refused(
                    f"{where} carries a private reasoning field {key!r}; "
                    f"free-form private reasoning is never persisted"
                )
            reject_private_reasoning(value, where)
    elif isinstance(body, list):
        for item in body:
            reject_private_reasoning(item, where)


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
    seen_destinations = set()
    for destination in writeback["declared_destinations"]:
        name = destination["destination_id"]
        if name in seen_destinations:
            raise Refused(f"destination {name!r} is declared twice")
        seen_destinations.add(name)
        # Durable projection begins at ADMITTED. A destination reachable from
        # PROPOSED or VERIFIED would let PR-open or CI-green become permanent
        # memory, which is the substitution this contract exists to block --
        # and it is not made safe by the destination being module-scoped.
        if destination["minimum_state"] not in ("ADMITTED", "CANONICAL"):
            raise Refused(
                f"destination {name!r} admits state "
                f"{destination['minimum_state']}; durable projection begins at "
                f"ADMITTED, after an admitted merge or release subject"
            )
        if destination["scope"] == "ROOT_GLOBAL":
            if destination["minimum_state"] != "CANONICAL":
                raise Refused(
                    f"root/global destination {name!r} admits state "
                    f"{destination['minimum_state']}; only CANONICAL may reach "
                    f"a root invariant"
                )
            if destination["human_owned"] is not True:
                raise Refused(f"root/global destination {name!r} must be human_owned")

    if contract.get("private_reasoning_persistence", "FORBIDDEN") != "FORBIDDEN":
        raise Refused("private reasoning persistence must remain FORBIDDEN")

    supersession = contract["supersession_policy"]
    if supersession.get("append_only_ledger") is not True:
        raise Refused("supersession_policy.append_only_ledger must be true")
    if not supersession.get("ledger_ref"):
        raise Refused(
            "supersession_policy.ledger_ref is absent; without a ledger, "
            "'supersedes' names a predecessor nothing can confirm exists"
        )

    reject_private_reasoning(contract, "contract")


def check_ledger(
    receipt: dict[str, Any],
    ledger: list[dict[str, Any]] | None,
) -> None:
    """Supersession is lineage, and lineage needs a record to point into.

    Without a ledger, `supersedes` is a claim about a predecessor that nothing
    can confirm ever existed, was current, or was in the state named.
    """
    supersedes = receipt.get("supersedes")
    if supersedes is None:
        return
    if ledger is None:
        raise Refused(
            "receipt supersedes a predecessor but no ledger was supplied to "
            "confirm it; an unverifiable lineage claim is not lineage"
        )

    entries = {entry["receipt_id"]: entry for entry in ledger}
    target = entries.get(supersedes["receipt_id"])
    if target is None:
        raise Refused(
            f"supersession target {supersedes['receipt_id']!r} is absent from "
            f"the ledger"
        )
    if target.get("current") is not True:
        raise Refused(
            f"supersession target {supersedes['receipt_id']!r} is not current; "
            f"superseding an already-superseded record loses the intervening "
            f"history"
        )
    if target["receipt_digest"] != supersedes["receipt_digest"]:
        raise Refused(
            f"supersession target digest does not match the ledger entry; the "
            f"receipt is replacing a different record than it names"
        )
    if target["state"] != supersedes["predecessor_state"]:
        raise Refused(
            f"supersession names predecessor state "
            f"{supersedes['predecessor_state']!r} but the ledger records "
            f"{target['state']!r}"
        )
    if target["subject_commit_sha"] != supersedes["predecessor_subject_commit_sha"]:
        raise Refused("supersession names a different predecessor subject than the ledger")
    if target.get("intent_id") != receipt["intent_id"]:
        raise Refused(
            f"supersession target belongs to intent {target.get('intent_id')!r}, "
            f"not {receipt['intent_id']!r}"
        )


def check_terminal_currency(
    receipt: dict[str, Any],
    ledger: list[dict[str, Any]] | None,
) -> None:
    """A terminal intent may not remain current in the ledger."""
    if ledger is None:
        return
    if receipt["to_state"] not in TERMINAL:
        return
    for entry in ledger:
        if entry["receipt_id"] == receipt["receipt_id"] and entry.get("current") is True:
            raise Refused(
                f"{receipt['to_state']} receipt {receipt['receipt_id']!r} is "
                f"still marked current in the ledger; a revoked or superseded "
                f"intent presented as current is the failure that state exists "
                f"to prevent"
            )


def validate_receipt(
    receipt: dict[str, Any],
    contract: dict[str, Any],
    contract_raw: bytes,
    ledger: list[dict[str, Any]] | None = None,
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
        seen_evaluators: set[str] = set()
        for run in runs:
            name = run["evaluator_id"]
            # "Owning" was a label anyone could write. These are the fields a
            # caller cannot produce without the evaluator and its receipt
            # actually existing.
            if name in seen_evaluators:
                raise Refused(
                    f"evaluator {name!r} appears twice; a duplicated run can "
                    f"pad a receipt with the appearance of independent coverage"
                )
            seen_evaluators.add(name)
            if str(run.get("evaluator_version", "")).strip().lower() in MUTABLE_VERSIONS:
                raise Refused(
                    f"evaluator {name!r} version "
                    f"{run.get('evaluator_version')!r} is mutable; the evidence "
                    f"would not identify which build produced it"
                )
            if run["execution_origin"] not in ("OWNING_WORKFLOW", "LOCAL_VERIFIED",
                                               "EXTERNAL_ATTESTED"):
                raise Refused(f"evaluator {name!r} has no admitted execution origin")
            if run["subject_commit_sha"] != subject["commit_sha"]:
                raise Refused(
                    f"evaluator {name!r} ran against "
                    f"{run['subject_commit_sha'][:12]} but the receipt subject is "
                    f"{subject['commit_sha'][:12]}; an old receipt does not carry "
                    f"forward to a new commit"
                )
            if run["subject_tree_sha"] != subject["tree_sha"]:
                raise Refused(
                    f"evaluator {name!r} ran against tree "
                    f"{run['subject_tree_sha'][:12]} but the subject tree is "
                    f"{subject['tree_sha'][:12]}"
                )
            if run["status"] != "PASS":
                raise Refused(
                    f"{target} requires passing owning evaluators; "
                    f"{name!r} is {run['status']}"
                )

    if "ADMITTED_MERGE_SUBJECT" in requires:
        merge = receipt.get("merge_subject")
        if not merge:
            raise Refused(f"{target} requires an admitted merge subject and none is present")
        # A non-null merge_subject proved nothing: a syntactically valid random
        # SHA satisfied it. Bind it to the candidate actually being promoted.
        if merge["repository"] != subject["repository"]:
            raise Refused("merge subject names a different repository than the candidate")
        if merge["candidate_head_sha"] != subject["commit_sha"]:
            raise Refused(
                f"merge subject admitted candidate "
                f"{merge['candidate_head_sha'][:12]}, not the promoted commit "
                f"{subject['commit_sha'][:12]}"
            )
        if merge["candidate_tree_sha"] != subject["tree_sha"]:
            raise Refused("merge subject admitted a different candidate tree")
        readback = merge["forge_readback"]
        if readback["observed_at_commit_sha"] != merge["merge_commit_sha"]:
            raise Refused(
                "forge readback observed a different commit than the merge it "
                "is offered as evidence for"
            )
        release = merge.get("release_artifact")
        if release is not None and release["artifact_digest"] == merge["merge_commit_sha"]:
            raise Refused(
                "release artifact digest repeats the merge commit; a release "
                "artifact is a different object from a commit identity"
            )

    if "HUMAN_APPROVAL" in requires:
        approval = receipt.get("approval")
        if not approval:
            raise Refused(f"{target} requires human approval and none is recorded")
        if approval["approver_kind"] != "HUMAN":
            raise Refused(
                f"approval was created by {approval['approver_kind']}; an agent "
                f"cannot manufacture the approval that authorises it"
            )
        # An agent can write approver_kind: HUMAN. It cannot honestly write
        # generated_by_agent: false, and the field being required makes the
        # substitution a stated lie rather than an omission.
        if approval.get("generated_by_agent") is not False:
            raise Refused(
                "approval declares generated_by_agent true; an agent-produced "
                "record is not a human approval however it is labelled"
            )
        if approval["readback_source"] not in ("GITHUB_API", "GITLAB_API",
                                               "FORGEJO_API", "HUMAN_SIGNED_RECEIPT"):
            raise Refused("approval has no trusted readback source")
        if not str(approval.get("review_ref", "")).strip():
            raise Refused("approval names no review reference to read back")
        if approval["approval_subject_commit_sha"] != subject["commit_sha"]:
            raise Refused(
                "approval was given for a different commit than the one being promoted"
            )

    if "SUPERSESSION_TARGET" in requires and not receipt.get("supersedes"):
        raise Refused(f"{target} requires a supersession target and none is named")

    reject_private_reasoning(receipt)
    check_ledger(receipt, ledger)
    check_terminal_currency(receipt, ledger)

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


def _fixtures() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    contract = {
        "schema_version": "intent-promotion-contract/v1",
        "contract_id": "skills-shared-intent-promotion",
        "contract_version": "1.1.0",
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
                 "minimum_state": "ADMITTED", "human_owned": False},
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
            "append_only_ledger": True,
            "ledger_ref": "evals/fixtures/intent-promotion/ledger.json",
        },
        "private_reasoning_persistence": "FORBIDDEN",
    }

    def evaluator_run() -> dict[str, Any]:
        return {
            "evaluator_id": "skill-eval-contract",
            "evaluator_version": "1.0.0",
            "evaluator_artifact_digest": "sha256:" + "e" * 64,
            "subject_commit_sha": "b" * 40,
            "subject_tree_sha": "c" * 40,
            "status": "PASS",
            "output_digest": "sha256:" + "d" * 64,
            "receipt_ref": "workflow-run:31794307867",
            "receipt_digest": "sha256:" + "7" * 64,
            "execution_origin": "OWNING_WORKFLOW",
        }

    merge_subject = {
        "repository": "ed3c/skills-shared",
        "merge_commit_sha": "f" * 40,
        "merge_tree_sha": "8" * 40,
        "candidate_head_sha": "b" * 40,
        "candidate_tree_sha": "c" * 40,
        "admitted_by": "ed3c",
        "forge_readback": {
            "source": "GITHUB_API",
            "observed_at_commit_sha": "f" * 40,
            "readback_digest": "sha256:" + "6" * 64,
        },
        "release_artifact": None,
    }

    # ADMITTED is the first state that may write durably, so that is the
    # canonical receipt rather than the easier VERIFIED one.
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
            "branch": "ctl/04b-intent-promotion-authority",
            "pull_request": 134,
        },
        "from_state": "VERIFIED",
        "to_state": "ADMITTED",
        "evaluator_receipts": [evaluator_run()],
        "merge_subject": merge_subject,
        "writebacks": [
            {"destination_id": "module-notes", "scope": "MODULE", "mode": "APPEND"}
        ],
        "approval": None,
        "supersedes": None,
        "caller_flags": [],
    }

    ledger = [
        {
            "receipt_id": "IPR-FIXTURE-PRIOR",
            "receipt_digest": "sha256:" + "5" * 64,
            "intent_id": "MI-CTL-EVIDENCE",
            "state": "CANONICAL",
            "subject_commit_sha": "3" * 40,
            "current": True,
        }
    ]
    return contract, receipt, ledger


def _selftest() -> int:
    import copy

    contract, receipt, ledger = _fixtures()
    contract_raw = (json.dumps(contract, indent=2, sort_keys=True) + "\n").encode("utf-8")
    receipt["contract_digest"] = digest_of(contract_raw)

    try:
        validate_contract(contract)
        validate_receipt(receipt, contract, contract_raw, ledger)
    except Refused as error:
        print(f"SELFTEST RED: canonical fixtures refused: {error}", file=sys.stderr)
        return 2

    survived: list[str] = []

    contract_mutations: list[tuple[str, Any]] = [
        ("durable module write authorized at VERIFIED",
         lambda c: c["writeback_policy"]["declared_destinations"][0].__setitem__("minimum_state", "VERIFIED")),
        ("durable project write authorized at PROPOSED",
         lambda c: c["writeback_policy"]["declared_destinations"][1].__setitem__("minimum_state", "PROPOSED")),
        ("root destination reachable below CANONICAL",
         lambda c: c["writeback_policy"]["declared_destinations"][2].__setitem__("minimum_state", "ADMITTED")),
        ("root destination not human owned",
         lambda c: c["writeback_policy"]["declared_destinations"][2].__setitem__("human_owned", False)),
        ("duplicate destination id",
         lambda c: c["writeback_policy"]["declared_destinations"].append(
             dict(c["writeback_policy"]["declared_destinations"][0]))),
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
        ("chain_of_thought field in the contract",
         lambda c: c.__setitem__("chain_of_thought", "why I decided this")),
        ("append-only ledger disabled",
         lambda c: c["supersession_policy"].__setitem__("append_only_ledger", False)),
        ("ledger reference removed",
         lambda c: c["supersession_policy"].__setitem__("ledger_ref", "")),
    ]
    for name, apply in contract_mutations:
        body = copy.deepcopy(contract)
        apply(body)
        try:
            validate_contract(body)
        except Refused:
            continue
        survived.append(f"contract: {name}")

    def receipt_case(name: str, apply: Any, use_ledger: Any = ...) -> None:
        body = copy.deepcopy(receipt)
        apply(body)
        supplied = ledger if use_ledger is ... else use_ledger
        try:
            validate_receipt(body, contract, contract_raw, supplied)
        except Refused:
            return
        survived.append(f"receipt: {name}")

    canonical_approval = {
        "approver_identity": "ed3c",
        "approver_kind": "HUMAN",
        "approval_subject_commit_sha": "b" * 40,
        "approval_receipt_digest": "sha256:" + "1" * 64,
        "generated_by_agent": False,
        "review_ref": "https://github.com/ed3c/skills-shared/pull/134#pullrequestreview-1",
        "readback_source": "GITHUB_API",
    }

    def to_canonical(r: dict[str, Any]) -> None:
        r["from_state"] = "ADMITTED"
        r["to_state"] = "CANONICAL"
        r["approval"] = copy.deepcopy(canonical_approval)
        r["writebacks"] = [
            {"destination_id": "root-context", "scope": "ROOT_GLOBAL", "mode": "APPEND"}
        ]

    # A canonical promotion must be admitted when fully evidenced, or the
    # mutations below would be passing for the wrong reason.
    canonical = copy.deepcopy(receipt)
    to_canonical(canonical)
    try:
        validate_receipt(canonical, contract, contract_raw, ledger)
    except Refused as error:
        print(f"SELFTEST RED: canonical promotion refused: {error}", file=sys.stderr)
        return 2

    receipt_case("PR opened promoted straight to a durable writeback",
                 lambda r: (r.__setitem__("from_state", "CANDIDATE"),
                            r.__setitem__("to_state", "PROPOSED"),
                            r.__setitem__("evaluator_receipts", []),
                            r.__setitem__("merge_subject", None)))
    receipt_case("CI green without an owning exact-head receipt",
                 lambda r: r.__setitem__("evaluator_receipts", []))
    receipt_case("old receipt applied to a new commit",
                 lambda r: r["evaluator_receipts"][0].__setitem__("subject_commit_sha", "e" * 40))
    receipt_case("evaluator ran against a different tree",
                 lambda r: r["evaluator_receipts"][0].__setitem__("subject_tree_sha", "e" * 40))
    receipt_case("failing evaluator inside a promotion",
                 lambda r: r["evaluator_receipts"][0].__setitem__("status", "FAIL"))
    receipt_case("duplicate evaluator id padding coverage",
                 lambda r: r["evaluator_receipts"].append(copy.deepcopy(r["evaluator_receipts"][0])))
    receipt_case("mutable evaluator version",
                 lambda r: r["evaluator_receipts"][0].__setitem__("evaluator_version", "latest"))
    receipt_case("merge subject admitting a different candidate",
                 lambda r: r["merge_subject"].__setitem__("candidate_head_sha", "9" * 40))
    receipt_case("merge subject admitting a different candidate tree",
                 lambda r: r["merge_subject"].__setitem__("candidate_tree_sha", "9" * 40))
    receipt_case("merge subject in a different repository",
                 lambda r: r["merge_subject"].__setitem__("repository", "ed3c/other"))
    receipt_case("forge readback observing a different commit",
                 lambda r: r["merge_subject"]["forge_readback"].__setitem__(
                     "observed_at_commit_sha", "9" * 40))
    receipt_case("release artifact digest repeating the merge commit",
                 lambda r: r["merge_subject"].__setitem__("release_artifact", {
                     "artifact_id": "v1", "artifact_digest": "f" * 40}))
    receipt_case("root write reached from ADMITTED",
                 lambda r: r.__setitem__("writebacks", [
                     {"destination_id": "root-context", "scope": "ROOT_GLOBAL", "mode": "APPEND"}]))
    receipt_case("root override flag with no human approval",
                 lambda r: r.__setitem__("caller_flags", ["--allow-root-override"]))
    receipt_case("agent-created approval labelled HUMAN",
                 lambda r: (to_canonical(r),
                            r["approval"].__setitem__("approver_kind", "AGENT")))
    receipt_case("approval admitting it was generated by an agent",
                 lambda r: (to_canonical(r),
                            r["approval"].__setitem__("generated_by_agent", True)))
    receipt_case("approval with no review reference to read back",
                 lambda r: (to_canonical(r),
                            r["approval"].__setitem__("review_ref", "   ")))
    receipt_case("approval for another head",
                 lambda r: (to_canonical(r),
                            r["approval"].__setitem__("approval_subject_commit_sha", "9" * 40)))
    receipt_case("canonical promotion with no approval at all",
                 lambda r: (to_canonical(r), r.__setitem__("approval", None)))
    receipt_case("supersede writeback without naming what it replaces",
                 lambda r: r["writebacks"][0].__setitem__("mode", "SUPERSEDE"))
    receipt_case("undeclared writeback destination",
                 lambda r: r.__setitem__("writebacks", [
                     {"destination_id": "somewhere-else", "scope": "MODULE", "mode": "APPEND"}]))
    receipt_case("destination scope claimed differently than declared",
                 lambda r: r.__setitem__("writebacks", [
                     {"destination_id": "module-notes", "scope": "PROJECT", "mode": "APPEND"}]))
    receipt_case("revoked intent still projecting",
                 lambda r: (r.__setitem__("from_state", "CANONICAL"),
                            r.__setitem__("to_state", "REVOKED"),
                            r.__setitem__("approval", copy.deepcopy(canonical_approval)),
                            r.__setitem__("merge_subject", None),
                            r.__setitem__("writebacks", [
                                {"destination_id": "module-notes", "scope": "MODULE",
                                 "mode": "APPEND"}])))
    receipt_case("superseded transition without a target",
                 lambda r: (r.__setitem__("from_state", "CANONICAL"),
                            r.__setitem__("to_state", "SUPERSEDED"),
                            r.__setitem__("merge_subject", None),
                            r.__setitem__("writebacks", [])))
    receipt_case("undeclared transition",
                 lambda r: (r.__setitem__("from_state", "HYPOTHESIS"),
                            r.__setitem__("to_state", "CANONICAL")))
    receipt_case("receipt issued under different contract bytes",
                 lambda r: r.__setitem__("contract_digest", "sha256:" + "2" * 64))
    receipt_case("receipt naming a different contract",
                 lambda r: r.__setitem__("contract_id", "some-other-contract"))
    receipt_case("private reasoning persisted in the receipt",
                 lambda r: r.__setitem__("chain_of_thought", "why I promoted this"))
    receipt_case("private reasoning nested inside an evaluator run",
                 lambda r: r["evaluator_receipts"][0].__setitem__("reasoning", "looked fine"))

    superseding = {
        "receipt_id": "IPR-FIXTURE-PRIOR",
        "receipt_digest": "sha256:" + "5" * 64,
        "predecessor_state": "CANONICAL",
        "predecessor_subject_commit_sha": "3" * 40,
    }

    def to_supersede(r: dict[str, Any]) -> None:
        r["from_state"] = "CANONICAL"
        r["to_state"] = "SUPERSEDED"
        r["merge_subject"] = None
        r["writebacks"] = []
        r["supersedes"] = copy.deepcopy(superseding)

    valid_supersede = copy.deepcopy(receipt)
    to_supersede(valid_supersede)
    try:
        validate_receipt(valid_supersede, contract, contract_raw, ledger)
    except Refused as error:
        print(f"SELFTEST RED: valid supersession refused: {error}", file=sys.stderr)
        return 2

    receipt_case("supersession target absent from the ledger",
                 lambda r: (to_supersede(r),
                            r["supersedes"].__setitem__("receipt_id", "IPR-NOT-THERE")))
    receipt_case("supersession target not current",
                 lambda r: to_supersede(r),
                 [{**ledger[0], "current": False}])
    receipt_case("supersession target digest mismatched",
                 lambda r: (to_supersede(r),
                            r["supersedes"].__setitem__("receipt_digest", "sha256:" + "4" * 64)))
    receipt_case("supersession naming the wrong predecessor state",
                 lambda r: (to_supersede(r),
                            r["supersedes"].__setitem__("predecessor_state", "ADMITTED")))
    receipt_case("supersession naming a different predecessor subject",
                 lambda r: (to_supersede(r),
                            r["supersedes"].__setitem__("predecessor_subject_commit_sha", "2" * 40)))
    receipt_case("supersession crossing intents",
                 lambda r: to_supersede(r),
                 [{**ledger[0], "intent_id": "MI-OTHER-INTENT"}])
    receipt_case("supersession with no ledger to confirm it",
                 lambda r: to_supersede(r), None)
    receipt_case("terminal intent still marked current in the ledger",
                 lambda r: to_supersede(r),
                 [ledger[0], {"receipt_id": "IPR-FIXTURE-001",
                              "receipt_digest": "sha256:" + "5" * 64,
                              "intent_id": "MI-CTL-EVIDENCE", "state": "SUPERSEDED",
                              "subject_commit_sha": "b" * 40, "current": True}])

    if survived:
        for name in survived:
            print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
        return 2

    print(f"SELFTEST GREEN: canonical, canonical-promotion and supersession "
          f"admitted; {len(contract_mutations) + 37} mutations refused")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("contract", "receipt", "selftest"))
    parser.add_argument("subject", type=Path, nargs="?")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--ledger", type=Path,
                        help="append-only supersession ledger; required to "
                             "validate a receipt that supersedes a predecessor")
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
            ledger = None
            if args.ledger is not None:
                try:
                    raw = args.ledger.read_bytes()
                except OSError as error:
                    raise Unusable(f"unreadable ledger: {args.ledger}: {error}") from error
                try:
                    ledger = json.loads(raw.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as error:
                    raise Unusable(f"unparseable ledger: {error}") from error
                if not isinstance(ledger, list):
                    raise Unusable("ledger must be a list of entries")
            validate_receipt(receipt, contract, contract_raw, ledger)
    except Unusable as error:
        # Distinct from a refusal: nothing was evaluated, so nothing was
        # refused. Collapsing the two makes a bad path read as a bad promotion.
        print(f"FATAL intent-promotion input: {error}", file=sys.stderr)
        return 64
    except Refused as error:
        print(f"INTENT PROMOTION RED: {error}", file=sys.stderr)
        return 2

    print(f"INTENT PROMOTION GREEN: {args.kind} verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
