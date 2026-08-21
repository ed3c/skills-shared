#!/usr/bin/env python3
"""The DTCR canonical fact/event ledger, on SQLite, for one exact subject.

What this stores and what it refuses to be
------------------------------------------
The ledger is the append-only record that a normalized observation *arrived*:
which node identities exist, which source range or upstream fact each one is
bound to, which impact edges were derived, and in what order those arrivals
happened. That is the whole of its authority. The source, the tests and the
history of the repository are read from Git and from the runs themselves, and a
row here never becomes any of them: `ledger_schema.authority_ceiling` is a CHECK
constraint pinned to one literal, so a database that claims to be source truth
cannot be opened, let alone queried.

Three laws are carried structurally rather than by convention, because each one
has a failure mode that reads as green:

*Sequence integrity.* `event.seq` is a dense chain starting at 1. A BEFORE
INSERT trigger refuses any row that is not exactly one past the head, and the
UPDATE/DELETE triggers refuse every rewrite, so there is no path that renumbers
history. The event's identity is the digest of its own content, derived here and
never supplied by a caller, which is why the same logical event cannot be
written twice under two identities: `event_digest` is UNIQUE, and
`verify_readback` recomputes every stored digest from the stored payload.

*Normalization before identity.* A provider's own symbol string is not an
identity in this ledger. `node_key` is the digest of the normalization scheme
digest together with the provider-scoped id, so two providers that spell the
same symbol differently get different keys, and the same spelling under two
schemes never silently merges.

*Bounded traversal.* `TRAVERSAL_SQL` is a module constant. It carries the depth
comparison, the cycle guard and the row limit in its text, `traverse` asserts
those three fragments are present before it executes anything, and no function
in this file builds traversal SQL from a string. An unbounded recursive CTE is
therefore not a query this adapter can be asked for; it is a query that does not
exist in it.

The exported reading of a ledger is deterministic: the same admitted input
replayed in the same order produces the same export digest, which `emit_receipt`
verifies by replaying its own export into a fresh in-memory database before it
will write a receipt. Raw database file bytes are *not* claimed to be identical
across hosts; the receipt records the local file digest as the local file
digest.

Exit codes: 0 green, 2 a refusal fired, 64 unusable input, 70 jsonschema absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "DTCR-SQLITE-LEDGER-UNUSABLE: jsonschema is required. This adapter "
        "validates every ingested observation and every emitted artifact "
        "against the frozen DTCR schemas; skipping that would report the same "
        "green as running it.",
        file=sys.stderr,
    )
    raise SystemExit(70)

ADAPTER_DIR = Path(__file__).resolve().parent
SKILL_DIR = ADAPTER_DIR.parents[1]
SCHEMA_DIR = SKILL_DIR / "references" / "schemas"

SCHEMA_VERSION = 1
AUTHORITY_CEILING = "LEDGER_IS_NOT_SOURCE_OR_TEST_TRUTH"
ADAPTER_NAME = "dtcr-sqlite-ledger"
ADAPTER_VERSION = "1.0.0"

# The closed edge vocabulary the frozen blast-radius-path schema admits. A
# traversal is only ever allowed to walk a subset of this.
ADMITTED_EDGE_KINDS = ("CALLS", "REFERENCES", "IMPLEMENTS", "INHERITS", "IMPORTS", "DEFINES")
# The frozen blast-radius-path schema caps depth_limit at 64 and requires at
# least 1. Repeating the bound here is deliberate: the query is refused before
# it runs, not after the schema rejects the result of a query that already ran.
MAX_DEPTH_LIMIT = 64
# Edge provenance vocabularies differ between the two frozen schemas: symbol-fact
# admits NOT_APPLICABLE, blast-radius-path admits MIXED instead. A relationship
# whose provenance is NOT_APPLICABLE has no graph provenance a traversal could
# report, so it is refused at ingest rather than laundered into MIXED later.
EDGE_PROVENANCE = ("COMPILER_RESOLVED_CALL", "OCCURRENCE_ENCLOSING_RANGE_HEURISTIC", "TEXTUAL_MATCH")


class LedgerRefusal(Exception):
    """A ledger law refused an operation. Carries the falsifier it killed."""


class Unusable(Exception):
    """The input could not be read at all, which is not the same as a refusal."""


# ---------------------------------------------------------------------------
# digests
# ---------------------------------------------------------------------------

def canonical(value: Any) -> bytes:
    """One byte sequence per value, independent of dict insertion order."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_of(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def node_key_of(provider_scoped_id: str, scheme_digest: str) -> str:
    """Identity = normalization scheme digest + provider string, never the string alone."""
    return digest_of({"scheme_digest": scheme_digest, "provider_scoped_id": provider_scoped_id})


# ---------------------------------------------------------------------------
# schema
# ---------------------------------------------------------------------------

