#!/usr/bin/env python3
"""Turn one exact source subject into a `dtcr/contract-compatibility-result/v1`
and a `dtcr/fact-plane-receipt/v1` for the optional Buf/Protobuf compatibility
lane, without making Buf or Protobuf universal (issue #549).

What this adapter is allowed to say
------------------------------------
Most subjects carry no Protobuf contract at all. For those, the only honest
verdict is `NOT_APPLICABLE`, produced by a deterministic file-name scan that
needs no `buf` binary: applicability is a glob over the declared subject, not
a provider invocation. When a subject does declare a contract artifact
(`*.proto`, `buf.yaml`, `buf.gen.yaml`, `buf.work.yaml`) and no `buf`
executable is available on the host, the verdict is `PROVIDER_UNAVAILABLE` --
again with no invented provider identity. Both verdicts are `grants`-const
`false` in every field the frozen schema exposes: a compatibility checker
observes an interface, and merge, release, deployment and task admission are
decisions people make holding that observation, never decisions this file
makes for them.

What this adapter refuses to fake
----------------------------------
The `buf` CLI is absent on the runtime this file was written against (`which
buf` empty), and its `breaking`/`lint` invocation contract has not been
verified against a real binary from a primary source reachable on this host.
Building a parser for an unverified external contract is exactly the
"[推論]-grade equivalence" this repository's law forbids, so this file does
not invent one: `find_cli` and `cli_identity` bind a real `buf --version`
identity when a real binary is present (generic, verifiable, safe), but no
code path here shells out to `buf breaking` or claims a `NO_BREAKING_CHANGE_
DETECTED` / `BREAKING_CHANGE_DETECTED` outcome. That is the `DTCR_BUF_ADAPTER_
VERIFIED` terminal's upgrade path, left for whoever admits a real `buf`
binary and can capture a fixture from it.

Refusals are named
-------------------
Every guard raises `Refusal` carrying the falsifier name it exists to kill.
The falsifiers owned here (the rest are refused by the frozen schemas
themselves; see `selftest.py` for the full table, including issue #549's
required ten):

    MUTABLE_OR_WRONG_SOURCE_SUBJECT
    PROTOBUF_CONTRACTS_PRESENT_BUT_CLAIMED_NOT_APPLICABLE
    NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE
    PROVIDER_UNAVAILABLE_CLAIMED_WHILE_BINARY_PRESENT
    BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED
    MUTABLE_BASELINE_ALIAS
    SOURCE_SCHEMA_DIGEST_ABSENT
    BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING
    GENERATED_ARTIFACT_USED_WITHOUT_SOURCE_BINDING
    STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE
    RECEIPT_DIGEST_TAMPERED

Usage
-----
    adapter.py check --repo <path> [--path <repo-relative> ...] \
        [--out <result.json>] [--receipt <receipt.json>]
    adapter.py identify [--bin <path>]

`check` derives the subject and the declared path list from Git itself (or
from `--path`, repeatable) and decides `NOT_APPLICABLE` or
`PROVIDER_UNAVAILABLE` from that evidence -- it never accepts a caller-
asserted outcome, which is what keeps `NO_PROTOBUF_TASK_FORCED_TO_PASS_
INSTEAD_OF_NOT_APPLICABLE` and its siblings unrepresentable from this
entrypoint. `identify` only probes a `buf` binary's own `--version`, unrelated
to applicability.

Exit 0 emitted, 2 refused, 64 unusable input, 70 the provider is absent for a
command that requires one.
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
from typing import Any, Iterable

ADAPTER_DIR = Path(__file__).resolve().parent
SKILL = ADAPTER_DIR.parents[1]
SCHEMAS = SKILL / "references" / "schemas"

RESULT_SCHEMA = "dtcr/contract-compatibility-result/v1"
RECEIPT_SCHEMA = "dtcr/fact-plane-receipt/v1"

ADAPTER_NAME = "dtcr-buf-adapter"
ADAPTER_VERSION = "1.0.0"
EXECUTABLE_NAME = "buf"

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

# The closed, deterministic contract-artifact vocabulary. A repository-relative
# path matches applicability by name alone -- no file is opened and no `buf`
# binary is consulted, which is what makes NOT_APPLICABLE reachable with zero
# provider on the machine.
CONTRACT_EXACT_NAMES = ("buf.yaml", "buf.gen.yaml", "buf.work.yaml")

# A ref that names a moving point rather than an exact commit. HEX40 already
# refuses anything that is not 40 hex characters; this list catches the
# well-known moving names that happen to also fail that pattern, so the
# refusal message can say which kind of mistake it was.
MUTABLE_ALIASES = {"main", "master", "head", "latest", "trunk", "release"}


class Refusal(Exception):
    """A named falsifier reached its own guard."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


