#!/usr/bin/env python3
"""Positive, semantic-mutation, and input-error controls for meta abstraction eval."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_meta_abstraction_eval.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "valid-meta-eval.json"


def run(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(path)],
        text=True,
        capture_output=True,
        check=False,
    )


def expect(path: Path, code: int, label: str) -> None:
    result = run(path)
    if result.returncode != code:
        raise AssertionError(
            f"{label}: expected exit {code}, got {result.returncode}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )


def write_case(directory: Path, label: str, data: dict) -> Path:
    path = directory / f"{label}.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main() -> int:
    valid = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expect(FIXTURE, 0, "positive")

    mutations: list[tuple[str, Callable[[dict], None]]] = [
        ("safety-violation", lambda d: d["controls"].__setitem__("safety_violations", 1)),
        ("unresolved-must", lambda d: (
            d["grounding"].__setitem__("must_terminal", 11),
            d["grounding"].__setitem__("unresolved_must", 1),
        )),
        ("negative-control-absent", lambda d: d["controls"].__setitem__("negative_control_executed", False)),
        ("held-out-absent", lambda d: d["generalization"].__setitem__("held_out_family_count", 0)),
        ("counterfactual-incomplete", lambda d: (
            d["generalization"]["conditions_exercised"].remove("METADATA_ONLY"),
            d["generalization"]["condition_success_rates"].pop("METADATA_ONLY"),
        )),
        ("l5-without-production-closure", lambda d: (
            d["candidate"].__setitem__("current_level", "L4"),
            d["candidate"].__setitem__("target_level", "L5"),
        )),
        ("accuracy-regression", lambda d: d["regression"]["candidate"].__setitem__("accuracy", 0.97)),
        ("token-regression", lambda d: d["regression"]["candidate"].__setitem__("avg_tokens", 1450.0)),
        ("latency-regression", lambda d: d["regression"]["candidate"].__setitem__("p95_latency_ms", 6000.0)),
        ("schema-regression", lambda d: d["regression"]["candidate"].__setitem__("schema_failure_rate", 0.002)),
        ("raw-private-reasoning", lambda d: d["controls"].__setitem__("raw_private_reasoning", True)),
        ("candidate-private-reasoning", lambda d: d["candidate"].__setitem__("raw_private_reasoning", True)),
        ("capability-widening", lambda d: d["controls"].__setitem__("unauthorized_capability_widening", True)),
        ("private-data-egress", lambda d: d["controls"].__setitem__("private_data_egress", True)),
        ("hidden-cot-claim", lambda d: d["controls"].__setitem__("model_weights_or_hidden_cot_claimed", True)),
        ("shadow-write-authority", lambda d: d["controls"].__setitem__("shadow_workers_read_only", False)),
        ("human-authority-removed", lambda d: d["controls"].__setitem__("human_promotion_authority", False)),
        ("rights-review-missing", lambda d: d["controls"].__setitem__("source_rights_reviewed", False)),
        ("declared-score-tamper", lambda d: d["promotion"].__setitem__("declared_raw_meta_score", 99.0)),
        ("level-skip", lambda d: d["candidate"].__setitem__("current_level", "L2")),
        ("duplicate-condition", lambda d: d["generalization"]["conditions_exercised"].append("NO_SKILL")),
        ("source-digest-missing", lambda d: d["candidate"]["source_anchors"][0].pop("content_sha256")),
        ("trace-incomplete", lambda d: d["regression"]["feedback"].__setitem__("trace_completeness", 0.80)),
    ]

    with tempfile.TemporaryDirectory(prefix="meta-eval-controls-") as tmp:
        directory = Path(tmp)
        for label, mutate in mutations:
            case = copy.deepcopy(valid)
            mutate(case)
            expect(write_case(directory, label, case), 2, label)

        malformed = directory / "malformed.json"
        malformed.write_text("{not-json", encoding="utf-8")
        expect(malformed, 64, "malformed-input")
        expect(directory / "absent.json", 64, "absent-input")

    print(
        "META ABSTRACTION EVAL GREEN: "
        f"positive=1 mutations_refused={len(mutations)} input_errors=2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
