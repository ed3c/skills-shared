#!/usr/bin/env python3
"""An index is a claim about a directory; check it both ways.

Two failures, one defect seen from either side: a link that points at nothing,
and a file the index never mentions. The first is loud when someone clicks it.
The second is silent forever -- the reader has no way to know the list is short,
so an index that omits things reads exactly like an index that is complete.

Written after a README claimed seventeen shared skills while the registry held
twenty-two. Nobody mistyped; the number was copied forward instead of measured,
and one day was enough to make it false. A count in prose has no way to go red.

  --links          every relative link in the document resolves (default on)
  --covers DIR     every file directly under DIR is named somewhere in the doc
  --selftest       plant each defect and prove the checker catches it

Exit: 0 clean · 1 the index disagrees with the tree · 64 usage.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LINK = re.compile(r"\]\(([^)\s]+?)(?:#[^)]*)?\)")
USAGE = 64
SKIP_PREFIXES = ("http://", "https://", "mailto:", "file://", "#")


def dead_links(doc: Path, root: Path) -> list[str]:
    text = doc.read_text(encoding="utf-8")
    dead = []
    for target in LINK.findall(text):
        if target.startswith(SKIP_PREFIXES):
            continue
        if not (root / target).exists():
            dead.append(f"DEAD-LINK   {doc.name} -> {target}")
    return dead


def uncovered(doc: Path, directory: Path) -> list[str]:
    """Files under `directory` that the document never names.

    Matching is by name, not by link: an index may legitimately mention a file
    in prose. What it may not do is leave it out entirely.
    """
    if not directory.is_dir():
        return [f"NO-SUCH-DIR {directory}"]
    text = doc.read_text(encoding="utf-8")
    missing = []
    for entry in sorted(directory.iterdir()):
        if entry.name.startswith(".") or entry.name == "__pycache__":
            continue
        # A document indexing its own directory does not owe itself an entry.
        # Requiring one is a rule with no reader behind it, and a rule that
        # fires on nothing real is how a checker gets switched off.
        if entry.resolve() == doc.resolve():
            continue
        if entry.name not in text:
            missing.append(f"UNINDEXED   {doc.name} never names {directory.name}/{entry.name}")
    return missing


def check(doc: Path, root: Path, covers: list[Path]) -> int:
    if not doc.is_file():
        print(f"FATAL no such document: {doc}", file=sys.stderr)
        return USAGE
    failures = dead_links(doc, root)
    for directory in covers:
        failures.extend(uncovered(doc, directory))
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    covered = ", ".join(d.name for d in covers) or "no directory"
    print(f"PASS {doc.name}: links resolve; {covered} fully indexed")
    return 0


def selftest() -> int:
    """A checker that cannot go red is a green light. Prove each colour."""
    import tempfile

    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "modules").mkdir()
        (root / "modules" / "a.md").write_text("a", encoding="utf-8")
        (root / "modules" / "b.md").write_text("b", encoding="utf-8")
        doc = root / "SKILL.md"
        covers = [root / "modules"]

        def expect(label: str, want: int) -> None:
            got = check(doc, root, covers)
            if got != want:
                failures.append(f"{label}: expected {want}, got {got}")

        doc.write_text("[a](modules/a.md) [b](modules/b.md)\n", encoding="utf-8")
        expect("complete index passes", 0)

        doc.write_text("[a](modules/a.md) [b](modules/b.md) [gone](modules/c.md)\n", encoding="utf-8")
        expect("a link to nothing fails", 1)

        doc.write_text("[a](modules/a.md)\n", encoding="utf-8")
        expect("an unmentioned file fails", 1)

        doc.write_text("b.md is covered in prose\n[a](modules/a.md)\n", encoding="utf-8")
        expect("naming a file in prose counts as indexed", 0)

        doc.write_text("[a](modules/a.md) b.md [ext](https://example.invalid/x)\n", encoding="utf-8")
        expect("external links are not the tree's problem", 0)

        # A README indexing the directory it lives in must not owe itself a line.
        readme = root / "modules" / "README.md"
        readme.write_text("[a](a.md) b.md\n", encoding="utf-8")
        if check(readme, root / "modules", [root / "modules"]) != 0:
            failures.append("a document must not be required to index itself")

    if failures:
        for failure in failures:
            print(f"SELFTEST-FAIL {failure}", file=sys.stderr)
        return 1
    print("PASS selftest: red on a dead link and on an unindexed file; quiet on prose and http")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", nargs="?", type=Path, help="the index to check")
    parser.add_argument("--root", type=Path, help="resolve links against this (default: doc's dir)")
    parser.add_argument(
        "--covers", type=Path, action="append", default=[],
        help="repeatable; every file directly under DIR must be named in the document",
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.document:
        parser.error("a document is required unless --selftest")
    return check(args.document, args.root or args.document.parent, args.covers)


if __name__ == "__main__":
    raise SystemExit(main())
