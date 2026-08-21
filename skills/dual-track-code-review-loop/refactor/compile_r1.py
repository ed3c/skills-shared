#!/usr/bin/env python3
"""Compile one bounded single-repository architecture refactor (R1) run.

    VIOLATION_BOUND
    -> USAGE_SIGNATURE_EXTRACTED
    -> MINIMAL_PORT_PROPOSED
    -> CHANGESET_AND_LEASE_BOUND
    -> DOMAIN_DEPENDENCY_INVERTED
    -> COMPOSITION_ROOT_UPDATED
    -> TYPECHECK_AND_TEST_READBACK
    -> SCIP_REINDEXED
    -> SQLITE_ARCHITECTURE_ASSERTED
    -> GLOBAL_BEHAVIOR_ASSERTED
    -> CANDIDATE_RECEIPT | BLOCKED | ROLLED_BACK

The input is one `dtcr/refactor-r1-request/v1` document describing a run. The
output is the four artifacts that run emits -- usage signature, minimal port,
changeset/lease binding, R1 receipt -- serialised canonically (`sort_keys`,
two-space indent, one trailing newline), so `--check` byte-compares a committed
projection instead of trusting that somebody regenerated it.

What this compiler will not do, and why each is a refusal rather than a warning:

* It does not apply anything. No file in any repository is read, written or
  parsed here; a request describes a run, and `establishes.applied_on_real
  _codebase` is pinned false on every receipt it emits. A consumer canary that
  actually applies a proposal is a separate, unexercised lane.
* It vendors no language adapter. The adapter law declares capability classes
  per language -- syntax-tree rewrite, type-aware rewrite, compiler diagnostic
  -- and pins version, license, grammar and formatter behavior. Naming LibCST,
  ts-morph or OpenRewrite here would make this file claim a rewrite capability
  it does not have, so an adapter is a declaration with `vendored` pinned false,
  and a run whose adapter has no implementation available terminates BLOCKED on
  ADAPTER_BLOCKED_ON_PROVIDER rather than reporting a green it never earned.
* It does not merge. `merge_admission` is single-valued and any decision-shaped
  field anywhere in the request is refused by name, because a field that is
  ignored travels in the input forever.

Three terminals and no fourth. BLOCKED names which link of the chain was never
reached; ROLLED_BACK is the honest exit when the change was applied and a
readback lane disagreed; CANDIDATE_RECEIPT requires every lane to have run and
agreed, and is still only a candidate -- merge is repository and Human
authority.

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
REPO_RELATIVE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*$")

# The adapter law as declared capability classes. No implementation is vendored:
# this table says which class of tooling a language has an adapter *shape* for,
# and a language absent from it cannot be reported as supported.
DECLARED_LANGUAGE_ADAPTERS = {
    "python": ("SYNTAX_TREE_REWRITE", "TYPE_AWARE_REWRITE", "COMPILER_DIAGNOSTIC"),
    "typescript": ("SYNTAX_TREE_REWRITE", "TYPE_AWARE_REWRITE", "COMPILER_DIAGNOSTIC"),
    "java": ("SYNTAX_TREE_REWRITE", "COMPILER_DIAGNOSTIC"),
    "kotlin": ("SYNTAX_TREE_REWRITE", "COMPILER_DIAGNOSTIC"),
    "go": ("TYPE_AWARE_REWRITE", "COMPILER_DIAGNOSTIC"),
    "c": ("COMPILER_DIAGNOSTIC",),
    "cpp": ("COMPILER_DIAGNOSTIC",),
    "swift": ("SYNTAX_TREE_REWRITE", "COMPILER_DIAGNOSTIC"),
}
REQUIRED_PINS = ("tool_version", "license_id", "grammar_or_dialect", "formatter_behavior")

# Decision-shaped keys. A request may not carry the decision it exists to ask a
# person for, at any depth.
DECISION_FIELDS = ("decision", "decided_by", "approved", "auto_merge", "merged", "verdict")

STATES = (
    "VIOLATION_BOUND",
    "USAGE_SIGNATURE_EXTRACTED",
    "MINIMAL_PORT_PROPOSED",
    "CHANGESET_AND_LEASE_BOUND",
    "DOMAIN_DEPENDENCY_INVERTED",
    "COMPOSITION_ROOT_UPDATED",
    "TYPECHECK_AND_TEST_READBACK",
    "SCIP_REINDEXED",
    "SQLITE_ARCHITECTURE_ASSERTED",
    "GLOBAL_BEHAVIOR_ASSERTED",
)
MEMBER_KINDS = ("METHOD", "TYPE", "FIELD", "CONSTRUCTOR")
OWNING_LAYERS = ("DOMAIN", "APPLICATION")

SIGNATURE_ID = "DTCR-US-001"
PORT_ID = "DTCR-PT-001"
BINDING_ID = "DTCR-CL-001"
RECEIPT_ID = "DTCR-R1-001"


class Refused(Exception):
    """The run cannot be compiled without inventing evidence for a state.

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
                    "AUTOMATIC_MERGE",
                    f"{where}.{key} carries a decision. This protocol proposes a "
                    f"merge candidate; merge, approval and rollback admission are "
                    f"repository and Human authority",
                )
            refuse_decision_fields(value, f"{where}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            refuse_decision_fields(value, f"{where}[{index}]")


def exact_subject(subject: Any, where: str) -> dict[str, str]:
    if not isinstance(subject, dict):
        raise Refused("STALE_SUBJECT", f"{where} must be an object")
    for key in ("repository_binding_id", "subject_commit", "subject_tree"):
        if key not in subject:
            raise Refused("STALE_SUBJECT", f"{where}.{key} is required")
    for key in ("subject_commit", "subject_tree"):
        if not EXACT_COMMIT.match(str(subject[key])):
            raise Refused(
                "STALE_SUBJECT",
                f"{where}.{key} is {subject[key]!r}: a branch, a tag or a moving "
                f"label binds the refactor to whatever that label pointed at",
            )
    return {key: subject[key] for key in ("repository_binding_id", "subject_commit", "subject_tree")}


# --------------------------------------------------------------------------
# VIOLATION_BOUND -> USAGE_SIGNATURE_EXTRACTED
# --------------------------------------------------------------------------

def compile_usage_signature(request: dict[str, Any], subject: dict[str, str]) -> dict[str, Any]:
    adapter = compile_adapter(request.get("adapter"))

    call_sites = request.get("call_sites")
    if not isinstance(call_sites, list) or not call_sites:
        raise Refused("UNREADABLE_INPUT", "request.call_sites is required and cannot be empty")

    members: dict[tuple[str, str], list[str]] = {}
    unresolved: list[str] = []
    for index, site in enumerate(call_sites):
        ref = str(require(site, "call_site_ref", f"request.call_sites[{index}]"))
        member = str(require(site, "member", f"request.call_sites[{index}]"))
        kind = str(require(site, "member_kind", f"request.call_sites[{index}]"))
        if kind not in MEMBER_KINDS:
            raise Refused(
                "UNREADABLE_INPUT",
                f"request.call_sites[{index}].member_kind is {kind!r}, which is not "
                f"one of {', '.join(MEMBER_KINDS)}",
            )
        if not site.get("resolved"):
            unresolved.append(ref)
            continue
        members.setdefault((member, kind), []).append(ref)

    if not members:
        raise Refused(
            "USAGE_SET_INCOMPLETE",
            "no call site resolved to a consumed member, so the usage set is empty "
            "and a Port of any width would satisfy it",
        )

    completeness = "PARTIAL_LOWER_BOUND" if unresolved else "COMPLETE_FOR_RESOLVED_CALL_SITES"
    claim = request.get("usage_extraction_claim")
    if claim != completeness:
        raise Refused(
            "USAGE_SET_INCOMPLETE",
            f"the request claims {claim!r} over {len(call_sites)} call sites of which "
            f"{len(unresolved)} did not resolve; this extraction is {completeness}. "
            f"An unresolved call site may consume a member nobody listed",
        )

    return {
        "schema": "dtcr/refactor-usage-signature/v1",
        "signature_id": SIGNATURE_ID,
        "subject": dict(subject),
        "violation_ref": str(require(request, "violation_ref", "request")),
        "provider_symbol": str(require(request, "provider_symbol", "request")),
        "adapter": adapter,
        "consumed_members": [
            {
                "member": member,
                "member_kind": kind,
                "call_site_refs": sorted(refs),
            }
            for (member, kind), refs in sorted(members.items())
        ],
        "extraction": {
            "call_sites_declared": len(call_sites),
            "call_sites_resolved": len(call_sites) - len(unresolved),
            "unresolved_call_site_refs": sorted(unresolved),
            "completeness": completeness,
        },
        "establishes": {
            "provider_surface_complete": False,
            "rewrite_applied": False,
        },
    }


def compile_adapter(adapter: Any) -> dict[str, Any]:
    if not isinstance(adapter, dict):
        raise Refused("UNREADABLE_INPUT", "request.adapter is required")
    language = str(require(adapter, "language", "request.adapter"))
    capability = str(require(adapter, "capability_class", "request.adapter"))
    declared = DECLARED_LANGUAGE_ADAPTERS.get(language)
    if declared is None:
        raise Refused(
            "UNSUPPORTED_LANGUAGE_PROMOTED_TO_SUPPORTED",
            f"{language!r} has no declared adapter capability class. Support means a "
            f"class is declared for the language, not that one could be written",
        )
    if capability not in declared:
        raise Refused(
            "UNSUPPORTED_LANGUAGE_PROMOTED_TO_SUPPORTED",
            f"{language!r} declares {', '.join(declared)} and this request claims "
            f"{capability!r}",
        )

    pins = adapter.get("pins")
    if not isinstance(pins, dict):
        raise Refused("ADAPTER_PINS_INCOMPLETE", "request.adapter.pins is required")
    for key in REQUIRED_PINS:
        if not str(pins.get(key) or "").strip():
            raise Refused(
                "ADAPTER_PINS_INCOMPLETE",
                f"request.adapter.pins.{key} is empty. An unpinned {key} makes the "
                f"same request produce a different diff on a different host",
            )

    state = adapter.get("provider_state")
    if state not in ("DECLARED_NOT_VENDORED", "BLOCKED_ON_PROVIDER"):
        raise Refused(
            "UNREADABLE_INPUT",
            f"request.adapter.provider_state is {state!r}; the two states are "
            f"DECLARED_NOT_VENDORED and BLOCKED_ON_PROVIDER, and there is no "
            f"EXERCISED because no adapter implementation ships behind this protocol",
        )

    return {
        "adapter_binding_id": str(require(adapter, "adapter_binding_id", "request.adapter")),
        "capability_class": capability,
        "language": language,
        "language_support": "SUPPORTED_BY_DECLARED_ADAPTER",
        "provider_state": state,
        "vendored": False,
        "pins": {key: str(pins[key]) for key in REQUIRED_PINS},
    }


# --------------------------------------------------------------------------
# MINIMAL_PORT_PROPOSED
# --------------------------------------------------------------------------

def compile_minimal_port(
    request: dict[str, Any], subject: dict[str, str], signature: dict[str, Any]
) -> dict[str, Any]:
    port = request.get("port")
    if not isinstance(port, dict):
        raise Refused("UNREADABLE_INPUT", "request.port is required")

    layer = port.get("owning_layer")
    if layer not in OWNING_LAYERS:
        raise Refused(
            "PORT_PLACED_OUTSIDE_OWNING_MODULE",
            f"request.port.owning_layer is {layer!r}. A Port outside the module that "
            f"consumes it leaves the high-level module importing downward to reach it",
        )

    consumed = {row["member"]: row for row in signature["consumed_members"]}
    declared_members = port.get("members")
    if not isinstance(declared_members, list) or not declared_members:
        raise Refused("UNREADABLE_INPUT", "request.port.members is required and cannot be empty")

    widened = sorted(set(map(str, declared_members)) - set(consumed))
    if widened:
        raise Refused(
            "PORT_WIDENED_WITH_UNUSED_PROVIDER_SURFACE",
            f"the Port declares {', '.join(widened)}, which no call site consumes. "
            f"Cloning the provider surface into the domain satisfies the dependency "
            f"rule and keeps the coupling",
        )

    remaining = port.get("concrete_imports_remaining")
    if not isinstance(remaining, list):
        raise Refused("UNREADABLE_INPUT", "request.port.concrete_imports_remaining is required")
    if remaining:
        raise Refused(
            "INJECTION_INCOMPLETE",
            f"{len(remaining)} concrete import(s) survive the injection, so the "
            f"forbidden edge survives the change that reports removing it: "
            f"{', '.join(map(str, sorted(remaining)))}",
        )

    replaced = port.get("construction_sites_replaced")
    if not isinstance(replaced, list) or not replaced:
        raise Refused(
            "UNREADABLE_INPUT",
            "request.port.construction_sites_replaced is required and cannot be empty: "
            "a Port nobody injects is a second way to reach the same concrete class",
        )

    return {
        "schema": "dtcr/refactor-minimal-port/v1",
        "port_id": PORT_ID,
        "signature_ref": SIGNATURE_ID,
        "subject": dict(subject),
        "owning_layer": layer,
        "port_members": [
            {
                "member": member,
                "member_kind": consumed[member]["member_kind"],
                "justified_by_call_site_refs": list(consumed[member]["call_site_refs"]),
            }
            for member in sorted(set(map(str, declared_members)))
        ],
        "unused_provider_members": [],
        "injection": {
            "construction_sites_replaced": sorted(set(map(str, replaced))),
            "concrete_imports_remaining": [],
        },
        "establishes": {
            "behavior_preserved": False,
            "applied": False,
        },
    }


# --------------------------------------------------------------------------
# CHANGESET_AND_LEASE_BOUND
# --------------------------------------------------------------------------

def within_lease(path: str, lease_paths: list[str]) -> bool:
    for lease in lease_paths:
        prefix = lease if lease.endswith("/") else lease + "/"
        if path == lease or path.startswith(prefix):
            return True
    return False


def compile_changeset(request: dict[str, Any], subject: dict[str, str]) -> dict[str, Any]:
    changeset = request.get("changeset")
    if not isinstance(changeset, dict):
        raise Refused("UNREADABLE_INPUT", "request.changeset is required")

    writers = sorted(set(map(str, changeset.get("lease_writers") or [])))
    if len(writers) != 1:
        raise Refused(
            "SECOND_CHANGESET_WRITER",
            f"{len(writers)} lease writers declared ({', '.join(writers) or 'none'}). "
            f"One lease has one writer; two make the changeset a record of whoever "
            f"wrote last",
        )

    lease_paths = sorted(set(map(str, changeset.get("lease_paths") or [])))
    if not lease_paths:
        raise Refused("UNREADABLE_INPUT", "request.changeset.lease_paths cannot be empty")
    for lease in lease_paths:
        if not REPO_RELATIVE.match(lease.rstrip("/")):
            raise Refused(
                "PATH_LEASE_ESCAPE",
                f"lease path {lease!r} is not repository-relative",
            )

    changed = sorted(set(map(str, changeset.get("changed_paths") or [])))
    if not changed:
        raise Refused(
            "UNREADABLE_INPUT",
            "request.changeset.changed_paths cannot be empty: a refactor that changed "
            "nothing is NO_CHANGE_WARRANTED, which is a different artifact",
        )
    for path in changed:
        if not REPO_RELATIVE.match(path) or ".." in path.split("/"):
            raise Refused(
                "PATH_LEASE_ESCAPE",
                f"changed path {path!r} is not repository-relative",
            )
        if not within_lease(path, lease_paths):
            raise Refused(
                "PATH_LEASE_ESCAPE",
                f"changed path {path!r} is outside the declared lease "
                f"({', '.join(lease_paths)}). A path nobody leased is a path somebody "
                f"else is writing",
            )

    # Required, not defaulted. A request that omits the key would skip the
    # generated-code check silently, and a check nobody ran reports the same
    # green as one that passed. An empty list is a claim; a missing key is not.
    if "generated_paths" not in changeset:
        raise Refused(
            "UNREADABLE_INPUT",
            "request.changeset.generated_paths is required. Declaring none is an "
            "empty list; omitting the key would turn the generated-code guard off "
            "without saying so",
        )
    generated = sorted(set(map(str, changeset["generated_paths"])))
    edited_generated = sorted(set(changed) & set(generated))
    if edited_generated:
        raise Refused(
            "GENERATED_CODE_EDITED_DIRECTLY",
            f"{', '.join(edited_generated)} is generated. The next generation reverts "
            f"the edit without failing anything in between",
        )

    frozen = changeset.get("behavior_tests")
    if not isinstance(frozen, list) or not frozen:
        raise Refused(
            "BEHAVIOR_TEST_ABSENT",
            "request.changeset.behavior_tests is empty: with no frozen oracle, "
            "behavior after the change is compared against nothing",
        )
    rows = []
    for index, test in enumerate(frozen):
        where = f"request.changeset.behavior_tests[{index}]"
        ref = str(require(test, "test_ref", where))
        pre = str(require(test, "pre_digest", where))
        post = str(require(test, "post_digest", where))
        for label, digest in (("pre_digest", pre), ("post_digest", post)):
            if not EXACT_DIGEST.match(digest):
                raise Refused("UNREADABLE_INPUT", f"{where}.{label} must be a sha256 digest")
        if pre != post:
            raise Refused(
                "BEHAVIOR_TEST_MUTATED",
                f"{ref} was rewritten by the change it is supposed to judge "
                f"({pre[:12]} -> {post[:12]}). A test the change edited measures the "
                f"change",
            )
        rows.append({"test_ref": ref, "pre_digest": pre, "post_digest": post})

    roots = changeset.get("composition_roots")
    if not isinstance(roots, list) or not roots:
        raise Refused(
            "COMPOSITION_ROOT_NOT_FOUND",
            "no composition root was bound, so the concrete implementation is wired "
            "somewhere nobody named",
        )
    admitted_roots = []
    for index, root in enumerate(roots):
        where = f"request.changeset.composition_roots[{index}]"
        root_path = str(require(root, "root_path", where))
        if root.get("admitted") is not True:
            raise Refused(
                "COMPOSITION_ROOT_NOT_FOUND",
                f"{root_path} is wired by this change and is not an admitted "
                f"composition root of this subject",
            )
        if not REPO_RELATIVE.match(root_path):
            raise Refused("PATH_LEASE_ESCAPE", f"composition root {root_path!r} is not repository-relative")
        admitted_roots.append({"root_path": root_path, "admitted": True})

    public_api = changeset.get("public_api")
    if not isinstance(public_api, dict) or "changed" not in public_api:
        raise Refused("UNREADABLE_INPUT", "request.changeset.public_api.changed is required")
    admission = public_api.get("contract_owner_admission")
    if admission not in ("NOT_REQUIRED", "ADMITTED"):
        raise Refused(
            "UNREADABLE_INPUT",
            f"request.changeset.public_api.contract_owner_admission is {admission!r}",
        )
    if public_api["changed"] and admission != "ADMITTED":
        raise Refused(
            "PUBLIC_API_CHANGED_WITHOUT_CONTRACT_OWNER",
            "the change alters a published interface and no contract owner admitted "
            "it. The break lands on whoever builds against it next",
        )

    admission_value = changeset.get("merge_admission")
    if admission_value != "HUMAN_ADMIT_REQUIRED":
        raise Refused(
            "AUTOMATIC_MERGE",
            f"request.changeset.merge_admission is {admission_value!r}. A green suite "
            f"and a clean graph are inputs to a merge decision, never the decision",
        )

    return {
        "schema": "dtcr/refactor-changeset-lease/v1",
        "binding_id": BINDING_ID,
        "port_ref": PORT_ID,
        "subject": dict(subject),
        "lease": {
            "lease_paths": lease_paths,
            "lease_writers": writers,
            "escaped_paths": [],
        },
        "changed_paths": changed,
        "generated_paths_touched": [],
        "behavior_tests": {
            "frozen": sorted(rows, key=lambda row: row["test_ref"]),
            "mutated_test_refs": [],
        },
        "composition_roots": sorted(admitted_roots, key=lambda row: row["root_path"]),
        "public_api": {
            "changed": bool(public_api["changed"]),
            "contract_owner_admission": admission,
        },
        "merge_admission": "HUMAN_ADMIT_REQUIRED",
    }


# --------------------------------------------------------------------------
# readback -> CANDIDATE_RECEIPT | BLOCKED | ROLLED_BACK
# --------------------------------------------------------------------------

def compile_receipt(
    request: dict[str, Any],
    subject: dict[str, str],
    signature: dict[str, Any],
    changeset: dict[str, Any],
) -> dict[str, Any]:
    readback = request.get("readback")
    if not isinstance(readback, dict):
        raise Refused("UNREADABLE_INPUT", "request.readback is required")

    typecheck = readback.get("typecheck")
    if typecheck not in ("PASS", "FAIL", "NOT_RUN"):
        raise Refused("UNREADABLE_INPUT", f"request.readback.typecheck is {typecheck!r}")
    tests = readback.get("behavior_tests")
    if not isinstance(tests, dict):
        raise Refused("UNREADABLE_INPUT", "request.readback.behavior_tests is required")
    state = tests.get("state")
    if state not in ("PASS", "FAIL", "NOT_RUN"):
        raise Refused("UNREADABLE_INPUT", f"request.readback.behavior_tests.state is {state!r}")
    total = tests.get("total")
    passed = tests.get("passed")
    if not isinstance(total, int) or total < 1 or not isinstance(passed, int) or passed < 0:
        raise Refused(
            "BEHAVIOR_DENOMINATOR_ABSENT",
            f"request.readback.behavior_tests declares passed={passed!r} of "
            f"total={total!r}. ONE_GREEN_TEST != FULL_DENOMINATOR, and a passed count "
            f"with no total behind it is a green over an unknown set",
        )
    if passed > total:
        raise Refused(
            "BEHAVIOR_DENOMINATOR_ABSENT",
            f"{passed} tests passed out of a declared {total}",
        )
    reindex = readback.get("reindex_state")
    if reindex not in ("REINDEXED", "NOT_REINDEXED"):
        raise Refused("UNREADABLE_INPUT", f"request.readback.reindex_state is {reindex!r}")
    edges = readback.get("forbidden_edge_count")
    cycles = readback.get("new_cycles")
    for label, value in (("forbidden_edge_count", edges), ("new_cycles", cycles)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise Refused("UNREADABLE_INPUT", f"request.readback.{label} is {value!r}")

    blocked_on: list[str] = []
    if signature["adapter"]["provider_state"] == "BLOCKED_ON_PROVIDER":
        blocked_on.append("ADAPTER_BLOCKED_ON_PROVIDER")
    if signature["extraction"]["completeness"] == "PARTIAL_LOWER_BOUND":
        blocked_on.append("USAGE_SET_PARTIAL")
    if typecheck == "NOT_RUN":
        blocked_on.append("TYPECHECK_NOT_RUN")
    if typecheck == "FAIL":
        blocked_on.append("TYPECHECK_FAILED")
    if state == "NOT_RUN":
        blocked_on.append("BEHAVIOR_ORACLE_NOT_RUN")
    if state == "FAIL":
        blocked_on.append("BEHAVIOR_ORACLE_FAILED")
    if reindex == "NOT_REINDEXED":
        blocked_on.append("SEMANTIC_INDEX_NOT_REBUILT")
    if edges > 0:
        blocked_on.append("FORBIDDEN_EDGE_STILL_PRESENT")

    rollback = compile_rollback(request.get("rollback"))
    regressed = state == "FAIL" or cycles > 0

    receipt: dict[str, Any] = {
        "schema": "dtcr/refactor-r1-receipt/v1",
        "receipt_id": RECEIPT_ID,
        "changeset_ref": changeset["binding_id"],
        "subject": dict(subject),
        "states_entered": states_entered(
            signature["adapter"]["provider_state"], typecheck, state, reindex
        ),
        "readback": {
            "typecheck": typecheck,
            "behavior_tests": {"state": state, "passed": passed, "total": total},
            "reindex_state": reindex,
            "forbidden_edge_count": edges,
            "new_cycles": cycles,
        },
        "establishes": {
            "applied_on_real_codebase": False,
            "behavior_equivalence_proven": False,
            "protocol_ready": False,
        },
        "authority": {"merge": False, "release": False, "production": False},
    }

    if regressed:
        if rollback is None:
            if cycles > 0:
                raise Refused(
                    "NEW_CYCLE_OR_LAYER_VIOLATION",
                    f"the readback found {cycles} new cycle(s). Removing one named "
                    f"violation by introducing an unnamed one is not a candidate, and "
                    f"no rollback was recorded",
                )
            raise Refused(
                "FORBIDDEN_EDGE_ZERO_BUT_BEHAVIOR_FAILED",
                f"the architecture lane reports {edges} forbidden edge(s) and the "
                f"behavior lane failed {total - passed} of {total} frozen tests. A "
                f"graph query that finds no illegal edge says nothing about whether "
                f"the program still does what it did; without a rollback record this "
                f"run has no honest terminal",
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
            "a rollback record was supplied for a run whose readback lanes all held. "
            "A rollback nobody can point at a failure for is a revert with a story",
        )

    if blocked_on:
        receipt["terminal_state"] = "BLOCKED"
        receipt["blocked_on"] = sorted(set(blocked_on))
        return receipt

    receipt["terminal_state"] = "CANDIDATE_RECEIPT"
    receipt["blocked_on"] = []
    return receipt


def compile_rollback(rollback: Any) -> dict[str, Any] | None:
    if rollback is None:
        return None
    if not isinstance(rollback, dict):
        raise Refused("UNREADABLE_INPUT", "request.rollback must be an object")
    restored = str(require(rollback, "restored_commit", "request.rollback"))
    if not EXACT_COMMIT.match(restored):
        raise Refused(
            "STALE_SUBJECT",
            f"request.rollback.restored_commit is {restored!r}: a rollback to a moving "
            f"label does not say what the tree was restored to",
        )
    # No `reason` field: the readback block already carries which lane failed, and
    # a second copy of that fact is a copy that can disagree with the first.
    if rollback.get("applied_change_reverted") is not True:
        raise Refused(
            "ROLLBACK_NOT_REVERTED",
            "the rollback record says the applied change was not reverted, which is a "
            "failed run wearing a reassuring name",
        )
    return {
        "restored_commit": restored,
        "applied_change_reverted": True,
    }


def states_entered(provider_state: str, typecheck: str, behavior: str, reindex: str) -> list[str]:
    """The states this run actually entered, in protocol order.

    Derived rather than declared: a run that stopped at the readback and lists
    every state is reporting the diagram instead of the run. The adapter gate is
    first because it is the one that most often makes the difference invisible --
    with no adapter implementation available nothing was rewritten, so neither
    the inversion nor the composition-root update was ever entered, however
    complete the proposal upstream of them looks.
    """
    entered = list(STATES[:4])
    if provider_state == "BLOCKED_ON_PROVIDER":
        return entered
    entered.extend(("DOMAIN_DEPENDENCY_INVERTED", "COMPOSITION_ROOT_UPDATED"))
    if typecheck == "NOT_RUN" and behavior == "NOT_RUN":
        return entered
    entered.append("TYPECHECK_AND_TEST_READBACK")
    if reindex == "REINDEXED":
        entered.append("SCIP_REINDEXED")
        entered.append("SQLITE_ARCHITECTURE_ASSERTED")
    if behavior != "NOT_RUN":
        entered.append("GLOBAL_BEHAVIOR_ASSERTED")
    return entered


# --------------------------------------------------------------------------

def compile_r1(source: Path) -> dict[str, Any]:
    request = load(source)
    if request.get("schema") != "dtcr/refactor-r1-request/v1":
        raise Refused(
            "UNREADABLE_INPUT", "input must be a dtcr/refactor-r1-request/v1 artifact"
        )
    refuse_decision_fields(request, "request")

    subject = exact_subject(request.get("subject"), "request.subject")
    signature = compile_usage_signature(request, subject)
    port = compile_minimal_port(request, subject, signature)
    changeset = compile_changeset(request, subject)
    receipt = compile_receipt(request, subject, signature, changeset)
    return {
        "schema": "dtcr/refactor-r1-projection/v1",
        "derived_from": source.name,
        "usage_signature": signature,
        "minimal_port": port,
        "changeset_lease": changeset,
        "receipt": receipt,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile one bounded R1 refactor run.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="byte-compare --out against a fresh compilation instead of writing it",
    )
    args = parser.parse_args()

    try:
        rendered = canonical(compile_r1(args.input))
    except Refused as error:
        print(f"DTCR-R1-RED {error}", file=sys.stderr)
        return 2
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        print(f"DTCR-R1-UNUSABLE malformed request: {error!r}", file=sys.stderr)
        return 64

    if args.out is None:
        sys.stdout.write(rendered)
        return 0
    if args.check:
        try:
            current = args.out.read_text(encoding="utf-8")
        except OSError as error:
            print(f"DTCR-R1-RED missing projection {args.out}: {error}", file=sys.stderr)
            return 2
        if current != rendered:
            print(
                f"DTCR-R1-RED {args.out} is not what {args.input.name} compiles to; "
                f"regenerate it rather than editing it",
                file=sys.stderr,
            )
            return 2
        print(f"DTCR-R1-GREEN projection is current: {args.out.name}")
        return 0
    args.out.write_text(rendered, encoding="utf-8")
    print(f"DTCR-R1-GREEN wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
