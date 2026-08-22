#!/usr/bin/env python3
"""Execute the semantic-context adapter against the frozen DTCR schemas.

Three lanes, and the numbers each one counts are printed, so a run can never
report a green it did not measure:

    positives   the committed corpus is projected with no provider on the
                machine, queried, consumed, reconciled and rebuilt, and every
                emitted artifact is validated against the read-only schemas in
                `../../references/schemas/`. The lane also measures the raw
                ranking *before* the freshness demotion, because a demotion that
                never had to move anything is decoration that a later reader
                would read as a guard.
    falsifiers  every falsifier named by issue #550 is run through the code path
                that owns it and must be refused *by that guard*. A defect that
                dies on an unrelated `required` proves nothing about the guard it
                was written for, so a schema-side row also performs a knockout:
                delete exactly the keyword the row names from a copy of the
                schema, change nothing else, and require the mutated instance to
                validate. A control still refused after its own guard is gone is
                refused by something else and the row naming it is wrong.
    provider    the committed provider receipt is checked without any provider,
                because a receipt whose own digests drifted describes a host that
                is no longer there and reads exactly like one that still matches.
                Then the pinned interpreter is tried for real. An importable
                vector store is a transport fact about one interpreter on one
                host; it is not a VECTOR retrieval lane, which stays
                BLOCKED_ON_PROVIDER on an embedding provider this runtime does
                not have. A missing interpreter is start-readiness, not a
                failure: the lane prints NOT_EXERCISED and stays green.

Exit 0 green, 2 a lane failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "DTCR-SEMANTIC-CONTEXT-SELFTEST-UNUSABLE: jsonschema is required. This suite executes "
        "the frozen schemas as deciding gates; skipping them would report the same green as "
        "running them.",
        file=sys.stderr,
    )
    raise SystemExit(70)

ADAPTER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ADAPTER_DIR))
import semantic_context as S  # noqa: E402

CORPUS = ADAPTER_DIR / "fixtures" / "public-corpus.json"
PROVIDER_RECEIPT = ADAPTER_DIR / "receipts" / "lancedb-provider.receipt.json"

# The query the positives lane rides. It is phrased the way the *superseded*
# record phrases it, which is why this corpus can measure the demotion at all.
QUERY = "persistence boundary domain isolation decision"

# The falsifiers issue #550 requires, plus the two this lane's own brief adds.
# Every one of them must be refused by at least one row below, and the table at
# the end prints the count per falsifier rather than a single total, so a
# falsifier that quietly lost its row is visible as a zero.
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
    "VECTOR_LANE_CLAIMED_WITHOUT_EMBEDDING_PROVIDER",
    "REBUILD_NON_DETERMINISTIC",
)

failures: list[str] = []
refused: dict[str, int] = {name: 0 for name in REQUIRED_FALSIFIERS}
checks = 0
validations = 0
workspaces: list[Path] = []


def fail(message: str) -> None:
    failures.append(message)
    print(f"  FAIL {message}")


def check(name: str, condition: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if not condition:
        fail(f"{name}: {detail or 'the assertion did not hold'}")


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((S.SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def validate(instance: Any, schema: dict[str, Any]) -> list[Any]:
    global validations
    validations += 1
    return sorted(Draft202012Validator(schema).iter_errors(instance), key=str)


def schema_path_of(error: Any) -> str:
    out = ""
    for part in error.absolute_schema_path:
        out += f"[{part}]" if isinstance(part, int) else (f".{part}" if out else str(part))
    return out


def knockout(schema: dict[str, Any], path: str) -> dict[str, Any]:
    """Delete exactly the keyword `path` names from a copy of `schema`."""
    node: Any = copy.deepcopy(schema)
    parts: list[Any] = []
    for chunk in path.split("."):
        while "[" in chunk:
            head, _, rest = chunk.partition("[")
            index, _, chunk = rest.partition("]")
            if head:
                parts.append(head)
            parts.append(int(index))
        if chunk:
            parts.append(chunk)
    root = node
    for part in parts[:-1]:
        node = node[part]
    del node[parts[-1]]
    return root


def corpus_copy(mutate: Callable[[dict[str, Any]], None] | None = None) -> Path:
    """A writable corpus in a temporary directory, optionally mutated first."""
    work = Path(tempfile.mkdtemp(prefix="dtcr-sc-"))
    workspaces.append(work)
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    if mutate is not None:
        mutate(data)
    target = work / "public-corpus.json"
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return target


def record_of(corpus: dict[str, Any], document_id: str) -> dict[str, Any]:
    for record in corpus["records"]:
        if record["document"]["document_id"] == document_id:
            return record
    raise AssertionError(f"{document_id} is not in the fixture; the plant has nothing to mutate")


# --------------------------------------------------------------------------
# lane 1: positives
# --------------------------------------------------------------------------

def lane_positives() -> dict[str, Any]:
    print("positives")
    backend = S.open_port(lane="KEYWORD", source=CORPUS)

    check("registered documents", len(backend.documents) == 5, str(len(backend.documents)))
    check("projected documents", backend.index["document_count"] == 4, str(backend.index["document_count"]))
    check(
        "the private record is registered and not projected",
        backend.unprojected == [{"document_id": "DTCR-DOC-004", "state": "NOT_PROJECTED_PRIVATE_PLANE"}],
        str(backend.unprojected),
    )
    check(
        "one projection receipt per projected chunk",
        len(backend.projection_receipts) == backend.index["chunk_count"],
        f"{len(backend.projection_receipts)} receipts against {backend.index['chunk_count']} chunks",
    )
    for receipt in backend.projection_receipts:
        if validate(receipt, load_schema("projection-receipt")):
            fail(f"{receipt['projection_receipt_id']} does not validate against the frozen schema")
    check(
        "no projection claims a provider call nobody placed",
        {receipt["transport"]["outcome"] for receipt in backend.projection_receipts} == {"SKIPPED_BY_POLICY"}
        and {receipt["transport"]["exit_code"] for receipt in backend.projection_receipts} == {None},
        str({receipt["transport"]["outcome"] for receipt in backend.projection_receipts}),
    )
    check(
        "the projector is pinned by digest rather than named",
        {receipt["embedding_provider"]["model_digest"] for receipt in backend.projection_receipts}
        == {S.NORMALIZER_DIGEST},
    )

    # The demotion has to move something, or the guard behind it is untested.
    raw = backend._matches(S.normalize(QUERY), ())
    check(
        "the superseded record outranks the newer one before the demotion",
        [document_id for _score, document_id in raw][:2] == ["DTCR-DOC-002", "DTCR-DOC-001"],
        str(raw),
    )

    answer = backend.retrieve(lane="KEYWORD", query_text=QUERY, top_k=5)
    result, binding = answer["retrieval_result"], answer["retrieval_binding"]
    if validate(answer["retrieval_query"], load_schema("retrieval-query")):
        fail("the emitted query does not validate against the frozen schema")
    if validate(result, load_schema("retrieval-result")):
        fail("the emitted result does not validate against the frozen schema")
    check(
        "the newer decision is returned above the record it superseded",
        [row["document_ref"] for row in result["rows"]] == ["DTCR-DOC-001", "DTCR-DOC-002"],
        str([row["document_ref"] for row in result["rows"]]),
    )
    check(
        "every returned row resolves to an exact source",
        all(row["back_reference_ref"] in backend.back_references for row in result["rows"]),
    )
    check(
        "every returned row carries its freshness ceiling",
        all(row["freshness_ref"] == backend.ceilings[row["document_ref"]]["ceiling_id"] for row in result["rows"]),
    )
    check(
        "the rows that nobody revalidated are counted beside the result",
        binding["never_revalidated_ranks"] == [2] and binding["historical_context_only_ranks"] == [2],
        str(binding),
    )
    check(
        "the result grants nothing",
        set(result["establishes"].values()) == {False}
        and set(binding["authority_ceiling"].values()) == {False},
    )

    kinds = {
        backend.back_references[row["back_reference_ref"]]["reference_kind"]
        for row in result["rows"]
    }
    check("a returned reference names a kind and carries its payload", kinds <= {
        "REPOSITORY_BLOB", "LEDGER_EVENT", "SOURCE_PACKET"}, str(kinds))

    narrowed = backend.retrieve(
        lane="KEYWORD",
        query_text="scheduler stall queue",
        top_k=5,
        filters=[{"field": "subsystem_tag", "value": "scheduler"}],
        query_id="DTCR-RQ-002",
        result_id="DTCR-RR-002",
    )
    check(
        "a metadata filter narrows to the subsystem it names",
        [row["document_ref"] for row in narrowed["retrieval_result"]["rows"]] == ["DTCR-DOC-003"],
        str([row["document_ref"] for row in narrowed["retrieval_result"]["rows"]]),
    )

    empty = backend.retrieve(
        lane="KEYWORD",
        query_text="thermostat firmware calibration",
        top_k=5,
        query_id="DTCR-RQ-003",
        result_id="DTCR-RR-003",
    )
    check(
        "a lane that ran and found nothing says EMPTY, not NOT_APPLICABLE",
        empty["retrieval_result"]["outcome"] == "EMPTY" and empty["retrieval_result"]["rows"] == [],
        str(empty["retrieval_result"]["outcome"]),
    )

    skipped = backend.retrieve(
        lane="NOT_APPLICABLE",
        query_text="rename one private helper across three call sites",
        top_k="NOT_APPLICABLE",
        query_id="DTCR-RQ-004",
        result_id="DTCR-RR-004",
        not_applicable_rationale=(
            "this task is a mechanical rename with no decision, incident or objective that stored "
            "context could bear on"
        ),
    )
    check(
        "a lane nobody entered carries no rows and states why",
        skipped["retrieval_result"]["outcome"] == "NOT_APPLICABLE"
        and skipped["retrieval_result"]["rows"] == []
        and skipped["retrieval_query"]["top_k"] == "NOT_APPLICABLE",
        str(skipped["retrieval_query"]["top_k"]),
    )

    manifest = backend.consume(
        result,
        ranks=[1, 2],
        manifest_ref="context manifest for the persistence boundary review",
        consuming_task_ref="review of the domain isolation violation candidate",
    )
    for row in manifest:
        if validate(row, load_schema("consumed-context-row")):
            fail(f"{row['consumed_row_id']} does not validate against the frozen schema")
    check(
        "every returned row is listed as consumed",
        S.reconcile_consumed(result, manifest) == {"returned": 2, "listed": 2},
    )
    check(
        "a consumed row carries the source, not only the score",
        all(row["back_reference_ref"] in backend.back_references for row in manifest),
    )

    rebuild = backend.lifecycle_receipt(operation="REBUILD")
    receipt = rebuild["semantic_index_lifecycle_receipt"]
    if validate(receipt, load_schema("semantic-index-lifecycle-receipt")):
        fail("the lifecycle receipt does not validate against the frozen schema")
    check(
        "a rebuild from the same source bytes derives the same index digest",
        receipt["index_digest_after"] == backend.index_digest
        and rebuild["lifecycle_binding"]["rebuilt_index_digest"] == backend.index_digest,
        f"{receipt['index_digest_after']} against {backend.index_digest}",
    )
    check(
        "a rebuild names the projections it was built from",
        len(receipt["projection_receipt_refs"]) == len(backend.projection_receipts),
    )
    deleted = backend.lifecycle_receipt(operation="DELETE", receipt_id="DTCR-LC-002",
                                        index_digest_before=backend.index_digest)
    check(
        "a delete leaves no digest behind and moves no admission",
        deleted["semantic_index_lifecycle_receipt"]["index_digest_after"] == "INDEX_ABSENT_AFTER_DELETE"
        and deleted["semantic_index_lifecycle_receipt"]["changes"]
        == {"task_admission": "UNCHANGED", "technical_evidence": "NO_NEW_EVIDENCE", "closure_state": "UNCHANGED"},
        str(deleted["semantic_index_lifecycle_receipt"]["changes"]),
    )

    # Rebuildability is a property of the input bytes, not of where they sit. A
    # byte-identical corpus at another path has to derive the same identity, or
    # the digest is binding something about this checkout.
    elsewhere = S.open_port(lane="KEYWORD", source=corpus_copy())
    check(
        "the same bytes at another path derive the same index and corpus digests",
        elsewhere.index_digest == backend.index_digest
        and elsewhere.corpus_digest == backend.corpus_digest,
        f"{elsewhere.index_digest} against {backend.index_digest}",
    )

    return {
        "registered": len(backend.documents),
        "projected": backend.index["document_count"],
        "chunks": backend.index["chunk_count"],
        "tokens": backend.index["token_count"],
        "projection_receipts": len(backend.projection_receipts),
        "corpus_digest": backend.corpus_digest,
        "index_digest": backend.index_digest,
        "normalizer_digest": S.NORMALIZER_DIGEST,
        "index_schema_digest": S.INDEX_SCHEMA_DIGEST,
    }


# --------------------------------------------------------------------------
# lane 2: falsifiers
# --------------------------------------------------------------------------

def expect_adapter_refusal(falsifier: str, mechanism: str, thunk: Callable[[], Any]) -> None:
    """The planted case has to go red, and by the guard the row names."""
    global checks
    checks += 1
    try:
        thunk()
    except S.Refusal as refusal:
        if refusal.reason != falsifier:
            fail(
                f"{falsifier}: refused by {refusal.reason} instead -- the planted defect never "
                f"reached the guard this row names"
            )
            return
        refused[falsifier] = refused.get(falsifier, 0) + 1
        print(f"  {falsifier}: refused by adapter guard, {mechanism}")
        return
    except Exception as error:  # noqa: BLE001 - anything else is still not the named guard
        fail(f"{falsifier}: raised {type(error).__name__} rather than its named refusal")
        return
    fail(f"{falsifier}: the planted defect was accepted ({mechanism} did not fire)")


def expect_schema_refusal(
    falsifier: str,
    schema_name: str,
    instance: dict[str, Any],
    keyword: str,
    knockout_at: str | None = None,
) -> None:
    """`keyword` is the guard as the validator reports it, and it must be the only one."""
    global checks
    checks += 1
    schema = load_schema(schema_name)
    errors = validate(instance, schema)
    if not errors:
        fail(f"{falsifier}: the frozen {schema_name} schema admitted the planted defect")
        return
    paths = {schema_path_of(error) for error in errors}
    if keyword not in paths:
        fail(f"{falsifier}: refused by {sorted(paths)}, not by the named guard {keyword}")
        return
    if len(paths) > 1:
        fail(f"{falsifier}: refused by more than the named guard ({sorted(paths)}); the row is not discriminating")
        return
    where = knockout_at or keyword
    if validate(instance, knockout(schema, where)):
        fail(f"{falsifier}: still refused after {where} was removed, so that keyword is not what refuses it")
        return
    refused[falsifier] = refused.get(falsifier, 0) + 1
    print(f"  {falsifier}: refused by {schema_name}#{keyword}, admitted once {where} is knocked out")


def lane_falsifiers(baseline: dict[str, Any]) -> None:
    print("falsifiers")
    clean = S.open_port(lane="KEYWORD", source=CORPUS)
    answer = clean.retrieve(lane="KEYWORD", query_text=QUERY, top_k=5)
    result = answer["retrieval_result"]

    # -- the source binding ------------------------------------------------

    def drifted_document_digest() -> None:
        def mutate(data: dict[str, Any]) -> None:
            document = record_of(data, "DTCR-DOC-001")["document"]
            document["document_digest"] = "0" * 63 + "1"
        S.open_port(lane="KEYWORD", source=corpus_copy(mutate))

    expect_adapter_refusal(
        "WRONG_OR_STALE_SOURCE_DIGEST",
        "the projector recomputes every declared digest from the bytes it read",
        drifted_document_digest,
    )

    def drifted_blob() -> None:
        def mutate(data: dict[str, Any]) -> None:
            blob = record_of(data, "DTCR-DOC-001")["back_reference"]["repository_blob"]
            blob["blob"] = blob["blob"][:-1] + ("0" if blob["blob"][-1] != "0" else "1")
        S.open_port(lane="KEYWORD", source=corpus_copy(mutate))

    expect_adapter_refusal(
        "WRONG_OR_STALE_SOURCE_DIGEST",
        "the Git object name of the projected bytes is derived and compared",
        drifted_blob,
    )

    def drifted_packet_size() -> None:
        def mutate(data: dict[str, Any]) -> None:
            record_of(data, "DTCR-DOC-003")["back_reference"]["source_packet"]["byte_count"] += 1
        S.open_port(lane="KEYWORD", source=corpus_copy(mutate))

    expect_adapter_refusal(
        "WRONG_OR_STALE_SOURCE_DIGEST",
        "the cited packet's byte count is measured, not read back",
        drifted_packet_size,
    )

    def source_moved_under_the_index() -> None:
        source = corpus_copy()
        stale = S.open_port(lane="KEYWORD", source=source)
        moved = json.loads(source.read_text(encoding="utf-8"))
        record_of(moved, "DTCR-DOC-001")["text"] += "\n\nA paragraph added after the index was built.\n"
        source.write_text(json.dumps(moved, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        stale.retrieve(lane="KEYWORD", query_text=QUERY, top_k=5)

    expect_adapter_refusal(
        "WRONG_OR_STALE_SOURCE_DIGEST",
        "a query re-derives the corpus digest before it answers",
        source_moved_under_the_index,
    )

    # -- back references ---------------------------------------------------

    def mismatched_back_reference() -> None:
        def mutate(data: dict[str, Any]) -> None:
            record_of(data, "DTCR-DOC-005")["document"]["back_reference_ref"] = "DTCR-BK-009"
        S.open_port(lane="KEYWORD", source=corpus_copy(mutate))

    expect_adapter_refusal(
        "ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE",
        "a registration's reference must be the reference the record carries",
        mismatched_back_reference,
    )

    def row_with_an_unresolvable_reference() -> None:
        orphaned = S.open_port(lane="KEYWORD", source=CORPUS)
        del orphaned.back_references["DTCR-BK-001"]
        orphaned.retrieve(lane="KEYWORD", query_text=QUERY, top_k=5)

    expect_adapter_refusal(
        "ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE",
        "a row is built only from a reference that resolves in this store",
        row_with_an_unresolvable_reference,
    )

    orphan_result = copy.deepcopy(result)
    del orphan_result["rows"][0]["back_reference_ref"]
    expect_schema_refusal(
        "ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE",
        "retrieval-result",
        orphan_result,
        "properties.rows.items.required",
    )

    # -- the private plane -------------------------------------------------

    def private_text_in_the_public_fixture() -> None:
        def mutate(data: dict[str, Any]) -> None:
            record_of(data, "DTCR-DOC-004")["text"] = "the advisory's own text, copied out of its carrier"
        S.open_port(lane="KEYWORD", source=corpus_copy(mutate))

    expect_adapter_refusal(
        "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",
        "a record on a private plane is registered by reference and never carries content here",
        private_text_in_the_public_fixture,
    )

    def resolved_locator_in_a_public_field() -> None:
        def mutate(data: dict[str, Any]) -> None:
            record_of(data, "DTCR-DOC-005")["document"]["owning_decision"] = (
                "service objective tracked at https://example.invalid/private-space/objectives"
            )
        S.open_port(lane="KEYWORD", source=corpus_copy(mutate))

    expect_adapter_refusal(
        "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",
        "the leak scan runs over every free-text field the frozen schemas leave unshaped",
        resolved_locator_in_a_public_field,
    )

    # -- authority edges ---------------------------------------------------

    def reference_naming_a_retrieval_row() -> None:
        def mutate(data: dict[str, Any]) -> None:
            record_of(data, "DTCR-DOC-001")["back_reference"]["repository_blob"]["path"] = (
                "docs/decisions/DTCR-RR-001-rank-1.md"
            )
        S.open_port(lane="KEYWORD", source=corpus_copy(mutate))

    expect_adapter_refusal(
        "VECTOR_TO_VECTOR_AUTHORITY_EDGE",
        "a back reference may cite source, ledger or packet, never another stored row",
        reference_naming_a_retrieval_row,
    )

    chained = copy.deepcopy(json.loads(CORPUS.read_text(encoding="utf-8")))
    chained_reference = record_of(chained, "DTCR-DOC-001")["back_reference"]
    chained_reference["vector_row_ref"] = "row 1 of the previous keyword query"
    expect_schema_refusal(
        "VECTOR_TO_VECTOR_AUTHORITY_EDGE",
        "source-back-reference",
        chained_reference,
        "additionalProperties",
    )

    # -- the consumed manifest ---------------------------------------------

    def a_read_row_in_no_list() -> None:
        partial = clean.consume(
            result,
            ranks=[1],
            manifest_ref="context manifest for the persistence boundary review",
            consuming_task_ref="review of the domain isolation violation candidate",
        )
        S.reconcile_consumed(result, partial)

    expect_adapter_refusal(
        "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
        "reconciliation compares the returned ranks against the listed ones",
        a_read_row_in_no_list,
    )

    def a_listed_row_the_query_never_returned() -> None:
        clean.consume(
            result,
            ranks=[1, 9],
            manifest_ref="context manifest for the persistence boundary review",
            consuming_task_ref="review of the domain isolation violation candidate",
        )

    expect_adapter_refusal(
        "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
        "a manifest entry is built only from a rank this result produced",
        a_listed_row_the_query_never_returned,
    )

    # -- freshness ---------------------------------------------------------

    def stale_record_left_on_top() -> None:
        S.DEMOTE_SUPERSEDED = False
        try:
            S.open_port(lane="KEYWORD", source=CORPUS).retrieve(
                lane="KEYWORD", query_text=QUERY, top_k=5
            )
        finally:
            S.DEMOTE_SUPERSEDED = True

    expect_adapter_refusal(
        "STALE_ADR_OVERRIDES_NEWER_EXPLICIT_DECISION",
        "with the demotion removed, the ordering assertion catches the reinstated record",
        stale_record_left_on_top,
    )

    def registration_without_a_ceiling() -> None:
        def mutate(data: dict[str, Any]) -> None:
            del record_of(data, "DTCR-DOC-003")["freshness_ceiling"]
        S.open_port(lane="KEYWORD", source=corpus_copy(mutate))

    expect_adapter_refusal(
        "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
        "a document with no recorded age is refused at registration",
        registration_without_a_ceiling,
    )

    def two_ages_for_one_document() -> None:
        def mutate(data: dict[str, Any]) -> None:
            record_of(data, "DTCR-DOC-005")["freshness_ceiling"]["observed_at"] = "2019-01-01"
        S.open_port(lane="KEYWORD", source=corpus_copy(mutate))

    expect_adapter_refusal(
        "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
        "the ceiling's age must be the age the registration recorded",
        two_ages_for_one_document,
    )

    reinstated = copy.deepcopy(
        record_of(json.loads(CORPUS.read_text(encoding="utf-8")), "DTCR-DOC-002")["freshness_ceiling"]
    )
    reinstated["usable_as"] = "CONTEXT_CANDIDATE"
    expect_schema_refusal(
        "STALE_ADR_OVERRIDES_NEWER_EXPLICIT_DECISION",
        "semantic-freshness-ceiling",
        reinstated,
        "allOf[0].then.properties.usable_as.const",
        knockout_at="allOf[0].then",
    )

    # -- the store is not a task -------------------------------------------

    def a_store_operation_that_moved_an_admission() -> None:
        moved = S.open_port(lane="KEYWORD", source=CORPUS)
        moved.task_admission = "ADVANCED"
        moved.lifecycle_receipt(operation="DELETE")

    expect_adapter_refusal(
        "REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION",
        "the admission is compared against the literal, before and after the operation",
        a_store_operation_that_moved_an_admission,
    )

    advanced = copy.deepcopy(
        S.open_port(lane="KEYWORD", source=CORPUS).lifecycle_receipt(operation="REBUILD")
    )["semantic_index_lifecycle_receipt"]
    advanced["changes"]["task_admission"] = "ADVANCED"
    expect_schema_refusal(
        "REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION",
        "semantic-index-lifecycle-receipt",
        advanced,
        "properties.changes.properties.task_admission.const",
    )

    def a_rebuild_that_does_not_reproduce() -> None:
        drifting = S.open_port(lane="KEYWORD", source=CORPUS)
        original = S.build_index
        state = {"n": 0}

        def nondeterministic(postings: Any) -> dict[str, Any]:
            state["n"] += 1
            index = original(postings)
            index["reading"] = state["n"]
            return index

        S.build_index = nondeterministic
        try:
            drifting.lifecycle_receipt(operation="REBUILD")
        finally:
            S.build_index = original

    expect_adapter_refusal(
        "REBUILD_NON_DETERMINISTIC",
        "the receipt rebuilds the whole store and compares the two index digests",
        a_rebuild_that_does_not_reproduce,
    )

    # -- identity ----------------------------------------------------------

    def one_identity_two_contents() -> None:
        def mutate(data: dict[str, Any]) -> None:
            duplicate = copy.deepcopy(record_of(data, "DTCR-DOC-005"))
            duplicate["text"] = duplicate["text"] + "\n\nA second content under the same identity.\n"
            duplicate["document"]["document_digest"] = S.sha256_hex(duplicate["text"].encode("utf-8"))
            data["records"].append(duplicate)
        S.open_port(lane="KEYWORD", source=corpus_copy(mutate))

    expect_adapter_refusal(
        "MUTABLE_INDEX_OR_MODEL_IDENTITY",
        "a document identity is registered once or not at all",
        one_identity_two_contents,
    )

    def an_index_that_outlived_its_projector() -> None:
        drifted = S.open_port(lane="KEYWORD", source=CORPUS)
        drifted.index["normalizer_digest"] = "0" * 64
        drifted.retrieve(lane="KEYWORD", query_text=QUERY, top_k=5)

    expect_adapter_refusal(
        "MUTABLE_INDEX_OR_MODEL_IDENTITY",
        "a query checks the index was built by the projector now loaded",
        an_index_that_outlived_its_projector,
    )

    unpinned = copy.deepcopy(clean.projection_receipts[0])
    del unpinned["embedding_provider"]["model_digest"]
    expect_schema_refusal(
        "MUTABLE_INDEX_OR_MODEL_IDENTITY",
        "projection-receipt",
        unpinned,
        "properties.embedding_provider.required",
    )

    # -- the bound on a query ----------------------------------------------

    for planted, mechanism in (
        ("all", "there is no value here spelling unbounded"),
        (0, "a neighbourhood of nothing is not a bounded query"),
        (S.MAX_TOP_K + 1, "the frozen ceiling of 200 is checked before the query runs"),
    ):
        expect_adapter_refusal(
            "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
            mechanism,
            lambda value=planted: clean.retrieve(lane="KEYWORD", query_text=QUERY, top_k=value),
        )

    promoted = copy.deepcopy(
        clean.consume(
            result,
            ranks=[1, 2],
            manifest_ref="context manifest for the persistence boundary review",
            consuming_task_ref="review of the domain isolation violation candidate",
        )[0]
    )
    promoted["basis_grade"] = "DETERMINISTIC_FACT"
    expect_schema_refusal(
        "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
        "consumed-context-row",
        promoted,
        "properties.basis_grade.const",
    )

    decided = copy.deepcopy(result)
    decided["establishes"]["decision"] = True
    expect_schema_refusal(
        "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
        "retrieval-result",
        decided,
        "properties.establishes.properties.decision.const",
    )

    # -- the lane nobody entered -------------------------------------------

    def a_skipped_lane_asked_for_rows() -> None:
        clean.retrieve(
            lane="NOT_APPLICABLE",
            query_text="a mechanical rename",
            top_k=5,
            not_applicable_rationale="stored context could not bear on a mechanical rename",
        )

    expect_adapter_refusal(
        "NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS",
        "a lane recorded as not entered may not carry a result size",
        a_skipped_lane_asked_for_rows,
    )

    def a_skipped_lane_with_no_reason() -> None:
        clean.retrieve(
            lane="NOT_APPLICABLE",
            query_text="a mechanical rename",
            top_k="NOT_APPLICABLE",
        )

    expect_adapter_refusal(
        "NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS",
        "an unexplained skip reads as an empty result",
        a_skipped_lane_with_no_reason,
    )

    manufactured = copy.deepcopy(result)
    manufactured["outcome"] = "NOT_APPLICABLE"
    manufactured["not_applicable_rationale"] = "stored context could not bear on a mechanical rename"
    expect_schema_refusal(
        "NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS",
        "retrieval-result",
        manufactured,
        "allOf[0].then.properties.rows.maxItems",
        knockout_at="allOf[0].then",
    )

    # -- the provider plane ------------------------------------------------

    for lane in ("VECTOR", "HYBRID"):
        expect_adapter_refusal(
            "VECTOR_LANE_CLAIMED_WITHOUT_EMBEDDING_PROVIDER",
            f"the port refuses {lane} rather than answering it from the keyword index",
            lambda value=lane: S.open_port(lane=value, source=CORPUS),
        )
    expect_adapter_refusal(
        "VECTOR_LANE_CLAIMED_WITHOUT_EMBEDDING_PROVIDER",
        "an already-open keyword backend refuses a vector query for the same reason",
        lambda: clean.retrieve(lane="VECTOR", query_text=QUERY, top_k=5),
    )

    expect_adapter_refusal(
        "EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS",
        "a provider binding presented to the port is not the human admission its terms need",
        lambda: S.open_port(
            lane="VECTOR",
            source=CORPUS,
            embedding_provider={"provider_name": "example-embedding-service", "dimension": 768},
        ),
    )

    transport_pass = copy.deepcopy(clean.projection_receipts[0])
    transport_pass["transport"] = {"outcome": "PASS", "exit_code": 0}
    transport_pass["establishes"]["semantic_correctness"] = True
    expect_schema_refusal(
        "EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS",
        "projection-receipt",
        transport_pass,
        "properties.establishes.properties.semantic_correctness.const",
    )

    cleared = copy.deepcopy(clean.projection_receipts[0])
    cleared["data_handling"]["provider_terms_admission"] = "CLEARED_BY_SUCCESSFUL_CALL"
    expect_schema_refusal(
        "EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS",
        "projection-receipt",
        cleared,
        "properties.data_handling.properties.provider_terms_admission.const",
    )


# --------------------------------------------------------------------------
# lane 3: provider
# --------------------------------------------------------------------------

def lane_provider() -> str:
    print("provider")
    if not PROVIDER_RECEIPT.is_file():
        fail(f"{PROVIDER_RECEIPT.name} is absent; the probe lane has nothing to check")
        return "ABSENT"
    committed = json.loads(PROVIDER_RECEIPT.read_text(encoding="utf-8"))
    check(
        "the committed provider receipt grants nothing",
        set(committed["establishes"].values()) == {False},
        str(committed["establishes"]),
    )
    check(
        "the vector retrieval lane and its provider are recorded as blocked, not absent",
        committed["lanes"]["vector_retrieval_lane"]["state"] == "BLOCKED_ON_PROVIDER"
        and committed["lanes"]["embedding_provider"]["state"] == "BLOCKED_ON_PROVIDER"
        and committed["lanes"]["provider_terms_model_rights_and_privacy"]["state"] == "HUMAN_ADMIT_REQUIRED",
        str({name: lane["state"] for name, lane in committed["lanes"].items()}),
    )
    try:
        S.scan_public(committed, "the committed provider receipt")
    except S.Refusal as refusal:
        fail(f"the committed provider receipt carries a private value: {refusal.detail}")

    observed = S.probe_lancedb()
    passing = next((attempt for attempt in observed["attempts"] if attempt["state"] == "PASS"), None)
    if passing is None:
        print(
            "  NOT_EXERCISED: no pinned interpreter on this host imports the vector store. "
            "A missing provider is start-readiness, not a failure."
        )
        return "NOT_EXERCISED (no pinned interpreter with the store)"

    recorded = next(
        (attempt for attempt in committed["attempts"] if attempt["state"] == "PASS"), None
    )
    if recorded is None:
        fail("this host imports the vector store and the committed receipt records no passing attempt")
        return "DISAGREES"
    for key in ("interpreter", "stdout", "stdout_sha256", "executable_sha256", "exit_code"):
        check(
            f"the committed receipt and this host agree on {key}",
            recorded[key] == passing[key],
            f"{recorded[key]!r} against {passing[key]!r}",
        )
    print(
        f"  {PROVIDER_RECEIPT.name}: this host reproduces the recorded import "
        f"({passing['stdout']}) through {passing['interpreter']}"
    )
    return f"EXERCISED (store import {passing['stdout']}, vector lane BLOCKED_ON_PROVIDER)"


def main() -> int:
    # A guard firing inside the positives lane is a red run, not a traceback: the
    # exit code is this file's whole contract with `tests/run-all.sh`, and an
    # uncaught refusal would leave it at 1, outside the 0/2/70 the caller reads.
    try:
        numbers = lane_positives()
        lane_falsifiers(numbers)
        provider = lane_provider()
    except S.Refusal as refusal:
        print(f"  FAIL the positives lane was refused by its own adapter: {refusal}")
        print("\nDTCR-SEMANTIC-CONTEXT SELFTEST RED")
        return 2
    finally:
        for workspace in workspaces:
            shutil.rmtree(workspace, ignore_errors=True)

    print("\nfalsifier coverage")
    for name in REQUIRED_FALSIFIERS:
        count = refused.get(name, 0)
        state = "PASS" if count else "FAIL"
        if not count:
            failures.append(f"{name}: no planted mutation was refused by it")
        print(f"  {state} {count:>2} {name}")

    print(
        "\nDTCR-SEMANTIC-CONTEXT denominators: "
        f"registered={numbers['registered']} projected={numbers['projected']} "
        f"chunks={numbers['chunks']} tokens={numbers['tokens']} "
        f"projection_receipts={numbers['projection_receipts']} "
        f"positives_checks={checks} schema_validations={validations} "
        f"planted_mutations={sum(refused.values())} "
        f"falsifiers={sum(1 for name in REQUIRED_FALSIFIERS if refused.get(name))}/"
        f"{len(REQUIRED_FALSIFIERS)} provider={provider} failures={len(failures)}"
    )
    print(
        f"corpus_digest={numbers['corpus_digest'][:16]} index_digest={numbers['index_digest'][:16]} "
        f"normalizer_digest={numbers['normalizer_digest'][:16]} "
        f"index_schema_digest={numbers['index_schema_digest'][:16]}"
    )
    if failures:
        print("DTCR-SEMANTIC-CONTEXT SELFTEST RED")
        return 2
    print("DTCR-SEMANTIC-CONTEXT SELFTEST GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
