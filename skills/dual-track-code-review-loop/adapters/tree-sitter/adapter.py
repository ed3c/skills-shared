#!/usr/bin/env python3
"""Turn one exact source subject plus one pinned grammar/query bundle into
`dtcr/syntax-match/v1` observations, a `dtcr/coverage-ceiling/v1` and a
`dtcr/fact-plane-receipt/v1`.

What this adapter is allowed to say
-----------------------------------
A Tree-sitter query match is the sentence *these bytes have this shape*. It is
not *these bytes mean this*. Every match this file emits is fixed at
`SYNTACTIC_CANDIDATE` with `establishes.semantic_binding`,
`establishes.call_edge` and `establishes.task_pass` all false, and no code path
here writes a symbol, a call edge, a task outcome or a merge admission. The
frozen schemas in `../../references/schemas/` are read-only inputs; this adapter
never edits them and validates against them rather than against a local copy.

Two modes, one emitter
----------------------
`replay` reads a fixture request: recorded `tree-sitter parse` and
`tree-sitter query` stdout, captured from a real run, replayed with no provider
on the machine. `live` shells out to the real CLI. Both funnel into the same
`emit_bundle`, so the deterministic tests exercise the code the live path uses
rather than a stand-in for it. A missing CLI is start-readiness, not a failure:
`live` refuses to invent output and the selftest reports `NOT_EXERCISED`.

Bundle identity
---------------
`bundles/*.bundle.json` pins a grammar and a query set by content digest:

    grammar_digest  sha256 over the canonical `sha256  path` listing of the
                    grammar's own defining files. A grammar named only by
                    language parses differently between two builds while
                    recording identically, so the name is not the identity.
    query_digest    sha256 over the query bytes, per file and over the set.
    bundle_digest   sha256 over the canonical manifest body.

All three are recomputed on load, which is what makes the identity checkable
without the grammar being installed: a flipped file digest breaks the
`grammar_digest` binding, and a flipped `grammar_digest` breaks
`bundle_digest`. In `live` mode the grammar files are digested again from the
resolved grammar directory, so the manifest is also checked against the bytes
the CLI actually parsed with.

Refusals are named
------------------
Every guard raises `Refusal` carrying the falsifier name it exists to kill, so
a planted defect proves *its own* guard rather than dying on an unrelated
schema keyword. The falsifiers owned here (the rest are refused by the frozen
schemas themselves; see `selftest.py` for the full table):

    MUTABLE_OR_WRONG_SOURCE_SUBJECT
    WRONG_GRAMMAR_OR_GRAMMAR_DIGEST
    PARSE_ERROR_HIDDEN
    BYTE_RANGE_OUT_OF_SOURCE
    MATCH_WITHOUT_SOURCE_BLOB_BINDING
    EMPTY_QUERY_REPORTED_AS_EXERCISED
    UNDECLARED_FILE_OMITTED_FROM_DENOMINATOR

Usage
-----
    adapter.py replay <request.json> [--out <bundle.json>]
    adapter.py live --bundle <bundle.json> --grammar-dir <dir> \
        --path <repo-relative> [--path ...] [--omit KIND:detail] \
        [--record <fixture-dir>] [--out <bundle.json>]

Exit 0 emitted, 2 refused, 70 the provider is absent in `live` mode.
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
from pathlib import Path
from typing import Any, Iterable

ADAPTER_DIR = Path(__file__).resolve().parent
SKILL = ADAPTER_DIR.parents[1]
SCHEMAS = SKILL / "references" / "schemas"

MATCH_SCHEMA = "dtcr/syntax-match/v1"
CEILING_SCHEMA = "dtcr/coverage-ceiling/v1"
RECEIPT_SCHEMA = "dtcr/fact-plane-receipt/v1"
BUNDLE_SCHEMA = "dtcr/tree-sitter-bundle/v1"
REQUEST_SCHEMA = "dtcr/tree-sitter-run-request/v1"

EXECUTABLE_NAME = "tree-sitter"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

# `capture: 0 - func.name, start: (0, 4), end: (0, 9), text: `alpha``
CAPTURE_LINE = re.compile(
    r"capture: (?P<index>\d+) - (?P<name>[^,\n]+), "
    r"start: \((?P<start_row>\d+), (?P<start_col>\d+)\), "
    r"end: \((?P<end_row>\d+), (?P<end_col>\d+)\), "
    r"text: `(?P<text>[^`\n]*)`"
)
CAPTURE_MARKER = re.compile(r"^\s*capture: \d+ - ", re.MULTILINE)
ERROR_NODE = re.compile(r"\((?:ERROR|MISSING)\b")
# `path\tParse:  0.41 ms  225 bytes/ms  (ERROR [0, 0] - [5, 22])`. It is on
# stdout beside the tree, and it repeats the first error node, so counting
# error nodes without dropping it counts one that is not in the tree.
STAT_LINE = re.compile(r"^.*\tParse:.*$", re.MULTILINE)
# Top-level query pattern opener at column 0: `(` or a predicate-free `;`
# comment is not one. Counted so an empty query cannot report itself exercised.
QUERY_PATTERN_OPENER = re.compile(r"^[(\[]", re.MULTILINE)
COMMENT_LINE = re.compile(r"^\s*;.*$", re.MULTILINE)


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


def point_to_byte(starts: list[int], size: int, row: int, column: int, where: str) -> int:
    if row < 0 or row >= len(starts):
        raise Refusal(
            "BYTE_RANGE_OUT_OF_SOURCE",
            f"{where}: row {row} is outside the {len(starts)} lines of the parsed blob",
        )
    offset = starts[row] + column
    if offset > size:
        raise Refusal(
            "BYTE_RANGE_OUT_OF_SOURCE",
            f"{where}: byte {offset} is past the {size}-byte blob",
        )
    return offset


# --------------------------------------------------------------------------
# provider output readers -- pure, so the recorded fixtures exercise them
# --------------------------------------------------------------------------
def count_error_nodes(parse_stdout: str) -> int:
    return len(ERROR_NODE.findall(STAT_LINE.sub("", parse_stdout)))


def read_parse(parse_stdout: str, exit_code: int, path: str) -> tuple[str, int]:
    """(parse_status, error_node_count) from one `tree-sitter parse` run."""
    if exit_code not in (0, 1):
        raise Refusal(
            "PROVIDER_INVOCATION_FAILED",
            f"{path}: tree-sitter parse exited {exit_code}; that is a broken invocation, "
            "not a parse result, and reporting it as a clean tree would report a floor as a ceiling",
        )
    errors = count_error_nodes(parse_stdout)
    if exit_code == 1 and errors == 0:
        raise Refusal(
            "PARSE_ERROR_HIDDEN",
            f"{path}: tree-sitter parse exited 1 but the recorded tree carries no ERROR or "
            "MISSING node; the failure is in the exit code only and the tree hides it",
        )
    if errors:
        return "PARSE_ERRORS_PRESENT", errors
    return "CLEAN", 0


def read_captures(query_stdout: str, path: str) -> list[dict[str, Any]]:
    """Captures from one `tree-sitter query` run, or a refusal if any line of
    its output did not parse. A capture silently dropped by a regex is a match
    the pass never reports and nobody can see missing."""
    captures = [
        {
            "capture_index": int(m.group("index")),
            "capture_name": m.group("name"),
            "start_row": int(m.group("start_row")),
            "start_column": int(m.group("start_col")),
            "end_row": int(m.group("end_row")),
            "end_column": int(m.group("end_col")),
            "text": m.group("text"),
        }
        for m in CAPTURE_LINE.finditer(query_stdout)
    ]
    announced = len(CAPTURE_MARKER.findall(query_stdout))
    if announced != len(captures):
        raise Refusal(
            "QUERY_OUTPUT_UNPARSED",
            f"{path}: {announced} capture lines in the provider output, {len(captures)} read; "
            "the difference is matches this pass would have dropped without saying so",
        )
    return captures


def count_query_patterns(query_text: str) -> int:
    return len(QUERY_PATTERN_OPENER.findall(COMMENT_LINE.sub("", query_text)))


# --------------------------------------------------------------------------
# bundle manifest
# --------------------------------------------------------------------------
def grammar_digest_of(files: list[dict[str, str]]) -> str:
    listing = "".join(f"{entry['sha256']}  {entry['path']}\n" for entry in sorted(files, key=lambda e: e["path"]))
    return sha256_hex(listing.encode("utf-8"))


def bundle_digest_of(manifest: dict[str, Any]) -> str:
    body = {key: value for key, value in manifest.items() if key != "bundle_digest"}
    return sha256_hex(canonical(body))


def load_bundle(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema") != BUNDLE_SCHEMA:
        raise Refusal("BUNDLE_SCHEMA_UNKNOWN", f"{path.name}: schema {manifest.get('schema')!r}")

    grammar = manifest["grammar"]
    recomputed = grammar_digest_of(grammar["files"])
    if recomputed != grammar["grammar_digest"]:
        raise Refusal(
            "WRONG_GRAMMAR_OR_GRAMMAR_DIGEST",
            f"{path.name}: grammar_digest {grammar['grammar_digest']} does not bind the recorded "
            f"file digests ({recomputed}); the manifest names one grammar and identifies another",
        )
    if bundle_digest_of(manifest) != manifest["bundle_digest"]:
        raise Refusal(
            "BUNDLE_DIGEST_MISMATCH",
            f"{path.name}: bundle_digest does not cover the manifest body as written",
        )

    query_texts: list[str] = []
    for query in manifest["queries"]:
        query_path = (path.parent / query["path"]).resolve()
        text = query_path.read_text(encoding="utf-8")
        if sha256_hex(text.encode("utf-8")) != query["sha256"]:
            raise Refusal(
                "WRONG_GRAMMAR_OR_GRAMMAR_DIGEST",
                f"{query['path']}: query bytes do not match the digest the bundle pinned",
            )
        patterns = count_query_patterns(text)
        if patterns != query["patterns"]:
            raise Refusal(
                "EMPTY_QUERY_REPORTED_AS_EXERCISED",
                f"{query['path']}: manifest claims {query['patterns']} patterns, the bytes carry {patterns}",
            )
        if patterns == 0:
            raise Refusal(
                "EMPTY_QUERY_REPORTED_AS_EXERCISED",
                f"{query['path']}: a query with no patterns matches nothing, and a run that "
                "reports it as exercised reports an empty result as a clean file",
            )
        query_texts.append(text)

    joined = "".join(query_texts).encode("utf-8")
    if sha256_hex(joined) != manifest["query_digest"]:
        raise Refusal(
            "TREE_SITTER_QUERY_DIGEST_ABSENT",
            f"{path.name}: query_digest does not cover the query set this bundle names",
        )
    manifest["_resolved_query_paths"] = [str((path.parent / q["path"]).resolve()) for q in manifest["queries"]]
    return manifest


def build_manifest(
    *,
    bundle_id: str,
    language: str,
    abi_version: int,
    grammar_source: str,
    grammar_license: str,
    cli_license: str,
    grammar_files: list[dict[str, str]],
    queries: list[dict[str, Any]],
    query_digest: str,
) -> dict[str, Any]:
    manifest = {
        "schema": BUNDLE_SCHEMA,
        "bundle_id": bundle_id,
        "language": language,
        "abi_version": abi_version,
        "grammar": {
            "source": grammar_source,
            "license": grammar_license,
            "files": grammar_files,
            "grammar_digest": grammar_digest_of(grammar_files),
        },
        "cli_license": cli_license,
        "queries": queries,
        "query_digest": query_digest,
    }
    manifest["bundle_digest"] = bundle_digest_of(manifest)
    return manifest


# --------------------------------------------------------------------------
# emitter
# --------------------------------------------------------------------------
def check_subject(subject: dict[str, Any]) -> None:
    for key in ("commit", "tree"):
        value = subject.get(key, "")
        if not HEX40.match(value):
            raise Refusal(
                "MUTABLE_OR_WRONG_SOURCE_SUBJECT",
                f"subject.{key}={value!r} is not an exact 40-hex object id; a branch, a tag, HEAD "
                "or latest names a moving tree and a fact dated to a moving tree is dated to nothing",
            )
    if not re.match(r"^DTCR-RB-[0-9a-f]{16}$", subject.get("repository_binding_id", "")):
        raise Refusal(
            "MUTABLE_OR_WRONG_SOURCE_SUBJECT",
            "subject.repository_binding_id must be the opaque binding id; a clone URL, an "
            "owner/name pair or a working-copy path each describe one account or one machine",
        )


def provider_block(provider: dict[str, Any], manifest: dict[str, Any], config_digest: str) -> dict[str, Any]:
    for key in ("version", "executable_sha256"):
        if not str(provider.get(key, "")).strip():
            raise Refusal("PROVIDER_IDENTITY_ABSENT", f"provider.{key} is empty")
    if not HEX64.match(provider["executable_sha256"]):
        raise Refusal("PROVIDER_IDENTITY_ABSENT", "provider.executable_sha256 is not a sha256")
    grammar_digest = manifest["grammar"]["grammar_digest"]
    query_digest = manifest["query_digest"]
    material = canonical(
        [
            EXECUTABLE_NAME,
            provider["version"],
            provider["executable_sha256"],
            config_digest,
            grammar_digest,
            query_digest,
        ]
    )
    return {
        "provider_binding_id": binding_id("DTCR-PB", material),
        "executable_name": EXECUTABLE_NAME,
        "version": provider["version"],
        "executable_sha256": provider["executable_sha256"],
        "config_digest": config_digest,
        "grammar": {
            "language": manifest["language"],
            "grammar_digest": grammar_digest,
            "abi_version": manifest["abi_version"],
        },
        "query_digest": query_digest,
    }


def config_digest_of(manifest: dict[str, Any]) -> str:
    """The invocation, with every machine-local path replaced by its role. A
    config digest that moves when the checkout moves identifies a machine."""
    return sha256_hex(
        canonical(
            {
                "parse_argv": [EXECUTABLE_NAME, "parse", "-p", "<GRAMMAR_DIR>", "<SOURCE>"],
                "query_argv": [EXECUTABLE_NAME, "query", "-p", "<GRAMMAR_DIR>", "<QUERY>", "<SOURCE>"],
                "bundle_digest": manifest["bundle_digest"],
                "one_source_per_invocation": True,
            }
        )
    )


def emit_bundle(
    *,
    subject: dict[str, Any],
    manifest: dict[str, Any],
    provider: dict[str, Any],
    declared_blobs: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    omissions: list[dict[str, str]],
    warnings: list[str],
    sequence: int = 1,
) -> dict[str, Any]:
    """`runs` items: {path, source (bytes), parse_stdout, parse_exit,
    query_stdout, query_exit}."""
    check_subject(subject)
    config_digest = config_digest_of(manifest)
    block = provider_block(provider, manifest, config_digest)

    declared = {entry["path"]: entry for entry in declared_blobs}
    if not declared:
        raise Refusal("MUTABLE_OR_WRONG_SOURCE_SUBJECT", "the subject declares no blobs")

    analysed: list[str] = []
    matches: list[dict[str, Any]] = []
    parse_errors_total = 0
    parse_exit = 0
    query_exit = 0

    for run in sorted(runs, key=lambda r: r["path"]):
        path = run["path"]
        if path not in declared:
            raise Refusal(
                "MATCH_WITHOUT_SOURCE_BLOB_BINDING",
                f"{path} was parsed but the subject never declared it; a match against a blob the "
                "subject does not carry is a match against a file nobody can resolve",
            )
        source: bytes = run["source"]
        actual = git_blob_sha1(source)
        if actual != declared[path]["blob"]:
            raise Refusal(
                "MATCH_WITHOUT_SOURCE_BLOB_BINDING",
                f"{path}: the bytes parsed hash to {actual}, the subject declares "
                f"{declared[path]['blob']}; the match would be attributed to a blob it never touched",
            )
        if declared[path].get("byte_count") != len(source):
            raise Refusal(
                "MATCH_WITHOUT_SOURCE_BLOB_BINDING",
                f"{path}: byte_count {declared[path].get('byte_count')} against {len(source)} bytes parsed",
            )

        parse_status, error_nodes = read_parse(run["parse_stdout"], run["parse_exit"], path)
        parse_errors_total += error_nodes
        parse_exit = max(parse_exit, run["parse_exit"])
        query_exit = max(query_exit, run["query_exit"])
        if run["query_exit"] != 0:
            raise Refusal(
                "PROVIDER_INVOCATION_FAILED",
                f"{path}: tree-sitter query exited {run['query_exit']}",
            )

        starts = line_starts(source)
        size = len(source)
        for capture in read_captures(run["query_stdout"], path):
            start_byte = point_to_byte(starts, size, capture["start_row"], capture["start_column"], path)
            end_byte = point_to_byte(starts, size, capture["end_row"], capture["end_column"], path)
            if end_byte < start_byte:
                raise Refusal("BYTE_RANGE_OUT_OF_SOURCE", f"{path}: end byte {end_byte} before start {start_byte}")
            text = capture["text"]
            if "\n" not in text and text:
                observed = source[start_byte:end_byte].decode("utf-8", "replace")
                if observed != text:
                    raise Refusal(
                        "BYTE_RANGE_OUT_OF_SOURCE",
                        f"{path}: bytes {start_byte}..{end_byte} read {observed!r}, the provider "
                        f"reported {text!r} for that capture",
                    )
            match = {
                "schema": MATCH_SCHEMA,
                "match_id": "DTCR-SM-000",
                "subject": dict(subject),
                "blob": {"path": path, "blob": declared[path]["blob"]},
                "range": {
                    "start_byte": start_byte,
                    "end_byte": end_byte,
                    "start_line": capture["start_row"] + 1,
                    "start_column": capture["start_column"],
                    "end_line": capture["end_row"] + 1,
                    "end_column": capture["end_column"],
                },
                "match_class": "SYNTACTIC_CANDIDATE",
                "grade": "DETERMINISTIC_FACT",
                "provider": copy.deepcopy(block),
                "parse_status": parse_status,
                "error_node_count": error_nodes,
                "completeness": (
                    "COMPLETE_FOR_ANALYSED_INPUTS" if parse_status == "CLEAN" and not omissions else "PARTIAL_LOWER_BOUND"
                ),
                "output_digest": "",
                "warnings": sorted(set(warnings) | {f"capture {capture['capture_name']} of query bundle {manifest['bundle_id']}"}),
                "omissions": sorted({entry["detail"] for entry in omissions}),
                "establishes": {"semantic_binding": False, "call_edge": False, "task_pass": False},
            }
            matches.append(match)
        analysed.append(path)

    if len(matches) > 999:
        # ponytail: the frozen match_id pattern is three digits. Batching by
        # subject is the upgrade path if a run ever needs more.
        raise Refusal("MATCH_ID_SPACE_EXHAUSTED", f"{len(matches)} matches exceed the DTCR-SM-999 id space")

    for index, match in enumerate(sorted(matches, key=lambda m: (m["blob"]["path"], m["range"]["start_byte"], m["range"]["end_byte"])), 1):
        match["match_id"] = f"DTCR-SM-{index:03d}"
        match["output_digest"] = sha256_hex(canonical({k: v for k, v in match.items() if k != "output_digest"}))
    matches.sort(key=lambda m: m["match_id"])

    unanalysed = sorted(set(declared) - set(analysed))
    declared_omissions = {entry["detail"] for entry in omissions}
    for path in unanalysed:
        if not any(path in detail for detail in declared_omissions):
            raise Refusal(
                "UNDECLARED_FILE_OMITTED_FROM_DENOMINATOR",
                f"{path} is in the subject's denominator, was not analysed, and is named in no "
                "omission; downstream it is indistinguishable from a file that was parsed and found clean",
            )

    complete = not omissions and parse_errors_total == 0
    ceiling = {
        "schema": CEILING_SCHEMA,
        "ceiling_id": "DTCR-CC-001",
        "subject": dict(subject),
        "provider_binding_id": block["provider_binding_id"],
        "analysed": {
            "numerator": len(analysed),
            "denominator": len(declared),
            "denominator_definition": "source blobs declared by the exact source subject and offered to this pass",
            "method": "one tree-sitter parse and one tree-sitter query invocation per declared blob at the pinned bundle digest",
        },
        "completeness": "COMPLETE_FOR_ANALYSED_INPUTS" if complete else "PARTIAL_LOWER_BOUND",
        "omissions": [dict(entry) for entry in omissions],
        "warnings": sorted(set(warnings)),
        "authority_ceiling": {
            "unanalysed_inputs_cleared": False,
            "semantic_completeness": False,
            "task_pass": False,
        },
    }

    bundle_body = {"matches": matches, "coverage_ceiling": ceiling}
    bundle_digest = sha256_hex(canonical(bundle_body))
    input_digest = sha256_hex(
        canonical(
            {
                "bundle_digest": manifest["bundle_digest"],
                "blobs": sorted((entry["path"], entry["blob"]) for entry in declared_blobs),
            }
        )
    )
    run_omissions = sorted(
        {entry["detail"] for entry in omissions}
        | {
            "this adapter writes no canonical ledger row: ledger_event carries the emitted bundle "
            "digest and this run's own sequence, not an allocation from a ledger"
        }
    )
    provider_runs = [
        {
            "provider_binding_id": block["provider_binding_id"],
            "executable_name": EXECUTABLE_NAME,
            "version": provider["version"],
            "executable_sha256": provider["executable_sha256"],
            "config_digest": config_digest,
            "input_digest": input_digest,
            "output_digest": sha256_hex(canonical(matches)),
            "exit_code": parse_exit,
            "outcome": "PASS" if parse_exit == 0 else "FAIL",
            "warnings": sorted(set(warnings)) + ([f"{parse_errors_total} error or missing nodes across the parsed blobs"] if parse_errors_total else []),
            "omissions": run_omissions,
        },
        {
            "provider_binding_id": block["provider_binding_id"],
            "executable_name": EXECUTABLE_NAME,
            "version": provider["version"],
            "executable_sha256": provider["executable_sha256"],
            "config_digest": config_digest,
            "input_digest": input_digest,
            "output_digest": sha256_hex(canonical([m["range"] for m in matches])),
            "exit_code": query_exit,
            "outcome": "PASS" if query_exit == 0 else "FAIL",
            "warnings": sorted(set(warnings)) + [f"{len(matches)} captures over {len(analysed)} analysed blobs"],
            "omissions": run_omissions,
        },
    ]
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": "DTCR-FR-001",
        "subject": dict(subject),
        "arrival": "STATIC",
        "provider_runs": provider_runs,
        "ledger_event": {
            "event_digest": bundle_digest,
            "sequence": sequence,
            "ledger_schema_digest": sha256_hex((SCHEMAS / "fact-plane-receipt.schema.json").read_bytes()),
        },
        "bundle_digest": bundle_digest,
        "coverage_ceiling_ref": ceiling["ceiling_id"],
        "summary": (
            f"tree-sitter {provider['version']} parsed {len(analysed)} of {len(declared)} declared blobs "
            f"under bundle {manifest['bundle_id']} and reported {len(matches)} syntactic candidates "
            f"with {parse_errors_total} error or missing nodes. Syntax only."
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
    return {"matches": matches, "coverage_ceiling": ceiling, "receipt": receipt}


# --------------------------------------------------------------------------
# replay mode
# --------------------------------------------------------------------------
def run_replay(request_path: Path) -> dict[str, Any]:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if request.get("schema") != REQUEST_SCHEMA:
        raise Refusal("REQUEST_SCHEMA_UNKNOWN", f"{request_path.name}: schema {request.get('schema')!r}")
    base = request_path.parent
    manifest = load_bundle((base / request["bundle"]).resolve())
    runs = []
    for path, recorded in sorted(request["recorded"].items()):
        runs.append(
            {
                "path": path,
                "source": (base / recorded["source"]).read_bytes(),
                "parse_stdout": (base / recorded["parse_stdout"]).read_text(encoding="utf-8"),
                "parse_exit": recorded["parse_exit"],
                "query_stdout": (base / recorded["query_stdout"]).read_text(encoding="utf-8"),
                "query_exit": recorded["query_exit"],
            }
        )
    return emit_bundle(
        subject=request["subject"],
        manifest=manifest,
        provider=request["provider"],
        declared_blobs=request["declared_blobs"],
        runs=runs,
        omissions=request.get("omissions", []),
        warnings=request.get("warnings", []),
        sequence=request.get("sequence", 1),
    )


# --------------------------------------------------------------------------
# live mode
# --------------------------------------------------------------------------
def find_cli() -> str | None:
    explicit = os.environ.get("DTCR_TS_BIN")
    if explicit:
        return explicit if Path(explicit).is_file() else None
    return shutil.which(EXECUTABLE_NAME)


def cli_identity(binary: str) -> dict[str, str]:
    version = subprocess.run([binary, "--version"], capture_output=True, text=True, check=True).stdout.strip()
    return {
        "version": version.split()[-1],
        "executable_sha256": sha256_hex(Path(binary).read_bytes()),
    }


def digest_grammar_dir(grammar_dir: Path, files: Iterable[str]) -> list[dict[str, str]]:
    out = []
    for rel in sorted(files):
        blob = (grammar_dir / rel).read_bytes()
        out.append({"path": rel, "sha256": sha256_hex(blob)})
    return out


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def live_subject(repo: Path, paths: list[str]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, bytes]]:
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
    blobs: list[dict[str, Any]] = []
    sources: dict[str, bytes] = {}
    for path in paths:
        try:
            recorded = git(repo, "rev-parse", f"HEAD:{path}")
        except subprocess.CalledProcessError as error:
            raise Refusal(
                "SUBJECT_PATH_ABSENT",
                f"{path} is not in the tree at {commit}; a live pass over an uncommitted file has "
                "no exact subject to be about",
            ) from error
        data = (repo / path).read_bytes()
        if git_blob_sha1(data) != recorded:
            raise Refusal(
                "MUTABLE_OR_WRONG_SOURCE_SUBJECT",
                f"{path} in the working tree differs from the blob at {commit}; the subject would "
                "name a commit and the pass would read something else",
            )
        blobs.append({"path": path, "blob": recorded, "byte_count": len(data)})
        sources[path] = data
    return subject, blobs, sources


def run_live(
    *,
    repo: Path,
    bundle_path: Path,
    grammar_dir: Path,
    paths: list[str],
    omissions: list[dict[str, str]],
    record_dir: Path | None = None,
    receipt_path: Path | None = None,
) -> dict[str, Any]:
    binary = find_cli()
    if binary is None:
        raise Refusal("PROVIDER_ABSENT", "no tree-sitter executable on PATH and DTCR_TS_BIN unset")
    manifest = load_bundle(bundle_path)
    observed = digest_grammar_dir(grammar_dir, [entry["path"] for entry in manifest["grammar"]["files"]])
    if observed != manifest["grammar"]["files"]:
        raise Refusal(
            "WRONG_GRAMMAR_OR_GRAMMAR_DIGEST",
            f"the grammar at the resolved directory does not match the digests bundle "
            f"{manifest['bundle_id']} pinned; two builds of one language parse differently",
        )
    identity = cli_identity(binary)
    subject, blobs, sources = live_subject(repo, paths)
    query_path = manifest["_resolved_query_paths"][0]

    runs = []
    recorded_files: dict[str, dict[str, Any]] = {}
    for path in paths:
        parse = subprocess.run(
            [binary, "parse", "-p", str(grammar_dir), path],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        query = subprocess.run(
            [binary, "query", "-p", str(grammar_dir), query_path, path],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        runs.append(
            {
                "path": path,
                "source": sources[path],
                "parse_stdout": parse.stdout,
                "parse_exit": parse.returncode,
                "query_stdout": query.stdout,
                "query_exit": query.returncode,
            }
        )
        recorded_files[path] = {
            "parse_stdout": parse.stdout,
            "parse_exit": parse.returncode,
            "query_stdout": query.stdout,
            "query_exit": query.returncode,
        }

    bundle = emit_bundle(
        subject=subject,
        manifest=manifest,
        provider=identity,
        declared_blobs=blobs,
        runs=runs,
        omissions=omissions,
        warnings=["live provider run: tree-sitter executed on the host against the subject commit"],
    )
    if record_dir is not None:
        write_fixture(record_dir, bundle_path, subject, blobs, identity, recorded_files, sources, omissions)
    if receipt_path is not None:
        write_live_receipt(receipt_path, bundle, manifest, paths)
    return bundle


def write_live_receipt(receipt_path: Path, bundle: dict[str, Any], manifest: dict[str, Any], paths: list[str]) -> None:
    """What one real execution on one host observed.

    The binary's install path is deliberately absent. The frozen provider block
    admits a bare executable name because a path describes one machine, and a
    receipt that pins this adapter to a checkout would be replayed nowhere. The
    sha256 of the executable is the identity that travels."""
    block = bundle["matches"][0]["provider"]
    runs = bundle["receipt"]["provider_runs"]
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "dtcr/tree-sitter-live-receipt/v1",
        "subject": bundle["receipt"]["subject"],
        "paths": sorted(paths),
        "provider": {
            "provider_binding_id": block["provider_binding_id"],
            "executable_name": block["executable_name"],
            "version": block["version"],
            "executable_sha256": block["executable_sha256"],
            "executable_location": "resolved from DTCR_TS_BIN or PATH; the install path is one machine and is not part of the identity",
            "config_digest": block["config_digest"],
            "language": block["grammar"]["language"],
            "abi_version": block["grammar"]["abi_version"],
            "grammar_digest": block["grammar"]["grammar_digest"],
            "grammar_source": manifest["grammar"]["source"],
            "grammar_license": manifest["grammar"]["license"],
            "query_digest": block["query_digest"],
        },
        "bundle_id": manifest["bundle_id"],
        "manifest_digest": manifest["bundle_digest"],
        "bundle_digest": bundle["receipt"]["bundle_digest"],
        "matches": len(bundle["matches"]),
        "coverage": bundle["coverage_ceiling"]["analysed"],
        "completeness": bundle["coverage_ceiling"]["completeness"],
        "exit_codes": {"parse": runs[0]["exit_code"], "query": runs[1]["exit_code"]},
        "establishes": {
            "semantic_truth": False,
            "task_pass": False,
            "merge": False,
            "language_coverage": False,
            "provider_available_elsewhere": False,
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_fixture(
    record_dir: Path,
    bundle_path: Path,
    subject: dict[str, Any],
    blobs: list[dict[str, Any]],
    identity: dict[str, str],
    recorded_files: dict[str, dict[str, Any]],
    sources: dict[str, bytes],
    omissions: list[dict[str, str]],
) -> None:
    """Freeze one live run as a replayable fixture. The stdout is written as
    the provider produced it; the paths in it are the repo-relative ones the
    invocation was given, because a recorded machine path would make the
    fixture describe one checkout."""
    record_dir.mkdir(parents=True, exist_ok=True)
    recorded: dict[str, Any] = {}
    for path, run in recorded_files.items():
        stem = Path(path).name
        (record_dir / f"{stem}.parse.stdout").write_text(run["parse_stdout"], encoding="utf-8")
        (record_dir / f"{stem}.query.stdout").write_text(run["query_stdout"], encoding="utf-8")
        recorded[path] = {
            "source": stem,
            "parse_stdout": f"{stem}.parse.stdout",
            "parse_exit": run["parse_exit"],
            "query_stdout": f"{stem}.query.stdout",
            "query_exit": run["query_exit"],
        }
        (record_dir / stem).write_bytes(sources[path])
    request = {
        "schema": REQUEST_SCHEMA,
        "subject": subject,
        "bundle": os.path.relpath(bundle_path, record_dir),
        "provider": {"version": identity["version"], "executable_sha256": identity["executable_sha256"]},
        "declared_blobs": blobs,
        "omissions": omissions,
        "warnings": [
            "recorded-output replay: the provider did not run in this pass; the stdout was captured "
            "from a real run against the subject commit named above"
        ],
        "recorded": recorded,
    }
    (record_dir / "request.json").write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)

    replay = sub.add_parser("replay", help="emit from a recorded fixture request, no provider needed")
    replay.add_argument("request", type=Path)
    replay.add_argument("--out", type=Path)

    live = sub.add_parser("live", help="run the tree-sitter CLI against the subject commit")
    live.add_argument("--bundle", type=Path, required=True)
    live.add_argument("--grammar-dir", type=Path, required=True)
    live.add_argument("--path", action="append", required=True, dest="paths")
    live.add_argument("--repo", type=Path, default=Path.cwd())
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
                bundle_path=args.bundle.resolve(),
                grammar_dir=args.grammar_dir.resolve(),
                paths=args.paths,
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
    text = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
