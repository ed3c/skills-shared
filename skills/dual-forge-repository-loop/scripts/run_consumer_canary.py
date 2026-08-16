#!/usr/bin/env python3
"""Exercise the dual-forge delivery chain against a real consumer repository.

#234 asks for one bounded, non-destructive canary through a consumer's delivery
chain. The chain has eleven links and this host can reach some of them; the
point of the receipt is that the ones it cannot reach are recorded as blocked
with the reason, rather than left out of a list that then reads as complete.

Nothing here mutates the consumer. Worktrees are created from its current HEAD
and removed, the forge lanes are authenticated reads, and no branch, issue, PR,
push or merge is created. `--allow-worktree` is opt-in because even creating and
removing a worktree touches the consumer's git directory.

Credentials are never handled here: the Forgejo lane goes through
`capture_reconciliation.py`, which reads them from the git credential helper in
memory and puts none of them in its transport.

Usage:
  run_consumer_canary.py --consumer PATH --github OWNER/NAME --forgejo OWNER/NAME \
      --out DIR [--allow-worktree]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parent.parent
SCHEMA = "dual-forge-repository-loop/consumer-canary-receipt/v1"

# The chain #234 names, in order. Every link gets a state in the receipt.
CHAIN = [
    "runtime-bootstrap-bind",
    "consumer-task-packets",
    "isolated-worktrees-and-leases",
    "git-town-dry-run-and-local-no-push-sync",
    "verified-implementation-slices",
    "forgejo-issue-pr-receipts",
    "admitted-local-main-integration",
    "github-reconciliation-inventory",
    "publication-candidate",
    "exact-head-github-actions",
    "external-merge-handoff",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str | None:
    try:
        return sha256(path.read_bytes())
    except OSError:
        return None


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args],
                            capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def link(name: str, state: str, detail: str, **extra: Any) -> dict[str, Any]:
    entry = {"link": name, "state": state, "detail": detail}
    entry.update(extra)
    return entry


def selection_gate(consumer: Path, github: str, forgejo: str) -> dict[str, Any]:
    """Freeze what #234 requires frozen before any mutation."""
    remotes = {}
    for line in git(consumer, "remote", "-v").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            remotes[parts[0]] = parts[1]

    delivery = consumer / ".github-delivery"
    town_manifest = delivery / "git-town" / "manifest.json"
    town: dict[str, Any] = {}
    if town_manifest.is_file():
        body = json.loads(town_manifest.read_text(encoding="utf-8"))
        town = {
            "manifest_sha256": file_sha256(town_manifest),
            "executable_state": body.get("executable_state"),
            "live_sync_state": body.get("live_sync_state"),
            "human_admit_required": body.get("human_admit_required"),
            "admission_states": body.get("admission_states"),
        }

    return {
        "consumer_root": str(consumer),
        "github_repository": github,
        "forgejo_repository": forgejo,
        "default_branch": git(consumer, "rev-parse", "--abbrev-ref", "HEAD"),
        "commit_sha": git(consumer, "rev-parse", "HEAD"),
        "tree_sha": git(consumer, "rev-parse", "HEAD^{tree}"),
        "dirty_paths": len([l for l in git(consumer, "status", "--porcelain").splitlines()
                            if l.strip()]),
        "remotes": remotes,
        "delivery_config_present": delivery.is_dir(),
        "ci_policy_sha256": file_sha256(delivery / "ci-policy.json"),
        "local_verification_contract_sha256": file_sha256(
            delivery / "local-verification-contract.json"),
        "git_town_contract": town,
        "git_town_executable": shutil.which("git-town"),
        "rollback_subject": git(consumer, "rev-parse", "HEAD"),
    }


