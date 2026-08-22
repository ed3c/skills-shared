#!/usr/bin/env python3
"""Execute the R2 cross-repository Expand and Contract compiler as a deciding gate.

Every check runs `compile_r2.py` as a subprocess and reads its exit code.
Nothing imports it and trusts a return value, because what a caller gets is an
exit code.

    fixture      two disposable git repositories are built from pinned bytes and
                 a pinned identity, their commits are compared against the
                 recorded subject, and each head is shown absent from the other
                 repository by a real `git cat-file` exit code. That absence is
                 the physical fact under FALSE_CROSS_REPO_GIT_PARENT, and it is
                 an independent arrival from the schema keyword and the compiler
                 refusal that restate it.
    stability    every committed projection is what its request compiles to, two
                 runs produce identical bytes, and a planted byte turns --check
                 red -- otherwise --check compares nothing.
    consumed     every contract-compatibility-result a request carries validates
                 against the frozen schema that types it. This protocol consumes
                 compatibility verdicts and produces none, so the frozen schema
                 is the boundary the requests have to hold to.
    composition  every emitted artifact validates against the committed schema
                 that types it, so the compiler and the contract cannot drift
                 apart while both stay green on their own.
    coverage     every value in the enums those schemas declare is emitted by a
                 real compilation of a committed request, except exactly the
                 values recorded below as unreachable at this head. The
                 exception list is asserted as an equality rather than printed
                 as a footnote: a value that becomes reachable, or a new value
                 nothing reaches, turns this lane red and asks a person to say
                 which it is.
    refusal      every named refusal fires from a single-field delta against a
                 request that compiles green, and every refusal code the
                 compiler declares is either fired here or recorded as
                 unreachable for the same reason its lane is.
    hollow       a request with every lane present and every lane empty produces
                 no artifact at all -- not a receipt full of absences, which
                 downstream reads as a run that happened and found nothing.
    controls     every schema-level refusal control is refused by the schema it
                 names and validates once the keyword its `refused_by` names is
                 removed, so a control refused by something else is caught
                 rather than credited.

Nothing here deploys anything, serves a request or observes traffic. The two
repositories exist for the duration of this process and are deleted with it;
every lane downstream of a deployment records its absence by name.

Exit 0 green, 2 a case failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import re
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
        "schemas against compiled output; skipping them would report the same green as "
        "running them.",
        file=sys.stderr,
    )
    raise SystemExit(70)

import fixture_repos

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
COMPILER = HERE / "compile_r2.py"
FIXTURES = HERE / "fixtures"
SCHEMAS = SKILL / "references" / "schemas"

RECEIPT = "dtcr/refactor-r2-receipt/v1"
BINDING = "dtcr/refactor-r2-binding/v1"
COMPATIBILITY = "dtcr/contract-compatibility-result/v1"

REQUESTS = (
    "two-repo-expand-contract.json",
    "two-repo-stopped-with-rollback.json",
    "two-repo-rolled-back.json",
    "two-repo-contract-verdict-absent.json",
)
ARTIFACTS = ("repository_binding", "receipt")

OTHER_DIGEST = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"


def values(*items: Any) -> set[Any]:
    return set(items)


def receipt_of(projection: dict) -> dict:
    return projection["receipt"]


# label -> (schema identity, path to the enum inside that schema, extractor over
# one projection). The denominator is read from the committed schema on the run,
# so a lane a sibling adds is covered on the run it lands.
COVERAGE: tuple[tuple[str, str, tuple[str, ...], Callable[[dict], set]], ...] = (
    (
        "terminal_state",
        RECEIPT,
        ("properties", "terminal_state", "enum"),
        lambda p: values(receipt_of(p)["terminal_state"]),
    ),
    (
        "phases",
        RECEIPT,
        ("properties", "phases_entered", "items", "enum"),
        lambda p: set(receipt_of(p)["phases_entered"]) | values(receipt_of(p)["last_phase_entered"]),
    ),
    (
        "blocked_on",
        RECEIPT,
        ("properties", "blocked_on", "items", "enum"),
        lambda p: set(receipt_of(p)["blocked_on"]),
    ),
    (
        "contract_outcome",
        RECEIPT,
        ("properties", "contract", "properties", "runs", "items", "properties", "outcome", "enum"),
        lambda p: values(receipt_of(p)["contract"]["outcome"])
        | {run["outcome"] for run in receipt_of(p)["contract"]["runs"]},
    ),
    (
        "adapter_capability_class",
        RECEIPT,
        ("properties", "contract", "properties", "adapter", "properties", "capability_class", "enum"),
        lambda p: values(receipt_of(p)["contract"]["adapter"]["capability_class"]),
    ),
    (
        "publication_intent",
        RECEIPT,
        ("properties", "contract", "properties", "publication", "properties", "intent", "enum"),
        lambda p: values(receipt_of(p)["contract"]["publication"]["intent"]),
    ),
    (
        "content_rights_admission",
        RECEIPT,
        (
            "properties", "contract", "properties", "publication", "properties", "rights",
            "properties", "content_rights_admission", "enum",
        ),
        lambda p: values(receipt_of(p)["contract"]["publication"]["rights"]["content_rights_admission"]),
    ),
    (
        "coexistence_runtime",
        RECEIPT,
        ("properties", "provider_coexistence", "properties", "runtime", "enum"),
        lambda p: values(receipt_of(p)["provider_coexistence"]["runtime"]),
    ),
    (
        "symbol_completeness",
        RECEIPT,
        ("$defs", "symbol_resolution", "properties", "completeness", "enum"),
        lambda p: {
            receipt_of(p)["provider_coexistence"][key]["completeness"]
            for key in ("legacy_symbol", "new_symbol")
        },
    ),
    (
        "migration_state",
        RECEIPT,
        ("properties", "consumer", "properties", "migration_state", "enum"),
        lambda p: values(receipt_of(p)["consumer"]["migration_state"]),
    ),
    (
        "fallback_arrival_state",
        RECEIPT,
        (
            "properties", "consumer", "properties", "fallback", "properties",
            "arrival_state", "enum",
        ),
        lambda p: {
            receipt_of(p)["consumer"]["fallback"]["arrival_state"]
        } if "fallback" in receipt_of(p)["consumer"] else set(),
    ),
    (
        "observation_state",
        RECEIPT,
        ("properties", "observation", "properties", "state", "enum"),
        lambda p: values(receipt_of(p)["observation"]["state"]),
    ),
    (
        "idempotency_state",
        RECEIPT,
        ("properties", "idempotency", "properties", "state", "enum"),
        lambda p: values(receipt_of(p)["idempotency"]["state"]),
    ),
    (
        "contraction_authorization",
        RECEIPT,
        ("properties", "contraction", "properties", "authorization", "enum"),
        lambda p: values(receipt_of(p)["contraction"]["authorization"]),
    ),
    (
        "caller_index_completeness",
        RECEIPT,
        ("$defs", "index_provenance", "properties", "completeness", "enum"),
        lambda p: {
            receipt_of(p)["contraction"]["caller_index"]["completeness"]
        } if "caller_index" in receipt_of(p)["contraction"] else set(),
    ),
    (
        "rollback_disposition",
        RECEIPT,
        ("properties", "rollback", "items", "properties", "disposition", "enum"),
        lambda p: {row["disposition"] for row in receipt_of(p).get("rollback", [])},
    ),
    (
        "applied_on_real_codebase",
        RECEIPT,
        ("properties", "establishes", "properties", "applied_on_real_codebase", "enum"),
        lambda p: values(receipt_of(p)["establishes"]["applied_on_real_codebase"]),
    ),
    (
        "repository_role",
        BINDING,
        ("properties", "repositories", "items", "properties", "role", "enum"),
        lambda p: {row["role"] for row in p["repository_binding"]["repositories"]},
    ),
)

# The declared values no committed request reaches at this head, each with the
# reason and the lane that owns it. Asserted as an equality against what the
# coverage lane finds missing, so this table cannot quietly disagree with the
# schemas: a value that becomes reachable turns the run red just as loudly as a
# new value nothing reaches.
UNREACHABLE_AT_THIS_HEAD: dict[tuple[str, str], str] = {
    ("phases", "E1_DUAL_RUN_AND_TELEMETRY"):
        "entering the dual-run phase needs observed traffic, which needs a deployed "
        "consumer canary; that lane is not this one and has never run",
    ("phases", "C2_LEGACY_CONTRACTION"):
        "entering the contraction phase needs a Human authorization naming an exact "
        "head, and a fixture that carried one would be fabricating the admission",
    ("terminal_state", "CANDIDATE_RECEIPT"):
        "a candidate needs the dual-run lane observed and nothing blocked; both are "
        "absences at this head, so no committed request reaches it",
    ("adapter_capability_class", "JSON_SCHEMA"):
        "a declared capability class with no vendored provider. A fixture differing "
        "from another only by this string would report repetition as coverage",
    ("adapter_capability_class", "ASYNCAPI"):
        "same: declared so the method is not Protobuf-only, exercised by nothing",
    ("publication_intent", "PUBLISHED"):
        "publishing the contract to a registry is a separately authorized operation "
        "and nothing in this wave publishes; the refusals around it still fire",
    ("content_rights_admission", "ADMITTED"):
        "content rights are admitted by a person against a registry's terms, and no "
        "run of this protocol can record that admission on its own behalf",
    ("coexistence_runtime", "OBSERVED"):
        "two surfaces serving at once is a fact about a deployment; both symbols "
        "resolving is a fact about a tree, and only the second is available here",
    ("symbol_completeness", "COMPLETE_FOR_ANALYSED_INPUTS"):
        "no symbol index at this head resolves every reference; the SCIP lane that "
        "would is a separate, unlanded issue",
    ("fallback_arrival_state", "EXERCISED"):
        "a fallback is exercised by an arrival, and nothing has called this consumer",
    ("observation_state", "OBSERVED"):
        "a fixture serves no requests, so the only truthful values are the absences",
    ("idempotency_state", "EXERCISED"):
        "exercising an idempotency mechanism needs a duplicate arrival to deduplicate",
    ("contraction_authorization", "ADMITTED"):
        "the contraction admission is a Human decision recorded against an exact head",
    ("caller_index_completeness", "COMPLETE_FOR_ANALYSED_INPUTS"):
        "same index ceiling as the provider symbols: every caller count here is a "
        "lower bound over a partial index",
    ("applied_on_real_codebase", "EXERCISED"):
        "no repository is read, written or deployed by this compiler; the bounded "
        "consumer canary that would move this value belongs to the live-canary lane",
}

# Refusal codes the compiler declares that no committed request can be one field
# away from, for the same reason a lane above is unreachable. Asserted the same
# way, so a code that stops being fired is caught rather than quietly retired.
UNFIRED_REFUSALS: dict[str, str] = {
    "ROLLBACK_WITHOUT_STOP":
        "firing it needs a run with an empty blocked_on list, and every committed "
        "request is blocked on at least the absent dual-run lane",
}


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


def declared_refusal_codes() -> set[str]:
    """Every code `compile_r2.py` can raise, read from its own bytes."""
    source = COMPILER.read_text(encoding="utf-8")
    return set(re.findall(r'raise Refused\(\s*"([A-Z_]+)"', source))


# --------------------------------------------------------------------------
# knockout, the half that makes a schema control mean something
# --------------------------------------------------------------------------

def parse_keyword_path(path: str) -> list[str | int]:
    segments: list[str | int] = []
    for token in path.split("."):
        head, *indices = re.split(r"\[(\d+)\]", token)
        if head:
            segments.append(head)
        segments.extend(int(value) for value in indices if value != "")
    return segments


def remove_keyword(document: Any, path: str) -> None:
    """Delete exactly the keyword `path` names, and nothing else.

    The one licensed extra deletion is the `not: {}` trap: emptying a `not` turns
    it from one guard into a refusal of everything, so the knockout would stay
    red and credit the guard it was trying to disprove.
    """
    segments = parse_keyword_path(path)
    trail: list[tuple[Any, str | int]] = []
    node = document
    for segment in segments:
        trail.append((node, segment))
        node = node[segment]
    parent, key = trail[-1]
    del parent[key]
    if parent == {} and len(trail) >= 2:
        grandparent, parent_key = trail[-2]
        if parent_key == "not":
            del grandparent[parent_key]


def knock_out(schema: dict[str, Any], refused_by: str) -> dict[str, Any]:
    mutated = copy.deepcopy(schema)
    for path in refused_by.split(" and "):
        remove_keyword(mutated, path.strip())
    return mutated


# --------------------------------------------------------------------------
# the mutations. Each is a single field away from a request that compiles.
# --------------------------------------------------------------------------

def mutate(request: dict[str, Any], edit: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    copied = copy.deepcopy(request)
    edit(copied)
    return copied


def candidate_mutations(base: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    provider_head = base["binding"]["repositories"][0]["subject_commit"]

    def branch_subject(row: dict) -> None:
        row["binding"]["repositories"][0]["subject_commit"] = "main"

    def cross_repo_parent(row: dict) -> None:
        row["binding"]["repositories"][1]["ancestry_within_repository"] = [provider_head]

    def one_repository(row: dict) -> None:
        row["binding"]["repositories"] = row["binding"]["repositories"][:1]

    def one_role(row: dict) -> None:
        row["binding"]["repositories"][1]["role"] = "PROVIDER"

    def duplicate_binding(row: dict) -> None:
        row["binding"]["repositories"][1]["repository_binding_id"] = (
            row["binding"]["repositories"][0]["repository_binding_id"]
        )

    def undeclared_adapter(row: dict) -> None:
        row["contract"]["adapter"]["capability_class"] = "GRAPHQL"

    def other_baseline(row: dict) -> None:
        row["contract"]["compatibility_runs"][1]["baseline"]["commit"] = (
            row["binding"]["repositories"][1]["ancestry_within_repository"][0]
        )

    def weakened_ruleset(row: dict) -> None:
        row["contract"]["compatibility_runs"][1]["provider"]["ruleset_digest"] = OTHER_DIGEST

    def drifted_stub(row: dict) -> None:
        row["contract"]["generated_artifacts"][1]["declared_digest"] = OTHER_DIGEST

    def published(row: dict) -> None:
        row["contract"]["publication"]["intent"] = "PUBLISHED"

    def account_as_rights(row: dict) -> None:
        row["contract"]["publication"]["rights"]["account_access"] = True

    def one_symbol_twice(row: dict) -> None:
        row["provider"]["new_symbol"]["symbol"] = row["provider"]["legacy_symbol"]["symbol"]

    def removes_legacy(row: dict) -> None:
        row["provider"]["removal_changesets"] = [
            {
                "change_unit_ref": "DTCR-CU-001",
                "removed_symbols": [row["provider"]["legacy_symbol"]["symbol"]],
            }
        ]

    def runtime_from_static(row: dict) -> None:
        row["provider"]["runtime"] = "OBSERVED"

    def no_fallback(row: dict) -> None:
        del row["consumer"]["fallback"]

    def fallback_exercised(row: dict) -> None:
        row["consumer"]["fallback"]["arrival_state"] = "EXERCISED"

    def continuity_claim(row: dict) -> None:
        row["observation"]["service_continuity"] = "no request failed during the window"

    def observed_without_denominator(row: dict) -> None:
        row["observation"]["state"] = "OBSERVED"

    def no_mechanism(row: dict) -> None:
        row["idempotency"]["mechanism"] = ""

    def arrival_without_traffic(row: dict) -> None:
        row["idempotency"]["arrival"] = "the arrival that would have exercised the dedupe"

    def self_authorized(row: dict) -> None:
        row["contraction"]["authorization"] = "AUTO_ON_ZERO_CALLERS"

    def decision_field(row: dict) -> None:
        row["contraction"]["approved"] = True

    def no_caller_index(row: dict) -> None:
        del row["contraction"]["caller_index"]

    def complete_partial_index(row: dict) -> None:
        row["contraction"]["caller_index"]["completeness"] = "COMPLETE_FOR_ANALYSED_INPUTS"

    def wrong_schema(row: dict) -> None:
        row["schema"] = "dtcr/refactor-r2-request/v2"

    return [
        ("STALE_SUBJECT", mutate(base, branch_subject)),
        ("FALSE_CROSS_REPO_GIT_PARENT", mutate(base, cross_repo_parent)),
        ("SINGLE_REPOSITORY_SUBJECT", mutate(base, one_repository)),
        ("ROLE_SET_INCOMPLETE", mutate(base, one_role)),
        ("DUPLICATE_REPOSITORY_BINDING", mutate(base, duplicate_binding)),
        ("UNSUPPORTED_CONTRACT_ADAPTER_PROMOTED_TO_SUPPORTED", mutate(base, undeclared_adapter)),
        ("CONTRACT_BASELINE_MISMATCH", mutate(base, other_baseline)),
        ("BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING", mutate(base, weakened_ruleset)),
        ("GENERATED_STUB_DRIFT", mutate(base, drifted_stub)),
        ("SCHEMA_PUBLISHED_WITHOUT_EXACT_SOURCE", mutate(base, published)),
        ("BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS", mutate(base, account_as_rights)),
        ("PROVIDER_COEXISTENCE_NOT_BOUND", mutate(base, one_symbol_twice)),
        ("PROVIDER_REMOVES_LEGACY_BEFORE_CONSUMER_MIGRATION", mutate(base, removes_legacy)),
        ("RUNTIME_COEXISTENCE_DERIVED_FROM_STATIC_FACTS", mutate(base, runtime_from_static)),
        ("CONSUMER_SWITCH_WITHOUT_FALLBACK", mutate(base, no_fallback)),
        ("FALLBACK_ARRIVAL_WITHOUT_TRAFFIC", mutate(base, fallback_exercised)),
        ("TELEMETRY_ABSENCE_PROMOTED_TO_SUCCESS", mutate(base, continuity_claim)),
        ("OBSERVATION_WITHOUT_DENOMINATOR", mutate(base, observed_without_denominator)),
        ("DUAL_RUN_WITHOUT_IDEMPOTENCY", mutate(base, no_mechanism)),
        ("DUAL_RUN_WITHOUT_IDEMPOTENCY", mutate(base, arrival_without_traffic)),
        ("AUTOMATIC_CONTRACTION_OR_MERGE", mutate(base, self_authorized)),
        ("AUTOMATIC_CONTRACTION_OR_MERGE", mutate(base, decision_field)),
        ("NO_REMAINING_CALLERS_IN_PARTIAL_INDEX", mutate(base, no_caller_index)),
        ("NO_REMAINING_CALLERS_IN_PARTIAL_INDEX", mutate(base, complete_partial_index)),
        ("UNREADABLE_INPUT", mutate(base, wrong_schema)),
    ]


def stop_mutations(base: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    def one_row_only(row: dict) -> None:
        row["rollback"] = row["rollback"][:1]

    def moving_restore(row: dict) -> None:
        row["rollback"][1]["restored_commit"] = "HEAD"

    return [
        ("ROLLBACK_ROW_MISSING_FOR_BINDING", mutate(base, one_row_only)),
        ("STALE_SUBJECT", mutate(base, moving_restore)),
    ]


# --------------------------------------------------------------------------

def main() -> int:
    failures: list[str] = []
    schemas = schema_documents()
    for identity in (RECEIPT, BINDING, COMPATIBILITY):
        if identity not in schemas:
            print(f"DTCR-R2-SELFTEST-RED {identity} is not in the tree", file=sys.stderr)
            return 2
    validators = {identity: Draft202012Validator(doc) for identity, doc in schemas.items()}

    # 0. the two disposable repositories, and the cross-repository absence that
    #    FALSE_CROSS_REPO_GIT_PARENT is about. A typed absence when git is not
    #    installed; never a silent pass.
    fixture_lane = "PROVIDER_UNAVAILABLE"
    git_arrivals = 0
    if fixture_repos.git_available():
        recorded = fixture_repos.recorded()
        with tempfile.TemporaryDirectory(prefix="dtcr-r2-scratch-") as scratch:
            built = fixture_repos.build(Path(scratch))
            for name in ("provider", "consumer"):
                for key in ("base_commit", "base_tree", "head_commit", "head_tree"):
                    git_arrivals += 1
                    if built[name][key] != recorded[name][key]:
                        failures.append(
                            f"{name}.{key} rebuilt to {built[name][key]} against the recorded "
                            f"{recorded[name][key]}: the committed projections carry the "
                            f"recorded value and are stale"
                        )
            provider = Path(built["provider"]["path"])
            consumer = Path(built["consumer"]["path"])
            for label, repo, oid in (
                ("provider head in consumer", consumer, built["provider"]["head_commit"]),
                ("consumer head in provider", provider, built["consumer"]["head_commit"]),
            ):
                git_arrivals += 1
                if not fixture_repos.object_absent(repo, oid):
                    failures.append(
                        f"{label}: the object resolves, so these two repositories share a "
                        f"graph and the cross-repository ancestry law has nothing to refuse"
                    )
        fixture_lane = "EXERCISED"

    with tempfile.TemporaryDirectory(prefix="dtcr-r2-scratch-") as scratch:
        work = Path(scratch)

        # 1. stability, against the committed bytes a caller would read.
        stability = 0
        for request in REQUESTS:
            source = FIXTURES / request
            projection = compiled_name(request)
            stability += 1
            result = run("--input", str(source), "--out", str(projection), "--check")
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

        # 2. the consumed lane: every compatibility verdict a request carries is
        #    a valid instance of the frozen schema that types it.
        consumed = 0
        for request in (*REQUESTS, "two-repo-hollow.json"):
            document = json.loads((FIXTURES / request).read_text(encoding="utf-8"))
            for index, verdict in enumerate(document["contract"]["compatibility_runs"]):
                consumed += 1
                errors = sorted(validators[COMPATIBILITY].iter_errors(verdict), key=str)
                if errors:
                    failures.append(
                        f"{request}: compatibility_runs[{index}] does not validate against "
                        f"the frozen {COMPATIBILITY}: {errors[0].message}"
                    )

        # 3. composition against the committed schemas.
        composition = 0
        projections: dict[str, dict] = {}
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

        # 4. every declared state is emitted, or recorded as unreachable here.
        covered = 0
        unreached: dict[tuple[str, str], None] = {}
        for label, identity, path, extract in COVERAGE:
            declared = enum_at(schemas[identity], path)
            emitted: set[str] = set()
            for document in projections.values():
                emitted |= extract(document)
            covered += len(declared)
            for value in sorted(declared - emitted):
                unreached[(label, value)] = None
            stray = sorted(emitted - declared)
            if stray:
                failures.append(
                    f"{label}: the compiler emitted {', '.join(stray)}, which {identity} "
                    f"does not declare"
                )
        for row in sorted(set(unreached) - set(UNREACHABLE_AT_THIS_HEAD)):
            failures.append(
                f"{row[0]}: {row[1]} is declared and no committed request compiles to it, "
                f"and it is not recorded as unreachable. A state only a test can construct "
                f"is not a state the protocol reaches"
            )
        for row in sorted(set(UNREACHABLE_AT_THIS_HEAD) - set(unreached)):
            failures.append(
                f"{row[0]}: {row[1]} is recorded as unreachable at this head and a "
                f"committed request now reaches it. Remove the record rather than "
                f"leaving the ceiling saying something the tree disagrees with"
            )

        # The phase enum is declared twice, on phases_entered and on
        # last_phase_entered. Two lists that can disagree is one list too many.
        if enum_at(schemas[RECEIPT], ("properties", "phases_entered", "items", "enum")) != enum_at(
            schemas[RECEIPT], ("properties", "last_phase_entered", "enum")
        ):
            failures.append(
                "phases_entered and last_phase_entered declare different phase enums, so a "
                "run could stop at a phase the protocol does not list"
            )

        # 5. every named refusal, from a single-field delta.
        refusals = 0
        fired: set[str] = set()
        cases = [
            ("two-repo-expand-contract.json", candidate_mutations),
            ("two-repo-stopped-with-rollback.json", stop_mutations),
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
                else:
                    fired.add(code)

        declared_codes = declared_refusal_codes()
        for code in sorted(declared_codes - fired - set(UNFIRED_REFUSALS)):
            failures.append(
                f"{code} is a refusal the compiler can raise and no single-field delta "
                f"fires it, so nothing here shows it is reachable or that it names what "
                f"it fires on"
            )
        for code in sorted(set(UNFIRED_REFUSALS) - (declared_codes - fired)):
            failures.append(
                f"{code} is recorded as unfired and is either fired now or no longer "
                f"declared; the record and the compiler disagree"
            )

        # 6. the hollow control: every lane present, every lane empty, no artifact.
        hollow_source = FIXTURES / "two-repo-hollow.json"
        hollow_out = work / "hollow.compiled.json"
        hollow = run("--input", str(hollow_source), "--out", str(hollow_out))
        refusals += 1
        if hollow.returncode != 2:
            failures.append(
                f"the hollow request exited {hollow.returncode} rather than being refused. "
                f"A request whose every lane is present and empty must produce no artifact"
            )
        elif "PROVIDER_COEXISTENCE_NOT_BOUND" not in hollow.stderr:
            failures.append(
                f"the hollow request was refused by something other than its empty "
                f"evidence: {hollow.stderr.strip()}"
            )
        if hollow_out.exists():
            failures.append(
                "the hollow request was refused and a projection was written anyway, so a "
                "refused run leaves an artifact downstream can read"
            )

        # a request the compiler cannot read at all is 64, not 2: a malformed
        # input and a refused one are different facts about the caller.
        broken = work / "broken.json"
        malformed = json.loads((FIXTURES / REQUESTS[0]).read_text(encoding="utf-8"))
        malformed["binding"]["repositories"][0]["ancestry_within_repository"] = 42
        broken.write_text(json.dumps(malformed), encoding="utf-8")
        refusals += 1
        unusable = run("--input", str(broken))
        if unusable.returncode != 64:
            failures.append(
                f"a structurally unusable request exited {unusable.returncode} rather than "
                f"64, so a broken caller reads as a refused one"
            )

    # 7. schema-level refusal controls, with the knockout that discriminates them.
    inventory = json.loads((FIXTURES / "schema-controls.json").read_text(encoding="utf-8"))
    controls = inventory["controls"]
    identities = [f"{row['schema_id']}/{row['case_id']}" for row in controls]
    if len(set(identities)) != len(identities):
        failures.append("two schema controls share an identity; a failure could not name one")
    discriminating = 0
    for row in controls:
        case_id, identity = row["case_id"], row["schema_id"]
        validator = validators.get(identity)
        if validator is None:
            failures.append(f"control {case_id} names schema {identity}, not in the tree")
            continue
        if validator.is_valid(row["instance"]):
            failures.append(f"control {case_id} is not refused by {identity} at all")
            continue
        try:
            mutated = knock_out(schemas[identity], row["refused_by"])
        except (KeyError, IndexError, TypeError) as error:
            failures.append(
                f"control {case_id}: refused_by names {row['refused_by']!r}, which does "
                f"not resolve in the schema ({error!r})"
            )
            continue
        errors = sorted(Draft202012Validator(mutated).iter_errors(row["instance"]), key=str)
        if errors:
            failures.append(
                f"control {case_id} is still refused after {row['refused_by']!r} was "
                f"removed, so it does not discriminate the guard it names: "
                f"{errors[0].message}"
            )
            continue
        discriminating += 1

    print(
        f"requests={len(REQUESTS)} stability_checks={stability} consumed_verdicts={consumed} "
        f"schema_compositions={composition} state_values_covered={covered} "
        f"unreachable_at_this_head={len(UNREACHABLE_AT_THIS_HEAD)} "
        f"refusal_deltas={refusals} schema_controls={len(controls)} "
        f"knockouts={discriminating} git_arrivals={git_arrivals} "
        f"two_repository_fixture={fixture_lane} applied_on_real_codebase=NOT_EXERCISED "
        f"live_canary=NOT_EXERCISED dual_run_observation=NOT_OBSERVED "
        f"contraction_authorization=HUMAN_ADMIT_REQUIRED"
    )
    if failures:
        for failure in failures:
            print(f"DTCR-R2-SELFTEST-RED {failure}", file=sys.stderr)
        return 2
    print(
        f"DTCR-R2-SELFTEST-GREEN {len(REQUESTS)} projections byte-stable and current over a "
        f"two-repository git fixture, {composition} emitted artifacts and {consumed} consumed "
        f"compatibility verdicts validate against their committed schemas, {covered} declared "
        f"state values emitted by a real compilation except the "
        f"{len(UNREACHABLE_AT_THIS_HEAD)} recorded as unreachable at this head, "
        f"{refusals} named refusals fired from single-field deltas, {discriminating} of "
        f"{len(controls)} schema controls discriminating under knockout of their own keyword"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
