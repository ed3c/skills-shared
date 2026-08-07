"""L0 thin step loop with injected execution."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any
from uuid import uuid4

from .envelope import make_envelope
from .gates import L3Config, L3State, l3_after_record, l3_preflight, l4_after_record
from .ledger import Ledger

Executor = Callable[[dict[str, Any]], dict[str, Any]]


def run_loop(
    *,
    task_packet: dict[str, Any],
    steps: Iterable[dict[str, Any]],
    ledger: Ledger,
    executor: Executor,
    l3_config: L3Config | None = None,
    parent_id: str | None = None,
    git_commit_sha: str | None = None,
) -> int:
    """Run deterministic L0 loop steps and return a deterministic exit code."""

    config = l3_config or L3Config()
    state, previous_id = ledger.rebuild_l3_state(config)
    if previous_id is None:
        previous_id = parent_id
    elif parent_id is not None and parent_id != previous_id:
        raise ValueError("parent_id does not match ledger tip")

    for step in steps:
        preflight = l3_preflight(state, config)
        if not preflight.allowed:
            return preflight.exit_code

        attempts = _resolve_max_attempts(task_packet, step)
        for attempt in range(1, attempts + 1):
            try:
                result = executor(step)
            except Exception as exc:
                result = {
                    "command": step.get("tool"),
                    "exit_code": 1,
                    "result_snapshot": None,
                    "error_snapshot": {"type": type(exc).__name__, "message": str(exc), "attempt": attempt},
                    "event_kind": "tool_error",
                    "handoff": {"next_action": "handled"} if attempt < attempts else None,
                }

            record = _make_record(
                task_packet=task_packet,
                step=step,
                result=result,
                state=state,
                previous_id=previous_id,
                git_commit_sha=git_commit_sha,
                attempt=attempt,
                attempts=attempts,
            )
            ledger.append(record)
            previous_id = record["id"]

            l4 = l4_after_record(record)
            if not l4.allowed:
                return l4.exit_code

            l3 = l3_after_record(state, config, record)
            if not l3.allowed:
                return l3.exit_code

            if record["exec"]["exit_code"] == 0:
                break

    return 0


def _resolve_max_attempts(task_packet: dict[str, Any], step: dict[str, Any]) -> int:
    raw = step.get("max_attempts", step.get("maxAttempts", task_packet.get("max_attempts", task_packet.get("maxAttempts", 1))))
    attempts = int(raw)
    if attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    return attempts


def _make_record(
    *,
    task_packet: dict[str, Any],
    step: dict[str, Any],
    result: dict[str, Any],
    state: L3State,
    previous_id: str | None,
    git_commit_sha: str | None,
    attempt: int,
    attempts: int,
) -> dict[str, Any]:
    record_id = result.get("id") or str(uuid4())
    budget_delta = result.get("budget") or {}
    cumulative_budget = {
        "tokens_used": state.total_tokens + int(budget_delta.get("tokens_used", 0)),
        "usd": state.total_usd + float(budget_delta.get("usd", 0.0)),
    }
    event_args = dict(step.get("args", {}))
    event_args["attempt"] = attempt
    event_args["max_attempts"] = attempts
    return make_envelope(
        id=record_id,
        parentId=previous_id,
        loop_layer="L0",
        task_ref={
            "packet_id": task_packet.get("packet_id"),
            "priority": task_packet.get("priority"),
            "passes": bool(result.get("passes", False)),
        },
        event={
            "kind": result.get("event_kind", "tool_result"),
            "tool": step.get("tool"),
            "args": event_args,
        },
        exec={
            "command": result.get("command", step.get("tool")),
            "exit_code": int(result.get("exit_code", 0)),
            "result_snapshot": result.get("result_snapshot"),
            "error_snapshot": result.get("error_snapshot"),
        },
        handoff=result.get("handoff"),
        budget=cumulative_budget,
        freshness={"git_commit_sha": git_commit_sha, "fact_stale": bool(result.get("fact_stale", False))},
    )
