#!/usr/bin/env python3
"""Run the SQLite ledger adapter against its fixtures, and plant every falsifier.

The positives come first and are reported first: a refusal credited to a harness
that was already red proves nothing about the guard it names. Then each planted
mutation is a case that has to go red, and every case names the falsifier it
kills and the mechanism that killed it, so a case that starts passing for a new
reason is visible as a changed mechanism rather than as a still-green run.

The end-to-end lane is deliberately not a mock: it creates a real database file
in a temporary directory, ingests both fixtures, walks them, and emits a receipt
carrying that file's sha256. A harness that only ever used `:memory:` would
report the same green while the file-digest binding was broken.

Exit 0 green, 2 a case failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ledger  # noqa: E402
from ledger import LedgerRefusal  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CORE = json.loads((FIXTURES / "core-observations.json").read_text(encoding="utf-8"))
CYCLIC = json.loads((FIXTURES / "cyclic-observations.json").read_text(encoding="utf-8"))

SCHEME_DIGEST = CORE["observations"][0]["symbol"]["identity"]["normalization"]["scheme_digest"]
PRICING = CORE["observations"][0]["symbol"]["identity"]["provider_scoped_id"]
LOOP = CYCLIC["observations"][0]["symbol"]["identity"]["provider_scoped_id"]

DUPLICATE_EVENT_ARGS = {
    "event_kind": "FACT_OBSERVED",
    "producer_kind": "TEXTUAL_MATCH",
    "source_digest": "f" * 64,
    "payload": {"planted": "the same logical event, appended twice"},
}

failures: list[str] = []
cases = 0
mutations: list[tuple[str, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    global cases
    cases += 1
    if not condition:
        failures.append(f"{name}: {detail or 'the assertion did not hold'}")


def refuses(falsifier: str, mechanism: str, thunk) -> None:
    """The planted case has to go red, and the record names what turned it red.

    Only the two refusal channels are caught: this adapter's own `LedgerRefusal`
    and SQLite's constraint failure. An `OperationalError` from a mistyped
    statement is not a guard firing, so it propagates and fails the run.
    """
    global cases
    cases += 1
    mutations.append((falsifier, mechanism))
    try:
        thunk()
    except (LedgerRefusal, sqlite3.IntegrityError):
        return
    failures.append(f"{falsifier} was not refused ({mechanism} did not fire)")


def loaded(fixture: dict, path: str = ":memory:") -> sqlite3.Connection:
    conn = ledger.create_ledger(Path(path), fixture["subject"])
    ledger.ingest(conn, fixture["observations"])
    return conn


# ---------------------------------------------------------------------------
# positives
# ---------------------------------------------------------------------------

def positives() -> None:
    conn = loaded(CORE)
    counts = ledger.verify_readback(conn)
    check(
        "ingest counts",
        counts == {"event": 9, "node": 4, "fact": 8, "edge": 3},
        f"counted {counts}",
    )

    walk = ledger.traverse(
        conn,
        seed_provider_id=PRICING,
        seed_scheme_digest=SCHEME_DIGEST,
        admitted_edge_kinds=["CALLS"],
        depth_limit=8,
        row_limit=5000,
    )
    path, binding = walk["blast_radius_path"], walk["traversal_binding"]
    check("calls-only depth", path["traversal_bounds"]["depth"] == 2, str(path["traversal_bounds"]))
    check(
        "calls-only termination",
        path["traversal_bounds"]["terminated_by"] == "EDGE_SET_EXHAUSTED",
        str(path["traversal_bounds"]),
    )
    check("calls-only hops", len(path["hops"]) == 2, str(len(path["hops"])))
    check("calls-only nodes", len(path["nodes_visited"]) == 3, str(len(path["nodes_visited"])))
    check(
        "calls-only denominators",
        (binding["input_edge_denominator"], binding["output_edge_denominator"]) == (2, 2),
        str(binding),
    )
    check(
        "reach is never the complete set",
        path["authority_ceiling"] == {"complete_reachable_set": False, "semantic_truth": False, "task_pass": False},
        str(path["authority_ceiling"]),
    )

    wider = ledger.traverse(
        conn,
        seed_provider_id=PRICING,
        seed_scheme_digest=SCHEME_DIGEST,
        admitted_edge_kinds=["CALLS", "REFERENCES"],
        depth_limit=8,
        row_limit=5000,
    )
    check(
        "a wider admitted set reaches further",
        len(wider["blast_radius_path"]["hops"]) == 3
        and wider["traversal_binding"]["input_edge_denominator"] == 3,
        str(wider["traversal_binding"]),
    )
    check(
        "the edge set digest moves with the denominator",
        wider["blast_radius_path"]["edge_set"]["edge_set_digest"]
        != path["edge_set"]["edge_set_digest"],
    )

    shallow = ledger.traverse(
        conn,
        seed_provider_id=PRICING,
        seed_scheme_digest=SCHEME_DIGEST,
        admitted_edge_kinds=["CALLS"],
        depth_limit=1,
        row_limit=5000,
    )
    check(
        "a depth-bounded walk says so and drops its completeness claim",
        shallow["blast_radius_path"]["traversal_bounds"]["terminated_by"] == "DEPTH_LIMIT_REACHED"
        and shallow["blast_radius_path"]["edge_set"]["edge_completeness"] == "PARTIAL_LOWER_BOUND",
        str(shallow["blast_radius_path"]["edge_set"]),
    )

    narrow = ledger.traverse(
        conn,
        seed_provider_id=PRICING,
        seed_scheme_digest=SCHEME_DIGEST,
        admitted_edge_kinds=["CALLS", "REFERENCES"],
        depth_limit=8,
        row_limit=1,
    )
    check(
        "a row-bounded walk says so",
        narrow["blast_radius_path"]["traversal_bounds"]["terminated_by"] == "ROW_LIMIT_REACHED",
        str(narrow["blast_radius_path"]["traversal_bounds"]),
    )

    cyclic_conn = loaded(CYCLIC)
    cycle = ledger.traverse(
        cyclic_conn,
        seed_provider_id=LOOP,
        seed_scheme_digest=SCHEME_DIGEST,
        admitted_edge_kinds=["CALLS"],
        depth_limit=8,
        row_limit=5000,
    )
    cyclic_path = cycle["blast_radius_path"]
    visited = [node["provider_scoped_id"] for node in cyclic_path["nodes_visited"]]
    check(
        "the cycle guard stops the walk and is named",
        cyclic_path["traversal_bounds"]["terminated_by"] == "CYCLE_GUARD"
        and cycle["traversal_binding"]["cycle_guard_fired"] is True,
        str(cyclic_path["traversal_bounds"]),
    )
    check("no node is visited twice", len(visited) == len(set(visited)) == 3, str(visited))
    check(
        "a mixed-provenance walk reports MIXED",
        cyclic_path["edge_set"]["edge_provenance"] == "MIXED",
        cyclic_path["edge_set"]["edge_provenance"],
    )

    # Replay is the deterministic-export lane: the same admitted input, replayed
    # in the recorded order, reads back to the same export digest.
    export = ledger.export_ledger(conn)
    replayed = ledger.replay(export)
    check(
        "replay reproduces the export",
        ledger.digest_of(ledger.export_ledger(replayed)) == ledger.digest_of(export),
    )
    replayed.close()
    conn.close()
    cyclic_conn.close()


# ---------------------------------------------------------------------------
# planted mutations
# ---------------------------------------------------------------------------

def plants() -> None:
    def wrong_subject() -> None:
        conn = loaded(CORE)
        stray = copy.deepcopy(CORE["observations"][0])
        stray["fact_id"] = "DTCR-SY-090"
        stray["subject"] = CYCLIC["subject"]
        ledger.ingest(conn, [stray])

    refuses("WRONG_REPOSITORY_OR_TREE", "one ledger holds one exact subject", wrong_subject)

    def out_of_sequence() -> None:
        conn = loaded(CORE)
        conn.execute(
            "INSERT INTO event (seq, event_digest, event_kind, producer_binding_id, producer_kind, "
            "source_digest, payload) VALUES (?, ?, 'FACT_OBSERVED', ?, 'TEXTUAL_MATCH', ?, '{}')",
            (99, "a" * 64, ledger.PROVIDER_BINDING_ID, "b" * 64),
        )

    refuses("SQLITE_EVENT_SEQUENCE_BREAK", "the sequence-integrity trigger", out_of_sequence)

    def event_id_drift() -> None:
        conn = loaded(CORE)
        head = conn.execute("SELECT MAX(seq) FROM event").fetchone()[0]
        conn.execute(
            "INSERT INTO event (seq, event_digest, event_kind, producer_binding_id, producer_kind, "
            "source_digest, payload) VALUES (?, ?, 'FACT_OBSERVED', ?, 'TEXTUAL_MATCH', ?, ?)",
            (head + 1, "c" * 64, ledger.PROVIDER_BINDING_ID, "d" * 64, '{"planted":true}'),
        )
        ledger.verify_readback(conn)

    refuses("SQLITE_EVENT_ID_DRIFT", "readback re-derives every digest", event_id_drift)

    def duplicate_logical_event() -> None:
        conn = loaded(CORE)
        ledger.append_event(conn, **DUPLICATE_EVENT_ARGS)
        ledger.append_event(conn, **DUPLICATE_EVENT_ARGS)

    refuses(
        "DUPLICATE_LOGICAL_EVENT_WITH_DIFFERENT_ID",
        "event_digest is derived from the content and is UNIQUE",
        duplicate_logical_event,
    )

    def duplicate_observation() -> None:
        conn = loaded(CORE)
        ledger.ingest(conn, [copy.deepcopy(CORE["observations"][0])])

    # Two guards stand behind a re-ingested observation, and the knockout lane
    # below shows the event digest alone is enough: with the UNIQUE on
    # event_digest removed, this same case is caught by the derived fact key.
    refuses(
        "DUPLICATE_LOGICAL_EVENT_WITH_DIFFERENT_ID",
        "the derived event digest, and behind it the derived fact key",
        duplicate_observation,
    )

    def fact_without_binding() -> None:
        conn = loaded(CORE)
        node_key = conn.execute("SELECT node_key FROM node LIMIT 1").fetchone()[0]
        conn.execute(
            "INSERT INTO fact (fact_key, fact_kind, node_key, provider_fact_id, event_seq) "
            "VALUES (?, 'SYMBOL', ?, 'DTCR-SY-091', 1)",
            ("e" * 64, node_key),
        )

    refuses(
        "FACT_WITHOUT_SOURCE_OR_UPSTREAM_BINDING",
        "the fact CHECK requires a blob range or an upstream identity",
        fact_without_binding,
    )

    def edge_endpoint_unbound() -> None:
        conn = loaded(CORE)
        stray = copy.deepcopy(CORE["observations"][5])
        stray["fact_id"] = "DTCR-SY-092"
        stray["relationship"]["to"]["provider_scoped_id"] = "example-scheme example-package ghost/Absent#gone()."
        ledger.ingest(conn, [stray])

    refuses("EDGE_ENDPOINT_UNBOUND", "the edge foreign key onto node", edge_endpoint_unbound)

    def unbounded_cte() -> None:
        conn = loaded(CORE)
        original = ledger.TRAVERSAL_SQL
        planted = original.replace("WHERE r.depth < :depth_limit\n       AND", "WHERE")
        if planted == original:
            raise AssertionError("the depth bound was not found in the statement to remove")
        ledger.TRAVERSAL_SQL = planted
        try:
            ledger.traverse(
                conn,
                seed_provider_id=PRICING,
                seed_scheme_digest=SCHEME_DIGEST,
                admitted_edge_kinds=["CALLS"],
                depth_limit=8,
                row_limit=5000,
            )
        finally:
            ledger.TRAVERSAL_SQL = original

    refuses("UNBOUNDED_RECURSIVE_CTE", "assert_bounded reads the statement before it runs", unbounded_cte)

    def unbounded_request() -> None:
        conn = loaded(CORE)
        ledger.traverse(
            conn,
            seed_provider_id=PRICING,
            seed_scheme_digest=SCHEME_DIGEST,
            admitted_edge_kinds=["CALLS"],
            depth_limit="UNBOUNDED",
            row_limit=5000,
        )

    refuses("UNBOUNDED_RECURSIVE_CTE", "depth_limit is a positive integer or nothing", unbounded_request)

    def depth_over_ceiling() -> None:
        conn = loaded(CORE)
        ledger.traverse(
            conn,
            seed_provider_id=PRICING,
            seed_scheme_digest=SCHEME_DIGEST,
            admitted_edge_kinds=["CALLS"],
            depth_limit=ledger.MAX_DEPTH_LIMIT + 1,
            row_limit=5000,
        )

    refuses(
        "TRAVERSAL_DEPTH_EXCEEDS_DECLARED_LIMIT",
        "the frozen ceiling of 64 is checked before the query runs",
        depth_over_ceiling,
    )

    def edge_kind_outside_set() -> None:
        conn = loaded(CORE)
        ledger.traverse(
            conn,
            seed_provider_id=PRICING,
            seed_scheme_digest=SCHEME_DIGEST,
            admitted_edge_kinds=["CALLS", "SIMILAR_EMBEDDING"],
            depth_limit=8,
            row_limit=5000,
        )

    refuses(
        "EDGE_KIND_OUTSIDE_ADMITTED_SET",
        "the closed edge vocabulary",
        edge_kind_outside_set,
    )

    def ingest_edge_kind_outside_set() -> None:
        conn = loaded(CORE)
        stray = copy.deepcopy(CORE["observations"][5])
        stray["fact_id"] = "DTCR-SY-093"
        stray["relationship"]["relationship_kind"] = "SIMILAR_EMBEDDING"
        ledger.ingest(conn, [stray])

    refuses(
        "EDGE_KIND_OUTSIDE_ADMITTED_SET",
        "the frozen symbol-fact schema refuses the kind at ingest",
        ingest_edge_kind_outside_set,
    )

    def cycle_path_duplication() -> None:
        # A visited set that walks the same node twice is refused by the frozen
        # schema, which is the guard the traversal's cycle stop exists to keep
        # true. Planting it directly proves the schema half still fires.
        conn = loaded(CYCLIC)
        walk = ledger.traverse(
            conn,
            seed_provider_id=LOOP,
            seed_scheme_digest=SCHEME_DIGEST,
            admitted_edge_kinds=["CALLS"],
            depth_limit=8,
            row_limit=5000,
        )
        path = copy.deepcopy(walk["blast_radius_path"])
        path["nodes_visited"].append(path["nodes_visited"][0])
        ledger.enforce("blast-radius-path", path, "the planted traversal")

    refuses("CYCLE_PATH_DUPLICATION", "nodes_visited uniqueItems", cycle_path_duplication)

    def partial_reported_as_complete() -> None:
        conn = loaded(CORE)
        original = ledger.derive_completeness
        ledger.derive_completeness = lambda terminated_by, walked: "COMPLETE_FOR_RESOLVED_EDGES"
        try:
            ledger.traverse(
                conn,
                seed_provider_id=PRICING,
                seed_scheme_digest=SCHEME_DIGEST,
                admitted_edge_kinds=["CALLS"],
                depth_limit=1,
                row_limit=5000,
            )
        finally:
            ledger.derive_completeness = original

    refuses(
        "PARTIAL_EDGE_SET_REPORTED_AS_COMPLETE_BLAST_RADIUS",
        "assert_not_overclaimed compares the claim against the stop reason",
        partial_reported_as_complete,
    )

    def transaction_failure_hidden() -> None:
        conn = loaded(CORE)
        before = ledger.row_counts(conn)
        good = copy.deepcopy(CORE["observations"][0])
        good["fact_id"] = "DTCR-SY-094"
        bad = copy.deepcopy(CORE["observations"][0])
        bad["fact_id"] = "DTCR-SY-095"
        bad["subject"] = CYCLIC["subject"]
        try:
            ledger.ingest(conn, [good, bad])
        finally:
            after = ledger.row_counts(conn)
            check(
                "a refused batch leaves no partial rows",
                after == before,
                f"{before} became {after}",
            )

    refuses("TRANSACTION_FAILURE_HIDDEN", "the batch is one transaction", transaction_failure_hidden)

    def row_promoted_to_source_truth() -> None:
        conn = ledger._connect(":memory:")
        conn.executescript(ledger.DDL)
        conn.execute(
            "INSERT INTO ledger_schema VALUES (?, ?, ?, 'SOURCE_TRUTH')",
            (ledger.SCHEMA_VERSION, ledger.LEDGER_SCHEMA_DIGEST, ledger.MIGRATION_DIGEST),
        )

    refuses(
        "DATABASE_ROW_PROMOTED_TO_SOURCE_TRUTH",
        "the authority_ceiling CHECK constraint",
        row_promoted_to_source_truth,
    )

    def query_pass_promoted() -> None:
        conn = loaded(CORE)
        walk = ledger.traverse(
            conn,
            seed_provider_id=PRICING,
            seed_scheme_digest=SCHEME_DIGEST,
            admitted_edge_kinds=["CALLS"],
            depth_limit=8,
            row_limit=5000,
        )
        path = copy.deepcopy(walk["blast_radius_path"])
        path["authority_ceiling"]["task_pass"] = True
        ledger.enforce("blast-radius-path", path, "the planted traversal")

    refuses(
        "QUERY_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS",
        "authority_ceiling.task_pass is a const",
        query_pass_promoted,
    )

    def receipt_promoted(tmp: Path) -> None:
        conn = ledger.create_ledger(tmp / "promoted.sqlite3", CORE["subject"])
        ledger.ingest(conn, CORE["observations"])
        artifact = ledger.emit_receipt(conn, tmp / "promoted.sqlite3")
        receipt = copy.deepcopy(artifact["fact_plane_receipt"])
        receipt["grants"]["task_pass"] = True
        ledger.enforce("fact-plane-receipt", receipt, "the planted receipt")

    def nondeterministic_export(tmp: Path) -> None:
        conn = ledger.create_ledger(tmp / "drifting.sqlite3", CORE["subject"])
        ledger.ingest(conn, CORE["observations"])
        original = ledger.export_ledger
        state = {"n": 0}

        def drifting(connection):
            state["n"] += 1
            document = original(connection)
            document["reading"] = state["n"]
            return document

        ledger.export_ledger = drifting
        try:
            ledger.emit_receipt(conn, tmp / "drifting.sqlite3")
        finally:
            ledger.export_ledger = original

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        refuses(
            "QUERY_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS",
            "grants.task_pass is a const in the frozen receipt",
            lambda: receipt_promoted(tmp),
        )
        refuses(
            "NONDETERMINISTIC_EXPORT_SILENTLY_ACCEPTED",
            "the receipt replays its own export before it will be written",
            lambda: nondeterministic_export(tmp),
        )

    def seed_absent() -> None:
        conn = loaded(CORE)
        ledger.traverse(
            conn,
            seed_provider_id="example-scheme example-package nowhere/Absent#gone().",
            seed_scheme_digest=SCHEME_DIGEST,
            admitted_edge_kinds=["CALLS"],
            depth_limit=8,
            row_limit=5000,
        )

    refuses("SEED_NOT_IN_LEDGER", "an absent seed is not an empty blast radius", seed_absent)

    def provider_id_without_normalization() -> None:
        conn = loaded(CORE)
        ledger.traverse(
            conn,
            seed_provider_id=PRICING,
            seed_scheme_digest="0" * 64,
            admitted_edge_kinds=["CALLS"],
            depth_limit=8,
            row_limit=5000,
        )

    refuses(
        "PROVIDER_ID_IS_NOT_A_UNIVERSAL_IDENTITY",
        "node_key binds the normalization scheme digest",
        provider_id_without_normalization,
    )

    def append_only() -> None:
        conn = loaded(CORE)
        conn.execute("UPDATE event SET payload = '{}' WHERE seq = 1")

    refuses("LEDGER_APPEND_ONLY", "the no-update trigger on event", append_only)


# ---------------------------------------------------------------------------
# knockouts
# ---------------------------------------------------------------------------

# Each entry removes exactly one guard from the DDL and re-runs the plant that
# names it. A plant that stays refused without its own guard is refused by
# something else, and the record naming the guard is what is wrong -- which is
# how the duplicate-event case above was found to be standing on two guards
# rather than the one it named.
KNOCKOUTS = (
    (
        "SQLITE_EVENT_SEQUENCE_BREAK",
        """CREATE TRIGGER event_sequence_integrity BEFORE INSERT ON event
