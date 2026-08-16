#!/usr/bin/env python3
"""Controls for #218 Lane B observers, plus the fixture invariant they rest on.

The look-alike control is only a control while the two fixtures still render the
same pixels. If someone edits one page's styling, a screenshot diff starts
separating them and the "image cannot carry a state claim" demonstration
quietly becomes a demonstration of nothing. That invariant is asserted here from
the markup, so it fails at edit time rather than at argument time.

The live render itself is not run here: Chromium is not present on every runner
and a verifier that needs it would be disabled rather than fixed. Live browser
receipts live in `evals/receipts/`.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "observe_multimodal.py"
FIXTURES = SKILL / "tests" / "fixtures" / "multimodal"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, check=False)


def expect(name: str, expected: int, *args: str) -> None:
    result = run(*args)
    if result.returncode != expected:
        raise SystemExit(
            f"{name}: expected exit {expected}, got {result.returncode}\n{result.stderr[-600:]}"
        )


expect("selftest", 0, "--selftest")
expect("missing-arguments", 64)
expect("no-lane-selected", 64, "--output", "/dev/null")
expect("browser-without-artifact-dir", 64,
       "--observe-browser", str(FIXTURES / "truthful.html"), "--output", "/dev/null")


def visible_markup(page: Path) -> str:
    """Everything a camera would see: markup minus comments and machine state."""
    text = page.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<script>.*?</script>", "", text, flags=re.S)
    text = re.sub(r'\sdata-state="[^"]*"', "", text)
    return re.sub(r"\s+", " ", text).strip()


truthful, lookalike = FIXTURES / "truthful.html", FIXTURES / "lookalike.html"
if visible_markup(truthful) != visible_markup(lookalike):
    raise SystemExit(
        "look-alike fixtures no longer render identically: the image-only "
        "false-positive control has stopped being a control"
    )

states = {
    page.name: re.search(r'id="status" data-state="([A-Z]+)"', page.read_text(encoding="utf-8")).group(1)
    for page in (truthful, lookalike)
}
if states["truthful.html"] == states["lookalike.html"]:
    raise SystemExit(f"look-alike fixtures no longer disagree on machine state: {states}")

print("MULTIMODAL GREEN: selftest passes; absent input and absent lane exit 64; "
      f"fixture pair renders identically while disagreeing on state {states}")
