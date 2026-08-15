"""Shared vocabulary and strict validators for procedural grounding receipts."""
from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "procedural-grounding-receipt/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ID_PATTERNS = {
    "source": re.compile(r"^SRC-[A-Z0-9][A-Z0-9-]*$"),
    "procedure": re.compile(r"^PROC-[A-Z0-9][A-Z0-9-]*$"),
    "observation": re.compile(r"^OBS-[A-Z0-9][A-Z0-9-]*$"),
    "fork": re.compile(r"^FORK-[A-Z0-9][A-Z0-9-]*$"),
    "capsule": re.compile(r"^CAP-[A-Z0-9][A-Z0-9-]*$"),
    "obligation": re.compile(r"^OBL-[A-Z0-9][A-Z0-9-]*$"),
}
RUNTIMES = {"CHATGPT_GITHUB_CONNECTOR", "GITHUB_ACTIONS", "CLAUDE_CODE_LOCAL", "CODEX_CLI_LOCAL", "CHATGPT_DESKTOP_WORKTREE", "UNKNOWN"}
CHECKPOINT_SEQUENCE = ["SKILL_DISCOVERY", "ARCHITECTURE_CHOICE", "FIRST_VERTICAL_SLICE", "NOVELTY_OR_DIVERGENCE", "FIRST_GREEN", "BEFORE_COMMIT", "BEFORE_PR_OR_PUBLICATION"]
CHECKPOINTS = set(CHECKPOINT_SEQUENCE)
CHECKPOINT_RANK = {name: index for index, name in enumerate(CHECKPOINT_SEQUENCE)}
PROOF_MODES = {"TEXT_ONLY", "STATIC_ARTIFACT", "EXECUTION_REQUIRED", "NEGATIVE_CONTROL_REQUIRED", "EXTERNAL_OR_HUMAN"}
CRITICALITIES = {"CRITICAL", "IMPORTANT", "ADVISORY"}
NOVELTIES = {"MODEL_PRIOR_LIKELY", "SKILL_SPECIFIC", "ENVIRONMENT_SPECIFIC", "UNKNOWN"}
ATOM_KINDS = {"DECISION", "PRECONDITION", "ACTION", "ASSERTION", "EVIDENCE", "RECOVERY", "PROHIBITION", "RESOURCE"}
ABSTRACTION_LEVELS = {"L0_EXACT_PROCEDURE", "L1_MECHANISM", "L2_INVARIANT", "L3_EXECUTABLE_ORACLE", "L4_TRANSFER_CAPSULE", "L5_META_CANDIDATE"}
UPTAKE_STATES = {"UNPROVEN", "DISCOVERED", "MENTIONED", "PLANNED", "HARNESS_ENCODED", "EXECUTED", "ASSERTED", "OBSERVED", "NEGATIVE_CONTROL_PASSED"}
UPTAKE_RANK = {"UNPROVEN": 0, "DISCOVERED": 1, "MENTIONED": 2, "PLANNED": 3, "HARNESS_ENCODED": 4, "ASSERTED": 5, "EXECUTED": 6, "OBSERVED": 7, "NEGATIVE_CONTROL_PASSED": 8}
MENTIONED_STATES = UPTAKE_STATES - {"UNPROVEN", "DISCOVERED"}
HARNESS_STATES = {"HARNESS_ENCODED", "ASSERTED", "EXECUTED", "OBSERVED", "NEGATIVE_CONTROL_PASSED"}
EXECUTION_STATES = {"EXECUTED", "OBSERVED", "NEGATIVE_CONTROL_PASSED"}
EVIDENCE_STATES = {"OBSERVED", "NEGATIVE_CONTROL_PASSED"}
MODALITIES = {"MODEL_OUTPUT", "SOURCE_DIFF", "STATIC_ARTIFACT", "TERMINAL", "TEST_REPORT", "TRACE_OR_LOG", "BROWSER_DOM", "ACCESSIBILITY_TREE", "SCREENSHOT", "VIDEO", "DEVICE", "DATABASE", "NETWORK", "EXTERNAL_STATE", "HUMAN_RECEIPT"}
FORK_MODES = {"IN_PROCESS_LOGICAL", "SEPARATE_CONTEXT", "SEPARATE_MODEL", "EXTERNAL_DETERMINISTIC_CHECKER"}
STOP_REASONS = {"COVERAGE_TARGET_REACHED", "CRITICAL_GAP_CLOSED", "NO_PROGRESS_LIMIT", "TOKEN_BUDGET", "DEPTH_BUDGET", "FORK_BUDGET", "BLOCKED_AUTHORITY", "BLOCKED_EVIDENCE"}
PAYLOAD_KINDS = {"ACTIONABLE_DELTA", "ASSERTION_PATCH", "PROBE_PLAN", "BLOCKER"}
INJECTION_DECISIONS = {"INJECTED", "REJECTED"}
OBLIGATION_STATES = {"OPEN", "SATISFIED", "BLOCKED"}
EVIDENCE_VOCABULARY = {"PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED", "SKIPPED_BY_POLICY"}
ATTRIBUTION_CONDITIONS = ["NO_SKILL", "METADATA_ONLY", "FULL_SKILL", "FULL_SKILL_PLUS_GROUNDING"]

