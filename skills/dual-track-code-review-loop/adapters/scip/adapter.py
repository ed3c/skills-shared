#!/usr/bin/env python3
"""Turn one SCIP index plus the exact source subject it was built from into
`dtcr/symbol-fact/v1` rows, a `dtcr/exact-source-subject/v1`, a
`dtcr/coverage-ceiling/v1` and a `dtcr/fact-plane-receipt/v1`.

What this adapter is allowed to say
-----------------------------------
The provider here is `scip-python`, and what it produces is a Python index of a
Python project. That sentence is the ceiling, and this file writes it down in
three places rather than leaving the reader to infer it: the ceiling's
`omissions` name the languages nothing indexed, `establishes.complete_call_graph`
is fixed false on every emitted row, and no code path writes a task outcome or a
merge admission.

The sharper ceiling is inside the language. `scip-python` 0.6.6 emits no
`SymbolInformation.relationships` at all, so every edge this adapter reports is
derived here, by nesting a non-definition occurrence inside the smallest
definition whose `enclosing_range` contains it. That inference is a floor: it
misses dynamic dispatch, `getattr`, reflection, callbacks, decorated
re-exports and generated code. `fixtures/python-package/dtcr_fixture/dynamic.py`
is in the subject precisely so this is a measured claim -- the index carries no
occurrence of `Pricing#apply()` in that file even though the code calls it --
and every derived edge is emitted as `REFERENCES` with provenance
`OCCURRENCE_ENCLOSING_RANGE_HEURISTIC` and completeness `PARTIAL_LOWER_BOUND`.
`CALLS` is not reachable from this code path.

Two modes, one emitter
----------------------
`replay` reads a recorded `index.scip` -- the real bytes a real `scip-python`
run wrote, committed under `fixtures/recorded/` -- and needs no provider on the
machine. `live` copies the subject blobs into a scratch project root, runs the
real indexer there and decodes what it wrote. Both funnel into `emit_facts`, so
the deterministic tests exercise the code the live path uses. A missing
indexer is start-readiness, not a failure: `live` refuses to invent an index
and the selftest reports `NOT_EXERCISED`.

One provider trap is written into both paths because it is silent. Handed a
`--cwd` that reaches the project through a symlink -- `/tmp` on this platform,
and every `mkdtemp` path under `/var/folders` -- scip-python 0.6.6 exits 0 and
writes a 56-byte, metadata-only index with no documents at all. `live`
resolves the scratch path so it cannot happen, and `check_index_binding`
refuses a document-free index so that if it happens anywhere else the run dies
instead of reporting a clean pass over nothing.

Identities, and what each one is worth
--------------------------------------
    indexer_sha256   sha256 over the canonical `sha256  name` listing of the
                     installed package's launcher and bundle files. The
                     launcher alone is a 1.4 KB shim identical across releases,
                     so digesting it would have produced an identity that
                     cannot tell two indexers apart.
    config_digest    the invocation, with every machine-local path replaced by
                     its role, plus the digest of the pinned `pyrightconfig.json`.
                     A config digest that moves when the checkout moves
                     identifies a machine.
    index_digest     sha256 of the `index.scip` bytes. It is NOT reproducible
                     across hosts: `Index.metadata.project_root` is an absolute
                     `file://` URL of the machine that ran the indexer, so the
                     same sources at two checkouts produce two digests. The
                     comparable one is `facts_digest_modulo_subject`, over the
                     emitted facts with the subject and the project root
                     stripped, and the live receipt records both.

Refusals are named
------------------
Every guard raises `Refusal` carrying the falsifier it exists to kill, so a
planted defect proves *its own* guard. Four are input guards, reached by
feeding the adapter a defective subject or index; six are post-conditions run
over the emitted artifacts on the way out, reached by mutating what was
emitted. `selftest.py` plants all ten, and the frozen schemas refuse most of
the same classes independently, which is the second arrival.

    SCIP_INDEX_WRONG_SUBJECT
    SCIP_INDEX_DIGEST_ABSENT
    INDEXER_VERSION_OR_CONFIG_UNBOUND
    STALE_INDEX_REUSED_AFTER_SOURCE_CHANGE
    PARTIAL_COVERAGE_PROMOTED_TO_COMPLETE
    OCCURRENCE_NESTING_PROMOTED_TO_CALL_GRAPH
    UNRESOLVED_SYMBOL_OMITTED_FROM_DENOMINATOR
    RELATIONSHIP_WITHOUT_SOURCE_RANGE
    PROVIDER_ID_PROMOTED_TO_UNIVERSAL_ID
    SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS

Usage
-----
    adapter.py replay <request.json> [--out <bundle.json>]
    adapter.py live --package <dir> [--repo <dir>] [--omit KIND:detail]
        [--record <fixture-dir>] [--receipt <path>] [--out <bundle.json>]

Exit 0 emitted, 2 refused, 70 the indexer is absent in `live` mode.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ADAPTER_DIR = Path(__file__).resolve().parent
SKILL = ADAPTER_DIR.parents[1]
SCHEMAS = SKILL / "references" / "schemas"

FACT_SCHEMA = "dtcr/symbol-fact/v1"
CEILING_SCHEMA = "dtcr/coverage-ceiling/v1"
RECEIPT_SCHEMA = "dtcr/fact-plane-receipt/v1"
REQUEST_SCHEMA = "dtcr/scip-run-request/v1"
LIVE_RECEIPT_SCHEMA = "dtcr/scip-live-receipt/v1"

EXECUTABLE_NAME = "scip-python"
INDEXER_NAME = "scip-python"
PROJECT_NAME = "dtcr-scip-fixture"
PROJECT_VERSION = "0"
INDEX_BASENAME = "index.scip"

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

# SCIP protocol field numbers, read off the serializer the installed provider
# itself ships, not off a remembered `scip.proto`. Each one was grepped out of
# `dist/scip-python.js` as the literal write call that emits it, e.g.
# `this.enclosing_range.length&&t.writePackedInt32(7,...)`. A field number
# recalled wrongly decodes into plausible garbage rather than failing, which is
# the one way this file could lie without any guard firing.
F_INDEX = {"metadata": 1, "documents": 2, "external_symbols": 3}
F_METADATA = {"version": 1, "tool_info": 2, "project_root": 3, "text_document_encoding": 4}
F_TOOLINFO = {"name": 1, "version": 2, "arguments": 3}
F_DOCUMENT = {"relative_path": 1, "occurrences": 2, "symbols": 3, "language": 4, "text": 5}
F_OCCURRENCE = {"range": 1, "symbol": 2, "symbol_roles": 3, "syntax_kind": 5, "enclosing_range": 7}
F_SYMBOL_INFORMATION = {"symbol": 1, "relationships": 4, "kind": 5, "display_name": 6}

# scip.SymbolRole, same source.
SYMBOL_ROLE_BITS = [(1, "DEFINITION"), (2, "IMPORT"), (4, "WRITE_ACCESS"), (8, "READ_ACCESS")]
TEXT_ENCODING_UTF8 = 1

# The normalization scheme that mediates provider identifiers into this
# contract's vocabulary. It is written out in full and digested, because
# `provider_scoped_identity` refuses a bare provider string precisely so that
# the rule under which one indexer's identifier is read is recorded beside it.
SYMBOL_SCHEME = "scip symbol grammar, scip-python descriptor-suffix mapping v1"
SYMBOL_SCHEME_RULES = """\
A SCIP symbol is `<scheme> <manager> <package> <version> <descriptors>`, and the
descriptor suffix carries the kind. This adapter maps suffixes to the frozen
symbol_kind vocabulary by the following total rule, applied to the final
descriptor:

    ends with `)` and the descriptor opens with `(`  -> OTHER   (parameter)
    ends with `().`                                  -> METHOD if any earlier
                                                        descriptor ends with `#`,
                                                        otherwise FUNCTION
    ends with `#`                                    -> TYPE
    ends with `:`                                    -> MODULE  (meta/module root)
    ends with `/`                                    -> MODULE  (namespace)
    ends with `.`                                    -> FIELD   (term)
    a symbol beginning with `local `                 -> OTHER   (document-local)
    anything else                                    -> OTHER

