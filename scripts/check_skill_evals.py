#!/usr/bin/env python3
"""Validate skill eval contracts and claim coverage using only the stdlib.

Public dev/gold cases live under evals/cases. Sealed holdout metadata lives under
evals/holdout and must contain only an opaque sealed_ref plus content hash, never
the actual prompt. This gate intentionally checks issue #16-style fabricated
coverage as well as holdout leakage.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_ROOTS = [ROOT / "evals" / "cases", ROOT / "evals" / "holdout"]
COVERAGE = ROOT / "evals" / "coverage.json"

class EvalError(Exception): pass

def load_object(path: Path) -> dict:
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise EvalError(f"{path.relative_to(ROOT)}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict): raise EvalError(f"{path.relative_to(ROOT)}: top level must be an object")
    return value

def nonempty_strings(value: object, *, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not value: raise EvalError(f"{path.relative_to(ROOT)}: {field} must be a non-empty array")
    if any(not isinstance(item, str) or not item.strip() for item in value): raise EvalError(f"{path.relative_to(ROOT)}: {field} must contain non-empty strings")
    if len(set(value)) != len(value): raise EvalError(f"{path.relative_to(ROOT)}: {field} contains duplicates")
    return value

def validate_case(path: Path) -> tuple[str, str, set[str]]:
    case = load_object(path)
    if case.get("schema_version") != "skill-eval/v1": raise EvalError(f"{path.relative_to(ROOT)}: unsupported schema_version")
    case_id, skill = case.get("id"), case.get("skill")
    if not isinstance(case_id, str) or not case_id.strip(): raise EvalError(f"{path.relative_to(ROOT)}: id must be a non-empty string")
    if not isinstance(skill, str) or not skill.strip(): raise EvalError(f"{path.relative_to(ROOT)}: skill must be a non-empty string")
    claims = set(nonempty_strings(case.get("claims"), field="claims", path=path))
    conditions = nonempty_strings(case.get("conditions"), field="conditions", path=path)
    if "candidate_skill" not in conditions or len(conditions) < 2: raise EvalError(f"{path.relative_to(ROOT)}: candidate_skill plus at least one comparison is required")
    task = case.get("task")
    if not isinstance(task, dict): raise EvalError(f"{path.relative_to(ROOT)}: task must be an object")
    split = case.get("split"); under_holdout = (ROOT / "evals" / "holdout") in path.parents
    prompt, sealed_ref, content_hash = task.get("prompt"), task.get("sealed_ref"), task.get("content_sha256")
    if split == "holdout":
        if not under_holdout: raise EvalError(f"{path.relative_to(ROOT)}: holdout case must live under evals/holdout")
        if prompt is not None: raise EvalError(f"{path.relative_to(ROOT)}: sealed holdout must not contain prompt text")
        if not isinstance(sealed_ref, str) or len(sealed_ref.strip()) < 8: raise EvalError(f"{path.relative_to(ROOT)}: sealed holdout requires opaque task.sealed_ref")
        if not isinstance(content_hash, str) or len(content_hash) != 64 or any(c not in '0123456789abcdef' for c in content_hash): raise EvalError(f"{path.relative_to(ROOT)}: sealed holdout requires lowercase sha256 content hash")
    else:
        if under_holdout: raise EvalError(f"{path.relative_to(ROOT)}: only split=holdout may live under evals/holdout")
        if not isinstance(prompt, str) or len(prompt.strip()) < 10: raise EvalError(f"{path.relative_to(ROOT)}: task.prompt is too short")
        if sealed_ref is not None or content_hash is not None: raise EvalError(f"{path.relative_to(ROOT)}: public case must not masquerade as sealed holdout")
    fixture = task.get("fixture")
    if fixture is not None:
        if not isinstance(fixture, str) or not fixture.strip(): raise EvalError(f"{path.relative_to(ROOT)}: task.fixture must be a non-empty path")
        fixture_path = (ROOT / fixture).resolve()
        try: fixture_path.relative_to(ROOT.resolve())
        except ValueError as exc: raise EvalError(f"{path.relative_to(ROOT)}: task.fixture escapes repository") from exc
        if not fixture_path.exists(): raise EvalError(f"{path.relative_to(ROOT)}: task.fixture does not exist: {fixture}")
    verifier = case.get("verifier")
    if not isinstance(verifier, dict): raise EvalError(f"{path.relative_to(ROOT)}: verifier must be an object")
    verifier_type = verifier.get("type")
    if verifier_type not in {"rule", "script", "artifact", "agent_judge", "composite"}: raise EvalError(f"{path.relative_to(ROOT)}: unsupported verifier.type")
    nonempty_strings(verifier.get("outcome_assertions"), field="verifier.outcome_assertions", path=path)
    if verifier_type == "agent_judge": raise EvalError(f"{path.relative_to(ROOT)}: agent_judge cannot be the sole verifier for a hard-gate case")
    if verifier_type == "script":
        command = verifier.get("command")
        if not isinstance(command, str) or not command.strip(): raise EvalError(f"{path.relative_to(ROOT)}: script verifier requires command")
        script_refs = [p for p in command.split() if p.endswith((".py", ".sh"))]
        if not script_refs or not (ROOT / script_refs[-1]).is_file(): raise EvalError(f"{path.relative_to(ROOT)}: verifier script does not resolve")
    return case_id, skill, claims

def main() -> int:
    errors, cases, case_paths = [], {}, []
    for root in CASE_ROOTS:
        if root.exists(): case_paths.extend(root.rglob("*.json"))
    case_paths = sorted(case_paths)
    if not case_paths: errors.append("evals: no runnable eval cases found")
    for path in case_paths:
        try:
            case_id, skill, claims = validate_case(path)
            if case_id in cases: errors.append(f"duplicate case id {case_id}: {cases[case_id][2].relative_to(ROOT)} and {path.relative_to(ROOT)}")
            else: cases[case_id] = (skill, claims, path)
        except EvalError as exc: errors.append(str(exc))
    try:
        coverage = load_object(COVERAGE); claim_map = coverage.get("claims")
        if coverage.get("schema_version") != "skill-eval-coverage/v1" or not isinstance(claim_map, dict) or not claim_map:
            errors.append("evals/coverage.json: invalid or empty coverage registry"); claim_map = {}
    except EvalError as exc: errors.append(str(exc)); claim_map = {}
    covered_case_ids = set()
    for claim_key, spec in claim_map.items():
        if not isinstance(claim_key, str) or ":" not in claim_key or not isinstance(spec, dict): errors.append(f"evals/coverage.json: malformed claim entry {claim_key!r}"); continue
        skill, claim = claim_key.split(":", 1)
        try: linked = nonempty_strings(spec.get("cases"), field=f"claims.{claim_key}.cases", path=COVERAGE)
        except EvalError as exc: errors.append(str(exc)); continue
        for case_id in linked:
            case = cases.get(case_id)
            if case is None: errors.append(f"evals/coverage.json: {claim_key} references missing case {case_id}"); continue
            case_skill, case_claims, _ = case
            if case_skill != skill: errors.append(f"evals/coverage.json: {claim_key} points to {case_id} owned by {case_skill}")
            if claim not in case_claims: errors.append(f"evals/coverage.json: fabricated coverage: {case_id} does not assert {claim}")
            covered_case_ids.add(case_id)
    for case_id, (skill, claims, path) in cases.items():
        for claim in claims:
            if f"{skill}:{claim}" not in claim_map: errors.append(f"{path.relative_to(ROOT)}: claim {claim} has no coverage registry entry")
        if case_id not in covered_case_ids: errors.append(f"{path.relative_to(ROOT)}: runnable case is not referenced by coverage registry")
    if errors:
        for error in errors: print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"PASS skill eval coverage: {len(cases)} cases, {len(claim_map)} claims"); return 0

if __name__ == "__main__": raise SystemExit(main())
