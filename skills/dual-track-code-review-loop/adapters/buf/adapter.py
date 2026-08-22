#!/usr/bin/env python3
"""Turn one pinned Protobuf baseline and one candidate into a
`dtcr/contract-compatibility-result/v1` plus a `dtcr/fact-plane-receipt/v1`,
and nothing else.

What this adapter is allowed to say
-----------------------------------
`buf breaking` reports the sentence *this interface artifact changed in a way
that is not wire/JSON compatible with that one*. It is not *this change may
ship*. Every result this file emits carries `grants` fixed to all-false by the
frozen schema, and no code path here writes a merge, a deployment, a release
or a task pass. The frozen schemas in `../../references/schemas/` are
read-only inputs; this adapter never edits them and validates against them
rather than against a local copy.

Optional, and explicit about it
--------------------------------
Not every task touches a Protobuf contract. When the exact task's declared
source blobs contain no `.proto` file, this adapter never runs the compare: it
emits `outcome: NOT_APPLICABLE` instead, with a real, reproducible
`artifact_digest` on both sides -- the sha256 of buf's own deterministic
output when it is handed a zero-file image, never a placeholder, a zero-hash
or an omitted field (`buf build` on a genuinely empty input refuses with
`Failure: image contains no files`, and that refusal is itself real,
reproducible bytes this adapter is entitled to hash). When buf itself cannot
be invoked at all (the binary is absent), this adapter emits no receipt at
all: it prints `NOT_EXERCISED` on stderr and exits 70, mirroring
`adapters/tree-sitter/adapter.py`'s `PROVIDER_ABSENT` idiom. `NOT_EXERCISED`
and `NOT_APPLICABLE` are not the same state and this adapter never lets one
stand in for the other.

Two modes, one emitter
-----------------------
`replay` reads a fixture request: recorded `buf build`/`buf breaking`/`buf
lint`/`buf --version` output, captured from a real run, replayed with no
provider on the machine. `live` shells out to the real CLI. Both funnel
through `emit_applicable`/`emit_not_applicable`, so the deterministic tests
exercise the code the live path uses rather than a stand-in for it.

Refusals are named
-------------------
Every guard raises `Refusal` carrying the falsifier name it exists to kill,
so a planted defect proves *its own* guard rather than dying on an unrelated
schema keyword. The falsifiers owned here (the rest are refused by the frozen
schemas themselves; see `selftest.py` for the full table):

    MUTABLE_BASELINE_ALIAS
    SOURCE_SCHEMA_DIGEST_ABSENT
    BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING
    GENERATED_ARTIFACT_USED_WITHOUT_SOURCE_BINDING
    BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED
    NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE
    BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS
    STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE

BSR/network publication is outside this adapter entirely: `ALLOWED_BUF_SUBCOMMANDS`
is a closed set of three read-only subcommands, `push`/`registry`/`login` are
never dispatched by any code path here, and no function in this file opens a
socket.

Usage
-----
    adapter.py replay <request.json> [--out <result.json>]
    adapter.py live --repo <dir> --baseline-commit <sha> \
        --baseline-dir <repo-relative dir> --candidate-dir <repo-relative dir> \
        [--baseline-cached-digest <sha256>] [--record <fixture-dir>] [--out <result.json>]
    adapter.py live-not-applicable --repo <dir> --baseline-commit <sha> \
        [--record <fixture-dir>] [--out <result.json>]

Exit 0 emitted, 2 refused, 70 the provider is absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ADAPTER_DIR = Path(__file__).resolve().parent
SKILL = ADAPTER_DIR.parents[1]
SCHEMAS = SKILL / "references" / "schemas"

COMPAT_SCHEMA = "dtcr/contract-compatibility-result/v1"
RECEIPT_SCHEMA = "dtcr/fact-plane-receipt/v1"
REQUEST_SCHEMA = "dtcr/buf-run-request/v1"

EXECUTABLE_NAME = "buf"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

# The maximal buf breaking category. Every narrower category (PACKAGE,
# WIRE_JSON, WIRE) is a subset of what FILE catches; a config that does not
# request it, or that adds any `except` rule at all, is a narrower net than
# this adapter is willing to certify a clean verdict under.
REQUIRED_BREAKING_CATEGORY = "FILE"

# BSR/network publication is out of scope for this deterministic adapter
# (issue #549). This is the entire set of subcommands any code path here may
# ever shell out to; there is no argument, flag or config value anywhere in
# this file that reaches `push`, `registry` or `login`.
ALLOWED_BUF_SUBCOMMANDS = ("build", "lint", "breaking")


class Refusal(Exception):
    """A named falsifier reached its own guard."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def binding_id(prefix: str, material: bytes) -> str:
    return f"{prefix}-{sha256_hex(material)[:16]}"


