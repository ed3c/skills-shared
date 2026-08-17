#!/usr/bin/env python3
"""Validate the cross-Skill adoption ledger against exact current repository bytes.

The audit itself is the thing most likely to lie. A classification is cheap to
write and reads the same whether or not anything backs it, so every state here
has to survive a mechanical re-derivation:

    PASS with no evidence path            -> nothing was actually looked at
    ABSENT with evidence paths            -> the finding contradicts itself
    an executable claim proved by prose   -> a Markdown route counted as a gate
    a frozen treatment with no registry   -> unhashed bytes called immutable
    a golden proof claimed, none indexed  -> canonical status asserted by wording
    a layer above the registered proof    -> fixture evidence promoted upward
    a gap with no owning issue            -> the gap disappears at read time

Exit codes: 0 green, 2 at least one refused claim, 70 unusable ledger/schema.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from check_golden_proof_registry import (
    LAYERS,
    RegistryError,
    read_json,
    safe_repo_path,
    validate_schema,
)

PASS = "PASS"
NEEDS_EVIDENCE = {"PASS", "PARTIAL", "NOT_EXERCISED"}
FORBIDS_EVIDENCE = {"ABSENT", "NOT_IMPLEMENTED"}
NEEDS_OWNER = {"PARTIAL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED", "HUMAN_ADMIT_REQUIRED"}
EXECUTABLE_CRITERIA = {
    "old_strengths_asserted",
    "route_reachable",
    "schema_and_semantic_gates_executable",
    "hollow_dead_route_controls",
    "matched_hermetic_task",
}
EXECUTABLE_SUFFIXES = (".py", ".sh", ".ts", ".bash")
FROZEN_ROLES = {
    "old_canonical_treatment_frozen": "OLD_CANONICAL",
    "refactor_as_landed_treatment_frozen": "REFACTOR_AS_LANDED",
}
MAX_LAYER_WITHOUT_PROOF = "L2_EXECUTABLE_CONTRACT"


def registry_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for proof in registry.get("proofs", []):
        if isinstance(proof, dict) and isinstance(proof.get("owner_skill"), str):
            index[proof["owner_skill"]] = proof
    return index


def validate(repo: Path, ledger: dict[str, Any], registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    proofs = registry_index(registry)
    known = set(ledger["known_issues"])
    audited = [entry["skill"] for entry in ledger["skills"]]

    duplicates = sorted({name for name in audited if audited.count(name) > 1})
    for name in duplicates:
        errors.append(f"DUPLICATE_SKILL_ENTRY {name}")
    dropped = sorted(set(ledger["in_scope"]) - set(audited))
    extra = sorted(set(audited) - set(ledger["in_scope"]))
    for name in dropped:
        errors.append(f"IN_SCOPE_SKILL_UNCLASSIFIED {name}")
    for name in extra:
        errors.append(f"CLASSIFIED_SKILL_OUT_OF_SCOPE {name}")

    for entry in ledger["skills"]:
        skill = entry["skill"]
        try:
            root = safe_repo_path(repo, f"skills/{skill}")
        except RegistryError as exc:
            errors.append(f"{skill} {exc}")
            continue
        if not (root / "SKILL.md").is_file():
            errors.append(f"AUDITED_SKILL_ABSENT {skill}")

        proof = proofs.get(skill)
        criteria = entry["criteria"]
        for name, finding in criteria.items():
            state = finding["state"]
            evidence = finding["evidence"]
            for value in evidence:
                try:
                    path = safe_repo_path(repo, value)
                except RegistryError as exc:
                    errors.append(f"{skill}:{name} {exc}")
                    continue
                if not path.exists():
                    errors.append(f"EVIDENCE_PATH_ABSENT {skill}:{name}:{value}")
            if state in NEEDS_EVIDENCE and not evidence:
                errors.append(f"EVIDENCE_REQUIRED {skill}:{name}:{state}")
            if state in FORBIDS_EVIDENCE and evidence:
                errors.append(f"EVIDENCE_FORBIDDEN {skill}:{name}:{state}")
            if (
                name in EXECUTABLE_CRITERIA
                and state in {"PASS", "PARTIAL"}
                and not any(value.endswith(EXECUTABLE_SUFFIXES) for value in evidence)
            ):
                errors.append(f"MARKDOWN_ONLY_EXECUTABLE_CLAIM {skill}:{name}")

            owner = finding.get("owner_issue")
            if state in NEEDS_OWNER and owner is None:
                errors.append(f"GAP_WITHOUT_OWNER_ISSUE {skill}:{name}:{state}")
            if state not in NEEDS_OWNER and owner is not None:
                errors.append(f"OWNER_ISSUE_ON_CLOSED_FINDING {skill}:{name}:{state}")
            if owner is not None and owner not in known:
                errors.append(f"OWNER_ISSUE_NOT_KNOWN {skill}:{name}:{owner}")

            role = FROZEN_ROLES.get(name)
            if role and state == PASS:
                frozen = [
                    treatment.get("path")
                    for treatment in (proof or {}).get("treatments", [])
                    if isinstance(treatment, dict) and treatment.get("role") == role
                ]
                if not frozen:
                    errors.append(f"FROZEN_TREATMENT_UNREGISTERED {skill}:{role}")
                elif not set(frozen) & set(evidence):
                    errors.append(f"FROZEN_TREATMENT_NOT_CONTENT_BOUND {skill}:{role}")

        registered = criteria["golden_proof_registered"]["state"] == PASS
        if registered and proof is None:
            errors.append(f"GOLDEN_PROOF_UNREGISTERED {skill}")
        if not registered and proof is not None:
            errors.append(f"REGISTERED_PROOF_UNDERSTATED {skill}")
        if registered and entry["golden_proof_id"] != (proof or {}).get("id"):
            errors.append(f"GOLDEN_PROOF_ID_MISMATCH {skill}:{entry['golden_proof_id']}")
        if not registered and entry["golden_proof_id"] is not None:
            errors.append(f"GOLDEN_PROOF_ID_WITHOUT_REGISTRATION {skill}")

        highest = entry["highest_layer"]
        index = LAYERS.index(highest)
        if proof is None:
            if index > LAYERS.index(MAX_LAYER_WITHOUT_PROOF):
                errors.append(f"LAYER_ABOVE_REGISTERED_PROOF {skill}:{highest}")
        elif proof.get("highest_layer") != highest:
            errors.append(f"LAYER_DISAGREES_WITH_REGISTRY {skill}:{highest}")
        if criteria["matched_hermetic_task"]["state"] == PASS and index < LAYERS.index("L3_HERMETIC_REAL_TASK"):
            errors.append(f"HERMETIC_PASS_BELOW_LAYER {skill}:{highest}")
        if criteria["live_model_runtime_ab"]["state"] == PASS and index < LAYERS.index("L4_MATCHED_LIVE_MODEL_RUNTIME"):
            errors.append(f"LIVE_PASS_BELOW_LAYER {skill}:{highest}")
        if criteria["molecular_traceability"]["state"] == PASS:
            errors.append(f"DELIVERY_PASS_WITHOUT_LIVE_RECEIPT {skill}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    repo = (args.repo_root or root.parents[1]).resolve()
    schema = args.schema or (root / "references/skill-adoption-ledger.schema.json")
    try:
        ledger = read_json(args.ledger)
        validate_schema(ledger, schema)
        registry_path = args.registry
        if registry_path is None:
            registry_path = safe_repo_path(repo, ledger["golden_proof_registry"])
        if not Path(registry_path).is_file():
            raise RegistryError(f"golden proof registry absent: {registry_path}")
        registry = read_json(Path(registry_path))
        errors = validate(repo, ledger, registry)
    except RegistryError as exc:
        print(f"SKILL-ADOPTION-MECHANISM-RED {exc}", file=sys.stderr)
        return 70
    if errors:
        for error in errors:
            print(f"SKILL-ADOPTION-RED {error}", file=sys.stderr)
        return 2
    gaps = sum(
        1
        for entry in ledger["skills"]
        for finding in entry["criteria"].values()
        if finding["state"] != PASS
    )
    print(
        f"SKILL-ADOPTION-GREEN skills={len(ledger['skills'])} gaps={gaps} "
        "owned by known issues; delivery state and live runtime not inferred"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