DDL = """
CREATE TABLE ledger_schema (
  schema_version INTEGER PRIMARY KEY CHECK (schema_version = 1),
  ledger_schema_digest TEXT NOT NULL CHECK (length(ledger_schema_digest) = 64 AND ledger_schema_digest NOT GLOB '*[^0-9a-f]*'),
  migration_digest TEXT NOT NULL CHECK (length(migration_digest) = 64 AND migration_digest NOT GLOB '*[^0-9a-f]*'),
  authority_ceiling TEXT NOT NULL CHECK (authority_ceiling = 'LEDGER_IS_NOT_SOURCE_OR_TEST_TRUTH')
);

CREATE TABLE subject (
  subject_row INTEGER PRIMARY KEY CHECK (subject_row = 1),
  repository_binding_id TEXT NOT NULL CHECK (repository_binding_id GLOB 'DTCR-RB-*' AND length(repository_binding_id) = 24),
  commit_sha TEXT NOT NULL CHECK (length(commit_sha) = 40 AND commit_sha NOT GLOB '*[^0-9a-f]*'),
  tree_sha TEXT NOT NULL CHECK (length(tree_sha) = 40 AND tree_sha NOT GLOB '*[^0-9a-f]*')
);

CREATE TABLE event (
  seq INTEGER PRIMARY KEY CHECK (seq >= 1),
  event_digest TEXT NOT NULL UNIQUE CHECK (length(event_digest) = 64 AND event_digest NOT GLOB '*[^0-9a-f]*'),
  event_kind TEXT NOT NULL CHECK (event_kind IN ('LEDGER_OPENED', 'FACT_OBSERVED')),
  producer_binding_id TEXT NOT NULL CHECK (producer_binding_id GLOB 'DTCR-PB-*' AND length(producer_binding_id) = 24),
  producer_kind TEXT NOT NULL CHECK (producer_kind IN ('COMPILER_RESOLVED_CALL', 'OCCURRENCE_ENCLOSING_RANGE_HEURISTIC', 'TEXTUAL_MATCH', 'NOT_APPLICABLE')),
  source_digest TEXT NOT NULL CHECK (length(source_digest) = 64 AND source_digest NOT GLOB '*[^0-9a-f]*'),
  payload TEXT NOT NULL
);

CREATE TABLE node (
  node_key TEXT PRIMARY KEY CHECK (length(node_key) = 64 AND node_key NOT GLOB '*[^0-9a-f]*'),
  provider_scoped_id TEXT NOT NULL CHECK (length(provider_scoped_id) >= 1),
  normalization_scheme TEXT NOT NULL CHECK (length(normalization_scheme) >= 2),
  normalization_scheme_digest TEXT NOT NULL CHECK (length(normalization_scheme_digest) = 64 AND normalization_scheme_digest NOT GLOB '*[^0-9a-f]*'),
  introduced_by_seq INTEGER NOT NULL REFERENCES event(seq)
);

CREATE TABLE fact (
  fact_key TEXT PRIMARY KEY CHECK (length(fact_key) = 64 AND fact_key NOT GLOB '*[^0-9a-f]*'),
  fact_kind TEXT NOT NULL CHECK (fact_kind IN ('SYMBOL', 'OCCURRENCE', 'RELATIONSHIP')),
  node_key TEXT NOT NULL REFERENCES node(node_key),
  provider_fact_id TEXT NOT NULL CHECK (length(provider_fact_id) >= 1),
  blob_path TEXT,
  blob_sha TEXT CHECK (blob_sha IS NULL OR (length(blob_sha) = 40 AND blob_sha NOT GLOB '*[^0-9a-f]*')),
  start_byte INTEGER,
  end_byte INTEGER,
  upstream_fact_identity TEXT,
  event_seq INTEGER NOT NULL REFERENCES event(seq),
  CHECK (
    (blob_path IS NOT NULL AND blob_sha IS NOT NULL AND start_byte IS NOT NULL AND end_byte IS NOT NULL)
    OR (upstream_fact_identity IS NOT NULL AND length(upstream_fact_identity) = 64)
  )
);

CREATE TABLE edge (
  edge_key TEXT PRIMARY KEY CHECK (length(edge_key) = 64 AND edge_key NOT GLOB '*[^0-9a-f]*'),
  from_node TEXT NOT NULL REFERENCES node(node_key),
  to_node TEXT NOT NULL REFERENCES node(node_key),
  edge_kind TEXT NOT NULL CHECK (edge_kind IN ('CALLS', 'REFERENCES', 'IMPLEMENTS', 'INHERITS', 'IMPORTS', 'DEFINES')),
  edge_provenance TEXT NOT NULL CHECK (edge_provenance IN ('COMPILER_RESOLVED_CALL', 'OCCURRENCE_ENCLOSING_RANGE_HEURISTIC', 'TEXTUAL_MATCH')),
  edge_completeness TEXT NOT NULL CHECK (edge_completeness IN ('COMPLETE_FOR_RESOLVED_EDGES', 'PARTIAL_LOWER_BOUND', 'UNKNOWN')),
  event_seq INTEGER NOT NULL REFERENCES event(seq),
  UNIQUE (from_node, to_node, edge_kind)
);

CREATE INDEX edge_from ON edge(from_node, edge_kind);

CREATE TRIGGER event_sequence_integrity BEFORE INSERT ON event
BEGIN
  SELECT RAISE(ABORT, 'SQLITE_EVENT_SEQUENCE_BREAK: an event must be exactly one past the ledger head')
  WHERE NEW.seq <> (SELECT IFNULL(MAX(seq), 0) + 1 FROM event);
END;

CREATE TRIGGER event_no_update BEFORE UPDATE ON event
BEGIN SELECT RAISE(ABORT, 'LEDGER_APPEND_ONLY: an event row cannot be updated'); END;
CREATE TRIGGER event_no_delete BEFORE DELETE ON event
BEGIN SELECT RAISE(ABORT, 'LEDGER_APPEND_ONLY: an event row cannot be deleted'); END;
CREATE TRIGGER node_no_update BEFORE UPDATE ON node
BEGIN SELECT RAISE(ABORT, 'LEDGER_APPEND_ONLY: a node row cannot be updated'); END;
CREATE TRIGGER node_no_delete BEFORE DELETE ON node
BEGIN SELECT RAISE(ABORT, 'LEDGER_APPEND_ONLY: a node row cannot be deleted'); END;
CREATE TRIGGER fact_no_update BEFORE UPDATE ON fact
BEGIN SELECT RAISE(ABORT, 'LEDGER_APPEND_ONLY: a fact row cannot be updated'); END;
CREATE TRIGGER fact_no_delete BEFORE DELETE ON fact
BEGIN SELECT RAISE(ABORT, 'LEDGER_APPEND_ONLY: a fact row cannot be deleted'); END;
CREATE TRIGGER edge_no_update BEFORE UPDATE ON edge
BEGIN SELECT RAISE(ABORT, 'LEDGER_APPEND_ONLY: an edge row cannot be updated'); END;
CREATE TRIGGER edge_no_delete BEFORE DELETE ON edge
BEGIN SELECT RAISE(ABORT, 'LEDGER_APPEND_ONLY: an edge row cannot be deleted'); END;
CREATE TRIGGER schema_no_update BEFORE UPDATE ON ledger_schema
BEGIN SELECT RAISE(ABORT, 'LEDGER_APPEND_ONLY: the schema row cannot be updated'); END;
"""

