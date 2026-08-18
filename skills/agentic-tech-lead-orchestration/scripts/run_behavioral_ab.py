#!/usr/bin/env python3
"""Run the #316 behavioral A/B: old T0-T10 monolith vs repaired modular Tech Lead.

Exit codes:
  0   every requested cell ran and the run receipt closed
  2   a cell was refused by a deterministic control, or the run could not close
  64  an arm body, the preregistration, the consumer subject or the host binary is absent

Why this exists
---------------
`tests/real_task_ab.py` closes orchestration structure on a synthetic subject and
ends by printing `matched_live_model_quality_cost_latency: NOT_EXERCISED`. That is
the honest state of that lane: it proves the mechanism executes, never that the
repaired body changes what a live model does. #316 asks exactly the question that
lane cannot answer.

So this script varies one thing and nothing else. Each cell is a fresh
non-interactive host process whose stdin is `<arm bytes>\\n\\n<task packet>`. The
packet is byte-identical across arms and its digest is recorded per cell, so a
difference in the results table can only come from the body that was prepended.

Scoring is deterministic
------------------------
Every check is decidable from the emitted packet plus `git cat-file` against the
pinned consumer tree. No model judges another model's output. The rubric is
frozen in `evals/behavioral-ab-preregistration.json`, which was committed before
any cell ran; this file reads the arm identities from it rather than restating
them, so an arm cannot drift away from the design it was registered under.

The packet spec deliberately describes fields, not laws
-------------------------------------------------------
It says what `attempts` is, never that failed attempts belong in it. Telling both
arms the rubric would hand every arm the answer and the experiment would measure
instruction-following instead of the procedure under test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
PREREGISTRATION = SKILL / "evals" / "behavioral-ab-preregistration.json"

REFUSED = 2
INVALID = 64

PLACEHOLDER = re.compile(r"REPLACE_WITH|PLACEHOLDER|TODO|FIXME|XXX|<[A-Za-z_][A-Za-z0-9_ -]*>")

HOST = {
    "id": "claude-code",
    "runtime": "CLAUDE_CODE_LOCAL",
    "binary": "claude",
    "model": "opus",
    # Read-only by construction. The consumer checkout is a sibling repository at
    # its own main tree; a host that could write would make the next cell's
    # subject depend on the previous cell's output.
    "allowed_tools": ["Read", "Glob", "Grep"],
    "disallowed_tools": ["Write", "Edit", "NotebookEdit", "Bash"],
}

# The real slice on the consumer subject. Listed in the packet so both arms see
# the same inventory and neither is rewarded for a lucky glob.
SLICE_PATHS = [
    "packages/harness-console-contracts/hc_contract.py",
    "packages/harness-console-contracts/hc_vocab.py",
    "packages/harness-console-contracts/schemas/console-projection.schema.json",
    "packages/harness-console-contracts/schemas/console-views.schema.json",
    "packages/harness-console-contracts/schemas/decision-request.schema.json",
    "packages/harness-console-contracts/schemas/manifest.json",
    "apps/harness-console/hc_views.py",
    "services/hitl-api/hitlapi.py",
    "services/hitl-api/hitl_request.py",
    "services/hitl-api/hitl_reducer.py",
    "services/hitl-api/control_hitl.py",
    "services/hitl-api/hitl_selftest.py",
]

FEATURE = {
    "TOURNAMENT": (
        "Decision-request payloads reaching services/hitl-api are not validated against "
        "packages/harness-console-contracts/schemas/decision-request.schema.json. Plan the work that "
        "closes that gap. The schema file and every other file under "
        "packages/harness-console-contracts/schemas/ is frozen for this task and may not be edited. "
        "Three differentiated candidates are wanted for the same bounded change: one minimal-diff, one "
        "architecture-types, one defensive-boundaries."
    ),
    "COOPERATIVE_DAG": (
        "The console projection needs one new field, stale_after_seconds, declared in "
        "packages/harness-console-contracts/schemas/console-projection.schema.json and honoured by both "
        "consumers: apps/harness-console/hc_views.py must render staleness, and "
        "services/hitl-api/hitl_reducer.py must refuse a stale decision. Plan the work. The contract "
        "package is the producer; the two consumers read its bytes."
    ),
}

FIELD_SPEC = """Emit ONE JSON object and nothing else -- no prose, no markdown fence. Keys:

  "subject"              object with "repository", "base_commit", "base_tree"
  "mode"                 string naming the topology you chose
  "nodes"                array. Each node: "id" (string), "kind" (one of
                         CANDIDATE, SIBLING, CHILD, CONVERGENCE), "focus" (string),
                         "write_paths" (array of repository-relative paths this node
                         may write), "read_only_paths" (array it may read but not
                         write), "depends_on" (array of node ids)
  "forbidden_paths"      array of repository-relative paths no node may write
  "edges"                array. Each edge: "producer" (node id), "produced_path",
                         "content_digest", "consumer" (node id), "consumed_digest",
                         "edge_type", "reason", "admission_receipt"
  "attempts"             array. Each attempt: "node" (node id), "attempt_id", "state"
  "selection"            object with "winner" (node id), "rationale" (string),
                         "denominator" (integer), "oracle_results" (array of
                         {"node", "attempt_id", "result"}); use null when the task
                         has nothing to select between
  "acceptance_commands"  array of argv arrays that decide whether the work is done
  "automation"           object with boolean "auto_merge", "auto_publish",
                         "auto_resolve_conflicts", "git_town_admitted"
  "human_admit_required" boolean
  "non_claims"           array of strings

