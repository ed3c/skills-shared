#!/usr/bin/env python3
"""Drive the Arena portable-Skill runner as the second physical harness.

`export_skill_eval_runtime.py` + `collect_skill_up_executor_evidence.py` cover
the skill-up lane: build immutable run inputs, then normalize the executor's own
report into non-promotable executor evidence. This file is the same two moves
for the Arena control plane's `skill-execution run` entry point, which executes
one command in a detached disposable Git worktree bound to an exact commit and
an exact Skill directory digest.

Two things make the Arena lane different, and both are recorded rather than
smoothed over:

  * Arena installs nothing. skill-up copies the Skill into `.claude/skills/`, so
    the agent discovers it; Arena checks the subject commit out as it is, so the
    prompt must name the canonical Skill path. That is a real harness delta and
    it belongs in the evidence, not in a footnote.
  * Arena's worktree is destroyed on exit (`cleanup=required`). The produced
    artifacts survive only because `file_content` assertions copy their bytes
    into the receipt's content-addressed store before cleanup. `collect`
    rebuilds a workspace from that store so the repository's own deterministic
    verifier -- not Arena's assertions and not skill-up's judge -- decides.

Neither subcommand grants promotion authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from export_skill_eval_runtime import RUNTIME_PROTOCOLS, public_case

ROOT = Path(__file__).resolve().parents[1]
# Matches evals/runtime/executors/bettor-arena.json. `arena` is already taken by
# a different repository's control plane, and two harnesses answering to one
# name is how a run trace ends up bound to an adapter that never ran it.
EXECUTOR = "bettor-arena"
# skill-execution assertion ids the collector reads bytes back from. Keeping the
# ids here rather than rediscovering them by shape means a renamed assertion is
# a loud FATAL in `collect`, not a silently empty workspace.
ARTIFACT_ASSERTION_PREFIX = "artifact-content-"


def exact_sha(value: str, name: str) -> str:
    if len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise SystemExit(f"{name} must be an exact lowercase 40-char commit SHA")
    return value


def canonical_bytes(value) -> bytes:
    """Byte-for-byte the Arena runner's canonical form.

    This mirrors an external contract, so it is duplicated rather than imported.
    Drift is not silent: the runner recomputes the assertion-set digest and
    refuses the request when the two disagree.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_json(value) -> str:
    return digest_bytes(canonical_bytes(value))


def directory_digest(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        item
        for item in root.rglob("*")
        if item.is_file() and "__pycache__" not in item.parts and not item.name.endswith(".pyc")
    )
    for item in files:
        digest.update(item.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return value


def run_identity(case_id: str, condition: str, skill_sha: str | None, provider: str,
                 model: str, engine: str, harness_version: str, repetition: int) -> str:
    """The skill-up collector's layout plus the harness name.

    That collector can leave the name implicit because it pins one harness SHA
    as a constant. A second harness cannot: two adapters whose versions are both
    40-hex would otherwise be able to collide onto one run_id. Pairing across
    harnesses is by (case, condition, sample), not by run_id, so naming the
    harness here costs nothing downstream.
    """
    parts = [case_id, condition, skill_sha or "none", provider, model, engine,
             EXECUTOR, harness_version, f"repetition:{repetition}"]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:24]


def build_prompt(case: dict, skill_source: str) -> str:
    protocol = RUNTIME_PROTOCOLS.get(case["id"])
    if protocol is None:
        raise SystemExit(f"case {case['id']!r} has no reviewed physical runtime protocol")
    delivery = (
        "The Skill under evaluation is checked out in this worktree at "
        f"`{skill_source}/SKILL.md`. This harness installs nothing into "
        "`.claude/skills`, so read that file before deciding how to route."
    )
    return case["task"]["prompt"].rstrip() + "\n\n" + delivery + "\n\n" + protocol["prompt_suffix"]


