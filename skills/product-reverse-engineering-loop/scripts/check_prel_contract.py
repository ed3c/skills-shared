#!/usr/bin/env python3
"""Validate one PREL artifact against its schema and the controlled closure laws.

Zero network, standard library plus the pinned Draft 2020-12 validator. The
checker never executes a model, never reaches a product surface, and never
promotes an evidence lane: it decides only whether the bytes in front of it
obey the contracts in `../references/`.

Two layers run, and both always run. The schema layer decides shape. The
semantic layer decides whether the artifact laundered evidence, and it is
written defensively so it still reports its own named refusal code on an
artifact the schema layer has already rejected -- a mutation that flips
`authority.merge` to true must be reported as
`PROMPT_GRANTS_RESERVED_AUTHORITY`, not merely as a schema `const` failure,
because the refusal code is what a Worker is told to look for.

Exits: 0 green, 2 a contract or control is red, 64 the checker could not run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REFERENCES = Path(__file__).resolve().parents[1] / "references"

SCHEMA_FILES = {
    "prel/product-signal/v1": "product-signal.schema.json",
    "prel/reverse-engineering-dossier/v1": "reverse-engineering-dossier.schema.json",
    "prel/problem-closure-matrix/v1": "problem-closure-matrix.schema.json",
    "prel/product-closure-audit/v1": "product-closure-audit.schema.json",
    "prel/prompt-packet/v1": "prompt-packet.schema.json",
    "prel/reverse-engineering-handoff/v1": "reverse-engineering-handoff.schema.json",
    "prel/session-dispatch-request/v1": "session-dispatch-request.schema.json",
    "prel/session-receipt/v1": "session-receipt.schema.json",
    "prel/external-projection-registry/v1": "external-projection-registry.schema.json",
}

# The closure ladder, in order. Two rungs share the IMPLEMENTATION lane because
# code existing and code being verified are different obligations produced by
# different evidence kinds, and collapsing them is how "we wrote it" becomes
# "it works".
CLOSURE_LEVELS = (
    ("SOURCE_ANCHORED", "SOURCE"),
    ("MECHANISM_BOUND", "MECHANISM"),
    ("IMPLEMENTED", "IMPLEMENTATION"),
    ("TECH_VERIFIED", "IMPLEMENTATION"),
    ("LIVE_WORKFLOW_VERIFIED", "RUNTIME"),
    ("USER_VALIDATED", "USER"),
    ("PAID_VALIDATED", "COMMERCIAL"),
)
LEVEL_RANK = {level: index for index, (level, _lane) in enumerate(CLOSURE_LEVELS)}

# Which evidence kinds may close each level. The kind decides, not the prose
# around it: a CI run is admissible where a suite is asked for and inadmissible
# everywhere above, which is the whole of "green CI is not a live, user or paid
# outcome". MODEL_JUDGMENT is admissible nowhere.
ADMISSIBLE_KINDS = {
    "SOURCE_ANCHORED": {"SOURCE_DOCUMENT", "ISSUE_RECORD"},
    "MECHANISM_BOUND": {"MECHANISM_OBSERVATION"},
    "IMPLEMENTED": {"CODE_SUBJECT"},
    "TECH_VERIFIED": {"DETERMINISTIC_SUITE", "CI_RUN"},
    "LIVE_WORKFLOW_VERIFIED": {"LIVE_WORKFLOW_RUN"},
    "USER_VALIDATED": {"USER_REPORT"},
    "PAID_VALIDATED": {"PAID_CONVERSION", "HUMAN_ADMISSION"},
}

# States that mean an oracle exists and nobody ran it. These are the obligations
# a first green silently inherits as closed unless they are reopened by name.
SKIPPED_STATES = {"NOT_EXERCISED", "NOT_IMPLEMENTED", "SKIPPED_BY_POLICY"}

PROMPT_SURFACES = (
    "STAGE_1_CONTROL_BINDER",
    "STAGE_2_SOURCE_INTAKE",
    "STAGE_3_EVIDENCE_COMPILER",
    "STAGE_4_YC_PRODUCT_REVERSE_ENGINEER",
    "STAGE_5_TECHNICAL_SYSTEMS_ARCHITECT",
    "STAGE_6_SHADOW_MONITOR",
    "STAGE_7_TECH_LEAD_PLANNER",
    "STAGE_8_MOLECULAR_WORKER",
    "STAGE_9_CONVERGENCE_OWNER",
)
ENVELOPE_ID = "COMMON_SYSTEM_ENVELOPE"

# Kinds that assert somebody watched the product do something. Everything else
# is a claim about the product, and the difference is the whole point of the
# intake stage.
OBSERVED_KINDS = {"OBSERVED_ARTIFACT", "PAID_CONVERSION"}
CLAIM_KINDS = {"SOURCE_STATEMENT", "MARKET_ATTENTION", "INFERENCE"}
TECHNICAL_LANES = {"DETERMINISTIC", "BEHAVIORAL"}
DEMAND_SLOTS = {"JOB", "PAIN"}

PLACEHOLDERS = {"", "-", "?", "n/a", "na", "tbd", "todo", "none", "unknown", "xxx"}

PRIVATE_REASONING = re.compile(
    r"chain[- ]of[- ]thought|private reasoning|inner monologue|hidden reasoning"
    r"|reasoning trace|think privately",
    re.IGNORECASE,
)
CONSUMER_TOPOLOGY = re.compile(
    r"/Users/|/home/|refs/heads/|origin/|github\.com|gitlab\.com|\.git\b|#\d+",
)
PRIOR_CHAT = re.compile(
    r"prior chat|previous chat|conversation|as discussed|earlier message|transcript",
    re.IGNORECASE,
)


class Unusable(Exception):
    """The checker could not read its input. Not the same as a refusal."""


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Unusable(f"unreadable artifact {path}: {error}") from error


def digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise Unusable(f"unreadable input {path}: {error}") from error


def schema_errors(artifact: Any, schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as error:  # pragma: no cover - environment guard
        raise Unusable("jsonschema Draft 2020-12 validator unavailable") from error
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, Exception) as error:  # noqa: BLE001
        raise Unusable(f"invalid or unreadable schema {schema_path}: {error}") from error
    found = sorted(
        Draft202012Validator(schema).iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )
    return [
        "SCHEMA_SHAPE "
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in found[:20]
    ]


def walk_strings(value: Any, path: str = "") -> list[tuple[str, str]]:
    """Every string leaf with the dotted path it was found at."""
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, dict):
        found: list[tuple[str, str]] = []
        for key, child in value.items():
            found.extend(walk_strings(child, f"{path}.{key}" if path else str(key)))
        return found
    if isinstance(value, list):
        found = []
        for index, child in enumerate(value):
            found.extend(walk_strings(child, f"{path}[{index}]"))
        return found
    return []


def hollow(value: Any) -> bool:
    return isinstance(value, str) and value.strip().casefold() in PLACEHOLDERS


def check_hollow(artifact: Any) -> list[str]:
    return [
        f"HOLLOW_EVIDENCE {path or '<root>'} is a placeholder, not evidence: {text!r}"
        for path, text in walk_strings(artifact)
        if hollow(text)
    ]


def signal_properties() -> set[str]:
    schema = load(REFERENCES / "product-signal.schema.json")
    return set(schema["$defs"]["signal"]["properties"])


def check_product_signal(artifact: dict) -> list[str]:
    problems: list[str] = []
    declared = signal_properties()
    compatibility = artifact.get("compatibility") or {}
    for field in compatibility.get("consumed_fields") or []:
        if field not in declared:
            problems.append(
                f"COMPATIBILITY_FIELD_UNKNOWN consumed_fields names {field!r}, which "
                f"this contract does not define; the producer binding has drifted"
            )

    signals = artifact.get("signals") or []
    known = {row.get("id") for row in signals if isinstance(row, dict)}
    for row in signals:
        if not isinstance(row, dict):
            continue
        identifier = row.get("id", "<unnamed>")
        kind, slot = row.get("kind"), row.get("slot")
        if kind in CLAIM_KINDS and row.get("observation") is not None:
            problems.append(
                f"SOURCE_STATEMENT_AS_OBSERVED_ARCHITECTURE {identifier}: kind {kind} "
                f"carries an observation block; a statement about the product is not "
                f"an observation of it"
            )
        if kind in OBSERVED_KINDS and row.get("observation") is None:
            problems.append(
                f"HOLLOW_EVIDENCE {identifier}: kind {kind} claims observation and "
                f"carries none"
            )
        if kind == "MARKET_ATTENTION" and slot in DEMAND_SLOTS:
            problems.append(
                f"MARKET_ATTENTION_AS_DEMAND {identifier}: attention was filed under "
                f"slot {slot}; attention is not a job and not a pain"
            )
        if slot == "MECHANISM" and kind in OBSERVED_KINDS and row.get("oracle") is None:
            problems.append(
                f"MECHANISM_WITHOUT_OBSERVABLE_ORACLE {identifier}: an observed "
                f"mechanism with no oracle cannot be refuted by anything"
            )
        for dependency in row.get("depends_on") or []:
            if dependency not in known:
                problems.append(
                    f"SIGNAL_DEPENDENCY_UNBOUND {identifier}: depends_on names "
                    f"{dependency}, which is not in this signal set"
                )
    return problems


def check_ceiling(ceiling: Any, where: str) -> list[str]:
    problems: list[str] = []
    if not isinstance(ceiling, dict):
        return problems
    for field in ("product_market_fit", "live_provider_execution", "production_readiness"):
        if ceiling.get(field) == "PASS":
            problems.append(
                f"CEILING_OVERCLAIM {where}.{field} is PASS; this lane is not "
                f"produced by any deterministic artifact"
            )
    return problems


def check_dossier(artifact: dict) -> list[str]:
    problems: list[str] = []
    job = artifact.get("job") or {}
    pain = artifact.get("pain") or {}
    workflow = artifact.get("workflow") or []
    mechanisms = artifact.get("mechanism_hypotheses") or []

    if (workflow or mechanisms) and (
        job.get("grade") == "ABSENT" or pain.get("grade") == "ABSENT"
    ):
        problems.append(
            "FEATURE_CLONE_WITHOUT_JOB_HYPOTHESIS the dossier carries workflow or "
            "mechanism content while job or pain is ABSENT; that is a feature list, "
            "not a product hypothesis"
        )

    for slot_name in ("job", "pain", "magic_moment"):
        slot = artifact.get(slot_name) or {}
        grade, ids = slot.get("grade"), slot.get("signal_ids") or []
        if grade not in (None, "ABSENT") and not ids:
            problems.append(
                f"UNGRADED_SLOT {slot_name} is graded {grade} and cites no signal"
            )
        if grade == "ABSENT" and (slot.get("statement") or "").strip():
            problems.append(
                f"UNGRADED_SLOT {slot_name} is ABSENT and still carries a statement"
            )

    for row in mechanisms:
        if not isinstance(row, dict):
            continue
        identifier = row.get("id", "<unnamed>")
        classification = row.get("classification")
        if classification == "OBSERVABLE_MECHANISM" and not row.get("oracle_id"):
            problems.append(
                f"MECHANISM_WITHOUT_OBSERVABLE_ORACLE {identifier} is classified "
                f"OBSERVABLE_MECHANISM with no oracle"
            )
        if classification == "VENDOR_CLAIMED_MECHANISM" and row.get("grade") != "CLAIMED":
            problems.append(
                f"SOURCE_STATEMENT_AS_OBSERVED_ARCHITECTURE {identifier} is a vendor "
                f"claim graded {row.get('grade')!r}"
            )

    graph = artifact.get("capability_graph") or {}
    nodes = {row.get("id") for row in graph.get("nodes") or [] if isinstance(row, dict)}
    for edge in graph.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        for end in ("from", "to"):
            if edge.get(end) not in nodes:
                problems.append(
                    f"CAPABILITY_EDGE_UNBOUND edge {end}={edge.get(end)!r} names no "
                    f"declared capability node"
                )

    for right in artifact.get("rights") or []:
        if isinstance(right, dict) and right.get("state") == "PASS":
            problems.append(
                f"CEILING_OVERCLAIM rights {right.get('id')} is PASS; a usage right "
                f"is admitted by a Human, never by a compiler"
            )

    problems.extend(check_ceiling(artifact.get("evidence_ceiling"), "evidence_ceiling"))
    return problems


def check_closure_matrix(artifact: dict) -> list[str]:
    problems: list[str] = []
    for row in artifact.get("rows") or []:
        if not isinstance(row, dict):
            continue
        identifier = row.get("id", "<unnamed>")
        lane, oracle_lane = row.get("lane"), row.get("oracle_lane")
        oracle_id, state = row.get("oracle_id"), row.get("closure_state")

        if lane in {"USER", "PAID"} and oracle_lane in TECHNICAL_LANES:
            if state == "CLOSED_BY_ORACLE" or row.get("evidence_state") == "PASS":
                problems.append(
                    f"TECHNICAL_PASS_AS_USER_VALIDATION {identifier}: a "
                    f"{oracle_lane} oracle was used to close a {lane} requirement"
                )
        if oracle_id is None and state in {"CLOSED_BY_ORACLE", "OPEN_WITH_ORACLE"}:
            problems.append(
                f"CLOSURE_STATE_UNSUPPORTED {identifier} claims {state} with no oracle"
            )
        if oracle_id is not None and oracle_lane is None:
            problems.append(
                f"CLOSURE_STATE_UNSUPPORTED {identifier} names an oracle with no lane"
            )
        if (
            oracle_lane is not None
            and lane != oracle_lane
            and state != "BLOCKED_LANE_MISMATCH"
        ):
            problems.append(
                f"CLOSURE_STATE_UNSUPPORTED {identifier}: lane {lane} closed by a "
                f"{oracle_lane} oracle without BLOCKED_LANE_MISMATCH"
            )
        if state == "BLOCKED_NO_ORACLE" and row.get("evidence_state") == "PASS":
            problems.append(
                f"CLOSURE_STATE_UNSUPPORTED {identifier} is blocked and PASS at once"
            )
    problems.extend(check_ceiling(artifact.get("evidence_ceiling"), "evidence_ceiling"))
    return problems


def audit_rung_problems(problem: dict, states: dict[str, str]) -> list[str]:
    """Per-rung controls: the level set, its anchors, and what they may close."""
    problems: list[str] = []
    identifier = problem.get("id", "<unnamed>")
    rungs = [row for row in problem.get("levels") or [] if isinstance(row, dict)]

    observed = tuple((row.get("level"), row.get("lane")) for row in rungs)
    if observed != CLOSURE_LEVELS:
        problems.append(
            f"AUDIT_LEVEL_SET_DRIFT {identifier}: levels must be exactly "
            f"{[list(pair) for pair in CLOSURE_LEVELS]} in order; found "
            f"{[list(pair) for pair in observed]}"
        )

    for row in rungs:
        level, state = row.get("level"), row.get("state")
        anchors = [item for item in row.get("anchors") or [] if isinstance(item, dict)]
        if state != "PASS":
            continue
        kinds = [item.get("kind") for item in anchors]
        if "MODEL_JUDGMENT" in kinds:
            problems.append(
                f"MODEL_JUDGE_OVERRIDE {identifier}.{level} is PASS on a model "
                f"judgement; a judge may describe evidence and may not be the "
                f"evidence"
            )
            continue
        if not anchors:
            problems.append(
                f"EVIDENCE_LANE_PROMOTION {identifier}.{level} is PASS with no "
                f"anchor; a state with no subject closes nothing"
            )
            continue
        admissible = ADMISSIBLE_KINDS.get(level, set())
        for kind in kinds:
            if kind not in admissible:
                problems.append(
                    f"EVIDENCE_LANE_PROMOTION {identifier}.{level} is closed by a "
                    f"{kind} anchor; that level admits {sorted(admissible)}"
                )
    # The ladder is recomputed, never read. A writer states the level and the
    # checker decides whether the states underneath it support the claim.
    prefix = 0
    for level, _lane in CLOSURE_LEVELS:
        if states.get(level) == "PASS":
            prefix += 1
        else:
            break
    if "FAIL" in states.values():
        expected = "FAILED"
    elif prefix:
        expected = CLOSURE_LEVELS[prefix - 1][0]
    else:
        expected = "BLOCKED"
    declared = problem.get("highest_earned_level")
    if declared != expected:
        problems.append(
            f"LEVEL_LADDER_SKIP {identifier} declares {declared!r}; the level "
            f"states earn {expected!r}"
        )

    expected_missing = sorted(
        {lane for level, lane in CLOSURE_LEVELS if states.get(level) != "PASS"}
    )
    if sorted(problem.get("missing_lanes") or []) != expected_missing:
        problems.append(
            f"MISSING_LANE_UNDECLARED {identifier} declares missing lanes "
            f"{sorted(problem.get('missing_lanes') or [])}; the level states "
            f"leave {expected_missing} open"
        )
    return problems


def check_closure_audit(artifact: dict) -> list[str]:
    """Controls for the read-only Shadow closure audit.

    Every control here answers one question: did this audit report what the
    subject's own bytes support, or did it inherit a conclusion from somewhere
    cheaper? Nothing in this function reaches a product, runs an oracle or
    promotes a lane; it decides only whether the artifact's states are carried
    by the anchors the artifact itself names.
    """
    problems: list[str] = []

    reviewer = artifact.get("reviewer") or {}
    if reviewer.get("writes_implementation") is not False:
        problems.append(
            "SHADOW_WRITE_AUTHORITY reviewer.writes_implementation is not false; "
            "a monitor that edits the thing it audits has no independent lane"
        )
    if reviewer.get("mode") != "READ_ONLY_FINDINGS_ONLY":
        problems.append(
            f"SHADOW_WRITE_AUTHORITY reviewer.mode is {reviewer.get('mode')!r}; the "
            f"only mode this contract defines is READ_ONLY_FINDINGS_ONLY"
        )

    authority = artifact.get("external_authority") or {}
    for decision, value in authority.items():
        if value != "HUMAN_ADMIT_REQUIRED":
            problems.append(
                f"MERGE_OR_RELEASE_AUTHORITY_ASSUMED external_authority.{decision} "
                f"is {value!r}; this audit decides none of these"
            )

    snapshot = artifact.get("public_snapshot") or {}
    if snapshot.get("completion_meaning") != "REVIEW_ONLY_NOT_MERGE_OR_RELEASE":
        problems.append(
            "MERGE_OR_RELEASE_AUTHORITY_ASSUMED public_snapshot.completion_meaning "
            "does not state that a completed review is neither a merge nor a release"
        )
    if snapshot.get("contains_private_reasoning") is not False:
        problems.append(
            "PRIVATE_REASONING_IN_PUBLIC_SNAPSHOT the snapshot does not declare "
            "contains_private_reasoning=false"
        )
    if snapshot.get("consumable_without_prior_conversation") is not True:
        problems.append(
            "SNAPSHOT_REQUIRES_PRIOR_CONVERSATION the snapshot does not declare "
            "itself consumable with no prior context"
        )

    for path, text in walk_strings(artifact):
        if PRIVATE_REASONING.search(text):
            problems.append(
                f"PRIVATE_REASONING_IN_PUBLIC_SNAPSHOT {path} publishes or requests "
                f"hidden reasoning: {text!r}"
            )
        if PRIOR_CHAT.search(text):
            problems.append(
                f"SNAPSHOT_REQUIRES_PRIOR_CONVERSATION {path} points a reader at "
                f"context that is not in this packet: {text!r}"
            )

    audited = [row for row in artifact.get("problems") or [] if isinstance(row, dict)]
    reopened = {
        (row.get("problem_id"), row.get("level"))
        for row in artifact.get("reopened_obligations") or []
        if isinstance(row, dict)
    }
    reported = 0

    for problem in audited:
        identifier = problem.get("id", "<unnamed>")
        rungs = [row for row in problem.get("levels") or [] if isinstance(row, dict)]
        states = {row.get("level"): row.get("state") for row in rungs}
        problems.extend(audit_rung_problems(problem, states))

        findings = [row for row in problem.get("findings") or [] if isinstance(row, dict)]
        reported += len(findings)
        for finding in findings:
            if finding.get("authority") != "FINDINGS_ONLY":
                problems.append(
                    f"SHADOW_WRITE_AUTHORITY {identifier}/{finding.get('id')} claims "
                    f"authority {finding.get('authority')!r}"
                )
            anchors = [row for row in finding.get("anchors") or [] if isinstance(row, dict)]
            if not anchors:
                problems.append(
                    f"UNANCHORED_FINDING {identifier}/{finding.get('id')} names no "
                    f"exact subject; an unanchored finding cannot be checked or repaired"
                )
            for anchor in anchors:
                subject = anchor.get("exact_subject") or {}
                if not subject.get("artifact") or not subject.get("digest"):
                    problems.append(
                        f"UNANCHORED_FINDING {identifier}/{finding.get('id')} carries "
                        f"an anchor with no exact subject binding"
                    )

        # A subject that claims more than it earned is only reported honestly if
        # the audit says so out loud; otherwise the audit absorbed the claim.
        claimed = problem.get("declared_status", {}).get("claimed_level")
        earned = problem.get("highest_earned_level")
        if LEVEL_RANK.get(claimed, -1) > LEVEL_RANK.get(earned, -1) and not any(
            row.get("code") == "DECLARED_STATUS_AHEAD_OF_EVIDENCE" for row in findings
        ):
            problems.append(
                f"CONTRADICTORY_CLOSURE_STATUS {identifier} is declared {claimed!r} "
                f"and earns {earned!r} with no DECLARED_STATUS_AHEAD_OF_EVIDENCE "
                f"finding"
            )

        for row in rungs:
            if row.get("state") in SKIPPED_STATES and (
                identifier,
                row.get("level"),
            ) not in reopened:
                problems.append(
                    f"FIRST_GREEN_OBLIGATION_SKIPPED {identifier}.{row.get('level')} "
                    f"is {row.get('state')} and is not reopened; a green elsewhere "
                    f"would inherit it as closed"
                )

    known_rungs = {
        (problem.get("id"), row.get("level"), row.get("state"))
        for problem in audited
        for row in problem.get("levels") or []
        if isinstance(row, dict)
    }
    for key in sorted(reopened, key=lambda pair: (str(pair[0]), str(pair[1]))):
        states = {state for identity, level, state in known_rungs if (identity, level) == key}
        if not states:
            problems.append(
                f"FIRST_GREEN_OBLIGATION_SKIPPED reopened obligation {key} names no "
                f"rung in this audit"
            )
        elif states == {"PASS"}:
            problems.append(
                f"FIRST_GREEN_OBLIGATION_SKIPPED reopened obligation {key} names a "
                f"rung that is PASS; reopening a closed lane hides which one is open"
            )

    denominator = artifact.get("review_denominator") or {}
    withdrawn = [row for row in denominator.get("findings_withdrawn") or [] if isinstance(row, dict)]
    if denominator.get("findings_reported") != reported:
        problems.append(
            f"DISSENT_OMITTED_FROM_DENOMINATOR review_denominator.findings_reported "
            f"is {denominator.get('findings_reported')!r} and {reported} findings "
            f"are carried by the problems"
        )
    if denominator.get("findings_raised") != reported + len(withdrawn):
        problems.append(
            f"DISSENT_OMITTED_FROM_DENOMINATOR {denominator.get('findings_raised')!r} "
            f"findings were raised, {reported} are reported and {len(withdrawn)} are "
            f"withdrawn with a reason; the difference left no record"
        )

    known_problems = {problem.get("id") for problem in audited}
    for item in artifact.get("issue_delta") or []:
        if not isinstance(item, dict):
            continue
        if item.get("write_authority") != "NO_WRITE_AUTHORITY":
            problems.append(
                f"SHADOW_WRITE_AUTHORITY issue delta {item.get('id')} claims write "
                f"authority {item.get('write_authority')!r}; this output is a proposal"
            )
        if item.get("problem_id") not in known_problems:
            problems.append(
                f"UNANCHORED_FINDING issue delta {item.get('id')} names problem "
                f"{item.get('problem_id')!r}, which this audit does not carry"
            )

    problems.extend(check_ceiling(artifact.get("evidence_ceiling"), "evidence_ceiling"))
    return problems


def check_handoff(artifact: dict) -> list[str]:
    problems: list[str] = []
    packets = [row for row in artifact.get("packets") or [] if isinstance(row, dict)]
    leases = {row.get("id"): list(row.get("paths_lease") or []) for row in packets}

    for path, text in walk_strings(artifact):
        if PRIOR_CHAT.search(text):
            problems.append(
                f"PRIOR_CHAT_PROSE_AS_HANDOFF {path} points at conversation prose "
                f"instead of a digest-bound artifact: {text!r}"
            )

    identifiers = sorted(leases)
    for index, left in enumerate(identifiers):
        for right in identifiers[index + 1:]:
            for one in leases[left]:
                for other in leases[right]:
                    if one.startswith(other) or other.startswith(one):
                        problems.append(
                            f"HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE {left} and "
                            f"{right} both hold {one!r}/{other!r}"
                        )

    for packet in packets:
        identifier = packet.get("id", "<unnamed>")
        edges = packet.get("depends_on") or []
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            parent = edge.get("packet_id")
            if parent not in leases:
                problems.append(
                    f"HANDOFF_EDGE_UNBOUND {identifier} depends on {parent}, which is "
                    f"not a packet here"
                )
                continue
            for consumed in edge.get("consumes") or []:
                if not any(consumed.startswith(lease) for lease in leases[parent]):
                    problems.append(
                        f"FALSE_SERIALIZATION_OF_INDEPENDENT_LEAVES {identifier} "
                        f"depends on {parent} but consumes {consumed!r}, which "
                        f"{parent} does not produce"
                    )
        owner = packet.get("convergence_owner")
        if len(edges) > 1 and not owner:
            problems.append(
                f"HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE {identifier} has "
                f"{len(edges)} incoming contracts and no convergence owner"
            )
        if len(edges) <= 1 and owner:
            problems.append(
                f"HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE {identifier} declares a "
                f"convergence owner without being a convergence"
            )

    order: dict[str, int] = {}

    def visit(identifier: str, seen: tuple[str, ...]) -> None:
        if identifier in order:
            return
        if identifier in seen:
            problems.append(
                f"HANDOFF_CYCLE {' -> '.join(seen + (identifier,))}"
            )
            order[identifier] = 0
            return
        packet = next((row for row in packets if row.get("id") == identifier), None)
        for edge in (packet or {}).get("depends_on") or []:
            if isinstance(edge, dict) and edge.get("packet_id") in leases:
                visit(edge["packet_id"], seen + (identifier,))
        order[identifier] = len(order)

    for identifier in identifiers:
        visit(identifier, ())

    for item in artifact.get("remaining") or []:
        if isinstance(item, dict) and item.get("state") == "PASS":
            problems.append(
                f"CEILING_OVERCLAIM remaining item {item.get('closure_row_id')} is "
                f"PASS; a remaining item is by definition not closed"
            )
    return problems


def check_prompt_packet(artifact: dict) -> list[str]:
    problems: list[str] = []
    envelope = artifact.get("envelope") or {}
    surfaces = [row for row in artifact.get("surfaces") or [] if isinstance(row, dict)]

    observed = tuple(row.get("id") for row in surfaces)
    if observed != PROMPT_SURFACES:
        problems.append(
            "PROMPT_SURFACE_SET_DRIFT surfaces must be exactly "
            f"{list(PROMPT_SURFACES)} in order; found {list(observed)}"
        )

    for holder, label in [(envelope, ENVELOPE_ID)] + [
        (row, row.get("id", "<unnamed>")) for row in surfaces
    ]:
        authority = holder.get("authority") or {}
        granted = sorted(key for key, value in authority.items() if value)
        if granted:
            problems.append(
                f"PROMPT_GRANTS_RESERVED_AUTHORITY {label} grants {granted}; these "
                f"operations are Human-owned and a prompt cannot hand them out"
            )
        if holder.get("requests_private_reasoning") is not False:
            problems.append(
                f"PROMPT_REQUESTS_PRIVATE_REASONING {label} does not declare "
                f"requests_private_reasoning=false"
            )
        if not (holder.get("human_owned_operations") or []):
            problems.append(
                f"PROMPT_GRANTS_RESERVED_AUTHORITY {label} names no Human-owned "
                f"operation, so nothing is reserved"
            )

    for path, text in walk_strings(artifact):
        if PRIVATE_REASONING.search(text):
            problems.append(
                f"PROMPT_REQUESTS_PRIVATE_REASONING {path} asks for hidden reasoning: "
                f"{text!r}"
            )
        if ".consumer_binding." in f".{path}.":
            continue
        if CONSUMER_TOPOLOGY.search(text):
            problems.append(
                f"CONSUMER_TOPOLOGY_IN_PORTABLE_CORE {path} carries a consumer "
                f"branch, issue, remote or machine path outside consumer_binding: "
                f"{text!r}"
            )

    declared = set(observed) | {ENVELOPE_ID}
    for row in surfaces:
        identifier = row.get("id", "<unnamed>")
        for field in ("start_dependencies", "completion_dependencies"):
            for dependency in row.get(field) or []:
                if dependency not in declared:
                    problems.append(
                        f"PROMPT_DEPENDENCY_UNBOUND {identifier}.{field} names "
                        f"{dependency!r}, which is not a surface in this packet"
                    )

    leases = {row.get("id"): list(row.get("lease") or []) for row in surfaces}
    identifiers = sorted(leases)
    for index, left in enumerate(identifiers):
        for right in identifiers[index + 1:]:
            overlap = sorted(set(leases[left]) & set(leases[right]))
            if overlap:
                problems.append(
                    f"HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE {left} and {right} "
                    f"share the writer lease {overlap}"
                )
    return problems


def check_session_dispatch(artifact: dict) -> list[str]:
    """C06/C07/C13 controls the schema's per-field `const`s cannot see.

    A `const` catches one field lying about itself; it cannot catch two
    requests that are each individually well-formed but jointly claim the
    same writer lease, or a CHILD whose declared parent does not exist among
    the requests it was dispatched beside.
    """
    problems: list[str] = []
    requests = [row for row in artifact.get("requests") or [] if isinstance(row, dict)]

    leases: dict[str, tuple[list[str], list[str]]] = {}
    for row in requests:
        identifier = row.get("id")
        if not identifier:
            continue
        lease = row.get("lease") or {}
        leases[identifier] = (
            list(lease.get("paths") or []),
            list(lease.get("resources") or []),
        )

    identifiers = sorted(leases)
    for index, left in enumerate(identifiers):
        for right in identifiers[index + 1:]:
            left_paths, left_resources = leases[left]
            right_paths, right_resources = leases[right]
            for one in left_paths:
                for other in right_paths:
                    if one == other or one.startswith(other) or other.startswith(one):
                        problems.append(
                            f"C06_OVERLAPPING_WRITER_LEASE {left} and {right} both "
                            f"hold path {one!r}/{other!r}"
                        )
            shared = sorted(set(left_resources) & set(right_resources))
            if shared:
                problems.append(
                    f"C06_OVERLAPPING_WRITER_LEASE {left} and {right} share "
                    f"resource {shared}"
                )

    for row in requests:
        identifier = row.get("id", "<unnamed>")
        relation = row.get("relation")
        parent = row.get("parent_request_id")
        if relation == "CHILD":
            if not parent:
                problems.append(
                    f"C07_HIDDEN_MULTI_PARENT_CONVERGENCE {identifier} is CHILD "
                    f"with no parent_request_id"
                )
            elif parent == identifier:
                problems.append(
                    f"C07_HIDDEN_MULTI_PARENT_CONVERGENCE {identifier} names "
                    f"itself as its own parent"
                )
        if relation == "SIBLING" and parent is not None:
            problems.append(
                f"C07_HIDDEN_MULTI_PARENT_CONVERGENCE {identifier} is SIBLING "
                f"but names parent {parent!r}"
            )
        rollback = row.get("rollback") or {}
        base = row.get("base") or {}
        if not rollback.get("commit"):
            problems.append(
                f"C13_ROLLBACK_SUBJECT_ABSENT_OR_EQUAL_TO_MUTABLE_ALIAS "
                f"{identifier} names no rollback commit"
            )
        if rollback.get("commit") and base.get("tree") and rollback.get("commit") == base.get("tree"):
            problems.append(
                f"C13_ROLLBACK_SUBJECT_ABSENT_OR_EQUAL_TO_MUTABLE_ALIAS "
                f"{identifier} rollback commit equals the base tree object, not "
                f"an exact commit to return to"
            )
    return problems


def check_session_receipt(artifact: dict) -> list[str]:
    problems: list[str] = []
    lifecycle = artifact.get("lifecycle") or {}
    order = (
        "LAUNCH_REQUESTED",
        "SESSION_OBSERVED",
        "RUNNING",
        "RESULT_RECEIVED",
        "ARTIFACTS_READ_BACK",
    )
    for level in order:
        observation = lifecycle.get(level) or {}
        if observation.get("state") == "PASS" and not observation.get("evidence_ref"):
            problems.append(
                f"C05_MISSING_EXACT_RECEIPT {level} is PASS with no evidence_ref"
            )
    prefix = {level: (lifecycle.get(level) or {}).get("state") for level in order}
    if prefix["RUNNING"] == "PASS" and prefix["SESSION_OBSERVED"] != "PASS":
        problems.append(
            "C09_SESSION_REQUEST_PROMOTED_TO_RUNNING RUNNING is PASS while "
            "SESSION_OBSERVED is not"
        )
    if prefix["RESULT_RECEIVED"] == "PASS" and prefix["RUNNING"] != "PASS":
        problems.append(
            "C09_SESSION_REQUEST_PROMOTED_TO_RUNNING RESULT_RECEIVED is PASS "
            "while RUNNING is not"
        )
    return problems


def check_external_projection(artifact: dict) -> list[str]:
    problems: list[str] = []
    for entry in artifact.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        identifier = entry.get("id", "<unnamed>")
        read_back = entry.get("read_back") or {}
        if (
            read_back.get("state") == "PASS"
            and read_back.get("compared_digest") != entry.get("export_digest")
        ):
            problems.append(
                f"C08_PROJECTION_USED_AS_MACHINE_AUTHORITY {identifier} read_back "
                f"is PASS but compared_digest does not match the observed "
                f"export_digest"
            )
        for subject in entry.get("canonical_subjects") or []:
            if not isinstance(subject, dict):
                continue
            commit = subject.get("commit")
            if commit in (None, "main", "HEAD", "latest") or not re.fullmatch(
                r"[0-9a-f]{40}", commit or ""
            ):
                problems.append(
                    f"C01_MUTABLE_SUBJECT {identifier} names a canonical subject "
                    f"whose commit is not an exact object: {commit!r}"
                )
    return problems


SEMANTIC = {
    "prel/product-signal/v1": check_product_signal,
    "prel/reverse-engineering-dossier/v1": check_dossier,
    "prel/problem-closure-matrix/v1": check_closure_matrix,
    "prel/product-closure-audit/v1": check_closure_audit,
    "prel/reverse-engineering-handoff/v1": check_handoff,
    "prel/prompt-packet/v1": check_prompt_packet,
    "prel/session-dispatch-request/v1": check_session_dispatch,
    "prel/session-receipt/v1": check_session_receipt,
    "prel/external-projection-registry/v1": check_external_projection,
}


def check_stale_subject(artifact: dict, source: Path) -> list[str]:
    declared = (artifact.get("derived_from") or {}).get("digest")
    actual = digest(source)
    if declared != actual:
        return [
            f"STALE_SUBJECT derived_from.digest is {declared!r} while {source.name} "
            f"currently hashes to {actual!r}; the artifact describes a subject that "
            f"has moved"
        ]
    return []


def walk_subjects(value: Any, path: str = "") -> list[tuple[str, dict]]:
    """Every `exact_subject` / `derived_from` binding, wherever it is nested."""
    found: list[tuple[str, dict]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}.{key}" if path else str(key)
            if key in {"exact_subject", "derived_from"} and isinstance(child, dict):
                found.append((here, child))
            else:
                found.extend(walk_subjects(child, here))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(walk_subjects(child, f"{path}[{index}]"))
    return found


def check_resolved_subjects(artifact: Any, roots: list[Path]) -> list[str]:
    """Every named subject must still exist and still hash to what was recorded.

    Without this, a digest is only a promise the artifact makes about a file
    nobody re-reads: the file moves, the packet keeps pointing at a subject that
    no longer exists, and every downstream state stays green describing bytes
    that are gone.

    More than one root may be given, because an audit's subjects genuinely live
    in different trees -- a README in the audited checkout, a captured issue
    snapshot beside the receipt. A subject resolves when some root holds a file
    of that name whose bytes hash to the recorded digest; a name that exists in
    a root with different bytes reports that root's digest, which is the useful
    half of the message.
    """
    problems: list[str] = []
    for where, binding in walk_subjects(artifact):
        name = binding.get("artifact")
        if not isinstance(name, str) or not name:
            continue
        found = [root / name for root in roots if (root / name).is_file()]
        if not found:
            problems.append(
                f"STALE_SUBJECT {where} names {name!r}, which is in none of "
                f"{[str(root) for root in roots]}"
            )
            continue
        actual = [digest(target) for target in found]
        if binding.get("digest") not in actual:
            problems.append(
                f"STALE_SUBJECT {where} records {binding.get('digest')!r} for "
                f"{name!r}, which currently hashes to {actual[0]!r}"
            )
    return problems


def check_catalogue(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise Unusable(f"unreadable catalogue {path}: {error}") from error
    return [
        f"PROMPT_SURFACE_SET_DRIFT catalogue {path.name} does not name {name}"
        for name in (ENVELOPE_ID,) + PROMPT_SURFACES
        if name not in text
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument(
        "--input",
        type=Path,
        help="the upstream artifact this one was compiled from; enables the "
        "stale-subject control",
    )
    parser.add_argument("--catalogue", type=Path)
    parser.add_argument(
        "--resolve-subjects",
        type=Path,
        action="append",
        help="directory the artifact's exact_subject/derived_from names resolve "
        "against; enables the stale-subject control on every binding. Repeat it "
        "when the audited subjects live in more than one tree",
    )
    args = parser.parse_args()

    if args.artifact is None and args.catalogue is None:
        print("PREL-RED usage: --artifact and/or --catalogue is required", file=sys.stderr)
        return 64

    try:
        problems: list[str] = []
        subject = "catalogue"
        if args.catalogue is not None:
            problems.extend(check_catalogue(args.catalogue))
        if args.artifact is not None:
            artifact = load(args.artifact)
            if not isinstance(artifact, dict):
                raise Unusable("artifact root must be an object")
            schema_name = artifact.get("schema")
            if schema_name not in SCHEMA_FILES:
                raise Unusable(
                    f"unknown artifact schema {schema_name!r}; known: "
                    f"{sorted(SCHEMA_FILES)}"
                )
            subject = schema_name
            problems.extend(schema_errors(artifact, REFERENCES / SCHEMA_FILES[schema_name]))
            problems.extend(check_hollow(artifact))
            problems.extend(SEMANTIC[schema_name](artifact))
            if args.input is not None:
                problems.extend(check_stale_subject(artifact, args.input))
            if args.resolve_subjects is not None:
                problems.extend(check_resolved_subjects(artifact, args.resolve_subjects))
    except Unusable as error:
        print(f"PREL-UNUSABLE {error}", file=sys.stderr)
        return 64

    if problems:
        for problem in problems:
            print(f"PREL-RED {problem}", file=sys.stderr)
        return 2
    print(f"PREL-GREEN {subject}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
