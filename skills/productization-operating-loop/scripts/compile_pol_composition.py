#!/usr/bin/env python3
"""Compose one C0 program and four admitted lane artifacts into six byte-stable documents.

    pol/composition-input/v1
      -> pol/productization-program/v1        the composed program
      -> pol/closure-matrix/v1                per-cell state, unknowns preserved
      -> prel/session-dispatch-request/v1     the bounded Tech Lead packets
      -> pol/session-dag/v1                   the graph over those packets
      -> prel/external-projection-registry/v1 projection requests, authority false
      -> pol/outcome-foldback-request/v1      the decision stub, decision empty

Six artifacts, one input, one pass. `--artifact NAME` selects which one is
written; every guard below runs on every invocation, because a refusal is a
property of the composition and not of the document somebody asked for.

What this compiler is not allowed to do
---------------------------------------
It makes no network call and opens no socket: the whole job is a pure function
from the input bytes to the output bytes, and `--selftest` asserts that no
network module is even named in this file. It has no clock, so no output
carries a timestamp this file invented -- policy staleness is read from the
record's own `terminal` field rather than computed against now, and a
wall-clock sentinel anywhere in the input is refused rather than filled in.
And it decides nothing: the outcome disposition is emitted empty, the four
options are pinned in full, and a closure cell whose claims disagree stays a
CONTRADICTION.

Pinned on every output regardless of the input
----------------------------------------------
    program_state           ISSUE_AND_SESSION_DAG_BOUND
    evidence_ceiling        DETERMINISTIC_COMPOSITION
    lifecycle_state         LAUNCH_REQUESTED       (dispatch request and DAG)
    running_session         null                   (dispatch request)
    observed_sessions       null                   (DAG)
    human_admit/merge/release lanes  HUMAN_ADMIT_REQUIRED, rung NONE
    every authority constant        false
    projection read_back            NOT_EXERCISED, all comparisons null
    foldback decision               "" with decided_by null and all four options

How the ladder is computed
--------------------------
Rung by rung, in order, from the input receipts alone. A rung is REACHED only
when a receipt of its own kind is present *and* its predecessor is REACHED. A
rung whose own receipt is present but whose predecessor is not REACHED is
NOT_REACHED with the receipt still attached -- the receipt is evidence of
something, and dropping it would hide the promotion this rule exists to
refuse. A rung with no receipt of its kind is NOT_EXERCISED. Nothing in the
input can raise a rung directly: an input that asserts `evidence_ladder` or a
lane artifact that claims a rung the receipts do not earn is refused
(K08_RUNG_PROMOTED_ABOVE_RECEIPTS).

How lane states are decided
---------------------------
    market, user            the artifact's own lane_state, verbatim
    commercial              PASS if a payment rung was earned, else UNKNOWN,
                            because a hypothesis contract means the lane was
                            entered and the answer is not established
    policy                  PASS when terminal is CURRENT and nothing changed;
                            HUMAN_ADMIT_REQUIRED when a change was detected,
                            because a changed rule is routed, never cleared
    source, mechanism,      PASS when the lane earned one of its own rungs,
    technical, runtime      UNKNOWN when it has a receipt but earned no rung,
                            NOT_EXERCISED when it has neither
    rights                  UNKNOWN: no Stage-1 lane asks the question, so the
                            answer is not known rather than clear
    human_admit, merge,     HUMAN_ADMIT_REQUIRED, rung NONE, pinned
    release

Refusal codes (exit 2)
----------------------
    K01_STALE_LANE_ARTIFACT           a lane artifact bound to another commit,
                                      or a policy record whose terminal is not
                                      CURRENT
    K02_MISSING_MANDATORY_LANE        market, user, commercial or policy absent
                                      or carrying the wrong schema identity
    K03_NONDETERMINISTIC_INPUT        a wall-clock sentinel where a value the
                                      input was supposed to supply belongs
    K04_AUTHORITY_WIDENING            an authority constant set true, an empty
                                      Human-owned operations list, or an input
                                      asserting the lanes the compiler computes
    K05_HIDDEN_DEPENDENCY             an edge or a parent naming an atom that
                                      is not in the graph
    K06_OVERLAPPING_WRITER_LEASE      two packets claiming the same path
    K07_CONTRADICTION_DROPPED         a cell asking to be reconciled, or
                                      asserting its own state
    K08_RUNG_PROMOTED_ABOVE_RECEIPTS  a rung claimed above what the receipts
                                      earn

Exits: 0 green, 2 the composition is refused with a named code, 64 the input
is malformed, 70 `--selftest` cannot run because jsonschema is absent.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
SKILLS = SKILL.parent

INPUT_SCHEMA = "pol/composition-input/v1"
PROGRAM_STATE = "ISSUE_AND_SESSION_DAG_BOUND"
EVIDENCE_CEILING = "DETERMINISTIC_COMPOSITION"

PROGRAM_AUTHORITY = {
    "merge": False,
    "release": False,
    "product_truth": False,
    "user_truth": False,
    "paid_truth": False,
    "rights_admission": False,
    "provider_execution": False,
    "production": False,
}
DISPATCH_AUTHORITY = {"merge": False, "permission": False, "secret": False, "production": False}
PROJECTION_AUTHORITY = {
    "implementation": False,
    "completion": False,
    "product_truth": False,
    "merge": False,
    "release": False,
}
FOLDBACK_DECISIONS = ["ITERATE", "KILL", "NARROW", "PRESERVE"]

MANDATORY_LANES = {
    "market": "pol/market-lane/v1",
    "user": "pol/user-lane/v1",
    "commercial": "pol/commercial-lane/v1",
    "policy": "pol/policy-lane/v1",
}

# rung key, the one receipt kind admissible for it, the rung's name
LADDER = [
    ("source_found", "SOURCE_LOCATED", "SOURCE_FOUND"),
    ("source_verified", "INDEPENDENT_SOURCE_READBACK", "SOURCE_VERIFIED"),
    ("job_supported", "JOB_EVIDENCE_TRACE", "JOB_SUPPORTED"),
    ("wedge_supported", "COMPARATOR_CASE_TRACE", "WEDGE_SUPPORTED"),
    ("mechanism_reproduced", "MECHANISM_REPLAY", "MECHANISM_REPRODUCED"),
    ("mvp_tech_verified", "DETERMINISTIC_COMMAND_EXIT", "MVP_TECH_VERIFIED"),
    ("live_workflow_verified", "LIVE_WORKFLOW_TRACE", "LIVE_WORKFLOW_VERIFIED"),
    ("user_validated", "REAL_USER_OBSERVATION", "USER_VALIDATED"),
    ("paid_validated", "PAYMENT_RECORD", "PAID_VALIDATED"),
    ("repeatable_commercial", "REPEATED_PAYMENT_SERIES", "REPEATABLE_COMMERCIAL"),
]
RECEIPT_KINDS = {kind for _, kind, _ in LADDER}

# Which rungs each lane may raise. A lane not listed raises none.
LANE_RUNGS = {
    "source": ["source_found", "source_verified"],
    "market": ["job_supported", "wedge_supported"],
    "mechanism": ["mechanism_reproduced"],
    "technical": ["mvp_tech_verified"],
    "runtime": ["live_workflow_verified"],
    "user": ["user_validated"],
    "commercial": ["paid_validated", "repeatable_commercial"],
}
RECEIPT_DERIVED_LANES = ("source", "mechanism", "technical", "runtime")
HUMAN_LANES = ("human_admit", "merge", "release")

# Strings that mean "fill this in from the clock". None of them may reach an
# output, because two runs of the same input would then differ.
WALL_CLOCK_SENTINELS = {"AUTO", "NOW", "$NOW", "${NOW}", "TODAY", "<timestamp>", "CURRENT_TIME"}

UNRESOLVED_STATES = {"CONTRADICTION", "UNKNOWN", "BLOCKED", "HUMAN_ADMIT_REQUIRED"}

ARTIFACTS = (
    "program",
    "closure-matrix",
    "session-dag",
    "dispatch-request",
    "external-projections",
    "outcome-foldback",
)


class Refused(Exception):
    """The composition cannot be produced without dropping something the input
    carried or claiming something it did not earn. Always carries a named code."""


class Unusable(Exception):
    """The input is not a composition input at all."""


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def dedupe_sorted(items: list[Any]) -> list[Any]:
    seen: list[Any] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    try:
        return sorted(seen)
    except TypeError:
        return sorted(seen, key=json.dumps)


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Unusable(f"unreadable input {path}: {error}") from error
    if not isinstance(value, dict):
        raise Unusable(f"{path}: root must be an object")
    return value


def require(draft: dict[str, Any], key: str) -> Any:
    if key not in draft:
        raise Unusable(f"composition input has no {key!r}")
    return draft[key]


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------


def check_no_wall_clock(node: Any, trail: str = "$") -> None:
    if isinstance(node, str):
        if node.strip() in WALL_CLOCK_SENTINELS:
            raise Refused(
                f"K03_NONDETERMINISTIC_INPUT {trail} is {node!r}, which asks this "
                f"compiler to read a clock it does not have; two runs of the same "
                f"input would then differ. Supply the value or leave the field out"
            )
    elif isinstance(node, dict):
        for key, value in node.items():
            check_no_wall_clock(value, f"{trail}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            check_no_wall_clock(value, f"{trail}[{index}]")


def check_no_authority_widening(node: Any, trail: str = "$") -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "authority" and isinstance(value, dict):
                granted = sorted(name for name, flag in value.items() if flag is True)
                if granted:
                    raise Refused(
                        f"K04_AUTHORITY_WIDENING {trail}.authority grants {granted}; "
                        f"every authority constant in this method is false, and a "
                        f"composition cannot be the step that turns one true"
                    )
            check_no_authority_widening(value, f"{trail}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            check_no_authority_widening(value, f"{trail}[{index}]")


def check_input_asserts_nothing_computed(draft: dict[str, Any]) -> None:
    for key in ("lanes", "evidence_ladder"):
        if key in draft:
            code = "K04_AUTHORITY_WIDENING" if key == "lanes" else "K08_RUNG_PROMOTED_ABOVE_RECEIPTS"
            raise Refused(
                f"{code} the input asserts {key!r}, which this compiler computes "
                f"from the receipts. An input that can write it is an input that "
                f"can raise a rung nothing earned"
            )
    if not draft.get("human_owned_operations"):
        raise Refused(
            "K04_AUTHORITY_WIDENING human_owned_operations is empty; a composition "
            "that lists no Human-owned operation has either not looked or has "
            "quietly assigned itself merge"
        )


def check_lanes(draft: dict[str, Any], subject_commit: str) -> dict[str, dict]:
    artifacts = draft.get("lane_artifacts")
    if not isinstance(artifacts, dict):
        raise Unusable("composition input has no lane_artifacts object")
    bound: dict[str, dict] = {}
    for lane, identity in MANDATORY_LANES.items():
        record = artifacts.get(lane)
        if not isinstance(record, dict):
            raise Refused(
                f"K02_MISSING_MANDATORY_LANE {lane} is absent; the four Stage-1 "
                f"lanes are mandatory, and composing three of them silently "
                f"reports the fourth as clean"
            )
        if record.get("schema") != identity:
            raise Refused(
                f"K02_MISSING_MANDATORY_LANE {lane} carries schema "
                f"{record.get('schema')!r}, not {identity!r}"
            )
        if record.get("subject_commit") != subject_commit:
            raise Refused(
                f"K01_STALE_LANE_ARTIFACT {lane} is bound to "
                f"{record.get('subject_commit')!r}, not to the program subject "
                f"{subject_commit!r}; a lane read at another commit describes "
                f"another subject"
            )
        bound[lane] = record
    terminal = bound["policy"].get("terminal")
    if terminal != "CURRENT":
        raise Refused(
            f"K01_STALE_LANE_ARTIFACT the policy record's terminal is {terminal!r}. "
            f"This compiler has no clock and does not compute staleness against "
            f"now; it reads the record's own terminal, and only CURRENT composes"
        )
    return bound


def check_graph(atoms: list[dict]) -> None:
    ids = [atom["atom_id"] for atom in atoms]
    if len(ids) != len(set(ids)):
        raise Unusable(f"duplicate atom id(s) in {sorted(ids)}")
    known = set(ids)
    for atom in atoms:
        named = list(atom.get("start_after") or []) + list(atom.get("complete_after") or [])
        parent = atom.get("parent_atom_id")
        if parent is not None:
            named.append(parent)
        for other in named:
            if other not in known:
                raise Refused(
                    f"K05_HIDDEN_DEPENDENCY {atom['atom_id']} depends on {other!r}, "
                    f"which is not one of the declared atoms. A dependency that is "
                    f"real and not in the graph is one the scheduler cannot see"
                )
        if atom.get("relation") == "CHILD" and parent is None:
            raise Refused(
                f"K05_HIDDEN_DEPENDENCY {atom['atom_id']} is a CHILD with no parent; "
                f"the subject it consumes is produced by something outside the graph"
            )
    for index, first in enumerate(atoms):
        for second in atoms[index + 1 :]:
            shared = overlapping_paths(first, second)
            if shared:
                raise Refused(
                    f"K06_OVERLAPPING_WRITER_LEASE {first['atom_id']} and "
                    f"{second['atom_id']} both claim {shared}; two writers on one "
                    f"path is not a parallel packet, it is a race"
                )
            resources = sorted(
                set(first.get("resources") or []) & set(second.get("resources") or [])
            )
            if resources:
                raise Refused(
                    f"K06_OVERLAPPING_WRITER_LEASE {first['atom_id']} and "
                    f"{second['atom_id']} both claim resource(s) {resources}"
                )


def normalise_path(value: str) -> str:
    return value.rstrip("/").removesuffix("/**").rstrip("/")


def overlapping_paths(first: dict, second: dict) -> list[str]:
    shared: list[str] = []
    for left in first.get("lease_paths") or []:
        for right in second.get("lease_paths") or []:
            a, b = normalise_path(left), normalise_path(right)
            if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                shared.append(left if len(a) >= len(b) else right)
    return dedupe_sorted(shared)


# --------------------------------------------------------------------------
# the ladder and the lanes
# --------------------------------------------------------------------------


def build_ladder(receipts: list[dict], subject_commit: str) -> dict[str, dict]:
    for receipt in receipts:
        if receipt.get("kind") not in RECEIPT_KINDS:
            raise Unusable(f"receipt of unknown kind {receipt.get('kind')!r}")
    ladder: dict[str, dict] = {}
    predecessor_reached = True
    for key, kind, _name in LADDER:
        own = dedupe_sorted(
            [
                {
                    "kind": kind,
                    "subject_commit": receipt.get("subject_commit", subject_commit),
                    **({"note": receipt["note"]} if receipt.get("note") else {}),
                }
                for receipt in receipts
                if receipt.get("kind") == kind
            ]
        )
        if own and predecessor_reached:
            state = "REACHED"
        elif own:
            state = "NOT_REACHED"
        else:
            state = "NOT_EXERCISED"
        ladder[key] = {"state": state, "receipts": own}
        predecessor_reached = state == "REACHED"
    return ladder


def earned_rung(ladder: dict[str, dict], lane: str) -> str:
    highest = "NONE"
    for key, _kind, name in LADDER:
        if key in LANE_RUNGS.get(lane, []) and ladder[key]["state"] == "REACHED":
            highest = name
    return highest


def check_no_rung_promotion(ladder: dict[str, dict], lanes: dict[str, dict]) -> None:
    for lane in ("market", "user"):
        claimed = lanes[lane].get("highest_rung_reached", "NONE")
        if claimed == "NONE":
            continue
        earned = earned_rung(ladder, lane)
        if claimed != earned:
            raise Refused(
                f"K08_RUNG_PROMOTED_ABOVE_RECEIPTS the {lane} artifact claims "
                f"{claimed}, and the receipts earn {earned}. The ladder is computed "
                f"from receipts, never copied from the artifact that wants the rung"
            )


def build_lanes(ladder: dict[str, dict], artifacts: dict[str, dict]) -> dict[str, dict]:
    lanes: dict[str, dict] = {}

    for lane in RECEIPT_DERIVED_LANES:
        rung = earned_rung(ladder, lane)
        carries_receipt = any(ladder[key]["receipts"] for key in LANE_RUNGS.get(lane, []))
        if rung != "NONE":
            state = "PASS"
        elif carries_receipt:
            state = "UNKNOWN"
        else:
            state = "NOT_EXERCISED"
        lanes[lane] = {"state": state, "highest_rung_reached": rung}

    lanes["market"] = {
        "state": artifacts["market"]["lane_state"],
        "highest_rung_reached": earned_rung(ladder, "market"),
    }
    lanes["user"] = {
        "state": artifacts["user"]["lane_state"],
        "highest_rung_reached": earned_rung(ladder, "user"),
    }
    commercial_rung = earned_rung(ladder, "commercial")
    lanes["commercial"] = {
        "state": "PASS" if commercial_rung != "NONE" else "UNKNOWN",
        "highest_rung_reached": commercial_rung,
        "note": "a commercial hypothesis was supplied; no payment receipt earns a rung",
    }
    changed = bool(artifacts["policy"].get("change", {}).get("changed"))
    lanes["policy"] = {
        "state": "HUMAN_ADMIT_REQUIRED" if changed else "PASS",
        "highest_rung_reached": "NONE",
        "note": "a detected change is routed to the people who own it, never cleared here"
        if changed
        else "terminal CURRENT with no detected change",
    }
    lanes["rights"] = {
        "state": "UNKNOWN",
        "highest_rung_reached": "NONE",
        "note": "no Stage-1 lane asks the rights question, so the answer is not known rather than clear",
    }
    for lane in HUMAN_LANES:
        lanes[lane] = {"state": "HUMAN_ADMIT_REQUIRED", "highest_rung_reached": "NONE"}
    return lanes


# --------------------------------------------------------------------------
# builders
# --------------------------------------------------------------------------


def build_closure_matrix(draft: dict, subject_commit: str) -> dict[str, Any]:
    cells: list[dict] = []
    for raw in draft.get("closure_cells") or []:
        cell_id = raw.get("cell_id", "<unnamed>")
        if raw.get("reconcile"):
            raise Refused(
                f"K07_CONTRADICTION_DROPPED {cell_id} asks to be reconciled. "
                f"Choosing between two lane artifacts is a reading, and this "
                f"compiler emits the disagreement instead of resolving it"
            )
        if "state" in raw:
            raise Refused(
                f"K07_CONTRADICTION_DROPPED {cell_id} asserts its own state "
                f"{raw['state']!r}; the state is computed from the claims, so an "
                f"asserted one can only differ from them by hiding one"
            )
        claims = sorted(
            (
                {
                    "source_record": claim["source_record"],
                    "statement": claim["statement"],
                    "disposition": claim["disposition"],
                }
                for claim in raw["claims"]
            ),
            key=json.dumps,
        )
        dispositions = {claim["disposition"] for claim in claims}
        if {"CONFIRMED", "CONTRADICTED"} <= dispositions:
            state = "CONTRADICTION"
        elif "UNKNOWN" in dispositions:
            state = "UNKNOWN"
        elif dispositions == {"CONTRADICTED"}:
            state = "FAIL"
        else:
            state = "PASS"
        cells.append(
            {
                "cell_id": raw["cell_id"],
                "lane": raw["lane"],
                "question": raw["question"],
                "state": state,
                "evidence_ceiling": raw["evidence_ceiling"],
                "claims": claims,
            }
        )
    cells.append(
        {
            "cell_id": "POL-CELL-999",
            "lane": "HUMAN_ADMIT",
            "question": "does a person admit this composition and everything below it",
            "state": "HUMAN_ADMIT_REQUIRED",
            "evidence_ceiling": EVIDENCE_CEILING,
            "claims": [
                {
                    "source_record": draft["program_id"],
                    "statement": "composition arranged the claims it was given and admitted none of them",
                    "disposition": "UNKNOWN",
                }
            ],
        }
    )
    cells.sort(key=lambda cell: cell["cell_id"])
    return {
        "schema": "pol/closure-matrix/v1",
        "matrix_id": draft["matrix_id"],
        "subject_commit": subject_commit,
        "evidence_ceiling": EVIDENCE_CEILING,
        "cells": cells,
        "unresolved_cell_ids": sorted(
            cell["cell_id"] for cell in cells if cell["state"] in UNRESOLVED_STATES
        ),
        "authority": dict(PROGRAM_AUTHORITY),
        "human_owned_operations": dedupe_sorted(list(draft["human_owned_operations"])),
    }


def build_program(draft: dict, lanes: dict, ladder: dict, atoms: list[dict]) -> dict[str, Any]:
    subject = draft["subject"]
    return {
        "schema": "pol/productization-program/v1",
        "program_id": draft["program_id"],
        "subject_commit": subject["commit"],
        "subject_tree": subject["tree"],
        "program_state": PROGRAM_STATE,
        "evidence_ceiling": EVIDENCE_CEILING,
        "lanes": lanes,
        "evidence_ladder": ladder,
        "method_refs": sorted(
            (
                {
                    "skill_name": ref["skill_name"],
                    "skill_md_sha256": ref["skill_md_sha256"],
                    "skill_md_bytes": ref["skill_md_bytes"],
                    "observed_commit": ref["observed_commit"],
                    "declared_interface": ref["declared_interface"],
                }
                for ref in draft["method_refs"]
            ),
            key=lambda ref: ref["skill_name"],
        ),
        "start_dependencies": sorted(
            (
                {
                    "atom_id": atom["atom_id"],
                    "satisfied_by": "READABLE_INTERFACE",
                    "interface_ref": atom["interface_ref"],
                }
                for atom in atoms
            ),
            key=lambda row: row["atom_id"],
        ),
        "completion_dependencies": sorted(
            (
                {
                    "atom_id": atom["atom_id"],
                    "satisfied_by": "ADMITTED_RECEIPT",
                    "receipt_ref": atom["receipt_ref"],
                }
                for atom in atoms
                if atom.get("receipt_ref")
            ),
            key=lambda row: row["atom_id"],
        ),
        "human_owned_operations": dedupe_sorted(list(draft["human_owned_operations"])),
        "authority": dict(PROGRAM_AUTHORITY),
        "rollback": {"base_commit": draft["rollback_commit"]},
    }


def build_dispatch_request(draft: dict, atoms: list[dict]) -> dict[str, Any]:
    subject = draft["subject"]
    by_atom = {atom["atom_id"]: atom for atom in atoms}
    requests = []
    for atom in atoms:
        parent = atom.get("parent_atom_id")
        requests.append(
            {
                "id": atom["request_id"],
                "relation": atom["relation"],
                "parent_request_id": by_atom[parent]["request_id"] if parent else None,
                "base": {"commit": subject["commit"], "tree": subject["tree"]},
                "branch": atom["branch"],
                "lease": {
                    "paths": dedupe_sorted(list(atom["lease_paths"])),
                    "resources": dedupe_sorted(list(atom.get("resources") or [])),
                },
                # A start edge is satisfied by reading an interface, so its
                # receipt field carries that interface. A completion edge is
                # satisfied by an admitted receipt, and no session has run, so
                # its receipt is null and the obligation stays open.
                "start_dependencies": sorted(
                    (
                        {
                            "subject": other,
                            "digest": subject["commit"],
                            "receipt": by_atom[other]["interface_ref"],
                        }
                        for other in atom.get("start_after") or []
                    ),
                    key=lambda row: row["subject"],
                ),
                "completion_dependencies": sorted(
                    (
                        {"subject": other, "digest": subject["commit"], "receipt": None}
                        for other in atom.get("complete_after") or []
                    ),
                    key=lambda row: row["subject"],
                ),
                "evidence_ceiling": {
                    "highest_claimable_lane": atom["highest_claimable_lane"],
                    "cannot_establish": dedupe_sorted(list(atom["cannot_establish"])),
                },
                "oracles": sorted(
                    (dict(oracle) for oracle in atom["oracles"]), key=lambda row: row["id"]
                ),
                "negative_controls": dedupe_sorted(list(atom["negative_controls"])),
                "rollback": {"subject": atom["atom_id"], "commit": draft["rollback_commit"]},
                "stop_states": dedupe_sorted(list(atom["stop_states"])),
                "output_paths": dedupe_sorted(list(atom["output_paths"])),
                "human_owned_operations": dedupe_sorted(list(draft["human_owned_operations"])),
                "requests_private_reasoning": False,
                "authority": dict(DISPATCH_AUTHORITY),
                "consumer_binding": dict(atom.get("consumer_binding") or {}),
            }
        )
    return {
        "schema": "prel/session-dispatch-request/v1",
        "lifecycle_state": "LAUNCH_REQUESTED",
        "running_session": None,
        "refusal_classes": dedupe_sorted(list(draft["refusal_classes"])),
        "requests": sorted(requests, key=lambda row: row["id"]),
    }


def build_session_dag(draft: dict, atoms: list[dict], dispatch: dict) -> dict[str, Any]:
    return {
        "schema": "pol/session-dag/v1",
        "dag_id": draft["dag_id"],
        "subject_commit": draft["subject"]["commit"],
        "lifecycle_state": "LAUNCH_REQUESTED",
        "observed_sessions": None,
        "dispatch_request_ref": {
            "schema": "prel/session-dispatch-request/v1",
            "path": draft["dispatch_request_path"],
            "sha256": digest(dispatch),
        },
        "nodes": sorted(
            (
                {
                    "node_id": atom["atom_id"],
                    "request_id": atom["request_id"],
                    "relation": atom["relation"],
                    "parent_node_id": atom.get("parent_atom_id"),
                    "lease_paths": dedupe_sorted(list(atom["lease_paths"])),
                    "evidence_ceiling": atom["evidence_ceiling"],
                }
                for atom in atoms
            ),
            key=lambda node: node["node_id"],
        ),
        "start_edges": sorted(
            (
                {
                    "from_node_id": other,
                    "to_node_id": atom["atom_id"],
                    "satisfied_by": "READABLE_INTERFACE",
                }
                for atom in atoms
                for other in atom.get("start_after") or []
            ),
            key=json.dumps,
        ),
        "completion_edges": sorted(
            (
                {
                    "from_node_id": other,
                    "to_node_id": atom["atom_id"],
                    "satisfied_by": "ADMITTED_RECEIPT",
                }
                for atom in atoms
                for other in atom.get("complete_after") or []
            ),
            key=json.dumps,
        ),
        "authority": dict(PROGRAM_AUTHORITY),
        "human_owned_operations": dedupe_sorted(list(draft["human_owned_operations"])),
    }


def build_external_projections(draft: dict) -> dict[str, Any]:
    entries = draft.get("projections") or []
    if not entries:
        raise Unusable("projections is empty; an empty registry projects nothing")
    return {
        "schema": "prel/external-projection-registry/v1",
        "authority": dict(PROJECTION_AUTHORITY),
        "evidence_ceiling": "HUMAN_PROJECTION",
        "entries": sorted(
            (
                {
                    "id": entry["id"],
                    "external_kind": entry["external_kind"],
                    "external_id": entry["external_id"],
                    "observed_revision": entry["observed_revision"],
                    "export_digest": entry["export_digest"],
                    "canonical_subjects": sorted(
                        (dict(subject) for subject in entry["canonical_subjects"]),
                        key=json.dumps,
                    ),
                    "backlinks": dedupe_sorted(list(entry["backlinks"])),
                    # Pinned: this compiler read nothing back, and a read-back
                    # state it invented would be the projection asserting its
                    # own currency.
                    "read_back": {
                        "state": "NOT_EXERCISED",
                        "compared_revision": None,
                        "compared_digest": None,
                        "observed_at": None,
                    },
                    "authority": dict(PROJECTION_AUTHORITY),
                }
                for entry in entries
            ),
            key=lambda entry: entry["id"],
        ),
        "human_owned_operations": dedupe_sorted(list(draft["human_owned_operations"])),
    }


def build_outcome_foldback(draft: dict, matrix: dict) -> dict[str, Any]:
    open_cells = [cell for cell in matrix["cells"] if cell["cell_id"] in matrix["unresolved_cell_ids"]]
    questions = [
        {
            "question_id": f"POL-FBQ-{index + 1:03d}",
            "cell_id": cell["cell_id"],
            "lane": cell["lane"],
            "question": cell["question"],
            "unresolved_input": cell["state"],
        }
        for index, cell in enumerate(open_cells)
    ]
    return {
        "schema": "pol/outcome-foldback-request/v1",
        "request_id": draft["foldback_id"],
        "subject_commit": draft["subject"]["commit"],
        "evidence_ceiling": EVIDENCE_CEILING,
        "decision": {
            "available_decisions": list(FOLDBACK_DECISIONS),
            "decision": "",
            "decided_by": None,
            "decision_owner": draft["decision_owner"],
        },
        "read_back_questions": questions,
        "authority": dict(PROGRAM_AUTHORITY),
        "human_owned_operations": dedupe_sorted(list(draft["human_owned_operations"])),
    }


# --------------------------------------------------------------------------
# composition
# --------------------------------------------------------------------------


def compile_all(draft: dict[str, Any]) -> dict[str, dict]:
    if draft.get("schema") != INPUT_SCHEMA:
        raise Unusable(f"composition input must be a {INPUT_SCHEMA} draft")
    check_no_wall_clock(draft)
    check_no_authority_widening(draft)
    check_input_asserts_nothing_computed(draft)

    subject = require(draft, "subject")
    subject_commit = subject["commit"]
    artifacts = check_lanes(draft, subject_commit)

    atoms = list(require(draft, "atoms"))
    if not atoms:
        raise Unusable("atoms is empty; a composition with no packet launches nothing")
    check_graph(atoms)

    ladder = build_ladder(list(draft.get("receipts") or []), subject_commit)
    check_no_rung_promotion(ladder, artifacts)
    lanes = build_lanes(ladder, artifacts)

    atoms = sorted(atoms, key=lambda atom: atom["atom_id"])
    matrix = build_closure_matrix(draft, subject_commit)
    dispatch = build_dispatch_request(draft, atoms)
    return {
        "program": build_program(draft, lanes, ladder, atoms),
        "closure-matrix": matrix,
        "session-dag": build_session_dag(draft, atoms, dispatch),
        "dispatch-request": dispatch,
        "external-projections": build_external_projections(draft),
        "outcome-foldback": build_outcome_foldback(draft, matrix),
    }


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------

NETWORK_NAMES = ("urllib", "socket", "http.client", "requests", "subprocess", "ftplib")

SUBJECT = "988a4e790af6a8bee31fd14e00e52a6e944b9f17"
TREE = "f8fe691090e4edd6a2aa40196430051ec05d11a7"


def lane_example(relative: str) -> dict:
    document = json.loads((SKILL / "references" / relative).read_text(encoding="utf-8"))
    return copy.deepcopy(document["examples"][0])


def fixture() -> dict[str, Any]:
    """One composition input built from the committed lane examples.

    The market example is bound to another commit and the user example claims a
    rung no receipt earns; both are patched here and both are reused unpatched
    below as the K01 and K08 cases, so the negative controls run against real
    admitted bytes rather than against strings written to fail.
    """
    market = {**lane_example("market/market-lane.schema.json"), "subject_commit": SUBJECT}
    user = {
        **lane_example("user/user-lane.schema.json"),
        "lane_state": "UNKNOWN",
        "highest_rung_reached": "NONE",
    }
    return {
        "schema": INPUT_SCHEMA,
        "program_id": "POL-PROG-010",
        "matrix_id": "POL-CLM-010",
        "dag_id": "POL-DAG-010",
        "foldback_id": "POL-FB-010",
        "subject": {"commit": SUBJECT, "tree": TREE},
        "rollback_commit": SUBJECT,
        "decision_owner": "the productization program owner",
        "dispatch_request_path": "skills/productization-operating-loop/references/session/dispatch-request.json",
        "lane_artifacts": {
            "market": market,
            "user": user,
            "commercial": lane_example("commercial/commercial-lane.schema.json"),
            "policy": lane_example("policy/policy-lane.schema.json"),
        },
        "receipts": [
            {"kind": "SOURCE_LOCATED", "subject_commit": SUBJECT, "note": "four lane contracts enumerated at this head"},
            {"kind": "INDEPENDENT_SOURCE_READBACK", "subject_commit": SUBJECT},
            {"kind": "DETERMINISTIC_COMMAND_EXIT", "subject_commit": SUBJECT, "note": "the POL suite exited zero"},
        ],
        "method_refs": [
            {
                "skill_name": "product-reverse-engineering-loop",
                "skill_md_sha256": "0e4aeff70b2dd68edc03a32c8857b96a2221cd20b8d98d2dbf8c40d7b14e6029",
                "skill_md_bytes": 11236,
                "observed_commit": SUBJECT,
                "declared_interface": "in: one external product subject at an exact identity. out: job, pain and mechanism signals. never: market, user or paid truth.",
            },
            {
                "skill_name": "agentic-tech-lead-orchestration",
                "skill_md_sha256": "8a295169f382a8a3df93458e8553d35b676d8078ac80f1c1bd56cb6dd15c3229",
                "skill_md_bytes": 18032,
                "observed_commit": SUBJECT,
                "declared_interface": "in: one admitted program. out: an atom DAG with one owner, one lease and one writer each. never: a session from a packet.",
            },
        ],
        "closure_cells": [
            {
                "cell_id": "POL-CELL-002",
                "lane": "USER",
                "question": "does the scenario reach first value without an account",
                "evidence_ceiling": "USER_SCENARIO_CONTRACT",
                "claims": [
                    {"source_record": "POL-USER-001", "statement": "first value is reached with no account and no key", "disposition": "CONFIRMED"},
                    {"source_record": "POL-CMRC-001", "statement": "the payment trigger requires an account before value", "disposition": "CONTRADICTED"},
                ],
            },
            {
                "cell_id": "POL-CELL-001",
                "lane": "MARKET",
                "question": "is the arena thin where the wedge is claimed",
                "evidence_ceiling": "MARKET_HYPOTHESIS_CONTRACT",
                "claims": [
                    {"source_record": "POL-MKT-001", "statement": "no comparator case was located in the named segment", "disposition": "UNKNOWN"}
                ],
            },
            {
                "cell_id": "POL-CELL-003",
                "lane": "TECHNICAL",
                "question": "does the committed suite exit zero at this commit",
                "evidence_ceiling": "DETERMINISTIC_COMPOSITION",
                "claims": [
                    {"source_record": "POL-PROG-010", "statement": "the committed POL suite exited zero at this commit", "disposition": "CONFIRMED"}
                ],
            },
        ],
        "atoms": [
            {
                "atom_id": "POL-ATOM-002",
                "request_id": "SDR-002",
                "relation": "SIBLING",
                "parent_atom_id": None,
                "branch": "agent/pol-e-eval-plane",
                "lease_paths": ["skills/productization-operating-loop/evals"],
                "evidence_ceiling": "DETERMINISTIC_EVAL_AND_SHADOW",
                "highest_claimable_lane": "DETERMINISTIC",
                "cannot_establish": ["user adoption", "payment"],
                "oracles": [{"id": "ORC-002", "lane": "DETERMINISTIC", "procedure": "run the eval plane and read its exit code", "refuted_by": "a green run with a planted defect in place"}],
                "negative_controls": ["planted defect must turn the plane red"],
                "stop_states": ["three qualifying failures against one acceptance target"],
                "output_paths": ["skills/productization-operating-loop/evals"],
                "interface_ref": "the eval plane contract at this head",
                "receipt_ref": "eval plane replay receipt",
            },
            {
                "atom_id": "POL-ATOM-001",
                "request_id": "SDR-001",
                "relation": "SIBLING",
                "parent_atom_id": None,
                "branch": "agent/pol-k-composition",
                "lease_paths": ["skills/productization-operating-loop/scripts", "skills/productization-operating-loop/references/session"],
                "evidence_ceiling": "DETERMINISTIC_COMPOSITION",
                "highest_claimable_lane": "DETERMINISTIC",
                "cannot_establish": ["market demand", "user adoption", "payment", "provider execution"],
                "oracles": [{"id": "ORC-001", "lane": "DETERMINISTIC", "procedure": "compile twice and byte-compare the two renderings", "refuted_by": "two renderings of one input that differ in any byte"}],
                "negative_controls": ["each refusal code must fire on its own crafted input"],
                "stop_states": ["a lane artifact bound to another commit"],
                "output_paths": ["skills/productization-operating-loop/scripts"],
                "interface_ref": "the composition compiler CLI at this head",
                "receipt_ref": "compiler selftest exit code",
            },
            {
                "atom_id": "POL-ATOM-003",
                "request_id": "SDR-003",
                "relation": "CHILD",
                "parent_atom_id": "POL-ATOM-001",
                "branch": "agent/pol-d-consumer-binding",
                "lease_paths": ["skills/productization-operating-loop/modules"],
                "evidence_ceiling": "DETERMINISTIC_COMPOSITION",
                "highest_claimable_lane": "DETERMINISTIC",
                "cannot_establish": ["merge", "release"],
                "oracles": [{"id": "ORC-003", "lane": "DETERMINISTIC", "procedure": "validate the consumer binding against the portable core", "refuted_by": "a consumer identity inside the portable core"}],
                "negative_controls": ["a consumer name in portable text must turn it red"],
                "stop_states": ["the portable interface is not readable at this head"],
                "output_paths": ["skills/productization-operating-loop/modules"],
                "start_after": ["POL-ATOM-001"],
                "complete_after": ["POL-ATOM-002"],
                "interface_ref": "the composed program contract at this head",
                "receipt_ref": "consumer binding receipt",
            },
        ],
        "refusal_classes": [
            "C01_MUTABLE_SUBJECT",
            "C04_START_DEPENDENCY_USED_AS_COMPLETION_PROOF",
            "C06_OVERLAPPING_WRITER_LEASE",
            "C09_SESSION_REQUEST_PROMOTED_TO_RUNNING",
        ],
        "projections": [
            {
                "id": "PRJ-001",
                "external_kind": "DOCUMENT",
                "external_id": "pol-composition-readout",
                "observed_revision": "rev-1",
                "export_digest": "0" * 64,
                "canonical_subjects": [
                    {
                        "path": "skills/productization-operating-loop/references/productization-program.schema.json",
                        "commit": SUBJECT,
                        "blob_digest": "0" * 40,
                    }
                ],
                "backlinks": ["skills/productization-operating-loop/README.md"],
            }
        ],
        "human_owned_operations": [
            "choosing one of the four outcome dispositions",
            "launching any session named in the DAG",
            "merge and release",
            "rights and licensing admission",
        ],
    }


def bad_fixtures() -> list[tuple[str, dict]]:
    """One crafted input per refusal code."""
    cases: list[tuple[str, dict]] = []

    stale = fixture()
    stale["lane_artifacts"]["market"] = lane_example("market/market-lane.schema.json")
    cases.append(("K01_STALE_LANE_ARTIFACT", stale))

    stale_policy = fixture()
    stale_policy["lane_artifacts"]["policy"]["terminal"] = "SUPERSEDED"
    cases.append(("K01_STALE_LANE_ARTIFACT", stale_policy))

    missing = fixture()
    del missing["lane_artifacts"]["commercial"]
    cases.append(("K02_MISSING_MANDATORY_LANE", missing))

    clock = fixture()
    clock["projections"][0]["observed_revision"] = "NOW"
    cases.append(("K03_NONDETERMINISTIC_INPUT", clock))

    widened = fixture()
    widened["lane_artifacts"]["commercial"]["authority"]["paid_truth"] = True
    cases.append(("K04_AUTHORITY_WIDENING", widened))

    asserted = fixture()
    asserted["lanes"] = {"market": {"state": "PASS", "highest_rung_reached": "WEDGE_SUPPORTED"}}
    cases.append(("K04_AUTHORITY_WIDENING", asserted))

    hidden = fixture()
    hidden["atoms"][2]["complete_after"] = ["POL-ATOM-404"]
    cases.append(("K05_HIDDEN_DEPENDENCY", hidden))

    overlap = fixture()
    overlap["atoms"][0]["lease_paths"] = ["skills/productization-operating-loop/scripts/compile_pol_composition.py"]
    cases.append(("K06_OVERLAPPING_WRITER_LEASE", overlap))

    reconciled = fixture()
    reconciled["closure_cells"][0]["reconcile"] = True
    cases.append(("K07_CONTRADICTION_DROPPED", reconciled))

    asserted_state = fixture()
    asserted_state["closure_cells"][0]["state"] = "PASS"
    cases.append(("K07_CONTRADICTION_DROPPED", asserted_state))

    promoted = fixture()
    promoted["lane_artifacts"]["user"] = lane_example("user/user-lane.schema.json")
    cases.append(("K08_RUNG_PROMOTED_ABOVE_RECEIPTS", promoted))

    ladder_asserted = fixture()
    ladder_asserted["evidence_ladder"] = {"paid_validated": {"state": "REACHED", "receipts": []}}
    cases.append(("K08_RUNG_PROMOTED_ABOVE_RECEIPTS", ladder_asserted))

    return cases


def selftest() -> int:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print(
            "POL-COMPILE-UNUSABLE: jsonschema is required. This selftest validates "
            "the compiled artifacts against the committed contracts; skipping that "
            "would report the same green as running it.",
            file=sys.stderr,
        )
        return 70

    failures: list[str] = []

    source = Path(__file__).read_text(encoding="utf-8")
    for name in NETWORK_NAMES:
        if f"import {name}" in source:
            failures.append(f"this compiler names the network module {name}")

    draft = fixture()
    first = compile_all(draft)
    second = compile_all(fixture())
    for name in ARTIFACTS:
        if canonical(first[name]) != canonical(second[name]):
            failures.append(f"{name} is not byte-stable across two compilations")

    # Same facts, different order: the compiled bytes must not move.
    shuffled = fixture()
    shuffled["atoms"].reverse()
    shuffled["closure_cells"].reverse()
    shuffled["receipts"].reverse()
    shuffled["method_refs"].reverse()
    shuffled["human_owned_operations"].reverse()
    shuffled["human_owned_operations"].append(shuffled["human_owned_operations"][0])
    reordered = compile_all(shuffled)
    for name in ARTIFACTS:
        if canonical(first[name]) != canonical(reordered[name]):
            failures.append(f"{name} moved when the input order moved")

    contracts = {
        "program": SKILL / "references" / "productization-program.schema.json",
        "closure-matrix": SKILL / "references" / "session" / "closure-matrix.schema.json",
        "session-dag": SKILL / "references" / "session" / "session-dag.schema.json",
        "outcome-foldback": SKILL / "references" / "session" / "outcome-foldback-request.schema.json",
        "dispatch-request": SKILLS
        / "product-reverse-engineering-loop"
        / "references"
        / "session-dispatch-request.schema.json",
        "external-projections": SKILLS
        / "product-reverse-engineering-loop"
        / "references"
        / "external-projection-registry.schema.json",
    }
    for name, path in contracts.items():
        validator = Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))
        for error in validator.iter_errors(first[name]):
            failures.append(f"{name} is refused by {path.name}: {error.message}")

    # The composed program preserved what the matrix preserved.
    if first["closure-matrix"]["unresolved_cell_ids"] != sorted(
        question["cell_id"] for question in first["outcome-foldback"]["read_back_questions"]
    ):
        failures.append("an unresolved cell did not reach the foldback request")
    if not any(cell["state"] == "CONTRADICTION" for cell in first["closure-matrix"]["cells"]):
        failures.append("the contradicting fixture cell did not survive into the matrix")
    if first["program"]["evidence_ladder"]["mvp_tech_verified"]["state"] != "NOT_REACHED":
        failures.append("a receipt with no earned predecessor was promoted")
    if not first["program"]["evidence_ladder"]["mvp_tech_verified"]["receipts"]:
        failures.append("an unpromoted receipt was dropped instead of preserved")

    cases = bad_fixtures()
    fired: set[str] = set()
    for expected, bad in cases:
        try:
            compile_all(bad)
        except Refused as refusal:
            if str(refusal).split()[0] != expected:
                failures.append(f"expected {expected}, got {str(refusal).split()[0]}")
            else:
                fired.add(expected)
        except Unusable as error:
            failures.append(f"expected {expected}, input was called unusable: {error}")
        else:
            failures.append(f"expected {expected}, the composition compiled")

    codes = {code for code, _ in cases}
    missing = sorted(codes - fired)
    if missing:
        failures.append(f"refusal code(s) never fired: {missing}")

    print(
        f"subject={SKILL} artifacts={len(ARTIFACTS)} contracts={len(contracts)} "
        f"refusal_cases={len(cases)} codes={len(codes)}"
    )
    if failures:
        for item in failures:
            print(f"POL-COMPILE-RED {item}", file=sys.stderr)
        return 2
    print(
        f"POL-COMPILE-GREEN {len(ARTIFACTS)} artifacts byte-stable across two "
        f"compilations and one reordering, validated against {len(contracts)} "
        f"committed contracts, {len(codes)} refusal codes fired by "
        f"{len(cases)} crafted inputs"
    )
    return 0


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--artifact", choices=ARTIFACTS)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="byte-compare --out against a fresh compilation instead of writing it",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="compile the committed lane examples, validate every artifact and fire every refusal code",
    )
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if args.input is None or args.artifact is None:
        parser.error("--input and --artifact are required unless --selftest is given")

    try:
        rendered = canonical(compile_all(load(args.input))[args.artifact])
    except Refused as error:
        print(f"POL-COMPILE-RED {args.artifact}: {error}", file=sys.stderr)
        return 2
    except Unusable as error:
        print(f"POL-COMPILE-UNUSABLE {args.artifact}: {error}", file=sys.stderr)
        return 64
    except (KeyError, TypeError) as error:
        print(f"POL-COMPILE-UNUSABLE {args.artifact}: malformed input: {error}", file=sys.stderr)
        return 64

    if args.out is None:
        sys.stdout.write(rendered)
        return 0

    if args.check:
        try:
            current = args.out.read_text(encoding="utf-8")
        except OSError as error:
            print(f"POL-COMPILE-RED missing projection {args.out}: {error}", file=sys.stderr)
            return 2
        if current != rendered:
            print(
                f"POL-COMPILE-RED {args.out} is not what {args.input.name} compiles "
                f"to; regenerate it rather than editing it",
                file=sys.stderr,
            )
            return 2
        print(f"POL-COMPILE-GREEN {args.artifact} projection is current")
        return 0

    args.out.write_text(rendered, encoding="utf-8")
    print(f"POL-COMPILE-GREEN wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