BEGIN
  SELECT RAISE(ABORT, 'SQLITE_EVENT_SEQUENCE_BREAK: an event must be exactly one past the ledger head')
  WHERE NEW.seq <> (SELECT IFNULL(MAX(seq), 0) + 1 FROM event);
END;
""",
        "",
    ),
    (
        "FACT_WITHOUT_SOURCE_OR_UPSTREAM_BINDING",
        """,
  CHECK (
    (blob_path IS NOT NULL AND blob_sha IS NOT NULL AND start_byte IS NOT NULL AND end_byte IS NOT NULL)
    OR (upstream_fact_identity IS NOT NULL AND length(upstream_fact_identity) = 64)
  )""",
        "",
    ),
    (
        "DATABASE_ROW_PROMOTED_TO_SOURCE_TRUTH",
        " CHECK (authority_ceiling = 'LEDGER_IS_NOT_SOURCE_OR_TEST_TRUTH')",
        "",
    ),
    (
        "DUPLICATE_LOGICAL_EVENT_WITH_DIFFERENT_ID",
        "event_digest TEXT NOT NULL UNIQUE",
        "event_digest TEXT NOT NULL",
    ),
    (
        "LEDGER_APPEND_ONLY",
        """CREATE TRIGGER event_no_update BEFORE UPDATE ON event
