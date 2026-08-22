#!/usr/bin/env python3
"""The DTCR semantic-context adapter: a rebuildable, non-authoritative store.

What this is and what it refuses to be
--------------------------------------
This adapter registers decision records, incident reviews, advisories, service
objectives, telemetry baselines and prior refactor outcomes so that a bounded
query can *suggest* which of them a reader might want, and it does that without
ever becoming a place a fact can be read from. Every emitted row carries the
exact source it came from, the ceiling it keeps for the rest of the task, and
constants saying what it did not establish. The whole store is disposable:
deleting it removes retrievable context and nothing else.

The KEYWORD lane needs no provider, and that is a schema fact
--------------------------------------------------------------
`retrieval-query.schema.json` closes `lane` over
`[KEYWORD, VECTOR, HYBRID, NOT_APPLICABLE]`, and `KEYWORD` is a first-class,
non-vector value. Nothing in the eight frozen M1 schemas requires an embedding
provider: `semantic-document.document_digest` is a plain sha256 content digest
and `retrieval-result.score_method` is free text with no metric enum behind it.
So the deterministic lane implemented here is the lane the contracts already
admit, not a synthetic vector lane wearing a keyword label. `open_port` is where
that distinction is enforced rather than described: asking this port for
`VECTOR` or `HYBRID` raises
`VECTOR_LANE_CLAIMED_WITHOUT_EMBEDDING_PROVIDER`, because a vector store with no
embedder cannot produce a projection and the frozen projection receipt has no
shape for one that was never computed.

Two things the vector lane is blocked on, and only one of them is the store
--------------------------------------------------------------------------
`probe_lancedb` tries a pinned separate interpreter and records what it found.
On a host where that interpreter has the embedded vector store, the probe
records `vector_store_import: PASS` with the exact version, the interpreter's
own content digest and the exit code behind it -- and the VECTOR retrieval lane
is *still* `BLOCKED_ON_PROVIDER`, because a vector store holds vectors somebody
else computed and no embedding provider is bound here. Collapsing those two into
one state is what turns an available store into a claimed lane; keeping them
apart is why the probe reports a passing import beside a blocked lane without
contradicting itself.

Four laws are carried structurally, because each has a failure that reads green:

*Non-authority.* The `authority`, `authority_ceiling` and `establishes`
constants come from the frozen schemas, and every artifact this module emits is
validated against them before it is returned. There is no path here that writes
a row and skips `enforce`.

*Back-reference completeness.* A document is registered only with a back
reference, and a row is emitted only with that reference carried onto it. The
projector recomputes the document digest, and for a `SOURCE_PACKET` reference
the packet sha256 and byte count as well, from the source bytes it actually
read, so a registration whose digest drifted from its own text is refused at
build time rather than returned as a plausible row later.

*Rebuild determinism.* `lifecycle_receipt` rebuilds the whole store from source
a second time and refuses `REBUILD_NON_DETERMINISTIC` unless the two index
digests are identical. The index is therefore reconstructible by anyone holding
the same input bytes, which is what makes deleting it cheap.

*Freshness before rank.* A superseded document is demoted below every
non-superseded one before ranks are assigned, and `assert_no_stale_override`
then checks the ordering that demotion was supposed to produce. Similarity has
no opinion about which document came last; this is where that opinion is
supplied.

Exit codes: 0 green, 2 a refusal fired, 64 unusable input, 70 jsonschema absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "DTCR-SEMANTIC-CONTEXT-UNUSABLE: jsonschema is required. This adapter "
        "validates every registration and every emitted artifact against the "
        "frozen DTCR schemas; skipping that would report the same green as "
        "running it.",
        file=sys.stderr,
    )
    raise SystemExit(70)

ADAPTER_DIR = Path(__file__).resolve().parent
SKILL_DIR = ADAPTER_DIR.parents[1]
SCHEMA_DIR = SKILL_DIR / "references" / "schemas"
FIXTURES = ADAPTER_DIR / "fixtures"
RECEIPTS = ADAPTER_DIR / "receipts"

ADAPTER_NAME = "dtcr-semantic-context"
ADAPTER_VERSION = "1.0.0"

# The lanes the frozen retrieval-query schema closes over, split by what each
# one physically needs on the host. The split is the whole point: three of the
# four are expressible here, and the fourth is refused rather than simulated.
LANES_WITHOUT_PROVIDER = ("KEYWORD", "NOT_APPLICABLE")
LANES_REQUIRING_EMBEDDING_PROVIDER = ("VECTOR", "HYBRID")

# The frozen retrieval-query schema caps top_k at 200. Repeating the bound here
# is deliberate: an unbounded neighbourhood is refused before the query runs,
# not after the schema rejects a result that was already computed.
MAX_TOP_K = 200


class Refusal(Exception):
    """An adapter law refused an operation. `reason` names the falsifier it kills."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


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


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    """The object name Git would give these bytes, derived here rather than shelled out.

    The frozen back reference carries a 40-hex blob for a `REPOSITORY_BLOB`
    citation, and a blob nobody recomputes is a citation that keeps resolving
    after the text under it moved. This is Git's own object rule -- the header
    `blob <byte count>\\0` in front of the content, SHA-1 over the whole thing --
    so the check needs no repository, no network and no subprocess.
    """
    header = f"blob {len(data)}".encode("ascii") + b"\x00"
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - Git's object name, not a security digest


# ---------------------------------------------------------------------------
# the projector: normalization and chunking
# ---------------------------------------------------------------------------

# The projection function, written down as data rather than only as code, so it
# has an identity a receipt can pin. A change to any value here changes
# NORMALIZER_DIGEST, which changes every index digest built under it, which is
# what refuses a query whose recorded index binding was produced by a different
# projector. Hashing the module file instead would churn the digest on every
# comment edit; hashing nothing at all is the MUTABLE_INDEX_OR_MODEL_IDENTITY
# failure this constant exists to make impossible.
NORMALIZER_SPEC: dict[str, Any] = {
    "normalizer": "dtcr/semantic-context-keyword-normalizer/v1",
    "casefold": True,
    "token_pattern": "[a-z0-9]+",
    "minimum_token_length": 3,
    "chunk_split": "blank-line-delimited paragraphs, in document order",
    # Every entry here has to be producible by `token_pattern` above, or it is a
    # stopword that can never fire: dead data inside the constant whose whole job
    # is to be an exact identity.
    "stopwords": [
        "and", "are", "but", "for", "not", "the", "was", "were", "with",
        "that", "this", "from", "has", "have", "its", "into", "than", "then",
        "they", "when", "which", "will", "would", "been", "over", "under",
    ],
}
NORMALIZER_DIGEST = digest_of(NORMALIZER_SPEC)

