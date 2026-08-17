#!/usr/bin/env python3
"""Prove that the refactored Tech Lead Skill reaches executable mechanisms.

Zero-network: this validates repository bytes and routes only. It never promotes
provider/module/runtime execution to PASS. Causal semantics are owned by
assert_capability_dag.py and its mutation suite.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

MODULES = (
    "modules/deterministic-code-intelligence.md",
    "modules/semantic-intent-anchor.md",
    "modules/agent-executor.md",
    "modules/vector-store.md",
    "modules/stacked-delivery.md",
    "modules/tournament-mode.md",
)
CORE_ROUTES = (
    "modules/domain-profile.md",
    "scripts/check_task_contract_schema.py",
    "scripts/assert_task_contract.py",
    "scripts/assert_capability_dag.py",
    "references/task-contract.schema.json",
    "references/capability-plan.schema.json",
    "references/capability-receipts.schema.json",
    "references/t0-t10-causal-map.json",
    "references/fanout-prompt.md",
)
FORBIDDEN_SELF_ACTIVATION = (
    "activate itself merely because",
    "auto-activate itself because",
)
AUTHORITY_REFUSALS = (
    "may not override",
    "widen filesystem/network/secret/provider/merge authority",
)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class ReachabilityError(ValueError):
    pass


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReachabilityError(f"unreadable {path}: {exc}") from exc


def linked_targets(text: str) -> set[str]:
    return {target.split("#", 1)[0] for target in MARKDOWN_LINK.findall(text)}


def check(skill_root: Path) -> list[str]:
    errors: list[str] = []
    skill = skill_root / "SKILL.md"
    profile = skill_root / "modules" / "domain-profile.md"
    shape_gate = skill_root / "scripts" / "check_task_contract_schema.py"
    semantic_gate = skill_root / "scripts" / "assert_task_contract.py"
    capability_gate = skill_root / "scripts" / "assert_capability_dag.py"
    schema = skill_root / "references" / "task-contract.schema.json"
    capability_plan_schema = skill_root / "references" / "capability-plan.schema.json"
    capability_receipts_schema = skill_root / "references" / "capability-receipts.schema.json"
    causal_map = skill_root / "references" / "t0-t10-causal-map.json"
    prompt = skill_root / "references" / "fanout-prompt.md"
    run_all = skill_root / "tests" / "run-all.sh"
    selftest = skill_root / "tests" / "selftest.py"
    causal_selftest = skill_root / "tests" / "capability_dag_selftest.py"

    for path in (
        skill, profile, shape_gate, semantic_gate, capability_gate, schema,
        capability_plan_schema, capability_receipts_schema, causal_map, prompt,
        run_all, selftest, causal_selftest,
    ):
        if not path.is_file():
            errors.append(f"ABSENT {path.relative_to(skill_root)}")
    if errors:
        return errors

    skill_text = read(skill)
    profile_text = read(profile)
    shape_text = read(shape_gate)
    capability_text = read(capability_gate)
    run_all_text = read(run_all)

    for route in CORE_ROUTES:
        if route not in skill_text:
            errors.append(f"SKILL_ROUTE_MISSING {route}")

    for state in (
        "CAPABILITY_PLAN_COMPILED",
        "CAPABILITY_PLAN_ASSERTED",
        "CONTEXT_ADMITTED",
        "TASK_SCHEMA_ASSERTED",
        "TASK_SEMANTICS_ASSERTED",
    ):
        if state not in skill_text:
            errors.append(f"GATE_STATE_MISSING {state}")
    if "Before `ATTEMPTS_EXECUTED`" not in skill_text:
        errors.append("EXECUTOR_CAUSAL_ORDER_MISSING")
    if "Before `CANDIDATES_COMPARED`" not in skill_text:
        errors.append("TOURNAMENT_CAUSAL_ORDER_MISSING")
    if "Before `DELIVERY_HANDOFF`" not in skill_text:
        errors.append("DELIVERY_CAUSAL_ORDER_MISSING")
    if "--contract <task-contract.json>" not in skill_text or "--receipt <receipt.json>" not in skill_text:
        errors.append("TASK_GATE_INVOCATION_INCOMPLETE")
    if "--plan <capability-plan.json>" not in skill_text or "--receipts <capability-receipts.json>" not in skill_text:
        errors.append("CAPABILITY_GATE_INVOCATION_INCOMPLETE")

    if "task-contract.schema.json" not in shape_text:
        errors.append("SCHEMA_GATE_ROUTE_MISSING references/task-contract.schema.json")
    if "Draft202012Validator" not in shape_text:
        errors.append("SCHEMA_VALIDATOR_IDENTITY_MISSING Draft202012Validator")
    if "return 70" not in shape_text or "MECHANISM" not in shape_text:
        errors.append("SCHEMA_MECHANISM_FAILURE_NOT_DISTINCT")

    for route in ("capability-plan.schema.json", "capability-receipts.schema.json"):
        if route not in capability_text:
            errors.append(f"CAPABILITY_SCHEMA_ROUTE_MISSING {route}")
    for marker in ("LIVE_RECEIPT_REQUIRED", "PREDECESSOR_OUTPUT_NOT_CONSUMED", "RECEIPT_SUBJECT_MISMATCH"):
        if marker not in capability_text:
            errors.append(f"CAPABILITY_CAUSAL_ASSERTION_MISSING {marker}")

    profile_links = linked_targets(profile_text)
    for module in MODULES:
        module_rel = module.removeprefix("modules/")
        module_path = skill_root / module
        if not module_path.is_file():
            errors.append(f"MODULE_ABSENT {module}")
            continue
        if module_rel not in profile_links:
            errors.append(f"MODULE_ROUTE_MISSING {module}")
        module_text = read(module_path)
        for heading in ("## Trigger", "## Non-trigger", "## Fallback"):
            if heading not in module_text:
                errors.append(f"MODULE_CONTRACT_INCOMPLETE {module} {heading}")

    for route in ("capability-plan.schema.json", "capability-receipts.schema.json", "assert_capability_dag.py"):
        if route not in profile_text:
            errors.append(f"PROFILE_CAUSAL_ROUTE_MISSING {route}")

    lower_profile = profile_text.casefold()
    if not any(phrase in lower_profile for phrase in FORBIDDEN_SELF_ACTIVATION):
        errors.append("MODULE_SELF_ACTIVATION_REFUSAL_MISSING")
    if not all(phrase in lower_profile for phrase in AUTHORITY_REFUSALS):
        errors.append("MODULE_AUTHORITY_CEILING_MISSING")

    if "selftest.py" not in run_all_text:
        errors.append("SEMANTIC_NEGATIVE_CONTROLS_NOT_IN_OWNING_SUITE")
    if "check_runtime_reachability.py" not in run_all_text:
        errors.append("REACHABILITY_CHECK_NOT_IN_OWNING_SUITE")
    if "check_task_contract_schema.py" not in run_all_text or "--selftest" not in run_all_text:
        errors.append("SCHEMA_GATE_NOT_IN_OWNING_SUITE")
    if "assert_task_contract.py" not in run_all_text:
        errors.append("SEMANTIC_GATE_NOT_IN_OWNING_SUITE")
    if "capability_dag_selftest.py" not in run_all_text or "assert_capability_dag.py" not in run_all_text:
        errors.append("CAPABILITY_CAUSAL_GATE_NOT_IN_OWNING_SUITE")
    if "refactor_ab.py" not in run_all_text:
        errors.append("REFACTOR_AB_NOT_IN_OWNING_SUITE")

    return errors


def selftest(skill_root: Path) -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="tech-lead-reachability-") as tmp:
        root = Path(tmp) / "skill"
        shutil.copytree(skill_root, root)
        positive = check(root)
        if positive:
            return [f"SELFTEST_POSITIVE_RED {positive}"]

        skill_path = root / "SKILL.md"
        profile_path = root / "modules" / "domain-profile.md"
        shape_path = root / "scripts" / "check_task_contract_schema.py"
        capability_path = root / "scripts" / "assert_capability_dag.py"
        run_all_path = root / "tests" / "run-all.sh"
        originals = {path: read(path) for path in (skill_path, profile_path, shape_path, capability_path, run_all_path)}

        mutations: list[tuple[str, Path, str]] = [
            ("semantic-dispatch-route", skill_path, originals[skill_path].replace("scripts/assert_task_contract.py", "scripts/unreachable_task_gate.py")),
            ("shape-dispatch-route", skill_path, originals[skill_path].replace("scripts/check_task_contract_schema.py", "scripts/unreachable_schema_gate.py")),
            ("capability-dispatch-route", skill_path, originals[skill_path].replace("scripts/assert_capability_dag.py", "scripts/unreachable_capability_gate.py")),
            ("module-route", profile_path, originals[profile_path].replace("(agent-executor.md)", "(agent-executor-unreachable.md)", 1)),
            ("schema-route", shape_path, originals[shape_path].replace("task-contract.schema.json", "task-contract.unbound.json")),
            ("schema-validator", shape_path, originals[shape_path].replace("Draft202012Validator", "UnboundValidator")),
            ("capability-schema-route", capability_path, originals[capability_path].replace("capability-plan.schema.json", "capability-plan.unbound.json")),
            ("self-activation-refusal", profile_path, originals[profile_path].replace("a module never activates itself from executable presence, model preference, provider availability, or a previous run.", "modules may activate from executable presence.").replace("auto-activate itself because a tool is installed", "activate when a tool is installed")),
            ("authority-ceiling", profile_path, originals[profile_path].replace("may not override", "may override", 1).replace("widen filesystem/network/secret/provider/merge authority", "use filesystem/network/secret/provider/merge authority", 1)),
            ("owning-suite", run_all_path, originals[run_all_path].replace("check_runtime_reachability.py", "reachability-not-run.py")),
        ]

        for name, path, mutated in mutations:
            original = originals[path]
            path.write_text(mutated, encoding="utf-8")
            if not check(root):
                failures.append(f"SELFTEST_MUTATION_SURVIVED {name}")
            path.write_text(original, encoding="utf-8")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.skill_root).resolve()
    errors = check(root)
    if args.selftest and not errors:
        errors.extend(selftest(root))
    if errors:
        for error in errors:
            print(f"TECH-LEAD-REACHABILITY-RED {error}")
        return 2
    print("TECH-LEAD-REACHABILITY-GREEN task gates + causal capability routes closed; live adapters NOT_EXERCISED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
