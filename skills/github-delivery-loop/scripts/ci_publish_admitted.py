#!/usr/bin/env python3
"""Admitted private-repository publication decision entrypoint.

Validation order is deliberate:
  1. snapshot schema and repository identity;
  2. compact exact-HEAD verification receipt;
  3. detailed evidence-sidecar binding;
  4. publication intent and billing-circuit policy.

No malformed compact receipt can reach sidecar field access or a publication
operation. This command decides only; it never pushes, reruns, transitions,
merges, changes billing, or changes permissions.

Exit codes: 0 ALLOW, 2 policy BLOCK, 64 malformed/stale/untrusted evidence.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import ci_publish_bound_gate as bound
import ci_publish_gate as policy


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ci_publish_admitted.py")
    parser.add_argument("--selftest", action="store_true")
    subs = parser.add_subparsers(dest="command")
    evaluate = subs.add_parser("evaluate")
    evaluate.add_argument("--snapshot", type=Path, required=True)
    evaluate.add_argument("--verification", type=Path, required=True)
    evaluate.add_argument("--verification-evidence", type=Path, required=True)
    evaluate.add_argument("--recovery", type=Path)
    evaluate.add_argument("--repo-root", type=Path, default=Path.cwd())
    evaluate.add_argument("--intent", choices=sorted(policy.INTENTS), required=True)
    evaluate.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        if args.command is not None:
            parser.error("--selftest cannot be combined with a command")
        try:
            bound.selftest()
            head = "1" * 40
            tree = "2" * 40
            compact, evidence = bound.fixture_evidence(head, tree)
            snapshot = policy.fixture_snapshot(head)
            policy.validate_snapshot(snapshot)
            policy.validate_verification(compact, 1326262274, head)
            bound.validate_evidence(evidence, compact, 1326262274, head, tree)
            malformed = dict(compact)
            malformed.pop("commands")
            try:
                policy.validate_verification(malformed, 1326262274, head)
            except policy.InputError:
                pass
            else:
                raise policy.InputError("malformed compact receipt unexpectedly passed")
            print("SELFTEST GREEN: admitted publication validation order")
            return 0
        except (policy.InputError, OSError) as exc:
            print(f"SELFTEST RED: {exc}", file=sys.stderr)
            return 1

    if args.command != "evaluate":
        parser.error("evaluate or --selftest is required")

    try:
        snapshot = policy.load_object(args.snapshot, "publish snapshot")
        verification = policy.load_object(args.verification, "local verification receipt")
        evidence = policy.load_object(
            args.verification_evidence, "local verification evidence"
        )
        recovery = (
            policy.load_object(args.recovery, "billing recovery receipt")
            if args.recovery is not None
            else None
        )
        root = args.repo_root.resolve()
        actual_head = policy.git_head(root)
        actual_tree = bound.git_tree(root)

        policy.validate_snapshot(snapshot)
        repository = snapshot["repository"]
        policy.validate_verification(
            verification,
            repository["repository_id"],
            actual_head,
        )
        bound.validate_evidence(
            evidence,
            verification,
            repository["repository_id"],
            actual_head,
            actual_tree,
        )
        decision = policy.evaluate(
            snapshot,
            verification,
            args.intent,
            actual_head,
            recovery,
        )
        policy.emit(decision, args.json)
        return 0 if decision.decision == "ALLOW" else 2
    except policy.InputError as exc:
        decision = policy.Decision(
            "BLOCK",
            "invalid-policy-input",
            args.intent,
            None,
            detail=str(exc),
        )
        policy.emit(decision, args.json, stream=sys.stderr)
        return 64
    except OSError as exc:
        print(f"BLOCK local-io-failure detail={exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
