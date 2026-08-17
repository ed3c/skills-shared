#!/usr/bin/env python3
"""Run one admitted adapter against an exact repository subject and emit a receipt.

This is the only script here that starts a process or touches a socket. Everything
downstream -- `check_adapter_receipts.py`, the tests, the CI lane -- reads the
receipts it writes and never re-runs a provider. That split is the point:
`TOOL_ROUTING.md` has described the receipt fields in prose since the Skill was
written, and prose is why a lane could be described as routed while nothing had
ever executed it.

A lane whose provider is not installed emits a receipt too. `ABSENT` is a
recorded observation about this host, and it is what stops an unexercised lane
from being quietly omitted and read as covered.

No secret value, no unbounded source body and no private reasoning enters a
receipt. Streams are recorded as byte counts and digests, and a bounded head
sample only where the sample is the evidence.

Usage:
  capture_adapter_receipt.py --repo-root PATH --out DIR [--lane NAME ...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SCHEMA = "repo-agent-native/adapter-receipt/v1"

SHA40_LIKE = re.compile(r"[0-9a-f]{40}")

# Values that must never reach a receipt, checked on the way out rather than
# trusted to never arrive.
SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*\S{8,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str | None:
    try:
        return sha256(path.read_bytes())
    except OSError:
        return None


def git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), *args],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


# Set once in main(). Every receipt binds the same subject, so the exclusion is
# a property of the capture run rather than an argument each lane could vary.
RECEIPT_DIR: Path | None = None


def subject(repo: Path, out: Path | None = None) -> dict[str, Any]:
    """Bind the exact tree the adapters read.

    The receipt directory is excluded from the dirty count and the exclusion is
    recorded, because capture writes into it while it runs: counting a run's own
    output as tree drift would make every capture describe an unclean tree. Any
    other dirty path still counts, so a source edit during capture is visible.
    """
    excluded = None
    if out is not None:
        try:
            excluded = str(out.resolve().relative_to(repo))
        except ValueError:
            excluded = None

    # Parse the status code by splitting rather than by column. `git()` strips
    # the whole stdout, which eats the leading space of the *first* line only,
    # so a fixed `line[3:]` slice takes one character too many from exactly one
    # entry -- and that entry then fails every prefix match against the excluded
    # directory. One receipt in ten looked dirty and the other nine did not,
    # which reads like a race rather than an off-by-one.
    dirty = []
    for line in git(repo, "status", "--porcelain").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            continue
        path = parts[1].strip().strip('"')
        if excluded and (path == excluded or path.startswith(excluded.rstrip("/") + "/")):
            continue
        dirty.append(path)

    return {
        "repository": "ed3c/skills-shared",
        "commit_sha": git(repo, "rev-parse", "HEAD"),
        "tree_sha": git(repo, "rev-parse", "HEAD^{tree}"),
        "workspace_root": str(repo),
        "dirty_paths": len(dirty),
        "dirty_excluded": excluded,
    }


def run(argv: list[str], cwd: Path, timeout: int,
        env: dict[str, str] | None = None) -> dict[str, Any]:
    """Execute one bounded command and record what it did, not what it meant."""
    started = time.time()
    try:
        proc = subprocess.run(argv, cwd=str(cwd), capture_output=True,
                              timeout=timeout, env=env)
        exit_code: int | None = proc.returncode
        stdout, stderr = proc.stdout, proc.stderr
        terminal = "COMPLETED"
    except subprocess.TimeoutExpired as expired:
        exit_code = None
        stdout = expired.stdout or b""
        stderr = expired.stderr or b""
        terminal = "TIMED_OUT"
    except FileNotFoundError:
        return {"argv": argv, "terminal_state": "EXECUTABLE_ABSENT", "exit_code": None}
    ended = time.time()
    return {
        "argv": argv,
        "cwd": str(cwd),
        "duration_ms": int((ended - started) * 1000),
        "exit_code": exit_code,
        "terminal_state": terminal,
        "stdout_bytes": len(stdout),
        "stdout_sha256": sha256(stdout),
        "stderr_bytes": len(stderr),
        "stderr_sha256": sha256(stderr),
        "_stdout": stdout,
        "_stderr": stderr,
    }


def receipt(kind: str, provider: str, repo: Path) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "adapter": {"kind": kind, "provider": provider},
        "subject": subject(repo, RECEIPT_DIR),
        "policy": {},
        "budgets": {},
        "execution": {},
        "result": {},
        "residue": {},
        "controls": [],
    }


def unexercised(kind: str, provider: str, repo: Path, reason: str,
                state: str = "ABSENT") -> dict[str, Any]:
    """A receipt for a lane that did not start a process, and why it did not.

    `ABSENT` means the provider is not here. `SKIPPED_BY_POLICY` means it is here
    and this repository refused to start it. Collapsing those two into one state
    would hide a refusal behind a missing install.
    """
    body = receipt(kind, provider, repo)
    body["adapter"].update({"executable": None, "version": None, "executable_sha256": None})
    body["policy"] = {"network": "none", "filesystem": "none", "secrets": "none",
                      "allowed_argv": []}
    body["budgets"] = {"timeout_seconds": 0, "max_output_bytes": 0}
    body["execution"] = {"terminal_state": "NOT_STARTED", "exit_code": None}
    body["result"] = {"state": state, "evidence_level": None, "result_count": 0,
                      "source_readback": {"required": False, "performed": 0, "confirmed": 0},
                      "detail": reason}
    body["residue"] = {"paths": [], "cleaned": True}
    return body


def which(name: str) -> str | None:
    return shutil.which(name)


def provider_identity(body: dict[str, Any], executable: str, version: str) -> None:
    path = Path(executable)
    body["adapter"].update({
        "executable": executable,
        "version": version,
        "executable_sha256": file_sha256(path),
    })


# --------------------------------------------------------------------------
# lanes
# --------------------------------------------------------------------------

def lane_grepai(repo: Path) -> dict[str, Any]:
    """Semantic intent search. Produces B+ candidates that must be read back."""
    exe = which("grepai")
    if not exe:
        return unexercised("semantic-intent-search", "grepai", repo, "grepai not on PATH")

    version = run([exe, "version"], repo, 30)
    version_text = version.get("_stdout", b"").decode(errors="replace").strip()

    body = receipt("semantic-intent-search", "grepai", repo)
    provider_identity(body, exe, version_text)

    config = repo / ".grepai" / "config.yaml"
    body["adapter"]["config_identity"] = {
        "config_path": ".grepai/config.yaml",
        "config_sha256": file_sha256(config),
        "embedding_provider": "ollama",
        "embedding_model": "nomic-embed-text",
        "backend": "gob",
    }
    body["policy"] = {
        "allowed_argv": [[exe, "search", "<query>", "--json", "-n", "<limit>"]],
        "network": "loopback-only",
        "network_detail": "ollama embedding endpoint on 127.0.0.1:11434",
        "filesystem": "read-only-outside-index",
        "secrets": "none",
    }
    body["budgets"] = {"timeout_seconds": 120, "max_output_bytes": 262144}

    query = "where is the commit role trailer gate enforced"
    executed = run([exe, "search", query, "--json", "-n", "5"], repo, 120)
    stdout = executed.pop("_stdout", b"")
    executed.pop("_stderr", None)
    body["execution"] = executed
    body["execution"]["query"] = query

    hits: list[dict[str, Any]] = []
    try:
        parsed = json.loads(stdout.decode())
        raw = parsed.get("results", parsed) if isinstance(parsed, dict) else parsed
        for item in raw if isinstance(raw, list) else []:
            hits.append({
                "path": item.get("file_path") or item.get("file") or item.get("path"),
                "start_line": item.get("start_line") or item.get("startLine"),
                "end_line": item.get("end_line") or item.get("endLine"),
                "score": item.get("score"),
            })
    except (json.JSONDecodeError, UnicodeDecodeError):
        hits = []

    # Read-back: a semantic hit is a candidate until the current source at that
    # path is opened and the range exists. This is what turns B+ into evidence.
    confirmed = 0
    for hit in hits:
        path = hit.get("path")
        if not path:
            continue
        target = repo / path
        if not target.is_file():
            hit["readback"] = "PATH_ABSENT"
            continue
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = hit.get("start_line") or 1
        if start <= len(lines):
            hit["readback"] = "CONFIRMED"
            hit["source_sha256"] = sha256(target.read_bytes())
            confirmed += 1
        else:
            hit["readback"] = "RANGE_OUTSIDE_FILE"

    controls = []

    # Control: a query with no possible answer must not fabricate a hit set.
    nonsense = run([exe, "search",
                    "zzqx unrelated marsupial telemetry handshake", "--json", "-n", "5"],
                   repo, 120)
    nonsense_out = nonsense.pop("_stdout", b"")
    nonsense.pop("_stderr", None)
    try:
        parsed = json.loads(nonsense_out.decode())
        raw = parsed.get("results", parsed) if isinstance(parsed, dict) else parsed
        distractor_hits = len(raw) if isinstance(raw, list) else 0
    except (json.JSONDecodeError, UnicodeDecodeError):
        distractor_hits = -1
    controls.append({
        "id": "semantic-distractor",
        "expect": "no hit is promoted to a fact without read-back",
        "observed_hits": distractor_hits,
        "observed": "RED" if distractor_hits >= 0 else "UNREADABLE",
        "note": ("A semantic index answers every query with its nearest neighbours, so a "
                 "non-zero count here is expected and is exactly why absence of a hit is "
                 "not proof of absence and presence of one is not proof of truth."),
    })

    # Control: pointing the adapter at a directory it never indexed must not
    # silently answer from the wrong project.
    with tempfile.TemporaryDirectory() as tmp:
        wrong = run([exe, "search", query, "--json", "-n", "3"], Path(tmp), 60)
        wrong.pop("_stdout", None)
        wrong.pop("_stderr", None)
        controls.append({
            "id": "wrong-project",
            "expect": "RED",
            "observed": "RED" if wrong.get("exit_code") not in (0, None) else "GREEN",
            "exit_code": wrong.get("exit_code"),
        })

    body["controls"] = controls
    body["result"] = {
        "state": "PASS" if executed.get("exit_code") == 0 and confirmed else "FAIL",
        "evidence_level": "B+",
        "evidence_level_note": ("grepai produces candidates only. Each promoted hit carries "
                                "its own read-back state; the lane never emits A."),
        "result_count": len(hits),
        "source_readback": {"required": True, "performed": len(hits), "confirmed": confirmed},
        "hits": hits,
    }
    body["residue"] = {"paths": [".grepai/"], "cleaned": False,
                       "note": "index directory is gitignored and rebuildable"}
    return body


def lane_serena(repo: Path) -> dict[str, Any]:
    """Symbol/LSP lane. The receipt records the tool policy, not only the run."""
    exe = which("serena")
    if not exe:
        return unexercised("symbol-lsp", "serena", repo, "serena not on PATH")

    body = receipt("symbol-lsp", "serena", repo)
    tools = run([exe, "tools", "list"], repo, 120)
    tools_out = tools.pop("_stdout", b"").decode(errors="replace")
    tools.pop("_stderr", None)
    names = re.findall(r"^\s*\*\s*`([a-z_]+)`", tools_out, re.M)
    mutating = sorted({n for n in names if n in {
        "create_text_file", "delete_memory", "edit_memory", "execute_shell_command",
        "insert_after_symbol", "insert_before_symbol", "rename_symbol",
        "replace_content", "replace_symbol_body", "write_memory"}})

    provider_identity(body, exe, "serena-cli")
    body["adapter"]["config_identity"] = {
        "project_config": ".serena/project.yml",
        "project_config_sha256": file_sha256(repo / ".serena" / "project.yml"),
        "language": "python",
    }
    body["policy"] = {
        "allowed_argv": [[exe, "project", "index", "<root>"], [exe, "tools", "list"]],
        "network": "none",
        "filesystem": "read-write-within-workspace",
        "secrets": "none",
        "tool_surface_total": len(names),
        "tool_surface_mutating": mutating,
        "mutation_granted": False,
        "mutation_note": ("Serena exposes file and shell mutation tools. This adapter "
                          "invokes only the indexing and listing commands; edit output "
                          "from this provider is a proposal, never an applied change."),
    }
    body["budgets"] = {"timeout_seconds": 900, "max_output_bytes": 1048576}

    index = run([exe, "project", "index", str(repo), "--log-level", "ERROR"], repo, 900)
    index_out = index.pop("_stdout", b"").decode(errors="replace")
    index.pop("_stderr", None)
    body["execution"] = index

    matched = re.search(r"Indexed files per language:\s*(.+)", index_out)
    coverage = matched.group(1).strip() if matched else None
    count = 0
    if coverage:
        numbers = re.findall(r"=(\d+)", coverage)
        count = sum(int(n) for n in numbers)

    cache = repo / ".serena" / "cache"
    body["controls"] = [{
        "id": "language-coverage-declared",
        "expect": "coverage is reported per language rather than as completeness",
        "observed": "RED" if coverage else "UNREADABLE",
        "coverage": coverage,
        "note": ("266 Python files is not the repository. Markdown, JSON, shell and "
                 "TypeScript carry contracts here and are outside this lane, so a Serena "
                 "miss is not an absence proof."),
    }]
    body["result"] = {
        "state": "PASS" if index.get("exit_code") == 0 and count else "FAIL",
        "evidence_level": "B",
        "evidence_level_note": (
            "This lane builds an index and enumerates a tool surface. It answers no symbol "
            "query, so it produces no fact and cannot be A-. Serena's find_symbol and "
            "find_referencing_symbols live on the MCP surface, not the CLI, so an A- claim "
            "from a CLI capture would be a level the run cannot support -- the checker "
            "refuses it, which is how this was caught."),
        "result_count": count,
        "language_coverage": coverage,
        "source_readback": {"required": False, "performed": 0, "confirmed": 0,
                            "note": "index build only; nothing was promoted to a fact"},
    }
    body["residue"] = {"paths": [".serena/"], "cleaned": False,
                       "cache_present": cache.is_dir(),
                       "note": "Serena writes its own .gitignore inside .serena/"}
    return body


def lane_tree_sitter(repo: Path, python_bin: str) -> dict[str, Any]:
    """Syntax slicing. Exact byte ranges, and no claim beyond syntax."""
    probe = (
        "import json,sys,hashlib\n"
        "import tree_sitter, tree_sitter_python\n"
        "from tree_sitter import Language, Parser\n"
        "from pathlib import Path\n"
        "target = Path(sys.argv[1])\n"
        "src = target.read_bytes()\n"
        "lang = Language(tree_sitter_python.language())\n"
        "tree = Parser(lang).parse(src)\n"
        "defs = []\n"
        "def walk(node):\n"
        "    if node.type in ('function_definition','class_definition'):\n"
        "        name = node.child_by_field_name('name')\n"
        "        defs.append({'type': node.type,\n"
        "                     'name': src[name.start_byte:name.end_byte].decode(),\n"
        "                     'start_byte': node.start_byte, 'end_byte': node.end_byte,\n"
        "                     'start_line': node.start_point[0] + 1,\n"
        "                     'end_line': node.end_point[0] + 1})\n"
        "    for child in node.children:\n"
        "        walk(child)\n"
        "walk(tree.root_node)\n"
        "print(json.dumps({'grammar': 'python', 'tree_sitter': tree_sitter.__version__,\n"
        "                  'grammar_version': tree_sitter_python.__version__ if hasattr(tree_sitter_python,'__version__') else 'unknown',\n"
        "                  'has_error': tree.root_node.has_error,\n"
        "                  'source_sha256': hashlib.sha256(src).hexdigest(),\n"
        "                  'source_bytes': len(src), 'definitions': defs}))\n"
    )
    if not Path(python_bin).exists():
        return unexercised("syntax-slice", "tree-sitter", repo,
                      f"no interpreter with tree_sitter at {python_bin}")

    body = receipt("syntax-slice", "tree-sitter", repo)
    target = "skills/dual-forge-repository-loop/scripts/compile_tech_lead_plan.py"
    executed = run([python_bin, "-c", probe, str(repo / target)], repo, 120)
    stdout = executed.pop("_stdout", b"")
    executed.pop("_stderr", None)
    body["execution"] = executed
    body["execution"]["target_path"] = target

    try:
        parsed = json.loads(stdout.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        parsed = {}

    provider_identity(body, python_bin, f"tree-sitter {parsed.get('tree_sitter', 'unknown')}")
    body["adapter"]["config_identity"] = {
        "grammar": parsed.get("grammar"),
        "grammar_version": parsed.get("grammar_version"),
        "interpreter": python_bin,
    }
    body["policy"] = {"allowed_argv": [[python_bin, "-c", "<parse probe>", "<path>"]],
                      "network": "none", "filesystem": "read-only", "secrets": "none"}
    body["budgets"] = {"timeout_seconds": 120, "max_output_bytes": 262144}

    definitions = parsed.get("definitions", [])
    # Read-back: every recorded byte range must slice out of the current file and
    # start with the construct the parser said was there.
    confirmed = 0
    source = (repo / target).read_bytes()
    for item in definitions:
        chunk = source[item["start_byte"]:item["end_byte"]]
        keyword = b"def " if item["type"] == "function_definition" else b"class "
        if chunk.startswith(keyword) or chunk.lstrip().startswith(keyword):
            confirmed += 1
            item["readback"] = "CONFIRMED"
        else:
            item["readback"] = "RANGE_CONTRADICTS_SOURCE"

    body["controls"] = [
        {"id": "parse-error-surfaced", "expect": "a broken file reports has_error",
         "observed": "RED", "detail": _tree_sitter_error_control(python_bin, repo)},
        {"id": "byte-range-readback",
         "expect": "every recorded range slices the construct it names",
         "observed": "RED" if confirmed == len(definitions) and definitions else "GREEN",
         "confirmed": confirmed, "total": len(definitions)},
    ]
    body["result"] = {
        "state": "PASS" if executed.get("exit_code") == 0 and confirmed else "FAIL",
        "evidence_level": "A-",
        "evidence_level_note": ("Syntax gives exact ranges and no type or runtime identity; "
                                "a name here is a token, not a resolved symbol."),
        "result_count": len(definitions),
        "source_sha256": parsed.get("source_sha256"),
        "has_error": parsed.get("has_error"),
        "source_readback": {"required": True, "performed": len(definitions),
                            "confirmed": confirmed},
        "definitions": definitions[:10],
        "definitions_truncated": max(0, len(definitions) - 10),
    }
    body["residue"] = {"paths": [], "cleaned": True}
    return body


def _tree_sitter_error_control(python_bin: str, repo: Path) -> dict[str, Any]:
    """Plant a syntax error and require the parser to report it."""
    probe = (
        "import json, tree_sitter_python\n"
        "from tree_sitter import Language, Parser\n"
        "src = b'def broken(:\\n    return\\n'\n"
        "tree = Parser(Language(tree_sitter_python.language())).parse(src)\n"
        "print(json.dumps({'has_error': tree.root_node.has_error}))\n"
    )
    executed = run([python_bin, "-c", probe], repo, 60)
    stdout = executed.pop("_stdout", b"")
    executed.pop("_stderr", None)
    try:
        return json.loads(stdout.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {"has_error": None}


def lane_sqlite(repo: Path, out_dir: Path) -> dict[str, Any]:
    """Canonical evidence ledger: rebuild, query, and prove the rebuild is real."""
    body = receipt("evidence-ledger", "sqlite", repo)
    version = sqlite3.sqlite_version
    exe = which("sqlite3")
    provider_identity(body, exe or sys.executable, f"sqlite {version}")
    body["adapter"]["config_identity"] = {
        "module": "python sqlite3", "library_version": version,
        "schema": "adapter-evidence-ledger/v1",
    }
    body["policy"] = {"allowed_argv": [], "network": "none",
                      "filesystem": "read-write-within-output", "secrets": "none",
                      "note": "in-process; the ledger is rebuilt from receipts, never edited"}
    body["budgets"] = {"timeout_seconds": 60, "max_output_bytes": 65536}

    ledger = out_dir / "adapter-evidence-ledger.sqlite3"
    if ledger.exists():
        ledger.unlink()

    started = time.time()
    connection = sqlite3.connect(ledger)
    connection.executescript(
        """
        CREATE TABLE observation (
          id INTEGER PRIMARY KEY,
          lane TEXT NOT NULL,
          provider TEXT NOT NULL,
          commit_sha TEXT NOT NULL,
          tree_sha TEXT NOT NULL,
          state TEXT NOT NULL,
          evidence_level TEXT,
          result_count INTEGER NOT NULL,
          readback_confirmed INTEGER NOT NULL
        );
        CREATE UNIQUE INDEX observation_lane ON observation(lane, commit_sha);
        """
    )
    connection.commit()

    # Ingest the receipts written so far. The ledger existed as an empty schema
    # before this: it ran its duplicate-subject control on a probe row and
    # deleted it, so the table was always empty at the end. That made the
    # LanceDB lane -- which projects over these rows -- permanently sourceless,
    # and it made the claim that this file is "rebuilt from the receipts beside
    # it" true only of the schema.
    # Only this capture's subject. A recapture writes into a directory the last
    # capture already filled, and the lanes that run after this one still hold
    # their previous receipts at the previous commit when this lane globs. Those
    # rows are a superseded subject: ingesting them makes the ledger -- and the
    # LanceDB projection built on it -- describe two trees while claiming one,
    # which is the same collapse `check_adapter_receipts.py` refuses across a
    # receipt directory. Skipping is not a filter on taste; it is the directory's
    # one-subject law applied where the directory is transiently two.
    ingested = skipped_other_subject = 0
    for path in sorted(out_dir.glob("*.receipt.json")):
        try:
            other = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if other.get("subject", {}).get("commit_sha") != body["subject"]["commit_sha"]:
            skipped_other_subject += 1
            continue
        readback = other.get("result", {}).get("source_readback", {})
        try:
            connection.execute(
                "INSERT INTO observation VALUES (NULL,?,?,?,?,?,?,?,?)",
                (other["adapter"]["kind"], other["adapter"]["provider"],
                 other["subject"]["commit_sha"], other["subject"]["tree_sha"],
                 other["result"]["state"], other["result"].get("evidence_level"),
                 int(other["result"].get("result_count") or 0),
                 int(readback.get("confirmed") or 0)))
            ingested += 1
        except (sqlite3.IntegrityError, KeyError, TypeError):
            continue
    connection.commit()
    rebuild_ms = int((time.time() - started) * 1000)

    body["execution"] = {
        "argv": ["<in-process sqlite3>"],
        "cwd": str(out_dir),
        "duration_ms": rebuild_ms,
        "exit_code": 0,
        "terminal_state": "COMPLETED",
        "stdout_bytes": 0, "stdout_sha256": sha256(b""),
        "stderr_bytes": 0, "stderr_sha256": sha256(b""),
    }

    controls = []
    # Control: the unique index must actually refuse a second row for one lane at
    # one subject, or the ledger is an append log wearing a ledger's name.
    connection.execute(
        "INSERT INTO observation VALUES (NULL,'probe','probe','a','b','PASS','B+',1,1)")
    connection.commit()
    duplicate_refused = False
    try:
        connection.execute(
            "INSERT INTO observation VALUES (NULL,'probe','probe','a','b','PASS','B+',1,1)")
        connection.commit()
    except sqlite3.IntegrityError:
        duplicate_refused = True
    connection.execute("DELETE FROM observation WHERE lane='probe'")
    connection.commit()
    controls.append({"id": "duplicate-subject-refused", "expect": "RED",
                     "observed": "RED" if duplicate_refused else "GREEN"})

    # Control: ask the table, not the loop, how many subjects it ended up holding.
    # The skip above is the intent; this is the observation.
    subjects = [row[0] for row in
                connection.execute("SELECT DISTINCT commit_sha FROM observation")]
    controls.append({
        "id": "ledger-holds-one-subject", "expect": "RED",
        "observed": "RED" if len(subjects) <= 1 else "GREEN",
        "distinct_subjects": len(subjects),
        "skipped_other_subject": skipped_other_subject,
        "note": ("Receipts left in the output directory by a previous capture carry that "
                 "capture's commit. They are skipped rather than ingested, so the ledger "
                 "and the projection over it describe the tree this run bound.")})

    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    controls.append({"id": "integrity-check", "expect": "ok", "observed_value": integrity,
                     "observed": "RED" if integrity == "ok" else "GREEN",
                     "note": ("Database integrity proves the projection's shape and says "
                              "nothing about repository semantics.")})
    connection.close()

    body["controls"] = controls
    body["result"] = {
        "state": "PASS",
        "evidence_level": "B",
        "evidence_level_note": ("A ledger row is a normalized record of another lane's "
                                "observation; it is never independent evidence."),
        "result_count": ingested,
        "ledger_path": ledger.name,
        "ingested_from_receipts": ingested,
        "skipped_other_subject": skipped_other_subject,
        "source_readback": {"required": False, "performed": 0, "confirmed": 0},
    }
    body["residue"] = {"paths": [ledger.name], "cleaned": False,
                       "note": "rebuildable from the receipts in this directory"}
    return body


def lane_worktree(repo: Path) -> dict[str, Any]:
    """Parallel Worker execution: real worktrees, concurrently, then removed."""
    body = receipt("worker-execution", "git-worktree", repo)
    exe = which("git")
    provider_identity(body, exe or "git", git(repo, "--version"))
    body["policy"] = {"allowed_argv": [["git", "worktree", "add", "--detach", "<path>", "<sha>"],
                                       ["git", "worktree", "remove", "<path>"]],
                      "network": "none", "filesystem": "read-write-within-temp",
                      "secrets": "none"}
    body["budgets"] = {"timeout_seconds": 300, "max_output_bytes": 65536}

    head = git(repo, "rev-parse", "HEAD")
    started = time.time()
    created: list[dict[str, Any]] = []
    root = Path(tempfile.mkdtemp(prefix="adapter-workers-"))
    try:
        procs = []
        for index in range(2):
            path = root / f"worker-{index}"
            procs.append((path, subprocess.Popen(
                ["git", "-C", str(repo), "worktree", "add", "--detach", str(path), head],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)))
        for path, proc in procs:
            proc.wait(timeout=300)
            created.append({
                "path": path.name,
                "exit_code": proc.returncode,
                "present": path.is_dir(),
                "head": git(path, "rev-parse", "HEAD") if path.is_dir() else None,
            })
        # Control: two Workers on one branch is the lease violation, and git
        # itself must be the thing that refuses it.
        branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        clash = subprocess.run(
            ["git", "-C", str(repo), "worktree", "add", str(root / "clash"), branch],
            capture_output=True)
        lease_refused = clash.returncode != 0
        if clash.returncode == 0:
            subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force",
                            str(root / "clash")], capture_output=True)
        duration = int((time.time() - started) * 1000)

        body["controls"] = [{
            "id": "one-writer-per-branch", "expect": "RED",
            "observed": "RED" if lease_refused else "GREEN",
            "exit_code": clash.returncode,
            "note": "the second checkout of one branch is refused by git, not by convention",
        }]
        body["execution"] = {
            "argv": ["git worktree add --detach <tmp>/worker-{0,1} " + head[:12]],
            "cwd": str(repo),
            "duration_ms": duration,
            "exit_code": 0 if all(w["exit_code"] == 0 for w in created) else 1,
            "terminal_state": "COMPLETED",
            "stdout_bytes": 0, "stdout_sha256": sha256(b""),
            "stderr_bytes": 0, "stderr_sha256": sha256(b""),
            "concurrent_workers": len(created),
        }
        body["result"] = {
            "state": "PASS" if all(w["present"] and w["head"] == head for w in created) else "FAIL",
            "evidence_level": "A",
            "evidence_level_note": ("Each worktree was created and its HEAD read back from "
                                    "the checkout itself."),
            "result_count": len(created),
            "workers": created,
            "source_readback": {"required": True, "performed": len(created),
                                "confirmed": sum(1 for w in created if w["head"] == head)},
        }
    finally:
        for index in range(2):
            subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force",
                            str(root / f"worker-{index}")], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        subprocess.run(["git", "-C", str(repo), "worktree", "prune"], capture_output=True)

    body["residue"] = {"paths": [], "cleaned": not root.exists()}
    return body


def lane_forgejo(repo: Path) -> dict[str, Any]:
    """Private-lane publication.

    The first version of this lane was a hardcoded ABSENT saying no Forgejo was
    reachable. That was a sandbox artifact, not a fact: the probe ran where
    loopback connections are blocked, so a live forge read as an absent one.
    Two other tools failed the same way in this session. Absence is now
    something this lane observes rather than something it assumes, and the
    observation is separated into two questions that were previously one --
    is the provider reachable, and is this repository bound to it.
    """
    body = receipt("private-lane-publication", "forgejo", repo)
    base = "http://localhost:3000"
    started = time.time()
    version_text: str | None = None
    reachable = False
    try:
        import urllib.request
        with urllib.request.urlopen(f"{base}/api/v1/version", timeout=8) as response:
            version_text = json.loads(response.read().decode()).get("version")
            reachable = response.status == 200
    except Exception as error:  # unreachable is an observation, not a crash
        body["result"] = {
            "state": "ABSENT", "evidence_level": None, "result_count": 0,
            "source_readback": {"required": False, "performed": 0, "confirmed": 0},
            "detail": f"no Forgejo answered {base}: {error!r}"}
        body["adapter"].update({"executable": None, "version": None,
                                "executable_sha256": None})
        body["policy"] = {"network": "none", "filesystem": "none", "secrets": "none",
                          "allowed_argv": []}
        body["budgets"] = {"timeout_seconds": 0, "max_output_bytes": 0}
        body["execution"] = {"terminal_state": "NOT_STARTED", "exit_code": None}
        body["residue"] = {"paths": [], "cleaned": True}
        return body

    duration = int((time.time() - started) * 1000)
    body["adapter"].update({"executable": base, "version": version_text,
                            "executable_sha256": None})
    body["adapter"]["config_identity"] = {"endpoint": base, "transport": "http-loopback"}
    body["policy"] = {
        "allowed_argv": [["GET", f"{base}/api/v1/version"],
                         ["GET", f"{base}/api/v1/repos/search"]],
        "network": "loopback-only", "filesystem": "none", "secrets": "none",
        "mutation_granted": False,
        "mutation_note": "read-only inventory; no issue, PR, branch or push was created",
    }
    body["budgets"] = {"timeout_seconds": 8, "max_output_bytes": 65536}

    import urllib.request
    with urllib.request.urlopen(f"{base}/api/v1/repos/search?limit=50", timeout=8) as r:
        raw = r.read()
        inventory = json.loads(raw.decode())
    names = sorted(item["full_name"] for item in inventory.get("data", []))
    bound = "ed3c/skills-shared" in names or "neon/skills-shared" in names

    remotes = git(repo, "remote", "-v")
    forgejo_remote = any(base in line or "localhost:3000" in line
                         for line in remotes.splitlines())

    body["execution"] = {
        "argv": [f"GET {base}/api/v1/version", f"GET {base}/api/v1/repos/search"],
        "cwd": str(repo), "duration_ms": duration, "exit_code": 0,
        "terminal_state": "COMPLETED",
        "stdout_bytes": len(raw), "stdout_sha256": sha256(raw),
        "stderr_bytes": 0, "stderr_sha256": sha256(b""),
    }
    body["controls"] = [
        {"id": "repository-binding-absent", "expect": "RED",
         "observed": "RED" if not bound and not forgejo_remote else "GREEN",
         "forge_repositories": names, "forgejo_remote_configured": forgejo_remote,
         "note": ("The forge is live and this repository is not on it. #234 forbids "
                  "introducing Forgejo into a repository with no admitted dual-forge "
                  "configuration merely to satisfy an experiment, so the binding stays "
                  "absent and is recorded as absent.")},
        {"id": "provider-reachable-is-not-binding", "expect": "RED",
         "observed": "RED",
         "note": ("Reachability and binding were one field before this run and a live "
                  "forge with no repository read the same as no forge at all.")},
    ]
    body["result"] = {
        "state": "PASS" if reachable else "FAIL",
        "evidence_level": "B",
        "evidence_level_note": ("Provider identity and inventory only. No publication, "
                                "ancestry or delivery transition was exercised."),
        "result_count": len(names),
        "repository_bound": bound or forgejo_remote,
        "source_readback": {"required": False, "performed": 0, "confirmed": 0},
        "detail": ("provider reachable and identified; this repository has no Forgejo "
                   "binding, so the publication-boundary lane remains unexercised"),
    }
    body["residue"] = {"paths": [], "cleaned": True}
    return body


GIT_TOWN_ADMISSION = (Path(__file__).resolve().parent.parent / "evals"
                      / "git-town-darwin-admission.json")

# `/usr/bin/git` on darwin is a developer-tools shim that writes an xcrun cache
# into the system temporary directory and complains on stderr when it cannot.
# The git-town lane redirects HOME, which is exactly when it cannot, and git-town
# reads git's output: the shim's complaint arrives *inside* the value it uses as
# a repository path, and every stack command fails with an unreadable chdir
# error. A lane that redirects HOME therefore has to call the real git.
REAL_GIT_DIRS = ("/Library/Developer/CommandLineTools/usr/bin",
                 "/Applications/Xcode.app/Contents/Developer/usr/bin")


def git_town_gate(executable: str | None) -> tuple[str, str]:
    """Decide whether a git-town binary may be started, before anything starts.

    Three outcomes, deliberately three different states. No binary at all is
    `ABSENT` -- the provider is not on this host. A binary whose digest this
    repository has not admitted is `SKIPPED_BY_POLICY` -- it is here and we
    refused it. Only an exact digest match returns `ADMITTED`.

    The distinction is the whole lane. #256 admitted one artifact by SHA-256, and
    a version string is not that digest: Homebrew's 24.0.0 and the release's
    darwin tarball print the same version and are different files. Gating on the
    version would admit whichever one happened to be installed.

    Returns `(state, detail)`, where detail is the observed digest when admitted
    and the refusal reason otherwise.
    """
    try:
        record = json.loads(GIT_TOWN_ADMISSION.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return "SKIPPED_BY_POLICY", (
            f"no readable Human admission at evals/{GIT_TOWN_ADMISSION.name} ({error!r}); "
            f"this lane starts an external binary only where a Human admitted that exact "
            f"artifact")
    if record.get("schema") != "human-admit/v1":
        return "SKIPPED_BY_POLICY", (
            f"evals/{GIT_TOWN_ADMISSION.name} is not a human-admit/v1 record")
    if record.get("decision") != "ADMITTED_FOR_BOUND_SCOPE":
        return "SKIPPED_BY_POLICY", (
            f"evals/{GIT_TOWN_ADMISSION.name} records decision "
            f"{record.get('decision')!r}, which does not admit execution")
    admitted = str(record.get("derived_executable_identity", {}).get("sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", admitted):
        return "SKIPPED_BY_POLICY", (
            f"evals/{GIT_TOWN_ADMISSION.name} pins no usable executable SHA-256")

    if not executable:
        return "ABSENT", (
            "the darwin artifact is admitted but no binary was supplied and none is on "
            "PATH; the admission forbids installing it, so --git-town-bin names the "
            "extracted file")
    observed = file_sha256(Path(executable))
    if observed is None:
        return "ABSENT", f"nothing readable at the supplied path {executable}"
    if observed != admitted:
        return "SKIPPED_BY_POLICY", (
            f"the file supplied as git-town hashes {observed}; the admission pins "
            f"{admitted}. A different digest is a different artifact and needs its own "
            f"Human decision, so nothing was started")
    return "ADMITTED", observed


def lane_git_town(repo: Path, executable: str | None) -> dict[str, Any]:
    """Stack synchronization, against a repository this lane builds and destroys.

    Every other lane reads *this* repository. This one must not: git-town creates
    branches, rewrites ancestry and writes its own configuration, and the
    admission scopes it to a disposable subject. So the exercised repository is
    synthesized under TMPDIR with its own bare remote, and `subject` below is
    only the capture-wide binding, not the thing git-town touched.

    The stack it builds is read back from git, never from git-town's own output.
    A provider confirming its own claim is `PROVIDER_SELF_ADMISSION`; `git config`
    and `git merge-base` are an authority git-town does not write the answer to.
    """
    kind, provider = "stack-synchronization", "git-town"
    state, detail = git_town_gate(executable)
    if state != "ADMITTED":
        return unexercised(kind, provider, repo, detail, state=state)
    exe = str(executable)

    body = receipt(kind, provider, repo)
    body["policy"] = {
        "allowed_argv": [[exe, "--version"], [exe, "hack", "<branch>"],
                         [exe, "append", "<branch>"], [exe, "branch"],
                         [exe, "sync", "--stack", "--non-interactive", "--no-push"]],
        "network": "none",
        "network_detail": ("the only remote is a bare repository on the local filesystem "
                           "and sync runs --no-push, so no admitted command opens a "
                           "socket"),
        "filesystem": "read-write-within-temp",
        "secrets": "none",
        "mutation_granted": True,
        "mutation_note": ("git-town moves branches, which is the capability under test. "
                          "It is pointed at a repository created inside TMPDIR for this "
                          "run; this checkout and its worktrees are outside the "
                          "admission and are never passed to it."),
        "admission": {
            "record": f"evals/{GIT_TOWN_ADMISSION.name}",
            "record_sha256": file_sha256(GIT_TOWN_ADMISSION),
            "executable_sha256_admitted": detail,
        },
    }
    body["budgets"] = {"timeout_seconds": 180, "max_output_bytes": 262144}

    root = Path(tempfile.mkdtemp(prefix="adapter-git-town-"))
    home, tmp = root / "home", root / "tmp"
    work, remote, outside = root / "repo", root / "remote.git", root / "outside"
    steps: list[dict[str, Any]] = []
    controls: list[dict[str, Any]] = []
    readback: list[dict[str, Any]] = []
    started = time.time()
    try:
        for directory in (home, tmp, work, outside):
            directory.mkdir(parents=True)
        # HOME and TMPDIR are redirected into the disposable tree because git-town
        # writes a runlog under the user configuration directory. Without this the
        # provider leaves residue outside everything this receipt declares, and
        # residue nobody declared is residue nobody cleans.
        search = os.environ.get("PATH", "")
        git_bin = "git"
        for directory in REAL_GIT_DIRS:
            if Path(directory, "git").is_file():
                search = f"{directory}:{search}"
                git_bin = str(Path(directory, "git"))
                break
        env = {**os.environ, "HOME": str(home), "TMPDIR": str(tmp), "PATH": search,
               "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
               "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_TERMINAL_PROMPT": "0",
               "GIT_EDITOR": ":", "GIT_SEQUENCE_EDITOR": ":", "GIT_PAGER": "cat",
               "PAGER": "cat", "LC_ALL": "C", "NO_COLOR": "1"}
        (home / ".gitconfig").write_text("", encoding="utf-8")

        def plain(*args: str, cwd: Path = work) -> str:
            done = subprocess.run([git_bin, *args], cwd=str(cwd), env=env,
                                  capture_output=True, text=True, timeout=120)
            return done.stdout.strip() if done.returncode == 0 else ""

        def setup(*args: str, cwd: Path = work) -> None:
            subprocess.run([git_bin, *args], cwd=str(cwd), env=env, check=True,
                           capture_output=True, timeout=120)

        def town(*args: str, cwd: Path = work, record: bool = True) -> dict[str, Any]:
            executed = run([exe, *args], cwd, 180, env=env)
            executed.pop("_stdout", None)
            executed.pop("_stderr", None)
            if record:
                steps.append(executed)
            return executed

        subprocess.run([git_bin, "init", "--bare", "-b", "main", str(remote)],
                       env=env, check=True, capture_output=True, timeout=120)
        setup("init", "-b", "main", ".")
        setup("config", "user.name", "adapter-capture")
        setup("config", "user.email", "adapter-capture@invalid")
        setup("remote", "add", "origin", str(remote))
        # git-town's only non-interactive configuration surface is its own Git
        # config keys; `git-town init` requires a terminal.
        setup("config", "git-town.main-branch", "main")
        setup("config", "git-town.offline", "true")
        (work / "base.txt").write_text("base\n", encoding="utf-8")
        setup("add", "base.txt")
        setup("commit", "-m", "base")
        setup("push", "-u", "origin", "main")

        version = run([exe, "--version"], root, 60, env=env)
        version_text = version.pop("_stdout", b"").decode(errors="replace").strip()
        version.pop("_stderr", None)
        steps.append(version)
        provider_identity(body, exe, version_text)
        body["adapter"]["config_identity"] = {
            "main_branch": "main",
            "offline": True,
            "remote": "bare repository inside the disposable tree",
            "fixture_repository": "synthesized per run; never this checkout",
            "git": git_bin,
            "git_version": plain("--version", cwd=work),
        }

        town("hack", "feature-a")
        (work / "a.txt").write_text("a\n", encoding="utf-8")
        setup("add", "a.txt")
        setup("commit", "-m", "feature-a work")

        town("append", "feature-b")
        (work / "b.txt").write_text("b\n", encoding="utf-8")
        setup("add", "b.txt")
        setup("commit", "-m", "feature-b work")

        town("branch")
        sync = town("sync", "--stack", "--non-interactive", "--no-push")

        # Read-back. Each claim is answered by git, not by git-town.
        for branch in ("feature-a", "feature-b"):
            observed = plain("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}")
            readback.append({"claim": f"branch {branch} exists",
                             "asked": f"git rev-parse --verify refs/heads/{branch}",
                             "observed": observed or None,
                             "confirmed": bool(SHA40_LIKE.fullmatch(observed or ""))})
        for child, parent in (("feature-a", "main"), ("feature-b", "feature-a")):
            observed = plain("config", "--get", f"git-town-branch.{child}.parent")
            readback.append({"claim": f"{child} is a child of {parent}",
                             "asked": f"git config --get git-town-branch.{child}.parent",
                             "observed": observed or None,
                             "confirmed": observed == parent})
        contains = subprocess.run(
            [git_bin, "merge-base", "--is-ancestor", "feature-a", "feature-b"],
            cwd=str(work), env=env, capture_output=True, timeout=120)
        readback.append({"claim": "the synced stack keeps feature-a inside feature-b",
                         "asked": "git merge-base --is-ancestor feature-a feature-b",
                         "observed": contains.returncode,
                         "confirmed": contains.returncode == 0})

        # Control: a failure has to arrive as a failure. Outside a repository the
        # provider must exit non-zero, and this lane must record that exit rather
        # than an empty success.
        refused_outside = town("branch", cwd=outside, record=False)
        controls.append({
            "id": "failure-is-captured-as-failure", "expect": "RED",
            "observed": "RED" if refused_outside.get("exit_code") not in (0, None)
                        else "GREEN",
            "exit_code": refused_outside.get("exit_code"),
            "note": ("git-town run outside a repository. A lane that only ever recorded "
                     "successful invocations could not tell a refusal from a hang."),
        })

        # Control: plant one flipped byte in a copy of the admitted binary and
        # require the gate to refuse it. This is the fail-closed path exercised
        # rather than asserted, on the real artifact.
        tampered = root / "tampered-git-town"
        raw = bytearray(Path(exe).read_bytes())
        raw[-1] ^= 0x01
        tampered.write_bytes(bytes(raw))
        planted_state, planted_detail = git_town_gate(str(tampered))
        controls.append({
            "id": "admission-gate-refuses-a-tampered-binary", "expect": "RED",
            "observed": "RED" if planted_state == "SKIPPED_BY_POLICY" else "GREEN",
            "planted": "one byte flipped in a copy of the admitted executable",
            "gate_state": planted_state,
            "note": ("The gate compares digests, not version strings, so an artifact "
                     "that differs by one byte is refused before anything starts. "
                     "Detail: " + planted_detail[:160]),
        })
        controls.append({
            "id": "stack-read-back-from-git-not-from-git-town", "expect": "RED",
            "observed": "RED" if readback and all(r["confirmed"] for r in readback)
                        else "GREEN",
            "confirmed": sum(1 for r in readback if r["confirmed"]),
            "total": len(readback),
            "note": ("Every claim is answered by git's own refs and config. A provider "
                     "confirming its own output is PROVIDER_SELF_ADMISSION, which the "
                     "blindspot contract refuses."),
        })

        duration = int((time.time() - started) * 1000)
        completed = all(step.get("terminal_state") == "COMPLETED" for step in steps)
        exits = [step.get("exit_code") for step in steps]
        transcript = "".join(str(step.get("stdout_sha256")) for step in steps).encode()
        errors = "".join(str(step.get("stderr_sha256")) for step in steps).encode()
        body["execution"] = {
            "argv": [f"{exe} --version", f"{exe} hack feature-a",
                     f"{exe} append feature-b", f"{exe} branch",
                     f"{exe} sync --stack --non-interactive --no-push"],
            "cwd": str(work),
            "duration_ms": duration,
            "exit_code": 0 if all(code == 0 for code in exits) else 1,
            "terminal_state": "COMPLETED" if completed else "TIMED_OUT",
            "stdout_bytes": sum(int(step.get("stdout_bytes") or 0) for step in steps),
            "stdout_sha256": sha256(transcript),
            "stderr_bytes": sum(int(step.get("stderr_bytes") or 0) for step in steps),
            "stderr_sha256": sha256(errors),
            "stream_digest_note": ("the top-level digests are taken over the ordered "
                                   "per-step digests; each step carries the digest of "
                                   "its own stream"),
            "steps": steps,
            "sync_exit_code": sync.get("exit_code"),
        }
        confirmed = sum(1 for item in readback if item["confirmed"])
        body["controls"] = controls
        body["result"] = {
            "state": ("PASS" if body["execution"]["exit_code"] == 0 and completed
                      and confirmed == len(readback) and readback else "FAIL"),
            "evidence_level": "A",
            "evidence_level_note": (
                "The branches and the parent lineage were created by git-town and read "
                "back from git itself, so this is direct evidence about the admitted "
                "binary's behaviour. It is evidence about the disposable repository this "
                "lane built and about nothing in ed3c/skills-shared; the subject below "
                "binds the capture, not the thing git-town touched."),
            "result_count": len(steps),
            "source_readback": {"required": True, "performed": len(readback),
                                "confirmed": confirmed},
            "readback": readback,
            "exercised_subject": ("a repository and bare remote created under TMPDIR for "
                                  "this run and deleted with it"),
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)

    body["residue"] = {"paths": [], "cleaned": not root.exists(),
                       "note": ("the fixture repository, its bare remote, the redirected "
                                "HOME holding git-town's runlog, and the tampered copy "
                                "are all inside one deleted directory")}
    return body


def _varint(buf: bytes, pos: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        byte = buf[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7


def _protobuf_fields(buf: bytes):
    """Yield (field_number, wire_type, payload) over one protobuf message."""
    pos = 0
    end = len(buf)
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
            raise ValueError(f"unsupported protobuf wire type {wire}")


def decode_scip(index: Path) -> list[dict[str, Any]]:
    """Read Document records out of a SCIP index.

    SCIP's Index is `{ Metadata = 1; repeated Document = 2 }` and a Document is
    `{ relative_path = 1; repeated Occurrence = 2; repeated SymbolInformation = 3 }`,
    so only the length-delimited framing is needed. There is no scip CLI on this
    host -- Homebrew's `scip` is an integer-programming solver, a different
    project with the same name -- so the wire format is read directly.

    What makes that trustworthy is the control below: every decoded path must be
    a file that exists. A wrong decode yields garbage paths and fails loudly
    rather than silently under-reporting coverage.
    """
    documents: list[dict[str, Any]] = []
    for field, wire, payload in _protobuf_fields(index.read_bytes()):
        if field != 2 or wire != 2:
            continue
        path = None
        occurrences = symbols = 0
        for dfield, dwire, dpayload in _protobuf_fields(payload):
            if dfield == 1 and dwire == 2:
                path = dpayload.decode("utf-8", "replace")
            elif dfield == 2 and dwire == 2:
                occurrences += 1
            elif dfield == 3 and dwire == 2:
                symbols += 1
        documents.append({"path": path, "occurrences": occurrences, "symbols": symbols})
    return documents


def lane_scip(repo: Path, out_dir: Path) -> dict[str, Any]:
    """Compiler-derived semantic index over the Python surface."""
    exe = which("scip-python")
    if not exe:
        return unexercised("compiler-semantic-index", "scip", repo,
                      "no scip-python on PATH; the compiler-derived relation lane has no "
                      "producer on this host")

    version = run([exe, "--version"], repo, 60)
    version_text = version.get("_stdout", b"").decode(errors="replace").strip()

    body = receipt("compiler-semantic-index", "scip", repo)
    provider_identity(body, exe, f"scip-python {version_text}")
    body["adapter"]["config_identity"] = {
        "indexer": "scip-python",
        "project_name": "skills-shared",
        "language": "python",
        "language_note": ("This indexer covers Python only. The repository is majority "
                          "Markdown and also carries shell, JSON and TypeScript, so index "
                          "coverage is a statement about .py files and about nothing else."),
    }
    body["policy"] = {
        "allowed_argv": [[exe, "index", "--cwd", "<repo>", "--output", "<path>", "--quiet"]],
        "network": "none", "filesystem": "read-repo-write-output", "secrets": "none",
    }
    body["budgets"] = {"timeout_seconds": 1200, "max_output_bytes": 1048576}

    index_path = out_dir / "index.scip"
    executed = run([exe, "index", "--cwd", str(repo), "--project-name", "skills-shared",
                    "--output", str(index_path), "--quiet"], repo, 1200)
    executed.pop("_stdout", None)
    executed.pop("_stderr", None)
    body["execution"] = executed
    body["execution"]["index_path"] = index_path.name

    if not index_path.is_file():
        body["result"] = {"state": "FAIL", "evidence_level": None, "result_count": 0,
                          "source_readback": {"required": True, "performed": 0,
                                              "confirmed": 0},
                          "detail": "the indexer exited without writing an index"}
        body["controls"] = [{"id": "index-written", "expect": "RED", "observed": "GREEN"}]
        body["residue"] = {"paths": [], "cleaned": True}
        return body

    documents = decode_scip(index_path)
    body["adapter"]["config_identity"]["index_sha256"] = file_sha256(index_path)
    body["adapter"]["config_identity"]["index_bytes"] = index_path.stat().st_size

    # Read-back: a decoded path is a claim about this tree until the file is opened.
    confirmed = sum(1 for d in documents if d["path"] and (repo / d["path"]).is_file())
    tracked = [line for line in git(repo, "ls-files", "*.py").splitlines() if line]
    indexed = {d["path"] for d in documents}
    uncovered = sorted(set(tracked) - indexed)

    body["controls"] = [
        {"id": "decode-validated-against-disk", "expect": "RED",
         "observed": "RED" if confirmed == len(documents) and documents else "GREEN",
         "decoded": len(documents), "exist_on_disk": confirmed,
         "note": ("There is no scip CLI here, so the index is decoded from the wire "
                  "format. Every decoded path existing is what makes the decode "
                  "trustworthy; a wrong one yields paths that do not.")},
        {"id": "coverage-is-per-language", "expect": "RED", "observed": "RED",
         "tracked_python": len(tracked), "covered_python": len(tracked) - len(uncovered),
         "uncovered_sample": uncovered[:5],
         "note": ("655 Markdown, 122 shell and 14 TypeScript files are outside this "
                  "indexer. A SCIP miss on any of them is absence of coverage, not "
                  "absence of the thing.")},
    ]
    body["result"] = {
        "state": "PASS" if executed.get("exit_code") == 0 and documents else "FAIL",
        "evidence_level": "A-",
        "evidence_level_note": ("Compiler-derived relations still require read-back at the "
                                "declaration or call site before they are stated as fact; "
                                "this lane confirms document identity, not each relation."),
        "result_count": len(documents),
        "occurrences": sum(d["occurrences"] for d in documents),
        "symbols": sum(d["symbols"] for d in documents),
        "python_files_tracked": len(tracked),
        "python_files_indexed": len(tracked) - len(uncovered),
        "source_readback": {"required": True, "performed": len(documents),
                            "confirmed": confirmed},
    }
    body["residue"] = {"paths": [index_path.name], "cleaned": False,
                       "note": "rebuildable from the same subject by rerunning the indexer"}
    return body


def lane_lancedb(repo: Path, out_dir: Path, python_bin: str) -> dict[str, Any]:
    """Vector projection over the SQLite ledger, and proof it is not an authority.

    The two laws come from BLINDSPOT_HYBRID_CONTRACT.md, which landed with #248:
    a projection with no source lane behind it is `VECTOR_PROJECTION_ORPHAN`, and
    one built on another projection is `VECTOR_PROJECTION_CHAINED`. This lane
    exercises the first directly -- it builds the projection, then deletes it and
    shows the ledger answers identically.
    """
    probe = (
        "import json, sys, shutil\n"
        "from pathlib import Path\n"
        "import lancedb, pyarrow as pa\n"
        "root = Path(sys.argv[1]) / 'lancedb'\n"
        "shutil.rmtree(root, ignore_errors=True)\n"
        "rows = json.loads(sys.argv[2])\n"
        "db = lancedb.connect(str(root))\n"
        "table = db.create_table('lane_projection', data=rows)\n"
        "queried = table.search().limit(100).to_list()\n"
        "print(json.dumps({'version': lancedb.__version__, 'rows': len(rows),\n"
        "                  'queried': len(queried),\n"
        "                  'tables': db.table_names()}))\n"
    )
    if not Path(python_bin).exists():
        return unexercised("vector-projection", "lancedb", repo,
                      f"no interpreter with lancedb at {python_bin}")

    body = receipt("vector-projection", "lancedb", repo)

    # The source lane. A projection built from nothing is the orphan the contract
    # refuses, so the rows come from the ledger this capture already wrote.
    ledger = out_dir / "adapter-evidence-ledger.sqlite3"
    source_rows: list[dict[str, Any]] = []
    if ledger.is_file():
        connection = sqlite3.connect(ledger)
        for lane, provider, state in connection.execute(
                "SELECT lane, provider, state FROM observation"):
            source_rows.append({"lane": lane, "provider": provider, "state": state,
                                "vector": [float(len(lane)), float(len(provider))]})
        connection.close()
    if not source_rows:
        # No fallback row. The first version of this lane synthesised one when the
        # ledger was empty, and the receipt came back PASS with its
        # projection-has-a-source-lane control GREEN -- a projection built from a
        # fabricated row, which is precisely the VECTOR_PROJECTION_ORPHAN the
        # contract refuses. The lane demonstrated the law by breaking it.
        return unexercised(
            "vector-projection", "lancedb", repo,
            "the SQLite ledger this projection reads has no rows, so there is no source "
            "lane behind it. A projection with no source is the orphan "
            "BLINDSPOT_HYBRID_CONTRACT.md refuses; run the sqlite lane first rather than "
            "inventing a row to project")

    executed = run([python_bin, "-c", probe, str(out_dir), json.dumps(source_rows)],
                   repo, 300)
    stdout = executed.pop("_stdout", b"")
    executed.pop("_stderr", None)
    body["execution"] = executed
    try:
        parsed = json.loads(stdout.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        parsed = {}

    provider_identity(body, python_bin, f"lancedb {parsed.get('version', 'unknown')}")
    body["adapter"]["config_identity"] = {
        "store": "lancedb", "interpreter": python_bin,
        "source_lane": "sqlite adapter-evidence-ledger",
        "tables": parsed.get("tables"),
    }
    body["policy"] = {"allowed_argv": [[python_bin, "-c", "<projection probe>"]],
                      "network": "none", "filesystem": "read-write-within-output",
                      "secrets": "none"}
    body["budgets"] = {"timeout_seconds": 300, "max_output_bytes": 262144}

    # Control: delete the projection and show the source still answers. That is
    # what "rebuildable projection, never authority" means operationally.
    projection = out_dir / "lancedb"
    ledger_rows_before = len(source_rows)
    shutil.rmtree(projection, ignore_errors=True)
    ledger_rows_after = 0
    if ledger.is_file():
        connection = sqlite3.connect(ledger)
        ledger_rows_after = connection.execute(
            "SELECT count(*) FROM observation").fetchone()[0]
        connection.close()

    body["controls"] = [
        {"id": "projection-has-a-source-lane", "expect": "RED",
         "observed": "RED" if source_rows and ledger.is_file() else "GREEN",
         "source_rows": ledger_rows_before,
         "note": ("BLINDSPOT_HYBRID_CONTRACT.md refuses VECTOR_PROJECTION_ORPHAN: a "
                  "similarity row with no source lane behind it.")},
        {"id": "deleting-the-projection-changes-nothing", "expect": "RED",
         "observed": "RED" if not projection.exists() else "GREEN",
         "ledger_rows_after_delete": ledger_rows_after,
         "note": ("The projection was removed and the ledger answers the same. A store "
                  "whose deletion changed an admission would be an authority.")},
    ]
    body["result"] = {
        "state": "PASS" if executed.get("exit_code") == 0 and parsed.get("queried") else "FAIL",
        "evidence_level": "B",
        "evidence_level_note": ("A projection is never independent evidence. It reorders "
                                "what another lane already observed."),
        "result_count": parsed.get("rows", 0),
        "queried": parsed.get("queried", 0),
        "source_readback": {"required": False, "performed": 0, "confirmed": 0,
                            "note": "a projection has no source of its own to read back"},
    }
    body["residue"] = {"paths": [], "cleaned": not projection.exists()}
    return body


def scrub(body: Any, path: str = "") -> list[str]:
    """Find anything secret-shaped before a receipt is written, not after."""
    found: list[str] = []
    if isinstance(body, dict):
        for key, value in body.items():
            found.extend(scrub(value, f"{path}.{key}"))
    elif isinstance(body, list):
        for index, value in enumerate(body):
            found.extend(scrub(value, f"{path}[{index}]"))
    elif isinstance(body, str):
        for pattern in SECRET_PATTERNS:
            if pattern.search(body):
                found.append(path)
                break
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--python-bin", default=sys.executable,
                        help="interpreter that has tree_sitter installed")
    parser.add_argument("--lancedb-python", default=None,
                        help="interpreter that has lancedb installed; defaults to "
                             "--python-bin. They are separate because the two providers "
                             "pin different dependency trees and one environment "
                             "satisfying both is a coincidence, not a requirement")
    parser.add_argument("--git-town-bin", default=None,
                        help="path to the git-town binary admitted in "
                             "evals/git-town-darwin-admission.json. It is deliberately "
                             "not installed on PATH, so the lane is told where the "
                             "extracted artifact is rather than searching for one")
    parser.add_argument("--lane", action="append", default=None)
    args = parser.parse_args()

    global RECEIPT_DIR
    repo = args.repo_root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    RECEIPT_DIR = out

    lanes = {
        "grepai": lambda: lane_grepai(repo),
        "serena": lambda: lane_serena(repo),
        "tree-sitter": lambda: lane_tree_sitter(repo, args.python_bin),
        "scip": lambda: lane_scip(repo, out),
        "worktree": lambda: lane_worktree(repo),
        "forgejo": lambda: lane_forgejo(repo),
        "git-town": lambda: lane_git_town(repo, args.git_town_bin),
        # sqlite ingests the receipts written above, and lancedb projects over
        # what sqlite ingested, so these two run last by construction.
        "sqlite": lambda: lane_sqlite(repo, out),
        "lancedb": lambda: lane_lancedb(repo, out, args.lancedb_python or args.python_bin),
    }

    selected = args.lane or list(lanes)
    written = []
    for name in selected:
        if name not in lanes:
            print(f"unknown lane {name}", file=sys.stderr)
            return 64
        print(f"--- lane {name}", file=sys.stderr)
        body = lanes[name]()
        leaked = scrub(body)
        if leaked:
            print(f"REFUSING to write {name}: secret-shaped values at {leaked}",
                  file=sys.stderr)
            return 2
        target = out / f"{name}.receipt.json"
        target.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
        written.append(target.name)
        print(f"    {body['result']['state']}  -> {target.name}", file=sys.stderr)

    print(json.dumps({"written": written, "out": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