# The shape of the index itself, separate from its contents. The frozen query
# schema carries both digests because they answer different questions: whether
# the store holds these documents, and whether it is the same kind of store.
INDEX_SCHEMA: dict[str, Any] = {
    "index": "dtcr/semantic-context-inverted-index/v1",
    "posting": ["document_id", "chunk_index", "term_frequency"],
    "ordering": "postings sorted by token, then document_id, then chunk_index",
    "normalizer_digest": NORMALIZER_DIGEST,
    "scoring": "1000 * distinct matched query tokens + total term frequency",
}
INDEX_SCHEMA_DIGEST = digest_of(INDEX_SCHEMA)

SCORE_METHOD = (
    "deterministic keyword overlap over the DTCR semantic-context inverted index: "
    "1000 x distinct matched query tokens + total term frequency, ties broken by "
    "document id; no embedding, vector or similarity metric is involved"
)

_TOKEN = re.compile(NORMALIZER_SPEC["token_pattern"])
_STOPWORDS = frozenset(NORMALIZER_SPEC["stopwords"])

_UNPRODUCIBLE_STOPWORDS = sorted(
    word
    for word in _STOPWORDS
    if _TOKEN.fullmatch(word) is None or len(word) < NORMALIZER_SPEC["minimum_token_length"]
)
if _UNPRODUCIBLE_STOPWORDS:  # pragma: no cover - refused at import, before any build
    raise Refusal(
        "MUTABLE_INDEX_OR_MODEL_IDENTITY",
        f"the projector spec lists stopwords its own tokenizer can never produce "
        f"({_UNPRODUCIBLE_STOPWORDS}). They change NORMALIZER_DIGEST, and so every index "
        f"digest built under it, while changing nothing about what the projector does.",
    )

# Set to False by the selftest to plant STALE_ADR_OVERRIDES_NEWER_EXPLICIT_DECISION.
# In every other caller this is the demotion that makes the assertion below
# unreachable, which is exactly the relationship a planted defect has to prove.
DEMOTE_SUPERSEDED = True


def normalize(text: str) -> list[str]:
    """Text to tokens, by the recorded spec and nothing else."""
    lowered = text.casefold() if NORMALIZER_SPEC["casefold"] else text
    minimum = NORMALIZER_SPEC["minimum_token_length"]
    return [
        token
        for token in _TOKEN.findall(lowered)
        if len(token) >= minimum and token not in _STOPWORDS
    ]


def chunks_of(text: str) -> list[str]:
    """Blank-line paragraphs, in document order. Empty paragraphs are not chunks."""
    return [block.strip() for block in text.split("\n\n") if block.strip()]


# ---------------------------------------------------------------------------
# leak scan
# ---------------------------------------------------------------------------

# Every free-text field the frozen schemas admit carries the leak-scan
# obligation from references/contracts/public-private-capability.md, and the
# schemas say so themselves: their free text is explicitly *not* shape-protected.
# So the scan lives here, where the artifacts are built, rather than in a review
# somebody performs on the way out.
#
# A home-anchored path (`~/.local/...`) is deliberately admitted: it names a tool
# location without naming an account, and the provider receipt records the pinned
# interpreter in exactly that form. A rooted absolute path is not admitted,
# because that is where the account identity lives.
LEAK_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*://"), "a resolved URL"),
    (re.compile(r"(?:^|[\s\"'(\[])/[A-Za-z0-9._\-]+/"), "a machine-local absolute path"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "an address-shaped value"),
)