def build_assertions(case_id: str, expected_artifacts: list[str], commit: str) -> dict:
    assertions = [
        {
            "id": "subject-is-requested-commit",
            "type": "subject_match",
            "severity": "hard",
            "expected": {"commit": commit},
        },
        {
            "id": "agent-exited-cleanly",
            "type": "exit_code",
            "severity": "advisory",
            "expected": {"equals": 0},
        },
    ]
    for index, relative in enumerate(expected_artifacts):
        assertions.append({
            "id": f"artifact-exists-{index}",
            "type": "file_exists",
            "severity": "hard",
            "expected": {"path": relative, "kind": "file"},
        })
        # file_content is what copies the produced bytes into the receipt store
        # before the worktree is destroyed. `contains "{"` is deliberately weak:
        # this assertion exists to preserve evidence, and the deterministic
        # verifier replay is what judges it.
        assertions.append({
            "id": f"{ARTIFACT_ASSERTION_PREFIX}{index}",
            "type": "file_content",
            "severity": "hard",
            "expected": {"path": relative, "contains": "{"},
        })
    return {
        "schema_version": "skill-assertion-set/v1",
        "id": f"{case_id}-arena-v1",
        "subject_policy": "exact-request-subject",
        "assertions": assertions,
    }


def command_export(args) -> int:
    exact_sha(args.skill_sha, "--skill-sha")
    exact_sha(args.commit, "--commit")
    _, case = public_case(args.case)
    if case["skill"] != args.skill:
        raise SystemExit(f"case {args.case} belongs to skill {case['skill']!r}, not {args.skill!r}")
    expected_artifacts = list(RUNTIME_PROTOCOLS[case["id"]]["collect_artifacts"])

    skill_root = Path(args.skill_root).resolve()
    if not (skill_root / "SKILL.md").is_file():
        raise SystemExit(f"skill root has no SKILL.md: {skill_root}")
    skill_source = f"skills/{args.skill}"

    assertions = build_assertions(case["id"], expected_artifacts, args.commit)
    request = {
        "schema_version": "skill-execution-request/v1",
        "request_id": f"{case['id']}-{EXECUTOR}-{args.condition}-rep{args.repetition}",
        "subject": {"repository": args.repository, "commit": args.commit, "tree": args.tree},
        "skill": {
            "name": args.skill,
            "canonical_source": f"{args.repository}/{skill_source}",
            "content_digest": directory_digest(skill_root),
        },
        "command": {
            "executable": "claude",
            "argv": [
                "--settings", json.dumps({"disableAllHooks": True}, separators=(",", ":")),
                "-p",
                "--permission-mode=bypassPermissions",
                "--output-format", "json",
                "--model", args.model_name,
            ],
            "cwd": ".",
            "stdin": {"mode": "literal", "literal": build_prompt(case, skill_source)},
            # No credential-shaped name is admissible here and the runner refuses
            # one outright; the agent CLI authenticates from its own host login
            # state under HOME. Egress configuration is host-specific and must be
            # named at the call site: the first physical run failed with
            # `ENOTFOUND` because the runner's explicit allowlist dropped the
            # host's proxy variables, and an unreachable API is indistinguishable
            # from a model that declined to produce the artifacts.
            "env_allowlist": sorted({"HOME", "PATH", "TMPDIR", "USER", *args.env_allow}),
            "timeout_ms": args.timeout_ms,
        },
        "sandbox": {
            "network": "inherit",
            "process_group": True,
            "writable_paths": ["evidence", "artifacts", ".claude"],
            "read_only_paths": ["skills", "scripts", "evals"],
            "max_output_bytes": 4_000_000,
            "cleanup": "required",
        },
        "expected_artifacts": expected_artifacts,
        "assertion_set": {"id": assertions["id"], "digest": digest_json(assertions)},
        "promotion_authority": False,
    }
    dump(Path(args.assertions_out), assertions)
    dump(Path(args.request_out), request)
    print(args.request_out)
    return 0


def artifact_bytes(receipt_dir: Path, digest: str) -> bytes:
    if not digest.startswith("sha256:") or len(digest) != 71:
        raise SystemExit(f"assertion evidence is not a content digest: {digest!r}")
    blob = receipt_dir / "artifacts" / digest.split(":", 1)[1]
    if not blob.is_file():
        raise SystemExit(f"receipt names artifact {digest} but the store has no such blob")
    data = blob.read_bytes()
    if digest_bytes(data) != digest:
        raise SystemExit(f"artifact store blob does not match its own digest: {digest}")
    return data


