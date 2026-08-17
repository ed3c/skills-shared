#!/usr/bin/env python3
"""Mutation controls for the portable refactor-proof and golden registry mechanisms."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_CONTRACT = ROOT / "scripts/check_refactor_proof.py"
CHECK_REGISTRY = ROOT / "scripts/check_golden_proof_registry.py"


def run(argv: list[str]) -> int:
    return subprocess.run(argv, text=True, capture_output=True, check=False).returncode


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def blob(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def contract_controls(temp: Path) -> dict[str, bool]:
    base = json.loads((ROOT / "references/example-refactor-proof.json").read_text(encoding="utf-8"))
    controls = {}

    def rejected(name: str, value) -> None:
        path = temp / f"contract-{name}.json"
        dump(path, value)
        controls[name] = run([sys.executable, str(CHECK_CONTRACT), "--contract", str(path)]) != 0

    bad = copy.deepcopy(base)
    bad["treatments"] = [row for row in bad["treatments"] if row["role"] != "REFACTOR_AS_LANDED"]
    rejected("missing_as_landed", bad)

    bad = copy.deepcopy(base)
    bad["treatments"][0]["blob_sha"] = "x" * 40
    rejected("invalid_frozen_identity", bad)

    bad = copy.deepcopy(base)
    bad["protected_strengths"][0]["new_assertion"] = ""
    rejected("old_strength_unasserted", bad)

    bad = copy.deepcopy(base)
    bad["proof_layers"]["L2_EXECUTABLE_CONTRACT"] = "NOT_EXERCISED"
    rejected("layer_gap", bad)

    bad = copy.deepcopy(base)
    bad["proof_layers"]["L4_MATCHED_LIVE_MODEL_RUNTIME"] = "PASS"
    rejected("false_live_pass_gap", bad)

    bad = copy.deepcopy(base)
    bad["matched_task"]["same_budget"] = False
    rejected("unfair_budget", bad)

    bad = copy.deepcopy(base)
    bad["denominator_policy"]["stale_retained"] = False
    rejected("stale_erased", bad)

    bad = copy.deepcopy(base)
    bad["cleanup"]["worktrees"] = "NOT_EXERCISED"
    rejected("dirty_cleanup", bad)

    bad = copy.deepcopy(base)
    bad["authority"]["merge"] = True
    rejected("merge_authority", bad)
    return controls


def fake_repo(temp: Path) -> tuple[Path, Path]:
    repo = temp / "repo"
    owner = repo / "skills/owner"
    tests = owner / "tests"
    fixtures = tests / "fixtures"
    fixtures.mkdir(parents=True)
    (owner / "SKILL.md").write_text("owner\n", encoding="utf-8")
    (tests / "entry.py").write_text("print('entry')\n", encoding="utf-8")
    (tests / "run-all.sh").write_text("python3 \"$ROOT/tests/entry.py\"\nentry.py\n", encoding="utf-8")
    rows = []
    for name, role, text in [
        ("old.txt", "OLD_CANONICAL", "old\n"),
        ("as-landed.txt", "REFACTOR_AS_LANDED", "as-landed\n"),
        ("repaired.txt", "REPAIRED_CANDIDATE", "repaired\n"),
    ]:
        path = fixtures / name
        path.write_text(text, encoding="utf-8")
        rows.append({"id": name, "role": role, "path": path.relative_to(repo).as_posix(), "blob_sha": blob(text)})
    registry = {
        "schema": "skill-refactor-proof-loop/golden-proof-registry/v1",
        "proofs": [{
            "id": "proof-v1",
            "owner_skill": "owner",
            "issue": 1,
            "pull_requests": [1],
            "entrypoint": "skills/owner/tests/entry.py",
            "runner": "skills/owner/tests/run-all.sh",
            "treatments": rows,
            "proof_layers": {
                "L0_SOURCE_FREEZE": "PASS",
                "L1_STRUCTURAL_REACHABILITY": "PASS",
                "L2_EXECUTABLE_CONTRACT": "PASS",
                "L3_HERMETIC_REAL_TASK": "PASS",
                "L4_MATCHED_LIVE_MODEL_RUNTIME": "NOT_EXERCISED",
                "L5_DELIVERY_AND_HUMAN_ADMIT": "HUMAN_ADMIT_REQUIRED"
            },
            "highest_layer": "L3_HERMETIC_REAL_TASK",
            "denominator": {
                "failed_retained": True,
                "stale_retained": True,
                "blocked_retained": True,
                "cancelled_retained": True,
                "superseded_retained": True
            },
            "cleanup": "CLEAN",
            "authority": {
                "provider_activation": False,
                "publication": False,
                "semantic_conflict_resolution": False,
                "merge": False,
                "release": False,
                "promotion": False,
                "rollback": False
            },
            "remaining_issues": [2]
        }]
    }
    path = temp / "registry-positive.json"
    dump(path, registry)
    return repo, path


def registry_controls(temp: Path) -> dict[str, bool]:
    repo, positive = fake_repo(temp)
    base = json.loads(positive.read_text(encoding="utf-8"))
    schema = ROOT / "references/golden-proof-registry.schema.json"
    command = [sys.executable, str(CHECK_REGISTRY), "--registry", str(positive), "--schema", str(schema), "--repo-root", str(repo)]
    if run(command) != 0:
        raise RuntimeError("positive fake registry did not pass")
    controls = {}

    def rejected(name: str, value, mutate_repo=None) -> None:
        local_repo = repo
        if mutate_repo:
            local_repo = temp / f"repo-{name}"
            shutil.copytree(repo, local_repo)
            mutate_repo(local_repo)
        path = temp / f"registry-{name}.json"
        dump(path, value)
        controls[name] = run([
            sys.executable,
            str(CHECK_REGISTRY),
            "--registry",
            str(path),
            "--schema",
            str(schema),
            "--repo-root",
            str(local_repo),
        ]) != 0

    bad = copy.deepcopy(base)
    bad["proofs"].append(copy.deepcopy(bad["proofs"][0]))
    rejected("duplicate_id", bad)

    bad = copy.deepcopy(base)
    bad["proofs"][0]["entrypoint"] = "skills/owner/tests/missing.py"
    rejected("missing_entrypoint", bad)

    def no_route(repo_root: Path) -> None:
        (repo_root / "skills/owner/tests/run-all.sh").write_text("echo no-route\n", encoding="utf-8")

    rejected("runner_hollow", copy.deepcopy(base), no_route)

    bad = copy.deepcopy(base)
    bad["proofs"][0]["treatments"][0]["blob_sha"] = "f" * 40
    rejected("blob_drift", bad)

    bad = copy.deepcopy(base)
    bad["proofs"][0]["proof_layers"]["L4_MATCHED_LIVE_MODEL_RUNTIME"] = "PASS"
    rejected("above_highest_pass", bad)

    bad = copy.deepcopy(base)
    bad["proofs"][0]["denominator"]["failed_retained"] = False
    rejected("denominator_erased", bad)

    bad = copy.deepcopy(base)
    bad["proofs"][0]["cleanup"] = "DIRTY"
    rejected("residue", bad)

    bad = copy.deepcopy(base)
    bad["proofs"][0]["authority"]["provider_activation"] = True
    rejected("provider_authority", bad)
    return controls


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="refactor-proof-selftest-") as raw:
        temp = Path(raw)
        controls = {**contract_controls(temp), **registry_controls(temp)}
    failed = sorted(name for name, killed in controls.items() if not killed)
    if failed:
        print(f"REFACTOR-PROOF-SELFTEST-RED survived={','.join(failed)}", file=sys.stderr)
        return 2
    print(f"REFACTOR-PROOF-SELFTEST-GREEN mutations={len(controls)} all refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
