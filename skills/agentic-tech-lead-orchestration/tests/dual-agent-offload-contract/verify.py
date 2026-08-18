#!/usr/bin/env python3
"""Execute the portable Dual-Agent offload method contract and its handoff packet.

Two documents, one gate. `method-contract.v1.schema.json` freezes the portable
vocabulary, the authority map and the *logical* runtime contracts an
implementation plane must satisfy. `handoff-requirements.v1.schema.json` binds
one exact subject to that frozen method and keeps start-readiness and
completion-readiness in separate arrays, because a start dependency can never
close a completion edge.

Shape is not the interesting half. Every one of the sixteen pre-registered
disagreement controls below mutates a document that stays schema-valid, so a
control only counts when a *semantic* law names the promotion. That is asserted
here, not assumed: each mutation is re-validated against its own JSON Schema
first, and a mutation the schema rejects fails the control rather than passing
it. Otherwise "the parser complained" would silently stand in for "the law
fired", and the law could be deleted without anything turning red.

This plane owns method and vocabulary only. It declares that five logical
runtime contracts must exist and what they must mean; it never defines their
wire shapes. Two repositories defining one interface is the drift this file
exists to make impossible, so M01 checks both the declared owner plane and the
directory itself.

Exit codes: 0 pass, 2 contract or control failure, 64 unreadable input.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Iterator

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

SKILL_ROOT = Path(__file__).resolve().parents[2]
REFERENCES = SKILL_ROOT / "references" / "dual-agent-offload"
CASES = SKILL_ROOT / "cases.json"

METHOD_SCHEMA = REFERENCES / "method-contract.v1.schema.json"
HANDOFF_SCHEMA = REFERENCES / "handoff-requirements.v1.schema.json"
METHOD_EXAMPLE = REFERENCES / "example-method-contract.json"
HANDOFF_EXAMPLE = REFERENCES / "example-handoff-requirements.json"
METHOD_DOCUMENT = REFERENCES / "OFFLOAD_METHOD.md"

# --- frozen portable vocabulary -------------------------------------------
# Frozen means frozen: the point of a contract leaf is that a later lane cannot
# quietly add a data class, drop a failure distinction, or rename a lane and
# still look green.
FROZEN_STATE_CHAIN = [
    "LOCAL_INTENT_BOUND",
    "DATA_CLASSIFIED",
    "AUTHORITY_AND_EFFECTS_DECLARED",
    "REQUIRED_RUNTIME_CONTRACTS_DECLARED",
    "OFFLOAD_HANDOFF_FROZEN",
]
FROZEN_DATA_CLASSES = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "LOCAL_ONLY"]
FROZEN_SIDE_EFFECT_CLASSES = ["READ_ONLY", "REVERSIBLE_WRITE", "IRREVERSIBLE_WRITE"]
FROZEN_LANES = [
    "LOCAL",
    "CLOUD",
    "TRANSPORT",
    "WORKFLOW",
    "TASK",
    "GATE",
    "EFFECT",
    "ARTIFACT",
    "USER_OUTCOME",
    "HUMAN_ADMIT",
    "RELEASE",
]
FROZEN_FAILURE_DISTINCTIONS = [
    "DISCONNECT",
    "DUPLICATE",
    "TIMEOUT",
    "CANCELLATION",
    "STALE_RESULT",
    "POLICY_REFUSAL",
    "CAPABILITY_REFUSAL",
    "PARTIAL_ARTIFACT",
    "CLEANUP_FAILURE",
    "UNKNOWN_EXTERNAL_EFFECT",
    "COMPENSATION_FAILURE",
]
FROZEN_RUNTIME_CONTRACT_IDS = [
    "runtime-env/dual-agent/offload-job/v1",
    "runtime-env/dual-agent/capability-grant/v1",
    "runtime-env/dual-agent/effect-intent/v1",
    "runtime-env/dual-agent/artifact-manifest/v1",
    "runtime-env/dual-agent/execution-receipt/v1",
]
# The wire-shape names this plane must never claim as its own identity.
WIRE_SCHEMA_NAMES = [
    "offload-job",
    "capability-grant",
    "effect-intent",
    "artifact-manifest",
    "execution-receipt",
]

CONTROL_REASONS = {
    "M01": "DUPLICATE_RUNTIME_SCHEMA_AUTHORITY",
    "M02": "MUTABLE_SUBJECT",
    "M03": "LANE_SUBSTITUTION",
    "M04": "ACK_PROMOTED_TO_TASK_PASS",
    "M05": "WRITE_WITHOUT_IDEMPOTENCY_OR_EFFECT_LEDGER",
    "M06": "LOCAL_ONLY_REMOTE_EGRESS",
    "M07": "SECRET_OR_SESSION_VALUE",
    "M08": "PROVIDER_NAME_AS_ARCHITECTURE_INVARIANT",
    "M09": "TERMINAL_STATE_COLLAPSE",
    "M10": "BROWSER_AS_API_EVIDENCE",
    "M11": "WORKER_SELF_PROMOTION",
    "M12": "START_DEPENDENCY_USED_AS_COMPLETION_PROOF",
    "M13": "SOURCE_OR_FIXTURE_AS_LIVE_PASS",
    "M14": "SHARED_MEMORY_AS_TRANSACTION_AUTHORITY",
    "M15": "CONSUMER_STATE_LEAKED_INTO_PORTABLE_CORE",
    "M16": "RUNTIME_CONTRACT_DECLARED_IMPLEMENTED_WITHOUT_DIGEST",
}

WRITE_CLASSES = {"REVERSIBLE_WRITE", "IRREVERSIBLE_WRITE"}
CAPABILITY_EVIDENCE = {
    "API": "API_OBSERVATION",
    "BROWSER_FALLBACK": "BROWSER_OBSERVATION",
    "LOCAL_PROCESS": "LOCAL_OBSERVATION",
}
SOLE_HOLDER = {
    "COMMIT_TASK_STATE": "CANONICAL_REDUCER",
    "COMMIT_EFFECT_LEDGER": "EFFECT_LEDGER",
    "EVALUATE_GATE": "GATE",
}
WORKER_CAPABILITIES = {"EXECUTE", "OBSERVE"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

SECRET_PATTERNS = [
    (re.compile(r"(?i)\bcookie\s*:\s*\S"), "HTTP cookie header"),
    (
        re.compile(r"(?i)\b(session|sid|token|secret|api[_-]?key|password|passwd)\s*=\s*\S"),
        "assigned credential or session value",
    ),
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{6,}|sk-[A-Za-z0-9]{6,}|xox[baprs]-[A-Za-z0-9-]{6,})\b"), "credential literal"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{8,}"), "bearer token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"(?i)(^|[\s\"'(])(/Users/|/home/[a-z]|/var/folders/|[A-Za-z]:\\)"), "machine-local host path"),
]
PROVIDER_PATTERNS = [
    (
        re.compile(
            r"(?i)\b(openai|chatgpt|gpt-[0-9]|anthropic|claude|gemini|copilot|bedrock|"
            r"vertex\s*ai|ollama|mistral|deepseek|qwen|cursor|codex|grok|llama)\b"
        ),
        "provider or model name",
    ),
]
CONSUMER_STATE_PATTERNS = [
    (re.compile(r"#\d+"), "consumer issue or change-request number"),
    (re.compile(r"\b[0-9a-f]{40}\b"), "exact commit SHA"),
    (re.compile(r"\b[0-9a-f]{64}\b"), "exact content digest"),
    (re.compile(r"refs/heads/|\bagent/\d"), "consumer branch reference"),
]


class Unusable(Exception):
    """The input could not be read at all. Not a contract violation."""


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Unusable(f"{path}: {error}") from error


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise Unusable(f"{path}: {error}") from error


def shape_errors(schema: dict[str, Any], document: Any, label: str) -> list[str]:
    return [
        f"SHAPE: {label}: {'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in Draft202012Validator(schema).iter_errors(document)
    ]


def walk_strings(node: Any, pointer: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk_strings(value, f"{pointer}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_strings(value, f"{pointer}/{index}")
    elif isinstance(node, str):
        yield pointer or "<root>", node


def scan(document: Any, patterns: list[tuple[re.Pattern[str], str]], reason: str) -> list[str]:
    found: list[str] = []
    for pointer, text in walk_strings(document):
        for pattern, label in patterns:
            if pattern.search(text):
                found.append(f"{reason}: {pointer} carries a {label}")
    return found


def method_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    machine = contract["state_machine"]
    if machine["states"] != FROZEN_STATE_CHAIN:
        errors.append("FROZEN_VOCABULARY_DRIFT: state chain is not the frozen offload chain")
    expected_transitions = [
        {"from": left, "to": right}
        for left, right in zip(FROZEN_STATE_CHAIN, FROZEN_STATE_CHAIN[1:])
    ]
    if machine["transitions"] != expected_transitions:
        errors.append("FROZEN_VOCABULARY_DRIFT: legal transitions are not the frozen chain edges")
    if machine["initial_state"] != FROZEN_STATE_CHAIN[0] or machine["terminal_state"] != FROZEN_STATE_CHAIN[-1]:
        errors.append("FROZEN_VOCABULARY_DRIFT: initial or terminal state drifted")
    for field, frozen in (
        ("data_classes", FROZEN_DATA_CLASSES),
        ("side_effect_classes", FROZEN_SIDE_EFFECT_CLASSES),
        ("evidence_lanes", FROZEN_LANES),
    ):
        if contract[field] != frozen:
            errors.append(f"FROZEN_VOCABULARY_DRIFT: {field} drifted from the frozen vocabulary")
    if [item["id"] for item in contract["failure_distinctions"]] != FROZEN_FAILURE_DISTINCTIONS:
        errors.append("FROZEN_VOCABULARY_DRIFT: required failure distinctions drifted")
    if set(contract["forbidden_promotions"]) != set(CONTROL_REASONS.values()):
        errors.append(
            "FROZEN_VOCABULARY_DRIFT: forbidden_promotions does not equal the executable control set"
        )

    # M13. A proposal is a document. Only an observed execution carries PASS.
    if contract["source"]["runtime_state"] == "PASS":
        errors.append(
            f"{CONTROL_REASONS['M13']}: source runtime_state PASS; a source proposal is not an observed run"
        )
    if contract["source"]["kind"] == "LIVE_SUBSTRATE_OBSERVED":
        errors.append(
            f"{CONTROL_REASONS['M13']}: portable method contract claims a live substrate observation"
        )

    # M01. This plane declares that the five runtime contracts must exist; it
    # never owns their wire shapes.
    declared = [item["contract_id"] for item in contract["required_runtime_contracts"]]
    if declared != FROZEN_RUNTIME_CONTRACT_IDS:
        errors.append("FROZEN_VOCABULARY_DRIFT: required runtime contract IDs drifted")
    for item in contract["required_runtime_contracts"]:
        if item["owner_plane"] != "RUNTIME_CONTRACT_PLANE":
            errors.append(
                f"{CONTROL_REASONS['M01']}: {item['contract_id']} is claimed by "
                f"{item['owner_plane']}; two planes owning one interface guarantees drift"
            )
        # M16 also applies here: a declared implementation with no digest is a claim.
        if item["implementation_state"] == "IMPLEMENTED" and not SHA256.match(item["digest"]):
            errors.append(
                f"{CONTROL_REASONS['M16']}: {item['contract_id']} declared IMPLEMENTED "
                f"with digest {item['digest']!r}"
            )

    # M09. Collapsing two failure distinctions into one terminal state is how a
    # timeout becomes a disconnect and nobody can tell afterwards.
    seen_terminals: dict[str, str] = {}
    for item in contract["failure_distinctions"]:
        previous = seen_terminals.get(item["terminal_state"])
        if previous is not None:
            errors.append(
                f"{CONTROL_REASONS['M09']}: {item['id']} and {previous} share terminal state "
                f"{item['terminal_state']}"
            )
        seen_terminals[item["terminal_state"]] = item["id"]

    # M14. A shared projection is a hint, never the transaction.
    for projection in contract["shared_projections"]:
        if projection["authority"] != "ADVISORY_ONLY":
            errors.append(
                f"{CONTROL_REASONS['M14']}: shared {projection['kind'].lower()} projection "
                f"{projection['id']} claims {projection['authority']}"
            )

    # M11. One canonical writer per kind of state, and admissions stay Human.
    holders: dict[str, list[str]] = {capability: [] for capability in SOLE_HOLDER}
    for entry in contract["authority_map"]:
        role, capabilities = entry["role"], entry["capabilities"]
        for capability in capabilities:
            if capability in SOLE_HOLDER:
                holders[capability].append(role)
                if role != SOLE_HOLDER[capability]:
                    errors.append(
                        f"{CONTROL_REASONS['M11']}: {role} holds {capability}, which belongs to "
                        f"{SOLE_HOLDER[capability]}"
                    )
            if capability.startswith("ADMIT_") and role != "HUMAN_OR_TRUSTED_POLICY":
                errors.append(f"{CONTROL_REASONS['M11']}: {role} holds Human admission {capability}")
        if role == "WORKER" and not set(capabilities) <= WORKER_CAPABILITIES:
            errors.append(
                f"{CONTROL_REASONS['M11']}: WORKER holds "
                f"{sorted(set(capabilities) - WORKER_CAPABILITIES)}; a Worker executes and observes"
            )
    for capability, roles in holders.items():
        if len(roles) != 1:
            errors.append(
                f"{CONTROL_REASONS['M11']}: {capability} has {len(roles)} writer(s); "
                "canonical state has exactly one"
            )

    for packet in contract["packets"]:
        packet_id = packet["id"]
        for lane, entry in packet["lane_states"].items():
            # M03. A lane is closed by its own observation or not at all.
            if entry["evidence_lane"] != lane:
                errors.append(
                    f"{CONTROL_REASONS['M03']}: {packet_id}: {entry['evidence_lane']} evidence "
                    f"cannot close the {lane} lane"
                )
            # M04. Nothing in this plane executed, so nothing here is PASS.
            if entry["state"] == "PASS":
                errors.append(
                    f"{CONTROL_REASONS['M04']}: {packet_id}: {lane} PASS; a portable method packet "
                    "carries an acknowledgement at most, never workflow, task, gate, effect, "
                    "artifact, user or release success"
                )
        # M05. At-least-once delivery makes an unguarded write a double write.
        if packet["side_effect_class"] in WRITE_CLASSES:
            if not packet["idempotency_key_required"] or not packet["effect_ledger_required"]:
                errors.append(
                    f"{CONTROL_REASONS['M05']}: {packet_id}: {packet['side_effect_class']} without "
                    "both an idempotency key and an effect ledger"
                )
            if packet["compensation"] == "NOT_REQUIRED":
                errors.append(
                    f"{CONTROL_REASONS['M05']}: {packet_id}: {packet['side_effect_class']} declares "
                    "no compensation path"
                )
        if packet["side_effect_class"] == "IRREVERSIBLE_WRITE" and not packet["human_admit_required"]:
            errors.append(
                f"{CONTROL_REASONS['M05']}: {packet_id}: irreversible write without Human admission"
            )
        # M06. LOCAL_ONLY means it does not leave the local lane.
        if packet["data_class"] == "LOCAL_ONLY" and (packet["egress_allowed"] or packet["execution_lane"] != "LOCAL"):
            errors.append(
                f"{CONTROL_REASONS['M06']}: {packet_id}: LOCAL_ONLY material with egress "
                f"{packet['egress_allowed']} on the {packet['execution_lane']} lane"
            )
        # M10. A browser fallback observes a rendered surface, not an interface.
        expected_evidence = CAPABILITY_EVIDENCE[packet["capability_class"]]
        if packet["evidence_class"] != expected_evidence:
            errors.append(
                f"{CONTROL_REASONS['M10']}: {packet_id}: {packet['capability_class']} capability "
                f"reporting {packet['evidence_class']}; it can only produce {expected_evidence}"
            )

    errors.extend(scan(contract, SECRET_PATTERNS, CONTROL_REASONS["M07"]))
    errors.extend(scan(contract, PROVIDER_PATTERNS, CONTROL_REASONS["M08"]))
    errors.extend(scan(contract, CONSUMER_STATE_PATTERNS, CONTROL_REASONS["M15"]))
    return errors


def handoff_errors(handoff: dict[str, Any], contract: dict[str, Any], contract_digest: str) -> list[str]:
    errors: list[str] = []

    # M02. An exact subject is a commit, not a name that moves under it.
    for owner, field, pattern, kind in (
        ("producer", "commit", SHA40, "commit"),
        ("producer", "tree", SHA40, "tree"),
        ("consumer", "base_commit", SHA40, "commit"),
        ("consumer", "base_tree", SHA40, "tree"),
        ("producer", "method_contract_digest", SHA256, "digest"),
    ):
        value = handoff[owner][field]
        if not pattern.match(value):
            errors.append(
                f"{CONTROL_REASONS['M02']}: {owner}.{field} {value!r} is not an exact {kind}"
            )
    if not SHA40.match(handoff["rollback"]["subject_commit"]):
        errors.append(
            f"{CONTROL_REASONS['M02']}: rollback.subject_commit "
            f"{handoff['rollback']['subject_commit']!r} is not an exact commit"
        )

    if handoff["producer"]["method_contract_id"] != contract["method"]["method_id"]:
        errors.append("METHOD_CONTRACT_BINDING_DRIFT: handoff names a different method contract")
    if handoff["producer"]["method_contract_digest"] != contract_digest:
        errors.append(
            f"METHOD_CONTRACT_DIGEST_DRIFT: handoff binds {handoff['producer']['method_contract_digest']} "
            f"but the frozen method contract hashes to {contract_digest}"
        )

    declared = [item["contract_id"] for item in handoff["required_runtime_contracts"]]
    if declared != FROZEN_RUNTIME_CONTRACT_IDS:
        errors.append("FROZEN_VOCABULARY_DRIFT: handoff runtime contract IDs drifted")
    unresolved = 0
    for item in handoff["required_runtime_contracts"]:
        if item["owner_plane"] != "RUNTIME_CONTRACT_PLANE":
            errors.append(
                f"{CONTROL_REASONS['M01']}: {item['contract_id']} is claimed by {item['owner_plane']}"
            )
        resolved = SHA256.match(item["digest"]) is not None
        if not resolved:
            unresolved += 1
            if item["digest"] != "UNRESOLVED":
                errors.append(
                    f"{CONTROL_REASONS['M02']}: {item['contract_id']} digest {item['digest']!r} is "
                    "neither an exact digest nor the explicit UNRESOLVED state"
                )
        # M16. Declaring an implementation without its digest is a claim, not a fact.
        if item["implementation_state"] == "IMPLEMENTED" and not resolved:
            errors.append(
                f"{CONTROL_REASONS['M16']}: {item['contract_id']} declared IMPLEMENTED with digest "
                f"{item['digest']!r}"
            )
    if unresolved and handoff["verdict"] == "PASS":
        errors.append(
            f"UNRESOLVED_RUNTIME_CONTRACT_PROMOTED_TO_PASS: {unresolved} runtime contract(s) "
            "unresolved; the handoff is BLOCKED_BY_RUNTIME_CONTRACT, not PASS"
        )

    # M12. Start-readiness is not completion-readiness, and never becomes it.
    for dependency in handoff["start_dependencies"]:
        if dependency["edge_class"] != "START":
            errors.append(f"EDGE_CLASS_DRIFT: start dependency {dependency['id']} is not a START edge")
    for dependency in handoff["completion_dependencies"]:
        if dependency["edge_class"] != "COMPLETION":
            errors.append(
                f"EDGE_CLASS_DRIFT: completion dependency {dependency['id']} is not a COMPLETION edge"
            )
        if dependency["proof"]["kind"] == "START_READINESS":
            errors.append(
                f"{CONTROL_REASONS['M12']}: completion dependency {dependency['id']} is closed by "
                "start readiness"
            )

    lease = handoff["path_lease"]
    for other in ("read_only", "forbidden"):
        overlap = sorted(set(lease["allowed"]) & set(lease[other]))
        if overlap:
            errors.append(f"PATH_LEASE_CONTRADICTION: {overlap} is both allowed and {other}")

    subjects = {gate["subject"] for gate in handoff["required_gates"]}
    for required in ("LOCAL_WORKTREE", "EXACT_HEAD"):
        if required not in subjects:
            errors.append(f"MISSING_GATE_SUBJECT: no required gate binds the {required} subject")

    for remaining in handoff["remaining_states"]:
        if remaining["state"] == "PASS":
            errors.append(
                f"REMAINING_STATE_PROMOTED_TO_PASS: {remaining['lane']} is listed as remaining and PASS"
            )
    covered = {item["lane"] for item in handoff["remaining_states"]}
    missing = [lane for lane in ("CLOUD", "TRANSPORT", "TASK", "EFFECT", "ARTIFACT", "USER_OUTCOME", "RELEASE") if lane not in covered]
    if missing:
        errors.append(f"UNDECLARED_REMAINING_LANE: {missing} are neither claimed nor declared remaining")

    expected_fixtures = [packet["id"] for packet in contract["packets"]] + [handoff["id"]]
    if handoff["positive_fixtures"] != expected_fixtures:
        errors.append(
            f"FIXTURE_REGISTRY_DRIFT: positive_fixtures {handoff['positive_fixtures']} does not equal "
            f"{expected_fixtures}"
        )
    if handoff["mutation_controls"] != sorted(CONTROL_REASONS):
        errors.append("CONTROL_REGISTRY_DRIFT: mutation_controls does not equal the executable control set")

    errors.extend(scan(handoff, SECRET_PATTERNS, CONTROL_REASONS["M07"]))
    errors.extend(scan(handoff, PROVIDER_PATTERNS, CONTROL_REASONS["M08"]))
    return errors


def wire_authority_errors() -> list[str]:
    """M01, enforced on the directory rather than only on the declaration.

    A later commit that adds `offload-job.v1.schema.json` here would create a
    second interface authority while every document-level check stayed green.
    """
    errors: list[str] = []
    for path in sorted(REFERENCES.glob("*.json")):
        document = load(path)
        for pointer, text in walk_strings(document):
            key = pointer.rsplit("/", 1)[-1]
            if key not in {"$id", "schema_version"}:
                continue
            for name in WIRE_SCHEMA_NAMES:
                if name in text:
                    errors.append(
                        f"{CONTROL_REASONS['M01']}: {path.name} declares {key} {text!r}; the "
                        f"{name} wire schema belongs to the Runtime Contract Plane"
                    )
    return errors


def method_document_errors(text: str) -> list[str]:
    """The method document is the only route a reader has to these controls.

    Schemas say what a document must contain; they never say why, and nobody
    navigates a JSON Schema to find out which of ten laws actually turns red.
    `OFFLOAD_METHOD.md` is where a reader arrives, so a control renamed or added
    in a later leaf with the prose left alone leaves that reader working from a
    list that is silently short -- and a short index and a complete one look
    identical from the inside. Route completeness is therefore asserted rather
    than assumed: every executable control, its refused promotion, every frozen
    runtime contract ID and every frozen state must be named where the reader is.

    This is a route check, not a semantic one. It proves the words are reachable,
    never that the paragraph around them is right.
    """
    errors: list[str] = []
    for label, required in (
        ("control", sorted(CONTROL_REASONS)),
        ("refused promotion", sorted(CONTROL_REASONS.values())),
        ("runtime contract", FROZEN_RUNTIME_CONTRACT_IDS),
        ("frozen state", FROZEN_STATE_CHAIN),
        ("failure distinction", FROZEN_FAILURE_DISTINCTIONS),
    ):
        missing = [item for item in required if item not in text]
        if missing:
            errors.append(
                f"METHOD_DOCUMENT_ROUTE_INCOMPLETE: {METHOD_DOCUMENT.name} never names "
                f"{label} {missing}; a reader arriving here would not learn it exists"
            )
    return errors


def case_registry_errors(contract: dict[str, Any]) -> list[str]:
    """The registered contract cases must be the ones that actually execute."""
    cases = load(CASES)
    registered = {
        case["id"]: {key: value for key, value in case.items() if key != "id"}
        for case in cases["cases"]
        if isinstance(case.get("id"), str) and case["id"].startswith("DA-")
    }
    expected: dict[str, dict[str, str]] = {
        f"DA-{packet['id']}": {"expected": "PASS"} for packet in contract["packets"]
    }
    expected["DA-P4"] = {"expected": "PASS"}
    for control, reason in CONTROL_REASONS.items():
        expected[f"DA-{control}"] = {"expected_failure": reason}
    if registered != expected:
        missing = sorted(set(expected) - set(registered))
        extra = sorted(set(registered) - set(expected))
        drifted = sorted(
            case_id for case_id in set(expected) & set(registered) if registered[case_id] != expected[case_id]
        )
        return [
            f"CASE_REGISTRY_DRIFT: cases.json missing={missing} unexpected={extra} drifted={drifted}"
        ]
    return []


def control_cases(
    contract: dict[str, Any], handoff: dict[str, Any]
) -> list[tuple[str, str, dict[str, Any], Callable[[dict[str, Any]], Any]]]:
    """Every mutation keeps its document schema-valid, so only a law can kill it."""
    return [
        ("M01", "method", contract,
         lambda d: d["required_runtime_contracts"][0].__setitem__("owner_plane", "INSTRUCTION_METHOD_PLANE")),
        ("M02", "handoff", handoff,
         lambda d: d["producer"].__setitem__("commit", "main")),
        ("M03", "method", contract,
         lambda d: d["packets"][0]["lane_states"]["TASK"].__setitem__("evidence_lane", "TRANSPORT")),
        ("M04", "method", contract,
         lambda d: d["packets"][0]["lane_states"]["TASK"].__setitem__("state", "PASS")),
        ("M05", "method", contract,
         lambda d: d["packets"][2].__setitem__("effect_ledger_required", False)),
        ("M06", "method", contract,
         lambda d: d["packets"][1].__setitem__("egress_allowed", True)),
        ("M07", "method", contract,
         lambda d: d["packets"][1].__setitem__(
             "purpose", "resume the local worker with Cookie: session=8f2c1a9b4d7e")),
        ("M08", "method", contract,
         lambda d: d["packets"][0].__setitem__(
             "purpose", "monitoring requires the OpenAI adapter, so the architecture assumes it")),
        ("M09", "method", contract,
         lambda d: d["failure_distinctions"][2].__setitem__(
             "terminal_state", d["failure_distinctions"][0]["terminal_state"])),
        ("M10", "method", contract,
         lambda d: d["packets"][0].__setitem__("capability_class", "BROWSER_FALLBACK")),
        ("M11", "method", contract,
         lambda d: d["authority_map"][1]["capabilities"].append("COMMIT_TASK_STATE")),
        ("M12", "handoff", handoff,
         lambda d: d["completion_dependencies"][1]["proof"].__setitem__("kind", "START_READINESS")),
        ("M13", "method", contract,
         lambda d: d["source"].__setitem__("runtime_state", "PASS")),
        ("M14", "method", contract,
         lambda d: d["shared_projections"][2].__setitem__("authority", "TRANSACTION_AUTHORITY")),
        ("M15", "method", contract,
         lambda d: d["packets"][2].__setitem__(
             "purpose",
             "write on behalf of consumer issue #362 at "
             "8f5548c5b94a31e074b3aa6cbce776f754c24f61")),
        ("M16", "handoff", handoff,
         lambda d: d["required_runtime_contracts"][3].__setitem__("implementation_state", "IMPLEMENTED")),
    ]


def main() -> int:
    try:
        method_schema = load(METHOD_SCHEMA)
        handoff_schema = load(HANDOFF_SCHEMA)
        contract = load(METHOD_EXAMPLE)
        handoff = load(HANDOFF_EXAMPLE)
        method_document = read_text(METHOD_DOCUMENT)
        contract_digest = hashlib.sha256(METHOD_EXAMPLE.read_bytes()).hexdigest()
        Draft202012Validator.check_schema(method_schema)
        Draft202012Validator.check_schema(handoff_schema)
    except (Unusable, SchemaError) as error:
        # Unreadable input and a malformed schema are not contract verdicts.
        print(f"FATAL dual-agent-offload: {error}", file=sys.stderr)
        return 64

    schemas = {"method": method_schema, "handoff": handoff_schema}
    failures: list[str] = []

    failures.extend(shape_errors(method_schema, contract, "example-method-contract.json"))
    failures.extend(shape_errors(handoff_schema, handoff, "example-handoff-requirements.json"))
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 2

    failures.extend(method_errors(contract))
    failures.extend(handoff_errors(handoff, contract, contract_digest))
    failures.extend(wire_authority_errors())
    failures.extend(method_document_errors(method_document))
    failures.extend(case_registry_errors(contract))
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 2

    for packet in contract["packets"]:
        print(f"POSITIVE {packet['id']}: {packet['purpose']}")
    print(f"POSITIVE {handoff['id']}: cross-plane handoff, verdict {handoff['verdict']}")

    killed = 0
    for control, target, document, mutate in control_cases(contract, handoff):
        reason = CONTROL_REASONS[control]
        candidate = copy.deepcopy(document)
        mutate(candidate)
        residual_shape = shape_errors(schemas[target], candidate, f"{control} mutant")
        if residual_shape:
            failures.append(
                f"{control} is not a semantic control: the mutant is schema-invalid "
                f"({residual_shape[0]}), so a parser failure would stand in for the law"
            )
            continue
        if target == "method":
            observed = method_errors(candidate)
        else:
            observed = handoff_errors(candidate, contract, contract_digest)
        if not any(error.startswith(f"{reason}:") for error in observed):
            failures.append(
                f"{control} did not turn red for {reason}; observed {observed or 'no error at all'}"
            )
            continue
        killed += 1

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 2

    print(
        f"DUAL-AGENT-OFFLOAD GREEN: method contract and handoff packet frozen; "
        f"{len(contract['packets']) + 1} positive fixtures pass, {killed}/{len(CONTROL_REASONS)} "
        "semantic controls killed; every runtime wire schema, transport, provider, effect, "
        "user outcome and release lane remains NOT_IMPLEMENTED or NOT_EXERCISED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