class ContractError(Exception):
    """Semantic contract failure."""

def fail(message: str) -> None:
    raise ContractError(message)

def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)

def require_dict(value: Any, path: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{path} must be an object")
    return value

def require_list(value: Any, path: str) -> list[Any]:
    require(isinstance(value, list), f"{path} must be an array")
    return value

def require_str(value: Any, path: str, *, nonempty: bool = True) -> str:
    require(isinstance(value, str), f"{path} must be a string")
    if nonempty:
        require(bool(value.strip()), f"{path} must be non-empty")
    return value

def require_bool(value: Any, path: str) -> bool:
    require(isinstance(value, bool), f"{path} must be a boolean")
    return value

def require_int(value: Any, path: str, *, minimum: int | None = None) -> int:
    require(isinstance(value, int) and not isinstance(value, bool), f"{path} must be an integer")
    if minimum is not None:
        require(value >= minimum, f"{path} must be >= {minimum}")
    return value

def require_number(value: Any, path: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{path} must be numeric")
    number = float(value)
    require(math.isfinite(number), f"{path} must be finite")
    if minimum is not None:
        require(number >= minimum, f"{path} must be >= {minimum}")
    if maximum is not None:
        require(number <= maximum, f"{path} must be <= {maximum}")
    return number

def require_enum(value: Any, allowed: set[str], path: str) -> str:
    text = require_str(value, path)
    require(text in allowed, f"{path} has unsupported value {text!r}")
    return text

def require_hex(value: Any, pattern: re.Pattern[str], path: str) -> str:
    text = require_str(value, path)
    require(bool(pattern.fullmatch(text)), f"{path} must match {pattern.pattern}")
    return text

def require_id(value: Any, kind: str, path: str) -> str:
    text = require_str(value, path)
    require(bool(ID_PATTERNS[kind].fullmatch(text)), f"{path} has invalid {kind} id {text!r}")
    return text

def require_keys(obj: dict[str, Any], required: Iterable[str], path: str) -> None:
    required_set = set(required)
    missing = sorted(required_set - set(obj))
    extra = sorted(set(obj) - required_set)
    require(not missing, f"{path} is missing required fields: {', '.join(missing)}")
    require(not extra, f"{path} contains unsupported fields: {', '.join(extra)}")

def require_unique(items: list[dict[str, Any]], key: str, path: str) -> None:
    seen: set[str] = set()
    for index, item in enumerate(items):
        value = require_str(item.get(key), f"{path}[{index}].{key}")
        require(value not in seen, f"{path} contains duplicate {key} {value}")
        seen.add(value)

def require_timestamp(value: Any, path: str) -> str:
    text = require_str(value, path)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        fail(f"{path} must be ISO-8601: {exc}")
    require(parsed.tzinfo is not None, f"{path} must include a timezone")
    return text

def approx_equal(left: float, right: float, tolerance: float = 1e-6) -> bool:
    return abs(left - right) <= tolerance

def parse_contract(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        raise SystemExit(64) from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"INPUT ERROR: invalid JSON: {exc}", file=sys.stderr)
        raise SystemExit(64) from exc
    if not isinstance(data, dict):
        print("INPUT ERROR: root must be an object", file=sys.stderr)
        raise SystemExit(64)
    return data

def strongest_state(observations: list[dict[str, Any]], procedure_id: str) -> str:
    states = [obs["uptake_state"] for obs in observations if obs["procedure_id"] == procedure_id]
    return max(states, key=UPTAKE_RANK.__getitem__) if states else "UNPROVEN"

def proof_satisfied(atom: dict[str, Any], state: str) -> bool:
    mode = atom["proof_mode"]
    if mode == "TEXT_ONLY":
        return state in MENTIONED_STATES
    if mode == "STATIC_ARTIFACT":
        return state in HARNESS_STATES
    if mode == "EXECUTION_REQUIRED":
        return state in {"EXECUTED", "OBSERVED"}
    if mode == "NEGATIVE_CONTROL_REQUIRED":
        return state == "NEGATIVE_CONTROL_PASSED"
    return False
