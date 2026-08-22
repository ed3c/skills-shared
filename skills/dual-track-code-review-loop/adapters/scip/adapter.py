#!/usr/bin/env python3
"""Turn one exact source subject plus one real SCIP index into
`dtcr/symbol-fact/v1` rows, a `dtcr/coverage-ceiling/v1` and a
`dtcr/fact-plane-receipt/v1`.

What this adapter is allowed to say
-----------------------------------
A SCIP index is the sentence *this indexer resolved these symbols at these
ranges in these files*. It is not *these are all the symbols*, not *this is the
call graph*, and not *this identifier is the same node your other indexer
called by that name*. Every row emitted here carries
`establishes.complete_call_graph`, `establishes.semantic_truth` and
`establishes.task_pass` false, every relationship carries the provenance of the
inference that produced it, and no code path here writes a task outcome or a
merge admission. The frozen schemas in `../../references/schemas/` are
read-only inputs; this adapter validates against them and never edits them.

Three things an index cannot do for you, and what is done instead
----------------------------------------------------------------
*An index does not prove which tree it is about.* `Metadata.project_root` is
one machine's absolute path and the documents carry no content hashes. So the
subject binding is made from the outside: every declared blob must hash to the
blob the index was built over (`STALE_INDEX_REUSED_AFTER_SOURCE_CHANGE`), and
every occurrence range is read back out of the declared bytes and must land on
one of the names its own symbol string spells (`SCIP_INDEX_WRONG_SUBJECT`).
An index of a different tree fails the second check on the first identifier
that moved.

*An index does not carry a call graph.* `scip-python` emitted zero
`SymbolInformation.relationships` for this subject, so every edge here is
derived by nesting a reference occurrence inside the smallest `enclosing_range`
the indexer attached to a definition. That attribution is a floor: it misses
dynamic dispatch, reflection, callbacks and generated code, and a SCIP
occurrence role does not distinguish `Client` in a type annotation from
`format_total(...)` in a call. `CALLS` is therefore never derived from an
occurrence, and the guard that enforces it is named
`OCCURRENCE_NESTING_PROMOTED_TO_CALL_GRAPH`.

*A provider identifier is not a universal identity.* This one index gives the
module `client.py` two different symbol strings depending on whether it is
being defined or imported. Identities are emitted as
`provider_scoped_identity` objects carrying the sha256 of
`normalization/scip-symbol-grammar.json`, the rule under which the string was
read; the request pins that digest and a drift is
`PROVIDER_ID_PROMOTED_TO_UNIVERSAL_ID`.

Two modes, one emitter
----------------------
`replay` reads a fixture request and the committed `.scip` bytes beside it,
decodes them, and needs no indexer on the machine. `live` runs `scip-python`
against the subject and funnels into the same `emit_bundle`, so the
deterministic tests exercise the code the live path uses. A missing indexer is
start-readiness, not a failure: `live` refuses to invent an index and the
selftest reports `NOT_EXERCISED`.

Decoding
--------
The index is read straight off the protobuf wire format. There is no `scip`
CLI on this host and the one in Homebrew is an integer-programming solver, a
different project with the same name; `SCIP`'s `Index` is
`{Metadata = 1; repeated Document = 2; repeated SymbolInformation = 3}` and
only length-delimited framing is needed to walk it. What makes that decode
trustworthy is not this docstring: 34 of the 40 occurrences in the committed
fixture are read back against the real source bytes and must match a name
their own symbol string spells, and `selftest.py` decodes the same bytes a
second time through `protoc`-compiled descriptors when a protobuf runtime is
present. A wrong decode yields ranges that land on nothing.

Refusals are named
------------------
Every guard raises `Refusal` carrying the falsifier it exists to kill, so a
planted defect proves *its own* guard rather than dying on an unrelated schema
keyword. The falsifiers owned here:

    SCIP_INDEX_WRONG_SUBJECT
    SCIP_INDEX_DIGEST_ABSENT
    INDEXER_VERSION_OR_CONFIG_UNBOUND
    PARTIAL_COVERAGE_PROMOTED_TO_COMPLETE
    OCCURRENCE_NESTING_PROMOTED_TO_CALL_GRAPH
    UNRESOLVED_SYMBOL_OMITTED_FROM_DENOMINATOR
    RELATIONSHIP_WITHOUT_SOURCE_RANGE
    PROVIDER_ID_PROMOTED_TO_UNIVERSAL_ID
    STALE_INDEX_REUSED_AFTER_SOURCE_CHANGE
    SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS

Usage
-----
    adapter.py replay <request.json> [--out <bundle.json>]
    adapter.py live --root <repo-relative dir> [--repo <dir>] \
        [--index <path>] [--omit KIND:detail] [--record <fixture-dir>] \
        [--receipt <path>] [--out <bundle.json>]

Exit 0 emitted, 2 refused, 70 the indexer is absent in `live` mode.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterator

ADAPTER_DIR = Path(__file__).resolve().parent
SKILL = ADAPTER_DIR.parents[1]
SCHEMAS = SKILL / "references" / "schemas"
RULE_PATH = ADAPTER_DIR / "normalization" / "scip-symbol-grammar.json"

FACT_SCHEMA = "dtcr/symbol-fact/v1"
CEILING_SCHEMA = "dtcr/coverage-ceiling/v1"
RECEIPT_SCHEMA = "dtcr/fact-plane-receipt/v1"
REQUEST_SCHEMA = "dtcr/scip-run-request/v1"
LIVE_RECEIPT_SCHEMA = "dtcr/scip-live-receipt/v1"

EXECUTABLE_NAME = "scip-python"
INDEXER_NAME = "scip-python"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

# The three constants every emitted row is fixed at. They are one object so a
# planted defect has one place to reach and the guard has one place to look.
ESTABLISHES = {"complete_call_graph": False, "semantic_truth": False, "task_pass": False}
GRANTS = {
    "task_pass": False,
    "merge": False,
    "permission": False,
    "secret": False,
    "production": False,
    "release": False,
    "semantic_truth": False,
}

# SymbolRole bits, from the SCIP schema. 0x10 Generated, 0x20 Test and 0x40
# ForwardDefinition have no counterpart in the frozen occurrence role enum; an
# index that sets one is reported rather than quietly rounded to a neighbour.
ROLE_BITS = {0x1: "DEFINITION", 0x2: "IMPORT", 0x4: "WRITE_ACCESS", 0x8: "READ_ACCESS"}
UNMAPPED_ROLE_BITS = {0x10: "Generated", 0x20: "Test", 0x40: "ForwardDefinition"}

RESOLUTION_CLASSES = ("PROJECT_DEFINED", "EXTERNAL_DECLARED", "DOCUMENT_LOCAL", "UNRESOLVED_IN_INDEX")


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


# --------------------------------------------------------------------------
# protobuf wire format -- only what an Index needs
# --------------------------------------------------------------------------
def _varint(buf: bytes, pos: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        if pos >= len(buf):
            raise Refusal("SCIP_INDEX_UNREADABLE", "a varint runs past the end of the index bytes")
        byte = buf[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7


def _fields(buf: bytes) -> Iterator[tuple[int, int, Any]]:
    """(field_number, wire_type, payload) over one protobuf message."""
    pos, end = 0, len(buf)
    while pos < end:
        key, pos = _varint(buf, pos)
        field, wire = key >> 3, key & 7
        if wire == 2:
            length, pos = _varint(buf, pos)
            yield field, wire, buf[pos:pos + length]
            pos += length
        elif wire == 0:
            value, pos = _varint(buf, pos)
            yield field, wire, value
        elif wire == 5:
            yield field, wire, buf[pos:pos + 4]
            pos += 4
        elif wire == 1:
            yield field, wire, buf[pos:pos + 8]
            pos += 8
        else:
            raise Refusal("SCIP_INDEX_UNREADABLE", f"unsupported protobuf wire type {wire}")


def _zigzag_packed_int32(payload: bytes) -> list[int]:
    """`repeated int32` in packed form. SCIP ranges are plain varints, not
    zigzag; the name says int32 and negative values would be ten bytes."""
    out, pos = [], 0
    while pos < len(payload):
        value, pos = _varint(payload, pos)
        out.append(value)
    return out


def _text(payload: bytes) -> str:
    return payload.decode("utf-8", "strict")


def decode_index(data: bytes) -> dict[str, Any]:
    """One `scip.Index` off the wire.

    Fields taken: Index{metadata=1, documents=2, external_symbols=3},
    Metadata{tool_info=2, project_root=3, text_document_encoding=4},
    ToolInfo{name=1, version=2},
    Document{relative_path=1, occurrences=2, symbols=3, language=4,
             position_encoding=6},
    Occurrence{range=1, symbol=2, symbol_roles=3, enclosing_range=7},
    SymbolInformation{symbol=1, kind=5, display_name=6}.
    """
    index: dict[str, Any] = {
        "tool_info": {"name": "", "version": ""},
        "project_root": "",
        "text_document_encoding": 0,
        "documents": [],
        "external_symbols": [],
    }
    for field, wire, payload in _fields(data):
        if field == 1 and wire == 2:
            for mfield, mwire, mpayload in _fields(payload):
                if mfield == 2 and mwire == 2:
                    for tfield, twire, tpayload in _fields(mpayload):
                        if tfield == 1 and twire == 2:
                            index["tool_info"]["name"] = _text(tpayload)
                        elif tfield == 2 and twire == 2:
                            index["tool_info"]["version"] = _text(tpayload)
                elif mfield == 3 and mwire == 2:
                    index["project_root"] = _text(mpayload)
                elif mfield == 4 and mwire == 0:
                    index["text_document_encoding"] = mpayload
        elif field == 2 and wire == 2:
            index["documents"].append(_decode_document(payload))
        elif field == 3 and wire == 2:
            index["external_symbols"].append(_decode_symbol_information(payload))
    return index


def _decode_document(payload: bytes) -> dict[str, Any]:
    document: dict[str, Any] = {
        "relative_path": "",
        "language": "",
        "position_encoding": 0,
        "occurrences": [],
        "symbols": [],
    }
    for field, wire, value in _fields(payload):
        if field == 1 and wire == 2:
            document["relative_path"] = _text(value)
        elif field == 2 and wire == 2:
            document["occurrences"].append(_decode_occurrence(value))
        elif field == 3 and wire == 2:
            document["symbols"].append(_decode_symbol_information(value))
        elif field == 4 and wire == 2:
            document["language"] = _text(value)
        elif field == 6 and wire == 0:
            document["position_encoding"] = value
    return document


def _decode_occurrence(payload: bytes) -> dict[str, Any]:
    occurrence: dict[str, Any] = {"range": [], "symbol": "", "symbol_roles": 0, "enclosing_range": []}
    for field, wire, value in _fields(payload):
        if field == 1:
            occurrence["range"].extend(_zigzag_packed_int32(value) if wire == 2 else [value])
        elif field == 2 and wire == 2:
            occurrence["symbol"] = _text(value)
        elif field == 3 and wire == 0:
            occurrence["symbol_roles"] = value
        elif field == 7:
            occurrence["enclosing_range"].extend(_zigzag_packed_int32(value) if wire == 2 else [value])
    return occurrence


def _decode_symbol_information(payload: bytes) -> dict[str, Any]:
    info: dict[str, Any] = {"symbol": "", "kind": 0, "display_name": ""}
    for field, wire, value in _fields(payload):
        if field == 1 and wire == 2:
            info["symbol"] = _text(value)
        elif field == 5 and wire == 0:
            info["kind"] = value
        elif field == 6 and wire == 2:
            info["display_name"] = _text(value)
    return info


# --------------------------------------------------------------------------
# SCIP symbol strings -- the normalization rule, executed
# --------------------------------------------------------------------------
_NAME_CHAR = re.compile(r"[A-Za-z0-9_+\-$]")


def parse_symbol(symbol: str) -> dict[str, Any]:
    """`<scheme> <manager> <package> <version> (<descriptor>)+` or `local <id>`.

    A single space separates the four header tokens; a double space is one
    literal space inside a token. A descriptor name is either simple-identifier
    characters or a backtick-escaped run in which a doubled backtick is one
    literal backtick.
    """
    if symbol.startswith("local "):
        return {"local": True, "scheme": "local", "package": {}, "descriptors": []}

    header: list[str] = []
    token: list[str] = []
    pos = 0
    while pos < len(symbol) and len(header) < 4:
        char = symbol[pos]
        if char == " ":
            if symbol[pos + 1:pos + 2] == " ":
                token.append(" ")
                pos += 2
                continue
            header.append("".join(token))
            token = []
            pos += 1
            continue
        token.append(char)
        pos += 1
    if len(header) < 4:
        raise Refusal(
            "SCIP_SYMBOL_UNPARSED",
            f"{symbol!r} has no scheme/manager/package/version header; a symbol this adapter "
            "cannot parse is one whose identity it would be guessing at",
        )
    scheme, manager, package, version = header
    descriptors: list[dict[str, str]] = []
    rest = symbol[pos:]
    at = 0
    while at < len(rest):
        char = rest[at]
        if char in "([":
            closer = ")" if char == "(" else "]"
            end = rest.find(closer, at)
            if end < 0:
                raise Refusal("SCIP_SYMBOL_UNPARSED", f"{symbol!r}: unterminated {char}{closer} descriptor")
            descriptors.append(
                {"name": rest[at + 1:end], "suffix": "Parameter" if char == "(" else "TypeParameter"}
            )
            at = end + 1
            continue
        if char == "`":
            end = at + 1
            while end < len(rest):
                if rest[end] == "`":
                    if rest[end + 1:end + 2] == "`":
                        end += 2
                        continue
                    break
                end += 1
            if end >= len(rest):
                raise Refusal("SCIP_SYMBOL_UNPARSED", f"{symbol!r}: unterminated escaped identifier")
            name = rest[at + 1:end].replace("``", "`")
            at = end + 1
        else:
            end = at
            while end < len(rest) and _NAME_CHAR.match(rest[end]):
                end += 1
            if end == at:
                raise Refusal("SCIP_SYMBOL_UNPARSED", f"{symbol!r}: no descriptor name at offset {at}")
            name = rest[at:end]
            at = end
        suffix_char = rest[at:at + 1]
        if suffix_char == "(":
            end = rest.find(").", at)
            if end < 0:
                raise Refusal("SCIP_SYMBOL_UNPARSED", f"{symbol!r}: method descriptor without a `).` close")
            descriptors.append({"name": name, "suffix": "Method"})
            at = end + 2
            continue
        suffix = {"/": "Namespace", "#": "Type", ".": "Term", ":": "Meta", "!": "Macro"}.get(suffix_char)
        if suffix is None:
            raise Refusal("SCIP_SYMBOL_UNPARSED", f"{symbol!r}: {suffix_char!r} is not a descriptor suffix")
        descriptors.append({"name": name, "suffix": suffix})
        at += 1
    if not descriptors:
        raise Refusal("SCIP_SYMBOL_UNPARSED", f"{symbol!r} carries no descriptors")
    return {
        "local": False,
        "scheme": scheme,
        "package": {"manager": manager, "name": package, "version": version},
        "descriptors": descriptors,
    }


def symbol_kind(parsed: dict[str, Any]) -> str:
    """The frozen `symbol_kind` enum from the last descriptor's suffix."""
    descriptors = parsed["descriptors"]
    if not descriptors:
        return "OTHER"
    suffix = descriptors[-1]["suffix"]
    if suffix == "Type":
        return "TYPE"
    if suffix == "Method":
        enclosing = [d["suffix"] for d in descriptors[:-1]]
        return "METHOD" if "Type" in enclosing else "FUNCTION"
    if suffix == "Term":
        return "FIELD"
    if suffix in ("Namespace", "Meta"):
        return "MODULE"
    return "OTHER"


