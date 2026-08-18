#!/usr/bin/env python3
"""Frozen deterministic A/B over this Skill's own refactor. No host, no network.

Issue #350. Four treatments, each one an immutable body this Skill actually
had. They are reproduced byte for byte from history rather than reconstructed:
`git cat-file -p <blob>` emits each fixture, and the blob identities below are
the ones the commits carry.

    A  74dc0b4  the body before the compile-the-rubric landing
    B0 2eab9dd  that landing exactly as it shipped, including what it dropped
    B1 2aa3e29  the uplift-arms repair
    B2 6021233  the live-lane repair, which is still the live SKILL.md

The landing at B0 is a real refactor and not an append: it rewrote the capsule
clauses, collapsed three disposition paragraphs into one, and replaced a
manually entered architecture dimension score with a compiled rubric. Rewrites
lose things, and this one lost three. A cleaner body is not evidence that it
kept what it replaced, so the losses are scored rather than described:

    the open-ended "any action the active host marks side-effecting" class,
    which narrowed to a closed enumeration and is now absent from the Skill;
    the body's route to scripts/check_meta_abstraction_eval.py;
    the body's route to references/meta-abstraction-eval-receipt.schema.json.

The last two are relocations, not deletions -- AGENTS.md, README.md, evals.json
and the meta standard still route them -- and that difference is asserted here,
because "moved out of the entrypoint" and "gone" read identically in prose. The
first one is a deletion, and RETAINED_NON_CLAIM records it as still open at HEAD
rather than letting a later reader infer it was repaired.

The matched hermetic task runs this Skill's own arm producer over all four
frozen bodies with one capsule, one procedure set and one builder, so the only
variable is the treatment. It observes no model and no host binary: the live
five-arm matrix stays with #232 and the preregistered #219 run stays unrun.

Exit codes: 0 green, 2 a refused claim.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # keep the suite from writing into scripts/

import hashlib
import json
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
FIXTURES = SKILL / "tests" / "fixtures" / "refactor"

sys.path.insert(0, str(SKILL / "scripts"))
import build_uplift_arms as builder  # noqa: E402  the producer under measurement

OLD = FIXTURES / "old-canonical-SKILL.txt"
LANDED = FIXTURES / "refactor-as-landed-SKILL.txt"
UPLIFT = FIXTURES / "uplift-arms-repaired-SKILL.txt"
LIVE = SKILL / "SKILL.md"

# B2 is the live body; the golden-proof registry pins its blob, so pinning it
# twice would only move the failure. The three frozen arms are pinned here.
EXPECTED_GIT_BLOBS = {
    OLD: "e3fff105c7e62b4f42964975d918701e76588fe1",
    LANDED: "a15f34f036e279b7559e14990aa8aadd69342fc9",
    UPLIFT: "1440da35e6c41e19de7720ccd1af5abb1225bd6a",
}

ORDER = [
    "A_OLD_CANONICAL",
    "B0_REFACTOR_AS_LANDED",
    "B1_UPLIFT_ARMS_REPAIRED",
    "B2_LIVE_LANES_REPAIRED",
]

DISPOSITIONS = (
    "VERIFIED",
    "SATISFIED_BY_PRIOR_EVIDENCE",
    "NOT_APPLICABLE_WITH_EVIDENCE",
    "BLOCKED",
    "FAILED",
    "WAIVED_WITH_AUTHORIZED_REASON",
)
ARM_NAMES = (
    "NO_SKILL",
    "METADATA_ONLY",
    "FULL_SKILL",
    "DELTA_CAPSULE",
    "DELTA_CAPSULE_PLUS_HARNESS",
)
DIMENSIONS = (
    "control flow and state governance",
    "tool boundary and idempotency",
    "context budget and memory",
    "fault tolerance, self-healing, and HITL",
    "Evals and observability",
)
LIVE_LANES = (
    "scripts/run_arm_trials.py",
    "scripts/retrieve_external_skill.py",
    "scripts/observe_multimodal.py",
    "scripts/trace_feedback_loop.py",
    "scripts/summarise_uplift_matrix.py",
    "scripts/bind_actions_receipt.py",
    "scripts/build_convergence_packet.py",
)

# Where each relocated guarantee went. A route that only moved is still a route;
# a route that moved nowhere is a deletion, and these are the files that decide
# which of the two happened.
RELOCATED_TO = {
    "meta_eval_checker_routed_from_body": (
        "check_meta_abstraction_eval.py",
        ("AGENTS.md", "README.md", "evals.json", "scripts/README.md",
         "references/meta-abstraction-eval-standard.md"),
    ),
    "meta_eval_receipt_schema_routed_from_body": (
        "meta-abstraction-eval-receipt.schema.json",
        ("README.md", "references/README.md"),
    ),
}

# Named, still-open loss. Restoring it is welcome and turns this red on purpose:
# the record of what a refactor cost has to be updated by whoever repays it.
RETAINED_NON_CLAIM = {
    "criterion": "host_marked_side_effect_class",
    "needle": "marks side-effecting",
    "scanned": ("SKILL.md", "AGENTS.md", "README.md",
                "references/context-capsule.schema.json",
                "references/runtime-receipt.schema.json"),
}


def has_all(text: str, needles: tuple[str, ...]) -> bool:
    return all(needle in text for needle in needles)


STRENGTHS = {
    "host_marked_side_effect_class":
        lambda t: "marks side-effecting" in t,
    "meta_eval_checker_routed_from_body":
        lambda t: "check_meta_abstraction_eval.py" in t,
    "meta_eval_receipt_schema_routed_from_body":
        lambda t: "meta-abstraction-eval-receipt.schema.json" in t,
    "delta_formula_exact":
        lambda t: "DELTA = APPLICABLE - ALREADY_SATISFIED - PRIOR_VERIFIED_EVIDENCE" in t,
    "six_terminal_dispositions":
        lambda t: has_all(t, DISPOSITIONS),
    "non_terminal_states_refused":
        lambda t: has_all(t, ("MENTIONED", "PLANNED", "EXECUTED_PENDING_VERIFICATION")),
    "latent_behavior_diagnostic_only":
        lambda t: has_all(t, ("SATISFIED_BY_LATENT_BEHAVIOR", "diagnostic only")),
    "capsule_admission_refuses_widening":
        lambda t: has_all(t, ("widen", "data egress")),
    "no_raw_private_reasoning":
        lambda t: has_all(t, ("NO RAW PRIVATE REASONING PAYLOADS", "raw-reasoning field")),
    "shadow_workers_read_only":
        lambda t: "SHADOW WORKERS ARE READ ONLY" in t,
    "close_gate_exit_codes":
        lambda t: has_all(t, ("0   contract closed", "2   semantic/contract refusal",
                              "64  absent or malformed input")),
    "model_statement_never_replaces_assertion":
        lambda t: "A model statement is never a substitute for a hard assertion." in t,
    "human_admit_promotion_authority":
        lambda t: "HUMAN ADMIT REMAINS THE PROMOTION AUTHORITY" in t,
    "five_attribution_arms":
        lambda t: has_all(t, ARM_NAMES),
    "architecture_dimension_weights":
        lambda t: has_all(t, DIMENSIONS),
    "not_exercised_not_promoted_by_prose":
        lambda t: "Do not promote `NOT_EXERCISED` states from prose" in t,
    "architecture_rubric_compiled":
        lambda t: has_all(t, ("references/agent-architecture-rubric.json",
                              "check_agent_architecture_eval.py")),
    "vibe_contradiction_law":
        lambda t: "A VIBE SIGNAL IS A CONTRADICTION" in t,
    "uplift_arms_routed":
        lambda t: "scripts/build_uplift_arms.py" in t,
    "uplift_preregistration_bound":
        lambda t: "skills/repository-capability-audit/evals/uplift-preregistration.json" in t,
    "live_lane_routes":
        lambda t: has_all(t, LIVE_LANES),
    "observed_qualifier_discipline":
        lambda t: has_all(t, ("OBSERVED (1 rep/arm)", "qualifies_for_219")),
}

# Read off the four bodies, then frozen. Drift in either direction is a refusal:
# a lost guarantee nobody recorded, or a repaid one nobody wrote down.
EXPECTED = {
    "host_marked_side_effect_class": (True, False, False, False),
    "meta_eval_checker_routed_from_body": (True, False, False, False),
    "meta_eval_receipt_schema_routed_from_body": (True, False, False, False),
    "delta_formula_exact": (True, True, True, True),
    "six_terminal_dispositions": (True, True, True, True),
    "non_terminal_states_refused": (True, True, True, True),
    "latent_behavior_diagnostic_only": (True, True, True, True),
    "capsule_admission_refuses_widening": (True, True, True, True),
    "no_raw_private_reasoning": (True, True, True, True),
    "shadow_workers_read_only": (True, True, True, True),
    "close_gate_exit_codes": (True, True, True, True),
    "model_statement_never_replaces_assertion": (True, True, True, True),
    "human_admit_promotion_authority": (True, True, True, True),
    "five_attribution_arms": (True, True, True, True),
    "architecture_dimension_weights": (True, True, True, True),
    "not_exercised_not_promoted_by_prose": (True, True, True, True),
    "architecture_rubric_compiled": (False, True, True, True),
    "vibe_contradiction_law": (False, True, True, True),
    "uplift_arms_routed": (False, False, True, True),
    "uplift_preregistration_bound": (False, False, True, True),
    "live_lane_routes": (False, False, False, True),
    "observed_qualifier_discipline": (False, False, False, True),
}

LANDED_REGRESSIONS = {
    "host_marked_side_effect_class",
    "meta_eval_checker_routed_from_body",
    "meta_eval_receipt_schema_routed_from_body",
}


def git_blob_sha(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def red(message: str) -> int:
    print(f"SHADOW-REFACTOR-AB-RED {message}", file=sys.stderr)
    return 2


def score(body: str) -> dict[str, bool]:
    return {name: bool(predicate(body)) for name, predicate in STRENGTHS.items()}


def build_arms(body: str) -> dict[str, str]:
    """The Skill's own producer, with the body as the only free variable."""
    capsule = builder.delta_capsule()
    return {
        "A_NO_SKILL": "",
        "B_METADATA_ONLY": builder.metadata_only(body),
        "C_FULL_SKILL": body,
        "D_DELTA_CAPSULE": capsule,
        "E_DELTA_CAPSULE_PLUS_HARNESS": capsule + builder.harness_text(),
    }


