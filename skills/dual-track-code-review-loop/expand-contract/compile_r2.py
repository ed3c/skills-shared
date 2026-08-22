#!/usr/bin/env python3
"""Compile one cross-repository Expand and Contract (R2) run.

    C1 CONTRACT_EXPANSION       central contract, baseline, compatibility verdict
    -> A1 PROVIDER_EXPANSION    new handler standing beside the legacy one
    -> A2 CONSUMER_INVERSION    domain Port, client adapter, fallback
    -> E1 DUAL_RUN_AND_TELEMETRY   split, denominator, window, idempotency
    -> C2 LEGACY_CONTRACTION    removal, only after a Human authorizes it
    -> CANDIDATE_RECEIPT | BLOCKED | STOPPED_WITH_ROLLBACK | ROLLED_BACK

The input is one `dtcr/refactor-r2-request/v1` document describing a run. The
output is the two artifacts it emits -- the multi-repository subject binding and
the R2 receipt -- serialised canonically (`sort_keys`, two-space indent, one
trailing newline), so `--check` byte-compares a committed projection instead of
trusting that somebody regenerated it.

Where this differs from `refactor/compile_r1.py`, and why each difference exists
rather than being a reuse:

* The subject is an array. Every R1 artifact carries one `repository_binding_id`
  under `additionalProperties: false`, which cannot express a run whose provider
  and consumer sides live at different commits in different repositories. That
  is not a widening of R1's subject; it is the reason this compiler exists.
* Ancestry is confined to its own repository, and the provider-to-consumer edge
  is typed `PROCESS_DEPENDENCY_NOT_GIT_PARENT`. A cross-repository ancestry
  entry is refused by name. The failure it prevents is invisible from either
  side: each repository resolves its own history cleanly, and only the joined
  graph carries a parent nothing can resolve.
* Rollback is one row per repository with its own disposition. R1's single
  `restored_commit` describes a run that was reverted; this protocol's ordinary
  stop leaves one repository expanded (frequently unrollbackably, because the
  surface is deployed) and the other reverted, and one commit cannot say that.
* Three lanes may only record absence here, and each says so in its own field:
  the dual-run observation, the idempotency of a write path, and the contraction
  authorization. Deriving any of them from the static facts next to it is
  refused by the name of the blocker it would breach.

What this compiler will not do. It applies nothing: no repository is read,
written or parsed here, and `establishes.applied_on_real_codebase` is emitted as
NOT_EXERCISED on every receipt. It vendors no compatibility provider: a
`dtcr/contract-compatibility-result/v1` record is an input it consumes, and
PROVIDER_UNAVAILABLE is a legal one. It contracts nothing and merges nothing:
`contraction.authorization` is single-valued unless a Human is named against an
exact head, and any decision-shaped field anywhere in the request is refused.
And it cannot print its own readiness -- `protocol_ready` is pinned false.

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
RESULT_ID = re.compile(r"^DTCR-CK-[0-9]{3}$")
BINDING_ID = re.compile(r"^DTCR-RB-[0-9a-f]{16}$")
PORT_ID = re.compile(r"^DTCR-PT-[0-9]{3}$")

# Decision-shaped keys, refused at every depth. A request may not carry the
# decision it exists to ask a person for.
DECISION_FIELDS = ("decision", "decided_by", "approved", "auto_merge", "merged", "verdict")

ROLES = ("PROVIDER", "CONSUMER")
# Two values, not the three the coverage-ceiling vocabulary carries. UNKNOWN is
# absent on purpose: every index this protocol records is named and digest-pinned,
# so an index whose completeness nobody characterised is refused rather than
# recorded, and a value nothing can emit would read downstream as a state the
# protocol reaches.
COMPLETENESS = ("COMPLETE_FOR_ANALYSED_INPUTS", "PARTIAL_LOWER_BOUND")
OUTCOMES = (
    "NO_BREAKING_CHANGE_DETECTED",
    "BREAKING_CHANGE_DETECTED",
    "NOT_APPLICABLE",
    "PROVIDER_UNAVAILABLE",
)
MIGRATION_STATES = ("MIGRATED", "REVERTED", "NOT_ENTERED")
OBSERVATION_STATES = ("OBSERVED", "NOT_OBSERVED", "NOT_EXERCISED")
DISPOSITIONS = ("REVERTED", "NOT_ROLLBACKABLE_DEPLOYED_SURFACE", "NOT_ENTERED")
AUTHORIZATIONS = ("HUMAN_ADMIT_REQUIRED", "ADMITTED")
PUBLICATION_INTENTS = ("NOT_PUBLISHED", "PUBLISHED")

C1, A1, A2, E1, C2 = (
    "C1_CONTRACT_EXPANSION",
    "A1_PROVIDER_EXPANSION",
    "A2_CONSUMER_INVERSION",
    "E1_DUAL_RUN_AND_TELEMETRY",
    "C2_LEGACY_CONTRACTION",
)

CROSS_BINDING_ID = "DTCR-XR-001"
RECEIPT_ID = "DTCR-R2-001"

# The contract-adapter capability classes this method admits, declared and not
# vendored, exactly as the R1 adapter law declares language adapters. Protobuf
# is the preferred candidate when it applies and is not universal; a class
# absent from this table cannot be reported as permitted by the method.
DECLARED_CONTRACT_ADAPTERS = ("PROTOBUF", "OPENAPI", "JSON_SCHEMA", "ASYNCAPI")


class Refused(Exception):
    """The run cannot be compiled without inventing evidence for a lane."""

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


def text(node: Any, key: str, where: str, minimum: int = 1) -> str:
    value = require(node, key, where)
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise Refused(
            "UNREADABLE_INPUT",
            f"{where}.{key} must be at least {minimum} characters of text, not {value!r}",
        )
    return value


def one_of(node: Any, key: str, where: str, admitted: tuple[str, ...], code: str) -> str:
    value = require(node, key, where)
    if value not in admitted:
        raise Refused(code, f"{where}.{key} is {value!r}; the values are {', '.join(admitted)}")
    return str(value)


def commit(value: Any, where: str) -> str:
    if not isinstance(value, str) or not EXACT_COMMIT.match(value):
        raise Refused(
            "STALE_SUBJECT",
            f"{where} is {value!r}: a branch, a tag or a moving label binds this run "
            f"to whatever that label pointed at when somebody read it",
        )
    return value


def digest(value: Any, where: str) -> str:
    if not isinstance(value, str) or not EXACT_DIGEST.match(value):
        raise Refused("UNREADABLE_INPUT", f"{where} must be a sha256 digest, not {value!r}")
    return value


def refuse_decision_fields(node: Any, where: str) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in DECISION_FIELDS:
                raise Refused(
                    "AUTOMATIC_CONTRACTION_OR_MERGE",
                    f"{where}.{key} carries a decision. Contraction, merge, release and "
                    f"publication are repository and Human authority; this protocol "
                    f"assembles the evidence they are decided on",
                )
            refuse_decision_fields(value, f"{where}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            refuse_decision_fields(value, f"{where}[{index}]")


# --------------------------------------------------------------------------
# the multi-repository subject
# --------------------------------------------------------------------------

def compile_binding(request: dict[str, Any]) -> dict[str, Any]:
    binding = request.get("binding")
    if not isinstance(binding, dict):
        raise Refused("UNREADABLE_INPUT", "request.binding is required")

    declared = binding.get("repositories")
    if not isinstance(declared, list) or len(declared) < 2:
        raise Refused(
            "SINGLE_REPOSITORY_SUBJECT",
            f"request.binding.repositories declares "
            f"{len(declared) if isinstance(declared, list) else 0} repository/ies. "
            f"A one-repository subject is an R1 refactor, which one commit can make "
            f"and which the R1 contracts already type",
        )

    rows: list[dict[str, Any]] = []
    for index, entry in enumerate(declared):
        where = f"request.binding.repositories[{index}]"
        identity = text(entry, "repository_binding_id", where, 2)
        if not BINDING_ID.match(identity):
            raise Refused("UNREADABLE_INPUT", f"{where}.repository_binding_id is {identity!r}")
        rows.append({
            "repository_binding_id": identity,
            "role": one_of(entry, "role", where, ROLES, "ROLE_SET_INCOMPLETE"),
            "subject_commit": commit(require(entry, "subject_commit", where), f"{where}.subject_commit"),
            "subject_tree": commit(require(entry, "subject_tree", where), f"{where}.subject_tree"),
            "ancestry_within_repository": sorted(
                commit(parent, f"{where}.ancestry_within_repository[{position}]")
                for position, parent in enumerate(
                    require(entry, "ancestry_within_repository", where)
                )
            ),
        })

    identities = [row["repository_binding_id"] for row in rows]
    if len(set(identities)) != len(identities):
        raise Refused(
            "DUPLICATE_REPOSITORY_BINDING",
            "two entries claim the same repository_binding_id, so a per-repository row "
            "downstream could not say which repository it is about",
        )
    for role in ROLES:
        if not any(row["role"] == role for row in rows):
            raise Refused(
                "ROLE_SET_INCOMPLETE",
                f"no repository holds the {role} role. An Expand and Contract run with "
                f"only one side of the contract is a change to one repository",
            )

    # FALSE_CROSS_REPO_GIT_PARENT. Two repositories share no object graph, so a
    # commit of one appearing in the ancestry of the other names an object that
    # repository cannot resolve -- and each side stays internally consistent, so
    # nothing but this comparison sees it.
    for row in rows:
        for other in rows:
            if other is row:
                continue
            foreign = {other["subject_commit"], *other["ancestry_within_repository"]}
            crossed = sorted(set(row["ancestry_within_repository"]) & foreign)
            if crossed:
                raise Refused(
                    "FALSE_CROSS_REPO_GIT_PARENT",
                    f"{row['repository_binding_id']} claims "
                    f"{', '.join(short(value) for value in crossed)} as ancestry, and that "
                    f"commit belongs to {other['repository_binding_id']}. Deployment order "
                    f"between two repositories is a process dependency; written as a git "
                    f"parent it produces a graph neither repository can resolve",
                )

    edges = binding.get("edges")
    if not isinstance(edges, list) or not edges:
        raise Refused(
            "UNREADABLE_INPUT",
            "request.binding.edges cannot be empty: an Expand and Contract run whose "
            "sides have no ordering between them is two unrelated changes",
        )
    known = set(identities)
    compiled_edges = []
    for index, edge in enumerate(edges):
        where = f"request.binding.edges[{index}]"
        source = text(edge, "from_repository_binding_id", where, 2)
        target = text(edge, "to_repository_binding_id", where, 2)
        for label, value in (("from", source), ("to", target)):
            if value not in known:
                raise Refused(
                    "UNREADABLE_INPUT",
                    f"{where}.{label}_repository_binding_id is {value!r}, which is not a "
                    f"declared repository of this run",
                )
        if source == target:
            raise Refused("UNREADABLE_INPUT", f"{where} points a repository at itself")
        compiled_edges.append({
            "from_repository_binding_id": source,
            "to_repository_binding_id": target,
            "edge_kind": "PROCESS_DEPENDENCY_NOT_GIT_PARENT",
        })

    return {
        "schema": "dtcr/refactor-r2-binding/v1",
        "binding_id": CROSS_BINDING_ID,
        "repositories": sorted(rows, key=lambda row: row["repository_binding_id"]),
        "edges": sorted(
            compiled_edges,
            key=lambda row: (row["from_repository_binding_id"], row["to_repository_binding_id"]),
        ),
        "establishes": {
            "git_ancestry_across_repositories": False,
            "single_atomic_commit": False,
            "simultaneous_deployment": False,
        },
    }


def short(value: str) -> str:
    return value[:12]


def role_of(binding: dict[str, Any], identity: str) -> str | None:
    for row in binding["repositories"]:
        if row["repository_binding_id"] == identity:
            return str(row["role"])
    return None


def bound(binding: dict[str, Any], node: Any, where: str, role: str) -> str:
    identity = text(node, "repository_binding_id", where, 2)
    actual = role_of(binding, identity)
    if actual is None:
        raise Refused(
            "UNREADABLE_INPUT",
            f"{where}.repository_binding_id is {identity!r}, which this run does not declare",
        )
    if actual != role:
        raise Refused(
            "ROLE_SET_INCOMPLETE",
            f"{where} binds {identity}, whose declared role is {actual} and not {role}",
        )
    return identity


# --------------------------------------------------------------------------
# C1 CONTRACT_EXPANSION
# --------------------------------------------------------------------------

def compile_contract(request: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    contract = request.get("contract")
    if not isinstance(contract, dict):
        raise Refused("UNREADABLE_INPUT", "request.contract is required")

    adapter = contract.get("adapter")
    if not isinstance(adapter, dict):
        raise Refused("UNREADABLE_INPUT", "request.contract.adapter is required")
    capability_class = one_of(
        adapter,
        "capability_class",
        "request.contract.adapter",
        DECLARED_CONTRACT_ADAPTERS,
        "UNSUPPORTED_CONTRACT_ADAPTER_PROMOTED_TO_SUPPORTED",
    )
    identity = bound(binding, contract, "request.contract", "PROVIDER")
    baseline = commit(
        require(contract, "baseline_commit", "request.contract"),
        "request.contract.baseline_commit",
    )

    runs = contract.get("compatibility_runs")
    if not isinstance(runs, list) or not runs:
        raise Refused(
            "UNREADABLE_INPUT",
            "request.contract.compatibility_runs cannot be empty. A contract expansion "
            "with no compatibility lane at all is not the same fact as one whose "
            "provider was unavailable, and only the second has an honest value",
        )
    compiled_runs = []
    for index, run in enumerate(runs):
        where = f"request.contract.compatibility_runs[{index}]"
        if not isinstance(run, dict) or run.get("schema") != "dtcr/contract-compatibility-result/v1":
            raise Refused(
                "UNREADABLE_INPUT",
                f"{where} must be a dtcr/contract-compatibility-result/v1 record; this "
                f"protocol consumes a compatibility verdict and never produces one",
            )
        result_id = text(run, "result_id", where, 2)
        if not RESULT_ID.match(result_id):
            raise Refused("UNREADABLE_INPUT", f"{where}.result_id is {result_id!r}")
        outcome = one_of(run, "outcome", where, OUTCOMES, "UNREADABLE_INPUT")
        run_baseline = commit(
            require(require(run, "baseline", where), "commit", f"{where}.baseline"),
            f"{where}.baseline.commit",
        )
        if run_baseline != baseline:
            raise Refused(
                "CONTRACT_BASELINE_MISMATCH",
                f"{where} was taken against {short(run_baseline)} and this run declares "
                f"{short(baseline)}. Two verdicts against two baselines are not two "
                f"readings of one change",
            )
        provider = require(run, "provider", where)
        compiled_runs.append({
            "result_id": result_id,
            "outcome": outcome,
            "config_digest": digest(
                require(provider, "config_digest", f"{where}.provider"),
                f"{where}.provider.config_digest",
            ),
            "ruleset_digest": digest(
                require(provider, "ruleset_digest", f"{where}.provider"),
                f"{where}.provider.ruleset_digest",
            ),
        })

    # BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING. The same artifacts under a
    # narrower ruleset produce a cleaner verdict, and the clean verdict is what
    # gets quoted. Compared inside one record so no second record is needed.
    for earlier, later in zip(compiled_runs, compiled_runs[1:]):
        if earlier["outcome"] != "BREAKING_CHANGE_DETECTED":
            continue
        if later["outcome"] != "NO_BREAKING_CHANGE_DETECTED":
            continue
        for label in ("ruleset_digest", "config_digest"):
            if earlier[label] != later[label]:
                raise Refused(
                    "BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING",
                    f"{earlier['result_id']} found a breaking change and "
                    f"{later['result_id']} did not, under a different {label} "
                    f"({short(earlier[label])} -> {short(later[label])}). The contract "
                    f"was not repaired; the rules that judge it were changed",
                )

    artifacts = contract.get("generated_artifacts")
    if not isinstance(artifacts, list):
        raise Refused(
            "UNREADABLE_INPUT",
            "request.contract.generated_artifacts is required. Declaring none is an "
            "empty list; omitting the key turns the stub-drift guard off without "
            "saying so",
        )
    compiled_artifacts = []
    by_name: dict[str, str] = {}
    for index, artifact in enumerate(artifacts):
        where = f"request.contract.generated_artifacts[{index}]"
        name = text(artifact, "artifact_name", where, 1)
        declared_digest = digest(
            require(artifact, "declared_digest", where), f"{where}.declared_digest"
        )
        owner = text(artifact, "repository_binding_id", where, 2)
        if role_of(binding, owner) is None:
            raise Refused("UNREADABLE_INPUT", f"{where}.repository_binding_id is {owner!r}")
        if by_name.setdefault(name, declared_digest) != declared_digest:
            raise Refused(
                "GENERATED_STUB_DRIFT",
                f"{name} is declared as {short(by_name[name])} by one repository and "
                f"{short(declared_digest)} by another. Two sides generating from one "
                f"contract and disagreeing about the bytes are two sides speaking "
                f"different protocols while both compile",
            )
        compiled_artifacts.append({
            "repository_binding_id": owner,
            "artifact_name": name,
            "declared_digest": declared_digest,
        })

    return {
        "repository_binding_id": identity,
        "adapter": {"capability_class": capability_class, "vendored": False},
        "baseline_commit": baseline,
        "outcome": compiled_runs[-1]["outcome"],
        "runs": compiled_runs,
        "generated_artifacts": sorted(
            compiled_artifacts,
            key=lambda row: (row["artifact_name"], row["repository_binding_id"]),
        ),
        "regeneration_comparison": "NOT_EXERCISED",
        "publication": compile_publication(contract.get("publication")),
    }


def compile_publication(publication: Any) -> dict[str, Any]:
    if not isinstance(publication, dict):
        raise Refused("UNREADABLE_INPUT", "request.contract.publication is required")
    where = "request.contract.publication"
    intent = one_of(publication, "intent", where, PUBLICATION_INTENTS, "UNREADABLE_INPUT")
    rights = require(publication, "rights", where)
    access = require(rights, "account_access", f"{where}.rights")
    if not isinstance(access, bool):
        raise Refused("UNREADABLE_INPUT", f"{where}.rights.account_access must be a boolean")
    admission = one_of(
        rights,
        "content_rights_admission",
        f"{where}.rights",
        AUTHORIZATIONS,
        "UNREADABLE_INPUT",
    )
    if access and admission != "ADMITTED":
        raise Refused(
            "BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS",
            "an account that can push to the registry is a capability. Whether these "
            "bytes may be published there is a permission somebody grants, and no "
            "amount of access is that grant",
        )
    compiled = {"intent": intent, "rights": {"account_access": access, "content_rights_admission": admission}}
    if intent != "PUBLISHED":
        for key in ("registry", "source_commit", "artifact_digest"):
            if key in publication:
                raise Refused(
                    "UNREADABLE_INPUT",
                    f"{where}.{key} is set on a record whose intent is {intent}",
                )
        return compiled
    # Every missing or inexact field here is one blocker and not three: a schema
    # nobody can trace back to a commit and a set of bytes is published all the
    # same, and everyone downstream builds against it.
    try:
        compiled["registry"] = text(publication, "registry", where, 2)
        compiled["source_commit"] = commit(
            require(publication, "source_commit", where), f"{where}.source_commit"
        )
        compiled["artifact_digest"] = digest(
            require(publication, "artifact_digest", where), f"{where}.artifact_digest"
        )
    except Refused as error:
        raise Refused(
            "SCHEMA_PUBLISHED_WITHOUT_EXACT_SOURCE",
            f"the contract is recorded as published and {error}. A published interface "
            f"that cannot be traced to the exact commit and the exact bytes it came from "
            f"is one everybody builds against and nobody can reproduce",
        ) from error
    return compiled


# --------------------------------------------------------------------------
# A1 PROVIDER_EXPANSION
# --------------------------------------------------------------------------

def compile_symbol(node: Any, where: str) -> dict[str, Any]:
    if not isinstance(node, dict):
        raise Refused("PROVIDER_COEXISTENCE_NOT_BOUND", f"{where} is required")
    symbol = require(node, "symbol", where)
    if not isinstance(symbol, str) or not symbol.strip():
        raise Refused(
            "PROVIDER_COEXISTENCE_NOT_BOUND",
            f"{where}.symbol is {symbol!r}. Coexistence is a statement about two named "
            f"symbols resolving at one commit; an unnamed one resolves to nothing",
        )
    return {
        "symbol": symbol,
        "index_id": text(node, "index_id", where, 2),
        "index_digest": digest(require(node, "index_digest", where), f"{where}.index_digest"),
        "completeness": one_of(
            node, "completeness", where, COMPLETENESS, "PROVIDER_COEXISTENCE_NOT_BOUND"
        ),
    }


def compile_provider(
    request: dict[str, Any], binding: dict[str, Any], observation_state: str
) -> dict[str, Any]:
    provider = request.get("provider")
    if not isinstance(provider, dict):
        raise Refused("UNREADABLE_INPUT", "request.provider is required")
    where = "request.provider"
    identity = bound(binding, provider, where, "PROVIDER")
    legacy = compile_symbol(provider.get("legacy_symbol"), f"{where}.legacy_symbol")
    new = compile_symbol(provider.get("new_symbol"), f"{where}.new_symbol")
    if legacy["symbol"] == new["symbol"]:
        raise Refused(
            "PROVIDER_COEXISTENCE_NOT_BOUND",
            f"both handlers are recorded as {legacy['symbol']!r}: one symbol resolving "
            f"once is not two surfaces standing beside each other",
        )

    removals = provider.get("removal_changesets")
    if not isinstance(removals, list):
        raise Refused(
            "UNREADABLE_INPUT",
            f"{where}.removal_changesets is required. Declaring none is an empty list; "
            f"omitting the key turns the removal guard off without saying so",
        )
    for index, changeset in enumerate(removals):
        row = f"{where}.removal_changesets[{index}]"
        reference = text(changeset, "change_unit_ref", row, 2)
        removed = require(changeset, "removed_symbols", row)
        if not isinstance(removed, list):
            raise Refused("UNREADABLE_INPUT", f"{row}.removed_symbols must be an array")
        collision = sorted({legacy["symbol"], new["symbol"]} & set(map(str, removed)))
        if collision:
            raise Refused(
                "PROVIDER_REMOVES_LEGACY_BEFORE_CONSUMER_MIGRATION",
                f"{reference} removes {', '.join(collision)} at the same head that is "
                f"supposed to serve it. Every consumer still on that surface fails at "
                f"the moment this ships, and the expansion it was paired with never "
                f"existed",
            )

    runtime = one_of(provider, "runtime", where, ("OBSERVED", "NOT_OBSERVED"), "UNREADABLE_INPUT")
    canary = provider.get("canary_receipt_ref")
    compiled = {
        "repository_binding_id": identity,
        "legacy_symbol": legacy,
        "new_symbol": new,
        "removal_changeset_absent": True,
        "runtime": runtime,
    }
    if runtime != "OBSERVED":
        if canary is not None:
            raise Refused(
                "UNREADABLE_INPUT",
                f"{where}.canary_receipt_ref is set on a lane recorded as {runtime}",
            )
        return compiled
    if not isinstance(canary, str) or len(canary.strip()) < 2:
        raise Refused(
            "RUNTIME_COEXISTENCE_DERIVED_FROM_STATIC_FACTS",
            "runtime coexistence is recorded as OBSERVED with no canary receipt behind "
            "it. Both symbols resolving at one commit is a fact about the tree; two "
            "surfaces serving at once is a fact about a deployment",
        )
    if observation_state != "OBSERVED":
        raise Refused(
            "RUNTIME_COEXISTENCE_DERIVED_FROM_STATIC_FACTS",
            f"runtime coexistence is OBSERVED while the dual-run lane is "
            f"{observation_state}. Nothing watched the deployment that would have seen it",
        )
    compiled["canary_receipt_ref"] = canary
    return compiled


# --------------------------------------------------------------------------
# A2 CONSUMER_INVERSION
# --------------------------------------------------------------------------

def compile_consumer(
    request: dict[str, Any], binding: dict[str, Any], observation_state: str
) -> dict[str, Any]:
    consumer = request.get("consumer")
    if not isinstance(consumer, dict):
        raise Refused("UNREADABLE_INPUT", "request.consumer is required")
    where = "request.consumer"
    identity = bound(binding, consumer, where, "CONSUMER")
    port = text(consumer, "port_ref", where, 2)
    if not PORT_ID.match(port):
        raise Refused("UNREADABLE_INPUT", f"{where}.port_ref is {port!r}")
    state = one_of(consumer, "migration_state", where, MIGRATION_STATES, "UNREADABLE_INPUT")

    compiled: dict[str, Any] = {
        "repository_binding_id": identity,
        "port_ref": port,
        "migration_state": state,
    }
    fallback = consumer.get("fallback")
    if fallback is None:
        if state == "MIGRATED":
            raise Refused(
                "CONSUMER_SWITCH_WITHOUT_FALLBACK",
                "the consumer switched to the new surface with no path back. A provider "
                "incident during the migration window becomes a consumer outage, and the "
                "bounded traffic migration the method is built around has no bound",
            )
        return compiled

    row = f"{where}.fallback"
    arrival_state = one_of(
        fallback, "arrival_state", row, ("EXERCISED", "NOT_EXERCISED"), "UNREADABLE_INPUT"
    )
    if arrival_state == "EXERCISED" and observation_state != "OBSERVED":
        raise Refused(
            "FALLBACK_ARRIVAL_WITHOUT_TRAFFIC",
            f"the fallback is recorded as exercised while the dual-run lane is "
            f"{observation_state}. With no traffic there was no arrival to trigger it, "
            f"and an untriggered branch is a branch that has never run",
        )
    compiled["fallback"] = {
        "trigger": text(fallback, "trigger", row, 8),
        "implementing_path": text(fallback, "implementing_path", row, 3),
        "arrival_state": arrival_state,
        "arrival_detail": text(fallback, "arrival_detail", row, 12),
    }
    return compiled


# --------------------------------------------------------------------------
# E1 DUAL_RUN_AND_TELEMETRY
# --------------------------------------------------------------------------

def compile_observation(request: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    observation = request.get("observation")
    if not isinstance(observation, dict):
        raise Refused("UNREADABLE_INPUT", "request.observation is required")
    where = "request.observation"
    state = one_of(observation, "state", where, OBSERVATION_STATES, "UNREADABLE_INPUT")
    absent_keys = sorted(
        key
        for key in (
            "split_ratio",
            "request_denominator",
            "environment_id",
            "provider_commit",
            "consumer_commit",
            "observation_window",
            "service_continuity",
        )
        if key in observation
    )
    if state != "OBSERVED":
        if absent_keys:
            raise Refused(
                "TELEMETRY_ABSENCE_PROMOTED_TO_SUCCESS",
                f"the dual-run lane is {state} and carries {', '.join(absent_keys)}. A "
                f"lane with no requests behind it has no split to report and no service "
                f"whose continuity could be described",
            )
        return {"state": state}

    # An OBSERVED lane missing any of its measurements is one refusal, not six.
    # A split ratio with no request count under it is a configuration setting
    # reported as a measurement, and the same is true of every field here.
    denominator = observation.get("request_denominator")
    try:
        if not isinstance(denominator, int) or isinstance(denominator, bool) or denominator < 1:
            raise Refused(
                "OBSERVATION_WITHOUT_DENOMINATOR",
                f"{where}.request_denominator is {denominator!r}",
            )
        compiled = {
            "state": state,
            "split_ratio": text(observation, "split_ratio", where, 3),
            "request_denominator": denominator,
            "environment_id": text(observation, "environment_id", where, 2),
            "provider_commit": commit(
                require(observation, "provider_commit", where), f"{where}.provider_commit"
            ),
            "consumer_commit": commit(
                require(observation, "consumer_commit", where), f"{where}.consumer_commit"
            ),
            "observation_window": text(observation, "observation_window", where, 4),
        }
    except Refused as error:
        raise Refused(
            "OBSERVATION_WITHOUT_DENOMINATOR",
            f"the dual-run lane is recorded as OBSERVED and {error}. An observation with "
            f"no denominator, no environment and no window is a sentence about traffic "
            f"rather than a measurement of it",
        ) from error
    commits = {row["subject_commit"] for row in binding["repositories"]}
    for label in ("provider_commit", "consumer_commit"):
        if compiled[label] not in commits:
            raise Refused(
                "OBSERVATION_WITHOUT_DENOMINATOR",
                f"{where}.{label} is {short(compiled[label])}, which is not a commit this "
                f"run binds. An observation of something else is not an observation of this",
            )
    if "service_continuity" in observation:
        compiled["service_continuity"] = text(observation, "service_continuity", where, 4)
    return compiled


def compile_idempotency(request: dict[str, Any], observation_state: str) -> dict[str, Any]:
    idempotency = request.get("idempotency")
    if not isinstance(idempotency, dict):
        raise Refused("UNREADABLE_INPUT", "request.idempotency is required")
    where = "request.idempotency"
    writes = require(idempotency, "writes_state", where)
    if not isinstance(writes, bool):
        raise Refused("UNREADABLE_INPUT", f"{where}.writes_state must be a boolean")
    mechanism = idempotency.get("mechanism")
    if not isinstance(mechanism, str) or len(mechanism.strip()) < 12:
        raise Refused(
            "DUAL_RUN_WITHOUT_IDEMPOTENCY",
            f"{where}.mechanism is {mechanism!r}. Running two implementations against one "
            f"arrival duplicates every write the second makes unless something "
            f"deduplicates them, and the name of the property is not the thing that "
            f"provides it",
        )
    arrival = idempotency.get("arrival")
    if not writes:
        if arrival is not None:
            raise Refused(
                "UNREADABLE_INPUT",
                f"{where}.arrival is set on a lane that declares it writes no state",
            )
        return {"writes_state": False, "mechanism": mechanism, "state": "NOT_APPLICABLE"}
    if arrival is None:
        return {
            "writes_state": True,
            "mechanism": mechanism,
            "state": "IDEMPOTENCY_DECLARED_NOT_EXERCISED",
        }
    if not isinstance(arrival, str) or len(arrival.strip()) < 8:
        raise Refused("UNREADABLE_INPUT", f"{where}.arrival is {arrival!r}")
    if observation_state != "OBSERVED":
        raise Refused(
            "DUAL_RUN_WITHOUT_IDEMPOTENCY",
            f"an arrival is named while the dual-run lane is {observation_state}. With no "
            f"observed traffic nothing arrived, so nothing exercised the mechanism and "
            f"the record would report a declaration as a run",
        )
    return {
        "writes_state": True,
        "mechanism": mechanism,
        "state": "EXERCISED",
        "arrival": arrival,
    }


# --------------------------------------------------------------------------
# C2 LEGACY_CONTRACTION
# --------------------------------------------------------------------------

def compile_contraction(request: dict[str, Any]) -> dict[str, Any]:
    contraction = request.get("contraction")
    if not isinstance(contraction, dict):
        raise Refused("UNREADABLE_INPUT", "request.contraction is required")
    where = "request.contraction"
    authorization = one_of(
        contraction, "authorization", where, AUTHORIZATIONS, "AUTOMATIC_CONTRACTION_OR_MERGE"
    )
    compiled: dict[str, Any] = {
        "authorization": authorization,
        "no_remaining_callers_proven": False,
    }
    if authorization == "ADMITTED":
        admitter = contraction.get("admitter")
        head = contraction.get("authorized_head")
        if not isinstance(admitter, str) or len(admitter.strip()) < 2:
            raise Refused(
                "AUTOMATIC_CONTRACTION_OR_MERGE",
                "the contraction is recorded as admitted with nobody named as the "
                "admitter. An authorization with no author is the run authorizing itself",
            )
        compiled["admitter"] = admitter
        compiled["authorized_head"] = commit(head, f"{where}.authorized_head")

    if "remaining_callers" not in contraction:
        for key in ("caller_index",):
            if key in contraction:
                raise Refused(
                    "UNREADABLE_INPUT",
                    f"{where}.{key} is set on a run that recorded no caller count",
                )
        return compiled

    remaining = contraction["remaining_callers"]
    if not isinstance(remaining, int) or isinstance(remaining, bool) or remaining < 0:
        raise Refused("UNREADABLE_INPUT", f"{where}.remaining_callers is {remaining!r}")
    compiled["remaining_callers"] = remaining

    index = contraction.get("caller_index")
    if index is None:
        if remaining == 0:
            raise Refused(
                "NO_REMAINING_CALLERS_IN_PARTIAL_INDEX",
                "a caller count of zero is recorded with no index behind it. Zero is the "
                "one count that reads as proof, and over an unnamed index it is a "
                "statement about whatever somebody happened to search",
            )
        return compiled
    row = f"{where}.caller_index"
    unresolved = require(index, "unresolved_symbols", row)
    if not isinstance(unresolved, int) or isinstance(unresolved, bool) or unresolved < 0:
        raise Refused("UNREADABLE_INPUT", f"{row}.unresolved_symbols is {unresolved!r}")
    out_of_index = require(index, "out_of_index_repositories", row)
    if not isinstance(out_of_index, list):
        raise Refused("UNREADABLE_INPUT", f"{row}.out_of_index_repositories must be an array")
    completeness = one_of(
        index, "completeness", row, COMPLETENESS, "NO_REMAINING_CALLERS_IN_PARTIAL_INDEX"
    )
    if remaining == 0 and completeness == "COMPLETE_FOR_ANALYSED_INPUTS" and (
        unresolved > 0 or out_of_index
    ):
        raise Refused(
            "NO_REMAINING_CALLERS_IN_PARTIAL_INDEX",
            f"the index reports itself complete while leaving {unresolved} symbol(s) "
            f"unresolved and {len(out_of_index)} repository/ies out of index. "
            f"COMPLETE_FOR_ANALYSED_INPUTS is a claim about what was parsed, and what "
            f"was not parsed was not cleared",
        )
    compiled["caller_index"] = {
        "index_id": text(index, "index_id", row, 2),
        "index_digest": digest(require(index, "index_digest", row), f"{row}.index_digest"),
        "completeness": completeness,
        "unresolved_symbols": unresolved,
        "out_of_index_repositories": sorted(set(map(str, out_of_index))),
    }
    return compiled


# --------------------------------------------------------------------------
# terminal
# --------------------------------------------------------------------------

def compile_rollback(request: dict[str, Any], binding: dict[str, Any]) -> list[dict[str, Any]] | None:
    rollback = request.get("rollback")
    if rollback is None:
        return None
    if not isinstance(rollback, list) or not rollback:
        raise Refused("UNREADABLE_INPUT", "request.rollback must be a non-empty array")
    declared = {row["repository_binding_id"] for row in binding["repositories"]}
    rows = []
    seen: set[str] = set()
    for index, entry in enumerate(rollback):
        where = f"request.rollback[{index}]"
        identity = text(entry, "repository_binding_id", where, 2)
        if identity not in declared:
            raise Refused("UNREADABLE_INPUT", f"{where}.repository_binding_id is {identity!r}")
        if identity in seen:
            raise Refused(
                "ROLLBACK_ROW_MISSING_FOR_BINDING",
                f"{identity} has two rollback rows, so the record says two things about "
                f"one repository",
            )
        seen.add(identity)
        rows.append({
            "repository_binding_id": identity,
            "restored_commit": commit(
                require(entry, "restored_commit", where), f"{where}.restored_commit"
            ),
            "disposition": one_of(entry, "disposition", where, DISPOSITIONS, "UNREADABLE_INPUT"),
            "reason": text(entry, "reason", where, 12),
        })
    missing = sorted(declared - seen)
    if missing:
        raise Refused(
            "ROLLBACK_ROW_MISSING_FOR_BINDING",
            f"{', '.join(missing)} has no rollback row. A stop that names one repository "
            f"and leaves the other unstated reads as a full revert, and the unstated side "
            f"is the one that is still expanded",
        )
    return sorted(rows, key=lambda row: row["repository_binding_id"])


def phases_entered(
    contract: dict[str, Any],
    consumer: dict[str, Any],
    observation: dict[str, Any],
    contraction: dict[str, Any],
) -> list[str]:
    """The phases this run entered, derived rather than declared.

    A phase is entered when its lane produced the evidence that phase exists to
    produce. C1 is entered by binding the contract to an exact baseline, which
    happens before any verdict; A1 needs that verdict to be clean, because an
    expansion shipped against a breaking contract is not an expansion. E1 needs
    observed traffic and C2 needs a Human, and both of those are absences at
    every head this compiler has ever run at.
    """
    entered = [C1]
    if contract["outcome"] != "NO_BREAKING_CHANGE_DETECTED":
        return entered
    entered.append(A1)
    if consumer["migration_state"] != "MIGRATED":
        return entered
    entered.append(A2)
    if observation["state"] != "OBSERVED":
        return entered
    entered.append(E1)
    if contraction["authorization"] != "ADMITTED":
        return entered
    entered.append(C2)
    return entered


def compile_receipt(
    binding: dict[str, Any],
    contract: dict[str, Any],
    provider: dict[str, Any],
    consumer: dict[str, Any],
    observation: dict[str, Any],
    idempotency: dict[str, Any],
    contraction: dict[str, Any],
    rollback: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    entered = phases_entered(contract, consumer, observation, contraction)

    blocked_on: list[str] = []
    if contract["outcome"] in ("PROVIDER_UNAVAILABLE", "NOT_APPLICABLE"):
        blocked_on.append("CONTRACT_VERDICT_ABSENT")
    if contract["outcome"] == "BREAKING_CHANGE_DETECTED":
        blocked_on.append("CONTRACT_BASELINE_BREAKING")
    if contract["generated_artifacts"]:
        blocked_on.append("GENERATED_ARTIFACT_REGENERATION_NOT_EXERCISED")
    if consumer["migration_state"] != "MIGRATED":
        blocked_on.append("CONSUMER_MIGRATION_INCOMPLETE")
    fallback = consumer.get("fallback")
    if fallback is not None and fallback["arrival_state"] != "EXERCISED":
        blocked_on.append("FALLBACK_NOT_EXERCISED")
    if observation["state"] != "OBSERVED":
        blocked_on.append("OBSERVATION_ABSENT")
    if idempotency["state"] == "IDEMPOTENCY_DECLARED_NOT_EXERCISED":
        blocked_on.append("IDEMPOTENCY_NOT_EXERCISED")
    index = contraction.get("caller_index")
    if index is not None and index["completeness"] != "COMPLETE_FOR_ANALYSED_INPUTS":
        blocked_on.append("CALLER_INDEX_PARTIAL")
    if contraction["authorization"] != "ADMITTED":
        blocked_on.append("CONTRACTION_NOT_AUTHORIZED")

    receipt: dict[str, Any] = {
        "schema": "dtcr/refactor-r2-receipt/v1",
        "receipt_id": RECEIPT_ID,
        "binding_ref": binding["binding_id"],
        "phases_entered": entered,
        "last_phase_entered": entered[-1],
        "contract": contract,
        "provider_coexistence": provider,
        "consumer": consumer,
        "observation": observation,
        "idempotency": idempotency,
        "contraction": contraction,
        "blocked_on": sorted(set(blocked_on)),
        "establishes": {
            "applied_on_real_codebase": "NOT_EXERCISED",
            "cross_repository_behavior_equivalence_proven": False,
            "service_interruption_absence_proven": False,
            "protocol_ready": False,
        },
        "authority": {
            "merge": False,
            "release": False,
            "production": False,
            "contraction": False,
            "schema_publication": False,
        },
    }

    if rollback is not None:
        receipt["rollback"] = rollback
        if not blocked_on:
            raise Refused(
                "ROLLBACK_WITHOUT_STOP",
                "every lane held and the run still recorded a rollback. A rollback nobody "
                "can point at a stopped lane for is a revert with a story attached",
            )
        every_row_reverted = all(row["disposition"] == "REVERTED" for row in rollback)
        receipt["terminal_state"] = "ROLLED_BACK" if every_row_reverted else "STOPPED_WITH_ROLLBACK"
        return receipt

    receipt["terminal_state"] = "BLOCKED" if blocked_on else "CANDIDATE_RECEIPT"
    return receipt


# --------------------------------------------------------------------------

def compile_r2(source: Path) -> dict[str, Any]:
    request = load(source)
    if request.get("schema") != "dtcr/refactor-r2-request/v1":
        raise Refused(
            "UNREADABLE_INPUT", "input must be a dtcr/refactor-r2-request/v1 artifact"
        )
    refuse_decision_fields(request, "request")

    binding = compile_binding(request)
    observation = compile_observation(request, binding)
    contract = compile_contract(request, binding)
    provider = compile_provider(request, binding, observation["state"])
    consumer = compile_consumer(request, binding, observation["state"])
    idempotency = compile_idempotency(request, observation["state"])
    contraction = compile_contraction(request)
    rollback = compile_rollback(request, binding)
    receipt = compile_receipt(
        binding, contract, provider, consumer, observation, idempotency, contraction, rollback
    )
    return {
        "schema": "dtcr/refactor-r2-projection/v1",
        "derived_from": source.name,
        "repository_binding": binding,
        "receipt": receipt,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile one cross-repository Expand and Contract (R2) run."
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
