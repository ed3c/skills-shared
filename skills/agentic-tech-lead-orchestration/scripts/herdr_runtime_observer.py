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
    if observation_aeHˆ]VÈ›X^ÛØœÙ\˜][Û—ØYÙWÜÙXÛÛ™È—N‚ˆ˜Z\ÙHÛÛ˜Xİ\œ›ÜŠˆˆœİ[H\™ˆØœÙ\˜][ÛˆYÙO^ÛØœÙ\˜][Û—ØYÙ_\È‚ˆˆ›[Z]^Ù]VÉÛX^ÛØœÙ\˜][Û—ØYÙWÜÙXÛÛ™É×_\È‚ˆ
B‚ˆ™\]Z\™WØİÙH]K™Ù]
œ™\]Z\™WÙ›Ü™YÜ›İ[™ØİÙ‹YJBˆYˆ™\]Z\™WØİÙ[™›Ü™YÜ›İ[™ØİÙ[ˆ
›Û™KˆŠN‚ˆ˜Z\ÙHÛÛ˜Xİ\œ›ÜŠ’\™ˆØœÙ\˜][ÛˆXÚÜÈ›Ü™YÜ›İ[™ØİÙÈØ[››İš[™YÙ[ÈÛÜšİ™YHŠBˆYˆ›Ü™YÜ›İ[™ØİÙ›İ[ˆ
›Û™KˆŠN‚ˆYˆ]
İŠ›Ü™YÜ›İ[™ØİÙ
JKœ™\ÛÛ™J
HOH]
]VÈÛÜšİ™YH—JKœ™\ÛÛ™J
N‚ˆ˜Z\ÙHÛÛ˜Xİ\œ›ÜŠˆˆ™›Ü™YÜ›İ[™ØİÙİÛÜšİ™YHZ\ÛX]ÚˆØœÙ\™YÙ›Ü™YÜ›İ[™ØİÙ\ŸK‚ˆˆ™^XİYÙ]VÉİÛÜšİ™YI×H\ŸH‚ˆ
B‚ˆ›ÜˆšY[^XİYXİX[[ˆ
ˆ
œ[™WÚY‹]K™Ù]
™^XİYÜ[™WÚYŠK[™JKˆ
ÛÜšÜÜXÙWÚY‹]K™Ù]
™^XİYİÛÜšÜÜXÙWÚYŠKÛÜšÜÜXÙJKˆ
œ›ØÙ\Ü×ÚY‹]K™Ù]
™^XİYÜ›ØÙ\Ü×ÚYŠK›ØÙ\ÜÊKˆ
˜YÙ[ÜÙ\ÜÚ[Û—ÚY‹]K™Ù]
™^XİYØYÙ[ÜÙ\ÜÚ[Û—ÚYŠK˜]]™WÜÙ\ÜÚ[ÛŠKˆ
œ›ØÙ\Ü×Üİ\YØ]İ[š^‹]K™Ù]
™^XİYÜ›ØÙ\Ü×Üİ\YØ]İ[š^ŠK›ØÙ\Ü×Üİ\YØ]
Kˆ
N‚ˆYˆ^XİY\È›İ›Û™H[™İŠ^XİY
HOHİŠXİX[
N‚ˆ˜Z\ÙHÛÛ˜Xİ\œ›ÜŠˆÙšY[HZ\ÛX]Úˆ^XİYÙ^XİY\ŸKØœÙ\™YØXİX[\ŸHŠB‚ˆ™\]Z\™WÛ]™[™\ÜÈH]K™Ù]
œ™\]Z\™WÜ›ØÙ\Ü×Û]™[™\ÜÈ‹YJBˆYˆ™\]Z\™WÛ]™[™\ÜÈ[™X\Y[ˆÈ”•S“’S‘È‹“ĞÒÑQ‹’QHŸN‚ˆYˆ›ØÙ\Ü×Ø[]™H\È›İYN‚ˆYˆ˜]]™WÜÙ\ÜÚ[Ûˆ›İ[ˆ
›Û™KˆŠN‚ˆ˜Z\ÙHÛÛ˜Xİ\œ›ÜŠˆ›Üœ[ˆÙ\ÜÚ[Û‹Ü›ØÙ\ÜÈØœÙ\˜][Ûˆ›Û\›Z[˜[Ù\ÜÚ[Ûˆ\È›È]™H›ØÙ\ÜÈ‚ˆ
Bˆ˜Z\ÙHÛÛ˜Xİ\œ›ÜŠ››Û\›Z[˜[\™ˆØœÙ\˜][Ûˆ\È›È]™H›ØÙ\ÜÈŠB‚ˆ™\]Z\™WØÛX[—İ\›Z[˜[H]K™Ù]
œ™\]Z\™WØÛX[—İ\›Z[˜[‹YJBˆYˆX\YOH‘Ó‘WĞĞS‘QUHˆ[™™\]Z\™WØÛX[—İ\›Z[˜[‚ˆYˆÛX[\Üİ]HOHÓPSˆ‚ˆ˜Z\ÙHÛÛ˜Xİ\œ›ÜŠ‘Ó‘WĞĞS‘QUH™\]Z\™\ÈÛX[\Üİ]OPÓPSˆŠBˆYˆ™\ÚYYWØÛİ[OH‚ˆ˜Z\ÙHÛÛ˜Xİ\œ›ÜŠ‘Ó‘WĞĞS‘QUH™\]Z\™\È™\ÚYYWØÛİ[LŠB‚ˆ™]\›ˆÂˆœØÚ[XWİ™\œÚ[ÛˆˆKˆ\Ú×ÚYˆ]VÈ\Ú×ÚY—Kˆ˜][\ÚYˆ]VÈ˜][\ÚY—Kˆœ™\Èˆ]VÈœ™\È—Kˆ˜˜\ÙWÜÚHˆ]VÈ˜˜\ÙWÜÚH—Kˆ™YWÜÚHˆ]VÈ™YWÜÚH—KˆÛÜšİ™YHˆ]VÈÛÜšİ™YH—Kˆ\™Ù]ˆ]VÈ\™Ù]—Kˆœ[™WÚYˆ[™KˆÛÜšÜÜXÙWÚYˆÛÜšÜÜXÙKˆœ›ØÙ\Ü×ÚYˆ›ØÙ\ÜËˆœ›ØÙ\Ü×Üİ\YØ]İ[š^ˆ›ØÙ\Ü×Üİ\YØ]ˆœ›ØÙ\Ü×Ø[]™Hˆ›ØÙ\Ü×Ø[]™Kˆ˜YÙ[ÜÙ\ÜÚ[Û—ÚYˆ˜]]™WÜÙ\ÜÚ[Û‹ˆ™›Ü™YÜ›İ[™ØİÙˆ›Ü™YÜ›İ[™ØİÙˆœÛİ\˜ÙWÛØœÙ\™YØ]İ[š^ˆÛİ\˜ÙWÛØœÙ\™YØ]ˆ›ØœÙ\™YØ]İ[š^ˆ›İËˆ›ØœÙ\˜][Û—ØYÙWÜÙXÛÛ™ÈˆØœÙ\˜][Û—ØYÙKˆ˜ÛX[\Üİ]HˆÛX[\Üİ]Kˆœ™\ÚYYWØÛİ[ˆ™\ÚYYWØÛİ[ˆœ˜]×Üİ]Hˆ˜]×Üİ]Kˆ›ØœÙ\™\—Üİ]HˆX\Yˆš\™—Ø]˜Z[X›HˆYKˆ˜]]Üš]]]™Hˆ˜[ÙKˆ˜ÛÛ›Û\—Ü™XY˜XÚ×Ü™\]Z\™YˆYKˆ™]šY[˜ÙWØÙZ[[™Èˆ“Ğ”ÑT•‘T—ÒQS•UWÑ”‘TÒ‘TÔ×ĞÓPS•TÓÓ“H‹ˆB‚‚™YˆØœÙ\™J]NˆXİÜİ‹[WJHOˆXİÜİ‹[WN‚ˆ˜[Y]WÛX[šY™\İ
]JBˆYˆÚ][ÚXÚ
š\™ˆŠH\È›Û™N‚ˆ™]\›ˆ˜[˜XÚ×Ü™XÙZ\
]JBˆYÙ[HÜ[ŠÈš\™ˆ‹˜YÙ[‹™Ù]‹]VÈ\™Ù]—WJBˆ^Z[ˆHÜ[ŠÈš\™ˆ‹˜YÙ[‹™^Z[ˆ‹]VÈ\™Ù]—K‹KZœÛÛˆ—JBˆ™]\›ˆ™YXÙWÛØœÙ\˜][ÛŠ]KYÙ[^Z[ŠB‚‚™YˆXZ[Š
HOˆ[‚ˆ\œÙ\ˆH\™Ü\œÙK\™İ[Y[\œÙ\Š
Bˆ\œÙ\‹˜YØ\™İ[Y[
›X[šY™\İŠBˆ\œÙ\‹˜YØ\™İ[Y[
‹K[İ]]ŠBˆ\™ÜÈH\œÙ\‹œ\œÙWØ\™ÜÊ
Bˆ]HHœÛÛ‹›ØYÊ]
\™ÜË›X[šY™\İ
Kœ™XYİ^
[˜ÛÙ[™ÏH]‹NŠJBˆ™XÙZ\HØœÙ\™J]JBˆ^HœÛÛ‹™[\Ê™XÙZ\[™[L‹ÛÜÚÙ^\ÏUYJH
È—ˆ‚ˆYˆ\™ÜË›İ]]‚ˆ]
\™ÜË›İ]]
KÜš]Wİ^
^[˜ÛÙ[™ÏH]‹NŠBˆ[ÙN‚ˆš[
^[™HˆŠBˆ™]\›ˆ‚‚šYˆ×Û˜[YW×ÈOH—×ÛXZ[—×È‚ˆ˜Z\ÙHŞ\İ[Q^]
XZ[Š
JB