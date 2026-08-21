#!/usr/bin/env python3
"""Optional, non-authoritative Herdr runtime observer.

The adapter reduces Herdr JSON to identity, freshness, liveness, and cleanup
facts. It never promotes terminal UI state to implementation acceptance and
never persists terminal transcript, credentials, or private reasoning.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

STATES = {
    "working": "RUNNING",
    "running": "RUNNING",
    "blocked": "BLOCKED",
    "idle": "IDLE",
    "done": "DONE_CANDIDATE",
    "completed": "DONE_CANDIDATE",
    "unknown": "UNKNOWN",
}
FORBIDDEN = (
    "api_key", "apikey", "token", "credential", "secret",
    "reasoning", "transcript", "visible_text", "screen_text",
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
REPO_ID = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class ContractError(ValueError):
    pass


def _keys(value: Any, prefix: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path.lower()
            yield from _keys(child, path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _keys(child, f"{prefix}[{index}]")


def _positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ContractError(f"{label} must be a positive integer")
    return value


def validate_manifest(data: dict[str, Any]) -> None:
    required = {
        "task_id", "attempt_id", "repo", "base_sha", "tree_sha", "worktree",
        "target", "max_observation_age_seconds",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ContractError("missing required fields: " + ", ".join(missing))

    for field in ("task_id", "attempt_id", "worktree", "target"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise ContractError(f"{field} must be non-empty string")
    if not isinstance(data["repo"], str) or not REPO_ID.fullmatch(data["repo"]):
        raise ContractError("repo must be exact owner/name")
    if not isinstance(data["base_sha"], str) or not HEX40.fullmatch(data["base_sha"]):
        raise ContractError("base_sha must be an exact 40-hex Git commit")
    if not isinstance(data["tree_sha"], str) or not HEX40.fullmatch(data["tree_sha"]):
        raise ContractError("tree_sha must be an exact 40-hex Git tree")
    _positive_int(data["max_observation_age_seconds"], "max_observation_age_seconds")

    if data.get("authoritative") is True:
        raise ContractError("Herdr observer can never be authoritative")
    for field in (
        "require_foreground_cwd", "require_process_liveness", "require_clean_terminal"
    ):
        if field in data and not isinstance(data[field], bool):
            raise ContractError(f"{field} must be boolean")
    if "expected_process_started_at_unix" in data:
        _positive_int(data["expected_process_started_at_unix"], "expected_process_started_at_unix")

    for key in _keys(data):
        leaf = key.rsplit(".", 1)[-1].replace("-", "_")
        if any(fragment in leaf for fragment in FORBIDDEN):
            raise ContractError(f"forbidden durable field: {key}")


def fallback_receipt(data: dict[str, Any]) -> dict[str, Any]:
    validate_manifest(data)
    return {
        "schema_version": 1,
        "task_id": data["task_id"],
        "attempt_id": data["attempt_id"],
        "repo": data["repo"],
        "base_sha": data["base_sha"],
        "tree_sha": data["tree_sha"],
        "worktree": data["worktree"],
        "target": data["target"],
        "observer_state": "UNAVAILABLE_FALLBACK",
        "herdr_available": False,
        "authoritative": False,
        "controller_readback_required": True,
        "evidence_ceiling": "NO_HERDR_OBSERVATION",
    }


def _run(argv: list[str]) -> dict[str, Any]:
    process = subprocess.run(argv, text=True, capture_output=True)
    if process.returncode:
        raise ContractError(
            f"Herdr command failed ({process.returncode}): {process.stderr.strip()}"
        )
    try:
        value = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise ContractError(f"Herdr did not return JSON: {exc}") from exc
    if not isinstance(value, (dict, list)):
        raise ContractError("Herdr JSON root must be object/array")
    return value


def _find(value: Any, *names: str):
    wanted = set(names)
    if isinstance(value, dict):
        for key, child in value.items():
            if key in wanted and child not in (None, ""):
                return child
        for child in value.values():
            found = _find(child, *names)
            if found not in (None, ""):
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find(child, *names)
            if found not in (None, ""):
                return found
    return None


def _native_session_id(agent: dict[str, Any]):
    session = _find(agent, "agent_session", "agentSession")
    if isinstance(session, dict):
        value = (
            session.get("value")
            or session.get("id")
            or session.get("session_id")
            or session.get("sessionId")
        )
        if value not in (None, ""):
            return value
    return _find(agent, "agent_session_id", "agentSessionId")


def _observed_at(agent: dict[str, Any], explain: dict[str, Any]) -> int:
    names = (
        "observed_at_unix", "observedAtUnix", "updated_at_unix", "updatedAtUnix",
        "last_seen_at_unix", "lastSeenAtUnix",
    )
    value = _find(explain, *names)
    if value in (None, ""):
        value = _find(agent, *names)
    return _positive_int(value, "Herdr source observation timestamp")


def _process_alive(agent: dict[str, Any], explain: dict[str, Any]) -> bool | None:
    value = _find(agent, "process_alive", "processAlive", "alive")
    if value in (None, ""):
        value = _find(explain, "process_alive", "processAlive", "alive")
    if value in (None, ""):
        return None
    if not isinstance(value, bool):
        raise ContractError("process_alive must be boolean when reported")
    return value


def _process_started_at(agent: dict[str, Any], explain: dict[str, Any]) -> int | None:
    names = (
        "process_started_at_unix", "processStartedAtUnix", "started_at_unix", "startedAtUnix",
    )
    value = _find(agent, *names)
    if value in (None, ""):
        value = _find(explain, *names)
    if value in (None, ""):
        return None
    return _positive_int(value, "process_started_at_unix")


def _cleanup(agent: dict[str, Any], explain: dict[str, Any]) -> tuple[str | None, int | None]:
    state = _find(explain, "cleanup_state", "cleanupState")
    if state in (None, ""):
        state = _find(agent, "cleanup_state", "cleanupState")
    count = _find(explain, "residue_count", "residueCount")
    if count in (None, ""):
        count = _find(agent, "residue_count", "residueCount")
    if state not in (None, ""):
        state = str(state).strip().upper()
        if state not in {"CLEAN", "DIRTY", "NOT_APPLICABLE"}:
            raise ContractError(f"unsupported cleanup_state: {state}")
    if count not in (None, ""):
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ContractError("residue_count must be a non-negative integer")
    return state, count


def reduce_observation(
    data: dict[str, Any],
    agent: dict[str, Any],
    explain: dict[str, Any],
    *,
    now_unix: int | None = None,
) -> dict[str, Any]:
    validate_manifest(data)
    now = int(time.time()) if now_unix is None else _positive_int(now_unix, "now_unix")

    raw_state = _find(explain, "final_state", "state") or _find(agent, "state", "status") or "unknown"
    raw_state = str(raw_state).lower()
    mapped = STATES.get(raw_state, "UNKNOWN")

    pane = _find(agent, "pane_id", "paneId") or _find(explain, "pane_id", "paneId")
    workspace = _find(agent, "workspace_id", "workspaceId") or _find(explain, "workspace_id", "workspaceId")
    process = _find(agent, "process_id", "processId", "pid")
    foreground_cwd = _find(agent, "foreground_cwd", "foregroundCwd")
    native_session = _native_session_id(agent)
    source_observed_at = _observed_at(agent, explain)
    process_alive = _process_alive(agent, explain)
    process_started_at = _process_started_at(agent, explain)
    cleanup_state, residue_count = _cleanup(agent, explain)

    if source_observed_at > now:
        raise ContractError("Herdr source observation timestamp is in the future")
    observation_age = now - source_observed_at
    if observation_age > data["max_observation_age_seconds"]:
        raise ContractError(
            f"Herdr observation is stale: age={observation_age}s "
            f"max={data['max_observation_age_seconds']}s"
        )

    require_cwd = data.get("require_foreground_cwd", True)
    if require_cwd and foreground_cwd in (None, ""):
        raise ContractError("Herdr observation lacks foreground_cwd; cannot bind agent to worktree")
    if foreground_cwd not in (None, ""):
        if Path(str(foreground_cwd)).resolve() != Path(data["worktree"]).resolve():
            raise ContractError(
                f"foreground_cwd/worktree mismatch: observed {foreground_cwd!r}, "
                f"expected {data['worktree']!r}"
            )

    for field, expected, actual in (
        ("pane_id", data.get("expected_pane_id"), pane),
        ("workspace_id", data.get("expected_workspace_id"), workspace),
        ("process_id", data.get("expected_process_id"), process),
        ("agent_session_id", data.get("expected_agent_session_id"), native_session),
    ):
        if expected is not None and str(expected) != str(actual):
            raise ContractError(f"{field} mismatch: expected {expected!r}, observed {actual!r}")

    expected_started = data.get("expected_process_started_at_unix")
    if expected_started is not None:
        if process_started_at is None:
            raise ContractError("process_started_at_unix missing; cannot reject PID reuse")
        if process_started_at != expected_started:
            raise ContractError(
                f"process_started_at_unix mismatch: expected {expected_started!r}, "
                f"observed {process_started_at!r}"
            )

    if mapped != "DONE_CANDIDATE" and data.get("require_process_liveness", True):
        if process_alive is not True:
            raise ContractError("nonterminal Herdr observation lacks a live process; orphan session refused")

    if mapped == "DONE_CANDIDATE" and data.get("require_clean_terminal", True):
        if cleanup_state != "CLEAN" or residue_count != 0:
            raise ContractError(
                "terminal Herdr state requires cleanup_state=CLEAN and residue_count=0"
            )

    return {
        "schema_version": 1,
        "task_id": data["task_id"],
        "attempt_id": data["attempt_id"],
        "repo": data["repo"],
        "base_sha": data["base_sha"],
        "tree_sha": data["tree_sha"],
        "worktree": data["worktree"],
        "target": data["target"],
        "pane_id": pane,
        "workspace_id": workspace,
        "process_id": process,
        "process_started_at_unix": process_started_at,
        "process_alive": process_alive,
        "agent_session_id": native_session,
        "foreground_cwd": foreground_cwd,
        "source_observed_at_unix": source_observed_at,
        "observed_at_unix": now,
        "observation_age_seconds": observation_age,
        "cleanup_state": cleanup_state,
        "residue_count": residue_count,
        "raw_state": raw_state,
        "observer_state": mapped,
        "herdr_available": True,
        "authoritative": False,
        "controller_readback_required": True,
        "evidence_ceiling": "OBSERVER_IDENTITY_FRESHNESS_CLEANUP_ONLY",
    }


def observe(data: dict[str, Any]) -> dict[str, Any]:
    validate_manifest(data)
    if shutil.which("herdr") is None:
        return fallback_receipt(data)
    agent = _run(["herdr", "agent", "get", data["target"]])
    explain = _run(["herdr", "agent", "explain", data["target"], "--json"])
    if not isinstance(agent, dict) or not isinstance(explain, dict):
        raise ContractError("Herdr observer expects object-shaped agent/explain JSON")
    return reduce_observation(data, agent, explain)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--output")
    args = parser.parse_args()
    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    receipt = observe(data)
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
