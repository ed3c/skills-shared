#!/usr/bin/env python3
"""Frozen deterministic A/B proof for the github-delivery-loop generalization.

Three treatments of one subject -- this Skill's body -- scored on the same
criteria and run against the same matched task:

    A   OLD_CANONICAL        the GitHub-specific body before #242
    B0  REFACTOR_AS_LANDED   the generalized DL-01..DL-09 core exactly as it landed
    B1  REPAIRED_CANDIDATE   the live SKILL.md

A and B0 are frozen fixtures pinned by Git blob identity; their bytes are the
bytes history recorded, and they are evidence rather than implementation. B1 is
the live body, so it is never pinned here -- when it changes, it is measured
again rather than re-frozen against itself.

This is a structural and executable-contract experiment. It proves nothing about
model behavior, provider runtime, or delivery: no network, no forge, no
credentials, and every subprocess runs against a matched local tree.

The regression it keeps in the denominator is real and dated. #242 generalized
the core and dropped the index-discipline claim from the body; commit 9a14f52
then had to index `tests/procedural-core/` in `tests/README.md`, which #242 had
added without naming, and that gap surfaced only on merge. B1 restores the claim
and binds the receipt shape gate; B0 stays exactly as it landed, regression
visible.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = Path("tests") / "refactor-proof" / "fixtures"

# Frozen by Git blob identity, taken from the commits that produced them:
#   A  = SKILL.md at bca8e5a~1 (pre-refactor canonical body)
#   B0 = SKILL.md at bca8e5a   ("refactor: generalize github-delivery-loop
#                                procedural core (#242)")
EXPECTED_BLOBS = {
    FIXTURE_DIR / "pre-refactor-SKILL.txt": "1e26bfae0630fa2635996380e05014bea8ecbf4c",
    FIXTURE_DIR / "refactor-as-landed-SKILL.txt": "3faf7ca0e35a651648e80b1ad486c1921cc1d6d4",
}

# The one strength the landed refactor dropped, and the one the repair added.
REGRESSED_CRITERION = "index_discipline_asserted"
REPAIR_CRITERION = "receipt_shape_gate_bound"

MATCHED_TREE = ("modules", "scripts", "tests", "evals.json", "README.md")


@dataclass(frozen=True)
class Arm:
    name: str
    role: str
    path: Path
    text: str


class ProofError(RuntimeError):
    pass


def git_blob_sha(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def load_core_checker(root: Path):
    """Reuse the Skill's own portable-core contract instead of restating it."""
    path = root / "scripts" / "check_procedural_core.py"
    spec = importlib.util.spec_from_file_location("gdl_check_procedural_core", path)
    if spec is None or spec.loader is None:
        raise ProofError(f"cannot load portable-core checker: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def score(text: str, core_checker) -> dict[str, bool]:
    lower = text.casefold()
    try:
        core = core_checker.bounded_core(text)
    except ValueError:
        core = None

    law_rows = [line for line in text.splitlines() if line.startswith("| DL-L")]
    laws_executable = (
        all(law in text for law in core_checker.LAW_IDS)
        and len(law_rows) == len(core_checker.LAW_IDS)
        and all(
            any(f"| {law} |" in row and "`" in row and ("python3 " in row or "bash " in row) for row in law_rows)
            for law in core_checker.LAW_IDS
        )
    )

    return {
        # Introduced by the refactor.
        "portable_core_forge_neutral": core is not None
        and not any(
            core_checker.re.search(pattern, core, flags=core_checker.re.IGNORECASE)
            for pattern, _label in core_checker.FORBIDDEN_CORE_PATTERNS
        ),
        "procedure_atoms_enumerated": core is not None
        and all(atom in core for atom in core_checker.ATOM_IDS),
        "hard_laws_executable": laws_executable,
        # Old strengths that had to survive the refactor. Either the concrete
        # pre-refactor phrasing or its portable successor earns the point; the
        # criterion is the guarantee, not the wording that carried it.
        "absence_distinguished_from_refusal": "缺席，不是拒絕" in text
        or all(state in text for state in core_checker.EVIDENCE_STATES),
        "local_and_remote_evidence_distinct": "不得混稱" in text
        or "remote/provider evidence are distinct" in lower,
        "integration_authority_external": "人類 admit" in text
        or "external authority" in lower,
        # Held by A, dropped by B0, restored by B1.
        REGRESSED_CRITERION: "tests/index/verify.sh" in text
        and ("單向失效" in text or "fails one way only" in lower),
        # Added by B1.
        REPAIR_CRITERION: "delivery_receipt.schema.json" in text,
    }


def dominates(candidate: dict[str, bool], baseline: dict[str, bool]) -> bool:
    return all((not baseline[key]) or candidate[key] for key in baseline) and any(
        candidate[key] and not baseline[key] for key in baseline
    )


def run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=None if cwd is None else str(cwd),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def matched_task(arm: Arm, root: Path, scratch: Path) -> dict[str, object]:
    """Run the same two local oracles against every treatment.

    The tree is matched by construction: every arm gets the same `modules/`,
    `scripts/`, `tests/` and `evals.json` through symlinks, and only `SKILL.md`
    differs. Real subprocesses, fixed argv, zero network.
    """
    arm_root = scratch / arm.name
    arm_root.mkdir(parents=True)
    for entry in MATCHED_TREE:
        source = root / entry
        if source.exists():
            (arm_root / entry).symlink_to(source)
    (arm_root / "SKILL.md").write_text(arm.text, encoding="utf-8")

    core = run(
        [sys.executable, str(arm_root / "scripts" / "check_procedural_core.py"), "--root", str(arm_root)]
    )

    # Route oracle: does this body name a receipt shape gate that, executed,
    # actually refuses a receipt every semantic assertion would have accepted?
    if "delivery_receipt.schema.json" not in arm.text:
        shape = {"state": "NOT_IMPLEMENTED", "reason": "body names no receipt shape gate"}
    else:
        probe = arm_root / "receipt-shape-probe"
        shutil.copytree(root / "tests" / "check-receipt" / "fixtures" / "good", probe)
        receipt_path = probe / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["pr_url"] = receipt["pr_urls"][0]
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        result = run(
            [
                sys.executable,
                str(arm_root / "scripts" / "github_delivery.py"),
                "check",
                "--registry",
                str(probe / "registry.json"),
            ]
        )
        refused = result.returncode != 0 and "RECEIPT-SHAPE" in result.stderr
        shape = {
            "state": "PASS" if refused else "FAIL",
            "reason": "planted out-of-schema field refused" if refused else "planted field accepted",
            "exit": result.returncode,
        }

    return {
        "portable_core_contract": {"state": "PASS" if core.returncode == 0 else "FAIL", "exit": core.returncode},
        "receipt_shape_route": shape,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(argv)
    root = args.skill_root.resolve()

    try:
        for relative, expected in EXPECTED_BLOBS.items():
            path = root / relative
            observed = git_blob_sha(path.read_text(encoding="utf-8"))
            if observed != expected:
                print(
                    f"DELIVERY-REFACTOR-AB-RED frozen treatment drift {relative.name}: "
                    f"expected={expected} observed={observed}",
                    file=sys.stderr,
                )
                return 2

        core_checker = load_core_checker(root)
        arms = [
            Arm(
                "A_OLD_CANONICAL",
                "OLD_CANONICAL",
                root / FIXTURE_DIR / "pre-refactor-SKILL.txt",
                (root / FIXTURE_DIR / "pre-refactor-SKILL.txt").read_text(encoding="utf-8"),
            ),
            Arm(
                "B0_REFACTOR_AS_LANDED",
                "REFACTOR_AS_LANDED",
                root / FIXTURE_DIR / "refactor-as-landed-SKILL.txt",
                (root / FIXTURE_DIR / "refactor-as-landed-SKILL.txt").read_text(encoding="utf-8"),
            ),
            Arm(
                "B1_INDEX_AND_SHAPE_REPAIRED",
                "REPAIRED_CANDIDATE",
                root / "SKILL.md",
                (root / "SKILL.md").read_text(encoding="utf-8"),
            ),
        ]
    except (OSError, UnicodeError, ProofError) as error:
        print(f"DELIVERY-REFACTOR-AB-RED unusable treatment: {error}", file=sys.stderr)
        return 2

    results = {arm.name: score(arm.text, core_checker) for arm in arms}
    old = results["A_OLD_CANONICAL"]
    landed = results["B0_REFACTOR_AS_LANDED"]
    current = results["B1_INDEX_AND_SHAPE_REPAIRED"]

    if not old[REGRESSED_CRITERION]:
        print(
            f"DELIVERY-REFACTOR-AB-RED old treatment never held {REGRESSED_CRITERION}; "
            "the claimed regression is fabricated",
            file=sys.stderr,
        )
        return 2
    if landed[REGRESSED_CRITERION]:
        print(
            f"DELIVERY-REFACTOR-AB-RED as-landed treatment still holds {REGRESSED_CRITERION}; "
            "the scorer cannot see the regression it exists to expose",
            file=sys.stderr,
        )
        return 2
    if not current[REGRESSED_CRITERION]:
        print(
            f"DELIVERY-REFACTOR-AB-RED repaired candidate did not restore {REGRESSED_CRITERION}",
            file=sys.stderr,
        )
        return 2
    if not current[REPAIR_CRITERION]:
        print(
            f"DELIVERY-REFACTOR-AB-RED repaired candidate did not bind {REPAIR_CRITERION}",
            file=sys.stderr,
        )
        return 2

    survivors = {key: value for key, value in old.items() if key != REGRESSED_CRITERION}
    if not dominates(landed, survivors):
        lost = [key for key in survivors if survivors[key] and not landed[key]]
        print(
            f"DELIVERY-REFACTOR-AB-RED B0 lost old strengths beyond the known regression: {lost}",
            file=sys.stderr,
        )
        return 2
    if not dominates(current, landed) or not dominates(current, old):
        lost = [key for key in old if old[key] and not current[key]]
        print(
            f"DELIVERY-REFACTOR-AB-RED B1 does not dominate every prior treatment; regressions={lost}",
            file=sys.stderr,
        )
        return 2

    with tempfile.TemporaryDirectory(prefix="gdl-refactor-ab-") as raw_scratch:
        scratch = Path(raw_scratch)
        try:
            tasks = {arm.name: matched_task(arm, root, scratch) for arm in arms}
        except (OSError, subprocess.SubprocessError) as error:
            print(f"DELIVERY-REFACTOR-AB-RED matched task could not run: {error}", file=sys.stderr)
            return 2
    residue_removed = not scratch.exists()

    expected_task = {
        "A_OLD_CANONICAL": ("FAIL", "NOT_IMPLEMENTED"),
        "B0_REFACTOR_AS_LANDED": ("PASS", "NOT_IMPLEMENTED"),
        "B1_INDEX_AND_SHAPE_REPAIRED": ("PASS", "PASS"),
    }
    for name, (core_state, shape_state) in expected_task.items():
        observed = (
            tasks[name]["portable_core_contract"]["state"],
            tasks[name]["receipt_shape_route"]["state"],
        )
        if observed != (core_state, shape_state):
            print(
                f"DELIVERY-REFACTOR-AB-RED matched task disagrees for {name}: "
                f"expected={(core_state, shape_state)} observed={observed}",
                file=sys.stderr,
            )
            return 2

    report = {
        "schema": "github-delivery-loop/refactor-ab/v1",
        "evidence_scope": "deterministic structural and executable-contract closure on a matched local tree",
        "network": "NOT_EXERCISED",
        "live_model_runtime": "NOT_EXERCISED",
        "delivery_and_merge_authority": "HUMAN_ADMIT_REQUIRED",
        "subjects": {
            arm.name: {
                "role": arm.role,
                "path": arm.path.relative_to(root).as_posix(),
                "blob_sha": git_blob_sha(arm.text),
            }
            for arm in arms
        },
        "results": results,
        "totals": {name: sum(values.values()) for name, values in results.items()},
        "matched_task": tasks,
        "denominator": {
            "as_landed_regression_retained": True,
            "treatments_scored": len(arms),
        },
        "cleanup": {"scratch_arms_removed": residue_removed},
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print(
        "DELIVERY-REFACTOR-AB-GREEN A held the index-discipline claim; B0 dropped it while adding the "
        "portable core; B1 restores it, binds the receipt shape gate and dominates every prior treatment; "
        "live model/provider A/B and delivery authority NOT_EXERCISED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
