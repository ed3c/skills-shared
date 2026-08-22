#!/usr/bin/env python3
"""The DTCR semantic-context adapter: a rebuildable, non-authoritative store.

What this plane is and what it refuses to be
--------------------------------------------
It holds decision records, incident reviews, advisories, service objectives,
telemetry baselines and prior refactor outcomes *by reference*, so that a task
can be handed text somebody once wrote about the subsystem it is touching. That
is the whole of its authority. It does not hold facts, it does not hold task
state, and nothing retrieved from it moves either: every artifact it emits is
validated against the frozen DTCR schemas, and those schemas pin the ceilings as
constants rather than as advice.

Five laws are carried structurally here, because each one has a failure that
reads as green:

*Registration is by digest and back reference, never by locator.* A document
enters the store as an identity (`document_digest`) plus the exact thing it came
from (`DTCR-BK-...`). `register` refuses a document whose back reference is not
registered, and refuses a public document whose bytes do not hash to its own
recorded digest. A private-carrier record is registrable -- its digest and its
back reference are not private content -- but its text is not present in this
tree, so `project` refuses to project it here and the run receipt records that
absence as a typed state rather than as an empty success.

*The index is derived, and its identity is derived with it.* `index_digest` is
the digest of the projected rows and `index_schema_digest` is the digest of the
projection algorithm and its dimension. A query carries both, and `query`
recomputes both before it reads a row: an index or a model that moved under a
stable name is refused rather than queried.

*Ranking is not ordering-by-authority.* Rows are ordered by score, and then
`enforce_supersession_order` moves a superseded document below the document that
superseded it whenever both are in the same result. `assert_supersession_order`
re-checks the emitted order, so removing the enforcement does not produce a
quietly wrong ranking, it produces a red run.

*A consumed row is a listed row.* `consume` builds the manifest for exactly the
ranks that were read, and `reconcile_manifest` compares the manifest against
those ranks in both directions. The frozen consumed-context-row schema says in
its own description that it cannot enforce manifest completeness; this is the
consumer check it names.

*Lifecycle operations are observational.* `lifecycle` digests the task-admission
mapping before and after the operation and refuses any operation that moved it.
The port also only ever holds a read-only view of that mapping, so the refusal
is the second arrival rather than the only one.

Backends
--------
`ReferenceBackend` is the deterministic, zero-network, in-memory backend. It
needs no API key, no embedding service and no network, and its projection is a
hashed-token vector whose algorithm string is part of the pinned model identity.
It is not a good retriever and does not claim to be; it exists so the adapter's
laws can be proven without a provider.

`LanceDBBackend` is the optional provider lane. It binds the exact installed
capability if one is observed and otherwise raises `ProviderUnavailable`. It
does not implement retrieval: no run has ever exercised a LanceDB store through
this port, so writing one here would add a state that only a test could
construct. The lane's committed receipt says `NOT_EXERCISED`, and that is the
honest word for it.

Exit codes: 0 green, 2 a refusal fired, 64 unusable input, 70 jsonschema absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "DTCR-SEMANTIC-CONTEXT-UNUSABLE: jsonschema is required. This adapter "
        "validates every registration, query, result, manifest entry and "
        "receipt against the frozen DTCR schemas; skipping that would report "
        "the same green as running it.",
        file=sys.stderr,
    )
    raise SystemExit(70)

ADAPTER_DIR = Path(__file__).resolve().parent
SKILL_DIR = ADAPTER_DIR.parents[1]
SCHEMA_DIR = SKILL_DIR / "references" / "schemas"
FIXTURE = ADAPTER_DIR / "fixtures" / "public-context-store.json"
RECEIPTS = ADAPTER_DIR / "receipts"
REPO_ROOT = SKILL_DIR.parents[1]

ADAPTER_NAME = "dtcr-semantic-context"
ADAPTER_VERSION = "1.0.0"

# The eight frozen schemas this adapter consumes. Nothing here defines a second
# source or fact identity: identity is the digest plus the back reference the
# frozen schemas already carry.
CONSUMED_SCHEMAS = (
    "semantic-document",
    "source-back-reference",
    "projection-receipt",
    "retrieval-query",
    "retrieval-result",
    "consumed-context-row",
    "semantic-freshness-ceiling",
    "semantic-index-lifecycle-receipt",
)

# The projection algorithm *is* the model identity here. The digest below is
# taken over this string and the dimension, so an edit to either produces a
# different model identity and a different index schema digest, which is what
# stops an index from moving under a stable name.
PROJECTION_ALGORITHM = (
    "dtcr-reference-token-hash-v1: lowercase ascii word tokens of the chunk, each token "
    "hashed with sha256 and folded into DIMENSION buckets by the first four bytes of its "
    "digest, one count per occurrence, L2-normalised, components rounded to 9 decimals"
)
DIMENSION = 64
MODEL_ID = "dtcr-reference-token-hash-v1"
PROVIDER_BINDING_ID = "DTCR-PB-6ad2f1c40be95837"
TOKEN = re.compile(r"[a-z0-9]+")

# Leak-scan patterns. The scanner never scans this module, because a scanner
# that trips on its own pattern definitions reports the definitions rather than
# a leak; the selftest plants a real instance to show the scanner still bites.
URI_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*://")
PRIVATE_MARKERS = (
    "docs.google.com",
    "drive.google.com",
    "/Users/",
    "/home/",
    "C:\\",
    "file://",
)


class Refusal(Exception):
    """An adapter law or a frozen schema refused an operation."""

    def __init__(self, falsifier: str, mechanism: str, detail: str = "") -> None:
        super().__init__(f"{falsifier} refused by {mechanism}: {detail}" if detail else f"{falsifier} refused by {mechanism}")
        self.falsifier = falsifier
        self.mechanism = mechanism
        self.detail = detail


class ProviderUnavailable(Exception):
    """A provider lane could not be entered. Start-readiness, not a failure."""

    def __init__(self, provider: str, reason: str, detail: str = "") -> None:
        super().__init__(f"{provider} NOT_EXERCISED ({reason}): {detail}")
        self.provider = provider
        self.reason = reason
        self.detail = detail


class Unusable(Exception):
    """The input could not be read at all, which is not the same as a refusal."""


# ---------------------------------------------------------------------------
# digests and the deterministic projection
# ---------------------------------------------------------------------------

def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_of(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def model_digest() -> str:
    """The model identity. Derived, so it cannot be stale while the model moves."""
    return digest_of({"algorithm": PROJECTION_ALGORITHM, "dimension": DIMENSION, "model_id": MODEL_ID})


def index_schema_digest() -> str:
    return digest_of(
        {
            "algorithm": PROJECTION_ALGORITHM,
            "dimension": DIMENSION,
            "model_id": MODEL_ID,
            "adapter": ADAPTER_NAME,
            "adapter_version": ADAPTER_VERSION,
            "schemas": list(CONSUMED_SCHEMAS),
        }
    )


def normalize_chunks(text: str) -> list[bytes]:
    """The deterministic chunk normalizer: paragraphs, stripped, non-empty.

    A projection is of a chunk and the receipt says so. Splitting here rather
    than at the call site is what keeps two callers from disagreeing about what
    was compared while both cite the same document.
    """
    chunks = [part.strip() for part in text.replace("\r\n", "\n").split("\n\n")]
    return [chunk.encode("utf-8") for chunk in chunks if chunk]


def project_chunk(chunk: bytes) -> tuple[float, ...]:
    """A hashed-token vector. Deterministic on every host: sha256, not hash()."""
    buckets = [0.0] * DIMENSION
    for token in TOKEN.findall(chunk.decode("utf-8").lower()):
        index = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:4], "big") % DIMENSION
        buckets[index] += 1.0
    norm = math.sqrt(sum(value * value for value in buckets))
    if norm == 0.0:
        return tuple(buckets)
    return tuple(round(value / norm, 9) for value in buckets)


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    return round(sum(a * b for a, b in zip(left, right)), 6)


# ---------------------------------------------------------------------------
# frozen schema validators
# ---------------------------------------------------------------------------

_VALIDATORS: dict[str, Draft202012Validator] = {}


def validator(name: str) -> Draft202012Validator:
    if name not in _VALIDATORS:
        path = SCHEMA_DIR / f"{name}.schema.json"
        if not path.is_file():
            raise Unusable(f"frozen schema {path} is absent; nothing here can be validated")
        _VALIDATORS[name] = Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))
    return _VALIDATORS[name]


def enforce(name: str, instance: Any, falsifier: str, what: str) -> Any:
    """Validate against a frozen schema, and name the keyword that refused."""
    errors = sorted(validator(name).iter_errors(instance), key=str)
    if errors:
        pointer = "/".join(str(part) for part in errors[0].schema_path)
        raise Refusal(falsifier, f"{name}.schema.json {pointer}", f"{what}: {errors[0].message}")
    return instance


# ---------------------------------------------------------------------------
# leak scan
# ---------------------------------------------------------------------------

def scan_for_leaks(value: Any, where: str) -> None:
    """Refuse a resolved address or a private locator in a public artifact."""
    if isinstance(value, str):
        if URI_SCHEME.search(value):
            raise Refusal(
                "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",
                "scan_for_leaks URI scheme",
                f"{where} carries a resolved address",
            )
        if value.startswith("/") or value.startswith("~/"):
            raise Refusal(
                "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",
                "scan_for_leaks absolute path",
                f"{where} carries a machine-local path",
            )
        for marker in PRIVATE_MARKERS:
            if marker in value:
                raise Refusal(
                    "PRIVATE_URL_OR_PRIVATE_VALUE_IN_PUBLIC_RECEIPT",
                    "scan_for_leaks private marker",
                    f"{where} carries a private-carrier marker",
                )
    elif isinstance(value, Mapping):
        for key, item in value.items():
            scan_for_leaks(key, f"{where}.{key}")
            scan_for_leaks(item, f"{where}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            scan_for_leaks(item, f"{where}[{index}]")


# ---------------------------------------------------------------------------
# the port
# ---------------------------------------------------------------------------

class SemanticContextPort(ABC):
    """Provider-neutral semantic context. Every backend answers exactly this."""

    backend_name: str

    @abstractmethod
    def register(self, document: dict, freshness: dict | None, content: dict) -> dict:
        """Register one document by digest and back reference."""

    @abstractmethod
    def project(self, document_id: str) -> list[dict]:
        """Project one registered document's chunks, returning projection receipts."""

    @abstractmethod
    def build_index(self) -> dict:
        """Build the index and return the index binding a query must carry."""

    @abstractmethod
    def query(self, text: str, lane: str, top_k: Any, filters: list[dict], not_applicable_rationale: str | None = None) -> tuple[dict, dict]:
        """Run one bounded query and return the recorded query and its result."""

    @abstractmethod
    def lifecycle(self, operation: str, performed_at: str) -> dict:
        """Rebuild, delete or compact the index and return the lifecycle receipt."""