# --------------------------------------------------------------------------
# guards -- each one is the one place its named falsifier is refused
# --------------------------------------------------------------------------
def check_baseline_ref(ref: str) -> None:
    """MUTABLE_BASELINE_ALIAS. Refused before any git or buf invocation: a
    branch, a tag or HEAD names a moving baseline, and a compatibility verdict
    against a moving baseline is not reproducible. This is stricter than the
    frozen schema's own `baseline.commit` pattern check (BUF_WRONG_BASELINE,
    refused_by properties.baseline.properties.commit.pattern): that one
    refuses a bad value already written into an emitted document; this one
    refuses the CLI argument before a single buf process is spent comparing
    against something that might move under it."""
    if not HEX40.match(ref):
        raise Refusal(
            "MUTABLE_BASELINE_ALIAS",
            f"--baseline-commit {ref!r} is not an exact 40-hex commit; a branch name, a tag or "
            "HEAD names a baseline that can move between this invocation and the next one",
        )


def check_declared_blobs(applicable: bool, declared_blobs: list[str]) -> None:
    """SOURCE_SCHEMA_DIGEST_ABSENT. An applicable lane with no declared
    `.proto` blobs has no schema/module input to bind an input_digest to; the
    contradiction is refused here rather than laundered into an empty digest."""
    if applicable and not declared_blobs:
        raise Refusal(
            "SOURCE_SCHEMA_DIGEST_ABSENT",
            "the applicable lane was entered with zero declared .proto blobs; there is no source "
            "to derive a schema/module input digest from",
        )


def check_breaking_config(config: dict[str, Any]) -> None:
    """BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING. Refused before buf runs:
    a narrower `use` list or any `except` entry can make a genuinely breaking
    change invisible to the exact same binary and the exact same artifacts
    (verified against this repo's own fixture: `except: [FIELD_NO_DELETE]`
    turns a real field-removal from a 3-finding breaking exit into a clean
    exit 0). The floor is fixed rather than configurable, because a
    configurable floor is a second knob this same falsifier could turn."""
    breaking = config.get("breaking", {})
    use = breaking.get("use", [])
    excepts = breaking.get("except", [])
    if excepts:
        raise Refusal(
            "BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING",
            f"breaking.except={excepts!r} narrows the ruleset below the floor; any excepted rule "
            "is a rule this adapter can no longer certify a clean verdict under",
        )
    if REQUIRED_BREAKING_CATEGORY not in use:
        raise Refusal(
            "BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING",
            f"breaking.use={use!r} does not include the maximal {REQUIRED_BREAKING_CATEGORY!r} "
            "category; a narrower category is a narrower net over the same artifacts",
        )


def check_no_bsr_intent(subcommand: str) -> None:
    """BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS. The closed set this
    adapter ever shells buf out with. `push`, `registry` and `login` are not
    strings any function in this file can produce here; this guard is what
    keeps that true under a future edit rather than by convention alone."""
    if subcommand not in ALLOWED_BUF_SUBCOMMANDS:
        raise Refusal(
            "BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS",
            f"{subcommand!r} is outside the closed set {ALLOWED_BUF_SUBCOMMANDS}; BSR account "
            "access is not content rights and this adapter never attempts either",
        )


def check_provider_probe(identity: dict[str, Any]) -> None:
    """BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED. `shutil.which` finding a
    path on PATH is start-readiness; it is not the same claim as `buf
    --version` having actually run and returned something. This guard refuses
    an identity block that was not built from a real, successful probe."""
    if identity.get("probe_exit_code") != 0 or not str(identity.get("version", "")).strip():
        raise Refusal(
            "BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED",
            f"provider identity carries probe_exit_code={identity.get('probe_exit_code')!r} and "
            f"version={identity.get('version')!r}; being found on PATH is not the same claim as "
            "having actually run",
        )
    if not HEX64.match(str(identity.get("executable_sha256", ""))):
        raise Refusal("PROVIDER_IDENTITY_ABSENT", "provider.executable_sha256 is not a sha256")


