#!/usr/bin/env python3
"""Validate a #234 consumer canary receipt. Zero network, no consumer access.

The rule this exists for is link coverage. #234 names an eleven-link delivery
chain, and a receipt that reports four exercised links and says nothing about
the other seven reads exactly like a receipt that walked the whole chain. Every
declared link must carry a state, the coverage summary is recomputed rather than
believed, and a link cannot be EXERCISED while the receipt also says no mutation
of the kind that link requires took place.

Exit codes: 0 pass, 2 receipt failure, 64 unusable input, 70 evaluator defect.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "dual-forge-repository-loop/consumer-canary-receipt/v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
STATES = {"EXERCISED", "BLOCKED", "NOT_EXERCISED", "SKIPPED_BY_POLICY", "FAIL"}
SECRET = re.compile(r"(gh[pousr]_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9]{20,}"
                    r"|://[^/\s:]+:[^/\s@]+@)")

# Links that cannot be honestly EXERCISED by a canary that mutated nothing.
NEEDS_MUTATION = {
    "consumer-task-packets": "consumer_files_changed",
    "verified-implementation-slices": "consumer_files_changed",
    "admitted-local-main-integration": "merges",
    "publication-candidate": "pushes",
    "external-merge-handoff": "merges",
}


class Refused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def refuse(code: str, detail: str) -> None:
    raise Refused(code, detail)


def check_shape(body: Any) -> None:
    if not isinstance(body, dict) or body.get("schema") != SCHEMA:
        refuse("RECEIPT_MALFORMED", f"schema must be {SCHEMA}")
    for section in ("consumer_selection_gate", "chain", "chain_declared", "coverage",
                    "mutations_performed", "declared_non_claims"):
        if section not in body:
            refuse("RECEIPT_MALFORMED", f"receipt has no {section}")


def check_gate(body: dict[str, Any]) -> None:
    """#234's consumer selection gate, frozen before mutation or not frozen at all."""
    gate = body["consumer_selection_gate"]
    for field in ("github_repository", "forgejo_repository", "default_branch",
                  "commit_sha", "tree_sha", "remotes", "rollback_subject"):
        if not gate.get(field):
            refuse("SELECTION_GATE_INCOMPLETE", f"selection gate has no {field}")
    for field in ("commit_sha", "tree_sha", "rollback_subject"):
        if not SHA40.fullmatch(str(gate[field])):
            refuse("SELECTION_GATE_INCOMPLETE",
                   f"{field} is not a 40-character lowercase SHA")
    remotes = gate["remotes"]
    if not isinstance(remotes, dict) or len(remotes) < 2:
        refuse("SELECTION_GATE_INCOMPLETE",
               "a dual-forge consumer needs both remotes recorded")
    if gate.get("dirty_paths"):
        refuse("SELECTION_GATE_INCOMPLETE",
               f"{gate['dirty_paths']} dirty path(s); the receipt describes no particular "
               f"subject")
    if not gate.get("delivery_config_present"):
        refuse("SELECTION_GATE_INCOMPLETE",
               "#234 forbids introducing dual-forge delivery into a repository that has "
               "no admitted configuration; this one must already have it")


def check_links(body: dict[str, Any]) -> None:
    declared = body["chain_declared"]
    chain = body["chain"]
    if not isinstance(declared, list) or not declared:
        refuse("RECEIPT_MALFORMED", "chain_declared is empty")

    seen: dict[str, str] = {}
    for entry in chain:
        name = entry.get("link")
        if name not in declared:
            refuse("LINK_COVERAGE_INCOMPLETE", f"chain records unknown link {name!r}")
        if name in seen:
            refuse("LINK_COVERAGE_INCOMPLETE", f"link {name} recorded twice")
        if entry.get("state") not in STATES:
            refuse("LINK_COVERAGE_INCOMPLETE",
                   f"link {name} state {entry.get('state')!r} is not admitted")
        if not str(entry.get("detail", "")).strip():
            refuse("LINK_COVERAGE_INCOMPLETE", f"link {name} carries no detail")
        seen[name] = entry["state"]

    missing = [name for name in declared if name not in seen]
    if missing:
        refuse("LINK_COVERAGE_INCOMPLETE",
               f"the chain declares {len(declared)} links and the receipt states "
               f"{len(seen)}; unstated: {missing}")

    if "FAIL" in seen.values():
        failed = sorted(k for k, v in seen.items() if v == "FAIL")
        refuse("LINK_FAILED", f"link(s) reported FAIL: {failed}")