class LanceDBBackend(SemanticContextPort):
    """The optional provider lane, bound only when the capability is observed.

    Constructing this binds the exact installed library. It does not implement
    retrieval: no LanceDB store has ever been exercised through this port, so a
    retrieval implementation here would be a state only a test could reach. Every
    port call therefore refuses with the lane's own name, and the lane's receipt
    records `NOT_EXERCISED` rather than a pass nobody earned.
    """

    backend_name = "LANCEDB"

    def __init__(self) -> None:
        self.binding = bind_lancedb()

    def _not_exercised(self, call: str) -> None:
        raise ProviderUnavailable(
            "lancedb",
            "LANCEDB_RUNTIME_NOT_EXERCISED",
            f"{call} has no exercised implementation behind this port; the deterministic "
            "reference backend is what proves the adapter laws",
        )

    def register(self, document: dict, freshness: dict | None, content: dict) -> dict:
        self._not_exercised("register")

    def project(self, document_id: str) -> list[dict]:
        self._not_exercised("project")

    def build_index(self) -> dict:
        self._not_exercised("build_index")

    def query(self, text: str, lane: str, top_k: Any, filters: list[dict], not_applicable_rationale: str | None = None) -> tuple[dict, dict]:
        self._not_exercised("query")

    def lifecycle(self, operation: str, performed_at: str) -> dict:
        self._not_exercised("lifecycle")


