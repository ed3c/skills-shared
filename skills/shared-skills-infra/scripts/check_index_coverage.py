#!/usr/bin/env python3
"""Run the index checker over this repository: links everywhere, coverage where declared.

Two halves with different reach, on purpose.

Link resolution applies to every document and needs no manifest -- a link that
points at nothing is a defect wherever it appears. Directory coverage applies
only where a document opts in, because completeness is a claim a document makes
rather than a property a checker can infer. `traceability-index.md` carries an
index heading and indexes decisions rather than the files beside it; pointing a
directory check at it reports defects that are not there, and a checker that
cries wolf gets its output skipped.

Found on its first run: one dead link that had been sitting in a module since it
was written (`references/contracts.md` written from the skill root rather than
from `modules/`, so the target existed and the path did not), and a test
directory added three commits earlier that its own index never named.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKER = Path(__file__).resolve().parent / "check_index.py"
MANIFEST = ROOT / "evals" / "index-coverage.json"
SKIP_PARTS = {"superseded", ".git", "node_modules", "__pycache__"}


class CoverageError(Exception):
    pass


def documents(root: Path) -> list[Path]:
    return [
        p for p in sorted(root.rglob("*.md"))
        if not SKIP_PARTS & set(p.relative_to(root).parts)
    ]


def run_checker(document: Path, directory: Path | None, root: Path) -> tuple[int, str]:
    argv = [sys.executable, str(CHECKER), str(document)]
    if directory is not None:
        argv += ["--covers", str(directory)]
    done = subprocess.run(argv, capture_output=True, text=True, check=False, cwd=root)
    return done.returncode, (done.stderr.strip() or done.stdout.strip())


def load_manifest(path: Path) -> list[dict[str, str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CoverageError(f"manifest unusable: {error}") from error
    if value.get("schema") != "index-coverage/v1":
        raise CoverageError("manifest.schema must be index-coverage/v1")
    entries = value.get("covers")
    if not isinstance(entries, list) or not entries:
        raise CoverageError("manifest.covers must be a non-empty array")
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"document", "directory"}:
            raise CoverageError(f"manifest entry must be document/directory: {entry!r}")
    return entries


def selftest() -> int:
    """Plant both defects in a copy and require each half to catch its own.

    Without this the coverage half is a tripwire: on a clean tree, removing it
    leaves the run green because nothing is currently unindexed, so it survives
    removal exactly like an assertion that cannot fail. The guard-control gate
    reported precisely that, which is what it is for.
    """
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory(prefix="index-coverage.") as raw:
        root = Path(raw) / "repo"
        (root / "skills" / "demo").mkdir(parents=True)
        (root / "evals").mkdir(parents=True)
        shutil.copy2(CHECKER, root / "check_index.py")
        (root / "skills" / "demo" / "a.md").write_text("# A\n", encoding="utf-8")
        index = root / "skills" / "demo" / "README.md"
        index.write_text("# Demo\n\n## Index\n\n- [`a.md`](a.md)\n", encoding="utf-8")
        (root / "evals" / "index-coverage.json").write_text(json.dumps({
            "schema": "index-coverage/v1",
            "covers": [{"document": "skills/demo/README.md", "directory": "skills/demo"}],
        }), encoding="utf-8")

        def run(target: Path) -> int:
            return evaluate(target)[0]

        if run(root) != 0:
            print("SELFTEST RED: a clean fixture was refused", file=sys.stderr)
            return 2

        # A file the index never names.
        (root / "skills" / "demo" / "b.md").write_text("# B\n", encoding="utf-8")
        if run(root) == 0:
            print("SELFTEST RED: an unindexed file was accepted", file=sys.stderr)
            return 2
        (root / "skills" / "demo" / "b.md").unlink()

        # A link that points at nothing.
        index.write_text(index.read_text() + "- [`gone.md`](gone.md)\n", encoding="utf-8")
        if run(root) == 0:
            print("SELFTEST RED: a dead link was accepted", file=sys.stderr)
            return 2

    print("SELFTEST GREEN: an unindexed file and a dead link are each caught")
    return 0


def evaluate(root: Path) -> tuple[int, list[str], int, int]:
    """The one evaluation path. A second copy for the selftest would drift from
    the one CI runs, and then the selftest would be proving something else."""
    entries = load_manifest(root / "evals" / "index-coverage.json")
    problems: list[str] = []
    scanned = documents(root)
    for document in scanned:
        code, detail = run_checker(document, None, root)
        if code:
            problems.append(f"{document.relative_to(root)}: {detail}")
    for entry in entries:
        document, directory = root / entry["document"], root / entry["directory"]
        if not document.is_file():
            problems.append(f"{entry['document']}: declared as an index and absent")
            continue
        if not directory.is_dir():
            problems.append(f"{entry['directory']}: declared as covered and absent")
            continue
        code, detail = run_checker(document, directory, root)
        if code:
            problems.append(f"{entry['document']}: {detail}")
    return (1 if problems else 0), problems, len(scanned), len(entries)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    root = args.repo_root.resolve()

    if not CHECKER.is_file():
        print(f"INDEX COVERAGE UNUSABLE: checker missing at {CHECKER}", file=sys.stderr)
        return 70
    try:
        code, problems, scanned, declared = evaluate(root)
    except CoverageError as error:
        print(f"INDEX COVERAGE UNUSABLE: {error}", file=sys.stderr)
        return 64
    if code:
        print("INDEX COVERAGE RED:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(
        f"INDEX COVERAGE GREEN: links resolve in {scanned} document(s); "
        f"{declared} declared index(es) name every file beside them"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
