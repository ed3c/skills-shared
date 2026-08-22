#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHECKER = ROOT / "scripts" / "check_case_graph.py"
SCHEMA = ROOT / "references" / "case-graph.schema.json"
TEMPLATE = ROOT / "references" / "case-graph-template.json"
GOOD = HERE / "fixtures" / "good.json"

spec = importlib.util.spec_from_file_location("case_graph_checker", CHECKER)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
base = json.loads(GOOD.read_text(encoding="utf-8"))
template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
validator = Draft202012Validator(schema)
Draft202012Validator.check_schema(schema)


def shape_errors(doc: dict) -> list[str]:
    return [error.message for error in validator.iter_errors(doc)]


def expect_green(name: str, doc: dict) -> None:
    shape = shape_errors(doc)
    if shape:
        raise AssertionError(f"{name}: schema red: {shape}")
    errors = mod.validate(doc)
    if errors:
        raise AssertionError(f"{name}: expected green, got {errors}")


def expect_red(name: str, doc: dict, needle: str) -> None:
    errors = mod.validate(doc)
    if not errors:
        raise AssertionError(f"{name}: expected red")
    joined = "\n".join(errors)
    if needle not in joined:
        raise AssertionError(f"{name}: expected {needle!r}; got {joined}")


expect_green("positive migration-copy graph", base)
expect_green("non-laundering prototype template", template)

m = copy.deepcopy(base)
m["cases"][1]["implementation_ids"] = []
m["coverage"]["required_case"] = 0.5
m["coverage"]["implementation_binding"] = 0.5
m["gate"]["status"] = "READY_FOR_PROTOTYPE"
expect_red("orphan required case", m, "requires implementation_ids")

m = copy.deepcopy(base)
m["source_behaviors"][1]["disposition"] = "UNMAPPED"
m["coverage"]["source_behavior_disposition"] = 0.5
m["gate"]["status"] = "READY_FOR_PROTOTYPE"
expect_red("silent semantic loss", m, "invalid/unmapped disposition")

m = copy.deepcopy(base)
m["edges"] = [e for e in m["edges"] if not (e["from"] == "SRC-002" and e["to"] == "CASE-002")]
m["coverage"]["source_behavior_disposition"] = 0.5
m["gate"]["status"] = "READY_FOR_PROTOTYPE"
expect_red("unbound source behavior", m, "requires a case edge")

m = copy.deepcopy(base)
m["source_behaviors"][1]["disposition"] = "DROP_EXPLICIT"
m["source_behaviors"][1]["decision_id"] = None
m["gate"]["status"] = "READY_FOR_PROTOTYPE"
expect_red("unauthorized drop", m, "requires decision_id")

m = copy.deepcopy(base)
m["cases"][1]["oracle_ids"] = []
m["coverage"]["required_case"] = 0.5
m["coverage"]["oracle"] = 0.5
m["gate"]["status"] = "READY_FOR_PROTOTYPE"
expect_red("required case without oracle", m, "requires oracle_ids")

# An empty REQUIRED_CASE denominator makes every ratio vacuously 1.0; a READY
# gate must refuse it instead of admitting a graph that proves nothing.
m = copy.deepcopy(base)
for case in m["cases"]:
    case["classification"] = "DUPLICATE_EQUIVALENCE_CLASS"
expect_red("empty required-case denominator", m, "non-empty REQUIRED_CASE denominator")

m = copy.deepcopy(base)
m["cases"][1]["evidence_ids"] = []
m["coverage"]["executed_evidence"] = 0.5
m["gate"]["status"] = "READY_FOR_IMPLEMENTATION"
expect_red("evidence laundering", m, "PASS requires evidence_ids")

m = copy.deepcopy(base)
m["evidence"][1]["state"] = "NOT_EXERCISED"
m["coverage"]["executed_evidence"] = 0.5
m["gate"]["status"] = "READY_FOR_IMPLEMENTATION"
expect_red("evidence state mismatch", m, "is not backed by referenced evidence")

# Executed FAIL is still execution coverage, but cannot authorize publication.
m = copy.deepcopy(base)
m["cases"][1]["evidence_state"] = "FAIL"
m["evidence"][1]["state"] = "FAIL"
expect_red("failed required case publication", m, "every required case to have subject-bound PASS evidence")

m = copy.deepcopy(base)
m["edges"].append({"from": "EVID-002", "to": "INT-002", "kind": "INVALID_BACKEDGE"})
expect_red("provenance cycle", m, "contains a cycle")

m = copy.deepcopy(base)
m["cases"].append({
    "id": "CASE-003",
    "classification": "UNKNOWN_BLOCKING",
    "intent_ids": ["INT-002"],
    "axis_ids": ["AXIS-002"],
    "invariant_or_state_refs": [],
    "implementation_ids": [],
    "oracle_ids": [],
    "evidence_ids": [],
    "decision_id": None,
    "evidence_state": "ABSENT"
})
m["coverage"]["unknown_blocking_count"] = 1
expect_red("unknown blocking promotion", m, "require gate BLOCKED")

m = copy.deepcopy(base)
m["intent_atoms"].append({"id": "INT-003", "statement": "Preserve recovery semantics."})
expect_red("hidden intent denominator", m, "coverage.intent must be recomputed")

# Node identity is global across the provenance DAG, not merely unique inside
# each node family. Otherwise an edge endpoint can become ambiguous.
m = copy.deepcopy(base)
m["oracles"][1]["id"] = "INT-002"
expect_red("cross-category duplicate id", m, "duplicate id INT-002 across intent_atoms and oracles")

# Implementation and evidence receipts must bind the exact graph revision and
# digest; a path-looking subject_ref alone cannot prove freshness.
m = copy.deepcopy(base)
m["implementations"][1]["subject_revision"] = "stale-revision"
expect_red("stale implementation subject", m, "implementation IMPL-002 subject_revision")

m = copy.deepcopy(base)
m["evidence"][1]["subject_digest"] = "sha256:" + "f" * 64
expect_red("stale evidence subject", m, "evidence EVID-002 subject_digest")

# Decision records are authority-bearing state, not prose labels.
m = copy.deepcopy(base)
m["source_behaviors"][1]["disposition"] = "DROP_EXPLICIT"
m["source_behaviors"][1]["decision_id"] = "DEC-001"
m["decisions"] = [{"id": "DEC-001", "authority": "", "rationale": "explicit test mutation"}]
expect_red("hollow authority decision", m, "decision DEC-001 requires authority")

print("CASE-GRAPH-MUTATIONS-GREEN exact-subject + global-id controls")