def check_coverage(body: dict[str, Any]) -> None:
    chain = body["chain"]
    computed = {
        "exercised": sorted(l["link"] for l in chain if l["state"] == "EXERCISED"),
        "blocked": sorted(l["link"] for l in chain if l["state"] == "BLOCKED"),
        "not_exercised": sorted(l["link"] for l in chain
                                if l["state"] in {"NOT_EXERCISED", "SKIPPED_BY_POLICY"}),
    }
    for key, value in computed.items():
        if body["coverage"].get(key) != value:
            refuse("COVERAGE_MISREPORTED",
                   f"coverage.{key} does not match the chain; the chain gives {value}")


def check_mutation_consistency(body: dict[str, Any]) -> None:
    """A link that requires a mutation cannot be EXERCISED by a canary that made none."""
    mutations = body["mutations_performed"]
    states = {l["link"]: l["state"] for l in body["chain"]}
    for name, required in NEEDS_MUTATION.items():
        if states.get(name) == "EXERCISED" and not mutations.get(required):
            refuse("EXERCISED_WITHOUT_MUTATION",
                   f"{name} is EXERCISED while mutations_performed.{required} is false; "
                   f"that link cannot happen without it")
    worktree = states.get("isolated-worktrees-and-leases")
    if worktree == "EXERCISED" and not mutations.get("worktrees_created_and_removed"):
        refuse("EXERCISED_WITHOUT_MUTATION",
               "worktree link is EXERCISED with no worktree recorded")


def check_blocked_evidence(body: dict[str, Any]) -> None:
    """A BLOCKED link must carry the observation that blocks it, not an assertion."""
    for entry in body["chain"]:
        if entry["state"] != "BLOCKED":
            continue
        evidence = {k: v for k, v in entry.items()
                    if k not in {"link", "state", "detail"} and v not in (None, "", [])}
        if not evidence:
            refuse("BLOCKED_WITHOUT_EVIDENCE",
                   f"{entry['link']} is BLOCKED with no recorded observation; a blocker "
                   f"nobody measured is a blocker nobody can clear")


def check_reconciliation(body: dict[str, Any]) -> None:
    for entry in body["chain"]:
        if entry["link"] != "github-reconciliation-inventory":
            continue
        if entry["state"] != "EXERCISED":
            return
        if entry.get("replay_exit_code") != 0:
            refuse("RECONCILIATION_UNPROVEN",
                   f"reconciliation is EXERCISED with replay exit "
                   f"{entry.get('replay_exit_code')!r}; exhaustiveness was not checked")
        for field in ("github_open_prs", "github_open_issues"):
            if not isinstance(entry.get(field), int):
                refuse("RECONCILIATION_UNPROVEN", f"reconciliation records no {field}")


def check_secrets(body: Any, path: str = "") -> None:
    if isinstance(body, dict):
        for key, value in body.items():
            check_secrets(value, f"{path}.{key}")
    elif isinstance(body, list):
        for index, value in enumerate(body):
            check_secrets(value, f"{path}[{index}]")
    elif isinstance(body, str) and SECRET.search(body):
        refuse("SECRET_IN_RECEIPT", f"credential-shaped value at {path}")


CHECKS = (check_gate, check_links, check_coverage, check_mutation_consistency,
          check_blocked_evidence, check_reconciliation)


def validate(body: Any) -> None:
    check_shape(body)
    check_secrets(body)
    for check in CHECKS:
        check(body)


