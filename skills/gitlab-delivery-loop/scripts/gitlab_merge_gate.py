#!/usr/bin/env python3
"""Probe every merge-authority layer before work starts, then land admitted MRs.

Merge is not one permission bit. Four independent layers can refuse, each on a
different host, which is why patching one host does not stop the next one from
blocking. `preflight` runs each layer's own gate for real -- it pipes a
synthetic PreToolUse payload through the configured hooks and calls
`codex execpolicy check` -- instead of guessing, and names the layer plus its
fix. `land` merges only what a human admitted, pinned to the admitted head SHA.

Layers:
  L1 HUMAN-ADMIT   `merge-admit` label applied by a project Owner, after the
                   head commit, on GitLab (auditable resource label event).
  L2 HOST-POLICY   the local shell gate of whichever agent host is running.
  L3 GITLAB        draft state, conflicts, detailed_merge_status, approvals.
  L4 MERGE         performed by `land`, with --sha and --auto-merge=false.

Usage:
  gitlab_merge_gate.py preflight --project GROUP/PROJECT [--host H] [--snapshot F]
  gitlab_merge_gate.py land --project GROUP/PROJECT [--dry-run]
  gitlab_merge_gate.py bootstrap --project GROUP/PROJECT

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
from urllib.parse import quote

ADMIT_LABEL = "merge-admit"
FORGE = "gitlab"
DEFAULT_HOST = "gitlab.com"
# GitLab access levels: 10 Guest, 20 Reporter, 30 Developer, 40 Maintainer,
# 50 Owner. Only Owner counts as the human landing decision -- Maintainer can
# already merge, so requiring Maintainer would admit anyone who can merge anyway.
OWNER_ACCESS_LEVEL = 50
HOST_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?(?::[0-9]{1,5})?")
PROJECT_RE = re.compile(
    r"[A-Za-z0-9_.][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_.][A-Za-z0-9_.-]*)+"
)
SHA_RE = re.compile(r"[0-9a-f]{40}")
NOT_READY = 3

# `detailed_merge_status` replaced the coarse `merge_status`. Only `mergeable`
# means landable; the rest are separated so an unfinished computation never
# reads as a refusal, and a refusal never reads as "retry later".
LANDABLE = "mergeable"
UNSTABLE = {"ci_still_running", "ci_must_pass"}
NOT_COMPUTED = {"unchecked", "checking", "preparing"}
STATUS_FIX = {
    "conflict": "CONFLICTING -- rebase onto the target branch",
    "draft_status": "MR is a draft -- mark it ready first",
    "need_rebase": "needs rebase onto the target branch",
    "discussions_not_resolved": "unresolved threads -- resolve them first",
    "not_approved": "required approvals missing",
    "not_open": "MR is not open",
    "blocked_status": "blocked by another merge request",
    "policies_denied": "denied by a security policy",
}


class GateError(RuntimeError):
    """Raised when merge authority cannot be established."""


def _iso(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _glab(args: list[str]) -> str:
    if shutil.which("glab") is None:
        raise GateError("glab CLI not on PATH -- install it or use --snapshot")
    done = subprocess.run(["glab", *args], capture_output=True, text=True)
    if done.returncode != 0:
        raise GateError(f"glab {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def _glab_json(host: str, path: str, empty: Any) -> Any:
    """Empty output is absence, not a parse error, so it gets an explicit exit."""
    raw = _glab(["api", "--hostname", host, path]).strip()
    if not raw:
        return empty
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise GateError(f"glab api {path} returned non-JSON: {raw[:120]}") from error


def _encoded(project: str) -> str:
    return quote(project, safe="")


# --------------------------------------------------------------------------
# snapshot: one shape for live GitLab and for offline replay in tests
# --------------------------------------------------------------------------


def fetch_snapshot(host: str, project: str) -> dict[str, Any]:
    """Read the live admitted-MR set. Never called by tests; they use --snapshot."""
    encoded = _encoded(project)
    meta = _glab_json(host, f"projects/{encoded}", {})
    if not meta.get("id"):
        raise GateError(f"could not read project {project} on {host}")
    namespace = meta.get("namespace") or {}
    merge_requests = _glab_json(
        host,
        f"projects/{encoded}/merge_requests?state=opened&labels={ADMIT_LABEL}&per_page=100",
        [],
    )
    pulls: list[dict[str, Any]] = []
    for merge_request in merge_requests:
        iid = merge_request["iid"]
        head = merge_request.get("sha") or ""
        commit = _glab_json(host, f"projects/{encoded}/repository/commits/{head}", {})
        events = _glab_json(
            host,
            f"projects/{encoded}/merge_requests/{iid}/resource_label_events?per_page=100",
            [],
        )
        admit = None
        for event in events:
            if (
                event.get("action") == "add"
                and (event.get("label") or {}).get("name") == ADMIT_LABEL
            ):
                actor = (event.get("user") or {}).get("username")
                admit = {
                    "actor": actor,
                    "at": event.get("created_at"),
                    "access_level": _access_level(host, encoded, actor),
                }
        pulls.append(
            {
                "admit": admit,
                "detailed_merge_status": merge_request.get("detailed_merge_status"),
                "draft": bool(merge_request.get("draft")),
                "has_conflicts": bool(merge_request.get("has_conflicts")),
                "head_committed_at": commit.get("committed_date"),
                "iid": iid,
                "sha": head,
                "title": merge_request.get("title", ""),
                "web_url": merge_request.get("web_url", ""),
            }
        )
    return {
        "forge": FORGE,
        "host": host,
        "merge_requests": pulls,
        "namespace_kind": namespace.get("kind"),
        "namespace_path": namespace.get("full_path") or namespace.get("path"),
        "project": meta.get("path_with_namespace", project),
        "project_id": meta.get("id"),
    }


def _access_level(host: str, encoded: str, username: str | None) -> int | None:
    """Resolve one member's access level.

    GitLab's project payload has an `owner` field only for personal namespaces;
    for group-owned projects it is null (probed live on a real group project).
    So ownership is read from membership instead, filtered by `query=` so a
    project with thousands of inherited members costs one request, not pages.
    """
    if not username:
        return None
    members = _glab_json(
        host,
        f"projects/{encoded}/members/all?query={quote(username, safe='')}&per_page=100",
        [],
    )
    for member in members:
        if member.get("username") == username:
            level = member.get("access_level")
            return level if isinstance(level, int) else None
    return None


def load_snapshot(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateError(f"unreadable snapshot: {path}: {error}") from error
    if value.get("forge") != FORGE:
        raise GateError(
            f"snapshot forge is {value.get('forge')!r}, not {FORGE!r} -- this is the GitLab "
            "skill; use github-delivery-loop for GitHub snapshots"
        )
    for field in ("host", "project", "merge_requests"):
        if field not in value:
            raise GateError(f"snapshot lacks '{field}': {path}")
    return value


# --------------------------------------------------------------------------
# L1 human admit
# --------------------------------------------------------------------------


def check_admit(merge_request: dict[str, Any], snapshot: dict[str, Any]) -> str | None:
    """Return a refusal reason, or None when the human admit holds."""
    admit = merge_request.get("admit")
    if not isinstance(admit, dict) or not admit.get("actor"):
        return f"no `{ADMIT_LABEL}` label event -- nobody admitted this MR"
    actor = admit["actor"]
    level = admit.get("access_level")
    personal_owner = (
        snapshot.get("namespace_kind") == "user"
        and snapshot.get("namespace_path") == actor
    )
    if not personal_owner and (
        not isinstance(level, int) or level < OWNER_ACCESS_LEVEL
    ):
        return (
            f"`{ADMIT_LABEL}` applied by {actor} with access_level={level} -- "
            f"an Owner ({OWNER_ACCESS_LEVEL}) must admit"
        )
    try:
        admitted_at = _iso(admit["at"])
        head_at = _iso(merge_request["head_committed_at"])
    except (KeyError, TypeError, ValueError) as error:
        return f"unparseable admit/head timestamp: {error}"
    if admitted_at < head_at:
        return (
            f"admit-stale: labelled {admit['at']} but head {str(merge_request['sha'])[:7]} "
            f"landed {merge_request['head_committed_at']} -- re-apply the label"
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


def _run_pretooluse(
    commands: list[str], merge_cmd: list[str]
) -> tuple[str, str] | None:
    """Return a refusal, or None when no hook blocks the real merge command."""
    if not commands:
        return None
    payload = json.dumps(
        {
            "session_id": "gitlab-merge-gate-preflight",
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
    merged["permissions"] = {
        **user.get("permissions", {}),
        **project.get("permissions", {}),
    }
    sources = [
        str(p) for p in (project_path, user_path if user_path.is_file() else None) if p
    ]
    return (" over ".join(sources) or "no .codex/config.toml found"), merged


def probe_codex(host: str, project: str, merge_cmd: list[str]) -> tuple[str, str]:
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
                f"enabled = true -- the sandbox cannot reach {host} at all"
            )
        notes.append(f"profile '{profile}' has network enabled")
    elif profile != ":danger-full-access":
        return "BLOCK", (
            f"{where}: default_permissions={profile!r} -- built-in presets disable "
            'network; define a profile extending ":workspace" with '
            "[permissions.<name>.network] enabled = true"
        )
    # Evaluate the whole rules directory, the way Codex loads it. Deriving the
    # filename from the project couples the probe to the installer's naming
    # convention, so a hand-written rule under any other name reads as absent --
    # a false red, the same modelling error as reading only the nearest config.
    rules_dir = Path.home() / ".codex" / "rules"
    rule_files = sorted(rules_dir.glob("*.rules")) if rules_dir.is_dir() else []
    installer_hint = (
        f"run install-codex-merge-rule.sh --host {host} --project {project} "
        f"--rules-dir {rules_dir}"
    )
    if not rule_files:
        return "BLOCK", f"no execpolicy rule files in {rules_dir} -- {installer_hint}"
    if shutil.which("codex") is None:
        return (
            "UNKNOWN",
            f"codex not on PATH; {len(rule_files)} rule file(s) unverified",
        )
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
# L3 GitLab
# --------------------------------------------------------------------------


def check_gitlab(merge_request: dict[str, Any], allow_unstable: bool) -> str | None:
    if merge_request.get("draft"):
        return "MR is a draft -- mark it ready first"
    if not SHA_RE.fullmatch(str(merge_request.get("sha", ""))):
        return "sha is not a full 40-character SHA"
    if merge_request.get("has_conflicts"):
        return "CONFLICTING -- rebase onto the target branch"
    status = merge_request.get("detailed_merge_status")
    if status == LANDABLE:
        return None
    if status in UNSTABLE:
        return (
            None
            if allow_unstable
            else f"detailed_merge_status={status} (pass --allow-unstable)"
        )
    if status in NOT_COMPUTED:
        return f"detailed_merge_status={status} -- GitLab has not finished computing; retry"
    return f"detailed_merge_status={status}: {STATUS_FIX.get(str(status), 'not mergeable')}"


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------


def repo_ref(host: str, project: str) -> str:
    """`glab -R` accepts a full URL, which pins the host explicitly.

    A bare GROUP/PROJECT would be resolved against whichever host glab infers
    from the current directory -- fine on gitlab.com, wrong on self-managed.
    """
    return f"https://{host}/{project}"


def merge_command(host: str, project: str, iid: int, sha: str) -> list[str]:
    """Build the one merge command this skill is ever allowed to run.

    `--auto-merge=false` is load-bearing, not cosmetic. `glab mr merge` enables
    auto-merge by default whenever a pipeline is running, which returns success
    while nothing has merged -- exactly the "success without the artifact"
    failure this skill exists to refuse. `--sha` is GitLab's HEAD pin: the merge
    fails unless the source branch still points at the admitted commit.
    """
    return [
        "glab",
        "mr",
        "merge",
        "-R",
        repo_ref(host, project),
        str(iid),
        "--squash",
        "--sha",
        sha,
        "--auto-merge=false",
        "--yes",
    ]


def detect_project(host: str) -> tuple[str, str]:
    """Resolve host and GROUP/PROJECT from the current directory's git remote."""
    raw = _glab(["repo", "view", "-F", "json"]).strip()
    try:
        meta = json.loads(raw)
    except json.JSONDecodeError as error:
        raise GateError(f"glab repo view returned non-JSON: {raw[:120]}") from error
    project = meta.get("path_with_namespace")
    if not isinstance(project, str) or PROJECT_RE.fullmatch(project) is None:
        raise GateError(f"could not resolve a GitLab project from {os.getcwd()}")
    web_url = str(meta.get("web_url") or "")
    match = re.match(r"https://([^/]+)/", web_url)
    return (match.group(1) if match else host), project


