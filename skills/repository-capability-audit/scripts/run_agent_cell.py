#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "evals" / "agent-effectiveness-contract.json"
SENSITIVE_ENV_MARKERS = (
    "API_KEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "CREDENTIAL",
    "AUTH",
    "PRIVATE_KEY",
)


class CellError(RuntimeError):
    pass


def canonical_digest(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_command(value: str, placeholders: dict[str, str]) -> list[str]:
    try:
        raw = json.loads(value)
    except json.JSONDecodeError as exc:
        raise CellError("command must be a JSON array of strings") from exc
    if (
        not isinstance(raw, list)
        or not raw
        or not all(isinstance(item, str) and item for item in raw)
    ):
        raise CellError(
            "command must be a non-empty JSON array of non-empty strings"
        )
    result = []
    for item in raw:
        try:
            result.append(item.format_map(placeholders))
        except KeyError as exc:
            raise CellError(
                f"unknown command placeholder: {exc.args[0]}"
            ) from exc
    return result


def sanitized_environment(allowed: set[str]) -> tuple[dict[str, str], list[str]]:
    result: dict[str, str] = {}
    removed: list[str] = []
    for key, value in os.environ.items():
        upper = key.upper()
        sensitive = any(marker in upper for marker in SENSITIVE_ENV_MARKERS)
        if sensitive and key not in allowed:
            removed.append(key)
            continue
        result[key] = value
    return result, sorted(removed)


def run_process(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
    stdout_path: Path,
    stderr_path: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    timed_out = False
    try:
        process = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        exit_code = process.returncode
        stdout = process.stdout
        stderr = process.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        stderr += f"\nTIMEOUT after {timeout_seconds}s\n"
    duration_ms = round((time.monotonic() - started) * 1000)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    return {
        "argv": argv,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_ms": duration_ms,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout_sha256": file_digest(stdout_path),
        "stderr_sha256": file_digest(stderr_path),
    }


def validate_hex(value: str, length: int, name: str) -> None:
    if len(value) != length or any(
        char not in "0123456789abcdef" for char in value
    ):
        raise CellError(
            f"{name} must be lowercase hexadecimal with length {length}"
        )


def validate_metrics(metrics: Any, required: list[str]) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        raise CellError("evaluator metrics must be a JSON object")
    missing = sorted(set(required) - set(metrics))
    extra = sorted(set(metrics) - set(required))
    if missing or extra:
        raise CellError(
            f"metrics fields differ: missing={missing} extra={extra}"
        )
    bool_fields = {
        "task_success",
        "evidence_packet_complete",
        "exact_subject_continuity",
        "negative_control_valid",
        "explicit_non_claim_accuracy",
        "trigger_correct",
        # A host that does not report spend and a host that spent nothing both
        # write cost_usd = 0. Without this flag the two are the same number, and
        # a mean over mixed hosts silently reads unreported spend as free.
        "cost_observed",
    }
    int_fields = {
        "material_defects_found",
        "material_defects_total",
        "false_pass_count",
        "false_pass_opportunities",
        "tool_calls",
        "input_tokens",
        "output_tokens",
        "duration_ms",
    }
    for name in bool_fields:
        if type(metrics[name]) is not bool:
            raise CellError(f"metric {name} must be boolean")
    for name in int_fields:
        if type(metrics[name]) is not int or metrics[name] < 0:
            raise CellError(
                f"metric {name} must be a non-negative integer"
            )
    if (
        not isinstance(metrics["cost_usd"], (int, float))
        or metrics["cost_usd"] < 0
    ):
        raise CellError("metric cost_usd must be a non-negative number")
    if not metrics["cost_observed"] and metrics["cost_usd"] != 0:
        raise CellError(
            "metric cost_usd must be 0 when cost_observed is false; an unobserved "
            "cost cannot carry a figure"
        )
    if metrics["material_defects_found"] > metrics["material_defects_total"]:
        raise CellError(
            "material_defects_found exceeds material_defects_total"
        )
    if metrics["false_pass_count"] > metrics["false_pass_opportunities"]:
        raise CellError(
            "false_pass_count exceeds false_pass_opportunities"
        )
    return metrics


def manifest_files(workspace: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted(workspace.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        result.append(
            {
                "path": path.relative_to(workspace).as_posix(),
                "sha256": file_digest(path),
                "bytes": path.stat().st_size,
            }
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute one matched Agent A/B cell"
    )
    parser.add_argument("--profile", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--repository-id", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--repetition", type=int, required=True)
    parser.add_argument("--arm-order", type=int, required=True)
    parser.add_argument("--task-file", type=Path, required=True)
    parser.add_argument("--treatment-file", type=Path, required=True)
    parser.add_argument("--evaluator-file", type=Path, required=True)
    parser.add_argument("--agent-command-json", required=True)
    parser.add_argument("--evaluator-command-json", required=True)
    parser.add_argument(
        "--agent-class",
        choices=["language_model_agent", "deterministic_fixture"],
        required=True,
    )
    parser.add_argument("--agent-provider", required=True)
    parser.add_argument("--agent-family", required=True)
    parser.add_argument("--agent-model", required=True)
    parser.add_argument("--agent-version", required=True)
    parser.add_argument("--agent-harness", required=True)
    parser.add_argument("--agent-harness-version", required=True)
    parser.add_argument("--runtime-identity", required=True)
    parser.add_argument("--runtime-version", required=True)
    parser.add_argument("--toolset-digest", required=True)
    parser.add_argument("--evaluator-identity", required=True)
    parser.add_argument("--evaluator-version", required=True)
    parser.add_argument(
        "--evaluator-owner",
        choices=["independent", "producer"],
        required=True,
    )
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--max-tool-calls", type=int, default=100)
    parser.add_argument("--max-input-tokens", type=int, default=200000)
    parser.add_argument("--max-output-tokens", type=int, default=20000)
    parser.add_argument("--allow-env", action="append", default=[])
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        validate_hex(args.commit, 40, "commit")
        validate_hex(args.tree, 40, "tree")
        validate_hex(args.toolset_digest, 64, "toolset-digest")
        if args.repetition < 1 or args.arm_order < 0:
            raise CellError(
                "repetition must be positive and arm-order must be non-negative"
            )
        for path, name in (
            (args.task_file, "task-file"),
            (args.treatment_file, "treatment-file"),
            (args.evaluator_file, "evaluator-file"),
        ):
            if not path.is_file():
                raise CellError(f"{name} is missing: {path}")
        workspace = args.workspace.resolve()
        if workspace.exists() and any(workspace.iterdir()):
            raise CellError("workspace must be absent or empty")
        workspace.mkdir(parents=True, exist_ok=True)
        logs = workspace / ".agent-eval-logs"
        logs.mkdir()
        metrics_file = workspace / "agent-eval-metrics.json"
        placeholders = {
            "task_file": str(args.task_file.resolve()),
            "treatment_file": str(args.treatment_file.resolve()),
            "evaluator_file": str(args.evaluator_file.resolve()),
            "workspace": str(workspace),
            "metrics_file": str(metrics_file),
            "agent_stdout": str(logs / "agent.stdout.log"),
            "agent_stderr": str(logs / "agent.stderr.log"),
        }
        agent_argv = parse_command(args.agent_command_json, placeholders)
        evaluator_argv = parse_command(
            args.evaluator_command_json,
            placeholders,
        )
        env, removed_env = sanitized_environment(set(args.allow_env))
        env.update(
            {
                "RCA_EVAL_PROFILE": args.profile,
                "RCA_EVAL_CASE_ID": args.case_id,
                "RCA_EVAL_WORKSPACE": str(workspace),
                "RCA_EVAL_TASK_FILE": placeholders["task_file"],
                "RCA_EVAL_TREATMENT_FILE": placeholders["treatment_file"],
                "RCA_EVAL_METRICS_FILE": str(metrics_file),
            }
        )
        agent_run = run_process(
            agent_argv,
            cwd=workspace,
            env=env,
            timeout_seconds=args.timeout_seconds,
            stdout_path=logs / "agent.stdout.log",
            stderr_path=logs / "agent.stderr.log",
        )
        evaluator_run = run_process(
            evaluator_argv,
            cwd=workspace,
            env=env,
            timeout_seconds=args.timeout_seconds,
            stdout_path=logs / "evaluator.stdout.log",
            stderr_path=logs / "evaluator.stderr.log",
        )
        if evaluator_run["exit_code"] != 0:
            raise CellError("independent evaluator command failed")
        if not metrics_file.is_file():
            raise CellError(
                "independent evaluator did not create metrics file"
            )
        contract = read_json(CONTRACT)
        metrics = validate_metrics(
            read_json(metrics_file),
            contract["required_metrics"],
        )
        payload: dict[str, Any] = {
            "schema": "repository-capability-audit-agent-run/v1",
            "agent_class": args.agent_class,
            "profile": args.profile,
            "case_id": args.case_id,
            "repository_id": args.repository_id,
            "repository_subject": {
                "commit": args.commit,
                "tree": args.tree,
            },
            "repetition": args.repetition,
            "arm_order": args.arm_order,
            "task_digest": file_digest(args.task_file),
            "treatment_digest": file_digest(args.treatment_file),
            "evaluator_digest": file_digest(args.evaluator_file),
            "agent": {
                "provider": args.agent_provider,
                "family": args.agent_family,
                "model": args.agent_model,
                "version": args.agent_version,
                "harness": args.agent_harness,
                "harness_version": args.agent_harness_version,
            },
            "runtime": {
                "identity": args.runtime_identity,
                "version": args.runtime_version,
                "toolset_digest": args.toolset_digest,
            },
            "budgets": {
                "timeout_seconds": args.timeout_seconds,
                "max_tool_calls": args.max_tool_calls,
                "max_input_tokens": args.max_input_tokens,
                "max_output_tokens": args.max_output_tokens,
            },
            "evaluator": {
                "identity": args.evaluator_identity,
                "version": args.evaluator_version,
                "owner": args.evaluator_owner,
                "command": evaluator_argv,
            },
            "agent_run": agent_run,
            "evaluator_run": evaluator_run,
            "removed_ambient_environment_names": removed_env,
            "metrics": metrics,
            "artifacts": manifest_files(workspace),
        }
        payload["receipt_id"] = canonical_digest(
            {
                "profile": args.profile,
                "case_id": args.case_id,
                "repository_id": args.repository_id,
                "repository_subject": payload["repository_subject"],
                "repetition": args.repetition,
                "task_digest": payload["task_digest"],
                "treatment_digest": payload["treatment_digest"],
                "agent": payload["agent"],
                "runtime": payload["runtime"],
            }
        )
        payload["receipt_digest"] = canonical_digest(payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        print(args.output)
        return 0
    except (
        CellError,
        OSError,
        ValueError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"AGENT CELL INVALID: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