class Unusable(Exception):
    """The input could not be read at all, which is not the same as a refusal."""


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def binding_id(prefix: str, material: bytes) -> str:
    return f"{prefix}-{sha256_hex(material)[:16]}"


def file_digest(path: Path) -> str:
    return sha256_hex(Path(path).read_bytes())


# --------------------------------------------------------------------------
# applicability -- a name glob over the declared subject, no provider needed
# --------------------------------------------------------------------------
def contract_glob_match(path: str) -> bool:
    name = Path(path).name
    return name in CONTRACT_EXACT_NAMES or name.endswith(".proto")


def detect_applicability(declared_paths: Iterable[str]) -> tuple[bool, list[str]]:
    """Whether any declared path names a Protobuf/Buf contract artifact, and
    which ones. Pure string matching over the paths the caller declares --
    this never touches a filesystem or a `buf` binary, so it is reachable on
    any host, with or without a provider."""
    basis = sorted({path for path in declared_paths if contract_glob_match(path)})
    return bool(basis), basis


def scope_digest(declared_paths: Iterable[str]) -> str:
    return sha256_hex(canonical({"declared_paths": sorted(set(declared_paths))}))


# --------------------------------------------------------------------------
# subject
# --------------------------------------------------------------------------
def check_subject(subject: dict[str, Any]) -> None:
    for key in ("commit", "tree"):
        value = subject.get(key, "")
        if not HEX40.match(value):
            raise Refusal(
                "MUTABLE_OR_WRONG_SOURCE_SUBJECT",
                f"subject.{key}={value!r} is not an exact 40-hex object id; a branch, a tag, HEAD "
                "or latest names a moving tree and a verdict dated to a moving tree is dated to nothing",
            )
    if not re.match(r"^DTCR-RB-[0-9a-f]{16}$", subject.get("repository_binding_id", "")):
        raise Refusal(
            "MUTABLE_OR_WRONG_SOURCE_SUBJECT",
            "subject.repository_binding_id must be the opaque binding id; a clone URL, an "
            "owner/name pair or a working-copy path each describe one account or one machine",
        )


def adapter_identity() -> dict[str, str]:
    """This adapter's own identity, used as the `provider` for the two lanes
    that never invoke `buf`: a deterministic glob and a presence check are
    still runs, and a run without an identity behind it is unattributable."""
    return {
        "executable_name": ADAPTER_NAME,
        "version": ADAPTER_VERSION,
        "executable_sha256": file_digest(Path(__file__)),
    }


# --------------------------------------------------------------------------
# baseline resolution -- MUTABLE_BASELINE_ALIAS, STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE
# --------------------------------------------------------------------------
def resolve_baseline_commit(value: str) -> str:
    """Refuse before a baseline is ever pinned, not just after: the frozen
    result schema refuses a branch name in the *emitted instance*
    (BUF_WRONG_BASELINE); this refuses one at the *input* to pinning it, which
    is where a caller who meant to resolve a ref first would otherwise slip a
    moving name straight through."""
    if not HEX40.match(value):
        kind = "a well-known moving name" if value.lower() in MUTABLE_ALIASES else "not an exact 40-hex commit"
        raise Refusal(
            "MUTABLE_BASELINE_ALIAS",
            f"baseline commit {value!r} is {kind}; a branch, tag, HEAD or latest names a point that "
            "moves, and a baseline pinned to a moving point stops being the baseline it named",
        )
    return value


def require_source_bytes(label: str, data: bytes | None) -> bytes:
    if not data:
        raise Refusal(
            "SOURCE_SCHEMA_DIGEST_ABSENT",
            f"{label} has no backing bytes to digest; an artifact_digest with nothing behind it is a "
            "string that looks like a digest, not a digest of the schema it names",
        )
    return data