def rebuild_workspace(receipt: dict, request: dict, receipt_dir: Path, workspace: Path) -> list[str]:
    by_id = {row.get("id"): row for row in receipt.get("assertions", [])}
    rebuilt: list[str] = []
    for index, relative in enumerate(request.get("expected_artifacts", [])):
        row = by_id.get(f"{ARTIFACT_ASSERTION_PREFIX}{index}")
        if row is None:
            raise SystemExit(f"receipt has no content assertion for expected artifact {relative}")
        if row.get("status") != "PASS":
            # A produced-but-unreadable artifact and a never-produced one must not
            # look alike downstream; refuse instead of writing a partial workspace.
            raise SystemExit(f"artifact {relative} was not captured: status={row.get('status')}")
        evidence = row.get("evidence") or []
        if not evidence:
            raise SystemExit(f"artifact {relative} assertion carries no evidence digest")
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(artifact_bytes(receipt_dir, str(evidence[0])))
        rebuilt.append(relative)
    return rebuilt


def agent_metrics(receipt: dict, receipt_dir: Path) -> dict:
    """Token accounting is ABSENT unless the agent's own stdout carries it."""
    metrics = {
        "duration_ms": int(receipt.get("timing", {}).get("duration_ms", 0) or 0),
        "input_tokens": 0,
        "output_tokens": 0,
        "token_accounting": "ABSENT",
    }
    digest = receipt.get("artifacts", {}).get("stdout")
    if not isinstance(digest, str):
        return metrics
    try:
        payload = json.loads(artifact_bytes(receipt_dir, digest).decode("utf-8"))
    except (SystemExit, UnicodeDecodeError, json.JSONDecodeError):
        return metrics
    usage = payload.get("usage") if isinstance(payload, dict) else None
    if not isinstance(usage, dict):
        return metrics
    input_tokens, output_tokens = usage.get("input_tokens"), usage.get("output_tokens")
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        return metrics
    metrics.update({
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "token_accounting": "PASS",
    })
    return metrics


def command_collect(args) -> int:
    exact_sha(args.skill_sha, "--skill-sha")
    exact_sha(args.eval_suite_sha, "--eval-suite-sha")
    receipt_dir = Path(args.receipt_dir).resolve()
    receipt = load(receipt_dir / "receipt.json")
    request = load(receipt_dir / "request.json")
    if receipt.get("schema_version") != "skill-execution-receipt/v1":
        raise SystemExit("unsupported Arena receipt schema")
    if receipt.get("request_id") != request.get("request_id"):
        raise SystemExit("receipt/request identity mismatch")
    if receipt.get("subject") != request.get("subject"):
        raise SystemExit("receipt subject does not match the requested subject")

    workspace = Path(args.workspace_out).resolve()
    rebuilt = rebuild_workspace(receipt, request, receipt_dir, workspace)
    metrics = agent_metrics(receipt, receipt_dir)
    status = str(receipt.get("status", "")).lower()
    evidence = {
        "schema_version": "skill-eval-executor-evidence/v1",
        "run_id": run_identity(args.case_id, args.condition, args.skill_sha, args.model_provider,
                               args.model_name, args.engine, args.harness_version, args.repetition),
        "case_id": args.case_id,
        "condition": args.condition,
        "skill": args.skill,
        "skill_sha": args.skill_sha,
        "eval_suite_sha": args.eval_suite_sha,
        "sampling": {"repetition_index": args.repetition, "seed_controlled": False, "model_seed": None},
        "model": {"provider": args.model_provider, "name": args.model_name},
        "harness": {"name": EXECUTOR, "version": args.harness_version, "engine": args.engine},
        "outcome": {
            "passed": status == "pass",
            "status": status,
            "verifier": "arena/portable-assertions",
            "duration_ms": metrics["duration_ms"],
            "input_tokens": metrics["input_tokens"],
            "output_tokens": metrics["output_tokens"],
            "token_accounting": metrics["token_accounting"],
        },
        "skill_delivery": "canonical-path-in-worktree",
        "rebuilt_workspace": {"path": str(workspace), "artifacts": rebuilt},
        "raw_report": {"path": str(receipt_dir / "receipt.json"),
                       "sha256": hashlib.sha256((receipt_dir / "receipt.json").read_bytes()).hexdigest()},
        "promotion": {
            "eligible": False,
            "reason": "executor assertions are not deterministic promotion authority",
            "required_next_receipt": "skill-eval-verifier-receipt/v1",
        },
    }
    dump(Path(args.output), evidence)
    print(evidence["run_id"])
    return 0


