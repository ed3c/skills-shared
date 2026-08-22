#!/usr/bin/env python3
"""Execute the R2 Expand & Contract compiler as a deciding gate.

Every check here runs `compile_r2.py` as a subprocess and reads its own exit
code. Nothing imports it and trusts a return value, because the thing being
tested is what a caller gets, and a caller gets an exit code.

    stability   every committed projection is what its request compiles to, and
                two runs of one request produce identical bytes. A planted byte
                in a copy has to turn --check red, or --check compares nothing.
    composition every emitted artifact validates against the committed schema
                that types it, so the compiler and the contract cannot drift
                apart while both stay green on their own.
    coverage    every value in the state enums those schemas declare is emitted
                by a real compilation of a committed request. This is the lane
                that stops a contract from declaring states nothing produces: a
                terminal only a test constructs does not exist, and a schema
                that lists it reads downstream as a protocol that reaches it.
    refusal     every named refusal fires from a single-field delta against a
                request that compiles green, so the refusal is attributable to
                the field rather than to a fixture that is broken in general.

The schemas' own `x-refusal-controls` are deliberately not re-run here. The
skill-level suite already executes every control in the tree and knocks out the
keyword each one names, and a second copy of that lane would report the same
green over the same bytes -- what this file owns is the compiler.

One coverage ceiling is stated rather than asserted, and it is the adapter law's
`contract_format` enum. Six formats have a declared capability class and the
fixtures exercise five of them; the sixth would be a fixture differing from an
existing one only in a string, and would report as coverage what is really
repetition. The number is printed on every run so the ceiling is visible instead
of implied.

Nothing here migrates anything. The fixtures are synthetic multi-repository
requests: no repository is read, parsed or written by the compiler under test,
no registry is contacted, and every receipt it emits pins
`applied_on_real_codebase` and `consumer_canary_observed` false. The real
bounded consumer canary that would exercise those lanes is a separate,
unexercised issue.

Exit 0 green, 2 a case failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "DTCR-R2-UNUSABLE: jsonschema is required. This suite executes the committed "
        "schemas against compiled output; skipping them would report the same green "
        "as running them.",
        file=sys.stderr,
    )
    raise SystemExit(70)

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
COMPILER = HERE / "compile_r2.py"
FIXTURES = HERE / "fixtures"
SCHEMAS = SKILL / "references" / "schemas"

REQUESTS = (
    "protobuf-orders-happy-path.json",
    "openapi-billing-consumer-lagging.json",
    "asyncapi-shipping-rolled-back.json",
    "protobuf-registry-publication-blocked.json",
    "json-schema-inventory-adapter-blocked.json",
    "avro-events-compatibility-failed.json",
)

EXPANSION = "dtcr/refactor-r2-contract-expansion/v1"
MIGRATION = "dtcr/refactor-r2-consumer-migration/v1"
RECEIPT = "dtcr/refactor-r2-receipt/v1"


def values(*items: Any) -> set[Any]:
    return set(items)


def migrations(projection: dict) -> list[dict]:
    return projection["consumer_migrations"]


# label -> (schema identity, path to the enum inside that schema, extractor over
# one projection). The denominator is read from the committed schema on the run,
# so a lane a sibling adds is covered on the run it lands rather than on the run
# somebody remembers to extend a constant here.
COVERAGE: tuple[tuple[str, str, tuple[str, ...], Callable[[dict], set]], ...] = (
    (
        "terminal_state",
        RECEIPT,
        ("properties", "terminal_state", "enum"),
        lambda p: values(p["receipt"]["terminal_state"]),
    ),
    (
        "states_entered",
        RECEIPT,
        ("properties", "states_entered", "items", "enum"),
        lambda p: set(p["receipt"]["states_entered"]),
    ),
    (
        "blocked_on",
        RECEIPT,
        ("properties", "blocked_on", "items", "enum"),
        lambda p: set(p["receipt"]["blocked_on"]),
    ),
    (
        "dual_run",
        RECEIPT,
        ("properties", "observation", "properties", "dual_run", "enum"),
        lambda p: values(p["receipt"]["observation"]["dual_run"]),
    ),
    (
        "window_verdict",
        RECEIPT,
        ("properties", "observation", "properties", "window_verdict", "enum"),
        lambda p: values(p["receipt"]["observation"]["window_verdict"]),
    ),
    (
        "telemetry_state",
        RECEIPT,
        ("properties", "observation", "properties", "telemetry", "properties", "state", "enum"),
        lambda p: values(p["receipt"]["observation"]["telemetry"]["state"]),
    ),
    (
        "coexistence_window_state",
        RECEIPT,
        ("properties", "provider_coexistence", "properties", "coexistence_window_state", "enum"),
        lambda p: values(p["receipt"]["provider_coexistence"]["coexistence_window_state"]),
    ),
    (
        "inventory_completeness",
        RECEIPT,
        ("properties", "downstream", "properties", "inventory_completeness", "enum"),
        lambda p: values(p["receipt"]["downstream"]["inventory_completeness"]),
    ),
    (
        "rollback_phase",
        RECEIPT,
        ("properties", "rollback_subjects", "items", "properties", "phase", "enum"),
        lambda p: {row["phase"] for row in p["receipt"]["rollback_subjects"]},
    ),
    (
        "capability_class",
        EXPANSION,
        ("properties", "adapter", "properties", "capability_class", "enum"),
        lambda p: values(p["contract_expansion"]["adapter"]["capability_class"]),
    ),
    (
        "provider_state",
        EXPANSION,
        ("properties", "adapter", "properties", "provider_state", "enum"),
        lambda p: values(p["contract_expansion"]["adapter"]["provider_state"]),
    ),
    (
        "baseline_rule_category",
        EXPANSION,
        ("properties", "compatibility", "properties", "baseline_rule_category", "enum"),
        lambda p: values(p["contract_expansion"]["compatibility"]["baseline_rule_category"]),
    ),
    (
        "run_rule_category",
        EXPANSION,
        ("properties", "compatibility", "properties", "run_rule_category", "enum"),
        lambda p: values(p["contract_expansion"]["compatibility"]["run_rule_category"]),
    ),
    (
        "compatibility_result",
        EXPANSION,
        ("properties", "compatibility", "properties", "result", "enum"),
        lambda p: values(p["contract_expansion"]["compatibility"]["result"]),
    ),
    (
        "publication_intent",
        EXPANSION,
        ("properties", "publication", "properties", "intent", "enum"),
        lambda p: values(p["contract_expansion"]["publication"]["intent"]),
    ),
    (
        "account_access",
        EXPANSION,
        ("properties", "publication", "properties", "account_access", "enum"),
        lambda p: values(p["contract_expansion"]["publication"]["account_access"]),
    ),
    (
        "migration_state",
        MIGRATION,
        ("properties", "migration_state", "enum"),
        lambda p: {row["migration_state"] for row in migrations(p)},
    ),
    (
        "fallback_state",
        MIGRATION,
        ("properties", "fallback_state", "enum"),
        lambda p: {row["fallback_state"] for row in migrations(p)},
    ),
    (
        "verification_state",
        MIGRATION,
        ("properties", "verification", "properties", "state", "enum"),
        lambda p: {row["verification"]["state"] for row in migrations(p)},
    ),
)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(COMPILER), *args], capture_output=True, text=True
    )


def compiled_name(request: str) -> Path:
    return FIXTURES / request.replace(".json", ".compiled.json")


def schema_documents() -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for path in sorted(SCHEMAS.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        identity = document.get("properties", {}).get("schema", {}).get("const")
        if isinstance(identity, str):
            documents[identity] = document
    return documents


def enum_at(document: dict[str, Any], path: tuple[str, ...]) -> set[str]:
    node: Any = document
    for key in path:
        node = node[key]
    return set(node)


def artifacts(projection: dict[str, Any]) -> list[dict[str, Any]]:
    return [projection["contract_expansion"], *migrations(projection), projection["receipt"]]


# --------------------------------------------------------------------------
# the mutations. Each is a single field away from a request that compiles.
# --------------------------------------------------------------------------

def mutate(request: dict[str, Any], edit: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    copied = copy.deepcopy(request)
    edit(copied)
    return copied


OTHER_DIGEST = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
OTHER_COMMIT = "cb48fdc7e8c6bd6db2ff32188047eab9a5340c9f"


def candidate_mutations(base: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Single-field deltas against the happy path, which compiles to a candidate."""

    def branch_subject(row: dict) -> None:
        row["contract"]["subject_commit"] = "main"

    def undeclared_format(row: dict) -> None:
        row["adapter"]["contract_format"] = "thrift"

    def capability_not_declared(row: dict) -> None:
        # json-schema declares SCHEMA_COMPATIBILITY_CHECK only, and this request
        # claims CODE_GENERATION.
        row["adapter"]["contract_format"] = "json-schema"

    def unpinned(row: dict) -> None:
        row["adapter"]["pins"]["license_id"] = ""

    def looser_rules(row: dict) -> None:
        row["compatibility"]["baseline_rule_category"] = "FILE"

    def narrowed_comparison(row: dict) -> None:
        row["compatibility"]["excluded_paths"] = ["proto/orders/v2/order.proto"]

    def stale_stub(row: dict) -> None:
        row["generated_artifacts"][0]["generated_from_commit"] = OTHER_COMMIT

    def consumer_built_elsewhere(row: dict) -> None:
        row["consumers"][0]["generated_artifact_digest"] = OTHER_DIGEST

    def publish_from_a_label(row: dict) -> None:
        row["publication"] = {
            "intent": "REGISTRY_PUBLISH",
            "account_access": "ABSENT",
            "content_rights": "HUMAN_ADMIT_REQUIRED",
            "source_commit": "HEAD",
            "source_tree": row["contract"]["subject_tree"],
            "registry_binding": "DTCR-REG-declared-not-contacted",
        }

    def publish_from_other_bytes(row: dict) -> None:
        row["publication"] = {
            "intent": "REGISTRY_PUBLISH",
            "account_access": "ABSENT",
            "content_rights": "HUMAN_ADMIT_REQUIRED",
            "source_commit": OTHER_COMMIT,
            "source_tree": row["contract"]["subject_tree"],
            "registry_binding": "DTCR-REG-declared-not-contacted",
        }

    def rights_from_account(row: dict) -> None:
        row["publication"]["content_rights"] = "CLEARED"

    def replaced_in_place(row: dict) -> None:
        row["contract"]["contract_version_new"] = row["contract"]["contract_version_old"]

    def no_fallback(row: dict) -> None:
        row["consumers"][0]["fallback_state"] = "ABSENT"

    def no_port(row: dict) -> None:
        row["consumers"][0]["port_bound"] = False

    def migrated_but_split(row: dict) -> None:
        row["consumers"][0]["traffic_on_new_percent"] = 60

    def contract_over_a_laggard(row: dict) -> None:
        row["consumers"][1]["migration_state"] = "IN_PROGRESS"

    def no_denominator(row: dict) -> None:
        row["consumers"][0]["verification"]["total"] = 0

    def migrated_unverified(row: dict) -> None:
        row["consumers"][0]["verification"]["state"] = "FAIL"

    def double_writes(row: dict) -> None:
        row["observation"]["idempotency_key_bound"] = False

    def unwatched_window(row: dict) -> None:
        row["observation"]["telemetry"]["state"] = "ABSENT"

    def empty_window(row: dict) -> None:
        row["observation"]["telemetry"]["samples"] = 0

    def partial_zero(row: dict) -> None:
        row["downstream"]["inventory_completeness"] = "PARTIAL_LOWER_BOUND"

    def self_authorised(row: dict) -> None:
        row["contraction"]["authorization"] = "AUTO_ON_GREEN_TELEMETRY"

    def decision_field(row: dict) -> None:
        row["contraction"]["approved"] = True

    def foreign_parent(row: dict) -> None:
        row["consumers"][0]["declared_parent_commits"] = [row["contract"]["subject_commit"]]

    def one_repository_twice(row: dict) -> None:
        row["consumers"][1]["consumer_binding_id"] = row["consumers"][0]["consumer_binding_id"]

    def phase_with_no_way_back(row: dict) -> None:
        row["rollback_subjects"] = [
            entry for entry in row["rollback_subjects"]
            if entry["phase"] != "C2_LEGACY_CONTRACTION"
        ]

    def two_restore_points(row: dict) -> None:
        first = row["rollback_subjects"][0]
        row["rollback_subjects"].append({**first, "restored_commit": OTHER_COMMIT})

    def revert_with_a_story(row: dict) -> None:
        row["rollback"] = {
            "phase": "A2_CONSUMER_INVERSION",
            "repository_binding_id": row["consumers"][0]["consumer_binding_id"],
            "applied_change_reverted": True,
        }

    def wrong_schema(row: dict) -> None:
        row["schema"] = "dtcr/refactor-r2-request/v2"

    return [
        ("STALE_SUBJECT", mutate(base, branch_subject)),
        ("UNSUPPORTED_CONTRACT_FORMAT_PROMOTED_TO_SUPPORTED", mutate(base, undeclared_format)),
        (
            "UNSUPPORTED_CONTRACT_FORMAT_PROMOTED_TO_SUPPORTED",
            mutate(base, capability_not_declared),
        ),
        ("ADAPTER_PINS_INCOMPLETE", mutate(base, unpinned)),
        ("BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING", mutate(base, looser_rules)),
        ("BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING", mutate(base, narrowed_comparison)),
        ("GENERATED_STUB_DRIFT", mutate(base, stale_stub)),
        ("GENERATED_STUB_DRIFT", mutate(base, consumer_built_elsewhere)),
        ("SCHEMA_PUBLISHED_WITHOUT_EXACT_SOURCE", mutate(base, publish_from_a_label)),
        ("SCHEMA_PUBLISHED_WITHOUT_EXACT_SOURCE", mutate(base, publish_from_other_bytes)),
        ("BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS", mutate(base, rights_from_account)),
        ("CONTRACT_REPLACED_NOT_EXPANDED", mutate(base, replaced_in_place)),
        ("CONSUMER_SWITCH_WITHOUT_FALLBACK", mutate(base, no_fallback)),
        ("CONSUMER_SWITCH_WITHOUT_FALLBACK", mutate(base, no_port)),
        ("PROVIDER_REMOVES_LEGACY_BEFORE_CONSUMER_MIGRATION", mutate(base, migrated_but_split)),
        (
            "PROVIDER_REMOVES_LEGACY_BEFORE_CONSUMER_MIGRATION",
            mutate(base, contract_over_a_laggard),
        ),
        ("VERIFICATION_DENOMINATOR_ABSENT", mutate(base, no_denominator)),
        ("CONSUMER_MIGRATED_WITHOUT_VERIFICATION", mutate(base, migrated_unverified)),
        ("DUAL_RUN_WITHOUT_IDEMPOTENCY", mutate(base, double_writes)),
        ("TELEMETRY_ABSENCE_PROMOTED_TO_SUCCESS", mutate(base, unwatched_window)),
        ("TELEMETRY_ABSENCE_PROMOTED_TO_SUCCESS", mutate(base, empty_window)),
        ("NO_REMAINING_CALLERS_IN_PARTIAL_INDEX", mutate(base, partial_zero)),
        ("AUTOMATIC_CONTRACTION_OR_MERGE", mutate(base, self_authorised)),
        ("AUTOMATIC_CONTRACTION_OR_MERGE", mutate(base, decision_field)),
        ("FALSE_CROSS_REPO_GIT_PARENT", mutate(base, foreign_parent)),
        ("FALSE_CROSS_REPO_GIT_PARENT", mutate(base, one_repository_twice)),
        ("ROLLBACK_SUBJECT_ABSENT_FOR_PHASE", mutate(base, phase_with_no_way_back)),
        ("ROLLBACK_SUBJECT_ABSENT_FOR_PHASE", mutate(base, two_restore_points)),
        ("ROLLBACK_WITHOUT_REGRESSION", mutate(base, revert_with_a_story)),
        ("UNREADABLE_INPUT", mutate(base, wrong_schema)),
    ]