def bind_lancedb() -> dict[str, Any]:
    """Bind the exact installed LanceDB, or say plainly that there is none."""
    try:
        import lancedb  # type: ignore
    except ImportError as exc:
        raise ProviderUnavailable("lancedb", "PROVIDER_ABSENT", exc.__class__.__name__) from exc
    version = getattr(lancedb, "__version__", "NOT_PUBLISHED_BY_PROVIDER")
    module = getattr(lancedb, "__file__", None)
    return {
        "library": "lancedb",
        "version": version,
        "module_digest": text_digest(Path(module).read_text(encoding="utf-8", errors="replace")) if module else "ABSENT",
        "license_state": "HUMAN_ADMIT_REQUIRED",
    }


def probe_lancedb_lane() -> dict[str, Any]:
    """The typed state of the LanceDB lane on this host, never a fabricated pass."""
    try:
        binding = bind_lancedb()
    except ProviderUnavailable as absence:
        return {
            "lane": "LANCEDB",
            "state": "NOT_EXERCISED",
            "reason": absence.reason,
            "observed": {"import_module": "lancedb", "import_error_class": absence.detail},
            "binding": None,
        }
    return {
        "lane": "LANCEDB",
        "state": "NOT_EXERCISED",
        "reason": "LANCEDB_RUNTIME_NOT_EXERCISED",
        "observed": {"import_module": "lancedb", "import_error_class": "ABSENT"},
        "binding": binding,
    }


# ---------------------------------------------------------------------------
# the deterministic reference backend
# ---------------------------------------------------------------------------