def check_artifact_source_binding(image_supplied: bool, source_blobs: list[str]) -> None:
    """GENERATED_ARTIFACT_USED_WITHOUT_SOURCE_BINDING. A pre-built
    FileDescriptorSet handed to this adapter in place of a source directory
    carries no source binding of its own; without a declared blob list it is
    an artifact this adapter cannot trace back to text anyone can review."""
    if image_supplied and not source_blobs:
        raise Refusal(
            "GENERATED_ARTIFACT_USED_WITHOUT_SOURCE_BINDING",
            "a pre-built artifact was supplied with no source blob list; a generated artifact "
            "used in place of source with no binding back to it is unreviewable",
        )


def check_stale_baseline(cached_digest: str | None, recomputed_digest: str) -> None:
    """STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE. This adapter always
    recomputes the baseline artifact_digest from a real buf build; if a caller
    also supplies a previously cached digest for what it believes is the same
    baseline and the two disagree, the cached one describes a contract that
    has since changed and is refused rather than trusted."""
    if cached_digest and cached_digest != recomputed_digest:
        raise Refusal(
            "STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE",
            f"cached baseline digest {cached_digest} does not match {recomputed_digest} freshly "
            "recomputed for the declared baseline commit; the baseline's contract has moved since "
            "the cached digest was recorded",
        )


def decide_applicability(declared_proto_blobs: list[str]) -> str:
    """The dispatcher-level fork: which lane `live` enters. This is the first
    barrier, not the only one -- `emit_applicable`'s own `if not
    declared_blobs` guard is the second and is what
    NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE's falsifier row
    in `selftest.py` targets, because that is the one place a zero-source
    compare could still fall through to a clean pass if this function's own
    caller ever stopped checking its result."""
    return "APPLICABLE" if declared_proto_blobs else "NOT_APPLICABLE"


# --------------------------------------------------------------------------
# provider identity and invocation
# --------------------------------------------------------------------------
def find_cli() -> str | None:
    explicit = os.environ.get("DTCR_BUF_BIN")
    if explicit:
        return explicit if Path(explicit).is_file() else None
    return shutil.which(EXECUTABLE_NAME)


def cli_identity(binary: str) -> dict[str, Any]:
    """The only place a provider identity is built. `probe_exit_code` is
    carried into the identity block precisely so `check_provider_probe` can
    tell a real invocation from a bare PATH lookup."""
    result = subprocess.run([binary, "--version"], capture_output=True, text=True)
    version = result.stdout.strip()
    if result.returncode != 0 or not version:
        raise Refusal(
            "BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED",
            f"'{binary} --version' exited {result.returncode} with stdout {version!r}",
        )
    return {
        "version": version,
        "executable_sha256": sha256_hex(Path(binary).read_bytes()),
        "probe_exit_code": result.returncode,
    }


def run_buf(binary: str, subcommand: str, args: list[str], *, cwd: Path, binary_output: bool = False) -> subprocess.CompletedProcess:
    check_no_bsr_intent(subcommand)
    return subprocess.run(
        [binary, subcommand, *args],
        cwd=cwd,
        capture_output=True,
        text=not binary_output,
    )


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def live_subject(repo: Path) -> dict[str, str]:
    commit = git(repo, "rev-parse", "HEAD")
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    root = git(repo, "rev-list", "--max-parents=0", "HEAD").splitlines()[-1]
    return {
        "repository_binding_id": binding_id("DTCR-RB", root.encode("ascii")),
        "commit": commit,
        "tree": tree,
    }


def declared_proto_blobs(repo: Path, candidate_dir: str) -> list[str]:
    listed = git(repo, "ls-files", candidate_dir)
    return sorted(path for path in listed.splitlines() if path.endswith(".proto"))


def build_artifact(binary: str, module_dir: Path) -> bytes:
    result = run_buf(binary, "build", [str(module_dir), "-o", "-#format=binpb"], cwd=module_dir, binary_output=True)
    if result.returncode != 0:
        raise Refusal(
            "PROVIDER_INVOCATION_FAILED",
            f"buf build {module_dir} exited {result.returncode}: {result.stderr.decode('utf-8', 'replace').strip()}",
        )
    return result.stdout


