#!/usr/bin/env python3
"""Validate the portable Local Handoff Execution Queue contract."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = ROOT / "references" / "example-local-handoff-queue.json"
SHA40 = set("0123456789abcdef")
ALLOWED_STATES = {"ACTIVE", "BLOCKED_BY_PREDECESSOR", "COMPLETE"}
EVIDENCE_STATES = {"PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED", "SKIPPED_BY_POLICY", "HUMAN_ADMIT_REQUIRED"}
FORBIDDEN_AUTOMATION = {"merge", "force_push", "issue_close", "queue_advance", "provider_activation", "semantic_conflict_resolution"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("queue root must be an object")
    return value


def is_sha40(value: object) -> bool:
    text = str(value)
    return len(text) == 40 and all(ch in SHA40 for ch in text)


def validate(queue: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if queue.get("schema_version") != "agentic-tech-lead/local-handoff-queue/v1":
        errors.append("schema_version drifted")
    subject = queue.get("subject", {})
    for key in ("commit", "tree", "rollback_commit"):
        if not is_sha40(subject.get(key)):
            errors.append(f"subject.{key} must be exact SHA-40")
    if not subject.get("repository"):
        errors.append("subject.repository missing")

    authority = queue.get("authority", {})
    automation_forbidden = set(authority.get("automation_forbidden", []))
    if not FORBIDDEN_AUTOMATION.issubset(automation_forbidden):
        errors.append("automation authority widened")
    if not authority.get("human_owned"):
        errors.append("human_owned authority missing")

    items = queue.get("items")
    if not isinstance(items, list) or not items:
        return errors + ["items must be a non-empty array"]
    ids = [str(item.get("id")) for item in items if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("duplicate item id")
    item_by_id = {str(item.get("id")): item for item in items if isinstance(item, dict)}
    active = [item for item in items if isinstance(item, dict) and item.get("state") == "ACTIVE"]
    if len(active) != 1:
        errors.append("exactly one ACTIVE item is required")
    current = queue.get("current", {})
    if current.get("state") != "ACTIVE":
        errors.append("current.state must be ACTIVE")
    if len(active) == 1 and current.get("active_item") != active[0].get("id"):
        errors.append("current.active_item does not match ACTIVE item")

    seen_complete: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"items[{index}] must be an object")
            continue
        item_id = str(item.get("id"))
        state = item.get("state")
        if state not in ALLOWED_STATES:
            errors.append(f"{item_id}: invalid state")
        entry = item.get("entry", {})
        if entry.get("required_subject_commit") != subject.get("commit"):
            errors.append(f"{item_id}: stale required subject")
        predecessor = entry.get("predecessor")
        if predecessor is not None:
            if predecessor not in item_by_id:
                errors.append(f"{item_id}: unknown predecessor")
            elif state in {"ACTIVE", "COMPLETE"} and predecessor not in seen_complete:
                errors.append(f"{item_id}: executable before predecessor COMPLETE")
        if not isinstance(entry.get("required_capabilities", []), list):
            errors.append(f"{item_id}: required_capabilities must be array")

        runtime = item.get("runtime_lane", {})
        commands = runtime.get("commands", [])
        unresolved = runtime.get("unresolved_operations", [])
        if not isinstance(commands, list) or not isinstance(unresolved, list):
            errors.append(f"{item_id}: commands/unresolved_operations must be arrays")
            commands, unresolved = [], []
        if not commands and not unresolved:
            errors.append(f"{item_id}: no command or unresolved operation lane")
        for operation in unresolved:
            if not isinstance(operation, dict) or not operation.get("operation_id") or not operation.get("resolver_source") or operation.get("required_output") != "CONCRETE_COMMAND_CONTRACT":
                errors.append(f"{item_id}: unresolved operation contract invalid")
        if unresolved and state == "COMPLETE":
            errors.append(f"{item_id}: unresolved operation cannot be COMPLETE")
        for command in commands:
            argv = command.get("argv", []) if isinstance(command, dict) else []
            if not argv or any("REPLACE_WITH_" in str(arg) or "PLACEHOLDER" in str(arg) for arg in argv):
                errors.append(f"{item_id}: placeholder or empty command")
            if not isinstance(command, dict) or not command.get("cwd") or int(command.get("timeout_seconds", 0) or 0) <= 0:
                errors.append(f"{item_id}: command execution bounds missing")

        receipt = item.get("receipt", {})
        if not receipt.get("path") or not receipt.get("schema"):
            errors.append(f"{item_id}: durable receipt contract missing")
        required_states = set(receipt.get("required_states", []))
        if not required_states or not required_states.issubset(EVIDENCE_STATES):
            errors.append(f"{item_id}: invalid evidence states")
        if not receipt.get("forbidden_promotions", []):
            errors.append(f"{item_id}: evidence promotion guard missing")
        if runtime.get("live_evidence_required") is True and "PASS" not in required_states:
            errors.append(f"{item_id}: live lane has no PASS receipt state")

        exit_contract = item.get("exit", {})
        if exit_contract.get("requires_receipt") is not True or exit_contract.get("required_verdict") != "PASS":
            errors.append(f"{item_id}: exit must require validated PASS receipt")
        next_id = item.get("next")
        if next_id is not None and next_id not in item_by_id:
            errors.append(f"{item_id}: next item unknown")
        if next_id is not None and index + 1 < len(items) and items[index + 1].get("id") != next_id:
            errors.append(f"{item_id}: next item skips queue order")
        if state == "COMPLETE":
            seen_complete.add(item_id)
    return errors


def selftest(queue: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    base = copy.deepcopy(queue)
    items = base.get("items")
    if isinstance(items, list) and len(items) == 1 and isinstance(items[0], dict):
        # A schema-valid queue may hold a single item (one-item epochs occur when
        # the active handoff mutates the subject before the next queue can be
        # compiled). The two-active and successor-early controls need a second
        # item, so synthesize a bounded successor inside the selftest only.
        first = items[0]
        successor = copy.deepcopy(first)
        successor["id"] = f"{first.get('id')}-selftest-successor"
        successor["state"] = "BLOCKED_BY_PREDECESSOR"
        successor.setdefault("entry", {})["predecessor"] = first.get("id")
        successor["next"] = None
        first["next"] = successor["id"]
        items.append(successor)
        sanity = validate(base)
        if sanity:
            return [f"selftest successor synthesis broke queue validity: {e}" for e in sanity]
    cases = []
    def add(name: str, mutate, needle: str) -> None: cases.append((name, mutate, needle))
    add("two active", lambda q: q["items"][1].__setitem__("state", "ACTIVE"), "one ACTIVE")
    add("stale subject", lambda q: q["items"][0]["entry"].__setitem__("required_subject_commit", "f" * 40), "stale required subject")
    add("successor early", lambda q: q["items"][1].__setitem__("state", "ACTIVE"), "predecessor COMPLETE")
    add("missing lane", lambda q: (q["items"][0]["runtime_lane"].__setitem__("commands", []), q["items"][0]["runtime_lane"].__setitem__("unresolved_operations", [])), "no command or unresolved")
    add("placeholder", lambda q: q["items"][0]["runtime_lane"]["commands"][0].__setitem__("argv", ["REPLACE_WITH_COMMAND"]), "placeholder")
    add("authority widened", lambda q: q["authority"].__setitem__("automation_forbidden", ["merge"]), "authority widened")
    add("receipt missing", lambda q: q["items"][0]["receipt"].__setitem__("path", ""), "receipt contract missing")
    add("promotion guard missing", lambda q: q["items"][0]["receipt"].__setitem__("forbidden_promotions", []), "promotion guard missing")
    add("exit laundering", lambda q: q["items"][0]["exit"].__setitem__("required_verdict", "NOT_EXERCISED"), "validated PASS")
    add("skip next", lambda q: q["items"][0].__setitem__("next", q["items"][0]["id"]), "skips queue order")
    add("unresolved complete", lambda q: (q["items"][0]["runtime_lane"].__setitem__("unresolved_operations", [{"operation_id":"resolve-x","resolver_source":"consumer manifest","required_output":"CONCRETE_COMMAND_CONTRACT"}]), q["items"][0].__setitem__("state", "COMPLETE"), q["items"][1].__setitem__("state", "ACTIVE"), q["current"].__setitem__("active_item", q["items"][1]["id"])), "unresolved operation cannot be COMPLETE")
    for name, mutate, needle in cases:
        candidate = copy.deepcopy(base); mutate(candidate); found = validate(candidate)
        if not any(needle.lower() in error.lower() for error in found): failures.append(f"control did not turn red: {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE); parser.add_argument("--selftest", action="store_true"); args = parser.parse_args()
    try: queue = load(args.queue)
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr); return 64
    errors = selftest(queue) if args.selftest else validate(queue)
    if errors:
        for error in errors: print(f"FAIL: {error}")
        return 2
    print("SELFTEST GREEN: Local Handoff Execution Queue controls" if args.selftest else f"PASS: Local Handoff Execution Queue ({len(queue['items'])} item(s), active={queue['current']['active_item']})")
    return 0

if __name__ == "__main__": raise SystemExit(main())
