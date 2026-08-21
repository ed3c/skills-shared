#!/usr/bin/env python3
"""Execute every committed contract in `references/`, counted from the bytes.

Nothing here is a recorded result. The schema list, the positive count, the
control count and the knockout count are all measured on the run, so a fifth
schema or a tenth control joins the suite without this file changing -- and a
schema that quietly loses a control changes the printed number rather than
staying green.

    schemas    every references/**/*.schema.json
    positives  every in-schema `examples` entry, which must validate
    controls   every in-schema `x-refusal-control`, whose instance must be
               refused by the schema as committed
    knockouts  one per control: delete exactly the single keyword its
               `refused_by` names, change nothing else, and require the
               instance to become valid -- a control that survives its own
               knockout is not discriminating the guard it claims
    routes     every schema file and the checker must be linked from
               README.md, AGENTS.md and references/README.md, so a new
               contract cannot arrive unrouted
    counts     every quantity the four documents state in prose -- states,
               drift kinds, roles, terminal states, aliases, ceilings, refusal
               codes -- must equal what the contracts and the checker measure,
               and a quantity no document states at all is a failure rather
               than a tidy-up: the count is the reconciliation
    pinned     the coordinator instruction in the join schema must equal the
               bytes in references/coordinator-instruction.json, which is the
               second independent arrival for the one string this plane is
               not allowed to paraphrase
    red path   a planted defect on a throwaway copy must turn the suite red,
               because a suite that has never gone red is a suite whose green
               means nothing

`GHPC_REFERENCES` overrides the subject. It is what the red-path stage uses,
and it is deliberately not set by tests/run-all.sh, so a normal invocation
always reads the tree.

Exit 0 green, 2 a control or a count failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "GHPC-SELFTEST-UNUSABLE: jsonschema is required. This suite executes "
        "the committed schemas as deciding gates; skipping them would report "
        "the same green as running them.",
        file=sys.stderr,
    )
    raise SystemExit(70)

# The refusal-code count is read by importing the checker, and an import writes
# a __pycache__ beside it. A verification run must not leave anything in the
# checkout it was verifying.
sys.dont_write_bytecode = True

SKILL = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCES = SKILL / "references"
CHECKER = "scripts/compile_portfolio_control.py"
CHECKER_PATH = SKILL / CHECKER
ROUTING_DOCUMENTS = ("README.md", "AGENTS.md", "references/README.md")
JOIN_SCHEMA = "ghpc/subagent-join/v1"

# The planted defect. Removing this keyword makes GHPC-XC-EPOCH-001's instance
# -- a branch name where the forty-hex subject belongs -- validate, so the
# suite must report that the control is no longer refused at all.
PLANTED_FILE = "schemas/portfolio-epoch.schema.json"
PLANTED_KEYWORD = "properties.subject.properties.main_commit.pattern"


class Red(Exception):
    """The suite cannot decide anything, which is not the same as a pass."""


def parse_keyword_path(path: str) -> list[str | int]:
    parts: list[str | int] = []
    for token in re.split(r"\.(?![^\[]*\])", path):
        while True:
            match = re.match(r"^([^\[]*)\[(\d+)\](.*)$", token)
            if not match:
                if token:
                    parts.append(token)
                break
            head, index, token = match.group(1), int(match.group(2)), match.group(3)
            if head:
                parts.append(head)
            parts.append(index)
    return parts


def remove_keyword(document: Any, path: str) -> None:
    parts = parse_keyword_path(path)
    node = document
    for part in parts[:-1]:
        node = node[part]
    leaf = parts[-1]
    if isinstance(node, list):
        node.pop(leaf)
    else:
        del node[leaf]


def load_schemas(references: Path) -> dict[str, tuple[Path, dict[str, Any]]]:
    files = sorted(references.glob("**/*.schema.json"))
    if not files:
        raise Red(f"no schemas found under {references}")
    schemas: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in files:
        document = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(document)
        identity = document.get("properties", {}).get("schema", {}).get("const")
        if not isinstance(identity, str):
            raise Red(f"{path.name}: no properties.schema.const, so nothing can name it")
        if identity in schemas:
            raise Red(f"two schemas claim the identity {identity}")
        schemas[identity] = (path, document)
    return schemas


def check_routes(references: Path, schemas: dict[str, tuple[Path, dict[str, Any]]]) -> list[str]:
    """Every schema and the checker must be reachable from all three documents.

    A contract nobody routed is a contract nobody reads, and the reader who
    needs it most is the one who does not already know it exists. This is also
    the stale-prose ratchet: adding a schema is what changes these documents,
    not remembering to.
    """
    failures: list[str] = []
    if references.resolve() != DEFAULT_REFERENCES.resolve():
        return failures  # a throwaway copy has no documents of its own to route
    for document in ROUTING_DOCUMENTS:
        path = SKILL / document
        if not path.is_file():
            failures.append(f"routing document absent: {document}")
            continue
        text = path.read_text(encoding="utf-8")
        for _identity, (schema_path, _schema) in sorted(schemas.items()):
            relative = schema_path.relative_to(SKILL).as_posix()
            token = (
                relative
                if document != "references/README.md"
                else schema_path.relative_to(references).as_posix()
            )
            if token not in text:
                failures.append(f"{document} does not route {relative}")
        if CHECKER.rsplit("/", 1)[1] not in text:
            failures.append(f"{document} does not route {CHECKER}")
    return failures


def measured_counts(schemas: dict[str, tuple[Path, dict[str, Any]]]) -> dict[str, int]:
    """Every quantity the prose states, measured from the contracts instead.

    The two `portfolio_state` enums are compared rather than one of them read,
    because a fork between the epoch's states and the join's is exactly the
    drift a count taken from either one alone would not see.
    """
    try:
        epoch = schemas["ghpc/portfolio-epoch/v1"][1]["$defs"]
        join = schemas["ghpc/subagent-join/v1"][1]["$defs"]
    except KeyError as error:
        # An absent contract is a named state, not a count of zero: measuring
        # the prose against a vocabulary that is not there would silently agree
        # with whatever the documents happened to say.
        raise Red(f"a contract the stated counts are measured from is absent: {error}") from error
    if epoch["portfolio_state"]["enum"] != join["portfolio_state"]["enum"]:
        raise Red(
            "the epoch and the join carry different portfolio_state enums; one "
            "vocabulary has forked into two and every stated count is now "
            "describing whichever half was read"
        )
    ceilings = {
        document["properties"]["evidence_ceiling"]["const"]
        for _path, document in schemas.values()
    }
    spec = importlib.util.spec_from_file_location("_ghpc_checker", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise Red(f"cannot load the checker that owns the refusal codes: {CHECKER_PATH}")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    try:
        return {
            "ordered portfolio states": len(epoch["portfolio_state"]["enum"]),
            "drift kinds": len(epoch["typed_delta"]["properties"]["delta_kind"]["enum"]),
            "subagent roles": len(join["role"]["enum"]),
            "agent terminal states": len(
                join["agent_result"]["properties"]["terminal_state"]["enum"]
            ),
            "routing aliases": len(join["model_binding"]["properties"]["alias"]["enum"]),
            "evidence ceilings": len(ceilings),
            "checker refusal codes": len(checker.CODES),
        }
    except (KeyError, AttributeError) as error:
        raise Red(f"a vocabulary the stated counts are measured from moved: {error}") from error


def check_stated_counts(
    references: Path, schemas: dict[str, tuple[Path, dict[str, Any]]]
) -> list[str]:
    """No number may be stated in prose unless the contracts still measure it.

    This is the ratchet, not a nicety. A denominator that moved and a sentence
    that did not is how a document stops describing the tree while still
    reading like it does, and it is the failure this repository has already
    paid for more than once.
    """
    if references.resolve() != DEFAULT_REFERENCES.resolve():
        return []
    failures: list[str] = []
    counted = measured_counts(schemas)
    documents = {
        name: (SKILL / name).read_text(encoding="utf-8")
        for name in ROUTING_DOCUMENTS + ("references/controlled-vocabulary.md",)
        if (SKILL / name).is_file()
    }
    for label, measured in sorted(counted.items()):
        pattern = re.compile(rf"(\d+) {re.escape(label)}")
        sites = 0
        for name, text in sorted(documents.items()):
            for match in pattern.finditer(text):
                sites += 1
                if int(match.group(1)) != measured:
                    failures.append(
                        f"{name} states {match.group(0)!r} and the contracts "
                        f"measure {measured}"
                    )
        if sites == 0:
            failures.append(
                f"no document states a count for {label!r}; the count is the "
                f"reconciliation, and removing it is not satisfying it "
                f"(measured now: {measured})"
            )
    return failures


def check_pinned_instruction(
    references: Path, schemas: dict[str, tuple[Path, dict[str, Any]]]
) -> list[str]:
    """The one string the plane may not paraphrase, arriving twice."""
    data_path = references / "coordinator-instruction.json"
    if not data_path.is_file():
        return [f"pinned instruction data absent: {data_path}"]
    data = json.loads(data_path.read_text(encoding="utf-8"))
    stored = data.get("instruction")
    if JOIN_SCHEMA not in schemas:
        return [f"{JOIN_SCHEMA} is absent, so the pinned instruction has one arrival only"]
    _path, join = schemas[JOIN_SCHEMA]
    declared = join.get("properties", {}).get("coordinator_instruction", {}).get("const")
    if stored != declared:
        return [
            "coordinator instruction differs between "
            f"references/coordinator-instruction.json ({stored!r}) and "
            f"{JOIN_SCHEMA} ({declared!r})"
        ]
    return []


def verify(references: Path) -> tuple[list[str], dict[str, int]]:
    failures: list[str] = []
    schemas = load_schemas(references)
    counts = {"schemas": len(schemas), "positives": 0, "controls": 0, "knockouts": 0}

    for identity, (path, document) in sorted(schemas.items()):
        validator = Draft202012Validator(document)
        for index, example in enumerate(document.get("examples", [])):
            counts["positives"] += 1
            errors = list(validator.iter_errors(example))
            if errors:
                failures.append(
                    f"positive {identity}#examples[{index}] rejected: {errors[0].message}"
                )
        for control in document.get("x-refusal-controls", []):
            counts["controls"] += 1
            case = control.get("case_id", "<unnamed>")
            named = control["refused_by"]
            if re.search(r"\s+and\s+", named):
                failures.append(
                    f"control {case} names more than one keyword ({named!r}); a control "
                    f"that needs two guards does not prove either of them"
                )
                continue
            if ".not." in named or named.endswith(".not"):
                failures.append(
                    f"control {case} names a keyword inside a `not` ({named!r}); removing "
                    f"it leaves `not: {{}}`, which refuses everything and credits the guard "
                    f"for a refusal it did not make"
                )
                continue
            instance = control["instance"]
            if not list(validator.iter_errors(instance)):
                failures.append(f"control {case} is not refused by {identity} at all")
                continue
            mutated = copy.deepcopy(document)
            try:
                remove_keyword(mutated, named)
            except (KeyError, IndexError, TypeError):
                failures.append(
                    f"control {case}: refused_by path {named!r} is not in {path.name}"
                )
                continue
            counts["knockouts"] += 1
            residual = list(Draft202012Validator(mutated).iter_errors(instance))
            if residual:
                failures.append(
                    f"control {case} is still refused after {named!r} was removed "
                    f"({residual[0].message}), so it does not discriminate the guard it names"
                )

    failures.extend(check_routes(references, schemas))
    failures.extend(check_stated_counts(references, schemas))
    failures.extend(check_pinned_instruction(references, schemas))
    return failures, counts


def prove_red_path(references: Path) -> str:
    """Plant one defect on a throwaway copy and require the suite to go red."""
    with tempfile.TemporaryDirectory(prefix="ghpc-red-path-") as tmp:
        copy_root = Path(tmp) / "references"
        shutil.copytree(references, copy_root)
        target = copy_root / PLANTED_FILE
        document = json.loads(target.read_text(encoding="utf-8"))
        remove_keyword(document, PLANTED_KEYWORD)
        target.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")
        failures, _counts = verify(copy_root)
        if not failures:
            raise Red(
                f"planted defect survived: removing {PLANTED_KEYWORD} from "
                f"{PLANTED_FILE} left the suite green, so its green is not evidence"
            )
        return failures[0]


def main() -> int:
    override = os.environ.get("GHPC_REFERENCES")
    references = Path(override).resolve() if override else DEFAULT_REFERENCES
    if not references.is_dir():
        raise Red(f"subject is not a directory: {references}")

    failures, counts = verify(references)
    print(
        f"subject={references} schemas={counts['schemas']} "
        f"positives={counts['positives']} controls={counts['controls']} "
        f"knockouts={counts['knockouts']}"
    )
    if failures:
        for item in failures:
            print(f"GHPC-SELFTEST-RED {item}", file=sys.stderr)
        return 2

    observed = prove_red_path(references)
    print(
        f"GHPC-SELFTEST-GREEN {counts['positives']} positive instances validate, "
        f"{counts['controls']} controls refused, {counts['knockouts']} of "
        f"{counts['controls']} discriminating under knockout of their own named "
        f"keyword; red path proven by planting {PLANTED_KEYWORD} in "
        f"{PLANTED_FILE} -> {observed}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Red as red:
        print(f"GHPC-SELFTEST-RED {red}", file=sys.stderr)
        raise SystemExit(2)
