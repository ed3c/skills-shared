#!/usr/bin/env python3
"""Probe every merge-authority layer before work starts, then land authorized PRs.

Merge is not one permission bit. Four independent layers can refuse, each on a
different host, which is why patching one host does not stop the next one from
blocking. `preflight` runs each layer's own gate for real -- it pipes a
synthetic PreToolUse payload through the configured Claude Code hooks and calls
`codex execpolicy check` -- instead of guessing, and names the layer plus its
fix. `land` pins every merge to the checked head SHA.

Layers:
  L1 AUTHORITY     either a fresh `merge-admit` owner label, or an explicit
                   owner-auto policy whose immutable user identity matches the
                   authenticated viewer and repository owner at runtime.
  L2 HOST-POLICY   the local shell gate of whichever agent host is running.
  L3 GITHUB        token scopes, draft state, mergeability, branch rules.
  L4 MERGE         performed by `land`, with --match-head-commit.

Usage:
  merge_gate.py preflight --repo OWNER/REPO [--pr N] [--snapshot FILE] [--allow-unstable]
  merge_gate.py land --repo OWNER/REPO [--pr N] [--dry-run] [--allow-unstable]
  merge_gate.py configure-owner --owner LOGIN

Exit codes: 0 ready, 1 a layer refuses, 3 nothing authorized (absence != refusal),
4 a gate could not be evaluated (inability != refusal -- the repair is to the
hook configuration or to this probe, never to a permission).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ADMIT_LABEL = "merge-admit"
POLICY_VERSION = 1
POLICY_MODE = "owner-auto"
REPO_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
SHA_RE = re.compile(r"[0-9a-f]{40}")
LANDABLE_STATES = {"CLEAN", "HAS_HOOKS"}
NOT_READY = 3
# A gate that could not be evaluated is neither a pass nor a refusal. It sat
# under exit 1 until a hook referencing an unset variable crashed with exit 2 --
# the blocking contract -- and preflight reported a policy refusal that no
# policy had made. Same three-way discipline as NOT_READY: absence, inability
# and refusal each get their own exit, because each has a different repair.
UNEVALUABLE = 4

MERGE_MUTATION = """mutation($pullRequestId:ID!,$expectedHeadOid:GitObjectID!){
  mergePullRequest(input:{pullRequestId:$pullRequestId,expectedHeadOid:$expectedHeadOid,mergeMethod:SQUASH}){
    pullRequest{number merged mergedAt mergeCommit{oid}}
  }
}"""


class GateError(RuntimeError):
    """Raised when merge authority cannot be established."""


def positive_pull_number(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("--pr must be a positive integer") from error
    if number < 1:
        raise argparse.ArgumentTypeError("--pr must be a positive integer")
    return number


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
        raise GateError(
            f"gh {' '.join(args)} returned non-JSON: {raw[:120]}"
        ) from error


def default_policy_path() -> Path:
    return Path.home() / ".config" / "github-delivery-loop" / "merge-policy.json"


def load_policy(path: Path | None) -> tuple[dict[str, Any] | None, Path | None]:
    """Load the optional user policy. An absent default keeps human-admit mode.

    An explicitly named policy must exist, and any present policy must validate;
    silently falling back to labels after a policy typo would broaden authority.
    """
    candidate = path or default_policy_path()
    if not candidate.is_file():
        if path is not None:
            raise GateError(f"policy file does not exist: {candidate}")
        return None, None
    try:
        policy = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateError(f"unreadable policy: {candidate}: {error}") from error
    if policy.get("version") != POLICY_VERSION or policy.get("mode") != POLICY_MODE:
        raise GateError(
            f"unsupported policy in {candidate}: expected version={POLICY_VERSION}, "
            f"mode={POLICY_MODE}"
        )
    owner = policy.get("owner")
    if not isinstance(owner, dict):
        raise GateError(f"policy lacks owner object: {candidate}")
    login = owner.get("login")
    owner_id = owner.get("id")
    owner_type = owner.get("type")
    if not isinstance(login, str) or not login or not isinstance(owner_id, int):
        raise GateError(f"policy owner login/id invalid: {candidate}")
    if owner_type != "User":
        raise GateError(f"policy owner type must be User, got {owner_type!r}")
    if set(policy) != {"version", "mode", "owner"}:
        raise GateError(f"policy fields drifted: {candidate}")
    return policy, candidate


# --------------------------------------------------------------------------
# snapshot: one shape for live GitHub and for offline replay in tests
# --------------------------------------------------------------------------


def fetch_snapshot(
    repository: str,
    policy: dict[str, Any] | None = None,
    pull_number: int | None = None,
) -> dict[str, Any]:
    """Read live repository identity and the PR set for the active authority mode."""
    repo = _gh_json(
        [
            "api",
            f"repos/{repository}",
            "--jq",
            "{full_name:.full_name,node_id:.node_id,owner:{login:.owner.login,id:.owner.id,type:.owner.type},permissions:.permissions}",
        ],
        {},
    )
    if not repo.get("owner", {}).get("login"):
        raise GateError(f"could not read the owner of {repository}")
    viewer = _gh_json(["api", "user", "--jq", "{login:.login,id:.id,type:.type}"], {})
    fields = "id,number,url,title,state,isDraft,headRefOid,mergeable,mergeStateStatus"
    if pull_number is not None:
        pull = _gh_json(
            [
                "pr",
                "view",
                str(pull_number),
                "--repo",
                repository,
                "--json",
                fields,
            ],
            {},
        )
        if not pull:
            raise GateError(f"could not read PR #{pull_number} in {repository}")
        pulls = [pull]
    else:
        pull_args = [
            "pr",
            "list",
            "--repo",
            repository,
            "--state",
            "open",
        ]
        if policy is None:
            pull_args += ["--label", ADMIT_LABEL]
        pull_args += ["--json", fields]
        pulls = _gh_json(pull_args, [])
    for pull in pulls:
        head = pull["headRefOid"]
        pull["head_committed_at"] = _gh_json(
            [
                "api",
                f"repos/{repository}/commits/{head}",
                "--jq",
                "{d:.commit.committer.date}",
            ],
            {},
        ).get("d")
        if policy is None:
            pull["admit"] = _gh_json(
                [
                    "api",
                    f"repos/{repository}/issues/{pull['number']}/events",
                    "--paginate",
                    "--jq",
                    f'[.[]|select(.event=="labeled" and .label.name=="{ADMIT_LABEL}")]'
                    "|last|{actor:.actor.login,at:.created_at}",
                ],
                None,
            )
    return {
        "repo": repository,
        "canonical_repo": repo.get("full_name"),
        "repository_node_id": repo.get("node_id"),
        "owner": repo["owner"],
        "viewer": viewer,
        "permissions": repo.get("permissions", {}),
        "pulls": pulls,
    }


def load_snapshot(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateError(f"unreadable snapshot: {path}: {error}") from error
    for field in ("repo", "owner", "pulls"):
        if field not in value:
            raise GateError(f"snapshot lacks '{field}': {path}")
    return value


def select_pulls(
    pulls: list[dict[str, Any]], pull_number: int | None
) -> list[dict[str, Any]]:
    """Return the explicitly requested PR, or preserve the all-PR scope."""
    if pull_number is None:
        return pulls
    selected = [pull for pull in pulls if pull.get("number") == pull_number]
    if len(selected) != 1:
        raise GateError(
            f"PR #{pull_number} must appear exactly once in the active snapshot; "
            f"found {len(selected)}"
        )
    return selected


# --------------------------------------------------------------------------
# L1 human admit
# --------------------------------------------------------------------------


def check_admit(pull: dict[str, Any], owner: str) -> str | None:
    """Return a refusal reason, or None when the human admit holds."""
    admit = pull.get("admit")
    if not isinstance(admit, dict) or not admit.get("actor"):
        return f"no `{ADMIT_LABEL}` label event -- nobody admitted this PR"
    if admit["actor"] != owner:
        return (
            f"`{ADMIT_LABEL}` applied by {admit['actor']}, not repository owner {owner}"
        )
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


def owner_login(snapshot: dict[str, Any]) -> str:
    owner = snapshot.get("owner")
    return str(owner.get("login", "")) if isinstance(owner, dict) else str(owner)


def check_owner_policy(snapshot: dict[str, Any], policy: dict[str, Any]) -> str | None:
    """Prove that this is the configured user's personal repository.

    Admin permission alone is deliberately insufficient: collaborators and
    organization owners can have admin while the repository is not personally
    owned by the configured GitHub User.
    """
    expected = policy["owner"]
    owner = snapshot.get("owner")
    viewer = snapshot.get("viewer")
    if not isinstance(owner, dict) or not isinstance(viewer, dict):
        return "snapshot lacks structured repository owner/viewer identity"
    if owner.get("type") != "User":
        return f"repository owner type is {owner.get('type')!r}, not personal User"
    for field in ("login", "id"):
        if owner.get(field) != expected[field]:
            return (
                f"repository owner {field}={owner.get(field)!r} does not match "
                f"configured owner {expected[field]!r}"
            )
        if viewer.get(field) != expected[field]:
            return (
                f"authenticated viewer {field}={viewer.get(field)!r} does not match "
                f"configured owner {expected[field]!r}"
            )
    canonical = snapshot.get("canonical_repo")
    requested = snapshot.get("repo")
    if canonical and str(canonical).lower() != str(requested).lower():
        return (
            f"repository redirected from {requested} to {canonical}; use canonical name"
        )
    if snapshot.get("permissions", {}).get("admin") is not True:
        return "authenticated owner does not have repository admin permission"
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


_SHELL_VAR = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")


def _repo_root_or_cwd() -> Path:
    done = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    top = done.stdout.strip()
    return Path(top) if done.returncode == 0 and top else Path.cwd()


def _hook_env() -> dict[str, str]:
    """The environment a host really gives its hooks, not this process's.

    Claude Code sets CLAUDE_PROJECT_DIR on every hook invocation, and hook
    commands are written against it. Probing without it made a repo-relative
    hook resolve to `/`; python exited 2 on the missing file, and exit 2 IS the
    blocking contract -- so a hook that CRASHED was reported as a hook that
    REFUSED, and preflight died on a policy decision nobody had made.
    """
    env = os.environ.copy()
    env.setdefault("CLAUDE_PROJECT_DIR", str(_repo_root_or_cwd()))
    return env


def _unresolvable_vars(command: str, env: dict[str, str]) -> list[str]:
    """Variables the hook command needs that this probe cannot supply.

    Checked BEFORE running, because afterwards the two are indistinguishable: an
    interpreter that cannot open its script exits 2, and so does a hook that
    deliberately refuses.

    The tempting discriminator -- probe with a benign command and call it broken
    if that is refused too -- is wrong. Deny-by-default hooks are legitimate and
    common (the tail of a real auto-approve.sh refuses anything not allowlisted),
    so "it refused something harmless" carries no information about breakage.
    An unset variable does, and it is decidable without running anything.
    """
    return sorted({name for name in _SHELL_VAR.findall(command) if name not in env})


def _run_pretooluse(
    commands: list[str], merge_cmd: list[str]
) -> tuple[str, str] | None:
    """Return a refusal or an un-evaluable gate, or None when nothing blocks."""
    if not commands:
        return None
    env = _hook_env()
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
        missing = _unresolvable_vars(command, env)
        if missing:
            return "ERROR", (
                f"{command}: references {', '.join('$' + m for m in missing)}, "
                "unset here -- this gate could NOT be evaluated, which is not the "
                "same as it refusing"
            )
        done = subprocess.run(
            ["bash", "-c", command],
            input=payload,
            capture_output=True,
            text=True,
            env=env,
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
            'network; define a profile extending ":workspace" with '
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
# L3 GitHub
# --------------------------------------------------------------------------


def check_github(pull: dict[str, Any], allow_unstable: bool) -> str | None:
    if "state" in pull and pull.get("state") != "OPEN":
        return f"state={pull.get('state')} -- PR is not open"
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
    value = _gh(
        ["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]
    ).strip()
    if REPO_RE.fullmatch(value) is None:
        raise GateError(f"could not resolve a GitHub repository from {os.getcwd()}")
    return value


def _install_owner_rule(policy: dict[str, Any], rules_dir: Path) -> Path:
    rule = rules_dir / f"github-merge-owner-{policy['owner']['login']}.rules"
    if shutil.which("codex") is None:
        print(f"SKIP    execpolicy rule: codex not on PATH ({rule.name})")
        return rule
    if rule.is_file():
        probe = subprocess.run(
            [
                "codex",
                "execpolicy",
                "check",
                "--rules",
                str(rule),
                "--",
                "python3",
                str(Path(__file__).resolve()),
                "land",
                "--repo",
                f"{policy['owner']['login']}/future-repository",
            ],
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0 and "allow" in probe.stdout.lower():
            print(f"OK      owner execpolicy rule already installed: {rule}")
            return rule
        print(f"REPAIR  owner execpolicy rule is unreadable or does not allow: {rule}")
    installer = Path(__file__).resolve().parent / "install-codex-merge-rule.sh"
    done = subprocess.run(
        [
            "bash",
            str(installer),
            "--owner",
            policy["owner"]["login"],
            "--gate",
            str(Path(__file__).resolve()),
            "--rules-dir",
            str(rules_dir),
        ],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        raise GateError(f"install-codex-merge-rule.sh failed: {done.stderr.strip()}")
    print(f"CREATED owner execpolicy rule: {rule} (restart Codex to load it)")
    return rule


def configure_owner(owner: str, policy_path: Path, rules_dir: Path) -> int:
    """Create the immutable user-identity policy from the live GitHub viewer."""
    viewer = _gh_json(["api", "user", "--jq", "{login:.login,id:.id,type:.type}"], {})
    if viewer.get("login") != owner:
        raise GateError(
            f"authenticated GitHub viewer is {viewer.get('login')!r}, not {owner!r}"
        )
    if viewer.get("type") != "User" or not isinstance(viewer.get("id"), int):
        raise GateError(f"authenticated viewer is not a stable GitHub User: {viewer}")
    policy = {
        "version": POLICY_VERSION,
        "mode": POLICY_MODE,
        "owner": {"login": owner, "id": viewer["id"], "type": "User"},
    }
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    if policy_path.exists():
        shutil.copy2(policy_path, policy_path.with_suffix(policy_path.suffix + ".bak"))
    fd, raw_temporary = tempfile.mkstemp(
        prefix=f".{policy_path.name}.", dir=policy_path.parent
    )
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(policy, stream, indent=2, sort_keys=True)
            stream.write("\n")
        temporary.chmod(0o600)
        temporary.replace(policy_path)
    finally:
        if temporary.exists():
            temporary.unlink()
    _install_owner_rule(policy, rules_dir)
    print(f"CONFIGURED owner-auto policy for {owner} ({viewer['id']}) at {policy_path}")
    return 0


def bootstrap(
    repository: str,
    rules_dir: Path,
    allow_unstable: bool,
    policy: dict[str, Any] | None,
    policy_path: Path | None,
) -> int:
    """Make one repository ready for this mechanism. Idempotent: safe to re-run.

    Only the two per-repository pieces live here. Everything else -- the skill
    itself, both hosts' PreToolUse blacklists, the Codex sandbox profile -- is
    user-level and already applies to every project without per-repo work.
    """
    if policy is not None:
        _install_owner_rule(policy, rules_dir)
        print("SKIP    merge-admit label: owner-auto policy is active")
        print(f"--- preflight {repository} ---")
        return preflight(repository, None, allow_unstable, policy, policy_path, None)

    labels = _gh_json(
        ["label", "list", "-R", repository, "--search", ADMIT_LABEL, "--json", "name"],
        [],
    )
    if any(label.get("name") == ADMIT_LABEL for label in labels):
        print(f"OK      label `{ADMIT_LABEL}` already exists in {repository}")
    else:
        _gh(
            [
                "label",
                "create",
                ADMIT_LABEL,
                "-R",
                repository,
                "-c",
                "0E8A16",
                "-d",
                "owner admits this PR for agent landing",
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
            [
                "bash",
                str(installer),
                "--repo",
                repository,
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

    print(f"--- preflight {repository} ---")
    return preflight(repository, None, allow_unstable, None, None, None)


def merge_command(
    repository: str, pull: dict[str, Any], policy: dict[str, Any] | None
) -> list[str]:
    number = pull["number"]
    head = pull["headRefOid"]
    if policy is not None:
        pull_id = pull.get("id")
        if not isinstance(pull_id, str) or not pull_id:
            raise GateError(f"PR #{number} lacks GraphQL node id")
        return [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={MERGE_MUTATION}",
            "-f",
            f"pullRequestId={pull_id}",
            "-f",
            f"expectedHeadOid={head}",
        ]
    return [
        "gh",
        "pr",
        "merge",
        "--repo",
        repository,
        str(number),
        "--squash",
        "--match-head-commit",
        head,
    ]


def probe_command(
    repository: str,
    pull: dict[str, Any],
    policy: dict[str, Any] | None,
    policy_path: Path | None,
    pull_number: int | None,
) -> list[str]:
    if policy is None:
        return merge_command(repository, pull, None)
    command = [
        "python3",
        str(Path(__file__).resolve()),
        "land",
        "--repo",
        repository,
    ]
    if policy_path is not None and policy_path != default_policy_path():
        command += ["--policy", str(policy_path)]
    if pull_number is not None:
        command += ["--pr", str(pull_number)]
    return command


def preflight(
    repository: str,
    snapshot_path: Path | None,
    allow_unstable: bool,
    policy: dict[str, Any] | None,
    policy_path: Path | None,
    pull_number: int | None,
) -> int:
    snapshot = (
        load_snapshot(snapshot_path)
        if snapshot_path
        else fetch_snapshot(repository, policy, pull_number)
    )
    if snapshot["repo"] != repository:
        raise GateError(f"snapshot repo {snapshot['repo']} != --repo {repository}")
    pulls = select_pulls(snapshot["pulls"], pull_number)
    ready: list[dict[str, Any]] = []
    blocked = 0
    owner_reason = check_owner_policy(snapshot, policy) if policy else None
    if owner_reason and not pulls:
        blocked = 1
        print(f"BLOCK {repository} [L1 OWNER-IDENTITY] {owner_reason}", file=sys.stderr)
    for pull in sorted(pulls, key=lambda item: item["number"]):
        head = str(pull.get("headRefOid", ""))[:7]
        admit_reason = owner_reason
        if policy is None:
            admit_reason = check_admit(pull, owner_login(snapshot))
        reason = admit_reason or check_github(pull, allow_unstable and policy is None)
        layer = (
            "L1 OWNER-IDENTITY"
            if policy is not None and admit_reason
            else "L1 HUMAN-ADMIT"
            if admit_reason
            else "L3 GITHUB"
        )
        if reason:
            blocked += 1
            print(f"BLOCK #{pull['number']} {head} [{layer}] {reason}", file=sys.stderr)
        else:
            ready.append(pull)
            print(f"READY #{pull['number']} {head} {pull.get('title', '')[:60]}")

    # The host probe runs even with nothing admitted: knowing which layer will
    # refuse is worth most *before* the work starts, not after.
    sample = (ready or pulls or [{"number": 1, "headRefOid": "0" * 40}])[0]
    probe_cmd = probe_command(repository, sample, policy, policy_path, pull_number)
    host = active_host()
    host_blocked = False
    host_unevaluable = False
    for name, (verdict, detail) in (
        ("claude-code", probe_claude_code(probe_cmd)),
        ("codex", probe_codex(repository, probe_cmd)),
    ):
        marker = "<-- active" if name == host else ""
        loud = verdict in ("BLOCK", "ERROR") and name == host
        print(
            f"L2 HOST-POLICY {name}: {verdict} -- {detail} {marker}".rstrip(),
            file=sys.stderr if loud else sys.stdout,
        )
        if name == host and verdict == "BLOCK":
            host_blocked = True
        if name == host and verdict == "ERROR":
            host_unevaluable = True

    # Un-evaluable is its own exit, for the same reason NO-ADMIT is: folding it
    # into "refused" sends someone to widen a permission that was never narrow.
    # The repair here is to the PROBE or the hook config, not to any policy.
    if host_unevaluable:
        print(
            f"UNEVALUABLE L2 HOST-POLICY on {host}; nothing merged and nothing "
            "refused -- fix the hook configuration, not a permission.",
            file=sys.stderr,
        )
        return UNEVALUABLE
    if host_blocked:
        print(f"REFUSED by L2 HOST-POLICY on {host}; nothing merged.", file=sys.stderr)
        return 1
    if blocked:
        print(f"REFUSED: {blocked} authorized PR(s) failed L1/L3.", file=sys.stderr)
        return 1
    if not ready:
        if policy is not None:
            print(f"NO-OPEN-PR {repository}: owner identity passed; no PR is open.")
        else:
            print(
                f"NO-ADMIT {repository}: no open PR carries the `{ADMIT_LABEL}` label."
            )
            print(
                f"  human admit = apply `{ADMIT_LABEL}` on GitHub (works from a phone)."
            )
        return NOT_READY
    print(f"PREFLIGHT GREEN: {len(ready)} PR(s) landable on {repository} via {host}")
    return 0


def land(
    repository: str,
    allow_unstable: bool,
    dry_run: bool,
    policy: dict[str, Any] | None,
    pull_number: int | None,
) -> int:
    """Merge the requested PR, or every admitted PR when no scope is given."""
    landed = 0
    while True:
        snapshot = fetch_snapshot(repository, policy, pull_number)
        owner_reason = check_owner_policy(snapshot, policy) if policy else None
        if owner_reason:
            print(
                f"REFUSED {repository} [L1 OWNER-IDENTITY] {owner_reason}",
                file=sys.stderr,
            )
            return 1
        pulls = select_pulls(snapshot["pulls"], pull_number)
        if pull_number is not None:
            pull = pulls[0]
            admit_reason = owner_reason
            if policy is None:
                admit_reason = check_admit(pull, owner_login(snapshot))
            reason = admit_reason or check_github(
                pull, allow_unstable and policy is None
            )
            if reason:
                layer = (
                    "L1 OWNER-IDENTITY"
                    if policy is not None and admit_reason
                    else "L1 HUMAN-ADMIT"
                    if admit_reason
                    else "L3 GITHUB"
                )
                print(
                    f"BLOCK #{pull_number} {str(pull.get('headRefOid', ''))[:7]} "
                    f"[{layer}] {reason}",
                    file=sys.stderr,
                )
                return 1
            pending = [pull]
        else:
            pending = [
                pull
                for pull in sorted(pulls, key=lambda item: item["number"])
                if (
                    policy is not None
                    or check_admit(pull, owner_login(snapshot)) is None
                )
                and check_github(pull, allow_unstable and policy is None) is None
            ]
        if not pending:
            break
        pull = pending[0]
        command = merge_command(repository, pull, policy)
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
        if pull_number is not None:
            break
    if landed == 0:
        marker = "NO-LANDABLE-PR" if policy is not None else "NO-ADMIT"
        print(f"{marker} {repository}: nothing was landable.")
        return NOT_READY
    print(f"LANDED={landed}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, helptext in (
        ("preflight", "probe every merge-authority layer without merging"),
        ("land", "merge authorized PRs, pinned to their checked head SHA"),
        (
            "bootstrap",
            "make one repository ready for the active authority mode; idempotent",
        ),
    ):
        sub = commands.add_parser(name, help=helptext)
        sub.add_argument(
            "--repo", help="OWNER/REPO; defaults to the current directory's remote"
        )
        sub.add_argument(
            "--policy",
            type=Path,
            help="owner-auto policy; defaults to ~/.config/github-delivery-loop/merge-policy.json when present",
        )
        sub.add_argument("--allow-unstable", action="store_true")
        if name == "preflight":
            sub.add_argument("--snapshot", type=Path, help="offline replay; no network")
            sub.add_argument(
                "--pr",
                type=positive_pull_number,
                help="evaluate only this pull request",
            )
        elif name == "land":
            sub.add_argument("--dry-run", action="store_true")
            sub.add_argument(
                "--pr", type=positive_pull_number, help="merge only this pull request"
            )
        else:
            sub.add_argument(
                "--rules-dir", type=Path, default=Path.home() / ".codex" / "rules"
            )
    configure = commands.add_parser(
        "configure-owner",
        help="bind owner-auto mode to the authenticated immutable GitHub User",
    )
    configure.add_argument("--owner", required=True, help="personal GitHub login")
    configure.add_argument("--policy", type=Path, default=default_policy_path())
    configure.add_argument(
        "--rules-dir", type=Path, default=Path.home() / ".codex" / "rules"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "configure-owner":
            return configure_owner(args.owner, args.policy, args.rules_dir)
        policy, policy_path = load_policy(args.policy)
        repository = args.repo or detect_repository()
        if REPO_RE.fullmatch(repository) is None:
            print(
                f"FAIL --repo must be OWNER/REPOSITORY: {repository}", file=sys.stderr
            )
            return 64
        if args.command == "preflight":
            return preflight(
                repository,
                args.snapshot,
                args.allow_unstable,
                policy,
                policy_path,
                args.pr,
            )
        if args.command == "bootstrap":
            return bootstrap(
                repository,
                args.rules_dir,
                args.allow_unstable,
                policy,
                policy_path,
            )
        return land(repository, args.allow_unstable, args.dry_run, policy, args.pr)
    except GateError as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
