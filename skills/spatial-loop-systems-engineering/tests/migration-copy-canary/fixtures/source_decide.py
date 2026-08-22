#!/usr/bin/env python3
"""Source side of the migration/copy canary: the bytes a target must preserve.

This is deliberately the smallest thing that carries the failure mode #407
names. It routes one evidence state to one publication disposition, and one of
its branches -- `SKIPPED_BY_POLICY` -> `HOLD_FOR_POLICY_REVIEW` -- is never
exercised by the legacy caller surface. That is the branch a compatibility-only
migration drops without anything turning red.

`KNOWN_EVIDENCE_STATES` is the declared input domain. The differential parity
oracle enumerates it from here rather than from its own copy, so a state added
to the source widens the comparison instead of silently leaving the target
unchecked.
"""
from __future__ import annotations

# Declared input domain, aligned with the case-graph evidence states.
KNOWN_EVIDENCE_STATES = (
    "PASS",
    "FAIL",
    "ABSENT",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "SKIPPED_BY_POLICY",
    "HUMAN_ADMIT_REQUIRED",
)

# The legacy caller surface: the only states the compatibility suite covers.
# Branch B is outside it, which is exactly why compatibility cannot see it.
LEGACY_COMPATIBILITY_STATES = ("PASS", "FAIL", "ABSENT")


def decide(evidence_state: str, human_admit_required: bool = False) -> str:
    """Route one evidence state to its publication disposition."""
    if evidence_state not in KNOWN_EVIDENCE_STATES:
        raise ValueError(f"unknown evidence state: {evidence_state}")
    if human_admit_required:
        return "HOLD_FOR_HUMAN_ADMIT"
    if evidence_state == "PASS":
        return "PUBLISH_ELIGIBLE"
    if evidence_state == "SKIPPED_BY_POLICY":
        # Decision branch B. A policy skip is withheld work a reviewer must
        # dispose of explicitly; collapsing it into BLOCK loses the obligation.
        return "HOLD_FOR_POLICY_REVIEW"
    if evidence_state == "HUMAN_ADMIT_REQUIRED":
        return "HOLD_FOR_HUMAN_ADMIT"
    return "BLOCK"
