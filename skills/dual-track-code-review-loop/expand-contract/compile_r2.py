#!/usr/bin/env python3
"""Compile one cross-repository Expand & Contract refactor (R2) run.

    C1 CONTRACT_EXPANSION
       CONTRACT_BASELINE_BOUND
       CONTRACT_EXPANDED
       GENERATED_ARTIFACTS_PINNED
    A1 PROVIDER_EXPANSION
       PROVIDER_SURFACE_COEXISTING
    A2 CONSUMER_INVERSION
       CONSUMER_PORT_INVERTED
       CONSUMER_TRAFFIC_MIGRATED
    E1 DUAL_RUN_AND_TELEMETRY
       DUAL_RUN_OBSERVED
       TELEMETRY_WINDOW_OBSERVED
    C2 LEGACY_CONTRACTION
       DOWNSTREAM_INVENTORY_TAKEN
       LEGACY_CONTRACTION_PROPOSED
    -> CONTRACTION_CANDIDATE | BLOCKED | ROLLED_BACK

The input is one `dtcr/refactor-r2-request/v1` document describing a run across
several repositories. The output is the artifacts that run emits -- one contract
expansion, one consumer migration receipt *per consumer*, and one R2 receipt --
serialised canonically (`sort_keys`, two-space indent, one trailing newline), so
`--check` byte-compares a committed projection instead of trusting that somebody
regenerated it.

Why a per-consumer artifact rather than a list inside the receipt: the whole
safety property of Expand & Contract is that the provider may contract only
after *every* consumer receipt is bound. A consumer that migrated is a fact
about a different repository, at a different commit, with its own rollback
subject, and flattening those into rows of one document loses exactly the
binding the contraction gate reads.

What this compiler will not do, and why each is a refusal rather than a warning:

* It does not apply anything and it opens no socket. No repository is read,
  written or parsed here, no registry is contacted, and
  `establishes.applied_on_real_codebase` is pinned false on every receipt it
  emits. The real bounded consumer canary is a separate, unexercised lane and
  belongs to the issue that owns a real consumer repository.
* It vendors no contract adapter. The adapter law declares capability classes
  per contract format -- wire compatibility, schema compatibility, code
  generation, registry publication -- and pins version, license, rule set and
  codegen determinism. Naming Buf, openapi-generator or AsyncAPI's toolchain
  here would make this file claim a capability it does not have, so an adapter
  is a declaration with `vendored` pinned false, and a run whose adapter has no
  implementation available terminates BLOCKED on
  CONTRACT_ADAPTER_BLOCKED_ON_PROVIDER rather than reporting a green it never
  earned.
* It does not contract and it does not merge. Removing the legacy surface is
  proposed, never executed: `contraction.legacy_surface_removed` is pinned
  false and `contraction.authorization` is single-valued, so a request that
  carries the decision it exists to ask a person for is refused by name.
* It fabricates no Git ancestry between repositories. A provider commit is not
  a parent of a consumer commit however tightly the deployment couples them;
  cross-repository order is a process edge and lives in the receipt as one.

Three terminals and no fourth. BLOCKED names which link of the chain was never
reached; ROLLED_BACK is the honest exit when a consumer or the observation
window disagreed after traffic moved; CONTRACTION_CANDIDATE requires every
consumer receipt to be bound and every observation lane to have run and agreed,
and is still only a candidate -- contraction, publication and merge are
repository and Human authority.

Exits: 0 green, 2 refused with a named code or a --check projection is stale,
64 the compiler could not read the request at all.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

EXACT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
EXACT_DIGEST = re.compile(r"^[0-9a-f]{64}$")
BINDING_ID = re.compile(r"^DTCR-RB-[0-9a-f]{16}$")
REPO_RELATIVE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*$")

# The adapter law as declared capability classes, one table per contract format.
# No implementation is vendored: this says which class of tooling a format has an
# adapter *shape* for, and a format absent from it cannot be reported as
# supported. Protobuf is listed first because the PDF's flow is a Protobuf one,
# and it is deliberately not the only entry -- a protocol that only works when
# the contract happens to be Protobuf is a Buf procedure with a general name.
DECLARED_CONTRACT_ADAPTERS = {
    "protobuf": (
        "WIRE_COMPATIBILITY_CHECK",
        "SCHEMA_COMPATIBILITY_CHECK",
        "CODE_GENERATION",
        "REGISTRY_PUBLICATION",
    ),
    "openapi": ("SCHEMA_COMPATIBILITY_CHECK", "CODE_GENERATION"),
    "json-schema": ("SCHEMA_COMPATIBILITY_CHECK",),
    "asyncapi": ("SCHEMA_COMPATIBILITY_CHECK", "CODE_GENERATION"),
    "graphql": ("SCHEMA_COMPATIBILITY_CHECK", "CODE_GENERATION"),
    "avro": ("WIRE_COMPATIBILITY_CHECK", "SCHEMA_COMPATIBILITY_CHECK"),
}
REQUIRED_PINS = ("tool_version", "license_id", "rule_set_or_dialect", "codegen_determinism")

# Compatibility rule categories, ordered by how much they forbid. The order is
# the whole point of BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING: a run that
# reports PASS under a looser category than the baseline recorded did not pass
# the baseline's check, it passed a different and easier one.
RULE_CATEGORY_STRICTNESS = {"WIRE": 1, "WIRE_JSON": 2, "PACKAGE": 3, "FILE": 4}

# Decision-shaped keys. A request may not carry the decision it exists to ask a
# person for, at any depth. `window_verdict` is not on this list and is not
# matched by it: the check is exact key equality, and an observation window's
# verdict is a reading, not an authorisation.
DECISION_FIELDS = (
    "decision",
    "decided_by",
    "approved",
    "auto_merge",
    "merged",
    "verdict",
    "auto_contract",
    "contracted",
)

# The five phases of the canonical DAG, and the state whose arrival means the
# phase was entered. Rollback subjects are demanded per phase, so this mapping is
# what turns "rollback subject at every phase" into a countable obligation.
PHASE_ENTRY_STATE = (
    ("C1_CONTRACT_EXPANSION", "CONTRACT_BASELINE_BOUND"),
    ("A1_PROVIDER_EXPANSION", "PROVIDER_SURFACE_COEXISTING"),
    ("A2_CONSUMER_INVERSION", "CONSUMER_PORT_INVERTED"),
    ("E1_DUAL_RUN_AND_TELEMETRY", "DUAL_RUN_OBSERVED"),
    ("C2_LEGACY_CONTRACTION", "DOWNSTREAM_INVENTORY_TAKEN"),
)
PHASES = tuple(phase for phase, _ in PHASE_ENTRY_STATE)

MIGRATION_STATES = ("NOT_STARTED", "IN_PROGRESS", "MIGRATED", "ROLLED_BACK")

EXPANSION_ID = "DTCR-R2X-001"
RECEIPT_ID = "DTCR-R2-001"

# Every hard blocker this protocol names, in the order the issue names them. The
# receipt asserts each is absent from the run it describes; the compiler refuses
# any request in which one is present, so a receipt that admits one cannot be
# emitted, and the schema pins each false besides so a hand-written receipt
# cannot admit one either.
HARD_BLOCKERS = (
    "BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING",
    "SCHEMA_PUBLISHED_WITHOUT_EXACT_SOURCE",
    "GENERATED_STUB_DRIFT",
    "PROVIDER_REMOVES_LEGACY_BEFORE_CONSUMER_MIGRATION",
    "CONSUMER_SWITCH_WITHOUT_FALLBACK",
    "DUAL_RUN_WITHOUT_IDEMPOTENCY",
    "TELEMETRY_ABSENCE_PROMOTED_TO_SUCCESS",
    "NO_REMAINING_CALLERS_IN_PARTIAL_INDEX",
    "BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS",
    "AUTOMATIC_CONTRACTION_OR_MERGE",
    "FALSE_CROSS_REPO_GIT_PARENT",
)


class Refused(Exception):
    """The run cannot be compiled without inventing evidence for a phase.

    Carries the named code so a caller acts on which law fired, not on the fact
    that something did.
    """

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Refused("UNREADABLE_INPUT", f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise Refused("UNREADABLE_INPUT", f"{path}: root must be an object")
    return value


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def require(node: Any, key: str, where: str) -> Any:
    if not isinstance(node, dict) or key not in node:
        raise Refused("UNREADABLE_INPUT", f"{where}.{key} is required")
    return node[key]


def refuse_decision_fields(node: Any, where: str) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in DECISION_FIELDS:
                raise Refused(
                    "AUTOMATIC_CONTRACTION_OR_MERGE",
                    f"{where}.{key} carries a decision. This protocol proposes a "
                    f"contraction candidate; removing the legacy surface, publishing "
                    f"the contract and merging are repository and Human authority",
                )
            refuse_decision_fields(value, f"{where}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            refuse_decision_fields(value, f"{where}[{index}]")


def exact_subject(subject: Any, where: str, id_key: str) -> dict[str, str]:
    """One repository, pinned to the commit and tree that were actually read.

    Each participant repository carries its own binding, and the bindings are
    checked to be distinct downstream: a cross-repository run in which the
    provider and a consumer share one binding id is a single-repository run
    wearing R2's name, and the R1 protocol already owns that shape.
    """
    if not isinstance(subject, dict):
        raise Refused("STALE_SUBJECT", f"{where} must be an object")
    for key in (id_key, "subject_commit", "subject_tree"):
        if key not in subject:
            raise Refused("STALE_SUBJECT", f"{where}.{key} is required")
    if not BINDING_ID.match(str(subject[id_key])):
        raise Refused("STALE_SUBJECT", f"{where}.{id_key} is {subject[id_key]!r}")
    for key in ("subject_commit", "subject_tree"):
        if not EXACT_COMMIT.match(str(subject[key])):
            raise Refused(
                "STALE_SUBJECT",
                f"{where}.{key} is {subject[key]!r}: a branch, a tag or a moving "
                f"label binds a five-phase migration to whatever that label pointed "
                f"at while the phases were running",
            )
    return {
        "repository_binding_id": str(subject[id_key]),
        "subject_commit": str(subject["subject_commit"]),
        "subject_tree": str(subject["subject_tree"]),
    }


# --------------------------------------------------------------------------
# C1 CONTRACT_EXPANSION
# --------------------------------------------------------------------------

def compile_adapter(adapter: Any) -> dict[str, Any]:
    if not isinstance(adapter, dict):
        raise Refused("UNREADABLE_INPUT", "request.adapter is required")
    fmt = str(require(adapter, "contract_format", "request.adapter"))
    capability = str(require(adapter, "capability_class", "request.adapter"))
    declared = DECLARED_CONTRACT_ADAPTERS.get(fmt)
    if declared is None:
        raise Refused(
            "UNSUPPORTED_CONTRACT_FORMAT_PROMOTED_TO_SUPPORTED",
            f"{fmt!r} has no declared adapter capability class. Support means a class "
            f"is declared for the format, not that one could be written",
        )
    if capability not in declared:
        raise Refused(
            "UNSUPPORTED_CONTRACT_FORMAT_PROMOTED_TO_SUPPORTED",
            f"{fmt!r} declares {', '.join(declared)} and this request claims "
            f"{capability!r}",
        )

    pins = adapter.get("pins")
    if not isinstance(pins, dict):
        raise Refused("ADAPTER_PINS_INCOMPLETE", "request.adapter.pins is required")
    for key in REQUIRED_PINS:
        if not str(pins.get(key) or "").strip():
            raise Refused(
                "ADAPTER_PINS_INCOMPLETE",
                f"request.adapter.pins.{key} is empty. An unpinned {key} makes the same "
                f"contract generate different stubs on a different host, and the drift "
                f"lands in a consumer repository nobody was watching",
            )

    state = adapter.get("provider_state")
    if state not in ("DECLARED_NOT_VENDORED", "BLOCKED_ON_PROVIDER"):
        raise Refused(
            "UNREADABLE_INPUT",
            f"request.adapter.provider_state is {state!r}; the two states are "
            f"DECLARED_NOT_VENDORED and BLOCKED_ON_PROVIDER, and there is no EXERCISED "
            f"because no adapter implementation ships behind this protocol",
        )

    return {
        "adapter_binding_id": str(require(adapter, "adapter_binding_id", "request.adapter")),
        "capability_class": capability,
        "contract_format": fmt,
        "format_support": "SUPPORTED_BY_DECLARED_ADAPTER",
        "provider_state": state,
        "vendored": False,
        "pins": {key: str(pins[key]) for key in REQUIRED_PINS},
    }


def compile_compatibility(request: dict[str, Any]) -> dict[str, Any]:
    node = request.get("compatibility")
    if not isinstance(node, dict):
        raise Refused("UNREADABLE_INPUT", "request.compatibility is required")

    baseline = str(require(node, "baseline_commit", "request.compatibility"))
    if not EXACT_COMMIT.match(baseline):
        raise Refused(
            "STALE_SUBJECT",
            f"request.compatibility.baseline_commit is {baseline!r}: a compatibility "
            f"result is a statement about two exact trees, and a moving baseline makes "
            f"it a statement about neither",
        )

    baseline_category = str(require(node, "baseline_rule_category", "request.compatibility"))
    run_category = str(require(node, "run_rule_category", "request.compatibility"))
    for label, category in (
        ("baseline_rule_category", baseline_category),
        ("run_rule_category", run_category),
    ):
        if category not in RULE_CATEGORY_STRICTNESS:
            raise Refused(
                "UNREADABLE_INPUT",
                f"request.compatibility.{label} is {category!r}, which is not one of "
                f"{', '.join(sorted(RULE_CATEGORY_STRICTNESS))}",
            )

    result = node.get("result")
    if result not in ("PASS", "FAIL", "NOT_RUN"):
        raise Refused("UNREADABLE_INPUT", f"request.compatibility.result is {result!r}")

    # Required, not defaulted. A request that omits the key would turn the
    # exclusion guard off silently, and a guard nobody ran reports the same green
    # as one that passed. Declaring none is an empty list.
    if "excluded_paths" not in node:
        raise Refused(
            "UNREADABLE_INPUT",
            "request.compatibility.excluded_paths is required. Declaring none is an "
            "empty list; omitting the key would hide whether the check was narrowed",
        )
    excluded = sorted(set(map(str, node["excluded_paths"])))
    for path in excluded:
        if not REPO_RELATIVE.match(path.rstrip("/")):
            raise Refused("UNREADABLE_INPUT", f"excluded path {path!r} is not repository-relative")

    weakened = RULE_CATEGORY_STRICTNESS[run_category] < RULE_CATEGORY_STRICTNESS[baseline_category]
    if result == "PASS" and weakened:
        raise Refused(
            "BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING",
            f"the baseline records {baseline_category} and this run reports PASS under "
            f"{run_category}, which forbids strictly less. The check that would have "
            f"failed was replaced by one that could not",
        )
    if result == "PASS" and excluded:
        raise Refused(
            "BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING",
            f"the run reports PASS with {len(excluded)} path(s) excluded from the "
            f"comparison ({', '.join(excluded)}). A green over the paths that were "
            f"still being compared says nothing about the ones that were not",
        )

    return {
        "baseline_commit": baseline,
        "baseline_rule_category": baseline_category,
        "run_rule_category": run_category,
        "excluded_paths": excluded,
        "result": result,
        "rule_category_weakened": False,
    }


def compile_generated(request: dict[str, Any], contract: dict[str, str]) -> list[dict[str, Any]]:
    rows = request.get("generated_artifacts")
    if not isinstance(rows, list) or not rows:
        raise Refused(
            "UNREADABLE_INPUT",
            "request.generated_artifacts is required and cannot be empty: an expansion "
            "nobody generated stubs from is a schema edit, and consumers migrate "
            "against stubs",
        )
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        where = f"request.generated_artifacts[{index}]"
        path = str(require(row, "artifact_path", where))
        digest = str(require(row, "digest", where))
        origin = str(require(row, "generated_from_commit", where))
        if not REPO_RELATIVE.match(path):
            raise Refused("UNREADABLE_INPUT", f"{where}.artifact_path is not repository-relative")
        if not EXACT_DIGEST.match(digest):
            raise Refused("UNREADABLE_INPUT", f"{where}.digest must be a sha256 digest")
        if not EXACT_COMMIT.match(origin):
            raise Refused("UNREADABLE_INPUT", f"{where}.generated_from_commit must be a commit")
        if origin != contract["subject_commit"]:
            raise Refused(
                "GENERATED_STUB_DRIFT",
                f"{path} was generated from {origin[:12]} and the contract subject is "
                f"{contract['subject_commit'][:12]}. Stubs from an earlier contract "
                f"compile against the new one until the field somebody added is the "
                f"field somebody reads",
            )
        out.append({"artifact_path": path, "digest": digest, "generated_from_commit": origin})
    return sorted(out, key=lambda row: row["artifact_path"])


def compile_publication(request: dict[str, Any], contract: dict[str, str]) -> dict[str, Any]:
    node = request.get("publication")
    if not isinstance(node, dict):
        raise Refused("UNREADABLE_INPUT", "request.publication is required")

    intent = node.get("intent")
    if intent not in ("NONE", "REGISTRY_PUBLISH"):
        raise Refused("UNREADABLE_INPUT", f"request.publication.intent is {intent!r}")

    access = node.get("account_access")
    if access not in ("ABSENT", "AVAILABLE"):
        raise Refused("UNREADABLE_INPUT", f"request.publication.account_access is {access!r}")

    # Single-valued, and checked before the no-publication early return rather
    # than after it. Holding a registry account is a capability; whether this
    # schema's content may be published under somebody's terms is a rights
    # question, and no state of this protocol answers the second. Accepting a
    # CLEARED value here and pinning HUMAN_ADMIT_REQUIRED into the receipt anyway
    # would leave the claim travelling in the request forever, unrefused and
    # unread -- so the value a request may carry is exactly one.
    rights = node.get("content_rights")
    if rights != "HUMAN_ADMIT_REQUIRED":
        raise Refused(
            "BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS",
            f"request.publication.content_rights is {rights!r} while account access is "
            f"{access!r}. Being able to push to a registry is a capability; being "
            f"allowed to publish that schema's content is a rights and terms question, "
            f"and the account answers only the first",
        )

    published: dict[str, Any] = {
        "intent": intent,
        "account_access": access,
        "content_rights": "HUMAN_ADMIT_REQUIRED",
        "performed": False,
    }

    if intent == "NONE":
        # A run that publishes nothing still records that it did not, so a reader
        # cannot mistake an absent field for an absent decision.
        return published

    expected = {"source_commit": contract["subject_commit"], "source_tree": contract["subject_tree"]}
    for key, bound in expected.items():
        value = str(require(node, key, "request.publication"))
        if not EXACT_COMMIT.match(value):
            raise Refused(
                "SCHEMA_PUBLISHED_WITHOUT_EXACT_SOURCE",
                f"request.publication.{key} is {value!r}. A registry artifact whose "
                f"source is a moving label cannot be traced back to the bytes that "
                f"produced it once the label moves",
            )
        if value != bound:
            raise Refused(
                "SCHEMA_PUBLISHED_WITHOUT_EXACT_SOURCE",
                f"request.publication.{key} is {value[:12]} and the contract subject "
                f"holds {bound[:12]}. The artifact would be published from bytes "
                f"nobody bound to this run",
            )
        published[key] = value

    published["registry_binding"] = str(require(node, "registry_binding", "request.publication"))
    return published


def compile_expansion(
    request: dict[str, Any],
    contract: dict[str, str],
    adapter: dict[str, Any],
    compatibility: dict[str, Any],
    generated: list[dict[str, Any]],
    publication: dict[str, Any],
) -> dict[str, Any]:
    old = str(require(request["contract"], "contract_version_old", "request.contract"))
    new = str(require(request["contract"], "contract_version_new", "request.contract"))
    if old == new:
        raise Refused(
            "CONTRACT_REPLACED_NOT_EXPANDED",
            f"the old and new contract versions are both {old!r}. Expand & Contract "
            f"exists because the new surface runs beside the old one; editing one "
            f"version in place is the atomic change this protocol is the alternative to",
        )
    return {
        "schema": "dtcr/refactor-r2-contract-expansion/v1",
        "expansion_id": EXPANSION_ID,
        "subject": dict(contract),
        "contract_version_old": old,
        "contract_version_new": new,
        "adapter": adapter,
        "compatibility": compatibility,
        "generated_artifacts": generated,
        "publication": publication,
        "establishes": {
            "old_surface_removed": False,
            "published": False,
        },
    }


# --------------------------------------------------------------------------
# A1 PROVIDER_EXPANSION / A2 CONSUMER_INVERSION
# --------------------------------------------------------------------------

def compile_provider(request: dict[str, Any]) -> dict[str, Any]:
    node = request.get("provider")
    if not isinstance(node, dict):
        raise Refused("UNREADABLE_INPUT", "request.provider is required")
    subject = exact_subject(node, "request.provider", "repository_binding_id")
    for key in ("legacy_surface_present", "new_surface_present"):
        if not isinstance(node.get(key), bool):
            raise Refused("UNREADABLE_INPUT", f"request.provider.{key} must be a boolean")
    window = node.get("coexistence_window_state")
    if window not in ("OBSERVED", "NOT_OBSERVED"):
        raise Refused(
            "UNREADABLE_INPUT", f"request.provider.coexistence_window_state is {window!r}"
        )
    return {
        "subject": subject,
        "legacy_surface_present": bool(node["legacy_surface_present"]),
        "new_surface_present": bool(node["new_surface_present"]),
        "coexistence_window_state": window,
    }


def compile_consumers(
    request: dict[str, Any],
    contract: dict[str, str],
    generated: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = request.get("consumers")
    if not isinstance(rows, list) or not rows:
        raise Refused(
            "UNREADABLE_INPUT",
            "request.consumers is required and cannot be empty: a contract with no "
            "bound consumer has nothing to migrate, and the contraction gate would "
            "clear over an empty set",
        )
    digests = {row["digest"] for row in generated}
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        where = f"request.consumers[{index}]"
        subject = exact_subject(row, where, "consumer_binding_id")

        state = row.get("migration_state")
        if state not in MIGRATION_STATES:
            raise Refused("UNREADABLE_INPUT", f"{where}.migration_state is {state!r}")

        fallback = row.get("fallback_state")
        if fallback not in ("BOUND", "ABSENT"):
            raise Refused("UNREADABLE_INPUT", f"{where}.fallback_state is {fallback!r}")

        traffic = row.get("traffic_on_new_percent")
        if not isinstance(traffic, int) or isinstance(traffic, bool) or not 0 <= traffic <= 100:
            raise Refused("UNREADABLE_INPUT", f"{where}.traffic_on_new_percent is {traffic!r}")

        if traffic > 0 and fallback != "BOUND":
            raise Refused(
                "CONSUMER_SWITCH_WITHOUT_FALLBACK",
                f"{subject['repository_binding_id']} sends {traffic}% of its traffic to "
                f"the new surface with no fallback bound. The first failure on the new "
                f"path has nowhere to go, and a migration with no way back is a cutover",
            )

        # MIGRATED is the word the contraction gate counts, so it has to mean the
        # legacy path carries none of this consumer's traffic. A consumer recorded
        # MIGRATED while still sending part of its calls to the old surface is the
        # exact shape that makes deleting that surface look safe.
        if state == "MIGRATED" and traffic != 100:
            raise Refused(
                "PROVIDER_REMOVES_LEGACY_BEFORE_CONSUMER_MIGRATION",
                f"{subject['repository_binding_id']} reports MIGRATED with {traffic}% of "
                f"its traffic on the new surface, so the remaining {100 - traffic}% still "
                f"calls the legacy one that this state is read as permission to remove",
            )

        if not isinstance(row.get("port_bound"), bool):
            raise Refused("UNREADABLE_INPUT", f"{where}.port_bound must be a boolean")
        if state in ("IN_PROGRESS", "MIGRATED") and not row["port_bound"]:
            raise Refused(
                "CONSUMER_SWITCH_WITHOUT_FALLBACK",
                f"{subject['repository_binding_id']} reports {state} with no domain Port "
                f"bound, so its domain calls the generated client directly and there is "
                f"no seam a fallback could be installed at",
            )

        digest = str(require(row, "generated_artifact_digest", where))
        if not EXACT_DIGEST.match(digest):
            raise Refused("UNREADABLE_INPUT", f"{where}.generated_artifact_digest must be sha256")
        if state != "NOT_STARTED" and digest not in digests:
            raise Refused(
                "GENERATED_STUB_DRIFT",
                f"{subject['repository_binding_id']} built against stub digest "
                f"{digest[:12]}, which the contract expansion did not emit. The consumer "
                f"is migrating onto a surface that is not the one that was expanded",
            )

        verification = row.get("verification")
        if not isinstance(verification, dict):
            raise Refused("UNREADABLE_INPUT", f"{where}.verification is required")
        vstate = verification.get("state")
        if vstate not in ("PASS", "FAIL", "NOT_RUN"):
            raise Refused("UNREADABLE_INPUT", f"{where}.verification.state is {vstate!r}")
        total = verification.get("total")
        passed = verification.get("passed")
        if (
            not isinstance(total, int)
            or isinstance(total, bool)
            or total < 1
            or not isinstance(passed, int)
            or isinstance(passed, bool)
            or passed < 0
            or passed > total
        ):
            raise Refused(
                "VERIFICATION_DENOMINATOR_ABSENT",
                f"{where}.verification declares passed={passed!r} of total={total!r}. A "
                f"consumer receipt with a passed count and no set behind it is what the "
                f"contraction gate would read as a bound migration",
            )
        if state == "MIGRATED" and vstate != "PASS":
            raise Refused(
                "CONSUMER_MIGRATED_WITHOUT_VERIFICATION",
                f"{subject['repository_binding_id']} reports MIGRATED with its "
                f"verification lane {vstate}. The receipt the contraction gate counts "
                f"would be a receipt for a migration nobody verified",
            )

        out.append(
            {
                "schema": "dtcr/refactor-r2-consumer-migration/v1",
                "migration_id": f"DTCR-R2M-{index + 1:03d}",
                "expansion_ref": EXPANSION_ID,
                "subject": subject,
                "contract_subject_commit": contract["subject_commit"],
                "port_bound": bool(row["port_bound"]),
                "client_adapter_ref": str(require(row, "client_adapter_ref", where)),
                "fallback_state": fallback,
                "traffic_on_new_percent": traffic,
                "generated_artifact_digest": digest,
                "migration_state": state,
                "verification": {"state": vstate, "passed": passed, "total": total},
                "establishes": {
                    "legacy_call_path_removed": False,
                    "cross_repository_git_parent": False,
                },
            }
        )
    return sorted(out, key=lambda row: row["migration_id"])


def compile_participants(
    request: dict[str, Any],
    contract: dict[str, str],
    provider: dict[str, Any],
    consumers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Every declared Git parent must belong to the repository that declares it.

    The deployment order across these repositories is real and is recorded as a
    process edge. It is not ancestry: a consumer commit does not descend from the
    provider commit it talks to, and a receipt that writes it down as one makes
    `git merge-base` answer a question nobody asked it.

    The reach of this check is exactly the commits this run declares. A parent
    that belongs to a repository nobody listed cannot be recognised as foreign
    from inside a request, so what is refused here is the fabrication the run
    itself makes visible -- naming another *participant's* commit as a parent.
    """
    participants = [
        ("request.contract", contract, request.get("contract")),
        ("request.provider", provider["subject"], request.get("provider")),
    ]
    for index, consumer in enumerate(consumers):
        participants.append(
            (f"request.consumers[{index}]", consumer["subject"], request["consumers"][index])
        )

    bindings = [subject["repository_binding_id"] for _, subject, _ in participants]
    if len(set(bindings)) != len(bindings):
        raise Refused(
            "FALSE_CROSS_REPO_GIT_PARENT",
            "two participants share one repository binding id, so a commit in one is "
            "indistinguishable from a commit in the other and every ancestry check "
            "below would compare a repository against itself",
        )

    owned: dict[str, set[str]] = {}
    for _, subject, _ in participants:
        owned.setdefault(subject["repository_binding_id"], set()).add(subject["subject_commit"])
    everything = set().union(*owned.values())

    rows: list[dict[str, Any]] = []
    for where, subject, node in participants:
        binding = subject["repository_binding_id"]
        declared = node.get("declared_parent_commits")
        if not isinstance(declared, list):
            raise Refused(
                "UNREADABLE_INPUT",
                f"{where}.declared_parent_commits is required. Declaring none is an "
                f"empty list; omitting the key would turn the ancestry guard off",
            )
        for parent in sorted(set(map(str, declared))):
            if not EXACT_COMMIT.match(parent):
                raise Refused("STALE_SUBJECT", f"{where}.declared_parent_commits holds {parent!r}")
            if parent in (everything - owned[binding]):
                raise Refused(
                    "FALSE_CROSS_REPO_GIT_PARENT",
                    f"{where} declares {parent[:12]} as a Git parent, and that commit "
                    f"belongs to another repository in this run. Cross-repository order "
                    f"is a process edge; writing it as ancestry invents a history "
                    f"neither repository has",
                )
        rows.append(
            {
                "repository_binding_id": binding,
                "kind": "PROCESS_EDGE",
                "git_parent": False,
            }
        )
    return sorted(rows, key=lambda row: row["repository_binding_id"])


