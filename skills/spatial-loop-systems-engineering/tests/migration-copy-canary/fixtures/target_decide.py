#!/usr/bin/env python3
"""Target side of the migration/copy canary: the faithful copy of the source.

The migration adapts the *shape* -- an if-chain becomes a dispatch table --
while preserving every source branch, so semantic parity holds even though the
bytes differ. This is the control arm.

`verify.sh` plants the semantic loss on a throwaway copy of this file by
deleting the `SKIPPED_BY_POLICY` row of `_DISPOSITION_BY_STATE`. The accepted
input domain stays intact, so the interface does not change and the legacy
compatibility oracle stays green; only the differential parity oracle can see
that branch B now falls through to the table default.
"""
from __future__ import annotations

# Interface surface: which inputs this target accepts. Kept separate from the
# dispatch table so that losing a branch is a silent wrong answer rather than a
# loud rejection -- the failure mode a compatibility suite is blind to.
ACCEPTED_EVIDENCE_STATES = (
    "PASS",
    "FAIL",
    "ABSENT",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "SKIPPED_BY_POLICY",
    "HUMAN_ADMIT_REQUIRED",
)

_DISPOSITION_BY_STATE = {
    "PASS": "PUBLISH_ELIGIBLE",
    "FAIL": "BLOCK",
    "ABSENT": "BLOCK",
    "NOT_IMPLEMENTED": "BLOCK",
    "NOT_EXERCISED": "BLOCK",
    "SKIPPED_BY_POLICY": "HOLD_FOR_POLICY_REVIEW",
    "HUMAN_ADMIT_REQUIRED": "HOLD_FOR_HUMAN_ADMIT",
}


def decide(evidence_state: str, human_admit_required: bool = False) -> str:
    """Route one evidence state to its publication disposition."""
    if evidence_state not in ACCEPTED_EVIDENCE_STATES:
        raise ValueError(f"unknown evidence state: {evidence_state}")
    if human_admit_required:
        return "HOLD_FOR_HUMAN_ADMIT"
    return _DISPOSITION_BY_STATE.get(evidence_state, "BLOCK")
