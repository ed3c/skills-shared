#!/usr/bin/env python3
"""Read a committed case graph back against the exact commit it claims.

`scripts/check_case_graph.py` proves the graph is internally closed: every
required case has an owner, an oracle and recomputed coverage. It cannot prove
the graph is talking about real bytes -- a subject digest is just a string to
it. This entrypoint closes that gap for
`references/case-graph-local-handoff-wave1.json`:

    schema        the graph validates against references/case-graph.schema.json
    manifest      every pinned path is read back with `git cat-file` at
                  `subject.revision`, and its bytes must reproduce both the
                  recorded git blob name and the recorded sha256
    digest        the manifest recomputes to `subject.digest`
    readback      every `readback_assertions` entry on an oracle resolves its
                  JSON pointer inside those same committed bytes and equals the
                  recorded value

Bytes come from the commit, never from the working tree, so a sibling worker
advancing an unrelated file cannot turn this red and cannot turn it green
either. The claims live in the graph and the truth lives in the commit; only
their disagreement is reportable.

Exit: 0 the graph is bound to its subject, 2 a named binding violation,
64 the graph or the subject could not be read at all.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

from jsonschema import Draft202012Validator  # noqa: E402

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
GRAPH = SKILL_ROOT / "references" / "case-graph-local-handoff-wave1.json"
SCHEMA = SKILL_ROOT / "references" / "case-graph.schema.json"

DIGEST_RECIPE = "sha256 over sorted UTF-8 lines '<sha256>  <path>\\n'"


class UnusableInput(Exception):
    """The graph or the subject could not be read. Not a binding result."""


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise UnusableInput(f"{path}: {exc}") from exc


def git_blob(repo_root: Path, revision: str, path: str) -> bytes:
    """The committed bytes of one path, or an unusable-input stop."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "cat-file", "blob", f"{revision}:{path}"],
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise UnusableInput(f"git unavailable: {exc}") from exc
    if result.returncode != 0:
        raise UnusableInput(
            f"subject blob unreadable at {revision}:{path}: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout


def blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def manifest_digest(entries: list[tuple[str, str]]) -> str:
    body = "".join(f"{sha}  {path}\n" for path, sha in sorted(entries))
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


def resolve_pointer(document: Any, pointer: str) -> Any:
    """RFC 6901 JSON pointer. A miss is a value, not an exception."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise UnusableInput(f"malformed json pointer: {pointer!r}")
    node = document
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict):
            if token not in node:
                return f"<ABSENT at {pointer}>"
            node = node[token]
        elif isinstance(node, list):
            if not token.isdigit() or int(token) >= len(node):
                return f"<ABSENT at {pointer}>"
            node = node[int(token)]
        else:
            return f"<ABSENT at {pointer}>"
    return node


def check_schema(graph: Any, schema: Any) -> list[str]:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    return [f"SCHEMA_RED {error.message}" for error in validator.iter_errors(graph)]


def check_manifest(graph: Any, repo_root: Path) -> tuple[list[str], dict[str, Any]]:
    """Read every pinned path back at the subject revision."""
    findings: list[str] = []
    subject = graph.get("subject") or {}
    revision = subject.get("revision")
    manifest = subject.get("manifest")
    if not isinstance(manifest, list) or not manifest:
        raise UnusableInput("subject.manifest must be a non-empty array")
    if subject.get("manifest_digest_recipe") != DIGEST_RECIPE:
        findings.append(
            f"DIGEST_RECIPE_DRIFT recorded={subject.get('manifest_digest_recipe')!r} "
            f"expected={DIGEST_RECIPE!r}"
        )

    pairs: list[tuple[str, str]] = []
    committed: dict[str, Any] = {}
    for entry in manifest:
        path = entry.get("path")
        raw = git_blob(repo_root, revision, path)
        actual_sha256 = hashlib.sha256(raw).hexdigest()
        actual_blob = blob_sha1(raw)
        if actual_blob != entry.get("git_blob_sha1"):
            findings.append(
                f"BLOB_IDENTITY_DRIFT {path} committed={actual_blob} "
                f"recorded={entry.get('git_blob_sha1')}"
            )
        if actual_sha256 != entry.get("sha256"):
            findings.append(
                f"CONTENT_DIGEST_DRIFT {path} committed={actual_sha256} "
                f"recorded={entry.get('sha256')}"
            )
        pairs.append((path, actual_sha256))
        committed[path] = raw

    recomputed = manifest_digest(pairs)
    if recomputed != subject.get("digest"):
        findings.append(
            f"SUBJECT_DIGEST_DRIFT recomputed={recomputed} recorded={subject.get('digest')}"
        )
    return findings, committed


def check_readbacks(graph: Any, committed: dict[str, bytes]) -> tuple[list[str], int]:
    """Every recorded pointer claim must hold inside the committed bytes."""
    findings: list[str] = []
    checked = 0
    for oracle in graph.get("oracles", []):
        for assertion in oracle.get("readback_assertions", []) or []:
            checked += 1
            path = assertion.get("path")
            pointer = assertion.get("pointer")
            expected = assertion.get("equals")
            raw = committed.get(path)
            if raw is None:
                findings.append(
                    f"READBACK_OFF_MANIFEST {oracle.get('id')} {path} "
                    "is not pinned in subject.manifest"
                )
                continue
            try:
                document = json.loads(raw.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                findings.append(f"READBACK_UNPARSEABLE {path}: {exc}")
                continue
            actual = resolve_pointer(document, pointer)
            if actual != expected:
                findings.append(
                    f"READBACK_MISMATCH {oracle.get('id')} {path}{pointer} "
                    f"committed={actual!r} recorded={expected!r}"
                )
    return findings, checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, default=GRAPH)
    parser.add_argument("--schema", type=Path, default=SCHEMA)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    try:
        graph = read_json(args.graph)
        schema = read_json(args.schema)
        findings = check_schema(graph, schema)
        manifest_findings, committed = check_manifest(graph, args.repo_root.resolve())
        findings.extend(manifest_findings)
        readback_findings, checked = check_readbacks(graph, committed)
        findings.extend(readback_findings)
    except UnusableInput as exc:
        print(f"CASE-GRAPH-EVIDENCE-UNUSABLE {exc}", file=sys.stderr)
        return 64

    subject = graph.get("subject") or {}
    if findings:
        for finding in findings:
            print(f"CASE-GRAPH-EVIDENCE-RED {finding}", file=sys.stderr)
        return 2
    print(
        f"CASE-GRAPH-EVIDENCE-GREEN subject={subject.get('id')}@{subject.get('revision')[:8]} "
        f"pinned={len(committed)} readbacks={checked}; committed bytes only, "
        "no working-tree or live-runtime claim"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
