#!/usr/bin/env python3
"""Matched real-task A/B entry point for Agentic Tech Lead treatments."""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from real_task_fixture import (
    AUTHORITY, HISTORICAL, ROOT, TASK_ID, CanaryError, blob, build_subject,
    digest, dump, proc, sha_file, worker,
)
from real_task_runtime import run_arm


def features(text: str) -> dict[str, Any]:
    lower = text.casefold()
    return {"treatment_blob": blob(text), "task_gate": "scripts/assert_task_contract.py" in text,
            "capability_gate": "scripts/assert_capability_dag.py" in text,
            "t0_t10": ("T0 ROUTE" in text and "T10 HANDOFF" in text) or "t0-t10-causal-map.json" in text,
            "portable_core": "PORTABLE_CORE_START" in text,
            "global_objective": "global objective" in lower or "global-objective" in lower,
            "closure_laws": "closure lanes do not substitute" in lower and "completion-readiness" in lower,
            "offload_method": "tests/dual-agent-offload-contract/verify.py" in text and "may never claim it is implemented or live" in lower}


def treatment_metadata() -> dict[str, dict[str, Any]]:
    """Every historical arm is a frozen fixture; the newest arm is the live body.

    A treatment therefore has exactly one immutable subject. When the live body
    changes again, freeze it as the next fixture instead of letting the previous
    arm's identity drift with it.
    """
    out: dict[str, dict[str, Any]] = {}
    for name, (relative, expected) in HISTORICAL.items():
        text = (ROOT / relative).read_text(); observed = blob(text)
        if observed != expected: raise CanaryError(f"frozen treatment drift {name}")
        out[name] = features(text)
    out["B4_OFFLOAD_METHOD_BOUND"] = features((ROOT / "SKILL.md").read_text())
    return out


def task_contract(base: str, tree: str, lock: str) -> dict[str, Any]:
    return {"schema": "agentic-tech-lead/task-contract/v1", "task_id": TASK_ID, "mode": "TOURNAMENT", "subject": {"base_commit": base, "base_tree": tree},
        "goal": {"objective": "Implement parallel pricing/receipt Workers, tournament selection, and verified checkout convergence.", "non_goals": ["provider activation", "automatic merge", "new dependencies"]},
        "paths": {"write": ["src/**"], "read_only": ["contracts/**", "oracles/**"], "forbidden": [".git/**"], "changed": ["src/pricing.py", "src/receipt.py", "src/checkout.py"]},
        "architecture": {"interface_locks": [{"path": "contracts/checkout.py", "sha256": lock}], "dependency_policy": "NO_NEW_DEPENDENCIES", "allowed_dependencies": [], "state_policy": "integer cents/basis points; no global mutable state", "no_double_graph": True},
        "providers": [{"id": "scip-sqlite", "role": "DETERMINISTIC_GRAPH", "state": "DEGRADED"}, {"id": "tree-sitter", "role": "STRUCTURAL_SLICER", "state": "DEGRADED"}, {"id": "serena", "role": "AGENT_EXECUTOR", "state": "DEGRADED"}],
        "branches": [{"name": "pricing-minimal", "parent": "BASE", "focus": "minimal", "write": ["src/pricing.py"]}, {"name": "pricing-defensive", "parent": "BASE", "focus": "defensive", "write": ["src/pricing.py"]},
                     {"name": "pricing-buggy", "parent": "BASE", "focus": "negative-control", "write": ["src/pricing.py"]}, {"name": "receipt", "parent": "BASE", "focus": "receipt", "write": ["src/receipt.py"]},
                     {"name": "checkout", "parent": "VERIFIED_PREREQUISITES", "focus": "convergence", "write": ["src/checkout.py"]}],
        "acceptance": {"commands": [[sys.executable, f"oracles/{name}.py"] for name in ("pricing", "receipt", "checkout_local", "global")], "immutable_assertions": ["CONTRACT_LOCK", "LOCAL_ORACLES", "GLOBAL_OBJECTIVE", "FAILED_CANDIDATE_DENOMINATOR"]},
        "budgets": {"max_repairs_per_signature": 1, "max_workers": 5}, "automation": {"git_town_admitted": False, "auto_restack": False, "auto_publish": False, "auto_resolve_conflicts": False, "auto_merge": False}}


