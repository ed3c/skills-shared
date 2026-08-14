#!/usr/bin/env python3
"""Controls for the guard-control gate.

#122 requires that a check added to catch a shape must itself be shown to go
red on a planted instance of that shape. So each case here builds a disposable
repository containing a real guard, a real verify script, and a real manifest,
and asserts what the gate concludes.

The cases that matter most are the two ways this gate could be hollow:

  - a guard with no control must be reported (the shape it exists for);
  - a mutation that changed nothing must never be reported as a finding,
    because that is how eight false findings were produced by hand.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_guard_controls import Unusable, check_guard, neutralise  # noqa: E402

GUARDED = '''#!/usr/bin/env python3
import sys

def check(value):
    if value < 0:
        raise ValueError("negative")
    return value

if __name__ == "__main__":
    raise SystemExit(0)
'''

# A guard whose removal nothing observes: the verify never exercises it.
UNCONTROLLED_VERIFY = '''#!/usr/bin/env bash
set -euo pipefail
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('m', 'guarded.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.check(1) == 1
"
'''

CONTROLLED_VERIFY = '''#!/usr/bin/env bash
set -euo pipefail
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('m', 'guarded.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.check(1) == 1
try:
    m.check(-1)
except ValueError:
    pass
else:
    raise AssertionError('negative accepted')
"
'''

ALWAYS_FAILING_VERIFY = '''#!/usr/bin/env bash
set -euo pipefail
# An early step that always fails: everything after it is unreachable.
python3 -c "raise SystemExit(3)"
python3 -c "print('never reached')"
'''


def build(root: Path, verify_body: str) -> None:
    (root / "guarded.py").write_text(GUARDED, encoding="utf-8")
    verify = root / "verify.sh"
    verify.write_text(verify_body, encoding="utf-8")
    verify.chmod(0o755)


def guard_entry(anchor: str = '    if value < 0:') -> dict[str, Any]:
    return {
        "id": "fixture-guard",
        "file": "guarded.py",
        "anchor": anchor,
        "verify": ["bash", "verify.sh"],
    }


def run_selftest(repo_root: Path) -> int:
    failures: list[str] = []

    def expect(condition: bool, label: str) -> None:
        if not condition:
            failures.append(label)

    # A controlled guard is admitted.
    with tempfile.TemporaryDirectory(prefix="gc-good.") as raw:
        root = Path(raw)
        build(root, CONTROLLED_VERIFY)
        problems = check_guard(root, guard_entry(), 60)
        expect(problems == [], f"controlled guard was refused: {problems}")

    # The shape this gate exists for: nothing observes the guard's removal.
    with tempfile.TemporaryDirectory(prefix="gc-uncontrolled.") as raw:
        root = Path(raw)
        build(root, UNCONTROLLED_VERIFY)
        problems = check_guard(root, guard_entry(), 60)
        expect(any("cannot fail" in p for p in problems),
               f"an uncontrolled guard was not reported: {problems}")

    # Shape C: a verify whose assertions are unreachable is reported as
    # unproven, not as uncontrolled. Those are different findings.
    with tempfile.TemporaryDirectory(prefix="gc-unreachable.") as raw:
        root = Path(raw)
        build(root, ALWAYS_FAILING_VERIFY)
        problems = check_guard(root, guard_entry(), 60)
        expect(any("unreachable" in p for p in problems),
               f"an unreachable assertion was not reported: {problems}")
        expect(not any("cannot fail" in p for p in problems),
               "an unreachable verify was misreported as an uncontrolled guard")

    # A drifted anchor is reported rather than silently passing.
    with tempfile.TemporaryDirectory(prefix="gc-drift.") as raw:
        root = Path(raw)
        build(root, CONTROLLED_VERIFY)
        problems = check_guard(root, guard_entry('    if value < -999:'), 60)
        expect(any("absent" in p for p in problems),
               f"a drifted anchor was not reported: {problems}")

    # An ambiguous anchor is reported: a mutation could not say which guard it
    # removed.
    with tempfile.TemporaryDirectory(prefix="gc-ambiguous.") as raw:
        root = Path(raw)
        build(root, CONTROLLED_VERIFY)
        (root / "guarded.py").write_text(
            GUARDED + "\ndef check2(value):\n    if value < 0:\n        raise ValueError('x')\n",
            encoding="utf-8")
        problems = check_guard(root, guard_entry(), 60)
        expect(any("appears 2 times" in p for p in problems),
               f"an ambiguous anchor was not reported: {problems}")

    # The precedence trap that produced eight false findings by hand.
    compound = "    if not isinstance(value, int) or value < 0:"
    expect(neutralise(compound) == "    if False:",
           f"compound condition was prefixed rather than replaced: {neutralise(compound)!r}")
    expect(neutralise("        elif x != y:") == "        elif False:",
           "elif was not preserved")
    expect(neutralise("    validate(x)") == "    pass",
           "a bare statement was not neutralised to pass")

    # The real tree must be untouched: a crash mid-run must not leave a guard
    # removed in the repository being checked.
    with tempfile.TemporaryDirectory(prefix="gc-isolation.") as raw:
        root = Path(raw)
        build(root, UNCONTROLLED_VERIFY)
        before = (root / "guarded.py").read_text(encoding="utf-8")
        check_guard(root, guard_entry(), 60)
        expect((root / "guarded.py").read_text(encoding="utf-8") == before,
               "the gate modified the tree it was checking")

    # An unreadable target is unusable input, not a finding.
    with tempfile.TemporaryDirectory(prefix="gc-absent.") as raw:
        root = Path(raw)
        build(root, CONTROLLED_VERIFY)
        entry = guard_entry()
        entry["file"] = "not-here.py"
        try:
            check_guard(root, entry, 60)
            failures.append("an absent target was not reported as unusable")
        except Unusable:
            pass

    if failures:
        for item in failures:
            print(f"SELFTEST RED: {item}", file=sys.stderr)
        return 2
    print("SELFTEST GREEN: controlled guard admitted; uncontrolled, unreachable, "
          "drifted and ambiguous cases each reported distinctly")
    return 0
