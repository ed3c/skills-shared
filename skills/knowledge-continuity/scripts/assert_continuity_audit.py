#!/usr/bin/env python3
"""Refuse a continuity audit record that claims more than it measured.

The shape gate is `references/continuity-audit.schema.json`. It can only say the
record is well formed. This is the separate semantic gate, and it exists because
the two cheap lies about a document audit are both schema-valid:

    a green mechanical run reported as convergence
        -> `SKILL.md` says 只有機械層綠不算收斂, and prose has never once
           stopped anybody. `CONVERGED` now requires every §4 human question to
           carry a named admitter.
    a record whose rule list no longer matches the checker
        -> the rule set is read back out of `check_knowledge_continuity.py`
           rather than trusted from the file, so a rule added, removed or
           silently dropped from the emitter turns this red instead of leaving
           an audit that measured four things while claiming five.

The subject digest is recomputed from the bytes on disk for the same reason: an
audit of a document that has since changed is a statement about nothing.

Exit codes: 0 green, 2 at least one refused claim, 70 unusable input.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from check_knowledge_continuity import (  # noqa: E402
    AUDIT_SCHEMA,
    HUMAN_LANE,
    audit as build_audit,
    evaluate,
)

SCHEMA = SCRIPTS.parent / "references" / "continuity-audit.schema.json"


class Unusable(Exception):
    """The input could not be read at all. Not a refused claim."""


def implemented_rule_ids() -> list[str]:
    """Ask the checker which rules exist instead of restating them here."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as handle:
        probe = Path(handle.name)
        handle.write("# probe\n")
    try:
        return [rule.rule_id for rule in evaluate(probe)]
    finally:
        probe.unlink(missing_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Unusable(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Unusable(f"{path}: audit root must be an object")
    return value


def validate_shape(value: dict[str, Any], schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - environment defect, not a claim
        raise Unusable("jsonschema Draft 2020-12 validator unavailable") from exc
    try:
        schema = read_json(schema_path)
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise Unusable(f"invalid/unreadable schema {schema_path}: {exc}") from exc
    return [
        f"SHAPE {'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(
            Draft202012Validator(schema).iter_errors(value),
            key=lambda error: list(error.absolute_path),
        )[:10]
    ]


def validate(value: dict[str, Any], subject_root: Path) -> list[str]:
    errors: list[str] = []

    subject = value["subject"]
    path = (subject_root / subject["path"]).resolve()
    try:
        path.relative_to(subject_root.resolve())
    except ValueError:
        errors.append(f"SUBJECT_PATH_ESCAPES_ROOT {subject['path']}")
        return errors
    if not path.is_file():
        errors.append(f"SUBJECT_ABSENT {subject['path']}")
    elif hashlib.sha256(path.read_bytes()).hexdigest() != subject["sha256"]:
        errors.append(f"SUBJECT_DIGEST_DRIFT {subject['path']}")

    mechanical = value["mechanical"]
    rules = mechanical["rules"]
    reported = [row["rule_id"] for row in rules]
    if reported != implemented_rule_ids():
        errors.append(f"RULE_SET_DISAGREES_WITH_CHECKER {','.join(reported)}")
    for row in rules:
        if (row["state"] == "FAIL") != (row["breaks"] > 0):
            errors.append(f"RULE_STATE_CONTRADICTS_COUNT {row['rule_id']}")
        if len(row["lines"]) != row["breaks"]:
            errors.append(f"RULE_LINES_CONTRADICT_COUNT {row['rule_id']}")
    total = sum(row["breaks"] for row in rules)
    if mechanical["total_breaks"] != total:
        errors.append(f"TOTAL_CONTRADICTS_RULES {mechanical['total_breaks']}!={total}")
    if mechanical["exit_code"] != (0 if mechanical["total_breaks"] == 0 else 2):
        errors.append(f"EXIT_CODE_CONTRADICTS_TOTAL {mechanical['exit_code']}")

    lane = value["human_lane"]
    if [(row["id"], row["question"]) for row in lane] != list(HUMAN_LANE):
        errors.append(f"HUMAN_LANE_DISAGREES_WITH_SKILL {len(lane)}")
    for row in lane:
        if row["state"] == "HUMAN_ADMIT_REQUIRED" and row["admitted_by"] is not None:
            errors.append(f"UNADMITTED_ITEM_NAMES_AN_ADMITTER {row['id']}")
        if row["state"] in {"PASS", "FAIL"} and row["admitted_by"] is None:
            errors.append(f"HUMAN_VERDICT_WITHOUT_ADMITTER {row['id']}")

    convergence = value["convergence"]
    admitted = all(row["state"] == "PASS" and row["admitted_by"] for row in lane)
    if convergence == "CONVERGED":
        if mechanical["total_breaks"] != 0:
            errors.append("CONVERGED_WITH_OPEN_BREAKS")
        if not admitted:
            errors.append("MECHANICAL_GREEN_PRESENTED_AS_CONVERGENCE")
    if convergence == "MECHANICAL_ONLY" and any(
        row["state"] != "HUMAN_ADMIT_REQUIRED" for row in lane
    ):
        errors.append("MECHANICAL_ONLY_CARRIES_HUMAN_VERDICTS")
    if convergence == "NOT_CONVERGED" and mechanical["total_breaks"] == 0 and admitted:
        errors.append("NOT_CONVERGED_WITHOUT_ANY_OPEN_LANE")
    return errors


def check(audit_path: Path, schema_path: Path, subject_root: Path) -> list[str]:
    value = read_json(audit_path)
    if value.get("schema") != AUDIT_SCHEMA:
        raise Unusable(f"{audit_path}: schema must be {AUDIT_SCHEMA}")
    shape = validate_shape(value, schema_path)
    return shape if shape else validate(value, subject_root)


def selftest(schema_path: Path) -> int:
    """Every planted defect must be refused, and by its own name."""
    root = SCRIPTS.parent
    good = root / "tests/check-knowledge-continuity/fixtures/good/doc.md"
    hollow = root / "tests/check-knowledge-continuity/fixtures/hollow/doc.md"
    base = build_audit(good, evaluate(good))
    base["subject"]["path"] = good.relative_to(root).as_posix()

    mutations: dict[str, tuple[dict[str, Any], str]] = {}

    def plant(name: str, expected: str, mutate) -> None:
        value = copy.deepcopy(base)
        mutate(value)
        mutations[name] = (value, expected)

    plant("subject_digest_drift", "SUBJECT_DIGEST_DRIFT",
          lambda v: v["subject"].update(sha256="0" * 64))
    plant("subject_absent", "SUBJECT_ABSENT",
          lambda v: v["subject"].update(path="tests/never-written.md"))
    plant("rule_dropped", "RULE_SET_DISAGREES_WITH_CHECKER",
          lambda v: v["mechanical"]["rules"].pop())
    plant("rule_state_lies", "RULE_STATE_CONTRADICTS_COUNT",
          lambda v: v["mechanical"]["rules"][0].update(state="FAIL"))
    plant("total_lies", "TOTAL_CONTRADICTS_RULES",
          lambda v: v["mechanical"].update(total_breaks=7))
    plant("exit_code_lies", "EXIT_CODE_CONTRADICTS_TOTAL",
          lambda v: v["mechanical"].update(exit_code=2))
    plant("human_lane_truncated", "HUMAN_LANE_DISAGREES_WITH_SKILL",
          lambda v: v["human_lane"].pop())
    plant("mechanical_green_as_convergence", "MECHANICAL_GREEN_PRESENTED_AS_CONVERGENCE",
          lambda v: v.update(convergence="CONVERGED"))
    plant("machine_admits_human_lane", "MECHANICAL_ONLY_CARRIES_HUMAN_VERDICTS",
          lambda v: v["human_lane"][0].update(state="PASS", admitted_by="the checker"))
    plant("human_verdict_without_admitter", "HUMAN_VERDICT_WITHOUT_ADMITTER",
          lambda v: v["human_lane"][0].update(state="PASS"))

    survivors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="continuity-audit-selftest-") as raw:
        temp = Path(raw)
        positive = temp / "positive.json"
        positive.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
        errors = check(positive, schema_path, root)
        if errors:
            print(f"CONTINUITY-AUDIT-SELFTEST-RED positive={errors}", file=sys.stderr)
            return 2

        broken = build_audit(hollow, evaluate(hollow))
        broken["subject"]["path"] = hollow.relative_to(root).as_posix()
        breaking = temp / "hollow.json"
        breaking.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
        errors = check(breaking, schema_path, root)
        if errors:
            print(f"CONTINUITY-AUDIT-SELFTEST-RED hollow={errors}", file=sys.stderr)
            return 2
        if broken["mechanical"]["exit_code"] != 2 or broken["convergence"] != "MECHANICAL_ONLY":
            print("CONTINUITY-AUDIT-SELFTEST-RED hollow record did not report its breaks", file=sys.stderr)
            return 2

        for name, (value, expected) in mutations.items():
            path = temp / f"{name}.json"
            path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
            found = check(path, schema_path, root)
            if not any(error.startswith(expected) or expected in error for error in found):
                survivors.append(name)
    if survivors:
        print(
            f"CONTINUITY-AUDIT-SELFTEST-RED survived={','.join(sorted(survivors))}",
            file=sys.stderr,
        )
        return 2
    print(
        f"CONTINUITY-AUDIT-SELFTEST-GREEN mutations={len(mutations)} all refused by name"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--schema", type=Path, default=SCHEMA)
    parser.add_argument(
        "--subject-root",
        type=Path,
        default=SCRIPTS.parent,
        help="root the audit subject path is resolved against (default: the Skill root)",
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.selftest:
            return selftest(args.schema)
        if args.audit is None:
            parser.error("需要 --audit <record.json>，或 --selftest")
        errors = check(args.audit, args.schema, args.subject_root.resolve())
    except Unusable as exc:
        print(f"CONTINUITY-AUDIT-MECHANISM-RED {exc}", file=sys.stderr)
        return 70
    if errors:
        for error in errors:
            print(f"CONTINUITY-AUDIT-RED {error}", file=sys.stderr)
        return 2
    print("CONTINUITY-AUDIT-GREEN mechanical lane bound to the checker; human lane not inferred")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
