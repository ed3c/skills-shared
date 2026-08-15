#!/usr/bin/env python3
"""Validate skill eval contracts, claim coverage, and benchmark freshness.

Public dev/gold cases live under evals/cases. Sealed holdout metadata lives under
evals/holdout and must contain only an opaque sealed_ref plus content hash, never
the actual prompt. Real-incident evals additionally bind to live implementation
anchors so deleted or moved code cannot leave an obsolete benchmark looking green.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_ROOTS = [ROOT / "evals" / "cases", ROOT / "evals" / "holdout"]
COVERAGE = ROOT / "evals" / "coverage.json"
REAL_INCIDENT_KINDS = {"github_issue", "production_incident"}
COMMENT_PREFIX_SUFFIXES = {".py", ".sh", ".yaml", ".yml", ".toml"}


class EvalError(Exception):
    pass


def load_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvalError(f"{path.relative_to(ROOT)}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise EvalError(f"{path.relative_to(ROOT)}: top level must be an object")
    return value


def nonempty_strings(value: object, *, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not value:
        raise EvalError(f"{path.relative_to(ROOT)}: {field} must be a non-empty array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise EvalError(f"{path.relative_to(ROOT)}: {field} must contain non-empty strings")
    if len(set(value)) != len(value):
        raise EvalError(f"{path.relative_to(ROOT)}: {field} contains duplicates")
    return value


def validate_implementation_targets(case: dict, path: Path, skill: str) -> None:
    source = case.get("source")
    source_kind = source.get("kind") if isinstance(source, dict) else None
    targets = case.get("implementation_targets")
    if source_kind in REAL_INCIDENT_KINDS and (not isinstance(targets, list) or not targets):
        raise EvalError(
            f"{path.relative_to(ROOT)}: real-incident eval requires implementation_targets "
            "so benchmark drift is observable"
        )
    if targets is None:
        return
    if not isinstance(targets, list) or not targets:
        raise EvalError(f"{path.relative_to(ROOT)}: implementation_targets must be a non-empty array")

    repo_root = ROOT.resolve()
    skill_root = (ROOT / "skills" / skill).resolve()
    seen: set[tuple[str, str]] = set()
    for index, target in enumerate(targets):
        label = f"implementation_targets[{index}]"
        if not isinstance(target, dict):
            raise EvalError(f"{path.relative_to(ROOT)}: {label} must be an object")
        raw_path, anchor = target.get("path"), target.get("anchor")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise EvalError(f"{path.relative_to(ROOT)}: {label}.path must be a non-empty string")
        if not isinstance(anchor, str) or len(anchor.strip()) < 3 or not any(ch.isalnum() for ch in anchor):
            raise EvalError(f"{path.relative_to(ROOT)}: {label}.anchor must be a meaningful token")
        identity = (raw_path, anchor)
        if identity in seen:
            raise EvalError(f"{path.relative_to(ROOT)}: duplicate implementation target {raw_path!r} / {anchor!r}")
        seen.add(identity)

        target_path = (ROOT / raw_path).resolve()
        try:
            target_path.relative_to(repo_root)
        except ValueError as exc:
            raise EvalError(f"{path.relative_to(ROOT)}: {label}.path escapes repository") from exc
        try:
            target_path.relative_to(skill_root)
        except ValueError as exc:
            raise EvalError(
                f"{path.relative_to(ROOT)}: {label}.path must stay under skills/{skill}/"
            ) from exc
        if not target_path.is_file():
            raise EvalError(
                f"{path.relative_to(ROOT)}: stale implementation target does not exist: {raw_path}"
            )
        try:
            lines = target_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            raise EvalError(f"{path.relative_to(ROOT)}: cannot read implementation target {raw_path}: {exc}") from exc
        candidates = [line for line in lines if line.strip()]
        if target_path.suffix.lower() in COMMENT_PREFIX_SUFFIXES:
            candidates = [line for line in candidates if not line.lstrip().startswith("#")]
        if not any(anchor in line for line in candidates):
            raise EvalError(
                f"{path.relative_to(ROOT)}: stale implementation anchor {anchor!r} not found "
                f"on a non-comment line in {raw_path}"
            )


def validate_case(path: Path) -> tuple[str, str, set[str]]:
    case = load_object(path)
    if case.get("schema_version") != "skill-eval/v1":
        raise EvalError(f"{path.relative_to(ROOT)}: unsupported schema_version")
    case_id, skill = case.get("id"), case.get("skill")
    if not isinstance(case_id, str) or not case_id.strip():
        raise EvalError(f"{path.relative_to(ROOT)}: id must be a non-empty string")
    if not isinstance(skill, str) or not skill.strip():
        raise EvalError(f"{path.relative_to(ROOT)}: skill must be a non-empty string")
    validate_implementation_targets(case, path, skill)
    claims = set(nonempty_strings(case.get("claims"), field="claims", path=path))
    conditions = nonempty_strings(case.get("conditions"), field="conditions", path=path)
    if "candidate_skill" not in conditions or len(conditions) < 2:
        raise EvalError(f"{path.relative_to(ROOT)}: candidate_skill plus at least one comparison is required")
    task = case.get("task")
    if not isinstance(task, dict):
        raise EvalError(f"{path.relative_to(ROOT)}: task must be an object")
    split = case.get("split")
    under_holdout = (ROOT / "evals" / "holdout") in path.parents
    prompt, sealed_ref, content_hash = task.get("prompt"), task.get("sealed_ref"), task.get("content_sha256")
    if split == "holdout":
        if not under_holdout:
            raise EvalError(f"{path.relative_to(ROOT)}: holdout case must live under evals/holdout")
        if prompt is not None:
            raise EvalError(f"{path.relative_to(ROOT)}: sealed holdout must not contain prompt text")
        if not isinstance(sealed_ref, str) or len(sealed_ref.strip()) < 8:
            raise EvalError(f"{path.relative_to(ROOT)}: sealed holdout requires opaque task.sealed_ref")
        if not isinstance(content_hash, str) or len(content_hash) != 64 or any(c not in "0123456789abcdef" for c in content_hash):
            raise EvalError(f"{path.relative_to(ROOT)}: sealed holdout requires lowercase sha256 content hash")
    else:
        if under_holdout:
            raise EvalError(f"{path.relative_to(ROOT)}: only split=holdout may live under evals/holdout")
        if not isinstance(prompt, str) or len(prompt.strip()) < 10:
            raise EvalError(f"{path.relative_to(ROOT)}: task.prompt is too short")
        if sealed_ref is not None or content_hash is not None:
            raise EvalError(f"{path.relative_to(ROOT)}: public case must not masquerade as sealed holdout")
    fixture = task.get("fixture")
    if fixture is not None:
        if not isinstance(fixture, str) or not fixture.strip():
            raise EvalError(f"{path.relative_to(ROOT)}: task.fixture must be a non-empty path")
        fixture_path = (ROOT / fixture).resolve()
        try:
            fixture_path.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise EvalError(f"{path.relative_to(ROOT)}: task.fixture escapes repository") from exc
        if not fixture_path.exists():
            raise EvalError(f"{path.relative_to(ROOT)}: task.fixture does not exist: {fixture}")
    verifier = case.get("verifier")
    if not isinstance(verifier, dict):
        raise EvalError(f"{path.relative_to(ROOT)}: verifier must be an object")
    verifier_type = verifier.get("type")
    if verifier_type not in {"rule", "script", "artifact", "agent_judge", "composite"}:
        raise EvalError(f"{path.relative_to(ROOT)}: unsupported verifier.type")
    nonempty_strings(verifier.get("outcome_assertions"), field="verifier.outcome_assertions", path=path)
    if verifier_type == "agent_judge":
        raise EvalError(f"{path.relative_to(ROOT)}: agent_judge cannot be the sole verifier for a hard-gate case")
    if verifier_type == "script":
        command = verifier.get("command")
        if not isinstance(command, str) or not command.strip():
            raise EvalError(f"{path.relative_to(ROOT)}: script verifier requires command")
        script_refs = [p for p in command.split() if p.endswith((".py", ".sh"))]
        if not script_refs or not (ROOT / script_refs[-1]).is_file():
            raise EvalError(f"{path.relative_to(ROOT)}: verifier script does not resolve")
    return case_id, skill, claims


def main() -> int:
    errors, cases, case_paths = [], {}, []
    for root in CASE_ROOTS:
        if root.exists():
            case_paths.extend(root.rglob("*.json"))
    case_paths = sorted(case_paths)
    if not case_paths:
        errors.append("evals: no runnable eval cases found")
    for path in case_paths:
        try:
            case_id, skill, claims = validate_case(path)
            if case_id in cases:
                errors.append(
                    f"duplicate case id {case_id}: {cases[case_id][2].relative_to(ROOT)} and {path.relative_to(ROOT)}"
                )
            else:
                cases[case_id] = (skill, claims, path)
        except EvalError as exc:
            errors.append(str(exc))
    try:
        coverage = load_object(COVERAGE)
        claim_map = coverage.get("claims")
        if coverage.get("schema_version") != "skill-eval-coverage/v1" or not isinstance(claim_map, dict) or not claim_map:
            errors.append("evals/coverage.json: invalid or empty coverage registry")
            claim_map = {}
    except EvalError as exc:
        errors.append(str(exc))
        claim_map = {}
    covered_case_ids = set()
    for claim_key, spec in claim_map.items():
        if not isinstance(claim_key, str) or ":" not in claim_key or not isinstance(spec, dict):
            errors.append(f"evals/coverage.json: malformed claim entry {claim_key!r}")
            continue
        skill, claim = claim_key.split(":", 1)
        try:
            linked = nonempty_strings(spec.get("cases"), field=f"claims.{claim_key}.cases", path=COVERAGE)
        except EvalError as exc:
            errors.append(str(exc))
            continue
        for case_id in linked:
            case = cases.get(case_id)
            if case is None:
                errors.append(f"evals/coverage.json: {claim_key} references missing case {case_id}")
                continue
            case_skill, case_claims, _ = case
            if case_skill != skill:
                errors.append(f"evals/coverage.json: {claim_key} points to {case_id} owned by {case_skill}")
            if claim not in case_claims:
                errors.append(f"evals/coverage.json: fabricated coverage: {case_id} does not assert {claim}")
            covered_case_ids.add(case_id)
    for case_id, (skill, claims, path) in cases.items():
        for claim in claims:
            if f"{skill}:{claim}" not in claim_map:
                errors.append(f"{path.relative_to(ROOT)}: claim {claim} has no coverage registry entry")
        if case_id not in covered_case_ids:
            errors.append(f"{path.relative_to(ROOT)}: runnable case is not referenced by coverage registry")
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"PASS skill eval coverage: {len(cases)} cases, {len(claim_map)} claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
