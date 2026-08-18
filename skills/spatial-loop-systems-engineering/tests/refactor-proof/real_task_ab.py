#!/usr/bin/env python3
"""Run one matched hermetic task against every frozen treatment of this Skill.

The task is the smallest thing this Skill actually owns end to end: given a
repair trajectory against one invariant, decide whether a fourth patch is
allowed, and gate that decision on the persisted system contract. Every arm gets
the identical inputs -- the same committed contract fixture, the same attempts
fixture, the same live `scripts/check_system_contract.py` run both as a CLI
subprocess and as an imported library -- and one attempt each. No network, no
model, no clock in the receipt.

The arms differ only in what their frozen body can tell an executor:

    A, B1, B2  define a qualifying failed attempt and name the states that are
               not one, so the trajectory resolves to BOUNDED_RETRY (two
               qualifying failures, not three) and all three produce the same
               receipt identity
    B0         says "three consecutive qualifying failures" with the definition
               deleted. It cannot decide the question, so it is retained as
               BLOCKED_QUALIFYING_RULE_ABSENT with the exact missing tokens
               rather than being dropped or credited with a guess

B0 stays in the denominator. A blocked arm that disappears from the count is the
failure mode this whole loop exists to refuse.

Exit: 0 every assertion held, 2 a named assertion failed, 64 unusable input.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

from refactor_ab import TREATMENTS, normalize, windows  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parents[2]
ATTEMPTS = "tests/refactor-proof/fixtures/attempts.json"
CONTRACT = "tests/system-contract/fixtures/good.json"
CHECKER = "scripts/check_system_contract.py"

PINNED = {
    ATTEMPTS: "1f0125cb5ce8068794747fb5eecbda402d336078",
    CONTRACT: "c5da95d5f6a667078b89a737f9f7d439ad8a6244",
}

# The states a treatment must exclude before its escalation counter is decidable.
NON_QUALIFYING = ["absent", "not_exercised", "skipped_by_policy"]

BOUNDED_RETRY = "BOUNDED_RETRY"
ESCALATE = "ESCALATION_REQUIRED"
BLOCKED = "BLOCKED_QUALIFYING_RULE_ABSENT"
ROUTE_ABSENT = "BLOCKED_CHECKER_ROUTE_ABSENT"


class TaskError(Exception):
    """Input could not be read at all. Not a task result."""


def blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def checker_route(body: str) -> bool:
    """Does this body route to its own deterministic contract checker?"""
    return bool(re.search(r"check_system_contract\.py\s+\\?\s*check", body))


def excluded_states(body: str) -> list[str]:
    """Which non-qualifying states does this body attach to its own counter?"""
    for window in windows(body, ["qualifying"], 700):
        found = [state for state in NON_QUALIFYING if state in window]
        if len(found) == len(NON_QUALIFYING):
            return found
    return []


def run_cli(checker: Path, contract: Path) -> int:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, str(checker), "check", str(contract)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    ).returncode


def run_library(checker: Path, contract: Path) -> int:
    """Same checker, called as a library, so a CLI-only wrapper cannot fake it."""
    spec = importlib.util.spec_from_file_location("_spatial_contract_checker", checker)
    if spec is None or spec.loader is None:
        raise TaskError(f"checker not importable: {checker}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return int(module.main([str(checker), "check", str(contract)]))


def promoted_gate(contract: Path, scratch: Path) -> Path:
    """The same contract with its gate promoted above its capability evidence.

    The old body stated this as a law in prose; the checker enforces it. One
    required capability is NOT_EXERCISED, so READY_FOR_IMPLEMENTATION must be
    refused. Every arm runs this identical negative control.
    """
    document = json.loads(contract.read_text(encoding="utf-8"))
    document["implementation_gate"]["status"] = "READY_FOR_IMPLEMENTATION"
    target = scratch / "promoted-gate-contract.json"
    target.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return target


def decide(attempts: dict, excluded: list[str]) -> tuple[str, int]:
    # The filter is the treatment's own rule, not this harness's opinion: only
    # the states its body excludes are dropped from the counter.
    qualifying = [
        row
        for row in attempts["attempts"]
        if row["subject_changed"] and row["oracle_result"].lower() not in excluded
    ]
    count = len(qualifying)
    decision = ESCALATE if count >= attempts["escalation_threshold"] else BOUNDED_RETRY
    return decision, count


def receipt(arm_result: dict) -> str:
    payload = json.dumps(
        {key: arm_result[key] for key in ("decision", "qualifying", "cli_rc", "library_rc")},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def run(root: Path, scratch: Path) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    for rel, pinned in PINNED.items():
        path = root / rel
        if not path.is_file():
            raise TaskError(f"task input absent: {rel}")
        actual = blob_sha(path)
        if actual != pinned:
            errors.append(f"TASK_INPUT_DRIFT {rel} {actual} != {pinned}")

    checker = root / CHECKER
    if not checker.is_file():
        raise TaskError(f"checker absent: {CHECKER}")
    contract = root / CONTRACT
    attempts = json.loads((root / ATTEMPTS).read_text(encoding="utf-8"))
    mutated = promoted_gate(contract, scratch)

    results: list[dict] = []
    for arm, role, rel, _pinned in TREATMENTS:
        path = root / rel
        if not path.is_file():
            raise TaskError(f"treatment absent: {rel}")
        body = normalize(path.read_text(encoding="utf-8"))
        result: dict = {"arm": arm, "role": role, "blocked": None}

        if not checker_route(body):
            result.update(blocked=ROUTE_ABSENT, missing=["check_system_contract.py check"])
            results.append(result)
            continue

        result["cli_rc"] = run_cli(checker, contract)
        result["library_rc"] = run_library(checker, mutated)

        excluded = excluded_states(body)
        if not excluded:
            result.update(
                blocked=BLOCKED,
                missing=[
                    state.upper()
                    for state in NON_QUALIFYING
                    if state not in " ".join(windows(body, ["qualifying"], 700))
                ],
            )
            results.append(result)
            continue

        decision, count = decide(attempts, excluded)
        result.update(decision=decision, qualifying=count, excluded=excluded)
        result["receipt"] = receipt(result)
        results.append(result)
    return results, errors


def assertions(results: list[dict]) -> list[str]:
    errors: list[str] = []
    if len(results) != len(TREATMENTS):
        errors.append(f"DENOMINATOR_INCOMPLETE {len(results)} != {len(TREATMENTS)}")

    closed = [row for row in results if row["blocked"] is None]
    blocked = [row for row in results if row["blocked"] is not None]

    if [row["arm"] for row in blocked] != ["B0_REFACTOR_AS_LANDED"]:
        errors.append(
            "UNEXPECTED_BLOCKED_SET " + ",".join(row["arm"] for row in blocked)
        )
    for row in blocked:
        if row["blocked"] != BLOCKED:
            errors.append(f"BLOCKED_REASON_UNEXPECTED {row['arm']}:{row['blocked']}")
        if not row.get("missing"):
            errors.append(f"BLOCKED_WITHOUT_NAMED_GAP {row['arm']}")

    for row in closed:
        if row["decision"] != BOUNDED_RETRY:
            errors.append(f"WRONG_DECISION {row['arm']}:{row['decision']}")
        if row["qualifying"] != 2:
            errors.append(f"WRONG_QUALIFYING_COUNT {row['arm']}:{row['qualifying']}")
        if row["cli_rc"] != 0:
            errors.append(f"COMMITTED_CONTRACT_REFUSED {row['arm']}:{row['cli_rc']}")
        if row["library_rc"] != 2:
            errors.append(f"PROMOTED_GATE_ADMITTED {row['arm']}:{row['library_rc']}")

    receipts = {row["receipt"] for row in closed}
    if len(receipts) != 1:
        errors.append("RECEIPT_IDENTITY_SPLIT " + ",".join(sorted(receipts)))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", type=Path, default=SKILL_ROOT)
    args = parser.parse_args(argv)
    root = args.skill_root.resolve()
    scratch = Path(tempfile.mkdtemp(prefix="spatial-loop-ab-"))
    try:
        results, errors = run(root, scratch)
    except (TaskError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"REAL-TASK-AB-MECHANISM-RED {exc}", file=sys.stderr)
        return 64
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    if scratch.exists():
        errors.append(f"SCRATCH_RESIDUE {scratch}")
    errors.extend(assertions(results))

    for row in results:
        if row["blocked"] is not None:
            print(f"{row['arm']} {row['blocked']} missing={','.join(row['missing'])}")
        else:
            print(
                f"{row['arm']} {row['decision']} qualifying={row['qualifying']}/3 "
                f"cli={row['cli_rc']} library={row['library_rc']} receipt={row['receipt']}"
            )
    if errors:
        for error in errors:
            print(f"REAL-TASK-AB-RED {error}", file=sys.stderr)
        return 2
    closed = [row for row in results if row["blocked"] is None]
    print(
        f"REAL-TASK-AB-GREEN arms={len(results)} closed={len(closed)} "
        f"blocked={len(results) - len(closed)} retained in denominator; "
        "one attempt each, zero network, scratch removed; "
        "fixture evidence only, no live model or runtime claim"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
