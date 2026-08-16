#!/usr/bin/env python3
"""Render and verify a thin repository control-plane attachment.

The canonical Skill bodies stay in skills-shared. A consumer stores only
requirements, immutable bindings, runtime identifiers, policy ceilings, and
receipts. This tool never installs host software, fetches the network, writes
credentials, or mutates GitHub.

Commands:
  profile-check  validate the portable composition profile
  attach         dry-run/apply/check the two thin consumer source files
  verify         verify source files, generated Skill binding, and no shadows
  monitor-plan   turn an offline GitHub issue snapshot into a deterministic plan

Exit codes: 0 valid, 2 semantic violation, 3 absent/not exercised, 64 bad input.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from repository_control_plane_consumer import attach, verify
from repository_control_plane_monitor import monitor_plan
from repository_control_plane_profile import (
    DEFAULT_PROFILE,
    EXIT_INPUT,
    ContractError,
    load_profile,
    sha256_document,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        type=Path,
        default=DEFAULT_PROFILE,
        help="portable repository-control-plane profile",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("profile-check", help="validate the portable profile")

    attach_parser = subparsers.add_parser("attach", help="render thin consumer source files")
    attach_parser.add_argument("--target-root", type=Path, required=True)
    attach_parser.add_argument("--consumer-repository-id", required=True)
    attach_parser.add_argument("--runtime-env-commit", required=True)
    mode = attach_parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")

    verify_parser = subparsers.add_parser("verify", help="verify a consumer attachment")
    verify_parser.add_argument("--target-root", type=Path, required=True)

    monitor_parser = subparsers.add_parser(
        "monitor-plan", help="build a deterministic plan from an offline issue snapshot"
    )
    monitor_parser.add_argument("--target-root", type=Path, required=True)
    monitor_parser.add_argument("--issues", type=Path, required=True)
    monitor_parser.add_argument("--output", type=Path)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        profile = load_profile(args.profile)
        if args.command == "profile-check":
            print(
                f"PASS {profile['id']} {sha256_document(profile)} "
                f"skills={len(profile['selected_skills'])}"
            )
            return 0
        if args.command == "attach":
            return attach(
                profile,
                target_root=args.target_root,
                consumer_repository_id=args.consumer_repository_id,
                runtime_env_commit=args.runtime_env_commit,
                apply=args.apply,
                check_only=args.check,
            )
        if args.command == "verify":
            return verify(profile, target_root=args.target_root)
        if args.command == "monitor-plan":
            return monitor_plan(
                profile,
                target_root=args.target_root,
                issues_path=args.issues,
                output_path=args.output,
            )
        parser.error(f"unknown command: {args.command}")
    except ContractError as error:
        print(f"INVALID {error}", file=sys.stderr)
        return EXIT_INPUT
    return EXIT_INPUT


if __name__ == "__main__":
    raise SystemExit(main())