# --------------------------------------------------------------------------
# E1 DUAL_RUN_AND_TELEMETRY / C2 LEGACY_CONTRACTION
# --------------------------------------------------------------------------

def compile_observation(request: dict[str, Any]) -> dict[str, Any]:
    node = request.get("observation")
    if not isinstance(node, dict):
        raise Refused("UNREADABLE_INPUT", "request.observation is required")

    dual_run = node.get("dual_run")
    if dual_run not in ("EXERCISED", "NOT_EXERCISED"):
        raise Refused("UNREADABLE_INPUT", f"request.observation.dual_run is {dual_run!r}")
    if not isinstance(node.get("idempotency_key_bound"), bool):
        raise Refused(
            "UNREADABLE_INPUT", "request.observation.idempotency_key_bound must be a boolean"
        )
    if dual_run == "EXERCISED" and not node["idempotency_key_bound"]:
        raise Refused(
            "DUAL_RUN_WITHOUT_IDEMPOTENCY",
            "the run sent each request down both the legacy and the new path with no "
            "idempotency key bound. Every write in the comparison window happened "
            "twice, and the comparison it was run to produce is between two states the "
            "run itself created",
        )

    verdict = node.get("window_verdict")
    if verdict not in ("HELD", "REGRESSED", "NOT_OBSERVED"):
        raise Refused("UNREADABLE_INPUT", f"request.observation.window_verdict is {verdict!r}")

    telemetry = node.get("telemetry")
    if not isinstance(telemetry, dict):
        raise Refused("UNREADABLE_INPUT", "request.observation.telemetry is required")
    tstate = telemetry.get("state")
    if tstate not in ("PASS", "FAIL", "ABSENT"):
        raise Refused("UNREADABLE_INPUT", f"request.observation.telemetry.state is {tstate!r}")
    samples = telemetry.get("samples")
    if not isinstance(samples, int) or isinstance(samples, bool) or samples < 0:
        raise Refused("UNREADABLE_INPUT", f"request.observation.telemetry.samples is {samples!r}")

    if tstate == "ABSENT" and verdict == "HELD":
        raise Refused(
            "TELEMETRY_ABSENCE_PROMOTED_TO_SUCCESS",
            "the observation window is recorded as HELD with no telemetry behind it. "
            "Nothing broke that anybody was watching is a statement about the watching",
        )
    if tstate == "PASS" and samples == 0:
        raise Refused(
            "TELEMETRY_ABSENCE_PROMOTED_TO_SUCCESS",
            "the telemetry lane reports PASS over zero samples. An error rate computed "
            "from an empty window is zero for the same reason a switched-off meter is",
        )

    return {
        "dual_run": dual_run,
        "idempotency_key_bound": bool(node["idempotency_key_bound"]),
        "window_verdict": verdict,
        "telemetry": {"state": tstate, "samples": samples},
    }


