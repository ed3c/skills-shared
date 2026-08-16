#!/usr/bin/env python3
"""Validate a Tech Lead fan-out contract before any branch or worktree exists.

The Planner owns the contract, the branch graph, the context subject, the
budgets and the acceptance oracles. Workers own only their leased surfaces.
Everything this checker refuses is a shape that looks like parallel work and is
not: competitors judged against different context, siblings writing the same
file, a child branch whose "dependency" is only that someone stacked it, a
convergence that starts before its inputs exist, and a plan that quietly grants
itself the semantic-merge decision a Human owns.

Each refusal carries its own code, because a single generic failure tells the
Planner that the plan is wrong without telling it which law it broke.

Exit codes: 0 pass, 2 contract failure, 64 input/usage, 70 evaluator failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "git-town-tech-lead-fanout/v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

MODES = {"TOURNAMENT", "COOPERATIVE", "SERIAL_STACK", "HYBRID"}
FOCUSES = {"minimal-diff", "architecture-types", "defensive-boundaries", "performance-security"}

REQUIRED_HUMAN = {
    "semantic_conflict_resolution",
    "winner_admission",
    "merge_or_ship",
    "release_promotion",
}

# Retired provider. It may appear as historical prose; it may never be a
# provider a Worker's context depends on.
FORBIDDEN_PROVIDERS = {"code-graph-rag", "code_graph_rag", "codegraphrag"}

# States that mean "this lane did not run". Reporting one of them is honest;
# rewriting one into PASS is the laundering this checker exists to catch.
UNEXERCISED = {"ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED", "SKIPPED_BY_POLICY"}


class Failure(Exception):
    """Contract violation. Carries the code that names the broken law."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def fail(code: str, detail: str) -> None:
    raise Failure(code, detail)


def path_overlap(left: str, right: str) -> bool:
    """True when two leases can reach the same file.

    Globs are compared on the literal prefix before the first wildcard, so
    `skills/a/**` and `skills/a/b.py` collide, and `skills/a` and `skills/ab`
    do not.
    """
    a = left.split("*", 1)[0].rstrip("/")
    b = right.split("*", 1)[0].rstrip("/")
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def check_structure(data: Any) -> None:
    if not isinstance(data, dict):
        fail("CONTRACT_MALFORMED", "contract must be a JSON object")
    if data.get("schema_version") != SCHEMA_VERSION:
        fail("CONTRACT_MALFORMED", f"schema_version must be {SCHEMA_VERSION}")
    if data.get("mode") not in MODES:
        fail("CONTRACT_MALFORMED", f"mode must be one of {sorted(MODES)}")
    workers = data.get("workers")
    if not isinstance(workers, list) or not workers:
        fail("CONTRACT_MALFORMED", "workers must be a non-empty array")
    ids: set[str] = set()
    branches: set[str] = set()
    for index, worker in enumerate(workers):
        if not isinstance(worker, dict):
            fail("CONTRACT_MALFORMED", f"workers[{index}] must be an object")
        worker_id = worker.get("id")
        if not isinstance(worker_id, str) or not worker_id:
            fail("CONTRACT_MALFORMED", f"workers[{index}].id must be a non-empty string")
        if worker_id in ids:
            fail("CONTRACT_MALFORMED", f"duplicate worker id {worker_id}")
        ids.add(worker_id)
        branch = worker.get("branch")
        if not isinstance(branch, str) or not branch:
            fail("CONTRACT_MALFORMED", f"{worker_id} has no branch")
        if branch in branches:
            fail("CONTRACT_MALFORMED", f"two Workers share branch {branch}")
        branches.add(branch)
        if not isinstance(worker.get("writable_paths"), list) or not worker["writable_paths"]:
            fail("CONTRACT_MALFORMED", f"{worker_id} declares no writable path lease")
        if not isinstance(worker.get("depends_on"), list):
            fail("CONTRACT_MALFORMED", f"{worker_id}.depends_on must be an array")
    for worker in workers:
        for dependency in worker["depends_on"]:
            if dependency not in ids:
                fail("CONTRACT_MALFORMED",
                     f"{worker['id']} depends on unknown Worker {dependency}")


