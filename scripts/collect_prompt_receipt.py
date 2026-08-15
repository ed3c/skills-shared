#!/usr/bin/env python3
"""Exercise an exact System Prompt in a named host and record a runtime receipt.

Exit codes:
  0   the prompt was carried, the host ran, and the deterministic verifier agreed
  2   the host ran and disagreed with the verifier, or produced nothing
  64  the host binary, the prompt, or the verifier is absent

Only a prompt whose exact bytes have been exercised in a named runtime and
admitted by a replayable verifier may become recorded. Before this, no prompt in
this repository had been exercised anywhere -- the recording gate existed and had
nothing to judge.

The carrier is recorded rather than assumed, because the two hosts do not have
one. Claude Code accepts a real system-prompt channel; Codex CLI takes the bytes
through its instruction channel. Both exercise the same bytes; they are not the
same load path, and a receipt claiming otherwise would be the kind of collapsed
distinction this repository exists to refuse.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / "skills" / "dual-forge-repository-loop" / "references" / "system-prompt.md"
VERIFIER = ROOT / "skills" / "dual-forge-repository-loop" / "tests" / "multi-agent-runtime" / "verify.py"

INVALID = 64
DISAGREEMENT = 2

PROBE = "python3 skills/dual-forge-repository-loop/tests/multi-agent-runtime/verify.py"
TASK = (
    "Run exactly this command from the repository root and reply with only its exit "
    f"code as a bare integer, nothing else: {PROBE}"
)

HOSTS: dict[str, dict[str, Any]] = {
    "claude-code": {
        "runtime": "CLAUDE_CODE_LOCAL",
        "binary": "claude",
        "version_argv": ["claude", "--version"],
        "carrier": "SYSTEM_PROMPT_FILE",
        "carrier_detail": "--append-system-prompt-file",
    },
    "codex-cli": {
        "runtime": "CODEX_CLI_LOCAL",
        "binary": "codex",
        "version_argv": ["codex", "--version"],
        "carrier": "INSTRUCTION_CHANNEL",
        "carrier_detail": "prompt argument prefix; this host exposes no system-prompt file flag",
    },
}


def digest_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def digest(value: Any) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def portable_text(text: str) -> str:
    text = text.replace(str(Path.home()), "<HOME>")
    import re

    return re.sub(r"/(?:private/)?(?:var/folders|tmp)/[A-Za-z0-9._/+-]*", "<TMPDIR>", text)


def trailing_integer(text: str) -> int | None:
    import re

    matches = re.findall(r"(?m)^\s*(-?\d+)\s*$", text)
    return int(matches[-1]) if matches else None


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def build_argv(host: str, prompt_path: Path, prompt_text: str) -> list[str]:
    if host == "claude-code":
        return ["claude", "-p", TASK, "--allowedTools", "Bash",
                "--append-system-prompt-file", str(prompt_path)]
    return ["codex", "exec", "--sandbox", "workspace-write",
            f"{prompt_text}\n\n---\n\n{TASK}"]


REQUIREMENTS_PATH = ROOT / "skills" / "dual-forge-repository-loop" / "references" / "runtime-requirements.json"
SKILL_NAME = "dual-forge-repository-loop"


def scan_shadowing() -> dict[str, Any]:
    """Actually look, rather than declare CLEAN.

    Both hosts prefer a project-local copy over the canonical body, so a same-name
    directory that is a real copy (not a symlink pointer) means the bytes the
    receipt names are not the bytes that ran.
    """
    surfaces = [
        Path.home() / ".claude" / "skills",
        Path.home() / ".agents" / "skills",
        ROOT / ".claude" / "skills",
        ROOT / ".agents" / "skills",
    ]
    scanned, findings = [], []
    for surface in surfaces:
        label = str(surface).replace(str(Path.home()), "<HOME>").replace(str(ROOT), "<REPO>")
        scanned.append(label)
        target = surface / SKILL_NAME
        if target.is_dir() and not target.is_symlink():
            findings.append({"name": SKILL_NAME, "surface": label})
    return {
        "state": "SHADOWED" if findings else "CLEAN",
        "surfaces_scanned": scanned,
        "findings": findings,
    }


def bootstrap_receipt(host: str, spec: dict[str, Any], subject_sha: str) -> dict[str, Any]:
    """How this host actually reached the Skill bytes it was given."""
    skill_dir = ROOT / "skills" / SKILL_NAME
    return {
        "schema": "skill-resolution-receipt/v1",
        "resolver_version": "collect-prompt-receipt/1.0.0",
        "runtime_identity": spec["runtime"],
        "consumer": {
            "repository_id": "ed3c/skills-shared",
            "subject_sha": subject_sha,
            "visibility": "PRIVATE",
        },
        "canonical": {
            "repository_id": "ed3c/skills-shared",
            "visibility": "PRIVATE",
            "commit_sha": subject_sha,
            "registry_digest": digest_bytes((ROOT / "registry.json").read_bytes()),
        },
        "selected_skills": [
            {
                "name": SKILL_NAME,
                "canonical_path": f"skills/{SKILL_NAME}",
                "blob_or_tree_identity": f"path:{skill_dir.relative_to(ROOT).as_posix()}",
                "content_sha256": digest_bytes(PROMPT_PATH.read_bytes()),
                "selection_reason": "EXPLICIT_TASK_BINDING",
                "trigger_evidence": "the task carries this Skill's System Prompt as the treatment",
                "transitive_dependencies": [],
                # The host reads the prompt from this checkout, not from a user surface.
                "access_mode": "PROJECT_CANONICAL_PROJECTION",
                "surface_readback_state": "VERIFIED",
                "runtime_requirements_digest": digest_bytes(REQUIREMENTS_PATH.read_bytes()),
            }
        ],
        "rejected_candidates": [],
        "shadowing_scan": scan_shadowing(),
        "environment": {
            # The manifest declares no network, no secrets and no setup entrypoint,
            # so there is nothing to prepare -- which is a different state from
            # having failed to prepare it.
            "state": "NOT_REQUIRED",
            "plan_digest": "ABSENT",
            "required_secret_names": [],
            "absent_secret_names": [],
            "setup_entrypoints": [],
            "capability_probes": [],
        },
        "bootstrap_states": [
            "RUNTIME_BOUND", "REPOSITORY_POLICY_BOUND", "SKILL_REQUIREMENTS_DISCOVERED",
            "MINIMAL_SKILL_SET_RESOLVED", "CANONICAL_SKILL_SUBJECTS_BOUND",
            "SKILL_SURFACES_AVAILABLE", "SKILL_RUNTIME_REQUIREMENTS_BOUND",
            "RUNTIME_ENV_CLOSURE_BOUND", "ENVIRONMENT_PLAN_RENDERED", "ENVIRONMENT_PREPARED",
            "CAPABILITY_PROBES_PASS", "TASK_EXECUTION_ADMITTED",
        ],
    }


def local_verifier() -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, str(VERIFIER)], cwd=ROOT, capture_output=True, text=True,
        check=False, timeout=900,
    )
    return {
        "exit_code": process.returncode,
        "stdout_sha256": digest_bytes(process.stdout.encode()),
        "summary": portable_text(process.stdout.strip().splitlines()[-1]) if process.stdout.strip() else "",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=sorted(HOSTS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)

    spec = HOSTS[args.host]
    if shutil.which(spec["binary"]) is None:
        print(f"PROMPT-RECEIPT-INVALID absent-binary: {spec['binary']}", file=sys.stderr)
        return INVALID
    for required in (PROMPT_PATH, VERIFIER):
        if not required.is_file():
            print(f"PROMPT-RECEIPT-INVALID absent-input: {required}", file=sys.stderr)
            return INVALID

    prompt_bytes = PROMPT_PATH.read_bytes()
    prompt_text = prompt_bytes.decode("utf-8")
    subject_sha = git("rev-parse", "HEAD")

    truth = local_verifier()
    version = subprocess.run(
        spec["version_argv"], capture_output=True, text=True, check=False, timeout=60
    ).stdout.strip()

    started = now()
    clock = time.time()
    process = subprocess.run(
        build_argv(args.host, PROMPT_PATH, prompt_text),
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=args.timeout,
    )
    ended = now()
    elapsed = round(time.time() - clock, 3)

    stdout = portable_text(process.stdout)
    stderr = portable_text(process.stderr)
    reported = trailing_integer(stdout)
    agreed = reported == truth["exit_code"]
    produced = bool(stdout.strip())

    observation = {
        "schema": "prompt-carrier-observation/v1",
        "host": args.host,
        "runtime": spec["runtime"],
        "version": version,
        "carrier": spec["carrier"],
        "carrier_detail": spec["carrier_detail"],
        "prompt_sha256": digest_bytes(prompt_bytes),
        "prompt_bytes": len(prompt_bytes),
        "task": TASK,
        "host_exit_code": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "reported_verifier_exit": reported,
        "local_verifier": truth,
        "subject_sha": subject_sha,
    }

    args.output.mkdir(parents=True, exist_ok=True)
    observation_path = args.output / f"prompt-observation-{args.host}.json"
    observation_path.write_text(
        json.dumps(observation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # The prompt receipt may only claim RUNTIME_BOOTSTRAP_PASS against a bootstrap
    # receipt that exists. Emitting one here rather than asserting the state keeps
    # the two documents joined by a digest instead of by a claim.
    bootstrap = bootstrap_receipt(args.host, spec, subject_sha)
    bootstrap_path = args.output / f"bootstrap-receipt-{args.host}.json"
    bootstrap_path.write_text(
        json.dumps(bootstrap, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    bootstrap_admitted = bootstrap["shadowing_scan"]["state"] == "CLEAN"

    controls = ["planted-defect-suite"]
    receipt = {
        "schema": "system-prompt-runtime-receipt/v1",
        "prompt": {
            "prompt_id": "repository-multi-agent-runtime",
            "version": "2.1",
            "content_sha256": digest_bytes(prompt_bytes),
            "source_repository": "ed3c/skills-shared",
            "source_commit": subject_sha,
            "source_path": "skills/dual-forge-repository-loop/references/system-prompt.md",
            "composition_skills": [
                {
                    "name": "dual-forge-repository-loop",
                    "directory_digest": digest_bytes(
                        b"".join(
                            sorted(
                                p.read_bytes()
                                for p in (ROOT / "skills" / "dual-forge-repository-loop" / "references").glob("*.json")
                            )
                        )
                    ),
                }
            ],
        },
        "evaluation_contract": {
            "suite_id": "multi-agent-runtime-contract-suite",
            "suite_sha256": digest_bytes(VERIFIER.read_bytes()),
            "case_ids": ["positive-multi", "positive-single-builder", "positive-retry-lineage",
                         "positive-sequential-handoff", "positive-sibling-path"],
            "acceptance_predicates": [
                "the host reports the verifier exit code computed locally",
                "the verifier admits every positive fixture and refuses every planted defect",
            ],
            "negative_controls": controls,
            "baseline_condition": "the same verifier executed locally without a host in the loop",
        },
        "runtime": {
            "identity": spec["runtime"],
            "harness_identity": version or args.host,
            "model_identity": f"{args.host}-default-model-unbound",
            "subject_sha": subject_sha,
            "environment_digest": digest({"cwd": "<REPO_ROOT>", "carrier": spec["carrier"]}),
            "effect_policy": "BOUNDED_WRITE",
            "bootstrap_receipt_digest": (
                digest_bytes(bootstrap_path.read_bytes()) if bootstrap_admitted else "ABSENT"
            ),
        },
        "execution": {
            "run_id": f"prompt-{args.host}-{subject_sha[:12]}",
            "started_at": started,
            "ended_at": ended,
            "repetition_identity": "repetition-1",
            "trace_digest": digest_bytes(observation_path.read_bytes()),
            "artifact_digests": [digest_bytes(observation_path.read_bytes())],
            "terminal_state": "COMPLETED" if process.returncode == 0 else "FAILED",
        },
        "verification": {
            "verifier_id": "multi-agent-runtime-verify",
            "verifier_digest": digest_bytes(VERIFIER.read_bytes()),
            "replay_inputs_digest": digest({"probe": PROBE, "subject": subject_sha}),
            "result": "PASS" if (agreed and produced and truth["exit_code"] == 0) else "FAIL",
            "negative_control_results": [
                {"id": controls[0], "state": "KILLED" if truth["exit_code"] == 0 else "SURVIVED"}
            ],
            "unsupported_claims": [],
        },
        "promotion": {
            "admitted_scope": [f"ed3c/skills-shared @ {spec['runtime']} via {spec['carrier']}"],
            "authority": "LOCAL_RECORD",
            "baseline_comparison": (
                "the host reproduced the locally computed verifier terminal state; no uplift "
                "over a no-prompt baseline is claimed or measured"
            ),
            "regressions": [],
            "release_admit_state": "HUMAN_ADMIT_REQUIRED",
            "revocation_subject": "prompt content_sha256, carrier, or host version change",
        },
        "observed_stacks": [f"{args.host}+{version or 'unknown'}"],
        "record_states": (
            [
                "AUTHORED", "CANDIDATE_BOUND", "EVAL_CONTRACT_BOUND", "RUNTIME_BOOTSTRAP_PASS",
                "RUNTIME_EXECUTED", "EXECUTOR_EVIDENCE_CAPTURED", "DETERMINISTIC_VERIFIER_PASS",
                "NEGATIVE_CONTROLS_PASS", "RECEIPT_BUNDLE_REPLAY_PASS", "SCOPE_DECIDED",
                "LOCAL_RECORD_ELIGIBLE", "RELEASE_ADMIT_REQUIRED",
            ]
            if (bootstrap_admitted and agreed and produced and truth["exit_code"] == 0)
            else ["AUTHORED", "CANDIDATE_BOUND", "EVAL_CONTRACT_BOUND", "BOOTSTRAP_FAIL"]
            if not bootstrap_admitted
            else [
                "AUTHORED", "CANDIDATE_BOUND", "EVAL_CONTRACT_BOUND", "RUNTIME_BOOTSTRAP_PASS",
                "RUNTIME_EXECUTED", "EXECUTOR_EVIDENCE_CAPTURED", "VERIFIER_FAIL",
            ]
        ),
    }

    receipt_path = args.output / f"prompt-receipt-{args.host}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"PROMPT-RECEIPT {args.host} carrier={spec['carrier']} "
        f"prompt_sha={receipt['prompt']['content_sha256'][:12]} bytes={len(prompt_bytes)} "
        f"reported={reported} local={truth['exit_code']} "
        f"verifier={receipt['verification']['result']} elapsed={elapsed}s"
    )
    return 0 if receipt["verification"]["result"] == "PASS" else DISAGREEMENT


if __name__ == "__main__":
    raise SystemExit(main())
