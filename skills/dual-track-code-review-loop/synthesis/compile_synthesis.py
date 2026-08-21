#!/usr/bin/env python3
"""Compile the DTCR synthesis and problem-closure projections deterministically.

    exact task + source subject
    + deterministic fact bundle
    + semantic context bundle or the literal NOT_APPLICABLE
    + admitted invariants
    -> synthesis packet -> candidate review card -> Human/Tech Lead decision

    Problem -> Claim -> Requirement -> Mechanism -> Owner -> Oracle
    -> positive/negative denominator -> evidence lane
    -> ClosureRecord | BLOCKED | REJECTED_OVERCLAIM | NOT_APPLICABLE

Every output is a pure function of the input bytes plus this file, serialised
canonically (`sort_keys`, two-space indent, one trailing newline), so `--check`
byte-compares a committed projection instead of trusting that somebody
regenerated it. The compiler adds no review semantics: a claim with no observed
fact comes out `NO_OBSERVED_FACT`, a lane with no bundle comes out
`NOT_APPLICABLE` with the rationale the request had to state, and every
decision field is pinned empty because the card recommends and never decides.

Three states this compiler deliberately cannot emit, and why none is a bug:

* a decision. `decision_state` is pinned `HUMAN_ADMIT_REQUIRED` on every card
  regardless of input, because MODEL_SUMMARY != REVIEW_DECISION. A request that
  carries a decision, a merge or an approval field is refused rather than
  ignored: ignoring it would let the field travel in the input forever.
* a benchmark. A static count, a graph query and a symbol index measure the
  tree, not the running system, so `benchmark_established` is pinned false and
  a performance claim without an executed measurement record stays a claim.
* a closure from an unexecuted oracle. Compiling an oracle is not running one.
  `CLOSURE_RECORD_EMITTED` requires a receipt reference the input carried from
  a lane that actually ran; without it the row is `BLOCKED`, naming the exact
  link of the chain that is missing.

The problem-closure vocabulary is the one
`skills/agentic-tech-lead-orchestration/references/contracts/problem-closure.schema.json`
already owns. This compiler references it and adds only what that ledger has no
term for: the split between a rejected source claim and an implemented
mechanism, which are two states here and cannot collapse into one.

Exits: 0 green, 2 refused with a named code or a --check projection is stale,
64 the compiler could not run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

EXACT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
EXACT_DIGEST = re.compile(r"^[0-9a-f]{64}$")

# Every field a request may not carry. The card recommends; these words are the
# shape a promotion takes on the way in.
DECISION_FIELDS = ("decision", "decided_by", "approved", "merge", "auto_merge", "verdict")

# Pinned on every output regardless of input. Each key is the illegal promotion
# spelled out, so a reader of the JSON sees the law and not a policy name.
HARD_LAWS = {
    "static_metric_is_benchmark": False,
    "retrieved_incident_is_current_failure": False,
    "model_summary_is_review_decision": False,
    "one_green_test_is_full_denominator": False,
    "no_illegal_graph_edge_is_behavior_preserved": False,
    "source_claim_rejected_is_problem_solved": False,
    "technical_pass_is_user_or_paid_validation": False,
}
AUTHORITY = {
    "merge": False,
    "permission": False,
    "secret": False,
    "production": False,
    "user_value": False,
    "paid_demand": False,
    "release": False,
}
CLOSURE_AUTHORITY = {
    "merge": False,
    "release": False,
    "user_value": False,
    "paid_demand": False,
}
VOCABULARY_REF = (
    "skills/agentic-tech-lead-orchestration/references/contracts/"
    "problem-closure.schema.json"
)
CONFIRMED = "CONFIRMED_AGAINST_DETERMINISTIC_FACT"

MEASUREMENT_KEYS = (
    "value",
    "unit",
    "method",
    "sample_size",
    "environment_id",
    "subject_commit",
    "measured_at",
)


class Refused(Exception):
    """The input cannot be compiled without inventing a review semantic.

    Carries the named code so a caller can act on which law fired, not on the
    fact that something did.
    """

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Refused("UNREADABLE_INPUT", f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise Refused("UNREADABLE_INPUT", f"{path}: root must be an object")
    return value


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def require_exact_subject(subject: Any, where: str) -> dict[str, str]:
    if not isinstance(subject, dict):
        raise Refused("STALE_SUBJECT", f"{where}: subject must be an object")
    for key in ("repository_binding_id", "subject_commit", "subject_tree"):
        if key not in subject:
            raise Refused("STALE_SUBJECT", f"{where}: no {key}")
    for key in ("subject_commit", "subject_tree"):
        if not EXACT_COMMIT.match(str(subject[key])):
            raise Refused(
                "STALE_SUBJECT",
                f"{where}.{key} is {subject[key]!r}: a branch, a tag or a moving "
                f"label dates the finding to nothing",
            )
    return {key: subject[key] for key in ("repository_binding_id", "subject_commit", "subject_tree")}


def refuse_decision_fields(node: Any, where: str) -> None:
    """A request may not carry the decision it is asking a human to make."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in DECISION_FIELDS:
                raise Refused(
                    "RECOMMENDATION_PROMOTED_TO_DECISION",
                    f"{where}.{key} carries a decision. The card recommends; the "
                    f"decision fields are Human/Tech-Lead owned and this compiler "
                    f"pins them empty",
                )
            refuse_decision_fields(value, f"{where}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            refuse_decision_fields(value, f"{where}[{index}]")


# --------------------------------------------------------------------------
# review synthesis
# --------------------------------------------------------------------------

def compile_review(source: Path) -> dict[str, Any]:
    request = load(source)
    if request.get("schema") != "dtcr/synthesis-request/v1":
        raise Refused(
            "UNREADABLE_INPUT", "input must be a dtcr/synthesis-request/v1 artifact"
        )
    refuse_decision_fields(request, "request")

    subject = require_exact_subject(request.get("subject"), "request.subject")
    task = request.get("task") or {}
    for key in ("task_ref", "owner", "lease_paths", "task_state_writers"):
        if not task.get(key):
            raise Refused("UNREADABLE_INPUT", f"request.task.{key} is required")

    writers = sorted(set(task["task_state_writers"]))
    if len(writers) != 1:
        raise Refused(
            "SECOND_TASK_STATE_WRITER",
            f"{len(writers)} task-state writers declared ({', '.join(writers) or 'none'}). "
            f"One mutable task state has one writer; two writers make the ledger "
            f"a record of whoever wrote last",
        )

    facts = request.get("fact_bundle") or {}
    if facts.get("subject_commit") != subject["subject_commit"]:
        raise Refused(
            "STALE_SUBJECT",
            f"fact bundle ran against {facts.get('subject_commit')!r} and the task "
            f"subject is {subject['subject_commit']!r}",
        )
    ceiling = facts.get("coverage_ceiling")
    if not isinstance(ceiling, dict):
        raise Refused(
            "COVERAGE_CEILING_OMITTED",
            "the fact bundle carries no coverage ceiling. A bundle with no ceiling "
            "reads downstream as a bundle over everything",
        )

    observations = sorted(facts.get("observations") or [], key=lambda row: row["observation_ref"])
    if not observations:
        raise Refused("UNREADABLE_INPUT", "fact bundle carries no observations")
    for row in observations:
        if row.get("suppressed_by_context"):
            raise Refused(
                "DETERMINISTIC_FACT_OMITTED",
                f"{row['observation_ref']} is marked suppressed because retrieved "
                f"context disagrees. Context may explain a fact and may never "
                f"delete one",
            )

    invariants = {row["invariant_ref"]: row for row in request.get("invariants") or []}
    admitted = {ref for ref, row in invariants.items() if row.get("admission") == "ADMITTED"}
    for row in observations:
        ref = row.get("invariant_ref")
        if ref is None:
            continue
        if ref not in admitted:
            raise Refused(
                "UNADMITTED_INVARIANT",
                f"{row['observation_ref']} cites invariant {ref}, which is not an "
                f"admitted invariant of this subject",
            )

    semantic = compile_semantic_lane(request.get("semantic_bundle"))
    claims = compile_claims(request.get("claims") or [], facts, observations)

    packet = {
        "schema": "dtcr/synthesis-packet/v1",
        "packet_id": "DTCR-SP-001",
        "task_ref": task["task_ref"],
        "subject": subject,
        "fact_lane": {
            "state": "PRESENT",
            "receipt_ref": facts["receipt_ref"],
            "bundle_digest": facts["bundle_digest"],
            "coverage_ceiling_ref": ceiling["ceiling_ref"],
            "observation_refs": [row["observation_ref"] for row in observations],
        },
        "semantic_lane": semantic["lane"],
        "invariant_refs": sorted(admitted),
        "authority": dict(AUTHORITY),
    }
    if not EXACT_DIGEST.match(str(packet["fact_lane"]["bundle_digest"])):
        raise Refused(
            "UNREADABLE_INPUT", "fact_bundle.bundle_digest must be a sha256 digest"
        )

    card = compile_card(packet, request, facts, ceiling, observations, invariants, semantic, claims)
    return {
        "schema": "dtcr/synthesis-projection/v1",
        "derived_from": source.name,
        "synthesis_packet": packet,
        "review_card": card,
    }


def compile_semantic_lane(bundle: Any) -> dict[str, Any]:
    """The optional lane, typed so an absent lane cannot read as a quiet one."""
    if bundle == "NOT_APPLICABLE":
        return {
            "lane": {
                "state": "NOT_APPLICABLE",
                "rationale": "the request declared the literal NOT_APPLICABLE for the "
                "semantic context lane",
                "consumed_row_refs": [],
            },
            "rows": [],
        }
    if not isinstance(bundle, dict):
        raise Refused(
            "UNREADABLE_INPUT",
            "semantic_bundle must be an object or the literal NOT_APPLICABLE. An "
            "omitted lane and an absent one are different facts",
        )
    rows = []
    for row in sorted(bundle.get("rows") or [], key=lambda item: item["row_rank"]):
        for key in ("back_reference_ref", "freshness_ref", "document_ref"):
            if not row.get(key):
                raise Refused(
                    "SEMANTIC_ROW_WITHOUT_BACK_REFERENCE",
                    f"row {row.get('row_rank')} of {bundle.get('result_ref')} carries no "
                    f"{key}. A row a reader cannot resolve to a source is a score",
                )
        if row.get("influence", "CONTEXT_ONLY") != "CONTEXT_ONLY":
            raise Refused(
                "RETRIEVED_INCIDENT_AS_CURRENT_FAILURE",
                f"row {row['row_rank']} declares influence {row['influence']!r}. A "
                f"retrieved incident is evidence that something once happened "
                f"somewhere, never that it is happening here now",
            )
        rows.append(
            {
                "result_ref": bundle["result_ref"],
                "row_rank": row["row_rank"],
                "document_ref": row["document_ref"],
                "back_reference_ref": row["back_reference_ref"],
                "freshness_ref": row["freshness_ref"],
                "freshness_state": row.get("freshness_state", "UNKNOWN"),
                "basis_grade": "SEMANTIC_CONTEXT_CANDIDATE",
                "influence": "CONTEXT_ONLY",
                "establishes_current_failure": False,
            }
        )
    return {
        "lane": {
            "state": "PRESENT",
            "result_ref": bundle["result_ref"],
            "consumed_row_refs": [row["back_reference_ref"] for row in rows],
        },
        "rows": rows,
    }


def compile_claims(
    claims: list[dict[str, Any]], facts: dict[str, Any], observations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Pair each source claim with the observed facts, and nothing else."""
    measurements = {row["claim_id"]: row for row in facts.get("measurements") or []}
    known = {row["observation_ref"] for row in observations}
    compiled = []
    for claim in sorted(claims, key=lambda row: row["claim_id"]):
        refs = sorted(set(claim.get("observed_fact_refs") or []) & known)
        measurement = measurements.get(claim["claim_id"])
        if measurement is not None:
            missing = [key for key in MEASUREMENT_KEYS if key not in measurement]
            if missing:
                raise Refused(
                    "FABRICATED_MEASUREMENT",
                    f"{claim['claim_id']} carries a measurement missing "
                    f"{', '.join(missing)}. A figure without its method, sample and "
                    f"exact subject is a number somebody remembered",
                )
            if not EXACT_COMMIT.match(str(measurement["subject_commit"])):
                raise Refused(
                    "FABRICATED_MEASUREMENT",
                    f"{claim['claim_id']} measurement names subject "
                    f"{measurement['subject_commit']!r} rather than an exact commit",
                )
            measurement_class = "EXECUTED_MEASUREMENT"
        elif claim.get("claim_class") == "PERFORMANCE_CLAIM":
            if claim.get("claimed_improvement") is not None:
                raise Refused(
                    "FABRICATED_MEASUREMENT",
                    f"{claim['claim_id']} states an improvement of "
                    f"{claim['claimed_improvement']!r} with no executed measurement "
                    f"in the fact bundle. STATIC_METRIC != BENCHMARK",
                )
            measurement_class = "NOT_MEASURED"
        else:
            measurement_class = "STATIC_METRIC" if refs else "NOT_MEASURED"

        if not refs:
            verdict = "NO_OBSERVED_FACT"
        elif claim.get("contradicted_by_fact"):
            verdict = "OBSERVED_FACT_CONTRADICTS"
        elif measurement_class == "STATIC_METRIC" and claim.get("claim_class") == "PERFORMANCE_CLAIM":
            verdict = "NO_OBSERVED_FACT"
        else:
            verdict = "OBSERVED_FACT_SUPPORTS"

        compiled.append(
            {
                "claim_id": claim["claim_id"],
                "claim": claim["claim"],
                "claim_class": claim.get("claim_class", "SOURCE_STATEMENT"),
                "claim_source_ref": claim["claim_source_ref"],
                "measurement_class": measurement_class,
                "observed_fact_refs": refs,
                "verdict": verdict,
                "benchmark_established": False,
            }
        )
    if not compiled:
        raise Refused("UNREADABLE_INPUT", "request.claims is empty: there is nothing to review")
    return compiled


def compile_card(
    packet: dict[str, Any],
    request: dict[str, Any],
    facts: dict[str, Any],
    ceiling: dict[str, Any],
    observations: list[dict[str, Any]],
    invariants: dict[str, Any],
    semantic: dict[str, Any],
    claims: list[dict[str, Any]],
) -> dict[str, Any]:
    task = request["task"]
    confirmed = [row for row in observations if row.get("state") == CONFIRMED]
    unresolved = [row for row in observations if row.get("state") in {"OPEN", "BLOCKED"}]

    by_invariant: dict[str, list[dict[str, Any]]] = {}
    for row in observations:
        if row.get("invariant_ref"):
            by_invariant.setdefault(row["invariant_ref"], []).append(row)

    admitted_rows = []
    for ref in sorted(packet["invariant_refs"]):
        cited = by_invariant.get(ref, [])
        admitted_rows.append(
            {
                "invariant_ref": ref,
                "statement": invariants[ref]["statement"],
                "violated_case_refs": sorted(
                    row["observation_ref"] for row in cited if row.get("state") == CONFIRMED
                ),
                "unresolved_case_refs": sorted(
                    row["observation_ref"] for row in cited if row.get("state") != CONFIRMED
                ),
            }
        )

    controls = [
        {
            "control_id": f"NC-{index + 1:03d}",
            "refuses": refuses,
            "observed_if_absent": observed,
        }
        for index, (refuses, observed) in enumerate(negative_controls(confirmed, claims))
    ]

    plan = []
    for index, ref in enumerate(sorted(row["invariant_ref"] for row in confirmed)):
        positives = len([row for row in confirmed if row["invariant_ref"] == ref])
        negatives = len([row for row in controls if ref in row["refuses"]])
        plan.append(
            {
                "step_id": f"VP-{index + 1:03d}",
                "oracle": f"re-run the deterministic fact plane against {ref} at the "
                f"head commit of the change and assert the confirmed cases are absent",
                "arrival": "STATIC",
                "denominator_definition": denominator_definition(ceiling),
                "positive_denominator": positives,
                "negative_denominator": max(negatives, 1),
                "executed": False,
            }
        )
    plan.append(
        {
            "step_id": f"VP-{len(plan) + 1:03d}",
            "oracle": "run the owning test suite at the head commit and record its "
            "exit code beside the count of cases it actually enumerated",
            "arrival": "SANDBOX",
            "denominator_definition": denominator_definition(ceiling),
            "positive_denominator": len(observations),
            "negative_denominator": max(len(controls), 1),
            "executed": False,
        }
    )

    if confirmed:
        action, rationale = (
            "PROPOSE_BOUNDED_REFACTOR",
            f"{len(confirmed)} case(s) confirmed against a deterministic fact",
        )
    elif unresolved or any(row["verdict"] != "OBSERVED_FACT_SUPPORTS" for row in claims):
        action, rationale = (
            "REQUEST_MISSING_EVIDENCE",
            "no case is confirmed and at least one claim or case has no deterministic "
            "fact behind it",
        )
    else:
        action, rationale = (
            "RECOMMEND_NO_CHANGE",
            "every observation resolved and every claim is carried by an observed fact",
        )

    return {
        "schema": "dtcr/review-card/v1",
        "card_id": "DTCR-RC-001",
        "card_class": "MODEL_SUMMARY_RECOMMENDATION",
        "packet_ref": packet["packet_id"],
        "subject": dict(packet["subject"]),
        "claim_vs_observed_fact": claims,
        "coverage_ceiling": {
            "ceiling_ref": ceiling["ceiling_ref"],
            "analysed": ceiling.get("analysed", "NOT_MEASURED"),
            "completeness": ceiling.get("completeness", "UNKNOWN"),
            "omissions": sorted(ceiling.get("omissions") or []),
            "unanalysed_inputs_cleared": False,
        },
        "changed_symbols_and_blast_radius": {
            "changed_symbol_refs": sorted(facts.get("changed_symbol_refs") or []),
            "blast_radius_path_refs": sorted(facts.get("blast_radius_path_refs") or []),
            "edge_provenance": facts.get("graph_provenance", "NOT_APPLICABLE"),
            "edge_completeness": facts.get("graph_completeness", "UNKNOWN"),
            "behavior_preserved": False,
        },
        "admitted_invariants": admitted_rows,
        "retrieved_context": {
            "state": packet["semantic_lane"]["state"],
            "rationale": packet["semantic_lane"].get(
                "rationale", "the semantic context lane was consulted"
            ),
            "rows": semantic["rows"],
        },
        "benefits": graded(request, "benefits"),
        "costs": graded(request, "costs"),
        "failure_modes": graded(request, "failure_modes"),
        "unknowns": sorted(
            (request.get("assessments") or {}).get("unknowns") or [],
            key=lambda row: row["statement"],
        ),
        "required_negative_controls": controls,
        "recommended_action": {
            "action": action,
            "rationale": rationale,
            "binding": "RECOMMENDATION_ONLY",
        },
        "owner_and_lease": {
            "owner": task["owner"],
            "lease_paths": sorted(task["lease_paths"]),
            "task_state_writer": sorted(task["task_state_writers"])[0],
            "task_state_writer_count": 1,
        },
        "verification_plan": plan,
        "claims_not_proven": claims_not_proven(claims, packet, confirmed),
        "decision": {
            "decision_text": "",
            "decided_by": "",
            "decision_state": "HUMAN_ADMIT_REQUIRED",
        },
        "hard_laws": dict(HARD_LAWS),
        "authority": dict(AUTHORITY),
    }


def denominator_definition(ceiling: dict[str, Any]) -> str:
    analysed = ceiling.get("analysed")
    if isinstance(analysed, dict):
        return analysed["denominator_definition"]
    return (
        "the coverage ceiling reports NOT_MEASURED, so the denominator of this "
        "step is unnamed and one green run says nothing about the rest"
    )


def negative_controls(
    confirmed: list[dict[str, Any]], claims: list[dict[str, Any]]
) -> list[tuple[str, str]]:
    """Derived, never carried. A control a request supplies is a control it chose."""
    rows = [
        (
            f"a pass over a subject without the edge behind {row['observation_ref']} "
            f"still reporting {row['invariant_ref']} as violated",
            f"the case survives when its deterministic basis is removed, which makes "
            f"the basis decorative",
        )
        for row in sorted(confirmed, key=lambda item: item["observation_ref"])
    ]
    rows.extend(
        (
            f"{row['claim_id']} reading as supported once its observed facts are removed",
            "the claim was carried by the review card rather than by the fact plane",
        )
        for row in claims
        if row["verdict"] != "OBSERVED_FACT_SUPPORTS"
    )
    rows.append(
        (
            "the recommended action staying the same after every deterministic "
            "observation is removed from the bundle",
            "the recommendation was produced by the summary rather than by the facts",
        )
    )
    return rows


def graded(request: dict[str, Any], slot: str) -> list[dict[str, Any]]:
    """Benefit, cost and failure-mode entries keep the grade their basis supports."""
    rows = []
    for row in sorted((request.get("assessments") or {}).get(slot) or [], key=lambda item: item["statement"]):
        basis = sorted(row.get("basis_refs") or [])
        rows.append(
            {
                "statement": row["statement"],
                "grade": "OBSERVED_FACT" if basis else "ANALYST_EXPECTATION",
                "basis_refs": basis,
            }
        )
    return rows


def claims_not_proven(
    claims: list[dict[str, Any]], packet: dict[str, Any], confirmed: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = [
        {"statement": row["claim"], "lane": "DETERMINISTIC_FACT_ABSENT"}
        for row in claims
        if row["verdict"] != "OBSERVED_FACT_SUPPORTS"
    ]
    if confirmed:
        rows.append(
            {
                "statement": "removing the illegal edges these cases name preserves the "
                "behaviour of the code that used them",
                "lane": "BEHAVIOURAL",
            }
        )
    if packet["semantic_lane"]["state"] == "NOT_APPLICABLE":
        rows.append(
            {
                "statement": "no decision record, incident write-up or budget was "
                "consulted for this review",
                "lane": "SEMANTIC",
            }
        )
    rows.append({"statement": "any user derives value from this change", "lane": "USER"})
    rows.append({"statement": "anybody pays for this change", "lane": "PAID"})
    rows.append(
        {
            "statement": "this change may be merged, released or run in production",
            "lane": "HUMAN_ADMIT",
        }
    )
    return sorted(rows, key=lambda row: (row["lane"], row["statement"]))


# --------------------------------------------------------------------------
# problem closure
# --------------------------------------------------------------------------

CHAIN = ("requirement", "mechanism", "owner", "oracle", "denominators", "evidence_lane")
BLOCKED_ON = {
    "requirement": "REQUIREMENT_ABSENT",
    "mechanism": "MECHANISM_ABSENT",
    "owner": "OWNER_ABSENT",
    "oracle": "ORACLE_ABSENT",
    "denominators": "DENOMINATOR_ABSENT",
    "evidence_lane": "EVIDENCE_LANE_ABSENT",
}


def compile_closure(source: Path) -> dict[str, Any]:
    request = load(source)
    if request.get("schema") != "dtcr/problem-closure-request/v1":
        raise Refused(
            "UNREADABLE_INPUT", "input must be a dtcr/problem-closure-request/v1 artifact"
        )
    refuse_decision_fields(request, "request")
    subject = require_exact_subject(request.get("subject"), "request.subject")

    writers = sorted(set(request.get("ledger_writers") or []))
    if len(writers) != 1:
        raise Refused(
            "SECOND_TASK_STATE_WRITER",
            f"{len(writers)} ledger writers declared. One closure ledger has one "
            f"writer; a second writer makes the ledger a record of whoever ran last",
        )

    floors = request.get("denominator_floors") or {}
    rows = []
    for index, problem in enumerate(
        sorted(request.get("problems") or [], key=lambda row: row["problem_id"])
    ):
        rows.append(compile_closure_row(index, problem, subject, floors))
    if not rows:
        raise Refused("UNREADABLE_INPUT", "request.problems is empty")

    return {
        "schema": "dtcr/problem-closure-projection/v1",
        "derived_from": source.name,
        "subject": subject,
        "vocabulary_ref": VOCABULARY_REF,
        "ledger_writer": writers[0],
        "denominator": {
            "problem_ids": [row["problem_id"] for row in rows],
            "closure_states": {
                state: len([row for row in rows if row["closure_state"] == state])
                for state in sorted({row["closure_state"] for row in rows})
            },
        },
        "rows": rows,
    }


def compile_closure_row(
    index: int, problem: dict[str, Any], subject: dict[str, str], floors: dict[str, Any]
) -> dict[str, Any]:
    problem_id = problem["problem_id"]
    claim_state = problem.get("source_claim_state", "OPEN")
    mechanism = problem.get("mechanism") or {}
    mechanism_state = mechanism.get("mechanism_state", "NOT_PROPOSED")
    lane = problem.get("evidence_lane") or {}
    receipt_ref = lane.get("receipt_ref")

    row: dict[str, Any] = {
        "schema": "dtcr/problem-closure-row/v1",
        "row_id": f"DTCR-PC-{index + 1:03d}",
        "problem_id": problem_id,
        "subject_commit": subject["subject_commit"],
        "vocabulary_ref": VOCABULARY_REF,
        "source": {
            "kind": problem["source"]["kind"],
            "identity": problem["source"]["identity"],
            "location": problem["source"]["location"],
        },
        "claim": {
            "statement": problem["claim"],
            "claim_class": problem.get("claim_class", "SOURCE_STATEMENT"),
            "source_claim_state": claim_state,
        },
        "requirement": problem.get("requirement"),
        "mechanism": (
            {"statement": mechanism["statement"], "mechanism_state": mechanism_state}
            if mechanism
            else None
        ),
        "owner": problem.get("owner"),
        "oracle": problem.get("oracle"),
        "denominators": problem.get("denominators"),
        "evidence_lane": {
            "lane": lane.get("lane", "NOT_EXERCISED"),
            "receipt_ref": receipt_ref,
            "arrival": lane.get("arrival"),
        },
        "separation": {
            "source_claim_rejected_is_problem_solved": False,
            "closed_by_this_compiler": False,
        },
        "authority": dict(CLOSURE_AUTHORITY),
    }

    if problem.get("closed") and mechanism_state != "VERIFIED_BY_RECEIPT":
        raise Refused(
            "SOURCE_OVERCLAIM_CLOSED_WITHOUT_MECHANISM",
            f"{problem_id} is asked to close while its mechanism is {mechanism_state}. "
            f"SOURCE_CLAIM_REJECTED != TECHNICAL_PROBLEM_SOLVED, and neither is an "
            f"implemented mechanism a verified one",
        )

    denominators = problem.get("denominators")
    if isinstance(denominators, dict):
        for key in ("positive", "negative"):
            if key not in denominators:
                raise Refused(
                    "UNREADABLE_INPUT", f"{problem_id}.denominators.{key} is required"
                )
            floor = (floors.get(problem_id) or {}).get(key)
            if floor is not None and denominators[key] < floor:
                raise Refused(
                    "DENOMINATOR_SHRINKAGE",
                    f"{problem_id} declares a {key} denominator of {denominators[key]} "
                    f"against a recorded floor of {floor}. The same green over a "
                    f"smaller set is not the same green",
                )
        if denominators["negative"] < 1:
            raise Refused(
                "DENOMINATOR_SHRINKAGE",
                f"{problem_id} declares no negative denominator. "
                f"ONE_GREEN_TEST != FULL_DENOMINATOR",
            )

    if claim_state == "NOT_APPLICABLE":
        rationale = problem.get("not_applicable_rationale")
        if not rationale:
            raise Refused(
                "UNREADABLE_INPUT",
                f"{problem_id} is NOT_APPLICABLE with no rationale, which reads "
                f"downstream as a problem nobody looked at",
            )
        row["closure_state"] = "NOT_APPLICABLE"
        row["not_applicable_rationale"] = rationale
        row["blocked_on"] = []
        row["closure_record_ref"] = None
        return row

    if claim_state == "REJECTED_OVERCLAIM":
        row["closure_state"] = "REJECTED_OVERCLAIM"
        row["blocked_on"] = []
        row["closure_record_ref"] = None
        return row

    missing = [BLOCKED_ON[link] for link in CHAIN if not problem.get(link)]
    if receipt_ref is None:
        missing.append("VERIFICATION_RECEIPT_ABSENT")
    if mechanism_state != "VERIFIED_BY_RECEIPT":
        missing.append("MECHANISM_NOT_VERIFIED")
    if missing:
        row["closure_state"] = "BLOCKED"
        row["blocked_on"] = sorted(set(missing))
        row["closure_record_ref"] = None
        return row

    row["closure_state"] = "CLOSURE_RECORD_EMITTED"
    row["blocked_on"] = []
    row["closure_record_ref"] = problem["closure_record_ref"]
    return row


# --------------------------------------------------------------------------

STAGES = {"review": compile_review, "closure": compile_closure}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=sorted(STAGES))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="byte-compare --out against a fresh compilation instead of writing it",
    )
    args = parser.parse_args()

    try:
        rendered = canonical(STAGES[args.stage](args.input))
    except Refused as error:
        print(f"DTCR-SYNTH-RED {args.stage} {error}", file=sys.stderr)
        return 2
    except (KeyError, TypeError, IndexError) as error:
        print(
            f"DTCR-SYNTH-UNUSABLE {args.stage}: malformed input: {error!r}",
            file=sys.stderr,
        )
        return 64

    if args.out is None:
        sys.stdout.write(rendered)
        return 0
    if args.check:
        try:
            current = args.out.read_text(encoding="utf-8")
        except OSError as error:
            print(f"DTCR-SYNTH-RED missing projection {args.out}: {error}", file=sys.stderr)
            return 2
        if current != rendered:
            print(
                f"DTCR-SYNTH-RED {args.out} is not what {args.input.name} compiles to; "
                f"regenerate it rather than editing it",
                file=sys.stderr,
            )
            return 2
        print(f"DTCR-SYNTH-GREEN {args.stage} projection is current")
        return 0
    args.out.write_text(rendered, encoding="utf-8")
    print(f"DTCR-SYNTH-GREEN wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
