#!/usr/bin/env python3
"""Validate the Productization Operating Loop implementation preflight.

This gate proves preparation-graph consistency only. It does not execute product,
market, user, payment, policy, provider, KAW, merge, release, or legal lanes.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

REQUIRED_IDS = {
    "POL-C0", "POL-M", "POL-U", "POL-B", "POL-P", "POL-R",
    "POL-K", "POL-E", "POL-D", "POL-A", "POL-KAW", "POL-LIVE", "POL-T",
}
REQUIRED_FIELDS = {
    "owner", "state", "relation", "start_dependencies", "completion_dependencies",
    "planned_paths", "outputs", "negative_controls", "evidence_ceiling",
    "next_safe_transition",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("preflight must be a JSON object")
    return value


def _atom_map(value: dict[str, Any]) -> dict[str, dict[str, Any]]:
    atoms = value.get("atoms")
    if not isinstance(atoms, list):
        return {}
    return {
        atom.get("id"): atom
        for atom in atoms
        if isinstance(atom, dict) and isinstance(atom.get("id"), str)
    }


def validate(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if value.get("schema") != "productization-implementation-preflight/v1":
        errors.append("unexpected schema")
    if value.get("phase_target") != "PRODUCTIZATION_PREIMPLEMENTATION_READY":
        errors.append("unexpected phase target")

    atoms = value.get("atoms")
    if not isinstance(atoms, list):
        return errors + ["atoms must be a list"]

    ids = [atom.get("id") for atom in atoms if isinstance(atom, dict)]
    duplicates = sorted(k for k, n in Counter(ids).items() if k and n > 1)
    if duplicates:
        errors.append(f"duplicate atom ids: {duplicates}")
    missing = sorted(REQUIRED_IDS - set(ids))
    if missing:
        errors.append(f"missing required atoms: {missing}")

    by_id = _atom_map(value)
    for atom_id, atom in by_id.items():
        missing_fields = sorted(field for field in REQUIRED_FIELDS if field not in atom)
        if missing_fields:
            errors.append(f"{atom_id} missing fields: {missing_fields}")
            continue
        if not atom["owner"]:
            errors.append(f"{atom_id} missing owner")
        if not atom["outputs"]:
            errors.append(f"{atom_id} missing outputs")
        if not atom["negative_controls"]:
            errors.append(f"{atom_id} missing negative controls")
        if not atom["evidence_ceiling"]:
            errors.append(f"{atom_id} missing evidence ceiling")
        if not atom["next_safe_transition"]:
            errors.append(f"{atom_id} missing next transition")

    # Stage-1 siblings all wait for the same portable interface and must stay path-disjoint.
    stage1 = ["POL-M", "POL-U", "POL-B", "POL-P"]
    for atom_id in stage1:
        atom = by_id.get(atom_id, {})
        if "POL-C0 readable exact interface" not in atom.get("start_dependencies", []):
            errors.append(f"{atom_id} missing C0 start dependency")
        if atom.get("state") != "BLOCKED_ON_C0_INTERFACE":
            errors.append(f"{atom_id} must remain blocked until C0 interface is readable")

    k = by_id.get("POL-K", {})
    required_k_receipts = {
        "POL-C0 receipt", "POL-M receipt", "POL-U receipt", "POL-B receipt", "POL-P receipt"
    }
    if not required_k_receipts.issubset(set(k.get("completion_dependencies", []))):
        errors.append("POL-K missing Stage-1 completion receipts")
    if k.get("state") != "BLOCKED_ON_STAGE1":
        errors.append("POL-K must remain blocked on Stage-1")

    e = by_id.get("POL-E", {})
    if e.get("state") != "BLOCKED_ON_K":
        errors.append("POL-E must remain blocked on POL-K")
    if set(k.get("planned_paths", [])) & set(e.get("planned_paths", [])):
        errors.append("POL-K and POL-E writer paths overlap")

    d = by_id.get("POL-D", {})
    if d.get("relation") != "CONVERGENCE":
        errors.append("POL-D must be the convergence owner")
    if d.get("state") != "BLOCKED_ON_IMPLEMENTATION_RECEIPTS":
        errors.append("POL-D must remain blocked on implementation receipts")

    a = by_id.get("POL-A", {})
    if a.get("state") != "BLOCKED_ON_ADMITTED_METHOD_AND_WRITER_RECONCILIATION":
        errors.append("POL-A cannot start before method admission and writer reconciliation")

    r = by_id.get("POL-R", {})
    if r.get("relation") != "PROCESS_EVIDENCE_SIBLING":
        errors.append("POL-R must remain a process/evidence sibling")

    kaw = by_id.get("POL-KAW", {})
    if kaw.get("relation") != "EXTERNAL_CONSUMER_ADAPTER":
        errors.append("POL-KAW must remain an external consumer adapter")
    if kaw.get("owner") != "ed3c/kotlin-auto-webview#135":
        errors.append("POL-KAW owner drifted")

    live = by_id.get("POL-LIVE", {})
    if live.get("relation") != "EXTERNAL_EVIDENCE":
        errors.append("POL-LIVE must remain external evidence")
    if live.get("state") != "BLOCKED_EXTERNAL_EVIDENCE":
        errors.append("POL-LIVE cannot be implementation-ready")

    # Exact lease strings cannot have two owners. Prefix/wildcard semantic overlap is
    # reviewed by Tech Lead; this catches accidental literal collisions deterministically.
    path_owners: dict[str, list[str]] = {}
    for atom_id, atom in by_id.items():
        for path in atom.get("planned_paths", []):
            path_owners.setdefault(path, []).append(atom_id)
    overlaps = {path: owners for path, owners in path_owners.items() if len(owners) > 1}
    if overlaps:
        errors.append(f"exact path lease overlap: {overlaps}")

    external = value.get("human_external_authority")
    if not isinstance(external, list) or not external:
        errors.append("human_external_authority must be non-empty")
    else:
        required_authority = {
            "legal and usage-rights admission", "user/customer/payment truth",
            "merge", "release or promotion",
        }
        if not required_authority.issubset(set(external)):
            errors.append("required Human/external authority disappeared")

    laws = value.get("laws")
    if not isinstance(laws, list) or not laws:
        errors.append("laws must be non-empty")
    else:
        required_laws = {
            "market attention != demand",
            "prompt packet != observed session",
            "process dependency != Git ancestry",
        }
        if not required_laws.issubset(set(laws)):
            errors.append("load-bearing productization law disappeared")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path", nargs="?",
        default="docs/traceability/productization-operating-loop/implementation-preflight.json",
        type=Path,
    )
    args = parser.parse_args()
    errors = validate(load(args.path))
    print(json.dumps({"status": "FAIL" if errors else "PASS", "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
