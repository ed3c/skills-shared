#!/usr/bin/env python3
"""Matched hermetic real-task A/B for the forge-delivery-loop treatments.

One task, run once per frozen treatment against the same exact inputs:

    subject          tests/issue-state/fixtures/request-valid.json, unmodified
    contracts        the three committed schemas under contracts/
    implementation   the live scripts/issue_state.py, called as a real CLI and
                     as a library with injected readers
    budget           one attempt per arm, no retries
    oracles          CLI validate exits 0; the readback chain yields a
                     schema-valid receipt whose clock-independent identity is
                     the same for every arm that reached it
    carrier          this process; no network, no forge, no credential read

An arm reaches the task only through what its own body routes to. That is the
whole point of the comparison: B0 still ships the same scripts, and an executor
holding only B0 cannot learn from it that a receipt needs a pre-observation
captured before the mutation. A route that exists on disk but not in the body
is the failure mode a green structural checker cannot see.

Every attempt stays in the denominator, including the blocked arm and every
planted mutation that was refused. Zero network by construction: the readers
are injected, so there is no code path that could reach a live forge.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from refactor_ab import EXPECTED_GIT_BLOBS, LANDED, OLD, git_blob_sha  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "SKILL.md"
REQUEST = ROOT / "tests" / "issue-state" / "fixtures" / "request-valid.json"
ISSUE_STATE = ROOT / "scripts" / "issue_state.py"
RECEIPT_SCHEMA = ROOT / "contracts" / "forgejo-issue-state-readback-receipt.v1.schema.json"
TASK_ID = "terminal-work-item-closure-v1"

# The ordered chain an arm has to name before it can drive the task. Naming the
# script alone is not the route: B0 lists the file and stops there.
CHAIN = ("scripts/issue_state.py", "capture-pre-live", "verify-live")


class TaskError(RuntimeError):
    pass


def load_issue_state():
    spec = importlib.util.spec_from_file_location("issue_state", ISSUE_STATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def readers(request: dict[str, Any]) -> tuple[Callable, Callable, Callable]:
    """Deterministic stand-ins for the three authenticated reads.

    They are the task's fixture surface and are labelled FIXTURE everywhere in
    the report. Nothing here may be reported as a live forge observation.
    """

    def issue(state: str) -> dict[str, Any]:
        return {
            "number": request["issue_number"],
            "state": state,
            "body": "Source: " + request["idempotency_marker"],
        }

    def source_reader(command: list[str], _name: str) -> dict[str, Any]:
        if "/issues/" in command[-1]:
            return {"html_url": request["source_receipt"]["issue_url"], "state": "closed"}
        return {
            "html_url": request["source_receipt"]["pull_request_url"],
            "merged_at": "2026-08-12T16:26:16Z",
            "merge_commit_sha": request["source_receipt"]["merge_sha"],
            "body": "Closes #50",
        }

    return issue, source_reader, lambda state: (lambda _request: issue(state))


def timeline_for(pre: dict[str, Any]) -> Callable:
    created = datetime.fromisoformat(pre["observed_at"]) + timedelta(seconds=1)
    return lambda _request: [
        {"type": "close", "created_at": created.isoformat(), "user": {"login": "neon"}}
    ]


def route_state(body: str) -> tuple[bool, list[str]]:
    missing = [token for token in CHAIN if token not in body]
    return (not missing), missing


def run_arm(name: str, body: str, module, request: dict[str, Any], scratch: Path) -> dict[str, Any]:
    reachable, missing = route_state(body)
    if not reachable:
        return {
            "arm": name,
            "route_reachable": False,
            "missing_route_tokens": missing,
            "execution_state": "BLOCKED_READBACK_ROUTE_ABSENT",
            "functional_output": "NOT_EXERCISED",
            "evidence_kind": "FIXTURE",
        }

    cli = subprocess.run(
        [sys.executable, str(ISSUE_STATE), "validate", "--request", str(REQUEST)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if cli.returncode != 0:
        raise TaskError(f"{name}: real CLI validate failed: {cli.stderr.strip()}")

    issue, source_reader, reader_for = readers(request)
    pre = module.capture_pre_live(request, reader_for("open"))
    receipt = module.verify_live(
        request, pre, reader_for("closed"),
        source_reader=source_reader, timeline_reader=timeline_for(pre),
    )
    if receipt["status"] != "verified":
        raise TaskError(f"{name}: readback chain did not verify")

    from jsonschema import Draft202012Validator, FormatChecker

    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(receipt)
    (scratch / f"{name}-receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    return {
        "arm": name,
        "route_reachable": True,
        "missing_route_tokens": [],
        "execution_state": "PASS",
        "functional_output": "PASS",
        "evidence_kind": "FIXTURE",
        "cli_validate_exit": cli.returncode,
        # observed_at and pre_observation_sha256 carry the clock, so the
        # identity compared across arms deliberately excludes them.
        "receipt_identity": {
            field: receipt[field]
            for field in (
                "request_sha256", "source_observation_sha256", "post_observation_sha256",
                "state", "idempotency_marker", "source_merge_sha", "maturity_effect",
            )
        },
    }


def planted_mutations(module, request: dict[str, Any]) -> dict[str, bool]:
    """The live gate has to be able to go red, or the arms' green means nothing."""
    _issue, source_reader, reader_for = readers(request)
    pre = module.capture_pre_live(request, reader_for("open"))
    timeline = timeline_for(pre)
    refused: dict[str, bool] = {}

    def refuses(label: str, run: Callable[[], Any]) -> None:
        try:
            run()
        except ValueError:
            refused[label] = True
        else:
            refused[label] = False

    hand_filled = copy.deepcopy(pre)
    hand_filled["producer"] = "operator-authored"
    refuses("hand_filled_observation", lambda: module.verify_live(
        request, hand_filled, reader_for("closed"),
        source_reader=source_reader, timeline_reader=timeline))

    wrong_repo = copy.deepcopy(pre)
    wrong_repo["repository"] = "neon/wrong"
    refuses("wrong_repository", lambda: module.verify_live(
        request, wrong_repo, reader_for("closed"),
        source_reader=source_reader, timeline_reader=timeline))

    refuses("no_authenticated_closure_event", lambda: module.verify_live(
        request, pre, reader_for("closed"),
        source_reader=source_reader, timeline_reader=lambda _request: []))

    refuses("post_state_never_changed", lambda: module.verify_live(
        request, pre, reader_for("open"),
        source_reader=source_reader, timeline_reader=timeline))

    no_op = copy.deepcopy(request)
    no_op["expected_state"] = no_op["desired_state"]
    refuses("no_op_transition", lambda: module.validate_request(no_op))
    return refused