LEDGER_SCHEMA_DIGEST = hashlib.sha256(DDL.encode("utf-8")).hexdigest()
# One migration exists. The digest covers the ordered list rather than the last
# entry, so inserting a migration ahead of another changes it.
MIGRATION_DIGEST = digest_of([{"version": SCHEMA_VERSION, "ddl_sha256": LEDGER_SCHEMA_DIGEST}])
PROVIDER_BINDING_ID = "DTCR-PB-" + digest_of({"name": ADAPTER_NAME, "version": ADAPTER_VERSION})[:16]


# ---------------------------------------------------------------------------
# bounded traversal
# ---------------------------------------------------------------------------

TRAVERSAL_SQL = """
WITH RECURSIVE reach(from_node, to_node, edge_kind, depth, path) AS (
    SELECT e.from_node, e.to_node, e.edge_kind, 1,
           '|' || e.from_node || '|' || e.to_node || '|'
      FROM edge e
     WHERE e.from_node = :seed
       AND e.edge_kind IN (SELECT value FROM json_each(:admitted_kinds))
  UNION ALL
    SELECT e.from_node, e.to_node, e.edge_kind, r.depth + 1,
           r.path || e.to_node || '|'
      FROM edge e
      JOIN reach r ON e.from_node = r.to_node
     WHERE r.depth < :depth_limit
       AND instr(r.path, '|' || e.to_node || '|') = 0
       AND e.edge_kind IN (SELECT value FROM json_each(:admitted_kinds))
)
SELECT from_node, to_node, edge_kind, depth, path
  FROM reach
 ORDER BY depth, from_node, to_node, edge_kind
 LIMIT :row_limit
"""

# The three fragments that make the recursion terminate. `traverse` asserts all
# three are present in the SQL it is about to execute, so a future edit that
# drops one turns every traversal red instead of turning one of them unbounded.
REQUIRED_BOUNDS = (
    ("r.depth < :depth_limit", "depth bound"),
    ("instr(r.path, '|' || e.to_node || '|') = 0", "cycle guard"),
    ("LIMIT :row_limit", "row bound"),
)


def assert_bounded(sql: str) -> None:
    missing = [name for fragment, name in REQUIRED_BOUNDS if fragment not in sql]
    if missing:
        raise LedgerRefusal(
            "UNBOUNDED_RECURSIVE_CTE: the traversal statement is missing its "
            + ", ".join(missing)
            + ". A recursive CTE over a graph with cycles either carries its bounds or runs "
            "until something else stops it."
        )


# ---------------------------------------------------------------------------
# frozen schema validators
# ---------------------------------------------------------------------------

_VALIDATORS: dict[str, Draft202012Validator] = {}


def validator(name: str) -> Draft202012Validator:
    """A validator for one frozen DTCR schema, read from the skill's references."""
    if name not in _VALIDATORS:
        path = SCHEMA_DIR / f"{name}.schema.json"
        if not path.is_file():
            raise Unusable(f"frozen schema {path} is absent; nothing here can be validated")
        _VALIDATORS[name] = Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))
    return _VALIDATORS[name]


def enforce(name: str, instance: Any, what: str) -> Any:
    errors = sorted(validator(name).iter_errors(instance), key=str)
    if errors:
        raise LedgerRefusal(f"{what} is refused by the frozen {name} schema: {errors[0].message}")
    return instance


# ---------------------------------------------------------------------------
# open / create
# ---------------------------------------------------------------------------

