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
# Every in-scope Skill now carries a registered proof, so gap/absence mutations
# use live_model_runtime_ab (kept NOT_IMPLEMENTED by the zero-network law) and
# proof-absence mutations run against a registry copy with this proof stripped.
REGISTRY = ROOT / "references/golden-proof-registry.json"
STRIPPED_REGISTRY_MUTATIONS = {
    "unregistered_golden_proof_claimed",
    "layer_above_registered_proof",
}


def run(path: Path, registry: Path | None = None) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(CHECKER), "--ledger", str(path), "--schema", str(SCHEMA)]
    if registry is not None:
        argv += ["--registry", str(registry)]
    return subprocess.run(argv, text=True, capture_output=True, check=False)


def entry(value: dict, skill: str) -> dict:
    return next(row for row in value["skills"] if row["skill"] == skill)


def leaf(value: dict, skill: str) -> dict:
    return next(row for row in value["migration_order"] if row["skill"] == skill)


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
    entry(contradiction, UNPROVEN)["criteria"]["live_model_runtime_ab"]["evidence"] = [
        f"skills/{UNPROVEN}/SKILL.md"
    ]
    mutations["absent_finding_with_evidence"] = (contradiction, "EVIDENCE_FORBIDDEN")

    claimed = copy.deepcopy(base)
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
    entry(orphan, UNPROVEN)["criteria"]["live_model_runtime_ab"].pop("owner_issue")
    mutations["gap_without_owner_issue"] = (orphan, "GAP_WITHOUT_OWNER_ISSUE")

    invented = copy.deepcopy(base)
    entry(invented, UNPROVEN)["criteria"]["live_model_runtime_ab"]["owner_issue"] = 99999
    mutations["gap_owned_by_unknown_issue"] = (invented, "OWNER_ISSUE_NOT_KNOWN")

    # The migration order is derived from observable coupling, so every way of
    # asserting an order that the edges do not support has to name itself.
    cycle = copy.deepcopy(base)
    row = leaf(cycle, "github-delivery-loop")
    row["depends_on"] = ["dual-forge-repository-loop"]
    row["basis"] = ["skills/dual-forge-repository-loop/scripts/check_dual_forge_contract.py"]
    mutations["migration_order_cycle"] = (cycle, "MIGRATION_ORDER_CYCLE")

    resequenced = copy.deepcopy(base)
    order = resequenced["migration_order"]
    order[-2], order[-1] = order[-1], order[-2]
    mutations["migration_order_resequenced"] = (resequenced, "MIGRATION_ORDER_NOT_CANONICAL")

    unknown_leaf = copy.deepcopy(base)
    leaf(unknown_leaf, UNPROVEN)["issue"] = 99999
    mutations["migration_leaf_issue_unknown"] = (unknown_leaf, "MIGRATION_ISSUE_NOT_KNOWN")

    idle_leaf = copy.deepcopy(base)
    leaf(idle_leaf, UNPROVEN)["issue"] = 318
    mutations["migration_leaf_owns_no_gap"] = (idle_leaf, "MIGRATION_ISSUE_OWNS_NO_GAP")

    shared_leaf = copy.deepcopy(base)
    shared = leaf(shared_leaf, "controlled-technical-language-harness")["issue"]
    entry(shared_leaf, UNPROVEN)["criteria"]["live_model_runtime_ab"]["owner_issue"] = shared
    mutations["migration_leaf_owns_another_skills_gap"] = (shared_leaf, "MIGRATION_ISSUE_NOT_SKILL_LEAF")

    unordered = copy.deepcopy(base)
    unordered["migration_order"] = [
        row for row in unordered["migration_order"] if row["skill"] != UNPROVEN
    ]
    mutations["migration_skill_unordered"] = (unordered, "MIGRATION_SKILL_UNORDERED")

    strayed = copy.deepcopy(base)
    stray = copy.deepcopy(leaf(strayed, UNPROVEN))
    stray["skill"] = "skill-that-does-not-exist"
    strayed["migration_order"].append(stray)
    mutations["migration_skill_out_of_scope"] = (strayed, "MIGRATION_SKILL_OUT_OF_SCOPE")

    twice = copy.deepcopy(base)
    twice["migration_order"].append(copy.deepcopy(leaf(twice, UNPROVEN)))
    mutations["migration_duplicate_skill"] = (twice, "MIGRATION_DUPLICATE_SKILL")

    ghost_blocker = copy.deepcopy(base)
    row = leaf(ghost_blocker, UNPROVEN)
    row["depends_on"] = ["skill-that-does-not-exist"]
    row["basis"] = ["skills/skill-refactor-proof-loop/tests/run-all.sh"]
    mutations["migration_blocker_unknown_skill"] = (ghost_blocker, "MIGRATION_DEPENDENCY_UNKNOWN_SKILL")

    unbacked = copy.deepcopy(base)
    leaf(unbacked, "dual-forge-repository-loop")["basis"] = []
    mutations["migration_blocker_without_basis"] = (unbacked, "MIGRATION_BASIS_REQUIRED")

    padded = copy.deepcopy(base)
    leaf(padded, UNPROVEN)["basis"] = ["skills/skill-refactor-proof-loop/tests/run-all.sh"]
    mutations["migration_basis_without_blocker"] = (padded, "MIGRATION_BASIS_FORBIDDEN")

    imagined = copy.deepcopy(base)
    leaf(imagined, "dual-forge-repository-loop")["basis"] = [
        "skills/dual-forge-repository-loop/scripts/never_written.py"
    ]
    mutations["migration_basis_path_absent"] = (imagined, "MIGRATION_BASIS_PATH_ABSENT")

    survivors = []
    with tempfile.TemporaryDirectory(prefix="adoption-selftest-") as raw:
        temp = Path(raw)
        positive = run(BASE)
        if positive.returncode != 0:
            print(f"ADOPTION-LEDGER-SELFTEST-RED positive={positive.stderr.strip()}", file=sys.stderr)
            return 2
        stripped = json.loads(REGISTRY.read_text(encoding="utf-8"))
        stripped["proofs"] = [
            proof for proof in stripped["proofs"] if proof.get("owner_skill") != UNPROVEN
        ]
        stripped_path = temp / "registry-without-subject-proof.json"
        stripped_path.write_text(json.dumps(stripped, indent=2) + "\n", encoding="utf-8")
        for name, (value, expected) in mutations.items():
            path = temp / f"{name}.json"
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            done = run(path, stripped_path if name in STRIPPED_REGISTRY_MUTATIONS else None)
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
