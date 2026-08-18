#!/usr/bin/env python3
"""Frozen deterministic A/B/B1 for the dual-forge-repository-loop refactor.

The refactor under test is real: `d757a5c` ("Refactor remaining Skill procedural
cores and control-plane contracts", #270) replaced a 494-line host-specific
monolith with a 74-line portable core plus a 24-line domain profile. That commit
is the only material refactor `git log --follow` reports for this Skill body, so
its parent and its own bytes are the two historical treatments, frozen here by
Git blob identity and recomputed on every run.

What the refactor actually traded is the finding. It gained a bounded,
host-neutral core with numbered laws and an executable boundary assertion. It
also dropped three properties the monolith had: the mandatory runtime-identity
preflight, the routes from the body to this Skill's own deterministic
mechanisms, and the refusal to overwrite history. On the ten binary criteria
below the old body and the landed refactor tie at 7 -- which is the point. A
shorter, cleaner body is not evidence of preservation, and a total that ties
says nothing about which properties were kept.

B1 is the live `SKILL.md`: it keeps the three new properties and restores the
three dropped ones, so it is the first arm to dominate both predecessors.

The comparison is not scored on text alone. Each arm is materialised into its
own scratch tree where only `SKILL.md` differs -- every script, reference,
module and eval is the same file, reached by symlink -- and two real subprocess
oracles run against it:

    portable-core contract   scripts/check_skill_core_boundaries.py
    owned-route probe        every skill-scoped `scripts/*.py` route the body
                             names must resolve in that tree, and the routes
                             carrying a pinned `selftest` must exit 0

Zero network, no model, no provider, no forge, no CI. Fixtures and this
repository's own checkers only.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TESTS = Path(__file__).resolve().parent
SKILL_ROOT = TESTS.parents[1]
SKILL_NAME = SKILL_ROOT.name
REPO = SKILL_ROOT.parents[1]
MANIFEST = REPO / "evals" / "skill-core-boundaries.json"
BOUNDARY_CHECKER = REPO / "scripts" / "check_skill_core_boundaries.py"

FIXTURES = TESTS / "fixtures"
OLD = FIXTURES / "pre-refactor-SKILL.txt"
LANDED = FIXTURES / "refactor-as-landed-SKILL.txt"
CURRENT = SKILL_ROOT / "SKILL.md"

# Bytes taken from history, not authored here:
#   OLD    = d757a5c~1:skills/dual-forge-repository-loop/SKILL.md
#   LANDED = d757a5c:skills/dual-forge-repository-loop/SKILL.md
EXPECTED_GIT_BLOBS = {
    OLD: "bd3559e730c9a4f16c95d72b675d9c8cae4c9f7f",
    LANDED: "1e88ad5b1bf883de42ccc6bac83b75d56fe8b62d",
}

CORE_START = "<!-- PORTABLE_CORE_START -->"
CORE_END = "<!-- PORTABLE_CORE_END -->"
# The same tokens evals/skill-core-boundaries.json forbids inside this Skill's
# core. Duplicated deliberately: the criterion has to be scorable on a frozen
# historical body that predates the manifest entry.
HOST_TOKENS = ("github", "forgejo", "actions", "codex", "claude")
CORE_LAWS = tuple(f"CORE-LAW-{index:03d}" for index in range(1, 6))
BOUNDARY_ROUTE = f"python3 scripts/check_skill_core_boundaries.py --skill {SKILL_NAME}"
EVIDENCE_STATES = (
    "PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED",
    "NOT_EXERCISED", "SKIPPED_BY_POLICY", "HUMAN_ADMIT_REQUIRED",
)

ROUTE = re.compile(rf"(?:skills/{re.escape(SKILL_NAME)}/)?scripts/([a-z0-9_]+\.py)")
PREFIXED_ROUTE = re.compile(rf"skills/{re.escape(SKILL_NAME)}/scripts/([a-z0-9_]+\.py)")

# Routed mechanisms with a pinned, zero-network self-check. Arbitrary scripts are
# never invoked with a guessed argument: a producer would either refuse with an
# argparse status indistinguishable from a real failure, or worse, run.
PINNED_SELFTESTS = {
    "check_consumer_canary.py": ("selftest",),
    "check_prompt_baseline.py": ("selftest",),
    "check_scheduler_receipt.py": ("selftest",),
}


class ProofError(RuntimeError):
    pass


def git_blob_sha(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def frozen_drift(expected: dict[Path, str]) -> list[str]:
    """Return one message per treatment whose bytes no longer hash to its identity."""
    drift: list[str] = []
    for path, want in expected.items():
        got = git_blob_sha(path.read_text(encoding="utf-8"))
        if got != want:
            drift.append(f"{path.name}: expected={want} observed={got}")
    return drift


def portable_core(text: str) -> str | None:
    if CORE_START not in text or CORE_END not in text:
        return None
    return text.split(CORE_START, 1)[1].split(CORE_END, 1)[0]


def claimed_routes(text: str) -> list[str]:
    """Owned-mechanism routes the body claims.

    A route counts as claimed when it is written with this Skill's full path, or
    when a bare `scripts/<name>.py` names a file this Skill actually owns. A bare
    route to a repository-level script is not a claim on an owned mechanism, so
    the landed refactor's single `scripts/check_skill_core_boundaries.py` route
    is scored as "no owned mechanism routed" rather than as a broken one.
    """
    owned = {path.name for path in (SKILL_ROOT / "scripts").glob("*.py")}
    claimed = set(PREFIXED_ROUTE.findall(text))
    claimed |= {name for name in ROUTE.findall(text) if name in owned}
    return sorted(claimed)


def score(text: str) -> dict[str, bool]:
    lower = text.casefold()
    core = portable_core(text)
    core_lower = core.casefold() if core is not None else ""
    routes = claimed_routes(text)

    return {
        # --- old strengths the monolith held ---
        "plane_evidence_separation": (
            "neither plane proves the other" in lower
            or "one plane cannot proxy another" in lower
        ) and ("separate evidence lanes" in lower or "distinct evidence states" in lower),
        "exact_subject_binding": "exact subject" in lower or "exact commit sha" in lower,
        "evidence_state_vocabulary": all(state in text for state in EVIDENCE_STATES),
        "human_merge_authority_retained": (
            "does not create permission to merge" in lower
            or "create merge authority" in lower
            or "human-owned merge" in lower
        ),
        "runtime_identity_preflight_bound": (
            "references/runtime-identity-contract.md" in text
            and "before any repository mutation" in lower
            and "fails closed" in lower
        ),
        "owned_mechanism_routes_named": len(routes) >= 3,
        "history_overwrite_refused": (
            "force ref update" in lower or "push --force" in lower
        ) and ("history rewrite" in lower or "overwrit" in lower),
        # --- properties the refactor introduced ---
        "portable_core_host_neutral": core is not None and not any(
            token in core_lower.replace(BOUNDARY_ROUTE.casefold(), "")
            for token in HOST_TOKENS
        ),
        "numbered_core_laws_executable": core is not None and all(
            law in core for law in CORE_LAWS
        ) and BOUNDARY_ROUTE in core,
        "domain_module_routed": core is not None and "modules/domain-profile.md" in core,
    }


def dominates(candidate: dict[str, bool], baseline: dict[str, bool]) -> bool:
    return all((not baseline[k]) or candidate[k] for k in baseline) and any(
        candidate[k] and not baseline[k] for k in baseline
    )


def build_arm(root: Path, text: str, *, drop_script: str | None = None) -> Path:
    """Materialise one arm: identical tree, only SKILL.md differs.

    `scripts/` is rebuilt as per-file symlinks rather than one directory link so
    a planted control can withhold exactly one mechanism without touching the
    repository.
    """
    arm = root / "skills" / SKILL_NAME
    arm.mkdir(parents=True)
    for entry in sorted(SKILL_ROOT.iterdir()):
        if entry.name == "SKILL.md":
            continue
        if entry.name == "scripts":
            (arm / "scripts").mkdir()
            for script in sorted(entry.iterdir()):
                if script.name == drop_script:
                    continue
                (arm / "scripts" / script.name).symlink_to(script)
            continue
        (arm / entry.name).symlink_to(entry)
    (arm / "SKILL.md").write_text(text, encoding="utf-8")
    return arm


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True, timeout=300, check=False
    )


def core_contract_oracle(root: Path) -> str:
    """Run this repository's portable-core boundary checker against one arm."""
    result = run(
        [
            sys.executable, str(BOUNDARY_CHECKER),
            "--root", str(root), "--manifest", str(MANIFEST), "--skill", SKILL_NAME,
        ],
        cwd=REPO,
    )
    return "PASS" if result.returncode == 0 else "FAIL"