def check_base(data: dict[str, Any]) -> None:
    """One immutable base commit for the whole fan-out.

    A moving base means two competitors that both passed were never compared:
    they answered different questions.
    """
    base = data.get("base")
    if not isinstance(base, dict):
        fail("MUTABLE_BASE", "base must be an object")
    if base.get("immutable") is not True:
        fail("MUTABLE_BASE", "base.immutable must be true")
    for field in ("commit_sha", "tree_sha"):
        value = base.get(field)
        if not isinstance(value, str) or not SHA40.fullmatch(value):
            fail("MUTABLE_BASE", f"base.{field} must be a 40-character lowercase SHA")


def check_context(data: dict[str, Any]) -> None:
    """One context bundle digest, and no retired provider under a Worker."""
    bundle = data.get("context_bundle")
    if not isinstance(bundle, dict):
        fail("CONTRACT_MALFORMED", "context_bundle must be an object")
    digest = bundle.get("digest")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        fail("CONTRACT_MALFORMED", "context_bundle.digest must be a 64-character SHA-256")

    for provider in bundle.get("providers") or []:
        name = str(provider.get("name", "")).strip().lower()
        if name in FORBIDDEN_PROVIDERS and provider.get("required_provider"):
            fail("FORBIDDEN_CONTEXT_PROVIDER",
                 f"{provider.get('name')} is retired and cannot be a required context provider")

    funnel = bundle.get("compiler_truth_funnel")
    if not isinstance(funnel, dict):
        fail("CONTRACT_MALFORMED", "context_bundle.compiler_truth_funnel must be an object")
    state = funnel.get("state")
    if state == "PASS" and not str(funnel.get("evidence", "")).strip():
        fail("CONTEXT_FUNNEL_STATE_LAUNDERED",
             "compiler_truth_funnel PASS carries no evidence; an unexercised funnel "
             "stays NOT_EXERCISED rather than being normalized into PASS")
    if state in UNEXERCISED and str(funnel.get("evidence", "")).strip():
        # Not a violation on its own, but a state that did not run cannot also
        # carry run evidence.
        fail("CONTEXT_FUNNEL_STATE_LAUNDERED",
             f"compiler_truth_funnel is {state} yet carries run evidence")


def check_budgets(data: dict[str, Any]) -> None:
    budgets = data.get("budgets")
    if not isinstance(budgets, dict):
        fail("CONTRACT_MALFORMED", "budgets must be an object")
    for field in ("max_workers", "max_tokens_per_worker",
                  "max_wall_clock_seconds", "max_retries_per_worker"):
        value = budgets.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            fail("CONTRACT_MALFORMED", f"budgets.{field} must be a non-negative integer")
    if not budgets.get("circuit_breakers"):
        fail("CONTRACT_MALFORMED", "budgets.circuit_breakers must name at least one breaker")

    workers = data["workers"]
    if len(workers) > budgets["max_workers"]:
        fail("WORKER_BUDGET_OVERFLOW",
             f"{len(workers)} Workers exceed budgets.max_workers={budgets['max_workers']}")
    for worker in workers:
        token_budget = worker.get("token_budget")
        if token_budget is not None and token_budget > budgets["max_tokens_per_worker"]:
            fail("WORKER_BUDGET_OVERFLOW",
                 f"{worker['id']} requests {token_budget} tokens over the "
                 f"per-Worker budget {budgets['max_tokens_per_worker']}")


def check_acceptance(data: dict[str, Any]) -> None:
    """Acceptance oracles are immutable for everyone they judge.

    A competitor that can edit the test it is scored against has not passed the
    test; it has moved it.
    """
    acceptance = data.get("acceptance")
    if not isinstance(acceptance, dict):
        fail("CONTRACT_MALFORMED", "acceptance must be an object")
    immutable = acceptance.get("immutable_paths")
    if not isinstance(immutable, list) or not immutable:
        fail("CONTRACT_MALFORMED", "acceptance.immutable_paths must be non-empty")
    if not acceptance.get("oracles"):
        fail("CONTRACT_MALFORMED", "acceptance.oracles must be non-empty")

    for worker in data["workers"]:
        for lease in worker["writable_paths"]:
            for protected in immutable:
                if path_overlap(lease, protected):
                    fail("ACCEPTANCE_TEST_MUTATED",
                         f"{worker['id']} leases {lease}, which reaches the immutable "
                         f"acceptance path {protected}")


