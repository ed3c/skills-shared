#!/usr/bin/env python3
"""Compile the three PREL projections deterministically.

    product signals -> dossier -> problem closure matrix -> executable handoff

Every output is a pure function of its input bytes plus this file, serialized
canonically (`sort_keys`, two-space indent, one trailing newline), so `--check`
byte-compares a committed projection instead of trusting that someone
regenerated it. The compilers add no product semantics: a slot with no
admissible signal comes out `ABSENT`, a mechanism with no oracle comes out
`UNOBSERVABLE_MECHANISM`, and a capability edge exists only where a signal
declared `depends_on`.

Two states this compiler deliberately cannot emit, and the reason each is not a
bug:

* `CLOSED_BY_ORACLE`. Compiling an oracle is not running one. A row closes only
  when a consumer records an executed oracle in that row's own lane, so this
  repository's lane leaves the state `NOT_IMPLEMENTED` rather than manufacture
  it. `check_prel_contract.py` still validates the state, because the artifact
  it validates may come from a consumer that did run one.
* a serialized packet graph. Nothing in a signal set proves that one
  implementation packet consumes another's output, so every compiled packet is
  a sibling. An edge is a consumer's claim and the checker refuses it unless
  the successor consumes a path the predecessor actually leases.

Exits: 0 green, 2 the compilation is refused or a --check projection is stale,
64 the compiler could not run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

GRADE_BY_KIND = {
    "OBSERVED_ARTIFACT": "OBSERVED",
    "PAID_CONVERSION": "OBSERVED",
    "USER_INTERVIEW": "REPORTED",
    "THIRD_PARTY_REPORT": "REPORTED",
    "SOURCE_STATEMENT": "CLAIMED",
    "MARKET_ATTENTION": "CLAIMED",
    "INFERENCE": "INFERRED",
}
GRADE_RANK = {"OBSERVED": 0, "REPORTED": 1, "CLAIMED": 2, "INFERRED": 3, "ABSENT": 4}
TECHNICAL_LANES = {"DETERMINISTIC", "BEHAVIORAL"}
OWNER_BY_LANE = {
    "DETERMINISTIC": "PORTABLE_DETERMINISTIC_OWNER",
    "BEHAVIORAL": "PORTABLE_DETERMINISTIC_OWNER",
    "USER": "CONSUMER_USER_EVIDENCE_OWNER",
    "PAID": "CONSUMER_COMMERCIAL_EVIDENCE_OWNER",
    "HUMAN_ADMIT": "HUMAN_ADMIT_OWNER",
}
CEILING = {
    "portable_procedure": "PASS",
    "deterministic_contract": "PASS",
    "product_market_fit": "NOT_EXERCISED",
    "live_provider_execution": "NOT_EXERCISED",
    "production_readiness": "NOT_EXERCISED",
}
HUMAN_ADMIT = [
    "commercial or usage rights admission",
    "merge",
    "permission or legal expansion",
    "release or promotion",
    "rollback",
]
STOP_LOSS = {
    "condition": (
        "any compiled MVP scope row is still BLOCKED_NO_ORACLE, "
        "BLOCKED_NOT_FALSIFIABLE or BLOCKED_LANE_MISMATCH after the closure "
        "matrix is compiled"
    ),
    "action": (
        "stop implementation and return the row to its named owner as a "
        "remaining item"
    ),
}


class Refused(Exception):
    """The input cannot be compiled without inventing product semantics."""


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Refused(f"unreadable input {path}: {error}") from error
    if not isinstance(value, dict):
        raise Refused(f"{path}: root must be an object")
    return value


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def derived_from(path: Path) -> dict[str, str]:
    return {
        "artifact": path.name,
        "digest": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def slot_projection(signals: list[dict], slot: str) -> dict[str, Any]:
    rows = sorted(
        (row for row in signals if row.get("slot") == slot),
        key=lambda row: (GRADE_RANK[GRADE_BY_KIND[row["kind"]]], row["id"]),
    )
    if not rows:
        return {"grade": "ABSENT", "statement": "", "signal_ids": []}
    return {
        "grade": GRADE_BY_KIND[rows[0]["kind"]],
        "statement": rows[0]["statement"],
        "signal_ids": sorted(row["id"] for row in rows),
    }


def compile_dossier(source: Path) -> dict[str, Any]:
    document = load(source)
    if document.get("schema") != "prel/product-signal/v1":
        raise Refused("dossier input must be a prel/product-signal/v1 artifact")
    signals = sorted(document.get("signals") or [], key=lambda row: row["id"])
    for row in signals:
        if row.get("kind") not in GRADE_BY_KIND:
            raise Refused(f"{row.get('id')}: unknown evidence kind {row.get('kind')!r}")

    mechanisms = []
    for index, row in enumerate(r for r in signals if r["slot"] == "MECHANISM"):
        oracle = row.get("oracle") or {}
        if row["kind"] == "SOURCE_STATEMENT":
            classification, oracle_id = "VENDOR_CLAIMED_MECHANISM", None
        elif oracle.get("lane") in TECHNICAL_LANES:
            classification, oracle_id = "OBSERVABLE_MECHANISM", oracle["id"]
        else:
            classification, oracle_id = "UNOBSERVABLE_MECHANISM", None
        mechanisms.append(
            {
                "id": f"MECH-{index + 1:03d}",
                "classification": classification,
                "grade": GRADE_BY_KIND[row["kind"]],
                "statement": row["statement"],
                "oracle_id": oracle_id,
                "signal_ids": [row["id"]],
                "_lane": oracle.get("lane"),
            }
        )

    capability_rows = [row for row in signals if row["slot"] == "CAPABILITY"]
    node_id = {row["id"]: f"CAP-{index + 1:03d}" for index, row in enumerate(capability_rows)}
    nodes = [
        {
            "id": node_id[row["id"]],
            "capability": row["statement"],
            "grade": GRADE_BY_KIND[row["kind"]],
            "signal_ids": [row["id"]],
        }
        for row in capability_rows
    ]
    edges = sorted(
        (
            {
                "from": node_id[parent],
                "to": node_id[row["id"]],
                "basis": f"declared dependency {parent} -> {row['id']}",
            }
            for row in capability_rows
            for parent in row.get("depends_on") or []
            if parent in node_id
        ),
        key=lambda edge: (edge["from"], edge["to"]),
    )

    rights = [
        {
            "id": f"RGT-{index + 1:03d}",
            "resource": row["statement"],
            "state": "HUMAN_ADMIT_REQUIRED",
            "owner": row["source_ref"],
        }
        for index, row in enumerate(r for r in signals if r["slot"] == "RIGHTS")
    ]

    magic_moment = slot_projection(signals, "MAGIC_MOMENT")
    scope = []
    for mechanism in mechanisms:
        if mechanism["classification"] != "OBSERVABLE_MECHANISM":
            continue
        scope.append(
            {
                "id": f"REQ-{len(scope) + 1:03d}",
                "requirement": f"reproduce {mechanism['id']}: {mechanism['statement']}",
                "lane": mechanism["_lane"],
                "oracle_id": mechanism["oracle_id"],
                "source_id": mechanism["id"],
            }
        )
    if magic_moment["grade"] != "ABSENT":
        scope.append(
            {
                "id": f"REQ-{len(scope) + 1:03d}",
                "requirement": f"deliver the magic moment: {magic_moment['statement']}",
                "lane": "USER",
                "oracle_id": None,
                "source_id": "MAGIC_MOMENT",
            }
        )
    if not scope:
        raise Refused(
            "no observable mechanism and no graded magic moment: there is nothing an "
            "MVP could be scoped to, and an empty MVP is not a small one"
        )

    dossier = {
        "schema": "prel/reverse-engineering-dossier/v1",
        "subject": document["subject"],
        "derived_from": derived_from(source),
        "job": slot_projection(signals, "JOB"),
        "pain": slot_projection(signals, "PAIN"),
        "workflow": [
            {
                "grade": GRADE_BY_KIND[row["kind"]],
                "statement": row["statement"],
                "signal_ids": [row["id"]],
            }
            for row in signals
            if row["slot"] == "WORKFLOW"
        ],
        "magic_moment": magic_moment,
        "mechanism_hypotheses": [
            {key: value for key, value in row.items() if key != "_lane"}
            for row in mechanisms
        ],
        "capability_graph": {"nodes": nodes, "edges": edges},
        "rights": rights,
        "mvp": {
            "scope": scope,
            "excluded": sorted(
                row["statement"]
                for row in mechanisms
                if row["classification"] != "OBSERVABLE_MECHANISM"
            ),
            "stop_loss": dict(STOP_LOSS),
        },
        "evidence_ceiling": dict(CEILING),
    }
    return dossier


def compile_closure(source: Path) -> dict[str, Any]:
    dossier = load(source)
    if dossier.get("schema") != "prel/reverse-engineering-dossier/v1":
        raise Refused("closure input must be a prel/reverse-engineering-dossier/v1 artifact")

    rows: list[dict[str, Any]] = []

    def add(source_id: str, requirement: str, lane: str, oracle_id: str | None) -> None:
        oracle_lane = lane if oracle_id else None
        if oracle_id is None:
            state, evidence = "BLOCKED_NO_ORACLE", "ABSENT"
        else:
            state, evidence = "OPEN_WITH_ORACLE", "NOT_EXERCISED"
        rows.append(
            {
                "id": f"CLR-{len(rows) + 1:03d}",
                "source_id": source_id,
                "requirement": requirement,
                "lane": lane,
                "oracle_id": oracle_id,
                "oracle_lane": oracle_lane,
                "closure_state": state,
                "evidence_state": evidence,
                "owner": OWNER_BY_LANE[lane],
            }
        )

    for item in dossier["mvp"]["scope"]:
        add(item["source_id"], item["requirement"], item["lane"], item["oracle_id"])

    for mechanism in dossier["mechanism_hypotheses"]:
        if mechanism["classification"] == "OBSERVABLE_MECHANISM":
            continue
        if mechanism["classification"] == "VENDOR_CLAIMED_MECHANISM":
            lane, state, evidence = "HUMAN_ADMIT", "BLOCKED_NOT_FALSIFIABLE", "ABSENT"
        else:
            lane, state, evidence = "BEHAVIORAL", "BLOCKED_NO_ORACLE", "ABSENT"
        rows.append(
            {
                "id": f"CLR-{len(rows) + 1:03d}",
                "source_id": mechanism["id"],
                "requirement": f"design an oracle for {mechanism['id']}: {mechanism['statement']}",
                "lane": lane,
                "oracle_id": None,
                "oracle_lane": None,
                "closure_state": state,
                "evidence_state": evidence,
                "owner": OWNER_BY_LANE[lane],
            }
        )

    for right in dossier["rights"]:
        rows.append(
            {
                "id": f"CLR-{len(rows) + 1:03d}",
                "source_id": right["id"],
                "requirement": f"admit usage rights for {right['resource']}",
                "lane": "HUMAN_ADMIT",
                "oracle_id": None,
                "oracle_lane": None,
                "closure_state": "HUMAN_ADMIT_REQUIRED",
                "evidence_state": "HUMAN_ADMIT_REQUIRED",
                "owner": OWNER_BY_LANE["HUMAN_ADMIT"],
            }
        )

    return {
        "schema": "prel/problem-closure-matrix/v1",
        "subject": dossier["subject"],
        "derived_from": derived_from(source),
        "rows": rows,
        "evidence_ceiling": dict(CEILING),
    }


def compile_handoff(source: Path) -> dict[str, Any]:
    matrix = load(source)
    if matrix.get("schema") != "prel/problem-closure-matrix/v1":
        raise Refused("handoff input must be a prel/problem-closure-matrix/v1 artifact")

    # The packet's exact subject is the matrix that defined its row, not the
    # dossier upstream of it: a row can move while the dossier stands still.
    subject = derived_from(source)
    packets, remaining = [], []
    for row in matrix["rows"]:
        executable = (
            row["closure_state"] == "OPEN_WITH_ORACLE"
            and row["lane"] in TECHNICAL_LANES
        )
        if not executable:
            remaining.append(
                {
                    "closure_row_id": row["id"],
                    "criterion": row["requirement"],
                    "state": row["evidence_state"],
                    "owner": row["owner"],
                }
            )
            continue
        packets.append(
            {
                "id": f"PKT-{len(packets) + 1:03d}",
                "closure_row_id": row["id"],
                "exact_subject": dict(subject),
                "entry_condition": (
                    f"closure row {row['id']} is OPEN_WITH_ORACLE against the "
                    f"digest named in exact_subject"
                ),
                "paths_lease": [f"prel/{row['id']}/"],
                "verification": {
                    "lane": row["oracle_lane"],
                    "procedure": f"run oracle {row['oracle_id']} and record its verdict",
                },
                "exit_condition": (
                    f"oracle {row['oracle_id']} produced a verdict bound to the same "
                    f"subject digest"
                ),
                "depends_on": [],
                "convergence_owner": None,
            }
        )

    return {
        "schema": "prel/reverse-engineering-handoff/v1",
        "subject": matrix["subject"],
        "derived_from": dict(subject),
        "packets": packets,
        "remaining": remaining,
        "human_admit": list(HUMAN_ADMIT),
    }


STAGES = {
    "dossier": compile_dossier,
    "closure": compile_closure,
    "handoff": compile_handoff,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=sorted(STAGES))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="byte-compare --out against a fresh compilation instead of writing it",
    )
    args = parser.parse_args()

    try:
        rendered = canonical(STAGES[args.stage](args.input))
    except Refused as error:
        print(f"PREL-COMPILE-RED {args.stage}: {error}", file=sys.stderr)
        return 2
    except (KeyError, TypeError) as error:
        print(f"PREL-COMPILE-UNUSABLE {args.stage}: malformed input: {error}", file=sys.stderr)
        return 64

    if args.out is None:
        sys.stdout.write(rendered)
        return 0

    if args.check:
        try:
            current = args.out.read_text(encoding="utf-8")
        except OSError as error:
            print(f"PREL-COMPILE-RED missing projection {args.out}: {error}", file=sys.stderr)
            return 2
        if current != rendered:
            print(
                f"PREL-COMPILE-RED {args.out} is not what {args.input.name} compiles "
                f"to; regenerate it rather than editing it",
                file=sys.stderr,
            )
            return 2
        print(f"PREL-COMPILE-GREEN {args.stage} projection is current")
        return 0

    args.out.write_text(rendered, encoding="utf-8")
    print(f"PREL-COMPILE-GREEN wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
