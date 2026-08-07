"""Deterministic L3/L4 gates for the MVP loop."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class L3Config:
    max_iterations: int = 8
    max_tokens: int | None = None
    max_usd: float | None = None
    duplicate_threshold: int = 3
    duplicate_window: int = 8
    max_interleaving: int = 3

    def __post_init__(self) -> None:
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        if self.duplicate_threshold < 2:
            raise ValueError("duplicate_threshold must be >= 2")
        if self.duplicate_window < self.max_interleaving:
            raise ValueError("duplicate_window must be >= max_interleaving")


@dataclass
class L3State:
    iterations: int = 0
    total_tokens: int = 0
    total_usd: float = 0.0
    signatures: deque[str] = field(default_factory=deque)
    signature_counts: Counter[str] = field(default_factory=Counter)
    pending_exit_code: int = 0
    pending_reason: str | None = None


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    exit_code: int
    reason: str | None = None


def l3_preflight(state: L3State, config: L3Config) -> GateDecision:
    if state.pending_exit_code:
        return GateDecision(False, state.pending_exit_code, state.pending_reason)
    if state.iterations >= config.max_iterations:
        return GateDecision(False, 10, "max_iterations")
    return GateDecision(True, 0)


def l3_after_record(state: L3State, config: L3Config, record: dict[str, Any]) -> GateDecision:
    signature = _apply_record_state(state, config, record)
    budget_hit = _budget_exceeded(state, config)
    dup_hit = _duplicate_hit(state, config, signature)
    max_hit = state.iterations >= config.max_iterations

    if budget_hit:
        return _set_pending_stop(state, 20, "budget")
    if dup_hit:
        return _set_pending_stop(state, 21, "dup")
    if max_hit:
        return _set_pending_stop(state, 10, "max_iterations")
    return GateDecision(True, 0)


def l4_after_record(record: dict[str, Any]) -> GateDecision:
    if _deterministic_failure(record):
        return GateDecision(False, 30, "l4_unhandled_exec_failure")
    if _is_proxy_warning(record):
        return GateDecision(True, 0, "proxy_warning")
    return GateDecision(True, 0)


def sig_with_result(record: dict[str, Any]) -> str:
    payload = {
        "command": record["exec"]["command"],
        "event_args": record["event"].get("args"),
        "result_snapshot": record["exec"]["result_snapshot"],
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _budget_exceeded(state: L3State, config: L3Config) -> bool:
    if config.max_tokens is not None and state.total_tokens >= config.max_tokens:
        return True
    if config.max_usd is not None and state.total_usd >= config.max_usd:
        return True
    return False


def _duplicate_hit(state: L3State, config: L3Config, signature: str) -> bool:
    return state.signature_counts[signature] >= config.duplicate_threshold


def _handoff_handled(record: dict[str, Any]) -> bool:
    next_action = record["handoff"].get("next_action")
    return next_action in {"handled", "stop", "escalate"}


def _deterministic_failure(record: dict[str, Any]) -> bool:
    return record["exec"]["exit_code"] != 0 and not _handoff_handled(record)


def _is_proxy_warning(record: dict[str, Any]) -> bool:
    return record["event"].get("kind") in {"judge_warning", "proxy_warning"}


def _apply_record_state(state: L3State, config: L3Config, record: dict[str, Any]) -> str:
    state.iterations += 1
    state.total_tokens = int(record["budget"]["tokens_used"])
    state.total_usd = float(record["budget"]["usd"])
    signature = sig_with_result(record)
    state.signatures.append(signature)
    state.signature_counts[signature] += 1
    # duplicate_window counts allowed interleaving steps, so retain the
    # current record plus that many prior signatures in the active scope.
    while len(state.signatures) > config.duplicate_window + 1:
        evicted = state.signatures.popleft()
        state.signature_counts[evicted] -= 1
        if state.signature_counts[evicted] == 0:
            del state.signature_counts[evicted]
    return signature


def _set_pending_stop(state: L3State, exit_code: int, reason: str) -> GateDecision:
    state.pending_exit_code = exit_code
    state.pending_reason = reason
    return GateDecision(False, exit_code, reason)