def bootstrap(host: str, project: str, rules_dir: Path, allow_unstable: bool) -> int:
    """Make one project ready for this mechanism. Idempotent: safe to re-run.

    Only the two per-project pieces live here. Everything else -- the skill
    itself, both hosts' PreToolUse blacklists, the Codex sandbox profile -- is
    user-level and already applies to every project without per-project work.
    """
    reference = repo_ref(host, project)
    raw = _glab(
        ["label", "list", "-R", reference, "-F", "json", "--per-page", "100"]
    ).strip()
    labels = json.loads(raw) if raw else []
    if any(label.get("name") == ADMIT_LABEL for label in labels):
        print(f"OK      label `{ADMIT_LABEL}` already exists in {project}")
    else:
        _glab(
            [
                "label",
                "create",
                "-R",
                reference,
                "--name",
                ADMIT_LABEL,
                "--color",
                "#0E8A16",
                "--description",
                "owner admits this MR for agent landing",
            ]
        )
        print(f"CREATED label `{ADMIT_LABEL}` in {project}")

    slug = f"{host}-{project}".replace("/", "-").replace(".", "-")
    rule = rules_dir / f"gitlab-merge-{slug}.rules"
    if shutil.which("codex") is None:
        print(f"SKIP    execpolicy rule: codex not on PATH ({rule.name})")
    elif rule.is_file():
        print(f"OK      execpolicy rule already installed: {rule}")
    else:
        installer = Path(__file__).resolve().parent / "install-codex-merge-rule.sh"
        done = subprocess.run(
            [
                "bash",
                str(installer),
                "--host",
                host,
                "--project",
                project,
                "--rules-dir",
                str(rules_dir),
            ],
            capture_output=True,
            text=True,
        )
        if done.returncode != 0:
            raise GateError(
                f"install-codex-merge-rule.sh failed: {done.stderr.strip()}"
            )
        print(f"CREATED execpolicy rule: {rule} (restart Codex to load it)")

    print(f"--- preflight {host}/{project} ---")
    return preflight(host, project, None, allow_unstable)