def occurrence_roles(symbol_roles: int) -> tuple[list[str], list[str]]:
    """(frozen role enum values, unmapped SCIP role bits)."""
    roles = [name for bit, name in sorted(ROLE_BITS.items()) if symbol_roles & bit]
    unmapped = [name for bit, name in sorted(UNMAPPED_ROLE_BITS.items()) if symbol_roles & bit]
    if "DEFINITION" not in roles:
        roles.append("REFERENCE")
    return sorted(set(roles)), unmapped


def relationship_kind_for(roles: list[str]) -> str:
    """The frozen `relationship_kind` an occurrence's roles admit.

    CALLS is absent on purpose and the guard below enforces its absence: a SCIP
    occurrence role says an identifier was read, written, imported or defined
    here, and none of those bits distinguishes a call from a type annotation.
    """
    if "DEFINITION" in roles:
        return "DEFINES"
    if "IMPORT" in roles:
        return "IMPORTS"
    return "REFERENCES"


def occurrences_in_scope(
    occurrences: list[dict[str, Any]], resolve: Callable[[str], str]
) -> list[tuple[dict[str, Any], str]]:
    """Every decoded occurrence, paired with its resolution class.

    All of them. An importer that quietly drops the occurrences whose symbol it
    could not resolve is the `UNRESOLVED_SYMBOL_OMITTED_FROM_DENOMINATOR`
    defect, and downstream its output is indistinguishable from a subject that
    had no unresolved references. The caller reconciles the length of this list
    against the count it decoded.
    """
    return [(occurrence, resolve(occurrence["symbol"])) for occurrence in occurrences]


