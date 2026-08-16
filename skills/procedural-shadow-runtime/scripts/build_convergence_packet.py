#!/usr/bin/env python3
"""Assemble the #220 convergence packet and decide its own terminal outcome.

Exit codes:
  0   the packet closed as ADMITTED_FOR_BOUND_SCOPE against a Human record
  2   the packet closed as HOLD_FOR_MORE_EVIDENCE or REJECTED
  64  a named receipt, the rollback subject, or the output path is absent

This script cannot promote anything. Its most useful output is a refusal with
an itemised reason, and that is the output it produces today.

Three rules it exists to enforce.

Every lane is named, including the ones that did not close. A packet that lists
only its successes has removed the denominator, and the resulting score is the
score of whatever happened to work. Each prerequisite issue appears here with a
state drawn from a fixed vocabulary, and a lane with no receipt is ABSENT rather
than omitted.

Every receipt is re-read and re-digested at packet time. A path recorded in a
document is a claim about a file; a digest computed from the bytes is evidence
about its contents. If a receipt moves or changes after the packet is built, a
rebuild disagrees.

The rollback bundle must be a different tree from the candidate. A rollback that
resolves to the candidate is not a rollback, and the failure is invisible in
every artefact that only records its name.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
RECEIPTS = SKILL / "evals" / "receipts"

INVALID = 64
NOT_ADMITTED = 2

LANE_STATES = {"PASS", "FAIL", "BLOCKED", "ABSENT", "NOT_EXERCISED", "TERMINAL_EXCLUSION"}
LEVELS = ["L0", "L1", "L2", "L3", "L4", "L5"]
TERMINAL_OUTCOMES = {"ADMITTED_FOR_BOUND_SCOPE", "HOLD_FOR_MORE_EVIDENCE", "REJECTED",
                     "SUPERSEDED", "REVOKED"}

# Values that must never appear in a release artefact. Checked against the
# packet's own bytes, because a privacy review that is only a sentence is a
# sentence.
FORBIDDEN_PATTERNS = [
    (r"/Users/[A-Za-z0-9._-]+", "absolute home path"),
    (r"(?i)\b(?:api[_-]?key|secret|password|bearer)\b\s*[:=]\s*\S+", "credential-shaped value"),
    # Field shapes, not the English phrase. Matching prose flagged this packet's
    # own "no claim from private chain-of-thought inspection" -- a scanner that
    # cannot tell a disclaimer from a payload trains its reader to skip it.
    (r'"(?:chain_of_thought|chain-of-thought|raw_reasoning|private_reasoning|'
     r'hidden_reasoning|reasoning_trace)"\s*:', "private reasoning field"),
    (r"\b\d{13,19}\b", "primary-account-number-shaped digits"),
    (r"[A-Za-z0-9._%+-]+@(?!example\.invalid)[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "email address"),
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def bind_receipt(relative: str) -> dict[str, Any]:
    """Re-read and re-digest. A recorded path is a claim; the bytes are evidence."""
    path = SKILL / relative
    if not path.is_file():
        return {"path": relative, "present": False, "sha256": None}
    return {"path": relative, "present": True, "sha256": sha256_bytes(path.read_bytes())}


def run_checker(script: str, *relative_args: str) -> dict[str, Any]:
    """Arguments are skill-relative in and out.

    Recording the resolved absolute paths put one developer's home directory in
    the release artefact three times over, and the packet's own privacy scan is
    what found it.
    """
    resolved = [str(SKILL / item) for item in relative_args]
    result = subprocess.run([sys.executable, str(SKILL / "scripts" / script), *resolved],
                            capture_output=True, text=True, check=False)
    return {"checker": script, "args": list(relative_args), "exit_code": result.returncode,
            "stdout": result.stdout.strip()[:400]}


LANES: list[dict[str, Any]] = [
    {
        "issue": "#212",
        "lane": "exact-head GitHub Actions execution and replayable artifacts",
        "receipts": ["evals/receipts/github-actions-exact-head.json"],
        "if_absent": "ABSENT",
        "note": "The workflow uploads an exact-head evidence bundle; the receipt binding a run_id, job_id and head SHA is written after that run completes.",
    },
    {
        "issue": "#213",
        "lane": "Claude Code adapter and live exact-subject receipts",
        "receipts": ["evals/receipts/arm-trials-claude-code-23753e11b417.json",
                     "evals/receipts/host-claude-code-f94866291d8c.json"],
        "if_absent": "ABSENT",
        "note": "Five matched arms plus a prior deterministic-probe receipt. One repetition: mechanism, not the preregistered matrix.",
    },
    {
        "issue": "#214",
        "lane": "Codex CLI adapter and live exact-subject receipts",
        "receipts": ["evals/receipts/arm-trials-codex-cli-23753e11b417.json",
                     "evals/receipts/host-codex-cli-f94866291d8c.json"],
        "if_absent": "ABSENT",
        "note": "Same adapter, distinct host evidence; sandbox and approval policy bound per cell.",
    },
    {
        "issue": "#215",
        "lane": "first consumer-repository binding and domain-decoupled canaries",
        "receipts": ["evals/receipts/consumer-canary-ios-device-autopilot-30aa45c654ed.json",
                     "evals/receipts/consumer-runtime-receipt-ios-device-autopilot-30aa45c654ed.json"],
        "if_absent": "ABSENT",
        "note": "ed3c/ios-device-autopilot; the consumer branch is committed locally and unpushed.",
    },
    {
        "issue": "#216",
        "lane": "production-to-Golden feedback closure",
        "receipts": ["evals/receipts/feedback-closure-canary-2026-08-16.json"],
        "if_absent": "ABSENT",
        "note": "Admitted production-like canary, not production traffic. All seven states closed against a named Human adjudication.",
    },
    {
        "issue": "#217",
        "lane": "external semantic judge with deterministic non-override gates",
        "receipts": ["evals/receipts/judge-verdict-0-anchor-positive-0a7f7e3148cc.json",
                     "evals/receipts/judge-verdict-2-anchor-injection-0a7f7e3148cc.json"],
        "if_absent": "ABSENT",
        "note": "Closed upstream of this packet; anchors included so the calibration is re-checkable here.",
    },
    {
        "issue": "#218",
        "lane": "external registry retrieval and multimodal observation",
        "receipts": ["evals/receipts/retrieval-obra-superpowers-b36e0829c6d0.json",
                     "evals/receipts/multimodal-browser-truthful.json",
                     "evals/receipts/multimodal-browser-lookalike.json",
                     "evals/receipts/multimodal-device-lane.json"],
        "if_absent": "ABSENT",
        "note": "Two independent lanes. The device lane is NOT_EXERCISED and says so in its own bundle.",
    },
    {
        "issue": "#219",
        "lane": "matched cross-model/cross-harness causal uplift",
        "receipts": ["evals/uplift-matrix-summary.json"],
        "if_absent": "ABSENT",
        "note": "PARTIAL by owner decision, and saturated on this case set. No preregistered contrast is available.",
    },
]


def evaluate_lanes() -> list[dict[str, Any]]:
    lanes = []
    for lane in LANES:
        bound = [bind_receipt(item) for item in lane["receipts"]]
        present = [item for item in bound if item["present"]]
        state = "PASS" if len(present) == len(bound) else (
            "ABSENT" if not present else "BLOCKED")
        lanes.append({**lane, "receipts": bound, "state": state,
                      "receipts_present": len(present), "receipts_named": len(bound)})
    return lanes


def level_gates(lanes: list[dict[str, Any]], uplift: dict[str, Any] | None) -> list[dict[str, Any]]:
    """One entry per level, each with the single reason it is or is not reachable."""
    by_issue = {lane["issue"]: lane for lane in lanes}
    ci_closed = by_issue["#212"]["state"] == "PASS"
    hosts_closed = by_issue["#213"]["state"] == "PASS" and by_issue["#214"]["state"] == "PASS"
    consumer_closed = by_issue["#215"]["state"] == "PASS"
    attribution_qualifies = bool(uplift and uplift.get("qualifies_for_219"))
    production_real = False  # the canary is admitted as production-like, never as production

    return [
        {"level": "L0", "reachable": hosts_closed,
         "blocked_by": None if hosts_closed else "no live host receipt"},
        {"level": "L1", "reachable": hosts_closed and ci_closed,
         "blocked_by": None if (hosts_closed and ci_closed) else "no exact-head CI receipt (#212)"},
        {"level": "L2", "reachable": hosts_closed and ci_closed and consumer_closed,
         "blocked_by": None if (hosts_closed and ci_closed and consumer_closed)
                       else "invariant oracle not exercised outside this repository"},
        {"level": "L3", "reachable": False,
         "blocked_by": "held-out transfer absent: one consumer repository is not a held-out family"},
        {"level": "L4", "reachable": attribution_qualifies,
         "blocked_by": None if attribution_qualifies
                       else "five-arm attribution is PARTIAL and its primary metric is saturated (#219)"},
        {"level": "L5", "reachable": production_real,
         "blocked_by": "production feedback closed on an admitted canary, not on production traffic (#216)"},
    ]


def privacy_review(packet_bytes: bytes) -> dict[str, Any]:
    findings = []
    text = packet_bytes.decode("utf-8", errors="replace")
    for pattern, label in FORBIDDEN_PATTERNS:
        for match in re.findall(pattern, text):
            findings.append({"kind": label, "sample": str(match)[:60]})
    return {"executed": True, "findings": findings,
            "result": "CLEAN" if not findings else "FINDINGS_PRESENT"}


def build(rollback_ref: str, admit_record: Path | None) -> dict[str, Any]:
    candidate_commit = git("rev-parse", "HEAD")
    candidate_tree = git("rev-parse", f"HEAD:skills/procedural-shadow-runtime")
    try:
        rollback_commit = git("rev-parse", rollback_ref)
        rollback_tree = git("rev-parse", f"{rollback_ref}:skills/procedural-shadow-runtime")
    except subprocess.CalledProcessError:
        print(f"PACKET-INVALID unresolvable-rollback: {rollback_ref}", file=sys.stderr)
        raise SystemExit(INVALID)

    lanes = evaluate_lanes()
    summary_path = SKILL / "evals" / "uplift-matrix-summary.json"
    uplift = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else None
    gates = level_gates(lanes, uplift)

    recomputation = [
        run_checker("check_runtime_receipt.py",
                    "evals/receipts/consumer-runtime-receipt-ios-device-autopilot-30aa45c654ed.json"),
        run_checker("check_runtime_receipt.py",
                    "evals/receipts/arm-trials-claude-code-23753e11b417.json"),
        run_checker("check_runtime_receipt.py",
                    "evals/receipts/arm-trials-codex-cli-23753e11b417.json"),
    ]

    highest_reachable = None
    for gate in gates:
        if gate["reachable"]:
            highest_reachable = gate["level"]
        else:
            break

    blocking = [lane["issue"] for lane in lanes if lane["state"] != "PASS"]
    recompute_failed = [item for item in recomputation if item["exit_code"] != 0]

    packet: dict[str, Any] = {
        "schema": "convergence-packet/v1",
        "candidate": {
            "repository": "ed3c/skills-shared",
            "commit": candidate_commit,
            "skill_path": "skills/procedural-shadow-runtime",
            "skill_tree": candidate_tree,
        },
        "rollback": {
            "ref": rollback_ref,
            "commit": rollback_commit,
            "skill_tree": rollback_tree,
            # A rollback that resolves to the candidate is not a rollback, and
            # nothing downstream would notice.
            "distinct_from_candidate": rollback_tree != candidate_tree,
        },
        "lanes": lanes,
        "level_gates": gates,
        "current_admitted_level": "NONE",
        "_why_none": "No prior Human Admit record exists for this candidate. Level skipping is forbidden, so the only proposable level is the first unreached one.",
        "proposed_next_level": LEVELS[0] if highest_reachable is None else (
            LEVELS[LEVELS.index(highest_reachable) + 1] if highest_reachable != "L5" else "L5"),
        "highest_reachable_level": highest_reachable,
        "recomputation": recomputation,
        "security_privacy_licensing": {
            "source_rights_review": "evals/rights-reviews/obra-superpowers-verification-before-completion.json",
            "external_content_treated_as": "UNTRUSTED_INPUT",
            "data_egress": "no repository or user content was sent to an external registry or provider",
            "provider_enrolment": "NONE",
            "privacy_scan": None,
        },
        "known_limitations": [
            "The #219 matrix is PARTIAL at one repetition per arm and its primary metric is saturated on this case set; no causal contrast is available at any confidence.",
            "Production feedback closed on an explicitly admitted canary. No production traffic was observed and no L5 claim follows.",
            "One consumer repository is a consumer canary, not held-out cross-domain transfer.",
            "The device multimodal lane is NOT_EXERCISED; no simulator was authorised.",
            "The consumer binding branch is committed locally and unpushed, so its subject is not independently retrievable.",
        ],
        "excluded_claims": [
            "no claim about model training membership",
            "no claim from private chain-of-thought inspection",
            "no claim that the Skill improved any outcome on any host",
            "no claim of portability beyond the two hosts and one consumer named here",
        ],
        "human_admit": None,
        "terminal_outcome": None,
    }

    packet["security_privacy_licensing"]["privacy_scan"] = privacy_review(
        json.dumps(packet, sort_keys=True).encode()
    )

    reasons: list[str] = []
    if blocking:
        reasons.append(f"lanes not closed: {blocking}")
    if recompute_failed:
        reasons.append(f"recomputation failed: {[item['args'] for item in recompute_failed]}")
    if not packet["rollback"]["distinct_from_candidate"]:
        reasons.append("rollback tree equals candidate tree")
    if packet["security_privacy_licensing"]["privacy_scan"]["result"] != "CLEAN":
        reasons.append("privacy scan found forbidden values")
    if highest_reachable is None:
        reasons.append("no level gate is reachable")

    if reasons:
        packet["terminal_outcome"] = "HOLD_FOR_MORE_EVIDENCE"
        packet["hold_reasons"] = reasons
        return packet

    if admit_record is None:
        packet["terminal_outcome"] = "HOLD_FOR_MORE_EVIDENCE"
        packet["hold_reasons"] = [
            "every machine gate passed; ELIGIBLE_FOR_HUMAN_ADMIT is not a terminal outcome and "
            "no Human Admit record was supplied"
        ]
        return packet

    record = json.loads(admit_record.read_text(encoding="utf-8"))
    for key in ("approver", "decision", "scope", "conditions", "expiry", "admitted_level"):
        if not record.get(key):
            packet["terminal_outcome"] = "HOLD_FOR_MORE_EVIDENCE"
            packet["hold_reasons"] = [f"Human Admit record incomplete: {key} missing"]
            return packet
    if record["decision"] not in TERMINAL_OUTCOMES:
        packet["terminal_outcome"] = "HOLD_FOR_MORE_EVIDENCE"
        packet["hold_reasons"] = [f"unknown decision {record['decision']!r}"]
        return packet
    if record["admitted_level"] != packet["proposed_next_level"]:
        packet["terminal_outcome"] = "HOLD_FOR_MORE_EVIDENCE"
        packet["hold_reasons"] = [
            f"record admits {record['admitted_level']} but the packet proposes "
            f"{packet['proposed_next_level']}; level skipping is forbidden"
        ]
        return packet

    packet["human_admit"] = record
    packet["terminal_outcome"] = record["decision"]
    return packet


def selftest() -> int:
    """The refusals, without touching the real packet."""
    for state in LANE_STATES:
        if not isinstance(state, str):
            return 1

    dirty = privacy_review(
        b'{"path": "/Users/someone/x", "api_key: abcdef", "raw_reasoning": "x", "pan": "4111111111111111"}'
    )
    if dirty["result"] != "FINDINGS_PRESENT" or len(dirty["findings"]) < 4:
        print(f"SELFTEST RED: the privacy scan missed planted values: {dirty}", file=sys.stderr)
        return 1
    clean = privacy_review(
        b'{"path": "<REPO>/skills/x", "contact": "ada@example.invalid",'
        b' "note": "no claim from private chain-of-thought inspection"}'
    )
    if clean["result"] != "CLEAN":
        print(f"SELFTEST RED: the privacy scan flagged clean content: {clean}", file=sys.stderr)
        return 1

    closed = [{"issue": issue, "state": "PASS"} for issue in
              ["#212", "#213", "#214", "#215", "#216", "#217", "#218", "#219"]]
    gates = level_gates(closed, {"qualifies_for_219": True})
    if not gates[0]["reachable"] or not gates[2]["reachable"]:
        print("SELFTEST RED: fully closed lanes did not reach L0-L2", file=sys.stderr)
        return 1
    if gates[3]["reachable"] or gates[5]["reachable"]:
        print("SELFTEST RED: L3 or L5 was reachable without held-out transfer or production",
              file=sys.stderr)
        return 1

    partial = level_gates(closed, {"qualifies_for_219": False})
    if partial[4]["reachable"]:
        print("SELFTEST RED: L4 was reachable from a PARTIAL attribution matrix", file=sys.stderr)
        return 1

    missing_ci = level_gates(
        [{**lane, "state": "ABSENT"} if lane["issue"] == "#212" else lane for lane in closed],
        {"qualifies_for_219": True})
    if missing_ci[1]["reachable"]:
        print("SELFTEST RED: L1 was reachable with no exact-head CI receipt", file=sys.stderr)
        return 1

    if bind_receipt("evals/receipts/definitely-not-here.json")["present"]:
        print("SELFTEST RED: an absent receipt reported present", file=sys.stderr)
        return 1

    print(
        "SELFTEST GREEN: the privacy scan catches planted paths and credentials while passing "
        "reserved-range contact values; L3 and L5 are unreachable on this evidence by "
        "construction; L4 is unreachable from a PARTIAL matrix; L1 is unreachable without an "
        "exact-head CI receipt; an absent receipt never reports present"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--rollback-ref", default="2eab9ddddd782188a46b32a3b829863ebd44d678",
                        help="commit whose skill tree is the rollback bundle")
    parser.add_argument("--human-admit", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if not args.output:
        print("PACKET-INVALID: --output is required unless --selftest", file=sys.stderr)
        return INVALID

    packet = build(args.rollback_ref, args.human_admit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"PACKET {packet['terminal_outcome']} "
          f"proposed={packet['proposed_next_level']} "
          f"highest_reachable={packet['highest_reachable_level']} "
          f"rollback_distinct={packet['rollback']['distinct_from_candidate']} "
          f"privacy={packet['security_privacy_licensing']['privacy_scan']['result']}")
    for lane in packet["lanes"]:
        print(f"  {lane['issue']:<5} {lane['state']:<8} "
              f"{lane['receipts_present']}/{lane['receipts_named']}  {lane['lane']}")
    for reason in packet.get("hold_reasons", []):
        print(f"  HOLD: {reason}")
    return 0 if packet["terminal_outcome"] == "ADMITTED_FOR_BOUND_SCOPE" else NOT_ADMITTED


if __name__ == "__main__":
    raise SystemExit(main())