def selftest(body: dict[str, Any]) -> int:
    try:
        validate(body)
    except Refused as failure:
        print(f"SELFTEST RED: committed receipt already refused -- {failure}",
              file=sys.stderr)
        return 2

    def mutate(fn: Any) -> dict[str, Any]:
        copied = copy.deepcopy(body)
        fn(copied)
        return copied

    def drop_link(doc: dict[str, Any]) -> None:
        doc["chain"] = [l for l in doc["chain"]
                        if l["link"] != "git-town-dry-run-and-local-no-push-sync"]

    def blocked_bare(doc: dict[str, Any]) -> None:
        for entry in doc["chain"]:
            if entry["state"] == "BLOCKED":
                for key in list(entry):
                    if key not in {"link", "state", "detail"}:
                        entry.pop(key)
                break

    def claim_integration(doc: dict[str, Any]) -> None:
        """Claim a link that needs a merge, with the coverage kept consistent.

        The first version of this control changed the link state and left the
        coverage summary stale, so COVERAGE_MISREPORTED fired first and the law
        under test was never reached. A control that trips an earlier rule tests
        that rule, not the one it was written for.
        """
        for entry in doc["chain"]:
            if entry["link"] == "admitted-local-main-integration":
                entry["state"] = "EXERCISED"
                break
        chain = doc["chain"]
        doc["coverage"] = {
            "exercised": sorted(l["link"] for l in chain if l["state"] == "EXERCISED"),
            "blocked": sorted(l["link"] for l in chain if l["state"] == "BLOCKED"),
            "not_exercised": sorted(
                l["link"] for l in chain
                if l["state"] in {"NOT_EXERCISED", "SKIPPED_BY_POLICY"}),
        }

    controls = [
        ("dirty-consumer", "SELECTION_GATE_INCOMPLETE",
         mutate(lambda d: d["consumer_selection_gate"].update({"dirty_paths": 2}))),
        ("one-remote", "SELECTION_GATE_INCOMPLETE",
         mutate(lambda d: d["consumer_selection_gate"].update(
             {"remotes": {"github": "git@github.com:x/y.git"}}))),
        ("no-delivery-config", "SELECTION_GATE_INCOMPLETE",
         mutate(lambda d: d["consumer_selection_gate"].update(
             {"delivery_config_present": False}))),
        ("link-omitted", "LINK_COVERAGE_INCOMPLETE", mutate(drop_link)),
        ("link-state-invented", "LINK_COVERAGE_INCOMPLETE",
         mutate(lambda d: d["chain"][0].update({"state": "MOSTLY_DONE"}))),
        ("coverage-inflated", "COVERAGE_MISREPORTED",
         mutate(lambda d: d["coverage"].update({"exercised": d["chain_declared"]}))),
        ("integration-without-merge", "EXERCISED_WITHOUT_MUTATION",
         mutate(claim_integration)),
        ("blocked-without-evidence", "BLOCKED_WITHOUT_EVIDENCE", mutate(blocked_bare)),
        ("reconciliation-unreplayed", "RECONCILIATION_UNPROVEN",
         mutate(lambda d: next(l for l in d["chain"]
                               if l["link"] == "github-reconciliation-inventory")
                .update({"replay_exit_code": 1}))),
        ("credential-in-remote", "SECRET_IN_RECEIPT",
         mutate(lambda d: d["consumer_selection_gate"]["remotes"].update(
             {"forgejo": "http://user:hunter2@localhost:3000/neon/x.git"}))),
    ]

    failed = 0
    for name, code, doc in controls:
        try:
            validate(doc)
        except Refused as failure:
            if failure.code == code:
                print(f"REFUSED {code} ({name})")
                continue
            print(f"CONTROL FAILED {name}: expected {code}, got {failure.code}",
                  file=sys.stderr)
            failed += 1
            continue
        print(f"CONTROL FAILED {name}: expected {code}, nothing was refused",
              file=sys.stderr)
        failed += 1

    if failed:
        return 2
    print(f"SELFTEST GREEN: committed consumer canary admitted; "
          f"{len(controls)} planted defects refused")
    return 0


def main(argv: list[str] | None = None) -> int:
    default = (Path(__file__).resolve().parent.parent / "evals" / "receipts"
               / "consumer-canary.receipt.json")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", nargs="?", default="check", choices=["check", "selftest"])
    parser.add_argument("--receipt", type=Path, default=default)
    args = parser.parse_args(argv)

    try:
        body = json.loads(args.receipt.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"USAGE: {error}", file=sys.stderr)
        return 64
    except json.JSONDecodeError as error:
        print(f"USAGE: unparseable receipt: {error}", file=sys.stderr)
        return 64

    if args.mode == "selftest":
        return selftest(body)

    try:
        validate(body)
    except Refused as failure:
        print(f"CONSUMER CANARY REFUSED {failure.code}: {failure.detail}", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"EVALUATOR FAILURE: {error!r}", file=sys.stderr)
        return 70

    coverage = body["coverage"]
    gate = body["consumer_selection_gate"]
    print(f"CONSUMER CANARY GREEN: {gate['github_repository']} / "
          f"{gate['forgejo_repository']} at {gate['commit_sha'][:12]}; "
          f"{len(coverage['exercised'])} exercised, {len(coverage['blocked'])} blocked, "
          f"{len(coverage['not_exercised'])} not exercised of "
          f"{len(body['chain_declared'])} links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