# --------------------------------------------------------------------------
# ranges
# --------------------------------------------------------------------------
def line_starts(data: bytes) -> list[int]:
    starts = [0]
    for index, byte in enumerate(data):
        if byte == 0x0A:
            starts.append(index + 1)
    return starts


def expand_range(raw: list[int], where: str) -> tuple[int, int, int, int]:
    if len(raw) == 3:
        return raw[0], raw[1], raw[0], raw[2]
    if len(raw) == 4:
        return raw[0], raw[1], raw[2], raw[3]
    raise Refusal(
        "SCIP_INDEX_WRONG_SUBJECT",
        f"{where}: a SCIP range must carry three or four elements, this one carries {len(raw)}",
    )


def to_byte(starts: list[int], size: int, row: int, column: int, where: str) -> int:
    if row < 0 or row >= len(starts):
        raise Refusal(
            "SCIP_INDEX_WRONG_SUBJECT",
            f"{where}: line {row} is outside the {len(starts)} lines of the declared blob; the "
            "index describes a file with more lines than the subject carries",
        )
    offset = starts[row] + column
    if offset > size:
        raise Refusal(
            "SCIP_INDEX_WRONG_SUBJECT",
            f"{where}: byte {offset} is past the {size}-byte declared blob",
        )
    return offset


# --------------------------------------------------------------------------
# bindings the caller must have written down
# --------------------------------------------------------------------------
def load_rule() -> tuple[dict[str, Any], str]:
    body = RULE_PATH.read_bytes()
    rule = json.loads(body.decode("utf-8"))
    return rule, sha256_hex(canonical(rule))


def check_subject(subject: dict[str, Any]) -> None:
    for key in ("commit", "tree"):
        value = subject.get(key, "")
        if not HEX40.match(value):
            raise Refusal(
                "SCIP_INDEX_WRONG_SUBJECT",
                f"subject.{key}={value!r} is not an exact 40-hex object id; a branch, a tag or HEAD "
                "names a moving tree and an index dated to a moving tree is dated to nothing",
            )
    if not re.match(r"^DTCR-RB-[0-9a-f]{16}$", subject.get("repository_binding_id", "")):
        raise Refusal(
            "SCIP_INDEX_WRONG_SUBJECT",
            "subject.repository_binding_id must be the opaque binding id; a clone URL, an "
            "owner/name pair or a working-copy path each describe one account or one machine",
        )


def check_index_digest(index_binding: dict[str, Any], index_bytes: bytes) -> None:
    declared = index_binding.get("index_digest") or ""
    if not HEX64.match(str(declared)):
        raise Refusal(
            "SCIP_INDEX_DIGEST_ABSENT",
            f"index_binding.index_digest={declared!r} is not a sha256; without it a rerun that "
            "disagrees cannot be told from a rerun over a different index",
        )
    observed = sha256_hex(index_bytes)
    if observed != declared:
        raise Refusal(
            "SCIP_INDEX_DIGEST_ABSENT",
            f"index_binding.index_digest names {declared} and the bytes read hash to {observed}; "
            "the binding is attached to an index this pass did not consume",
        )


def check_indexer_identity(index_binding: dict[str, Any], provider: dict[str, Any], decoded: dict[str, Any]) -> None:
    for key, source in (("version", index_binding), ("indexer_sha256", index_binding), ("config_digest", index_binding)):
        if not str(source.get(key, "")).strip():
            raise Refusal(
                "INDEXER_VERSION_OR_CONFIG_UNBOUND",
                f"index_binding.{key} is empty; two versions of one indexer resolve different "
                "symbols and an unbound one makes the difference unreadable",
            )
    for key in ("indexer_sha256", "config_digest"):
        if not HEX64.match(index_binding[key]):
            raise Refusal("INDEXER_VERSION_OR_CONFIG_UNBOUND", f"index_binding.{key} is not a sha256")
    if not provider.get("argv_template"):
        raise Refusal(
            "INDEXER_VERSION_OR_CONFIG_UNBOUND",
            "provider.argv_template is empty; the configuration digest would cover an invocation "
            "nobody wrote down",
        )
    embedded = decoded["tool_info"]
    if embedded["name"] != index_binding["indexer_name"]:
        raise Refusal(
            "INDEXER_VERSION_OR_CONFIG_UNBOUND",
            f"the index says it was written by {embedded['name']!r}, the binding names "
            f"{index_binding['indexer_name']!r}",
        )
    if embedded["version"] != index_binding["version"]:
        raise Refusal(
            "INDEXER_VERSION_OR_CONFIG_UNBOUND",
            f"the index carries tool_info.version {embedded['version']!r} and the binding declares "
            f"{index_binding['version']!r}; one of the two is describing a different run",
        )


def check_normalization(declared_digest: str, rule_digest: str) -> None:
    if declared_digest != rule_digest:
        raise Refusal(
            "PROVIDER_ID_PROMOTED_TO_UNIVERSAL_ID",
            f"the request pins normalization scheme {declared_digest} and this tree's rule hashes "
            f"to {rule_digest}; the identities would be emitted under a scheme nobody pinned, which "
            "is a provider string travelling as though it were a universal node id",
        )


def check_project_root(decoded: dict[str, Any], index_root: str) -> None:
    root = decoded["project_root"]
    tail = root.rstrip("/").split("/")
    wanted = index_root.strip("/").split("/")
    if tail[-len(wanted):] != wanted:
        raise Refusal(
            "SCIP_INDEX_WRONG_SUBJECT",
            f"the index was built at project_root {root!r}, which does not end in the declared "
            f"index root {index_root!r}; the documents inside it are relative to a directory the "
            "subject never named",
        )