def compile_downstream(request: dict[str, Any]) -> dict[str, Any]:
    node = request.get("downstream")
    if not isinstance(node, dict):
        raise Refused("UNREADABLE_INPUT", "request.downstream is required")
    completeness = node.get("inventory_completeness")
    if completeness not in ("COMPLETE_FOR_ADMITTED_INDEX", "PARTIAL_LOWER_BOUND"):
        raise Refused(
            "UNREADABLE_INPUT", f"request.downstream.inventory_completeness is {completeness!r}"
        )
    remaining = node.get("remaining_legacy_callers")
    if not isinstance(remaining, int) or isinstance(remaining, bool) or remaining < 0:
        raise Refused(
            "UNREADABLE_INPUT", f"request.downstream.remaining_legacy_callers is {remaining!r}"
        )
    if completeness == "PARTIAL_LOWER_BOUND" and remaining == 0:
        raise Refused(
            "NO_REMAINING_CALLERS_IN_PARTIAL_INDEX",
            "the inventory is a partial lower bound and it reports zero remaining legacy "
            "callers. Zero found in the part that was indexed is not zero, and it is the "
            "number the contraction gate would read as permission to delete the surface",
        )
    notice = str(require(node, "deprecation_notice_ref", "request.downstream")).strip()
    if not notice:
        raise Refused(
            "UNREADABLE_INPUT",
            "request.downstream.deprecation_notice_ref is empty: a surface removed with "
            "no notice anybody can point at was removed without warning by definition",
        )
    return {
        "inventory_completeness": completeness,
        "remaining_legacy_callers": remaining,
        "deprecation_notice_ref": notice,
    }