def compare() -> dict[str, Any]:
    for path, expected in EXPECTED_GIT_BLOBS.items():
        if git_blob_sha(path.read_text(encoding="utf-8")) != expected:
            raise TaskError(f"frozen treatment drift {path.name}")

    module = load_issue_state()
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    bodies = {
        "A_OLD_CANONICAL": OLD.read_text(encoding="utf-8"),
        "B0_REFACTOR_AS_LANDED": LANDED.read_text(encoding="utf-8"),
        "B1_CONTROLS_REBOUND": CURRENT.read_text(encoding="utf-8"),
    }
    with tempfile.TemporaryDirectory(prefix="forgejo-real-task-") as raw:
        scratch = Path(raw)
        results = {name: run_arm(name, body, module, request, scratch)
                   for name, body in bodies.items()}
        refused = planted_mutations(module, request)
        residue = sorted(p.name for p in scratch.iterdir())

    if scratch.exists():
        raise TaskError("scratch directory survived the run")
    if not all(refused.values()):
        raise TaskError(f"planted mutation survived: {sorted(k for k, v in refused.items() if not v)}")

    executed = [row for row in results.values() if row["functional_output"] == "PASS"]
    identities = {json.dumps(row["receipt_identity"], sort_keys=True) for row in executed}
    if len(identities) != 1:
        raise TaskError("executed arms produced different receipts on the same task")
    if results["B0_REFACTOR_AS_LANDED"]["execution_state"] != "BLOCKED_READBACK_ROUTE_ABSENT":
        raise TaskError("B0 route regression is no longer exposed by the matched task")
    if len(executed) != 2:
        raise TaskError(f"expected two executed arms, got {len(executed)}")

    return {
        "schema": "forgejo-delivery-loop/real-task-ab/v1",
        "task": {
            "id": TASK_ID,
            "subject": str(REQUEST.relative_to(ROOT)),
            "request_sha256": executed[0]["receipt_identity"]["request_sha256"],
            "same_contracts_budget_carrier": True,
            "network": "NONE",
        },
        "results": results,
        "denominator": {
            "attempts": len(results) + len(refused),
            "executed": len(executed),
            "blocked_retained": 1,
            "refused_mutations_retained": len(refused),
            "planted_mutations": refused,
        },
        "output_equivalence_for_executed_arms": True,
        "b0_route_regression_exposed": True,
        "cleanup": {"scratch_removed": True, "artifacts_written": residue},
        "merge_route_sweep": "OWNED_BY tests/merge-authority/verify.sh",
        "evidence_kind": "FIXTURE",
        "live_forge_readback": "NOT_EXERCISED",
        "behavioral_model_uplift": "NOT_EXERCISED",
        "publication_and_merge_authority": "HUMAN_ADMIT_REQUIRED",
    }


def main() -> int:
    try:
        report = compare()
    except (TaskError, OSError, subprocess.SubprocessError, KeyError, ValueError) as exc:
        print(f"FORGEJO-REAL-TASK-AB-RED {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    print(
        "FORGEJO-REAL-TASK-AB-GREEN matched hermetic task closed on fixtures; B0 blocked on the "
        "absent readback route; A and B1 produced the same receipt identity; five planted mutations "
        "refused; scratch clean; live forge readback and model uplift NOT_EXERCISED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