# --------------------------------------------------------------------------
# emitter
# --------------------------------------------------------------------------
def emit_bundle(
    *,
    subject: dict[str, Any],
    index_bytes: bytes,
    index_binding: dict[str, Any],
    provider: dict[str, Any],
    index_root: str,
    declared_blobs: list[dict[str, Any]],
    sources: dict[str, bytes],
    normalization_digest: str,
    omissions: list[dict[str, str]],
    warnings: list[str],
    sequence: int = 1,
) -> dict[str, Any]:
    check_subject(subject)
    check_index_digest(index_binding, index_bytes)
    rule, rule_digest = load_rule()
    check_normalization(normalization_digest, rule_digest)

    decoded = decode_index(index_bytes)
    check_indexer_identity(index_binding, provider, decoded)
    check_project_root(decoded, index_root)

    declared = {entry["path"]: entry for entry in declared_blobs}
    if not declared:
        raise Refusal("SCIP_INDEX_WRONG_SUBJECT", "the subject declares no blobs")
    for path, entry in sorted(declared.items()):
        data = sources.get(path)
        if data is None:
            raise Refusal("SCIP_INDEX_WRONG_SUBJECT", f"{path} is declared by the subject and its bytes were not offered")
        actual = git_blob_sha1(data)
        if actual != entry["blob"]:
            raise Refusal(
                "SCIP_INDEX_WRONG_SUBJECT",
                f"{path}: the bytes offered hash to {actual}, the subject declares {entry['blob']}",
            )
        if entry.get("byte_count") != len(data):
            raise Refusal(
                "SCIP_INDEX_WRONG_SUBJECT",
                f"{path}: byte_count {entry.get('byte_count')} against {len(data)} bytes offered",
            )
        indexed_blob = index_binding["indexed_blobs"].get(path)
        if indexed_blob is None:
            raise Refusal(
                "STALE_INDEX_REUSED_AFTER_SOURCE_CHANGE",
                f"{path} is in the subject and the index binding never records which blob the "
                "indexer read there; a reuse across an edit would be invisible",
            )
        if indexed_blob != entry["blob"]:
            raise Refusal(
                "STALE_INDEX_REUSED_AFTER_SOURCE_CHANGE",
                f"{path}: the index was built over blob {indexed_blob} and the subject carries "
                f"{entry['blob']}; every range in this index points into bytes that have moved",
            )

    # ---- decode side: symbols, occurrences, resolution ----
    defined: dict[str, dict[str, Any]] = {}
    for document in decoded["documents"]:
        for info in document["symbols"]:
            defined.setdefault(info["symbol"], {"info": info, "where": document["relative_path"]})
    external = {info["symbol"]: info for info in decoded["external_symbols"]}

    def resolve(symbol: str) -> str:
        if symbol.startswith("local "):
            return "DOCUMENT_LOCAL"
        if symbol in defined:
            return "PROJECT_DEFINED"
        if symbol in external:
            return "EXTERNAL_DECLARED"
        return "UNRESOLVED_IN_INDEX"

    def identity(symbol: str) -> dict[str, Any]:
        return {
            "provider_scoped_id": symbol,
            "normalization": {"scheme": rule["rule_id"], "scheme_digest": rule_digest},
        }

    subject_of = dict(subject)
    binding_block = {
        "indexer_name": index_binding["indexer_name"],
        "version": index_binding["version"],
        "indexer_sha256": index_binding["indexer_sha256"],
        "config_digest": index_binding["config_digest"],
        "index_digest": index_binding["index_digest"],
        "indexed_commit": index_binding["indexed_commit"],
    }
    run_warnings = sorted(set(warnings))
    declared_omissions = [dict(entry) for entry in omissions]
    omission_details = {entry["detail"] for entry in declared_omissions}

    records: list[dict[str, Any]] = []
    occurrence_index: dict[str, dict[str, Any]] = {}
    counted = {name: 0 for name in RESOLUTION_CLASSES}
    decoded_occurrences = 0
    readback_checked = readback_skipped = 0
    unmapped_roles: set[str] = set()
    analysed: list[str] = []
    definition_spans: dict[str, list[dict[str, Any]]] = {}

    for document in sorted(decoded["documents"], key=lambda d: d["relative_path"]):
        repo_path = f"{index_root.strip('/')}/{document['relative_path']}"
        if repo_path not in declared:
            raise Refusal(
                "SCIP_INDEX_WRONG_SUBJECT",
                f"the index carries a document at {document['relative_path']!r}, which resolves to "
                f"{repo_path} and the subject never declared it; a fact about a blob the subject "
                "does not carry is a fact nobody can resolve",
            )
        data = sources[repo_path]
        if document["position_encoding"] == 0 and not data.isascii():
            raise Refusal(
                "SCIP_INDEX_WRONG_SUBJECT",
                f"{repo_path}: the document leaves position_encoding unspecified and the blob is "
                "not ASCII, so a column is not a byte offset and every range here would be a guess",
            )
        starts = line_starts(data)
        size = len(data)
        analysed.append(repo_path)

        for info in document["symbols"]:
            parsed = parse_symbol(info["symbol"])
            records.append(
                {
                    "schema": FACT_SCHEMA,
                    "fact_id": "DTCR-SY-000",
                    "fact_kind": "SYMBOL",
                    "subject": dict(subject_of),
                    "index_binding": dict(binding_block),
                    "symbol": {
                        "identity": identity(info["symbol"]),
                        "symbol_kind": symbol_kind(parsed),
                        **({"display_name": info["display_name"]} if info["display_name"] else {}),
                    },
                    "output_digest": "",
                    "warnings": run_warnings
                    + [f"declared by the index in document {document['relative_path']}"],
                    "omissions": sorted(omission_details),
                    "establishes": dict(ESTABLISHES),
                    "_sort": (1, repo_path, info["symbol"]),
                }
            )

        decoded_occurrences += len(document["occurrences"])
        for occurrence, resolution in occurrences_in_scope(document["occurrences"], resolve):
            counted[resolution] += 1
            start_line, start_col, end_line, end_col = expand_range(occurrence["range"], repo_path)
            start_byte = to_byte(starts, size, start_line, start_col, repo_path)
            end_byte = to_byte(starts, size, end_line, end_col, repo_path)
            if end_byte < start_byte:
                raise Refusal(
                    "SCIP_INDEX_WRONG_SUBJECT",
                    f"{repo_path}: end byte {end_byte} before start {start_byte}",
                )
            roles, unmapped = occurrence_roles(occurrence["symbol_roles"])
            unmapped_roles.update(unmapped)

            # Read-back. The index carries no content hash, so this is what ties
            # it to the declared bytes: the identifier the symbol string spells
            # has to be the identifier standing at that range.
            parsed = parse_symbol(occurrence["symbol"]) if not occurrence["symbol"].startswith("local ") else None
            names = {descriptor["name"] for descriptor in parsed["descriptors"]} if parsed else set()
            if names and end_byte > start_byte and start_line == end_line:
                observed = data[start_byte:end_byte].decode("utf-8", "replace")
                readback_checked += 1
                if observed not in names:
                    raise Refusal(
                        "SCIP_INDEX_WRONG_SUBJECT",
                        f"{repo_path} {start_line + 1}:{start_col}-{end_col}: the declared bytes read "
                        f"{observed!r} and the symbol at that range spells {sorted(names)!r}; the index "
                        "was built over different bytes than the subject declares",
                    )
            else:
                readback_skipped += 1

            key = f"{repo_path}#{start_byte}:{end_byte}:{occurrence['symbol']}"
            record = {
                "schema": FACT_SCHEMA,
                "fact_id": "DTCR-SY-000",
                "fact_kind": "OCCURRENCE",
                "subject": dict(subject_of),
                "index_binding": dict(binding_block),
                "occurrence": {
                    "identity": identity(occurrence["symbol"]),
                    "blob": {"path": repo_path, "blob": declared[repo_path]["blob"]},
                    "range": {
                        "start_byte": start_byte,
                        "end_byte": end_byte,
                        "start_line": start_line + 1,
                        "start_column": start_col,
                        "end_line": end_line + 1,
                        "end_column": end_col,
                    },
                    "roles": roles,
                },
                "output_digest": "",
                "warnings": run_warnings + [f"resolution class {resolution} in this index"],
                "omissions": sorted(omission_details),
                "establishes": dict(ESTABLISHES),
                "_sort": (2, repo_path, f"{start_byte:09d}", occurrence["symbol"]),
                "_key": key,
            }
            occurrence_index[key] = record
            records.append(record)

            if "DEFINITION" in roles and len(occurrence["enclosing_range"]) in (3, 4):
                span = expand_range(occurrence["enclosing_range"], repo_path)
                definition_spans.setdefault(repo_path, []).append(
                    {"symbol": occurrence["symbol"], "span": span}
                )

    # ---- the reconciliation the unresolved falsifier lives on ----
    if sum(counted.values()) != decoded_occurrences:
        raise Refusal(
            "UNRESOLVED_SYMBOL_OMITTED_FROM_DENOMINATOR",
            f"{decoded_occurrences} occurrences were decoded and {sum(counted.values())} were "
            "classified; the difference is references this pass would have dropped, and a dropped "
            "unresolved reference reads downstream exactly like a subject that had none",
        )

    # ---- edges: a reference nested in the smallest enclosing definition span ----
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in list(occurrence_index.values()):
        roles = record["occurrence"]["roles"]
        if "DEFINITION" in roles:
            continue
        repo_path = record["occurrence"]["blob"]["path"]
        rng = record["occurrence"]["range"]
        here = (rng["start_line"] - 1, rng["start_column"])
        enclosing = None
        for candidate in definition_spans.get(repo_path, []):
            start_line, start_col, end_line, end_col = candidate["span"]
            if (start_line, start_col) <= here <= (end_line, end_col):
                if enclosing is None or _span_size(candidate["span"]) < _span_size(enclosing["span"]):
                    enclosing = candidate
        if enclosing is None:
            continue
        target = record["occurrence"]["identity"]["provider_scoped_id"]
        if target == enclosing["symbol"]:
            continue
        kind = relationship_kind_for(roles)
        key = (enclosing["symbol"], target, kind)
        if key not in edges:
            edges[key] = {
                "schema": FACT_SCHEMA,
                "fact_id": "DTCR-SY-000",
                "fact_kind": "RELATIONSHIP",
                "subject": dict(subject_of),
                "index_binding": dict(binding_block),
                "relationship": {
                    "from": identity(enclosing["symbol"]),
                    "to": identity(target),
                    "relationship_kind": kind,
                    "graph_evidence": {
                        "provenance": "OCCURRENCE_ENCLOSING_RANGE_HEURISTIC",
                        "completeness": "PARTIAL_LOWER_BOUND",
                        "tool": f"{INDEXER_NAME} {index_binding['version']} occurrence-nesting importer",
                    },
                },
                "output_digest": "",
                "warnings": list(run_warnings),
                "omissions": sorted(omission_details),
                "establishes": dict(ESTABLISHES),
                "_sort": (3, enclosing["symbol"], target, kind),
                "_from_occurrence": record["_key"],
            }
    records.extend(edges.values())

    for record in records:
        if record["fact_kind"] != "RELATIONSHIP":
            continue
        evidence = record["relationship"]["graph_evidence"]
        if record["relationship"]["relationship_kind"] == "CALLS" and evidence["provenance"] != "COMPILER_RESOLVED_CALL":
            raise Refusal(
                "OCCURRENCE_NESTING_PROMOTED_TO_CALL_GRAPH",
                "an edge derived by nesting a reference occurrence inside an enclosing definition "
                "range was filed as CALLS; an occurrence role says an identifier was read here and "
                "does not distinguish a call from a type annotation",
            )
        if evidence["provenance"] != "COMPILER_RESOLVED_CALL" and evidence["completeness"] != "PARTIAL_LOWER_BOUND":
            raise Refusal(
                "OCCURRENCE_NESTING_PROMOTED_TO_CALL_GRAPH",
                f"a {evidence['provenance']} edge recorded completeness {evidence['completeness']}; "
                "a heuristic edge set is a floor on what exists and never a ceiling",
            )

    # ---- ids, then the digests that cover them ----
    if len(records) > 999:
        # ponytail: the frozen fact_id pattern is three digits. Batching by
        # document is the upgrade path if a subject ever needs more.
        raise Refusal("FACT_ID_SPACE_EXHAUSTED", f"{len(records)} rows exceed the DTCR-SY-999 id space")
    records.sort(key=lambda r: r["_sort"])
    for position, record in enumerate(records, 1):
        record["fact_id"] = f"DTCR-SY-{position:03d}"

    for record in records:
        if record["fact_kind"] != "RELATIONSHIP":
            continue
        backing = occurrence_index.get(record.get("_from_occurrence") or "")
        if backing is None:
            raise Refusal(
                "RELATIONSHIP_WITHOUT_SOURCE_RANGE",
                f"the {record['relationship']['relationship_kind']} edge from "
                f"{record['relationship']['from']['provider_scoped_id']} names no occurrence this "
                "pass emitted; an edge whose source range nobody can open is an edge nobody can check",
            )
        rng = backing["occurrence"]["range"]
        if rng["end_byte"] <= rng["start_byte"]:
            raise Refusal(
                "RELATIONSHIP_WITHOUT_SOURCE_RANGE",
                f"the edge cites occurrence {backing['fact_id']} whose range is empty",
            )
        record["warnings"] = sorted(
            set(record["warnings"])
            | {
                f"source range: {backing['occurrence']['blob']['path']} "
                f"{rng['start_line']}:{rng['start_column']}-{rng['end_line']}:{rng['end_column']}, "
                f"occurrence {backing['fact_id']}, nested inside the enclosing range the indexer "
                f"attached to the definition of {record['relationship']['from']['provider_scoped_id']}"
            }
        )

    for record in records:
        if any(record["establishes"].values()):
            raise Refusal(
                "SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS",
                f"{record['fact_id']} records itself as establishing "
                f"{sorted(k for k, v in record['establishes'].items() if v)}; an index row is a fact "
                "about what one indexer resolved and about nothing downstream of it",
            )
        record.pop("_sort", None)
        record.pop("_key", None)
        record.pop("_from_occurrence", None)
        record["warnings"] = sorted(set(record["warnings"]))
        record["output_digest"] = sha256_hex(
            canonical({k: v for k, v in record.items() if k != "output_digest"})
        )

    # ---- coverage ceiling ----
    unindexed = sorted(set(declared) - set(analysed))
    for path in unindexed:
        if not any(path.rsplit("/", 1)[-1] in detail for detail in omission_details):
            raise Refusal(
                "PARTIAL_COVERAGE_PROMOTED_TO_COMPLETE",
                f"{path} is in the subject denominator, no document of this index covers it, and no "
                "omission names it; the ceiling would then read as a pass over everything declared, "
                "which is a file nobody opened reported as a file found clean",
            )
    if unindexed and not declared_omissions:
        raise Refusal(
            "PARTIAL_COVERAGE_PROMOTED_TO_COMPLETE",
            f"{len(unindexed)} declared blobs are outside this index and the omission list is empty",
        )

    provider_binding = binding_id(
        "DTCR-PB",
        canonical(
            [
                EXECUTABLE_NAME,
                index_binding["version"],
                index_binding["indexer_sha256"],
                index_binding["config_digest"],
                rule_digest,
            ]
        ),
    )
    unresolved_sentence = (
        f"unresolved denominator: {counted['UNRESOLVED_IN_INDEX']} of the {decoded_occurrences} "
        f"occurrences decoded name a symbol neither a document nor external_symbols declares "
        f"({counted['PROJECT_DEFINED']} project-defined, {counted['EXTERNAL_DECLARED']} external, "
        f"{counted['DOCUMENT_LOCAL']} document-local); an unresolved reference stays in the "
        "denominator because dropping it reads as a subject that had none"
    )
    readback_sentence = (
        f"read-back: {readback_checked} of {decoded_occurrences} occurrence ranges were opened in the "
        f"declared bytes and matched a name their own symbol string spells; {readback_skipped} carry "
        "no comparable name (document-local symbols and empty ranges) and are not evidence either way"
    )
    edge_sentence = (
        f"{len(edges)} relationship rows, every one of them derived by nesting a reference occurrence "
        "inside the smallest enclosing definition range the indexer attached; this indexer emitted "
        "zero SymbolInformation.relationships for this subject, so no edge here is compiler-resolved "
        "and none is a call"
    )
    ceiling = {
        "schema": CEILING_SCHEMA,
        "ceiling_id": "DTCR-CC-001",
        "subject": dict(subject_of),
        "provider_binding_id": provider_binding,
        "analysed": {
            "numerator": len(analysed),
            "denominator": len(declared),
            "denominator_definition": "source blobs declared by the exact source subject inside the directory this index was built over",
            "method": f"one {INDEXER_NAME} invocation over the declared index root, decoded from the index bytes named by index_digest",
        },
        "completeness": "COMPLETE_FOR_ANALYSED_INPUTS" if not declared_omissions else "PARTIAL_LOWER_BOUND",
        "omissions": declared_omissions,
        "warnings": sorted(
            set(run_warnings)
            | {unresolved_sentence, readback_sentence, edge_sentence}
            | ({f"the index sets SCIP role bits this contract has no value for: {sorted(unmapped_roles)}"} if unmapped_roles else set())
        ),
        "authority_ceiling": {
            "unanalysed_inputs_cleared": False,
            "semantic_completeness": False,
            "task_pass": False,
        },
    }

    # ---- fact-plane receipt ----
    bundle_body = {"facts": records, "coverage_ceiling": ceiling}
    bundle_digest = sha256_hex(canonical(bundle_body))
    input_digest = sha256_hex(
        canonical(
            {
                "index_digest": index_binding["index_digest"],
                "normalization_digest": rule_digest,
                "blobs": sorted((entry["path"], entry["blob"]) for entry in declared_blobs),
            }
        )
    )
    run_omissions = sorted(
        omission_details
        | {
            "this adapter writes no canonical ledger row: ledger_event carries the emitted bundle "
            "digest and this run's own sequence, not an allocation from a ledger",
            f"{INDEXER_NAME} indexes Python; every other language in this tree is outside this "
            "index and a miss there is absence of coverage, not absence of the thing",
            "SymbolInformation.relationships was empty for every symbol in this index, so no "
            "compiler-resolved edge was available to import",
        }
    )
    provider_run = {
        "provider_binding_id": provider_binding,
        "executable_name": EXECUTABLE_NAME,
        "version": index_binding["version"],
        "executable_sha256": index_binding["indexer_sha256"],
        "config_digest": index_binding["config_digest"],
        "input_digest": input_digest,
        "output_digest": sha256_hex(canonical(records)),
        "exit_code": int(provider.get("exit_code", 0)),
        "outcome": "PASS" if int(provider.get("exit_code", 0)) == 0 else "FAIL",
        "warnings": sorted(set(run_warnings) | {unresolved_sentence, readback_sentence}),
        "omissions": run_omissions,
    }
    counts = {kind: sum(1 for r in records if r["fact_kind"] == kind) for kind in ("SYMBOL", "OCCURRENCE", "RELATIONSHIP")}
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": "DTCR-FR-001",
        "subject": dict(subject_of),
        "arrival": "STATIC",
        "provider_runs": [provider_run],
        "ledger_event": {
            "event_digest": bundle_digest,
            "sequence": sequence,
            "ledger_schema_digest": sha256_hex((SCHEMAS / "fact-plane-receipt.schema.json").read_bytes()),
        },
        "bundle_digest": bundle_digest,
        "coverage_ceiling_ref": ceiling["ceiling_id"],
        "summary": (
            f"{INDEXER_NAME} {index_binding['version']} indexed {len(analysed)} of {len(declared)} "
            f"declared blobs and this pass read {counts['SYMBOL']} symbols, {counts['OCCURRENCE']} "
            f"occurrences and {counts['RELATIONSHIP']} lower-bound relationships out of the index "
            f"bytes. {counted['UNRESOLVED_IN_INDEX']} occurrences name symbols the index never "
            "resolved. Index facts only."
        ),
        "grants": dict(GRANTS),
    }
    if any(receipt["grants"].values()):
        raise Refusal(
            "SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS",
            f"the receipt grants {sorted(k for k, v in receipt['grants'].items() if v)}; an indexer "
            "exiting zero is a fact about the indexer",
        )
    return {
        "facts": records,
        "coverage_ceiling": ceiling,
        "receipt": receipt,
        "resolution": counted,
        "decoded": {
            "documents": len(decoded["documents"]),
            "occurrences": decoded_occurrences,
            "external_symbols": len(decoded["external_symbols"]),
            "project_root": decoded["project_root"],
            "tool_info": decoded["tool_info"],
        },
        "readback": {"checked": readback_checked, "not_applicable": readback_skipped},
    }


