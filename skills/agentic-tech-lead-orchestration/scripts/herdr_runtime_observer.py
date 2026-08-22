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
    if "herdr_session" in data and (not isinstance(data["herdr_session"], str) or not data["herdr_session"].strip()):
        raise ContractError("herdr_session must be non-empty string")
    if "expected_agent_session_source" in data and (not isinstance(data["expected_agent_session_source"], str) or not data["expected_agent_session_source"].strip()):
        raise ContractError("expected_agent_session_source must be non-empty string")
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


def _run(argv: list[str], session: str | None = None) -> dict[str, Any]:
    if session:
        argv = [argv[0], "--session", session, *argv[1:]]
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
    # Fail closed on herdr's error envelope. Observed 2026-08-22 on herdr 0.8.0:
    # a failing command exits NON-zero and writes {"id":..,"error":{code,message}}
    # to stderr, so the returncode branch above already catches it. This check
    # covers the shape the frozen contract was never tested against - an error
    # envelope arriving on stdout with exit 0 - rather than an observed failure.
    if isinstance(value, dict) and isinstance(value.get("error"), dict):
        raise ContractError(
            "Herdr returned an error envelope: "
            f"{value['error'].get('code')}: {value['error'].get('message')}"
        )
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
    """herdr 0.8.0 publishes the native session only as AgentSessionInfo.value.

    The former `agent_session_id`/`sessionId`/`id` fallbacks named fields that
    exist on no herdr surface; keeping them was the #466 defect in miniature.
    """
    session = _find(agent, "agent_session", "agentSession")
    if isinstance(session, dict):
        value = session.get("value")
        if value not in (None, ""):
            return value
    return None


def _freshness(agent: dict[str, Any], explain: dict[str, Any], now: int) -> tuple[int, str]:
    """Return (source_observed_at_unix, observation_time_source).

    herdr 0.8.0 publishes no wall clock on AgentInfo or `agent explain` (verified:
    `herdr api schema --json`, AgentInfo has 22 properties, none a timestamp). When no
    herdr clock is present the observer stamps its own and the receipt SAYS SO; freshness
    then rests on the observer having taken the sample itself, and ordering rests on the
    herdr-published monotonic state_change_seq.
    """
    names = (
        "observed_at_unix", "observedAtUnix", "updated_at_unix", "updatedAtUnix",
        "last_seen_at_unix", "lastSeenAtUnix",
    )
    value = _find(explain, *names)
    if value in (None, ""):
        value = _find(agent, *names)
    if value not in (None, ""):
        return _positive_int(value, "Herdr source observation timestamp"), "HERDR_SOURCE_CLOCK"
    return now, "OBSERVER_LOCAL_CLOCK"


def _state_change_seq(agent: dict[str, Any]) -> int:
    value = _find(agent, "state_change_seq", "stateChangeSeq")
    if value in (None, ""):
        value = _find(agent, "revision")
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ContractError("herdr state_change_seq/revision must be a non-negative integer")
    return value


def _ps_process(pid: int) -> tuple[bool, int | None]:
    """OS_AUXILIARY. herdr 0.8.0 publishes no liveness flag and no process start time."""
    proc = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], text=True, capture_output=True)
    text = proc.stdout.strip()
    if proc.returncode or not text:
        return False, None
    return True, int(time.mktime(time.strptime(text, "%a %b %d %H:%M:%S %Y")))


