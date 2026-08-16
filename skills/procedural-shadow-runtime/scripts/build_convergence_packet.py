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


def has_object(sha: str | None) -> bool:
    """Is this object present in the current checkout at all?

    Every history question in this file has to ask this first. A shallow clone
    is CI's normal shape, and an absent object makes `merge-base` and
    `rev-parse` fail for a reason that has nothing to do with the answer.
    """
    if not sha:
        return False
    return subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{sha}^{{commit}}"],
                          capture_output=True, check=False).returncode == 0


def bind_receipt(relative: str) -> dict[str, Any]:
    """Re-read, re-digest, and read what the receipt itself concluded.

    Presence is not closure. A receipt whose own close_state is FAIL or BLOCKED
    counts against its lane; without this, dropping a red receipt into the
    directory turned its lane green -- which is the exact shape of evidence
    theatre this packet exists to prevent.
    """
    path = SKILL / relative
    if not path.is_file():
        return {"path": relative, "present": False, "sha256": None, "close_state": None}
    payload = path.read_bytes()
    try:
        close_state = json.loads(payload).get("close_state")
    except (json.JSONDecodeError, AttributeError):
        close_state = None
    return {"path": relative, "present": True, "sha256": sha256_bytes(payload),
            # Artefacts that are not runtime receipts have no close_state; that
            # is not a failure, so it is recorded as None rather than as red.
            "close_state": close_state}


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
        red = [item["path"] for item in present
               if item["close_state"] in {"FAIL", "BLOCKED"}]
        if not present:
            state = "ABSENT"
        elif len(present) != len(bound):
            state = "BLOCKED"
        elif red:
            state = "FAIL"
        else:
            state = "PASS"
        lanes.append({**lane, "receipts": bound, "state": state,
                      "receipts_present": len(present), "receipts_named": len(bound),
                      "red_receipts": red})
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


def load_rollback(path: Path) -> dict[str, Any]:
    """Rollback identity is committed data, not something resolved from history.

    Resolving it with `git rev-parse` passed on a full clone and exited 64 on
    CI's shallow checkout: the packet could only ever be green on the machine
    that wrote it. The SHAs are recorded; whether this checkout can resolve them
    is reported as an observation beside them.
    """
    if not path.is_file():
        print(f"PACKET-INVALID absent-rollback-bundle: {path}", file=sys.stderr)
        raise SystemExit(INVALID)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    for key in ("commit", "skill_tree", "tested_rollback_procedure"):
        if not bundle.get(key):
            print(f"PACKET-INVALID rollback-bundle-incomplete: {key}", file=sys.stderr)
            raise SystemExit(INVALID)
    return bundle