The mapping is a reading of the identifier, not a fact the indexer asserted:
scip-python 0.6.6 leaves SymbolInformation.kind unset on every symbol it emits,
so a symbol_kind sourced from the provider would have been unavailable and a
symbol_kind sourced from a guess would have been unfalsifiable. This rule is
the falsifiable middle: it is total, it is digested here, and a consumer that
disagrees with it can say exactly which clause it disagrees with.
"""


class Refusal(Exception):
    """A named falsifier reached its own guard."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


def binding_id(prefix: str, material: bytes) -> str:
    return f"{prefix}-{sha256_hex(material)[:16]}"


def line_starts(data: bytes) -> list[int]:
    starts = [0]
    for index, byte in enumerate(data):
        if byte == 0x0A:
            starts.append(index + 1)
    return starts


SYMBOL_SCHEME_DIGEST = sha256_hex(SYMBOL_SCHEME_RULES.encode("utf-8"))


# --------------------------------------------------------------------------
# protobuf wire reader -- pure, so the recorded index exercises it
# --------------------------------------------------------------------------
def _varint(data: bytes, index: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if index >= len(data):
            raise Refusal("SCIP_INDEX_UNREADABLE", "a varint runs past the end of the index bytes")
        byte = data[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index
        shift += 7
        if shift > 63:
            raise Refusal("SCIP_INDEX_UNREADABLE", "a varint is longer than 64 bits")


def wire_fields(data: bytes) -> list[tuple[int, int, Any]]:
    """(field_number, wire_type, value) for one protobuf message body.

    Every field is returned, including ones no accessor here reads, and a wire
    type this reader does not decode is a refusal rather than a skip. Skipping
    an undecodable field would let a truncated or foreign index read as a short
    one, and a short index is exactly what this adapter must never mistake for
    a small project."""
    out: list[tuple[int, int, Any]] = []
    index = 0
    while index < len(data):
        key, index = _varint(data, index)
        number, wire = key >> 3, key & 7
        if wire == 0:
            value, index = _varint(data, index)
        elif wire == 2:
            length, index = _varint(data, index)
            value = data[index:index + length]
            if len(value) != length:
                raise Refusal("SCIP_INDEX_UNREADABLE", "a length-delimited field runs past the end of the index")
            index += length
        elif wire == 5:
            value, index = data[index:index + 4], index + 4
        elif wire == 1:
            value, index = data[index:index + 8], index + 8
        else:
            raise Refusal("SCIP_INDEX_UNREADABLE", f"wire type {wire} is not one this reader decodes")
        out.append((number, wire, value))
    return out


def _packed_ints(data: bytes) -> list[int]:
    out: list[int] = []
    index = 0
    while index < len(data):
        value, index = _varint(data, index)
        out.append(value)
    return out


def _first(fields: list[tuple[int, int, Any]], number: int, default: Any = None) -> Any:
    for num, _wire, value in fields:
        if num == number:
            return value
    return default


def _all(fields: list[tuple[int, int, Any]], number: int) -> list[Any]:
    return [value for num, _wire, value in fields if num == number]


def _text(value: Any) -> str | None:
    return None if value is None else bytes(value).decode("utf-8")


def decode_index(data: bytes) -> dict[str, Any]:
    """The parts of a SCIP index this adapter is prepared to speak for."""
    top = wire_fields(data)
    metadata_bytes = _first(top, F_INDEX["metadata"])
    if metadata_bytes is None:
        raise Refusal(
            "INDEXER_VERSION_OR_CONFIG_UNBOUND",
            "the index carries no Metadata, so the tool that wrote it is unnamed and the "
            "identity in the receipt would be the caller's assertion rather than the index's",
        )
    metadata = wire_fields(metadata_bytes)
    tool_bytes = _first(metadata, F_METADATA["tool_info"])
    tool = wire_fields(tool_bytes) if tool_bytes is not None else []
    documents = []
    for document_bytes in _all(top, F_INDEX["documents"]):
        fields = wire_fields(document_bytes)
        occurrences = []
        for occurrence_bytes in _all(fields, F_DOCUMENT["occurrences"]):
            occ = wire_fields(occurrence_bytes)
            occurrences.append(
                {
                    "range": _packed_ints(_first(occ, F_OCCURRENCE["range"], b"")),
                    "symbol": _text(_first(occ, F_OCCURRENCE["symbol"])) or "",
                    "symbol_roles": _first(occ, F_OCCURRENCE["symbol_roles"], 0),
                    "enclosing_range": _packed_ints(_first(occ, F_OCCURRENCE["enclosing_range"], b"")),
                }
            )
        symbols = []
        for symbol_bytes in _all(fields, F_DOCUMENT["symbols"]):
            sym = wire_fields(symbol_bytes)
            symbols.append(
                {
                    "symbol": _text(_first(sym, F_SYMBOL_INFORMATION["symbol"])) or "",
                    "kind": _first(sym, F_SYMBOL_INFORMATION["kind"]),
                    "display_name": _text(_first(sym, F_SYMBOL_INFORMATION["display_name"])),
                    "relationships": len(_all(sym, F_SYMBOL_INFORMATION["relationships"])),
                }
            )
        documents.append(
            {
                "relative_path": _text(_first(fields, F_DOCUMENT["relative_path"])) or "",
                "language": _text(_first(fields, F_DOCUMENT["language"])),
                "occurrences": occurrences,
                "symbols": symbols,
            }
        )
    externals = [
        _text(_first(wire_fields(blob), F_SYMBOL_INFORMATION["symbol"])) or ""
        for blob in _all(top, F_INDEX["external_symbols"])
    ]
    return {
        "tool_name": _text(_first(tool, F_TOOLINFO["name"])) or "",
        "tool_version": _text(_first(tool, F_TOOLINFO["version"])) or "",
        "project_root": _text(_first(metadata, F_METADATA["project_root"])) or "",
        "text_document_encoding": _first(metadata, F_METADATA["text_document_encoding"], 0),
        "documents": documents,
        "external_symbols": externals,
        "provider_relationship_count": sum(s["relationships"] for d in documents for s in d["symbols"]),
    }


# --------------------------------------------------------------------------
# symbol reading
# --------------------------------------------------------------------------
def descriptors_of(symbol: str) -> str:
    """The descriptor tail of a SCIP symbol: everything after the fourth space-
    separated header field. `local 3` has no descriptors and says so."""
    if symbol.startswith("local "):
        return ""
    parts = symbol.split(" ", 4)
    return parts[4] if len(parts) == 5 else ""


def symbol_kind_of(symbol: str) -> str:
    tail = descriptors_of(symbol)
    if not tail:
        return "OTHER"
    if tail.endswith(")") and "(" in tail.rsplit("/", 1)[-1]:
        return "OTHER"
    if tail.endswith("()."):
        return "METHOD" if "#" in tail[: -len("().")] else "FUNCTION"
    if tail.endswith("#"):
        return "TYPE"
    if tail.endswith(":") or tail.endswith("/"):
        return "MODULE"
    if tail.endswith("."):
        return "FIELD"
    return "OTHER"


def display_name_of(symbol: str, provided: str | None) -> str | None:
    if provided:
        return provided
    tail = descriptors_of(symbol)
    return tail or None


def identity_of(symbol: str) -> dict[str, Any]:
    return {
        "provider_scoped_id": symbol,
        "normalization": {"scheme": SYMBOL_SCHEME, "scheme_digest": SYMBOL_SCHEME_DIGEST},
    }


def roles_of(bitmask: int) -> list[str]:
    roles = [name for bit, name in SYMBOL_ROLE_BITS if bitmask & bit]
    if not roles:
        # Measured, not assumed: on the committed fixture index scip-python
        # 0.6.6 sets Definition (1) on definitions and ReadAccess (8) on plain
        # references, so this branch is not the ordinary path. It exists
        # because the frozen occurrence requires at least one role and an
        # occurrence with every bit clear would otherwise be unrepresentable;
        # REFERENCE is what the absence of every access bit means.
        return ["REFERENCE"]
    return roles


def expand_range(raw: list[int]) -> tuple[int, int, int, int]:
    """SCIP packs a single-line range as [line, start_col, end_col] and a
    multi-line one as [start_line, start_col, end_line, end_col]."""
    if len(raw) == 3:
        return raw[0], raw[1], raw[0], raw[2]
    if len(raw) == 4:
        return raw[0], raw[1], raw[2], raw[3]
    raise Refusal("OCCURRENCE_RANGE_UNREADABLE", f"a range of {len(raw)} integers is neither the 3- nor the 4-form")


def byte_range(starts: list[int], size: int, raw: list[int], where: str) -> dict[str, int]:
    start_row, start_col, end_row, end_col = expand_range(raw)
    offsets = []
    for row, column in ((start_row, start_col), (end_row, end_col)):
        if row < 0 or row >= len(starts):
            raise Refusal(
                "OCCURRENCE_RANGE_OUT_OF_SOURCE",
                f"{where}: row {row} is outside the {len(starts)} lines of the indexed blob",
            )
        offset = starts[row] + column
        if offset > size:
            raise Refusal(
                "OCCURRENCE_RANGE_OUT_OF_SOURCE",
                f"{where}: byte {offset} is past the {size}-byte blob",
            )
        offsets.append(offset)
    if offsets[1] < offsets[0]:
        raise Refusal("OCCURRENCE_RANGE_OUT_OF_SOURCE", f"{where}: end byte {offsets[1]} before start {offsets[0]}")
    return {
        "start_byte": offsets[0],
        "end_byte": offsets[1],
        "start_line": start_row + 1,
        "start_column": start_col,
        "end_line": end_row + 1,
        "end_column": end_col,
    }


IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def identifier_of(symbol: str) -> str | None:
    """The bare name the final descriptor of a SCIP symbol carries, when it
    carries one. `.../Pricing#apply().` yields `apply`, `.../apply().(amount)`
    yields `amount`.

    A module or namespace descriptor yields nothing on purpose: its occurrence
    in the source is the dotted import path (`dtcr_fixture.core`), not the
    descriptor's own name (`__init__`), so there is no name here to hold the
    bytes to. Measured against the committed index, not assumed."""
    tail = descriptors_of(symbol)
    if not tail:
        return None
    last = tail.rsplit("/", 1)[-1]
    if not last or last.endswith(":") or last.endswith("/"):
        return None
    if last.endswith(")") and "(" in last:
        last = last[last.rindex("(") + 1: -1]
    else:
        last = last.rstrip("().#").rsplit("#", 1)[-1]
    return last if IDENTIFIER.match(last) else None


def check_range_names_symbol(source: bytes, spans: dict[str, int], symbol: str, where: str) -> None:
    """Read the bytes the occurrence points at and require them to spell the
    symbol's own name.

    Without this the range decoding is only checked for being well formed. A
    row/column arithmetic error, a UTF-16 column read as a byte offset or a
    misread packed range still yields offsets inside the blob, still validates
    against the frozen schema, and points at the wrong text -- and every
    consumer downstream opens the file at the number this adapter wrote."""
    name = identifier_of(symbol)
    if name is None or spans["end_byte"] <= spans["start_byte"]:
        return
    observed = source[spans["start_byte"]: spans["end_byte"]].decode("utf-8", "replace")
    if observed != name:
        raise Refusal(
            "OCCURRENCE_RANGE_OUT_OF_SOURCE",
            f"{where}: bytes {spans['start_byte']}..{spans['end_byte']} read {observed!r}, the symbol "
            f"names {name!r}; the range is inside the blob and points at the wrong text",
        )


# --------------------------------------------------------------------------
# input guards
# --------------------------------------------------------------------------
def check_subject(subject: dict[str, Any]) -> None:
    for key in ("commit", "tree"):
        value = subject.get(key, "")
        if not HEX40.match(value):
            raise Refusal(
                "SCIP_INDEX_WRONG_SUBJECT",
                f"subject.{key}={value!r} is not an exact 40-hex object id; a branch, a tag or HEAD "
                "names a moving tree, and an index dated to a moving tree is dated to nothing",
            )
    if not re.match(r"^DTCR-RB-[0-9a-f]{16}$", subject.get("repository_binding_id", "")):
        raise Refusal(
            "SCIP_INDEX_WRONG_SUBJECT",
            "subject.repository_binding_id must be the opaque binding id; a clone URL, an owner/name "
            "pair or a working-copy path each describe one account or one machine",
        )


def check_index_binding(index: dict[str, Any], provider: dict[str, Any], index_bytes: bytes) -> None:
    declared = provider.get("index_sha256", "")
    if not HEX64.match(str(declared)):
        raise Refusal(
            "SCIP_INDEX_DIGEST_ABSENT",
            "the request declares no sha256 for the index bytes; without it a rerun that disagrees "
            "cannot be told from a rerun over a different index",
        )
    observed = sha256_hex(index_bytes)
    if observed != declared:
        raise Refusal(
            "SCIP_INDEX_DIGEST_ABSENT",
            f"the index bytes hash to {observed}, the request declares {declared}; the facts would be "
            "attributed to an index nobody here read",
        )
    for key in ("version", "indexer_sha256", "config_digest"):
        if not str(provider.get(key, "")).strip():
            raise Refusal(
                "INDEXER_VERSION_OR_CONFIG_UNBOUND",
                f"provider.{key} is empty; two releases of one indexer produce different edges and "
                "record identically when the version, the build or the configuration is unwritten",
            )
    for key in ("indexer_sha256", "config_digest"):
        if not HEX64.match(provider[key]):
            raise Refusal("INDEXER_VERSION_OR_CONFIG_UNBOUND", f"provider.{key} is not a sha256")
    if index["tool_name"] != INDEXER_NAME or index["tool_version"] != provider["version"]:
        raise Refusal(
            "INDEXER_VERSION_OR_CONFIG_UNBOUND",
            f"the index was written by {index['tool_name']!r} {index['tool_version']!r}, the request "
            f"binds {INDEXER_NAME!r} {provider['version']!r}; the identity in the receipt would not be "
            "the identity that produced the facts",
        )
    if not index["documents"]:
        raise Refusal(
            "SCIP_INDEX_EMPTY_OVER_DECLARED_SUBJECT",
            "the index carries no Document at all. Measured on this host: scip-python 0.6.6 exits 0 "
            "and writes a 56-byte metadata-only index when --cwd is reached through a symlink "
            "(/tmp -> /private/tmp, and every mkdtemp path on this platform), because the project "
            "root it records and the real paths it resolves no longer share a prefix. An empty index "
            "is a broken invocation, and reported as a pass it is a clean bill of health for a run "
            "that read nothing",
        )
    if index["text_document_encoding"] != TEXT_ENCODING_UTF8:
        raise Refusal(
            "SCIP_INDEX_ENCODING_UNSUPPORTED",
            f"text_document_encoding={index['text_document_encoding']} is not UTF8; the column numbers "
            "would be UTF-16 code units and every byte offset computed from them would be wrong "
            "wherever the source is not ASCII",
        )


def check_index_subject(index: dict[str, Any], provider: dict[str, Any], subject: dict[str, Any]) -> None:
    indexed_commit = provider.get("indexed_commit", "")
    if not HEX40.match(str(indexed_commit)):
        raise Refusal(
            "SCIP_INDEX_WRONG_SUBJECT",
            "the request records no exact commit the index was built from; the schema requires it "
            "beside the commit the facts are about so that the two can be compared",
        )
    if indexed_commit != subject["commit"]:
        raise Refusal(
            "SCIP_INDEX_WRONG_SUBJECT",
            f"the index was built from {indexed_commit} and the facts are dated to {subject['commit']}; "
            "an index of another tree describes symbols that may not exist in this one",
        )


# --------------------------------------------------------------------------
# post-condition guards -- run on the emit path, planted in selftest.py
# --------------------------------------------------------------------------
def guard_identities(facts: list[dict[str, Any]]) -> None:
    def check(identity: Any, where: str) -> None:
        if not isinstance(identity, dict):
            raise Refusal(
                "PROVIDER_ID_PROMOTED_TO_UNIVERSAL_ID",
                f"{where}: the identity is a bare {type(identity).__name__}; a scip-python identifier "
                "read as a universal node id makes two indexers' rows look like the same node",
            )
        normalization = identity.get("normalization") or {}
        if normalization.get("scheme_digest") != SYMBOL_SCHEME_DIGEST:
            raise Refusal(
                "PROVIDER_ID_PROMOTED_TO_UNIVERSAL_ID",
                f"{where}: the identity carries no normalization scheme this adapter wrote, so the rule "
                "under which the provider's identifier is read is recorded nowhere",
            )

    for fact in facts:
        if "symbol" in fact:
            check(fact["symbol"].get("identity"), f"{fact['fact_id']}.symbol")
        if "occurrence" in fact:
            check(fact["occurrence"].get("identity"), f"{fact['fact_id']}.occurrence")
        if "relationship" in fact:
            check(fact["relationship"].get("from"), f"{fact['fact_id']}.relationship.from")
            check(fact["relationship"].get("to"), f"{fact['fact_id']}.relationship.to")
        if any(fact.get("establishes", {}).values()):
            raise Refusal(
                "SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS",
                f"{fact['fact_id']}: an index row recorded itself as establishing something",
            )


def guard_relationships(facts: list[dict[str, Any]]) -> None:
    for fact in facts:
        if fact.get("fact_kind") != "RELATIONSHIP":
            continue
        evidence = fact["relationship"]["graph_evidence"]
        kind = fact["relationship"]["relationship_kind"]
        if evidence["provenance"] in ("OCCURRENCE_ENCLOSING_RANGE_HEURISTIC", "TEXTUAL_MATCH"):
            if kind in ("CALLS", "IMPLEMENTS", "INHERITS"):
                raise Refusal(
                    "OCCURRENCE_NESTING_PROMOTED_TO_CALL_GRAPH",
                    f"{fact['fact_id']}: an edge obtained by nesting a reference inside a definition "
                    f"range is filed as {kind}; that inference misses dynamic dispatch, reflection and "
                    "callbacks, and naming it a call turns a floor into a ceiling",
                )
            if evidence["completeness"] not in ("PARTIAL_LOWER_BOUND", "UNKNOWN"):
                raise Refusal(
                    "OCCURRENCE_NESTING_PROMOTED_TO_CALL_GRAPH",
                    f"{fact['fact_id']}: a range-nesting edge recorded as {evidence['completeness']}",
                )
        occurrence = fact.get("occurrence")
        if not occurrence or "range" not in occurrence:
            raise Refusal(
                "RELATIONSHIP_WITHOUT_SOURCE_RANGE",
                f"{fact['fact_id']}: an edge with no occurrence behind it; nobody can open the file and "
                "see what the edge was read from, and nobody can tell it from an edge somebody assumed",
            )


def unresolved_sentence(unresolved: int, referenced: int) -> str:
    """The denominator the issue names, written as one sentence so a consumer
    reads the ratio and the set it is over in the same breath. `referenced`
    counts distinct symbols that appear in at least one non-definition
    occurrence -- not every symbol in the index, which would flatter the
    ratio with definitions that were never in question."""
    return (
        f"{unresolved} of the {referenced} distinct symbols that appear in a non-definition "
        "occurrence have no definition occurrence anywhere in this index; they are the unresolved "
        "denominator, and an edge into one of them is bounded by whatever indexed that symbol "
        "elsewhere, which in this run was nothing"
    )


def guard_ceiling(ceiling: dict[str, Any], unresolved: int, referenced: int) -> None:
    if ceiling["omissions"] and ceiling["completeness"] == "COMPLETE_FOR_ANALYSED_INPUTS":
        raise Refusal(
            "PARTIAL_COVERAGE_PROMOTED_TO_COMPLETE",
            f"the ceiling records {len(ceiling['omissions'])} omissions and reports itself complete; a "
            "pass that skipped anything is a lower bound by construction",
        )
    if unresolved and unresolved_sentence(unresolved, referenced) not in ceiling["warnings"]:
        raise Refusal(
            "UNRESOLVED_SYMBOL_OMITTED_FROM_DENOMINATOR",
            f"{unresolved} referenced symbols resolve to no definition in this index and the ceiling "
            "names no denominator for them; downstream they are indistinguishable from symbols that "
            "were resolved and found to have no edges",
        )
    if any(ceiling["authority_ceiling"].values()):
        raise Refusal(
            "SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS",
            "the ceiling cleared something it did not analyse",
        )


def guard_receipt(receipt: dict[str, Any]) -> None:
    granted = sorted(key for key, value in receipt["grants"].items() if value)
    if granted:
        raise Refusal(
            "SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS",
            f"the receipt grants {granted}; scip-python exiting zero is a fact about one process over "
            "one language, and the task it was run for is closed by a closure record that reads this "
            "receipt rather than by the receipt itself",
        )


# --------------------------------------------------------------------------
# emitter
# --------------------------------------------------------------------------
def config_digest_of(pyright_config: bytes) -> str:
    """The invocation, with every machine-local path replaced by its role."""
    return sha256_hex(
        canonical(
            {
                "argv": [
                    EXECUTABLE_NAME,
                    "index",
                    "--cwd",
                    "<PROJECT_ROOT>",
                    "--project-name",
                    PROJECT_NAME,
                    "--project-version",
                    PROJECT_VERSION,
                    "--output",
                    INDEX_BASENAME,
                ],
                "pyrightconfig_digest": sha256_hex(pyright_config),
                "one_project_per_invocation": True,
                # Pinned rather than defaulted: --project-version defaults to the
                # current git revision, which would move the symbol strings of
                # every row on every commit and make two honest runs disagree.
                "project_version_pinned": True,
            }
        )
    )


def emit_facts(
    *,
    subject: dict[str, Any],
    provider: dict[str, Any],
    index_bytes: bytes,
    project_root_prefix: str,
    documents: dict[str, dict[str, Any]],
    omissions: list[dict[str, str]],
    warnings: list[str],
    sequence: int = 1,
) -> dict[str, Any]:
    """`documents` maps an index-relative path to
    {path (repo-relative), blob (git sha1), source (bytes)}."""
    check_subject(subject)
    index = decode_index(index_bytes)
    check_index_binding(index, provider, index_bytes)
    check_index_subject(index, provider, subject)

    index_binding = {
        "indexer_name": INDEXER_NAME,
        "version": provider["version"],
        "indexer_sha256": provider["indexer_sha256"],
        "config_digest": provider["config_digest"],
        "index_digest": sha256_hex(index_bytes),
        "indexed_commit": provider["indexed_commit"],
    }

    indexed_paths = [document["relative_path"] for document in index["documents"]]
    for relative in indexed_paths:
        if relative not in documents:
            raise Refusal(
                "SCIP_INDEX_WRONG_SUBJECT",
                f"the index carries a document for {relative!r}, which the subject never declared; a "
                "fact about a blob the subject does not carry is a fact nobody can resolve",
            )
    for relative, declared in sorted(documents.items()):
        actual = git_blob_sha1(declared["source"])
        if actual != declared["blob"]:
            raise Refusal(
                "STALE_INDEX_REUSED_AFTER_SOURCE_CHANGE",
                f"{declared['path']}: the bytes offered here hash to {actual}, the subject declares "
                f"{declared['blob']}; an index is only about the bytes it read, and reusing it across "
                "an edit reports the old tree's symbols at the new tree's commit",
            )

    # The two ceilings the issue title asks to be made explicit. They are
    # emitted on every run rather than passed in by the caller, because a
    # ceiling a caller can forget is a ceiling that goes missing on the run
    # that needed it. Both are measured on the index actually decoded, not
    # asserted: the relationship count is read off the provider's own
    # SymbolInformation rows, and it is zero for scip-python 0.6.6.
    #
    # They are built here, above the emitter, so that every symbol-fact row
    # carries them too. The frozen symbol-fact schema says an empty omission
    # list is itself a claim -- that nothing was skipped -- and rows shipped
    # with an empty one would make that claim on every symbol in a
    # python-only, edge-derived index.
    #
    # Their presence also fixes `completeness` at PARTIAL_LOWER_BOUND for the
    # life of this adapter -- the frozen ceiling refuses COMPLETE beside a
    # non-empty omission list -- which is the correct reading and is why
    # nothing here computes a COMPLETE branch.
    structural_omissions = [
        {
            "omission_kind": "LANGUAGE_NOT_INSTALLED",
            "detail": (
                "scip-python indexes Python. Every blob of the subject repository in any other "
                "language is outside this run, no indexer for it was installed, and unindexed is "
                "not clean. This bundle is python scope only and carries no cross-language edge."
            ),
        },
        {
            "omission_kind": "PROVIDER_UNSUPPORTED_CONSTRUCT",
            "detail": (
                f"scip-python {provider['version']} emitted {index['provider_relationship_count']} "
                "SymbolInformation.relationships across this index, counted on the decoded bytes, so "
                "no edge in this bundle is compiler-resolved. Every edge was derived here by nesting "
                "a non-definition occurrence inside the smallest definition whose enclosing_range "
                "contains it, which misses dynamic dispatch, getattr, reflection, callbacks, "
                "decorated re-exports and generated code."
            ),
        },
    ]
    all_omissions = structural_omissions + [dict(entry) for entry in omissions]
    omission_details = sorted({entry["detail"] for entry in all_omissions})

    facts: list[dict[str, Any]] = []
    emitted_symbols: set[str] = set()
    defined: set[str] = set()
    referenced: set[str] = set()
    unenclosed_references = 0

    def new_fact(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        fact = {
            "schema": FACT_SCHEMA,
            "fact_id": "DTCR-SY-000",
            "fact_kind": kind,
            "subject": dict(subject),
            "index_binding": dict(index_binding),
            "output_digest": "",
            "warnings": sorted(set(warnings)),
            "omissions": list(omission_details),
            "establishes": {"complete_call_graph": False, "semantic_truth": False, "task_pass": False},
        }
        fact.update(payload)
        return fact

    for document in sorted(index["documents"], key=lambda d: d["relative_path"]):
        relative = document["relative_path"]
        declared = documents[relative]
        source: bytes = declared["source"]
        starts = line_starts(source)
        size = len(source)
        blob_ref = {"path": declared["path"], "blob": declared["blob"]}

        for symbol in sorted(document["symbols"], key=lambda s: s["symbol"]):
            # One row per symbol, not per document that mentions it. The frozen
            # symbol_record has no blob field -- deliberately, a symbol is not
            # located anywhere, its occurrences are -- so two rows for one
            # symbol would be two rows a consumer cannot tell apart, and the
            # SYMBOL count would silently mean "declarations seen" instead.
            if symbol["symbol"] in emitted_symbols:
                continue
            emitted_symbols.add(symbol["symbol"])
            facts.append(
                new_fact(
                    "SYMBOL",
                    {
                        "symbol": {
                            key: value
                            for key, value in (
                                ("identity", identity_of(symbol["symbol"])),
                                ("symbol_kind", symbol_kind_of(symbol["symbol"])),
                                ("display_name", display_name_of(symbol["symbol"], symbol["display_name"])),
                            )
                            if value is not None
                        }
                    },
                )
            )

        # Definition ranges first: an edge is a reference nested in the
        # smallest definition whose enclosing_range contains it, so the
        # enclosing set has to be complete before any reference is placed.
        enclosing: list[tuple[dict[str, int], str]] = []
        for occurrence in document["occurrences"]:
            if occurrence["enclosing_range"]:
                where = f"{declared['path']} {occurrence['symbol']}"
                enclosing.append((byte_range(starts, size, occurrence["enclosing_range"], where), occurrence["symbol"]))

        for occurrence in sorted(document["occurrences"], key=lambda o: (o["range"], o["symbol"])):
            where = f"{declared['path']} {occurrence['symbol']}"
            spans = byte_range(starts, size, occurrence["range"], where)
            check_range_names_symbol(source, spans, occurrence["symbol"], where)
            roles = roles_of(occurrence["symbol_roles"])
            record = {"identity": identity_of(occurrence["symbol"]), "blob": dict(blob_ref), "range": spans, "roles": roles}
            facts.append(new_fact("OCCURRENCE", {"occurrence": record}))
            if "DEFINITION" in roles:
                defined.add(occurrence["symbol"])
                continue
            referenced.add(occurrence["symbol"])

            containers = [
                (span, symbol)
                for span, symbol in enclosing
                if span["start_byte"] <= spans["start_byte"] and spans["end_byte"] <= span["end_byte"]
                and symbol != occurrence["symbol"]
            ]
            if not containers:
                # A reference at module scope -- an import line, a decorator --
                # is inside no definition, so no edge is derivable for it. It is
                # counted rather than dropped: a reference that produced no edge
                # and a reference nobody looked at read identically downstream.
                unenclosed_references += 1
                continue
            span, container = min(containers, key=lambda item: item[0]["end_byte"] - item[0]["start_byte"])
            facts.append(
                new_fact(
                    "RELATIONSHIP",
                    {
                        "relationship": {
                            "from": identity_of(container),
                            "to": identity_of(occurrence["symbol"]),
                            # REFERENCES, never CALLS. What was observed is that
                            # an occurrence of `to` lies inside the definition of
                            # `from`; whether control ever reaches it is not in
                            # the index.
                            "relationship_kind": "REFERENCES",
                            "graph_evidence": {
                                "provenance": "OCCURRENCE_ENCLOSING_RANGE_HEURISTIC",
                                "completeness": "PARTIAL_LOWER_BOUND",
                                "tool": "scip-python occurrence/enclosing-range importer",
                            },
                        },
                        # The occurrence the edge was read from, carried on the
                        # same row so the edge has a byte range somebody can open.
                        "occurrence": copy.deepcopy(record),
                    },
                )
            )

    if len(facts) > 999:
        # ponytail: the frozen fact_id pattern is three digits. Batching by
        # document is the upgrade path if a subject ever needs more.
        raise Refusal("FACT_ID_SPACE_EXHAUSTED", f"{len(facts)} facts exceed the DTCR-SY-999 id space")

    def sort_key(fact: dict[str, Any]) -> tuple[Any, ...]:
        occurrence = fact.get("occurrence") or {}
        blob = (occurrence.get("blob") or {}).get("path", "")
        span = occurrence.get("range") or {}
        return (
            {"SYMBOL": 0, "OCCURRENCE": 1, "RELATIONSHIP": 2}[fact["fact_kind"]],
            blob,
            span.get("start_byte", -1),
            span.get("end_byte", -1),
            canonical(fact.get("symbol") or fact.get("relationship") or {}).decode("utf-8"),
        )

    for index_of_fact, fact in enumerate(sorted(facts, key=sort_key), 1):
        fact["fact_id"] = f"DTCR-SY-{index_of_fact:03d}"
        fact["output_digest"] = sha256_hex(canonical({k: v for k, v in fact.items() if k != "output_digest"}))
    facts.sort(key=lambda f: f["fact_id"])

    unresolved = sorted(referenced - defined)
    provider_binding = binding_id(
        "DTCR-PB",
        canonical(
            [
                EXECUTABLE_NAME,
                provider["version"],
                provider["indexer_sha256"],
                provider["config_digest"],
                index_binding["index_digest"],
                SYMBOL_SCHEME_DIGEST,
            ]
        ),
    )

    edge_count = sum(1 for fact in facts if fact["fact_kind"] == "RELATIONSHIP")
    ceiling_warnings = sorted(
        set(warnings)
        | {
            unresolved_sentence(len(unresolved), len(referenced)),
            f"{edge_count} edges were derived from occurrence nesting and {unenclosed_references} "
            "non-definition occurrences lie inside no definition range and produced none; the "
            "provider itself emitted "
            f"{index['provider_relationship_count']} relationships, so no edge here is compiler-resolved",
            "the denominator beside this warning counts indexed documents; it says nothing about how "
            "many symbols, edges or bytes of those documents the indexer resolved",
        }
    )
    # The subject as its own record, so a consumer that reads only one document
    # of this bundle still gets the exact commit, tree and blob list the facts
    # are about rather than the tree it imagines. NO_DIFF_SUBJECT because an
    # index run is over a whole project root, not over a change.
    source_subject = {
        "schema": "dtcr/exact-source-subject/v1",
        "subject_id": "DTCR-SS-001",
        "repository_binding_id": subject["repository_binding_id"],
        "commit": subject["commit"],
        "tree": subject["tree"],
        "blobs": [
            {"path": entry["path"], "blob": entry["blob"], "byte_count": len(entry["source"])}
            for entry in sorted(documents.values(), key=lambda e: e["path"])
        ],
        "diff": "NO_DIFF_SUBJECT",
        "authority_ceiling": {
            "semantic_truth": False,
            "complete_account_of_behaviour": False,
            "task_pass": False,
            "merge": False,
        },
    }

    ceiling = {
        "schema": CEILING_SCHEMA,
        "ceiling_id": "DTCR-CC-001",
        "subject": dict(subject),
        "provider_binding_id": provider_binding,
        "analysed": {
            "numerator": len(indexed_paths),
            "denominator": len(documents),
            "denominator_definition": (
                f"python source blobs under {project_root_prefix} declared by the exact source subject "
                "and offered to this indexer run"
            ),
            "method": (
                "one scip-python index invocation over the declared project root at the pinned "
                "pyrightconfig digest, one document per declared blob"
            ),
        },
        "completeness": "PARTIAL_LOWER_BOUND",
        "omissions": all_omissions,
        "warnings": ceiling_warnings,
        "authority_ceiling": {
            "unanalysed_inputs_cleared": False,
            "semantic_completeness": False,
            "task_pass": False,
        },
    }

    bundle_body = {"facts": facts, "exact_source_subject": source_subject, "coverage_ceiling": ceiling}
    bundle_digest = sha256_hex(canonical(bundle_body))
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": "DTCR-FR-001",
        "subject": dict(subject),
        "arrival": "STATIC",
        "provider_runs": [
            {
                "provider_binding_id": provider_binding,
                "executable_name": EXECUTABLE_NAME,
                "version": provider["version"],
                "executable_sha256": provider["indexer_sha256"],
                "config_digest": provider["config_digest"],
                "input_digest": sha256_hex(
                    canonical(sorted((entry["path"], entry["blob"]) for entry in documents.values()))
                ),
                "output_digest": index_binding["index_digest"],
                "exit_code": provider.get("exit_code", 0),
                "outcome": "PASS" if provider.get("exit_code", 0) == 0 else "FAIL",
                "warnings": sorted(
                    set(warnings)
                    | {
                        f"{len(unresolved)} referenced symbols resolve to no definition in this index; "
                        f"{unenclosed_references} non-definition occurrences lie inside no definition "
                        "range and produced no edge"
                    }
                ),
                "omissions": sorted(
                    set(omission_details)
                    | {
                        "this adapter writes no canonical ledger row: ledger_event carries the emitted "
                        "bundle digest and this run's own sequence, not an allocation from a ledger"
                    }
                ),
            }
        ],
        "ledger_event": {
            "event_digest": bundle_digest,
            "sequence": sequence,
            "ledger_schema_digest": sha256_hex((SCHEMAS / "fact-plane-receipt.schema.json").read_bytes()),
        },
        "bundle_digest": bundle_digest,
        "coverage_ceiling_ref": ceiling["ceiling_id"],
        "summary": (
            f"scip-python {provider['version']} indexed {len(indexed_paths)} of {len(documents)} declared "
            f"python blobs and yielded {len(facts)} rows: "
            f"{sum(1 for f in facts if f['fact_kind'] == 'SYMBOL')} symbols, "
            f"{sum(1 for f in facts if f['fact_kind'] == 'OCCURRENCE')} occurrences and {edge_count} "
            f"range-nesting edges, with {len(unresolved)} referenced symbols left unresolved. "
            "Python scope only; no edge here is compiler-resolved."
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

    guard_identities(facts)
    guard_relationships(facts)
    guard_ceiling(ceiling, len(unresolved), len(referenced))
    guard_receipt(receipt)
    return {
        "facts": facts,
        "exact_source_subject": source_subject,
        "coverage_ceiling": ceiling,
        "receipt": receipt,
        "index_summary": {
            "project_root_is_machine_local": True,
            "documents": len(indexed_paths),
            "provider_relationships": index["provider_relationship_count"],
            "external_symbols": len(index["external_symbols"]),
            "unresolved_symbols": unresolved,
            "referenced_symbols": len(referenced | defined),
            "unenclosed_references": unenclosed_references,
        },
    }


def facts_digest_modulo_subject(facts: list[dict[str, Any]]) -> str:
    """The part of an emission a second host can reproduce.

    The subject commit and the index digest are in every row, and the index
    digest moves with the absolute project root the indexer recorded, so two
    honest runs over the same bytes at two checkouts agree on nothing
    whole-record. Stripping both leaves what the indexer actually determined:
    the same bundle, the same config and the same sources produce this digest
    anywhere."""
    stripped = []
    for fact in facts:
        copied = {key: value for key, value in fact.items() if key not in ("subject", "output_digest")}
        binding = dict(copied["index_binding"])
        binding.pop("index_digest", None)
        binding.pop("indexed_commit", None)
        copied["index_binding"] = binding
        stripped.append(copied)
    return sha256_hex(canonical(stripped))


# --------------------------------------------------------------------------
# replay mode
# --------------------------------------------------------------------------
def run_replay(request_path: Path) -> dict[str, Any]:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if request.get("schema") != REQUEST_SCHEMA:
        raise Refusal("REQUEST_SCHEMA_UNKNOWN", f"{request_path.name}: schema {request.get('schema')!r}")
    base = request_path.parent
    documents = {
        relative: {
            "path": f"{request['project_root_prefix']}/{relative}",
            "blob": entry["blob"],
            "source": (base / entry["source"]).read_bytes(),
        }
        for relative, entry in request["documents"].items()
    }
    return emit_facts(
        subject=request["subject"],
        provider=request["provider"],
        index_bytes=(base / request["index"]).read_bytes(),
        project_root_prefix=request["project_root_prefix"],
        documents=documents,
        omissions=request.get("omissions", []),
        warnings=request.get("warnings", []),
        sequence=request.get("sequence", 1),
    )


# --------------------------------------------------------------------------
# live mode
# --------------------------------------------------------------------------
def find_cli() -> str | None:
    explicit = os.environ.get("DTCR_SCIP_BIN")
    if explicit:
        return explicit if Path(explicit).is_file() else None
    return shutil.which(EXECUTABLE_NAME)


def package_files(binary: str) -> list[Path]:
    """The launcher plus the bundle it loads. `index.js` on its own is a 1.4 KB
    shim that is byte-identical across releases, so a digest of it would report
    two different indexers as one."""
    entry = Path(binary).resolve()
    dist = entry.parent / "dist"
    return [entry] + sorted(path for path in dist.glob("*.js")) if dist.is_dir() else [entry]


def cli_identity(binary: str) -> dict[str, str]:
    version = subprocess.run([binary, "--version"], capture_output=True, text=True, check=True).stdout.strip()
    files = package_files(binary)
    listing = "".join(f"{sha256_hex(path.read_bytes())}  {path.name}\n" for path in files)
    return {
        "version": version,
        "indexer_sha256": sha256_hex(listing.encode("utf-8")),
        "indexer_digest_definition": (
            f"sha256 over the canonical `sha256  name` listing of the {len(files)} installed package "
            "files that run: the launcher and every bundle beside it"
        ),
        "entry_sha256": sha256_hex(files[0].read_bytes()),
    }


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def live_subject(repo: Path, paths: list[str]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    commit = git(repo, "rev-parse", "HEAD")
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    root = git(repo, "rev-list", "--max-parents=0", "HEAD").splitlines()[-1]
    subject = {
        # Opaque and stable: the root commit identifies this repository without
        # naming a remote, an owner or a checkout directory.
        "repository_binding_id": binding_id("DTCR-RB", root.encode("ascii")),
        "commit": commit,
        "tree": tree,
    }
    declared: dict[str, dict[str, Any]] = {}
    for path in paths:
        try:
            recorded = git(repo, "rev-parse", f"HEAD:{path}")
        except subprocess.CalledProcessError as error:
            raise Refusal(
                "SUBJECT_PATH_ABSENT",
                f"{path} is not in the tree at {commit}; a live index over an uncommitted file has no "
                "exact subject to be about",
            ) from error
        data = (repo / path).read_bytes()
        if git_blob_sha1(data) != recorded:
            raise Refusal(
                "STALE_INDEX_REUSED_AFTER_SOURCE_CHANGE",
                f"{path} in the working tree differs from the blob at {commit}; the subject would name "
                "a commit and the indexer would read something else",
            )
        declared[path] = {"blob": recorded, "source": data}
    return subject, declared


def run_live(
    *,
    repo: Path,
    package_dir: Path,
    omissions: list[dict[str, str]],
    warnings: list[str],
    record_dir: Path | None = None,
    receipt_path: Path | None = None,
) -> dict[str, Any]:
    binary = find_cli()
    if binary is None:
        raise Refusal("PROVIDER_ABSENT", f"no {EXECUTABLE_NAME} executable on PATH and DTCR_SCIP_BIN unset")
    prefix = str(package_dir.relative_to(repo))
    config_bytes = (package_dir / "pyrightconfig.json").read_bytes()
    sources = sorted(str(path.relative_to(repo)) for path in package_dir.rglob("*.py"))
    subject, declared = live_subject(repo, sources + [f"{prefix}/pyrightconfig.json"])
    identity = cli_identity(binary)

    # The indexer runs against a scratch copy rather than the checkout. Two
    # reasons, both load-bearing: `--output` is joined onto `--cwd`, so a live
    # run against the tree would write an artifact into the subject it is
    # indexing; and running from a path that is not this checkout is what shows
    # the emitted facts do not carry the machine the indexer ran on.
    #
    # `.resolve()` is not tidiness. mkdtemp returns /var/folders/... on this
    # platform and /var is a symlink to /private/var, and scip-python handed a
    # symlinked --cwd exits 0 having written a metadata-only index with zero
    # documents. Passing the resolved path is the whole difference between a
    # real index and a silent empty one; the guard in check_index_binding is
    # the second, independent arrival on the same failure.
    with tempfile.TemporaryDirectory(prefix="dtcr-scip-live-") as scratch:
        root = Path(scratch).resolve() / "project"
        for path, entry in declared.items():
            target = root / Path(path).relative_to(prefix)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(entry["source"])
        run = subprocess.run(
            [
                binary,
                "index",
                "--cwd",
                str(root),
                "--project-name",
                PROJECT_NAME,
                "--project-version",
                PROJECT_VERSION,
                "--output",
                INDEX_BASENAME,
                "--quiet",
            ],
            capture_output=True,
            text=True,
        )
        index_path = root / INDEX_BASENAME
        if run.returncode != 0 or not index_path.is_file():
            raise Refusal(
                "PROVIDER_INVOCATION_FAILED",
                f"{EXECUTABLE_NAME} index exited {run.returncode} and left "
                f"{'no' if not index_path.is_file() else 'an'} index; that is a broken invocation, not "
                f"an empty project. stderr: {run.stderr.strip()[:400]}",
            )
        index_bytes = index_path.read_bytes()

    provider = {
        "version": identity["version"],
        "indexer_sha256": identity["indexer_sha256"],
        "config_digest": config_digest_of(config_bytes),
        "index_sha256": sha256_hex(index_bytes),
        "indexed_commit": subject["commit"],
        "exit_code": run.returncode,
    }
    documents = {
        str(Path(path).relative_to(prefix)): {"path": path, "blob": entry["blob"], "source": entry["source"]}
        for path, entry in declared.items()
        if path.endswith(".py")
    }
    bundle = emit_facts(
        subject=subject,
        provider=provider,
        index_bytes=index_bytes,
        project_root_prefix=prefix,
        documents=documents,
        omissions=omissions,
        warnings=warnings + ["live provider run: scip-python indexed the subject blobs on this host"],
    )
    if record_dir is not None:
        write_fixture(record_dir, repo, prefix, subject, provider, documents, index_bytes, omissions)
    if receipt_path is not None:
        write_live_receipt(receipt_path, bundle, identity, provider, binary, sorted(documents))
    return bundle


def write_live_receipt(
    receipt_path: Path,
    bundle: dict[str, Any],
    identity: dict[str, str],
    provider: dict[str, Any],
    binary: str,
    documents: list[str],
) -> None:
    """What one real execution on one host observed.

    The install path is deliberately absent: a path describes one machine, and a
    receipt that pinned this adapter to a checkout would be replayed nowhere.
    The listing digest of the installed package is the identity that travels."""
    binding = bundle["facts"][0]["index_binding"]
    summary = bundle["index_summary"]
    node = subprocess.run(["node", "--version"], capture_output=True, text=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": LIVE_RECEIPT_SCHEMA,
        "subject": bundle["receipt"]["subject"],
        "documents": documents,
        "provider": {
            "provider_binding_id": bundle["coverage_ceiling"]["provider_binding_id"],
            "executable_name": EXECUTABLE_NAME,
            "version": binding["version"],
            "indexer_sha256": binding["indexer_sha256"],
            "indexer_digest_definition": identity["indexer_digest_definition"],
            "entry_sha256": identity["entry_sha256"],
            "executable_location": (
                "resolved from DTCR_SCIP_BIN or PATH; the install path is one machine and is not part "
                "of the identity"
            ),
            "config_digest": binding["config_digest"],
            "host_runtime": node.stdout.strip() or "NOT_MEASURED",
            "symbol_scheme_digest": SYMBOL_SCHEME_DIGEST,
        },
        "index": {
            "index_digest": binding["index_digest"],
            "index_digest_is_host_local": (
                "Index.metadata.project_root is an absolute file:// URL of the directory the indexer "
                "ran in, so this digest identifies one run on one machine and two honest runs over the "
                "same bytes disagree on it. facts_digest_modulo_subject is the comparable one."
            ),
            "indexed_commit": binding["indexed_commit"],
            "provider_emitted_relationships": summary["provider_relationships"],
            "external_symbols": summary["external_symbols"],
        },
        "subject_blobs": {
            fact["occurrence"]["blob"]["path"]: fact["occurrence"]["blob"]["blob"]
            for fact in bundle["facts"]
            if "occurrence" in fact
        },
        "facts_digest_modulo_subject": facts_digest_modulo_subject(bundle["facts"]),
        "facts": {
            "total": len(bundle["facts"]),
            "symbols": sum(1 for f in bundle["facts"] if f["fact_kind"] == "SYMBOL"),
            "occurrences": sum(1 for f in bundle["facts"] if f["fact_kind"] == "OCCURRENCE"),
            "relationships": sum(1 for f in bundle["facts"] if f["fact_kind"] == "RELATIONSHIP"),
            "unresolved_symbols": summary["unresolved_symbols"],
            "referenced_symbols": summary["referenced_symbols"],
            "unenclosed_references": summary["unenclosed_references"],
        },
        "coverage": bundle["coverage_ceiling"]["analysed"],
        "completeness": bundle["coverage_ceiling"]["completeness"],
        "exit_codes": {"index": provider["exit_code"]},
        "establishes": {
            "complete_call_graph": False,
            "cross_language_coverage": False,
            "semantic_truth": False,
            "task_pass": False,
            "merge": False,
            "provider_available_elsewhere": False,
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_fixture(
    record_dir: Path,
    repo: Path,
    prefix: str,
    subject: dict[str, Any],
    provider: dict[str, Any],
    documents: dict[str, dict[str, Any]],
    index_bytes: bytes,
    omissions: list[dict[str, str]],
) -> None:
    """Freeze one live run as a replayable fixture: the index bytes exactly as
    the indexer wrote them, and a request that points back at the committed
    sources rather than copying them.

    The source pointers are relative to the request file, not to the repository
    root, because that is where `run_replay` resolves them from. A pointer
    relative to anything else resolves to a path that does not exist and the
    replay dies on an OSError rather than on a named refusal."""
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / INDEX_BASENAME).write_bytes(index_bytes)
    request = {
        "schema": REQUEST_SCHEMA,
        "subject": subject,
        "index": INDEX_BASENAME,
        "project_root_prefix": prefix,
        "provider": {key: provider[key] for key in ("version", "indexer_sha256", "config_digest", "index_sha256", "indexed_commit", "exit_code")},
        "documents": {
            relative: {"source": os.path.relpath(repo / entry["path"], record_dir), "blob": entry["blob"]}
            for relative, entry in sorted(documents.items())
        },
        "omissions": omissions,
        "warnings": [
            "recorded-index replay: the indexer did not run in this pass; these are the bytes a real "
            "scip-python run wrote against the subject commit named above, and the absolute "
            "project_root inside them is the recording host's scratch directory, excluded from every "
            "digest this adapter compares across hosts"
        ],
    }
    (record_dir / "request.json").write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)

    replay = sub.add_parser("replay", help="emit from a recorded index, no indexer needed")
    replay.add_argument("request", type=Path)
    replay.add_argument("--out", type=Path)

    live = sub.add_parser("live", help="run the scip-python indexer against the subject commit")
    live.add_argument("--package", type=Path, required=True)
    live.add_argument("--repo", type=Path, default=Path.cwd())
    live.add_argument("--omit", action="append", default=[], help="KIND:detail")
    live.add_argument("--warn", action="append", default=[])
    live.add_argument("--record", type=Path)
    live.add_argument("--receipt", type=Path)
    live.add_argument("--out", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.mode == "replay":
            bundle = run_replay(args.request)
        else:
            omissions = []
            for item in args.omit:
                kind, _, detail = item.partition(":")
                omissions.append({"omission_kind": kind, "detail": detail})
            bundle = run_live(
                repo=args.repo.resolve(),
                package_dir=args.package.resolve(),
                omissions=omissions,
                warnings=list(args.warn),
                record_dir=args.record.resolve() if args.record else None,
                receipt_path=args.receipt.resolve() if args.receipt else None,
            )
    except Refusal as refusal:
        if refusal.reason == "PROVIDER_ABSENT":
            print(f"NOT_EXERCISED {refusal}", file=sys.stderr)
            return 70
        print(f"REFUSED {refusal}", file=sys.stderr)
        return 2
    text = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
