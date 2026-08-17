#!/usr/bin/env python3
"""Plant molecular Stack defects and require every one to turn red."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check_refactor_proof_stack.py"
SCHEMA = ROOT / "references/refactor-proof-stack.schema.json"
BASE = ROOT / "references/refactor-proof-stack.json"


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rejected(path: Path) -> bool:
    result = subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--stack",
            str(path),
            "--schema",
            str(SCHEMA),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode != 0


def node(value, node_id: str):
    return next(row for row in value["nodes"] if row["id"] == node_id)


def main() -> int:
    base = json.loads(BASE.read_text(encoding="utf-8"))
    mutations = {}

    missing_parent = copy.deepcopy(base)
    missing_parent["edges"] = [
        edge for edge in missing_parent["edges"]
        if not (
            edge["to"] == "proof-contract-registry"
            and edge["type"] == "CONSUMES_UNMERGED_BYTES"
        )
    ]
    mutations["child_without_parent_artifact"] = missing_parent

    wrong_base = copy.deepcopy(base)
    node(wrong_base, "agent-docs-state-machines")["base_branch"] = "main"
    mutations["wrong_child_base"] = wrong_base

    fake_sibling = copy.deepcopy(base)
    node(fake_sibling, "proof-contract-registry")["stack_class"] = "SIBLING"
    mutations["fake_serial_sibling"] = fake_sibling

    two_convergence = copy.deepcopy(base)
    node(two_convergence, "agent-docs-state-machines")["stack_class"] = "CONVERGENCE"
    mutations["multiple_convergence_owners"] = two_convergence

    stale_head = copy.deepcopy(base)
    node(stale_head, "tech-lead-hermetic-golden")["head"]["observed_sha"] = "a" * 40
    mutations["self_embedded_open_head"] = stale_head

    fake_merged = copy.deepcopy(base)
    target = node(fake_merged, "proof-contract-registry")
    target["state"] = "MERGED"
    target["head"] = {"policy": "IMMUTABLE_MERGED_COMMIT", "observed_sha": None}
    mutations["merged_without_immutable_receipt"] = fake_merged

    external_paths = copy.deepcopy(base)
    node(external_paths, "live-scheduler-evidence")["owns_paths"] = ["skills/**"]
    mutations["external_evidence_owns_paths"] = external_paths

    widened = copy.deepcopy(base)
    widened["authority"]["merge"] = True
    mutations["stack_merge_authority"] = widened

    duplicate_issue = copy.deepcopy(base)
    node(duplicate_issue, "cross-skill-adoption-audit")["issues"] = [321]
    mutations["duplicate_issue_owner"] = duplicate_issue

    failures = []
    with tempfile.TemporaryDirectory(prefix="refactor-stack-selftest-") as raw:
        root = Path(raw)
        for name, value in mutations.items():
            path = root / f"{name}.json"
            dump(path, value)
            if not rejected(path):
                failures.append(name)
    if failures:
        print(
            f"REFACTOR-STACK-SELFTEST-RED survived={','.join(sorted(failures))}",
            file=sys.stderr,
        )
        return 2
    print(f"REFACTOR-STACK-SELFTEST-GREEN mutations={len(mutations)} all refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