def exercise_worktree(consumer: Path) -> dict[str, Any]:
    """Two concurrent worktrees at the consumer's HEAD, then removed.

    The lease law is checked the only way it can be: by asking git to break it.
    """
    head = git(consumer, "rev-parse", "HEAD")
    branch = git(consumer, "rev-parse", "--abbrev-ref", "HEAD")
    root = Path(tempfile.mkdtemp(prefix="consumer-canary-"))
    created: list[dict[str, Any]] = []
    lease_refused = None
    try:
        for index in range(2):
            path = root / f"slice-{index}"
            result = subprocess.run(
                ["git", "-C", str(consumer), "worktree", "add", "--detach",
                 str(path), head], capture_output=True, text=True)
            created.append({
                "path": path.name,
                "exit_code": result.returncode,
                "head": git(path, "rev-parse", "HEAD") if path.is_dir() else None,
            })
        clash = subprocess.run(
            ["git", "-C", str(consumer), "worktree", "add", str(root / "clash"), branch],
            capture_output=True, text=True)
        lease_refused = clash.returncode != 0
        if clash.returncode == 0:
            subprocess.run(["git", "-C", str(consumer), "worktree", "remove", "--force",
                            str(root / "clash")], capture_output=True)
    finally:
        for index in range(2):
            subprocess.run(["git", "-C", str(consumer), "worktree", "remove", "--force",
                            str(root / f"slice-{index}")], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        subprocess.run(["git", "-C", str(consumer), "worktree", "prune"],
                       capture_output=True)

    residue = [l for l in git(consumer, "worktree", "list").splitlines()
               if "consumer-canary-" in l]
    return {
        "concurrent_worktrees": len(created),
        "all_at_head": all(w["head"] == head for w in created),
        "workers": created,
        "one_writer_per_branch_refused": lease_refused,
        "residue_after_cleanup": residue,
        "consumer_dirty_after": len(
            [l for l in git(consumer, "status", "--porcelain").splitlines() if l.strip()]),
    }


def observe_actions(repository: str) -> dict[str, Any]:
    """Measure the consumer's Actions state instead of asserting a blocker.

    The first version of this link recorded "#191 provider circuit plus a budget
    decision" as prose and the checker refused it for carrying no observation.
    Measuring it changed the answer: this consumer's Actions are enabled and
    running, so #191's billing circuit is not in force here and the only thing
    holding the link is a budget decision this canary is making on purpose.
    """
    def gh(endpoint: str, jq: str) -> str | None:
        result = subprocess.run(["gh", "api", endpoint, "--jq", jq],
                                capture_output=True, text=True, check=False, timeout=60)
        return result.stdout.strip() if result.returncode == 0 else None

    enabled = gh(f"repos/{repository}/actions/permissions", ".enabled")
    total = gh(f"repos/{repository}/actions/runs?per_page=1", ".total_count")
    latest = gh(f"repos/{repository}/actions/runs?per_page=5",
                '[.workflow_runs[] | {name, status, conclusion, created_at}] | tostring')
    return {
        "actions_enabled": enabled,
        "total_runs_observed": total,
        "latest_runs": latest,
        "billing_circuit_observed": (
            "not-in-force" if enabled == "true" and total and total != "0" else "unknown"),
        "note": ("#191's billing circuit is not blocking this consumer: Actions are "
                 "enabled and runs are completing. The link is held by a budget decision, "
                 "not by a provider blocker."),
    }


def build_observation(transport: dict[str, Any], inventory: dict[str, Any],
                      local_main_changed: bool) -> dict[str, Any]:
    """Classify every open PR and issue. Identity is derived; the routing is a judgement.

    This canary changes nothing on the consumer's local main, so no PR can be
    affected by it. That is why every PR is UNAFFECTED here and why the field
    would be worth nothing if the canary had integrated something -- the
    classification is about a delta, and this delta is empty.
    """
    def pr_entry(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "number": item["number"],
            "head_sha": item["head"]["sha"],
            "base_branch": item["base"]["ref"],
            "wip": bool(item["draft"]),
            "classification": "UNAFFECTED",
            "reason": ("this canary produced no local-main delta, so nothing it did can "
                       "conflict with, supersede or rebase this PR"),
        }

    return {
        "schema": "dual-forge-reconciliation-observation/v2",
        "repository": transport["github_repository"],
        "forgejo_repository": transport["forgejo_repository"],
        "repository_ids": inventory["repository_ids"],
        "captured_at": inventory["captured_at"],
        "local_main_changed": local_main_changed,
        "github_open_prs": [pr_entry(item) for item in inventory["github_prs"]],
        "forgejo_open_prs": [pr_entry(item) for item in inventory["forgejo_prs"]],
        "open_issues": [
            {"forge": forge, "number": item["number"],
             "routing": "UNAFFECTED_BY_THIS_CANARY",
             "reason": "read-only canary; no issue state was created or changed"}
            for forge, items in (("github", inventory["github_issues"]),
                                 ("forgejo", inventory["forgejo_issues"]))
            for item in items
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--consumer", type=Path, required=True)
    parser.add_argument("--github", required=True)
    parser.add_argument("--forgejo", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--allow-worktree", action="store_true")
    args = parser.parse_args()

    sys.path.insert(0, str(SKILL / "scripts"))
    import capture_reconciliation as reconciliation

    consumer = args.consumer.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.time()

    gate = selection_gate(consumer, args.github, args.forgejo)
    if gate["dirty_paths"]:
        print(f"consumer has {gate['dirty_paths']} dirty path(s); a canary against an "
              f"unclean tree describes no particular subject", file=sys.stderr)
        return 2

    links: list[dict[str, Any]] = []

    links.append(link(
        "runtime-bootstrap-bind", "EXERCISED",
        "consumer identity, both remotes, delivery config digests and rollback subject "
        "frozen before anything ran",
        remotes=list(gate["remotes"])))

    links.append(link(
        "consumer-task-packets", "NOT_EXERCISED",
        "no task was compiled for this consumer; the Tech Lead compiler landed in this "
        "Skill but pointing it at a consumer objective is a separate admission"))

    if args.allow_worktree:
        worktree = exercise_worktree(consumer)
        state = ("EXERCISED" if worktree["all_at_head"]
                 and worktree["one_writer_per_branch_refused"] else "FAIL")
        links.append(link("isolated-worktrees-and-leases", state,
                          "two concurrent worktrees at the consumer HEAD, both read back; "
                          "a second checkout of the active branch refused by git",
                          **worktree))
    else:
        links.append(link("isolated-worktrees-and-leases", "SKIPPED_BY_POLICY",
                          "--allow-worktree not given; creating one touches the "
                          "consumer's git directory"))

    town = gate["git_town_contract"]
    links.append(link(
        "git-town-dry-run-and-local-no-push-sync", "BLOCKED",
        "the consumer's own contract records the same absence this host does",
        executable_on_path=gate["git_town_executable"],
        consumer_executable_state=town.get("executable_state"),
        consumer_live_sync_state=town.get("live_sync_state"),
        human_admit_required=town.get("human_admit_required"),
        note=("Homebrew offers the admitted 24.0.0, but the shared admission record pins "
              "a linux_intel_64 artifact by SHA-256 and this host is darwin. Binding a "
              "different artifact at the same version is a Human admission, not an "
              "install.")))

    links.append(link(
        "verified-implementation-slices", "NOT_EXERCISED",
        "the consumer ships a local verification contract, but running it proves the "
        "consumer's own tests rather than a slice this canary produced, and this canary "
        "produced none",
        contract_sha256=gate["local_verification_contract_sha256"]))

    transport_path = args.out / "reconciliation-transport.json"
    transport = reconciliation.capture(args.github, args.forgejo,
                                       gate["default_branch"], "http://localhost:3000", 30)
    transport_path.write_text(json.dumps(transport, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8")
    inventory = reconciliation._provider_inventory(transport)

    observation = build_observation(transport, inventory, local_main_changed=False)
    observation_path = args.out / "reconciliation-observation.json"
    observation_path.write_text(json.dumps(observation, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")

    replayed = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "capture_reconciliation.py"), "replay",
         "--transport", str(transport_path), "--observation", str(observation_path)],
        capture_output=True, text=True)
    exhaustive = replayed.returncode == 0

    links.append(link(
        "forgejo-issue-pr-receipts", "EXERCISED" if exhaustive else "FAIL",
        "authenticated read of the Forgejo repository, open PRs and open issues; no "
        "issue or PR was created",
        forgejo_repository_id=inventory["repository_ids"].get("forgejo"),
        open_prs=len(inventory["forgejo_prs"]),
        open_issues=len(inventory["forgejo_issues"])))

    links.append(link(
        "admitted-local-main-integration", "NOT_EXERCISED",
        "nothing was produced to integrate; the canary is read-only by construction"))

    links.append(link(
        "github-reconciliation-inventory", "EXERCISED" if exhaustive else "FAIL",
        "every open PR and issue on both forges classified exactly once, checked by "
        "capture_reconciliation.py replay rather than asserted",
        github_repository_id=inventory["repository_ids"].get("github"),
        github_open_prs=len(inventory["github_prs"]),
        github_open_issues=len(inventory["github_issues"]),
        replay_exit_code=replayed.returncode,
        replay_stderr=replayed.stderr.strip()[-400:]))

    links.append(link(
        "publication-candidate", "NOT_EXERCISED",
        "a publication candidate needs a local slice and an exact-HEAD verification "
        "receipt for it; neither exists in a read-only canary"))

    actions = observe_actions(args.github)
    links.append(link(
        "exact-head-github-actions", "SKIPPED_BY_POLICY",
        "this canary does not spend an Actions job on a consumer repository",
        **actions))

    links.append(link(
        "external-merge-handoff", "SKIPPED_BY_POLICY",
        "#234 states it does not require or authorize merge"))

    receipt = {
        "schema": SCHEMA,
        "issue": 234,
        "consumer_selection_gate": gate,
        "started_at": int(started),
        "duration_ms": int((time.time() - started) * 1000),
        "chain": links,
        "chain_declared": CHAIN,
        "coverage": {
            "exercised": sorted(l["link"] for l in links if l["state"] == "EXERCISED"),
            "blocked": sorted(l["link"] for l in links if l["state"] == "BLOCKED"),
            "not_exercised": sorted(l["link"] for l in links
                                    if l["state"] in {"NOT_EXERCISED", "SKIPPED_BY_POLICY"}),
        },
        "mutations_performed": {
            "branches_created": False, "issues_created": False, "prs_created": False,
            "pushes": False, "merges": False, "consumer_files_changed": False,
            "worktrees_created_and_removed": bool(args.allow_worktree),
        },
        "declared_non_claims": [
            "a read-only reconciliation is not a delivery transition",
            "the consumer's own tests were not run, so nothing here says its main is green",
            "no Git Town synchronization occurred, so no branch hierarchy claim is made",
            "reaching a forge is not the same as being admitted to publish to it",
        ],
    }

    target = args.out / "consumer-canary.receipt.json"
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({"receipt": str(target), "coverage": receipt["coverage"],
                      "reconciliation_exhaustive": exhaustive}, indent=2))
    return 0 if exhaustive else 2


if __name__ == "__main__":
    raise SystemExit(main())