def capability_documents(base: str, tree: str) -> tuple[dict[str, Any], dict[str, Any]]:
    transitions = [
        {"id": "deterministic-context", "module_path": "modules/deterministic-code-intelligence.md", "selection": "REQUIRED", "trigger": {"matched": True, "evidence": ["immutable contracts/tests"]}, "predecessor_transitions": [], "requires_states": ["SYSTEM_CONTRACT_EXTRACTED"], "produces_state": "DETERMINISTIC_CONTEXT_READY", "required_before_state": "CONTEXT_ADMITTED", "fallback": "STOP", "runtime_state": "NOT_EXERCISED", "authority": AUTHORITY},
        {"id": "worker-execution", "module_path": "modules/agent-executor.md", "selection": "REQUIRED", "trigger": {"matched": True, "evidence": ["bounded worktree attempts"]}, "predecessor_transitions": ["deterministic-context"], "requires_states": ["CONTEXT_ADMITTED", "DETERMINISTIC_CONTEXT_READY"], "produces_state": "ATTEMPTS_EXECUTED", "required_before_state": "ATTEMPTS_EXECUTED", "fallback": "STOP", "runtime_state": "NOT_EXERCISED", "authority": AUTHORITY},
        {"id": "candidate-tournament", "module_path": "modules/tournament-mode.md", "selection": "REQUIRED", "trigger": {"matched": True, "evidence": ["three candidates share one contract"]}, "predecessor_transitions": ["worker-execution"], "requires_states": ["ATTEMPTS_EXECUTED"], "produces_state": "CANDIDATES_COMPARED", "required_before_state": "CANDIDATES_COMPARED", "fallback": "STOP", "runtime_state": "NOT_EXERCISED", "authority": AUTHORITY},
        {"id": "stack-delivery", "module_path": "modules/stacked-delivery.md", "selection": "NOT_APPLICABLE", "trigger": {"matched": False, "evidence": []}, "predecessor_transitions": [], "requires_states": ["GLOBAL_OBJECTIVE_ASSERTED"], "produces_state": "DELIVERY_HANDOFF", "required_before_state": "DELIVERY_HANDOFF", "fallback": "SKIP", "runtime_state": "NOT_EXERCISED", "authority": AUTHORITY},
    ]
    plan = {"schema": "agentic-tech-lead/capability-plan/v1", "task_id": TASK_ID, "subject": {"base_commit": base, "base_tree": tree}, "transitions": transitions}
    inputs = {"deterministic-context": ["SYSTEM_CONTRACT_EXTRACTED"], "worker-execution": ["CONTEXT_ADMITTED", "DETERMINISTIC_CONTEXT_READY"], "candidate-tournament": ["ATTEMPTS_EXECUTED"]}
    receipts = {"schema": "agentic-tech-lead/capability-receipts/v1", "receipts": [{"schema": "agentic-tech-lead/capability-receipt/v1", "task_id": TASK_ID, "transition_id": row["id"], "module_path": row["module_path"],
        "subject": {"base_commit": base, "base_tree": tree}, "attempt_id": f"fixture-{row['id']}", "evidence_kind": "FIXTURE", "verdict": "PASS", "input_states": inputs[row["id"]], "output_state": row["produces_state"],
        "evidence_sha256": digest(row["id"]), "source_readback": row["id"] == "deterministic-context", "authority": AUTHORITY} for row in transitions if row["selection"] != "NOT_APPLICABLE"]}
    return plan, receipts