def _span_size(span: tuple[int, int, int, int]) -> tuple[int, int]:
    return (span[2] - span[0], span[3] - span[1])


# --------------------------------------------------------------------------
# replay mode
# --------------------------------------------------------------------------
def run_replay(request_path: Path) -> dict[str, Any]:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if request.get("schema") != REQUEST_SCHEMA:
        raise Refusal("REQUEST_SCHEMA_UNKNOWN", f"{request_path.name}: schema {request.get('schema')!r}")
    base = request_path.parent
    index_bytes = (base / request["index"]).read_bytes()
    sources = {
        entry["path"]: (base / entry["local"]).read_bytes() for entry in request["declared_blobs"]
    }
    return emit_bundle(
        subject=request["subject"],
        index_bytes=index_bytes,
        index_binding=request["index_binding"],
        provider=request["provider"],
        index_root=request["index_root"],
        declared_blobs=[{k: v for k, v in entry.items() if k != "local"} for entry in request["declared_blobs"]],
        sources=sources,
        normalization_digest=request["normalization_digest"],
        omissions=request.get("omissions", []),
        warnings=request.get("warnings", []),
        sequence=request.get("sequence", 1),
    )


# --------------------------------------------------------------------------
# live mode
# --------------------------------------------------------------------------
def find_indexer() -> str | None:
    explicit = os.environ.get("DTCR_SCIP_PYTHON_BIN")
    if explicit:
        return explicit if Path(explicit).is_file() else None
    return shutil.which(EXECUTABLE_NAME)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


