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

# Closure is opt-in by key presence (pre-invariant graphs stay valid), so the
# exemplar itself must keep the array — losing it would silently switch the
# whole closure lane off for everything cloned from this fixture.
assert "invariants" in base, "fixture must declare invariants; closure is key-presence-gated"
assert "invariants" in template, "template must declare invariants; closure is key-presence-gated"

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

# Reclassifying a required case out of scope is the cheapest silent scope
# reduction available; it needs the same decision record as an explicit drop.
m = copy.deepcopy(base)
m["cases"][1]["classification"] = "OUT_OF_SCOPE_EXPLICIT"
expect_red("undecided scope reduction", m, "out-of-scope case CASE-002 requires decision_id")

# Declared invariants live in the one global id space and must close in both
# directions: no case may reference an undeclared one, and no declared one may
# sit unreferenced as decoration.
m = copy.deepcopy(base)
m["invariants"].append({"id": "INV-COMPAT", "statement": "Second declaration of the same invariant id."})
expect_red("duplicate invariant id", m, "duplicate id INV-COMPAT within invariants")

m = copy.deepcopy(base)
m["invariants"] = [inv for inv in m["invariants"] if inv["id"] != "INV-BRANCH-B"]
expect_red("dangling invariant reference", m, "case CASE-002 references undeclared invariant INV-BRANCH-B")

m = copy.deepcopy(base)
m["invariants"].append({"id": "INV-ORPHANED", "statement": "Declared but bound to no case."})
expect_red("unreferenced declared invariant", m, "invariant INV-ORPHANED is referenced by no case")

m = copy.deepcopy(base)
m["invariants"][0]["statement"] = "   "
expect_red("hollow invariant statement", m, "invariant INV-COMPAT requires statement")

# The schema and the checker are two independent enforcement surfaces. A term
# added to one and not the other silently stops being enforced on the way in.
vocabularies = {
    "source behavior disposition": (
        set(schema["$defs"]["sourceBehavior"]["properties"]["disposition"]["enum"]),
        mod.PRESERVATION_DISPOSITIONS | mod.DECISION_REQUIRED | {"UNKNOWN_BLOCKING"},
    ),
    "case classification": (
        set(schema["$defs"]["caseNode"]["properties"]["classification"]["enum"]),
        mod.CASE_CLASSES,
    ),
    "gate status": (
        set(schema["properties"]["gate"]["properties"]["status"]["enum"]),
        mod.GATES,
    ),
    "case evidence_state": (
        set(schema["$defs"]["caseNode"]["properties"]["evidence_state"]["enum"]),
        mod.EVIDENCE_STATES,
    ),
    "evidence state": (
        set(schema["$defs"]["evidence"]["properties"]["state"]["enum"]),
        mod.EVIDENCE_STATES,
    ),
}
for vocabulary, (from_schema, from_checker) in vocabularies.items():
    if from_schema != from_checker:
        raise AssertionError(
            f"{vocabulary} vocabulary drifted: schema-only={sorted(from_schema - from_checker)}, "
            f"checker-only={sorted(from_checker - from_schema)}"
        )

# Structural required-key parity: the shipped fixture and template must satisfy
# the schema's own required lists node-by-node, not merely validate as a whole.
NODE_DEFS = {
    "intent_atoms": "idNode",
    "semantic_axes": "axisNode",
    "source_behaviors": "sourceBehavior",
    "cases": "caseNode",
    "implementations": "implementation",
    "oracles": "oracle",
    "evidence": "evidence",
    "decisions": "decision",
    "invariants": "invariant",
    "edges": "edge",
}
for label, doc in (("fixture good.json", base), ("template case-graph-template.json", template)):
    missing = [key for key in schema["required"] if key not in doc]
    if missing:
        raise AssertionError(f"{label} missing schema-required top-level keys {missing}")
    for member, def_name in NODE_DEFS.items():
        required = schema["$defs"][def_name]["required"]
        for i, node in enumerate(doc.get(member, [])):
            absent = [field for field in required if field not in node]
            if absent:
                raise AssertionError(f"{label} {member}[{i}] missing schema-required keys {absent}")
    for member in ("subject", "coverage", "gate"):
        required = schema["properties"][member]["required"]
        absent = [field for field in required if field not in doc.get(member, {})]
        if absent:
            raise AssertionError(f"{label} {member} missing schema-required keys {absent}")

print("CASE-GRAPH-MUTATIONS-GREEN exact-subject + global-id + invariant-closure + schema-parity controls")