def probe_empty_module(binary: str, empty_image: Path) -> dict[str, Any]:
    """The real, reproducible value the NOT_APPLICABLE digest convention
    rests on. `buf build` on a genuinely empty image does not succeed -- it
    refuses with a fixed message -- and that refusal is itself deterministic
    bytes this adapter is entitled to hash, not a placeholder it invented."""
    result = run_buf(binary, "build", [str(empty_image), "-o", "-#format=json"], cwd=empty_image.parent, binary_output=True)
    payload = {
        "exit_code": result.returncode,
        "stdout": result.stdout.decode("utf-8", "replace"),
        "stderr": result.stderr.decode("utf-8", "replace"),
    }
    return {"digest": sha256_hex(canonical(payload)), **payload}


def parse_breaking_findings(stdout: str, repo_prefix: str) -> list[dict[str, Any]]:
    findings = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        path = row["path"]
        if repo_prefix and path.startswith(repo_prefix):
            path = path[len(repo_prefix):]
        findings.append(
            {
                "finding_kind": "BREAKING",
                "rule_id": row["type"],
                "location": f"{path}:{row['start_line']}:{row['start_column']}",
                "detail": row["message"],
            }
        )
    return findings


def run_breaking(binary: str, repo: Path, candidate_dir: Path, baseline_dir: Path, *, use: list[str], excepts: list[str]) -> dict[str, Any]:
    config: dict[str, Any] = {"version": "v2", "breaking": {"use": list(use)}}
    if excepts:
        config["breaking"]["except"] = list(excepts)
    check_breaking_config(config)
    result = run_buf(
        binary,
        "breaking",
        [str(candidate_dir), "--against", str(baseline_dir), "--config", json.dumps(config), "--error-format=json"],
        cwd=repo,
    )
    # buf breaking exits 100 when it found breaking changes; that is a clean
    # invocation reporting a real verdict, not a crash. Anything else nonzero
    # is a broken invocation and is refused rather than read as a verdict.
    if result.returncode not in (0, 100):
        raise Refusal(
            "PROVIDER_INVOCATION_FAILED",
            f"buf breaking exited {result.returncode}: {result.stderr.strip()}",
        )
    findings = parse_breaking_findings(result.stdout, str(repo) + os.sep)
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "findings": findings,
        "config": config,
        "config_digest": sha256_hex(canonical(config)),
    }


def run_lint(binary: str, repo: Path, candidate_dir: Path) -> dict[str, Any]:
    result = run_buf(binary, "lint", [str(candidate_dir), "--error-format=json"], cwd=repo)
    if result.returncode not in (0, 100):
        raise Refusal(
            "PROVIDER_INVOCATION_FAILED",
            f"buf lint exited {result.returncode}: {result.stderr.strip()}",
        )
    return {"exit_code": result.returncode, "stdout": result.stdout}


# --------------------------------------------------------------------------
# emitters -- the shared core both `live` and `replay` funnel through
# --------------------------------------------------------------------------
def provider_block(identity: dict[str, Any], config_digest: str, ruleset_digest: str) -> dict[str, Any]:
    check_provider_probe(identity)
    material = canonical([EXECUTABLE_NAME, identity["version"], identity["executable_sha256"], config_digest, ruleset_digest])
    return {
        "provider_binding_id": binding_id("DTCR-PB", material),
        "executable_name": EXECUTABLE_NAME,
        "version": identity["version"],
        "executable_sha256": identity["executable_sha256"],
        "config_digest": config_digest,
        "ruleset_digest": ruleset_digest,
    }