def _connect(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_ledger(path: Path, subject: dict[str, str]) -> sqlite3.Connection:
    """Create a ledger bound to exactly one subject, and record that opening."""
    path = Path(path)
    if path.exists():
        raise LedgerRefusal(f"{path} already exists; a ledger is never reopened for creation")
    conn = _connect(path)
    conn.executescript(DDL)
    conn.execute(
        "INSERT INTO ledger_schema VALUES (?, ?, ?, ?)",
        (SCHEMA_VERSION, LEDGER_SCHEMA_DIGEST, MIGRATION_DIGEST, AUTHORITY_CEILING),
    )
    conn.execute(
        "INSERT INTO subject VALUES (1, ?, ?, ?)",
        (subject["repository_binding_id"], subject["commit"], subject["tree"]),
    )
    append_event(
        conn,
        event_kind="LEDGER_OPENED",
        producer_kind="NOT_APPLICABLE",
        source_digest=digest_of(subject),
        payload={
            "schema_version": SCHEMA_VERSION,
            "ledger_schema_digest": LEDGER_SCHEMA_DIGEST,
            "migration_digest": MIGRATION_DIGEST,
            "authority_ceiling": AUTHORITY_CEILING,
        },
    )
    return conn


def open_ledger(path: Path) -> sqlite3.Connection:
    path = Path(path)
    if not path.is_file():
        raise Unusable(f"{path} is not a ledger file")
    conn = _connect(path)
    row = conn.execute("SELECT * FROM ledger_schema").fetchone()
    if row is None:
        raise Unusable(f"{path} carries no ledger_schema row")
    if row["ledger_schema_digest"] != LEDGER_SCHEMA_DIGEST:
        raise LedgerRefusal(
            f"{path} was written under schema digest {row['ledger_schema_digest']}, and this "
            f"adapter carries {LEDGER_SCHEMA_DIGEST}. A migration has to be written down before "
            f"a reader may assume the two are the same shape."
        )
    return conn


def read_subject(conn: sqlite3.Connection) -> dict[str, str]:
    row = conn.execute("SELECT * FROM subject").fetchone()
    if row is None:
        raise Unusable("the ledger carries no subject row")
    return {
        "repository_binding_id": row["repository_binding_id"],
        "commit": row["commit_sha"],
        "tree": row["tree_sha"],
    }


# ---------------------------------------------------------------------------
# append
# ---------------------------------------------------------------------------

def append_event(
    conn: sqlite3.Connection,
    *,
    event_kind: str,
    producer_kind: str,
    source_digest: str,
    payload: dict[str, Any],
) -> tuple[int, str]:
    """Append one event. The identity is derived here and never supplied.

    Because the digest is a function of the content, the same logical event
    always derives the same identity, and the UNIQUE constraint on
    `event_digest` is what refuses a second copy of it under a second name.
    """
    subject = read_subject(conn)
    head = conn.execute("SELECT IFNULL(MAX(seq), 0) FROM event").fetchone()[0]
    body = {
        "ledger_schema_digest": LEDGER_SCHEMA_DIGEST,
        "subject": subject,
        "event_kind": event_kind,
        "producer_binding_id": PROVIDER_BINDING_ID,
        "producer_kind": producer_kind,
        "source_digest": source_digest,
        "payload": payload,
    }
    event_digest = digest_of(body)
    try:
        conn.execute(
            "INSERT INTO event (seq, event_digest, event_kind, producer_binding_id, "
            "producer_kind, source_digest, payload) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                head + 1,
                event_digest,
                event_kind,
                PROVIDER_BINDING_ID,
                producer_kind,
                source_digest,
                canonical(payload).decode("utf-8"),
            ),
        )
    except sqlite3.IntegrityError as exc:
        if "event.event_digest" in str(exc):
            raise LedgerRefusal(
                f"DUPLICATE_LOGICAL_EVENT: {event_digest} is already at sequence "
                f"{conn.execute('SELECT seq FROM event WHERE event_digest = ?', (event_digest,)).fetchone()[0]}. "
                f"The identity is the content, so a second copy cannot take a second identity."
            ) from exc
        raise LedgerRefusal(f"the event was refused by the ledger schema: {exc}") from exc
    return head + 1, event_digest


def _observation_nodes(observation: dict[str, Any]) -> list[dict[str, str]]:
    """Every provider identity the observation introduces or refers to."""
    kind = observation["fact_kind"]
    if kind == "SYMBOL":
        identities = [observation["symbol"]["identity"]]
    elif kind == "OCCURRENCE":
        identities = [observation["occurrence"]["identity"]]
    else:
        identities = [observation["relationship"]["from"], observation["relationship"]["to"]]
    return [
        {
            "provider_scoped_id": identity["provider_scoped_id"],
            "normalization_scheme": identity["normalization"]["scheme"],
            "normalization_scheme_digest": identity["normalization"]["scheme_digest"],
        }
        for identity in identities
    ]