def compile_contraction(
    request: dict[str, Any], provider: dict[str, Any], consumers: list[dict[str, Any]]
) -> dict[str, Any]:
    node = request.get("contraction")
    if not isinstance(node, dict):
        raise Refused("UNREADABLE_INPUT", "request.contraction is required")

    requested = node.get("legacy_surface_removal_requested")
    if not isinstance(requested, bool):
        raise Refused(
            "UNREADABLE_INPUT",
            "request.contraction.legacy_surface_removal_requested must be a boolean",
        )
    authorization = node.get("authorization")
    if authorization != "HUMAN_ADMIT_REQUIRED":
        raise Refused(
            "AUTOMATIC_CONTRACTION_OR_MERGE",
            f"request.contraction.authorization is {authorization!r}. A bound receipt "
            f"from every consumer and a clean observation window are inputs to the "
            f"decision to delete the old surface, never the decision",
        )

    unbound = sorted(
        row["subject"]["repository_binding_id"]
        for row in consumers
        if row["migration_state"] != "MIGRATED"
    )
    if requested and unbound:
        raise Refused(
            "PROVIDER_REMOVES_LEGACY_BEFORE_CONSUMER_MIGRATION",
            f"contraction is requested while {len(unbound)} consumer(s) have no bound "
            f"migration receipt ({', '.join(unbound)}). The consumers that are still on "
            f"the legacy surface find out at their next call",
        )
    if not provider["legacy_surface_present"] and unbound:
        raise Refused(
            "PROVIDER_REMOVES_LEGACY_BEFORE_CONSUMER_MIGRATION",
            f"the provider reports the legacy surface already gone while "
            f"{len(unbound)} consumer(s) are not migrated ({', '.join(unbound)}). "
            f"Expand & Contract is the order, and this run ran it backwards",
        )

    return {
        "legacy_surface_removal_requested": requested,
        "legacy_surface_removed": False,
        "authorization": "HUMAN_ADMIT_REQUIRED",
        "consumer_receipts_bound": len(consumers) - len(unbound),
        "consumer_receipts_required": len(consumers),
    }