def bind_baseline(*, commit: str, artifact_name: str, artifact_bytes: bytes | None, claimed_digest: str) -> tuple[str, str, str]:
    """Recompute the baseline digest from bytes actually read, every time.
    STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE is what a cached digest from
    an earlier read, carried forward past a later edit to the same artifact,
    would otherwise look like: unchanged."""
    resolve_baseline_commit(commit)
    data = require_source_bytes(f"baseline {artifact_name}", artifact_bytes)
    actual = sha256_hex(data)
    if actual != claimed_digest:
        raise Refusal(
            "STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE",
            f"claimed artifact_digest {claimed_digest} does not match the sha256 {actual} of the "
            f"baseline bytes read at commit {commit}; a digest computed before the contract changed "
            "and reused afterward names a baseline that no longer exists",
        )
    return commit, artifact_name, actual


def bind_candidate(*, artifact_path: str, artifact_bytes: bytes | None, declared_paths: Iterable[str]) -> tuple[str, str]:
    """A candidate artifact must trace to a path the subject actually
    declared. A generated file (a `.pb.go`, a build output) that nobody
    declared as source has no source binding a checker could attribute a
    finding to."""
    declared = set(declared_paths)
    if artifact_path not in declared:
        raise Refusal(
            "GENERATED_ARTIFACT_USED_WITHOUT_SOURCE_BINDING",
            f"{artifact_path} is not among the subject's declared paths; a candidate not traceable "
            "to a declared source blob is a generated artifact standing in for a source it was never bound to",
        )
    data = require_source_bytes(artifact_path, artifact_bytes)
    return artifact_path, sha256_hex(data)


def resolve_config(*, config_bytes: bytes | None, claimed_ruleset_digest: str) -> str:
    """The ruleset identity is the config's own bytes, re-read and re-hashed,
    never a label carried forward from an earlier, stricter config.
    BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING is a caller who narrowed the
    enabled rule categories but kept quoting the old, wider ruleset_digest."""
    data = require_source_bytes("buf config", config_bytes)
    actual = sha256_hex(data)
    if actual != claimed_ruleset_digest:
        raise Refusal(
            "BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING",
            f"claimed ruleset_digest {claimed_ruleset_digest} does not match the sha256 {actual} of "
            "the config bytes actually supplied; a weakened config quoting the old digest would report "
            "the old, stricter ruleset's identity over the new, weaker check",
        )
    return actual


# --------------------------------------------------------------------------
# provider (buf itself) -- identity only, never an invented invocation
# --------------------------------------------------------------------------
def find_cli() -> str | None:
    explicit = os.environ.get("DTCR_BUF_BIN")
    if explicit:
        return explicit if Path(explicit).is_file() else None
    return shutil.which(EXECUTABLE_NAME)


def cli_identity(binary: str) -> dict[str, str]:
    """`buf --version` only: generic across CLIs and safe to depend on without
    a verified `buf`-specific contract. Presence on PATH is not identity --
    BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED is a binary found but never
    actually asked, or asked and answering nothing usable, treated as if it
    had proven itself anyway."""
    try:
        result = subprocess.run([binary, "--version"], capture_output=True, text=True)
    except OSError as error:
        raise Refusal(
            "BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED",
            f"{binary} is on PATH but could not be executed ({error}); a path that resolves but does "
            "not run is not an identity this adapter can bind",
        ) from error
    version = result.stdout.strip().splitlines()[0].strip() if result.stdout.strip() else ""
    if result.returncode != 0 or not version:
        raise Refusal(
            "BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED",
            f"{binary} was found on PATH but `--version` exited {result.returncode} with "
            f"{'no' if not version else 'unusable'} output; presence on PATH is not identity, and a "
            "binary that cannot report its own version cannot be promoted to an exercised provider run",
        )
    return {"version": version, "executable_sha256": file_digest(Path(binary))}


