#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "agentic-tech-lead/task-contract/v1"
ALLOWED_MODES = {"STACK", "TOURNAMENT"}
ALLOWED_STATES = {"EXACT", "DEGRADED", "BLOCKED"}
ROLE_BY_PROVIDER = {"grepai": "INTENT_ANCHOR", "scip-sqlite": "DETERMINISTIC_GRAPH", "tree-sitter": "STRUCTURAL_SLICER", "serena": "AGENT_EXECUTOR", "lancedb": "VECTOR_CANDIDATE_STORE"}
FORBIDDEN_PROVIDERS = {"code-graph-rag", "code_graph_rag", "code graph rag"}
HEX_RE = re.compile(r"^[0-9a-f]{7,64}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

class UsageError(Exception): pass

@dataclass(frozen=True)
class Failure:
    assertion: str
    detail: str

def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file(): raise UsageError(f"contract not found: {path}")
    if path.stat().st_size > 4 * 1024 * 1024: raise UsageError("contract exceeds 4 MiB")
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise UsageError(f"invalid contract JSON: {exc}") from exc
    if not isinstance(value, dict): raise UsageError("contract root must be an object")
    return value

def _canonical_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def _is_safe_repo_path(value: Any, *, allow_git_forbidden: bool = False) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"): return False
    path = PurePosixPath(value)
    if ".." in path.parts: return False
    if path.parts[:1] == (".git",): return allow_git_forbidden
    return True

def _matches(path: str, pattern: str) -> bool:
    if fnmatch.fnmatchcase(path, pattern): return True
    if pattern.endswith("/**"):
        root = pattern[:-3].rstrip("/")
        return path == root or path.startswith(root + "/")
    return False

def _list(value: Any) -> list[Any]: return value if isinstance(value, list) else []

def _validate_exact_provider_subject(provider_id: str, provider: dict[str, Any], task_subject: dict[str, Any], failures: list[Failure]) -> None:
    subject = provider.get("subject")
    if not isinstance(subject, dict):
        failures.append(Failure("PROVIDER_EXACT_SUBJECT", f"{provider_id} EXACT requires subject metadata")); return
    for key in ("commit", "tree"):
        value = subject.get(key); expected = task_subject.get("base_commit" if key == "commit" else "base_tree")
        if not isinstance(value, str) or not HEX_RE.fullmatch(value): failures.append(Failure("PROVIDER_EXACT_SUBJECT", f"{provider_id} subject.{key} must be immutable hex"))
        elif value != expected: failures.append(Failure("PROVIDER_SUBJECT_MISMATCH", f"{provider_id} subject.{key} != task subject"))
    if not isinstance(subject.get("version"), str) or not subject.get("version", "").strip(): failures.append(Failure("PROVIDER_EXACT_SUBJECT", f"{provider_id} subject.version is required"))
    coverage = subject.get("coverage_sha256")
    if not isinstance(coverage, str) or not SHA256_RE.fullmatch(coverage): failures.append(Failure("PROVIDER_EXACT_SUBJECT", f"{provider_id} subject.coverage_sha256 is required"))
    if subject.get("source_readback") is not True: failures.append(Failure("PROVIDER_EXACT_SUBJECT", f"{provider_id} EXACT requires source_readback=true"))

def validate(contract: dict[str, Any]) -> list[Failure]:
    failures: list[Failure] = []
    def fail(assertion: str, detail: str) -> None: failures.append(Failure(assertion, detail))
    required = {"schema","task_id","mode","subject","goal","paths","architecture","case_obligations","providers","branches","acceptance","budgets","automation"}
    missing = sorted(required - contract.keys())
    if missing: fail("REQUIRED_FIELDS", f"missing: {', '.join(missing)}")
    if contract.get("schema") != SCHEMA: fail("SCHEMA_ID", f"expected {SCHEMA}")
    if not isinstance(contract.get("task_id"), str) or not contract.get("task_id", "").strip(): fail("TASK_ID", "task_id must be a non-empty string")
    mode = contract.get("mode")
    if mode not in ALLOWED_MODES: fail("MODE", "mode must be STACK or TOURNAMENT")

    subject = contract.get("subject") if isinstance(contract.get("subject"), dict) else {}
    for key in ("base_commit", "base_tree"):
        value = subject.get(key)
        if not isinstance(value, str) or not HEX_RE.fullmatch(value): fail("IMMUTABLE_SUBJECT", f"subject.{key} must be a 7-64 lowercase hex id")

    goal = contract.get("goal") if isinstance(contract.get("goal"), dict) else {}
    if not isinstance(goal.get("objective"), str) or not goal.get("objective", "").strip(): fail("GOAL", "goal.objective must be non-empty")
    if not isinstance(goal.get("non_goals"), list): fail("GOAL", "goal.non_goals must be an array")

    paths = contract.get("paths") if isinstance(contract.get("paths"), dict) else {}
    write, read_only, forbidden, changed = map(_list, (paths.get("write"), paths.get("read_only"), paths.get("forbidden"), paths.get("changed")))
    if not write: fail("PATH_LEASE", "paths.write must be non-empty")
    for group_name, values in (("write",write),("read_only",read_only),("forbidden",forbidden),("changed",changed)):
        for value in values:
            if not _is_safe_repo_path(value, allow_git_forbidden=(group_name == "forbidden")): fail("SAFE_PATH", f"paths.{group_name} contains unsafe path/pattern: {value!r}")
    for path in changed:
        if not isinstance(path, str): continue
        if any(_matches(path,p) for p in forbidden if isinstance(p,str)): fail("FORBIDDEN_PATH", f"changed path is forbidden: {path}")
        if any(_matches(path,p) for p in read_only if isinstance(p,str)): fail("READ_ONLY_PATH", f"changed path is read-only: {path}")
        if not any(_matches(path,p) for p in write if isinstance(p,str)): fail("WRITE_BOUNDARY", f"changed path is outside write lease: {path}")

    architecture = contract.get("architecture") if isinstance(contract.get("architecture"), dict) else {}
    locks = _list(architecture.get("interface_locks"))
    if not locks: fail("INTERFACE_LOCKS", "at least one interface lock is required")
    for index, lock in enumerate(locks):
        if not isinstance(lock, dict) or not _is_safe_repo_path(lock.get("path")) or not isinstance(lock.get("sha256"), str) or not SHA256_RE.fullmatch(lock["sha256"]): fail("INTERFACE_LOCKS", f"interface_locks[{index}] requires safe path and sha256")
    dependency_policy = architecture.get("dependency_policy")
    if dependency_policy not in {"NO_NEW_DEPENDENCIES","ALLOWLIST"}: fail("DEPENDENCY_POLICY", "dependency_policy must be NO_NEW_DEPENDENCIES or ALLOWLIST")
    if dependency_policy == "ALLOWLIST" and not isinstance(architecture.get("allowed_dependencies"), list): fail("DEPENDENCY_POLICY", "ALLOWLIST requires allowed_dependencies array")
    if not isinstance(architecture.get("state_policy"), str) or not architecture.get("state_policy", "").strip(): fail("STATE_POLICY", "state_policy must be non-empty")
    if architecture.get("no_double_graph") is not True: fail("NO_DOUBLE_GRAPH", "architecture.no_double_graph must be true")

    providers = _list(contract.get("providers")); seen_providers:set[str]=set(); provider_states:dict[str,str]={}
    for index, provider in enumerate(providers):
        if not isinstance(provider, dict): fail("PROVIDER_CONTRACT", f"providers[{index}] must be an object"); continue
        pid=str(provider.get("id","")).strip().lower(); role=provider.get("role"); state=provider.get("state")
        if not pid or pid in seen_providers: fail("PROVIDER_CONTRACT", f"providers[{index}] has absent/duplicate id"); continue
        seen_providers.add(pid); provider_states[pid]=str(state)
        if pid in FORBIDDEN_PROVIDERS or "code-graph-rag" in pid: fail("NO_CODE_GRAPH_RAG", f"forbidden active provider: {pid}")
        expected_role=ROLE_BY_PROVIDER.get(pid)
        if expected_role and role != expected_role: fail("PROVIDER_ROLE", f"{pid} role must be {expected_role}")
        if state not in ALLOWED_STATES: fail("PROVIDER_STATE", f"{pid or index} state must be EXACT, DEGRADED, or BLOCKED")
        elif state == "EXACT" and pid in {"scip-sqlite","tree-sitter"}: _validate_exact_provider_subject(pid, provider, subject, failures)
    for required_provider in ("scip-sqlite","tree-sitter"):
        if required_provider not in seen_providers: fail("DETERMINISTIC_CONTEXT", f"missing {required_provider} provider declaration")

    branches=_list(contract.get("branches")); branch_names:set[str]=set(); branch_writes:dict[str,list[str]]={}; parent_by_branch:dict[str,str]={}; focuses:set[str]=set()
    if not branches: fail("BRANCHES", "at least one branch is required")
    for index, branch in enumerate(branches):
        if not isinstance(branch, dict): fail("BRANCHES", f"branches[{index}] must be an object"); continue
        name=branch.get("name"); parent=branch.get("parent"); focus=branch.get("focus"); bwrite=_list(branch.get("write"))
        if not isinstance(name,str) or not name or name in branch_names: fail("BRANCHES", f"branches[{index}] has absent/duplicate name"); continue
        branch_names.add(name); parent_by_branch[name]=parent if isinstance(parent,str) else ""; branch_writes[name]=[p for p in bwrite if isinstance(p,str)]
        if not isinstance(parent,str) or not parent: fail("BRANCH_PARENT", f"{name} parent must be non-empty")
        if not isinstance(focus,str) or not focus: fail("BRANCH_FOCUS", f"{name} focus must be non-empty")
        elif mode == "TOURNAMENT" and focus in focuses: fail("BRANCH_FOCUS", f"tournament focus must be unique: {focus}")
        else: focuses.add(str(focus))
        if not bwrite: fail("BRANCH_WRITE", f"{name} write set must be non-empty")
        for pattern in bwrite:
            if not _is_safe_repo_path(pattern): fail("BRANCH_WRITE", f"{name} has unsafe write pattern: {pattern!r}")
    for name in branch_names:
        cursor=name; visited:set[str]=set()
        while cursor in branch_names:
            if cursor in visited: fail("DAG_CYCLE", f"cycle contains branch {cursor}"); break
            visited.add(cursor); cursor=parent_by_branch.get(cursor,"")
    if mode != "TOURNAMENT":
        names=sorted(branch_writes)
        for index,left in enumerate(names):
            for right in names[index+1:]:
                if parent_by_branch.get(right)==left or parent_by_branch.get(left)==right: continue
                for a in branch_writes[left]:
                    for b in branch_writes[right]:
                        ar=a.split("/**",1)[0].rstrip("/"); br=b.split("/**",1)[0].rstrip("/")
                        if ar==br or ar.startswith(br+"/") or br.startswith(ar+"/"): fail("PATH_LEASE_OVERLAP", f"sibling branches {left} and {right} overlap at {ar or br}")

    # ICPG -> Tech Lead ownership gate. This freezes the denominator and prevents
    # a short prompt or local Worker success from silently deleting required cases.
    case_contract = contract.get("case_obligations") if isinstance(contract.get("case_obligations"), dict) else {}
    if not isinstance(case_contract.get("case_graph_ref"), str) or not case_contract.get("case_graph_ref", "").strip(): fail("CASE_GRAPH_BINDING", "case_graph_ref must be non-empty")
    digest=case_contract.get("case_graph_sha256")
    if not isinstance(digest,str) or not SHA256_RE.fullmatch(digest): fail("CASE_GRAPH_BINDING", "case_graph_sha256 must be immutable sha256")
    required_cases=_list(case_contract.get("required_case_ids")); owners=_list(case_contract.get("branch_case_owners")); convergence=case_contract.get("convergence_owner")
    if not required_cases or any(not isinstance(x,str) or not x for x in required_cases) or len(set(required_cases)) != len(required_cases): fail("CASE_DENOMINATOR", "required_case_ids must be non-empty and unique")
    if not isinstance(convergence,str) or convergence not in branch_names: fail("CASE_CONVERGENCE_OWNER", "convergence_owner must name a declared branch")
    observed:list[str]=[]; owner_branches:set[str]=set()
    for index, owner in enumerate(owners):
        if not isinstance(owner,dict): fail("CASE_OWNER", f"branch_case_owners[{index}] must be an object"); continue
        branch=owner.get("branch"); case_ids=_list(owner.get("case_ids"))
        if not isinstance(branch,str) or branch not in branch_names: fail("CASE_OWNER", f"case owner {branch!r} is not a declared branch")
        if branch in owner_branches: fail("CASE_OWNER", f"branch {branch!r} appears more than once in case ownership map")
        owner_branches.add(str(branch))
        if not case_ids or any(not isinstance(x,str) or not x for x in case_ids): fail("CASE_OWNER", f"branch {branch!r} must own non-empty case_ids")
        observed.extend(x for x in case_ids if isinstance(x,str))
    duplicates=sorted({x for x in observed if observed.count(x)>1})
    if duplicates: fail("CASE_DUPLICATE_OWNER", f"required cases have multiple owners: {', '.join(duplicates)}")
    missing_cases=sorted(set(required_cases)-set(observed)); extra_cases=sorted(set(observed)-set(required_cases))
    if missing_cases: fail("CASE_UNOWNED", f"required cases have no owner: {', '.join(missing_cases)}")
    if extra_cases: fail("CASE_UNKNOWN_OWNER", f"ownership map contains cases outside denominator: {', '.join(extra_cases)}")

    acceptance=contract.get("acceptance") if isinstance(contract.get("acceptance"),dict) else {}; commands=_list(acceptance.get("commands")); assertions=_list(acceptance.get("immutable_assertions"))
    if not commands or any(not isinstance(command,list) or not command or any(not isinstance(arg,str) or not arg for arg in command) for command in commands): fail("ACCEPTANCE_COMMANDS", "commands must be non-empty argv arrays")
    if not assertions or any(not isinstance(item,str) or not item for item in assertions): fail("IMMUTABLE_ASSERTIONS", "immutable_assertions must contain stable ids")

    budgets=contract.get("budgets") if isinstance(contract.get("budgets"),dict) else {}; repairs=budgets.get("max_repairs_per_signature"); workers=budgets.get("max_workers")
    if not isinstance(repairs,int) or isinstance(repairs,bool) or not 0<=repairs<=3: