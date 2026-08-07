#!/usr/bin/env python3
"""Probe every merge-authority layer before work starts, then land admitted PRs.

Merge is not one permission bit. Four independent layers can refuse, each on a
different host, which is why patching one host does not stop the next one from
blocking. `preflight` runs each layer's own gate for real -- it pipes a
synthetic PreToolUse payload through the configured Claude Code hooks and calls
`codex execpolicy check` -- instead of guessing, and names the layer plus its
fix. `land` merges only what a human admitted, pinned to the admitted head SHA.

Layers:
  L1 HUMAN-ADMIT   `merge-admit` label applied by the repository owner, after
                   the head commit, on GitHub (auditable server-side event).
  L2 HOST-POLICY   the local shell gate of whichever agent host is running.
  L3 GITHUB        token scopes, draft state, mergeability, branch rules.
  L4 MERGE         performed by `land`, with --match-head-commit.

Usage:
  merge_gate.py preflight --repo OWNER/REPO [--snapshot FILE] [--allow-unstable]
  merge_gate.py land --repo OWNER/REPO [--dry-run] [--allow-unstable]

Exit codes: 0 ready, 1 a layer refuses, 3 nothing admitted (absence != refusal).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ADMIT_LABEL = "merge-admit"
REPO_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
SHA_RE = re.compile(r"[0-9a-f]{40}")
LANDABLE_STATES = {"CLEAN", "HAS_HOOKS"}
NOT_READY = 3


class GateError(RuntimeError):
    """Raised when merge authority cannot be established."""


def _iso(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _gh(args: list[str]) -> str:
    if shutil.which("gh") is None:
        raise GateError("gh CLI not on PATH -- install it or use --snapshot")
    done = subprocess.run(["gh", *args], capture_output=True, text=True)
    if done.returncode != 0:
        raise GateError(f"gh {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def _gh_json(args: list[str], empty: Any) -> Any:
    """`gh` prints nothing at all for some empty result sets -- a repo with no
    labels, an issue with no matching events. Empty output is absence, not a
    parse error, so it gets an explicit exit instead of a traceback."""
    raw = _gh(args).strip()
    if not raw:
        return empty
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise GateError(f"gh {' '.join(args)} returned non-JSON: {raw[:120]}") from error


# --------------------------------------------------------------------------
# snapshot: one shape for live GitHub and for offline replay in tests
# --------------------------------------------------------------------------


def fetch_snapshot(repository: str) -> dict[str, Any]:
    """Read the live admitted-PR set. Never called by tests; they use --snapshot."""
    owner = _gh_json(["api", f"repos/{repository}", "--jq", "{login:.owner.login}"], {})
    if not owner.get("login"):
        raise GateError(f"could not read the owner of {repository}")
    fields = "number,url,title,isDraft,headRefOid,mergeable,mergeStateStatus"
    pulls = _gh_json(
        [
            "pr", "list", "--repo", repository, "--state", "open",
            "--label", ADMIT_LABEL, "--json", fields,
        ],
        [],
    )
    for pull in pulls:
        head = pull["headRefOid"]
        pull["head_committed_at"] = _gh_json(
            ["api", f"repos/{repository}/commits/{head}", "--jq", "{d:.commit.committer.date}"],
            {},
        ).get("d")
        pull["admit"] = _gh_json(
            [
                "api", f"repos/{repository}/issues/{pull['number']}/events",
                "--paginate", "--jq",
                f'[.[]|select(.event=="labeled" and .label.name=="{ADMIT_LABEL}")]'
                "|last|{actor:.actor.login,at:.created_at}",
            ],
            None,
        )
    return {"repo": repository, "owner": owner["login"], "pulls": pulls}


def load_snapshot(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateError(f"unreadable snapshot: {path}: {error}") from error
    for field in ("repo", "owner", "pulls"):
        if field not in value:
            raise GateError(f"snapshot lacks '{field}': {path}")
    return value


# --------------------------------------------------------------------------
# L1 human admit
# --------------------------------------------------------------------------


def check_admit(pull: dict[str, Any], owner: str) -> str | None:
    """Return a refusal reason, or None when the human admit holds."""
    admit = pull.get("admit")
    if not isinstance(admit, dict) or not admit.get("actor"):
        return f"no `{ADMIT_LABEL}` label event -- nobody admitted this PR"
    if admit["actor"] != owner:
        return f"`{ADMIT_LABEL}` applied by {admit['actor']}, not repository owner {owner}"
    try:
        admitted_at = _iso(admit["at"])
        head_at = _iso(pull["head_committed_at"])
    except (KeyError, ValueError) as error:
        return f"unparseable admit/head timestamp: {error}"
    if admitted_at < head_at:
        return (
            f"admit-stale: labelled {admit['at']} but head {pull['headRefOid'][:7]} "
            f"landed {pull['head_committed_at']} -- re-apply the label"
        )
    return None


# --------------------------------------------------------------------------
# L2 host policy -- run each host's own gate, do not guess
# --------------------------------------------------------------------------


def active_host() -> str:
    if os.environ.get("CODEX_SANDBOX"):
        return "codex"
    if os.environ.get("CLAUDECODE"):
        return "claude-code"
    return "shell"


def _hook_commands(sources: list[Path]) -> list[str]:
    """Collect PreToolUse command hooks from settings files that declare them."""
    commands: list[str] = []
    for path in sources:
        if not path.is_file():
            continue
        try:
            settings = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for entry in settings.get("hooks", {}).get("PreToolUse", []):
            matcher = entry.get("matcher", "*")
            if matcher not in ("*", "") and "Bash" not in matcher:
                continue
            for hook in entry.get("hooks", []):
                if hook.get("type") == "command" and hook.get("command"):
                    commands.append(hook["command"])
    return commands


def _claude_hook_commands() -> list[str]:
    home = Path.home() / ".claude"
    project = Path.cwd() / ".claude"
    return _hook_commands(
        [
            home / "settings.json",
            home / "settings.local.json",
            project / "settings.json",
            project / "settings.local.json",
        ]
    )


def _codex_hook_commands() -> list[str]:
    # Codex mirrors Claude Code's PreToolUse plane in ~/.codex/hooks.json. It is
    # a separate gate from execpolicy and from the sandbox permission profile:
    # a rule that says allow and a profile with network still lose to a hook
    # that exits 2, so probing only the first two reports a false green.
    return _hook_commands([Path.home() / ".codex" / "hooks.json"])


def _run_pretooluse(commands: list[str], merge_cmd: list[str]) -> tuple[str, str] | None:
    """Return a refusal, or None when no hook blocks the real merge command."""
    if not commands:
        return None
    payload = json.dumps(
        {
            "session_id": "merge-gate-preflight",
            "hook_event_name": "PreToolUse",
            "cwd": os.getcwd(),
            "tool_name": "Bash",
            "tool_input": {"command": " ".join(merge_cmd)},
        }
    )
    for command in commands:
        done = subprocess.run(
            ["bash", "-c", command], input=payload, capture_output=True, text=True
        )
        if done.returncode == 2:
            reason = (done.stderr or done.stdout).strip().splitlines()
            return "BLOCK", f"{command}: {reason[0] if reason else 'exit 2'}"
    return None


def probe_claude_code(merge_cmd: list[str]) -> tuple[str, str]:
    """Feed the real merge command through the configured PreToolUse hooks."""
    commands = _claude_hook_commands()
    refusal = _run_pretooluse(commands, merge_cmd)
    if refusal:
        return refusal
    if not commands:
        return "ALLOW", "no PreToolUse hook configured"
    return "ALLOW", f"{len(commands)} PreToolUse hook(s) returned non-blocking"


def _load_toml(path: Path) -> dict[str, Any]:
    import tomllib

    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _codex_config() -> tuple[str, dict[str, Any]]:
    """Resolve Codex config the way Codex does: project layer over user layer.

    A project `.codex/config.toml` that says nothing about permissions inherits
    the user-level default. Reading only the nearest file reports a false red on
    every repo whose config exists purely for MCP servers.
    """
    user_path = Path.home() / ".codex" / "config.toml"
    project_path = None
    for directory in (Path.cwd(), *Path.cwd().parents):
        candidate = directory / ".codex" / "config.toml"
        if candidate.is_file() and candidate != user_path:
            project_path = candidate
            break

    user = _load_toml(user_path) if user_path.is_file() else {}
    project = _load_toml(project_path) if project_path else {}
    merged: dict[str, Any] = {**user, **project}
    merged["permissions"] = {**user.get("permissions", {}), **project.get("permissions", {})}
    sources = [str(p) for p in (project_path, user_path if user_path.is_file() else None) if p]
    return (" over ".join(sources) or "no .codex/config.toml found"), merged


def probe_codex(repository: str, merge_cmd: list[str]) -> tuple[str, str]:
    """Check all three Codex sub-gates: network grant, PreToolUse hook, execpolicy."""
    where, config = _codex_config()
    notes: list[str] = []
    codex_hooks = _codex_hook_commands()
    hook_refusal = _run_pretooluse(codex_hooks, merge_cmd)
    if hook_refusal:
        return hook_refusal
    if codex_hooks:
        notes.append(f"{len(codex_hooks)} PreToolUse hook(s) returned non-blocking")
    profile = config.get("default_permissions")
    if isinstance(profile, str) and not profile.startswith(":"):
        network = config.get("permissions", {}).get(profile, {}).get("network", {})
        if not network.get("enabled"):
            return "BLOCK", (
                f"{where}: profile '{profile}' has no [permissions.{profile}.network] "
                "enabled = true -- the sandbox cannot reach github.com at all"
            )
        notes.append(f"profile '{profile}' has network enabled")
    elif profile != ":danger-full-access":
        # No named profile: the built-in presets (and the built-in default when
        # `default_permissions` is absent) all disable network, so `gh` and
        # `git push` fail inside the sandbox before merge is even reachable.
        return "BLOCK", (
            f"{where}: default_permissions={profile!r} -- built-in presets disable "
            "network; define a profile extending \":workspace\" with "
            "[permissions.<name>.network] enabled = true"
        )
    # Evaluate the whole rules directory, the way Codex loads it. Deriving the
    # filename from the repository couples the probe to the installer's naming
    # convention, so a hand-written rule under any other name reads as absent --
    # a false red, the same modelling error as reading only the nearest config.
    rules_dir = Path.home() / ".codex" / "rules"
    rule_files = sorted(rules_dir.glob("*.rules")) if rules_dir.is_dir() else []
    installer_hint = (
        f"run install-codex-merge-rule.sh --repo {repository} --rules-dir {rules_dir}"
    )
    if not rule_files:
        return "BLOCK", f"no execpolicy rule files in {rules_dir} -- {installer_hint}"
    if shutil.which("codex") is None:
        return "UNKNOWN", f"codex not on PATH; {len(rule_files)} rule file(s) unverified"
    rule_args: list[str] = []
    for rule_file in rule_files:
        rule_args += ["--rules", str(rule_file)]
    done = subprocess.run(
        ["codex", "execpolicy", "check", *rule_args, "--", *merge_cmd],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0 or "allow" not in done.stdout.lower():
        return "BLOCK", (
            f"no rule in {rules_dir} allows this merge ({len(rule_files)} file(s) checked) "
            f"-- {installer_hint}"
        )
    notes.append(f"execpolicy allows ({len(rule_files)} rule file(s) checked)")
    return "ALLOW", "; ".join(notes)


# --------------------------------------------------------------------------
# L3 GitHub
# --------------------------------------------------------------------------


def check_github(pull: dict[str, Any], allow_unstable: bool) -> str | None:
    if pull.get("isDraft"):
        return "PR is a draft -- mark it ready for review first"
    if not SHA_RE.fullmatch(str(pull.get("headRefOid", ""))):
        return "headRefOid is not a full 40-character SHA"
    mergeable = pull.get("mergeable")
    if mergeable == "CONFLICTING":
        return "CONFLICTING -- rebase onto the base branch"
    if mergeable != "MERGEABLE":
        return f"mergeable={mergeable} -- GitHub has not finished computing; retry"
    state = pull.get("mergeStateStatus")
    if state == "UNSTABLE" and allow_unstable:
        return None
    if state not in LANDABLE_STATES:
        return f"mergeStateStatus={state}"
    return None


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------


def detect_repository() -> str:
    """Resolve OWNER/REPO from the current directory's git remote."""
    value = _gh(["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]).strip()
    if REPO_RE.fullmatch(value) is None:
        raise GateError(f"could not resolve a GitHub repository from {os.getcwd()}")
    return value


def bootstrap(repository: str, rules_dir: Path, allow_unstable: bool) -> int:
    """Make one repository ready for this mechanism. Idempotent: safe to re-run.

    Only the two per-repository pieces live here. Everything else -- the skill
    itself, both hosts' PreToolUse blacklists, the Codex sandbox profile -- is
    user-level and already applies to every project without per-repo work.
    """
    labels = _gh_json(
        ["label", "list", "-R", repository, "--search", ADMIT_LABEL, "--json", "name"], []
    )
    if any(label.get("name") == ADMIT_LABEL for label in labels):
        print(f"OK      label `{ADMIT_LABEL}` already exists in {repository}")
    else:
        _gh(
            [
                "label", "create", ADMIT_LABEL, "-R", repository, "-c", "0E8A16",
                "-d", "owner admits this PR for agent landing",
            ]
        )
        print(f"CREATED label `{ADMIT_LABEL}` in {repository}")

    rule = rules_dir / f"github-merge-{repository.replace('/', '-')}.rules"
    if shutil.which("codex") is None:
        print(f"SKIP    execpolicy rule: codex not on PATH ({rule.name})")
    elif rule.is_file():
        print(f"OK      execpolicy rule already installed: {rule}")
    else:
        installer = Path(__file__).resolve().parent / "install-codex-merge-rule.sh"
        done = subprocess.run(
            ["bash", str(installer), "--repo", repository, "--rules-dir", str(rules_dir)],
            capture_output=True,
            text=True,
        )
        if done.returncode != 0:
            raise GateError(f"install-codex-merge-rule.sh failed: {done.stderr.strip()}")
        print(f"CREATED execpolicy rule: {rule} (restart Codex to load it)")

    print(f"--- preflight {repository} ---")
    return preflight(repository, None, allow_unstable)


def merge_command(repository: str, number: int, head: str) -> list[str]:
    return [
        "gh", "pr", "merge", "--repo", repository, str(number),
        "--squash", "--match-head-commit", head,
    ]


def preflight(repository: str, snapshot_path: Path | None, allow_unstable: bool) -> int:
    snapshot = load_snapshot(snapshot_path) if snapshot_path else fetch_snapshot(repository)
    if snapshot["repo"] != repository:
        raise GateError(f"snapshot repo {snapshot['repo']} != --repo {repository}")
    pulls = snapshot["pulls"]
    ready: list[dict[str, Any]] = []
    blocked = 0
    for pull in sorted(pulls, key=lambda item: item["number"]):
        head = str(pull.get("headRefOid", ""))[:7]
        admit_reason = check_admit(pull, snapshot["owner"])
        reason = admit_reason or check_github(pull, allow_unstable)
        layer = "L1 HUMAN-ADMIT" if admit_reason else "L3 GITHUB"
        if reason:
            blocked += 1
            print(f"BLOCK #{pull['number']} {head} [{layer}] {reason}", file=sys.stderr)
        else:
            ready.append(pull)
            print(f"READY #{pull['number']} {head} {pull.get('title', '')[:60]}")

    # The host probe runs even with nothing admitted: knowing which layer will
    # refuse is worth most *before* the work starts, not after.
    sample = (ready or pulls or [{"number": 1, "headRefOid": "0" * 40}])[0]
    probe_cmd = merge_command(repository, sample["number"], sample["headRefOid"])
    host = active_host()
    host_blocked = False
    for name, (verdict, detail) in (
        ("claude-code", probe_claude_code(probe_cmd)),
        ("codex", probe_codex(repository, probe_cmd)),
    ):
        marker = "<-- active" if name == host else ""
        stream = sys.stderr if verdict == "BLOCK" and name == host else sys.stdout
        print(f"L2 HOST-POLICY {name}: {verdict} -- {detail} {marker}".rstrip(), file=stream)
        if verdict == "BLOCK" and name == host:
            host_blocked = True

    if host_blocked:
        print(f"REFUSED by L2 HOST-POLICY on {host}; nothing merged.", file=sys.stderr)
        return 1
    if blocked:
        print(f"REFUSED: {blocked} admitted PR(s) failed L1/L3.", file=sys.stderr)
        return 1
    if not ready:
        print(f"NO-ADMIT {repository}: no open PR carries the `{ADMIT_LABEL}` label.")
        print(f"  human admit = apply `{ADMIT_LABEL}` on GitHub (works from a phone).")
        return NOT_READY
    print(f"PREFLIGHT GREEN: {len(ready)} PR(s) landable on {repository} via {host}")
    return 0


def land(repository: str, allow_unstable: bool, dry_run: bool) -> int:
    """Merge every admitted PR, re-checking each one against a fresh snapshot."""
    landed = 0
    while True:
        snapshot = fetch_snapshot(repository)
        pending = [
            pull
            for pull in sorted(snapshot["pulls"], key=lambda item: item["number"])
            if check_admit(pull, snapshot["owner"]) is None
            and check_github(pull, allow_unstable) is None
        ]
        if not pending:
            break
        pull = pending[0]
        command = merge_command(repository, pull["number"], pull["headRefOid"])
        if dry_run:
            print(f"DRY-RUN {' '.join(command)}")
            return 0
        done = subprocess.run(command, capture_output=True, text=True)
        if done.returncode != 0:
            print(f"FAIL #{pull['number']}: {done.stderr.strip()}", file=sys.stderr)
            print(f"LANDED={landed} before the failure.", file=sys.stderr)
            return 1
        landed += 1
        print(f"LANDED #{pull['number']} {pull['headRefOid'][:7]}")
    if landed == 0:
        print(f"NO-ADMIT {repository}: nothing was landable.")
        return NOT_READY
    print(f"LANDED={landed}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, helptext in (
        ("preflight", "probe every merge-authority layer without merging"),
        ("land", "merge the admitted PRs, pinned to their admitted head SHA"),
        ("bootstrap", "make one repository ready (label + execpolicy rule); idempotent"),
    ):
        sub = commands.add_parser(name, help=helptext)
        sub.add_argument("--repo", help="OWNER/REPO; defaults to the current directory's remote")
        sub.add_argument("--allow-unstable", action="store_true")
        if name == "preflight":
            sub.add_argument("--snapshot", type=Path, help="offline replay; no network")
        elif name == "land":
            sub.add_argument("--dry-run", action="store_true")
        else:
            sub.add_argument("--rules-dir", type=Path, default=Path.home() / ".codex" / "rules")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        repository = args.repo or detect_repository()
        if REPO_RE.fullmatch(repository) is None:
            print(f"FAIL --repo must be OWNER/REPOSITORY: {repository}", file=sys.stderr)
            return 64
        if args.command == "preflight":
            return preflight(repository, args.snapshot, args.allow_unstable)
        if args.command == "bootstrap":
            return bootstrap(repository, args.rules_dir, args.allow_unstable)
        return land(repository, args.allow_unstable, args.dry_run)
    except GateError as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
