#!/usr/bin/env python3
"""Validate one PREL artifact against its schema and the controlled closure laws.

Zero network, standard library plus the pinned Draft 2020-12 validator. The
checker never executes a model, never reaches a product surface, and never
promotes an evidence lane: it decides only whether the bytes in front of it
obey the contracts in `../references/`.

Two layers run, and both always run. The schema layer decides shape. The
semantic layer decides whether the artifact laundered evidence, and it is
written defensively so it still reports its own named refusal code on an
artifact the schema layer has already rejected -- a mutation that flips
`authority.merge` to true must be reported as
`PROMPT_GRANTS_RESERVED_AUTHORITY`, not merely as a schema `const` failure,
because the refusal code is what a Worker is told to look for.

Exits: 0 green, 2 a contract or control is red, 64 the checker could not run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REFERENCES = Path(__file__).resolve().parents[1] / "references"

SCHEMA_FILES = {
    "prel/product-signal/v1": "product-signal.schema.json",
    "prel/reverse-engineering-dossier/v1": "reverse-engineering-dossier.schema.json",
    "prel/problem-closure-matrix/v1": "problem-closure-matrix.schema.json",
    "prel/prompt-packet/v1": "prompt-packet.schema.json",
    "prel/reverse-engineering-handoff/v1": "reverse-engineering-handoff.schema.json",
}

PROMPT_SURFACES = (
    "STAGE_1_CONTROL_BINDER",
    "STAGE_2_SOURCE_INTAKE",
    "STAGE_3_EVIDENCE_COMPILER",
    "STAGE_4_YC_PRODUCT_REVERSE_ENGINEER",
    "STAGE_5_TECHNICAL_SYSTEMS_ARCHITECT",
    "STAGE_6_SHADOW_MONITOR",
    "STAGE_7_TECH_LEAD_PLANNER",
    "STAGE_8_MOLECULAR_WORKER",
    "STAGE_9_CONVERGENCE_OWNER",
)
ENVELOPE_ID = "COMMON_SYSTEM_ENVELOPE"

# Kinds that assert somebody watched the product do something. Everything else
# is a claim about the product, and the difference is the whole point of the
# intake stage.
OBSERVED_KINDS = {"OBSERVED_ARTIFACT", "PAID_CONVERSION"}
CLAIM_KINDS = {"SOURCE_STATEMENT", "MARKET_ATTENTION", "INFERENCE"}
TECHNICAL_LANES = {"DETERMINISTIC", "BEHAVIORAL"}
DEMAND_SLOTS = {"JOB", "PAIN"}

PLACEHOLDERS = {"", "-", "?", "n/a", "na", "tbd", "todo", "none", "unknown", "xxx"}

PRIVATE_REASONING = re.compile(
    r"chain[- ]of[- ]thought|private reasoning|inner monologue|hidden reasoning"
    r"|reasoning trace|think privately",
    re.IGNORECASE,
)
CONSUMER_TOPOLOGY = re.compile(
    r"/Users/|/home/|refs/heads/|origin/|github\.com|gitlab\.com|\.git\b|#\d+",
)
PRIOR_CHAT = re.compile(
    r"prior chat|previous chat|conversation|as discussed|earlier message|transcript",
    re.IGNORECASE,
)


class Unusable(Exception):
    """The checker could not read its input. Not the same as a refusal."""


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Unusable(f"unreadable artifact {path}: {error}") from error


def digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise Unusable(f"unreadable input {path}: {error}") from error


def schema_errors(artifact: Any, schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as error:  # pragma: no cover - environment guard
        raise Unusable("jsonschema Draft 2020-12 validator unavailable") from error
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, Exception) as error:  # noqa: BLE001
        raise Unusable(f"invalid or unreadable schema {schema_path}: {error}") from error
    found = sorted(
        Draft202012Validator(schema).iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )
    return [
        "SCHEMA_SHAPE "
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in found[:20]
    ]


def walk_strings(value: Any, path: str = "") -> list[tuple[str, str]]:
    """Every string leaf with the dotted path it was found at."""
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, dict):
        found: list[tuple[str, str]] = []
        for key, child in value.items():
            found.extend(walk_strings(child, f"{path}.{key}" if path else str(key)))
        return found
    if isinstance(value, list):
        found = []
        for index, child in enumerate(value):
            found.extend(walk_strings(child, f"{path}[{index}]"))
        return found
    return []


def hollow(value: Any) -> bool:
    return isinstance(value, str) and value.strip().casefold() in PLACEHOLDERS


def check_hollow(artifact: Any) -> list[str]:
    return [
        f"HOLLOW_EVIDENCE {path or '<root>'} is a placeholder, not evidence: {text!r}"
        for path, text in walk_strings(artifact)
        if hollow(text)
    ]


def signal_properties() -> set[str]:
    schema = load(REFERENCES / "product-signal.schema.json")
    return set(schema["$defs"]["signal"]["properties"])


def check_product_signal(artifact: dict) -> list[str]:
    problems: list[str] = []
    declared = signal_properties()
    compatibility = artifact.get("compatibility") or {}
    for field in compatibility.get("consumed_fields") or []:
        if field not in declared:
            problems.append(
                f"COMPATIBILITY_FIELD_UNKNOWN consumed_fields names {field!r}, which "
                f"this contract does not define; the producer binding has drifted"
            )

    signals = artifact.get("signals") or []
    known = {row.get("id") for row in signals if isinstance(row, dict)}
    for row in signals:
        if not isinstance(row, dict):
            continue
        identifier = row.get("id", "<unnamed>")
        kind, slot = row.get("kind"), row.get("slot")
        if kind in CLAIM_KINDS and row.get("observation") is not None:
            problems.append(
                f"SOURCE_STATEMENT_AS_OBSERVED_ARCHITECTURE {identifier}: kind {kind} "
                f"carries an observation block; a statement about the product is not "
                f"an observation of it"
            )
        if kind in OBSERVED_KINDS and row.get("observation") is None:
            problems.append(
                f"HOLLOW_EVIDENCE {identifier}: kind {kind} claims observation and "
                f"carries none"
            )
        if kind == "MARKET_ATTENTION" and slot in DEMAND_SLOTS:
            problems.append(
                f"MARKET_ATTENTION_AS_DEMAND {identifier}: attention was filed under "
                f"slot {slot}; attention is not a job and not a pain"
            )
        if slot == "MECHANISM" and kind in OBSERVED_KINDS and row.get("oracle") is None:
            problems.append(
                f"MECHANISM_WITHOUT_OBSERVABLE_ORACLE {identifier}: an observed "
                f"mechanism with no oracle cannot be refuted by anything"
            )
        for dependency in row.get("depends_on") or []:
            if dependency not in known:
                problems.append(
                    f"SIGNAL_DEPENDENCY_UNBOUND {identifier}: depends_on names "
                    f"{dependency}, which is not in this signal set"
                )
    return problems


def check_ceiling(ceiling: Any, where: str) -> list[str]:
    problems: list[str] = []
    if not isinstance(ceiling, dict):
        return problems
    for field in ("product_market_fit", "live_provider_execution", "production_readiness"):
        if ceiling.get(field) == "PASS":
            problems.append(
                f"CEILING_OVERCLAIM {where}.{field} is PASS; this lane is not "
                f"produced by any deterministic artifact"
            )
    return problems


def check_dossier(artifact: dict) -> list[str]:
    problems: list[str] = []
    job = artifact.get("job") or {}
    pain = artifact.get("pain") or {}
    workflow = artifact.get("workflow") or []
    mechanisms = artifact.get("mechanism_hypotheses") or []

    if (workflow or mechanisms) and (
        job.get("grade") == "ABSENT" or pain.get("grade") == "ABSENT"
    ):
        problems.append(
            "FEATURE_CLONE_WITHOUT_JOB_HYPOTHESIS the dossier carries workflow or "
            "mechanism content while job or pain is ABSENT; that is a feature list, "
            "not a product hypothesis"
        )

    for slot_name in ("job", "pain", "magic_moment"):
        slot = artifact.get(slot_name) or {}
        grade, ids = slot.get("grade"), slot.get("signal_ids") or []
        if grade not in (None, "ABSENT") and not ids:
            problems.append(
                f"UNGRADED_SLOT {slot_name} is graded {grade} and cites no signal"
            )
        if grade == "ABSENT" and (slot.get("statement") or "").strip():
            problems.append(
                f"UNGRADED_SLOT {slot_name} is ABSENT and still carries a statement"
            )

    for row in mechanisms:
        if not isinstance(row, dict):
            continue
        identifier = row.get("id", "<unnamed>")
        classification = row.get("classification")
        if classification == "OBSERVABLE_MECHANISM" and not row.get("oracle_id"):
            problems.append(
                f"MECHANISM_WITHOUT_OBSERVABLE_ORACLE {identifier} is classified "
                f"OBSERVABLE_MECHANISM with no oracle"
            )
        if classification == "VENDOR_CLAIMED_MECHANISM" and row.get("grade") != "CLAIMED":
            problems.append(
                f"SOURCE_STATEMENT_AS_OBSERVED_ARCHITECTURE {identifier} is a vendor "
                f"claim graded {row.get('grade')!r}"
            )

    graph = artifact.get("capability_graph") or {}
    nodes = {row.get("id") for row in graph.get("nodes") or [] if isinstance(row, dict)}
    for edge in graph.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        for end in ("from", "to"):
            if edge.get(end) not in nodes:
                problems.append(
                    f"CAPABILITY_EDGE_UNBOUND edge {end}={edge.get(end)!r} names no "
                    f"declared capability node"
                )

    for right in artifact.get("rights") or []:
        if isinstance(right, dict) and right.get("state") == "PASS":
            problems.append(
                f"CEILING_OVERCLAIM rights {right.get('id')} is PASS; a usage right "
                f"is admitted by a Human, never by a compiler"
            )

    problems.extend(check_ceiling(artifact.get("evidence_ceiling"), "evidence_ceiling"))
    return problems


def check_closure_matrix(artifact: dict) -> list[str]:
    problems: list[str] = []
    for row in artifact.get("rows") or []:
        if not isinstance(row, dict):
            continue
        identifier = row.get("id", "<unnamed>")
        lane, oracle_lane = row.get("lane"), row.get("oracle_lane")
        oracle_id, state = row.get("oracle_id"), row.get("closure_state")

        if lane in {"USER", "PAID"} and oracle_lane in TECHNICAL_LANES:
            if state == "CLOSED_BY_ORACLE" or row.get("evidence_state") == "PASS":
                problems.append(
                    f"TECHNICAL_PASS_AS_USER_VALIDATION {identifier}: a "
                    f"{oracle_lane} oracle was used to close a {lane} requirement"
                )
        if oracle_id is None and state in {"CLOSED_BY_ORACLE", "OPEN_WITH_ORACLE"}:
            problems.append(
                f"CLOSURE_STATE_UNSUPPORTED {identifier} claims {state} with no oracle"
            )
        if oracle_id is not None and oracle_lane is None:
            problems.append(
                f"CLOSURE_STATE_UNSUPPORTED {identifier} names an oracle with no lane"
            )
        if (
            oracle_lane is not None
            and lane != oracle_lane
            and state != "BLOCKED_LANE_MISMATCH"
        ):
            problems.append(
                f"CLOSURE_STATE_UNSUPPORTED {identifier}: lane {lane} closed by a "
                f"{oracle_lane} oracle without BLOCKED_LANE_MISMATCH"
            )
        if state == "BLOCKED_NO_ORACLE" and row.get("evidence_state") == "PASS":
            problems.append(
                f"CLOSURE_STATE_UNSUPPORTED {identifier} is blocked and PASS at once"
            )
    problems.extend(check_ceiling(artifact.get("evidence_ceiling"), "evidence_ceiling"))
    return problems


def check_handoff(artifact: dict) -> list[str]:
    problems: list[str] = []
    packets = [row for row in artifact.get("packets") or [] if isinstance(row, dict)]
    leases = {row.get("id"): list(row.get("paths_lease") or []) for row in packets}

    for path, text in walk_strings(artifact):
        if PRIOR_CHAT.search(text):
            problems.append(
                f"PRIOR_CHAT_PROSE_AS_HANDOFF {path} points at conversation prose "
                f"instead of a digest-bound artifact: {text!r}"
            )

    identifiers = sorted(leases)
    for index, left in enumerate(identifiers):
        for right in identifiers[index + 1:]:
            for one in leases[left]:
                for other in leases[right]:
                    if one.startswith(other) or other.startswith(one):
                        problems.append(
                            f"HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE {left} and "
                            f"{right} both hold {one!r}/{other!r}"
                        )

    for packet in packets:
        identifier = packet.get("id", "<unnamed>")
        edges = packet.get("depends_on") or []
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            parent = edge.get("packet_id")
            if parent not in leases:
                problems.append(
                    f"HANDOFF_EDGE_UNBOUND {identifier} depends on {parent}, which is "
                    f"not a packet here"
                )
                continue
            for consumed in edge.get("consumes") or []:
                if not any(consumed.startswith(lease) for lease in leases[parent]):
                    problems.append(
                        f"FALSE_SERIALIZATION_OF_INDEPENDENT_LEAVES {identifier} "
                        f"depends on {parent} but consumes {consumed!r}, which "
                        f"{parent} does not produce"
                    )
        owner = packet.get("convergence_owner")
        if len(edges) > 1 and not owner:
            problems.append(
                f"HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE {identifier} has "
                f"{len(edges)} incoming contracts and no convergence owner"
            )
        if len(edges) <= 1 and owner:
            problems.append(
                f"HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE {identifier} declares a "
                f"convergence owner without being a convergence"
            )

    order: dict[str, int] = {}

    def visit(identifier: str, seen: tuple[str, ...]) -> None:
        if identifier in order:
            return
        if identifier in seen:
            problems.append(
                f"HANDOFF_CYCLE {' -> '.join(seen + (identifier,))}"
            )
            order[identifier] = 0
            return
        packet = next((row for row in packets if row.get("id") == identifier), None)
        for edge in (packet or {}).get("depends_on") or []:
            if isinstance(edge, dict) and edge.get("packet_id") in leases:
                visit(edge["packet_id"], seen + (identifier,))
        order[identifier] = len(order)

    for identifier in identifiers:
        visit(identifier, ())

    for item in artifact.get("remaining") or []:
        if isinstance(item, dict) and item.get("state") == "PASS":
            problems.append(
                f"CEILING_OVERCLAIM remaining item {item.get('closure_row_id')} is "
                f"PASS; a remaining item is by definition not closed"
            )
    return problems


def check_prompt_packet(artifact: dict) -> list[str]:
    problems: list[str] = []
    envelope = artifact.get("envelope") or {}
    surfaces = [row for row in artifact.get("surfaces") or [] if isinstance(row, dict)]

    observed = tuple(row.get("id") for row in surfaces)
    if observed != PROMPT_SURFACES:
        problems.append(
            "PROMPT_SURFACE_SET_DRIFT surfaces must be exactly "
            f"{list(PROMPT_SURFACES)} in order; found {list(observed)}"
        )

    for holder, label in [(envelope, ENVELOPE_ID)] + [
        (row, row.get("id", "<unnamed>")) for row in surfaces
    ]:
        authority = holder.get("authority") or {}
        granted = sorted(key for key, value in authority.items() if value)
        if granted:
            problems.append(
                f"PROMPT_GRANTS_RESERVED_AUTHORITY {label} grants {granted}; these "
                f"operations are Human-owned and a prompt cannot hand them out"
            )
        if holder.get("requests_private_reasoning") is not False:
            problems.append(
                f"PROMPT_REQUESTS_PRIVATE_REASONING {label} does not declare "
                f"requests_private_reasoning=false"
            )
        if not (holder.get("human_owned_operations") or []):
            problems.append(
                f"PROMPT_GRANTS_RESERVED_AUTHORITY {label} names no Human-owned "
                f"operation, so nothing is reserved"
            )

    for path, text in walk_strings(artifact):
        if PRIVATE_REASONING.search(text):
            problems.append(
                f"PROMPT_REQUESTS_PRIVATE_REASONING {path} asks for hidden reasoning: "
                f"{text!r}"
            )
        if ".consumer_binding." in f".{path}.":
            continue
        if CONSUMER_TOPOLOGY.search(text):
            problems.append(
                f"CONSUMER_TOPOLOGY_IN_PORTABLE_CORE {path} carries a consumer "
                f"branch, issue, remote or machine path outside consumer_binding: "
                f"{text!r}"
            )

    declared = set(observed) | {ENVELOPE_ID}
    for row in surfaces:
        identifier = row.get("id", "<unnamed>")
        for field in ("start_dependencies", "completion_dependencies"):
            for dependency in row.get(field) or []:
                if dependency not in declared:
                    problems.append(
                        f"PROMPT_DEPENDENCY_UNBOUND {identifier}.{field} names "
                        f"{dependency!r}, which is not a surface in this packet"
                    )

    leases = {row.get("id"): list(row.get("lease") or []) for row in surfaces}
    identifiers = sorted(leases)
    for index, left in enumerate(identifiers):
        for right in identifiers[index + 1:]:
            overlap = sorted(set(leases[left]) & set(leases[right]))
            if overlap:
                problems.append(
                    f"HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE {left} and {right} "
                    f"share the writer lease {overlap}"
                )
    return problems


SEMANTIC = {
    "prel/product-signal/v1": check_product_signal,
    "prel/reverse-engineering-dossier/v1": check_dossier,
    "prel/problem-closure-matrix/v1": check_closure_matrix,
    "prel/reverse-engineering-handoff/v1": check_handoff,
    "prel/prompt-packet/v1": check_prompt_packet,
}


def check_stale_subject(artifact: dict, source: Path) -> list[str]:
    declared = (artifact.get("derived_from") or {}).get("digest")
    actual = digest(source)
    if declared != actual:
        return [
            f"STALE_SUBJECT derived_from.digest is {declared!r} while {source.name} "
            f"currently hashes to {actual!r}; the artifact describes a subject that "
            f"has moved"
        ]
    return []


def walk_subjects(value: Any, path: str = "") -> list[tuple[str, dict]]:
    """Every `exact_subject` / `derived_from` binding, wherever it is nested."""
    found: list[tuple[str, dict]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}.{key}" if path else str(key)
            if key in {"exact_subject", "derived_from"} and isinstance(child, dict):
                found.append((here, child))
            else:
                found.extend(walk_subjects(child, here))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(walk_subjects(child, f"{path}[{index}]"))
    return found


def check_resolved_subjects(artifact: Any, root: Path) -> list[str]:
    """Every named subject must still exist and still hash to what was recorded.

    Without this, a digest is only a promise the artifact makes about a file
    nobody re-reads: the file moves, the packet keeps pointing at a subject that
    no longer exists, and every downstream state stays green describing bytes
    that are gone.
    """
    problems: list[str] = []
    for where, binding in walk_subjects(artifact):
        name = binding.get("artifact")
        if not isinstance(name, str) or not name:
            continue
        target = root / name
        if not target.is_file():
            problems.append(
                f"STALE_SUBJECT {where} names {name!r}, which is not in {root}"
            )
            continue
        actual = digest(target)
        if binding.get("digest") != actual:
            problems.append(
                f"STALE_SUBJECT {where} records {binding.get('digest')!r} for "
                f"{name!r}, which currently hashes to {actual!r}"
            )
    return problems


def check_catalogue(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise Unusable(f"unreadable catalogue {path}: {error}") from error
    return [
        f"PROMPT_SURFACE_SET_DRIFT catalogue {path.name} does not name {name}"
        for name in (ENVELOPE_ID,) + PROMPT_SURFACES
        if name not in text
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument(
        "--input",
        type=Path,
        help="the upstream artifact this one was compiled from; enables the "
        "stale-subject control",
    )
    parser.add_argument("--catalogue", type=Path)
    parser.add_argument(
        "--resolve-subjects",
        type=Path,
        help="directory the artifact's exact_subject/derived_from names resolve "
        "against; enables the stale-subject control on every binding",
    )
    args = parser.parse_args()

    if args.artifact is None and args.catalogue is None:
        print("PREL-RED usage: --artifact and/or --catalogue is required", file=sys.stderr)
        return 64

    try:
        problems: list[str] = []
        subject = "catalogue"
        if args.catalogue is not None:
            problems.extend(check_catalogue(args.catalogue))
        if args.artifact is not None:
            artifact = load(args.artifact)
            if not isinstance(artifact, dict):
                raise Unusable("artifact root must be an object")
            schema_name = artifact.get("schema")
            if schema_name not in SCHEMA_FILES:
                raise Unusable(
                    f"unknown artifact schema {schema_name!r}; known: "
                    f"{sorted(SCHEMA_FILES)}"
                )
            subject = schema_name
            problems.extend(schema_errors(artifact, REFERENCES / SCHEMA_FILES[schema_name]))
            problems.extend(check_hollow(artifact))
            problems.extend(SEMANTIC[schema_name](artifact))
            if args.input is not None:
                problems.extend(check_stale_subject(artifact, args.input))
            if args.resolve_subjects is not None:
                problems.extend(check_resolved_subjects(artifact, args.resolve_subjects))
    except Unusable as error:
        print(f"PREL-UNUSABLE {error}", file=sys.stderr)
        return 64

    if problems:
        for problem in problems:
            print(f"PREL-RED {problem}", file=sys.stderr)
        return 2
    print(f"PREL-GREEN {subject}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
