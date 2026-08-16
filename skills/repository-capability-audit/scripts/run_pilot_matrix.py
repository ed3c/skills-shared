#!/usr/bin/env python3
"""Drive the frozen pilot matrix: real hosts, real arms, one repetition.

Exit codes:
  0   every cell completed and was scored
  2   at least one cell failed; failures stay in the denominator with a reason
  64  the preregistration, corpus, or a host binary is absent

Each arm starts in a fresh session and an empty workspace, receives only its own
treatment, and is scored by an evaluator it cannot see. Arm order is derived from
the cell identity rather than chosen at run time, so it is reproducible and
recorded. There are no retries: the preregistration forbids them, so a failed
cell is reported rather than repeated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SKILL = Path(__file__).resolve().parents[1]
PREREG = SKILL / "evals" / "pilot-preregistration.json"
CORPUS = SKILL / "evals" / "held-out-corpus.json"
RESOLVER = SKILL / "scripts" / "resolve_holdout_ground_truth.py"
EVALUATOR = SKILL / "scripts" / "pilot_evaluator.py"

INVALID = 64
CELL_FAILURE = 2

SOURCE_SKILLS = [
    "controlled-technical-language-harness",
    "external-verify",
    "github-delivery-loop",
    "judge-loop-chooser",
    "knowledge-continuity",
    "spatial-loop-systems-engineering",
]

OUTPUT_SHAPE = (
    'Write your findings to agent-output.json in the current working directory, '
    'with exactly this shape: {"tree_sha": "<the tree sha you were given>", '
    '"evidence_paths": ["<repository-relative paths you actually resolved>"], '
    '"claims": ["<what the tree supports>"], "non_claims": ["<what it does not>"], '
    '"escalate": <true if this subject warrants a runtime capability audit, false if it does not>}'
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def portable(text: str) -> str:
    text = text.replace(str(Path.home()), "<HOME>")
    return re.sub(r"/(?:private/)?(?:var/folders|tmp)/[A-Za-z0-9._/+-]*", "<TMPDIR>", text)


def treatment_text(arm: str) -> str:
    if arm == "no_skill":
        return ""
    body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if arm == "candidate_trimmed_skill":
        return body
    parts = [body]
    for name in SOURCE_SKILLS:
        path = ROOT / "skills" / name / "SKILL.md"
        if path.is_file():
            parts.append(f"\n\n===== {name} =====\n\n" + path.read_text(encoding="utf-8"))
    return "".join(parts)


def arm_order(repository_id: str, host: str, arms: list[str]) -> list[str]:
    seed = int(sha256_text(f"{repository_id}|{host}")[:8], 16)
    return [arms[(seed + index) % len(arms)] for index in range(len(arms))]


def run_host(host: str, model: str, prompt: str, workspace: Path, timeout: int) -> dict[str, Any]:
    if host == "claude-code":
        argv = ["claude", "-p", prompt, "--allowedTools", "Bash,Read,Write,Glob,Grep",
                "--model", model, "--output-format", "json"]
    else:
        # A cell workspace is a fresh empty directory, and this host refuses to run
        # outside a git repository. Without this flag it exits before reaching the
        # model, which scores as a zero the arm never earned.
        argv = ["codex", "exec", "-m", model, "--sandbox", "workspace-write",
                "--skip-git-repo-check", "--json", prompt]
    started = time.time()
    process = subprocess.run(
        # Both CLIs read stdin when it is not closed; inheriting this process's
        # stdin made the first smoke cell exit 1 in 539ms without ever reaching
        # the model.
        argv, cwd=workspace, capture_output=True, text=True, check=False,
        timeout=timeout, stdin=subprocess.DEVNULL,
    )
    duration_ms = int((time.time() - started) * 1000)
    usage = {"tool_calls": 0, "input_tokens": 0, "output_tokens": 0,
             "duration_ms": duration_ms, "cost_usd": 0.0, "cost_observed": False}
    if host == "claude-code":
        try:
            payload = json.loads(process.stdout)
            u = payload.get("usage", {})
            usage.update({
                "tool_calls": int(payload.get("num_turns", 0)),
                "input_tokens": int(u.get("input_tokens", 0)) + int(u.get("cache_read_input_tokens", 0)),
                "output_tokens": int(u.get("output_tokens", 0)),
                "cost_usd": float(payload.get("total_cost_usd", 0.0)),
                "cost_observed": True,
            })
        except Exception:
            pass
    else:
        for line in process.stdout.splitlines():
            try:
                event = json.loads(line)
            except Exception:
                continue
            if event.get("type") == "turn.completed":
                u = event.get("usage", {})
                usage.update({
                    "input_tokens": int(u.get("input_tokens", 0)),
                    "output_tokens": int(u.get("output_tokens", 0)),
                })
    return {"exit_code": process.returncode, "usage": usage,
            "stdout": portable(process.stdout)[-4000:], "stderr": portable(process.stderr)[-4000:]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--limit", type=int, default=0, help="stop after N cells (smoke use only)")
    parser.add_argument(
        "--only-host",
        help="run one host family. For re-running cells that never reached a model "
             "because of a harness defect; not for retrying a cell that did.",
    )
    parser.add_argument(
        "--repetitions", type=int, default=0,
        help="override the preregistered repetition count. The pilot froze 1; #228's "
             "own matrix specifies 5. Passing this makes the run a different frozen "
             "design, and the result records which.",
    )
    args = parser.parse_args()

    for required in (PREREG, CORPUS, RESOLVER, EVALUATOR):
        if not required.is_file():
            print(f"PILOT-INVALID absent-input: {required}", file=sys.stderr)
            return INVALID

    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    arms = sorted(prereg["arms"])
    hosts = prereg["hosts"]
    for host in hosts:
        if shutil.which("claude" if host["family"] == "claude-code" else "codex") is None:
            print(f"PILOT-INVALID absent-binary for {host['family']}", file=sys.stderr)
            return INVALID

    # One family per repository, chosen deterministically: the pilot runs three
    # repositories, not three families, and mixing both would confound them.
    by_repo: dict[str, dict[str, Any]] = {}
    for family in corpus["task_families"]:
        by_repo.setdefault(family["repository_id"], family)
    repositories = {r["repository_id"]: r for r in corpus["repositories"]}

    repetitions = args.repetitions or prereg["matrix"]["repetitions"]
    active_hosts = [h for h in hosts if not args.only_host or h["family"] == args.only_host]
    total_cells = len(by_repo) * len(active_hosts) * repetitions * len(arms)

    args.output.mkdir(parents=True, exist_ok=True)
    cells: list[dict[str, Any]] = []
    failures = 0
    count = 0

    for repository_id, family in sorted(by_repo.items()):
        repo = repositories[repository_id]
        resolved = subprocess.run(
            [sys.executable, str(RESOLVER), "--repository", repository_id,
             "--tree-sha", repo["tree_sha"], "--family", family["family_id"],
             "--emit", "ground-truth"],
            capture_output=True, text=True, check=False, timeout=300,
        )
        if resolved.returncode != 0:
            print(f"PILOT-INVALID unresolved-ground-truth: {repository_id}", file=sys.stderr)
            return INVALID
        truth = json.loads(resolved.stdout)[0]
        truth_path = args.output / f"ground-truth-{repository_id.replace('/', '_')}.json"
        truth_path.write_text(json.dumps(truth, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        for host in hosts:
            if args.only_host and host["family"] != args.only_host:
                continue
            for repetition in range(1, repetitions + 1):
              for arm in arm_order(repository_id, host["family"], arms):
                if args.limit and count >= args.limit:
                    break
                count += 1
                cell_id = (f"{repository_id.replace('/', '_')}__{host['family']}"
                           f"__{arm}__rep{repetition}")
                workspace = args.output / "cells" / cell_id
                if workspace.exists():
                    shutil.rmtree(workspace)
                workspace.mkdir(parents=True)

                treatment = treatment_text(arm)
                task = (
                    f"Audit this pinned repository subject and report only what its tree supports.\n"
                    f"repository: {repository_id}\ntree_sha: {repo['tree_sha']}\n"
                    f"question: {truth['asks']}\n\n"
                    f"You may inspect the repository through the GitHub API, for example:\n"
                    f"  gh api /repos/{repository_id}/git/trees/{repo['tree_sha']}?recursive=1\n\n"
                    f"{OUTPUT_SHAPE}\n"
                    f"Cite only paths you actually resolved. Do not invent paths."
                )
                # The leading prose is not decoration: a Skill body starts with
                # YAML frontmatter, so a prompt beginning `---` is parsed as a
                # flag and the CLI exits in ~150ms without reaching the model.
                prompt = (
                    "You are given the following Skill text as your working method.\n\n"
                    f"===== SKILL =====\n\n{treatment}\n\n===== TASK =====\n\n{task}"
                    if treatment else task
                )

                result = run_host(host["family"], host["model"], prompt, workspace, args.timeout)
                usage_path = workspace / ".usage.json"
                usage_path.write_text(json.dumps(result["usage"], indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")
                metrics_path = workspace / "agent-eval-metrics.json"
                evaluated = subprocess.run(
                    [sys.executable, str(EVALUATOR), "--ground-truth", str(truth_path),
                     "--usage", str(usage_path), "--metrics-file", str(metrics_path),
                     "--workspace", str(workspace)],
                    capture_output=True, text=True, check=False, timeout=120,
                )
                ok = evaluated.returncode == 0 and metrics_path.is_file()
                metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if ok else None
                if not ok:
                    failures += 1
                cells.append({
                    "cell_id": cell_id,
                    "repository_id": repository_id,
                    "family_id": family["family_id"],
                    "host_family": host["family"],
                    "model": host["model"],
                    "arm": arm,
                    "repetition": repetition,
                    "host_exit_code": result["exit_code"],
                    "scored": ok,
                    "failure_reason": None if ok else portable(evaluated.stderr)[-400:],
                    "metrics": metrics,
                    "treatment_sha256": sha256_text(treatment),
                    "treatment_bytes": len(treatment.encode("utf-8")),
                })
                print(f"cell {count}/{total_cells} {cell_id} scored={ok} "
                      f"found={metrics['material_defects_found'] if metrics else '-'}")

    report = {
        "schema": "rca-pilot-result/v1",
        "preregistration_id": prereg["preregistration_id"],
        "status": "PILOT" if repetitions == 1 else "MATRIX",
        "repetitions": repetitions,
        "corpus_id": corpus["corpus_id"],
        "cells": cells,
        "cell_count": len(cells),
        "failed_cells": failures,
        "non_claims": prereg["declared_non_claims"],
    }
    (args.output / "pilot-result.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"PILOT COMPLETE cells={len(cells)} failed={failures}")
    return 0 if failures == 0 else CELL_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