class ReferenceBackend(SemanticContextPort):
    """In-memory, zero-network, deterministic. No key, no service, no socket."""

    backend_name = "REFERENCE_IN_MEMORY"

    def __init__(self, task_admission: Mapping[str, str]) -> None:
        # The port holds a read-only view. A backend that cannot reach the
        # admission mapping cannot move it, which is the structural half of
        # DELETE_OR_REBUILD_INDEX != TASK_STATE_CHANGE; `lifecycle` digests it
        # before and after as the observational half.
        self._admission_source = task_admission
        self.task_admission: Mapping[str, str] = MappingProxyType(dict(task_admission))
        self.back_references: dict[str, dict] = {}
        self.documents: dict[str, dict] = {}
        self.freshness: dict[str, dict] = {}
        self.content: dict[str, str] = {}
        self.absences: dict[str, str] = {}
        self.projections: dict[str, dict] = {}
        self.vectors: dict[str, tuple[float, ...]] = {}
        self.index_binding: dict[str, Any] | None = None
        self._counters = {"PR": 0, "RQ": 0, "RR": 0, "CX": 0, "LC": 0}

    # -- ids -----------------------------------------------------------------

    def _next(self, prefix: str) -> str:
        self._counters[prefix] += 1
        return f"DTCR-{prefix}-{self._counters[prefix]:03d}"

    # -- registration --------------------------------------------------------

    def register_back_reference(self, reference: dict) -> dict:
        enforce("source-back-reference", reference, "FROZEN_SCHEMA_REFUSED_THE_BACK_REFERENCE", "the back reference")
        reference_id = reference["back_reference_id"]
        if reference_id in self.back_references:
            raise Refusal(
                "BACK_REFERENCE_ID_REUSED",
                "one back reference id is registered once",
                reference_id,
            )
        self.back_references[reference_id] = reference
        return reference

    def register(self, document: dict, freshness: dict | None, content: dict) -> dict:
        enforce("semantic-document", document, "FROZEN_SCHEMA_REFUSED_THE_REGISTRATION", "the registration")
        document_id = document["document_id"]
        if document["back_reference_ref"] not in self.back_references:
            raise Refusal(
                "ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE",
                "the back reference must be registered before the document",
                f"{document_id} cites {document['back_reference_ref']}, which is not in this store",
            )
        plane, text = content.get("plane"), content.get("text")
        if plane != document["storage_plane"]:
            raise Refusal(
                "PRIVATE_CONTEXT_NOT_PUBLIC_PROMPT",
                "content plane must equal the declared storage plane",
                f"{document_id} declares {document['storage_plane']} and was handed {plane}",
            )
        if text is None:
            # A record whose content lives in a private or consumer-local
            # carrier is registrable by digest and back reference; its text is
            # simply not here, and that absence is typed rather than empty.
            self.absences[document_id] = "CONSUMER_LOCAL_CONTENT_ABSENT"
        else:
            if text_digest(text) != document["document_digest"]:
                raise Refusal(
                    "WRONG_OR_STALE_SOURCE_DIGEST",
                    "document_digest must be the digest of the registered content",
                    f"{document_id} recorded {document['document_digest'][:16]} for content hashing to {text_digest(text)[:16]}",
                )
            self.content[document_id] = text
        if freshness is not None:
            enforce("semantic-freshness-ceiling", freshness, "FROZEN_SCHEMA_REFUSED_THE_FRESHNESS_CEILING", "the freshness ceiling")
            if freshness["document_ref"] != document_id:
                raise Refusal(
                    "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
                    "a freshness ceiling belongs to the document it names",
                    f"{freshness['ceiling_id']} names {freshness['document_ref']}, registered under {document_id}",
                )
            self.freshness[document_id] = freshness
        self.documents[document_id] = document
        return document

    # -- projection ----------------------------------------------------------

    def project(self, document_id: str) -> list[dict]:
        document = self.documents.get(document_id)
        if document is None:
            raise Refusal("ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE", "the document must be registered", document_id)
        text = self.content.get(document_id)
        if text is None:
            raise Refusal(
                "PRIVATE_CONTEXT_NOT_PUBLIC_PROMPT",
                "content held in a private or consumer-local carrier is not projected in the public plane",
                f"{document_id} is registered by reference; its text is not in this tree",
            )
        receipts = []
        for index, chunk in enumerate(normalize_chunks(text)):
            vector = project_chunk(chunk)
            receipt = {
                "schema": "dtcr/projection-receipt/v1",
                "projection_receipt_id": self._next("PR"),
                "document_ref": document_id,
                "input_document_digest": document["document_digest"],
                "chunk": {
                    "chunk_index": index,
                    "chunk_digest": hashlib.sha256(chunk).hexdigest(),
                    "chunk_byte_count": len(chunk),
                },
                "embedding_provider": {
                    "provider_binding_id": PROVIDER_BINDING_ID,
                    "provider_name": "deterministic-reference-projection",
                    "model_id": MODEL_ID,
                    "model_digest": model_digest(),
                    "dimension": DIMENSION,
                    "config_digest": index_schema_digest(),
                },
                "output_projection_digest": digest_of(list(vector)),
                # No provider was called: this projection is a local pure
                # function. NOT_EXERCISED is the transport state, and its exit
                # code is null because there was no process to exit.
                "transport": {"outcome": "NOT_EXERCISED", "exit_code": None},
                "data_handling": {
                    "content_plane": document["storage_plane"],
                    "provider_terms_admission": "HUMAN_ADMIT_REQUIRED",
                },
                "establishes": {
                    "semantic_correctness": False,
                    "retrieval_quality": False,
                    "technical_authority": False,
                },
            }
            enforce("projection-receipt", receipt, "FROZEN_SCHEMA_REFUSED_THE_PROJECTION_RECEIPT", "the projection receipt")
            self.projections[receipt["projection_receipt_id"]] = receipt
            self.vectors[receipt["projection_receipt_id"]] = vector
            receipts.append(receipt)
        return receipts

    def project_all(self) -> list[dict]:
        receipts: list[dict] = []
        for document_id in sorted(self.documents):
            if document_id in self.absences:
                continue
            receipts.extend(self.project(document_id))
        return receipts

    # -- index ---------------------------------------------------------------

    def index_rows(self) -> list[dict]:
        rows = []
        for receipt_id in sorted(self.projections):
            receipt = self.projections[receipt_id]
            rows.append(
                {
                    "projection_receipt_id": receipt_id,
                    "document_ref": receipt["document_ref"],
                    "chunk_index": receipt["chunk"]["chunk_index"],
                    "chunk_digest": receipt["chunk"]["chunk_digest"],
                    "output_projection_digest": receipt["output_projection_digest"],
                }
            )
        return rows

    def current_index_digest(self) -> str:
        return digest_of({"rows": self.index_rows(), "index_schema_digest": index_schema_digest()})

    def build_index(self) -> dict:
        for receipt in self.projections.values():
            document = self.documents[receipt["document_ref"]]
            if receipt["input_document_digest"] != document["document_digest"]:
                raise Refusal(
                    "WRONG_OR_STALE_SOURCE_DIGEST",
                    "every projection is rebound to its document digest at build time",
                    f"{receipt['projection_receipt_id']} was projected from "
                    f"{receipt['input_document_digest'][:16]}, the document now reads "
                    f"{document['document_digest'][:16]}",
                )
        if not self.projections:
            raise Refusal("AN_INDEX_WITH_NO_PROJECTIONS_IS_NOT_AN_INDEX", "build_index refuses an empty index", "no projections")
        self.index_binding = {
            "index_digest": self.current_index_digest(),
            "index_schema_digest": index_schema_digest(),
            "projection_receipt_refs": sorted(self.projections),
        }
        return self.index_binding

    # -- retrieval -----------------------------------------------------------

    def _matches_filters(self, document: dict, filters: list[dict]) -> bool:
        for item in filters:
            field, value = item["field"], item["value"]
            if field == "subsystem_tag" and value not in document["subsystem_tags"]:
                return False
            if field == "document_kind" and document["document_kind"] != value:
                return False
            if field == "visibility_class" and document["visibility_class"] != value:
                return False
            if field == "owning_decision" and document["owning_decision"] != value:
                return False
            if field == "observed_after" and not document["observed_at"] > value:
                return False
        return True

    def superseding_document(self, document_id: str) -> str | None:
        """Which registered document supersedes this one, if any is registered."""
        ceiling = self.freshness.get(document_id)
        if ceiling is None or ceiling["supersession"] == "NOT_SUPERSEDED":
            return None
        named = ceiling["supersession"]["superseding_decision_ref"]
        for candidate_id, candidate in sorted(self.documents.items()):
            if candidate["owning_decision"] == named:
                return candidate_id
        return None

    def enforce_supersession_order(self, rows: list[dict]) -> list[dict]:
        """A superseded document never sits above the document that replaced it.

        Similarity has no opinion about which decision came last, so an old
        record with more overlapping words outranks its own replacement unless
        something moves it. This is that something.
        """
        ordered = list(rows)
        for _ in range(len(ordered)):
            moved = False
            positions = {row["document_ref"]: index for index, row in enumerate(ordered)}
            for index, row in enumerate(ordered):
                newer = self.superseding_document(row["document_ref"])
                if newer is not None and newer in positions and positions[newer] > index:
                    ordered.insert(positions[newer] + 1, ordered.pop(index))
                    moved = True
                    break
            if not moved:
                break
        return ordered

    def assert_supersession_order(self, rows: list[dict]) -> None:
        positions = {row["document_ref"]: index for index, row in enumerate(rows)}
        for document_id, index in positions.items():
            newer = self.superseding_document(document_id)
            if newer is not None and newer in positions and positions[newer] > index:
                raise Refusal(
                    "STALE_ADR_OVERRIDES_NEWER_EXPLICIT_DECISION",
                    "assert_supersession_order compares the emitted order against supersession",
                    f"{document_id} is superseded by {newer} and was ranked above it",
                )

    def query(
        self,
        text: str,
        lane: str,
        top_k: Any,
        filters: list[dict],
        not_applicable_rationale: str | None = None,
    ) -> tuple[dict, dict]:
        if self.index_binding is None:
            raise Refusal("MUTABLE_INDEX_OR_MODEL_IDENTITY", "a query needs an index binding", "no index has been built")
        # The identity the query will carry has to be the identity the store has
        # now. A model or an index that moved under a stable name is refused
        # before a row is read, not after a result was already emitted.
        if index_schema_digest() != self.index_binding["index_schema_digest"]:
            raise Refusal(
                "MUTABLE_INDEX_OR_MODEL_IDENTITY",
                "index_schema_digest is recomputed before every query",
                "the projection algorithm or dimension moved under a stable index identity",
            )
        if self.current_index_digest() != self.index_binding["index_digest"]:
            raise Refusal(
                "MUTABLE_INDEX_OR_MODEL_IDENTITY",
                "index_digest is recomputed before every query",
                "the indexed rows moved under a stable index identity",
            )

        query = {
            "schema": "dtcr/retrieval-query/v1",
            "query_id": self._next("RQ"),
            "lane": lane,
            "query_digest": text_digest(text),
            "top_k": top_k,
            "filters": filters,
            "index_binding": self.index_binding,
            "establishes": {"decision": False, "technical_authority": False, "task_pass": False},
        }
        if not_applicable_rationale is not None:
            query["not_applicable_rationale"] = not_applicable_rationale
        enforce("retrieval-query", query, "FROZEN_SCHEMA_REFUSED_THE_QUERY", "the query")

        if lane == "NOT_APPLICABLE":
            result = {
                "schema": "dtcr/retrieval-result/v1",
                "result_id": self._next("RR"),
                "query_ref": query["query_id"],
                "outcome": "NOT_APPLICABLE",
                "not_applicable_rationale": not_applicable_rationale,
                "rows": [],
                "establishes": {"deterministic_fact": False, "decision": False, "task_pass": False},
            }
            enforce("retrieval-result", result, "FROZEN_SCHEMA_REFUSED_THE_NOT_APPLICABLE_RESULT", "the not-applicable result")
            return query, result

        if not isinstance(top_k, int):
            # The frozen schema admits the NOT_APPLICABLE literal for any lane;
            # a lane that is going to read rows still needs a number, and this
            # is a refusal rather than the crash the conversion would be.
            raise Refusal(
                "AN_UNBOUNDED_NEIGHBOURHOOD_IS_NOT_A_QUERY",
                "a lane that reads rows carries an integer top_k",
                f"{lane} was given {top_k!r}",
            )
        probe = project_chunk(text.encode("utf-8"))
        best: dict[str, float] = {}
        for row in self.index_rows():
            document = self.documents[row["document_ref"]]
            if not self._matches_filters(document, filters):
                continue
            score = cosine(probe, self.vectors[row["projection_receipt_id"]])
            if score <= 0.0:
                continue
            if document["document_id"] not in self.freshness:
                raise Refusal(
                    "UNKNOWN_FRESHNESS_SILENTLY_TREATED_CURRENT",
                    "a candidate with no registered freshness ceiling is refused, not returned",
                    f"{document['document_id']} has no DTCR-FC row",
                )
            best[row["document_ref"]] = max(best.get(row["document_ref"], 0.0), score)

        ranked = sorted(best.items(), key=lambda item: (-item[1], item[0]))[: int(top_k)]
        rows = [
            {
                "rank": 0,
                "row_class": "SEMANTIC_ROW",
                "authority": "NON_AUTHORITATIVE_CANDIDATE",
                "document_ref": document_id,
                "back_reference_ref": self.documents[document_id]["back_reference_ref"],
                "freshness_ref": self.freshness[document_id]["ceiling_id"],
                "score": score,
                "score_method": (
                    f"cosine similarity over the {MODEL_ID} projection at dimension {DIMENSION}, "
                    f"best chunk per document, over the projections named by this index binding"
                ),
            }
            for document_id, score in ranked
        ]
        rows = self.enforce_supersession_order(rows)
        for rank, row in enumerate(rows, start=1):
            row["rank"] = rank
        self.assert_supersession_order(rows)

        result = {
            "schema": "dtcr/retrieval-result/v1",
            "result_id": self._next("RR"),
            "query_ref": query["query_id"],
            "outcome": "ROWS_RETURNED" if rows else "EMPTY",
            "rows": rows,
            "establishes": {"deterministic_fact": False, "decision": False, "task_pass": False},
        }
        enforce("retrieval-result", result, "FROZEN_SCHEMA_REFUSED_THE_RESULT", "the result")
        return query, result

    # -- consumption ---------------------------------------------------------

    def consume(self, result: dict, read_ranks: Iterable[int], manifest_ref: str, task_ref: str, consumed_at: str) -> list[dict]:
        by_rank = {row["rank"]: row for row in result["rows"]}
        manifest = []
        for rank in sorted(set(read_ranks)):
            row = by_rank.get(rank)
            if row is None:
                raise Refusal(
                    "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
                    "a manifest entry must name a row this result returned",
                    f"rank {rank} is not in {result['result_id']}",
                )
            entry = {
                "schema": "dtcr/consumed-context-row/v1",
                "consumed_row_id": self._next("CX"),
                "manifest_ref": manifest_ref,
                "result_ref": result["result_id"],
                "row_rank": rank,
                "document_ref": row["document_ref"],
                "back_reference_ref": row["back_reference_ref"],
                "freshness_ref": row["freshness_ref"],
                "basis_grade": "SEMANTIC_CONTEXT_CANDIDATE",
                "influence": "CONTEXT_ONLY",
                "consuming_task_ref": task_ref,
                "consumed_at": consumed_at,
            }
            enforce("consumed-context-row", entry, "FROZEN_SCHEMA_REFUSED_THE_MANIFEST_ENTRY", "the manifest entry")
            manifest.append(entry)
        reconcile_manifest(result, manifest, read_ranks)
        return manifest

    # -- lifecycle -----------------------------------------------------------

    def lifecycle(self, operation: str, performed_at: str) -> dict:
        before_admission = digest_of(dict(self._admission_source))
        before = self.index_binding["index_digest"] if self.index_binding else "NO_PRIOR_INDEX"
        refs = sorted(self.projections)

        if operation == "REBUILD":
            self.index_binding = None
            after = self.build_index()["index_digest"]
        elif operation == "DELETE":
            self.index_binding = None
            self.projections.clear()
            self.vectors.clear()
            after = "INDEX_ABSENT_AFTER_DELETE"
            refs = []
        elif operation == "COMPACT":
            after = self.current_index_digest()
        else:
            raise Unusable(f"{operation} is not a lifecycle operation")

        if digest_of(dict(self._admission_source)) != before_admission:
            raise Refusal(
                "REBUILD_OR_DELETE_CHANGES_TASK_ADMISSION",
                "the admission mapping is digested before and after every lifecycle operation",
                f"{operation} moved task admission",
            )

        receipt = {
            "schema": "dtcr/semantic-index-lifecycle-receipt/v1",
            "lifecycle_receipt_id": self._next("LC"),
            "operation": operation,
            "performed_at": performed_at,
            "index_digest_before": before,
            "index_digest_after": after,
            "projection_receipt_refs": refs,
            "changes": {
                "task_admission": "UNCHANGED",
                "technical_evidence": "NO_NEW_EVIDENCE",
                "closure_state": "UNCHANGED",
            },
        }
        enforce("semantic-index-lifecycle-receipt", receipt, "FROZEN_SCHEMA_REFUSED_THE_LIFECYCLE_RECEIPT", "the lifecycle receipt")
        return receipt