def preflight(
    host: str, project: str, snapshot_path: Path | None, allow_unstable: bool
) -> int:
    snapshot = (
        load_snapshot(snapshot_path) if snapshot_path else fetch_snapshot(host, project)
    )
    if snapshot["project"] != project:
        raise GateError(
            f"snapshot project {snapshot['project']} != --project {project}"
        )
    if snapshot["host"] != host:
        raise GateError(f"snapshot host {snapshot['host']} != --host {host}")
    merge_requests = snapshot["merge_requests"]
    ready: list[dict[str, Any]] = []
    blocked = 0
    for merge_request in sorted(merge_requests, key=lambda item: item["iid"]):
        head = str(merge_request.get("sha", ""))[:7]
        admit_reason = check_admit(merge_request, snapshot)
        reason = admit_reason or check_gitlab(merge_request, allow_unstable)
        layer = "L1 HUMAN-ADMIT" if admit_reason else "L3 GITLAB"
        if reason:
            blocked += 1
            print(
                f"BLOCK !{merge_request['iid']} {head} [{layer}] {reason}",
                file=sys.stderr,
            )
        else:
            ready.append(merge_request)
            print(
                f"READY !{merge_request['iid']} {head} {merge_request.get('title', '')[:60]}"
            )

    # The host probe runs even with nothing admitted: knowing which layer will
    # refuse is worth most *before* the work starts, not after.
    sample = (ready or merge_requests or [{"iid": 1, "sha": "0" * 40}])[0]
    probe_cmd = merge_command(host, project, sample["iid"], sample["sha"])
    active = active_host()
    host_blocked = False
    for name, (verdict, detail) in (
        ("claude-code", probe_claude_code(probe_cmd)),
        ("codex", probe_codex(host, project, probe_cmd)),
    ):
        marker = "<-- active" if name == active else ""
        stream = sys.stderr if verdict == "BLOCK" and name == active else sys.stdout
        print(
            f"L2 HOST-POLICY {name}: {verdict} -- {detail} {marker}".rstrip(),
            file=stream,
        )
        if verdict == "BLOCK" and name == active:
            host_blocked = True

    if host_blocked:
        print(
            f"REFUSED by L2 HOST-POLICY on {active}; nothing merged.", file=sys.stderr
        )
        return 1
    if blocked:
        print(f"REFUSED: {blocked} admitted MR(s) failed L1/L3.", file=sys.stderr)
        return 1
    if not ready:
        print(
            f"NO-ADMIT {host}/{project}: no open MR carries the `{ADMIT_LABEL}` label."
        )
        print(f"  human admit = apply `{ADMIT_LABEL}` on GitLab (works from a phone).")
        return NOT_READY
    print(
        f"PREFLIGHT GREEN: {len(ready)} MR(s) landable on {host}/{project} via {active}"
    )
    return 0