def check_authority(data: dict[str, Any]) -> None:
    """Human keeps winner admission, semantic conflicts, merge and promotion."""
    if data.get("semantic_conflict_resolution") == "automatic":
        fail("AUTOMATIC_SEMANTIC_RESOLUTION",
             "semantic_conflict_resolution must be human; a fan-out cannot grant "
             "itself the merge decision")
    ranking = data.get("ranking")
    if not isinstance(ranking, dict):
        fail("CONTRACT_MALFORMED", "ranking must be an object")
    if ranking.get("winner_admission") == "automatic":
        fail("AUTOMATIC_SEMANTIC_RESOLUTION",
             "ranking.winner_admission must be human")
    if not ranking.get("hard_gates"):
        fail("CONTRACT_MALFORMED", "ranking.hard_gates must name at least one gate")
    if ranking.get("qualitative_review_after_hard_gates") is not True:
        fail("QUALITATIVE_BEFORE_HARD_GATE",
             "qualitative review may only rank what already survived the "
             "deterministic hard gates")
    if ranking.get("cross_competitor_cherry_pick") is True:
        fail("CHERRY_PICK_ACROSS_COMPETITORS",
             "competitors implement incompatible architectures; parts of two "
             "cannot be combined without a Human semantic decision")

    declared = set(data.get("human_owned_operations") or [])
    missing = sorted(REQUIRED_HUMAN - declared)
    if missing:
        fail("AUTOMATIC_SEMANTIC_RESOLUTION",
             "human_owned_operations is missing: " + ", ".join(missing))


def check_competitors(data: dict[str, Any]) -> None:
    """Tournament competitors: same base, same context, different strategy."""
    competitors = [w for w in data["workers"] if w["role"] == "competitor"]
    if data["mode"] == "TOURNAMENT" and len(competitors) < 2:
        fail("CONTRACT_MALFORMED", "TOURNAMENT needs at least two competitors")
    if data["mode"] == "COOPERATIVE" and competitors:
        fail("CONTRACT_MALFORMED", "COOPERATIVE admits no competitor Workers")

    bundle_digest = data["context_bundle"]["digest"]
    seen_focus: dict[str, str] = {}
    for worker in competitors:
        focus = worker.get("focus")
        if focus not in FOCUSES:
            fail("MISSING_BRANCH_FOCUS",
                 f"{worker['id']} declares no branch focus; competitors without a "
                 f"differentiated strategy are repeats, not a tournament")
        if focus in seen_focus:
            fail("MISSING_BRANCH_FOCUS",
                 f"{worker['id']} repeats the focus of {seen_focus[focus]}")
        seen_focus[focus] = worker["id"]

        digest = worker.get("context_digest", bundle_digest)
        if digest != bundle_digest:
            fail("CONTEXT_DIGEST_MISMATCH",
                 f"{worker['id']} was given context {digest[:12]} while the fan-out "
                 f"bundle is {bundle_digest[:12]}; the competitors answered "
                 f"different questions")
        if worker["depends_on"]:
            fail("UNDECLARED_DEPENDENCY",
                 f"{worker['id']} is a competitor and cannot depend on another Worker")


def check_leases(data: dict[str, Any]) -> None:
    """Workers that run at the same time cannot write the same path.

    Two Workers are concurrent unless one transitively depends on the other, so
    a stacked child may inherit its parent's lease and a sibling may not.

    Two competitors are the exception, and the only one: a tournament is
    defined by several branches writing the same surface from the same base,
    and at most one of them is ever admitted. A competitor against anything
    else is still a collision, because any competitor could be the one that
    lands.
    """
    workers = {w["id"]: w for w in data["workers"]}

    def ancestors(worker_id: str, seen: set[str] | None = None) -> set[str]:
        seen = seen or set()
        for dependency in workers[worker_id]["depends_on"]:
            if dependency not in seen:
                seen.add(dependency)
                ancestors(dependency, seen)
        return seen

    order = sorted(workers)
    for i, left_id in enumerate(order):
        for right_id in order[i + 1:]:
            if right_id in ancestors(left_id) or left_id in ancestors(right_id):
                continue
            if workers[left_id]["role"] == "competitor" and workers[right_id]["role"] == "competitor":
                continue
            for left_path in workers[left_id]["writable_paths"]:
                for right_path in workers[right_id]["writable_paths"]:
                    if path_overlap(left_path, right_path):
                        fail("PATH_OVERLAP",
                             f"{left_id} and {right_id} run concurrently and both "
                             f"write {left_path} / {right_path}")


