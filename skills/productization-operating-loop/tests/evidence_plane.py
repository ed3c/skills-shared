#!/usr/bin/env python3
"""Shadow the whole Productization loop: one honest composition, one edit at a time.

`tests/selftest.py` replays each contract against itself, and the compiler's own
`--selftest` replays the compiler against itself. Neither asks the question this
file asks: when a false promotion is written into a composition, does *anything*
in the admitted stack refuse it by name, or does the loop compile it into a green
program? The answer turned out to be "both, depending on the promotion", and the
gaps are what this plane owns.

    Builder side, consumed read-only
        references/**/*.schema.json          eight frozen contracts
        scripts/compile_pol_composition.py   the composition compiler

    Shadow side, owned here
        tests/fixtures/evidence-plane-base.json   one composition that survives
                                                  every gate below
        the eight E-codes                         what the frozen stack does not
                                                  already refuse

Every planted control is the base with exactly one edit, so the base is the
knockout twin of all of them: if the base were red the whole plane would be a
checker that fails everything, and if an edit changes nothing the control is not
discriminating. Both are asserted on every run.

Where the refusal comes from
----------------------------
A case declares the code it expects and the guard it expects to be refused by,
and both must match. "Something went wrong" is not a detection: a plane that
reports one generic failure for fourteen different promotions cannot tell a
market-attention laundering from a dropped payment denominator.

    INPUT stage    the four lane artifacts are validated against their own frozen
                   contracts before the compiler sees them, and then the compiler
                   runs. The compiler checks a lane artifact's `schema` string and
                   its `subject_commit` and nothing else, so a lane artifact its
                   own contract refuses composes today; E01 is that gap.
    OUTPUT stage   the six compiled artifacts are re-validated after a downstream
                   edit, which is the real laundering path: nothing in the stack
                   re-reads a document somebody edited after it was compiled.
    REOPEN pass    the plane's own gates, run over the compiled artifacts, asking
                   what a first green does not: which lane was skipped, which
                   cleared cell rests on no rung, which failed attempt left the
                   denominator, which subject is stale.

Refusal codes owned here (the K-codes belong to the compiler)
-------------------------------------------------------------
    E01_LANE_CONTRACT_REFUSED_THE_ARTIFACT   a lane artifact its own contract
                                             refuses, admitted into a composition
    E02_COMPILED_ARTIFACT_REFUSED_BY_ITS_CONTRACT
                                             a compiled document edited after the
                                             fact into something its contract refuses
    E03_PASS_CELL_WITHOUT_AN_EARNED_RUNG     hollow: providers present, a cell
                                             cleared, and no rung under it
    E04_LANE_STATE_ABOVE_ITS_LADDER          a lane reported PASS whose own rungs
                                             are not REACHED
    E05_FIRST_GREEN_HID_A_SKIPPED_LANE       a lane nobody entered, recorded by no
                                             cell and no read-back question
    E06_ATTEMPT_DROPPED_FROM_DENOMINATOR     a prior failed or blocked attempt that
                                             is no longer anywhere in the matrix
    E07_STALE_SUBJECT_REUSED                 a receipt or a canonical subject bound
                                             to a commit that is not the subject
    E08_PROJECTION_READBACK_WITHOUT_COMPARISON
                                             a projection reported read back with
                                             nothing compared

The plane keeps its own rung-to-lane map rather than importing the compiler's. A
shared map is one edit away from promoting a lane in both places at once; two maps
mean a widened compiler map shows up here as a lane whose PASS this file cannot
account for.

Evidence ceiling: mutation sensitivity and closure semantics on committed bytes.
Nothing here observes a user, a payment, a market or a live provider, and no case
below is evidence that the product is wanted.

Exit 0 green, 2 a control failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Callable, NamedTuple, NoReturn

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "POL-PLANE-UNUSABLE: jsonschema is required. This plane executes the "
        "committed contracts as deciding gates; skipping them would report the "
        "same green as running them.",
        file=sys.stderr,
    )
    raise SystemExit(70)

SKILL = Path(__file__).resolve().parents[1]
SKILLS = SKILL.parent
REFERENCES = SKILL / "references"
FIXTURE = SKILL / "tests" / "fixtures" / "evidence-plane-base.json"
CASES = SKILL / "cases.json"

sys.path.insert(0, str(SKILL / "scripts"))
from compile_pol_composition import Refused, Unusable, compile_all  # noqa: E402

# The six compiled artifacts and the contract that owns each. Two of them live in
# the Reverse loop, which is where those two shapes were admitted.
OUTPUT_CONTRACTS = {
    "program": REFERENCES / "productization-program.schema.json",
    "closure-matrix": REFERENCES / "session" / "closure-matrix.schema.json",
    "session-dag": REFERENCES / "session" / "session-dag.schema.json",
    "outcome-foldback": REFERENCES / "session" / "outcome-foldback-request.schema.json",
    "dispatch-request": SKILLS
    / "product-reverse-engineering-loop"
    / "references"
    / "session-dispatch-request.schema.json",
    "external-projections": SKILLS
    / "product-reverse-engineering-loop"
    / "references"
    / "external-projection-registry.schema.json",
}

LANE_CONTRACTS = {
    "market": REFERENCES / "market" / "market-lane.schema.json",
    "user": REFERENCES / "user" / "user-lane.schema.json",
    "commercial": REFERENCES / "commercial" / "commercial-lane.schema.json",
    "policy": REFERENCES / "policy" / "policy-lane.schema.json",
}

# Restated here on purpose; see the module docstring. A lane absent from this map
# raises no rung and is exempt from E03 and E04, because the question "which rung
# did policy reach" has no answer rather than a negative one.
PLANE_LANE_RUNGS: dict[str, tuple[str, ...]] = {
    "source": ("source_found", "source_verified"),
    "market": ("job_supported", "wedge_supported"),
    "mechanism": ("mechanism_reproduced",),
    "technical": ("mvp_tech_verified",),
    "runtime": ("live_workflow_verified",),
    "user": ("user_validated",),
    "commercial": ("paid_validated", "repeatable_commercial"),
}
LANE_OF_CELL = {name.upper(): name for name in PLANE_LANE_RUNGS}
OPEN_ATTEMPT_STATES = {"FAILED", "BLOCKED"}


def fatal(reason: str) -> NoReturn:
    """The plane itself cannot run: a missing contract, an absent base, a control
    that names nothing. Exits where the absence is found rather than raising, so
    that an absence during module setup is still a named exit 2 and not a
    traceback at exit 1 that nobody reads as a refusal."""
    print(f"POL-PLANE-RED {reason}", file=sys.stderr)
    raise SystemExit(2)


class Refusal(NamedTuple):
    code: str
    refused_by: str
    detail: str


class Report(NamedTuple):
    refusals: tuple[Refusal, ...]
    first_green: bool
    compiled: bool


def codes(refusals: tuple[Refusal, ...]) -> list[str]:
    return [item.code for item in refusals]


# --------------------------------------------------------------------------
# the base composition
# --------------------------------------------------------------------------


def load_contracts() -> tuple[dict[Path, Draft202012Validator], dict[Path, str]]:
    built: dict[Path, Draft202012Validator] = {}
    identities: dict[Path, str] = {}
    for path in set(OUTPUT_CONTRACTS.values()) | set(LANE_CONTRACTS.values()):
        if not path.is_file():
            fatal(f"contract {path} is not on the tree; the plane has nothing to decide with")
        document = json.loads(path.read_text(encoding="utf-8"))
        identity = document.get("properties", {}).get("schema", {}).get("const")
        if not isinstance(identity, str):
            fatal(f"{path.name} has no properties.schema.const, so no refusal can name it")
        built[path] = Draft202012Validator(document)
        identities[path] = identity
    return built, identities


VALIDATORS, IDENTITIES = load_contracts()


def contract_refusals(document: Any, path: Path, code: str, subject: str) -> list[Refusal]:
    """Every guard in `path` that refuses `document`, named by its own keyword path."""
    found: list[Refusal] = []
    for error in VALIDATORS[path].iter_errors(document):
        keyword = "/".join(str(part) for part in error.absolute_schema_path)
        found.append(
            Refusal(code, f"{IDENTITIES[path]}#{keyword}", f"{subject}: {error.message[:160]}")
        )
    return found


def load_base() -> dict[str, Any]:
    if not FIXTURE.is_file():
        fatal(f"the base composition {FIXTURE} is absent; every control is one edit of it")
    base = json.loads(FIXTURE.read_text(encoding="utf-8"))
    artifacts: dict[str, Any] = {}
    for lane, binding in base["lane_examples"].items():
        path = REFERENCES / binding["schema_path"]
        if not path.is_file():
            fatal(f"{lane}: the lane contract {path} is absent")
        document = json.loads(path.read_text(encoding="utf-8"))
        examples = document.get("examples") or []
        if not examples:
            fatal(f"{lane}: {path.name} carries no example, so the base has no admitted bytes")
        artifacts[lane] = {**copy.deepcopy(examples[0]), **binding["patch"]}
    base["composition"]["lane_artifacts"] = artifacts
    return base


BASE = load_base()
SUBJECT = BASE["subject_commit"]
STALE = BASE["stale_commit"]


def draft() -> dict[str, Any]:
    return copy.deepcopy(BASE["composition"])


def attempts() -> list[dict[str, Any]]:
    return copy.deepcopy(BASE["prior_attempts"])


# --------------------------------------------------------------------------
# the reopen pass: what a first green does not ask
# --------------------------------------------------------------------------


def reopen(built: dict[str, dict], prior: list[dict]) -> list[Refusal]:
    program = built["program"]
    matrix = built["closure-matrix"]
    foldback = built["outcome-foldback"]
    registry = built["external-projections"]
    ladder = program["evidence_ladder"]
    found: list[Refusal] = []

    def reached(lane: str) -> bool:
        return any(ladder[rung]["state"] == "REACHED" for rung in PLANE_LANE_RUNGS[lane])

    # E03 -- hollow. Providers can all be present and every slot filled while no
    # rung under a cleared cell was ever reached; that cell is a claim about the
    # world resting on a document that says nothing happened.
    for cell in matrix["cells"]:
        lane = LANE_OF_CELL.get(cell["lane"])
        if cell["state"] == "PASS" and lane and not reached(lane):
            found.append(
                Refusal(
                    "E03_PASS_CELL_WITHOUT_AN_EARNED_RUNG",
                    "reopen pass over the closure matrix and the evidence ladder",
                    f"{cell['cell_id']} is PASS in the {cell['lane']} lane and no rung of that "
                    f"lane is REACHED",
                )
            )

    # E04 -- a lane cleared above its own ladder. The compiler copies the market
    # and user lane states verbatim from their artifacts and derives the rest, so
    # both an artifact that overclaims and a later edit land here. A lane that is
    # missing entirely is already an E02 against the program contract, which
    # requires all twelve; reading it here would crash instead of reporting.
    for lane, rungs in PLANE_LANE_RUNGS.items():
        state = program["lanes"].get(lane)
        if state is None:
            continue
        if state["state"] == "PASS" and not reached(lane):
            found.append(
                Refusal(
                    "E04_LANE_STATE_ABOVE_ITS_LADDER",
                    "reopen pass over the program lanes and the evidence ladder",
                    f"lane {lane} is PASS while none of {list(rungs)} is REACHED",
                )
            )

    # E05 -- the skipped lane. A lane nobody entered is a fact, and a composition
    # is entitled to report it; what it is not entitled to do is leave it out of
    # every cell and every read-back question, which is how a first green stays
    # green while a lane quietly never happened.
    recorded = {cell["lane"] for cell in matrix["cells"]}
    recorded |= {question["lane"] for question in foldback["read_back_questions"]}
    for lane in PLANE_LANE_RUNGS:
        row = program["lanes"].get(lane)
        if row is not None and row["state"] == "NOT_EXERCISED" and lane.upper() not in recorded:
            found.append(
                Refusal(
                    "E05_FIRST_GREEN_HID_A_SKIPPED_LANE",
                    "reopen pass over the program lanes, the matrix and the foldback questions",
                    f"lane {lane} was never entered and no cell or read-back question records it",
                )
            )

    # E06 -- the denominator. A failed or blocked attempt is the most useful row
    # in the ledger and the cheapest one to lose, because losing it looks exactly
    # like never having attempted.
    present = {cell["cell_id"] for cell in matrix["cells"]}
    unresolved = set(matrix["unresolved_cell_ids"])
    for attempt in prior:
        if attempt["state"] not in OPEN_ATTEMPT_STATES:
            continue
        cell_id = attempt["cell_id"]
        if cell_id not in present:
            found.append(
                Refusal(
                    "E06_ATTEMPT_DROPPED_FROM_DENOMINATOR",
                    "reopen pass over the prior attempt ledger and the closure matrix",
                    f"{attempt['attempt_id']} is {attempt['state']} on {cell_id}, and {cell_id} "
                    f"is not in the matrix at all",
                )
            )
        elif cell_id not in unresolved:
            found.append(
                Refusal(
                    "E06_ATTEMPT_DROPPED_FROM_DENOMINATOR",
                    "reopen pass over the prior attempt ledger and the closure matrix",
                    f"{attempt['attempt_id']} is {attempt['state']} on {cell_id}, and {cell_id} "
                    f"is no longer counted as unresolved",
                )
            )

    # E07 -- the stale subject. The compiler carries a receipt's own
    # subject_commit into the ladder without comparing it to the program subject,
    # so a receipt earned at an older head raises a rung here today.
    for rung, row in ladder.items():
        for receipt in row["receipts"]:
            if receipt.get("subject_commit") != program["subject_commit"]:
                found.append(
                    Refusal(
                        "E07_STALE_SUBJECT_REUSED",
                        "reopen pass over the evidence ladder receipts",
                        f"the {rung} receipt is bound to {receipt.get('subject_commit')!r}, not to "
                        f"the program subject",
                    )
                )
    for entry in registry["entries"]:
        for subject in entry["canonical_subjects"]:
            if subject.get("commit") != program["subject_commit"]:
                found.append(
                    Refusal(
                        "E07_STALE_SUBJECT_REUSED",
                        "reopen pass over the external projection canonical subjects",
                        f"{entry['id']} projects {subject.get('path')} at "
                        f"{subject.get('commit')!r}, not at the program subject",
                    )
                )

    # E08 -- the projection read back against nothing. The registry contract
    # admits PASS beside three nulls, because it cannot know whether a comparison
    # happened; the plane can, and a state that settles a comparison nobody made
    # is a write reported as a confirmation.
    for entry in registry["entries"]:
        back = entry["read_back"]
        if back["state"] in {"PASS", "FAIL"} and (
            back["compared_revision"] is None or back["compared_digest"] is None
        ):
            found.append(
                Refusal(
                    "E08_PROJECTION_READBACK_WITHOUT_COMPARISON",
                    "reopen pass over the external projection read-back states",
                    f"{entry['id']} reports read_back {back['state']} with nothing compared",
                )
            )
    return found


# --------------------------------------------------------------------------
# one adjudication
# --------------------------------------------------------------------------


def adjudicate(
    composition: dict[str, Any],
    prior: list[dict],
    edit_output: Callable[[dict[str, dict]], None] | None = None,
) -> Report:
    found: list[Refusal] = []

    for lane, path in LANE_CONTRACTS.items():
        artifact = composition.get("lane_artifacts", {}).get(lane)
        if artifact is None:
            continue  # absence is the compiler's K02, not a contract question
        found.extend(
            contract_refusals(
                artifact, path, "E01_LANE_CONTRACT_REFUSED_THE_ARTIFACT", f"lane {lane}"
            )
        )

    try:
        built = compile_all(composition)
    except Refused as refusal:
        code = str(refusal).split()[0]
        found.append(Refusal(code, "scripts/compile_pol_composition.py", str(refusal)[:200]))
        return Report(tuple(found), first_green=False, compiled=False)
    except Unusable as error:
        found.append(
            Refusal(
                "POL-COMPILE-UNUSABLE",
                "scripts/compile_pol_composition.py",
                str(error)[:200],
            )
        )
        return Report(tuple(found), first_green=False, compiled=False)

    # Everything the admitted stack decides has now decided. Whatever is found
    # below this line was green a moment ago.
    first_green = not found
    if edit_output is not None:
        edit_output(built)

    for name, path in OUTPUT_CONTRACTS.items():
        found.extend(
            contract_refusals(
                built[name], path, "E02_COMPILED_ARTIFACT_REFUSED_BY_ITS_CONTRACT", name
            )
        )
    found.extend(reopen(built, prior))
    return Report(tuple(found), first_green=first_green, compiled=True)


# --------------------------------------------------------------------------
# the planted controls
# --------------------------------------------------------------------------


def lane_control(schema_path: str, case_id: str, lane: str) -> Callable[[dict], None]:
    """Swap in the lane contract's own refusal-control instance, rebound to the subject.

    The false promotion is not written here: it is the one the contract authors
    froze into the schema, replayed through a composition. A control written from
    scratch would be a string built to fail; this one is admitted bytes.
    """

    document = json.loads((REFERENCES / schema_path).read_text(encoding="utf-8"))
    matches = [
        control
        for control in document.get("x-refusal-controls", [])
        if control.get("case_id") == case_id
    ]
    if len(matches) != 1:
        fatal(f"{schema_path}: expected exactly one control named {case_id}, found {len(matches)}")
    instance = copy.deepcopy(matches[0]["instance"])

    def apply(composition: dict) -> None:
        composition["lane_artifacts"][lane] = {**instance, "subject_commit": SUBJECT}

    return apply


# The fourteen false promotions preregistered in the issue, in its words. This is
# the denominator: a control that quietly stops being planted is a promotion that
# quietly stops being refused, and the two are indistinguishable from a green run
# unless the list is written down before the cases are.
PREREGISTERED = (
    "market attention -> demand",
    "feature delta -> differentiation wedge",
    "pain -> willingness to switch",
    "interest -> user validation",
    "one payment -> repeatable business",
    "consumer subscription -> API entitlement",
    "policy page -> legal/rights clearance",
    "technical PASS -> user/paid PASS",
    "projection write -> canonical completion",
    "prompt packet -> Session observed",
    "bootstrap PASS -> Agent/provider PASS",
    "first green hides skipped lanes",
    "stale policy/source/PR receipt reused",
    "failed/blocked attempt removed from denominator",
)
# Not preregistered in the issue's list, required by it in the same breath: a
# composition where every provider is present and no evidence is.
UNPREREGISTERED = ("hollow evidence",)


class Control(NamedTuple):
    control_id: str          # the false promotion this case plants, in the issue's words
    case_id: str
    promotion: str
    stage: str               # INPUT or OUTPUT
    expect_code: str
    expect_refused_by: str
    edit_input: Callable[[dict], None] | None
    edit_output: Callable[[dict[str, dict]], None] | None


def _stale_source_receipt(composition: dict) -> None:
    composition["receipts"][0]["subject_commit"] = STALE


def _stale_projection_subject(composition: dict) -> None:
    composition["projections"][0]["canonical_subjects"][0]["commit"] = STALE


def _drop_cell(cell_id: str) -> Callable[[dict], None]:
    def apply(composition: dict) -> None:
        before = len(composition["closure_cells"])
        composition["closure_cells"] = [
            cell for cell in composition["closure_cells"] if cell["cell_id"] != cell_id
        ]
        if len(composition["closure_cells"]) != before - 1:
            fatal(f"the base carries no cell {cell_id}, so this control edits nothing")

    return apply


def _hollow(composition: dict) -> None:
    """Providers present, evidence absent: four lane artifacts, two method refs,
    one projection, five cells -- and not one receipt under any of it."""
    composition["receipts"] = []


def _promote_user_rung(composition: dict) -> None:
    composition["lane_artifacts"]["user"]["highest_rung_reached"] = "USER_VALIDATED"


def _projection_claims_completion(composition: dict) -> None:
    composition["projections"][0]["authority"] = {"completion": True}


def _paid_reached_on_a_command_exit(built: dict[str, dict]) -> None:
    built["program"]["evidence_ladder"]["paid_validated"] = {
        "state": "REACHED",
        "receipts": [{"kind": "DETERMINISTIC_COMMAND_EXIT", "subject_commit": SUBJECT}],
    }


def _dag_claims_observed_sessions(built: dict[str, dict]) -> None:
    built["session-dag"]["observed_sessions"] = [
        {"node_id": "POL-ATOM-001", "state": "SESSION_OBSERVED"}
    ]


def _runtime_lane_passes_on_a_bootstrap(built: dict[str, dict]) -> None:
    built["program"]["lanes"]["runtime"] = {
        "state": "PASS",
        "highest_rung_reached": "LIVE_WORKFLOW_VERIFIED",
    }


def _projection_read_back_passes(built: dict[str, dict]) -> None:
    built["external-projections"]["entries"][0]["read_back"] = {
        "state": "PASS",
        "compared_revision": None,
        "compared_digest": None,
        "observed_at": None,
    }


CONTROLS: tuple[Control, ...] = (
    Control(
        "market attention -> demand",
        "market-attention-as-demand",
        "an attention signal filed against a slot that says somebody switched or paid",
        "INPUT",
        "E01_LANE_CONTRACT_REFUSED_THE_ARTIFACT",
        "pol/market-lane/v1#properties/market_arena/properties/arena_signals/items/allOf/0/then/properties/supports/enum",
        lane_control("market/market-lane.schema.json", "POL-XC-MKT-001", "market"),
        None,
    ),
    Control(
        "feature delta -> differentiation wedge",
        "feature-difference-as-wedge",
        "a difference measured against a product carried as a live wedge hypothesis",
        "INPUT",
        "E01_LANE_CONTRACT_REFUSED_THE_ARTIFACT",
        "pol/market-lane/v1#properties/wedge_hypothesis/allOf/0/then/properties/wedge_state/const",
        lane_control("market/market-lane.schema.json", "POL-XC-MKT-002", "market"),
        None,
    ),
    Control(
        "pain -> willingness to switch",
        "pain-as-willingness-to-switch",
        "a reported pain about the incumbent filed as a confirmed switch",
        "INPUT",
        "E01_LANE_CONTRACT_REFUSED_THE_ARTIFACT",
        "pol/user-lane/v1#properties/switching_cost/allOf/0/then/properties/evidence/properties/kind/enum",
        lane_control("user/user-lane.schema.json", "POL-XC-USER-001", "user"),
        None,
    ),
    Control(
        "interest -> user validation",
        "interest-as-adoption",
        "an expressed-interest signal filed as observed adoption",
        "INPUT",
        "E01_LANE_CONTRACT_REFUSED_THE_ARTIFACT",
        "pol/user-lane/v1#properties/adoption_status/allOf/0/then/properties/evidence/properties/kind/const",
        lane_control("user/user-lane.schema.json", "POL-XC-USER-002", "user"),
        None,
    ),
    Control(
        "one payment -> repeatable business",
        "one-payment-as-repeatable-business",
        "a repeatable commercial claim resting on fewer than two distinct payments",
        "INPUT",
        "E01_LANE_CONTRACT_REFUSED_THE_ARTIFACT",
        "pol/commercial-lane/v1#properties/repeatable_commercial_claim/allOf/0/then/properties/distinct_payment_events/minItems",
        lane_control("commercial/commercial-lane.schema.json", "POL-XC-CL-002", "commercial"),
        None,
    ),
    Control(
        "consumer subscription -> API entitlement",
        "consumer-subscription-as-api-entitlement",
        "a consumer subscription asserted to grant the API entitlement",
        "INPUT",
        "E01_LANE_CONTRACT_REFUSED_THE_ARTIFACT",
        "pol/commercial-lane/v1#properties/existing_subscription_leverage/additionalProperties",
        lane_control("commercial/commercial-lane.schema.json", "POL-XC-CL-005", "commercial"),
        None,
    ),
    Control(
        "policy page -> legal/rights clearance",
        "policy-diff-as-legal-clearance",
        "a mechanical diff between two policy revisions filed as a legal clearance",
        "INPUT",
        "E01_LANE_CONTRACT_REFUSED_THE_ARTIFACT",
        "pol/policy-lane/v1#properties/authority/properties/legal_clearance/const",
        lane_control("policy/policy-lane.schema.json", "POL-XC-PL-005", "policy"),
        None,
    ),
    Control(
        "technical PASS -> user/paid PASS",
        "technical-exit-as-user-validation",
        "a user lane claiming USER_VALIDATED when the only receipt is a command exit",
        "INPUT",
        "K08_RUNG_PROMOTED_ABOVE_RECEIPTS",
        "scripts/compile_pol_composition.py",
        _promote_user_rung,
        None,
    ),
    Control(
        "technical PASS -> user/paid PASS",
        "command-exit-as-payment-receipt",
        "a compiled ladder edited to report paid_validated REACHED on a command exit",
        "OUTPUT",
        "E02_COMPILED_ARTIFACT_REFUSED_BY_ITS_CONTRACT",
        "pol/productization-program/v1#properties/evidence_ladder/allOf/8/then/properties/paid_validated/properties/receipts/contains",
        None,
        _paid_reached_on_a_command_exit,
    ),
    Control(
        "projection write -> canonical completion",
        "projection-claims-completion-authority",
        "a projection entry asserting completion authority for the canonical subject",
        "INPUT",
        "K04_AUTHORITY_WIDENING",
        "scripts/compile_pol_composition.py",
        _projection_claims_completion,
        None,
    ),
    Control(
        "projection write -> canonical completion",
        "projection-read-back-without-comparison",
        "a projection reported read back PASS with no revision and no digest compared",
        "OUTPUT",
        "E08_PROJECTION_READBACK_WITHOUT_COMPARISON",
        "reopen pass over the external projection read-back states",
        None,
        _projection_read_back_passes,
    ),
    Control(
        "prompt packet -> Session observed",
        "dispatch-graph-claims-observed-sessions",
        "a requested-packet graph edited to report that its sessions were observed",
        "OUTPUT",
        "E02_COMPILED_ARTIFACT_REFUSED_BY_ITS_CONTRACT",
        "pol/session-dag/v1#properties/observed_sessions/const",
        None,
        _dag_claims_observed_sessions,
    ),
    Control(
        "bootstrap PASS -> Agent/provider PASS",
        "bootstrap-exit-as-provider-execution",
        "the runtime lane cleared to PASS while no live workflow trace exists",
        "OUTPUT",
        "E04_LANE_STATE_ABOVE_ITS_LADDER",
        "reopen pass over the program lanes and the evidence ladder",
        None,
        _runtime_lane_passes_on_a_bootstrap,
    ),
    Control(
        "first green hides skipped lanes",
        "skipped-runtime-lane-unrecorded",
        "the one cell that recorded an unentered lane, removed",
        "INPUT",
        "E05_FIRST_GREEN_HID_A_SKIPPED_LANE",
        "reopen pass over the program lanes, the matrix and the foldback questions",
        _drop_cell("POL-CELL-004"),
        None,
    ),
    Control(
        "stale policy/source/PR receipt reused",
        "stale-policy-terminal-reused",
        "a policy record composed while its own terminal says it was superseded",
        "INPUT",
        "K01_STALE_LANE_ARTIFACT",
        "scripts/compile_pol_composition.py",
        lambda composition: composition["lane_artifacts"]["policy"].update(
            {"terminal": "SUPERSEDED"}
        ),
        None,
    ),
    Control(
        "stale policy/source/PR receipt reused",
        "stale-source-receipt-reused",
        "a source receipt earned at an older head, reused to raise a rung here",
        "INPUT",
        "E07_STALE_SUBJECT_REUSED",
        "reopen pass over the evidence ladder receipts",
        _stale_source_receipt,
        None,
    ),
    Control(
        "stale policy/source/PR receipt reused",
        "stale-projection-subject-reused",
        "a projection still naming the canonical subject at the commit before this one",
        "INPUT",
        "E07_STALE_SUBJECT_REUSED",
        "reopen pass over the external projection canonical subjects",
        _stale_projection_subject,
        None,
    ),
    Control(
        "failed/blocked attempt removed from denominator",
        "blocked-attempt-removed-from-matrix",
        "the cell carrying a blocked prior attempt, removed from the composition",
        "INPUT",
        "E06_ATTEMPT_DROPPED_FROM_DENOMINATOR",
        "reopen pass over the prior attempt ledger and the closure matrix",
        _drop_cell("POL-CELL-005"),
        None,
    ),
    Control(
        "hollow evidence",
        "hollow-providers-no-receipts",
        "four lane artifacts, two method refs, one projection, five cells, no receipt",
        "INPUT",
        "E03_PASS_CELL_WITHOUT_AN_EARNED_RUNG",
        "reopen pass over the closure matrix and the evidence ladder",
        _hollow,
        None,
    ),
)


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------


def reconcile_cases(ran: list[str]) -> list[str]:
    """cases.json is the declared inventory; this run is the actual one."""
    if not CASES.is_file():
        return [f"{CASES.name} is absent; the planted inventory cannot be reconciled"]
    try:
        document = json.loads(CASES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{CASES.name} is unreadable, which is not the same fact as declaring nothing: {error}"]
    declared = document.get("planted_controls")
    if not isinstance(declared, list) or not declared:
        return [f"{CASES.name}: planted_controls must be a non-empty array"]
    problems = []
    for name in sorted(set(declared) - set(ran)):
        problems.append(f"{CASES.name} declares {name!r}, and no control by that name ran")
    for name in sorted(set(ran) - set(declared)):
        problems.append(f"control {name!r} ran and {CASES.name} does not declare it")
    if len(declared) != len(set(declared)):
        problems.append(f"{CASES.name}: planted_controls repeats a name")
    return problems


def main() -> int:
    failures: list[str] = []

    base = adjudicate(draft(), attempts())
    if base.refusals:
        for refusal in base.refusals:
            failures.append(
                f"the base composition is refused by {refusal.code} ({refusal.refused_by}): "
                f"{refusal.detail}. Every control is one edit of this base, so a red base makes "
                f"the whole plane a checker that fails everything"
            )

    first_green = 0
    plane_codes: set[str] = set()
    compiler_codes: set[str] = set()
    ran: list[str] = []

    for control in CONTROLS:
        ran.append(control.case_id)
        composition = draft()
        if control.edit_input is not None:
            control.edit_input(composition)
        report = adjudicate(composition, attempts(), control.edit_output)
        matched = [
            refusal
            for refusal in report.refusals
            if refusal.code == control.expect_code
            and refusal.refused_by.startswith(control.expect_refused_by)
        ]
        if not matched:
            failures.append(
                f"{control.case_id}: expected {control.expect_code} from "
                f"{control.expect_refused_by}, got {sorted(set(codes(report.refusals))) or 'a green run'}"
            )
            continue
        if control.stage == "OUTPUT" and not report.compiled:
            failures.append(f"{control.case_id}: an OUTPUT control never reached a compiled artifact")
        if report.first_green:
            first_green += 1
        if control.expect_code.startswith("K") or control.expect_code == "POL-COMPILE-UNUSABLE":
            compiler_codes.add(control.expect_code)
        else:
            plane_codes.add(control.expect_code)

    failures.extend(reconcile_cases(ran))

    planted = {control.control_id for control in CONTROLS}
    for promotion in PREREGISTERED:
        if promotion not in planted:
            failures.append(
                f"the preregistered promotion {promotion!r} has no planted case; an unplanted "
                f"control is a promotion nothing refuses"
            )
    for promotion in sorted(planted - set(PREREGISTERED) - set(UNPREREGISTERED)):
        failures.append(
            f"a case plants {promotion!r}, which is neither preregistered nor declared "
            f"unpreregistered; the denominator is fixed before the cases, not by them"
        )

    print(
        f"subject={SKILL} preregistered_promotions={len(PREREGISTERED)} "
        f"other_promotions={len(UNPREREGISTERED)} planted_cases={len(CONTROLS)} "
        f"first_green_reopened={first_green} plane_codes={len(plane_codes)} "
        f"compiler_codes={len(compiler_codes)} contracts={len(OUTPUT_CONTRACTS)} "
        f"lane_contracts={len(LANE_CONTRACTS)}"
    )
    if failures:
        for item in failures:
            print(f"POL-PLANE-RED {item}", file=sys.stderr)
        return 2
    print(
        f"POL-PLANE-GREEN the base composition passes every gate, {len(CONTROLS)} planted cases "
        f"covering all {len(PREREGISTERED)} preregistered false promotions and "
        f"{len(UNPREREGISTERED)} hollow case are each refused by the exact guard they name, and "
        f"{first_green} of them were green to the admitted stack until the reopen pass"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