# --------------------------------------------------------------------------
# result / receipt construction
# --------------------------------------------------------------------------
def build_compatibility_result(
    *,
    subject: dict[str, Any],
    outcome: str,
    rationale: str,
    findings: list[dict[str, Any]],
    baseline: dict[str, str],
    candidate: dict[str, str],
    provider_identity: dict[str, str],
    config_digest: str,
    ruleset_digest: str,
    result_id: str = "DTCR-CK-001",
) -> dict[str, Any]:
    resolve_baseline_commit(baseline["commit"])
    material = canonical(
        [
            provider_identity["executable_name"],
            provider_identity["version"],
            provider_identity["executable_sha256"],
            config_digest,
            ruleset_digest,
        ]
    )
    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "result_id": result_id,
        "subject": dict(subject),
        "baseline": dict(baseline),
        "candidate": dict(candidate),
        "provider": {
            "provider_binding_id": binding_id("DTCR-PB", material),
            "executable_name": provider_identity["executable_name"],
            "version": provider_identity["version"],
            "executable_sha256": provider_identity["executable_sha256"],
            "config_digest": config_digest,
            "ruleset_digest": ruleset_digest,
        },
        "outcome": outcome,
        "rationale": rationale,
        "findings": findings,
        "grants": {"deployment": False, "merge": False, "release": False, "task_pass": False},
    }
    return result


def emit_not_applicable(*, subject: dict[str, Any], declared_paths: list[str], result_id: str = "DTCR-CK-001") -> dict[str, Any]:
    check_subject(subject)
    applicable, basis = detect_applicability(declared_paths)
    if applicable:
        raise Refusal(
            "PROTOBUF_CONTRACTS_PRESENT_BUT_CLAIMED_NOT_APPLICABLE",
            f"{len(basis)} declared path(s) match the contract glob ({basis[:3]}{'...' if len(basis) > 3 else ''}); "
            "NOT_APPLICABLE describes a subject with nothing in scope, and this is not that subject",
        )
    digest = scope_digest(declared_paths)
    identity = adapter_identity()
    return build_compatibility_result(
        subject=subject,
        outcome="NOT_APPLICABLE",
        rationale=(
            f"{len(declared_paths)} declared path(s) were scanned by name and none is a *.proto file "
            f"or one of {', '.join(CONTRACT_EXACT_NAMES)}; no Buf/Protobuf contract task applies at "
            "this subject, so no buf binary was sought"
        ),
        findings=[],
        baseline={"commit": subject["commit"], "artifact_name": "NO_PROTOBUF_CONTRACT_IN_SCOPE", "artifact_digest": digest},
        candidate={"artifact_name": "NO_PROTOBUF_CONTRACT_IN_SCOPE", "artifact_digest": digest},
        provider_identity=identity,
        config_digest=digest,
        ruleset_digest=digest,
        result_id=result_id,
    )


def emit_provider_unavailable(*, subject: dict[str, Any], declared_paths: list[str], result_id: str = "DTCR-CK-001") -> dict[str, Any]:
    check_subject(subject)
    applicable, basis = detect_applicability(declared_paths)
    if not applicable:
        raise Refusal(
            "NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE",
            "PROVIDER_UNAVAILABLE was requested but no declared path matches the contract glob; an "
            "absent provider is not the reason to report when there was nothing for it to check",
        )
    found = find_cli()
    if found is not None:
        raise Refusal(
            "PROVIDER_UNAVAILABLE_CLAIMED_WHILE_BINARY_PRESENT",
            f"a buf executable resolved at {found}; PROVIDER_UNAVAILABLE describes a host with no "
            "provider, and this is not that host",
        )
    digest = sha256_hex(canonical({"basis": basis}))
    identity = adapter_identity()
    return build_compatibility_result(
        subject=subject,
        outcome="PROVIDER_UNAVAILABLE",
        rationale=(
            f"{len(basis)} declared path(s) match the contract glob ({', '.join(basis)}), and no buf "
            "executable resolved from DTCR_BUF_BIN or PATH; the compatibility check needs a real buf "
            "binary and none is on this host, so the lane is blocked on the provider, not clean"
        ),
        findings=[],
        baseline={"commit": subject["commit"], "artifact_name": "PROTOBUF_CONTRACT_PRESENT_PROVIDER_ABSENT", "artifact_digest": digest},
        candidate={"artifact_name": "PROTOBUF_CONTRACT_PRESENT_PROVIDER_ABSENT", "artifact_digest": digest},
        provider_identity=identity,
        config_digest=digest,
        ruleset_digest=digest,
        result_id=result_id,
    )


