#!/usr/bin/env python3
"""Bind an A/B comparison to external authority bytes.

The A/B scorer checks that every arm was graded by the same evaluator. It
reads that evaluator's identity from a JSON field the caller wrote. So a
comparison can be perfectly fair between arms and still be measured by an
evaluator that never ran.

The authority layer reads external evidence bytes and refuses identities that
nothing produced. But an A/B result does not inherit that guarantee by sitting
downstream of it in the repository history: an older PASS predates the layer,
and ancestry is not evidence.

This wrapper is the composition. It requires the exact bytes of the run, the
scorer, the authority checker and the authority bundle; it runs the authority
checker *first* and refuses to score at all if that fails; and it requires each
evaluator the A/B named to appear in the authority bundle's external evidence,
matching on id, version and artifact digest. An identity that exists only as
caller-authored JSON is refused.

The result claims VERIFIED and nothing more. An offline fixture comparison has
no merge, no release, no human approval and no physical run behind it, so
ADMITTED, CANONICAL, generalization and compliance are all refused here rather
than left to a reader to discount.

Exits: 0 admitted, 2 refused, 64 unusable input, 70 a gate could not run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA = "controlled-language-ab-authority-manifest/v1"
REQUIRED_ARTIFACTS = ("ab_run", "ab_scorer", "authority_checker", "authority_bundle")
FORBIDDEN_CLAIM_STATES = ("ADMITTED", "CANONICAL", "RELEASED", "CERTIFIED")


class Refused(Exception):
    """Read, and does not hold together."""


class Unusable(Exception):
    """Could not be read at all."""


class GateUnavailable(Exception):
    """A gate could not be executed. Not the same as the gate refusing."""


def digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def resolve(root: Path, relative: str, label: str) -> Path:
    if relative.startswith("/") or ".." in Path(relative).parts:
        raise Refused(f"{label} path {relative!r} is not repository-relative")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as error:
        raise Refused(f"{label} path {relative!r} escapes the repository") from error
    return candidate


def bind(root: Path, declared: dict[str, Any], label: str) -> tuple[Path, bytes]:
    path = resolve(root, declared["path"], label)
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise Unusable(f"{label}: unreadable {declared['path']}: {error}") from error
    actual = digest_bytes(raw)
    if actual != declared["artifact_digest"]:
        raise Refused(
            f"{label} digest {declared['artifact_digest']} does not match "
            f"{declared['path']} ({actual}); the manifest is bound to bytes that "
            f"are no longer there"
        )
    return path, raw


def run_gate(argv: list[str], root: Path, label: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            argv, cwd=root, capture_output=True, text=True, check=False, timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GateUnavailable(f"{label} could not be executed: {error}") from error
    return result.returncode, result.stdout


def evaluate(root: Path, manifest_path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as error:
        raise Unusable(f"unreadable manifest: {error}") from error
    except json.JSONDecodeError as error:
        raise Unusable(f"unparseable manifest: {error}") from error
    if not isinstance(manifest, dict):
        raise Unusable("manifest root must be an object")
    if manifest.get("schema_version") != SCHEMA:
        raise Refused(f"schema_version is not {SCHEMA}")

    known = set(REQUIRED_ARTIFACTS) | {"schema_version", "claimed_state"}
    extra = sorted(set(manifest) - known)
    if extra:
        raise Refused(f"manifest carries undeclared reference(s): {', '.join(extra)}")
    for field in REQUIRED_ARTIFACTS:
        if field not in manifest:
            raise Refused(f"manifest is missing {field}")

    bound: dict[str, tuple[Path, bytes]] = {}
    for field in REQUIRED_ARTIFACTS:
        bound[field] = bind(root, manifest[field], field)

    # One check, not two. An earlier version refused FORBIDDEN_CLAIM_STATES
    # first and then required VERIFIED; removing the first left the selftest
    # green, because the second caught every case. A guard whose removal changes
    # nothing is not a guard, it is a comment with a syntax error budget.
    claimed = manifest.get("claimed_state", "VERIFIED")
    if claimed != "VERIFIED":
        reason = (
            "an offline fixture comparison has no merge, release, human approval "
            "or physical run behind it"
            if claimed in FORBIDDEN_CLAIM_STATES
            else "only VERIFIED is available to this composition"
        )
        raise Refused(f"claimed_state {claimed!r}: {reason}")

    # Authority first. If external evidence does not hold, there is nothing for
    # a fairness score to be a score *of*, and running the scorer anyway would
    # produce a number a reader could quote.
    authority_argv = [
        sys.executable, str(bound["authority_checker"][0]),
        "--bundle", str(bound["authority_bundle"][0]),
    ]
    code, authority_stdout = run_gate(authority_argv, root, "authority checker")
    if code == 64:
        raise Refused("authority checker reported unusable input (64)")
    if code == 70:
        raise GateUnavailable("authority checker failed internally (70)")
    if code != 0:
        raise Refused(f"authority checker refused the bundle (exit {code})")
    try:
        authority_receipt = json.loads(authority_stdout)
    except json.JSONDecodeError as error:
        raise GateUnavailable(f"authority checker emitted no receipt: {error}") from error

    scorer_argv = [
        sys.executable, str(bound["ab_scorer"][0]),
        "--bundle", str(bound["ab_run"][0]),
    ]
    code, scorer_stdout = run_gate(scorer_argv, root, "A/B scorer")
    if code == 64:
        raise Refused("A/B scorer reported unusable input (64)")
    if code != 0:
        # A failing scorer is never covered by a passing authority check.
        raise Refused(f"A/B scorer refused the run (exit {code})")
    try:
        ab_receipt = json.loads(scorer_stdout)
    except json.JSONDecodeError as error:
        raise GateUnavailable(f"A/B scorer emitted no receipt: {error}") from error
    if ab_receipt.get("status") != "PASS":
        raise Refused(f"A/B receipt status is {ab_receipt.get('status')!r}")

    # The composition itself: every evaluator the A/B named must be an identity
    # the authority layer read out of external bytes.
    ab_run = json.loads(bound["ab_run"][1].decode("utf-8"))
    declared = ab_run.get("evaluator_identities") or []
    if not declared:
        raise Refused("the A/B run declares no evaluator identity")

    bundle_root = bound["authority_bundle"][0].parent
    external: list[dict[str, Any]] = []
    bundle = json.loads(bound["authority_bundle"][1].decode("utf-8"))
    for item in bundle.get("evidence", {}).get("evaluator_receipts", []):
        evidence_path = (bundle_root / item["path"]).resolve()
        try:
            external.append(json.loads(evidence_path.read_text(encoding="utf-8")))
        except OSError as error:
            raise Unusable(f"unreadable evaluator evidence: {error}") from error

    matched: list[str] = []
    for identity in declared:
        hit = None
        for evidence in external:
            if (evidence.get("evaluator_id") == identity.get("id")
                    and evidence.get("evaluator_version") == identity.get("version")
                    and evidence.get("evaluator_artifact_digest") == identity.get("artifact_digest")):
                hit = evidence
                break
        if hit is None:
            raise Refused(
                f"A/B evaluator {identity.get('id')!r} v{identity.get('version')} "
                f"appears only as caller-authored JSON; the authority bundle "
                f"holds no external evidence matching its id, version and "
                f"artifact digest"
            )
        if hit.get("status") != "PASS":
            raise Refused(
                f"external evidence for evaluator {identity.get('id')!r} reports "
                f"status {hit.get('status')!r}"
            )
        if hit.get("execution_origin") not in ("OWNING_WORKFLOW", "LOCAL_VERIFIED",
                                               "EXTERNAL_ATTESTED"):
            raise Refused(
                f"external evidence for evaluator {identity.get('id')!r} has no "
                f"admitted execution origin"
            )
        matched.append(identity["id"])

    # Nothing stronger than the offline fixtures support may ride along.
    if ab_receipt.get("generalization_claimed"):
        raise Refused("the A/B receipt claims generalization from offline fixtures")
    if ab_receipt.get("physical_runs"):
        raise Refused("the A/B receipt reports physical runs in an offline composition")
    if ab_receipt.get("compliance_claim") not in (None, "HUMAN_ADMIT_REQUIRED"):
        raise Refused(
            f"the A/B receipt carries a compliance claim "
            f"{ab_receipt.get('compliance_claim')!r}"
        )

    return {
        "schema_version": "controlled-language-ab-authority-receipt/v1",
        "manifest_digest": digest_bytes(manifest_path.read_bytes()),
        "ab_run_digest": manifest["ab_run"]["artifact_digest"],
        "ab_scorer_digest": manifest["ab_scorer"]["artifact_digest"],
        "authority_checker_digest": manifest["authority_checker"]["artifact_digest"],
        "authority_bundle_digest": manifest["authority_bundle"]["artifact_digest"],
        "authority_receipt_digest": digest_bytes(authority_stdout.encode("utf-8")),
        "ab_receipt_digest": digest_bytes(scorer_stdout.encode("utf-8")),
        "evaluators_bound_to_external_evidence": sorted(matched),
        "gate_order": ["authority", "ab_scorer"],
        "state": "VERIFIED",
        "physical_runs": "NOT_EXERCISED",
        "generalization": "NOT_EXERCISED",
        "human_approval": "NOT_REQUIRED_FOR_VERIFIED_FIXTURE_AUTHORITY",
        "merge_or_release": "NOT_REQUIRED_FOR_VERIFIED_FIXTURE_AUTHORITY",
        "compliance_claim": "NOT_CLAIMED",
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from ab_authority_selftest import run_selftest
        return run_selftest(args.repo_root.resolve())

    if args.manifest is None:
        parser.error("--manifest or --selftest is required")

    try:
        receipt = evaluate(args.repo_root.resolve(), args.manifest)
    except Unusable as error:
        print(f"FATAL A/B authority input: {error}", file=sys.stderr)
        return 64
    except GateUnavailable as error:
        print(f"CHECKER RED: {error}", file=sys.stderr)
        return 70
    except Refused as error:
        print(f"AB AUTHORITY RED: {error}", file=sys.stderr)
        return 2

    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
