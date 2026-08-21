#!/usr/bin/env python3
"""Decide one portfolio control bundle and emit a byte-stable verdict.

    ghpc/portfolio-bundle/v1
      epoch        ghpc/portfolio-epoch/v1
      join         ghpc/subagent-join/v1
      ci_epoch     ghpc/one-shot-ci-epoch/v1
      composition  ghpc/authority-composition/v1
        -> ghpc/portfolio-control-verdict/v1

Each member is judged first by its own schema in `references/schemas/`. What
this file adds is the nine contradictions no single member can see, because
each of them needs two documents to be visible at once: an epoch and a join
bound to different subjects both look fine alone.

What this checker is not allowed to do
--------------------------------------
It makes no network call and opens no socket -- `--selftest` reads this file's
own import statements and asserts that not one of them names a network module,
because the one thing a portfolio controller must never do is fetch the state
it is supposed to have been handed.
It has no clock, so nothing it writes carries a time this file invented. And it
decides nothing semantic: a green verdict says the bundle does not contradict
itself, never that the work is right, that the PR should merge, or that a
hosted run means anything beyond having executed.

Refusal codes (exit 2)
----------------------
    K01_MIXED_SNAPSHOT_EPOCH             a member bound to a different subject
                                         than the epoch's own commit and tree
    K02_JOIN_INCOMPLETE_ADVANCE          a portfolio state at or past
                                         ALL_REQUIRED_AGENTS_TERMINAL, or an
                                         advanced transition, while a requested
                                         agent is still DISPATCHED or RUNNING
    K03_SUPERSEDED_EPOCH_NOT_SUPERSEDED  a retired epoch whose subject equals
                                         the current one, or whose delta does
                                         not start at the subject it retired
    K04_AUTHORITY_ROUTE_ABSENT           a composed authority routed at a path
                                         that is not on this tree
    K05_COORDINATOR_INSTRUCTION_ALTERED  the join's instruction differs from the
                                         pinned bytes at the routed data file
    K06_CI_EPOCH_NOT_EXACT_HEAD          a hosted receipt whose tested head is
                                         not the candidate head, or an equality
                                         attestation the two digests contradict
    K07_REQUIRED_ROLE_MISSING            a required role with no requested agent
    K08_SHAPE_EXAMPLE_USED_AS_RECEIPT    a reserved 900-999 identifier inside a
                                         bundle that is not a schema example
    K09_OVERLAPPING_EXCLUSIVE_LEASE      two exclusive writers over paths that
                                         are not disjoint

Path overlap in K09 is compared conservatively: a trailing `/**` is stripped and
two leases collide when one path equals the other or is nested under it at a
segment boundary. A pattern this comparison cannot decide -- a `*` anywhere
other than a trailing `/**` -- is reported as a collision rather than assumed
disjoint, because assuming disjoint is the failure the check exists to catch.

Exits: 0 green, 2 refused with a named code, 64 the input is unusable, 70
`--selftest` cannot run because jsonschema is absent.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
DEFAULT_REFERENCES = SKILL / "references"

BUNDLE_SCHEMA = "ghpc/portfolio-bundle/v1"
VERDICT_SCHEMA = "ghpc/portfolio-control-verdict/v1"
MEMBERS = {
    "epoch": "ghpc/portfolio-epoch/v1",
    "join": "ghpc/subagent-join/v1",
    "ci_epoch": "ghpc/one-shot-ci-epoch/v1",
    "composition": "ghpc/authority-composition/v1",
}
CODES = (
    "K01_MIXED_SNAPSHOT_EPOCH",
    "K02_JOIN_INCOMPLETE_ADVANCE",
    "K03_SUPERSEDED_EPOCH_NOT_SUPERSEDED",
    "K04_AUTHORITY_ROUTE_ABSENT",
    "K05_COORDINATOR_INSTRUCTION_ALTERED",
    "K06_CI_EPOCH_NOT_EXACT_HEAD",
    "K07_REQUIRED_ROLE_MISSING",
    "K08_SHAPE_EXAMPLE_USED_AS_RECEIPT",
    "K09_OVERLAPPING_EXCLUSIVE_LEASE",
)
PORTFOLIO_STATES = (
    "REQUEST_BOUND",
    "RUNTIME_AND_AUTHORITY_ADMITTED",
    "REPOSITORY_SET_FROZEN",
    "GITHUB_SNAPSHOT_EPOCH_BOUND",
    "ISSUE_PR_DENOMINATOR_COMPLETE",
    "ACCEPTANCE_CONTRACTS_COMPILED",
    "ADVERSARIAL_DRIFT_AUDITED",
    "MULTI_GRAPH_MODEL_ASSERTED",
    "READY_WAVES_COMPUTED",
    "SUBAGENTS_DISPATCHED",
    "ALL_REQUIRED_AGENTS_TERMINAL",
    "RESULTS_SCHEMA_VALIDATED",
    "FINDINGS_CONSOLIDATED",
    "LOCAL_WORKTREES_EXECUTED",
    "EXACT_HEAD_LOCAL_GATES_PASS",
    "DRAFT_PUBLICATION",
    "ONE_SHOT_CI_EPOCH",
    "CI_JOBS_STEPS_ARTIFACTS_READ_BACK",
    "PR_ACCEPTANCE_RECONCILED",
    "READY_FOR_HUMAN_ADMIT",
    "MERGE_IN_TRUE_DEPENDENCY_ORDER",
    "EXACT_MAIN_READBACK",
    "ISSUE_CLOSURE_RECONCILED",
    "PORTFOLIO_EPOCH_CLOSED",
)
BARRIER = PORTFOLIO_STATES.index("ALL_REQUIRED_AGENTS_TERMINAL")
NON_TERMINAL = ("DISPATCHED", "RUNNING")
RESERVED_BLOCK = range(900, 1000)
AUTHORITY = {
    "merge": False,
    "release": False,
    "promotion": False,
    "provider_execution": False,
    "production": False,
}
HUMAN_OWNED = (
    "admitting a composed authority kind",
    "closing an Issue against unresolved acceptance",
    "merge and release",
)
NETWORK_MODULES = ("socket", "urllib", "requests", "http.client", "httpx", "ftplib")


class Unusable(Exception):
    """The input cannot be judged, which is not the same as being refused."""


class Refused(Exception):
    """A named contradiction. Carries the code and what contradicted what."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def canonical(document: Any) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def digest(document: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(document).encode("utf-8")).hexdigest()


