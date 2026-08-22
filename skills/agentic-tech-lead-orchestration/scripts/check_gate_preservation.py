#!/usr/bin/env python3
"""Refuse a landing that deletes the gates its own base carried — issue #605.

Every other gate in this suite judges the tree in front of it. None of them can
see a gate that is no longer there: when a merge drops a check, the suite goes
green *because* the check vanished. Two shadow-proven instances on this
repository: the #466 receipt paper gate was deleted by a merge, and two
per-queue selftest invocations were dropped.

The subject is therefore the range ``base..HEAD``, not the tree:

* an ``assert_*``/``check_*`` script, ``run-all.sh``, ``verify.sh``,
  ``*selftest*.py`` or workflow file that existed at the base and is gone at
  HEAD, and
* an invocation line (``python3 …``, ``bash …``, a ``python3 - <<'PY'`` heredoc
  gate, ``run: python3 …``) that a shell runner or workflow carried at the base
  and no longer carries at HEAD.

A deleted invocation whose exact text reappears anywhere else in the same range
is a move, not a deletion. An intended deletion must be *named* with an explicit
``--allow`` pattern at the call site — there is no fuzzy heuristic that decides
a deletion was meant, because the deletions this gate exists to catch all looked
intentional to whoever made them.

Base selection, highest authority first:

1. explicit ``--base``;
2. ``GITHUB_BASE_REF`` (pull request) resolved through ``merge-base``;
3. the first parent of HEAD, which is the pre-merge base of a merge commit.

When none of those yields a commit object — a shallow CI checkout, a root
commit, a tree with no git — the result is a printed ``SKIPPED_BY_POLICY`` line
naming the reason. It is never a silent pass: an absent subject and an audited
subject with no deletions must not look the same (issue #576 class).

Exits: 0 green or skipped-by-policy, 2 deletions found, 64 usage, 70 mechanism.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# The change surface a gate can disappear from. Deliberately wider than the
# gate-file set below: a runner keeps its invocations, a fixture does not.
GATE_PATHSPECS = (
    "*run-all.sh",
    "*/tests/*",
    "*scripts/assert_*",
    "*scripts/check_*",
    ".github/workflows/*",
)

# Files that *are* a gate. Losing one is a deletion regardless of its contents.
GATE_FILE_PATTERNS = (
    "*scripts/assert_*.py",
    "*scripts/check_*.py",
    "*run-all.sh",
    "*verify.sh",
    "*selftest*.py",
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
)

# Files that *list* gates. Only these are read line by line; a gate list lives in
# a shell runner or a workflow, and scanning Python sources would report every
# refactored subprocess argv as a lost gate.
RUNNER_FILE_PATTERNS = ("*.sh", ".github/workflows/*.yml", ".github/workflows/*.yaml")

RUNNER = re.compile(r"\b(python3|python|bash|sh|pytest|npx|node)\s")
# A runner word alone is prose. These are what make the line an invocation.
QUALIFIER = re.compile(r"(\.py\b|\.sh\b|\s-m\s|<<|--selftest)")
MIN_ALLOW_LENGTH = 8


class InputError(ValueError):
    pass


class MechanismError(RuntimeError):
    pass


class SkippedByPolicy(Exception):
    """No derivable subject. Printed loudly, never converted to a silent pass."""


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise MechanismError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _rev(repo: Path, revision: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", f"{revision}^{{commit}}"],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _normalize(line: str) -> str:
    return " ".join(line.split())


def _is_invocation(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False
    return bool(RUNNER.search(stripped) and QUALIFIER.search(stripped))


def select_base(repo: Path, explicit: str | None, base_ref: str | None) -> tuple[str, str]:
    """Return (base commit, how it was selected) or raise SkippedByPolicy."""
    if explicit:
        resolved = _rev(repo, explicit)
        if resolved is None:
            raise InputError(f"--base {explicit!r} is not a commit in this repository")
        return resolved, f"--base {explicit}"

    shallow = _git(repo, "rev-parse", "--is-shallow-repository").strip() == "true"

    advertised = (base_ref if base_ref is not None else os.environ.get("GITHUB_BASE_REF", "")).strip()
    if advertised:
        for candidate in (f"origin/{advertised}", advertised):
            resolved = _rev(repo, candidate)
            if resolved is None:
                continue
            merge_base = _git(repo, "merge-base", resolved, "HEAD").strip()
            if re.fullmatch(r"[0-9a-f]{40}", merge_base) is None:
                raise MechanismError(f"invalid merge-base against {candidate}")
            return merge_base, f"merge-base(origin PR base {advertised}, HEAD)"
        if shallow:
            raise SkippedByPolicy(
                f"shallow checkout cannot name PR base {advertised!r}; "
                "a base-carried gate cannot be read, so nothing is claimed"
            )
        raise MechanismError(
            f"advertised PR base {advertised!r} resolves to no commit in a full "
            "checkout; refusing to widen the subject"
        )

    parent = _rev(repo, "HEAD^1")
    if parent is None:
        raise SkippedByPolicy(
            "HEAD has no reachable first parent"
            + (" (shallow checkout)" if shallow else " (root commit)")
            + "; no base tree exists to compare gates against"
        )
    return parent, "first parent of HEAD"


def _deleted_gate_files(repo: Path, base: str, head: str) -> tuple[list[str], int]:
    """Deleted gate files, and how many files on the gate surface the range touched."""
    raw = _git(repo, "diff", "--name-status", "-M", base, head, "--", *GATE_PATHSPECS)
    changed = [line for line in raw.splitlines() if line.strip()]
    deleted: list[str] = []
    for line in changed:
        fields = line.split("\t")
        if len(fields) >= 2 and fields[0].startswith("D") and _matches(fields[1], GATE_FILE_PATTERNS):
            deleted.append(fields[1])
    return deleted, len(changed)


def _invocation_delta(repo: Path, base: str, head: str) -> tuple[list[tuple[str, str]], set[str]]:
    """Deleted invocation lines from runner files, and every added line's text."""
    raw = _git(
        repo, "diff", "--no-color", "--no-ext-diff", "-U0", "-M", base, head, "--", *GATE_PATHSPECS
    )
    removed: list[tuple[str, str]] = []
    added: set[str] = set()
    path = ""
    file_deleted = False
    for line in raw.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            file_deleted = target == "/dev/null"
            path = "" if file_deleted else target[2:] if target.startswith("b/") else target
            continue
        if line.startswith(("--- ", "diff --git", "index ", "@@", "old mode", "new mode",
                            "similarity index", "rename ")):
            continue
        if line.startswith("+"):
            body = line[1:]
            if _is_invocation(body):
                added.add(_normalize(body))
        elif line.startswith("-") and not file_deleted and path:
            body = line[1:]
            if _matches(path, RUNNER_FILE_PATTERNS) and _is_invocation(body):
                removed.append((path, _normalize(body)))
    return removed, added