def reconcile_manifest(result: dict, manifest: list[dict], read_ranks: Iterable[int]) -> None:
    """The consumer check the frozen consumed-context-row schema asks for.

    Its own description says nothing in that document can prove every consumed
    row was listed. This compares both directions: every rank that was read is
    listed, and every listed entry names a row this result returned.
    """
    listed = {entry["row_rank"] for entry in manifest}
    read = set(read_ranks)
    returned = {row["rank"] for row in result["rows"]}
    missing = sorted(read - listed)
    if missing:
        raise Refusal(
            "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
            "reconcile_manifest compares the ranks read against the ranks listed",
            f"{result['result_id']} rank(s) {missing} were read and are in no manifest entry",
        )
    phantom = sorted(listed - returned)
    if phantom:
        raise Refusal(
            "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
            "reconcile_manifest compares the ranks listed against the rows returned",
            f"manifest lists rank(s) {phantom} that {result['result_id']} never returned",
        )
    for entry in manifest:
        if entry["result_ref"] != result["result_id"]:
            raise Refusal(
                "RETRIEVED_ROW_NOT_LISTED_AS_CONSUMED",
                "a manifest entry belongs to the result it names",
                f"{entry['consumed_row_id']} names {entry['result_ref']}",
            )


# ---------------------------------------------------------------------------
# the fixture run: one deterministic pass over the committed public store
# ---------------------------------------------------------------------------