BEGIN SELECT RAISE(ABORT, 'LEDGER_APPEND_ONLY: an event row cannot be updated'); END;
""",
        "",
    ),
)


def knockout_plant(falsifier: str) -> None:
    conn = loaded(CORE)
    if falsifier == "SQLITE_EVENT_SEQUENCE_BREAK":
        conn.execute(
            "INSERT INTO event (seq, event_digest, event_kind, producer_binding_id, producer_kind, "
            "source_digest, payload) VALUES (?, ?, 'FACT_OBSERVED', ?, 'TEXTUAL_MATCH', ?, '{}')",
            (99, "a" * 64, ledger.PROVIDER_BINDING_ID, "b" * 64),
        )
    elif falsifier == "FACT_WITHOUT_SOURCE_OR_UPSTREAM_BINDING":
        node_key = conn.execute("SELECT node_key FROM node LIMIT 1").fetchone()[0]
        conn.execute(
            "INSERT INTO fact (fact_key, fact_kind, node_key, provider_fact_id, event_seq) "
            "VALUES (?, 'SYMBOL', ?, 'DTCR-SY-091', 1)",
            ("e" * 64, node_key),
        )
    elif falsifier == "DATABASE_ROW_PROMOTED_TO_SOURCE_TRUTH":
        fresh = ledger._connect(":memory:")
        fresh.executescript(ledger.DDL)
        fresh.execute(
            "INSERT INTO ledger_schema VALUES (?, ?, ?, 'SOURCE_TRUTH')",
            (ledger.SCHEMA_VERSION, ledger.LEDGER_SCHEMA_DIGEST, ledger.MIGRATION_DIGEST),
        )
    elif falsifier == "DUPLICATE_LOGICAL_EVENT_WITH_DIFFERENT_ID":
        ledger.append_event(conn, **DUPLICATE_EVENT_ARGS)
        ledger.append_event(conn, **DUPLICATE_EVENT_ARGS)
    else:
        conn.execute("UPDATE event SET payload = '{}' WHERE seq = 1")


def knockouts() -> int:
    original_ddl, original_digest = ledger.DDL, ledger.LEDGER_SCHEMA_DIGEST
    discriminating = 0
    for falsifier, fragment, replacement in KNOCKOUTS:
        global cases
        cases += 1
        if fragment not in original_ddl:
            failures.append(f"knockout {falsifier}: the guard it names is not in the DDL")
            continue
        ledger.DDL = original_ddl.replace(fragment, replacement)
        ledger.LEDGER_SCHEMA_DIGEST = ledger.hashlib.sha256(ledger.DDL.encode("utf-8")).hexdigest()
        try:
            knockout_plant(falsifier)
            discriminating += 1
        except (LedgerRefusal, sqlite3.IntegrityError) as exc:
            failures.append(
                f"knockout {falsifier}: still refused after its own guard was removed, so the "
                f"record naming that guard is wrong: {exc}"
            )
        finally:
            ledger.DDL, ledger.LEDGER_SCHEMA_DIGEST = original_ddl, original_digest
    return discriminating


# ---------------------------------------------------------------------------
# end to end on a real file
# ---------------------------------------------------------------------------

def end_to_end() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        db = tmp / "dtcr-ledger.sqlite3"
        conn = ledger.create_ledger(db, CORE["subject"])
        ledger.ingest(conn, CORE["observations"])
        conn.close()

        reopened = ledger.open_ledger(db)
        walk = ledger.traverse(
            reopened,
            seed_provider_id=PRICING,
            seed_scheme_digest=SCHEME_DIGEST,
            admitted_edge_kinds=["CALLS", "REFERENCES"],
            depth_limit=8,
            row_limit=5000,
        )
        artifact = ledger.emit_receipt(reopened, db)
        reopened.close()

        binding = artifact["ledger_binding"]
        check(
            "the receipt binds this file's digest",
            binding["database_sha256"] == ledger.file_digest(db),
            binding["database_sha256"],
        )
        check(
            "the receipt binds the subject commit and the row counts",
            binding["subject"] == CORE["subject"]
            and binding["row_counts"] == {"event": 9, "node": 4, "fact": 8, "edge": 3},
            str(binding["row_counts"]),
        )
        check(
            "the receipt grants nothing",
            set(artifact["fact_plane_receipt"]["grants"].values()) == {False},
        )
        return {
            "database_sha256": binding["database_sha256"],
            "export_digest": binding["export_digest"],
            "ledger_schema_digest": binding["ledger_schema_digest"],
            "migration_digest": binding["migration_digest"],
            "head_event_digest": artifact["fact_plane_receipt"]["ledger_event"]["event_digest"],
            "head_sequence": artifact["fact_plane_receipt"]["ledger_event"]["sequence"],
            "row_counts": binding["row_counts"],
            "output_edge_denominator": walk["traversal_binding"]["output_edge_denominator"],
            "input_edge_denominator": walk["traversal_binding"]["input_edge_denominator"],
        }


def main() -> int:
    positives()
    plants()
    discriminating = knockouts()
    receipt = end_to_end()
    print(
        f"fixtures=2 cases={cases} planted_mutations={len(mutations)} "
        f"knockouts={discriminating}/{len(KNOCKOUTS)} "
        f"ledger_schema_digest={ledger.LEDGER_SCHEMA_DIGEST[:16]} "
        f"database_sha256={receipt['database_sha256'][:16]} "
        f"export_digest={receipt['export_digest'][:16]} "
        f"row_counts={json.dumps(receipt['row_counts'], sort_keys=True)}"
    )
    if failures:
        for failure in failures:
            print(f"DTCR-SQLITE-LEDGER-RED {failure}", file=sys.stderr)
        return 2
    print(
        f"DTCR-SQLITE-LEDGER-GREEN {cases} cases, {len(mutations)} planted mutations refused, "
        f"{discriminating} of {len(KNOCKOUTS)} guards discriminating under knockout of themselves, "
        f"one real database file created, ingested, traversed and receipted on this host"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