def verify_live_gates(task: dict[str, Any], plan: dict[str, Any], receipts: dict[str, Any], temp: Path) -> dict[str, Any]:
    """Exercise the live gate scripts and their planted mutations.

    These are the current repository's checkers, so the receipts belong to the
    live arm, not to a frozen body that can no longer change them.
    """
    temp.mkdir(); paths = {name: temp / f"{name}.json" for name in ("task", "plan", "receipts")}; dump(paths["task"], task); dump(paths["plan"], plan); dump(paths["receipts"], receipts)
    task_receipt = temp / "task-receipt.json"
    commands = {
        "task_schema": [sys.executable, str(ROOT / "scripts/check_task_contract_schema.py"), "--contract", str(paths["task"])],
        "task_semantics": [sys.executable, str(ROOT / "scripts/assert_task_contract.py"), "--contract", str(paths["task"]), "--receipt", str(task_receipt)],
        "capability_causality": [sys.executable, str(ROOT / "scripts/assert_capability_dag.py"), "--contract", str(paths["task"]), "--plan", str(paths["plan"]), "--receipts", str(paths["receipts"]), "--admit-state", "CANDIDATES_COMPARED", "--fixture-mode"],
    }
    checks = {name: proc(cmd, cwd=ROOT, check=False).returncode == 0 for name, cmd in commands.items()}
    if not all(checks.values()): raise CanaryError(f"live gate failed {checks}")
    mutations: dict[str, tuple[dict[str, Any], list[str]]] = {}
    wrong_subject = copy.deepcopy(receipts); wrong_subject["receipts"][1]["subject"]["base_tree"] = "f" * 40
    wrong_module = copy.deepcopy(receipts); wrong_module["receipts"][1]["module_path"] = "modules/vector-store.md"
    missing_input = copy.deepcopy(receipts); missing_input["receipts"][2]["input_states"] = ["OTHER"]
    bad_contract = copy.deepcopy(task); bad_contract["paths"]["changed"].append("contracts/checkout.py")
    bad_test = copy.deepcopy(task); bad_test["paths"]["changed"].append("oracles/global.py")
    mutations.update({"wrong_subject": (wrong_subject, ["capability"]), "wrong_module": (wrong_module, ["capability"]), "missing_predecessor_consumption": (missing_input, ["capability"]),
                      "read_only_contract": (bad_contract, ["task"]), "immutable_test": (bad_test, ["task"])})
    planted: dict[str, bool] = {}
    for name, (value, kind) in mutations.items():
        path = temp / f"bad-{name}.json"; dump(path, value)
        if kind[0] == "capability": cmd = [sys.executable, str(ROOT / "scripts/assert_capability_dag.py"), "--contract", str(paths["task"]), "--plan", str(paths["plan"]), "--receipts", str(path), "--admit-state", "CANDIDATES_COMPARED", "--fixture-mode"]
        else: cmd = [sys.executable, str(ROOT / "scripts/assert_task_contract.py"), "--contract", str(path), "--receipt", str(temp / f"receipt-{name}.json")]
        planted[name] = proc(cmd, cwd=ROOT, check=False).returncode != 0
    live_cmd = commands["capability_causality"][:-1]; planted["fixture_cannot_promote_live"] = proc(live_cmd, cwd=ROOT, check=False).returncode != 0
    if not all(planted.values()): raise CanaryError(f"live gate mutation survived {planted}")
    return {"checks": checks, "planted": planted}


