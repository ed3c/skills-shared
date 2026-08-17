#!/usr/bin/env python3
"""Frozen deterministic A/B/C/D for the Agentic Tech Lead refactor.

This is a structural/executable-contract experiment, not a model-behavior test.
It keeps every historical treatment immutable and scores the current candidate
on the same binary criteria plus one causal-transition criterion introduced by
Shadow issue #309.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
OLD = FIXTURES / "pre-refactor-SKILL.txt"
LANDED = FIXTURES / "refactor-as-landed-SKILL.txt"
LANDED_PROFILE = FIXTURES / "refactor-as-landed-domain-profile.txt"
REACHABILITY = FIXTURES / "reachability-repaired-SKILL.txt"
REACHABILITY_PROFILE = FIXTURES / "reachability-repaired-domain-profile.txt"
CURRENT = ROOT / "SKILL.md"
CURRENT_PROFILE = ROOT / "modules" / "domain-profile.md"

EXPECTED_GIT_BLOBS = {
    OLD: "a01f53592cda98f61b413b4467afa96356fb4ef7",
    LANDED: "8b2da7443aff7a9f53412b5af280048203bbd5e9",
    LANDED_PROFILE: "812f161c8abbe0517502ea988673197519132c1c",
    REACHABILITY: "51c3fd81749598957f2b993c4d31c3b4c8c277c1",
    REACHABILITY_PROFILE: "7726ccc5a45db8e31723d457b9129b4697fdca3c",
}

PROVIDER_TOKENS = ("grepai", "scip", "tree-sitter", "serena", "lancedb")
MODULE_LINKS = (
    "deterministic-code-intelligence.md",
    "semantic-intent-anchor.md",
    "agent-executor.md",
    "vector-store.md",
    "stacked-delivery.md",
    "tournament-mode.md",
)


@dataclass(frozen=True)
class Arm:
    name: str
    skill: str
    profile: str = ""


def git_blob_sha(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def portable_core(text: str) -> str | None:
    start = "<!-- PORTABLE_CORE_START -->"
    end = "<!-- PORTABLE_CORE_END -->"
    if start not in text or end not in text:
        return None
    return text.split(start, 1)[1].split(end, 1)[0]


def has_all(text: str, needles: tuple[str, ...]) -> bool:
    lower = text.casefold()
    return all(needle.casefold() in lower for needle in needles)


def score(arm: Arm) -> dict[str, bool]:
    skill = arm.skill
    profile = arm.profile
    core = portable_core(skill)
    lower = skill.casefold()
    profile_lower = profile.casefold()

    provider_neutral = core is not None and not any(
        token in core.casefold() for token in PROVIDER_TOKENS
    )

    task_gate = "scripts/assert_task_contract.py" in skill
    gate_before_workers = task_gate and (
        "validate a task packet before dispatch" in lower
        or "before any worker is admitted" in lower
        or "any non-zero result blocks dispatch" in lower
    )

    old_direct_router = (
        "modules/README.md" in skill
        and has_all(skill, PROVIDER_TOKENS)
        and "selected by trigger" in lower
    )
    refactor_router = bool(profile) and all(link in profile for link in MODULE_LINKS)
    concrete_router = old_direct_router or refactor_router

    readback = "current-source readback" in lower or "exact-source readback" in lower
    candidate_ceiling = any(
        phrase in lower
        for phrase in (
            "search is not truth",
            "produce candidates",
            "candidate evidence",
            "retrieval candidates",
            "never canonical task state",
            "never self-validating",
        )
    )
    evidence_ceiling = readback and candidate_ceiling

    dag_lease = (
        ("path-disjoint" in lower or "writers disjoint" in lower or "overlapping leases" in lower)
        and "dag" in lower
        and "dependency" in lower
    )
    bounded_repair = (
        "at most three" in lower
        or "max_repairs_per_signature" in lower
        or "bounded retries" in lower
    )
    global_objective = "global objective" in lower or "global-objective" in lower
    human_authority = (
        "human" in lower
        and "merge" in lower
        and ("not a merged system" in lower or "human-owned" in lower or "human governed" in lower or "human/repository authority" in lower)
    )
    self_activation_refusal = (
        "selected by trigger" in lower
        or "never activates itself" in profile_lower
        or "auto-activate itself" in profile_lower
    )

    # The old monolith has an explicit causal T0→T10 chain. A modular arm gets
    # equivalent credit only if it has an executable receipt-gated transition
    # checker and a plan/receipt contract; reachability alone is insufficient.
    old_causal_chain = all(f"T{i}" in skill for i in range(11)) and "T0 ROUTE" in skill and "T10 HANDOFF" in skill
    modular_causal_chain = (
        "scripts/assert_capability_dag.py" in skill
        and "capability-plan.schema.json" in skill
        and "capability-receipts.schema.json" in skill
        and "t0-t10-causal-map.json" in skill
        and "predecessor" in profile_lower
        and "capability receipt" in profile_lower
        and "required_before_state" in profile_lower
        and "fixture" in profile_lower
        and "live" in profile_lower
    )

    return {
        "portable_core_provider_neutral": provider_neutral,
        "pre_dispatch_task_assertion_reachable": task_gate,
        "task_assertion_ordered_before_workers": gate_before_workers,
        "concrete_module_trigger_routing": concrete_router,
        "evidence_ceiling_and_readback": evidence_ceiling,
        "dag_and_writer_lease_guard": dag_lease,
        "bounded_repair": bounded_repair,
        "global_objective_retention": global_objective,
        "human_delivery_authority": human_authority,
        "module_self_activation_refused": self_activation_refusal,
        "causal_module_transitions_closed": old_causal_chain or modular_causal_chain,
    }


def dominates(candidate: dict[str, bool], baseline: dict[str, bool]) -> bool:
    return all((not baseline[k]) or candidate[k] for k in baseline) and any(
        candidate[k] and not baseline[k] for k in baseline
    )


def main() -> int:
    for path, expected in EXPECTED_GIT_BLOBS.items():
        observed = git_blob_sha(path.read_text(encoding="utf-8"))
        if observed != expected:
            print(f"TECH-LEAD-AB-RED fixture drift {path.name}: expected={expected} observed={observed}", file=sys.stderr)
            return 2

    arms = [
        Arm("A_OLD_MONOLITH", OLD.read_text(encoding="utf-8")),
        Arm("B0_REFACTOR_AS_LANDED", LANDED.read_text(encoding="utf-8"), LANDED_PROFILE.read_text(encoding="utf-8")),
        Arm("B1_REACHABILITY_REPAIRED", REACHABILITY.read_text(encoding="utf-8"), REACHABILITY_PROFILE.read_text(encoding="utf-8")),
        Arm("B2_CAUSAL_DAG_REPAIRED", CURRENT.read_text(encoding="utf-8"), CURRENT_PROFILE.read_text(encoding="utf-8")),
    ]
    results = {arm.name: score(arm) for arm in arms}
    totals = {name: sum(values.values()) for name, values in results.items()}

    old = results["A_OLD_MONOLITH"]
    landed = results["B0_REFACTOR_AS_LANDED"]
    reachability = results["B1_REACHABILITY_REPAIRED"]
    causal = results["B2_CAUSAL_DAG_REPAIRED"]

    expected_landed_regressions = {
        "pre_dispatch_task_assertion_reachable",
        "task_assertion_ordered_before_workers",
        "concrete_module_trigger_routing",
    }
    if [k for k in expected_landed_regressions if landed[k]]:
        print("TECH-LEAD-AB-RED B0 scorer failed to expose landed regressions", file=sys.stderr)
        return 2
    if not all(old[k] for k in expected_landed_regressions):
        print("TECH-LEAD-AB-RED old treatment lost known executable routes", file=sys.stderr)
        return 2

    if not dominates(reachability, {k: v for k, v in old.items() if k != "causal_module_transitions_closed"}):
        print("TECH-LEAD-AB-RED B1 no longer dominates old on the original #307 dimensions", file=sys.stderr)
        return 2
    if reachability["causal_module_transitions_closed"]:
        print("TECH-LEAD-AB-RED B1 incorrectly credited with receipt-gated causal closure", file=sys.stderr)
        return 2
    if not causal["causal_module_transitions_closed"]:
        print("TECH-LEAD-AB-RED B2 did not close causal module transitions", file=sys.stderr)
        return 2
    if not dominates(causal, reachability) or not dominates(causal, old):
        regressed = [k for k in old if old[k] and not causal[k]]
        print(f"TECH-LEAD-AB-RED B2 does not dominate prior treatments; regressions={regressed}", file=sys.stderr)
        return 2

    report = {
        "schema": "agentic-tech-lead/refactor-ab/v2",
        "evidence_scope": "deterministic structural, executable-contract, and causal-transition closure only",
        "behavioral_model_uplift": "NOT_EXERCISED",
        "live_provider_runtime": "NOT_EXERCISED",
        "subjects": {
            "A_OLD_MONOLITH": EXPECTED_GIT_BLOBS[OLD],
            "B0_REFACTOR_AS_LANDED": EXPECTED_GIT_BLOBS[LANDED],
            "B0_DOMAIN_PROFILE": EXPECTED_GIT_BLOBS[LANDED_PROFILE],
            "B1_REACHABILITY_REPAIRED": EXPECTED_GIT_BLOBS[REACHABILITY],
            "B1_DOMAIN_PROFILE": EXPECTED_GIT_BLOBS[REACHABILITY_PROFILE],
            "B2_CAUSAL_DAG_REPAIRED": git_blob_sha(CURRENT.read_text(encoding="utf-8")),
            "B2_DOMAIN_PROFILE": git_blob_sha(CURRENT_PROFILE.read_text(encoding="utf-8")),
        },
        "results": results,
        "totals": totals,
        "landed_refactor_regression_exposed": True,
        "reachability_repair_preserved": True,
        "causal_dag_repair_dominates_prior_treatments": True,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print("TECH-LEAD-AB-GREEN B0 regressions exposed; B1 restores reachability; B2 adds receipt-gated causal closure and dominates prior deterministic treatments; live model/provider A/B NOT_EXERCISED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
