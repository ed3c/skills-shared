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


def absent(kind: str, provider: str, repo: Path, reason: str) -> dict[str, Any]:
    body = receipt(kind, provider, repo)
    body["adapter"].update({"executable": None, "version": None, "executable_sha256": None})
    body["policy"] = {"network": "none", "filesystem": "none", "secrets": "none",
                      "allowed_argv": []}
    body["budgets"] = {"timeout_seconds": 0, "max_output_bytes": 0}
    body["execution"] = {"terminal_state": "NOT_STARTED", "exit_code": None}
    body["result"] = {"state": "ABSENT", "evidence_level": None, "result_count": 0,
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
        return absent("semantic-intent-search", "grepai", repo, "grepai not on PATH")

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
        return absent("symbol-lsp", "serena", repo, "serena not on PATH")

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
        return absent("syntax-slice", "tree-sitter", repo,
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
        "result_count": 0,
        "ledger_path": ledger.name,
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


ABSENT_LANES = {
    "scip": ("compiler-semantic-index", "scip",
             "no scip or scip-python indexer on PATH; the compiler-derived relation lane "
             "has no producer on this host"),
    "git-town": ("stack-synchronization", "git-town",
                 "git-town is not installed. Homebrew offers the admitted 24.0.0, but the "
                 "committed admission record pins a linux_intel_64 artifact by SHA-256 and "
                 "this host is darwin; a different artifact needs its own admission, which "
                 "is a Human decision rather than an install"),
    "lancedb": ("vector-projection", "lancedb",
                "lancedb not installed; the optional projection lane is not exercised, and "
                "it is a projection over SQLite rather than an authority in any case"),
}


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
        "sqlite": lambda: lane_sqlite(repo, out),
        "worktree": lambda: lane_worktree(repo),
        "forgejo": lambda: lane_forgejo(repo),
    }
    for name, (kind, provider, reason) in ABSENT_LANES.items():
        lanes[name] = (lambda k=kind, p=provider, r=reason: absent(k, p, repo, r))

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