def scan_public(value: Any, where: str) -> None:
    """Refuse a private locator or address anywhere in a public artifact."""
    if isinstance(value, str):
        for pattern, what in LEAK_PATTERNS:
            if pattern.search(value):
                raise Refusal(
                    "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",
                    f"{where} carries {what} ({value!r}). A public artifact in this "
                    f"subtree registers private records by digest and reference, never "
                    f"by locator.",
                )
    elif isinstance(value, dict):
        for key, item in value.items():
            scan_public(item, f"{where}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            scan_public(item, f"{where}[{index}]")


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
    """Validate against a frozen schema, then leak-scan. Both, or neither."""
    errors = sorted(validator(name).iter_errors(instance), key=str)
    if errors:
        raise Refusal(
            "FROZEN_SCHEMA_REFUSED",
            f"{what} is refused by the frozen {name} schema: {errors[0].message}",
        )
    scan_public(instance, what)
    return instance


# ---------------------------------------------------------------------------
# the corpus
# ---------------------------------------------------------------------------

def load_corpus(path: Path) -> dict[str, Any]:
    """Read one registration fixture and check it is shaped like a corpus.

    The fixture holds synthetic public text beside each registration. That text
    is the *source*, not part of any emitted artifact: the frozen semantic
    document has no body, excerpt or locator key at all, so what this adapter
    publishes about a document is its digest and its back reference.
    """
    path = Path(path)
    if not path.is_file():
        raise Unusable(f"{path} is not a corpus fixture")
    try:
        corpus = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Unusable(f"{path} is not readable JSON: {exc}") from exc
    for key in ("corpus_id", "as_of", "records"):
        if key not in corpus:
            raise Unusable(f"{path} carries no {key!r}")
    if not corpus["records"]:
        raise Unusable(f"{path} registers no records; a store over nothing answers everything")
    return corpus


def corpus_digest_of(corpus: dict[str, Any]) -> str:
    """Identity of the input bytes a build consumed, in registration order.

    This is what `assert_current` recomputes. An index whose store still answers
    after its source moved is the stale-index failure, and it reads exactly like
    a fresh one.
    """
    return digest_of(
        [
            {
                "document_id": record["document"]["document_id"],
                "document_digest": record["document"]["document_digest"],
                "text_sha256": sha256_hex(record["text"].encode("utf-8")) if "text" in record else None,
            }
            for record in corpus["records"]
        ]
    )


# ---------------------------------------------------------------------------
# projection
# ---------------------------------------------------------------------------

def _verify_source_binding(record: dict[str, Any], text: str) -> None:
    """Recompute every declared digest from the bytes actually read.

    A registration is a claim about content. The claim is checked here, against
    the text this build projected, because a document digest that drifted from
    its own source produces rows that look exactly like correct ones.
    """
    document = record["document"]
    raw = text.encode("utf-8")
    observed = sha256_hex(raw)
    if observed != document["document_digest"]:
        raise Refusal(
            "WRONG_OR_STALE_SOURCE_DIGEST",
            f"{document['document_id']} registers digest {document['document_digest']} and its "
            f"own source text derives {observed}. A store keyed by a digest nobody recomputes "
            f"holds whatever it was told.",
        )
    blob = record["back_reference"].get("repository_blob")
    if blob is not None:
        expected = git_blob_sha1(raw)
        if blob["blob"] != expected:
            raise Refusal(
                "WRONG_OR_STALE_SOURCE_DIGEST",
                f"{document['document_id']} cites blob {blob['blob']} at {blob['path']} and the "
                f"source it was projected from is Git object {expected}. A blob citation that "
                f"still resolves after the text under it moved points a later reader at content "
                f"this row was never built from.",
            )
    packet = record["back_reference"].get("source_packet")
    if packet is None:
        return
    if packet["sha256"] != observed:
        raise Refusal(
            "WRONG_OR_STALE_SOURCE_DIGEST",
            f"{document['document_id']} cites packet {packet['packet_id']} at sha256 "
            f"{packet['sha256']}, and the source it was projected from derives {observed}.",
        )
    if packet["byte_count"] != len(raw):
        raise Refusal(
            "WRONG_OR_STALE_SOURCE_DIGEST",
            f"{document['document_id']} cites packet {packet['packet_id']} at "
            f"{packet['byte_count']} bytes and its source is {len(raw)} bytes.",
        )


def _verify_back_reference(back_reference: dict[str, Any], document_id: str) -> None:
    """A reference may cite source, ledger or packet. Never another stored row.

    The frozen schema closes the object, so a `vector_row_ref` key is already
    refused there. What the schema cannot see is a reference whose *payload*
    spells a retrieval identity into a field that admits free text, which is the
    same authority edge written one level down.
    """
    for field, value in (
        ("packet_id", back_reference.get("source_packet", {}).get("packet_id")),
        ("path", back_reference.get("repository_blob", {}).get("path")),
    ):
        if isinstance(value, str) and re.search(r"DTCR-(RR|RQ|CX)-[0-9]{3}", value):
            raise Refusal(
                "VECTOR_TO_VECTOR_AUTHORITY_EDGE",
                f"{document_id}'s back reference names {value!r} in {field}, which is a "
                f"retrieval identity. A chain of similarity hits citing each other is how a "
                f"store with no authority acquires one.",
            )


def project(corpus: dict[str, Any]) -> dict[str, Any]:
    """Registrations plus source text to documents, chunks and projection receipts.

    A record whose visibility is not `PUBLIC_TREE` carries no text in this public
    fixture and is therefore registered but not projected: it is retrievable only
    from the plane that holds it. That is the split written as a build outcome
    rather than as a redaction somebody remembers to perform.
    """
    documents: dict[str, dict[str, Any]] = {}
    back_references: dict[str, dict[str, Any]] = {}
    ceilings: dict[str, dict[str, Any]] = {}
    receipts: list[dict[str, Any]] = []
    postings: list[tuple[str, str, int, int]] = []
    unprojected: list[dict[str, str]] = []
    receipt_number = 0

    for index, record in enumerate(corpus["records"]):
        document = enforce("semantic-document", record["document"], f"records[{index}].document")
        back_reference = enforce(
            "source-back-reference", record["back_reference"], f"records[{index}].back_reference"
        )
        document_id = document["document_id"]
        if document_id in documents:
            raise Refusal(
                "MUTABLE_INDEX_OR_MODEL_IDENTITY",
                f"{document_id} is registered twice. One identity holding two contents is a "
                f"store whose answers depend on ingestion order.",
            )
        if back_reference["back_reference_id"] != document["back_reference_ref"]:
            raise Refusal(
                "ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE",
                f"{document_id} points at {document['back_reference_ref']} and the record carries "
                f"{back_reference['back_reference_id']}.",
            )
        _verify_back_reference(back_reference, document_id)

        ceiling = record.get("freshness_ceiling")
        if ceiling is None:
            raise Refusal(
                "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
                f"{document_id} is registered with no freshness ceiling. A document whose age "
                f"and supersession nobody wrote down is read as current by every later reader.",
            )
        ceiling = enforce(
            "semantic-freshness-ceiling", ceiling, f"records[{index}].freshness_ceiling"
        )
        if ceiling["document_ref"] != document_id:
            raise Refusal(
                "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
                f"{document_id} carries the ceiling {ceiling['ceiling_id']}, which is about "
                f"{ceiling['document_ref']}.",
            )
        for field in ("observed_at", "observed_revision"):
            if ceiling[field] != document[field]:
                raise Refusal(
                    "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
                    f"{document_id} was registered at {field}={document[field]!r} and its ceiling "
                    f"{ceiling['ceiling_id']} records {ceiling[field]!r}. Two ages for one "
                    f"document means the reader is told whichever one the row happened to carry.",
                )

        documents[document_id] = document
        back_references[back_reference["back_reference_id"]] = back_reference
        ceilings[document_id] = ceiling

        text = record.get("text")
        if document["visibility_class"] != "PUBLIC_TREE" or document["storage_plane"] != "PUBLIC_TREE":
            if text is not None:
                raise Refusal(
                    "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",
                    f"{document_id} is a {document['visibility_class']} record and this public "
                    f"fixture carries its text. A private record is registered by digest and "
                    f"reference from its own plane; copying its content here is the leak.",
                )
            unprojected.append(
                {"document_id": document_id, "state": "NOT_PROJECTED_PRIVATE_PLANE"}
            )
            continue
        if text is None:
            raise Refusal(
                "ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE",
                f"{document_id} declares the public tree as its plane and carries no source "
                f"text, so nothing here can be projected or recomputed for it.",
            )
        # The emitted artifacts are scanned by `enforce`, and the source text is
        # not one of them -- no schema here has a body key. But this text is
        # committed in the public tree beside the registration, so the same
        # obligation covers it, and the scan has to be spelled out here because
        # nothing downstream will ever look at it.
        scan_public(text, f"records[{index}].text")
        _verify_source_binding(record, text)

        for chunk_index, chunk in enumerate(chunks_of(text)):
            raw = chunk.encode("utf-8")
            tokens = normalize(chunk)
            frequency: dict[str, int] = {}
            for token in tokens:
                frequency[token] = frequency.get(token, 0) + 1
            for token in sorted(frequency):
                postings.append((token, document_id, chunk_index, frequency[token]))
            receipt_number += 1
            receipts.append(
                _projection_receipt(document, chunk_index, raw, receipt_number, len(frequency))
            )

    if not receipts:
        raise Refusal(
            "NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS",
            "no public record in this corpus projected to a single chunk, so an index built "
            "here would answer every query with an emptiness it never measured.",
        )
    return {
        "documents": documents,
        "back_references": back_references,
        "ceilings": ceilings,
        "projection_receipts": receipts,
        "postings": postings,
        "unprojected": unprojected,
    }


def _projection_receipt(
    document: dict[str, Any],
    chunk_index: int,
    raw: bytes,
    number: int,
    dimension: int,
) -> dict[str, Any]:
    """The frozen projection receipt for one deterministic keyword projection.

    The frozen shape is about an embedding provider, and this lane has none. The
    honest way to fill it is not to invent a model: `provider_name` is this
    adapter, `model_digest` is the real sha256 of the projector spec (so it is
    pinned rather than `NOT_PUBLISHED_BY_PROVIDER`), `dimension` is the number of
    distinct tokens this chunk actually projected to, and `transport.outcome` is
    `SKIPPED_BY_POLICY` with no exit code, because no provider call was made --
    the default suite is required to run with no network and no API key. A
    `PASS` here would be a transport claim about a call nobody placed.
    """
    receipt = {
        "schema": "dtcr/projection-receipt/v1",
        "projection_receipt_id": f"DTCR-PR-{number:03d}",
        "document_ref": document["document_id"],
        "input_document_digest": document["document_digest"],
        "chunk": {
            "chunk_index": chunk_index,
            "chunk_digest": sha256_hex(raw),
            "chunk_byte_count": len(raw),
        },
        "embedding_provider": {
            "provider_binding_id": "DTCR-PB-" + digest_of(
                {"name": ADAPTER_NAME, "version": ADAPTER_VERSION, "lane": "KEYWORD"}
            )[:16],
            "provider_name": ADAPTER_NAME,
            "model_id": NORMALIZER_SPEC["normalizer"],
            "model_digest": NORMALIZER_DIGEST,
            "dimension": max(dimension, 1),
            "config_digest": INDEX_SCHEMA_DIGEST,
        },
        "output_projection_digest": digest_of(
            {"normalizer_digest": NORMALIZER_DIGEST, "chunk_sha256": sha256_hex(raw)}
        ),
        "transport": {"outcome": "SKIPPED_BY_POLICY", "exit_code": None},
        "data_handling": {
            "content_plane": "PUBLIC_TREE",
            "provider_terms_admission": "HUMAN_ADMIT_REQUIRED",
        },
        "establishes": {
            "semantic_correctness": False,
            "retrieval_quality": False,
            "technical_authority": False,
        },
    }
    return enforce("projection-receipt", receipt, f"the projection receipt for {document['document_id']}")


def build_index(postings: Sequence[tuple[str, str, int, int]]) -> dict[str, Any]:
    """A plain inverted index. Ordered, so its digest is a function of content."""
    grouped: dict[str, list[list[Any]]] = {}
    for token, document_id, chunk_index, frequency in sorted(postings):
        grouped.setdefault(token, []).append([document_id, chunk_index, frequency])
    documents = sorted({posting[1] for posting in postings})
    return {
        **INDEX_SCHEMA,
        "postings": grouped,
        "document_count": len(documents),
        "chunk_count": len({(posting[1], posting[2]) for posting in postings}),
        "token_count": len(grouped),
    }


# ---------------------------------------------------------------------------
# the port
# ---------------------------------------------------------------------------

class KeywordReferenceBackend:
    """The deterministic, zero-network backend the frozen contracts already admit.

    It holds no authority and says so in every artifact it emits. It is
    rebuildable from its source bytes alone, which is the property that makes
    `DELETE` a storage operation rather than a decision.
    """

    def __init__(self, source: Path) -> None:
        self.source = Path(source)
        self.corpus = load_corpus(self.source)
        self.as_of = self.corpus["as_of"]
        projected = project(self.corpus)
        self.documents = projected["documents"]
        self.back_references = projected["back_references"]
        self.ceilings = projected["ceilings"]
        self.projection_receipts = projected["projection_receipts"]
        self.unprojected = projected["unprojected"]
        self.index = build_index(projected["postings"])
        self.index_digest = digest_of(self.index)
        self.corpus_digest = corpus_digest_of(self.corpus)
        # Nothing about a store is a task state. The value is carried so that a
        # lifecycle operation can be shown to have left it alone, not so that
        # anything here can move it.
        self.task_admission = "UNCHANGED"

    # -- rebuild -----------------------------------------------------------

    def rebuild(self) -> "KeywordReferenceBackend":
        """Read the same source again and build again. Same bytes, same digest."""
        return KeywordReferenceBackend(self.source)

    def assert_current(self) -> None:
        """Refuse to answer over an index whose source has moved underneath it."""
        observed = corpus_digest_of(load_corpus(self.source))
        if observed != self.corpus_digest:
            raise Refusal(
                "WRONG_OR_STALE_SOURCE_DIGEST",
                f"this index was built over corpus digest {self.corpus_digest} and its source "
                f"now derives {observed}. A stale index answers with the same confidence as a "
                f"fresh one, which is why it is refused here rather than reported beside the rows.",
            )
        recomputed = digest_of(build_index(_postings_of(self.index)))
        if recomputed != self.index_digest:
            raise Refusal(
                "MUTABLE_INDEX_OR_MODEL_IDENTITY",
                f"this index reports digest {self.index_digest} and its own contents derive "
                f"{recomputed}.",
            )
        if self.index["normalizer_digest"] != NORMALIZER_DIGEST:
            raise Refusal(
                "MUTABLE_INDEX_OR_MODEL_IDENTITY",
                f"this index was built by projector {self.index['normalizer_digest']} and the "
                f"projector now loaded is {NORMALIZER_DIGEST}. An index identity that survives a "
                f"change to what produced it is not an identity.",
            )

    # -- retrieval ---------------------------------------------------------

    def _matches(self, tokens: Sequence[str], filters: Sequence[dict[str, str]]) -> list[tuple[int, str]]:
        """Score every admitted document against the query tokens, high first.

        Two numbers per document, in the order the recorded scoring says: how
        many *distinct* query tokens it matched at all, and the total term
        frequency behind those matches. Distinct-first is what stops a document
        that repeats one query word in ten chunks from outranking a document that
        matched every word once, and counting the distinct half per token rather
        than per posting is why the same token appearing in two chunks of one
        document adds frequency and not breadth.
        """
        admitted = {
            document_id
            for document_id, document in self.documents.items()
            if _passes_filters(document, filters)
        }
        matched: dict[str, int] = {}
        total: dict[str, int] = {}
        for token in dict.fromkeys(tokens):
            hit_this_token: set[str] = set()
            for document_id, _chunk_index, frequency in self.index["postings"].get(token, []):
                if document_id not in admitted:
                    continue
                hit_this_token.add(document_id)
                total[document_id] = total.get(document_id, 0) + frequency
            for document_id in hit_this_token:
                matched[document_id] = matched.get(document_id, 0) + 1
        return sorted(
            (
                (1000 * matched[document_id] + total[document_id], document_id)
                for document_id in matched
            ),
            key=lambda pair: (-pair[0], pair[1]),
        )

    def retrieve(
        self,
        *,
        lane: str,
        query_text: str,
        top_k: int | str,
        filters: Sequence[dict[str, str]] = (),
        query_id: str = "DTCR-RQ-001",
        result_id: str = "DTCR-RR-001",
        not_applicable_rationale: str | None = None,
    ) -> dict[str, Any]:
        """One bounded query, recorded before its rows are read.

        Returns the two frozen artifacts unmodified, plus a binding block holding
        what the frozen shapes have no room for: the denominators, which rows
        were never revalidated, and which documents this public build could not
        project at all.
        """
        if lane in LANES_REQUIRING_EMBEDDING_PROVIDER:
            raise Refusal(
                "VECTOR_LANE_CLAIMED_WITHOUT_EMBEDDING_PROVIDER",
                f"the {lane} lane needs an embedding provider to project a query into the same "
                f"space as the stored rows, and this port binds none. Answering it from the "
                f"keyword index would return keyword rows under a vector label, which is the "
                f"synthetic lane the frozen retrieval contracts refuse.",
            )
        if lane not in LANES_WITHOUT_PROVIDER:
            raise Refusal(
                "NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS",
                f"{lane!r} is not one of the lanes the frozen retrieval-query schema closes over.",
            )
        self.assert_current()

        query = {
            "schema": "dtcr/retrieval-query/v1",
            "query_id": query_id,
            "lane": lane,
            "query_digest": sha256_hex(query_text.encode("utf-8")),
            "top_k": top_k,
            "filters": list(filters),
            "index_binding": {
                "index_digest": self.index_digest,
                "index_schema_digest": INDEX_SCHEMA_DIGEST,
                "projection_receipt_refs": [
                    receipt["projection_receipt_id"] for receipt in self.projection_receipts
                ],
            },
            "establishes": {"decision": False, "technical_authority": False, "task_pass": False},
        }
        if lane == "NOT_APPLICABLE":
            if not not_applicable_rationale:
                raise Refusal(
                    "NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS",
                    "a lane recorded as not applicable with no reason beside it reads as an "
                    "empty result rather than as a lane nobody entered.",
                )
            if top_k != "NOT_APPLICABLE":
                # Coercing it here would be the quieter version of the same
                # failure: a caller who asked for k rows on a lane nobody entered
                # gets a clean record saying the lane was skipped.
                raise Refusal(
                    "NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS",
                    f"the NOT_APPLICABLE lane was asked for top_k={top_k!r}. A lane carrying a "
                    f"result size is a lane somebody intends to run anyway.",
                )
            query["not_applicable_rationale"] = not_applicable_rationale
            enforce("retrieval-query", query, "the emitted query")
            result = enforce(
                "retrieval-result",
                {
                    "schema": "dtcr/retrieval-result/v1",
                    "result_id": result_id,
                    "query_ref": query_id,
                    "outcome": "NOT_APPLICABLE",
                    "not_applicable_rationale": not_applicable_rationale,
                    "rows": [],
                    "establishes": {"deterministic_fact": False, "decision": False, "task_pass": False},
                },
                "the emitted result",
            )
            return {
                "retrieval_query": query,
                "retrieval_result": result,
                "retrieval_binding": _binding(self, 0, 0, [], []),
            }

        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise Refusal(
                "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
                f"top_k={top_k!r} is not a positive integer. There is no value here spelling "
                f"unbounded: an unbounded neighbourhood is not a query, it is the store.",
            )
        if top_k > MAX_TOP_K:
            raise Refusal(
                "TOP_K_RESULT_PROMOTED_TO_VIOLATION_BASIS",
                f"top_k={top_k} exceeds the frozen ceiling of {MAX_TOP_K}.",
            )
        enforce("retrieval-query", query, "the emitted query")

        tokens = normalize(query_text)
        ranked = self._matches(tokens, filters)
        ordered = _order_by_freshness(ranked, self.ceilings) if DEMOTE_SUPERSEDED else ranked
        selected = ordered[:top_k]

        rows: list[dict[str, Any]] = []
        for rank, (score, document_id) in enumerate(selected, start=1):
            rows.append(self._row(rank, score, document_id))
        assert_no_stale_override(rows, self.documents, self.ceilings)

        result = {
            "schema": "dtcr/retrieval-result/v1",
            "result_id": result_id,
            "query_ref": query_id,
            "outcome": "ROWS_RETURNED" if rows else "EMPTY",
            "rows": rows,
            "establishes": {"deterministic_fact": False, "decision": False, "task_pass": False},
        }
        enforce("retrieval-result", result, "the emitted result")
        never = [
            row["rank"]
            for row in rows
            if self.ceilings[row["document_ref"]]["revalidated_at"] == "NEVER_REVALIDATED"
        ]
        historical = [
            row["rank"]
            for row in rows
            if self.ceilings[row["document_ref"]]["usable_as"] == "HISTORICAL_CONTEXT_ONLY"
        ]
        return {
            "retrieval_query": query,
            "retrieval_result": result,
            "retrieval_binding": _binding(self, len(ranked), len(rows), never, historical),
        }

    def _row(self, rank: int, score: int, document_id: str) -> dict[str, Any]:
        """One returned row, with the exact source it came from carried onto it."""
        document = self.documents[document_id]
        back_reference_ref = document.get("back_reference_ref")
        if not back_reference_ref or back_reference_ref not in self.back_references:
            raise Refusal(
                "ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE",
                f"{document_id} would be returned at rank {rank} with no resolvable back "
                f"reference. Retrieval returns it, a reader reads it, and nothing says where "
                f"it came from.",
            )
        ceiling = self.ceilings.get(document_id)
        if ceiling is None:
            raise Refusal(
                "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
                f"{document_id} would be returned at rank {rank} with no freshness ceiling.",
            )
        return {
            "rank": rank,
            "row_class": "SEMANTIC_ROW",
            "authority": "NON_AUTHORITATIVE_CANDIDATE",
            "document_ref": document_id,
            "back_reference_ref": back_reference_ref,
            "freshness_ref": ceiling["ceiling_id"],
            "score": score,
            "score_method": SCORE_METHOD,
        }

    # -- consumption -------------------------------------------------------

    def consume(
        self,
        result: dict[str, Any],
        *,
        ranks: Iterable[int],
        manifest_ref: str,
        consuming_task_ref: str,
        first_id: int = 1,
    ) -> list[dict[str, Any]]:
        """Record which returned rows were actually read while doing a task."""
        by_rank = {row["rank"]: row for row in result["rows"]}
        manifest: list[dict[str, Any]] = []
        for offset, rank in enumerate(sorted(dict.fromkeys(ranks))):
            row = by_rank.get(rank)
            if row is None:
                raise Refusal(
                    "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
                    f"rank {rank} is listed as consumed and {result['result_id']} never returned "
                    f"it. A manifest that names rows the query did not produce is not an audit "
                    f"of what was read.",
                )
            manifest.append(
                enforce(
                    "consumed-context-row",
                    {
                        "schema": "dtcr/consumed-context-row/v1",
                        "consumed_row_id": f"DTCR-CX-{first_id + offset:03d}",
                        "manifest_ref": manifest_ref,
                        "result_ref": result["result_id"],
                        "row_rank": rank,
                        "document_ref": row["document_ref"],
                        "back_reference_ref": row["back_reference_ref"],
                        "freshness_ref": row["freshness_ref"],
                        "basis_grade": "SEMANTIC_CONTEXT_CANDIDATE",
                        "influence": "CONTEXT_ONLY",
                        "consuming_task_ref": consuming_task_ref,
                        "consumed_at": self.as_of,
                    },
                    f"the consumed row for rank {rank}",
                )
            )
        return manifest

    # -- lifecycle ---------------------------------------------------------

    def _assert_admission_unchanged(self, operation: str, when: str) -> None:
        if self.task_admission != "UNCHANGED":
            raise Refusal(
                "REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION",
                f"the task admission reads {self.task_admission!r} {when} a {operation}. "
                f"Removing or rebuilding a store removes or rebuilds retrievable context and "
                f"nothing else; a store operation that moved an admission is an authority this "
                f"plane never had.",
            )

    def lifecycle_receipt(
        self,
        *,
        operation: str,
        receipt_id: str = "DTCR-LC-001",
        index_digest_before: str = "NO_PRIOR_INDEX",
    ) -> dict[str, Any]:
        """Rebuild or delete, and record what that did not change.

        A `REBUILD` is verified rather than asserted: the whole store is built a
        second time from the same source, and a receipt is refused unless the two
        index digests are identical. An index nobody can reproduce is not
        disposable, whatever the receipt says about it.
        """
        if operation not in ("REBUILD", "DELETE", "COMPACT"):
            raise Refusal("REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION", f"{operation!r} is not a lifecycle operation")
        # Checked against the literal, not only against the reading taken a line
        # earlier: a before/after comparison is satisfied by an admission that was
        # already moved before the operation started, which is the same failure
        # arriving through a caller instead of through this method.
        self._assert_admission_unchanged(operation, "before")
        rebuilt = self.rebuild()
        if rebuilt.index_digest != self.index_digest:
            raise Refusal(
                "REBUILD_NON_DETERMINISTIC",
                f"rebuilding from the same source produced index digest {rebuilt.index_digest} "
                f"against {self.index_digest}. An index that cannot be re-derived from its input "
                f"bytes is a store nobody can reconstruct or safely delete.",
            )
        if rebuilt.corpus_digest != self.corpus_digest:
            raise Refusal(
                "REBUILD_NON_DETERMINISTIC",
                f"the rebuild read corpus digest {rebuilt.corpus_digest} against "
                f"{self.corpus_digest}.",
            )
        after = "INDEX_ABSENT_AFTER_DELETE" if operation == "DELETE" else rebuilt.index_digest
        receipt = enforce(
            "semantic-index-lifecycle-receipt",
            {
                "schema": "dtcr/semantic-index-lifecycle-receipt/v1",
                "lifecycle_receipt_id": receipt_id,
                "operation": operation,
                "performed_at": self.as_of,
                "index_digest_before": index_digest_before,
                "index_digest_after": after,
                "projection_receipt_refs": [
                    receipt["projection_receipt_id"] for receipt in rebuilt.projection_receipts
                ],
                "changes": {
                    "task_admission": "UNCHANGED",
                    "technical_evidence": "NO_NEW_EVIDENCE",
                    "closure_state": "UNCHANGED",
                },
            },
            "the emitted lifecycle receipt",
        )
        self._assert_admission_unchanged(operation, "after")
        return {
            "semantic_index_lifecycle_receipt": receipt,
            "lifecycle_binding": {
                "source_basename": self.source.name,
                "corpus_digest": self.corpus_digest,
                "index_digest": self.index_digest,
                "rebuilt_index_digest": rebuilt.index_digest,
                "normalizer_digest": NORMALIZER_DIGEST,
                "index_schema_digest": INDEX_SCHEMA_DIGEST,
                "document_count": self.index["document_count"],
                "chunk_count": self.index["chunk_count"],
                "token_count": self.index["token_count"],
                "projection_receipt_count": len(self.projection_receipts),
                "unprojected": self.unprojected,
                "authority_ceiling": {
                    "current_policy": False,
                    "deterministic_fact": False,
                    "reproduced_failure": False,
                    "task_pass": False,
                    "merge": False,
                },
                "omissions": [
                    "documents on a private or consumer-local plane are registered here by digest "
                    "and reference; their content was never read, so nothing in these counts "
                    "covers them",
                    "the rebuild digest is over this adapter's own projection of the same source "
                    "bytes; it says nothing about whether the source is current in its own plane",
                ],
            },
        }


def _postings_of(index: dict[str, Any]) -> list[tuple[str, str, int, int]]:
    return [
        (token, document_id, chunk_index, frequency)
        for token, entries in index["postings"].items()
        for document_id, chunk_index, frequency in entries
    ]


def _passes_filters(document: dict[str, Any], filters: Sequence[dict[str, str]]) -> bool:
    """Metadata filters over the closed registration vocabulary only."""
    for entry in filters:
        field, value = entry["field"], entry["value"]
        if field == "subsystem_tag":
            if value not in document["subsystem_tags"]:
                return False
        elif field == "observed_after":
            if document["observed_at"] < value:
                return False
        elif document.get(field) != value:
            return False
    return True


def _order_by_freshness(
    ranked: Sequence[tuple[int, str]], ceilings: dict[str, dict[str, Any]]
) -> list[tuple[int, str]]:
    """Superseded documents rank below every document that is not superseded.

    Not a tie-break and not a score adjustment: a superseded record is bound to
    HISTORICAL_CONTEXT_ONLY by its own ceiling, and a store that lets it outrank
    the decision that replaced it has quietly reinstated it.
    """
    return sorted(
        ranked,
        key=lambda pair: (
            1 if ceilings[pair[1]]["usable_as"] == "HISTORICAL_CONTEXT_ONLY" else 0,
            -pair[0],
            pair[1],
        ),
    )


def assert_no_stale_override(
    rows: Sequence[dict[str, Any]],
    documents: dict[str, dict[str, Any]],
    ceilings: dict[str, dict[str, Any]],
) -> None:
    """A superseded row may never outrank the decision that superseded it."""
    rank_by_decision = {
        documents[row["document_ref"]]["owning_decision"]: row["rank"] for row in rows
    }
    for row in rows:
        supersession = ceilings[row["document_ref"]]["supersession"]
        if not isinstance(supersession, dict):
            continue
        newer = rank_by_decision.get(supersession["superseding_decision_ref"])
        if newer is not None and newer > row["rank"]:
            raise Refusal(
                "STALE_ADR_OVERRIDES_NEWER_EXPLICIT_DECISION",
                f"{row['document_ref']} was superseded by "
                f"{supersession['superseding_decision_ref']!r} on "
                f"{supersession['superseded_at']}, and it is returned at rank {row['rank']} "
                f"above the newer decision at rank {newer}. Similarity has no opinion about "
                f"which of two documents came last.",
            )


def _binding(
    backend: "KeywordReferenceBackend",
    candidates: int,
    returned: int,
    never_revalidated_ranks: Sequence[int],
    historical_ranks: Sequence[int],
) -> dict[str, Any]:
    """What the frozen result has no room for, stated beside it rather than inside."""
    return {
        "lane_requires_provider": False,
        "corpus_digest": backend.corpus_digest,
        "index_digest": backend.index_digest,
        "index_schema_digest": INDEX_SCHEMA_DIGEST,
        "normalizer_digest": NORMALIZER_DIGEST,
        "registered_documents": len(backend.documents),
        "projected_documents": backend.index["document_count"],
        "candidate_denominator": candidates,
        "returned_denominator": returned,
        "never_revalidated_ranks": list(never_revalidated_ranks),
        "historical_context_only_ranks": list(historical_ranks),
        "unprojected": backend.unprojected,
        "authority_ceiling": {
            "current_policy": False,
            "deterministic_fact": False,
            "reproduced_failure": False,
            "decision": False,
            "task_pass": False,
            "merge": False,
        },
        "omissions": [
            "rows are ranked by keyword overlap; a document nobody phrased the way this query "
            "phrases it is absent from the candidate denominator and from every count here",
            "the manifest of consumed rows cannot prove its own completeness; reconcile_consumed "
            "checks the returned set against it, and nothing checks what a reader read outside it",
        ],
    }


def reconcile_consumed(result: dict[str, Any], manifest: Sequence[dict[str, Any]]) -> dict[str, int]:
    """Every returned row must appear in the manifest, or the manifest is not one.

    The frozen consumed-context-row schema says plainly that it cannot enforce
    its own completeness, and names the reconciliation as a consumer check. This
    is that check: the expensive failure in a retrieval lane is not a bad row, it
    is a row that influenced the work and appears in no list.
    """
    returned = {row["rank"] for row in result["rows"]}
    listed = {row["row_rank"] for row in manifest}
    missing = sorted(returned - listed)
    if missing:
        raise Refusal(
            "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
            f"{result['result_id']} returned ranks {sorted(returned)} and the manifest lists "
            f"{sorted(listed)}; {missing} were read by whoever held the result and appear in no "
            f"list a later reader could audit.",
        )
    for row in manifest:
        if row["result_ref"] != result["result_id"]:
            raise Refusal(
                "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
                f"a manifest entry cites {row['result_ref']} and this result is "
                f"{result['result_id']}.",
            )
    return {"returned": len(returned), "listed": len(listed)}


def open_port(
    *,
    lane: str,
    source: Path,
    embedding_provider: dict[str, Any] | None = None,
) -> KeywordReferenceBackend:
    """The SemanticContextPort: one lane in, one backend or one refusal out.

    There is exactly one backend behind this port, and that is the honest state
    of the tree rather than a gap: the LanceDB adapter the parent issue names is
    optional, needs an embedding provider to have anything to store, and is
    represented here by the refusal below rather than by a class that would
    answer keyword rows under a vector name.
    """
    if lane in LANES_REQUIRING_EMBEDDING_PROVIDER:
        if embedding_provider is None:
            raise Refusal(
                "VECTOR_LANE_CLAIMED_WITHOUT_EMBEDDING_PROVIDER",
                f"the {lane} lane was requested with no embedding provider bound. A vector store "
                f"holds vectors somebody else computed; with no embedder there is nothing to "
                f"store, and a lane that answers anyway is answering from somewhere it did not "
                f"say.",
            )
        raise Refusal(
            "EMBEDDING_TRANSPORT_PASS_PROMOTED_TO_SEMANTIC_PASS",
            f"an embedding provider binding was supplied for the {lane} lane, and its terms, "
            f"model rights and privacy plane are HUMAN_ADMIT_REQUIRED by the frozen projection "
            f"receipt. No binding presented to this port converts into that admission.",
        )
    if lane not in LANES_WITHOUT_PROVIDER:
        raise Refusal(
            "NOT_APPLICABLE_FORCED_TO_SYNTHETIC_PASS",
            f"{lane!r} is not one of {list(LANES_WITHOUT_PROVIDER + LANES_REQUIRING_EMBEDDING_PROVIDER)}.",
        )
    return KeywordReferenceBackend(source)


# ---------------------------------------------------------------------------
# the optional vector-store provider probe
# ---------------------------------------------------------------------------

# Pinned separate interpreters, in the order they are tried. This is the
# convention already admitted and receipted at
# `skills/repo-agent-native/references/TOOL_ROUTING.md` (`--lancedb-python`):
# the provider is never installed into the shared or CI environment, so a probe
# that checks only the default `python3` records an available provider as an
# absent one.
LANCEDB_INTERPRETER_CANDIDATES = (
    "~/.local/state/skills-shared-runs/recapture-venv/bin/python",
)
PROBE_SOURCE = "import lancedb; print(lancedb.__version__)"


def fold_home(path: str) -> str:
    """`/…/home/x/y` to `~/y`. A tool location, with no account identity in it."""
    home = str(Path.home())
    return "~" + path[len(home):] if path.startswith(home) else path


def probe_lancedb(interpreter: str | None = None) -> dict[str, Any]:
    """Try to import the vector store through a pinned interpreter, and record it.

    This starts a local process and opens no socket. What it can establish is
    that a vector *store* is importable at an exact version; what it cannot
    establish, and does not claim, is a VECTOR retrieval lane -- that needs an
    embedding provider, which is a separate transport, model, privacy and terms
    plane whose admission the frozen projection receipt fixes at
    HUMAN_ADMIT_REQUIRED.
    """
    candidates = [interpreter] if interpreter else []
    candidates.append(os.environ.get("DTCR_LANCEDB_PYTHON") or "")
    candidates.extend(LANCEDB_INTERPRETER_CANDIDATES)
    attempts: list[dict[str, Any]] = []
    for candidate in [entry for entry in candidates if entry]:
        resolved = Path(candidate).expanduser()
        folded = fold_home(str(resolved))
        if not resolved.is_file():
            attempts.append({"interpreter": folded, "state": "ABSENT", "exit_code": None})
            continue
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, local import only
            [str(resolved), "-c", PROBE_SOURCE],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        attempts.append(
            {
                "interpreter": folded,
                "state": "PASS" if completed.returncode == 0 else "FAIL",
                "exit_code": completed.returncode,
                "stdout": completed.stdout.strip()[:120],
                "stdout_sha256": sha256_hex(completed.stdout.encode("utf-8")),
                "stderr_bytes": len(completed.stderr.encode("utf-8")),
                "executable_sha256": sha256_hex(resolved.resolve().read_bytes()),
            }
        )
        if completed.returncode == 0:
            break
    passing = next((attempt for attempt in attempts if attempt["state"] == "PASS"), None)
    receipt = {
        "receipt": "dtcr/semantic-context-provider-probe/v1",
        "adapter": {"name": ADAPTER_NAME, "version": ADAPTER_VERSION},
        "probe": {"argv_tail": ["-c", PROBE_SOURCE], "network": "NONE", "timeout_seconds": 120},
        "attempts": attempts,
        "lanes": {
            "keyword_reference_backend": {
                "state": "PASS",
                "why": "the frozen retrieval-query lane enum admits KEYWORD, and no schema in the "
                "M1 set requires an embedding provider; this lane is exercised by selftest.py "
                "on every run with no provider on the host",
            },
            "vector_store_import": {
                "state": passing["state"] if passing else "ABSENT",
                "why": "an importable embedded vector store is a transport fact about one pinned "
                "interpreter on one host; it is not a retrieval lane",
            },
            "embedding_provider": {
                "state": "BLOCKED_ON_PROVIDER",
                "why": "a vector store holds vectors somebody else computed. No embedding "
                "provider is bound on this runtime, so there is nothing to store and no query "
                "to project",
            },
            "vector_retrieval_lane": {
                "state": "BLOCKED_ON_PROVIDER",
                "why": "blocked on the embedding provider above, not on the store: open_port "
                "refuses VECTOR and HYBRID with "
                "VECTOR_LANE_CLAIMED_WITHOUT_EMBEDDING_PROVIDER rather than answering them "
                "from the keyword index",
            },
            "provider_terms_model_rights_and_privacy": {
                "state": "HUMAN_ADMIT_REQUIRED",
                "why": "fixed by projection-receipt.schema.json's provider_terms_admission "
                "constant; no volume of successful calls converts into it",
            },
        },
        "establishes": {
            "semantic_correctness": False,
            "retrieval_quality": False,
            "technical_authority": False,
            "vector_lane_available": False,
            "task_pass": False,
        },
        "omissions": [
            "the interpreter is recorded home-relative and by content digest; this receipt is "
            "evidence for that one interpreter on that one host and transfers to no other",
            "library licence and NOTICE state were not read by this probe and remain "
            "HUMAN_ADMIT_REQUIRED",
        ],
    }
    scan_public(receipt, "the provider probe receipt")
    return receipt


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--selftest", action="store_true", help="run the adapter's own battery")
    sub = parser.add_subparsers(dest="command")

    default_corpus = FIXTURES / "public-corpus.json"

    build_cmd = sub.add_parser("build", help="project a corpus and report the index identity")
    build_cmd.add_argument("--corpus", type=Path, default=default_corpus)

    query_cmd = sub.add_parser("query", help="one bounded query over a built index")
    query_cmd.add_argument("--corpus", type=Path, default=default_corpus)
    query_cmd.add_argument("--lane", default="KEYWORD")
    query_cmd.add_argument("--text", required=True)
    query_cmd.add_argument("--top-k", type=int, default=5)
    query_cmd.add_argument(
        "--rationale",
        default=None,
        help="required for --lane NOT_APPLICABLE: why stored context could not help this task",
    )

    lifecycle_cmd = sub.add_parser("lifecycle", help="rebuild or delete, and receipt what did not change")
    lifecycle_cmd.add_argument("--corpus", type=Path, default=default_corpus)
    lifecycle_cmd.add_argument("--operation", default="REBUILD", choices=("REBUILD", "DELETE", "COMPACT"))

    probe_cmd = sub.add_parser("probe-provider", help="try the pinned vector-store interpreter")
    probe_cmd.add_argument("--lancedb-python", dest="lancedb_python", default=None)
    probe_cmd.add_argument("--out", type=Path)

    args = parser.parse_args(argv)
    if args.selftest:
        import selftest  # noqa: PLC0415 - the battery imports this module, so import it late

        return selftest.main()
    if args.command is None:
        parser.print_help()
        return 64

    try:
        if args.command == "build":
            backend = open_port(lane="KEYWORD", source=args.corpus)
            print(
                json.dumps(
                    {
                        "corpus_digest": backend.corpus_digest,
                        "index_digest": backend.index_digest,
                        "index_schema_digest": INDEX_SCHEMA_DIGEST,
                        "normalizer_digest": NORMALIZER_DIGEST,
                        "registered_documents": len(backend.documents),
                        "projected_documents": backend.index["document_count"],
                        "chunks": backend.index["chunk_count"],
                        "tokens": backend.index["token_count"],
                        "projection_receipts": len(backend.projection_receipts),
                        "unprojected": backend.unprojected,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        elif args.command == "query":
            backend = open_port(lane=args.lane, source=args.corpus)
            print(
                json.dumps(
                    backend.retrieve(
                        lane=args.lane,
                        query_text=args.text,
                        top_k="NOT_APPLICABLE" if args.lane == "NOT_APPLICABLE" else args.top_k,
                        not_applicable_rationale=args.rationale,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
        elif args.command == "lifecycle":
            backend = open_port(lane="KEYWORD", source=args.corpus)
            print(
                json.dumps(
                    backend.lifecycle_receipt(operation=args.operation),
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            receipt = probe_lancedb(args.lancedb_python)
            text = json.dumps(receipt, indent=2, sort_keys=True)
            if args.out:
                Path(args.out).write_text(text + "\n", encoding="utf-8")
            print(text)
    except Refusal as exc:
        print(f"DTCR-SEMANTIC-CONTEXT-REFUSED {exc}", file=sys.stderr)
        return 2
    except Unusable as exc:
        print(f"DTCR-SEMANTIC-CONTEXT-UNUSABLE {exc}", file=sys.stderr)
        return 64
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