# --------------------------------------------------------------------------
# rollback
# --------------------------------------------------------------------------

def compile_rollback_subjects(
    request: dict[str, Any],
    states: list[str],
    contract: dict[str, str],
    provider: dict[str, Any],
    consumers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """One restore point per phase entered, in the repository that phase writes.

    The obligation is per phase and not per run because the phases write to
    different repositories at different times. A single "rollback to this commit"
    for a five-phase migration names one repository, and the four it does not
    name are the ones still carrying the half-applied change.
    """
    declared = request.get("rollback_subjects")
    if not isinstance(declared, list):
        raise Refused(
            "UNREADABLE_INPUT",
            "request.rollback_subjects is required and is a list of one restore point "
            "per phase entered",
        )

    rows: dict[tuple[str, str], str] = {}
    for index, row in enumerate(declared):
        where = f"request.rollback_subjects[{index}]"
        phase = str(require(row, "phase", where))
        binding = str(require(row, "repository_binding_id", where))
        restored = str(require(row, "restored_commit", where))
        if phase not in PHASES:
            raise Refused("UNREADABLE_INPUT", f"{where}.phase is {phase!r}")
        if not EXACT_COMMIT.match(restored):
            raise Refused(
                "STALE_SUBJECT",
                f"{where}.restored_commit is {restored!r}: a restore point on a moving "
                f"label does not say what the tree would be restored to",
            )
        # Last-write-wins would silently pick one of two disagreeing restore
        # points, and the one it dropped is the tree somebody would have gone
        # back to. Two rows for one phase and one repository is a conflict, not
        # an update.
        if rows.get((phase, binding), restored) != restored:
            raise Refused(
                "ROLLBACK_SUBJECT_ABSENT_FOR_PHASE",
                f"{phase} in {binding} declares two different restore points "
                f"({rows[(phase, binding)][:12]} and {restored[:12]}), so the record "
                f"does not say which tree the phase would be put back to",
            )
        rows[(phase, binding)] = restored

    entered = [phase for phase, entry in PHASE_ENTRY_STATE if entry in states]
    required: list[tuple[str, str]] = []
    for phase in entered:
        if phase == "C1_CONTRACT_EXPANSION":
            required.append((phase, contract["repository_binding_id"]))
        elif phase == "A2_CONSUMER_INVERSION":
            # Every consumer that started moving has its own tree to put back.
            required.extend(
                (phase, row["subject"]["repository_binding_id"])
                for row in consumers
                if row["migration_state"] != "NOT_STARTED"
            )
        else:
            required.append((phase, provider["subject"]["repository_binding_id"]))

    missing = sorted(
        f"{phase}/{binding}" for phase, binding in required if (phase, binding) not in rows
    )
    if missing:
        raise Refused(
            "ROLLBACK_SUBJECT_ABSENT_FOR_PHASE",
            f"the run entered {len(entered)} phase(s) and declares no restore point for "
            f"{', '.join(missing)}. A phase with no rollback subject is a phase that can "
            f"only go forward",
        )

    return sorted(
        (
            {"phase": phase, "repository_binding_id": binding, "restored_commit": restored}
            for (phase, binding), restored in rows.items()
        ),
        key=lambda row: (row["phase"], row["repository_binding_id"]),
    )


def compile_rollback(rollback: Any, subjects: list[dict[str, Any]]) -> dict[str, Any] | None:
    if rollback is None:
        return None
    if not isinstance(rollback, dict):
        raise Refused("UNREADABLE_INPUT", "request.rollback must be an object")
    phase = str(require(rollback, "phase", "request.rollback"))
    binding = str(require(rollback, "repository_binding_id", "request.rollback"))
    match = [
        row
        for row in subjects
        if row["phase"] == phase and row["repository_binding_id"] == binding
    ]
    if not match:
        raise Refused(
            "ROLLBACK_SUBJECT_ABSENT_FOR_PHASE",
            f"the rollback names {phase}/{binding} and no restore point was declared for "
            f"it, so the record does not say what the tree was put back to",
        )
    # No `reason` field: which lane failed is already in the receipt's observation
    # and blocked_on, and a second copy of that fact is a copy that can disagree.
    if rollback.get("applied_change_reverted") is not True:
        raise Refused(
            "ROLLBACK_NOT_REVERTED",
            "the rollback record says the applied change was not reverted, which is a "
            "half-migrated fleet wearing a reassuring name",
        )
    return {
        "phase": phase,
        "repository_binding_id": binding,
        "restored_commit": match[0]["restored_commit"],
        "applied_change_reverted": True,
    }


# --------------------------------------------------------------------------
# terminal
# --------------------------------------------------------------------------

def states_entered(
    adapter: dict[str, Any],
    provider: dict[str, Any],
    consumers: list[dict[str, Any]],
    observation: dict[str, Any],
    downstream: dict[str, Any],
) -> list[str]:
    """The states this run actually entered, in protocol order.

    Derived rather than declared: a run that stopped at the provider and lists
    every state is reporting the diagram instead of the run. The adapter gate is
    first because it is the one that most often makes the difference invisible --
    with no adapter implementation available no stub was generated, so no
    consumer could have compiled against one however complete the expansion
    upstream of it looks.
    """
    entered = ["CONTRACT_BASELINE_BOUND", "CONTRACT_EXPANDED"]
    if adapter["provider_state"] == "BLOCKED_ON_PROVIDER":
        return entered
    entered.append("GENERATED_ARTIFACTS_PINNED")
    if not (provider["legacy_surface_present"] and provider["new_surface_present"]):
        return entered
    entered.append("PROVIDER_SURFACE_COEXISTING")
    if not any(row["port_bound"] for row in consumers):
        return entered
    entered.append("CONSUMER_PORT_INVERTED")
    if not any(row["traffic_on_new_percent"] > 0 for row in consumers):
        return entered
    entered.append("CONSUMER_TRAFFIC_MIGRATED")
    if observation["dual_run"] != "EXERCISED":
        return entered
    entered.append("DUAL_RUN_OBSERVED")
    if observation["telemetry"]["state"] == "ABSENT":
        return entered
    entered.append("TELEMETRY_WINDOW_OBSERVED")
    entered.append("DOWNSTREAM_INVENTORY_TAKEN")
    if downstream["inventory_completeness"] != "COMPLETE_FOR_ADMITTED_INDEX":
        return entered
    entered.append("LEGACY_CONTRACTION_PROPOSED")
    return entered


def compile_receipt(
    request: dict[str, Any],
    contract: dict[str, str],
    expansion: dict[str, Any],
    provider: dict[str, Any],
    consumers: list[dict[str, Any]],
    participants: list[dict[str, Any]],
) -> dict[str, Any]:
    observation = compile_observation(request)
    downstream = compile_downstream(request)
    contraction = compile_contraction(request, provider, consumers)

    states = states_entered(expansion["adapter"], provider, consumers, observation, downstream)
    subjects = compile_rollback_subjects(request, states, contract, provider, consumers)
    rollback = compile_rollback(request.get("rollback"), subjects)

    blocked_on: list[str] = []
    if expansion["adapter"]["provider_state"] == "BLOCKED_ON_PROVIDER":
        blocked_on.append("CONTRACT_ADAPTER_BLOCKED_ON_PROVIDER")
    if expansion["compatibility"]["result"] == "NOT_RUN":
        blocked_on.append("COMPATIBILITY_CHECK_NOT_RUN")
    if expansion["compatibility"]["result"] == "FAIL":
        blocked_on.append("COMPATIBILITY_CHECK_FAILED")
    if any(row["migration_state"] != "MIGRATED" for row in consumers):
        blocked_on.append("CONSUMER_MIGRATION_INCOMPLETE")
    if observation["dual_run"] != "EXERCISED":
        blocked_on.append("DUAL_RUN_NOT_EXERCISED")
    if observation["telemetry"]["state"] == "ABSENT":
        blocked_on.append("TELEMETRY_WINDOW_ABSENT")
    if observation["window_verdict"] == "NOT_OBSERVED":
        # A window nobody watched is not a window that held. Without this the
        # terminal reachable from an unobserved window is CONTRACTION_CANDIDATE,
        # which is the whole telemetry-absence failure wearing the observation
        # lane's name instead of the telemetry lane's.
        blocked_on.append("OBSERVATION_WINDOW_NOT_OBSERVED")
    if downstream["inventory_completeness"] == "PARTIAL_LOWER_BOUND":
        blocked_on.append("DOWNSTREAM_INVENTORY_PARTIAL")
    if downstream["remaining_legacy_callers"] > 0:
        blocked_on.append("LEGACY_CALLERS_STILL_PRESENT")
    if expansion["publication"]["intent"] == "REGISTRY_PUBLISH":
        # Not conditional on which credential is present. Publishing a contract to
        # an external registry is a rights and terms operation, and this protocol
        # has no state in which it clears one.
        blocked_on.append("REGISTRY_PUBLICATION_HUMAN_ADMIT_REQUIRED")

    receipt: dict[str, Any] = {
        "schema": "dtcr/refactor-r2-receipt/v1",
        "receipt_id": RECEIPT_ID,
        "expansion_ref": EXPANSION_ID,
        "subject": dict(contract),
        "participants": participants,
        "consumer_migration_refs": [row["migration_id"] for row in consumers],
        "states_entered": states,
        "provider_coexistence": provider,
        "observation": observation,
        "downstream": downstream,
        "contraction": contraction,
        "rollback_subjects": subjects,
        "hard_blockers": {code: False for code in HARD_BLOCKERS},
        "establishes": {
            "applied_on_real_codebase": False,
            "consumer_canary_observed": False,
            "protocol_ready": False,
        },
        "authority": {
            "contraction": False,
            "merge": False,
            "production": False,
            "publication": False,
        },
    }

    regressed = (
        any(row["migration_state"] == "ROLLED_BACK" for row in consumers)
        or observation["telemetry"]["state"] == "FAIL"
        or observation["window_verdict"] == "REGRESSED"
    )

    if regressed:
        if rollback is None:
            raise Refused(
                "REGRESSION_WITHOUT_ROLLBACK",
                "a consumer rolled back or the observation window regressed, and no "
                "rollback record was supplied. Traffic is on the new surface, a lane "
                "disagreed, and the receipt has no honest terminal to reach",
            )
        receipt["terminal_state"] = "ROLLED_BACK"
        # The lanes that failed stay named. A rolled-back run whose blocked_on is
        # empty reads downstream like a clean run somebody reverted for taste.
        receipt["blocked_on"] = sorted(set(blocked_on))
        receipt["rollback"] = rollback
        return receipt

    if rollback is not None:
        raise Refused(
            "ROLLBACK_WITHOUT_REGRESSION",
            "a rollback record was supplied for a run in which every consumer held and "
            "the observation window did not regress. A rollback nobody can point at a "
            "failure for is a revert with a story",
        )

    if blocked_on:
        receipt["terminal_state"] = "BLOCKED"
        receipt["blocked_on"] = sorted(set(blocked_on))
        return receipt

    receipt["terminal_state"] = "CONTRACTION_CANDIDATE"
    receipt["blocked_on"] = []
    return receipt


# --------------------------------------------------------------------------

def compile_r2(source: Path) -> dict[str, Any]:
    request = load(source)
    if request.get("schema") != "dtcr/refactor-r2-request/v1":
        raise Refused(
            "UNREADABLE_INPUT", "input must be a dtcr/refactor-r2-request/v1 artifact"
        )
    refuse_decision_fields(request, "request")

    contract = exact_subject(request.get("contract"), "request.contract", "repository_binding_id")
    adapter = compile_adapter(request.get("adapter"))
    compatibility = compile_compatibility(request)
    generated = compile_generated(request, contract)
    publication = compile_publication(request, contract)
    expansion = compile_expansion(
        request, contract, adapter, compatibility, generated, publication
    )

    provider = compile_provider(request)
    consumers = compile_consumers(request, contract, generated)
    participants = compile_participants(request, contract, provider, consumers)

    receipt = compile_receipt(request, contract, expansion, provider, consumers, participants)
    return {
        "schema": "dtcr/refactor-r2-projection/v1",
        "derived_from": source.name,
        "contract_expansion": expansion,
        "consumer_migrations": consumers,
        "receipt": receipt,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile one cross-repository Expand & Contract (R2) refactor run."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="byte-compare --out against a fresh compilation instead of writing it",
    )
    args = parser.parse_args()

    try:
        rendered = canonical(compile_r2(args.input))
    except Refused as error:
        print(f"DTCR-R2-RED {error}", file=sys.stderr)
        return 2
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        print(f"DTCR-R2-UNUSABLE malformed request: {error!r}", file=sys.stderr)
        return 64

    if args.out is None:
        sys.stdout.write(rendered)
        return 0
    if args.check:
        try:
            current = args.out.read_text(encoding="utf-8")
        except OSError as error:
            print(f"DTCR-R2-RED missing projection {args.out}: {error}", file=sys.stderr)
            return 2
        if current != rendered:
            print(
                f"DTCR-R2-RED {args.out} is not what {args.input.name} compiles to; "
                f"regenerate it rather than editing it",
                file=sys.stderr,
            )
            return 2
        print(f"DTCR-R2-GREEN projection is current: {args.out.name}")
        return 0
    args.out.write_text(rendered, encoding="utf-8")
    print(f"DTCR-R2-GREEN wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
