#!/usr/bin/env python3
"""Validate a held-out-corpus/v1 declaration before any live Agent is run.

Exit codes:
  0   the corpus is held out, sealed, and independently evaluated
  2   structurally valid corpus violates the separation it claims
  64  missing, unreadable, malformed, or schema-invalid input
  70  required validator dependency is unavailable

Running a live Agent against the fixtures used to design a Skill measures
memorization. This checks the separation that makes a treatment result mean
anything: that no listed repository was used to design the fixtures, that the
answers are sealed rather than shipped, that the evaluator is not the evaluated
Agent, and that the corpus was frozen rather than tuned after a result was seen.

It reads a declaration. It does not fetch a repository, open sealed material, or
run an Agent -- a corpus that passes here is admissible to run, not evidence that
anything ran.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from _json_schema_validation import (
    load_json_document,
    require_draft202012_validator,
    schema_errors as shared_schema_errors,
)

SCHEMA_INVALID = 64
SEMANTIC_FAIL = 2
SCHEMA_NAME = "held-out-corpus.schema.json"
PREFIX = "HELD-OUT-CORPUS"
Draft202012Validator = require_draft202012_validator(PREFIX)

# A corpus that only contains defect families measures whether an Agent escalates,
# never whether it correctly declines to. Both directions or neither.
REQUIRED_NON_TRIGGER = {"text-only-non-trigger", "metadata-only-control", "wrong-skill-control"}
REQUIRED_POSITIVE = {"real-capability-with-evidence"}
MINIMUM_DEFECT_FAMILIES = 3


def semantic_errors(corpus: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    repositories = corpus["repositories"]
    families = corpus["task_families"]

    reused = sorted(
        repo["repository_id"] for repo in repositories if repo["used_to_design_fixtures"]
    )
    if reused:
        errors.append("not-held-out: " + ",".join(reused))

    unauthorized = sorted(
        repo["repository_id"]
        for repo in repositories
        if repo["authorization_state"] == "PRIVATE_UNAUTHORIZED"
    )
    if unauthorized:
        errors.append("unauthorized-repository: " + ",".join(unauthorized))

    ids = [repo["repository_id"] for repo in repositories]
    duplicates = sorted({rid for rid, count in Counter(ids).items() if count > 1})
    if duplicates:
        # Three entries pointing at one repository is one repository wearing a
        # set's clothing; the variation this corpus claims would not exist.
        errors.append("duplicate-repository: " + ",".join(duplicates))

    for dimension in ("language", "build_shape", "capability_boundary"):
        values = {repo[dimension] for repo in repositories}
        if len(values) < 2:
            errors.append(
                f"corpus-not-varied:{dimension}: every repository declares {values.pop()!r}"
            )

    known = set(ids)
    for family in families:
        if family["repository_id"] not in known:
            errors.append(
                f"family-unknown-repository:{family['family_id']}: {family['repository_id']}"
            )
        overlap = sorted(
            set(family["required_evidence_levels"]) & set(family["forbidden_evidence_levels"])
        )
        if overlap:
            errors.append(
                f"evidence-level-contradiction:{family['family_id']}: {','.join(overlap)}"
            )
        if family["hidden_task_digest"] == family["ground_truth_digest"]:
            # Identical digests mean the task and its answer are the same object,
            # so whatever the Agent is shown already contains what it is scored on.
            errors.append(f"task-equals-ground-truth:{family['family_id']}")

    present = {family["family_id"] for family in families}
    missing_non_trigger = sorted(REQUIRED_NON_TRIGGER - present)
    if missing_non_trigger:
        errors.append("non-trigger-families-absent: " + ",".join(missing_non_trigger))
    missing_positive = sorted(REQUIRED_POSITIVE - present)
    if missing_positive:
        errors.append("positive-family-absent: " + ",".join(missing_positive))
    defect_families = present - REQUIRED_NON_TRIGGER - REQUIRED_POSITIVE
    if len(defect_families) < MINIMUM_DEFECT_FAMILIES:
        errors.append(
            f"too-few-defect-families: {len(defect_families)} < {MINIMUM_DEFECT_FAMILIES}"
        )

    digests = [family["ground_truth_digest"] for family in families]
    repeated = sorted({d for d, count in Counter(digests).items() if count > 1})
    if repeated:
        errors.append("shared-ground-truth-digest: " + ",".join(d[:12] for d in repeated))

    return errors


def check(path: Path, schema_root: Path) -> int:
    corpus = load_json_document(path, prefix=PREFIX, invalid_exit=SCHEMA_INVALID)
    schema = load_json_document(
        schema_root / SCHEMA_NAME, prefix=PREFIX, invalid_exit=SCHEMA_INVALID
    )

    schema_errors = shared_schema_errors(corpus, schema, Draft202012Validator)
    if schema_errors:
        for error in schema_errors:
            print(f"{PREFIX}-INVALID {error}", file=sys.stderr)
        return SCHEMA_INVALID

    errors = semantic_errors(corpus)
    if errors:
        for error in errors:
            print(f"{PREFIX}-RED {error}", file=sys.stderr)
        return SEMANTIC_FAIL

    print(
        "HELD-OUT-CORPUS-GREEN "
        f"corpus={corpus['corpus_id']} "
        f"repositories={len(corpus['repositories'])} "
        f"families={len(corpus['task_families'])} "
        f"evaluator={corpus['evaluator']['owner']} "
        f"frozen_at={corpus['frozen_at_commit'][:12]} "
        "-- admissible to run, not evidence that anything ran"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "references",
    )
    args = parser.parse_args(argv)
    return check(args.corpus, args.schema_root)


if __name__ == "__main__":
    raise SystemExit(main())
