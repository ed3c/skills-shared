#!/usr/bin/env python3
"""Frozen deterministic A/B for the forge-delivery-loop portable-core refactor.

The refactor is real and is in this repository's history: commit d757a5c
(PR #270) replaced a 224-line host-bound body with a portable core, deleting
161 lines. Nothing measured whether the strengths in those deleted lines
survived, and a shorter body reads the same whether they did or not.

So the strengths are named here as binary criteria and every treatment is
scored on the same list:

    A_OLD_CANONICAL        blob 9f47aa5d, the body PR #189 left behind
    B0_REFACTOR_AS_LANDED  blob c75c7f2d, exactly what PR #270 landed
    B1_CONTROLS_REBOUND    the live SKILL.md, this leaf's repair

A and B0 are frozen fixtures; B1 is the live body, so a treatment always has
exactly one immutable subject. When the live body changes again, freeze it as
the next fixture first rather than letting B1's identity drift with it.

This is a structural/executable-contract experiment. It says nothing about
model behaviour and nothing about any live forge: zero network, no clock.
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
CURRENT = ROOT / "SKILL.md"
CURRENT_PROFILE = ROOT / "modules" / "domain-profile.md"

EXPECTED_GIT_BLOBS = {
    OLD: "9f47aa5d8c90b1141afd7ca15ef06e086c7f2fbb",
    LANDED: "c75c7f2d7e94eb0b4ec0a5b4355084849154fe15",
    LANDED_PROFILE: "aadb2efb4d4d67ed84342de40493cc87bfe13ac1",
}

# The same tokens evals/skill-core-boundaries.json forbids inside the bounded
# core. Duplicated as a literal on purpose: this file must keep scoring frozen
# treatments the same way after the manifest changes.
HOST_TOKENS = ("forgejo", "chrome", "localhost", "keychain", "runtime-env")
EVIDENCE_STATES = (
    "PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED",
    "SKIPPED_BY_POLICY", "HUMAN_ADMIT_REQUIRED",
)
CORE_ASSERTION = "python3 scripts/check_skill_core_boundaries.py --skill forgejo-delivery-loop"


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


def score(arm: Arm) -> dict[str, bool]:
    """Twelve binary criteria, each written so both the old body and a portable
    body can earn it. The old body is in Chinese and names concrete tools; the
    portable bodies are in English and name laws. A criterion that only one
    dialect could satisfy would measure translation, not preservation."""
    skill = arm.skill
    profile = arm.profile
    core = portable_core(skill)

    # 1-2. strengths the refactor kept.
    exact_subject = "synced_at_commit" in skill or "CORE-LAW-001" in skill
    local_not_remote = (
        ("check_delivery_receipt.py" in skill and "delivery_status.py" in skill)
        or "CORE-LAW-002" in skill
    )
    credential_delegated = "runtime-env local-env migrate-forgejo-keychain" in skill

    # 3-7. strengths PR #270 dropped. Each names the control that holds it, not
    # the sentiment: a body that says "merge stays human" without reaching the
    # sweep cannot notice when merge is re-widened.
    merge_sweep = "tests/merge-authority/" in skill and "mutation_allowed" in skill
    readback_chain = all(
        token in skill for token in ("capture-pre-live", "verify-live", "readback-receipt")
    )
    self_report_refused = "verified receipt" in skill and (
        "自填" in skill or "hand-filled" in skill
    )
    index_both_ways = "tests/index/verify.sh" in skill and "tests/run-all.sh" in skill
    router_before_mutation = "route.ts" in skill and "--selftest" in skill

    # 8-12. what the refactor bought, scored so the old body cannot claim it.
    core_host_neutral = core is not None and not any(
        token in core.replace(CORE_ASSERTION, "").casefold() for token in HOST_TOKENS
    )
    module_trigger_routing = (
        "modules/domain-profile.md" in skill
        and "## Trigger" in profile
        and "## Non-trigger" in profile
        and "## Evidence ceiling" in profile
    )
    evidence_vocabulary = all(state in skill for state in EVIDENCE_STATES)
    module_cannot_widen = "CORE-LAW-004" in skill and "may not override" in profile.casefold()

    return {
        "exact_subject_bound": exact_subject,
        "local_evidence_is_not_remote_evidence": local_not_remote,
        "credential_ownership_delegated": credential_delegated,
        "merge_authority_sweep_reachable": merge_sweep,
        "typed_readback_chain_named": readback_chain,
        "self_filled_observation_refused": self_report_refused,
        "index_checked_both_ways": index_both_ways,
        "router_runs_before_mutation": router_before_mutation,
        "portable_core_host_neutral": core_host_neutral,
        "module_trigger_routing": module_trigger_routing,
        "evidence_vocabulary_uncollapsed": evidence_vocabulary,
        "module_cannot_widen_authority": module_cannot_widen,
    }


def dominates(candidate: dict[str, bool], baseline: dict[str, bool]) -> bool:
    return all((not baseline[k]) or candidate[k] for k in baseline) and any(
        candidate[k] and not baseline[k] for k in baseline
    )


def red(message: str) -> int:
    print(f"FORGEJO-REFACTOR-AB-RED {message}", file=sys.stderr)
    return 2


def main() -> int:
    for path, expected in EXPECTED_GIT_BLOBS.items():
        observed = git_blob_sha(path.read_text(encoding="utf-8"))
        if observed != expected:
            return red(f"frozen treatment drift {path.name}: expected={expected} observed={observed}")

    landed_profile = LANDED_PROFILE.read_text(encoding="utf-8")
    arms = [
        Arm("A_OLD_CANONICAL", OLD.read_text(encoding="utf-8")),
        Arm("B0_REFACTOR_AS_LANDED", LANDED.read_text(encoding="utf-8"), landed_profile),
        Arm(
            "B1_CONTROLS_REBOUND",
            CURRENT.read_text(encoding="utf-8"),
            CURRENT_PROFILE.read_text(encoding="utf-8"),
        ),
    ]
    results = {arm.name: score(arm) for arm in arms}
    totals = {name: sum(values.values()) for name, values in results.items()}
    old, landed, rebound = (
        results["A_OLD_CANONICAL"],
        results["B0_REFACTOR_AS_LANDED"],
        results["B1_CONTROLS_REBOUND"],
    )

    # The regressions this leaf exists to measure. If the scorer stops seeing
    # them it has been tuned to agree with the current body, so it goes red
    # rather than reporting a green that means nothing.
    expected_landed_regressions = {
        "merge_authority_sweep_reachable",
        "typed_readback_chain_named",
        "self_filled_observation_refused",
        "index_checked_both_ways",
        "router_runs_before_mutation",
    }
    held = sorted(k for k in expected_landed_regressions if landed[k])
    if held:
        return red(f"B0 scorer failed to expose landed regressions: {held}")
    if not all(old[k] for k in expected_landed_regressions):
        return red("old treatment did not hold the strengths B0 is measured against")
    refactor_gains = {"portable_core_host_neutral", "module_trigger_routing", "evidence_vocabulary_uncollapsed"}
    if any(old[k] for k in refactor_gains):
        return red("old treatment credited with portable-core properties it never had")
    if not all(landed[k] for k in refactor_gains):
        return red("B0 lost the portable-core properties the refactor was for")
    if not dominates(rebound, old):
        return red(f"B1 does not dominate A; regressions={[k for k in old if old[k] and not rebound[k]]}")
    if not dominates(rebound, landed):
        return red(f"B1 does not dominate B0; regressions={[k for k in landed if landed[k] and not rebound[k]]}")

    report = {
        "schema": "forgejo-delivery-loop/refactor-ab/v1",
        "evidence_scope": "deterministic structural and executable-contract only",
        "behavioral_model_uplift": "NOT_EXERCISED",
        "live_forge_runtime": "NOT_EXERCISED",
        "subjects": {
            "A_OLD_CANONICAL": EXPECTED_GIT_BLOBS[OLD],
            "B0_REFACTOR_AS_LANDED": EXPECTED_GIT_BLOBS[LANDED],
            "B0_DOMAIN_PROFILE": EXPECTED_GIT_BLOBS[LANDED_PROFILE],
            "B1_CONTROLS_REBOUND": git_blob_sha(CURRENT.read_text(encoding="utf-8")),
            "B1_DOMAIN_PROFILE": git_blob_sha(CURRENT_PROFILE.read_text(encoding="utf-8")),
        },
        "results": results,
        "totals": totals,
        "landed_refactor_regression_exposed": sorted(expected_landed_regressions),
        "rebound_dominates_both_prior_treatments": True,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print(
        "FORGEJO-REFACTOR-AB-GREEN A=%d B0=%d B1=%d; five old strengths dropped by PR #270 are "
        "exposed and rebound without re-importing host semantics; live forge/model A/B NOT_EXERCISED"
        % (totals["A_OLD_CANONICAL"], totals["B0_REFACTOR_AS_LANDED"], totals["B1_CONTROLS_REBOUND"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