def lagging_mutations(base: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Deltas against the run whose second consumer has not finished moving.

    The third branch of PROVIDER_REMOVES_LEGACY_BEFORE_CONSUMER_MIGRATION needs a
    consumer that is already lagging, so it is reachable from this base by one
    field and from the happy path only by two.
    """

    def legacy_already_gone(row: dict) -> None:
        row["provider"]["legacy_surface_present"] = False

    return [("PROVIDER_REMOVES_LEGACY_BEFORE_CONSUMER_MIGRATION", mutate(base, legacy_already_gone))]


def rollback_mutations(base: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Deltas against the run that rolled back after a partial migration."""

    def not_reverted(row: dict) -> None:
        row["rollback"]["applied_change_reverted"] = False

    def moving_restore(row: dict) -> None:
        row["rollback_subjects"][0]["restored_commit"] = "HEAD"

    def rollback_elsewhere(row: dict) -> None:
        row["rollback"]["repository_binding_id"] = row["provider"]["repository_binding_id"]

    def no_rollback(row: dict) -> None:
        del row["rollback"]

    return [
        ("ROLLBACK_NOT_REVERTED", mutate(base, not_reverted)),
        ("STALE_SUBJECT", mutate(base, moving_restore)),
        ("ROLLBACK_SUBJECT_ABSENT_FOR_PHASE", mutate(base, rollback_elsewhere)),
        # The same regressed window with the rollback record removed: a consumer
        # that rolled back and a run with nowhere honest to go is refused rather
        # than terminated.
        ("REGRESSION_WITHOUT_ROLLBACK", mutate(base, no_rollback)),
    ]


# --------------------------------------------------------------------------

def main() -> int:
    failures: list[str] = []
    stability = composition = refusals = 0
    schemas = schema_documents()
    validators = {identity: Draft202012Validator(doc) for identity, doc in schemas.items()}

    with tempfile.TemporaryDirectory() as scratch:
        work = Path(scratch)

        # 1. stability, against the committed bytes a caller would read.
        for request in REQUESTS:
            source = FIXTURES / request
            projection = compiled_name(request)
            result = run("--input", str(source), "--out", str(projection), "--check")
            stability += 1
            if result.returncode != 0:
                failures.append(
                    f"{request}: committed projection is not what it compiles to "
                    f"(exit {result.returncode}) {result.stderr.strip()}"
                )
                continue
            first = run("--input", str(source))
            second = run("--input", str(source))
            stability += 1
            if first.stdout != second.stdout:
                failures.append(f"{request}: two runs of one request produced different bytes")

            planted = work / f"planted-{request}"
            planted.write_text(
                projection.read_text(encoding="utf-8").replace(
                    '"receipt_id": "DTCR-R2-001"', '"receipt_id": "DTCR-R2-009"', 1
                ),
                encoding="utf-8",
            )
            stability += 1
            if run("--input", str(source), "--out", str(planted), "--check").returncode != 2:
                failures.append(
                    f"{request}: --check accepted a projection with a planted byte, so it "
                    f"proves nothing about the committed one"
                )

        # 2. composition against the committed schemas.
        projections = {}
        for request in REQUESTS:
            document = json.loads(compiled_name(request).read_text(encoding="utf-8"))
            projections[request] = document
            for artifact in artifacts(document):
                composition += 1
                validator = validators.get(artifact["schema"])
                if validator is None:
                    failures.append(
                        f"{request}: emitted {artifact['schema']}, which no committed "
                        f"schema declares"
                    )
                    continue
                errors = sorted(validator.iter_errors(artifact), key=str)
                if errors:
                    failures.append(
                        f"{request}: emitted {artifact['schema']} does not validate "
                        f"against its committed schema: {errors[0].message}"
                    )

        # 3. every declared state is emitted by a real compilation.
        covered = 0
        for label, identity, path, extract in COVERAGE:
            declared = enum_at(schemas[identity], path)
            emitted: set[str] = set()
            for document in projections.values():
                emitted |= extract(document)
            covered += len(declared)
            missing = sorted(declared - emitted)
            if missing:
                failures.append(
                    f"{label}: {', '.join(missing)} is declared by {identity} and no "
                    f"committed request compiles to it. A state only a test can "
                    f"construct is not a state the protocol reaches"
                )
            stray = sorted(emitted - declared)
            if stray:
                failures.append(
                    f"{label}: the compiler emitted {', '.join(stray)}, which {identity} "
                    f"does not declare"
                )

        formats = {
            document["contract_expansion"]["adapter"]["contract_format"]
            for document in projections.values()
        }
        declared_formats = enum_at(
            schemas[EXPANSION], ("properties", "adapter", "properties", "contract_format", "enum")
        )

        # 4. every named refusal, from a single-field delta.
        cases = [
            ("protobuf-orders-happy-path.json", candidate_mutations),
            ("openapi-billing-consumer-lagging.json", lagging_mutations),
            ("asyncapi-shipping-rolled-back.json", rollback_mutations),
        ]
        for fixture, builder in cases:
            base = json.loads((FIXTURES / fixture).read_text(encoding="utf-8"))
            for index, (code, mutated) in enumerate(builder(base)):
                path_ = work / f"{fixture}-{index:02d}.json"
                path_.write_text(json.dumps(mutated), encoding="utf-8")
                result = run("--input", str(path_))
                refusals += 1
                if result.returncode != 2:
                    failures.append(
                        f"{code}: the mutation compiled with exit {result.returncode} "
                        f"instead of being refused"
                    )
                elif code not in result.stderr:
                    failures.append(
                        f"{code}: refused, but the message names something else: "
                        f"{result.stderr.strip()}"
                    )

        # a request the compiler cannot read at all is 64, not 2: a malformed
        # input and a refused one are different facts about the caller.
        broken = work / "broken.json"
        malformed = json.loads((FIXTURES / REQUESTS[0]).read_text(encoding="utf-8"))
        malformed["compatibility"]["excluded_paths"] = 42
        broken.write_text(json.dumps(malformed), encoding="utf-8")
        refusals += 1
        unusable = run("--input", str(broken))
        if unusable.returncode != 64:
            failures.append(
                f"a structurally unusable request exited {unusable.returncode} rather than "
                f"64, so a broken caller reads as a refused one"
            )

    print(
        f"requests={len(REQUESTS)} stability_checks={stability} "
        f"schema_compositions={composition} state_values_covered={covered} "
        f"refusal_codes={refusals} "
        f"contract_formats_exercised={len(formats)}/{len(declared_formats)} "
        f"applied_on_real_codebase=NOT_EXERCISED consumer_canary=NOT_EXERCISED"
    )
    if failures:
        for failure in failures:
            print(f"DTCR-R2-SELFTEST-RED {failure}", file=sys.stderr)
        return 2
    print(
        f"DTCR-R2-SELFTEST-GREEN {len(REQUESTS)} projections byte-stable and current, "
        f"{composition} emitted artifacts validate against their committed schemas, "
        f"{covered} declared state values all emitted by a real compilation, "
        f"{refusals} named refusals fired from single-field deltas"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
