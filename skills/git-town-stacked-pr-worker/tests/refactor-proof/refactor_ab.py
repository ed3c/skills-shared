#!/usr/bin/env python3
"""Frozen deterministic A/B plus a matched hermetic task for the #270 refactor.

Real history, not an invented experiment. `git log --follow` on this Skill's
body finds exactly one material refactor: `d757a5c` "Refactor remaining Skill
procedural cores and control-plane contracts (#270)" replaced the Git-Town/
GitHub monolith with the portable stacked-branch core plus
`modules/domain-profile.md`. The three historical arms are that commit's
parent, that commit, and the body as it stood before this proof landed; the
fourth arm is the live `SKILL.md`.

Every historical arm is a frozen fixture and the newest arm is the live body,
so a treatment has exactly one immutable subject. The blobs are recomputed on
every run, which is what makes editing a treatment to improve its score turn
the suite red instead of green.

What the scorer measures is structural and executable-contract only. No model,
no provider, no forge, no network: `L4_MATCHED_LIVE_MODEL_RUNTIME` stays
NOT_EXERCISED and is not inferable from anything below.

Exit codes: 0 green, 2 a refused claim, 64 unusable input.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

SKILL_ROOT = Path(__file__).resolve().parents[2]
SKILL_NAME = SKILL_ROOT.name
REPO_ROOT = SKILL_ROOT.parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

OLD = FIXTURES / "pre-refactor-SKILL.txt"
LANDED = FIXTURES / "refactor-as-landed-SKILL.txt"
MOLECULAR = FIXTURES / "molecular-index-bound-SKILL.txt"
CURRENT = SKILL_ROOT / "SKILL.md"

# Frozen at the exact bytes history holds, so a fixture edited to win is a
# different file and the run refuses before scoring anything.
EXPECTED_GIT_BLOBS = {
    OLD: "36d894d756ceca6d754b4c248b70680c7d199148",
    LANDED: "714f1b0e3abb6d569f59c0eef18c09318d0886cf",
    MOLECULAR: "b06742db95cff1e43ed8eeae7db451012b3a2fb6",
}

A_OLD = "A_OLD_CANONICAL"
B0_LANDED = "B0_REFACTOR_AS_LANDED"
B1_MOLECULAR = "B1_MOLECULAR_INDEX_BOUND"
B2_REPAIRED = "B2_OWNED_GATE_ROUTE_REPAIRED"
ARMS = (A_OLD, B0_LANDED, B1_MOLECULAR, B2_REPAIRED)

# The two strengths #270 dropped from the whole Skill surface, not merely from
# SKILL.md. Everything else A claimed survives somewhere a reader still reaches:
# the Worker outcome vocabulary and the credential refusal in SYSTEM_PROMPT.md,
# the read order and the reference routes in README.md, the repo-owned
# inventory in modules/domain-profile.md. These two are reachable from nowhere.
DROPPED_BY_LANDED_REFACTOR = ("owned_suite_runner_routed", "shared_body_shadowing_refused")
GAINED_BY_LANDED_REFACTOR = (
    "portable_core_bounded",
    "core_laws_enumerated",
    "domain_module_trigger_routed",
    "core_boundary_assertion_executable",
)

# Everything validate() in check_publication_boundary.py reads, plus what the
# core-boundary manifest reads. Linked rather than copied so every arm gets
# byte-identical inputs and only SKILL.md differs.
MATCHED_INPUTS = (
    "SYSTEM_PROMPT.md",
    "PUBLICATION_POLICY.md",
    "evals.json",
    "references",
    "scripts",
    "tests",
    "modules",
)


class ProofError(Exception):
    pass


@dataclass(frozen=True)
class Arm:
    name: str
    skill: str


def git_blob_sha(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def portable_core(text: str) -> str | None:
    start = "<!-- PORTABLE_CORE_START -->"
    end = "<!-- PORTABLE_CORE_END -->"
    if start not in text or end not in text:
        return None
    return text.split(start, 1)[1].split(end, 1)[0]


def score(arm: Arm) -> dict[str, bool]:
    skill = arm.skill
    lower = skill.casefold()
    core = portable_core(skill)

    # --- strengths the old canonical body already had -------------------
    publication_boundary_composed = (
        "Compose the target Agent instruction surface from the **contents**, not file paths"
        in skill
        and all(intent in skill for intent in ("initial-pr", "ready-for-review", "batched-repair"))
        and "billing-open" in skill
    )
    background_sync_never_pushes = (
        "Background synchronization may never invoke `git town sync --push`" in skill
    )
    sync_is_not_correctness = (
        "does not prove implementation correctness" in lower
        or "synchronization is not correctness" in lower
    )
    sibling_over_artificial_stack = (
        "artificial serial stack" in lower or "path-disjoint sibling work must not be serialized" in lower
    )
    one_writer_one_lease = (
        ("one writer" in lower or "one branch writer lease" in lower)
        and ("lease" in lower)
    )
    evidence_states_preserved = all(
        state in skill
        for state in ("PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED", "SKIPPED_BY_POLICY")
    )

    # --- the two strengths the landed refactor dropped -------------------
    owned_suite_runner_routed = "tests/run-all.sh" in skill
    shared_body_shadowing_refused = (
        "shadow the shared canonical body" in lower and "governance error" in lower
    )

    # --- what the refactor bought ---------------------------------------
    portable_core_bounded = core is not None
    core_laws_enumerated = core is not None and all(
        f"CORE-LAW-{index:03d}" in core for index in range(1, 6)
    )
    domain_module_trigger_routed = core is not None and (
        "modules/domain-profile.md" in core and "only when" in core.casefold()
    )
    core_boundary_assertion_executable = (
        f"python3 scripts/check_skill_core_boundaries.py --skill {SKILL_NAME}" in skill
    )

    # --- what B1 added on top of the landed refactor ---------------------
    molecular_stack_index_law = (
        "CORE-LAW-006" in skill and "MOLECULAR_STACK_INDEX.md" in skill
    )

    return {
        "publication_boundary_composed": publication_boundary_composed,
        "background_sync_never_pushes": background_sync_never_pushes,
        "sync_is_not_correctness": sync_is_not_correctness,
        "sibling_over_artificial_stack": sibling_over_artificial_stack,
        "one_writer_one_lease": one_writer_one_lease,
        "evidence_states_preserved": evidence_states_preserved,
        "owned_suite_runner_routed": owned_suite_runner_routed,
        "shared_body_shadowing_refused": shared_body_shadowing_refused,
        "portable_core_bounded": portable_core_bounded,
        "core_laws_enumerated": core_laws_enumerated,
        "domain_module_trigger_routed": domain_module_trigger_routed,
        "core_boundary_assertion_executable": core_boundary_assertion_executable,
        "molecular_stack_index_law": molecular_stack_index_law,
    }


def dominates(candidate: dict[str, bool], baseline: dict[str, bool]) -> bool:
    return all((not baseline[key]) or candidate[key] for key in baseline) and any(
        candidate[key] and not baseline[key] for key in baseline
    )


def read_arms(current_text: str | None = None) -> dict[str, Arm]:
    for path, expected in EXPECTED_GIT_BLOBS.items():
        observed = git_blob_sha(path.read_text(encoding="utf-8"))
        if observed != expected:
            raise ProofError(
                f"frozen treatment drift {path.name}: expected={expected} observed={observed}"
            )
    live = CURRENT.read_text(encoding="utf-8") if current_text is None else current_text
    return {
        A_OLD: Arm(A_OLD, OLD.read_text(encoding="utf-8")),
        B0_LANDED: Arm(B0_LANDED, LANDED.read_text(encoding="utf-8")),
        B1_MOLECULAR: Arm(B1_MOLECULAR, MOLECULAR.read_text(encoding="utf-8")),
        B2_REPAIRED: Arm(B2_REPAIRED, live),
    }


def assert_treatment_relations(results: dict[str, dict[str, bool]]) -> None:
    old, landed = results[A_OLD], results[B0_LANDED]
    molecular, repaired = results[B1_MOLECULAR], results[B2_REPAIRED]

    for key in DROPPED_BY_LANDED_REFACTOR:
        if not old[key]:
            raise ProofError(f"old canonical treatment never held {key}; the regression story is wrong")
        if landed[key] or molecular[key]:
            raise ProofError(f"scorer failed to expose the landed regression on {key}")
        # Asserted by name: domination alone would let a candidate that drops a
        # restored strength pass whenever the baseline never held it either.
        if not repaired[key]:
            raise ProofError(f"repaired candidate does not restore {key}")
    for key in GAINED_BY_LANDED_REFACTOR:
        if old[key]:
            raise ProofError(f"old canonical treatment already held {key}; it is not a refactor gain")
        if not landed[key]:
            raise ProofError(f"landed refactor did not deliver {key}")
    if landed["molecular_stack_index_law"] or not molecular["molecular_stack_index_law"]:
        raise ProofError("B1 treatment identity drift: CORE-LAW-006 is B1's, not B0's")
    if dominates(landed, old) or dominates(molecular, old):
        raise ProofError("landed refactor is being scored as if it lost nothing")
    for baseline_name in (A_OLD, B0_LANDED, B1_MOLECULAR):
        if not dominates(repaired, results[baseline_name]):
            regressed = [
                key for key in results[baseline_name] if results[baseline_name][key] and not repaired[key]
            ]
            raise ProofError(f"repaired candidate does not dominate {baseline_name}; regressions={regressed}")


# ---------------------------------------------------------------------------
# Matched hermetic task
# ---------------------------------------------------------------------------


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        command, cwd=REPO_ROOT, capture_output=True, text=True, check=False, env=environment
    )


def build_matched_root(scratch: Path, arm: Arm) -> Path:
    """One scratch repository per arm: identical inputs, only SKILL.md differs."""
    skill_root = scratch / "skills" / SKILL_NAME
    skill_root.mkdir(parents=True)
    for relative in MATCHED_INPUTS:
        source = SKILL_ROOT / relative
        if not source.exists():
            raise ProofError(f"matched input absent: {relative}")
        (skill_root / relative).symlink_to(source)
    (skill_root / "SKILL.md").write_text(arm.skill, encoding="utf-8")
    return skill_root


def hermetic_task(arms: dict[str, Arm]) -> dict[str, Any]:
    """Same oracles, same inputs, same budget; the only variable is the body.

    Both oracles are real subprocesses of the repository's own checkers, not a
    re-implementation of what they would have said.
    """
    manifest = REPO_ROOT / "evals" / "skill-core-boundaries.json"
    if not manifest.is_file():
        raise ProofError(f"core-boundary manifest absent: {manifest}")

    results: dict[str, Any] = {}
    scratch_roots: list[Path] = []
    with tempfile.TemporaryDirectory(
        prefix="gtsp-refactor-proof-", dir=os.environ.get("TMPDIR", "/tmp")
    ) as raw:
        for name in ARMS:
            scratch = Path(raw) / name
            scratch_roots.append(scratch)
            skill_root = build_matched_root(scratch, arms[name])
            core = run([
                sys.executable,
                str(REPO_ROOT / "scripts/check_skill_core_boundaries.py"),
                "--root", str(scratch),
                "--manifest", str(manifest),
                "--skill", SKILL_NAME,
            ])
            publication = run([
                sys.executable,
                str(SKILL_ROOT / "scripts/check_publication_boundary.py"),
                "--root", str(skill_root),
            ])
            results[name] = {
                "treatment_blob": git_blob_sha(arms[name].skill),
                "core_boundary_oracle": "PASS" if core.returncode == 0 else "FAIL",
                "publication_boundary_oracle": "PASS" if publication.returncode == 0 else "FAIL",
            }
        # The gate the retained strength rests on has to be able to go red, or
        # every arm's PASS on it means nothing. Run against the live arm, which
        # is the only one whose bytes the current repository can still change.
        selftest = run([
            sys.executable,
            str(SKILL_ROOT / "scripts/check_publication_boundary.py"),
            "--root", str(Path(raw) / B2_REPAIRED / "skills" / SKILL_NAME),
            "--selftest",
        ])
        results[B2_REPAIRED]["publication_gate_mutations_killed"] = selftest.returncode == 0

    residue = sorted(str(path) for path in scratch_roots if path.exists())
    if residue:
        raise ProofError(f"cleanup incomplete, scratch roots survive: {residue}")

    if results[A_OLD]["core_boundary_oracle"] != "FAIL":
        raise ProofError("old canonical body cannot satisfy a portable-core boundary it predates")
    for name in (B0_LANDED, B1_MOLECULAR, B2_REPAIRED):
        if results[name]["core_boundary_oracle"] != "PASS":
            raise ProofError(f"{name} failed the core-boundary oracle")
    for name in ARMS:
        if results[name]["publication_boundary_oracle"] != "PASS":
            raise ProofError(f"{name} lost the publication-boundary contract the refactor had to retain")
    if not results[B2_REPAIRED]["publication_gate_mutations_killed"]:
        raise ProofError("publication-boundary gate did not kill its planted mutations")
    return {"cleanup": "CLEAN", "network": "NONE", "arms": results}


# ---------------------------------------------------------------------------
# Controls: the entrypoint has to be able to go red
# ---------------------------------------------------------------------------


def selftest() -> list[str]:
    failures: list[str] = []

    def expect_red(name: str, action: Callable[[], object]) -> None:
        try:
            action()
        except ProofError:
            return
        failures.append(f"control did not turn red: {name}")

    original = EXPECTED_GIT_BLOBS[OLD]

    def drift() -> object:
        EXPECTED_GIT_BLOBS[OLD] = git_blob_sha("bytes this treatment never had")
        try:
            return read_arms()
        finally:
            EXPECTED_GIT_BLOBS[OLD] = original

    expect_red("FROZEN_TREATMENT_BYTES_DRIFTED", drift)

    live = CURRENT.read_text(encoding="utf-8")
    for name, needle in (
        ("CANDIDATE_DROPS_SUITE_RUNNER_ROUTE", "[`tests/run-all.sh`](tests/run-all.sh)"),
        ("CANDIDATE_DROPS_SHARED_BODY_LAW", "shadow the shared canonical body"),
    ):
        if needle not in live:
            failures.append(f"control cannot be planted, live body lacks: {needle!r}")
            continue
        mutated = live.replace(needle, "the suite", 1)
        expect_red(name, lambda text=mutated: assert_treatment_relations(
            {arm: score(value) for arm, value in read_arms(text).items()}
        ))

    # A control that only ever proves red is worth nothing: the unmutated body
    # must still be green through the same path.
    try:
        assert_treatment_relations({arm: score(value) for arm, value in read_arms().items()})
    except ProofError as error:
        failures.append(f"positive control is already red: {error}")
    return failures


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args != ["--selftest"]:
        print(f"usage: {Path(__file__).name} [--selftest]", file=sys.stderr)
        return 64
    try:
        if args == ["--selftest"]:
            failures = selftest()
            if failures:
                for failure in failures:
                    print(f"GTSP-REFACTOR-PROOF-RED {failure}", file=sys.stderr)
                return 2
            print("GTSP-REFACTOR-PROOF-SELFTEST-GREEN 3 planted control(s) killed")
            return 0

        arms = read_arms()
        results = {name: score(arm) for name, arm in arms.items()}
        assert_treatment_relations(results)
        task = hermetic_task(arms)
    except ProofError as error:
        print(f"GTSP-REFACTOR-PROOF-RED {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"GTSP-REFACTOR-PROOF-FATAL {error}", file=sys.stderr)
        return 64

    report = {
        "schema": "git-town-stacked-pr-worker/refactor-ab/v1",
        "refactor_commit": "d757a5cc66f5062f638af532078f8643b1175647",
        "refactor_issue": 270,
        "evidence_scope": "deterministic structural and executable-contract only",
        "subjects": {name: git_blob_sha(arm.skill) for name, arm in arms.items()},
        "results": results,
        "totals": {name: sum(values.values()) for name, values in results.items()},
        "landed_refactor_regression_exposed": True,
        "regressed_criteria": list(DROPPED_BY_LANDED_REFACTOR),
        "retained_elsewhere_not_claimed_as_loss": {
            "stable_worker_outcomes": "SYSTEM_PROMPT.md",
            "credential_and_secret_refusal": "SYSTEM_PROMPT.md",
            "mandatory_read_order": "README.md",
            "adoption_eval_and_profile_routes": "README.md",
            "repo_owned_inventory": "modules/domain-profile.md",
            "git_town_version_identity": "SYSTEM_PROMPT.md",
        },
        "matched_hermetic_task": task,
        "behavioral_model_uplift": "NOT_EXERCISED",
        "live_git_town_runtime": "NOT_EXERCISED",
        "remote_publication": "NOT_EXERCISED",
        "merge_authority": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print(
        "GTSP-REFACTOR-PROOF-GREEN #270 exposed on two dropped strengths; B2 restores both and "
        "dominates every prior treatment; matched hermetic task closed with no network and no residue; "
        "live model/Git Town/publication uplift NOT_EXERCISED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
