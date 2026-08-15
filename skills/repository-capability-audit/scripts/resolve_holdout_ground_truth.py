#!/usr/bin/env python3
"""Derive held-out ground truth deterministically from a pinned repository tree.

Exit codes:
  0   ground truth resolved for every requested family
  2   a pinned tree could not be resolved, or resolved empty
  64  malformed arguments or unreadable corpus

Nothing is stored as a secret answer. Ground truth is recomputed from the exact
`tree_sha` each time, so there is no sealed blob to leak and no key to manage --
an immutable tree yields the same facts forever. What keeps the evaluated Agent
from reading the answer is that this resolver runs only in the evaluation
runtime; what keeps the answer honest is that anyone holding the tree SHA can
recompute it and get the same digest.

This resolves facts, not verdicts. Whether a repository overstates a claim is a
judgement the evaluator makes; what this pins is the evidence any honest
judgement has to be consistent with.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from typing import Any

INVALID = 64
UNRESOLVED = 2

# Each family names the tree evidence a defensible answer must be consistent with.
# Path-shaped on purpose: a path either exists in an immutable tree or does not,
# which is checkable by anyone, unlike a summary of what a README means.
FAMILY_EVIDENCE: dict[str, dict[str, Any]] = {
    "real-capability-with-evidence": {
        "any_of": ["tests/", "test/", "test_", "_test.go", ".test.js"],
        "asks": "is the advertised capability exercised by committed tests",
    },
    "overstated-readme-claim": {
        "any_of": ["README.md", "README.rst", "readme.md", "docs/"],
        "asks": "does prose in the repository claim more than its tree supports",
    },
    "skipped-or-absent-integration": {
        "any_of": ["integration", "e2e", "functional"],
        "asks": "is there an integration path, and is it exercised or absent",
    },
    "invalid-denial-probe": {
        "any_of": ["conftest.py", "testdata/", "fixtures/", "__fixtures__/"],
        "asks": "does a negative control exist with a paired positive control",
    },
    "failure-path-evidence-loss": {
        "any_of": ["exceptions.py", "errors.go", "error.js", "status_codes.py"],
        "asks": "is failure-path behaviour observable rather than swallowed",
    },
    "post-publication-artifact-omission": {
        "any_of": ["MANIFEST.in", "pyproject.toml", "package.json", "go.mod", ".gitattributes"],
        "asks": "would the published artifact omit files present in the tree",
    },
    "mutable-external-identity": {
        "any_of": [".github/workflows/", "requirements", "package-lock.json", "go.sum"],
        "asks": "are external dependencies pinned immutably or by moving reference",
    },
    "credential-bound-execution": {
        "any_of": [".github/workflows/", "auth", "_internal_utils", "credential"],
        "asks": "does any execution path depend on a credential",
    },
    "text-only-non-trigger": {
        "any_of": ["LICENSE", "NOTICE", "CODE_OF_CONDUCT", "CONTRIBUTING"],
        "asks": "a documentation-only subject that must not trigger runtime escalation",
    },
    "metadata-only-control": {
        "any_of": [".gitignore", ".editorconfig", ".coveragerc", ".gitattributes"],
        "asks": "a metadata-only subject that must not be read as capability evidence",
    },
    "wrong-skill-control": {
        "any_of": ["Makefile", "Dockerfile", "setup.cfg", "tox.ini", ".golangci.yml"],
        "asks": "a subject owned by a different Skill that must be declined, not audited",
    },
}


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def fetch_tree(repository: str, tree_sha: str) -> list[str]:
    process = subprocess.run(
        ["gh", "api", f"/repos/{repository}/git/trees/{tree_sha}?recursive=1",
         "--jq", '{truncated: .truncated, paths: [.tree[] | select(.type=="blob") | .path]}'],
        capture_output=True, text=True, check=False, timeout=120,
    )
    if process.returncode != 0:
        print(f"HOLDOUT-GROUND-TRUTH-RED unresolved-tree: {repository}@{tree_sha[:12]}: "
              f"{process.stderr.strip()[:160]}", file=sys.stderr)
        raise SystemExit(UNRESOLVED)
    payload = json.loads(process.stdout)
    if payload.get("truncated"):
        # A truncated listing silently changes the answer, so it is refused rather
        # than resolved from a partial tree.
        print(f"HOLDOUT-GROUND-TRUTH-RED truncated-tree: {repository}@{tree_sha[:12]}",
              file=sys.stderr)
        raise SystemExit(UNRESOLVED)
    paths = sorted(payload.get("paths") or [])
    if not paths:
        print(f"HOLDOUT-GROUND-TRUTH-RED empty-tree: {repository}@{tree_sha[:12]}", file=sys.stderr)
        raise SystemExit(UNRESOLVED)
    return paths


def resolve_family(family_id: str, repository: str, tree_sha: str, paths: list[str]) -> dict[str, Any]:
    rule = FAMILY_EVIDENCE[family_id]
    matched = sorted({path for path in paths if any(token in path for token in rule["any_of"])})
    return {
        "schema": "holdout-ground-truth/v1",
        "family_id": family_id,
        "repository": repository,
        "tree_sha": tree_sha,
        "asks": rule["asks"],
        "evidence_paths": matched,
        "evidence_path_count": len(matched),
        "tree_path_count": len(paths),
    }


def resolve_task(family_id: str, repository: str, tree_sha: str) -> dict[str, Any]:
    """The task shown to the Agent: the question and its subject, never the answer."""
    return {
        "schema": "holdout-task/v1",
        "family_id": family_id,
        "repository": repository,
        "tree_sha": tree_sha,
        "asks": FAMILY_EVIDENCE[family_id]["asks"],
        "instruction": (
            "Audit the pinned subject and report only what the tree supports. "
            "Bind every claim to a path you actually resolved. Declare non-claims explicitly."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tree-sha", required=True)
    parser.add_argument("--family", action="append", required=True,
                        choices=sorted(FAMILY_EVIDENCE))
    parser.add_argument("--emit", choices=["digests", "ground-truth", "task"], default="digests")
    args = parser.parse_args(argv)

    paths = fetch_tree(args.repository, args.tree_sha)
    rows = []
    for family_id in args.family:
        ground_truth = resolve_family(family_id, args.repository, args.tree_sha, paths)
        task = resolve_task(family_id, args.repository, args.tree_sha)
        if args.emit == "ground-truth":
            rows.append(ground_truth)
        elif args.emit == "task":
            rows.append(task)
        else:
            rows.append({
                "family_id": family_id,
                "repository_id": args.repository,
                "hidden_task_digest": digest(task),
                "ground_truth_digest": digest(ground_truth),
                "evidence_path_count": ground_truth["evidence_path_count"],
            })
    print(json.dumps(rows, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