def build(rollback_path: Path, admit_record: Path | None) -> dict[str, Any]:
    candidate_commit = git("rev-parse", "HEAD")
    candidate_tree = git("rev-parse", "HEAD:skills/procedural-shadow-runtime")
    bundle = load_rollback(rollback_path)
    rollback_commit = bundle["commit"]
    rollback_tree = bundle["skill_tree"]
    try:
        resolved = git("rev-parse", f"{rollback_commit}:skills/procedural-shadow-runtime")
        resolution_state = "RESOLVED_AND_MATCHES" if resolved == rollback_tree else "RESOLVED_AND_DIFFERS"
    except subprocess.CalledProcessError:
        # A shallow checkout is the normal CI shape. Not resolvable here is a
        # fact about this checkout, not a defect in the bundle.
        resolution_state = "UNRESOLVABLE_IN_THIS_CHECKOUT"

    lanes = evaluate_lanes()

    # A CI receipt can never name the commit that contains it: committing the
    # receipt moves HEAD. What it must not be is unrelated. #212 forbids
    # promoting a stale or parent-head run to exact-head PASS, so the
    # relationship is recorded rather than assumed.
    ci_receipt = RECEIPTS / "github-actions-exact-head.json"
    ci_head = None
    ci_relation = "ABSENT"
    if ci_receipt.is_file():
        ci_head = json.loads(ci_receipt.read_text(encoding="utf-8")).get("subject", {}).get("current_sha")
        if ci_head == candidate_commit:
            ci_relation = "EXACT"
        elif not has_object(ci_head):
            # Third instance of one root cause in this file: a history lookup
            # that is green wherever history is complete. A depth-1 clone does
            # not contain the earlier commit at all, and "cannot resolve" is not
            # "unrelated" -- reading it as unrelated made this check fail in the
            # only environment it was written to run in.
            ci_relation = "UNRESOLVABLE_IN_THIS_CHECKOUT"
        else:
            try:
                git("merge-base", "--is-ancestor", ci_head, candidate_commit)
                ci_relation = "ANCESTOR_OF_CANDIDATE"
            except subprocess.CalledProcessError:
                ci_relation = "UNRELATED_TO_CANDIDATE"
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
            "bundle": str(rollback_path.relative_to(SKILL)) if rollback_path.is_relative_to(SKILL)
                      else rollback_path.name,
            "commit": rollback_commit,
            "skill_tree": rollback_tree,
            "resolution_state": resolution_state,
            "tested_procedure": bundle["tested_rollback_procedure"],
            # Compared as recorded SHAs, so the check holds in a shallow
            # checkout too. A rollback that resolves to the candidate is not a
            # rollback, and nothing downstream would notice.
            "distinct_from_candidate": rollback_tree != candidate_tree,
        },
        "lanes": lanes,
        "level_gates": gates,
        "ci_subject": {"receipt_head": ci_head, "candidate_commit": candidate_commit,
                       "relation": ci_relation},
        "current_admitted_level": "NONE",
        "_why_none": "No prior Human Admit record exists for this candidate.",
        # One level above what is admitted, never one above what is reachable.
        # Promotion advances a single step from the admitted position, so a
        # candidate whose evidence reaches L2 from an admitted NONE still
        # proposes L0. Proposing the top of the reachable range would skip
        # every level under it in one move.
        "proposed_next_level": LEVELS[0],
        "highest_reachable_level": highest_reachable,
        "_why_reachable_is_not_proposed": (
            "highest_reachable_level is what the evidence would support if levels could be "
            "skipped. They cannot. It is reported so the gap between evidence and position is "
            "visible, not so it can be admitted in one step."
        ),
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
    if ci_relation == "UNRELATED_TO_CANDIDATE":
        reasons.append(f"CI receipt head {ci_head} is not an ancestor of the candidate")
    if highest_reachable is None:
        reasons.append("no level gate is reachable")

    if resolution_state == "RESOLVED_AND_DIFFERS":
        reasons.append("recorded rollback tree disagrees with the resolved commit")

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

    # Absence must be distinguishable from disagreement before any history
    # question is asked. Reading "not in this clone" as "unrelated" is what made
    # the CI-subject check fail in the only environment it runs in.
    if has_object("0" * 40) or not has_object(git("rev-parse", "HEAD")) or has_object(None):
        print("SELFTEST RED: object presence is not decided correctly", file=sys.stderr)
        return 1

    # A receipt that closed FAIL must not close its lane merely by existing.
    for lane in evaluate_lanes():
        red = [item for item in lane["receipts"] if item["close_state"] in {"FAIL", "BLOCKED"}]
        if red and lane["state"] == "PASS":
            print(f"SELFTEST RED: {lane['issue']} closed PASS holding {red[0]['close_state']} "
                  f"receipt {red[0]['path']}", file=sys.stderr)
            return 1

    # The shallow-checkout case, which is CI's normal shape and which exited 64
    # here until the rollback identity stopped being resolved from history.
    import tempfile
    bundle = json.loads((SKILL / "evals" / "rollback-bundle.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        unresolvable = Path(tmp) / "rollback.json"
        unresolvable.write_text(json.dumps({**bundle, "commit": "0" * 40}), encoding="utf-8")
        packet = build(unresolvable, None)
        if packet["rollback"]["resolution_state"] != "UNRESOLVABLE_IN_THIS_CHECKOUT":
            print(f"SELFTEST RED: an unresolvable rollback reported "
                  f"{packet['rollback']['resolution_state']}", file=sys.stderr)
            return 1
        if not packet["rollback"]["distinct_from_candidate"]:
            print("SELFTEST RED: distinctness stopped holding without history", file=sys.stderr)
            return 1

        # Anchored on HEAD, which resolves in any checkout. Anchoring the drift
        # control on a historical commit made it silently unreachable in a
        # shallow clone -- the same class of defect this whole change is about,
        # found by running the suite in a depth-1 clone rather than assuming.
        drifted = Path(tmp) / "drifted.json"
        drifted.write_text(json.dumps({**bundle, "commit": git("rev-parse", "HEAD"),
                                       "skill_tree": "1" * 40}), encoding="utf-8")
        packet = build(drifted, None)
        if packet["rollback"]["resolution_state"] != "RESOLVED_AND_DIFFERS":
            print("SELFTEST RED: a recorded tree disagreeing with its commit was not caught",
                  file=sys.stderr)
            return 1
        if "recorded rollback tree disagrees with the resolved commit" not in packet.get("hold_reasons", []):
            print("SELFTEST RED: a drifted rollback record did not hold the packet", file=sys.stderr)
            return 1

        incomplete = Path(tmp) / "incomplete.json"
        incomplete.write_text(json.dumps({"commit": "0" * 40}), encoding="utf-8")
        try:
            build(incomplete, None)
        except SystemExit as exit_code:
            if exit_code.code != 64:
                print(f"SELFTEST RED: an incomplete bundle exited {exit_code.code}", file=sys.stderr)
                return 1
        else:
            print("SELFTEST RED: an incomplete rollback bundle was accepted", file=sys.stderr)
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
    parser.add_argument("--rollback-bundle", type=Path,
                        default=SKILL / "evals" / "rollback-bundle.json",
                        help="committed rollback identity; resolvability is observed, not required")
    parser.add_argument("--human-admit", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if not args.output:
        print("PACKET-INVALID: --output is required unless --selftest", file=sys.stderr)
        return INVALID

    packet = build(args.rollback_bundle, args.human_admit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"PACKET {packet['terminal_outcome']} "
          f"proposed={packet['proposed_next_level']} "
          f"highest_reachable={packet['highest_reachable_level']} "
          f"rollback_distinct={packet['rollback']['distinct_from_candidate']} "
          f"rollback={packet['rollback']['resolution_state']} "
          f"ci_subject={packet['ci_subject']['relation']} "
          f"privacy={packet['security_privacy_licensing']['privacy_scan']['result']}")
    for lane in packet["lanes"]:
        print(f"  {lane['issue']:<5} {lane['state']:<8} "
              f"{lane['receipts_present']}/{lane['receipts_named']}  {lane['lane']}")
    for reason in packet.get("hold_reasons", []):
        print(f"  HOLD: {reason}")
    return 0 if packet["terminal_outcome"] == "ADMITTED_FOR_BOUND_SCOPE" else NOT_ADMITTED


if __name__ == "__main__":
    raise SystemExit(main())
