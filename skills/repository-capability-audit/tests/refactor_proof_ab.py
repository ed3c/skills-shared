#!/usr/bin/env python3
"""Matched hermetic A/B over the frozen bodies of this Skill (issue #351).

What this is, and what it is not
--------------------------------
This Skill's body was never structurally refactored. `git log --follow` on
`SKILL.md` returns exactly three revisions, and every diff between them is a
pure append: the thirteen RCA rules, the terminal-state vocabulary, the state
machine, the required-output manifest and the stop conditions are byte-stable
across all three. So no monolith was split here and nothing was rewritten.
`REFACTOR_AS_LANDED` is the golden-proof registry's role vocabulary, not a
claim that revision B0 restructured anything -- it is simply the first landed
revision of the body after the canonical one. Inventing a restructuring to fit
the role name would be exactly the fabrication the proof loop exists to refuse.

What did change between revisions is measurable and is what this scores: each
revision binds one more executable refusal into the procedure.

    A_OLD_CANONICAL           core-ablation route only
    B0_REFACTOR_AS_LANDED     + the saturated-primary-metric refusal (#219)
    B1_CONTRIBUTION_GATE_BOUND + the contribution-drift refusal (#233)

The task is therefore: plant one defect per refusal in one hermetic subject,
give every arm the same subject, the same budget and the same oracles, and run
only the checkers that arm's own bytes declare. An arm that never named a
checker cannot catch what that checker catches, and that difference is read off
real subprocess exit codes rather than asserted.

Every guard is exercised as a matched pair -- clean subject must exit 0, planted
subject must exit non-zero -- which is this Skill's own RCA-005 applied to its
own proof: a checker that only ever goes green is indistinguishable from one
that cannot go red.

Ceilings this run does not touch: it observes no model, no provider and no host
binary, so live model/runtime uplift stays NOT_EXERCISED and is owned by #256.

Exit codes:
  0   the matched task closed; every control and planted mutation behaved
  2   a control, a mutation or a treatment identity failed
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SCRIPTS = ROOT / "scripts"

# Matched budget: identical for every arm, so a slow guard cannot look like a
# failed one on a loaded machine.
TIMEOUT_SECONDS = 300

# path -> (git blob sha, commit the bytes were read out of).
# The blob is recomputed from the file below; the commit is recorded so any
# reader can replay `git cat-file blob <sha>` and see it is real history rather
# than a hand-written copy of it.
ARMS: dict[str, dict[str, Any]] = {
    "A_OLD_CANONICAL": {
        "role": "OLD_CANONICAL",
        "path": FIXTURES / "old-canonical-SKILL.txt",
        "blob_sha": "0cbced53d29090b1cd7cd875482a4658351f053b",
        "source_commit": "f59d3f8",
    },
    "B0_REFACTOR_AS_LANDED": {
        "role": "REFACTOR_AS_LANDED",
        "path": FIXTURES / "refactor-as-landed-SKILL.txt",
        "blob_sha": "2283322fb3997f00e710bfef90fd5ac1388d9127",
        "source_commit": "2aa3e29",
    },
    "B1_CONTRIBUTION_GATE_BOUND": {
        "role": "REPAIRED_CANDIDATE",
        "path": ROOT / "SKILL.md",
        "blob_sha": "b9ccc71f63ef5f34be16cae303452c90a4e1532b",
        "source_commit": "110ac7c",
    },
}
ARM_ORDER = ["A_OLD_CANONICAL", "B0_REFACTOR_AS_LANDED", "B1_CONTRIBUTION_GATE_BOUND"]

# Each defect is caught by exactly one checker. An arm detects it only when its
# own bytes name that checker's path.
GUARDS: dict[str, str] = {
    "core_ablation_delta_lost": "scripts/check_core.py",
    "saturated_primary_metric": "scripts/analyze_arm_separation.py",
    "contribution_table_drift": "scripts/publish_source_contribution.py",
}

# Guarantees arm A already made. A later arm that drops one is a lost old
# strength, not a cleaner document.
RULE_HEADING = re.compile(r"^### (RCA-\d{3}) ", re.MULTILINE)
EXPECTED_RULES = [f"RCA-{n:03d}" for n in range(1, 14)]
TERMINAL_STATES = (
    "PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED",
    "NOT_EXERCISED", "BLOCKED_INFRASTRUCTURE", "SKIPPED_BY_POLICY",
)
SCRIPT_REF = re.compile(r"skills/repository-capability-audit/(scripts/[A-Za-z0-9_./-]+\.py)")


class ProofError(Exception):
    """A control, mutation or identity assertion refused the run."""


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def run(argv: list[str]) -> int:
    completed = subprocess.run(
        argv, cwd=REPO, capture_output=True, text=True,
        check=False, timeout=TIMEOUT_SECONDS,
    )
    return completed.returncode


def declared_guards(body: str) -> list[str]:
    return sorted(name for name, script in GUARDS.items() if script in body)


def dead_routes(body: str) -> list[str]:
    """Script paths a body names that do not exist in the current tree."""
    return sorted({ref for ref in SCRIPT_REF.findall(body) if not (ROOT / ref).is_file()})


def old_strengths(body: str) -> dict[str, bool]:
    rules = RULE_HEADING.findall(body)
    return {
        "thirteen_rca_rules": rules == EXPECTED_RULES,
        "terminal_state_vocabulary": all(state in body for state in TERMINAL_STATES),
        "state_machine": "## State machine" in body,
        "required_output_manifest": "## Required output" in body and "SHA256SUMS" in body,
        "stop_conditions": "## Stop conditions" in body,
        "core_self_check_route": "scripts/run_ablation.py" in body and "scripts/check_core.py" in body,
        "domain_instances_stay_in_modules": "modules/" in body,
    }


def build_subject(temp: Path) -> dict[str, dict[str, Path]]:
    """One subject, two versions per defect: clean and planted.

    Everything is derived from committed bytes, so the subject is reproducible
    on any host and reaches no network.
    """
    clean = temp / "clean"
    planted = temp / "planted"
    for directory in (clean, planted):
        directory.mkdir(parents=True)

    report = json.loads((ROOT / "evals/expected/effectiveness.json").read_text(encoding="utf-8"))
    (clean / "effectiveness.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    broken = copy.deepcopy(report)
    broken["ablations"]["RCA-007"]["effective"] = False
    broken["ablations"]["RCA-007"]["score_delta"] = 0.0
    (planted / "effectiveness.json").write_text(json.dumps(broken, indent=2, sort_keys=True), encoding="utf-8")

    matrix = json.loads((ROOT / "evals/matrix-slice1-result.json").read_text(encoding="utf-8"))
    (clean / "matrix.json").write_text(json.dumps(matrix, indent=2, sort_keys=True), encoding="utf-8")
    flattened = copy.deepcopy(matrix)
    for cell in flattened["cells"]:
        metrics = cell.get("metrics")
        if isinstance(metrics, dict) and "false_pass_count" in metrics:
            # Identical in every cell of every arm: zero within-arm variance, so
            # the primary metric carries no treatment signal at all.
            metrics["false_pass_count"] = 10
            metrics["false_pass_opportunities"] = 28
    (planted / "matrix.json").write_text(json.dumps(flattened, indent=2, sort_keys=True), encoding="utf-8")

    for directory in (clean, planted):
        root = directory / "skill-root"
        (root / "modules").mkdir(parents=True)
        shutil.copytree(ROOT / "evals", root / "evals")
        shutil.copy2(ROOT / "modules/measurement-limits.md", root / "modules/measurement-limits.md")
    table = planted / "skill-root/evals/live-source-contribution.md"
    # A hand-maintained row appended after generation: exactly the drift the
    # #233 guard exists to refuse.
    table.write_text(table.read_text(encoding="utf-8") + "| hand-edited | 99 |\n", encoding="utf-8")

    return {
        "core_ablation_delta_lost": {
            "clean": clean / "effectiveness.json", "planted": planted / "effectiveness.json"},
        "saturated_primary_metric": {
            "clean": clean / "matrix.json", "planted": planted / "matrix.json"},
        "contribution_table_drift": {
            "clean": clean / "skill-root", "planted": planted / "skill-root"},
    }


def guard_command(defect: str, subject: Path) -> list[str]:
    script = str(SCRIPTS / Path(GUARDS[defect]).name)
    if defect == "contribution_table_drift":
        return [sys.executable, script, "--skill-root", str(subject), "--check"]
    flag = "--report" if defect == "core_ablation_delta_lost" else "--result"
    return [sys.executable, script, flag, str(subject)]


def exercise_guards(subject: dict[str, dict[str, Path]]) -> dict[str, dict[str, int]]:
    """Matched positive/negative control for every guard (RCA-005 on ourselves)."""
    observed: dict[str, dict[str, int]] = {}
    for defect, versions in subject.items():
        clean = run(guard_command(defect, versions["clean"]))
        planted = run(guard_command(defect, versions["planted"]))
        if clean != 0:
            raise ProofError(f"positive control failed: {defect} exited {clean} on a clean subject")
        if planted == 0:
            raise ProofError(f"planted defect survived: {defect} exited 0 on a defective subject")
        observed[defect] = {"clean_exit": clean, "planted_exit": planted}
    return observed


def score(name: str, body: str, observed: dict[str, dict[str, int]]) -> dict[str, Any]:
    guards = declared_guards(body)
    detection = {
        defect: ("DETECTED" if defect in guards else "NOT_DETECTED")
        for defect in sorted(GUARDS)
    }
    strengths = old_strengths(body)
    return {
        "arm": name,
        "role": ARMS[name]["role"],
        "treatment_blob": git_blob(body.encode("utf-8")),
        "source_commit": ARMS[name]["source_commit"],
        "declared_guards": guards,
        "detection": detection,
        "detected_count": sum(1 for v in detection.values() if v == "DETECTED"),
        "defect_denominator": len(GUARDS),
        "old_strengths": strengths,
        "old_strengths_held": all(strengths.values()),
        "dead_routes": dead_routes(body),
        "planted_exit_codes": {d: observed[d]["planted_exit"] for d in guards},
    }


def read_arms() -> dict[str, str]:
    bodies: dict[str, str] = {}
    for name, meta in ARMS.items():
        raw = Path(meta["path"]).read_bytes()
        observed = git_blob(raw)
        if observed != meta["blob_sha"]:
            raise ProofError(
                f"frozen treatment drift {name}: {observed} != {meta['blob_sha']}"
            )
        bodies[name] = raw.decode("utf-8")
    return bodies


def mutations(bodies: dict[str, str], observed: dict[str, dict[str, int]]) -> dict[str, bool]:
    """Plant a lie in the live arm's bytes and require the scorer to refuse it.

    A scorer that only ever reads committed bytes is green by construction.
    These are in-memory copies; no file on disk is touched.
    """
    live = bodies["B1_CONTRIBUTION_GATE_BOUND"]
    baseline = score("B1_CONTRIBUTION_GATE_BOUND", live, observed)
    b0_count = score("B0_REFACTOR_AS_LANDED", bodies["B0_REFACTOR_AS_LANDED"], observed)["detected_count"]
    if not baseline["old_strengths_held"] or baseline["dead_routes"]:
        raise ProofError("the unmutated live arm is already red; controls prove nothing")
    # Without this the dominance control is vacuous: a scorer that credits every
    # arm with every guard collapses baseline and B0 onto the same count, and
    # "the mutation lost dominance" then passes because there was none to lose.
    if baseline["detected_count"] <= b0_count:
        raise ProofError(
            f"no dominance to lose: B1 detects {baseline['detected_count']} and B0 detects {b0_count}"
        )

    start = live.index("### RCA-007 ")
    end = live.index("### RCA-008 ")
    without_rule = live[:start] + live[end:]
    dead = live.replace("scripts/check_core.py", "scripts/check_core_absent.py")
    ungated = live.replace(
        "scripts/analyze_arm_separation.py", "scripts/analyze_arm_separation_absent.py"
    )

    dropped = score("B1_CONTRIBUTION_GATE_BOUND", without_rule, observed)
    routed = score("B1_CONTRIBUTION_GATE_BOUND", dead, observed)
    weakened = score("B1_CONTRIBUTION_GATE_BOUND", ungated, observed)

    return {
        "old_strength_dropped_is_refused": not dropped["old_strengths_held"],
        "dead_route_is_refused": bool(routed["dead_routes"]),
        "erased_guard_loses_dominance": weakened["detected_count"] <= b0_count,
    }


def compare(temp: Path) -> dict[str, Any]:
    bodies = read_arms()
    subject = build_subject(temp)
    observed = exercise_guards(subject)
    results = {name: score(name, bodies[name], observed) for name in ARM_ORDER}

    for name, row in results.items():
        if not row["old_strengths_held"]:
            raise ProofError(f"BLOCKED_OLD_STRENGTH_LOST {name}: {row['old_strengths']}")
        if row["dead_routes"]:
            raise ProofError(f"BLOCKED_DEAD_ROUTE {name}: {row['dead_routes']}")

    counts = [results[name]["detected_count"] for name in ARM_ORDER]
    if counts != sorted(counts) or len(set(counts)) != len(counts):
        raise ProofError(f"treatment identity drift: detection is not strictly ordered {counts}")

    planted = mutations(bodies, observed)
    if not all(planted.values()):
        raise ProofError(f"planted mutation survived the scorer: {planted}")

    return {
        "schema": "repository-capability-audit/refactor-proof-ab/v1",
        "issue": 351,
        "history": {
            "skill_body_revisions": 3,
            "material_restructuring": "NONE_IN_HISTORY",
            "note": "Every diff between the three revisions is a pure append; "
                    "REFACTOR_AS_LANDED is the registry's role name for the first "
                    "landed revision after the canonical one, not a restructuring.",
        },
        "matched_task": {
            "same_subject": True,
            "same_oracles": sorted(GUARDS),
            "same_budget_seconds": TIMEOUT_SECONDS,
            "carrier": "local python3 subprocess; no network, no model, no host binary",
        },
        "guard_controls": observed,
        "results": results,
        "detection_ranking": ARM_ORDER,
        "planted_mutations": planted,
        "denominator": {
            "arms_scored": len(ARM_ORDER),
            "undetected_defects_retained": True,
            "superseded_arms_retained": True,
            "failed_stale_blocked_cancelled_retained": True,
        },
        "live_model_runtime_ab": "NOT_EXERCISED",
        "live_model_runtime_owner_issue": 256,
        "delivery_and_merge_authority": False,
    }


def selftest() -> int:
    """Cheap verification face: run the planted mutations without the subject build."""
    try:
        bodies = read_arms()
        stub = {defect: {"clean_exit": 0, "planted_exit": 2} for defect in GUARDS}
        planted = mutations(bodies, stub)
    except (ProofError, OSError, ValueError) as exc:
        print(f"REFACTOR-PROOF-AB-SELFTEST-RED {exc}", file=sys.stderr)
        return 2
    if not all(planted.values()):
        print(f"REFACTOR-PROOF-AB-SELFTEST-RED mutation survived: {planted}", file=sys.stderr)
        return 2
    print(f"REFACTOR-PROOF-AB-SELFTEST-GREEN {len(planted)} planted mutations refused; "
          "frozen treatment blobs match history")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true",
                        help="run only the planted-mutation controls")
    parser.add_argument("--output", type=Path, help="write the report JSON here")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()

    try:
        with tempfile.TemporaryDirectory(prefix="rca-refactor-proof-") as raw:
            temp = Path(raw)
            report = compare(temp)
        if temp.exists():
            raise ProofError(f"residue: {temp} survived the run")
    except (ProofError, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"REFACTOR-PROOF-AB-RED {exc}", file=sys.stderr)
        return 2

    report["cleanup"] = "CLEAN"
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload)
    print(
        "REFACTOR-PROOF-AB-GREEN matched hermetic task closed on one subject; "
        f"detection {'<'.join(str(report['results'][a]['detected_count']) for a in ARM_ORDER)} "
        "of 3; every old strength held in every arm; "
        f"{len(report['planted_mutations'])} planted mutations refused; "
        "live model/runtime uplift NOT_EXERCISED (owner #256)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