Digests you cannot compute may be given as the string you would bind there. Do not
invent a hex digest you did not read."""


class Refused(RuntimeError):
    """A deterministic control refused the run. Not a host failure."""


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise Refused(f"git {' '.join(args)} in {repo.name} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def blob_sha1(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def portable(text: str) -> str:
    """Strip machine-specific paths before anything is recorded."""
    text = text.replace(str(ROOT), "<REPO>").replace(str(Path.home()), "<HOME>")
    return re.sub(r"/(?:private/)?(?:var/folders|tmp)/[A-Za-z0-9._/+-]*", "<TMPDIR>", text)


def refuse_prompt_in_argv(argv: list[str], prompt: str) -> None:
    """No arm text on the command line.

    Both bodies open with YAML front matter. `claude -p ---\\nname: ...` parses the
    body as options, so exactly one arm would die of what its treatment contains
    and the result would still look like data.
    """
    head = prompt[:80]
    if head and any(head in token for token in argv):
        raise Refused("harness bug: arm text reached argv; pass the prompt on stdin")


# ---------------------------------------------------------------- subject


def tree_has(consumer: Path, tree: str, path: str) -> bool:
    """Existence is asked of the pinned tree, never of the working directory."""
    if not path or path.startswith("/") or ".." in PurePosixPath(path).parts:
        return False
    return subprocess.run(
        ["git", "-C", str(consumer), "cat-file", "-e", f"{tree}:{path}"],
        capture_output=True, check=False,
    ).returncode == 0


def path_is_real(consumer: Path, tree: str, raw: str) -> bool:
    """A planned path is real if it exists, or if the directory it would land in does.

    A plan names files that do not exist yet; refusing those would score planning
    as fabrication. Refusing a path whose whole parent chain is absent is what
    catches an invented module.
    """
    if not isinstance(raw, str) or not raw.strip():
        return False
    cleaned = raw.strip().lstrip("./")
    parts = PurePosixPath(cleaned).parts
    if not parts or cleaned.startswith("/") or ".." in parts:
        return False
    # A lease may be a glob (src/**). Everything from the first glob component on
    # is a pattern, so only the concrete prefix can be checked.
    concrete: list[str] = []
    for part in parts:
        if any(char in part for char in "*?["):
            break
        concrete.append(part)
    if not concrete:
        return False
    if tree_has(consumer, tree, "/".join(concrete)):
        return True
    return len(concrete) > 1 and tree_has(consumer, tree, "/".join(concrete[:-1]))


# ---------------------------------------------------------------- prompt


def build_packet(shape: str, repository: str, commit: str, tree: str) -> str:
    listing = "\n".join(f"  {path}" for path in SLICE_PATHS)
    return (
        "=== TASK PACKET ===\n"
        f"Repository: {repository}\n"
        f"base_commit: {commit}\n"
        f"base_tree: {tree}\n"
        "The checkout is READ-ONLY for this task. You are producing the orchestration plan, "
        "not the edit.\n\n"
        f"Files already present in this slice at this subject:\n{listing}\n\n"
        f"Task shape: {shape}\n"
        f"Task: {FEATURE[shape]}\n\n"
        f"{FIELD_SPEC}\n"
    )


def build_prompt(arm_text: str, packet: str) -> str:
    return f"{arm_text}\n\n{packet}"


def cell_order(shape: str, repetition: int, arms: list[str]) -> list[str]:
    """Deterministic per-cell shuffle, recomputable from the receipt.

    A fixed arm order would become part of the treatment: whichever arm always ran
    first would always meet the freshest host state.
    """
    return sorted(arms, key=lambda arm: digest(f"{shape}|{repetition}|{arm}"))


# ---------------------------------------------------------------- host


def extract_json_object(text: str) -> dict[str, Any] | None:
    """The outermost balanced JSON object in the host's output.

    Hosts wrap answers in fences despite the contract. Failing the cell for
    framing would score obedience to formatting rather than the procedure under
    test -- but nothing is repaired: no parseable object scores schema_ok False.
    """
    start = text.find("{")
    while start != -1:
        depth, in_string, escaped = 0, False, False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        value = json.loads(text[start:index + 1])
                    except json.JSONDecodeError:
                        break
                    if isinstance(value, dict):
                        return value
                    break
        start = text.find("{", start + 1)
    return None


def run_host(prompt: str, cwd: Path, timeout: int) -> dict[str, Any]:
    argv = [
        HOST["binary"], "-p",
        "--model", HOST["model"],
        "--output-format", "json",
        "--allowedTools", *HOST["allowed_tools"],
        "--disallowedTools", *HOST["disallowed_tools"],
    ]
    refuse_prompt_in_argv(argv, prompt)
    started = time.time()
    try:
        process = subprocess.run(argv, cwd=cwd, input=prompt, capture_output=True,
                                 text=True, check=False, timeout=timeout)
        stdout, stderr, code = process.stdout, process.stderr, process.returncode
    except subprocess.TimeoutExpired:
        stdout, stderr, code = "", f"timeout after {timeout}s", 124
    elapsed = round(time.time() - started, 3)
    envelope: dict[str, Any] = {}
    try:
        parsed = json.loads(stdout)
        if isinstance(parsed, dict):
            envelope = parsed
    except json.JSONDecodeError:
        pass
    usage = envelope.get("usage") if isinstance(envelope.get("usage"), dict) else {}
    text = envelope.get("result") if isinstance(envelope.get("result"), str) else stdout
    return {
        "argv": [portable(token) for token in argv],
        "exit_code": code,
        "stderr_tail": portable(stderr.strip())[-400:],
        "text": text,
        "duration_ms": int(elapsed * 1000),
        "cost_observed": isinstance(envelope.get("total_cost_usd"), (int, float)),
        "cost_usd": envelope.get("total_cost_usd"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "tool_calls": envelope.get("num_turns"),
        # A host that exited non-zero or said nothing did not answer badly: it did
        # not answer. Scoring that as a wrong answer credits the treatment for an
        # outage, and the cell still stays in the denominator.
        "cell_state": "SCORED" if code == 0 and text.strip() else "HOST_ERROR",
    }


# ---------------------------------------------------------------- scoring


def _strings(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


def _nodes(packet: dict[str, Any]) -> list[dict[str, Any]]:
    value = packet.get("nodes")
    return [item for item in value if isinstance(item, dict) and isinstance(item.get("id"), str)] if isinstance(value, list) else []


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        if state.get(node) == 1:
            return True
        if state.get(node) == 2:
            return False
        state[node] = 1
        for nxt in graph.get(node, []):
            if nxt in graph and visit(nxt):
                return True
        state[node] = 2
        return False

    return any(visit(node) for node in graph)


def score(packet: dict[str, Any] | None, shape: str, consumer: Path, tree: str,
          commit: str, repository: str) -> dict[str, Any]:
    """Every gate is decidable from the packet plus the pinned consumer tree."""
    common = ["schema_ok", "exact_subject_continuity", "depends_on_resolvable", "acyclic",
              "write_readonly_disjoint", "lease_disjoint", "no_auto_merge",
              "evidence_packet_complete", "no_placeholder_commands"]
    tournament = ["three_differentiated_candidates", "candidates_share_base",
                  "denominator_complete", "winner_declared_with_rationale"]
    dag = ["edges_fully_bound", "edge_implies_dependency", "no_false_parallelism",
           "convergence_after_all_inputs", "attempts_cover_every_node"]
    names = common + (tournament if shape == "TOURNAMENT" else dag)
    checks = dict.fromkeys(names, False)
    if packet is None:
        return {"checks": checks, "checks_passed": 0, "checks_total": len(names),
                "cited_paths": 0, "fabricated_paths": 0, "path_fabrication_rate": None,
                "fabricated": []}

    nodes = _nodes(packet)
    ids = {node["id"] for node in nodes}
    subject = packet.get("subject") if isinstance(packet.get("subject"), dict) else {}
    automation = packet.get("automation") if isinstance(packet.get("automation"), dict) else {}
    edges = [item for item in packet.get("edges", []) if isinstance(item, dict)] if isinstance(packet.get("edges"), list) else []
    attempts = [item for item in packet.get("attempts", []) if isinstance(item, dict)] if isinstance(packet.get("attempts"), list) else []
    selection = packet.get("selection") if isinstance(packet.get("selection"), dict) else {}
    forbidden = set(_strings(packet.get("forbidden_paths")))
    commands = packet.get("acceptance_commands") if isinstance(packet.get("acceptance_commands"), list) else []

    checks["schema_ok"] = bool(
        nodes and subject and isinstance(packet.get("mode"), str)
        and isinstance(packet.get("automation"), dict)
        and isinstance(packet.get("non_claims"), list)
        and isinstance(packet.get("acceptance_commands"), list)
    )
    checks["exact_subject_continuity"] = (
        subject.get("base_commit") == commit and subject.get("base_tree") == tree
        and str(subject.get("repository", "")).endswith(repository.split("/")[-1])
    )

    graph = {node["id"]: _strings(node.get("depends_on")) for node in nodes}
    checks["depends_on_resolvable"] = bool(nodes) and all(dep in ids for deps in graph.values() for dep in deps)
    checks["acyclic"] = bool(nodes) and not _has_cycle(graph)

    disjoint = bool(nodes)
    for node in nodes:
        writes = set(_strings(node.get("write_paths")))
        if writes & set(_strings(node.get("read_only_paths"))) or writes & forbidden:
            disjoint = False
    checks["write_readonly_disjoint"] = disjoint

    overlap = False
    for index, left in enumerate(nodes):
        for right in nodes[index + 1:]:
            shared = set(_strings(left.get("write_paths"))) & set(_strings(right.get("write_paths")))
            # Tournament candidates are replicas of one lease, not two writers.
            if shared and not (left.get("kind") == "CANDIDATE" and right.get("kind") == "CANDIDATE"):
                overlap = True
    checks["lease_disjoint"] = bool(nodes) and not overlap

    checks["no_auto_merge"] = (
        automation.get("auto_merge") is False and automation.get("auto_publish") is False
        and automation.get("auto_resolve_conflicts") is False
        and automation.get("git_town_admitted") is False
        and packet.get("human_admit_required") is True
    )
    checks["evidence_packet_complete"] = bool(_strings(packet.get("non_claims")))

    flat = " ".join(str(token) for command in commands if isinstance(command, list) for token in command)
    checks["no_placeholder_commands"] = bool(commands) and all(isinstance(c, list) and c for c in commands) and not PLACEHOLDER.search(flat)

    if shape == "TOURNAMENT":
        candidates = [node for node in nodes if node.get("kind") == "CANDIDATE"]
        foci = [str(node.get("focus", "")).strip().casefold() for node in candidates]
        checks["three_differentiated_candidates"] = len(candidates) >= 3 and len(set(foci)) == len(foci) and all(foci)
        checks["candidates_share_base"] = bool(candidates) and all(not _strings(node.get("depends_on")) for node in candidates)
        candidate_ids = {node["id"] for node in candidates}
        candidate_attempts = [item for item in attempts if item.get("node") in candidate_ids]
        oracles = selection.get("oracle_results") if isinstance(selection.get("oracle_results"), list) else []
        judged = {item.get("attempt_id") for item in oracles if isinstance(item, dict)}
        checks["denominator_complete"] = (
            len(candidate_attempts) >= 3
            and selection.get("denominator") == len(candidate_attempts)
            and {item.get("attempt_id") for item in candidate_attempts} <= judged
        )
        checks["winner_declared_with_rationale"] = (
            selection.get("winner") in candidate_ids and len(str(selection.get("rationale", "")).strip()) >= 40
        )
    else:
        edge_keys = ("producer", "produced_path", "content_digest", "consumer",
                     "consumed_digest", "edge_type", "reason", "admission_receipt")
        checks["edges_fully_bound"] = bool(edges) and all(
            all(isinstance(edge.get(key), str) and edge[key].strip() for key in edge_keys) for edge in edges
        )
        checks["edge_implies_dependency"] = bool(edges) and all(
            edge.get("producer") in graph.get(edge.get("consumer"), []) for edge in edges
        )
        consumers = {edge.get("consumer") for edge in edges}
        checks["no_false_parallelism"] = bool(edges) and not any(
            node["id"] in consumers and node.get("kind") == "SIBLING" for node in nodes
        )
        convergence = [node for node in nodes if node.get("kind") == "CONVERGENCE"]
        checks["convergence_after_all_inputs"] = (
            len(convergence) == 1 and set(_strings(convergence[0].get("depends_on"))) >= (ids - {convergence[0]["id"]})
        )
        checks["attempts_cover_every_node"] = bool(nodes) and ids <= {item.get("node") for item in attempts}

    cited: list[str] = []
    for node in nodes:
        cited += _strings(node.get("write_paths")) + _strings(node.get("read_only_paths"))
    cited += sorted(forbidden)
    cited += [edge["produced_path"] for edge in edges if isinstance(edge.get("produced_path"), str)]
    fabricated = sorted({path for path in cited if not path_is_real(consumer, tree, path)})
    return {
        "checks": checks,
        "checks_passed": sum(1 for value in checks.values() if value),
        "checks_total": len(names),
        "cited_paths": len(cited),
        "fabricated_paths": len(fabricated),
        # No opportunities means no rate. A 0.0 would let a packet that cited
        # nothing outrank one that cited ten paths and got nine right.
        "path_fabrication_rate": round(len(fabricated) / len(cited), 4) if cited else None,
        "fabricated": fabricated,
    }


# ---------------------------------------------------------------- verdict


def summarise(cells: list[dict[str, Any]], shapes: list[str], arms: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for shape in shapes:
        for arm in arms:
            rows = [cell for cell in cells if cell["shape"] == shape and cell["arm"] == arm]
            scored = [cell for cell in rows if cell["cell_state"] == "SCORED"]
            rates = [cell["score"]["path_fabrication_rate"] for cell in scored
                     if cell["score"]["path_fabrication_rate"] is not None]
            passed = [cell["score"]["checks_passed"] for cell in scored]
            out[f"{shape}|{arm}"] = {
                "attempts": len(rows),
                "scored": len(scored),
                "host_errors": len(rows) - len(scored),
                "mean_checks_passed": round(sum(passed) / len(passed), 4) if passed else None,
                "checks_total": scored[0]["score"]["checks_total"] if scored else None,
                "mean_path_fabrication_rate": round(sum(rates) / len(rates), 4) if rates else None,
                "per_check_pass_count": {
                    name: sum(1 for cell in scored if cell["score"]["checks"][name])
                    for name in (scored[0]["score"]["checks"] if scored else {})
                },
            }
    return out


def verdict(summary: dict[str, Any], cells: list[dict[str, Any]], shapes: list[str],
            arms: list[str], reps: int, minimum: int) -> dict[str, Any]:
    """The floor is applied before the numbers are looked at, by design."""
    reasons: list[str] = []
    if reps < minimum:
        reasons.append(f"repetitions_per_cell {reps} < preregistered minimum {minimum}")
    if any(cell["cell_state"] != "SCORED" for cell in cells):
        reasons.append("at least one cell did not return a scorable packet")
    if reasons:
        return {"verdict": "INSUFFICIENT_EVIDENCE", "reasons": reasons}

    a, b = arms[0], arms[1]
    better_b = better_a = tie = 0
    for shape in shapes:
        left, right = summary[f"{shape}|{a}"], summary[f"{shape}|{b}"]
        la, lb = left["mean_checks_passed"], right["mean_checks_passed"]
        fa = left["mean_path_fabrication_rate"] or 0.0
        fb = right["mean_path_fabrication_rate"] or 0.0
        if lb > la and fb <= fa:
            better_b += 1
        elif la > lb and fa <= fb:
            better_a += 1
        elif la == lb and fa == fb:
            tie += 1
    if tie == len(shapes):
        return {"verdict": "NO_DETECTABLE_DIFFERENCE", "reasons": []}
    if better_b == len(shapes):
        return {"verdict": "B_DOMINATES", "reasons": []}
    if better_a == len(shapes):
        return {"verdict": "A_DOMINATES", "reasons": []}
    return {"verdict": "TRADEOFF", "reasons": []}


# ---------------------------------------------------------------- selftest


def _packet(shape: str, commit: str, tree: str, repository: str) -> dict[str, Any]:
    """A packet that satisfies every check, used as the positive control."""
    common = {
        "subject": {"repository": repository, "base_commit": commit, "base_tree": tree},
        "mode": shape,
        "forbidden_paths": ["packages/harness-console-contracts/schemas/manifest.json"],
        "acceptance_commands": [["python3", "services/hitl-api/hitl_selftest.py"]],
        "automation": {"auto_merge": False, "auto_publish": False,
                       "auto_resolve_conflicts": False, "git_town_admitted": False},
        "human_admit_required": True,
        "non_claims": ["no provider, Git Town or Forgejo lane is claimed"],
    }
    if shape == "TOURNAMENT":
        nodes = [{"id": f"cand-{focus}", "kind": "CANDIDATE", "focus": focus,
                  "write_paths": ["services/hitl-api/hitl_request.py"],
                  "read_only_paths": ["packages/harness-console-contracts/schemas/decision-request.schema.json"],
                  "depends_on": []}
                 for focus in ("minimal-diff", "architecture-types", "defensive-boundaries")]
        attempts = [{"node": node["id"], "attempt_id": f"a-{node['id']}", "state": "RESULT_VERIFIED"} for node in nodes]
        return {**common, "nodes": nodes, "edges": [], "attempts": attempts,
                "selection": {"winner": "cand-minimal-diff",
                              "rationale": "smallest verified diff passing every immutable oracle on the frozen schema",
                              "denominator": 3,
                              "oracle_results": [{"node": item["node"], "attempt_id": item["attempt_id"],
                                                  "result": "PASS"} for item in attempts]}}
    nodes = [
        {"id": "contract", "kind": "CHILD", "focus": "producer",
         "write_paths": ["packages/harness-console-contracts/schemas/console-projection.schema.json"],
         "read_only_paths": [], "depends_on": []},
        {"id": "views", "kind": "CHILD", "focus": "consumer",
         "write_paths": ["apps/harness-console/hc_views.py"], "read_only_paths": [], "depends_on": ["contract"]},
        {"id": "reducer", "kind": "CHILD", "focus": "consumer",
         "write_paths": ["services/hitl-api/hitl_reducer.py"], "read_only_paths": [], "depends_on": ["contract"]},
        {"id": "converge", "kind": "CONVERGENCE", "focus": "integration",
         "write_paths": ["packages/harness-console-contracts/schemas/manifest.json"],
         "read_only_paths": [], "depends_on": ["contract", "views", "reducer"]},
    ]
    edges = [{"producer": "contract", "produced_path": "packages/harness-console-contracts/schemas/console-projection.schema.json",
              "content_digest": "sha256:unmerged-parent-bytes", "consumer": consumer,
              "consumed_digest": "sha256:unmerged-parent-bytes", "edge_type": "CONTRACT_BYTES",
              "reason": "consumer reads the new field", "admission_receipt": "receipt://contract-verified"}
             for consumer in ("views", "reducer")]
    attempts = [{"node": node["id"], "attempt_id": f"a-{node['id']}", "state": "RESULT_VERIFIED"} for node in nodes]
    return {**common, "nodes": nodes, "edges": edges, "attempts": attempts, "selection": None,
            "forbidden_paths": []}


def build_selftest_subject(root: Path) -> Path:
    """A throwaway checkout carrying exactly the slice inventory.

    The selftest does not borrow the real consumer: it runs in CI where that
    checkout is absent, and a scorer whose controls only fire on one developer's
    filesystem is not a control.
    """
    repo = root / "subject"
    repo.mkdir(parents=True)
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "canary"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "canary@example.invalid"], check=True)
    for relative in SLICE_PATHS:
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# fixture stand-in for {relative}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "fixture: slice inventory"], check=True)
    return repo


def selftest(root: Path) -> int:
    """Score fixed packets against a real tree. No host, no network, no spend."""
    repository = "ed3c/bettor-arena"
    consumer = build_selftest_subject(root)
    commit = git(consumer, "rev-parse", "HEAD")
    tree = git(consumer, "rev-parse", "HEAD^{tree}")

    for shape in ("TOURNAMENT", "COOPERATIVE_DAG"):
        clean = score(_packet(shape, commit, tree, repository), shape, consumer, tree, commit, repository)
        if clean["checks_passed"] != clean["checks_total"] or clean["path_fabrication_rate"] != 0.0:
            failing = [name for name, ok in clean["checks"].items() if not ok]
            print(f"SELFTEST RED: a correct {shape} packet did not score clean: {failing} {clean}", file=sys.stderr)
            return 1

    # Each mutation must turn exactly the check it targets red. A mutation that
    # turns nothing red means the check is decorative; one that turns everything
    # red means the scorer collapsed rather than discriminated.
    def mutate(shape: str, change: Any) -> dict[str, Any]:
        packet = _packet(shape, commit, tree, repository)
        change(packet)
        return score(packet, shape, consumer, tree, commit, repository)

    plants: list[tuple[str, str, Any]] = [
        ("TOURNAMENT", "exact_subject_continuity", lambda p: p["subject"].update(base_tree="f" * 40)),
        ("TOURNAMENT", "depends_on_resolvable", lambda p: p["nodes"][0].update(depends_on=["ghost"])),
        ("TOURNAMENT", "no_auto_merge", lambda p: p["automation"].update(auto_merge=True)),
        ("TOURNAMENT", "evidence_packet_complete", lambda p: p.update(non_claims=[])),
        ("TOURNAMENT", "no_placeholder_commands",
         lambda p: p.update(acceptance_commands=[["REPLACE_WITH_REPOSITORY_TEST_COMMAND"]])),
        ("TOURNAMENT", "three_differentiated_candidates",
         lambda p: p["nodes"][1].update(focus="minimal-diff")),
        ("TOURNAMENT", "denominator_complete",
         lambda p: (p["attempts"].append({"node": "cand-minimal-diff", "attempt_id": "a-stale", "state": "STALE"}))),
        ("TOURNAMENT", "winner_declared_with_rationale", lambda p: p["selection"].update(rationale="looked best")),
        ("TOURNAMENT", "write_readonly_disjoint",
         lambda p: p["nodes"][0].update(read_only_paths=["services/hitl-api/hitl_request.py"])),
        ("COOPERATIVE_DAG", "lease_disjoint",
         lambda p: p["nodes"][1].update(write_paths=["services/hitl-api/hitl_reducer.py"])),
        ("COOPERATIVE_DAG", "edges_fully_bound", lambda p: p["edges"][0].update(admission_receipt="")),
        ("COOPERATIVE_DAG", "edge_implies_dependency", lambda p: p["nodes"][1].update(depends_on=[])),
        ("COOPERATIVE_DAG", "no_false_parallelism", lambda p: p["nodes"][1].update(kind="SIBLING")),
        ("COOPERATIVE_DAG", "convergence_after_all_inputs",
         lambda p: p["nodes"][3].update(depends_on=["contract"])),
        ("COOPERATIVE_DAG", "attempts_cover_every_node", lambda p: p["attempts"].pop()),
        ("COOPERATIVE_DAG", "acyclic",
         lambda p: (p["nodes"][0].update(depends_on=["converge"]))),
    ]
    for shape, target, change in plants:
        result = mutate(shape, change)
        if result["checks"][target]:
            print(f"SELFTEST RED: planted {target} on {shape} survived", file=sys.stderr)
            return 1

    # edge_implies_dependency and no_false_parallelism must not be the same check
    # wearing two names: each has to fall on its own without the other.
    only_dependency = mutate("COOPERATIVE_DAG", lambda p: p["nodes"][1].update(depends_on=[]))
    if not only_dependency["checks"]["no_false_parallelism"]:
        print("SELFTEST RED: a missing dependency also collapsed the sibling-label check", file=sys.stderr)
        return 1
    only_label = mutate("COOPERATIVE_DAG", lambda p: p["nodes"][1].update(kind="SIBLING"))
    if not only_label["checks"]["edge_implies_dependency"]:
        print("SELFTEST RED: a sibling label also collapsed the dependency check", file=sys.stderr)
        return 1

    fabricating = mutate("TOURNAMENT", lambda p: p["nodes"][0]["write_paths"].append("services/imaginary/nope.py"))
    if fabricating["fabricated_paths"] != 1:
        print(f"SELFTEST RED: an invented path was not caught: {fabricating['fabricated']}", file=sys.stderr)
        return 1
    planned = mutate("TOURNAMENT", lambda p: p["nodes"][0]["write_paths"].append("services/hitl-api/hitl_validate.py"))
    if planned["fabricated_paths"] != 0:
        print("SELFTEST RED: a new file in a real directory was scored as fabrication", file=sys.stderr)
        return 1
    escaping = mutate("TOURNAMENT", lambda p: p["nodes"][0].update(write_paths=["../../etc/passwd", "/etc/passwd"]))
    if escaping["fabricated_paths"] != 2:
        print("SELFTEST RED: paths escaping the repository scored as real", file=sys.stderr)
        return 1
    globbed = mutate("TOURNAMENT", lambda p: p["nodes"][0].update(write_paths=["services/hitl-api/**"]))
    if globbed["fabricated_paths"] != 0:
        print("SELFTEST RED: a lease glob over a real directory scored as fabrication", file=sys.stderr)
        return 1

    if score(None, "TOURNAMENT", consumer, tree, commit, repository)["checks_passed"]:
        print("SELFTEST RED: an unparseable response scored a check", file=sys.stderr)
        return 1

    for text, expected in [('{"a": 1}', {"a": 1}), ('```json\n{"a": 1}\n```', {"a": 1}),
                           ('x\n{"a": {"b": 2}}\ny', {"a": {"b": 2}}), ('{"a": "}"}', {"a": "}"}),
                           ("nothing", None), ("{unbalanced", None)]:
        if extract_json_object(text) != expected:
            print(f"SELFTEST RED: extract_json_object({text!r}) != {expected}", file=sys.stderr)
            return 1

    leaky = f"wrote {ROOT}/out.json from {Path.home()}/x and /var/folders/ab/cd/T/tmpq"
    if str(ROOT) in portable(leaky) or str(Path.home()) in portable(leaky) or "/var/folders/" in portable(leaky):
        print("SELFTEST RED: machine paths survived redaction", file=sys.stderr)
        return 1

    body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    prompt = build_prompt(body, build_packet("TOURNAMENT", "ed3c/bettor-arena", commit, tree))
    try:
        refuse_prompt_in_argv(["claude", "-p", prompt], prompt)
    except Refused:
        pass
    else:
        print("SELFTEST RED: arm text on the command line was not refused", file=sys.stderr)
        return 1

    shapes, arms = ["TOURNAMENT", "COOPERATIVE_DAG"], ["A", "B"]
    if cell_order("TOURNAMENT", 0, arms) == cell_order("COOPERATIVE_DAG", 0, arms):
        print("SELFTEST RED: two shapes received the same arm order", file=sys.stderr)
        return 1

    def cell(shape: str, arm: str, passed: int, rate: float, state: str = "SCORED") -> dict[str, Any]:
        return {"shape": shape, "arm": arm, "cell_state": state,
                "score": {"checks_passed": passed, "checks_total": 13,
                          "path_fabrication_rate": rate, "checks": {}}}

    dominating = [cell(shape, "A", 8, 0.2) for shape in shapes] + [cell(shape, "B", 11, 0.0) for shape in shapes]
    summary = summarise(dominating, shapes, arms)
    if verdict(summary, dominating, shapes, arms, 9, 9)["verdict"] != "B_DOMINATES":
        print("SELFTEST RED: a dominating B at full power did not read as B_DOMINATES", file=sys.stderr)
        return 1
    if verdict(summary, dominating, shapes, arms, 3, 9)["verdict"] != "INSUFFICIENT_EVIDENCE":
        print("SELFTEST RED: the power floor did not override a dominating table", file=sys.stderr)
        return 1
    mixed = [cell("TOURNAMENT", "A", 11, 0.0), cell("COOPERATIVE_DAG", "A", 8, 0.2),
             cell("TOURNAMENT", "B", 8, 0.2), cell("COOPERATIVE_DAG", "B", 11, 0.0)]
    if verdict(summarise(mixed, shapes, arms), mixed, shapes, arms, 9, 9)["verdict"] != "TRADEOFF":
        print("SELFTEST RED: a split table did not read as TRADEOFF", file=sys.stderr)
        return 1
    flat = [cell(shape, arm, 10, 0.1) for shape in shapes for arm in arms]
    if verdict(summarise(flat, shapes, arms), flat, shapes, arms, 9, 9)["verdict"] != "NO_DETECTABLE_DIFFERENCE":
        print("SELFTEST RED: an identical table did not read as NO_DETECTABLE_DIFFERENCE", file=sys.stderr)
        return 1
    outage = [cell(shape, "A", 8, 0.2) for shape in shapes] + [cell(shape, "B", 11, 0.0) for shape in shapes]
    outage[0]["cell_state"] = "HOST_ERROR"
    if verdict(summarise(outage, shapes, arms), outage, shapes, arms, 9, 9)["verdict"] != "INSUFFICIENT_EVIDENCE":
        print("SELFTEST RED: a host outage was laundered into a treatment verdict", file=sys.stderr)
        return 1

    print(
        "SELFTEST GREEN: both positive packets score clean against a pinned fixture tree; "
        f"{len(plants)} planted defects each turn their own check red; the dependency and "
        "sibling-label checks fall independently; invented and repository-escaping paths score as "
        "fabrication while a planned file in a real directory and a lease glob do not; "
        "the power floor, a split table, an identical table and a host outage each override the numbers"
    )
    return 0


# ---------------------------------------------------------------- main


def load_preregistration() -> dict[str, Any]:
    try:
        body = json.loads(PREREGISTRATION.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Refused(f"unreadable preregistration {PREREGISTRATION}: {error}") from error
    if body.get("schema") != "agentic-tech-lead/behavioral-ab-preregistration/v1":
        raise Refused("preregistration schema mismatch")
    return body


def resolve_arms(prereg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Arm identity comes from the frozen design, not from whatever is on disk."""
    out: dict[str, dict[str, Any]] = {}
    for name, spec in prereg["arms"].items():
        if not isinstance(spec, dict) or "material_path" not in spec:
            continue
        path = ROOT / spec["material_path"]
        if not path.is_file():
            raise Refused(f"arm material absent: {spec['material_path']}")
        observed = blob_sha1(path)
        if observed != spec["git_blob_sha1"]:
            raise Refused(
                f"arm {name} drifted from its preregistered identity: {observed} != {spec['git_blob_sha1']}"
            )
        out[name] = {"text": path.read_text(encoding="utf-8"), "blob_sha1": observed,
                     "path": spec["material_path"], "sha256": digest(path.read_bytes())}
    if len(out) != 2:
        raise Refused(f"expected exactly two arms, resolved {sorted(out)}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="resolve every binding and print the cell plan without invoking a host")
    parser.add_argument("--consumer", type=Path, default=Path.home() / "bettor-arena")
    parser.add_argument("--output", type=Path, help="directory for per-cell receipts")
    parser.add_argument("--result", type=Path, help="path for the run result document")
    parser.add_argument("--repetitions", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=420)
    # A previous run's attempts happened whether or not their receipts survived.
    # These record that fact in the denominator instead of quietly restarting the
    # count at zero; the lost scores are never admitted, only the attempt count.
    parser.add_argument("--prior-lost-attempts", type=int, default=0)
    parser.add_argument("--prior-lost-reason", default="")
    args = parser.parse_args(argv)

    try:
        if args.selftest:
            with tempfile.TemporaryDirectory(prefix="behavioral-ab-selftest-") as scratch:
                return selftest(Path(scratch))

        consumer = args.consumer.expanduser()
        if not (consumer / ".git").exists():
            print(f"BEHAVIORAL-AB-INVALID absent-consumer: {consumer}", file=sys.stderr)
            return INVALID

        prereg = load_preregistration()
        arms = resolve_arms(prereg)
        reps = args.repetitions if args.repetitions is not None else prereg["power"]["repetitions_per_cell_this_run"]
        minimum = prereg["power"]["minimum_repetitions_for_a_general_claim"]
        shapes = [item["id"] for item in prereg["task_shapes"]]
        repository = prereg["subject"]["consumer_repository"]

        if not args.dry_run and shutil.which(HOST["binary"]) is None:
            print(f"BEHAVIORAL-AB-INVALID absent-binary: {HOST['binary']}", file=sys.stderr)
            return INVALID
        if not args.dry_run and (not args.output or not args.result):
            print("BEHAVIORAL-AB-INVALID: --output and --result are required for a live run", file=sys.stderr)
            return INVALID

        commit = git(consumer, "rev-parse", "HEAD")
        tree = git(consumer, "rev-parse", "HEAD^{tree}")
        porcelain_before = digest(git(consumer, "status", "--porcelain"))
        packets = {shape: build_packet(shape, repository, commit, tree) for shape in shapes}

        bindings = {
            "packet_digests": {shape: digest(text.encode()) for shape, text in packets.items()},
            "scorer_sha256": digest(Path(__file__).read_bytes()),
            "timeout_seconds": args.timeout,
            "retries_permitted": 0,
        }
        # Identity of everything a cell's result depends on. A stored cell may be
        # reused only when this matches, so a resumed run cannot silently mix
        # results produced under two different rubrics or task packets.
        binding_digest = digest({"bindings": bindings, "arms": {n: s["blob_sha1"] for n, s in arms.items()},
                                 "commit": commit, "tree": tree})
        if args.output:
            args.output.mkdir(parents=True, exist_ok=True)

        cells: list[dict[str, Any]] = []
        for shape in shapes:
            for repetition in range(reps):
                for arm in cell_order(shape, repetition, sorted(arms)):
                    prompt = build_prompt(arms[arm]["text"], packets[shape])
                    if args.dry_run:
                        print(f"PLAN shape={shape} rep={repetition} arm={arm} "
                              f"prompt_bytes={len(prompt.encode())} packet_digest={digest(packets[shape].encode())[:12]}")
                        continue
                    path = args.output / f"cell-{shape.lower()}-{arm.lower()}-{repetition}-{commit[:12]}.json"
                    # Resume. A cell costs real tokens, so a run interrupted at
                    # cell eleven must not buy the first ten again -- and each
                    # cell is written the moment it is scored, because a receipt
                    # that only exists at the end does not exist.
                    if path.is_file():
                        stored = json.loads(path.read_text(encoding="utf-8"))
                        if stored.get("binding_digest") == binding_digest:
                            cells.append(stored)
                            print(f"CELL {shape} rep={repetition} arm={arm} REUSED "
                                  f"passed={stored['score']['checks_passed']}/{stored['score']['checks_total']}", flush=True)
                            continue
                    observation = run_host(prompt, consumer, args.timeout)
                    packet = extract_json_object(observation["text"])
                    cell = {
                        "shape": shape,
                        "arm": arm,
                        "repetition": repetition,
                        "cell_state": observation["cell_state"],
                        "binding_digest": binding_digest,
                        "prompt_digest": digest(prompt.encode()),
                        "packet_digest": digest(packets[shape].encode()),
                        "arm_blob_sha1": arms[arm]["blob_sha1"],
                        "response_digest": digest(observation["text"].encode()),
                        "response": observation["text"],
                        "observation": {k: v for k, v in observation.items() if k != "text"},
                        "score": score(packet, shape, consumer, tree, commit, repository),
                    }
                    path.write_text(json.dumps(cell, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                    cells.append(cell)
                    print(f"CELL {shape} rep={repetition} arm={arm} state={observation['cell_state']} "
                          f"passed={cell['score']['checks_passed']}/{cell['score']['checks_total']} "
                          f"fabricated={cell['score']['fabricated_paths']}", flush=True)
        if args.dry_run:
            print(f"PLAN-COMPLETE arms={sorted(arms)} shapes={shapes} repetitions={reps} "
                  f"cells={len(shapes) * reps * len(arms)}")
            return 0

        porcelain_after = digest(git(consumer, "status", "--porcelain"))
        summary = summarise(cells, shapes, sorted(arms))
        decision = verdict(summary, cells, shapes, sorted(arms), reps, minimum)

        result = {
            "schema": "agentic-tech-lead/behavioral-ab-result/v1",
            "issue": prereg["issue"],
            "preregistration": {
                "path": str(PREREGISTRATION.relative_to(ROOT)),
                "sha256": digest(PREREGISTRATION.read_bytes()),
                "frozen_before_execution": True,
            },
            "subject": {
                "consumer_repository": repository,
                "base_commit": commit,
                "base_tree": tree,
                "worktree_porcelain_before": porcelain_before,
                "worktree_porcelain_after": porcelain_after,
                "residue": "CLEAN" if porcelain_before == porcelain_after else "DIRTY",
                "skills_shared_head": git(ROOT, "rev-parse", "HEAD"),
            },
            "host": {**{k: v for k, v in HOST.items()},
                     "version": subprocess.run([HOST["binary"], "--version"], capture_output=True,
                                               text=True, check=False).stdout.strip()},
            "arms": {name: {k: v for k, v in spec.items() if k != "text"} for name, spec in arms.items()},
            "bindings": {**bindings, "binding_digest": binding_digest},
            "repetitions_per_cell": reps,
            "minimum_repetitions_for_a_general_claim": minimum,
            "denominator": {
                "attempts": len(cells),
                "scored": sum(1 for cell in cells if cell["cell_state"] == "SCORED"),
                "host_errors": sum(1 for cell in cells if cell["cell_state"] != "SCORED"),
                "prior_attempts_lost_without_receipts": args.prior_lost_attempts,
                "prior_attempts_lost_reason": args.prior_lost_reason,
                "prior_attempts_scores_admitted": False,
                "every_attempt_recorded": True,
            },
            "summary": summary,
            "cost_and_latency_recorded_never_scored": {
                f"{cell['shape']}|{cell['arm']}|{cell['repetition']}": {
                    k: cell["observation"][k] for k in
                    ("cost_usd", "input_tokens", "output_tokens", "duration_ms", "tool_calls")
                } for cell in cells
            },
            "conclusion": decision["verdict"],
            "conclusion_reasons": decision["reasons"],
            "not_exercised": {
                "linked_worktrees_and_physical_workers": "CLOSED_ELSEWHERE tests/real_task_ab.py",
                "provider_adapters": "NOT_EXERCISED",
                "git_town": "NOT_EXERCISED",
                "forgejo_and_github_publication": "NOT_EXERCISED",
                "merge_authority": "HUMAN_ADMIT_REQUIRED",
            },
            "evidence_boundary": prereg["evidence_boundary"],
        }
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        if result["subject"]["residue"] != "CLEAN":
            print("BEHAVIORAL-AB-RED consumer worktree changed during the run", file=sys.stderr)
            return REFUSED
        print(f"BEHAVIORAL-AB-COMPLETE conclusion={decision['verdict']} "
              f"cells={len(cells)} scored={result['denominator']['scored']} "
              f"residue={result['subject']['residue']}")
        return 0
    except Refused as error:
        print(f"BEHAVIORAL-AB-RED {error}", file=sys.stderr)
        return REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