def ingest(conn: sqlite3.Connection, observations: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Ingest schema-valid symbol facts as events, nodes, facts and impact edges.

    One transaction for the whole batch. A refusal anywhere rolls the batch back
    and raises, so a partially written batch is not a state this function can
    leave behind and call an outcome.
    """
    subject = read_subject(conn)
    before = row_counts(conn)
    conn.execute("BEGIN IMMEDIATE")
    try:
        for index, observation in enumerate(observations):
            enforce("symbol-fact", observation, f"observation[{index}]")
            if observation["subject"] != subject:
                raise LedgerRefusal(
                    f"WRONG_REPOSITORY_OR_TREE: observation[{index}] "
                    f"{observation['fact_id']} binds {observation['subject']}, and this ledger "
                    f"binds {subject}. One ledger holds one exact subject."
                )
            _ingest_one(conn, observation, index)
        conn.execute("COMMIT")
    except Exception as exc:
        conn.execute("ROLLBACK")
        after = row_counts(conn)
        if after != before:
            raise LedgerRefusal(
                f"TRANSACTION_FAILURE_HIDDEN: the batch was refused ({exc}) but the row counts "
                f"moved from {before} to {after}."
            ) from exc
        raise
    return row_counts(conn)


def _ingest_one(conn: sqlite3.Connection, observation: dict[str, Any], index: int) -> None:
    kind = observation["fact_kind"]
    source_digest = digest_of(observation)
    relationship = observation.get("relationship")
    producer_kind = relationship["graph_evidence"]["provenance"] if relationship else "NOT_APPLICABLE"
    if kind == "RELATIONSHIP" and producer_kind not in EDGE_PROVENANCE:
        raise LedgerRefusal(
            f"observation[{index}] {observation['fact_id']} is a relationship whose provenance is "
            f"{producer_kind!r}. An edge with no graph provenance has nothing a traversal could "
            f"report as its denominator, so it is refused here rather than reported as MIXED later."
        )
    seq, _digest = append_event(
        conn,
        event_kind="FACT_OBSERVED",
        producer_kind=producer_kind,
        source_digest=source_digest,
        payload={"fact_id": observation["fact_id"], "fact_kind": kind, "observation": observation},
    )

    for node in _observation_nodes(observation):
        key = node_key_of(node["provider_scoped_id"], node["normalization_scheme_digest"])
        if kind == "RELATIONSHIP":
            # An endpoint is not introduced by the edge that mentions it. The
            # foreign key below is what refuses an edge into an unbound node.
            continue
        conn.execute(
            "INSERT OR IGNORE INTO node VALUES (?, ?, ?, ?, ?)",
            (
                key,
                node["provider_scoped_id"],
                node["normalization_scheme"],
                node["normalization_scheme_digest"],
                seq,
            ),
        )

    index_binding = observation["index_binding"]
    if kind == "OCCURRENCE":
        occurrence = observation["occurrence"]
        identity = occurrence["identity"]
        node_key = node_key_of(identity["provider_scoped_id"], identity["normalization"]["scheme_digest"])
        blob, rng = occurrence["blob"], occurrence["range"]
        source = (blob["path"], blob["blob"], rng["start_byte"], rng["end_byte"], None)
    else:
        identity = (
            observation["symbol"]["identity"] if kind == "SYMBOL" else observation["relationship"]["from"]
        )
        node_key = node_key_of(identity["provider_scoped_id"], identity["normalization"]["scheme_digest"])
        source = (None, None, None, None, index_binding["index_digest"])

    fact_key = digest_of(
        {
            "fact_kind": kind,
            "node_key": node_key,
            "provider_fact_id": observation["fact_id"],
            "source": list(source),
            "output_digest": observation["output_digest"],
        }
    )
    try:
        conn.execute(
            "INSERT INTO fact (fact_key, fact_kind, node_key, provider_fact_id, blob_path, "
            "blob_sha, start_byte, end_byte, upstream_fact_identity, event_seq) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (fact_key, kind, node_key, observation["fact_id"], *source, seq),
        )
    except sqlite3.IntegrityError as exc:
        raise LedgerRefusal(
            f"observation[{index}] {observation['fact_id']}: the fact row was refused: {exc}"
        ) from exc

    if kind != "RELATIONSHIP":
        return

    # The relationship reads "from CALLS to". Impact runs the other way: a
    # change in the callee reaches the caller. The ledger stores the impact
    # direction, which is the direction the blast-radius traversal walks.
    source_identity, target_identity = relationship["from"], relationship["to"]
    caller = node_key_of(
        source_identity["provider_scoped_id"], source_identity["normalization"]["scheme_digest"]
    )
    callee = node_key_of(
        target_identity["provider_scoped_id"], target_identity["normalization"]["scheme_digest"]
    )
    edge_kind = relationship["relationship_kind"]
    edge_key = digest_of({"from": callee, "to": caller, "edge_kind": edge_kind})
    try:
        conn.execute(
            "INSERT INTO edge VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                edge_key,
                callee,
                caller,
                edge_kind,
                producer_kind,
                relationship["graph_evidence"]["completeness"],
                seq,
            ),
        )
    except sqlite3.IntegrityError as exc:
        raise LedgerRefusal(
            f"EDGE_ENDPOINT_UNBOUND: observation[{index}] {observation['fact_id']} draws a "
            f"{edge_kind} edge whose endpoints are not both nodes this ledger introduced: {exc}"
        ) from exc


def row_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("event", "node", "fact", "edge")
    }


# ---------------------------------------------------------------------------
# readback
# ---------------------------------------------------------------------------

def verify_readback(conn: sqlite3.Connection) -> dict[str, int]:
    """Recompute every derived identity from the stored bytes.

    A digest column that is only ever written and never recomputed records a
    claim nobody checks. This walks the chain: dense sequence from 1, every
    event digest re-derived from its own payload, every node key re-derived from
    its normalization, every edge endpoint resolvable.
    """
    subject = read_subject(conn)
    schema_row = conn.execute("SELECT * FROM ledger_schema").fetchone()
    if schema_row["authority_ceiling"] != AUTHORITY_CEILING:
        raise LedgerRefusal(
            "DATABASE_ROW_PROMOTED_TO_SOURCE_TRUTH: the ledger's authority ceiling reads "
            f"{schema_row['authority_ceiling']!r}."
        )
    expected = 0
    for row in conn.execute("SELECT * FROM event ORDER BY seq"):
        expected += 1
        if row["seq"] != expected:
            raise LedgerRefusal(
                f"SQLITE_EVENT_SEQUENCE_BREAK: sequence {row['seq']} found where {expected} was "
                f"due. A gap is either a deleted event or a renumbered one."
            )
        derived = digest_of(
            {
                "ledger_schema_digest": schema_row["ledger_schema_digest"],
                "subject": subject,
                "event_kind": row["event_kind"],
                "producer_binding_id": row["producer_binding_id"],
                "producer_kind": row["producer_kind"],
                "source_digest": row["source_digest"],
                "payload": json.loads(row["payload"]),
            }
        )
        if derived != row["event_digest"]:
            raise LedgerRefusal(
                f"SQLITE_EVENT_ID_DRIFT: event {row['seq']} stores {row['event_digest']} and its "
                f"own payload derives {derived}."
            )
    for row in conn.execute("SELECT * FROM node ORDER BY node_key"):
        derived = node_key_of(row["provider_scoped_id"], row["normalization_scheme_digest"])
        if derived != row["node_key"]:
            raise LedgerRefusal(
                f"NODE_IDENTITY_DRIFT: node {row['node_key']} does not derive from its own "
                f"normalization; a provider string was admitted as an identity without it."
            )
    unbound = conn.execute(
        "SELECT COUNT(*) FROM edge WHERE from_node NOT IN (SELECT node_key FROM node) "
        "OR to_node NOT IN (SELECT node_key FROM node)"
    ).fetchone()[0]
    if unbound:
        raise LedgerRefusal(f"EDGE_ENDPOINT_UNBOUND: {unbound} edge(s) point at no node row")
    return row_counts(conn)


def resolve_node(conn: sqlite3.Connection, provider_scoped_id: str, scheme_digest: str) -> str:
    key = node_key_of(provider_scoped_id, scheme_digest)
    row = conn.execute("SELECT node_key FROM node WHERE node_key = ?", (key,)).fetchone()
    if row is None:
        raise LedgerRefusal(
            f"SEED_NOT_IN_LEDGER: {provider_scoped_id!r} under scheme digest {scheme_digest[:12]}… "
            f"was never introduced. An absent seed is not an empty blast radius."
        )
    return key


def _node_object(conn: sqlite3.Connection, node_key: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM node WHERE node_key = ?", (node_key,)).fetchone()
    return {
        "provider_scoped_id": row["provider_scoped_id"],
        "normalization": {
            "scheme": row["normalization_scheme"],
            "scheme_digest": row["normalization_scheme_digest"],
        },
    }


# ---------------------------------------------------------------------------
# traversal
# ---------------------------------------------------------------------------

def edge_set_binding(conn: sqlite3.Connection, kinds: tuple[str, ...]) -> dict[str, Any]:
    """The complete admitted edge denominator this traversal could have walked."""
    rows = conn.execute(
        "SELECT from_node, to_node, edge_kind, edge_provenance, edge_completeness FROM edge "
        f"WHERE edge_kind IN ({','.join('?' * len(kinds))}) "
        "ORDER BY from_node, to_node, edge_kind",
        kinds,
    ).fetchall()
    return {
        "edge_set_digest": digest_of([dict(row) for row in rows]),
        "input_edge_denominator": len(rows),
        "rows": [dict(row) for row in rows],
    }


def derive_completeness(terminated_by: str, walked: list[dict[str, Any]]) -> str:
    """A truncated walk is a lower bound, whatever the edges themselves claimed."""
    if terminated_by != "EDGE_SET_EXHAUSTED":
        return "PARTIAL_LOWER_BOUND"
    claims = {row["edge_completeness"] for row in walked}
    if claims == {"COMPLETE_FOR_RESOLVED_EDGES"}:
        return "COMPLETE_FOR_RESOLVED_EDGES"
    if "UNKNOWN" in claims:
        return "UNKNOWN"
    return "PARTIAL_LOWER_BOUND"


def assert_not_overclaimed(terminated_by: str, completeness: str) -> None:
    if terminated_by != "EDGE_SET_EXHAUSTED" and completeness == "COMPLETE_FOR_RESOLVED_EDGES":
        raise LedgerRefusal(
            "PARTIAL_EDGE_SET_REPORTED_AS_COMPLETE_BLAST_RADIUS: the walk stopped at "
            f"{terminated_by} and the result claims to be complete for the resolved edges."
        )


def traverse(
    conn: sqlite3.Connection,
    *,
    seed_provider_id: str,
    seed_scheme_digest: str,
    admitted_edge_kinds: Iterable[str],
    depth_limit: int,
    row_limit: int,
    path_id: str = "DTCR-BR-010",
) -> dict[str, Any]:
    """Walk the admitted edge set from one seed, under declared bounds.

    Returns the frozen `dtcr/blast-radius-path/v1` instance together with the
    denominators the frozen schema has no room for: how many admitted edges the
    ledger holds, how many the path reports, and the digest of the database the
    walk read.
    """
    assert_bounded(TRAVERSAL_SQL)
    kinds = tuple(dict.fromkeys(admitted_edge_kinds))
    if not kinds:
        raise LedgerRefusal("an empty admitted edge set walks nothing and describes nothing")
    outside = [kind for kind in kinds if kind not in ADMITTED_EDGE_KINDS]
    if outside:
        raise LedgerRefusal(
            f"EDGE_KIND_OUTSIDE_ADMITTED_SET: {outside} is not in the closed vocabulary "
            f"{list(ADMITTED_EDGE_KINDS)}. Reach over an unadmitted kind is reach through a graph "
            f"nobody admitted."
        )
    for name, value, ceiling in (("depth_limit", depth_limit, MAX_DEPTH_LIMIT), ("row_limit", row_limit, None)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise LedgerRefusal(
                f"UNBOUNDED_RECURSIVE_CTE: {name}={value!r} is not a positive integer. There is no "
                f"value here spelling unbounded."
            )
        if ceiling is not None and value > ceiling:
            raise LedgerRefusal(f"{name}={value} exceeds the frozen ceiling of {ceiling}")

    seed_key = resolve_node(conn, seed_provider_id, seed_scheme_digest)
    binding = edge_set_binding(conn, kinds)
    rows = conn.execute(
        TRAVERSAL_SQL,
        {
            "seed": seed_key,
            "admitted_kinds": json.dumps(list(kinds)),
            "depth_limit": depth_limit,
            "row_limit": row_limit,
        },
    ).fetchall()
    if not rows:
        raise LedgerRefusal(
            f"EMPTY_REACH: no admitted {list(kinds)} edge leaves the seed. An absent path is "
            f"reported as absent, not as a blast radius of size one."
        )

    hops = [dict(row) for row in rows]
    depth = max(hop["depth"] for hop in hops)
    if depth > depth_limit:
        raise LedgerRefusal(
            f"TRAVERSAL_DEPTH_EXCEEDS_DECLARED_LIMIT: the walk reached depth {depth} under a "
            f"declared limit of {depth_limit}."
        )

    by_endpoints = {(row["from_node"], row["to_node"], row["edge_kind"]): row for row in binding["rows"]}
    walked = [by_endpoints[(hop["from_node"], hop["to_node"], hop["edge_kind"])] for hop in hops]

    cycle_blocked = any(
        edge["from_node"] == hop["to_node"] and f"|{edge['to_node']}|" in hop["path"]
        for hop in hops
        for edge in binding["rows"]
    )
    frontier_open = any(
        hop["depth"] == depth_limit and edge["from_node"] == hop["to_node"] for hop in hops for edge in binding["rows"]
    )
    if len(hops) == row_limit:
        terminated_by = "ROW_LIMIT_REACHED"
    elif frontier_open:
        terminated_by = "DEPTH_LIMIT_REACHED"
    elif cycle_blocked:
        terminated_by = "CYCLE_GUARD"
    else:
        terminated_by = "EDGE_SET_EXHAUSTED"

    completeness = derive_completeness(terminated_by, walked)
    assert_not_overclaimed(terminated_by, completeness)

    provenances = {row["edge_provenance"] for row in walked}
    visited: list[str] = [seed_key]
    for hop in hops:
        for endpoint in (hop["from_node"], hop["to_node"]):
            if endpoint not in visited:
                visited.append(endpoint)

    path = {
        "schema": "dtcr/blast-radius-path/v1",
        "path_id": path_id,
        "subject": read_subject(conn),
        "seed": _node_object(conn, seed_key),
        "edge_set": {
            "edge_set_digest": binding["edge_set_digest"],
            "admitted_edge_kinds": list(kinds),
            "edge_provenance": provenances.pop() if len(provenances) == 1 else "MIXED",
            "edge_completeness": completeness,
        },
        "hops": [
            {
                "from": _node_object(conn, hop["from_node"]),
                "to": _node_object(conn, hop["to_node"]),
                "edge_kind": hop["edge_kind"],
            }
            for hop in hops
        ],
        "nodes_visited": [_node_object(conn, key) for key in visited],
        "traversal_bounds": {
            "depth": depth,
            "depth_limit": depth_limit,
            "row_limit": row_limit,
            "terminated_by": terminated_by,
        },
        "authority_ceiling": {"complete_reachable_set": False, "semantic_truth": False, "task_pass": False},
    }
    enforce("blast-radius-path", path, "the emitted traversal")
    return {
        "blast_radius_path": path,
        "traversal_binding": {
            "ledger_schema_digest": LEDGER_SCHEMA_DIGEST,
            "traversal_sql_digest": hashlib.sha256(TRAVERSAL_SQL.encode("utf-8")).hexdigest(),
            "input_edge_denominator": binding["input_edge_denominator"],
            "output_edge_denominator": len(hops),
            "output_node_denominator": len(visited),
            "cycle_guard_fired": cycle_blocked,
            "authority_ceiling": {
                "source_truth": False,
                "test_truth": False,
                "git_history_truth": False,
                "complete_reachable_set": False,
                "task_pass": False,
                "merge": False,
            },
            "warnings": (
                []
                if terminated_by == "EDGE_SET_EXHAUSTED"
                else [f"the walk stopped at {terminated_by}, so the reported reach is a lower bound"]
            ),
            "omissions": [
                "edges the fact plane never resolved are absent from the denominator and from the walk",
                "dynamic dispatch, configuration and generated wiring move impact along edges no static set holds",
            ],
        },
    }


# ---------------------------------------------------------------------------
# export / replay
# ---------------------------------------------------------------------------

def export_ledger(conn: sqlite3.Connection) -> dict[str, Any]:
    """A deterministic reading of the ledger: same admitted input, same bytes."""
    tables = {
        "event": "SELECT * FROM event ORDER BY seq",
        "node": "SELECT * FROM node ORDER BY node_key",
        "fact": "SELECT * FROM fact ORDER BY fact_key",
        "edge": "SELECT * FROM edge ORDER BY edge_key",
    }
    return {
        "ledger_export": "dtcr/sqlite-ledger-export/v1",
        "schema_version": SCHEMA_VERSION,
        "ledger_schema_digest": LEDGER_SCHEMA_DIGEST,
        "migration_digest": MIGRATION_DIGEST,
        "authority_ceiling": AUTHORITY_CEILING,
        "subject": read_subject(conn),
        **{name: [dict(row) for row in conn.execute(sql)] for name, sql in tables.items()},
    }


def replay(export: dict[str, Any], path: Path | str = ":memory:") -> sqlite3.Connection:
    """Rebuild a ledger from an export, in the recorded order.

    The sequence trigger is live during the replay, so an export whose events do
    not form a dense chain cannot be replayed into a ledger at all.
    """
    conn = _connect(path)
    conn.executescript(DDL)
    conn.execute(
        "INSERT INTO ledger_schema VALUES (?, ?, ?, ?)",
        (
            export["schema_version"],
            export["ledger_schema_digest"],
            export["migration_digest"],
            export["authority_ceiling"],
        ),
    )
    subject = export["subject"]
    conn.execute(
        "INSERT INTO subject VALUES (1, ?, ?, ?)",
        (subject["repository_binding_id"], subject["commit"], subject["tree"]),
    )
    conn.execute("BEGIN IMMEDIATE")
    for row in export["event"]:
        conn.execute(
            "INSERT INTO event (seq, event_digest, event_kind, producer_binding_id, producer_kind, "
            "source_digest, payload) VALUES (:seq, :event_digest, :event_kind, :producer_binding_id, "
            ":producer_kind, :source_digest, :payload)",
            row,
        )
    for row in export["node"]:
        conn.execute(
            "INSERT INTO node VALUES (:node_key, :provider_scoped_id, :normalization_scheme, "
            ":normalization_scheme_digest, :introduced_by_seq)",
            row,
        )
    for row in export["fact"]:
        conn.execute(
            "INSERT INTO fact VALUES (:fact_key, :fact_kind, :node_key, :provider_fact_id, "
            ":blob_path, :blob_sha, :start_byte, :end_byte, :upstream_fact_identity, :event_seq)",
            row,
        )
    for row in export["edge"]:
        conn.execute(
            "INSERT INTO edge VALUES (:edge_key, :from_node, :to_node, :edge_kind, "
            ":edge_provenance, :edge_completeness, :event_seq)",
            row,
        )
    conn.execute("COMMIT")
    return conn


# ---------------------------------------------------------------------------
# receipt
# ---------------------------------------------------------------------------

def emit_receipt(
    conn: sqlite3.Connection,
    db_path: Path,
    *,
    receipt_id: str = "DTCR-FR-010",
    coverage_ceiling_ref: str = "DTCR-CC-010",
    summary: str | None = None,
) -> dict[str, Any]:
    """Bind the database file digest, the row counts and the subject commit.

    The frozen fact-plane receipt is emitted unmodified and nested, so it can be
    lifted out and validated on its own. Everything the frozen shape has no room
    for -- the file digest, the row counts, the export digest -- sits beside it
    in a binding block that states its own ceiling.
    """
    counts = verify_readback(conn)
    export = export_ledger(conn)
    export_digest = digest_of(export)

    replayed = replay(export)
    try:
        replayed_digest = digest_of(export_ledger(replayed))
    finally:
        replayed.close()
    if replayed_digest != export_digest:
        raise LedgerRefusal(
            f"NONDETERMINISTIC_EXPORT: replaying this ledger's own export produced "
            f"{replayed_digest} against {export_digest}. An export that cannot be replayed into "
            f"an equivalent ledger is not a record anyone can re-derive."
        )

    head = conn.execute("SELECT seq, event_digest FROM event ORDER BY seq DESC LIMIT 1").fetchone()
    if head is None:
        raise LedgerRefusal("a ledger with no events has nothing to receipt")
    source_digests = [row[0] for row in conn.execute("SELECT source_digest FROM event ORDER BY seq")]

    receipt = {
        "schema": "dtcr/fact-plane-receipt/v1",
        "receipt_id": receipt_id,
        "subject": read_subject(conn),
        "arrival": "SANDBOX",
        "provider_runs": [
            {
                "provider_binding_id": PROVIDER_BINDING_ID,
                "executable_name": ADAPTER_NAME,
                "version": ADAPTER_VERSION,
                "executable_sha256": file_digest(Path(__file__)),
                "config_digest": MIGRATION_DIGEST,
                "input_digest": digest_of(source_digests),
                "output_digest": export_digest,
                "exit_code": 0,
                "outcome": "PASS",
                "warnings": [],
                "omissions": [
                    "the ledger records the observations it was given; unobserved code is absent "
                    "from every count here",
                ],
            }
        ],
        "ledger_event": {
            "event_digest": head["event_digest"],
            "sequence": head["seq"],
            "ledger_schema_digest": LEDGER_SCHEMA_DIGEST,
        },
        "bundle_digest": export_digest,
        "coverage_ceiling_ref": coverage_ceiling_ref,
        "summary": summary
        or (
            f"{counts['event']} events, {counts['node']} nodes, {counts['fact']} facts and "
            f"{counts['edge']} edges were ingested against this commit and replayed to the same "
            f"export digest."
        ),
        "grants": {
            "task_pass": False,
            "merge": False,
            "permission": False,
            "secret": False,
            "production": False,
            "release": False,
            "semantic_truth": False,
        },
    }
    enforce("fact-plane-receipt", receipt, "the emitted receipt")
    return {
        "fact_plane_receipt": receipt,
        "ledger_binding": {
            "database_sha256": file_digest(Path(db_path)),
            "database_path_basename": Path(db_path).name,
            "row_counts": counts,
            "subject": read_subject(conn),
            "schema_version": SCHEMA_VERSION,
            "ledger_schema_digest": LEDGER_SCHEMA_DIGEST,
            "migration_digest": MIGRATION_DIGEST,
            "export_digest": export_digest,
            "replayed_export_digest": replayed_digest,
            "transaction_state": "COMMITTED",
            "authority_ceiling": {
                "source_truth": False,
                "test_truth": False,
                "git_history_truth": False,
                "task_pass": False,
                "merge": False,
            },
            "omissions": [
                "the coverage ceiling named by coverage_ceiling_ref is produced by the coverage "
                "lane; this adapter records the reference, not the ceiling",
                "database file bytes are recorded as this host's bytes; cross-host byte identity "
                "is not claimed, and the export digest is the portable identity",
            ],
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _read_fixture(path: Path) -> dict[str, Any]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("subject", "observations"):
        if key not in document:
            raise Unusable(f"{path} carries no {key!r}")
    return document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--selftest", action="store_true", help="run the adapter's own battery")
    sub = parser.add_subparsers(dest="command")

    ingest_cmd = sub.add_parser("ingest", help="create the ledger if absent and ingest observations")
    ingest_cmd.add_argument("--db", required=True, type=Path)
    ingest_cmd.add_argument("--observations", required=True, type=Path)

    traverse_cmd = sub.add_parser("traverse", help="bounded blast-radius walk from one seed")
    traverse_cmd.add_argument("--db", required=True, type=Path)
    traverse_cmd.add_argument("--seed", required=True)
    traverse_cmd.add_argument("--scheme-digest", required=True)
    traverse_cmd.add_argument("--edge-kinds", required=True, help="comma separated admitted kinds")
    traverse_cmd.add_argument("--depth-limit", required=True, type=int)
    traverse_cmd.add_argument("--row-limit", required=True, type=int)

    receipt_cmd = sub.add_parser("receipt", help="verify readback, replay the export, emit a receipt")
    receipt_cmd.add_argument("--db", required=True, type=Path)
    receipt_cmd.add_argument("--out", type=Path)

    args = parser.parse_args(argv)
    if args.selftest:
        import selftest  # noqa: PLC0415 - the battery imports this module, so import it late

        return selftest.main()
    if args.command is None:
        parser.print_help()
        return 64

    try:
        if args.command == "ingest":
            fixture = _read_fixture(args.observations)
            if args.db.exists():
                conn = open_ledger(args.db)
            else:
                conn = create_ledger(args.db, fixture["subject"])
            counts = ingest(conn, fixture["observations"])
            print(json.dumps({"row_counts": counts, "database_sha256": file_digest(args.db)}, indent=2))
        elif args.command == "traverse":
            conn = open_ledger(args.db)
            result = traverse(
                conn,
                seed_provider_id=args.seed,
                seed_scheme_digest=args.scheme_digest,
                admitted_edge_kinds=args.edge_kinds.split(","),
                depth_limit=args.depth_limit,
                row_limit=args.row_limit,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            conn = open_ledger(args.db)
            result = emit_receipt(conn, args.db)
            text = json.dumps(result, indent=2, sort_keys=True)
            if args.out:
                Path(args.out).write_text(text + "\n", encoding="utf-8")
            print(text)
    except LedgerRefusal as exc:
        print(f"DTCR-SQLITE-LEDGER-REFUSED {exc}", file=sys.stderr)
        return 2
    except Unusable as exc:
        print(f"DTCR-SQLITE-LEDGER-UNUSABLE {exc}", file=sys.stderr)
        return 64
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
