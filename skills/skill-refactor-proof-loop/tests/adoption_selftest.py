#!/usr/bin/env python3
"""Plant adoption-ledger defects and require each one to turn red for its own reason.

A returncode alone would let one loud rule cover for nine dead ones, so every
mutation names the error code that must appear.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check_skill_adoption_ledger.py"
SCHEMA = ROOT / "references/skill-adoption-ledger.schema.json"
BASE = ROOT / "references/skill-adoption-ledger.json"
PROVEN = "agentic-tech-lead-orchestration"
UNPROVEN = "knowledge-continuity"


def run(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--ledger", str(path), "--schema", str(SCHEMA)],
        text=True,
        capture_output=True,
        check=False,
    )


def entry(value: dict, skill: str) -> dict:
    return next(row for row in value["skills"] if row["skill"] == skill)


def main() -> int:
    base = json.loads(BASE.read_text(encoding="utf-8"))
    mutations: dict[str, tuple[dict, str]] = {}

    dropped = copy.deepcopy(base)
    dropped["skills"] = [row for row in dropped["skills"] if row["skill"] != UNPROVEN]
    mutations["dropped_in_scope_skill"] = (dropped, "IN_SCOPE_SKILL_UNCLASSIFIED")

    duplicated = copy.deepcopy(base)
    duplicated["skills"].append(copy.deepcopy(entry(duplicated, UNPROVEN)))
    mutations["duplicate_skill_entry"] = (duplicated, "DUPLICATE_SKILL_ENTRY")

    ghost = copy.deepcopy(base)
    ghost["in_scope"].append("skill-that-does-not-exist")
    ghost["skills"].append(copy.deepcopy(entry(ghost, UNPROVEN)))
    ghost["skills"][-1]["skill"] = "skill-that-does-not-exist"
    mutations["audited_skill_absent"] = (ghost, "AUDITED_SKILL_ABSENT")

    missing_path = copy.deepcopy(base)
    entry(missing_path, UNPROVEN)["criteria"]["route_reachable"]["evidence"] = [
        f"skills/{UNPROVEN}/scripts/never_written.py"
    ]
    mutations["evidence_path_absent"] = (missing_path, "EVIDENCE_PATH_ABSENT")

    prose = copy.deepcopy(base)
    entry(prose, UNPROVEN)["criteria"]["hollow_dead_route_controls"]["evidence"] = [
        f"skills/{UNPROVEN}/SKILL.md"
    ]
    mutations["markdown_route_counted_executable"] = (prose, "MARKDOWN_ONLY_EXECUTABLE_CLAIM")

    bare = copy.deepcopy(base)
    entry(bare, UNPROVEN)["criteria"]["route_reachable"]["evidence"] = []
    mutations["pass_without_evidence"] = (bare, "EVIDENCE_REQUIRED")

    contradiction = copy.deepcopy(base)
    entry(contradiction, UNPROVEN)["criteria"]["golden_proof_registered"]["evidence"] = [
        f"skills/{UNPROVEN}/SKILL.md"
    ]
    mutations["absent_finding_with_evidence"] = (contradiction, "EVIDENCE_FORBIDDEN")

    claimed = copy.deepcopy(base)
    row = entry(claimed, UNPROVEN)["criteria"]["golden_proof_registered"]
    row["state"] = "PASS"
    row["evidence"] = [base["golden_proof_registry"]]
    row.pop("owner_issue", None)
    mutations["unregistered_golden_proof_claimed"] = (claimed, "GOLDEN_PROOF_UNREGISTERED")

    hidden = copy.deepcopy(base)
    proven = entry(hidden, PROVEN)
    proven["criteria"]["golden_proof_registered"] = {
        "state": "ABSENT",
        "evidence": [],
        "owner_issue": hidden["audit_issue"],
    }
    proven["golden_proof_id"] = None
    mutations["registered_proof_understated"] = (hidden, "REGISTERED_PROOF_UNDERSTATED")

    unbound = copy.deepcopy(base)
    entry(unbound, PROVEN)["criteria"]["old_canonical_treatment_frozen"]["evidence"] = [
        f"skills/{PROVEN}/SKILL.md"
    ]
    mutations["frozen_treatment_not_content_bound"] = (unbound, "FROZEN_TREATMENT_NOT_CONTENT_BOUND")

    promoted = copy.deepcopy(base)
    entry(promoted, UNPROVEN)["highest_layer"] = "L4_MATCHED_LIVE_MODEL_RUNTIME"
    mutations["layer_above_registered_proof"] = (promoted, "LAYER_ABOVE_REGISTERED_PROOF")

    drifted = copy.deepcopy(base)
    entry(drifted, PROVEN)["highest_layer"] = "L2_EXECUTABLE_CONTRACT"
    mutations["layer_disagrees_with_registry"] = (drifted, "LAYER_DISAGREES_WITH_REGISTRY")

    live = copy.deepcopy(base)
    row = entry(live, UNPROVEN)["criteria"]["live_model_runtime_ab"]
    row["state"] = "PASS"
    row["evidence"] = [f"skills/{UNPROVEN}/tests/run-all.sh"]
    row.pop("owner_issue", None)
    mutations["fixture_promoted_to_live_pass"] = (live, "LIVE_PASS_BELOW_LAYER")

    delivered = copy.deepcopy(base)
    row = entry(delivered, PROVEN)["criteria"]["molecular_traceability"]
    row["state"] = "PASS"
    row.pop("owner_issue", None)
    mutations["delivery_pass_without_receipt"] = (delivered, "DELIVERY_PASS_WITHOUT_LIVE_RECEIPT")

    orphan = copy.deepcopy(base)
    entry(orphan, UNPROVEN)["criteria"]["matched_hermetic_task"].pop("owner_issue")
    mutations["gap_without_owner_issue"] = (orphan, "GAP_WITHOUT_OWNER_ISSUE")

    invented = copy.deepcopy(base)
    entry(invented, UNPROVEN)["criteria"]["matched_hermetic_task"]["owner_issue"] = 99999
    mutations["gap_owned_by_unknown_issue"] = (invented, "OWNER_ISSUE_NOT_KNOWN")

    survivors = []
    with tempfile.TemporaryDirectory(prefix="adoption-selftest-") as raw:
        temp = Path(raw)
        positive = run(BASE)
        if positive.returncode != 0:
            print(f"ADOPTION-LEDGER-SELFTEST-RED positive={positive.stderr.strip()}", file=sys.stderr)
            return 2
        for name, (value, expected) in mutations.items():
            path = temp / f"{name}.json"
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            done = run(path)
            if done.returncode == 0 or expected not in done.stderr:
                survivors.append(name)
    if survivors:
        print(
            f"ADOPTION-LEDGER-SELFTEST-RED survived={','.join(sorted(survivors))}",
            file=sys.stderr,
        )
        return 2
    print(f"ADOPTION-LEDGER-SELFTEST-GREEN mutations={len(mutations)} all refused by name")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