def load_fixture(path: Path = FIXTURE) -> dict:
    if not path.is_file():
        raise Unusable(f"{path} is absent; the deterministic lane has nothing to read")
    return json.loads(path.read_text(encoding="utf-8"))


TASK_ADMISSION = {
    "DTCR-TASK-001": "OPEN",
    "DTCR-TASK-002": "AWAITING_DETERMINISTIC_EVIDENCE",
    "DTCR-TASK-003": "CLOSED_WITH_RECEIPT",
}

QUERIES = (
    {
        "name": "domain-isolation",
        "text": "domain layer imports a persistence client at the boundary",
        "lane": "HYBRID",
        "top_k": 3,
        "filters": [{"field": "subsystem_tag", "value": "domain"}],
    },
    {
        "name": "checkout-persistence",
        "text": "checkout ledger client write path persistence rule",
        "lane": "VECTOR",
        "top_k": 4,
        "filters": [{"field": "subsystem_tag", "value": "checkout"}],
    },
    {
        "name": "scheduler-stall",
        "text": "scheduler queue stopped draining after a worker lease expired",
        "lane": "KEYWORD",
        "top_k": 2,
        "filters": [{"field": "document_kind", "value": "INCIDENT_REVIEW"}],
    },
    {
        "name": "mechanical-rename",
        "text": "rename a local variable in one function",
        "lane": "NOT_APPLICABLE",
        "top_k": "NOT_APPLICABLE",
        "filters": [],
        "rationale": "this task is a mechanical rename with no decision, incident or objective that stored context could bear on",
    },
)


