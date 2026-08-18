#!/usr/bin/env python3
"""Export a public skill-eval/v1 case into executor-neutral and skill-up runtime inputs.

This exporter does not execute a model and never resolves sealed holdouts. It only
materializes immutable run inputs. Promotion remains outside executor adapters.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS_SHA = "425e3f5a0c23e80f2c7933785d54c53ffe01b40c"

# Explicit physical protocols are intentionally case-scoped. A deterministic
# verifier may require more structure than the human-facing prompt exposes; we
# do not infer that hidden contract from prose at runtime.
RUNTIME_PROTOCOLS = {
    "autoresearch-metric-loop-plan": {
        "collect_artifacts": ["evidence/run.json", "artifacts/iteration-contract.json"],
        "prompt_suffix": """

Runtime evidence protocol (required for this evaluation):
- Do not only describe the plan in chat. Materialize `artifacts/iteration-contract.json` as a JSON object with non-empty keys: Goal, Scope, Metric, Direction, Verify, Guard, Iterations.
- Materialize `evidence/run.json` as JSON with: case_id=`autoresearch-metric-loop-plan`, decision=`invoke`, selected_skill=`autoresearch-composer`, and plan_artifact=`artifacts/iteration-contract.json`.
- These files are machine-verified after the agent exits. Do not claim success unless both files exist and match the requested contract.
""".strip(),
    }
}


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def public_case(case_id: str) -> tuple[Path, dict]:
    hits = list((ROOT / "evals" / "cases").rglob(f"{case_id}.json"))
    if len(hits) != 1:
        raise SystemExit(f"case {case_id!r}: expected exactly one public case, got {len(hits)}")
    case = load(hits[0])
    if case.get("split") == "holdout" or "sealed_ref" in case.get("task", {}):
        raise SystemExit("sealed holdout export is forbidden outside trusted runtime")
    return hits[0], case


def skill_up_config(case: dict, engine: str, provider: str, model: str) -> tuple[dict, dict]:
    protocol = RUNTIME_PROTOCOLS.get(case["id"])
    if protocol is None:
        raise SystemExit(f"case {case['id']!r} has no reviewed physical runtime protocol")
    prompt = case["task"]["prompt"].rstrip() + "\n\n" + protocol["prompt_suffix"]
    assertions = case["verifier"]["outcome_assertions"]
    eval_config = {
        "schema_version": "v1alpha1",
        "environment": {"type": "none"},
        "skills": [{"source": "local_path", "path": ".", "include": ["SKILL.md", "modules/**", "references/**", "scripts/**"]}],
        "engine": {"name": engine, "model": {"provider": provider, "name": model}},
        "cases": {
            "files": [f".runtime-eval/cases/{case['id']}.yaml"],
            "defaults": {
                "timeout_seconds": case.get("runtime", {}).get("timeout_seconds", 300),
                "max_turns": 12,
                "collect_artifacts": protocol["collect_artifacts"],
            },
            "parallelism": 1,
            "retry_policy": {"max_retries": 0, "retry_on": []}
        },
        "benchmark": {"enabled": True},
        "report": {"formats": ["json", "junit"], "artifacts": ["transcript"]}
    }
    case_config = {
        "id": case["id"],
        "title": f"skills-shared runtime export: {case['id']}",
        "input": {"prompt": prompt},
        # judge.model is required by the pinned skill-up whenever judge.type is
        # agent_judge, and it parses as "provider/name". Omitting it made every
        # export fail `skill-up validate` before a single model turn was spent,
        # which is why this exporter had never been physically exercised.
        "judge": {
            "type": "agent_judge",
            "model": f"{provider}/{model}",
            "criteria": assertions,
            "pass_threshold": 1.0,
        },
    }
    return eval_config, case_config


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--case", required=True)
    p.add_argument("--condition", required=True, choices=["current_skill", "candidate_skill"])
    p.add_argument("--skill-sha", required=True)
    p.add_argument("--engine", required=True)
    p.add_argument("--provider", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--skill-root", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    if len(args.skill_sha) != 40 or any(c not in "0123456789abcdef" for c in args.skill_sha):
        raise SystemExit("--skill-sha must be a lowercase 40-character commit SHA")

    case_path, case = public_case(args.case)
    skill_root = Path(args.skill_root).resolve()
    if not (skill_root / "SKILL.md").is_file():
        raise SystemExit(f"skill root has no SKILL.md: {skill_root}")

    out = Path(args.out).resolve()
    eval_config, case_config = skill_up_config(case, args.engine, args.provider, args.model)
    runtime_dir = skill_root / ".runtime-eval"
    dump(runtime_dir / "eval.yaml", eval_config)
    dump(runtime_dir / "cases" / f"{case['id']}.yaml", case_config)

    manifest = {
        "schema_version": "skill-eval-runtime-manifest/v1",
        "case_id": case["id"],
        "case_sha256": sha256(case_path),
        "skill": case["skill"],
        "condition": args.condition,
        "skill_sha": args.skill_sha,
        "executor": "skill-up",
        "executor_sha": HARNESS_SHA,
        "engine": args.engine,
        "provider": args.provider,
        "model": args.model,
        "fresh_workspace": bool(case.get("runtime", {}).get("fresh_workspace", False)),
        "max_retries": 0,
        "sampling": {
            "required_repetitions": int(case.get("runtime", {}).get("seed_count", 1)),
            "seed_controlled": False,
            "reason": "pinned skill-up CLI exposes iteration sampling but no model-seed flag",
        },
        "deterministic_artifacts": RUNTIME_PROTOCOLS[case["id"]]["collect_artifacts"],
        "promotion_authority": False,
        "skill_target": str((runtime_dir / "eval.yaml").relative_to(ROOT)) if runtime_dir.is_relative_to(ROOT) else str(runtime_dir / "eval.yaml")
    }
    dump(out, manifest)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