def _selftest() -> int:
    """Cheap verification surface: the digest and rebuild paths must refuse the
    shapes that would otherwise produce a confidently empty workspace."""
    import tempfile

    failures: list[str] = []
    assertions = build_assertions("case-x", ["evidence/run.json"], "a" * 40)
    if digest_json(assertions) != digest_json(json.loads(json.dumps(assertions))):
        failures.append("assertion digest is not stable across a JSON round trip")
    with tempfile.TemporaryDirectory(prefix="arena-lane.") as raw:
        work = Path(raw)
        store = work / "artifacts"
        store.mkdir()
        payload = b'{"case_id": "case-x"}'
        digest = digest_bytes(payload)
        (store / digest.split(":", 1)[1]).write_bytes(payload)
        request = {"expected_artifacts": ["evidence/run.json"]}
        good = {"assertions": [{"id": f"{ARTIFACT_ASSERTION_PREFIX}0", "status": "PASS",
                                "evidence": [digest]}]}
        rebuild_workspace(good, request, work, work / "ws")
        if (work / "ws" / "evidence" / "run.json").read_bytes() != payload:
            failures.append("rebuild_workspace did not restore the captured bytes")

        for name, receipt in (
            ("failed assertion", {"assertions": [{"id": f"{ARTIFACT_ASSERTION_PREFIX}0",
                                                  "status": "FAIL", "evidence": [digest]}]}),
            ("missing assertion", {"assertions": []}),
            ("evidence without a digest", {"assertions": [{"id": f"{ARTIFACT_ASSERTION_PREFIX}0",
                                                           "status": "PASS", "evidence": []}]}),
            ("digest with no blob", {"assertions": [{"id": f"{ARTIFACT_ASSERTION_PREFIX}0",
                                                     "status": "PASS",
                                                     "evidence": ["sha256:" + "b" * 64]}]}),
        ):
            try:
                rebuild_workspace(receipt, request, work, work / f"ws-{len(failures)}")
            except SystemExit:
                continue
            failures.append(f"rebuild_workspace accepted {name}")

        tampered = digest_bytes(b"other")
        (store / tampered.split(":", 1)[1]).write_bytes(payload)
        try:
            artifact_bytes(work, tampered)
            failures.append("artifact_bytes accepted a blob that fails its own digest")
        except SystemExit:
            pass

    if failures:
        for failure in failures:
            print(f"SELFTEST RED: {failure}", file=sys.stderr)
        return 2
    print("SELFTEST GREEN: arena lane export/collect guards refuse 5 silent-empty shapes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    sub = parser.add_subparsers(dest="command")

    export = sub.add_parser("export", help="materialize the Arena request and assertion set")
    export.add_argument("--case", required=True)
    export.add_argument("--skill", required=True)
    export.add_argument("--condition", required=True, choices=["current_skill", "candidate_skill"])
    export.add_argument("--repository", required=True)
    export.add_argument("--commit", required=True)
    export.add_argument("--tree", required=True)
    export.add_argument("--skill-sha", required=True)
    export.add_argument("--skill-root", required=True)
    export.add_argument("--model-name", required=True)
    export.add_argument("--repetition", type=int, required=True)
    export.add_argument("--timeout-ms", type=int, default=600_000)
    export.add_argument(
        "--env-allow", action="append", default=[], metavar="NAME",
        help="extra host environment variable name the agent needs (e.g. HTTPS_PROXY). "
             "The runner refuses credential-shaped names outright; only names travel "
             "into the request, never values.",
    )
    export.add_argument("--request-out", required=True)
    export.add_argument("--assertions-out", required=True)
    export.set_defaults(handler=command_export)

    collect = sub.add_parser("collect", help="normalize an Arena receipt into executor evidence")
    collect.add_argument("--receipt-dir", required=True)
    collect.add_argument("--case-id", required=True)
    collect.add_argument("--condition", required=True, choices=["current_skill", "candidate_skill"])
    collect.add_argument("--skill", required=True)
    collect.add_argument("--skill-sha", required=True)
    collect.add_argument("--eval-suite-sha", required=True)
    collect.add_argument("--model-provider", required=True)
    collect.add_argument("--model-name", required=True)
    collect.add_argument("--engine", required=True)
    collect.add_argument("--harness-version", required=True)
    collect.add_argument("--repetition", type=int, required=True)
    collect.add_argument("--workspace-out", required=True)
    collect.add_argument("--output", required=True)
    collect.set_defaults(handler=command_collect)

    args = parser.parse_args()
    if args.selftest:
        return _selftest()
    if args.command is None:
        parser.error("a subcommand or --selftest is required")
    if args.repetition < 1:
        raise SystemExit("--repetition must be >= 1")
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
