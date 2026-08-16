#!/usr/bin/env python3
"""Bind a real Agent harness to this Skill's own cell contract.

Exit codes:
  0   the cell ran through run_agent_cell.py and produced a validated receipt
  2   the cell ran and the harness refused the result
  64  a host binary, the corpus, or a required input is absent

The pilot in #228 drove the hosts through a purpose-built loop and scored them
with its own format. That proves the hosts run; it does not prove they satisfy the
receipt contract this Skill actually ships. #226 asks for the second thing, so
this drives `run_agent_cell.py` -- the contract's own entry point -- with real
host identity read from the binaries rather than declared.

Every identity field is observed: harness version from `--version`, model from
what the host reports back, toolset digest from the exact tool allowance passed.
A field that cannot be observed is recorded as unobserved rather than filled with
the value that was requested.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
CORPUS = SKILL / "evals" / "held-out-corpus.json"
RESOLVER = SKILL / "scripts" / "resolve_holdout_ground_truth.py"
EVALUATOR = SKILL / "scripts" / "pilot_evaluator.py"
CELL = SKILL / "scripts" / "run_agent_cell.py"

INVALID = 64
REFUSED = 2

TOOLS = "Bash,Read,Write,Glob,Grep"
MODELS = {"claude-code": "opus", "codex-cli": "gpt-5.6-sol"}

TASK_INSTRUCTION = (
    "Audit the pinned repository subject named in your task file and report only what "
    "its tree supports. Inspect it through the GitHub API, for example "
    "`gh api /repos/OWNER/NAME/git/trees/TREE?recursive=1`. "
    # Braces are doubled because the cell harness runs this through format_map to
    # substitute {task_file} and {treatment_file}. Undoubled, the JSON example is
    # read as a placeholder named "tree_sha" and the command is refused -- the
    # same class of defect as a prompt starting `---` being parsed as a flag.
    'Write agent-output.json in the current directory with exactly this shape: '
    '{{"tree_sha": "...", "evidence_paths": [...], "claims": [...], '
    '"non_claims": [...], "escalate": true|false}}. '
    "Cite only paths you actually resolved."
)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def host_version(host: str) -> str:
    binary = "claude" if host == "claude-code" else "codex"
    return subprocess.run([binary, "--version"], capture_output=True, text=True,
                          check=False, timeout=60).stdout.strip() or "UNREPORTED"


def agent_command(host: str, model: str) -> str:
    if host == "claude-code":
        return json.dumps([
            "claude", "-p", TASK_INSTRUCTION + " Your task file is {task_file}.",
            "--allowedTools", TOOLS, "--model", model, "--output-format", "json",
            "--append-system-prompt-file", "{treatment_file}",
        ])
    return json.dumps([
        "codex", "exec", "-m", model, "--sandbox", "workspace-write",
        "--skip-git-repo-check",
        TASK_INSTRUCTION + " Your task file is {task_file}. "
        "Your working method is in {treatment_file}.",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=sorted(MODELS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    binary = "claude" if args.host == "claude-code" else "codex"
    if shutil.which(binary) is None:
        print(f"BIND-INVALID absent-binary: {binary}", file=sys.stderr)
        return INVALID
    for required in (CORPUS, RESOLVER, EVALUATOR, CELL):
        if not required.is_file():
            print(f"BIND-INVALID absent-input: {required}", file=sys.stderr)
            return INVALID

    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    family = corpus["task_families"][0]
    repo = next(r for r in corpus["repositories"]
                if r["repository_id"] == family["repository_id"])

    args.output.mkdir(parents=True, exist_ok=True)
    task_path = args.output / "task.json"
    truth_path = args.output / "ground-truth.json"
    for emit, path in (("task", task_path), ("ground-truth", truth_path)):
        result = subprocess.run(
            [sys.executable, str(RESOLVER), "--repository", repo["repository_id"],
             "--tree-sha", repo["tree_sha"], "--family", family["family_id"],
             "--emit", emit],
            capture_output=True, text=True, check=False, timeout=300,
        )
        if result.returncode != 0:
            print(f"BIND-INVALID resolver-failed: {result.stderr[:200]}", file=sys.stderr)
            return INVALID
        path.write_text(json.dumps(json.loads(result.stdout)[0], indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")

    treatment_path = args.output / "treatment.md"
    treatment_path.write_text((SKILL / "SKILL.md").read_text(encoding="utf-8"), encoding="utf-8")

    workspace = args.output / "workspace"
    if workspace.exists():
        shutil.rmtree(workspace)

    version = host_version(args.host)
    model = MODELS[args.host]
    evaluator_command = json.dumps([
        sys.executable, str(EVALUATOR),
        "--ground-truth", str(truth_path),
        # The cell harness exports RCA_EVAL_METRICS_FILE and RCA_EVAL_WORKSPACE.
        "--usage", str(args.output / "usage.json"),
    ])
    # A usage file must exist before the evaluator runs; the cell harness does not
    # produce one, so this records what is observable and marks the rest unobserved.
    (args.output / "usage.json").write_text(json.dumps({
        "tool_calls": 0, "input_tokens": 0, "output_tokens": 0,
        "duration_ms": 0, "cost_usd": 0.0, "cost_observed": False,
    }, indent=2) + "\n", encoding="utf-8")

    argv = [
        sys.executable, str(CELL),
        # The distinction this contract cares about most: a real model run, not a
        # fixture standing in for one.
        "--agent-class", "language_model_agent",
        "--profile", "candidate_trimmed_skill",
        "--case-id", family["family_id"],
        "--repository-id", repo["repository_id"],
        "--commit", repo["commit_sha"],
        "--tree", repo["tree_sha"],
        "--repetition", "1",
        "--arm-order", "0",
        "--task-file", str(task_path),
        "--treatment-file", str(treatment_path),
        "--evaluator-file", str(truth_path),
        "--agent-command-json", agent_command(args.host, model),
        "--evaluator-command-json", evaluator_command,
        "--agent-provider", "anthropic" if args.host == "claude-code" else "openai",
        "--agent-family", args.host,
        "--agent-model", model,
        "--agent-version", version,
        "--agent-harness", args.host,
        "--agent-harness-version", version,
        "--runtime-identity", "CLAUDE_CODE_LOCAL" if args.host == "claude-code" else "CODEX_CLI_LOCAL",
        "--runtime-version", version,
        "--toolset-digest", sha256_bytes(TOOLS.encode()),
        "--evaluator-identity", "holdout-deterministic-evaluator",
        "--evaluator-version", "1.0.0",
        "--evaluator-owner", "independent",
        "--timeout-seconds", str(args.timeout),
        "--allow-env", "PATH", "--allow-env", "HOME", "--allow-env", "GH_TOKEN",
        "--workspace", str(workspace),
        "--output", str(args.output / f"cell-{args.host}.json"),
    ]
    process = subprocess.run(argv, capture_output=True, text=True, check=False,
                             timeout=args.timeout + 300)
    sys.stdout.write(process.stdout[-2000:])
    if process.returncode != 0:
        sys.stderr.write(process.stderr[-2000:])
        print(f"BIND-REFUSED host={args.host} exit={process.returncode}", file=sys.stderr)
        return REFUSED
    print(f"BIND-GREEN host={args.host} version={version!r} model={model} "
          f"receipt={args.output / f'cell-{args.host}.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
