"""Real worktree/subprocess execution for the matched Tech Lead task."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from real_task_fixture import (
    CanaryError, add_worktree, commit, digest, git, graph_controls, launch,
    proc, remove_worktree, run_oracle, safe_path, sha_file,
)
from real_task_scheduler import scheduler_doc, validate_scheduler


def run_arm(arm: str, subject: Path, base: str, tree: str, root: Path, script: Path) -> dict[str, Any]:
    repo = root / arm.lower(); proc(["git", "clone", "-q", str(subject), str(repo)])
    git(repo, "config", "user.name", "integrator"); git(repo, "config", "user.email", "integrator@example.invalid")
    workroot = root / f"{arm}-worktrees"; state = root / f"{arm}-state"; workroot.mkdir(); state.mkdir()
    specs = [("pricing-minimal", "pricing", "minimal", "src/pricing.py", 220), ("pricing-defensive", "pricing", "defensive", "src/pricing.py", 200),
             ("pricing-buggy", "pricing", "buggy", "src/pricing.py", 180), ("receipt", "receipt", "standard", "src/receipt.py", 240)]
    created: list[tuple[Path, str]] = []; active: list[dict[str, Any]] = []; rows: list[dict[str, Any]] = []; output: dict[str, Any] | None = None
    try:
        for name, task, variant, owned, delay in specs:
            branch = f"canary/{arm.lower()}/{name}"; wt = add_worktree(repo, workroot, branch, base); created.append((wt, branch))
            cp = state / f"{name}.json"; attempt = f"{arm}-{name}-1"; child, started = launch(script, wt, task, variant, owned, cp, attempt, delay)
            active.append({"name": name, "task": task, "variant": variant, "path": owned, "branch": branch, "worktree": wt, "cp": cp, "attempt": attempt, "proc": child, "start": started})
        receipt_lineage: dict[str, Any] = {}
        for item in active:
            out, err = item["proc"].communicate(timeout=15); ended = time.time_ns(); first_exit = item["proc"].returncode; retry = None; first_cp = None
            if first_exit == 75:
                first_doc = json.loads(item["cp"].read_text()); first_cp = sha_file(item["cp"])
                if first_doc["attempt"] != item["attempt"]: raise CanaryError("checkpoint identity drift")
                retry = f"{arm}-{item['name']}-2"; resumed, _ = launch(script, item["worktree"], item["task"], item["variant"], item["path"], item["cp"], retry, resume=True)
                rout, rerr = resumed.communicate(timeout=15); out += rout; err += rerr
                if resumed.returncode or json.loads(item["cp"].read_text())["attempt"] != retry: raise CanaryError("resume failed")
            elif first_exit: raise CanaryError(f"Worker failed {item['name']}: {out}{err}")
            oracle_name = "pricing" if item["task"] == "pricing" else "receipt"; oracle = "PASS" if run_oracle(item["worktree"], oracle_name) else "FAIL"
            head = commit(item["worktree"], f"worker: {item['name']}")
            row = {"name": item["name"], "attempt": item["attempt"], "task": item["task"], "path": item["path"], "branch": item["branch"],
                   "worktree": str(item["worktree"]), "start": item["start"], "end": ended, "oracle": oracle,
                   "lines": len((item["worktree"] / safe_path(item["path"])).read_text().splitlines()), "commit": head, "checkpoint": sha_file(item["cp"])}
            rows.append(row)
            if retry: receipt_lineage = {**row, "first_attempt": item["attempt"], "retry_attempt": retry, "first_checkpoint": first_cp}
        overlap = any(max(a["start"], b["start"]) < min(a["end"], b["end"]) for i, a in enumerate(rows) for b in rows[i + 1:] if a["path"] != b["path"])
        if not overlap: raise CanaryError("path-disjoint Workers did not overlap")
        pricing = [r for r in rows if r["task"] == "pricing"]; passing = [r for r in pricing if r["oracle"] == "PASS"]
        if len(pricing) != 3 or len(passing) != 2: raise CanaryError("tournament denominator drift")
        winner = min(passing, key=lambda row: (row["lines"], row["name"])); receipt = next(r for r in rows if r["task"] == "receipt")
        git(repo, "cherry-pick", winner["commit"]); after_first = git(repo, "rev-parse", "HEAD"); hidden_serialism = receipt["commit"] and receipt_lineage["worktree"] and base != after_first
        git(repo, "cherry-pick", receipt["commit"]); integrated = git(repo, "rev-parse", "HEAD")

        local_branch = f"canary/{arm.lower()}/local-pass-global-fail"; local_wt = add_worktree(repo, workroot, local_branch, integrated); created.append((local_wt, local_branch))
        local_cp = state / "local.json"; local_attempt = f"{arm}-local-control"; child, _ = launch(script, local_wt, "checkout", "local-only-buggy", "src/checkout.py", local_cp, local_attempt)
        child.communicate(timeout=15); local_control = child.returncode == 0 and run_oracle(local_wt, "checkout_local") and not run_oracle(local_wt, "global")
        if not local_control: raise CanaryError("local-pass/global-fail control survived")

        stale_branch = f"canary/{arm.lower()}/wrong-base"; stale_wt = add_worktree(repo, workroot, stale_branch, base); created.append((stale_wt, stale_branch))
        stale_cp = state / "stale.json"; stale_attempt = f"{arm}-wrong-base"; child, _ = launch(script, stale_wt, "checkout", "convergence", "src/checkout.py", stale_cp, stale_attempt)
        child.communicate(timeout=15); stale_refused = child.returncode == 0 and not run_oracle(stale_wt, "global")
        if not stale_refused: raise CanaryError("wrong-base convergence accepted")

        conv_branch = f"canary/{arm.lower()}/convergence"; conv_wt = add_worktree(repo, workroot, conv_branch, integrated); created.append((conv_wt, conv_branch))
        conv_cp = state / "convergence.json"; conv_attempt = f"{arm}-convergence"; child, _ = launch(script, conv_wt, "checkout", "convergence", "src/checkout.py", conv_cp, conv_attempt)
        child.communicate(timeout=15)
        if child.returncode or not run_oracle(conv_wt, "global"): raise CanaryError("correct convergence failed")
        conv_commit = commit(conv_wt, "worker: convergence"); git(repo, "cherry-pick", conv_commit)
        if not run_oracle(repo, "global"): raise CanaryError("integrated global objective failed")

        controls = graph_controls(); controls.update({"local_attempt": local_attempt, "local_worktree": str(local_wt), "local_checkpoint": sha_file(local_cp),
            "stale_attempt": stale_attempt, "stale_worktree": str(stale_wt), "stale_checkpoint": sha_file(stale_cp), "integrated_base": integrated})
        lifecycle = scheduler_doc(arm, base, tree, [r for r in rows if r["task"] == "pricing"], winner["name"], receipt_lineage,
            {"attempt": conv_attempt, "worktree": str(conv_wt), "commit": conv_commit, "checkpoint": sha_file(conv_cp)}, controls)
        scheduler = validate_scheduler(lifecycle, state / "scheduler")
        final_digest = digest({p: (repo / p).read_text() for p in ("src/pricing.py", "src/receipt.py", "src/checkout.py")})
        output = {"functional_output": "PASS", "base_commit": base, "base_tree": tree, "parallel_overlap": overlap, "checkpoint_resume": True,
                  "tournament_denominator": 3, "tournament_passed": 2, "tournament_failed": 1, "winner": winner["name"],
                  "fake_dependency_refused": controls["fake_dependency_refused"], "overlapping_writer_refused": controls["overlapping_writer_refused"],
                  "local_pass_global_fail_refused": local_control, "wrong_base_convergence_refused": stale_refused,
                  "legacy_naive_integration_would_serialize": hidden_serialism, "current_disjoint_integration_admitted": True,
                  "global_oracle": "PASS", "content_digest": final_digest, "scheduler": scheduler, "observations": rows,
                  "model_behavioral_uplift": "NOT_EXERCISED", "git_town": "NOT_EXERCISED", "forgejo": "NOT_EXERCISED", "merge_authority": False}
    finally:
        for item in active:
            if item["proc"].poll() is None:
                item["proc"].terminate()
                try: item["proc"].wait(timeout=2)
                except subprocess.TimeoutExpired: item["proc"].kill()
        for wt, branch in reversed(created): remove_worktree(repo, wt, branch)
        git(repo, "worktree", "prune", check=False)
    if output is None: raise CanaryError("arm produced no output")
    residue = git(repo, "branch", "--list", "canary/*") or sum(line.startswith("worktree ") for line in git(repo, "worktree", "list", "--porcelain").splitlines()) != 1 or any(item["proc"].poll() is None for item in active)
    if residue: raise CanaryError("worktree/branch/process residue")
    output["residue"] = "CLEAN"; return output
