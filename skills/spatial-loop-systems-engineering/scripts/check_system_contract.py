#!/usr/bin/env python3
"""Validate spatial-loop-system-contract/v1 with fail-closed cross-reference gates."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "spatial-loop-system-contract/v1"
EVIDENCE_STATES = {
    "PASS",
    "FAIL",
    "ABSENT",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "SKIPPED_BY_POLICY",
}
RISK_CLASSES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
GATE_STATES = {"BLOCKED", "READY_FOR_PROTOTYPE", "READY_FOR_IMPLEMENTATION"}
CLAIM_LEVELS = {"DESIGN_ONLY", "PROTOTYPE_ONLY", "IMPLEMENTATION_CANDIDATE"}
GATE_CLAIM_LEVEL = {
    "BLOCKED": "DESIGN_ONLY",
    "READY_FOR_PROTOTYPE": "PROTOTYPE_ONLY",
    "READY_FOR_IMPLEMENTATION": "IMPLEMENTATION_CANDIDATE",
}
ORACLE_TYPES = {"COMMAND", "METRIC", "FORMAL", "RUNTIME_PROBE", "REVIEW"}
VERIFICATION_LANES = {
    "STATIC",
    "MODEL_CHECK",
    "UNIT",
    "INTEGRATION",
    "PRIVILEGED",
    "HARDWARE",
    "FUZZ",
    "CHAOS",
    "SECURITY",
    "PERFORMANCE",
    "RECOVERY",
    "TEARDOWN",
}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PERFORMANCE_RE = re.compile(
    r"\b(fast|faster|high[- ]performance|low[- ]latency|latency|throughput|"
    r"zero[- ]copy|zero[- ]overhead|microsecond|millisecond|cold[- ]start|instant)\b|"
    r"(高效能|低延遲|延遲|吞吐|零拷貝|零開銷|微秒|毫秒|冷啟動|瞬時)",
    re.IGNORECASE,
)


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, label: str, message: str) -> None:
        self.errors.append(f"{label}: {message}")

    def obj(self, value: Any, label: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            self.error(label, "must be an object")
            return {}
        return value

    def array(self, value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
        if not isinstance(value, list):
            self.error(label, "must be an array")
            return []
        if nonempty and not value:
            self.error(label, "must be a non-empty array")
        return value

    def string(self, value: Any, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            self.error(label, "must be a non-empty string")
            return ""
        return value.strip()

    def boolean(self, value: Any, label: str) -> bool:
        if not isinstance(value, bool):
            self.error(label, "must be a boolean")
            return False
        return value

    def string_array(
        self, value: Any, label: str, *, nonempty: bool = False
    ) -> list[str]:
        values = self.array(value, label, nonempty=nonempty)
        result: list[str] = []
        for index, item in enumerate(values):
            text = self.string(item, f"{label}[{index}]")
            if text:
                result.append(text)
        if len(result) != len(set(result)):
            self.error(label, "must not contain duplicates")
        return result

    def ids(
        self, values: list[Any], label: str, *, nonempty: bool = True
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        if nonempty and not values:
            self.error(label, "must be a non-empty array")
        objects: list[dict[str, Any]] = []
        index: dict[str, dict[str, Any]] = {}
        for position, value in enumerate(values):
            item = self.obj(value, f"{label}[{position}]")
            objects.append(item)
            item_id = self.string(item.get("id"), f"{label}[{position}].id")
            if not item_id:
                continue
            if item_id in index:
                self.error(f"{label}[{position}].id", f"duplicate id {item_id}")
            else:
                index[item_id] = item
        return objects, index

    def evidence(
        self, item: dict[str, Any], label: str, *, state_field: str = "state"
    ) -> str:
        state = self.string(item.get(state_field), f"{label}.{state_field}")
        if state and state not in EVIDENCE_STATES:
            self.error(
                f"{label}.{state_field}",
                f"must be one of {sorted(EVIDENCE_STATES)}",
            )
        evidence = self.string_array(item.get("evidence"), f"{label}.evidence")
        if state in {"PASS", "FAIL"} and not evidence:
            self.error(f"{label}.evidence", f"{state} requires evidence")
        return state

    def oracle(self, value: Any, label: str) -> dict[str, Any]:
        oracle = self.obj(value, label)
        oracle_type = self.string(oracle.get("type"), f"{label}.type")
        if oracle_type and oracle_type not in ORACLE_TYPES:
            self.error(f"{label}.type", f"must be one of {sorted(ORACLE_TYPES)}")
        self.string(oracle.get("procedure"), f"{label}.procedure")
        self.string(oracle.get("pass_condition"), f"{label}.pass_condition")
        return oracle


def validate_contract(document: Any) -> list[str]:
    v = Validation()
    root = v.obj(document, "$")
    if root.get("schema") != SCHEMA:
        v.error("$.schema", f"must equal {SCHEMA!r}")

    subject = v.obj(root.get("subject"), "subject")
    v.string(subject.get("id"), "subject.id")
    v.string(subject.get("revision"), "subject.revision")
    digest = v.string(subject.get("digest"), "subject.digest")
    if digest and not DIGEST_RE.fullmatch(digest):
        v.error("subject.digest", "must be sha256:<64 lowercase hex>")

    objective = v.obj(root.get("objective"), "objective")
    objective_statement = v.string(objective.get("statement"), "objective.statement")
    v.string_array(objective.get("non_goals"), "objective.non_goals", nonempty=True)
    risk_class = v.string(objective.get("risk_class"), "objective.risk_class")
    if risk_class and risk_class not in RISK_CLASSES:
        v.error("objective.risk_class", f"must be one of {sorted(RISK_CLASSES)}")

    assumption_values = v.array(root.get("assumptions"), "assumptions", nonempty=True)
    assumptions, assumption_index = v.ids(assumption_values, "assumptions")
    assumption_states: dict[str, tuple[bool, str]] = {}
    for i, item in enumerate(assumptions):
        label = f"assumptions[{i}]"
        item_id = item.get("id")
        v.string(item.get("statement"), f"{label}.statement")
        v.string(item.get("owner"), f"{label}.owner")
        v.string(item.get("falsifier"), f"{label}.falsifier")
        required = v.boolean(item.get("required"), f"{label}.required")
        state = v.evidence(item, label)
        if isinstance(item_id, str):
            assumption_states[item_id] = (required, state)

    unknown_values = v.array(root.get("unknowns"), "unknowns")
    unknowns, unknown_index = v.ids(unknown_values, "unknowns", nonempty=False)
    for i, item in enumerate(unknowns):
        label = f"unknowns[{i}]"
        v.string(item.get("statement"), f"{label}.statement")
        v.string(item.get("discovery_method"), f"{label}.discovery_method")
        v.string(item.get("impact"), f"{label}.impact")
        v.evidence(item, label)

    realm_values = v.array(root.get("realms"), "realms", nonempty=True)
    realms, realm_index = v.ids(realm_values, "realms")
    if len(realm_index) < 2:
        v.error("realms", "must define at least two distinct realms")
    for i, item in enumerate(realms):
        label = f"realms[{i}]"
        v.string(item.get("trust"), f"{label}.trust")
        v.string(item.get("authority"), f"{label}.authority")
        v.string_array(
            item.get("entry_conditions"), f"{label}.entry_conditions", nonempty=True
        )
        v.string_array(
            item.get("exit_conditions"), f"{label}.exit_conditions", nonempty=True
        )

    boundary_values = v.array(root.get("boundaries"), "boundaries", nonempty=True)
    boundaries, _ = v.ids(boundary_values, "boundaries")
    for i, item in enumerate(boundaries):
        label = f"boundaries[{i}]"
        source = v.string(item.get("from"), f"{label}.from")
        target = v.string(item.get("to"), f"{label}.to")
        if source and source not in realm_index:
            v.error(f"{label}.from", f"references unknown realm {source}")
        if target and target not in realm_index:
            v.error(f"{label}.to", f"references unknown realm {target}")
        v.string(item.get("mechanism"), f"{label}.mechanism")
        v.string(item.get("enforcement_owner"), f"{label}.enforcement_owner")
        v.string(item.get("blast_radius"), f"{label}.blast_radius")
        v.string(item.get("failure_behavior"), f"{label}.failure_behavior")

    flow_values = v.array(root.get("flows"), "flows", nonempty=True)
    flows, _ = v.ids(flow_values, "flows")
    for i, item in enumerate(flows):
        label = f"flows[{i}]"
        source = v.string(item.get("from"), f"{label}.from")
        target = v.string(item.get("to"), f"{label}.to")
        if source and source not in realm_index:
            v.error(f"{label}.from", f"references unknown realm {source}")
        if target and target not in realm_index:
            v.error(f"{label}.to", f"references unknown realm {target}")
        for field in (
            "payload",
            "transport",
            "ordering",
            "backpressure",
            "failure_semantics",
        ):
            v.string(item.get(field), f"{label}.{field}")

    states = v.obj(root.get("states"), "states")
    nodes = v.string_array(states.get("nodes"), "states.nodes", nonempty=True)
    node_set = set(nodes)
    initial = v.string(states.get("initial"), "states.initial")
    if initial and initial not in node_set:
        v.error("states.initial", f"references unknown state {initial}")
    terminal = v.string_array(states.get("terminal"), "states.terminal", nonempty=True)
    for state in terminal:
        if state not in node_set:
            v.error("states.terminal", f"references unknown state {state}")

    transition_values = v.array(
        states.get("transitions"), "states.transitions", nonempty=True
    )
    transitions, transition_index = v.ids(transition_values, "states.transitions")
    for i, item in enumerate(transitions):
        label = f"states.transitions[{i}]"
        source = v.string(item.get("from"), f"{label}.from")
        target = v.string(item.get("to"), f"{label}.to")
        if source and source not in node_set:
            v.error(f"{label}.from", f"references unknown state {source}")
        if target and target not in node_set:
            v.error(f"{label}.to", f"references unknown state {target}")
        v.string(item.get("trigger"), f"{label}.trigger")
        v.string_array(
            item.get("preconditions"), f"{label}.preconditions", nonempty=True
        )
        v.string_array(
            item.get("postconditions"), f"{label}.postconditions", nonempty=True
        )
        v.string_array(item.get("evidence"), f"{label}.evidence", nonempty=True)

    invariant_values = v.array(root.get("invariants"), "invariants", nonempty=True)
    invariants, _ = v.ids(invariant_values, "invariants")
    invariant_statements: list[str] = []
    for i, item in enumerate(invariants):
        label = f"invariants[{i}]"
        statement = v.string(item.get("statement"), f"{label}.statement")
        if statement:
            invariant_statements.append(statement)
        for field in ("scope", "owner", "enforcement", "failure_state"):
            v.string(item.get(field), f"{label}.{field}")
        v.oracle(item.get("oracle"), f"{label}.oracle")

    capability_values = v.array(
        root.get("capabilities"), "capabilities", nonempty=True
    )
    capabilities, capability_index = v.ids(capability_values, "capabilities")
    capability_states: dict[str, tuple[bool, str]] = {}
    for i, item in enumerate(capabilities):
        label = f"capabilities[{i}]"
        item_id = item.get("id")
        v.string(item.get("statement"), f"{label}.statement")
        required = v.boolean(item.get("required"), f"{label}.required")
        v.oracle(item.get("probe"), f"{label}.probe")
        state = v.evidence(item, label)
        v.string(
            item.get("consequence_if_absent"), f"{label}.consequence_if_absent"
        )
        if isinstance(item_id, str):
            capability_states[item_id] = (required, state)

    resource_values = v.array(root.get("resources"), "resources", nonempty=True)
    resources, resource_index = v.ids(resource_values, "resources")
    lifecycle_owned: set[str] = set()
    for i, item in enumerate(resources):
        label = f"resources[{i}]"
        resource_id = item.get("id")
        realm = v.string(item.get("realm"), f"{label}.realm")
        if realm and realm not in realm_index:
            v.error(f"{label}.realm", f"references unknown realm {realm}")
        v.string(item.get("kind"), f"{label}.kind")
        limit_value = item.get("limit_value")
        if (
            isinstance(limit_value, bool)
            or not isinstance(limit_value, (int, float))
            or limit_value <= 0
        ):
            v.error(f"{label}.limit_value", "must be a positive number")
        for field in ("unit", "enforcement", "observation", "exceed_action"):
            v.string(item.get(field), f"{label}.{field}")
        owned = v.boolean(item.get("lifecycle_owned"), f"{label}.lifecycle_owned")
        if owned and isinstance(resource_id, str):
            lifecycle_owned.add(resource_id)

    failure_values = v.array(root.get("failures"), "failures", nonempty=True)
    failures, _ = v.ids(failure_values, "failures")
    for i, item in enumerate(failures):
        label = f"failures[{i}]"
        for field in (
            "fault",
            "collision_window",
            "detection",
            "containment",
            "reconciliation",
        ):
            v.string(item.get(field), f"{label}.{field}")
        v.oracle(item.get("oracle"), f"{label}.oracle")

    teardown_values = v.array(root.get("teardown"), "teardown", nonempty=True)
    teardowns: list[dict[str, Any]] = []
    teardown_resources: set[str] = set()
    for i, value in enumerate(teardown_values):
        label = f"teardown[{i}]"
        item = v.obj(value, label)
        teardowns.append(item)
        resource = v.string(item.get("resource"), f"{label}.resource")
        if resource:
            if resource not in resource_index:
                v.error(f"{label}.resource", f"references unknown resource {resource}")
            if resource in teardown_resources:
                v.error(f"{label}.resource", f"duplicate teardown for {resource}")
            teardown_resources.add(resource)
        for field in ("acquire_transition", "release_transition"):
            transition = v.string(item.get(field), f"{label}.{field}")
            if transition and transition not in transition_index:
                v.error(
                    f"{label}.{field}",
                    f"references unknown transition {transition}",
                )
        crash_transitions = v.string_array(
            item.get("crash_transitions"),
            f"{label}.crash_transitions",
            nonempty=True,
        )
        for transition in crash_transitions:
            if transition not in transition_index:
                v.error(
                    f"{label}.crash_transitions",
                    f"references unknown transition {transition}",
                )
        v.oracle(item.get("leak_oracle"), f"{label}.leak_oracle")

    missing_teardown = sorted(lifecycle_owned - teardown_resources)
    extra_teardown = sorted(teardown_resources - lifecycle_owned)
    for resource in missing_teardown:
        v.error("teardown", f"lifecycle-owned resource {resource} has no teardown")
    for resource in extra_teardown:
        v.error(
            "teardown",
            f"resource {resource} is not marked lifecycle_owned but has teardown",
        )

    loop_values = v.array(
        root.get("reconciliation_loops"),
        "reconciliation_loops",
        nonempty=True,
    )
    loops, _ = v.ids(loop_values, "reconciliation_loops")
    for i, item in enumerate(loops):
        label = f"reconciliation_loops[{i}]"
        v.string_array(item.get("observes"), f"{label}.observes", nonempty=True)
        for field in (
            "desired_state",
            "diff",
            "actuator",
            "convergence",
            "stop_condition",
        ):
            v.string(item.get(field), f"{label}.{field}")

    budget_values = v.array(root.get("performance_budgets"), "performance_budgets")
    budgets, _ = v.ids(budget_values, "performance_budgets", nonempty=False)
    for i, item in enumerate(budgets):
        label = f"performance_budgets[{i}]"
        v.string(item.get("metric"), f"{label}.metric")
        target = item.get("target")
        if isinstance(target, bool) or not isinstance(target, (int, float)):
            v.error(f"{label}.target", "must be a number")
        v.string(item.get("unit"), f"{label}.unit")
        v.string(item.get("percentile"), f"{label}.percentile")
        v.string(item.get("load_model"), f"{label}.load_model")
        v.string(
            item.get("environment_identity"), f"{label}.environment_identity"
        )
        v.string(item.get("measurement"), f"{label}.measurement")
        repetitions = item.get("repetitions")
        if (
            isinstance(repetitions, bool)
            or not isinstance(repetitions, int)
            or repetitions <= 0
        ):
            v.error(f"{label}.repetitions", "must be a positive integer")

    performance_text = " ".join([objective_statement, *invariant_statements])
    if performance_text and PERFORMANCE_RE.search(performance_text) and not budgets:
        v.error(
            "performance_budgets",
            "performance claim requires at least one performance_budgets entry",
        )

    verification_values = v.array(
        root.get("verification"), "verification", nonempty=True
    )
    verifications, verification_index = v.ids(
        verification_values, "verification"
    )
    verification_states: dict[str, tuple[bool, str]] = {}
    for i, item in enumerate(verifications):
        label = f"verification[{i}]"
        item_id = item.get("id")
        required = v.boolean(item.get("required"), f"{label}.required")
        lane = v.string(item.get("lane"), f"{label}.lane")
        if lane and lane not in VERIFICATION_LANES:
            v.error(
                f"{label}.lane",
                f"must be one of {sorted(VERIFICATION_LANES)}",
            )
        v.string_array(
            item.get("preconditions"), f"{label}.preconditions", nonempty=True
        )
        v.string(item.get("stimulus"), f"{label}.stimulus")
        v.oracle(item.get("oracle"), f"{label}.oracle")
        v.string(item.get("negative_control"), f"{label}.negative_control")
        state = v.evidence(item, label, state_field="status")
        if isinstance(item_id, str):
            verification_states[item_id] = (required, state)

    gate = v.obj(root.get("implementation_gate"), "implementation_gate")
    gate_status = v.string(gate.get("status"), "implementation_gate.status")
    if gate_status and gate_status not in GATE_STATES:
        v.error(
            "implementation_gate.status",
            f"must be one of {sorted(GATE_STATES)}",
        )
    claim_level = v.string(
        gate.get("claim_level"), "implementation_gate.claim_level"
    )
    if claim_level and claim_level not in CLAIM_LEVELS:
        v.error(
            "implementation_gate.claim_level",
            f"must be one of {sorted(CLAIM_LEVELS)}",
        )
    if gate_status in GATE_CLAIM_LEVEL and claim_level:
        expected = GATE_CLAIM_LEVEL[gate_status]
        if claim_level != expected:
            v.error(
                "implementation_gate.claim_level",
                f"{gate_status} requires {expected}",
            )

    blocking_unknowns = v.string_array(
        gate.get("blocking_unknowns"), "implementation_gate.blocking_unknowns"
    )
    for unknown in blocking_unknowns:
        if unknown not in unknown_index:
            v.error(
                "implementation_gate.blocking_unknowns",
                f"references unknown unknown {unknown}",
            )
    v.string_array(
        gate.get("allowed_actions"),
        "implementation_gate.allowed_actions",
        nonempty=True,
    )
    v.string_array(
        gate.get("forbidden_claims"),
        "implementation_gate.forbidden_claims",
        nonempty=True,
    )
    v.string(gate.get("rationale"), "implementation_gate.rationale")

    if gate_status == "READY_FOR_IMPLEMENTATION":
        if blocking_unknowns:
            v.error(
                "implementation_gate.blocking_unknowns",
                "READY_FOR_IMPLEMENTATION requires no blocking unknowns",
            )
        for capability_id, (required, state) in capability_states.items():
            if required and state != "PASS":
                v.error(
                    "implementation_gate.status",
                    f"required capability {capability_id} is {state or 'invalid'}, not PASS",
                )
        for assumption_id, (required, state) in assumption_states.items():
            if required and state != "PASS":
                v.error(
                    "implementation_gate.status",
                    f"required assumption {assumption_id} is {state or 'invalid'}, not PASS",
                )
        for verification_id, (required, state) in verification_states.items():
            if required and state not in {"PASS", "NOT_EXERCISED"}:
                v.error(
                    "implementation_gate.status",
                    f"required verification {verification_id} is {state or 'invalid'}; "
                    "its mechanism must exist and be PASS or NOT_EXERCISED",
                )

    v.string_array(root.get("human_admit"), "human_admit", nonempty=True)

    return v.errors


def load_document(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in {path}: {exc}") from exc


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] != "check":
        print(
            "USAGE: check_system_contract.py check <system-contract.json>",
            file=sys.stderr,
        )
        return 64

    path = Path(argv[2])
    if not path.is_file():
        print(f"CONTRACT INPUT ERROR: file not found: {path}", file=sys.stderr)
        return 64

    try:
        document = load_document(path)
    except RuntimeError as exc:
        print(f"CONTRACT INPUT ERROR: {exc}", file=sys.stderr)
        return 64

    errors = validate_contract(document)
    if errors:
        for error in errors:
            print(f"CONTRACT RED: {error}", file=sys.stderr)
        return 2

    subject = document["subject"]["id"]
    gate = document["implementation_gate"]["status"]
    print(f"CONTRACT GREEN: subject={subject} gate={gate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
