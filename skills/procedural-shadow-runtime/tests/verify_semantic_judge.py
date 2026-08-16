#!/usr/bin/env python3
"""Controls for the semantic-judge gate.

The gate exists for one sentence: a judge may lower a score but may never turn a
deterministic failure into PASS. So the control that matters most is the one that
plants exactly that and requires a refusal. Everything else here guards the
supporting rules that make the sentence checkable -- an unnamed failure, an
unavailable judge scoring anyway, an anchor behaving backwards.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CHECKER = SKILL / "scripts" / "check_semantic_judge.py"
SCHEMA_ROOT = SKILL / "references"

D64 = "a" * 64


def verdict(**overrides) -> dict:
    base = {
        "schema": "semantic-judge-verdict/v1",
        "case": {
            "case_id": "case-1", "case_digest": D64, "evidence_digest": D64,
            "presentation_order": 0, "blinded": True, "duplicate_of": None,
            "anchor": "NONE",
        },
        "rubric": {
            "rubric_id": "r/v1", "rubric_digest": D64,
            "scale_min": 0.0, "scale_max": 5.0, "threshold": 3.0,
        },
        "candidate": {"output_digest": D64, "produced_by": "claude-code"},
        "judge": {
            "provider": "openai", "model": "gpt-5.6-sol", "version": "0.146.0",
            "config_digest": D64, "prompt_template_digest": D64,
            "repetition_identity": "order-0", "available": True,
            "shares_session_with_candidate": False,
        },
        "deterministic": {"result": "PASS", "failed_gates": []},
        "advisory_scores": {
            "evidence_use": 4.0, "explanation_completeness": 4.0,
            "contradiction_handling": 4.0, "unsupported_claim_avoidance": 4.0,
            "clarity": 4.0,
        },
        "verdict": {
            "overall": 4.0, "outcome": "PASS", "rationale": "grounded",
            "cited_evidence": ["tests/test_requests.py"],
        },
        "usage": {"latency_ms": 100, "input_tokens": 10, "output_tokens": 5,
                  "cost_usd": 0.0, "cost_observed": False},
    }
    for path, value in overrides.items():
        node = base
        parts = path.split(".")
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = value
    return base


def run(documents: list[dict]) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for index, document in enumerate(documents):
            path = Path(tmp) / f"v{index}.json"
            path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            paths.append(str(path))
        process = subprocess.run(
            [sys.executable, str(CHECKER), *paths, "--schema-root", str(SCHEMA_ROOT)],
            capture_output=True, text=True, check=False,
        )
        return process.returncode, process.stderr


def main() -> int:
    failures: list[str] = []

    code, stderr = run([verdict()])
    if code != 0:
        failures.append(f"positive verdict refused: {stderr!r}")

    # A judge lowering a score on a deterministic PASS is its whole job.
    lowered = verdict()
    lowered["advisory_scores"]["evidence_use"] = 1.0
    lowered["verdict"]["overall"] = 2.0
    lowered["verdict"]["outcome"] = "FAIL"
    code, stderr = run([lowered])
    if code != 0:
        failures.append(f"judge lowering a passing case was refused: {stderr!r}")

    # An unavailable judge degrades to NOT_EXERCISED, which is admitted.
    unavailable = verdict()
    unavailable["judge"]["available"] = False
    unavailable["verdict"]["outcome"] = "NOT_EXERCISED"
    unavailable["verdict"]["cited_evidence"] = []
    code, stderr = run([unavailable])
    if code != 0:
        failures.append(f"unavailable judge degrading to NOT_EXERCISED was refused: {stderr!r}")

    cases = [
        ("deterministic-override",
         {"deterministic.result": "FAIL", "deterministic.failed_gates": ["safety"]},
         "deterministic-override"),
        ("unnamed-deterministic-failure",
         {"deterministic.result": "FAIL", "deterministic.failed_gates": [],
          "verdict.outcome": "FAIL", "verdict.overall": 1.0},
         "unnamed-deterministic-failure"),
        ("failed-gates-without-failure",
         {"deterministic.failed_gates": ["safety"]},
         "failed-gates-without-failure"),
        ("unavailable-judge-scored",
         {"judge.available": False},
         "unavailable-judge-scored"),
        ("available-judge-not-exercised",
         {"verdict.outcome": "NOT_EXERCISED"},
         "available-judge-not-exercised"),
        ("score-out-of-scale",
         {"advisory_scores.clarity": 9.0},
         "score-out-of-scale:clarity"),
        ("overall-out-of-scale",
         {"verdict.overall": 99.0},
         "overall-out-of-scale"),
        ("outcome-contradicts-threshold",
         {"verdict.overall": 1.0},
         "outcome-contradicts-threshold"),
        ("injection-anchor-passed",
         {"case.anchor": "INJECTION"},
         "injection-anchor-passed"),
        ("negative-anchor-passed",
         {"case.anchor": "NEGATIVE"},
         "negative-anchor-passed"),
        ("positive-anchor-failed",
         {"case.anchor": "POSITIVE", "verdict.overall": 1.0, "verdict.outcome": "FAIL"},
         "positive-anchor-failed"),
        ("verdict-without-cited-evidence",
         {"verdict.cited_evidence": []},
         "verdict-without-cited-evidence"),
    ]
    for name, overrides, marker in cases:
        code, stderr = run([verdict(**overrides)])
        if code != 2 or marker not in stderr:
            failures.append(f"{name}: expected code=2 marker={marker!r}; got {code} {stderr!r}")

    # A judge sharing session context with the evaluated model is not external,
    # and the schema makes that unspellable rather than merely discouraged.
    shared = verdict()
    shared["judge"]["shares_session_with_candidate"] = True
    code, stderr = run([shared])
    if code != 64 or "schema-invalid" not in stderr:
        failures.append(f"shared session: expected 64/schema-invalid, got {code} {stderr!r}")

    # Disagreement between repeats is reported, not averaged away.
    first = verdict()
    second = verdict(**{"case.duplicate_of": "case-1", "verdict.overall": 2.0,
                        "verdict.outcome": "FAIL"})
    second["case"]["case_id"] = "case-1-repeat"
    second["advisory_scores"] = {k: 2.0 for k in second["advisory_scores"]}
    process = subprocess.run(
        [sys.executable, str(CHECKER)], capture_output=True, text=True, check=False
    )
    code, stderr = run([first, second])
    if code != 0:
        failures.append(f"repeat pair refused: {stderr!r}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1

    print(
        "SEMANTIC JUDGE GREEN: a lowered score and an unavailable judge are admitted; "
        f"{len(cases)} planted override, anchor, scale and availability defects refused; "
        "a judge sharing the candidate's session is unspellable"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
