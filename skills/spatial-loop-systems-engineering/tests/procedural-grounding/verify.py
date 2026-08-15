#!/usr/bin/env python3
"""Positive, hollow, and mutation controls for procedural grounding."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

TEST_DIR = Path(__file__).resolve().parent
SKILL_DIR = TEST_DIR.parents[1]
CHECKER = SKILL_DIR / "scripts" / "check_procedural_grounding.py"
SCHEMA = SKILL_DIR / "references" / "procedural-grounding-receipt.schema.json"
FIXTURE = TEST_DIR / "fixtures" / "valid.json"


def run(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(path)],
        text=True,
        capture_output=True,
        check=False,
    )


def write_temp(data: dict[str, Any]) -> Path:
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
    with handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return Path(handle.name)


def expect_exit(label: str, path: Path, code: int) -> None:
    result = run(path)
    if result.returncode != code:
        print(f"FAIL {label}: expected exit {code}, got {result.returncode}", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS {label}: exit {code}")


def mutate(base: dict[str, Any], label: str, fn: Callable[[dict[str, Any]], None]) -> None:
    candidate = copy.deepcopy(base)
    fn(candidate)
    path = write_temp(candidate)
    try:
        expect_exit(label, path, 2)
    finally:
        path.unlink(missing_ok=True)


def main() -> int:
    reference = (SKILL_DIR / "references" / "procedural-grounding-shadow-plane.md").read_text(encoding="utf-8")
    module = (SKILL_DIR / "modules" / "agent-host-procedural-grounding.md").read_text(encoding="utf-8")
    readme = (SKILL_DIR / "README.md").read_text(encoding="utf-8")
    required_phrases = {
        "reference": [
            "observable behavioral procedural uptake",
            "SKILL_DISCOVERY",
            "FIRST_VERTICAL_SLICE",
            "NOVELTY_OR_DIVERGENCE",
            "FIRST_GREEN",
            "L0_EXACT_PROCEDURE",
            "L5_META_CANDIDATE",
            "Context Capsule",
            "NO_SKILL",
            "FULL_SKILL_PLUS_GROUNDING",
            "private reasoning trace",
        ],
        "module": [
            "skills.sh",
            "Skillsmith",
            "context: fork",
            "Codex CLI/app adapter",
            "IN_PROCESS_LOGICAL",
            "SEPARATE_CONTEXT",
            "is not a sandbox",
        ],
        "readme": [
            "PROCEDURAL_GROUNDING_DELTA",
            "procedural-grounding-receipt.schema.json",
            "check_procedural_grounding.py",
        ],
    }
    for label, phrases in required_phrases.items():
        body = {"reference": reference, "module": module, "readme": readme}[label]
        for phrase in phrases:
            if phrase not in body:
                print(f"FAIL {label} is missing required phrase {phrase!r}", file=sys.stderr)
                return 1
    print("PASS procedural grounding docs retain checkpoints, abstraction, attribution, host, and no-raw-reasoning boundaries")

    base = json.loads(FIXTURE.read_text(encoding="utf-8"))
    json.loads(SCHEMA.read_text(encoding="utf-8"))
    print("PASS schema parses as JSON")

    expect_exit("positive receipt", FIXTURE, 0)
    expect_exit("absent receipt", TEST_DIR / "fixtures" / "absent.json", 64)

    malformed = Path(tempfile.mkstemp(suffix=".json")[1])
    malformed.write_text("{not-json", encoding="utf-8")
    try:
        expect_exit("malformed receipt", malformed, 64)
    finally:
        malformed.unlink(missing_ok=True)

    mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("critical execution reduced to mention", lambda d: d["observations"][2].update(uptake_state="MENTIONED", evidence_modality="MODEL_OUTPUT", exit_code=None)),
        ("negative control not executed", lambda d: d["observations"][3].update(uptake_state="OBSERVED")),
        ("critical novel obligation left open", lambda d: d["obligations"][0].update(status="OPEN", evidence_ref=None)),
        ("unreviewed skill source", lambda d: d["skill_sources"][0].update(trust_state="UNREVIEWED")),
        ("blocked skill license", lambda d: d["skill_sources"][0].update(license_state="BLOCKED")),
        ("unreviewed executable skill script", lambda d: d["skill_sources"][0].update(scripts_state="UNREVIEWED")),
        ("denied dynamic context", lambda d: d["skill_sources"][0].update(dynamic_context_state="DENIED")),
        ("fork depth exceeds policy", lambda d: d["forks"][0].update(spawn_depth=9)),
        ("fork token budget exceeded", lambda d: d["forks"][0].update(tokens_used=3001)),
        ("global fork token budget exceeded", lambda d: d["policy"].update(max_total_tokens=2000)),
        ("unbounded no-progress epochs", lambda d: d["forks"][0].update(progress_epochs=[{"epoch": 1, "coverage_gain": 0.1}, {"epoch": 2, "coverage_gain": 0.1}, {"epoch": 3, "coverage_gain": 0.1}])),
        ("raw reasoning payload rejected", lambda d: d["capsules"][0].update(payload_kind="RAW_REASONING_TRACE")),
        ("low groundedness capsule injected", lambda d: d["capsules"][0].update(source_groundedness=0.1)),
        ("stale capsule injected", lambda d: d["capsules"][0].update(fresh_for_subject_sha="7777777777777777777777777777777777777777")),
        ("capsule token budget exceeded", lambda d: d["capsules"][0].update(token_count=9999)),
        ("authority-conflicted capsule injected", lambda d: d["capsules"][0].update(authority_conflict=True)),
        ("capsule expires before creation", lambda d: d["capsules"][0].update(expires_after_checkpoint="ARCHITECTURE_CHOICE")),
        ("stale runtime observation", lambda d: d["observations"][2].update(subject_sha="8888888888888888888888888888888888888888")),
        ("execution claimed from model output", lambda d: d["observations"][2].update(evidence_modality="MODEL_OUTPUT")),
        ("negative-control proof assigned to execution atom", lambda d: d["observations"][2].update(uptake_state="NEGATIVE_CONTROL_PASSED")),
        ("declared coverage is inflated", lambda d: d["declared_metrics"].update(execution_coverage=1.0)),
        ("unknown runtime promoted to PASS", lambda d: d["subject"].update(runtime="UNKNOWN")),
        ("separate context lacks provenance", lambda d: d["forks"][0].update(context_provenance="")),
        ("not-exercised attribution publishes lift", lambda d: d["attribution"].update(skill_lift=0.5)),
        ("external human proof promoted by checker", lambda d: d["procedure_atoms"][2].update(proof_mode="EXTERNAL_OR_HUMAN")),
        ("duplicate procedure identity", lambda d: d["procedure_atoms"][1].update(procedure_id="PROC-001")),
        ("unknown top-level field", lambda d: d.update(raw_reasoning_chain="forbidden")),
    ]

    for label, fn in mutations:
        mutate(base, label, fn)

    print(f"PROCEDURAL GROUNDING GREEN: positive=1 mutations_refused={len(mutations)} input_errors=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