def evaluate(
    repo: Path, base: str, head: str, allow: list[str]
) -> tuple[list[str], list[str], int, int]:
    """Return (findings, unused allow patterns, deletions seen, gate files in range)."""
    deleted_files, changed = _deleted_gate_files(repo, base, head)
    candidates = [(path, f"gate file deleted: {path}") for path in deleted_files]
    removed, added = _invocation_delta(repo, base, head)
    for path, text in removed:
        if text in added:  # moved or re-indented, not lost
            continue
        candidates.append((f"{path}: {text}", f"gate invocation deleted from {path}: {text}"))

    findings: list[str] = []
    used: set[str] = set()
    for subject, message in candidates:
        allowed = [pattern for pattern in allow if pattern in subject]
        if allowed:
            used.update(allowed)
            continue
        findings.append(message)
    return findings, [pattern for pattern in allow if pattern not in used], len(candidates), changed


def _selftest() -> list[str]:
    """Plant a deleted invocation and a deleted gate file; prove the check goes red."""
    failures: list[str] = []
    env = dict(os.environ)
    env.pop("GITHUB_BASE_REF", None)

    def run(root: Path, *args: str, base_ref: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--repo-root", str(root), *args],
            capture_output=True, text=True, check=False,
            env=env if base_ref is None else dict(env, GITHUB_BASE_REF=base_ref),
        )

    with tempfile.TemporaryDirectory(prefix="gate-preservation-selftest-") as scratch:
        root = Path(scratch)
        _git(root.parent, "init", "--quiet", "--initial-branch=main", str(root))
        _git(root, "config", "user.email", "selftest@claude-code.invalid")
        _git(root, "config", "user.name", "selftest")
        (root / "AGENTS.md").write_text("# scratch subject\n", encoding="utf-8")
        runner = root / "skills" / "demo" / "tests" / "run-all.sh"
        runner.parent.mkdir(parents=True)
        runner.write_text(
            "#!/usr/bin/env sh\n"
            "set -eu\n"
            'python3 "$ROOT/scripts/check_demo.py" --selftest\n'
            'python3 "$ROOT/scripts/assert_demo.py" --contract "$ROOT/x.json"\n'
            "python3 - \"$ROOT\" <<'PYRC'\n"
            "print('receipt paper gate')\n"
            "PYRC\n"
            'bash "$ROOT/tests/demo/verify.sh"\n',
            encoding="utf-8",
        )
        scripts = root / "skills" / "demo" / "scripts"
        scripts.mkdir(parents=True)
        for name in ("check_demo.py", "assert_demo.py"):
            (scripts / name).write_text("raise SystemExit(0)\n", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "--quiet", "-m", "base with four gates")
        _git(root, "branch", "pr-base")

        # The planted landing: drop the heredoc receipt gate (#466 shape), drop a
        # --selftest invocation (#605 instance B3), delete a gate script.
        runner.write_text(
            "#!/usr/bin/env sh\n"
            "set -eu\n"
            'python3 "$ROOT/scripts/check_demo.py"\n'
            'bash "$ROOT/tests/demo/verify.sh"\n'
            "echo unrelated\n",
            encoding="utf-8",
        )
        (scripts / "assert_demo.py").unlink()
        _git(root, "add", "-A")
        _git(root, "commit", "--quiet", "-m", "landing that deletes gates")

        red = run(root)
        if red.returncode != 2:
            failures.append(f"planted deletions did not turn the check red (exit {red.returncode})")
        for needle in ("assert_demo.py", "<<'PYRC'", "--selftest"):
            if needle not in red.stderr:
                failures.append(f"red output does not name the deleted gate {needle!r}")

        allowed = run(
            root,
            "--allow", "scripts/assert_demo.py",
            "--allow", "check_demo.py\" --selftest",
            "--allow", "<<'PYRC'",
        )
        if allowed.returncode != 0:
            failures.append(
                f"named deletions were not allowlisted (exit {allowed.returncode}): {allowed.stderr.strip()}"
            )

        stale = run(root, "--allow", "no-such-invocation-anywhere")
        if "GATE-PRESERVATION-NOTE" not in stale.stdout:
            failures.append("an unused allow pattern was not reported")

        # The CI pull-request shape: the base arrives as GITHUB_BASE_REF and is
        # reached through merge-base, not through the first parent.
        pull_request = run(root, base_ref="pr-base")
        if pull_request.returncode != 2:
            failures.append(
                f"PR-base derivation missed the same deletions (exit {pull_request.returncode})"
            )
        # A base ref that resolves to HEAD leaves an empty range. Reporting that
        # as an audited green is the #576 vacuous-green class.
        empty = run(root, base_ref="main")
        if empty.returncode != 0 or "SKIPPED_BY_POLICY" not in empty.stdout:
            failures.append(f"empty range was not reported (exit {empty.returncode})")

        # A landing that adds only new lines must stay green without any allowlist.
        runner.write_text(
            runner.read_text(encoding="utf-8") + 'python3 "$ROOT/scripts/check_new.py"\n',
            encoding="utf-8",
        )
        _git(root, "add", "-A")
        _git(root, "commit", "--quiet", "-m", "additive landing")
        green = run(root)
        if green.returncode != 0:
            failures.append(f"additive landing was not green (exit {green.returncode}): {green.stderr.strip()}")

    # No derivable base must print SKIPPED_BY_POLICY, not a silent pass.
    with tempfile.TemporaryDirectory(prefix="gate-preservation-rootcommit-") as scratch:
        root = Path(scratch)
        _git(root.parent, "init", "--quiet", "--initial-branch=main", str(root))
        _git(root, "config", "user.email", "selftest@claude-code.invalid")
        _git(root, "config", "user.name", "selftest")
        (root / "AGENTS.md").write_text("# scratch subject\n", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "--quiet", "-m", "root commit")
        skipped = run(root)
        if skipped.returncode != 0 or "SKIPPED_BY_POLICY" not in skipped.stdout:
            failures.append(
                f"root commit did not print SKIPPED_BY_POLICY (exit {skipped.returncode})"
            )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--base", default=None, help="explicit base revision; otherwise PR base or HEAD^1")
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="PATTERN",
        help="substring of a deleted gate path or invocation line that this landing intends to retire",
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.selftest:
            failures = _selftest()
            if failures:
                for failure in failures:
                    print(f"GATE-PRESERVATION-SELFTEST-RED {failure}", file=sys.stderr)
                return 2
            print(
                "GATE-PRESERVATION-SELFTEST-GREEN planted gate-file + heredoc + "
                "--selftest deletions turn red under both first-parent and PR-base "
                "derivation; allowlist, unused-allow note, additive landing, empty "
                "range and no-base SKIPPED_BY_POLICY behave"
            )
            return 0

        default_root = args.repo_root is None
        repo = (REPO_ROOT if default_root else args.repo_root).resolve()
        if default_root and not (repo / "AGENTS.md").is_file():
            raise InputError(f"default subject root {repo} does not contain AGENTS.md")
        for pattern in args.allow:
            if len(pattern.strip()) < MIN_ALLOW_LENGTH:
                raise InputError(
                    f"--allow {pattern!r} is too broad to name one deletion "
                    f"(needs at least {MIN_ALLOW_LENGTH} characters)"
                )
        if subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, check=False,
        ).returncode != 0:
            raise SkippedByPolicy(f"{repo} is not a git work tree; the base is unreadable here")

        base, how = select_base(repo, args.base, None)
        head = _rev(repo, "HEAD")
        if head is None:
            raise MechanismError("HEAD does not resolve to a commit")
        if base == head:
            raise SkippedByPolicy(
                f"the derived base ({how}) is HEAD itself, so the range holds no "
                "commit; an empty range is reported rather than counted as audited"
            )
        findings, unused, examined, changed = evaluate(repo, base, head, args.allow)
    except SkippedByPolicy as exc:
        print(f"GATE-PRESERVATION-SKIPPED_BY_POLICY {exc}")
        return 0
    except InputError as exc:
        print(f"GATE-PRESERVATION-INPUT-RED {exc}", file=sys.stderr)
        return 64
    except MechanismError as exc:
        print(f"GATE-PRESERVATION-MECHANISM-RED {exc}", file=sys.stderr)
        return 70

    for pattern in unused:
        print(f"GATE-PRESERVATION-NOTE unused allow pattern {pattern!r}; the deletion it named is no longer in range")
    if findings:
        for finding in findings:
            print(f"GATE-PRESERVATION-RED {finding}", file=sys.stderr)
        print(
            f"GATE-PRESERVATION-RED {len(findings)} gate(s) present at {base[:12]} "
            f"are absent at {head[:12]}; name each intended retirement with --allow",
            file=sys.stderr,
        )
        return 2
    print(
        f"GATE-PRESERVATION-GREEN base={base[:12]} ({how}) head={head[:12]}; "
        f"{changed} gate-surface file(s) changed in range, {examined} deletion(s) "
        f"found and named as intended"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
