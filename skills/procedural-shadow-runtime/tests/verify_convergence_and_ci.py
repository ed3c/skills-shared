#!/usr/bin/env python3
"""Controls for the #212 receipt binder and the #220 convergence packet.

Neither script may be run for real here: one needs a provider and the other
needs that provider's receipt. Both selftests are offline, and both are the
place their refusals are proven.

The packet check below is the one that matters over time. A convergence packet
whose terminal outcome drifts to ADMITTED without a Human Admit record is the
single worst failure this stack can have, and it would look like progress.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
BINDER = SKILL / "scripts" / "bind_actions_receipt.py"
PACKET = SKILL / "scripts" / "build_convergence_packet.py"


def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True, check=False)


def expect(name: str, script: Path, expected: int, *args: str) -> None:
    result = run(script, *args)
    if result.returncode != expected:
        raise SystemExit(
            f"{name}: expected exit {expected}, got {result.returncode}\n{result.stderr[-600:]}"
        )


expect("binder-selftest", BINDER, 0, "--selftest")
expect("binder-missing-arguments", BINDER, 64)
expect("packet-selftest", PACKET, 0, "--selftest")
expect("packet-missing-output", PACKET, 64)
expect("packet-absent-rollback-bundle", PACKET, 64,
       "--rollback-bundle", "/definitely/missing.json", "--output", "/dev/null")

with tempfile.TemporaryDirectory() as tmp:
    built = Path(tmp) / "packet.json"
    result = run(PACKET, "--output", str(built))
    if result.returncode not in (0, 2):
        raise SystemExit(f"packet build: unexpected exit {result.returncode}\n{result.stderr[-600:]}")
    packet = json.loads(built.read_text(encoding="utf-8"))

    if packet["terminal_outcome"] == "ADMITTED_FOR_BOUND_SCOPE" and not packet["human_admit"]:
        raise SystemExit("the packet admitted itself with no Human Admit record")
    if not packet["rollback"]["distinct_from_candidate"]:
        raise SystemExit("the rollback bundle resolves to the candidate tree")
    # Recorded identity must hold in a shallow checkout too. CI clones at
    # depth 1, so a rollback resolved from history is green only where the
    # author ran it.
    if packet["rollback"]["resolution_state"] not in {
        "RESOLVED_AND_MATCHES", "UNRESOLVABLE_IN_THIS_CHECKOUT"
    }:
        raise SystemExit(
            f"rollback identity drifted: {packet['rollback']['resolution_state']}"
        )
    if packet["security_privacy_licensing"]["privacy_scan"]["result"] != "CLEAN":
        raise SystemExit(
            "the packet's own privacy scan found forbidden values: "
            f"{packet['security_privacy_licensing']['privacy_scan']['findings']}"
        )

    # Every prerequisite issue must appear, closed or not. A lane that vanishes
    # from the packet has left the denominator.
    issues = {lane["issue"] for lane in packet["lanes"]}
    required = {"#212", "#213", "#214", "#215", "#216", "#217", "#218", "#219"}
    if issues != required:
        raise SystemExit(f"packet lanes {sorted(issues)} do not cover {sorted(required)}")

    for lane in packet["lanes"]:
        if lane["state"] == "PASS" and lane["receipts_present"] != lane["receipts_named"]:
            raise SystemExit(f"{lane['issue']} claims PASS with a missing receipt")

    # No level above the highest reachable one may be marked reachable: that is
    # what level skipping looks like in the artefact.
    reachable = [gate["level"] for gate in packet["level_gates"] if gate["reachable"]]
    ordered = [gate["level"] for gate in packet["level_gates"]]
    if reachable and reachable != ordered[:len(reachable)]:
        raise SystemExit(f"level gates skip a level: reachable={reachable}")

print(f"CONVERGENCE GREEN: both selftests pass; absent input and an unresolvable rollback exit 64; "
      f"the packet covers all eight prerequisite lanes, keeps a distinct rollback tree, scans "
      f"clean, never self-admits, and reaches {packet['highest_reachable_level']} with terminal "
      f"outcome {packet['terminal_outcome']}")