def emit_receipt(
    *,
    subject: dict[str, Any],
    result: dict[str, Any],
    provider_runs: list[dict[str, Any]],
    sequence: int = 1,
    receipt_id: str = "DTCR-FR-001",
    coverage_ceiling_ref: str = "DTCR-CC-001",
    summary: str,
) -> dict[str, Any]:
    bundle_digest = sha256_hex(canonical(result))
    return {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": receipt_id,
        "subject": dict(subject),
        "arrival": "STATIC",
        "provider_runs": provider_runs,
        "ledger_event": {
            "event_digest": bundle_digest,
            "sequence": sequence,
            "ledger_schema_digest": sha256_hex((SCHEMAS / "fact-plane-receipt.schema.json").read_bytes()),
        },
        "bundle_digest": bundle_digest,
        "coverage_ceiling_ref": coverage_ceiling_ref,
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


def verify_receipt(*, receipt: dict[str, Any], result: dict[str, Any]) -> None:
    """What a receipt has to hold against the result it claims to wrap: its
    own ledger event digest and its bundle_digest are both the sha256 of the
    result body, recomputed here rather than trusted from the stored field.
    A receipt whose digest was hand-edited after emission describes a result
    it no longer matches, and reads exactly like one that still does."""
    expected = sha256_hex(canonical(result))
    for field, actual in (
        ("bundle_digest", receipt.get("bundle_digest")),
        ("ledger_event.event_digest", receipt.get("ledger_event", {}).get("event_digest")),
    ):
        if actual != expected:
            raise Refusal(
                "RECEIPT_DIGEST_TAMPERED",
                f"{field}={actual} does not match the sha256 {expected} of the result this receipt "
                "claims to wrap; the two are supposed to be the same computation, done twice",
            )


def applicability_provider_run(*, declared_paths: list[str], applicable: bool, basis: list[str]) -> dict[str, Any]:
    identity = adapter_identity()
    digest = scope_digest(declared_paths)
    return {
        "provider_binding_id": binding_id("DTCR-PB", canonical([identity["executable_name"], identity["version"], identity["executable_sha256"]])),
        "executable_name": identity["executable_name"],
        "version": identity["version"],
        "executable_sha256": identity["executable_sha256"],
        "config_digest": digest,
        "input_digest": digest,
        "output_digest": sha256_hex(canonical({"applicable": applicable, "basis": basis})),
        "exit_code": 0,
        "outcome": "PASS",
        "warnings": [],
        "omissions": [] if applicable else ["no buf binary was sought because no declared path matched the contract glob"],
    }


# A stable, documented sentinel for a provider that was never found: the
# digest of a literal marker string, never the bytes of a binary. This is not
# a claimed buf identity -- warnings on the run say so explicitly.
_ABSENT_MARKER = b"buf:provider-absent"


def absent_provider_run(*, declared_paths: list[str], basis: list[str]) -> dict[str, Any]:
    digest = scope_digest(declared_paths)
    return {
        "provider_binding_id": binding_id("DTCR-PB", _ABSENT_MARKER),
        "executable_name": EXECUTABLE_NAME,
        "version": "absent",
        "executable_sha256": sha256_hex(_ABSENT_MARKER),
        "config_digest": digest,
        "input_digest": digest,
        "output_digest": sha256_hex(canonical({"basis": basis})),
        "exit_code": None,
        "outcome": "ABSENT",
        "warnings": [
            "executable_sha256 above digests the literal sentinel 'buf:provider-absent', not any "
            "binary; no buf executable was found on DTCR_BUF_BIN or PATH to have a real identity",
        ],
        "omissions": ["BSR/network publication and account-authorized comparisons are outside this deterministic adapter"],
    }


# --------------------------------------------------------------------------
# live subject (Git)
# --------------------------------------------------------------------------
def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def live_subject(repo: Path, paths: list[str] | None) -> tuple[dict[str, Any], list[str]]:
    commit = git(repo, "rev-parse", "HEAD")
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    root = git(repo, "rev-list", "--max-parents=0", "HEAD").splitlines()[-1]
    subject = {
        "repository_binding_id": binding_id("DTCR-RB", root.encode("ascii")),
        "commit": commit,
        "tree": tree,
    }
    if paths is not None:
        declared = sorted(set(paths))
    else:
        listing = git(repo, "ls-tree", "-r", "--name-only", "HEAD")
        declared = sorted(line for line in listing.splitlines() if line)
    return subject, declared


def run_check(*, repo: Path, paths: list[str] | None, sequence: int = 1) -> dict[str, Any]:
    """The only entrypoint that decides which of the two closable lanes
    applies, and it decides from evidence it gathers itself: it never accepts
    a caller-asserted outcome, which is what keeps every "claimed X while
    reality is Y" falsifier unrepresentable from here."""
    subject, declared_paths = live_subject(repo, paths)
    applicable, basis = detect_applicability(declared_paths)
    applicability_run = applicability_provider_run(declared_paths=declared_paths, applicable=applicable, basis=basis)

    if not applicable:
        result = emit_not_applicable(subject=subject, declared_paths=declared_paths)
        provider_runs = [applicability_run]
        summary = (
            f"{len(declared_paths)} declared path(s) scanned at {subject['commit'][:12]}; none is a "
            "Protobuf/Buf contract artifact, so DTCR_BUF_ADAPTER_NOT_APPLICABLE_WITH_RECEIPT applies "
            "and no buf binary was sought."
        )
    else:
        binary = find_cli()
        if binary is None:
            result = emit_provider_unavailable(subject=subject, declared_paths=declared_paths)
            provider_runs = [applicability_run, absent_provider_run(declared_paths=declared_paths, basis=basis)]
            summary = (
                f"{len(basis)} of {len(declared_paths)} declared path(s) match the contract glob at "
                f"{subject['commit'][:12]}, and no buf executable resolved; the live/VERIFIED lane "
                "stays BLOCKED_ON_PROVIDER."
            )
        else:
            # A real buf binary is present and a contract is in scope. This
            # adapter version binds identity only (see module docstring) and
            # does not invent buf's breaking-change invocation contract, so it
            # stops here rather than emit an outcome it cannot back with a
            # verified run.
            raise Unusable(
                f"a buf executable resolved at {binary} and {len(basis)} declared path(s) are in "
                "scope, but this adapter version does not invoke `buf breaking` without a verified "
                "command contract (see module docstring); run `adapter.py identify` for the bound "
                "identity, or admit a captured fixture before wiring the exercised lane"
            )

    receipt = emit_receipt(
        subject=subject,
        result=result,
        provider_runs=provider_runs,
        summary=summary,
    )
    verify_receipt(receipt=receipt, result=result)
    return {"result": result, "receipt": receipt, "applicable": applicable, "basis": basis, "declared_paths": declared_paths}


def run_identify(binary: str | None) -> dict[str, str] | None:
    resolved = binary or find_cli()
    if resolved is None:
        return None
    return {"executable_name": EXECUTABLE_NAME, **cli_identity(resolved)}


# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)

    check = sub.add_parser("check", help="derive applicability/provider state from Git and emit a receipt")
    check.add_argument("--repo", type=Path, default=Path.cwd())
    check.add_argument("--path", action="append", dest="paths", help="repo-relative path; repeatable, default is the whole tree")
    check.add_argument("--out", type=Path)
    check.add_argument("--receipt", type=Path)

    identify = sub.add_parser("identify", help="probe a buf binary's own --version; unrelated to applicability")
    identify.add_argument("--bin", dest="binary")

    args = parser.parse_args(argv)
    try:
        if args.mode == "check":
            bundle = run_check(repo=args.repo.resolve(), paths=args.paths)
            if args.out:
                args.out.write_text(json.dumps(bundle["result"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if args.receipt:
                args.receipt.parent.mkdir(parents=True, exist_ok=True)
                args.receipt.write_text(json.dumps(bundle["receipt"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if not args.out:
                sys.stdout.write(json.dumps(bundle["result"], indent=2, sort_keys=True) + "\n")
            return 0
        identity = run_identify(args.binary)
        if identity is None:
            print("NOT_EXERCISED: no buf executable on DTCR_BUF_BIN or PATH", file=sys.stderr)
            return 70
        sys.stdout.write(json.dumps(identity, indent=2, sort_keys=True) + "\n")
        return 0
    except Refusal as refusal:
        print(f"REFUSED {refusal}", file=sys.stderr)
        return 2
    except Unusable as unusable:
        print(f"UNUSABLE {unusable}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