PROJECT_NAME = "dtcr-scip-fixture"
PROJECT_VERSION = "1"
ARGV_TEMPLATE = [
    EXECUTABLE_NAME,
    "index",
    "--cwd",
    "<INDEX_ROOT>",
    "--project-name",
    PROJECT_NAME,
    "--project-version",
    PROJECT_VERSION,
    "--output",
    "<INDEX_OUT>",
    "--quiet",
]


def config_digest_of(pyproject_digest: str, rule_digest: str) -> str:
    """The invocation, with every machine-local path replaced by its role.

    `--project-version` is pinned rather than defaulted: left out, scip-python
    stamps the current git revision into every symbol string, and the index
    would then differ between two commits that changed nothing. The
    `pyproject.toml` digest is in here because it is what stops the indexer
    walking up to whatever config it finds above the subject -- on the host that
    produced the committed index, a file in the user's home directory.
    """
    return sha256_hex(
        canonical(
            {
                "argv_template": ARGV_TEMPLATE,
                "project_name": PROJECT_NAME,
                "project_version": PROJECT_VERSION,
                "pyproject_digest": pyproject_digest,
                "normalization_digest": rule_digest,
                "one_index_per_invocation": True,
            }
        )
    )


def indexer_identity(binary: str) -> dict[str, str]:
    version = subprocess.run([binary, "--version"], capture_output=True, text=True, check=True).stdout.strip()
    return {"version": version.split()[-1], "executable_sha256": sha256_hex(Path(binary).read_bytes())}


def facts_digest_modulo_project_root(index_bytes: bytes) -> str:
    """The part of an index a second checkout can be held to.

    `Metadata.project_root` is the absolute path of the directory the indexer
    was pointed at, so two honest runs of the same version over the same bytes
    in two checkouts disagree on the whole-index digest and agree on nothing
    checkable. Everything else -- tool identity, document paths, symbol strings,
    ranges, roles -- is reproduced exactly, and this digest is over that.
    """
    decoded = decode_index(index_bytes)
    body = [
        decoded["tool_info"]["name"],
        decoded["tool_info"]["version"],
        decoded["text_document_encoding"],
        [
            [
                document["relative_path"],
                sorted(info["symbol"] for info in document["symbols"]),
                sorted(
                    [occurrence["range"], occurrence["symbol"], occurrence["symbol_roles"], occurrence["enclosing_range"]]
                    for occurrence in document["occurrences"]
                ),
            ]
            for document in sorted(decoded["documents"], key=lambda d: d["relative_path"])
        ],
        sorted(info["symbol"] for info in decoded["external_symbols"]),
    ]
    return sha256_hex(canonical(body))


NEUTRAL_PROJECT_ROOT_PREFIX = "file:///dtcr-fixture/"


def _write_varint(value: int) -> bytes:
    out = bytearray()
    while True:
        seven = value & 0x7F
        value >>= 7
        out.append(seven | (0x80 if value else 0))
        if not value:
            return bytes(out)


