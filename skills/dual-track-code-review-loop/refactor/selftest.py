#!/usr/bin/env python3
"""Execute the R1 refactor compiler as a deciding gate.

Every check here runs `compile_r1.py` as a subprocess and reads its own exit
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

One coverage ceiling is stated rather than asserted, and it is the adapter law's
`language` enum. Eight languages have a declared capability class and the
fixtures exercise four of them; requiring all eight would mean writing four more
fixtures that differ only in a string, and would report as coverage what is
really repetition. The number is printed on every run so the ceiling is visible
instead of implied.

Nothing here applies a refactor to any codebase. The fixtures are synthetic
requests: no repository is read, parsed or written by the compiler under test,
and every receipt it emits pins `applied_on_real_codebase` false. The consumer
canary that would exercise that lane is a separate, unexercised issue.

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
        "DTCR-R1-UNUSABLE: jsonschema is required. This suite executes the committed "
        "schemas against compiled output; skipping them would report the same green "
        "as running them.",
        file=sys.stderr,
    )
    raise SystemExit(70)

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
COMPILER = HERE / "compile_r1.py"
FIXTURES = HERE / "fixtures"
SCHEMAS = SKILL / "references" / "schemas"

REQUESTS = (
    "python-order-domain.json",
    "typescript-billing-gateway.json",
    "go-ledger-blocked-on-provider.json",
    "python-order-domain-rolled-back.json",
    "java-inventory-typecheck-failed.json",
)
ARTIFACTS = ("usage_signature", "minimal_port", "changeset_lease", "receipt")

SIGNATURE = "dtcr/refactor-usage-signature/v1"
PORT = "dtcr/refactor-minimal-port/v1"
LEASE = "dtcr/refactor-changeset-lease/v1"
RECEIPT = "dtcr/refactor-r1-receipt/v1"


def values(*items: Any) -> set[Any]:
    return set(items)


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
        "typecheck",
        RECEIPT,
        ("properties", "readback", "properties", "typecheck", "enum"),
        lambda p: values(p["receipt"]["readback"]["typecheck"]),
    ),
    (
        "behavior_state",
        RECEIPT,
        ("properties", "readback", "properties", "behavior_tests", "properties", "state", "enum"),
        lambda p: values(p["receipt"]["readback"]["behavior_tests"]["state"]),
    ),
    (
        "reindex_state",
        RECEIPT,
        ("properties", "readback", "properties", "reindex_state", "enum"),
        lambda p: values(p["receipt"]["readback"]["reindex_state"]),
    ),
    (
        "completeness",
        SIGNATURE,
        ("properties", "extraction", "properties", "completeness", "enum"),
        lambda p: values(p["usage_signature"]["extraction"]["completeness"]),
    ),
    (
        "provider_state",
        SIGNATURE,
        ("properties", "adapter", "properties", "provider_state", "enum"),
        lambda p: values(p["usage_signature"]["adapter"]["provider_state"]),
    ),
    (
        "capability_class",
        SIGNATURE,
        ("properties", "adapter", "properties", "capability_class", "enum"),
        lambda p: values(p["usage_signature"]["adapter"]["capability_class"]),
    ),
    (
        "member_kind",
        SIGNATURE,
        ("properties", "consumed_members", "items", "properties", "member_kind", "enum"),
        lambda p: {row["member_kind"] for row in p["usage_signature"]["consumed_members"]}
        | {row["member_kind"] for row in p["minimal_port"]["port_members"]},
    ),
    (
        "owning_layer",
        PORT,
        ("properties", "owning_layer", "enum"),
        lambda p: values(p["minimal_port"]["owning_layer"]),
    ),
    (
        "contract_owner_admission",
        LEASE,
        ("properties", "public_api", "properties", "contract_owner_admission", "enum"),
        lambda p: values(p["changeset_lease"]["public_api"]["contract_owner_admission"]),
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


# --------------------------------------------------------------------------
# the mutations. Each is a single field away from a request that compiles.
# --------------------------------------------------------------------------

def mutate(request: dict[str, Any], edit: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    copied = copy.deepcopy(request)
    edit(copied)
    return copied


OTHER_DIGEST = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"


def candidate_mutations(base: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    def branch_subject(row: dict) -> None:
        row["subject"]["subject_commit"] = "main"

    def unresolved(row: dict) -> None:
        row["call_sites"][2]["resolved"] = False

    def undeclared_language(row: dict) -> None:
        row["adapter"]["language"] = "rust"

    def unpinned(row: dict) -> None:
        row["adapter"]["pins"]["license_id"] = ""

    def widened(row: dict) -> None:
        row["port"]["members"].append("vacuum")

    def import_left(row: dict) -> None:
        row["port"]["concrete_imports_remaining"] = [
            "domain/order/pricing.py:from infrastructure.sql import SqlOrderStore"
        ]

    def wrong_layer(row: dict) -> None:
        row["port"]["owning_layer"] = "INFRASTRUCTURE"

    def two_writers(row: dict) -> None:
        row["changeset"]["lease_writers"].append("a second writer who also holds this lease")

    def escaped_shape(row: dict) -> None:
        row["changeset"]["changed_paths"][2] = "../sibling-checkout/domain/order/pricing.py"

    def escaped_in_tree(row: dict) -> None:
        row["changeset"]["changed_paths"][2] = "infrastructure/sql/store.py"

    def generated(row: dict) -> None:
        row["changeset"]["changed_paths"].append("domain/order/generated/order_pb2.py")

    def rewritten_test(row: dict) -> None:
        row["changeset"]["behavior_tests"][0]["post_digest"] = OTHER_DIGEST

    def no_oracle(row: dict) -> None:
        row["changeset"]["behavior_tests"] = []

    def unadmitted_root(row: dict) -> None:
        row["changeset"]["composition_roots"][0]["admitted"] = False

    def api_changed(row: dict) -> None:
        row["changeset"]["public_api"]["changed"] = True

    def self_merge(row: dict) -> None:
        row["changeset"]["merge_admission"] = "AUTO_MERGE_ON_GREEN_SUITE"

    def decision_field(row: dict) -> None:
        row["changeset"]["approved"] = True

    def behavior_failed(row: dict) -> None:
        row["readback"]["behavior_tests"]["state"] = "FAIL"

    def cycle(row: dict) -> None:
        row["readback"]["new_cycles"] = 1

    def no_denominator(row: dict) -> None:
        row["readback"]["behavior_tests"]["total"] = 0

    def spurious_rollback(row: dict) -> None:
        row["rollback"] = {
            "restored_commit": "cb48fdc7e8c6bd6db2ff32188047eab9a5340c9f",
            "applied_change_reverted": True,
        }

    def wrong_schema(row: dict) -> None:
        row["schema"] = "dtcr/refactor-r1-request/v2"

    return [
        ("STALE_SUBJECT", mutate(base, branch_subject)),
        ("USAGE_SET_INCOMPLETE", mutate(base, unresolved)),
        ("UNSUPPORTED_LANGUAGE_PROMOTED_TO_SUPPORTED", mutate(base, undeclared_language)),
        ("ADAPTER_PINS_INCOMPLETE", mutate(base, unpinned)),
        ("PORT_WIDENED_WITH_UNUSED_PROVIDER_SURFACE", mutate(base, widened)),
        ("INJECTION_INCOMPLETE", mutate(base, import_left)),
        ("PORT_PLACED_OUTSIDE_OWNING_MODULE", mutate(base, wrong_layer)),
        ("SECOND_CHANGESET_WRITER", mutate(base, two_writers)),
        ("PATH_LEASE_ESCAPE", mutate(base, escaped_shape)),
        ("PATH_LEASE_ESCAPE", mutate(base, escaped_in_tree)),
        ("GENERATED_CODE_EDITED_DIRECTLY", mutate(base, generated)),
        ("BEHAVIOR_TEST_MUTATED", mutate(base, rewritten_test)),
        ("BEHAVIOR_TEST_ABSENT", mutate(base, no_oracle)),
        ("COMPOSITION_ROOT_NOT_FOUND", mutate(base, unadmitted_root)),
        ("PUBLIC_API_CHANGED_WITHOUT_CONTRACT_OWNER", mutate(base, api_changed)),
        ("AUTOMATIC_MERGE", mutate(base, self_merge)),
        ("AUTOMATIC_MERGE", mutate(base, decision_field)),
        ("FORBIDDEN_EDGE_ZERO_BUT_BEHAVIOR_FAILED", mutate(base, behavior_failed)),
        ("NEW_CYCLE_OR_LAYER_VIOLATION", mutate(base, cycle)),
        ("BEHAVIOR_DENOMINATOR_ABSENT", mutate(base, no_denominator)),
        ("ROLLBACK_WITHOUT_REGRESSION", mutate(base, spurious_rollback)),
        ("UNREADABLE_INPUT", mutate(base, wrong_schema)),
    ]


def rollback_mutations(base: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    def not_reverted(row: dict) -> None:
        row["rollback"]["applied_change_reverted"] = False

    def moving_restore(row: dict) -> None:
        row["rollback"]["restored_commit"] = "HEAD"

    def no_rollback(row: dict) -> None:
        del row["rollback"]

    return [
        ("ROLLBACK_NOT_REVERTED", mutate(base, not_reverted)),
        ("STALE_SUBJECT", mutate(base, moving_restore)),
        # The same readback with the rollback record removed: a behavior failure
        # with nowhere honest to go is refused rather than terminated.
        ("FORBIDDEN_EDGE_ZERO_BUT_BEHAVIOR_FAILED", mutate(base, no_rollback)),
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
                    '"receipt_id": "DTCR-R1-001"', '"receipt_id": "DTCR-R1-009"', 1
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
            for key in ARTIFACTS:
                artifact = document[key]
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

        languages = {
            document["usage_signature"]["adapter"]["language"] for document in projections.values()
        }
        declared_languages = enum_at(schemas[SIGNATURE], ("properties", "adapter", "properties", "language", "enum"))

        # 4. every named refusal, from a single-field delta.
        cases = [
            ("python-order-domain.json", candidate_mutations),
            ("python-order-domain-rolled-back.json", rollback_mutations),
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
        malformed["changeset"]["lease_writers"] = 42
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
        f"languages_exercised={len(languages)}/{len(declared_languages)} "
        f"applied_on_real_codebase=NOT_EXERCISED"
    )
    if failures:
        for failure in failures:
            print(f"DTCR-R1-SELFTEST-RED {failure}", file=sys.stderr)
        return 2
    print(
        f"DTCR-R1-SELFTEST-GREEN {len(REQUESTS)} projections byte-stable and current, "
        f"{composition} emitted artifacts validate against their committed schemas, "
        f"{covered} declared state values all emitted by a real compilation, "
        f"{refusals} named refusals fired from single-field deltas"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