def _fact_plane_receipt(
    *,
    subject: dict[str, str],
    provider: dict[str, Any],
    runs: list[dict[str, Any]],
    summary: str,
    sequence: int,
) -> dict[str, Any]:
    provider_runs = []
    for run in runs:
        exit_code = run["exit_code"]
        provider_runs.append(
            {
                "provider_binding_id": provider["provider_binding_id"],
                "executable_name": EXECUTABLE_NAME,
                "version": provider["version"],
                "executable_sha256": provider["executable_sha256"],
                "config_digest": run.get("config_digest", provider["config_digest"]),
                "input_digest": run["input_digest"],
                "output_digest": run["output_digest"],
                "exit_code": exit_code,
                "outcome": "PASS" if exit_code == 0 else "FAIL",
                "warnings": run.get("warnings", []),
                "omissions": run.get("omissions", []),
            }
        )
    bundle_digest = sha256_hex(canonical(provider_runs))
    return {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": "DTCR-FR-001",
        "subject": dict(subject),
        "arrival": "STATIC",
        "provider_runs": provider_runs,
        "ledger_event": {
            "event_digest": bundle_digest,
            "sequence": sequence,
            "ledger_schema_digest": sha256_hex((SCHEMAS / "fact-plane-receipt.schema.json").read_bytes()),
        },
        "bundle_digest": bundle_digest,
        "coverage_ceiling_ref": "DTCR-CC-001",
        "summary": summary,
        "grants": {
            "task_pass": False,
            "merge": False,
            "permission": False,
            "secret": False,
            "production": False,
            "release": False,
            "semantic_truth": False,
        },
    }


def emit_applicable(
    *,
    subject: dict[str, str],
    baseline_commit: str,
    baseline_artifact_name: str,
    candidate_artifact_name: str,
    baseline_bytes: bytes,
    candidate_bytes: bytes,
    breaking_run: dict[str, Any],
    lint_run: dict[str, Any],
    identity: dict[str, Any],
    declared_blobs: list[str],
    baseline_cached_digest: str | None,
    sequence: int = 1,
) -> dict[str, Any]:
    check_baseline_ref(baseline_commit)
    # Reachable from both `live` (which also checks before ever shelling out
    # to `buf breaking`) and `replay` (which never shells out at all): the
    # guard has to sit on the shared emitter, or a replayed fixture built
    # under a weakened config would replay clean without the falsifier that
    # is supposed to catch it ever firing.
    check_breaking_config(breaking_run["config"])

    baseline_digest = sha256_hex(baseline_bytes)
    candidate_digest = sha256_hex(candidate_bytes)
    check_stale_baseline(baseline_cached_digest, baseline_digest)

    ruleset_digest = sha256_hex(canonical(breaking_run["config"]["breaking"]))
    provider = provider_block(identity, breaking_run["config_digest"], ruleset_digest)

    findings = breaking_run["findings"]
    # NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE is refused
    # here, at the one place `outcome` is decided, deliberately distinct from
    # `check_declared_blobs` (SOURCE_SCHEMA_DIGEST_ABSENT, called by the `live`
    # dispatcher before this function is ever reached). That guard is the
    # dispatcher refusing to *enter* the applicable lane; this one is the
    # emitter itself refusing to let a zero-source compare fall through to a
    # clean verdict if it is ever reached anyway -- which is exactly the
    # "unguarded code path that defaults to pass" shape this falsifier names.
    # `selftest.py` proves it by calling this function directly with
    # `declared_blobs=[]`, bypassing the dispatcher-level guard entirely.
    if not declared_blobs:
        raise Refusal(
            "NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE",
            "emit_applicable was reached with zero declared .proto blobs; an outcome computed here "
            f"would default to {'NO_BREAKING_CHANGE_DETECTED' if not findings else 'BREAKING_CHANGE_DETECTED'} "
            "for a task that has no Protobuf contract to compare",
        )
    outcome = "BREAKING_CHANGE_DETECTED" if findings else "NO_BREAKING_CHANGE_DETECTED"

    compat = {
        "schema": COMPAT_SCHEMA,
        "result_id": "DTCR-CK-001",
        "subject": dict(subject),
        "baseline": {
            "commit": baseline_commit,
            "artifact_name": baseline_artifact_name,
            "artifact_digest": baseline_digest,
        },
        "candidate": {
            "artifact_name": candidate_artifact_name,
            "artifact_digest": candidate_digest,
        },
        "provider": provider,
        "outcome": outcome,
        "findings": findings,
        "grants": {"deployment": False, "merge": False, "release": False, "task_pass": False},
    }

    input_digest = sha256_hex(canonical({"baseline_digest": baseline_digest, "candidate_digest": candidate_digest, "declared_blobs": declared_blobs}))
    receipt = _fact_plane_receipt(
        subject=subject,
        provider=provider,
        runs=[
            {
                "exit_code": 0,
                "input_digest": sha256_hex(canonical({"role": "baseline_source"})),
                "output_digest": baseline_digest,
                "omissions": [],
            },
            {
                "exit_code": 0,
                "input_digest": sha256_hex(canonical({"role": "candidate_source", "blobs": declared_blobs})),
                "output_digest": candidate_digest,
                "omissions": [],
            },
            {
                "exit_code": breaking_run["exit_code"],
                "config_digest": breaking_run["config_digest"],
                "input_digest": input_digest,
                "output_digest": sha256_hex(breaking_run["stdout"].encode("utf-8")),
                "warnings": [f"{len(findings)} breaking finding(s)"] if findings else [],
                "omissions": [],
            },
            {
                "exit_code": lint_run["exit_code"],
                "input_digest": candidate_digest,
                "output_digest": sha256_hex(lint_run["stdout"].encode("utf-8")),
                "warnings": ["lint is advisory here; it is not a compatibility input"],
                "omissions": [],
            },
        ],
        summary=(
            f"buf {identity['version']} compared {candidate_artifact_name} against {baseline_artifact_name}@"
            f"{baseline_commit[:12]} under the {REQUIRED_BREAKING_CATEGORY} breaking category and found "
            f"{len(findings)} finding(s)."
        ),
        sequence=sequence,
    )
    return {"contract_compatibility_result": compat, "fact_plane_receipt": receipt}