def falsifiability_control() -> str | None:
    """A scorer that cannot go red scores nothing. Plant one loss and one gain."""
    body = OLD.read_text(encoding="utf-8")
    if not STRENGTHS["host_marked_side_effect_class"](body):
        return "control setup: the old canonical no longer carries the strength to remove"
    if STRENGTHS["host_marked_side_effect_class"](body.replace("marks side-effecting", "")):
        return "removing the side-effect class from A did not flip its criterion"
    if STRENGTHS["live_lane_routes"](body):
        return "control setup: the old canonical already carries the live lanes"
    if not STRENGTHS["live_lane_routes"](body + "\n".join(LIVE_LANES)):
        return "planting the live lanes into A did not flip its criterion"
    return None


def main() -> int:
    for path, expected in EXPECTED_GIT_BLOBS.items():
        observed = git_blob_sha(path.read_text(encoding="utf-8"))
        if observed != expected:
            return red(f"treatment drift {path.name}: expected={expected} observed={observed}")

    failure = falsifiability_control()
    if failure:
        return red(failure)

    bodies = {
        "A_OLD_CANONICAL": OLD.read_text(encoding="utf-8"),
        "B0_REFACTOR_AS_LANDED": LANDED.read_text(encoding="utf-8"),
        "B1_UPLIFT_ARMS_REPAIRED": UPLIFT.read_text(encoding="utf-8"),
        "B2_LIVE_LANES_REPAIRED": LIVE.read_text(encoding="utf-8"),
    }
    results = {name: score(body) for name, body in bodies.items()}

    for criterion, expected_row in EXPECTED.items():
        observed_row = tuple(results[name][criterion] for name in ORDER)
        if observed_row != expected_row:
            return red(
                f"old-strength matrix drift {criterion}: "
                f"expected={dict(zip(ORDER, expected_row))} "
                f"observed={dict(zip(ORDER, observed_row))}"
            )

    regressed = {
        criterion
        for criterion in STRENGTHS
        if results["A_OLD_CANONICAL"][criterion] and not results["B0_REFACTOR_AS_LANDED"][criterion]
    }
    if regressed != LANDED_REGRESSIONS:
        return red(f"landed regression set changed: {sorted(regressed)}")

    still_open = {
        criterion
        for criterion in LANDED_REGRESSIONS
        if not results["B2_LIVE_LANES_REPAIRED"][criterion]
    }

    # A relocated guarantee and a deleted one must not read the same.
    relocation = {}
    for criterion, (needle, filenames) in RELOCATED_TO.items():
        holders = [
            name for name in filenames
            if needle in (SKILL / name).read_text(encoding="utf-8")
        ]
        if not holders:
            return red(
                f"{criterion} left the body and is in none of {list(filenames)}: "
                "this is a deletion, not a relocation"
            )
        relocation[criterion] = holders

    scanned = {
        name: RETAINED_NON_CLAIM["needle"] in (SKILL / name).read_text(encoding="utf-8")
        for name in RETAINED_NON_CLAIM["scanned"]
    }
    if any(scanned.values()):
        return red(
            f"{RETAINED_NON_CLAIM['criterion']} is back in "
            f"{sorted(k for k, v in scanned.items() if v)}; update the retained non-claim"
        )

    # Every skills/ path the live body names has to resolve. A cross-Skill route
    # that does not is the same hollow route as an internal one, and this body
    # names two other Skills' artefacts.
    cited = sorted({
        match.rstrip(".,;:`)")
        for match in re.findall(r"skills/[A-Za-z0-9._/-]+", bodies["B2_LIVE_LANES_REPAIRED"])
        if "/" in match.rstrip(".,;:`)")[len("skills/"):]
    })
    unresolved = [value for value in cited if not (REPO / value).exists()]
    if unresolved:
        return red(f"the live body cites paths that do not resolve: {unresolved}")

    # Matched hermetic task: one builder, one capsule, one procedure set, four
    # bodies. Determinism first -- a producer that is not stable measures noise.
    arms = {name: build_arms(body) for name, body in bodies.items()}
    if any(build_arms(bodies[name]) != arms[name] for name in ORDER):
        return red("the arm producer is not deterministic across two builds on the same body")

    matched = {}
    for name in ORDER:
        digests = {arm: hashlib.sha256(text.encode()).hexdigest() for arm, text in arms[name].items()}
        if len(set(digests.values())) != len(digests):
            return red(f"{name}: the five arms are not pairwise distinct, so they separate nothing")
        body_bytes = len(arms[name]["C_FULL_SKILL"].encode())
        capsule_bytes = len(arms[name]["D_DELTA_CAPSULE"].encode())
        matched[name] = {
            "full_body_bytes": body_bytes,
            "capsule_bytes": capsule_bytes,
            "capsule_ratio_percent": round(100 * capsule_bytes / body_bytes, 1),
            "metadata_arm_digest": digests["B_METADATA_ONLY"][:12],
            "arm_set_digest": hashlib.sha256(
                json.dumps(sorted(digests.values())).encode()
            ).hexdigest()[:12],
        }

    invariant = {arms[name]["D_DELTA_CAPSULE"] for name in ORDER}
    if len(invariant) != 1:
        return red("the delta capsule is not body-invariant, so C vs D is not the treatment contrast")

    # The body states a measured ratio. It has to be the ratio of a body that
    # existed, or it is a number nobody can check.
    stated = re.search(r"capsule at ([0-9.]+)% of the full body", bodies["B2_LIVE_LANES_REPAIRED"])
    if not stated:
        return red("the live body no longer states the capsule ratio the arms are built to test")
    stated_value = float(stated.group(1))
    matches = [name for name in ORDER if matched[name]["capsule_ratio_percent"] == stated_value]
    if not matches:
        return red(
            f"the body states {stated_value}% but no frozen treatment measures it: "
            + str({name: matched[name]["capsule_ratio_percent"] for name in ORDER})
        )

    report = {
        "schema": "procedural-shadow-runtime/refactor-ab/v1",
        "issue": 350,
        "evidence_scope": "frozen body treatments and one deterministic offline arm build",
        "live_model_runtime_ab": "NOT_EXERCISED",
        "live_provider_or_host": "NOT_EXERCISED",
        "subjects": {
            "A_OLD_CANONICAL": EXPECTED_GIT_BLOBS[OLD],
            "B0_REFACTOR_AS_LANDED": EXPECTED_GIT_BLOBS[LANDED],
            "B1_UPLIFT_ARMS_REPAIRED": EXPECTED_GIT_BLOBS[UPLIFT],
            "B2_LIVE_LANES_REPAIRED": git_blob_sha(bodies["B2_LIVE_LANES_REPAIRED"]),
        },
        "results": results,
        "totals": {name: sum(values.values()) for name, values in results.items()},
        "landed_regressions": sorted(regressed),
        "landed_regressions_still_open_at_head": sorted(still_open),
        "relocated_not_deleted": relocation,
        "retained_non_claim": {
            "criterion": RETAINED_NON_CLAIM["criterion"],
            "state": "LOST_AND_OPEN",
            "scanned_files_without_it": sorted(scanned),
        },
        "cross_skill_paths_resolved": cited,
        "matched_hermetic_task": matched,
        "stated_capsule_ratio_percent": stated_value,
        "stated_ratio_matches_treatments": matches,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print(
        "SHADOW-REFACTOR-AB-GREEN four frozen bodies scored on 22 named guarantees "
        f"(A={report['totals']['A_OLD_CANONICAL']} B0={report['totals']['B0_REFACTOR_AS_LANDED']} "
        f"B1={report['totals']['B1_UPLIFT_ARMS_REPAIRED']} B2={report['totals']['B2_LIVE_LANES_REPAIRED']}); "
        f"the landed refactor's {len(regressed)} regressions are named and "
        f"{len(still_open)} are still open at HEAD; the arms are pairwise distinct per body "
        f"and the stated {stated_value}% ratio is the measured ratio of {', '.join(matches)}; "
        "live model/host A/B NOT_EXERCISED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
