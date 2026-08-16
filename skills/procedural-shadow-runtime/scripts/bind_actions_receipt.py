#!/usr/bin/env python3
"""Bind one exact-head GitHub Actions run into a replay-verified receipt.

Exit codes:
  0   a real runner executed the declared commands on the expected head SHA and
      the downloaded bundle replayed offline
  2   the run is bound but an assertion failed, or the provider circuit is open
  64  the run, the artifact, or the local subject is absent

#212. The distinction this exists to preserve is the one #191 cost a day to
learn: a workflow run can exist, be listed, be linked from a badge, and have
executed nothing. That incident's jobs came back with

    steps: []
    runner_id: 0
    conclusion: failure
    "the job was not started because an Actions budget is preventing further use"

which is a provider allocation failure and not a repository-test failure. A
receipt that renders both as red teaches its reader to stop believing red.

So `runner_absent` is its own terminal state, `PROVIDER_CIRCUIT_OPEN` is its own
close state, and the assertion that a runner existed is separate from the
assertion that the tests passed.

The bundle is verified twice: once in the job that produced it, and once here
against the downloaded bytes with no network. A bundle that only verifies where
it was made is not replayable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]

INVALID = 64
REFUSED = 2

REPOSITORY = "ed3c/skills-shared"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def gh_api(path: str) -> Any:
    result = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"gh api {path}: {result.stderr.strip()[-200:]}")
    return json.loads(result.stdout)


def classify_jobs(jobs: list[dict[str, Any]], focus_job: str | None = None) -> dict[str, Any]:
    """Separate three things a red run can mean, and scope the verdict to one job.

    A job with no steps and no runner did not fail; it never began. Reporting
    that as a test failure is how a billing incident becomes a code incident in
    everyone's memory.

    A job cancelled because a later push superseded the run did not fail either.
    This matrix carries a leg per skill, so a sibling leg cancelled mid-flight
    marks the whole run red while the leg this receipt is about succeeded on the
    exact head. `focus_job` is what keeps the receipt's subject the subject: the
    verdict is about that leg, and every sibling outcome is still recorded
    beside it rather than dropped.
    """
    started = [job for job in jobs if job.get("steps")]
    runnerless = [job["name"] for job in jobs if not job.get("steps")]
    cancelled = [job["name"] for job in jobs if job.get("conclusion") == "cancelled"]
    graded = [job for job in started
              if focus_job is None or job.get("name") == focus_job]
    failed = [job["name"] for job in graded
              if job.get("conclusion") not in {"success", "skipped"}]
    return {
        "job_count": len(jobs),
        "jobs_with_steps": len(started),
        "runnerless_jobs": runnerless,
        "cancelled_jobs": cancelled,
        "focus_job": focus_job,
        "focus_job_present": any(job.get("name") == focus_job for job in started)
                             if focus_job else None,
        "failed_jobs": failed,
        "sibling_jobs_failed": [job["name"] for job in started
                                if job.get("conclusion") not in {"success", "skipped"}
                                and job["name"] not in failed],
        "provider_circuit_open": bool(runnerless),
    }


def verify_bundle_offline(bundle: Path) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "evidence_bundle.py"), "verify", str(bundle)],
        capture_output=True, text=True, check=False,
    )
    return {"exit_code": result.returncode,
            "stdout": result.stdout.strip()[-400:],
            "stderr": result.stderr.strip()[-400:]}


def build_receipt(run: dict[str, Any], jobs: dict[str, Any], expected_sha: str,
                  bundle_verify: dict[str, Any], manifest: dict[str, Any] | None,
                  skill_digest: str) -> dict[str, Any]:
    procedure = "procedural-shadow-runtime.exact-head-ci-execution"
    same_head = run["head_sha"] == expected_sha
    runner_present = (jobs["jobs_with_steps"] > 0 and not jobs["provider_circuit_open"]
                      and jobs.get("focus_job_present") is not False)
    replayed = bundle_verify["exit_code"] == 0
    manifest_binds = bool(manifest and manifest.get("files")) and all(
        entry.get("sha256") for entry in (manifest or {}).get("files", [])
    )

    assertions = [
        {"assertion_id": "run-received-a-real-runner-with-non-empty-steps",
         "procedure_id": procedure, "result": "PASS" if runner_present else "FAIL"},
        {"assertion_id": "run-head-sha-equals-the-expected-subject",
         "procedure_id": procedure, "result": "PASS" if same_head else "FAIL"},
        {"assertion_id": "declared-suite-commands-concluded-without-repository-failure",
         "procedure_id": procedure,
         "result": "PASS" if runner_present and not jobs["failed_jobs"] else "FAIL"},
        {"assertion_id": "artifact-manifest-binds-every-file-by-sha256",
         "procedure_id": procedure, "result": "PASS" if manifest_binds else "FAIL"},
        {"assertion_id": "downloaded-bundle-replays-offline",
         "procedure_id": procedure, "result": "PASS" if replayed else "FAIL"},
    ]
    passed = all(item["result"] == "PASS" for item in assertions)

    close_state = "PASS" if passed else (
        # Not FAIL. The repository was never tested, and saying FAIL would claim
        # it was and lost.
        "BLOCKED" if jobs["provider_circuit_open"] else "FAIL"
    )
    return {
        "schema": "procedural-shadow-runtime-receipt/v1",
        "receipt_id": f"github-actions-{run['id']}-{run['head_sha'][:12]}",
        "checkpoint": "BEFORE_PR_OR_PUBLICATION",
        "subject": {
            "repository": REPOSITORY,
            "base_sha": run["head_sha"],
            "current_sha": run["head_sha"],
            "runtime": "GITHUB_ACTIONS",
            "context_digest": digest_json({"run": run["id"], "head": run["head_sha"]}),
        },
        "action": {
            "class": "EXACT_HEAD_CI_EXECUTION",
            "side_effecting": False,
            "intent_digest": digest_json({"workflow": run["name"], "head": run["head_sha"]}),
        },
        "applicable_procedures": [{
            "procedure_id": procedure,
            "criticality": "must",
            "source": {
                "repository": REPOSITORY,
                "ref": run["head_sha"],
                "path": "skills/procedural-shadow-runtime/SKILL.md",
                "content_sha256": skill_digest,
            },
        }],
        "assertions": assertions,
        "evidence": [{
            "evidence_id": f"actions-run-{run['id']}",
            "procedure_id": procedure,
            "kind": "COMMAND",
            "artifact_sha256": digest_json({"run": run, "jobs": jobs, "manifest": manifest}),
            "exact_subject": True,
        }],
        "dispositions": [{
            "procedure_id": procedure,
            "state": "VERIFIED" if passed else ("BLOCKED" if jobs["provider_circuit_open"] else "FAILED"),
            **({"reason": "Actions provider did not allocate a runner"} if jobs["provider_circuit_open"] else {}),
        }],
        "close_state": close_state,
        "actions_run": {
            "run_id": run["id"],
            "workflow": run["name"],
            "run_attempt": run.get("run_attempt"),
            "head_sha": run["head_sha"],
            "expected_sha": expected_sha,
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "event": run.get("event"),
            "jobs": jobs,
            # A provider failure and a repository-test failure are named
            # separately, in the artefact, not only in prose.
            # Three distinct meanings, never collapsed: no runner, this leg
            # failed, or a sibling leg was cancelled by a superseding push.
            "failure_class": ("PROVIDER_ALLOCATION" if jobs["provider_circuit_open"]
                              else ("REPOSITORY_TEST" if jobs["failed_jobs"]
                                    else ("SIBLING_JOB_CANCELLED" if jobs.get("cancelled_jobs")
                                          else "NONE"))),
            "bundle_offline_replay": bundle_verify,
            "manifest_file_count": len((manifest or {}).get("files", [])),
        },
    }


def selftest() -> int:
    """The provider-circuit distinction, offline, on the #191 shape."""
    budget_blocked = classify_jobs([
        {"name": "contract", "steps": [], "conclusion": "failure", "runner_id": 0},
        {"name": "suites", "steps": [], "conclusion": "failure", "runner_id": 0},
    ])
    if not budget_blocked["provider_circuit_open"] or budget_blocked["failed_jobs"]:
        print(f"SELFTEST RED: a runnerless run was classified as a test failure: {budget_blocked}",
              file=sys.stderr)
        return 1

    real_failure = classify_jobs([
        {"name": "contract", "steps": [{"name": "run"}], "conclusion": "failure"},
    ])
    if real_failure["provider_circuit_open"] or real_failure["failed_jobs"] != ["contract"]:
        print(f"SELFTEST RED: a real test failure was misclassified: {real_failure}", file=sys.stderr)
        return 1

    green = classify_jobs([{"name": "contract", "steps": [{"name": "run"}], "conclusion": "success"}])
    if green["provider_circuit_open"] or green["failed_jobs"]:
        print(f"SELFTEST RED: a green run was flagged: {green}", file=sys.stderr)
        return 1

    # A matrix leg cancelled by a superseding push marks the whole run red. The
    # receipt is about one leg, and that leg succeeded on the exact head.
    superseded = classify_jobs([
        {"name": "procedural-shadow-runtime", "steps": [{"name": "run"}], "conclusion": "success"},
        {"name": "another-skill", "steps": [{"name": "run"}], "conclusion": "cancelled"},
    ], focus_job="procedural-shadow-runtime")
    if superseded["failed_jobs"]:
        print(f"SELFTEST RED: a cancelled sibling failed the focused leg: {superseded}",
              file=sys.stderr)
        return 1
    if superseded["sibling_jobs_failed"] != ["another-skill"]:
        print("SELFTEST RED: the cancelled sibling was dropped instead of recorded",
              file=sys.stderr)
        return 1

    # Scoping must not become a way to ignore this leg's own failure.
    own_failure = classify_jobs([
        {"name": "procedural-shadow-runtime", "steps": [{"name": "run"}], "conclusion": "failure"},
        {"name": "another-skill", "steps": [{"name": "run"}], "conclusion": "success"},
    ], focus_job="procedural-shadow-runtime")
    if own_failure["failed_jobs"] != ["procedural-shadow-runtime"]:
        print("SELFTEST RED: focusing hid the focused leg's own failure", file=sys.stderr)
        return 1

    # A run that never contained this leg cannot be evidence about it.
    absent_leg = classify_jobs([
        {"name": "another-skill", "steps": [{"name": "run"}], "conclusion": "success"},
    ], focus_job="procedural-shadow-runtime")
    if absent_leg["focus_job_present"]:
        print("SELFTEST RED: an absent focus job reported present", file=sys.stderr)
        return 1

    run = {"id": 1, "name": "Skill Suites", "head_sha": "a" * 40, "status": "completed",
           "conclusion": "success", "event": "push", "run_attempt": 1}
    manifest = {"files": [{"path": "suite.log", "sha256": "b" * 64}]}

    good = build_receipt(run, green, "a" * 40, {"exit_code": 0}, manifest, "c" * 64)
    if good["close_state"] != "PASS" or good["actions_run"]["failure_class"] != "NONE":
        print(f"SELFTEST RED: a clean run did not close PASS: {good['close_state']}", file=sys.stderr)
        return 1

    blocked = build_receipt(run, budget_blocked, "a" * 40, {"exit_code": 64}, None, "c" * 64)
    if blocked["close_state"] != "BLOCKED":
        print(f"SELFTEST RED: a provider-blocked run closed {blocked['close_state']}, not BLOCKED",
              file=sys.stderr)
        return 1
    if blocked["actions_run"]["failure_class"] != "PROVIDER_ALLOCATION":
        print("SELFTEST RED: a provider failure was not named as one", file=sys.stderr)
        return 1

    red = build_receipt(run, real_failure, "a" * 40, {"exit_code": 0}, manifest, "c" * 64)
    if red["close_state"] != "FAIL" or red["actions_run"]["failure_class"] != "REPOSITORY_TEST":
        print(f"SELFTEST RED: a repository test failure closed {red['close_state']}", file=sys.stderr)
        return 1

    wrong_head = build_receipt(run, green, "9" * 40, {"exit_code": 0}, manifest, "c" * 64)
    if wrong_head["close_state"] == "PASS":
        print("SELFTEST RED: a run on another head closed PASS", file=sys.stderr)
        return 1

    unreplayable = build_receipt(run, green, "a" * 40, {"exit_code": 2}, manifest, "c" * 64)
    if unreplayable["close_state"] == "PASS":
        print("SELFTEST RED: a bundle that failed offline replay closed PASS", file=sys.stderr)
        return 1

    unbound = build_receipt(run, green, "a" * 40, {"exit_code": 0},
                            {"files": [{"path": "x"}]}, "c" * 64)
    if unbound["close_state"] == "PASS":
        print("SELFTEST RED: a manifest entry without a digest closed PASS", file=sys.stderr)
        return 1

    print(
        "SELFTEST GREEN: a runnerless run is PROVIDER_ALLOCATION and closes BLOCKED, never FAIL; "
        "a started job that failed is REPOSITORY_TEST and closes FAIL; a wrong head, an "
        "unreplayable bundle and an undigested manifest entry each refuse PASS"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--expected-sha", help="the head SHA this run must have executed")
    parser.add_argument("--job-name", default="procedural-shadow-runtime",
                        help="the matrix leg this receipt is about; sibling legs are recorded, not graded")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if not args.run_id or not args.output:
        print("ACTIONS-RECEIPT-INVALID: --run-id and --output are required unless --selftest",
              file=sys.stderr)
        return INVALID

    expected = args.expected_sha or subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()

    try:
        run = gh_api(f"/repos/{REPOSITORY}/actions/runs/{args.run_id}")
        jobs_payload = gh_api(f"/repos/{REPOSITORY}/actions/runs/{args.run_id}/jobs")
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(f"ACTIONS-RECEIPT-INVALID {exc}", file=sys.stderr)
        return INVALID

    jobs = classify_jobs(jobs_payload.get("jobs", []), args.job_name)

    manifest: dict[str, Any] | None = None
    bundle_verify = {"exit_code": 64, "stdout": "", "stderr": "artifact not downloaded"}
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "bundle"
        download = subprocess.run(
            ["gh", "run", "download", str(args.run_id), "--repo", REPOSITORY, "--dir", str(target)],
            capture_output=True, text=True, check=False,
        )
        if download.returncode == 0:
            roots = [path.parent for path in target.rglob("MANIFEST.json")]
            if roots:
                bundle_verify = verify_bundle_offline(roots[0])
                manifest = json.loads((roots[0] / "MANIFEST.json").read_text(encoding="utf-8"))
        else:
            bundle_verify["stderr"] = download.stderr.strip()[-400:]

    skill_digest = sha256_bytes((SKILL / "SKILL.md").read_bytes())
    receipt = build_receipt(run, jobs, expected, bundle_verify, manifest, skill_digest)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    detail = receipt["actions_run"]
    print(f"ACTIONS-RECEIPT close={receipt['close_state']} run={detail['run_id']} "
          f"head={detail['head_sha'][:12]} expected={detail['expected_sha'][:12]} "
          f"failure_class={detail['failure_class']} "
          f"jobs_with_steps={detail['jobs']['jobs_with_steps']}/{detail['jobs']['job_count']} "
          f"replay_exit={detail['bundle_offline_replay']['exit_code']} "
          f"manifest_files={detail['manifest_file_count']}")
    return 0 if receipt["close_state"] == "PASS" else REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