def deterministic_run(fixture: dict | None = None) -> dict[str, Any]:
    """One full pass: register, project, index, query, consume, rebuild, delete."""
    fixture = fixture or load_fixture()
    store = ReferenceBackend(TASK_ADMISSION)
    for reference in fixture["back_references"]:
        store.register_back_reference(reference)
    ceilings = {item["document_ref"]: item for item in fixture["freshness_ceilings"]}
    for entry in fixture["documents"]:
        document = entry["document"]
        store.register(document, ceilings.get(document["document_id"]), entry["content"])
    store.project_all()
    binding = store.build_index()

    queries = []
    consumed_total = 0
    for spec in QUERIES:
        query, result = store.query(
            spec["text"],
            spec["lane"],
            spec["top_k"],
            spec["filters"],
            spec.get("rationale"),
        )
        read_ranks = [row["rank"] for row in result["rows"][:2]]
        manifest = store.consume(
            result,
            read_ranks,
            manifest_ref=f"context manifest for the {spec['name']} review",
            task_ref=f"review bound to the {spec['name']} change unit",
            consumed_at="2026-08-22",
        ) if read_ranks else []
        consumed_total += len(manifest)
        # A row ranked below a row with a lower score is the supersession rule
        # having moved it. Recording which documents were moved keeps that
        # visible in the receipt instead of reading as a scoring bug.
        by_score = [
            row["document_ref"]
            for row in sorted(result["rows"], key=lambda item: (-item["score"], item["document_ref"]))
        ]
        emitted = [row["document_ref"] for row in result["rows"]]
        queries.append(
            {
                "name": spec["name"],
                "query_id": query["query_id"],
                "lane": query["lane"],
                "top_k": query["top_k"],
                "result_id": result["result_id"],
                "outcome": result["outcome"],
                "rows": [
                    {"rank": row["rank"], "document_ref": row["document_ref"], "score": row["score"]}
                    for row in result["rows"]
                ],
                "demoted_by_supersession": [
                    document_id
                    for document_id in emitted
                    if by_score.index(document_id) < emitted.index(document_id)
                ],
                "consumed_ranks": read_ranks,
                "result_digest": digest_of(result),
            }
        )

    index_row_count = len(store.index_rows())
    lifecycle = [store.lifecycle("REBUILD", "2026-08-22"), store.lifecycle("DELETE", "2026-08-22")]
    admission_after = digest_of(dict(TASK_ADMISSION))

    return {
        "store": store,
        "binding": binding,
        "queries": queries,
        "lifecycle": lifecycle,
        "consumed_total": consumed_total,
        "admission_digest": admission_after,
        "index_rows": index_row_count,
    }


