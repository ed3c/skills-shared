#!/usr/bin/env python3
"""Validate Git Town Worker integration with the GitHub publication gate.

This checker is zero-network. It verifies that the portable Worker contract composes
`PUBLICATION_POLICY.md`, that repository profile/eval/report fragments preserve the
three publication intents and fail-closed billing circuit, and that unattended Git
Town synchronization remains no-push.

Exit codes:
  0  contract valid
  2  contract violation
  64 missing/unreadable input
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any


class ContractError(ValueError):
    """A portable publication-boundary contract is incomplete or unsafe."""


REQUIRED_FILES = {
    "SKILL.md",
    "SYSTEM_PROMPT.md",
    "PUBLICATION_POLICY.md",
    "references/GITHUB_ACTIONS_PUBLICATION_ADOPTION.md",
    "references/GITHUB_ACTIONS_PUBLICATION_PROFILE.template.md",
    "references/GITHUB_ACTIONS_PUBLICATION_EVALS.md",
    "references/GITHUB_ACTIONS_PUBLICATION_REPORT.template.md",
    "evals.json",
}

MACHINE_PATH_PATTERNS = (
    re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    re.compile(r"/home/[A-Za-z0-9._-]+/"),
    re.compile(r"[A-Za-z]:\\Users\\"),
)

THREE_INTENTS = ("initial-pr", "ready-for-review", "batched-repair")


def read_text(root: Path, relative: str) -> str:
    path = root / relative
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContractError(f"missing required file: {relative}") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise ContractError(f"unreadable required file: {relative}: {exc}") from exc


def load_json(root: Path, relative: str) -> dict[str, Any]:
    text = read_text(root, relative)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON: {relative}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"JSON root must be an object: {relative}")
    return value


def require_markers(relative: str, text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise ContractError(f"{relative}: missing markers: {missing}")


def reject_machine_paths(relative: str, text: str) -> None:
    for pattern in MACHINE_PATH_PATTERNS:
        match = pattern.search(text)
        if match:
            raise ContractError(
                f"{relative}: machine-local path is not portable: {match.group(0)!r}"
            )


def check_skill(root: Path) -> None:
    relative = "SKILL.md"
    text = read_text(root, relative)
    require_markers(
        relative,
        text,
        (
            "Compose the target Agent instruction surface from the **contents**, not file paths, of [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) and [`PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md)",
            "GITHUB_ACTIONS_PUBLICATION_ADOPTION.md",
            "GITHUB_ACTIONS_PUBLICATION_PROFILE.template.md",
            "GITHUB_ACTIONS_PUBLICATION_EVALS.md",
            "GITHUB_ACTIONS_PUBLICATION_REPORT.template.md",
            "github-delivery-loop",
            "initial-pr",
            "ready-for-review",
            "batched-repair",
            "billing-open",
            # These four shared one line with `billing-open`, so deleting the
            # line was caught -- but deleting only these was not. Four of the
            # five blocking conditions #47 names had no control at all; the
            # guard looked like it worked because of the fifth.
            "stale local verification",
            "old-SHA checks",
            "repeated feedback",
            "ambiguous PR identity",
            "Background synchronization may never invoke `git town sync --push`",
            "local sync, local verification, publication decision, remote publication",
        ),
    )
    reject_machine_paths(relative, text)


def check_base_prompt(root: Path) -> None:
    relative = "SYSTEM_PROMPT.md"
    text = read_text(root, relative)
    require_markers(
        relative,
        text,
        (
            "git town sync --stack --dry-run --non-interactive --no-auto-resolve --no-push",
            "git town sync --stack --non-interactive --no-auto-resolve --no-push",
            "Default background behavior is no push.",
            "Do not bypass hooks or required CI.",
        ),
    )
    reject_machine_paths(relative, text)


def check_policy(root: Path) -> None:
    relative = "PUBLICATION_POLICY.md"
    text = read_text(root, relative)
    require_markers(
        relative,
        text,
        (
            "ci_publish_gate.py evaluate --intent <intent>",
            "github-actions-publish-snapshot/v1",
            "github-delivery-local-verification/v1",
            "initial-pr",
            "ready-for-review",
            "batched-repair",
            "git town sync --stack --non-interactive --no-auto-resolve --no-push",
            "git town sync --push",
            "snapshot state is:\n\n```text\nbilling-open",
            "owner-authored recovery receipt",
            "exact-HEAD local verification receipt",
            "a planted stale-head or billing-open case fails closed",
            "cancel-in-progress: true",
            "SKIPPED_BY_POLICY",
            "local sync",
            "local verification",
            "publication decision",
            "remote publication",
            "GitHub trusted check",
            "Human Admit",
        ),
    )
    for intent in THREE_INTENTS:
        if text.count(f"`{intent}`") < 1:
            raise ContractError(f"{relative}: missing exact publication intent {intent}")
    if "--no-push" not in text:
        raise ContractError(f"{relative}: unattended sync lost --no-push")
    reject_machine_paths(relative, text)


def check_profile_fragment(root: Path) -> None:
    relative = "references/GITHUB_ACTIONS_PUBLICATION_PROFILE.template.md"
    text = read_text(root, relative)
    require_markers(
        relative,
        text,
        (
            "git-town-stacked-pr-worker/github-actions-publication-profile/v1",
            "skill: github-delivery-loop",
            "github-actions-publish-snapshot/v1",
            "github-delivery-local-verification/v1",
            "github-actions-publish-decision/v1",
            "github-actions-billing-recovery/v1",
            "draft_checkpoint_push: denied",
            "feedback_reuse: denied",
            "exact_head_required: true",
            "a receipt for an older SHA is stale.",
            "draft_pr_runner_policy: no-runner",
            "obsolete_head_policy: cancel-in-progress",
            "mode: fail-closed",
            "blocked_state: billing-open",
            "git_town_push: denied",
            "post_push_fetch_required: true",
            "billing_recovery_receipt",
        ),
    )
    allowed_block = re.search(
        r"intents:\n\s+allowed:\n(?P<body>(?:\s+- [^\n]+\n)+)", text
    )
    if allowed_block is None:
        raise ContractError(f"{relative}: cannot parse allowed intents")
    intents = tuple(
        line.split("-", 1)[1].strip()
        for line in allowed_block.group("body").splitlines()
        if "-" in line
    )
    if intents != THREE_INTENTS:
        raise ContractError(
            f"{relative}: allowed intents drifted: got={intents} expected={THREE_INTENTS}"
        )
    reject_machine_paths(relative, text)


def check_eval_fragment(root: Path) -> None:
    relative = "references/GITHUB_ACTIONS_PUBLICATION_EVALS.md"
    text = read_text(root, relative)
    require_markers(
        relative,
        text,
        tuple(f"GTSP-{number}" for number in range(21, 29))
        + (
            "git town sync --stack --non-interactive --no-auto-resolve --no-push",
            "billing-open",
            "SKIPPED_BY_POLICY",
            "Human Admit",
        ),
    )
    reject_machine_paths(relative, text)


def check_adoption_fragment(root: Path) -> None:
    relative = "references/GITHUB_ACTIONS_PUBLICATION_ADOPTION.md"
    text = read_text(root, relative)
    require_markers(
        relative,
        text,
        (
            "git-town-stacked-pr-worker",
            "github-delivery-loop",
            "SYSTEM_PROMPT.md",
            "PUBLICATION_POLICY.md",
            "draft PR is visible without a runner-backed trusted job",
            "ready-for-review causes one exact-head trusted run",
            "a stale receipt/check and repeated feedback block",
            "billing-open",
            "merge and promotion remain Human Admit",
        ),
    )
    reject_machine_paths(relative, text)


def check_report_fragment(root: Path) -> None:
    relative = "references/GITHUB_ACTIONS_PUBLICATION_REPORT.template.md"
    text = read_text(root, relative)
    require_markers(
        relative,
        text,
        (
            "local Git Town sync",
            "exact-HEAD local verification",
            "publication decision",
            "remote publication",
            "post-push remote ancestry",
            "GitHub trusted check",
            "billing circuit",
            "owner recovery receipt",
            "Human Admit",
            "BLOCKED_INFRASTRUCTURE",
            "repository tests: NOT_EXERCISED",
            "merge: HUMAN_OWNED",
        ),
    )
    reject_machine_paths(relative, text)


def check_evals_json(root: Path) -> None:
    relative = "evals.json"
    value = load_json(root, relative)
    if set(value) != {"skill_name", "version", "_meta", "runnable", "evidence_boundary"}:
        raise ContractError(f"{relative}: top-level fields drifted")
    if value["skill_name"] != "git-town-stacked-pr-worker":
        raise ContractError(f"{relative}: wrong skill_name")
    if value["version"] != "1.3.0":
        raise ContractError(f"{relative}: expected version 1.3.0")

    boundary = value["evidence_boundary"]
    if not isinstance(boundary, dict) or not boundary:
        raise ContractError(f"{relative}: evidence_boundary must be a non-empty object")
    # Admitting the field is not enough: an evidence boundary whose values were
    # free text would let any lane be quietly relabelled into a pass.
    states = {"IMPLEMENTED", "EXERCISED", "NOT_IMPLEMENTED", "NOT_EXERCISED", "REQUIRED"}
    for lane, state in sorted(boundary.items()):
        if state not in states:
            raise ContractError(
                f"{relative}: evidence_boundary[{lane!r}] is {state!r}, not one of {sorted(states)}"
            )
    if boundary.get("remote_publication") != "NOT_EXERCISED":
        raise ContractError(f"{relative}: remote publication must remain NOT_EXERCISED")
    if boundary.get("human_admit") != "REQUIRED":
        raise ContractError(f"{relative}: human admit must remain REQUIRED")

    runnable = value["runnable"]
    if not isinstance(runnable, list) or len(runnable) != 3:
        raise ContractError(f"{relative}: exactly three focused runnable evals are required")
    base_required = {
        "id",
        "checker_script",
        "test_verify",
        "good_fixture",
        "hollow_fixture",
        "covers",
        "expected",
    }
    # Per-eval field sets, so a new optional field cannot be introduced on an
    # eval that was never admitted to carry it.
    # A null fixture carries its description in a field of its own, so the exact
    # set differs per eval by which side is a path and which is prose. Still an
    # exact set: a union across all three would let a prose field appear on an
    # eval whose fixture is a real path, which is the polymorphism the plane gate
    # removed.
    allowed_by_id = {
        "GTSP-PUBLISH-1": base_required | {"good_evidence", "hollow_mutations"},
        "GTSP-STACK-1": base_required | {"intent_contract", "hollow_mutations"},
        "GTSP-PROFILE-1": base_required | {"good_evidence", "hollow_mutations"},
    }
    if [item.get("id") if isinstance(item, dict) else None for item in runnable] != [
        "GTSP-PUBLISH-1",
        "GTSP-STACK-1",
        "GTSP-PROFILE-1",
    ]:
        raise ContractError(f"{relative}: focused eval ids or their order drifted")
    for entry in runnable:
        eval_id = entry["id"]
        if set(entry) != allowed_by_id[eval_id]:
            raise ContractError(f"{relative}: {eval_id} runnable fields drifted")
        path_fields = ["checker_script", "test_verify"]
        if "intent_contract" in entry:
            path_fields.append("intent_contract")
        for path_field in path_fields:
            path = entry[path_field]
            if not isinstance(path, str) or not (root / path).is_file():
                raise ContractError(f"{relative}: {eval_id} missing {path_field}: {path!r}")
        covers = entry["covers"]
        if not isinstance(covers, list) or len(covers) < 6:
            raise ContractError(
                f"{relative}: {eval_id} covers must name all load-bearing behaviors"
            )


def validate(root: Path) -> None:
    missing = sorted(relative for relative in REQUIRED_FILES if not (root / relative).is_file())
    if missing:
        raise ContractError(f"missing required files: {missing}")
    check_skill(root)
    check_base_prompt(root)
    check_policy(root)
    check_profile_fragment(root)
    check_eval_fragment(root)
    check_adoption_fragment(root)
    check_report_fragment(root)
    check_evals_json(root)


def copy_contract(source: Path, target: Path) -> None:
    """Copy everything validate() reads, including what evals.json points at.

    Anything left behind makes the fixture fail before a mutation is even
    applied, and expect_red then reports every mutation as killed while killing
    none of them.
    """
    extra = {"scripts/check_publication_boundary.py", "tests/publication-boundary/verify.sh"}
    try:
        document = json.loads((source / "evals.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        document = {}
    for case in document.get("runnable", []):
        if not isinstance(case, dict):
            continue
        for field in ("checker_script", "test_verify", "intent_contract",
                      "good_fixture", "hollow_fixture"):
            value = case.get(field)
            if isinstance(value, str):
                extra.add(value)
    for relative in REQUIRED_FILES | extra:
        src = source / relative
        if src.is_dir():
            shutil.copytree(src, target / relative, dirs_exist_ok=True)
        elif src.is_file():
            dst = target / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def expect_red(name: str, root: Path, mutate) -> None:
    with tempfile.TemporaryDirectory(prefix=f"gtsp-{name}.") as temp:
        fixture = Path(temp) / "skill"
        copy_contract(root, fixture)
        # The baseline has to be green or the mutation proves nothing. This
        # selftest reported "5 mutations killed" for its whole life while
        # killing none: copy_contract left out a script evals.json names, so
        # every fixture was already red and every mutation "passed" for a reason
        # that had nothing to do with the guard under test. A red baseline is a
        # broken fixture, which is a different finding from a live guard.
        try:
            validate(fixture)
        except ContractError as error:
            raise ContractError(
                f"selftest fixture is red before mutation {name!r}, so the "
                f"mutation would prove nothing: {error}"
            ) from error
        mutate(fixture)
        try:
            validate(fixture)
        except ContractError:
            return
        raise ContractError(f"selftest mutation unexpectedly passed: {name}")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise ContractError(f"selftest cannot plant mutation in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def selftest(root: Path) -> None:
    validate(root)
    expect_red(
        "background-push",
        root,
        lambda fixture: replace_once(
            fixture / "PUBLICATION_POLICY.md",
            "git town sync --stack --non-interactive --no-auto-resolve --no-push",
            "git town sync --stack --non-interactive --no-auto-resolve --push",
        ),
    )
    expect_red(
        "drop-billing-circuit",
        root,
        lambda fixture: replace_once(
            fixture / "PUBLICATION_POLICY.md",
            "billing-open",
            "billing-removed",
        ),
    )
    expect_red(
        "fourth-intent",
        root,
        lambda fixture: replace_once(
            fixture / "references/GITHUB_ACTIONS_PUBLICATION_PROFILE.template.md",
            "      - batched-repair\n",
            "      - batched-repair\n      - checkpoint\n",
        ),
    )
    expect_red(
        "collapse-trusted-check",
        root,
        lambda fixture: replace_once(
            fixture / "references/GITHUB_ACTIONS_PUBLICATION_REPORT.template.md",
            "| GitHub trusted check |",
            "| combined green state |",
        ),
    )
    # The stale-receipt law, in each of the two files that compose the Worker's
    # instruction surface and in the two that consumers read. Deleting the whole
    # SKILL.md line was already caught, but only because `billing-open` sat on
    # it; these four conditions had no control of their own.
    expect_red(
        "drop-stale-receipt-law",
        root,
        lambda fixture: replace_once(
            fixture / "SKILL.md",
            "stale local verification, old-SHA checks, repeated feedback, or ambiguous PR identity",
            "other conditions",
        ),
    )
    expect_red(
        "drop-exact-head-receipt",
        root,
        lambda fixture: replace_once(
            fixture / "PUBLICATION_POLICY.md",
            "exact-HEAD local verification receipt",
            "local verification receipt",
        ),
    )
    expect_red(
        "drop-stale-head-control",
        root,
        lambda fixture: replace_once(
            fixture / "PUBLICATION_POLICY.md",
            "a planted stale-head or billing-open case fails closed",
            "a planted billing-open case fails closed",
        ),
    )
    expect_red(
        "drop-older-sha-definition",
        root,
        lambda fixture: replace_once(
            fixture / "references/GITHUB_ACTIONS_PUBLICATION_PROFILE.template.md",
            "a receipt for an older SHA is stale.",
            "receipt freshness is advisory.",
        ),
    )
    expect_red(
        "drop-adoption-stale-check",
        root,
        lambda fixture: replace_once(
            fixture / "references/GITHUB_ACTIONS_PUBLICATION_ADOPTION.md",
            "a stale receipt/check and repeated feedback block",
            "repeated feedback blocks",
        ),
    )
    expect_red(
        "drop-policy-composition",
        root,
        lambda fixture: replace_once(
            fixture / "SKILL.md",
            "Compose the target Agent instruction surface from the **contents**, not file paths, of [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) and [`PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md)",
            "Compose the target Agent instruction surface from the base prompt only",
        ),
    )
    print("SELFTEST GREEN: Git Town / GitHub Actions publication boundary (10 mutations killed)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_publication_boundary.py")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="git-town-stacked-pr-worker skill root",
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.selftest:
            selftest(root)
        else:
            validate(root)
            print("PASS Git Town Worker consumes GitHub Actions publication policy")
        return 0
    except ContractError as exc:
        print(f"publication boundary RED: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"publication boundary FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