def emit_not_applicable(
    *,
    subject: dict[str, str],
    baseline_commit: str,
    identity: dict[str, Any],
    probe: dict[str, Any],
    sequence: int = 1,
) -> dict[str, Any]:
    check_baseline_ref(baseline_commit)
    config_digest = sha256_hex(
        canonical({"probe": "empty_module_build", "argv_role": [EXECUTABLE_NAME, "build", "<EMPTY_IMAGE>", "-o", "-#format=json"]})
    )
    ruleset_digest = sha256_hex(canonical({"use": [], "reason": "no_protobuf_sources_declared"}))
    provider = provider_block(identity, config_digest, ruleset_digest)

    compat = {
        "schema": COMPAT_SCHEMA,
        "result_id": "DTCR-CK-001",
        "subject": dict(subject),
        "baseline": {
            "commit": baseline_commit,
            "artifact_name": "no-protobuf-contract",
            "artifact_digest": probe["digest"],
        },
        "candidate": {
            "artifact_name": "no-protobuf-contract",
            "artifact_digest": probe["digest"],
        },
        "provider": provider,
        "outcome": "NOT_APPLICABLE",
        "rationale": (
            "zero .proto blobs are declared in this exact task's changed-path denominator; the "
            "Protobuf contract-compatibility lane does not apply to this task"
        ),
        "findings": [],
        "grants": {"deployment": False, "merge": False, "release": False, "task_pass": False},
    }

    receipt = _fact_plane_receipt(
        subject=subject,
        provider=provider,
        runs=[
            {
                "exit_code": probe["exit_code"],
                "config_digest": config_digest,
                "input_digest": sha256_hex(b""),
                "output_digest": probe["digest"],
                "warnings": ["buf was invoked against a zero-file image and refused it, by design"],
                "omissions": [],
            }
        ],
        summary=(
            f"buf {identity['version']} was probed against a zero-.proto exact task and reported no "
            "applicable Protobuf contract; the empty-module refusal was hashed as the artifact digest."
        ),
        sequence=sequence,
    )
    return {"contract_compatibility_result": compat, "fact_plane_receipt": receipt}