def _derive_cleanup(process_info: dict[str, Any] | None) -> tuple[str, int]:
    """OBSERVER_DERIVED. herdr 0.8.0 publishes no cleanup_state/residue_count."""
    if not isinstance(process_info, dict):
        raise ContractError("terminal state requires pane.process_info to derive residue")
    foreground = _find(process_info, "foreground_processes") or []
    return ("CLEAN", 0) if not foreground else ("DIRTY", len(foreground))


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
    process_info: dict[str, Any] | None = None,
    *,
    now_unix: int | None = None,
) -> dict[str, Any]:
    validate_manifest(data)
    now = int(time.time()) if now_unix is None else _positive_int(now_unix, "now_unix")

    raw_state = _find(explain, "final_state", "state") or _find(agent, "agent_status", "agentStatus", "state", "status") or "unknown"
    raw_state = str(raw_state).lower()
    mapped = STATES.get(raw_state, "UNKNOWN")

    pane = _find(agent, "pane_id", "paneId") or _find(explain, "pane_id", "paneId")
    workspace = _find(agent, "workspace_id", "workspaceId") or _find(explain, "workspace_id", "workspaceId")
    process = _find(agent, "process_id", "processId", "pid")
    process_facts_source = "HERDR_AGENT_SURFACE" if process not in (None, "") else "NOT_OBSERVED"
    if process in (None, ""):
        process = _find(process_info, "pid") if process_info else None
        if process not in (None, ""):
            process_facts_source = "HERDR_PANE_PROCESS_INFO_PLUS_OS_PS"
    foreground_cwd = _find(agent, "foreground_cwd", "foregroundCwd")
    native_session = _native_session_id(agent)
    session_source = _find(agent, "agent_session", "agentSession")
    session_source = session_source.get("source") if isinstance(session_source, dict) else None
    source_observed_at, observation_time_source = _freshness(agent, explain, now)
    state_change_seq = _state_change_seq(agent)
    process_alive = _process_alive(agent, explain)
    process_started_at = _process_started_at(agent, explain)
    if process_facts_source == "HERDR_PANE_PROCESS_INFO_PLUS_OS_PS" and process not in (None, ""):
        alive_os, started_os = _ps_process(int(process))
        if process_alive is None:
            process_alive = alive_os
        if process_started_at is None:
            process_started_at = started_os
    cleanup_state, residue_count = _cleanup(agent, explain)
    cleanup_source = "HERDR_PUBLISHED" if cleanup_state not in (None, "") else "NOT_OBSERVED"
    if cleanup_state in (None, "") and mapped == "DONE_CANDIDATE":
        cleanup_state, residue_count = _derive_cleanup(process_info)
        cleanup_source = "OBSERVER_DERIVED_PANE_PROCESS_INFO"

    # Shadow O5: staleness/future rejects may only anchor on a clock the OBSERVER
    # DID NOT PRODUCE. When observation_time_source is OBSERVER_LOCAL_CLOCK,
    # source_observed_at IS `now`, so comparing them proves nothing; ordering and
    # freshness then rest on herdr's own monotonic state_change_seq, which
    # collect_herdr_lifecycle checks across the sample sequence.
    if observation_time_source == "HERDR_SOURCE_CLOCK":
        if source_observed_at > now:
            raise ContractError("Herdr source observation timestamp is in the future")
        observation_age = now - source_observed_at
        if observation_age > data["max_observation_age_seconds"]:
            raise ContractError(
                f"Herdr observation is stale: age={observation_age}s "
                f"max={data['max_observation_age_seconds']}s"
            )
    else:
        observation_age = 0

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

    expected_source = data.get("expected_agent_session_source")
    if expected_source is not None and str(expected_source) != str(session_source):
        raise ContractError(
            f"agent_session.source mismatch: expected {expected_source!r}, observed {session_source!r}"
            " — a manually reported agent is not lifecycle evidence"
        )

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
        "agent_session_source": session_source,
        "foreground_cwd": foreground_cwd,
        "source_observed_at_unix": source_observed_at,
        "observed_at_unix": now,
        "observation_age_seconds": observation_age,
        "state_change_seq": state_change_seq,
        "observation_time_source": observation_time_source,
        "process_facts_source": process_facts_source,
        "cleanup_source": cleanup_source,
        "cleanup_state": cleanup_state,
        "residue_count": residue_count,
        "raw_state": raw_state,
        "observer_state": mapped,
        "herdr_available": True,
        "authoritative": False,
        "controller_readback_required": True,
        "evidence_ceiling": "OBSERVER_IDENTITY_FRESHNESS_CLEANUP_WITH_TYPED_AUXILIARY",
    }


def observe(data: dict[str, Any]) -> dict[str, Any]:
    validate_manifest(data)
    if shutil.which("herdr") is None:
        return fallback_receipt(data)
    session = data.get("herdr_session")
    agent = _run(["herdr", "agent", "get", data["target"]], session)
    explain = _run(["herdr", "agent", "explain", data["target"], "--json"], session)
    if not isinstance(agent, dict) or not isinstance(explain, dict):
        raise ContractError("Herdr observer expects object-shaped agent/explain JSON")
    pane = _find(agent, "pane_id", "paneId")
    process_info = _run(["herdr", "pane", "process-info", "--pane", str(pane)], session) if pane else None
    return reduce_observation(data, agent, explain, process_info)


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