def check_dependencies(data: dict[str, Any]) -> None:
    """A child edge must name the unmerged bytes or contract it consumes."""
    workers = {w["id"]: w for w in data["workers"]}
    for worker in data["workers"]:
        if worker["role"] == "child":
            if not worker["depends_on"]:
                fail("UNDECLARED_DEPENDENCY",
                     f"{worker['id']} is a child branch with no declared parent Worker")
            if not (worker.get("consumes_contracts") or worker.get("consumes_paths")):
                fail("UNDECLARED_DEPENDENCY",
                     f"{worker['id']} stacks on {worker['depends_on']} but names no "
                     f"consumed contract or path; stacking is not a dependency")
        if worker["role"] == "sibling" and worker["depends_on"]:
            # Independence is the whole claim a sibling makes. A sibling that
            # consumes unmerged sibling bytes is a child wearing the label that
            # lets it run early.
            fail("UNDECLARED_DEPENDENCY",
                 f"{worker['id']} is declared a sibling yet depends on "
                 f"{', '.join(worker['depends_on'])}; a real edge makes it a child")

    # Cycle detection over the declared graph.
    state: dict[str, int] = {}

    def visit(node: str) -> None:
        if state.get(node) == 1:
            fail("UNDECLARED_DEPENDENCY", f"dependency cycle reaches {node}")
        if state.get(node) == 2:
            return
        state[node] = 1
        for dependency in workers[node]["depends_on"]:
            visit(dependency)
        state[node] = 2

    for worker_id in workers:
        visit(worker_id)


def check_convergence(data: dict[str, Any]) -> None:
    """One named owner, and it starts only after every input it consumes."""
    workers = {w["id"]: w for w in data["workers"]}
    declared = [w for w in data["workers"] if w["role"] == "convergence"]
    convergence = data.get("convergence")

    if len(declared) > 1:
        fail("CONVERGENCE_OWNER_AMBIGUOUS",
             "more than one Worker claims the convergence role")
    if convergence is None:
        if declared:
            fail("CONVERGENCE_OWNER_AMBIGUOUS",
                 f"{declared[0]['id']} is a convergence Worker but the contract "
                 f"declares no convergence owner")
        return

    owner_id = convergence.get("owner_worker_id")
    if owner_id not in workers:
        fail("CONVERGENCE_OWNER_AMBIGUOUS",
             f"convergence owner {owner_id} is not a Worker in this fan-out")
    if workers[owner_id]["role"] != "convergence":
        fail("CONVERGENCE_OWNER_AMBIGUOUS",
             f"convergence owner {owner_id} does not hold the convergence role")

    inputs = convergence.get("inputs") or []
    for input_id in inputs:
        if input_id not in workers:
            fail("CONTRACT_MALFORMED", f"convergence input {input_id} is not a Worker")
    missing = [i for i in inputs if i not in workers[owner_id]["depends_on"]]
    if missing:
        fail("PREMATURE_CONVERGENCE",
             f"{owner_id} converges {', '.join(missing)} without depending on them; "
             f"convergence starts only after every input has an admitted subject")


CHECKS = (
    check_structure,
    check_base,
    check_context,
    check_budgets,
    check_acceptance,
    check_authority,
    check_competitors,
    check_leases,
    check_dependencies,
    check_convergence,
)


def validate(data: Any) -> None:
    for check in CHECKS:
        check(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("contract", type=Path, help="path to a fan-out contract JSON file")
    args = parser.parse_args(argv)

    try:
        body = json.loads(args.contract.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"USAGE: cannot read {args.contract}: {error}", file=sys.stderr)
        return 64
    except json.JSONDecodeError as error:
        print(f"USAGE: {args.contract} is not JSON: {error}", file=sys.stderr)
        return 64

    try:
        validate(body)
    except Failure as failure:
        print(f"FAN-OUT REFUSED {failure.code}: {failure.detail}", file=sys.stderr)
        return 2
    except Exception as error:  # evaluator defect, not a contract verdict
        print(f"EVALUATOR FAILURE: {error!r}", file=sys.stderr)
        return 70

    mode = body["mode"]
    print(f"FAN-OUT CONTRACT PASS: {mode}, {len(body['workers'])} Worker(s) on "
          f"{body['base']['commit_sha'][:12]}; no branch, worktree or Agent was created")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
