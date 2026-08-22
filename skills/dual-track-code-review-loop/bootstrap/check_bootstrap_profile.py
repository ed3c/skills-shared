#!/usr/bin/env python3
"""Decide whether the committed DTCR consumer bootstrap profile is still true.

The artifact this gate reads is a *profile*, not an engine. `shared-skills-infra`
already owns an atomic, rollback-tested, receipt-emitting consumer bootstrap with
its own planted-defect suite; what was missing for this procedure was a profile
naming it. So every check below compares the committed profile against something
that physically exists elsewhere in the tree, and nothing here re-implements a
binder, a receipt or a rollback.

    SCHEMA                       the artifact validates against its committed schema
    CONTROL_PLANE_SCHEMA         the embedded control-plane profile validates
                                 against `shared-skills-infra`'s committed schema,
                                 so the profile and the engine that will consume it
                                 cannot drift apart while both stay green alone
    SUBJECT_PIN                  every pinned object name resolves in this
                                 repository and the tree names are the ones that
                                 commit actually carries. This is what stops a pin
                                 from being typed rather than observed
    SKILL_CLOSURE                the Skill closure is the engine's default closure
                                 plus this procedure, and every named Skill has a
                                 canonical body here
    ENGINE_SURFACE               the engine scripts exist and the consumer surface
                                 the profile advertises is the engine's own path
                                 constants, not a list that was true once
    REGISTRY_PRECONDITION        the declared admission state equals what
                                 registry.json says, in both directions
    ATTACH_CLOSURE_PRECONDITION  the declared closure-admission state equals what
                                 the engine's REQUIRED_ORDER says, in both
                                 directions
    ATTACH_OBSERVATION           the engine is actually called, and its answer is
                                 the answer the profile claims it gives

The two precondition checks are the point of the artifact and the reason they
reconcile in both directions. Binding a consumer to this profile requires a Human
admission of `dual-track-code-review-loop` into `registry.json` that no Worker may
record on a person's behalf, and it requires an edit to a constant in a lane this
issue does not lease. A profile that quietly asserted those were fine would look
identical to one that had them; a profile that keeps claiming they are blocked
after they are lifted is the same failure pointing the other way, and stops anyone
noticing the binding is now available. So each declared state is compared to the
observed one and any disagreement is red.

`ATTACH_OBSERVATION` is what makes "blocked" an exit code rather than a sentence.
It calls the engine's own `validate_profile` on the embedded profile and asserts
the engine refuses, with the exact text it raised. The day both preconditions are
satisfied, that call stops refusing and this check turns red until the artifact is
re-derived -- which is the intended alarm, not a defect.

Zero network. Nothing here writes into any repository, admits any Skill, or
promotes bootstrap evidence into runtime, review, merge or release evidence.

Exit 0 every check held, 2 a check refused, 64 the input or the environment is
unusable (a distinct word is printed for each, because an absent validator and a
malformed document are different problems with different owners).
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SKILL_NAME = "dual-track-code-review-loop"
INFRA_SCRIPTS = ROOT / "skills" / "shared-skills-infra" / "scripts"
INFRA_REFERENCES = ROOT / "skills" / "shared-skills-infra" / "references"
DEFAULT_PROFILE = HERE / "dtcr-consumer-bootstrap-profile.json"
PROFILE_SCHEMA = HERE / "dtcr-consumer-bootstrap-profile.schema.json"
CONTROL_PLANE_SCHEMA = INFRA_REFERENCES / "repository-control-plane-profile.v1.schema.json"
REGISTRY = ROOT / "registry.json"

GREEN = "DTCR-BOOTSTRAP-PROFILE-GREEN"
RED = "DTCR-BOOTSTRAP-PROFILE-RED"
INVALID = "DTCR-BOOTSTRAP-PROFILE-INVALID"
UNUSABLE = "DTCR-BOOTSTRAP-PROFILE-UNUSABLE"
TERMINAL = "DTCR_GENERIC_CONSUMER_BOOTSTRAP_READY"

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        f"{UNUSABLE} jsonschema is required. This gate executes committed schemas as "
        "deciding validators; skipping them would print the same green as running them.",
        file=sys.stderr,
    )
    raise SystemExit(64)

sys.path.insert(0, str(INFRA_SCRIPTS))
try:
    import consumer_bootstrap_common as engine_paths
    import repository_control_plane as engine
except ImportError as exc:  # pragma: no cover - environment guard
    print(f"{UNUSABLE} the shared-skills-infra bootstrap engine is not importable: {exc}", file=sys.stderr)
    raise SystemExit(64)


class Refusal(Exception):
    def __init__(self, check: str, detail: str) -> None:
        super().__init__(detail)
        self.check = check
        self.detail = detail


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"{INVALID} unreadable JSON {path}: {exc}", file=sys.stderr)
        raise SystemExit(64) from exc


def git(*args: str) -> str | None:
    """Resolve one object name in this repository, or report absence as absence.

    A pin that does not resolve and a pin that resolves to something else are the
    same defect for the reader and different defects for whoever fixes it, so the
    caller gets None rather than a substituted value.
    """
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def validate_against(schema_path: Path, document: Any, check: str, subject: str) -> None:
    validator = Draft202012Validator(read_json(schema_path))
    errors = sorted(validator.iter_errors(document), key=lambda err: list(err.absolute_path))
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "<root>"
        raise Refusal(check, f"{subject} failed {schema_path.name} at {location}: {first.message}")


def reconcile(*, observed: bool, declared: str, satisfied: str, unsatisfied: str) -> str | None:
    """Both directions of one precondition, as a pure predicate.

    Returned as a message rather than raised so the selftest can exercise the
    direction whose observed side is a tree fact this suite is not allowed to
    mutate. Returns None when the declared state matches what was observed.
    """
    expected = satisfied if observed else unsatisfied
    if declared == expected:
        return None
    if observed:
        return (
            f"declared {declared} but the tree already satisfies this precondition; "
            f"a lifted block left standing hides that the binding is now available. Expected {expected}"
        )
    return (
        f"declared {declared} but the tree does not satisfy this precondition; "
        f"expected {expected}"
    )


def precondition(document: dict[str, Any], identifier: str) -> dict[str, Any]:
    for row in document["preconditions"]:
        if row["id"] == identifier:
            return row
    raise Refusal("SCHEMA", f"precondition {identifier} is absent from the artifact")


# ---------------------------------------------------------------------------
# checks, in the order they run; the first refusal is the reported one
# ---------------------------------------------------------------------------


def check_schema(document: dict[str, Any]) -> None:
    validate_against(PROFILE_SCHEMA, document, "SCHEMA", "bootstrap profile")
    declared = {row["id"] for row in document["preconditions"]}
    if declared != {"REGISTRY_ADMISSION", "ATTACH_CLOSURE_ADMISSION"}:
        raise Refusal("SCHEMA", f"precondition set drifted: {sorted(declared)}")
    residuals = {row["id"] for row in document["residuals"]}
    if "REAL_CONSUMER_APPLICATION" not in residuals:
        raise Refusal("SCHEMA", "the real-consumer residual is absent; the terminal would read as an executed bootstrap")


def check_control_plane_schema(document: dict[str, Any]) -> None:
    validate_against(
        CONTROL_PLANE_SCHEMA,
        document["control_plane_profile"],
        "CONTROL_PLANE_SCHEMA",
        "embedded control-plane profile",
    )


def check_subject_pin(document: dict[str, Any]) -> None:
    pin = document["subject_pin"]
    if not engine_paths.REPOSITORY_ID.fullmatch(pin["repository"]):
        raise Refusal("SUBJECT_PIN", f"repository identity must be owner/name, not {pin['repository']!r}")
    commit = git("rev-parse", "--verify", "--quiet", f"{pin['main_commit']}^{{commit}}")
    if commit is None:
        raise Refusal(
            "SUBJECT_PIN",
            f"pinned commit {pin['main_commit']} does not resolve in this repository; "
            "an invented or expanded object name names nothing",
        )
    if commit != pin["main_commit"]:
        raise Refusal("SUBJECT_PIN", f"pinned commit resolved to {commit}")
    for key, rev in (
        ("main_tree", f"{pin['main_commit']}^{{tree}}"),
        ("owned_tree", f"{pin['main_commit']}:{pin['owned_tree_path']}"),
    ):
        observed = git("rev-parse", "--verify", "--quiet", rev)
        if observed is None:
            raise Refusal("SUBJECT_PIN", f"{key} source {rev} does not resolve in this repository")
        if observed != pin[key]:
            raise Refusal(
                "SUBJECT_PIN",
                f"{key} is {pin[key]} but {rev} is {observed}; a tree moved without its commit is a substituted pin",
            )


def check_skill_closure(document: dict[str, Any]) -> None:
    skills = document["control_plane_profile"]["skills"]
    expected = [*engine.REQUIRED_ORDER, SKILL_NAME]
    if skills != expected:
        raise Refusal(
            "SKILL_CLOSURE",
            f"closure must be the engine's default closure plus {SKILL_NAME}; got {skills}",
        )
    for name in skills:
        if not (ROOT / "skills" / name / "SKILL.md").is_file():
            raise Refusal("SKILL_CLOSURE", f"canonical Skill body missing: skills/{name}/SKILL.md")


def check_engine_surface(document: dict[str, Any]) -> None:
    for relative in document["bootstrap_engine"]["scripts"]:
        if not (ROOT / relative).is_file():
            raise Refusal("ENGINE_SURFACE", f"named engine script is absent: {relative}")
    observed = {
        engine_paths.SOURCE_REL, engine_paths.PROFILE_REL, engine_paths.REQUIREMENTS_REL,
        engine_paths.BINDING_REL, engine_paths.RECEIPT_REL, engine_paths.WORKFLOW_REL,
    }
    declared = {Path(item) for item in document["generated_consumer_surface"]}
    if declared != observed:
        missing = sorted(path.as_posix() for path in observed - declared)
        extra = sorted(path.as_posix() for path in declared - observed)
        raise Refusal(
            "ENGINE_SURFACE",
            f"advertised consumer surface is not the engine's own; missing={missing} extra={extra}",
        )


def check_registry_precondition(document: dict[str, Any]) -> None:
    registry = read_json(REGISTRY)
    admitted = {row.get("name") for row in registry.get("shared", []) if isinstance(row, dict)}
    problem = reconcile(
        observed=SKILL_NAME in admitted,
        declared=precondition(document, "REGISTRY_ADMISSION")["state"],
        satisfied="SATISFIED",
        unsatisfied="HUMAN_ADMIT_REQUIRED",
    )
    if problem:
        raise Refusal("REGISTRY_PRECONDITION", f"registry.json admission of {SKILL_NAME}: {problem}")


def check_attach_closure_precondition(document: dict[str, Any]) -> None:
    problem = reconcile(
        observed=SKILL_NAME in engine.REQUIRED_ORDER,
        declared=precondition(document, "ATTACH_CLOSURE_ADMISSION")["state"],
        satisfied="SATISFIED",
        unsatisfied="NOT_IMPLEMENTED",
    )
    if problem:
        raise Refusal("ATTACH_CLOSURE_PRECONDITION", f"engine REQUIRED_ORDER closure: {problem}")


def check_attach_observation(document: dict[str, Any]) -> None:
    observation = document["attach_observation"]
    blocked = [row["id"] for row in document["preconditions"] if row["state"] != "SATISFIED"]
    try:
        engine.validate_profile(copy.deepcopy(document["control_plane_profile"]))
        raised: str | None = None
    except engine.ControlPlaneError as exc:
        raised = str(exc)
    if blocked and raised is None:
        raise Refusal(
            "ATTACH_OBSERVATION",
            f"preconditions {blocked} are declared unsatisfied but the engine accepted the profile",
        )
    if not blocked and raised is not None:
        raise Refusal(
            "ATTACH_OBSERVATION",
            f"every precondition is declared satisfied but the engine still refused: {raised}",
        )
    expected_state = "REFUSED" if raised is not None else "ACCEPTED"
    if observation["state"] != expected_state:
        raise Refusal("ATTACH_OBSERVATION", f"declared {observation['state']} but the engine {expected_state}")
    if observation["refusal_message"] != raised:
        raise Refusal(
            "ATTACH_OBSERVATION",
            f"declared refusal {observation['refusal_message']!r} but the engine raised {raised!r}",
        )


CHECKS: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
    ("SCHEMA", check_schema),
    ("CONTROL_PLANE_SCHEMA", check_control_plane_schema),
    ("SUBJECT_PIN", check_subject_pin),
    ("SKILL_CLOSURE", check_skill_closure),
    ("ENGINE_SURFACE", check_engine_surface),
    ("REGISTRY_PRECONDITION", check_registry_precondition),
    ("ATTACH_CLOSURE_PRECONDITION", check_attach_closure_precondition),
    ("ATTACH_OBSERVATION", check_attach_observation),
]


def run(profile_path: Path) -> int:
    document = read_json(profile_path)
    if not isinstance(document, dict):
        print(f"{INVALID} bootstrap profile root must be an object", file=sys.stderr)
        return 64
    for name, check in CHECKS:
        try:
            check(document)
        except Refusal as refusal:
            print(f"{RED} {refusal.check}: {refusal.detail}", file=sys.stderr)
            return 2
        except KeyError as exc:  # a field the schema requires is gone
            print(f"{RED} {name}: required field {exc} is absent", file=sys.stderr)
            return 2
    blocked = [f"{row['id']}={row['state']}" for row in document["preconditions"] if row["state"] != "SATISFIED"]
    residuals = " ".join(f"{row['id']}={row['state']}(#{row['owner_issue']})" for row in document["residuals"])
    print(f"{GREEN} checks={len(CHECKS)} profile={document['control_plane_profile']['profile']}")
    print(f"{GREEN} pinned_commit={document['subject_pin']['main_commit']} owned_tree={document['subject_pin']['owned_tree']}")
    print(f"{GREEN} engine={document['bootstrap_engine']['owner_skill']} attach={document['attach_observation']['state']} blocked={','.join(blocked) or 'none'}")
    print(f"{GREEN} residuals: {residuals}")
    print(f"{TERMINAL} profile_committed_and_reconciled consumer_bootstrap_executed=false")
    return 0


# ---------------------------------------------------------------------------
# selftest: every planted mutation is a single-field delta on the committed
# artifact, so a refusal is attributable to the field rather than to a fixture
# that is broken in general.
# ---------------------------------------------------------------------------


def _mutate_registry_state(document: dict[str, Any], state: str) -> None:
    precondition(document, "REGISTRY_ADMISSION")["state"] = state


def _mutate_closure_state(document: dict[str, Any], state: str) -> None:
    precondition(document, "ATTACH_CLOSURE_ADMISSION")["state"] = state


def _mutate_residual(document: dict[str, Any], state: str) -> None:
    for row in document["residuals"]:
        if row["id"] == "REAL_CONSUMER_APPLICATION":
            row["state"] = state


MUTATIONS: list[tuple[str, str, Callable[[dict[str, Any]], None]]] = [
    (
        "papered-over Human admission",
        "REGISTRY_PRECONDITION",
        lambda doc: _mutate_registry_state(doc, "SATISFIED"),
    ),
    (
        "Human admission downgraded to unfinished work",
        "REGISTRY_PRECONDITION",
        lambda doc: _mutate_registry_state(doc, "NOT_IMPLEMENTED"),
    ),
    (
        "engine closure gate declared already widened",
        "ATTACH_CLOSURE_PRECONDITION",
        lambda doc: _mutate_closure_state(doc, "SATISFIED"),
    ),
    (
        "profile that lost the procedure it exists to bind",
        "SKILL_CLOSURE",
        lambda doc: doc["control_plane_profile"]["skills"].remove(SKILL_NAME),
    ),
    (
        "substituted tree name under a real commit",
        "SUBJECT_PIN",
        lambda doc: doc["subject_pin"].update(
            {"owned_tree": "4b825dc642cb6eb9a060e54bf8d69288fbee4904"}
        ),
    ),
    (
        "invented commit that resolves to nothing",
        "SUBJECT_PIN",
        lambda doc: doc["subject_pin"].update(
            {"main_commit": "0" * 40}
        ),
    ),
    (
        "branch name where an exact object name belongs",
        "SCHEMA",
        lambda doc: doc["subject_pin"].update({"main_commit": "main"}),
    ),
    (
        "real-consumer lane promoted to a pass",
        "SCHEMA",
        lambda doc: _mutate_residual(doc, "HUMAN_ADMIT_REQUIRED"),
    ),
    (
        "profile that grants itself merge",
        "SCHEMA",
        lambda doc: doc["authority"].update({"automatic_merge": True}),
    ),
    (
        "runtime capability state outside the engine's closed set",
        "CONTROL_PLANE_SCHEMA",
        lambda doc: doc["control_plane_profile"]["runtime_capabilities"]["git_town"].update(
            {"installer_state": "INSTALLED"}
        ),
    ),
    (
        "advertised consumer surface the engine does not write",
        "ENGINE_SURFACE",
        lambda doc: doc["generated_consumer_surface"].remove(".agents/control-plane/source.json"),
    ),
    (
        "engine script reference that has rotted",
        "ENGINE_SURFACE",
        lambda doc: doc["bootstrap_engine"]["scripts"].append(
            "skills/shared-skills-infra/scripts/consumer_bootstrap_absent.py"
        ),
    ),
    (
        "refusal text the engine never raised",
        "ATTACH_OBSERVATION",
        lambda doc: doc["attach_observation"].update({"refusal_message": "profile is fine"}),
    ),
    (
        "blocked profile reported as accepted",
        "ATTACH_OBSERVATION",
        lambda doc: doc["attach_observation"].update({"state": "ACCEPTED", "refusal_message": None}),
    ),
]


def _invoke(profile_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--profile", str(profile_path)],
        text=True, capture_output=True, check=False,
    )


def selftest() -> int:
    failures: list[str] = []

    positive = _invoke(DEFAULT_PROFILE)
    if positive.returncode == 0:
        print("  positive  exit=0  committed artifact  OK")
    else:
        failures.append(f"committed artifact is not green: exit={positive.returncode} {positive.stderr.strip()}")
        print(f"  positive  exit={positive.returncode}  committed artifact  FAILED")

    committed = read_json(DEFAULT_PROFILE)
    with tempfile.TemporaryDirectory() as tmp:
        for index, (label, expected_check, mutate) in enumerate(MUTATIONS, start=1):
            document = copy.deepcopy(committed)
            mutate(document)
            if document == committed:
                failures.append(f"mutation {index} ({label}) changed nothing")
                print(f"  M{index:<2}      inert   {label}  FAILED")
                continue
            planted = Path(tmp) / f"mutation-{index}.json"
            planted.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            result = _invoke(planted)
            observed_check = ""
            match = re.search(rf"^{RED} ([A-Z_]+):", result.stderr, re.MULTILINE)
            if match:
                observed_check = match.group(1)
            if result.returncode != 2:
                failures.append(f"mutation {index} ({label}) exited {result.returncode}, expected 2")
                print(f"  M{index:<2}      exit={result.returncode}  {label}  FAILED")
            elif observed_check != expected_check:
                failures.append(
                    f"mutation {index} ({label}) was refused by {observed_check or '<unnamed>'},"
                    f" expected {expected_check}"
                )
                print(f"  M{index:<2}      {observed_check}  {label}  FAILED")
            else:
                print(f"  M{index:<2}      exit=2  {expected_check}  {label}  OK")

    # The observed side of REGISTRY_PRECONDITION is a tree fact this suite may not
    # mutate: admitting a Skill into registry.json is the Human act the whole
    # artifact exists to keep unrepresentable, so the reverse direction is
    # exercised against the predicate in process instead. It is a weaker arrival
    # than the subprocess runs above and is labelled as one.
    reverse = reconcile(observed=True, declared="HUMAN_ADMIT_REQUIRED", satisfied="SATISFIED", unsatisfied="HUMAN_ADMIT_REQUIRED")
    forward = reconcile(observed=False, declared="SATISFIED", satisfied="SATISFIED", unsatisfied="HUMAN_ADMIT_REQUIRED")
    agree = reconcile(observed=False, declared="HUMAN_ADMIT_REQUIRED", satisfied="SATISFIED", unsatisfied="HUMAN_ADMIT_REQUIRED")
    if reverse is None or forward is None or agree is not None:
        failures.append("reconcile() does not refuse in both directions")
        print("  P1       in-process  reconcile() both directions  FAILED")
    else:
        print("  P1       in-process  reconcile() both directions  OK (predicate arrival only)")

    print(f"selftest cases={len(MUTATIONS) + 2} failures={len(failures)}")
    if failures:
        for line in failures:
            print(f"{RED} selftest {line}", file=sys.stderr)
        return 2
    print(f"{GREEN} selftest planted={len(MUTATIONS)} every planted mutation was refused by its own check")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the committed DTCR consumer bootstrap profile.")
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--selftest", action="store_true", help="plant single-field mutations and require each to go red")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.profile.is_file():
        print(f"{INVALID} bootstrap profile is absent: {args.profile}", file=sys.stderr)
        return 64
    return run(args.profile)


if __name__ == "__main__":
    raise SystemExit(main())
