#!/usr/bin/env python3
"""Plant report/ledger drift and require `--check` to turn red for its own reason.

A byte-compare gate is the easiest kind of checker to leave hollow: point it at
a file it wrote itself in the same process and it is green forever. Each
mutation below breaks one side of the comparison and names the message that
must appear, so a renderer that stops reading the ledger, or a `--check` that
stops reading the report, cannot stay green.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
RENDERER = ROOT / "scripts/render_adoption_audit.py"
LEDGER = ROOT / "references/skill-adoption-ledger.json"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RENDERER), "--root", str(REPO), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    survivors = []
    with tempfile.TemporaryDirectory(prefix="render-selftest-") as raw:
        temp = Path(raw)
        report = temp / "report.md"

        written = run("--output", str(report))
        fresh = run("--check", "--output", str(report))
        if written.returncode != 0 or fresh.returncode != 0:
            print(
                f"RENDER-SELFTEST-RED positive={(written.stderr + fresh.stderr).strip()}",
                file=sys.stderr,
            )
            return 2

        rendered = report.read_text(encoding="utf-8")
        checks: dict[str, tuple[list[str], str]] = {}

        flipped = temp / "flipped.md"
        flipped.write_text(rendered.replace("PASS", "PaSS", 1), encoding="utf-8")
        checks["report_byte_flipped"] = (["--output", str(flipped)], "is stale")

        checks["report_absent"] = (["--output", str(temp / "never-written.md")], "is absent")

        drifted = temp / "drifted-ledger.json"
        value = json.loads(LEDGER.read_text(encoding="utf-8"))
        entry = copy.deepcopy(value["skills"][0])
        entry["criteria"]["route_reachable"]["state"] = "PARTIAL"
        entry["criteria"]["route_reachable"]["owner_issue"] = value["audit_issue"]
        value["skills"][0] = entry
        drifted.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        checks["ledger_changed_without_rerender"] = (
            ["--ledger", str(drifted), "--output", str(report)],
            "is stale",
        )

        for name, (args, expected) in checks.items():
            done = run("--check", *args)
            if done.returncode == 0 or expected not in done.stderr:
                survivors.append(name)

    if survivors:
        print(f"RENDER-SELFTEST-RED survived={','.join(sorted(survivors))}", file=sys.stderr)
        return 2
    print("RENDER-SELFTEST-GREEN mutations=3 all refused by name")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