# --------------------------------------------------------------------------
# live mode
# --------------------------------------------------------------------------
def run_live_applicable(args: argparse.Namespace) -> dict[str, Any]:
    check_baseline_ref(args.baseline_commit)
    binary = find_cli()
    if binary is None:
        raise Refusal("PROVIDER_ABSENT", "no buf executable on PATH and DTCR_BUF_BIN unset")
    identity = cli_identity(binary)

    repo = args.repo.resolve()
    subject = live_subject(repo)

    baseline_dir_abs = repo / args.baseline_dir
    candidate_dir_abs = repo / args.candidate_dir

    source_blobs = [s for s in (args.baseline_source_blobs or "").split(",") if s]
    check_artifact_source_binding(args.baseline_image is not None, source_blobs)

    declared = declared_proto_blobs(repo, args.candidate_dir)
    lane = decide_applicability(declared)
    if lane != "APPLICABLE":
        raise Refusal(
            "NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE",
            f"{args.candidate_dir} declares zero .proto blobs; the `live` (applicable) command was "
            "invoked for a task the applicability gate routes to NOT_APPLICABLE instead",
        )

    baseline_bytes = args.baseline_image.read_bytes() if args.baseline_image else build_artifact(binary, baseline_dir_abs)
    candidate_bytes = build_artifact(binary, candidate_dir_abs)

    breaking_run = run_breaking(binary, repo, candidate_dir_abs, baseline_dir_abs, use=[REQUIRED_BREAKING_CATEGORY], excepts=[])
    lint_run = run_lint(binary, repo, candidate_dir_abs)

    emitted = emit_applicable(
        subject=subject,
        baseline_commit=args.baseline_commit,
        baseline_artifact_name=Path(args.baseline_dir).name,
        candidate_artifact_name=Path(args.candidate_dir).name,
        baseline_bytes=baseline_bytes,
        candidate_bytes=candidate_bytes,
        breaking_run=breaking_run,
        lint_run=lint_run,
        identity=identity,
        declared_blobs=declared,
        baseline_cached_digest=args.baseline_cached_digest,
    )
    if args.record is not None:
        write_applicable_fixture(
            args.record.resolve(),
            subject=subject,
            args=args,
            baseline_bytes=baseline_bytes,
            candidate_bytes=candidate_bytes,
            breaking_run=breaking_run,
            lint_run=lint_run,
            identity=identity,
            declared=declared,
        )
    return emitted


def run_live_not_applicable(args: argparse.Namespace) -> dict[str, Any]:
    check_baseline_ref(args.baseline_commit)
    binary = find_cli()
    if binary is None:
        raise Refusal("PROVIDER_ABSENT", "no buf executable on PATH and DTCR_BUF_BIN unset")
    identity = cli_identity(binary)
    repo = args.repo.resolve()
    subject = live_subject(repo)

    empty_image = Path(args.empty_image) if args.empty_image else None
    cleanup = False
    if empty_image is None:
        import tempfile

        fd, name = tempfile.mkstemp(prefix="dtcr-buf-empty-", suffix=".binpb")
        os.close(fd)
        empty_image = Path(name)
        cleanup = True
    try:
        probe = probe_empty_module(binary, empty_image)
    finally:
        if cleanup:
            empty_image.unlink(missing_ok=True)

    emitted = emit_not_applicable(subject=subject, baseline_commit=args.baseline_commit, identity=identity, probe=probe)
    if args.record is not None:
        write_not_applicable_fixture(args.record.resolve(), subject=subject, baseline_commit=args.baseline_commit, probe=probe, identity=identity)
    return emitted


def write_applicable_fixture(
    record_dir: Path,
    *,
    subject: dict[str, str],
    args: argparse.Namespace,
    baseline_bytes: bytes,
    candidate_bytes: bytes,
    breaking_run: dict[str, Any],
    lint_run: dict[str, Any],
    identity: dict[str, Any],
    declared: list[str],
) -> None:
    """Freeze one live run as a replayable fixture: the real bytes each real
    invocation produced, plus a request.json `run_replay` can read with no
    provider on the machine. This is how `fixtures/breaking-pair/` was
    captured; re-running with `--record` reproduces the same shape."""
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / "baseline_build.binpb").write_bytes(baseline_bytes)
    (record_dir / "candidate_build.binpb").write_bytes(candidate_bytes)
    (record_dir / "breaking.stdout").write_text(breaking_run["stdout"], encoding="utf-8")
    (record_dir / "lint.stdout").write_text(lint_run["stdout"], encoding="utf-8")
    request = {
        "schema": REQUEST_SCHEMA,
        "kind": "applicable",
        "subject": subject,
        "baseline_commit": args.baseline_commit,
        "baseline_artifact_name": Path(args.baseline_dir).name,
        "candidate_artifact_name": Path(args.candidate_dir).name,
        "baseline_build": "baseline_build.binpb",
        "candidate_build": "candidate_build.binpb",
        "breaking_stdout": "breaking.stdout",
        "breaking_exit_code": breaking_run["exit_code"],
        "breaking_config": breaking_run["config"],
        "lint_stdout": "lint.stdout",
        "lint_exit_code": lint_run["exit_code"],
        "declared_blobs": declared,
        "identity": identity,
        "baseline_cached_digest": args.baseline_cached_digest,
    }
    (record_dir / "request.json").write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_not_applicable_fixture(
    record_dir: Path, *, subject: dict[str, str], baseline_commit: str, probe: dict[str, Any], identity: dict[str, Any]
) -> None:
    record_dir.mkdir(parents=True, exist_ok=True)
    request = {
        "schema": REQUEST_SCHEMA,
        "kind": "not_applicable",
        "subject": subject,
        "baseline_commit": baseline_commit,
        "probe": probe,
        "identity": identity,
    }
    (record_dir / "request.json").write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# replay mode