def compare() -> dict[str, Any]:
    metadata = treatment_metadata()
    with tempfile.TemporaryDirectory(prefix="tech-lead-real-task-") as raw:
        temp = Path(raw); subject, base, tree = build_subject(temp); task = task_contract(base, tree, sha_file(subject / "contracts/checkout.py")); plan, receipts = capability_documents(base, tree); gates = verify_live_gates(task, plan, receipts, temp / "live-gates")
        results: dict[str, Any] = {}
        for arm in ("A_OLD_MONOLITH", "B0_REFACTOR_AS_LANDED", "B1_REACHABILITY_REPAIRED", "B2_CAUSAL_DAG_REPAIRED", "B3_CLOSURE_LAWS_BOUND", "B4_OFFLOAD_METHOD_BOUND"):
            meta = metadata[arm]
            if arm == "B0_REFACTOR_AS_LANDED" and not meta["task_gate"]:
                results[arm] = {**meta, "execution_state": "BLOCKED_DISPATCH_ROUTE_ABSENT", "functional_output": "NOT_EXERCISED", "causal_closure": "FAIL"}; continue
            actual = run_arm(arm, subject, base, tree, temp, Path(__file__).resolve())
            closure = "PROCEDURAL_T0_T10_NO_CAPABILITY_RECEIPTS" if arm == "A_OLD_MONOLITH" else "REACHABLE_NOT_RECEIPT_GATED" if arm == "B1_REACHABILITY_REPAIRED" else "RECEIPT_GATED_FIXTURE_CLOSED"
            results[arm] = {**meta, **actual, "execution_state": "PASS", "causal_closure": closure, "live_gates": gates if arm == "B4_OFFLOAD_METHOD_BOUND" else None}
        executed = [row for row in results.values() if row.get("functional_output") == "PASS"]
        if len({row["content_digest"] for row in executed}) != 1: raise CanaryError("executed arms produced different bytes")
        if not results["A_OLD_MONOLITH"]["t0_t10"] or results["B1_REACHABILITY_REPAIRED"]["capability_gate"] or not results["B2_CAUSAL_DAG_REPAIRED"]["capability_gate"]: raise CanaryError("treatment identity/scoring drift")
        if results["B2_CAUSAL_DAG_REPAIRED"]["closure_laws"] or not results["B3_CLOSURE_LAWS_BOUND"]["closure_laws"]: raise CanaryError("closure-law treatment identity drift")
        if results["B3_CLOSURE_LAWS_BOUND"]["offload_method"] or not results["B4_OFFLOAD_METHOD_BOUND"]["offload_method"]: raise CanaryError("offload-method treatment identity drift")
        stages = {"contract_and_file_boundaries": "CLOSED_MECHANICALLY", "true_dag_worktrees_and_parallel_processes": "CLOSED_ON_SYNTHETIC_SUBJECT",
                  "checkpoint_retry_tournament_and_convergence": "CLOSED_ON_SYNTHETIC_SUBJECT", "global_objective_and_cleanup": "CLOSED_ON_SYNTHETIC_SUBJECT",
                  "grepai_scip_tree_sitter_serena_live_adapters": "NOT_EXERCISED", "git_town_restack_and_semantic_conflict": "NOT_EXERCISED",
                  "forgejo_github_publication": "NOT_EXERCISED", "matched_live_model_quality_cost_latency": "NOT_EXERCISED", "human_merge": "HUMAN_ADMIT_REQUIRED"}
        return {"schema": "agentic-tech-lead/real-task-ab/v1", "task": {"id": TASK_ID, "base_commit": base, "base_tree": tree, "same_base_tests_budgets_carrier": True},
                "results": results, "output_equivalence_for_executed_arms": True, "b0_runtime_regression_exposed": True,
                "b2_closure_dominates_without_model_claim": True, "b3_binds_closure_laws_without_model_claim": True, "b4_routes_offload_method_without_runtime_claim": True,
                "pdf_closed_loop_stage_state": stages, "behavioral_model_uplift": "NOT_EXERCISED",
                "live_provider_runtime": "NOT_EXERCISED", "git_town_forgejo_delivery": "NOT_EXERCISED", "merge_authority": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command"); w = sub.add_parser("worker")
    w.add_argument("--worktree", type=Path, required=True); w.add_argument("--task", choices=["pricing", "receipt", "checkout"], required=True); w.add_argument("--variant", required=True)
    w.add_argument("--owned-path", required=True); w.add_argument("--checkpoint", type=Path, required=True); w.add_argument("--attempt", required=True); w.add_argument("--delay-ms", type=int, default=0); w.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "worker": return worker(args)
        report = compare()
    except (CanaryError, OSError, subprocess.SubprocessError, KeyError, ValueError) as exc:
        print(f"TECH-LEAD-REAL-TASK-AB-RED {exc}", file=sys.stderr); return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    print("TECH-LEAD-REAL-TASK-AB-GREEN matched deterministic task closed; B0 route regression exposed; B2 receipt causality closed; B3 closure laws bound; B4 offload method routed from the live core; live model/provider/Stack/Forgejo uplift NOT_EXERCISED")
    return 0


if __name__ == "__main__": raise SystemExit(main())
