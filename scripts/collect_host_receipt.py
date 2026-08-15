#!/usr/bin/env python3
"""Drive a real host CLI over an exact repository subject and record what it did.

Exit codes:
  0   the host ran and its observation matched the locally computed ground truth
  2   the host ran and disagreed, or produced nothing
  64  the host binary is absent, or the repository subject cannot be read

A fixture cannot show that Claude Code or Codex CLI discovers a Skill, executes a
command, and reports a result. This runs the real CLI on the exact current commit,
records the raw observation, and emits a `procedural-shadow-runtime-receipt/v1`
that the repository's own checker validates.

What it establishes is narrow on purpose: that a named host executed a
deterministic probe on this subject and reported the same terminal state the
repository computes locally. It does not establish that a Skill changed the
host's behaviour, that one model outperforms another, or anything about
production. Those need a controlled comparison, not a single observation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

INVALID = 64
DISAGREEMENT = 2

# The probe is chosen so its answer is independently checkable: the repository can
# compute it locally, so a host that guesses instead of running is caught.
PROBE = "python3 scripts/evidence_bundle.py --selftest"
PROMPT = (
    "Run exactly this command in the current repository and reply with only its "
    f"exit code as a bare integer, nothing else: {PROBE}"
)

HOSTS: dict[str, dict[str, Any]] = {
    "claude-code": {
        "runtime": "CLAUDE_CODE_LOCAL",
        "binary": "claude",
        "version_argv": ["claude", "--version"],
        "argv": ["claude", "-p", PROMPT, "--allowedTools", "Bash"],
    },
    "codex-cli": {
        "runtime": "CODEX_CLI_LOCAL",
        "binary": "codex",
        "version_argv": ["codex", "--version"],
        "argv": ["codex", "exec", "--sandbox", "workspace-write", PROMPT],
    },
}


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


# Observed but not asserted: varies per run, nothing downstream compares it.
UNSTABLE_OBSERVATION_KEYS = ("elapsed_seconds",)


def stable_observation(observation: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in observation.items() if k not in UNSTABLE_OBSERVATION_KEYS}


def portable_text(text: str) -> str:
    """Strip machine-specific paths before anything is digested or committed.

    A host prints its own temp and home directories. Digesting those makes the
    receipt reproducible only on the machine that produced it -- the same defect
    that kept repository-capability-audit red on every host but one -- and
    committing them puts one developer's filesystem into a shared repository.
    """
    text = text.replace(str(Path.home()), "<HOME>")
    text = re.sub(r"/(?:private/)?(?:var/folders|tmp)/[A-Za-z0-9._/+-]*", "<TMPDIR>", text)
    return text


def trailing_integer(text: str) -> int | None:
    """The last bare integer the host emitted.

    Hosts frame their answer differently -- one replies with the digit alone, the
    other prints the command's own output first. Reading the last standalone
    integer accepts both without accepting prose that merely contains a digit.
    """
    matches = re.findall(r"(?m)^\s*(-?\d+)\s*$", text)
    return int(matches[-1]) if matches else None


def run_host(name: str, timeout: int) -> dict[str, Any]:
    spec = HOSTS[name]
    if shutil.which(spec["binary"]) is None:
        print(f"HOST-RECEIPT-INVALID absent-binary: {spec['binary']}", file=sys.stderr)
        raise SystemExit(INVALID)
    version = subprocess.run(
        spec["version_argv"], capture_output=True, text=True, check=False, timeout=60
    ).stdout.strip()
    started = time.time()
    process = subprocess.run(
        spec["argv"], cwd=ROOT, capture_output=True, text=True, check=False, timeout=timeout
    )
    elapsed = round(time.time() - started, 3)
    stdout = portable_text(process.stdout)
    stderr = portable_text(process.stderr)
    return {
        "host": name,
        "runtime": spec["runtime"],
        "binary": spec["binary"],
        "version": version,
        "argv": spec["argv"],
        "exit_code": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": digest(stdout.encode()),
        "reported_probe_exit": trailing_integer(stdout),
        # Elapsed time is observed, not asserted: it varies per run and nothing
        # downstream compares it, so it stays out of every digest.
        "elapsed_seconds": elapsed,
    }


def local_ground_truth() -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "evidence_bundle.py"), "--selftest"],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=300,
    )
    return {
        "command": PROBE,
        "exit_code": process.returncode,
        "stdout_sha256": digest(process.stdout.encode()),
    }


def build_receipt(observation: dict[str, Any], truth: dict[str, Any], subject: dict[str, Any],
                  observation_digest: str, skill_digest: str) -> dict[str, Any]:
    produced_output = bool(observation["stdout"].strip())
    agreed = observation["reported_probe_exit"] == truth["exit_code"]
    procedure = "procedural-shadow-runtime.execute-before-claiming"
    assertions = [
        {
            "assertion_id": "host-produced-observable-output",
            "procedure_id": procedure,
            "result": "PASS" if produced_output else "FAIL",
        },
        {
            "assertion_id": "host-reported-exit-matches-local-computation",
            "procedure_id": procedure,
            "result": "PASS" if agreed else "FAIL",
        },
    ]
    passed = all(item["result"] == "PASS" for item in assertions)
    return {
        "schema": "procedural-shadow-runtime-receipt/v1",
        "receipt_id": f"host-{observation['host']}-{subject['current_sha'][:12]}",
        "checkpoint": "BEFORE_PR_OR_PUBLICATION",
        "subject": subject,
        "action": {
            "class": "DETERMINISTIC_PROBE_EXECUTION",
            "side_effecting": False,
            "intent_digest": digest({"prompt": PROMPT, "probe": PROBE}),
        },
        "applicable_procedures": [
            {
                "procedure_id": procedure,
                "criticality": "must",
                "source": {
                    "repository": "ed3c/skills-shared",
                    "ref": subject["current_sha"],
                    "path": "skills/procedural-shadow-runtime/SKILL.md",
                    "content_sha256": skill_digest,
                },
            }
        ],
        "assertions": assertions,
        "evidence": [
            {
                "evidence_id": f"observation-{observation['host']}",
                "procedure_id": procedure,
                "kind": "COMMAND",
                "artifact_sha256": observation_digest,
                "exact_subject": True,
            }
        ],
        "dispositions": [
            {"procedure_id": procedure, "state": "VERIFIED" if passed else "FAILED"}
        ],
        "close_state": "PASS" if passed else "FAIL",
    }


def selftest() -> int:
    """Prove the adapter refuses a host that guesses, stays silent, or leaks paths."""
    subject = {
        "repository": "ed3c/skills-shared",
        "base_sha": "a" * 40,
        "current_sha": "a" * 40,
        "runtime": "CLAUDE_CODE_LOCAL",
        "context_digest": "b" * 64,
    }
    truth = {"command": PROBE, "exit_code": 0, "stdout_sha256": "c" * 64}
    base = {"host": "claude-code", "stdout": "0\n", "reported_probe_exit": 0}

    agreed = build_receipt({**base}, truth, subject, "d" * 64, "e" * 64)
    if agreed["close_state"] != "PASS":
        print("SELFTEST RED: an agreeing host did not close PASS", file=sys.stderr)
        return 1

    guessed = build_receipt(
        {**base, "stdout": "2\n", "reported_probe_exit": 2}, truth, subject, "d" * 64, "e" * 64
    )
    if guessed["close_state"] != "FAIL":
        print("SELFTEST RED: a host reporting the wrong exit code closed PASS", file=sys.stderr)
        return 1

    silent = build_receipt(
        {**base, "stdout": "   \n", "reported_probe_exit": None}, truth, subject, "d" * 64, "e" * 64
    )
    if silent["close_state"] != "FAIL":
        print("SELFTEST RED: a silent host closed PASS", file=sys.stderr)
        return 1

    # Reading the last standalone integer must accept a host that prints the
    # command's own output first, and must not accept prose containing a digit.
    cases = [("0\n", 0), ("noise\n\n0\n", 0), ("exit code 0 here\n", None), ("", None), ("1\n0\n", 0)]
    for text, expected in cases:
        if trailing_integer(text) != expected:
            print(f"SELFTEST RED: trailing_integer({text!r}) != {expected}", file=sys.stderr)
            return 1

    leaky = f"ran in {Path.home()}/repo and /var/folders/ab/cd/T/tmpxyz\n"
    cleaned = portable_text(leaky)
    if str(Path.home()) in cleaned or "/var/folders/" in cleaned:
        print(f"SELFTEST RED: paths survived redaction: {cleaned!r}", file=sys.stderr)
        return 1

    stable = stable_observation({"stdout": "0\n", "elapsed_seconds": 1.5})
    if "elapsed_seconds" in stable or digest(stable) != digest(
        stable_observation({"stdout": "0\n", "elapsed_seconds": 99.9})
    ):
        print("SELFTEST RED: elapsed time reached the digest", file=sys.stderr)
        return 1

    print(
        "SELFTEST GREEN: agreement closes PASS; a wrong exit code and a silent host each "
        "close FAIL; trailing-integer parsing accepts framed output and rejects prose; "
        "home and temp paths are redacted; elapsed time stays out of the digest"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--host", choices=sorted(HOSTS))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.host or not args.output:
        parser.error("--host and --output are required unless --selftest")

    skill_path = ROOT / "skills" / "procedural-shadow-runtime" / "SKILL.md"
    if not skill_path.is_file():
        print(f"HOST-RECEIPT-INVALID absent-skill: {skill_path}", file=sys.stderr)
        return INVALID
    skill_digest = digest(skill_path.read_bytes())

    subject = {
        "repository": "ed3c/skills-shared",
        "base_sha": git("rev-parse", "HEAD"),
        "current_sha": git("rev-parse", "HEAD"),
        "runtime": HOSTS[args.host]["runtime"],
        "context_digest": digest({"prompt": PROMPT, "skill": skill_digest}),
    }

    truth = local_ground_truth()
    observation = run_host(args.host, args.timeout)
    observation["local_ground_truth"] = truth
    observation["subject"] = subject

    args.output.mkdir(parents=True, exist_ok=True)
    observation_path = args.output / f"observation-{args.host}.json"
    observation_path.write_text(
        json.dumps(observation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    # Digest the semantic observation, not the file: elapsed_seconds differs on
    # every run, and hashing it would make an otherwise identical receipt look
    # like a different one each time.
    receipt = build_receipt(
        observation, truth, subject, digest(stable_observation(observation)), skill_digest
    )
    receipt_path = args.output / f"receipt-{args.host}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"HOST-RECEIPT {args.host} version={observation['version']!r} "
        f"host_exit={observation['exit_code']} "
        f"reported_probe_exit={observation['reported_probe_exit']} "
        f"local_probe_exit={truth['exit_code']} "
        f"close={receipt['close_state']} "
        f"elapsed={observation['elapsed_seconds']}s"
    )
    return 0 if receipt["close_state"] == "PASS" else DISAGREEMENT


if __name__ == "__main__":
    raise SystemExit(main())