def load_json(path: Path, what: str) -> Any:
    if not path.is_file():
        raise Unusable(f"{what} is absent: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Unusable(f"{what} is unreadable: {path}: {error}") from error


def load_schemas(references: Path) -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for identity in MEMBERS.values():
        name = identity.split("/")[1] + ".schema.json"
        document = load_json(references / "schemas" / name, f"schema {identity}")
        schemas[identity] = document
    return schemas


def validate_members(bundle: dict[str, Any], schemas: dict[str, dict[str, Any]]) -> None:
    """Each member judged by its own contract before anything is compared.

    A member that fails its own schema makes every cross-document comparison
    below meaningless, so it exits 64 rather than producing a K-code: the
    bundle is unusable, not contradictory.
    """
    try:
        from jsonschema import Draft202012Validator
    except ImportError as error:  # pragma: no cover - environment guard
        raise Unusable(
            "jsonschema is required to judge bundle members against their own "
            "contracts; a checker that skipped them would report the same green"
        ) from error
    for key, identity in MEMBERS.items():
        errors = list(Draft202012Validator(schemas[identity]).iter_errors(bundle[key]))
        if errors:
            raise Unusable(
                f"bundle member {key!r} does not satisfy {identity}: {errors[0].message}"
            )


def read_bundle(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise Unusable("a bundle is an object with four named members")
    if document.get("schema") != BUNDLE_SCHEMA:
        raise Unusable(
            f"bundle declares schema {document.get('schema')!r}; this checker "
            f"judges {BUNDLE_SCHEMA} and refuses to guess"
        )
    missing = [key for key in MEMBERS if key not in document]
    if missing:
        raise Unusable(
            f"bundle is missing {', '.join(sorted(missing))}. A member that is "
            f"absent is not a member that passed; every one of the four is "
            f"required because every check below needs two of them at once"
        )
    extra = sorted(set(document) - set(MEMBERS) - {"schema"})
    if extra:
        raise Unusable(f"bundle carries unknown members: {', '.join(extra)}")
    return document


def normalize_lease_path(path: str) -> tuple[str, bool]:
    """Strip a trailing `/**`; report whether the rest is still a pattern."""
    stem = path[:-3] if path.endswith("/**") else path
    return stem.rstrip("/"), "*" in stem


def leases_collide(first: str, second: str) -> bool:
    left, left_pattern = normalize_lease_path(first)
    right, right_pattern = normalize_lease_path(second)
    if left_pattern or right_pattern:
        return True  # undecidable, and undecidable is not disjoint
    if left == right:
        return True
    return left.startswith(right + "/") or right.startswith(left + "/")


def check_k01(bundle: dict[str, Any]) -> None:
    subject = bundle["epoch"]["subject"]
    expected = (subject["main_commit"], subject["tree"])
    observed = {
        "join": (bundle["join"]["epoch_ref"]["main_commit"], bundle["join"]["epoch_ref"]["tree"]),
        "ci_epoch": (
            bundle["ci_epoch"]["epoch_ref"]["main_commit"],
            bundle["ci_epoch"]["epoch_ref"]["tree"],
        ),
        "composition": (
            bundle["composition"]["subject_commit"],
            bundle["composition"]["subject_tree"],
        ),
    }
    for member, pair in sorted(observed.items()):
        if pair != expected:
            raise Refused(
                "K01_MIXED_SNAPSHOT_EPOCH",
                f"{member} is bound to {pair[0]}/{pair[1]} and the epoch to "
                f"{expected[0]}/{expected[1]}; two subjects in one bundle "
                f"describe a picture that never existed at either of them",
            )


def check_k02(bundle: dict[str, Any]) -> None:
    join = bundle["join"]
    pending = sorted(
        agent["task_id"]
        for agent in join["requested_agents"]
        if agent["terminal_state"] in NON_TERMINAL
    )
    if not pending:
        return
    state = bundle["epoch"]["portfolio_state"]
    if PORTFOLIO_STATES.index(state) >= BARRIER:
        raise Refused(
            "K02_JOIN_INCOMPLETE_ADVANCE",
            f"the epoch is at {state}, at or past the join barrier, while "
            f"{', '.join(pending)} has not terminated; dispatch is not completion",
        )
    if join["advanced_transitions"]:
        raise Refused(
            "K02_JOIN_INCOMPLETE_ADVANCE",
            f"the join advanced {', '.join(sorted(join['advanced_transitions']))} "
            f"while {', '.join(pending)} has not terminated",
        )


def check_k03(bundle: dict[str, Any]) -> None:
    current = bundle["epoch"]["subject"]["main_commit"]
    for retired in bundle["epoch"]["superseded_epochs"]:
        if retired["main_commit"] == current:
            raise Refused(
                "K03_SUPERSEDED_EPOCH_NOT_SUPERSEDED",
                f"{retired['epoch_id']} is listed as superseded and is bound to "
                f"the current subject {current}; nothing moved, so nothing was retired",
            )
        if retired["delta"]["from_digest"] != retired["main_commit"]:
            raise Refused(
                "K03_SUPERSEDED_EPOCH_NOT_SUPERSEDED",
                f"{retired['epoch_id']} was bound to {retired['main_commit']} and "
                f"its delta starts at {retired['delta']['from_digest']}; a delta "
                f"that does not start where the epoch stood retires a third subject",
            )


def instruction_path(bundle: dict[str, Any], references: Path) -> Path:
    """`coordinator_instruction_route` is Skill-relative, so it resolves against
    the parent of the references directory. Keeping it Skill-relative is what
    lets `--references` point the whole resolution at a throwaway copy without
    the route in the document changing."""
    return references.parent / bundle["composition"]["coordinator_instruction_route"]


def check_k04(bundle: dict[str, Any], references: Path) -> None:
    for entry in bundle["composition"]["composed_authorities"]:
        route = REPO / entry["owner_route"]
        if not route.exists():
            raise Refused(
                "K04_AUTHORITY_ROUTE_ABSENT",
                f"{entry['authority_kind']} is routed at {entry['owner_route']}, "
                f"which is not on this tree; a route to nothing reads exactly "
                f"like a route to the owner",
            )
    if not instruction_path(bundle, references).is_file():
        raise Refused(
            "K04_AUTHORITY_ROUTE_ABSENT",
            f"the coordinator instruction is routed at "
            f"{bundle['composition']['coordinator_instruction_route']}, which is "
            f"not on this tree",
        )


def check_k05(bundle: dict[str, Any], references: Path) -> None:
    route = instruction_path(bundle, references)
    pinned = load_json(route, "pinned coordinator instruction").get("instruction")
    declared = bundle["join"]["coordinator_instruction"]
    if pinned != declared:
        raise Refused(
            "K05_COORDINATOR_INSTRUCTION_ALTERED",
            f"the join carries {declared!r} and the pinned bytes are {pinned!r}; "
            f"the half that gets dropped is the half that makes the work joinable",
        )


def check_k06(bundle: dict[str, Any]) -> None:
    ci = bundle["ci_epoch"]
    head = ci["candidate"]["head_commit"]
    tested = ci["hosted_run"]["tested_head"]
    observed = ci["hosted_run"]["hosted_evidence_grade"] == "EXECUTION_OBSERVED"
    attested = ci["readback"]["tested_head_equals_candidate_head"]
    if observed and tested != head:
        raise Refused(
            "K06_CI_EPOCH_NOT_EXACT_HEAD",
            f"the run tested {tested} and the candidate head is {head}; a receipt "
            f"from another head is a receipt about another change",
        )
    if attested and tested != head:
        raise Refused(
            "K06_CI_EPOCH_NOT_EXACT_HEAD",
            f"the readback attests the tested head equals the candidate head, and "
            f"the digests are {tested} and {head}; the attestation is one arrival "
            f"and the digests are the other",
        )


def check_k07(bundle: dict[str, Any]) -> None:
    join = bundle["join"]
    present = {agent["role"] for agent in join["requested_agents"]}
    missing = sorted(set(join["required_roles"]) - present)
    if missing:
        raise Refused(
            "K07_REQUIRED_ROLE_MISSING",
            f"{', '.join(missing)} is required by this wave and has no requested "
            f"agent; a role nobody dispatched is JOIN_INCOMPLETE, never agreement",
        )


def check_k08(bundle: dict[str, Any]) -> None:
    identifiers = {
        "epoch": bundle["epoch"]["epoch_id"],
        "join": bundle["join"]["join_id"],
        "ci_epoch": bundle["ci_epoch"]["ci_epoch_id"],
        "composition": bundle["composition"]["composition_id"],
    }
    for member, identifier in sorted(identifiers.items()):
        if int(identifier.rsplit("-", 1)[1]) in RESERVED_BLOCK:
            raise Refused(
                "K08_SHAPE_EXAMPLE_USED_AS_RECEIPT",
                f"{member} carries {identifier}; the 900-999 block is reserved for "
                f"shape-only instances inside a schema's examples and never "
                f"describes an observed run",
            )


def check_k09(bundle: dict[str, Any]) -> None:
    writers: list[tuple[str, str]] = []
    for agent in bundle["join"]["requested_agents"]:
        if agent["lease"]["mode"] != "EXCLUSIVE_WRITE":
            continue
        for path in agent["lease"]["paths"]:
            writers.append((agent["task_id"], path))
    for index, (task, path) in enumerate(writers):
        for other_task, other_path in writers[index + 1 :]:
            if task == other_task:
                continue
            if leases_collide(path, other_path):
                raise Refused(
                    "K09_OVERLAPPING_EXCLUSIVE_LEASE",
                    f"{task} holds {path} and {other_task} holds {other_path}; two "
                    f"exclusive writers over the same bytes are not parallel work",
                )


def evaluate(bundle: dict[str, Any], references: Path) -> dict[str, Any]:
    check_k01(bundle)
    check_k02(bundle)
    check_k03(bundle)
    check_k04(bundle, references)
    check_k05(bundle, references)
    check_k06(bundle)
    check_k07(bundle)
    check_k08(bundle)
    check_k09(bundle)
    subject = bundle["epoch"]["subject"]
    return {
        "schema": VERDICT_SCHEMA,
        "bundle_digest": digest(bundle),
        "subject": {"main_commit": subject["main_commit"], "tree": subject["tree"]},
        "members_validated": sorted(MEMBERS.values()),
        "checks": [{"code": code, "state": "PASS"} for code in CODES],
        "join_state": bundle["join"]["join_state"],
        "portfolio_state": bundle["epoch"]["portfolio_state"],
        "hosted_evidence_grade": bundle["ci_epoch"]["hosted_run"]["hosted_evidence_grade"],
        "verdict": "NO_CONTRADICTION_FOUND",
        "evidence_ceiling": "REPOSITORY_BYTES_AND_LOCAL_GIT_ONLY",
        "authority": dict(AUTHORITY),
        "human_owned_operations": list(HUMAN_OWNED),
    }


def bundle_from_examples(references: Path) -> dict[str, Any]:
    """The bundle the committed schema examples describe, assembled once.

    Deriving it rather than committing a second copy of each member is what
    stops the fixture from drifting away from the contracts it is supposed to
    demonstrate. `--selftest` asserts that the committed fixture still equals
    what this function builds.
    """
    schemas = load_schemas(references)
    bundle: dict[str, Any] = {"schema": BUNDLE_SCHEMA}
    for key, identity in MEMBERS.items():
        examples = schemas[identity].get("examples") or []
        if not examples:
            raise Unusable(f"{identity} ships no examples, so no bundle can be derived")
        bundle[key] = copy.deepcopy(examples[0])
    return bundle


def mutations() -> dict[str, Any]:
    """One mutation per refusal code, each keeping every member schema-valid.

    A mutation that broke its member's own schema would exit 64 and prove
    nothing about the code it claims to fire.
    """

    def k01(bundle: dict[str, Any]) -> None:
        bundle["join"]["epoch_ref"]["main_commit"] = "0" * 40

    def k02(bundle: dict[str, Any]) -> None:
        bundle["epoch"]["portfolio_state"] = "LOCAL_WORKTREES_EXECUTED"

    def k03(bundle: dict[str, Any]) -> None:
        bundle["epoch"]["superseded_epochs"][0]["delta"]["from_digest"] = "1" * 40

    def k04(bundle: dict[str, Any]) -> None:
        bundle["composition"]["composed_authorities"][0]["owner_route"] = (
            "skills/no-such-authority/README.md"
        )

    def k06(bundle: dict[str, Any]) -> None:
        bundle["ci_epoch"]["readback"]["tested_head_equals_candidate_head"] = True

    def k07(bundle: dict[str, Any]) -> None:
        bundle["join"]["required_roles"].append("release-auditor")

    def k08(bundle: dict[str, Any]) -> None:
        bundle["epoch"]["epoch_id"] = "GHPC-EPOCH-900"

    def k09(bundle: dict[str, Any]) -> None:
        first = bundle["join"]["requested_agents"][0]
        second = copy.deepcopy(first)
        second["task_id"] = "GHPC-TASK-999"
        second["agent_id"] = "overlapping-writer"
        second["lease"]["paths"] = ["skills/github-portfolio-control/references"]
        bundle["join"]["requested_agents"].append(second)

    return {
        "K01_MIXED_SNAPSHOT_EPOCH": k01,
        "K02_JOIN_INCOMPLETE_ADVANCE": k02,
        "K03_SUPERSEDED_EPOCH_NOT_SUPERSEDED": k03,
        "K04_AUTHORITY_ROUTE_ABSENT": k04,
        "K06_CI_EPOCH_NOT_EXACT_HEAD": k06,
        "K07_REQUIRED_ROLE_MISSING": k07,
        "K08_SHAPE_EXAMPLE_USED_AS_RECEIPT": k08,
        "K09_OVERLAPPING_EXCLUSIVE_LEASE": k09,
    }


def selftest(references: Path) -> int:
    """Positive, byte-stability, no-network, and one planted defect per code."""
    failures: list[str] = []

    source = Path(__file__).read_text(encoding="utf-8")
    for number, line in enumerate(source.splitlines(), 1):
        statement = line.strip()
        if not statement.startswith(("import ", "from ")):
            continue
        for module in NETWORK_MODULES:
            if statement.startswith((f"import {module}", f"from {module}")):
                failures.append(
                    f"no-network: line {number} imports {module!r}; a controller "
                    f"that can fetch the state it was handed can fabricate it"
                )

    bundle = bundle_from_examples(references)
    committed = load_json(references / "fixtures" / "example-bundle.json", "example bundle")
    if canonical(committed) != canonical(bundle):
        failures.append(
            "the committed example bundle no longer equals the schemas' own "
            "examples[0]; regenerate it with --emit-bundle rather than editing it"
        )

    schemas = load_schemas(references)
    # PORTFOLIO_STATES above is a second copy of a vocabulary the contract owns,
    # and K02 reads its order to decide what "past the barrier" means. A copy
    # nobody compares is a fork waiting to happen, so compare it.
    contract_states = tuple(
        schemas["ghpc/portfolio-epoch/v1"]["$defs"]["portfolio_state"]["enum"]
    )
    if contract_states != PORTFOLIO_STATES:
        failures.append(
            "the ordered states this checker compares against have forked from "
            "the contract's own enum; K02 is deciding 'past the barrier' with a "
            "different vocabulary than the one the epoch was written in"
        )

    validate_members(bundle, schemas)
    verdict = evaluate(bundle, references)
    expected = load_json(
        references / "fixtures" / "example-bundle.verdict.json", "expected verdict"
    )
    if canonical(expected) != canonical(verdict):
        failures.append(
            "the emitted verdict is not byte-identical to the committed one; "
            "a compiler whose output moves has no --check worth running"
        )

    fired: list[str] = []
    for code, mutate in sorted(mutations().items()):
        mutated = copy.deepcopy(bundle)
        mutate(mutated)
        try:
            validate_members(mutated, schemas)
        except Unusable as error:
            failures.append(f"{code}: the mutation broke a member schema ({error})")
            continue
        try:
            evaluate(mutated, references)
        except Refused as refused:
            if refused.code != code:
                failures.append(f"{code}: fired as {refused.code} instead")
            else:
                fired.append(code)
            continue
        failures.append(f"{code}: the planted defect survived, so the check is inert")

    # K05 needs the pinned bytes themselves to move, and the join's own schema
    # pins the sentence, so the only honest way to plant it is on a throwaway
    # copy of references/ rather than on the document.
    with tempfile.TemporaryDirectory(prefix="ghpc-k05-") as tmp:
        copy_root = Path(tmp) / "references"
        shutil.copytree(references, copy_root)
        target = copy_root / "coordinator-instruction.json"
        tampered = json.loads(target.read_text(encoding="utf-8"))
        tampered["instruction"] = "Use subagents and consolidate their findings."
        target.write_text(canonical(tampered), encoding="utf-8")
        try:
            evaluate(copy.deepcopy(bundle), copy_root)
        except Refused as refused:
            if refused.code != "K05_COORDINATOR_INSTRUCTION_ALTERED":
                failures.append(
                    f"K05_COORDINATOR_INSTRUCTION_ALTERED: fired as {refused.code} instead"
                )
            else:
                fired.append("K05_COORDINATOR_INSTRUCTION_ALTERED")
        else:
            failures.append(
                "K05_COORDINATOR_INSTRUCTION_ALTERED: a paraphrased instruction "
                "survived, so the pin is inert"
            )

    missing = sorted(set(CODES) - set(fired))
    if missing:
        failures.append(f"no planted defect exercised {', '.join(missing)}")

    if failures:
        for item in failures:
            print(f"GHPC-COMPILE-SELFTEST-RED {item}", file=sys.stderr)
        return 2
    print(
        f"GHPC-COMPILE-SELFTEST-GREEN {len(MEMBERS)} members validate against their "
        f"own contracts, the derived bundle matches the committed fixture "
        f"byte-for-byte, the verdict is byte-stable, no import names a network "
        f"module, and {len(fired)} of {len(CODES)} refusal codes fired on their own "
        f"planted defect"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, help="a ghpc/portfolio-bundle/v1 document")
    parser.add_argument("--out", type=Path, help="write the verdict here")
    parser.add_argument("--check", type=Path, help="compare the verdict with this file")
    parser.add_argument(
        "--emit-bundle",
        type=Path,
        help="write the bundle derived from the schemas' examples[0] here",
    )
    parser.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    references = args.references.resolve()
    try:
        if not references.is_dir():
            raise Unusable(f"references directory is absent: {references}")
        if args.selftest:
            return selftest(references)
        if args.emit_bundle:
            args.emit_bundle.write_text(canonical(bundle_from_examples(references)), encoding="utf-8")
            print(f"GHPC-COMPILE-EMITTED {args.emit_bundle}")
            return 0
        if args.bundle is None:
            raise Unusable("--bundle, --emit-bundle or --selftest is required")
        bundle = read_bundle(load_json(args.bundle, "bundle"))
        validate_members(bundle, load_schemas(references))
        verdict = evaluate(bundle, references)
    except Unusable as error:
        print(f"GHPC-COMPILE-UNUSABLE {error}", file=sys.stderr)
        return 64
    except Refused as refused:
        print(f"GHPC-COMPILE-REFUSED {refused}", file=sys.stderr)
        return 2

    text = canonical(verdict)
    if args.check:
        try:
            observed = args.check.read_text(encoding="utf-8")
        except OSError as error:
            print(f"GHPC-COMPILE-UNUSABLE expected verdict unreadable: {error}", file=sys.stderr)
            return 64
        if observed != text:
            print(
                f"GHPC-COMPILE-REFUSED output drifted from {args.check}; the "
                f"compiler is not byte-stable at this input",
                file=sys.stderr,
            )
            return 2
        print(f"GHPC-COMPILE-GREEN {args.check} is byte-identical to a fresh run")
        return 0
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"GHPC-COMPILE-GREEN wrote {args.out}")
        return 0
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