# --------------------------------------------------------------------------
def run_replay(request_path: Path) -> dict[str, Any]:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if request.get("schema") != REQUEST_SCHEMA:
        raise Refusal("REQUEST_SCHEMA_UNKNOWN", f"{request_path.name}: schema {request.get('schema')!r}")
    base = request_path.parent
    kind = request["kind"]
    subject = request["subject"]
    identity = request["identity"]

    if kind == "not_applicable":
        probe = request["probe"]
        return emit_not_applicable(subject=subject, baseline_commit=request["baseline_commit"], identity=identity, probe=probe)

    if kind != "applicable":
        raise Refusal("REQUEST_SCHEMA_UNKNOWN", f"{request_path.name}: unknown kind {kind!r}")

    baseline_bytes = (base / request["baseline_build"]).read_bytes()
    candidate_bytes = (base / request["candidate_build"]).read_bytes()
    breaking_stdout = (base / request["breaking_stdout"]).read_text(encoding="utf-8") if request.get("breaking_stdout") else ""
    lint_stdout = (base / request["lint_stdout"]).read_text(encoding="utf-8") if request.get("lint_stdout") else ""

    breaking_run = {
        "exit_code": request["breaking_exit_code"],
        "stdout": breaking_stdout,
        "findings": parse_breaking_findings(breaking_stdout, ""),
        "config": request["breaking_config"],
        "config_digest": sha256_hex(canonical(request["breaking_config"])),
    }
    lint_run = {"exit_code": request["lint_exit_code"], "stdout": lint_stdout}

    return emit_applicable(
        subject=subject,
        baseline_commit=request["baseline_commit"],
        baseline_artifact_name=request["baseline_artifact_name"],
        candidate_artifact_name=request["candidate_artifact_name"],
        baseline_bytes=baseline_bytes,
        candidate_bytes=candidate_bytes,
        breaking_run=breaking_run,
        lint_run=lint_run,
        identity=identity,
        declared_blobs=request["declared_blobs"],
        baseline_cached_digest=request.get("baseline_cached_digest"),
    )


# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)

    replay = sub.add_parser("replay", help="emit from a recorded fixture request, no provider needed")
    replay.add_argument("request", type=Path)
    replay.add_argument("--out", type=Path)

    live = sub.add_parser("live", help="run the buf CLI against a real baseline/candidate pair")
    live.add_argument("--repo", type=Path, required=True)
    live.add_argument("--baseline-commit", required=True)
    live.add_argument("--baseline-dir", required=True)
    live.add_argument("--candidate-dir", required=True)
    live.add_argument("--baseline-cached-digest")
    live.add_argument("--baseline-image", type=Path)
    live.add_argument("--baseline-source-blobs")
    live.add_argument("--record", type=Path)
    live.add_argument("--out", type=Path)

    not_applicable = sub.add_parser("live-not-applicable", help="probe buf against a zero-.proto exact task")
    not_applicable.add_argument("--repo", type=Path, required=True)
    not_applicable.add_argument("--baseline-commit", required=True)
    not_applicable.add_argument("--empty-image", type=Path)
    not_applicable.add_argument("--record", type=Path)
    not_applicable.add_argument("--out", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.mode == "replay":
            emitted = run_replay(args.request)
        elif args.mode == "live":
            emitted = run_live_applicable(args)
        else:
            emitted = run_live_not_applicable(args)
    except Refusal as refusal:
        if refusal.reason == "PROVIDER_ABSENT":
            print(f"NOT_EXERCISED {refusal}", file=sys.stderr)
            return 70
        print(f"REFUSED {refusal}", file=sys.stderr)
        return 2
    text = json.dumps(emitted, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