def build_receipt(fixture: dict | None = None) -> dict[str, Any]:
    """The deterministic receipt. Same tree in, same bytes out, every host."""
    fixture = fixture or load_fixture()
    run = deterministic_run(fixture)
    store: ReferenceBackend = run["store"]
    receipt = {
        "schema": "dtcr/semantic-context-reference-receipt/v1",
        "adapter": {"name": ADAPTER_NAME, "version": ADAPTER_VERSION, "backend": ReferenceBackend.backend_name},
        "network": "NONE. The reference backend is a pure function of the committed fixture; "
        "no socket, no API key and no embedding service is involved in this lane.",
        "consumed_schemas": list(CONSUMED_SCHEMAS),
        "projection": {
            "algorithm": PROJECTION_ALGORITHM,
            "dimension": DIMENSION,
            "model_id": MODEL_ID,
            "model_digest": model_digest(),
            "provider_binding_id": PROVIDER_BINDING_ID,
            "transport": "NOT_EXERCISED",
        },
        "fixture": {
            "path": "skills/dual-track-code-review-loop/adapters/semantic-context/fixtures/public-context-store.json",
            "digest": digest_of(fixture),
            "documents": len(fixture["documents"]),
            "back_references": len(fixture["back_references"]),
            "freshness_ceilings": len(fixture["freshness_ceilings"]),
        },
        "coverage": {
            "document_kinds": sorted({entry["document"]["document_kind"] for entry in fixture["documents"]}),
            "reference_kinds": sorted({item["reference_kind"] for item in fixture["back_references"]}),
            "visibility_classes": sorted({entry["document"]["visibility_class"] for entry in fixture["documents"]}),
            "lanes": sorted({spec["lane"] for spec in QUERIES}),
        },
        "index": {
            "index_digest": run["binding"]["index_digest"],
            "index_schema_digest": run["binding"]["index_schema_digest"],
            "projection_receipts": len(run["binding"]["projection_receipt_refs"]),
            "rows": run["index_rows"],
        },
        "absences": dict(sorted(store.absences.items())),
        "queries": run["queries"],
        "consumed_rows": run["consumed_total"],
        "lifecycle": [
            {
                "lifecycle_receipt_id": item["lifecycle_receipt_id"],
                "operation": item["operation"],
                "index_digest_before": item["index_digest_before"],
                "index_digest_after": item["index_digest_after"],
                "changes": item["changes"],
            }
            for item in run["lifecycle"]
        ],
        "task_admission_digest_after_lifecycle": run["admission_digest"],
        "establishes": {
            "semantic_correctness": False,
            "retrieval_quality": False,
            "current_policy": False,
            "reproduced_failure": False,
            "deterministic_fact": False,
            "task_pass": False,
            "provider_lane_exercised": False,
        },
    }
    scan_for_leaks(receipt, "reference receipt")
    return receipt


def build_lane_receipt() -> dict[str, Any]:
    lane = probe_lancedb_lane()
    receipt = {
        "schema": "dtcr/semantic-context-provider-lane/v1",
        "adapter": {"name": ADAPTER_NAME, "version": ADAPTER_VERSION},
        **lane,
        "policy": (
            "LanceDB is a candidate adapter behind SemanticContextPort, not portable core "
            "authority. Entering the lane requires binding the exact installed library "
            "revision and its licence/NOTICE state, which is a human admission. Until a run "
            "has actually exercised it, the honest state is NOT_EXERCISED; the deterministic "
            "reference backend proves the adapter laws on its own."
        ),
        "establishes": {
            "provider_available_elsewhere": False,
            "retrieval_quality": False,
            "semantic_correctness": False,
            "task_pass": False,
        },
    }
    scan_for_leaks(receipt, "provider lane receipt")
    return receipt


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def write_json(path: Path, document: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DTCR semantic-context adapter")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("run", help="run the deterministic reference lane and print its receipt")
    freeze = sub.add_parser("receipt", help="write the deterministic reference receipt")
    freeze.add_argument("--out", type=Path, default=RECEIPTS / "reference-backend.json")
    lane = sub.add_parser("lane-receipt", help="write the provider-lane receipt for this host")
    lane.add_argument("--out", type=Path, default=RECEIPTS / "lancedb-lane.json")
    args = parser.parse_args(argv)

    try:
        if args.mode == "run":
            print(json.dumps(build_receipt(), indent=2, sort_keys=True))
        elif args.mode == "receipt":
            write_json(args.out, build_receipt())
            print(f"wrote {args.out.name}")
        else:
            write_json(args.out, build_lane_receipt())
            print(f"wrote {args.out.name}")
    except Refusal as refusal:
        print(f"DTCR-SEMANTIC-CONTEXT-REFUSED {refusal}", file=sys.stderr)
        return 2
    except Unusable as unusable:
        print(f"DTCR-SEMANTIC-CONTEXT-UNUSABLE {unusable}", file=sys.stderr)
        return 64
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
