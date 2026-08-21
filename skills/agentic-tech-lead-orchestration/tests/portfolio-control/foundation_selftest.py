#!/usr/bin/env python3
"""Hermetic C0 proof for repository portfolio control."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
REFERENCES = ROOT / "references"
CONTRACTS = REFERENCES / "contracts"
AGENTS = REFERENCES / "codex-agents"
PROMPT = REFERENCES / "prompts/repository-portfolio-controller-v3.md"
sys.path.insert(0, str(SCRIPTS))

from compile_repository_portfolio import compile_graph  # noqa: E402
from portfolio_control_lib import bind_digest  # noqa: E402
from assert_portfolio_multigraph import verify as verify_multigraph  # noqa: E402

BARRIER = "Use subagents. Wait for all agents and consolidate their findings."
SCHEMAS = [
    "repository-portfolio-snapshot.schema.json",
    "issue-pr-acceptance.schema.json",
    "portfolio-multigraph.schema.json",
    "subagent-dispatch.schema.json",
    "subagent-result.schema.json",
    "subagent-join-receipt.schema.json",
    "one-shot-ci-epoch.schema.json",
]
ROLES = [
    "portfolio-explorer",
    "acceptance-adversary",
    "dependency-auditor",
    "runtime-admission-auditor",
    "implementation-worker",
    "consolidation-verifier",
    "release-auditor",
]


def run(*argv: str) -> None:
    subprocess.run(argv, check=True, cwd=ROOT)


def acceptance(unit_id: str, number: int, path: str, *, parent: dict | None = None) -> dict:
    dependency = [] if parent is None else [{
        "unit_id": parent["unit_id"],
        "subject_digest": parent["digest"],
        "reason": "TRUE_CHILD: consumes exact unmerged parent contract bytes",
    }]
    packet = {
        "schema": "issue-pr-acceptance/v1",
        "unit_id": unit_id,
        "kind": "ISSUE",
        "repository": "ed3c/skills-shared",
        "number": number,
        "objective": f"Prove {unit_id}",
        "non_goals": ["merge, release and production"],
        "subjects": {"base_commit": "1" * 40, "base_tree": "2" * 40},
        "start_dependencies": dependency,
        "completion_dependencies": dependency,
        "leases": {"exclusive": [path], "read_only": ["AGENTS.md"], "forbidden": ["secrets/**"]},
        "prerequisites": [{"id": "runtime", "state": "PASS", "owner": "test", "unblock_condition": "already admitted"}],
        "oracles": ["deterministic checker exits zero"],
        "negative_controls": ["stale subject turns red"],
        "evidence_lanes": ["DETERMINISTIC"],
        "evidence_ceiling": "fixture-only deterministic mechanics",
        "rollback_subject": "3" * 40,
        "allowed_terminals": ["READY", "BLOCKED", "REJECTED"],
        "human_operations": ["merge"],
        "residual_owner": "issue-560",
    }
    return bind_digest(packet)


def main() -> int:
    for name in SCHEMAS:
        schema = json.loads((CONTRACTS / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        print(f"SCHEMA-GREEN {name}")

    prompt_text = PROMPT.read_text(encoding="utf-8")
    assert BARRIER in prompt_text
    assert "G1 start-dependency DAG" in prompt_text
    assert "ONE_SHOT_CI_EPOCH" in prompt_text
    assert "private chain of thought" in prompt_text

    for role in ROLES:
        path = AGENTS / f"{role}.toml.template"
        packet = tomllib.loads(path.read_text(encoding="utf-8"))
        assert packet["name"] == role
        assert packet["coordinator_barrier"] == BARRIER
        assert BARRIER in packet["developer_instructions"]
        if role == "implementation-worker":
            assert packet["sandbox_mode"] == "workspace-write"
        else:
            assert packet["sandbox_mode"] == "read-only"
        print(f"CODEX-AGENT-GREEN {role}")

    run(sys.executable, "-m", "py_compile", *[str(path) for path in sorted(SCRIPTS.glob("*portfolio*.py"))], str(SCRIPTS / "assert_subagent_dispatch.py"), str(SCRIPTS / "assert_subagent_join.py"), str(SCRIPTS / "assert_one_shot_ci_epoch.py"))
    run(sys.executable, str(SCRIPTS / "assert_portfolio_multigraph.py"), "--selftest")
    run(sys.executable, str(SCRIPTS / "assert_subagent_dispatch.py"), "--selftest")
    run(sys.executable, str(SCRIPTS / "assert_subagent_join.py"), "--selftest")
    run(sys.executable, str(SCRIPTS / "assert_one_shot_ci_epoch.py"), "--selftest")

    snapshot = bind_digest({
        "schema": "repository-portfolio-snapshot/v1",
        "epoch_id": "fixture-epoch",
        "observed_at": "2026-08-21T00:00:00Z",
        "runtime": {"class": "CODEX_CLI_LOCAL", "host": "fixture", "local_checkout": "PASS", "authority_ceiling": "deterministic fixture"},
        "repositories": [{
            "full_name": "ed3c/skills-shared",
            "visibility": "PUBLIC",
            "default_branch": "main",
            "main_commit": "1" * 40,
            "main_tree": "2" * 40,
            "issues": [],
            "pull_requests": [],
            "workflows": [],
            "path_writers": [],
        }],
    })
    contract = acceptance("C0-CONTRACT", 560, "references/contracts/**")
    implementation = acceptance("C0-IMPLEMENTATION", 561, "scripts/**", parent=contract)
    graph = compile_graph(snapshot, [contract, implementation])
    verify_multigraph(graph, json.loads((CONTRACTS / "portfolio-multigraph.schema.json").read_text(encoding="utf-8")))
    assert graph["ready_waves"] == [["C0-CONTRACT"], ["C0-IMPLEMENTATION"]]
    assert graph["graphs"]["G3"][0]["relation"] == "TRUE_CHILD"

    conflict_a = acceptance("CONFLICT-A", 562, "UNKNOWN")
    conflict_b = acceptance("CONFLICT-B", 563, "src/**")
    conflict_graph = compile_graph(snapshot, [conflict_a, conflict_b])
    verify_multigraph(conflict_graph, json.loads((CONTRACTS / "portfolio-multigraph.schema.json").read_text(encoding="utf-8")))
    assert conflict_graph["graphs"]["G4"], conflict_graph
    assert conflict_graph["ready_waves"] == [["CONFLICT-A"], ["CONFLICT-B"]]

    tracked_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [PROMPT, REFERENCES / "REPOSITORY_PORTFOLIO_CONTROL.md", *sorted(AGENTS.glob("*.toml.template"))]
    )
    for forbidden in ("/Users/neon", "private-repo.example", "BEGIN PRIVATE KEY", "ghp_"):
        assert forbidden not in tracked_text, forbidden

    print("REPOSITORY-PORTFOLIO-C0-GREEN schemas=7 agents=7 graph_mutations=6 dispatch_mutations=6 join_mutations=6 ci_mutations=6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