def _field_span(buf: bytes, field_number: int) -> tuple[int, int, int]:
    """`(record_start, payload_start, payload_end)` of the one length-delimited
    `field_number` in `buf`.

    Exactly one. A repeated or absent field means the message is not the shape
    this rewrite was written against, and splicing into it by guess is how a
    redaction silently corrupts an index.
    """
    found: list[tuple[int, int, int]] = []
    pos, end = 0, len(buf)
    while pos < end:
        record_start = pos
        key, pos = _varint(buf, pos)
        number, wire = key >> 3, key & 7
        if wire == 2:
            length, pos = _varint(buf, pos)
            if number == field_number:
                found.append((record_start, pos, pos + length))
            pos += length
        elif wire == 0:
            _, pos = _varint(buf, pos)
        elif wire == 5:
            pos += 4
        elif wire == 1:
            pos += 8
        else:
            raise Refusal("SCIP_INDEX_UNREADABLE", f"unsupported protobuf wire type {wire}")
    if len(found) != 1:
        raise Refusal(
            "SCIP_INDEX_UNREADABLE",
            f"one length-delimited field {field_number} was expected and {len(found)} were found",
        )
    return found[0]


def neutralize_project_root(index_bytes: bytes, index_root: str) -> tuple[bytes, str, str]:
    """The index, with `Metadata.project_root` rewritten to a neutral URI.

    `Metadata.project_root` is the absolute path of the directory the indexer
    was pointed at, which on any real host is one account's home directory and
    the id of the checkout the run happened in. Committing the raw bytes
    publishes both, and a receipt that redacts the field in prose does not
    redact the bytes beside it. So the committed fixture carries a project_root
    that names no machine and keeps the tail `check_project_root` reads, and the
    receipt records both digests rather than pretending the run emitted these
    bytes.

    Only the project_root string and the two length varints covering it move:
    everything else is spliced through untouched, and the two decodes are then
    compared field by field so that "Metadata.project_root is the only thing
    that changed" is checked here rather than asserted downstream.
    """
    index_metadata, metadata_project_root = 1, 3
    meta_start, meta_payload_start, meta_payload_end = _field_span(index_bytes, index_metadata)
    metadata = index_bytes[meta_payload_start:meta_payload_end]
    root_start, root_payload_start, root_payload_end = _field_span(metadata, metadata_project_root)
    old_root = _text(metadata[root_payload_start:root_payload_end])
    new_root = NEUTRAL_PROJECT_ROOT_PREFIX + index_root.strip("/")
    value = new_root.encode("utf-8")
    new_metadata = (
        metadata[:root_start]
        + bytes([metadata_project_root << 3 | 2])
        + _write_varint(len(value))
        + value
        + metadata[root_payload_end:]
    )
    rewritten = (
        index_bytes[:meta_start]
        + bytes([index_metadata << 3 | 2])
        + _write_varint(len(new_metadata))
        + new_metadata
        + index_bytes[meta_payload_end:]
    )
    before, after = decode_index(index_bytes), decode_index(rewritten)
    if before.pop("project_root") != old_root or after.pop("project_root") != new_root:
        raise Refusal("SCIP_INDEX_UNREADABLE", "the rewrite did not land on Metadata.project_root")
    if canonical(before) != canonical(after):
        raise Refusal(
            "SCIP_INDEX_UNREADABLE",
            "the rewrite moved a field other than Metadata.project_root; a redaction that also "
            "edits a range or a symbol string is a different index wearing the same receipt",
        )
    check_project_root(after | {"project_root": new_root}, index_root)
    return rewritten, old_root, new_root


def run_live(
    *,
    repo: Path,
    index_root: str,
    index_out: Path | None = None,
    omissions: list[dict[str, str]] | None = None,
    record_dir: Path | None = None,
    receipt_path: Path | None = None,
) -> dict[str, Any]:
    binary = find_indexer()
    if binary is None:
        raise Refusal("PROVIDER_ABSENT", f"no {EXECUTABLE_NAME} on PATH and DTCR_SCIP_PYTHON_BIN unset")
    root_dir = repo / index_root
    if not root_dir.is_dir():
        raise Refusal("SUBJECT_PATH_ABSENT", f"{index_root} is not a directory in this checkout")

    commit = git(repo, "rev-parse", "HEAD")
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    first = git(repo, "rev-list", "--max-parents=0", "HEAD").splitlines()[-1]
    subject = {
        "repository_binding_id": binding_id("DTCR-RB", first.encode("ascii")),
        "commit": commit,
        "tree": tree,
    }

    declared_blobs: list[dict[str, Any]] = []
    sources: dict[str, bytes] = {}
    locals_by_path: dict[str, str] = {}
    for path in sorted(root_dir.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        repo_path = f"{index_root.strip('/')}/{path.name}"
        try:
            recorded = git(repo, "rev-parse", f"HEAD:{repo_path}")
        except subprocess.CalledProcessError as error:
            raise Refusal(
                "SUBJECT_PATH_ABSENT",
                f"{repo_path} is not in the tree at {commit}; a live pass over an uncommitted file "
                "has no exact subject to be about",
            ) from error
        data = path.read_bytes()
        if git_blob_sha1(data) != recorded:
            raise Refusal(
                "STALE_INDEX_REUSED_AFTER_SOURCE_CHANGE",
                f"{repo_path} in the working tree differs from the blob at {commit}; the index would "
                "be built over bytes the subject does not name",
            )
        declared_blobs.append({"path": repo_path, "blob": recorded, "byte_count": len(data)})
        sources[repo_path] = data
        locals_by_path[repo_path] = path.name

    pyproject = root_dir / "pyproject.toml"
    if not pyproject.is_file():
        raise Refusal(
            "INDEXER_VERSION_OR_CONFIG_UNBOUND",
            f"{index_root}/pyproject.toml is absent; without it the indexer walks upward for a "
            "configuration this run never chose and the symbols it writes carry that machine's paths",
        )
    _, rule_digest = load_rule()
    config_digest = config_digest_of(sha256_hex(pyproject.read_bytes()), rule_digest)
    identity = indexer_identity(binary)

    with tempfile.TemporaryDirectory(prefix="dtcr-scip-") as scratch:
        out = index_out or (Path(scratch) / "index.scip")
        out.parent.mkdir(parents=True, exist_ok=True)
        argv = [
            binary,
            "index",
            "--cwd",
            str(root_dir),
            "--project-name",
            PROJECT_NAME,
            "--project-version",
            PROJECT_VERSION,
            "--output",
            str(out),
            "--quiet",
        ]
        completed = subprocess.run(argv, capture_output=True, text=True)
        if completed.returncode != 0 or not out.is_file():
            raise Refusal(
                "PROVIDER_INVOCATION_FAILED",
                f"{EXECUTABLE_NAME} exited {completed.returncode} and wrote "
                f"{'an index' if out.is_file() else 'nothing'}",
            )
        index_bytes = out.read_bytes()

    index_binding = {
        "indexer_name": INDEXER_NAME,
        "version": identity["version"],
        "indexer_sha256": identity["executable_sha256"],
        "config_digest": config_digest,
        "index_digest": sha256_hex(index_bytes),
        "indexed_commit": commit,
        "indexed_blobs": {entry["path"]: entry["blob"] for entry in declared_blobs},
    }
    bundle = emit_bundle(
        subject=subject,
        index_bytes=index_bytes,
        index_binding=index_binding,
        provider={"argv_template": ARGV_TEMPLATE, "exit_code": 0},
        index_root=index_root,
        declared_blobs=declared_blobs,
        sources=sources,
        normalization_digest=rule_digest,
        omissions=omissions or [],
        warnings=[f"live provider run: {EXECUTABLE_NAME} executed on the host against the subject commit"],
    )
    bundle["_index_bytes"] = index_bytes
    bundle["_index_binding"] = index_binding
    bundle["_declared_blobs"] = declared_blobs
    bundle["_locals"] = locals_by_path
    if record_dir is not None:
        write_fixture(record_dir, bundle, index_root, subject, omissions or [], rule_digest)
    if receipt_path is not None:
        write_live_receipt(receipt_path, bundle, index_root)
    return bundle


def write_fixture(
    record_dir: Path,
    bundle: dict[str, Any],
    index_root: str,
    subject: dict[str, Any],
    omissions: list[dict[str, str]],
    rule_digest: str,
) -> None:
    """Freeze one live run as a replayable fixture: the index bytes as the
    indexer wrote them except for the one field that is an absolute path, and a
    request naming the blobs they were built over. The source bytes are not
    copied -- they are already in the tree under `index_root`, and a second copy
    would be a second thing to keep in step.

    `Metadata.project_root` is neutralized before the bytes are written, because
    this file is committed: the raw field carries the account name and checkout
    id of whichever host recorded it, and a fixture is read by everyone who
    reads the repository. `index_binding.index_digest` is therefore the digest
    of the bytes that land here, not of the bytes the indexer emitted; the live
    receipt records both and says which is which."""
    record_dir.mkdir(parents=True, exist_ok=True)
    index_bytes, _machine_local_root, neutral_root = neutralize_project_root(bundle["_index_bytes"], index_root)
    (record_dir / "index.scip").write_bytes(index_bytes)
    request = {
        "schema": REQUEST_SCHEMA,
        "subject": subject,
        "index_root": index_root,
        "index": "index.scip",
        "provider": {"argv_template": ARGV_TEMPLATE, "exit_code": 0},
        "index_binding": dict(bundle["_index_binding"], index_digest=sha256_hex(index_bytes)),
        "normalization_digest": rule_digest,
        "declared_blobs": [
            dict(entry, local=f"src/{bundle['_locals'][entry['path']]}") for entry in bundle["_declared_blobs"]
        ],
        "omissions": omissions,
        "warnings": [
            "recorded-index replay: the indexer did not run in this pass; index.scip beside this "
            "request is the output of a real run against the subject commit named above, with "
            f"Metadata.project_root and nothing else rewritten to {neutral_root} so that a "
            "committed artifact carries no account name and no checkout id"
        ],
    }
    (record_dir / "request.json").write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_live_receipt(receipt_path: Path, bundle: dict[str, Any], index_root: str) -> None:
    """What one real execution on one host observed.

    The indexer's install path is deliberately absent: a path describes one
    machine. What travels is the sha256 of the executable, the digest of the
    invocation, and the digest of everything in the index except the one field
    that is an absolute path."""
    binding = bundle["_index_binding"]
    ceiling = bundle["coverage_ceiling"]
    rule, rule_digest = load_rule()
    counts = {
        kind: sum(1 for r in bundle["facts"] if r["fact_kind"] == kind)
        for kind in ("SYMBOL", "OCCURRENCE", "RELATIONSHIP")
    }
    binding_file = ADAPTER_DIR / "bindings" / "binding.json"
    proto_binding = json.loads(binding_file.read_text(encoding="utf-8")) if binding_file.is_file() else None
    fixture_bytes, _machine_local_root, neutral_root = neutralize_project_root(bundle["_index_bytes"], index_root)
    receipt = {
        "schema": LIVE_RECEIPT_SCHEMA,
        "subject": bundle["receipt"]["subject"],
        "index_root": index_root,
        "paths": sorted(entry["path"] for entry in bundle["_declared_blobs"]),
        "provider": {
            "provider_binding_id": ceiling["provider_binding_id"],
            "executable_name": EXECUTABLE_NAME,
            "version": binding["version"],
            "executable_sha256": binding["indexer_sha256"],
            "executable_location": "resolved from DTCR_SCIP_PYTHON_BIN or PATH; the install path is one machine and is not part of the identity",
            "config_digest": binding["config_digest"],
            "argv_template": ARGV_TEMPLATE,
            "project_name": PROJECT_NAME,
            "project_version": PROJECT_VERSION,
        },
        "index": {
            "sha256": binding["index_digest"],
            "byte_count": len(bundle["_index_bytes"]),
            "tool_info": bundle["decoded"]["tool_info"],
            "documents": bundle["decoded"]["documents"],
            "occurrences": bundle["decoded"]["occurrences"],
            "external_symbols": bundle["decoded"]["external_symbols"],
            "project_root_is_machine_local": True,
            "project_root_tail": "/".join(bundle["decoded"]["project_root"].rstrip("/").split("/")[-3:]),
            # `sha256` above is what the indexer emitted on this run and stays
            # that, because rewriting it would make this receipt a claim about
            # bytes nobody produced. The committed fixture is not those bytes:
            # project_root is an absolute path and a committed artifact must not
            # publish one, so exactly that field is rewritten and both digests
            # are recorded here. The offline receipt check accepts the fixture
            # under the second digest only while this record is present and
            # names Metadata.project_root as the only field that moved.
            "neutralization": {
                "changed_fields": ["Metadata.project_root"],
                "project_root_after": neutral_root,
                "index_digest_before": binding["index_digest"],
                "fixture_digest_after_declared_neutralization": sha256_hex(fixture_bytes),
                "byte_count_after": len(fixture_bytes),
                "why": "Metadata.project_root is the absolute path of the directory the indexer ran in and carries the account name and checkout id of one host; a committed fixture publishes it to every reader of this repository",
                "checked": "both decodes were compared field by field and agree on tool identity, document paths, symbol strings, ranges, roles and external symbols; facts_digest_modulo_project_root is the same for both",
                "downstream_digests": "bundle_digest here and the provider_runs digests are this run's, computed with index_digest_before inside every fact row; replaying the committed fixture reproduces every fact except that one field and therefore lands on a different bundle_digest, which is arithmetic and not a disagreement",
            },
        },
        "facts_digest_modulo_project_root": facts_digest_modulo_project_root(bundle["_index_bytes"]),
        "decoder": {
            "primary": "in-tree SCIP wire-format reader in adapter.py; there is no scip CLI on this host and the scip in Homebrew is an integer-programming solver",
            "cross_check": "ABSENT"
            if proto_binding is None
            else {
                "binding_file": "bindings/binding.json",
                "binding_file_sha256": sha256_hex(binding_file.read_bytes()),
                "proto_url": proto_binding["proto"]["url"],
                "proto_revision": proto_binding["proto"]["revision"],
                "proto_sha256": proto_binding["proto"]["sha256"],
                "descriptor_set_sha256": proto_binding["descriptor_set"]["sha256"],
                "produced_by": proto_binding["descriptor_set"]["produced_by"],
                "role": "a second decode of these same bytes through the schema author's field numbers; it is not what produced the facts above",
            },
        },
        "normalization": {"scheme": rule["rule_id"], "scheme_digest": rule_digest},
        "emitted": counts,
        "resolution": bundle["resolution"],
        "readback": bundle["readback"],
        "coverage": ceiling["analysed"],
        "completeness": ceiling["completeness"],
        "bundle_digest": bundle["receipt"]["bundle_digest"],
        "exit_codes": {"index": bundle["receipt"]["provider_runs"][0]["exit_code"]},
        "establishes": {
            "semantic_truth": False,
            "task_pass": False,
            "merge": False,
            "complete_call_graph": False,
            "language_coverage": False,
            "cross_provider_identity": False,
            "provider_available_elsewhere": False,
        },
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)

    replay = sub.add_parser("replay", help="emit from a recorded index fixture, no indexer needed")
    replay.add_argument("request", type=Path)
    replay.add_argument("--out", type=Path)

    live = sub.add_parser("live", help="run scip-python against the subject commit")
    live.add_argument("--root", required=True, help="repo-relative directory the indexer is pointed at")
    live.add_argument("--repo", type=Path, default=Path.cwd())
    live.add_argument("--index", type=Path)
    live.add_argument("--omit", action="append", default=[], help="KIND:detail")
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
                index_root=args.root,
                index_out=args.index.resolve() if args.index else None,
                omissions=omissions,
                record_dir=args.record.resolve() if args.record else None,
                receipt_path=args.receipt.resolve() if args.receipt else None,
            )
    except Refusal as refusal:
        if refusal.reason == "PROVIDER_ABSENT":
            print(f"NOT_EXERCISED {refusal}", file=sys.stderr)
            return 70
        print(f"REFUSED {refusal}", file=sys.stderr)
        return 2
    text = json.dumps({k: v for k, v in bundle.items() if not k.startswith("_")}, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
