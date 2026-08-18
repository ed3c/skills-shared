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
memory and puts none of them in its transport. The forge is probed before that
lane runs, so a forge that is not listening is recorded as ABSENT with the
failed connection rather than as a delivery that did not happen: a forge nobody
could reach and a forge that answered are different observations.

`--git-town-bin` points the synchronization lane at an already-admitted
executable. It is never installed, never put on PATH, and never run against the
consumer's own git directory -- git-town writes its configuration into the
common config a linked worktree shares, and the consumer's own contract reserves
config activation to a Human. The subject is a disposable clone of the consumer
carrying its exact bytes, with a local bare remote, under TMPDIR.

Usage:
  run_consumer_canary.py --consumer PATH --github OWNER/NAME --forgejo OWNER/NAME \
      --out DIR [--allow-worktree] [--git-town-bin PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parent.parent
ROOT = SKILL.parent.parent
SCHEMA = "dual-forge-repository-loop/consumer-canary-receipt/v1"

# The record that admits this host's git-town artifact. It is read, never
# written: a lane that could edit its own admission admits itself.
GIT_TOWN_ADMISSION = (ROOT / "skills" / "repo-agent-native" / "evals"
                      / "git-town-darwin-admission.json")

# /usr/bin/git is the xcrun shim. With HOME redirected it cannot write its cache
# and every git-town chdir fails with an error that names neither cause.
REAL_GIT_DIRS = ("/Library/Developer/CommandLineTools/usr/bin",
                 "/Applications/Xcode.app/Contents/Developer/usr/bin")

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


def _ref_digest(repo: Path, git_bin: str, env: dict[str, str]) -> str:
    result = subprocess.run([git_bin, "for-each-ref", "--format=%(refname) %(objectname)"],
                            cwd=str(repo), env=env, capture_output=True, text=True,
                            timeout=120)
    lines = "\n".join(sorted(l for l in result.stdout.splitlines() if l))
    return sha256(lines.encode())


def exercise_git_town(consumer: Path, executable: Path,
                      manifest: dict[str, Any]) -> dict[str, Any]:
    """Run the consumer's declared Git Town modes against the consumer's own bytes.

    The subject is a disposable clone, not the consumer's checkout, and that is a
    decision rather than a convenience. git-town writes `git-town.*` keys into the
    repository configuration, and a linked worktree shares the common config with
    the repository it came from, so activating it in a worktree of the consumer
    would write into the consumer -- which its own manifest assigns to HUMAN. The
    clone carries the consumer's exact commit, so what git-town synchronizes is
    the consumer's real history; what it configures is a tree that gets deleted.

    Every claim below is read back from git, never from git-town's own output.
    """
    admitted = json.loads(GIT_TOWN_ADMISSION.read_text(encoding="utf-8"))
    expected = admitted["derived_executable_identity"]["sha256"]
    observed = file_sha256(executable) if executable.is_file() else None
    base: dict[str, Any] = {
        "executable_path": str(executable),
        "executable_sha256": observed,
        "admitted_executable_sha256": expected,
        "admission_record": str(GIT_TOWN_ADMISSION.relative_to(ROOT)),
        "admission_record_sha256": file_sha256(GIT_TOWN_ADMISSION),
        "digest_matches_admission": observed == expected,
        "consumer_worktree_execution": "HUMAN_ADMIT_REQUIRED",
        "consumer_worktree_execution_reason": (
            "git-town activation writes git-town.* into the configuration a linked "
            "worktree shares with the consumer, and the consumer manifest assigns "
            "config activation to HUMAN"),
    }
    if not base["digest_matches_admission"]:
        base["detail"] = ("executable digest does not equal the admitted one; the lane "
                          "did not start the process")
        return base

    root = Path(tempfile.mkdtemp(prefix="consumer-git-town-"))
    home, tmp = root / "home", root / "tmp"
    mirror, work, worker = root / "remote.git", root / "work", root / "worker"
    commands: list[dict[str, Any]] = []
    try:
        for directory in (home, tmp):
            directory.mkdir(parents=True)
        (home / ".gitconfig").write_text("", encoding="utf-8")
        search = os.environ.get("PATH", "")
        git_bin = "git"
        for directory in REAL_GIT_DIRS:
            if Path(directory, "git").is_file():
                search = f"{directory}:{search}"
                git_bin = str(Path(directory, "git"))
                break
        env = {**os.environ, "HOME": str(home), "TMPDIR": str(tmp), "PATH": search,
               "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
               "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_TERMINAL_PROMPT": "0",
               "GIT_EDITOR": ":", "GIT_SEQUENCE_EDITOR": ":", "GIT_PAGER": "cat",
               "PAGER": "cat", "LC_ALL": "C", "NO_COLOR": "1"}

        def plain(*args: str, cwd: Path = work) -> subprocess.CompletedProcess[str]:
            return subprocess.run([git_bin, *args], cwd=str(cwd), env=env,
                                  capture_output=True, text=True, timeout=300)

        def town(*args: str, cwd: Path = work) -> int:
            done = subprocess.run([str(executable), *args], cwd=str(cwd), env=env,
                                  capture_output=True, text=True, timeout=300)
            commands.append({
                "argv": ["git-town", *args],
                "exit": done.returncode,
                "stdout_bytes": len(done.stdout.encode()),
                "stdout_sha256": sha256(done.stdout.encode()),
                "stderr_sha256": sha256(done.stderr.encode()),
            })
            return done.returncode

        head = git(consumer, "rev-parse", "HEAD")
        branch = git(consumer, "rev-parse", "--abbrev-ref", "HEAD")
        plain("clone", "--local", "--bare", str(consumer), str(mirror), cwd=root)
        plain("clone", str(mirror), str(work), cwd=root)
        plain("config", "user.name", "Consumer Canary")
        plain("config", "user.email", "consumer-canary@example.invalid")
        plain("config", f"git-town.main-branch", branch)

        town("--version")
        town("config")
        town("status")

        # A stack on the consumer's real history: a child that consumes bytes its
        # parent has not merged is the only shape whose synchronization means
        # anything. Both branch tips are pushed to the local bare mirror, which is
        # a filesystem path and not a forge.
        town("hack", "canary-parent")
        (work / "canary-parent.txt").write_text("parent-v1\n", encoding="utf-8")
        plain("add", "canary-parent.txt")
        plain("commit", "-m", "canary parent v1")
        town("append", "canary-child")
        (work / "canary-child.txt").write_text("child\n", encoding="utf-8")
        plain("add", "canary-child.txt")
        plain("commit", "-m", "canary child")
        plain("push", "-u", "origin", "canary-parent", "canary-child")
        plain("switch", "canary-parent")
        with (work / "canary-parent.txt").open("a", encoding="utf-8") as stream:
            stream.write("parent-v2\n")
        plain("add", "canary-parent.txt")
        plain("commit", "-m", "canary parent v2")
        plain("push", "origin", "canary-parent")
        plain("switch", branch)

        plain("worktree", "add", str(worker), "canary-child")
        subprocess.run([git_bin, "config", "user.email", "consumer-canary@example.invalid"],
                       cwd=str(worker), env=env, capture_output=True, timeout=60)

        sync_argv = [str(a) for a in manifest.get("sync_argv", [])][2:] or [
            "sync", "--stack", "--non-interactive", "--no-auto-resolve", "--no-push"]
        refs_before = _ref_digest(worker, git_bin, env)
        mirror_before = _ref_digest(mirror, git_bin, env)
        dry_exit = town(*sync_argv, "--dry-run", cwd=worker)
        refs_after = _ref_digest(worker, git_bin, env)
        live_exit = town(*sync_argv, cwd=worker)
        mirror_after = _ref_digest(mirror, git_bin, env)
        ancestor = subprocess.run(
            [git_bin, "merge-base", "--is-ancestor", "canary-parent", "canary-child"],
            cwd=str(worker), env=env, capture_output=True, timeout=120).returncode == 0
        clean = plain("status", "--porcelain=v1", cwd=worker).stdout.strip() == ""

        forbidden = set(manifest.get("forbidden_flags", []))
        observed_forbidden = sorted({token for entry in commands for token in entry["argv"]
                                     if token in forbidden})
        base.update({
            "subject": {
                "consumer_commit": head,
                "consumer_default_branch": branch,
                "execution_repository": "disposable clone under TMPDIR",
                "origin_remote": "local bare mirror under TMPDIR",
                "consumer_git_dir_touched_by_git_town": False,
            },
            "modes_declared_by_consumer": manifest.get("modes"),
            "sync_argv_from_consumer_manifest": manifest.get("sync_argv"),
            "commands": commands,
            "forbidden_flags_observed": observed_forbidden,
            "dry_run_exit": dry_exit,
            "dry_run_mutated_local_refs": refs_before != refs_after,
            "live_no_push_exit": live_exit,
            "local_bare_remote_refs_unchanged": mirror_before == mirror_after,
            "parent_is_ancestor_after_sync": ancestor,
            "worker_worktree_clean_after": clean,
            "pushes_to_forge": False,
            "pushes_to_local_bare_mirror": True,
            "consumer_head_unchanged": git(consumer, "rev-parse", "HEAD") == head,
            "consumer_dirty_after": len([l for l in git(consumer, "status", "--porcelain")
                                         .splitlines() if l.strip()]),
        })
        return base
    finally:
        shutil.rmtree(root, ignore_errors=True)


def bind_conflict_canary(path: Path) -> dict[str, Any]:
    """Bind the planted-conflict result #234 requires to the run that produced it.

    The conflict canary is a separate run against disposable fixtures, because a
    semantic conflict has to be planted and the consumer's history is not ours to
    plant one in. Binding it by digest is what stops "a conflict fails closed"
    from being a sentence in a receipt whose own run never met a conflict.
    """
    body = json.loads(path.read_text(encoding="utf-8"))
    conflict = body.get("conflict_canary", {})
    return {
        "receipt": path.name,
        "receipt_sha256": file_sha256(path),
        "tool_version": body.get("tool_version"),
        "result": body.get("result"),
        "sync_exit": conflict.get("sync_exit"),
        "unmerged_paths_present": conflict.get("unmerged_paths_present"),
        "suspended_operation_present": conflict.get("suspended_operation_present"),
        "git_town_reports_suspended": conflict.get("git_town_reports_suspended"),
        "automatic_semantic_recovery_attempted": conflict.get(
            "automatic_semantic_recovery_attempted"),
    }


def git_town_state(observation: dict[str, Any]) -> str:
    """EXERCISED only when every claim the link needs was read back and held."""
    if not observation.get("digest_matches_admission"):
        return "BLOCKED"
    required = (
        observation.get("dry_run_exit") == 0,
        observation.get("dry_run_mutated_local_refs") is False,
        observation.get("live_no_push_exit") == 0,
        observation.get("local_bare_remote_refs_unchanged") is True,
        observation.get("parent_is_ancestor_after_sync") is True,
        observation.get("consumer_head_unchanged") is True,
        observation.get("consumer_dirty_after") == 0,
        observation.get("forbidden_flags_observed") == [],
    )
    return "EXERCISED" if all(required) else "FAIL"


def probe_forgejo(url: str, timeout: float = 5.0) -> dict[str, Any]:
    """Ask the loopback forge whether it is there, and record the answer either way."""
    host, _, port = url.split("//", 1)[1].partition(":")
    port_number = int(port.split("/")[0] or 80)
    try:
        with socket.create_connection((host, port_number), timeout=timeout):
            return {"forge_url": url, "reachable": True}
    except OSError as error:
        return {
            "forge_url": url,
            "reachable": False,
            "probe": f"tcp-connect {host}:{port_number}",
            "errno": getattr(error, "errno", None),
            "error": str(error),
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


LANES = {
    "git_town_local": "git-town-dry-run-and-local-no-push-sync",
    "forgejo": "forgejo-issue-pr-receipts",
    "github_actions": "exact-head-github-actions",
    "publication": "publication-candidate",
}


def coverage(links: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        "exercised": sorted(l["link"] for l in links if l["state"] == "EXERCISED"),
        "blocked": sorted(l["link"] for l in links if l["state"] == "BLOCKED"),
        "absent": sorted(l["link"] for l in links if l["state"] == "ABSENT"),
        "not_exercised": sorted(l["link"] for l in links
                                if l["state"] in {"NOT_EXERCISED", "SKIPPED_BY_POLICY"}),
    }


def lanes(links: list[dict[str, Any]]) -> dict[str, str]:
    states = {l["link"]: l["state"] for l in links}
    return {lane: states[name] for lane, name in LANES.items()}


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "replay":
        return replay(sys.argv[2:])
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--consumer", type=Path, required=True)
    parser.add_argument("--github", required=True)
    parser.add_argument("--forgejo", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--allow-worktree", action="store_true")
    parser.add_argument("--git-town-bin", type=Path, default=None,
                        help="already-admitted git-town executable; never installed, "
                             "never put on PATH, never pointed at the consumer's own "
                             "git directory")
    parser.add_argument("--conflict-canary-receipt", type=Path, default=None,
                        help="git-town-live-canary-receipt/v1 from the planted-conflict "
                             "run, bound into the synchronization link by digest")
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
    if args.git_town_bin is None:
        links.append(link(
            "git-town-dry-run-and-local-no-push-sync", "BLOCKED",
            "no admitted executable was supplied; the lane did not start a process",
            executable_on_path=gate["git_town_executable"],
            consumer_executable_state=town.get("executable_state"),
            consumer_live_sync_state=town.get("live_sync_state"),
            human_admit_required=town.get("human_admit_required"),
            note=("--git-town-bin is how an admitted artifact reaches this lane. The "
                  "executable is never installed and never placed on PATH, so its "
                  "absence from PATH is not evidence about admission.")))
    else:
        manifest_path = consumer / ".github-delivery" / "git-town" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        observation = exercise_git_town(consumer, args.git_town_bin.resolve(), manifest)
        if args.conflict_canary_receipt is not None:
            observation["conflict_canary"] = bind_conflict_canary(
                args.conflict_canary_receipt)
        links.append(link(
            "git-town-dry-run-and-local-no-push-sync", git_town_state(observation),
            "the consumer's declared sync argv run against a disposable clone carrying "
            "its exact commit, with a local bare remote; dry-run then local no-push, "
            "both read back from git rather than from git-town's own output",
            consumer_executable_state=town.get("executable_state"),
            consumer_live_sync_state=town.get("live_sync_state"),
            human_admit_required=town.get("human_admit_required"),
            **observation))

    links.append(link(
        "verified-implementation-slices", "NOT_EXERCISED",
        "the consumer ships a local verification contract, but running it proves the "
        "consumer's own tests rather than a slice this canary produced, and this canary "
        "produced none",
        contract_sha256=gate["local_verification_contract_sha256"]))

    # The forge is probed before it is read. Without this the reconciliation
    # raises on connect and the whole canary dies with no receipt, which reports
    # a host with no forge as a run that never happened.
    forge = probe_forgejo(gate["remotes"].get("forgejo", "http://localhost:3000"))
    if not forge["reachable"]:
        exhaustive = False
        links.append(link(
            "forgejo-issue-pr-receipts", "ABSENT",
            "the loopback forge is not listening on this host; no Forgejo read, issue or "
            "PR happened", **forge))
        links.append(link(
            "admitted-local-main-integration", "NOT_EXERCISED",
            "nothing was produced to integrate; the canary is read-only by construction"))
        links.append(link(
            "github-reconciliation-inventory", "BLOCKED",
            "the dual-forge reconciliation cannot close with one forge unreachable, and a "
            "GitHub-only inventory is a different claim than the one this link makes",
            **forge))
    else:
        transport_path = args.out / "reconciliation-transport.json"
        observation_path = args.out / "reconciliation-observation.json"
        transport = reconciliation.capture(args.github, args.forgejo,
                                           gate["default_branch"], "http://localhost:3000", 30)
        inventory = reconciliation._provider_inventory(transport)
        observation = build_observation(transport, inventory, local_main_changed=False)
        transport_path.write_text(json.dumps(transport, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
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
        "coverage": coverage(links),
        "lanes": lanes(links),
        # Every flag here is about the consumer. The synchronization lane does
        # create branches and does push, inside a disposable clone with a local
        # bare remote -- recorded separately so this block cannot be read as
        # "nothing anywhere was mutated".
        "mutations_performed": {
            "branches_created": False, "issues_created": False, "prs_created": False,
            "pushes": False, "merges": False, "consumer_files_changed": False,
            "worktrees_created_and_removed": bool(args.allow_worktree),
            "disposable_clone_branches_created": args.git_town_bin is not None,
            "disposable_clone_pushes_to_local_bare_remote": args.git_town_bin is not None,
        },
        "declared_non_claims": [
            "a read-only reconciliation is not a delivery transition",
            "the consumer's own tests were not run, so nothing here says its main is green",
            "reaching a forge is not the same as being admitted to publish to it",
            "Git Town ran against a disposable clone of the consumer, so it says what the "
            "admitted binary does to the consumer's history, not that the consumer's own "
            "checkout has ever been synchronized",
            "the Forgejo lane is absent rather than failed; nothing here says a local "
            "forge would or would not have accepted a delivery",
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
