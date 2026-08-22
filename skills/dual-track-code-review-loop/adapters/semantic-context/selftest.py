#!/usr/bin/env python3
"""Run the semantic-context adapter against its fixture, and plant every falsifier.

Five lanes, in this order, because a refusal credited to a harness that was
already red proves nothing about the guard it names:

    positives   the deterministic run: register, project, index, query,
                consume, rebuild, delete, over the committed public fixture,
                with the denominators printed rather than described
    plants      the twelve named falsifiers, each planted as a single-field
                delta from a green artifact or as a call the adapter refuses,
                and each recorded under the code and mechanism that actually
                fired -- with one code renamed in a copy of the adapter to show
                the code half of that comparison goes red on demand
    receipts    the committed receipts are reproduced from this tree; the
                deterministic one has to match byte for byte, and the provider
                lane one is checked for shape without needing the provider
    leaks       every committed file in this subtree is scanned for a resolved
                address or a private locator, and the scanner is shown to bite
    provider    the LanceDB lane's state on this host, typed, never faked

Every planted case names the mechanism it expects. A case that starts passing
for a different reason is visible as a changed mechanism rather than as a still
green run.

Exit 0 green, 2 a case failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import socket
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


class NetworkRefused(AssertionError):
    """The default suite is zero-network. Opening a socket is a failed run."""


def _refuse_socket(*args: Any, **kwargs: Any):
    raise NetworkRefused(
        "the default semantic-context suite is zero-network and something tried to open a socket"
    )


# Armed before the adapter is imported, so an import-time call is caught too.
# "No network" written in a docstring is a claim; this is the arrival.
socket.socket = _refuse_socket  # type: ignore[assignment]
socket.create_connection = _refuse_socket  # type: ignore[assignment]

sys.path.insert(0, str(Path(__file__).resolve().parent))

import adapter as A  # noqa: E402
from adapter import ProviderUnavailable, Refusal  # noqa: E402

ADAPTER_DIR = Path(__file__).resolve().parent
FIXTURE = A.load_fixture()
CEILINGS = {item["document_ref"]: item for item in FIXTURE["freshness_ceilings"]}
DOCUMENTS = {entry["document"]["document_id"]: entry for entry in FIXTURE["documents"]}

failures: list[str] = []
cases = 0
plants: list[tuple[str, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    global cases
    cases += 1
    if not condition:
        failures.append(f"{name}: {detail or 'the assertion did not hold'}")


def refuses(falsifier: str, mechanism: str, thunk: Callable[[], Any]) -> None:
    """The planted case has to go red, for the mechanism *and* the code it names.

    Reading only `refusal.mechanism` left the falsifier half of every row
    unverified: renaming a code in the adapter, or collapsing all of them to one
    constant, kept this suite green. So both halves are compared, and the row is
    recorded from the refusal the adapter actually raised rather than from the
    literal argued above -- which is what makes the REQUIRED_FALSIFIERS
    accounting below an observation instead of a tautology.
    """
    global cases
    cases += 1
    try:
        thunk()
    except Refusal as refusal:
        if mechanism not in refusal.mechanism:
            failures.append(
                f"{falsifier} was refused by {refusal.mechanism!r}, not by the {mechanism!r} it names"
            )
            return
        if refusal.falsifier != falsifier:
            failures.append(
                f"{falsifier} was refused under the falsifier code {refusal.falsifier!r}, "
                f"not the {falsifier!r} it names"
            )
            return
        plants.append((refusal.falsifier, refusal.mechanism))
        return
    failures.append(f"{falsifier} was not refused ({mechanism} did not fire)")


def control(schema: str, case_id: str) -> dict:
    """One planted instance from a frozen schema's own refusal controls.

    Reading the instance from the contract rather than writing it here keeps the
    planted private address out of this subtree entirely, and keeps the plant
    bound to the control the schema says it kills.
    """
    document = json.loads((A.SCHEMA_DIR / f"{schema}.schema.json").read_text(encoding="utf-8"))
    for item in document.get("x-refusal-controls", []):
        if item["case_id"] == case_id:
            return copy.deepcopy(item["instance"])
    raise AssertionError(f"{case_id} is not a refusal control of {schema}")


def with_value(document: dict, value: Any, *path: str) -> dict:
    mutated = copy.deepcopy(document)
    cursor = mutated
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    return mutated


def without(document: dict, *path: str) -> dict:
    mutated = copy.deepcopy(document)
    cursor = mutated
    for key in path[:-1]:
        cursor = cursor[key]
    del cursor[path[-1]]
    return mutated


def loaded(skip: str | None = None, freshness_for: Callable[[str], dict | None] | None = None) -> A.ReferenceBackend:
    """A store loaded from the committed fixture, projected and indexed."""
    store = A.ReferenceBackend(A.TASK_ADMISSION)
    for reference in FIXTURE["back_references"]:
        store.register_back_reference(reference)
    for entry in FIXTURE["documents"]:
        document = entry["document"]
        if document["document_id"] == skip:
            continue
        ceiling = freshness_for(document["document_id"]) if freshness_for else CEILINGS.get(document["document_id"])
        store.register(document, ceiling, entry["content"])
    store.project_all()
    store.build_index()
    return store


CHECKOUT = {
    "text": "checkout ledger client write path persistence rule",
    "lane": "VECTOR",
    "top_k": 4,
    "filters": [{"field": "subsystem_tag", "value": "checkout"}],
}


# ---------------------------------------------------------------------------
# lane 1: positives
# ---------------------------------------------------------------------------

def positives() -> dict[str, Any]:
    print("positives")
    # The zero-network guard is checked for teeth before anything leans on it:
    # a guard that silently stopped being armed reports the same green.
    try:
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        check("the zero-network guard is armed", False, "a socket was opened without refusal")
    except NetworkRefused:
        check("the zero-network guard is armed", True)

    for name in A.CONSUMED_SCHEMAS:
        check(
            f"frozen schema {name} is present",
            (A.SCHEMA_DIR / f"{name}.schema.json").is_file(),
            "the adapter consumes it and cannot validate without it",
        )

    run = A.deterministic_run(FIXTURE)
    store: A.ReferenceBackend = run["store"]
    check("every fixture document registered", len(store.documents) == 9, str(len(store.documents)))
    check("every back reference registered", len(store.back_references) == 9, str(len(store.back_references)))
    check(
        "all six document kinds and all three reference kinds are exercised",
        len({entry["document"]["document_kind"] for entry in FIXTURE["documents"]}) == 6
        and len({item["reference_kind"] for item in FIXTURE["back_references"]}) == 3,
    )

    # The private-carrier record is registrable by digest and back reference and
    # is not projectable here. Its absence is typed, and it appears in no result.
    check(
        "the private-carrier record is registered and its content absence is typed",
        store.absences == {"DTCR-DOC-006": "CONSUMER_LOCAL_CONTENT_ABSENT"},
        str(store.absences),
    )
    returned = {row["document_ref"] for query in run["queries"] for row in query["rows"]}
    check("no private-carrier row was ever returned", "DTCR-DOC-006" not in returned, str(sorted(returned)))
    check(
        "no projection was made from a private plane",
        all(
            receipt["data_handling"]["content_plane"] == "PUBLIC_TREE"
            for receipt in store.projections.values()
        ),
    )

    checkout = next(query for query in run["queries"] if query["name"] == "checkout-persistence")
    check("top_k bounds the result", len(checkout["rows"]) <= checkout["top_k"], str(len(checkout["rows"])))
    positions = {row["document_ref"]: row["rank"] for row in checkout["rows"]}
    check(
        "the superseded record sits below the record that replaced it",
        positions["DTCR-DOC-002"] > positions["DTCR-DOC-003"],
        str(positions),
    )
    check(
        "and it sat there despite scoring higher, which is the whole point",
        checkout["demoted_by_supersession"] == ["DTCR-DOC-002"]
        and next(row for row in checkout["rows"] if row["document_ref"] == "DTCR-DOC-002")["score"]
        > next(row for row in checkout["rows"] if row["document_ref"] == "DTCR-DOC-003")["score"],
        str(checkout["rows"]),
    )

    not_applicable = next(query for query in run["queries"] if query["lane"] == "NOT_APPLICABLE")
    check(
        "the not-applicable lane carries no rows and no result size",
        not_applicable["rows"] == [] and not_applicable["top_k"] == "NOT_APPLICABLE",
        str(not_applicable),
    )
    check("consumed rows were listed for every rank read", run["consumed_total"] == 5, str(run["consumed_total"]))

    rebuild, delete = run["lifecycle"]
    check(
        "a rebuild reproduces the same index from the same projections",
        rebuild["index_digest_after"] == rebuild["index_digest_before"],
        str(rebuild),
    )
    check(
        "a delete leaves no digest behind",
        delete["index_digest_after"] == "INDEX_ABSENT_AFTER_DELETE" and delete["projection_receipt_refs"] == [],
        str(delete),
    )
    check(
        "neither moved task admission",
        run["admission_digest"] == A.digest_of(dict(A.TASK_ADMISSION))
        and all(item["changes"]["task_admission"] == "UNCHANGED" for item in run["lifecycle"]),
    )

    # The structural half of the same law: the port holds a read-only view, so
    # there is no write path to the admission mapping to begin with.
    try:
        store.task_admission["DTCR-TASK-001"] = "CLOSED"  # type: ignore[index]
        check("the port's view of task admission is read-only", False, "the assignment was accepted")
    except TypeError:
        check("the port's view of task admission is read-only", True)

    ceilings = [
        artifact["establishes"]
        for artifact in list(store.projections.values())
    ]
    check(
        "no projection receipt establishes anything",
        all(set(item.values()) == {False} for item in ceilings),
    )

    replay = A.build_receipt(FIXTURE)
    again = A.build_receipt(FIXTURE)
    check(
        "the deterministic lane is deterministic",
        A.digest_of(replay) == A.digest_of(again),
        "two runs over the same fixture disagreed",
    )
    print(
        f"  documents={len(store.documents)} projections={replay['index']['projection_receipts']} "
        f"index_rows={replay['index']['rows']} queries={len(run['queries'])} "
        f"consumed_rows={run['consumed_total']} lifecycle={len(run['lifecycle'])}"
    )
    return replay


# ---------------------------------------------------------------------------
# lane 2: the twelve falsifiers
# ---------------------------------------------------------------------------

def planted() -> None:
    print("plants")
    store = loaded()
    query, result = store.query(**CHECKOUT)
    manifest = store.consume(
        result,
        [1, 2],
        manifest_ref="context manifest for the planted review",
        task_ref="planted review",
        consumed_at="2026-08-22",
    )
    projection = store.projections["DTCR-PR-001"]
    _, not_applicable = store.query(
        "rename a local variable",
        "NOT_APPLICABLE",
        "NOT_APPLICABLE",
        [],
        "this task is a mechanical rename with no decision or incident that stored context could bear on",
    )

    # 1. ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE
    #
    # A registration with no `back_reference_ref` at all never reaches the
    # adapter's orphan guard: the frozen schema refuses it at the door, under
    # the one code that gate raises for every document it turns away. The row
    # is named for the code that is actually raised, because a row named for a
    # falsifier the adapter never utters is what F-02 was.
    entry = DOCUMENTS["DTCR-DOC-001"]
    refuses(
        "FROZEN_SCHEMA_REFUSED_THE_REGISTRATION",
        "semantic-document.schema.json required",
        lambda: A.ReferenceBackend(A.TASK_ADMISSION).register(
            without(entry["document"], "back_reference_ref"), None, entry["content"]
        ),
    )
    refuses(
        "ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE",
        "the back reference must be registered before the document",
        lambda: A.ReferenceBackend(A.TASK_ADMISSION).register(
            entry["document"], CEILINGS["DTCR-DOC-001"], entry["content"]
        ),
    )
    refuses(
        "ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE",
        "retrieval-result.schema.json properties/rows/items/required",
        lambda: A.enforce(
            "retrieval-result",
            {**result, "rows": [without(result["rows"][0], "back_reference_ref")]},
            "ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE",
            "the planted result",
        ),
    )

    # 2. WRONG_OR_STALE_SOURCE_DIGEST
    def tampered_digest() -> None:
        fresh = A.ReferenceBackend(A.TASK_ADMISSION)
        for reference in FIXTURE["back_references"]:
            fresh.register_back_reference(reference)
        fresh.register(with_value(entry["document"], "0" * 64, "document_digest"), None, entry["content"])

    refuses(
        "WRONG_OR_STALE_SOURCE_DIGEST",
        "document_digest must be the digest of the registered content",
        tampered_digest,
    )

    def digest_moved_under_the_index() -> None:
        drifting = loaded()
        drifting.documents["DTCR-DOC-001"] = with_value(
            drifting.documents["DTCR-DOC-001"], "f" * 64, "document_digest"
        )
        drifting.build_index()

    refuses(
        "WRONG_OR_STALE_SOURCE_DIGEST",
        "every projection is rebound to its document digest at build time",
        digest_moved_under_the_index,
    )

    # 3. PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT
    leaked = control("semantic-document", "DTCR-XC-DOC-002")["source_url"]
    refuses(
        "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",
        "scan_for_leaks URI scheme",
        lambda: A.scan_for_leaks({"fixture": {"path": leaked}}, "planted receipt"),
    )
    refuses(
        "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",
        "scan_for_leaks absolute path",
        lambda: A.scan_for_leaks({"fixture": {"path": "/private-carrier/incident-review.md"}}, "planted receipt"),
    )
    # The private locator planted in a back reference is refused by the frozen
    # schema before `register_back_reference` reaches any adapter law, so this
    # row carries that gate's code; the pointer is what names the law. The two
    # rows above are the ones that establish the falsifier itself.
    refuses(
        "FROZEN_SCHEMA_REFUSED_THE_BACK_REFERENCE",
        "source-back-reference.schema.json properties/repository_blob/properties/path/not",
        lambda: A.ReferenceBackend(A.TASK_ADMISSION).register_back_reference(
            control("source-back-reference", "DTCR-XC-BK-001")
        ),
    )

    # 4. VECTOR_TO_VECTOR_AUTHORITY_EDGE
    refuses(
        "FROZEN_SCHEMA_REFUSED_THE_BACK_REFERENCE",
        "source-back-reference.schema.json additionalProperties",
        lambda: A.ReferenceBackend(A.TASK_ADMISSION).register_back_reference(
            control("source-back-reference", "DTCR-XC-BK-002")
        ),
    )
    refuses(
        "VECTOR_TO_VECTOR_AUTHORITY_EDGE",
        "consumed-context-row.schema.json additionalProperties",
        lambda: A.enforce(
            "consumed-context-row",
            control("consumed-context-row", "DTCR-XC-CX-003"),
            "VECTOR_TO_VECTOR_AUTHORITY_EDGE",
            "the planted manifest entry",
        ),
    )

    # 5. RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED
    refuses(
        "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
        "reconcile_manifest compares the ranks read against the ranks listed",
        lambda: A.reconcile_manifest(result, manifest[:1], [1, 2]),
    )
    refuses(
        "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
        "reconcile_manifest compares the ranks listed against the rows returned",
        lambda: A.reconcile_manifest(
            {**result, "rows": result["rows"][:1]}, manifest, [1]
        ),
    )

    # 6. STALE_ADR_OVERRIDES_NEWER_EXPLICIT_DECISION
    def ordering_not_enforced() -> None:
        drifting = loaded()
        drifting.enforce_supersession_order = lambda rows: rows  # type: ignore[assignment]
        drifting.query(**CHECKOUT)

    refuses(
        "STALE_ADR_OVERRIDES_NEWER_EXPLICIT_DECISION",
        "assert_supersession_order compares the emitted order against supersession",
        ordering_not_enforced,
    )

    def superseded_offered_as_current() -> None:
        fresh = A.ReferenceBackend(A.TASK_ADMISSION)
        for reference in FIXTURE["back_references"]:
            fresh.register_back_reference(reference)
        stale = DOCUMENTS["DTCR-DOC-002"]
        fresh.register(
            stale["document"],
            with_value(CEILINGS["DTCR-DOC-002"], "CONTEXT_CANDIDATE", "usable_as"),
            stale["content"],
        )

    refuses(
        "FROZEN_SCHEMA_REFUSED_THE_FRESHNESS_CEILING",
        "semantic-freshness-ceiling.schema.json allOf/0/then",
        superseded_offered_as_current,
    )

    # 7. REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION
    def rebuild_moves_admission() -> None:
        drifting = loaded()
        original = A.ReferenceBackend.build_index

        def moving(self):  # the planted lifecycle operation writes into admission
            self._admission_source["DTCR-TASK-001"] = "CLOSED_BY_REBUILD"
            return original(self)

        A.ReferenceBackend.build_index = moving  # type: ignore[assignment]
        try:
            drifting.lifecycle("REBUILD", "2026-08-22")
        finally:
            A.ReferenceBackend.build_index = original  # type: ignore[assignment]
            A.TASK_ADMISSION["DTCR-TASK-001"] = "OPEN"

    refuses(
        "REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION",
        "the admission mapping is digested before and after every lifecycle operation",
        rebuild_moves_admission,
    )
    refuses(
        "REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION",
        "semantic-index-lifecycle-receipt.schema.json properties/changes/properties/task_admission/const",
        lambda: A.enforce(
            "semantic-index-lifecycle-receipt",
            control("semantic-index-lifecycle-receipt", "DTCR-XC-LC-001"),
            "REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION",
            "the planted lifecycle receipt",
        ),
    )
    refuses(
        "REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION",
        "semantic-index-lifecycle-receipt.schema.json properties/changes/properties/technical_evidence/const",
        lambda: A.enforce(
            "semantic-index-lifecycle-receipt",
            control("semantic-index-lifecycle-receipt", "DTCR-XC-LC-002"),
            "REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION",
            "the planted lifecycle receipt",
        ),
    )

    # 8. EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS
    refuses(
        "EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS",
        "projection-receipt.schema.json properties/establishes/properties/semantic_correctness/const",
        lambda: A.enforce(
            "projection-receipt",
            with_value(projection, True, "establishes", "semantic_correctness"),
            "EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS",
            "the planted projection receipt",
        ),
    )
    refuses(
        "EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS",
        "projection-receipt.schema.json allOf/0/then",
        lambda: A.enforce(
            "projection-receipt",
            with_value(projection, "PASS", "transport", "outcome"),
            "EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS",
            "the planted projection receipt",
        ),
    )
    refuses(
        "EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS",
        "projection-receipt.schema.json properties/data_handling/properties/provider_terms_admission/const",
        lambda: A.enforce(
            "projection-receipt",
            control("projection-receipt", "DTCR-XC-PR-003"),
            "EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS",
            "the planted projection receipt",
        ),
    )

    # 9. MUTABLE_INDEX_OR_MODEL_IDENTITY
    def model_moved_under_the_index() -> None:
        drifting = loaded()
        original = A.PROJECTION_ALGORITHM
        A.PROJECTION_ALGORITHM = original + " with an edited scorer"
        try:
            drifting.query(**CHECKOUT)
        finally:
            A.PROJECTION_ALGORITHM = original

    refuses(
        "MUTABLE_INDEX_OR_MODEL_IDENTITY",
        "index_schema_digest is recomputed before every query",
        model_moved_under_the_index,
    )

    def rows_moved_under_the_index() -> None:
        drifting = loaded()
        drifting.projections.pop("DTCR-PR-001")
        drifting.query(**CHECKOUT)

    refuses(
        "MUTABLE_INDEX_OR_MODEL_IDENTITY",
        "index_digest is recomputed before every query",
        rows_moved_under_the_index,
    )
    refuses(
        "MUTABLE_INDEX_OR_MODEL_IDENTITY",
        "projection-receipt.schema.json properties/embedding_provider/required",
        lambda: A.enforce(
            "projection-receipt",
            without(projection, "embedding_provider", "model_digest"),
            "MUTABLE_INDEX_OR_MODEL_IDENTITY",
            "the planted projection receipt",
        ),
    )

    # 10. TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS
    refuses(
        "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
        "consumed-context-row.schema.json properties/basis_grade/const",
        lambda: A.enforce(
            "consumed-context-row",
            with_value(manifest[0], "DETERMINISTIC_FACT", "basis_grade"),
            "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
            "the planted manifest entry",
        ),
    )
    refuses(
        "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
        "consumed-context-row.schema.json properties/influence/const",
        lambda: A.enforce(
            "consumed-context-row",
            with_value(manifest[0], "DETERMINED_OUTCOME", "influence"),
            "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
            "the planted manifest entry",
        ),
    )
    refuses(
        "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
        "retrieval-query.schema.json properties/establishes/properties/decision/const",
        lambda: A.enforce(
            "retrieval-query",
            with_value(query, True, "establishes", "decision"),
            "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
            "the planted query",
        ),
    )
    refuses(
        "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
        "retrieval-result.schema.json properties/establishes/properties/deterministic_fact/const",
        lambda: A.enforce(
            "retrieval-result",
            with_value(result, True, "establishes", "deterministic_fact"),
            "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
            "the planted result",
        ),
    )

    # 11. UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT
    def freshness_absent() -> None:
        blind = loaded(freshness_for=lambda document_id: None if document_id == "DTCR-DOC-003" else CEILINGS.get(document_id))
        blind.query(**CHECKOUT)

    refuses(
        "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
        "a candidate with no registered freshness ceiling is refused, not returned",
        freshness_absent,
    )
    refuses(
        "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
        "semantic-freshness-ceiling.schema.json properties/revalidated_at/anyOf",
        lambda: A.enforce(
            "semantic-freshness-ceiling",
            control("semantic-freshness-ceiling", "DTCR-XC-FC-005"),
            "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
            "the planted freshness ceiling",
        ),
    )

    # 12. NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS
    refuses(
        "NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS",
        "retrieval-result.schema.json allOf/0/then",
        lambda: A.enforce(
            "retrieval-result",
            {**not_applicable, "rows": [result["rows"][0]]},
            "NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS",
            "the planted not-applicable result",
        ),
    )
    refuses(
        "FROZEN_SCHEMA_REFUSED_THE_QUERY",
        "retrieval-query.schema.json allOf/0/then",
        lambda: store.query(
            "rename a local variable",
            "NOT_APPLICABLE",
            8,
            [],
            "this task is a mechanical rename with no decision or incident that stored context could bear on",
        ),
    )

    # The remaining hard laws, planted the same way: a single field moved on an
    # artifact this run actually emitted.
    refuses(
        "LANCEDB_ROW_PROMOTED_TO_SQLITE_EVENT",
        "retrieval-result.schema.json properties/rows/items/properties/row_class/const",
        lambda: A.enforce(
            "retrieval-result",
            {**result, "rows": [with_value(result["rows"][0], "LEDGER_EVENT", "row_class")]},
            "LANCEDB_ROW_PROMOTED_TO_SQLITE_EVENT",
            "the planted result",
        ),
    )
    refuses(
        "RETRIEVED_ROW_PROMOTED_TO_AUTHORITY",
        "retrieval-result.schema.json properties/rows/items/properties/authority/const",
        lambda: A.enforce(
            "retrieval-result",
            {**result, "rows": [with_value(result["rows"][0], "AUTHORITATIVE", "authority")]},
            "RETRIEVED_ROW_PROMOTED_TO_AUTHORITY",
            "the planted result",
        ),
    )
    refuses(
        "RETRIEVED_ADR_PROMOTED_TO_CURRENT_POLICY",
        "semantic-freshness-ceiling.schema.json properties/authority_ceiling/properties/current_policy/const",
        lambda: A.enforce(
            "semantic-freshness-ceiling",
            with_value(CEILINGS["DTCR-DOC-001"], True, "authority_ceiling", "current_policy"),
            "RETRIEVED_ADR_PROMOTED_TO_CURRENT_POLICY",
            "the planted freshness ceiling",
        ),
    )
    refuses(
        "RETRIEVED_RCA_PROMOTED_TO_REPRODUCED_FAILURE",
        "semantic-freshness-ceiling.schema.json properties/authority_ceiling/properties/reproduced_failure/const",
        lambda: A.enforce(
            "semantic-freshness-ceiling",
            with_value(CEILINGS["DTCR-DOC-004"], True, "authority_ceiling", "reproduced_failure"),
            "RETRIEVED_RCA_PROMOTED_TO_REPRODUCED_FAILURE",
            "the planted freshness ceiling",
        ),
    )
    # The adapter spells this law `PRIVATE_CONTEXT_NOT_PUBLIC_PROMPT` at both
    # guards. One vocabulary, and it is the adapter's -- the code the guard
    # raises is the fact; a second spelling here is what made the identity
    # comparison impossible to satisfy honestly.
    refuses(
        "PRIVATE_CONTEXT_NOT_PUBLIC_PROMPT",
        "content plane must equal the declared storage plane",
        lambda: loaded(skip="DTCR-DOC-006").register(
            DOCUMENTS["DTCR-DOC-006"]["document"],
            CEILINGS["DTCR-DOC-006"],
            {"plane": "PUBLIC_TREE", "text": "a private record pasted into the public tree"},
        ),
    )
    refuses(
        "PRIVATE_CONTEXT_NOT_PUBLIC_PROMPT",
        "content held in a private or consumer-local carrier is not projected in the public plane",
        lambda: store.project("DTCR-DOC-006"),
    )
    refuses(
        "PRIVATE_RECORD_STORED_IN_THE_PUBLIC_TREE",
        "semantic-document.schema.json allOf/0/then",
        lambda: A.enforce(
            "semantic-document",
            control("semantic-document", "DTCR-XC-DOC-003"),
            "PRIVATE_RECORD_STORED_IN_THE_PUBLIC_TREE",
            "the planted registration",
        ),
    )
    refuses(
        "STORED_DOCUMENT_REGISTERED_AS_AUTHORITATIVE",
        "semantic-document.schema.json properties/authority/const",
        lambda: A.enforce(
            "semantic-document",
            control("semantic-document", "DTCR-XC-DOC-001"),
            "STORED_DOCUMENT_REGISTERED_AS_AUTHORITATIVE",
            "the planted registration",
        ),
    )
    refuses(
        "UNBOUNDED_NEIGHBOURHOOD_WRITTEN_AS_A_QUERY",
        "retrieval-query.schema.json properties/top_k/oneOf",
        lambda: A.enforce(
            "retrieval-query",
            control("retrieval-query", "DTCR-XC-RQ-001"),
            "UNBOUNDED_NEIGHBOURHOOD_WRITTEN_AS_A_QUERY",
            "the planted query",
        ),
    )
    # The frozen schema admits the NOT_APPLICABLE literal for any lane, so a
    # reading lane carrying it is the adapter's own refusal rather than the
    # schema's -- and it is a refusal rather than a conversion crash.
    refuses(
        "AN_UNBOUNDED_NEIGHBOURHOOD_IS_NOT_A_QUERY",
        "a lane that reads rows carries an integer top_k",
        lambda: store.query("checkout ledger", "VECTOR", "NOT_APPLICABLE", []),
    )

    prove_falsifier_identity_is_load_bearing()

    # `plants` holds the codes the adapter raised and this suite verified, not
    # the codes this suite asked for, so a code drift in the adapter drops the
    # required row rather than answering it from this file's own literals.
    named = {falsifier for falsifier, _ in plants}
    for required in REQUIRED_FALSIFIERS:
        check(
            f"{required} is planted and was raised under that code",
            required in named,
            "the issue requires it and no case had it raised and verified",
        )


def prove_falsifier_identity_is_load_bearing() -> None:
    """A control that fires proves nothing until it is shown to fail on demand.

    The falsifier half of `refuses` is exercised the way the buf lane exercises
    its zero-source guard: one code literal is renamed at a verified source
    anchor in a throwaway copy of `adapter.py`, the same planted case is run
    against that copy through the real `refuses` path, and the harness has to
    record the falsifier-identity failure -- and has to leave the row out of the
    planted set. If this row is green, a renamed code in the real adapter is red.
    """
    work = Path(tempfile.mkdtemp(prefix="dtcr-semantic-context-"))
    try:
        source = (ADAPTER_DIR / "adapter.py").read_text(encoding="utf-8")
        anchor = (
            "        if URI_SCHEME.search(value):\n"
            "            raise Refusal(\n"
            '                "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",\n'
            '                "scan_for_leaks URI scheme",\n'
        )
        if anchor not in source:
            check(
                "the falsifier-identity red proof still targets a raised code (red proof)",
                False,
                "the source anchor moved; the mutation no longer renames a real falsifier code",
            )
            return
        drifted_path = work / "adapter.py"
        drifted_path.write_text(
            source.replace(
                anchor,
                anchor.replace(
                    '"PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT"',
                    '"A_FOREIGN_FALSIFIER_CODE"',
                ),
                1,
            ),
            encoding="utf-8",
        )
        spec = importlib.util.spec_from_file_location("adapter_drifted_code", drifted_path)
        assert spec is not None and spec.loader is not None
        drifted = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(drifted)
        # The copy defines its own `Refusal` class, which `refuses` would not
        # catch; point it back at the real one so the mutation under test is the
        # renamed code and nothing else.
        drifted.Refusal = Refusal

        leaked = control("semantic-document", "DTCR-XC-DOC-002")["source_url"]
        before, planted_before = len(failures), len(plants)
        refuses(
            "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",
            "scan_for_leaks URI scheme",
            lambda: drifted.scan_for_leaks({"fixture": {"path": leaked}}, "planted receipt"),
        )
        observed = failures[before:]
        del failures[before:]  # this red was planted here; it is not the run's red
        check(
            "renaming one falsifier code in the adapter turns its planted case red (red proof)",
            len(observed) == 1
            and "A_FOREIGN_FALSIFIER_CODE" in observed[0]
            and len(plants) == planted_before,
            f"observed={observed!r} planted_rows_added={len(plants) - planted_before}",
        )
        print(
            "  (red proof) the copied adapter raised 'A_FOREIGN_FALSIFIER_CODE' for the same "
            f"mechanism; the harness recorded {len(observed)} falsifier-identity failure and "
            f"{len(plants) - planted_before} planted rows -- the code half is load-bearing"
        )
    finally:
        shutil.rmtree(work, ignore_errors=True)


REQUIRED_FALSIFIERS = (
    "ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE",
    "WRONG_OR_STALE_SOURCE_DIGEST",
    "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",
    "VECTOR_TO_VECTOR_AUTHORITY_EDGE",
    "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
    "STALE_ADR_OVERRIDES_NEWER_EXPLICIT_DECISION",
    "REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION",
    "EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS",
    "MUTABLE_INDEX_OR_MODEL_IDENTITY",
    "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
    "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
    "NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS",
)


# ---------------------------------------------------------------------------
# lane 3: receipts
# ---------------------------------------------------------------------------

def receipts(fresh: dict[str, Any]) -> None:
    print("receipts")
    committed = A.RECEIPTS / "reference-backend.json"
    check("the deterministic receipt is committed", committed.is_file(), str(committed.name))
    if committed.is_file():
        check(
            "the committed deterministic receipt reproduces from this tree, byte for byte",
            committed.read_text(encoding="utf-8") == json.dumps(fresh, indent=2, sort_keys=True) + "\n",
            "re-run `python3 adapter.py receipt` and commit the result",
        )

    lane_path = A.RECEIPTS / "lancedb-lane.json"
    check("the provider lane receipt is committed", lane_path.is_file(), str(lane_path.name))
    if lane_path.is_file():
        lane = json.loads(lane_path.read_text(encoding="utf-8"))
        check(
            "the provider lane receipt records a typed absence, not a pass",
            lane["state"] in {"NOT_EXERCISED", "PROVIDER_UNAVAILABLE", "NOT_APPLICABLE"},
            str(lane.get("state")),
        )
        check(
            "the provider lane receipt establishes nothing",
            set(lane["establishes"].values()) == {False},
            str(lane["establishes"]),
        )

    completion = A.RECEIPTS / "lane-completion.json"
    check("the lane completion receipt is committed", completion.is_file(), str(completion.name))
    if completion.is_file():
        packet = json.loads(completion.read_text(encoding="utf-8"))
        check(
            "the completion receipt records #368's live state as not observed",
            packet.get("issue_368_state") == "NOT_OBSERVED",
            str(packet.get("issue_368_state")),
        )
        check(
            "the completion receipt hedges #521's live state rather than asserting it",
            "not reconfirmed" in packet.get("convergence_handoff", ""),
            packet.get("convergence_handoff", ""),
        )
        check(
            "every recorded gate carries an exit code",
            all("exit" in item for item in packet.get("gates", [])) and packet.get("gates"),
            str(packet.get("gates")),
        )


# ---------------------------------------------------------------------------
# lane 4: leaks
# ---------------------------------------------------------------------------

def leaks() -> int:
    print("leaks")
    scanned = 0
    # Committed text only. Build products are not in the tree this scan is
    # about, and reading one as text is how this lane first went red for a
    # reason that had nothing to do with a leak.
    for path in sorted(ADAPTER_DIR.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".json", ".md"}:
            continue
        if "__pycache__" in path.parts or path.name == "adapter.py":
            # adapter.py holds the patterns themselves; a scanner that reports
            # its own definitions reports nothing useful.
            continue
        text = path.read_text(encoding="utf-8")
        scanned += 1
        try:
            if path.suffix == ".json":
                A.scan_for_leaks(json.loads(text), path.name)
            else:
                for number, line in enumerate(text.splitlines(), start=1):
                    A.scan_for_leaks(line.strip(), f"{path.name}:{number}")
        except Refusal as refusal:
            failures.append(f"leak scan: {refusal}")
    check("the leak scan covered the committed subtree", scanned >= 4, str(scanned))
    print(f"  scanned={scanned} files (adapter.py excluded: it defines the patterns)")
    return scanned


# ---------------------------------------------------------------------------
# lane 5: the provider lane
# ---------------------------------------------------------------------------

def provider() -> str:
    print("provider")
    lane = A.probe_lancedb_lane()
    check(
        "the provider lane never reports a pass",
        lane["state"] == "NOT_EXERCISED",
        str(lane["state"]),
    )
    try:
        backend = A.LanceDBBackend()
    except ProviderUnavailable as absence:
        print(f"  NOT_EXERCISED: {absence.reason}. A missing provider is start-readiness, not a failure.")
        return f"NOT_EXERCISED ({absence.reason})"
    try:
        backend.query("anything", "VECTOR", 3, [])
        check("a bound but unexercised LanceDB lane refuses to answer", False, "it answered")
    except ProviderUnavailable as absence:
        check("a bound but unexercised LanceDB lane refuses to answer", absence.reason == "LANCEDB_RUNTIME_NOT_EXERCISED")
    print(f"  NOT_EXERCISED: bound {backend.binding['library']} {backend.binding['version']}, runtime lane never entered")
    return "NOT_EXERCISED (bound, runtime lane never entered)"


def main() -> int:
    try:
        fresh = positives()
        planted()
        receipts(fresh)
        scanned = leaks()
        lane = provider()
    except (Refusal, A.Unusable) as stopped:
        # A refusal escaping the positives lane is this suite's own red, and it
        # exits 2 like every other red rather than as an untyped traceback.
        print(f"DTCR-SEMANTIC-CONTEXT-RED the run stopped: {stopped}", file=sys.stderr)
        return 2
    print(
        f"documents=9 cases={cases} planted_falsifiers={len(plants)} "
        f"required_falsifiers={len(REQUIRED_FALSIFIERS)} scanned_files={scanned} "
        f"index_digest={fresh['index']['index_digest'][:16]} "
        f"model_digest={fresh['projection']['model_digest'][:16]} lancedb={lane}"
    )
    if failures:
        for failure in failures:
            print(f"DTCR-SEMANTIC-CONTEXT-RED {failure}", file=sys.stderr)
        return 2
    print(
        f"DTCR-SEMANTIC-CONTEXT-GREEN {cases} cases, {len(plants)} planted falsifiers refused under the "
        f"code and by the mechanism each names, {len(REQUIRED_FALSIFIERS)} required falsifiers all raised, "
        f"zero network, LanceDB {lane}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
