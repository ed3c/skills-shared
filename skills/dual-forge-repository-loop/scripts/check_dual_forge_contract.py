#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE = {"PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED", "SKIPPED_BY_POLICY", "HUMAN_ADMIT_REQUIRED"}
EXPECTED_HISTORY = [
    "GITHUB_BOUND",
    "LOCAL_SYNCED",
    "FORGEJO_ISSUES_BOUND",
    "WORKTREES_VERIFIED",
    "FORGEJO_PRS_MERGED",
    "LOCAL_MAIN_MERGED",
    "GITHUB_RECONCILED",
    "GITHUB_ACTIONS_VERIFIED",
    "GITHUB_PUBLICATION_READY",
]
REQUIRED_PUBLICATION_EVIDENCE = [
    "github_ingress",
    "forgejo_runtime",
    "local_worktrees",
    "local_main_merge",
    "github_reconciliation",
    "github_actions",
]


def fail(msg: str) -> int:
    print(f"FAIL {msg}", file=sys.stderr)
    return 2


def obj(v, name: str):
    if not isinstance(v, dict):
        raise ValueError(f"{name} must be an object")
    return v


def sha(v, name: str):
    if not isinstance(v, str) or not SHA40.fullmatch(v):
        raise ValueError(f"{name} must be a lowercase 40-hex commit SHA")
    return v


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_dual_forge_contract.py RECEIPT.json", file=sys.stderr)
        return 64
    path = Path(argv[1])
    if not path.is_file():
        print(f"INPUT_ERROR missing receipt: {path}", file=sys.stderr)
        return 64
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        obj(data, "root")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INPUT_ERROR {exc}", file=sys.stderr)
        return 64

    try:
        if data.get("schema_version") != "dual-forge-repository-loop/v1":
            raise ValueError("unsupported schema_version")

        authority = obj(data.get("authority"), "authority")
        if authority != {"implementation": "local-forgejo", "publication": "github", "actions": "github-actions"}:
            raise ValueError("authority planes must remain local-forgejo/github/github-actions")

        github = obj(data.get("github"), "github")
        forgejo = obj(data.get("forgejo"), "forgejo")
        local = obj(data.get("local"), "local")
        if github.get("remote_name") == forgejo.get("remote_name"):
            raise ValueError("GitHub and Forgejo remote names must be distinct")
        for remote in (github.get("remote_name"), forgejo.get("remote_name")):
            if not isinstance(remote, str) or not remote.strip() or "@" in remote or "://" in remote:
                raise ValueError("bindings contain remote names only; credential-bearing/URL values are forbidden")

        sha(github.get("observed_main_sha"), "github.observed_main_sha")
        sha(forgejo.get("observed_main_sha"), "forgejo.observed_main_sha")
        sha(local.get("local_main_sha"), "local.local_main_sha")

        ns = obj(data.get("issue_namespaces"), "issue_namespaces")
        fp, gp = ns.get("forgejo"), ns.get("github")
        if not isinstance(fp, str) or not isinstance(gp, str) or not fp or not gp or fp == gp:
            raise ValueError("Forgejo and GitHub issue namespaces must be non-empty and distinct")
        links = data.get("issue_links", [])
        if not isinstance(links, list):
            raise ValueError("issue_links must be an array")
        for i, link in enumerate(links):
            link = obj(link, f"issue_links[{i}]")
            fref, gref = link.get("forgejo_issue"), link.get("github_issue")
            if not isinstance(fref, str) or not fref.startswith(fp):
                raise ValueError(f"issue_links[{i}].forgejo_issue must use {fp!r}")
            if not isinstance(gref, str) or not gref.startswith(gp):
                raise ValueError(f"issue_links[{i}].github_issue must use {gp!r}")
            if fref == gref:
                raise ValueError("cross-forge issue identities cannot collapse")

        history = data.get("history")
        if not isinstance(history, list) or any(not isinstance(x, str) for x in history):
            raise ValueError("history must be an array of state names")
        if history[: len(EXPECTED_HISTORY)] != EXPECTED_HISTORY:
            raise ValueError("delivery history must preserve local-main-first and reconciliation-before-publication order")

        rec = obj(data.get("reconciliation"), "reconciliation")
        required_rec = [
            "remote_main_checked",
            "open_prs_enumerated",
            "affected_issues_enumerated",
            "conflicts_routed",
            "issue_states_routed",
            "candidate_contains_observed_github_main",
            "candidate_contains_local_main",
        ]

        pub = obj(data.get("publication"), "publication")
        candidate = sha(pub.get("candidate_sha"), "publication.candidate_sha")
        allowed = pub.get("allowed")
        if not isinstance(allowed, bool):
            raise ValueError("publication.allowed must be boolean")

        actions = obj(data.get("actions"), "actions")
        state = actions.get("state")
        if state not in EVIDENCE:
            raise ValueError("actions.state is not an admitted evidence state")
        head = sha(actions.get("head_sha"), "actions.head_sha")
        if state == "PASS" and not isinstance(actions.get("run_id"), str):
            raise ValueError("GitHub Actions PASS requires run_id")

        evidence = obj(data.get("evidence"), "evidence")
        for key, value in evidence.items():
            if value not in EVIDENCE:
                raise ValueError(f"evidence.{key} has invalid state {value!r}")

        if allowed:
            missing = [k for k in required_rec if rec.get(k) is not True]
            if missing:
                raise ValueError("publication allowed before reconciliation closed: " + ", ".join(missing))
            unproved = [k for k in REQUIRED_PUBLICATION_EVIDENCE if evidence.get(k) != "PASS"]
            if unproved:
                raise ValueError("publication allowed with unproved runtime lanes: " + ", ".join(unproved))
            if state != "PASS" or evidence.get("github_actions") != "PASS":
                raise ValueError("publication allowed without GitHub Actions PASS")
            if head != candidate:
                raise ValueError("GitHub Actions receipt is stale: head_sha != publication candidate")

    except ValueError as exc:
        return fail(str(exc))

    print("PASS dual-forge contract structurally closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