def land(host: str, project: str, allow_unstable: bool, dry_run: bool) -> int:
    """Merge every admitted MR, re-checking each one against a fresh snapshot."""
    landed = 0
    while True:
        snapshot = fetch_snapshot(host, project)
        pending = [
            merge_request
            for merge_request in sorted(
                snapshot["merge_requests"], key=lambda item: item["iid"]
            )
            if check_admit(merge_request, snapshot) is None
            and check_gitlab(merge_request, allow_unstable) is None
        ]
        if not pending:
            break
        merge_request = pending[0]
        command = merge_command(
            host, project, merge_request["iid"], merge_request["sha"]
        )
        if dry_run:
            print(f"DRY-RUN {' '.join(command)}")
            return 0
        done = subprocess.run(command, capture_output=True, text=True)
        if done.returncode != 0:
            print(
                f"FAIL !{merge_request['iid']}: {done.stderr.strip()}", file=sys.stderr
            )
            print(f"LANDED={landed} before the failure.", file=sys.stderr)
            return 1
        landed += 1
        print(f"LANDED !{merge_request['iid']} {merge_request['sha'][:7]}")
    if landed == 0:
        print(f"NO-ADMIT {host}/{project}: nothing was landable.")
        return NOT_READY
    print(f"LANDED={landed}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, helptext in (
        ("preflight", "probe every merge-authority layer without merging"),
        ("land", "merge the admitted MRs, pinned to their admitted head SHA"),
        ("bootstrap", "make one project ready (label + execpolicy rule); idempotent"),
    ):
        sub = commands.add_parser(name, help=helptext)
        sub.add_argument(
            "--project",
            help="GROUP[/SUBGROUP]/PROJECT; defaults to the current directory's remote",
        )
        sub.add_argument(
            "--host", default=None, help=f"GitLab host (default {DEFAULT_HOST})"
        )
        sub.add_argument("--allow-unstable", action="store_true")
        if name == "preflight":
            sub.add_argument("--snapshot", type=Path, help="offline replay; no network")
        elif name == "land":
            sub.add_argument("--dry-run", action="store_true")
        else:
            sub.add_argument(
                "--rules-dir", type=Path, default=Path.home() / ".codex" / "rules"
            )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        host = args.host or DEFAULT_HOST
        project = args.project
        if project is None:
            host, project = detect_project(host)
        if HOST_RE.fullmatch(host) is None:
            print(f"FAIL --host must be a hostname: {host}", file=sys.stderr)
            return 64
        if PROJECT_RE.fullmatch(project) is None:
            print(
                f"FAIL --project must be GROUP[/SUBGROUP]/PROJECT: {project}",
                file=sys.stderr,
            )
            return 64
        if args.command == "preflight":
            return preflight(host, project, args.snapshot, args.allow_unstable)
        if args.command == "bootstrap":
            return bootstrap(host, project, args.rules_dir, args.allow_unstable)
        return land(host, project, args.allow_unstable, args.dry_run)
    except GateError as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