def owned_route_oracle(arm: Path, text: str) -> tuple[str, dict[str, object]]:
    """Resolve and execute the owned-mechanism routes the arm's body claims."""
    claimed = claimed_routes(text)
    detail: dict[str, object] = {"claimed": claimed}
    if not claimed:
        return "NOT_IMPLEMENTED", detail
    unresolved = [name for name in claimed if not (arm / "scripts" / name).is_file()]
    detail["unresolved"] = unresolved
    if unresolved:
        return "FAIL", detail
    executed = {
        name: run([sys.executable, str(arm / "scripts" / name), *args], cwd=arm).returncode
        for name, args in sorted(PINNED_SELFTESTS.items())
        if name in claimed
    }
    detail["executed"] = executed
    if not executed:
        return "FAIL", detail
    return ("PASS" if all(code == 0 for code in executed.values()) else "FAIL"), detail


def hermetic_task(arms: dict[str, str]) -> tuple[dict[str, dict[str, object]], list[str]]:
    """Run every arm against the same tree, contracts and oracles."""
    observed: dict[str, dict[str, object]] = {}
    controls: list[str] = []
    with tempfile.TemporaryDirectory(
        prefix="dual-forge-refactor-proof-", dir=os.environ.get("TMPDIR") or None
    ) as raw:
        scratch = Path(raw)
        for name, text in arms.items():
            root = scratch / name
            arm = build_arm(root, text)
            route_state, detail = owned_route_oracle(arm, text)
            observed[name] = {
                "portable_core_contract": core_contract_oracle(root),
                "owned_route_probe": route_state,
                "owned_route_detail": detail,
            }

        # Control 1: the same live body, one routed mechanism withheld. A body
        # whose routes are only readable stays green here; one whose routes are
        # resolved goes red.
        withheld = build_arm(
            scratch / "control-route-drift", arms["B1_ROUTES_AND_PREFLIGHT_RESTORED"],
            drop_script="check_dual_forge_contract.py",
        )
        state, _ = owned_route_oracle(withheld, arms["B1_ROUTES_AND_PREFLIGHT_RESTORED"])
        if state != "FAIL":
            controls.append(f"withheld routed mechanism was not detected: {state}")

        # Control 2: a candidate that keeps the new core but drops the restored
        # routes. Domination against A catches it, and it is asserted by name so
        # the reason stays legible when the criterion list grows.
        stripped = arms["B1_ROUTES_AND_PREFLIGHT_RESTORED"].split("## Owned executable mechanisms")[0]
        if score(stripped)["owned_mechanism_routes_named"]:
            controls.append("route-stripped candidate still scored the restored strength")
        if dominates(score(stripped), score(arms["A_OLD_CANONICAL"])):
            controls.append("route-stripped candidate still dominated the old canonical body")

        # Control 3: frozen bytes are evidence, so a drifted treatment must be
        # refused rather than rescored.
        mutated = scratch / "control-drift-SKILL.txt"
        mutated.write_text(OLD.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        if not frozen_drift({mutated: EXPECTED_GIT_BLOBS[OLD]}):
            controls.append("mutated frozen treatment passed the blob identity check")

    if scratch.exists():
        controls.append(f"scratch tree survived the run: {scratch}")
    return observed, controls


def main() -> int:
    try:
        drift = frozen_drift(EXPECTED_GIT_BLOBS)
        if drift:
            raise ProofError("frozen treatment drift: " + "; ".join(drift))

        arms = {
            "A_OLD_CANONICAL": OLD.read_text(encoding="utf-8"),
            "B0_REFACTOR_AS_LANDED": LANDED.read_text(encoding="utf-8"),
            "B1_ROUTES_AND_PREFLIGHT_RESTORED": CURRENT.read_text(encoding="utf-8"),
        }
        results = {name: score(text) for name, text in arms.items()}
        totals = {name: sum(values.values()) for name, values in results.items()}
        old, landed, restored = (
            results["A_OLD_CANONICAL"],
            results["B0_REFACTOR_AS_LANDED"],
            results["B1_ROUTES_AND_PREFLIGHT_RESTORED"],
        )

        regressed = (
            "runtime_identity_preflight_bound",
            "owned_mechanism_routes_named",
            "history_overwrite_refused",
        )
        introduced = (
            "portable_core_host_neutral",
            "numbered_core_laws_executable",
            "domain_module_routed",
        )
        missing_old = [key for key in regressed if not old[key]]
        if missing_old:
            raise ProofError(f"old canonical body did not hold its named strengths: {missing_old}")
        kept_by_landed = [key for key in regressed if landed[key]]
        if kept_by_landed:
            raise ProofError(f"B0 scorer failed to expose the landed regressions: {kept_by_landed}")
        missing_new = [key for key in introduced if not landed[key]]
        if missing_new:
            raise ProofError(f"B0 did not introduce its named new properties: {missing_new}")
        if dominates(landed, old):
            raise ProofError("B0 was credited with dominating the body it regressed against")
        restored_gap = [key for key in regressed + introduced if not restored[key]]
        if restored_gap:
            raise ProofError(f"B1 does not hold every named property: {restored_gap}")
        if not dominates(restored, old) or not dominates(restored, landed):
            lost = [key for key in old if (old[key] or landed[key]) and not restored[key]]
            raise ProofError(f"B1 does not dominate both predecessors; regressions={lost}")

        observed, controls = hermetic_task(arms)
        if controls:
            raise ProofError("planted control survived: " + "; ".join(controls))
        expected_oracles = {
            "A_OLD_CANONICAL": ("FAIL", "PASS"),
            "B0_REFACTOR_AS_LANDED": ("PASS", "NOT_IMPLEMENTED"),
            "B1_ROUTES_AND_PREFLIGHT_RESTORED": ("PASS", "PASS"),
        }
        for name, (core_state, route_state) in expected_oracles.items():
            got = (observed[name]["portable_core_contract"], observed[name]["owned_route_probe"])
            if got != (core_state, route_state):
                raise ProofError(
                    f"{name} hermetic oracles moved: expected={(core_state, route_state)} observed={got}"
                )
    except (ProofError, OSError, subprocess.SubprocessError, KeyError, ValueError) as exc:
        print(f"DUAL-FORGE-REFACTOR-AB-RED {exc}", file=sys.stderr)
        return 2

    report = {
        "schema": "dual-forge-repository-loop/refactor-ab/v1",
        "refactor_commit": "d757a5cc66f5062f638af532078f8643b1175647",
        "evidence_scope": "deterministic structure and executable owned routes only",
        "subjects": {
            "A_OLD_CANONICAL": EXPECTED_GIT_BLOBS[OLD],
            "B0_REFACTOR_AS_LANDED": EXPECTED_GIT_BLOBS[LANDED],
            "B1_ROUTES_AND_PREFLIGHT_RESTORED": git_blob_sha(CURRENT.read_text(encoding="utf-8")),
        },
        "matched_task": {
            "same_tree_except_skill_body": True,
            "same_contracts_and_oracles": True,
            "network": "NOT_EXERCISED",
            "model_or_provider": "NOT_EXERCISED",
            "cleanup": "CLEAN",
        },
        "results": results,
        "totals": totals,
        "hermetic_oracles": observed,
        "landed_refactor_traded_strengths_without_dominating": True,
        "live_model_runtime_ab": "NOT_EXERCISED",
        "delivery_and_human_admit": "HUMAN_ADMIT_REQUIRED",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print(
        "DUAL-FORGE-REFACTOR-AB-GREEN A and B0 tie at "
        f"{totals['A_OLD_CANONICAL']} by trading three strengths for three; "
        "B1 holds all ten and dominates both; hermetic oracles ran on one matched "
        "tree with zero network; live model/provider/forge/CI NOT_EXERCISED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
