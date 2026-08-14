#!/usr/bin/env python3
"""Validate this repository's own publication profile. Zero network.

`skills-shared` publishes itself through `github-delivery-loop`, so it owns the
same inputs any consumer owns: an immutable repository id, a stable check name,
the exact set of publication intents, a billing stop rule, and one fixed local
verification contract. Until this existed those values lived in whatever JSON a
caller happened to write at the time, which is the hand-written-snapshot problem
the loop exists to remove -- one Actions run per local commit, and a profile
that could disagree with the producers without anything noticing.

The contract is validated by importing `local_verification.validate_contract`
rather than by re-deriving its rules here. A second parser would drift from the
first, and the argv/environment/shell rules would then be decided by whichever
one a given caller happened to run.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE_SCHEMA = "github-delivery-ci-publication-profile/v1"
INTENTS = ("initial-pr", "ready-for-review", "batched-repair")
# The states a receipt may describe. A profile that admits publication while
# billing is open is a profile that pays to learn nothing.
BILLING_ACTIONS = {"stop"}
HOST_PATHS = (
    re.compile(r"/Users/[^/\"]+/"),
    re.compile(r"/home/[^/\"]+/"),
    re.compile(r"[A-Za-z]:\\\\"),
)
# A committed file carrying one of these is a live observation, not configuration.
LIVE_SCHEMAS = (
    "github-delivery-local-verification/v1",
    "github-delivery-local-verification-evidence/v1",
    "github-actions-publish-snapshot/v1",
    "github-actions-publish-observation/v1",
    "github-actions-billing-recovery/v1",
)


class ProfileError(Exception):
    pass


def load_contract_validator(repo_root: Path):
    path = repo_root / "skills/github-delivery-loop/scripts/local_verification.py"
    if not path.is_file():
        raise ProfileError(f"canonical producer is absent: {path}")
    spec = importlib.util.spec_from_file_location("local_verification", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["local_verification"] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ProfileError(f"{label} is unreadable: {error}") from error
    except json.JSONDecodeError as error:
        raise ProfileError(f"{label} is not JSON: {error}") from error
    if not isinstance(value, dict):
        raise ProfileError(f"{label} must be an object")
    return value


def exact(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ProfileError(
            f"{label} fields drifted: missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )


def reject_host_paths(text: str, label: str) -> None:
    for pattern in HOST_PATHS:
        found = pattern.search(text)
        if found is not None:
            raise ProfileError(f"{label} carries a machine-local path: {found.group(0)!r}")


def check_workflow_declares(repo_root: Path, workflow: str, check_name: str) -> None:
    """The stable check name must name a job that exists.

    A check name is stable only if something answers to it. A name that resolves
    to nothing produces no check run, and an absent check run is reported as an
    absent blocker rather than as a missing observation.
    """
    path = repo_root / workflow
    if not path.is_file():
        raise ProfileError(f"profile names a workflow that does not exist: {workflow}")
    text = path.read_text(encoding="utf-8")
    if "${{" in check_name:
        raise ProfileError(
            f"check name {check_name!r} is a template, so the identity it resolves to "
            "depends on the run rather than on the repository"
        )
    if not re.search(rf"^  {re.escape(check_name)}:\s*$", text, re.MULTILINE):
        raise ProfileError(
            f"workflow {workflow} declares no job named {check_name!r}, so the stable "
            "check identity resolves to nothing"
        )


def check_generated_paths(repo_root: Path, paths: Any) -> None:
    if not isinstance(paths, list) or not paths:
        raise ProfileError("profile.generated_paths must list where receipts land")
    ignored = set()
    gitignore = repo_root / ".gitignore"
    if gitignore.is_file():
        ignored = {
            line.strip()
            for line in gitignore.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }
    for entry in paths:
        if not isinstance(entry, str) or not entry.strip():
            raise ProfileError("profile.generated_paths entries must be non-empty strings")
        if entry.startswith("/") or ".." in Path(entry).parts:
            raise ProfileError(f"generated path must be repository-relative: {entry!r}")
        if entry.startswith(".git/"):
            continue
        if entry in ignored or f"/{entry}" in ignored:
            continue
        raise ProfileError(
            f"generated path {entry!r} is neither under .git/ nor ignored, so a "
            "receipt written there would be committed as if it were configuration"
        )


def check_no_live_evidence(repo_root: Path) -> None:
    directory = repo_root / ".github-delivery"
    if not directory.is_dir():
        return
    for path in sorted(directory.rglob("*.json")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for schema in LIVE_SCHEMAS:
            if f'"{schema}"' in text:
                raise ProfileError(
                    f"{path.relative_to(repo_root)} carries a live {schema} document; "
                    "observations and receipts are produced, never committed"
                )


def check_profile(repo_root: Path) -> tuple[int, int]:
    profile_path = repo_root / ".github-delivery/ci-publication/profile.json"
    profile = load_json(profile_path, "publication profile")
    reject_host_paths(profile_path.read_text(encoding="utf-8"), "publication profile")

    exact(
        profile,
        {"schema", "repository", "check", "verification_contract", "intents",
         "billing", "generated_paths"},
        "profile",
    )
    if profile["schema"] != PROFILE_SCHEMA:
        raise ProfileError(f"profile.schema must be {PROFILE_SCHEMA}")

    repository = profile["repository"]
    if not isinstance(repository, dict):
        raise ProfileError("profile.repository must be an object")
    exact(repository, {"full_name", "repository_id", "private"}, "profile.repository")
    repository_id = repository["repository_id"]
    if not isinstance(repository_id, int) or isinstance(repository_id, bool) or repository_id <= 0:
        raise ProfileError("profile.repository.repository_id must be the immutable numeric id")
    if repository["private"] is not True:
        raise ProfileError(
            "this profile governs a private repository; a public one has different "
            "Actions economics and must not reuse it"
        )

    check = profile["check"]
    if not isinstance(check, dict):
        raise ProfileError("profile.check must be an object")
    exact(check, {"name", "workflow"}, "profile.check")
    check_workflow_declares(repo_root, check["workflow"], check["name"])

    intents = profile["intents"]
    if not isinstance(intents, list) or tuple(intents) != INTENTS:
        raise ProfileError(
            f"profile.intents must be exactly {list(INTENTS)} in order; a fourth intent "
            "is a publication this gate never evaluated"
        )

    billing = profile["billing"]
    if not isinstance(billing, dict):
        raise ProfileError("profile.billing must be an object")
    exact(billing, {"blocked_state", "on_blocked", "recovery"}, "profile.billing")
    if billing["blocked_state"] != "billing-open":
        raise ProfileError("profile.billing.blocked_state must be billing-open")
    if billing["on_blocked"] not in BILLING_ACTIONS:
        raise ProfileError(
            f"profile.billing.on_blocked must be one of {sorted(BILLING_ACTIONS)}; "
            "rerunning or continuing while the circuit is open pays for no observation"
        )
    if not isinstance(billing["recovery"], str) or not billing["recovery"].strip():
        raise ProfileError("profile.billing.recovery must say what reopens publication")

    check_generated_paths(repo_root, profile["generated_paths"])
    check_no_live_evidence(repo_root)

    contract_rel = profile["verification_contract"]
    if not isinstance(contract_rel, str) or not contract_rel.strip():
        raise ProfileError("profile.verification_contract must name one fixed contract")
    contract_path = repo_root / contract_rel
    if not contract_path.is_file():
        raise ProfileError(f"verification contract is absent: {contract_rel}")
    contract_text = contract_path.read_text(encoding="utf-8")
    reject_host_paths(contract_text, "verification contract")
    contract = load_json(contract_path, "verification contract")

    # One parser, the producer's own. Reimplementing the argv, environment and
    # shell-string rules here would let this file and the producer disagree
    # about what the contract means.
    producer = load_contract_validator(repo_root)
    try:
        validated = producer.validate_contract(contract, repository_id)
    except producer.VerificationError as error:
        raise ProfileError(f"verification contract refused by the producer: {error}") from error

    return len(validated["commands"]), len(intents)


def selftest() -> None:
    """Plant each shape #54 names and require a refusal that says which it is."""
    source = ROOT

    def build(root: Path, mutate=None) -> Path:
        (root / ".github-delivery/ci-publication").mkdir(parents=True, exist_ok=True)
        (root / ".github/workflows").mkdir(parents=True, exist_ok=True)
        (root / "skills/github-delivery-loop/scripts").mkdir(parents=True, exist_ok=True)
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        (root / "skills/github-delivery-loop/scripts/local_verification.py").write_text(
            (source / "skills/github-delivery-loop/scripts/local_verification.py")
            .read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (root / ".github/workflows/skill-eval-contract.yml").write_text(
            "name: fixture\non:\n  workflow_dispatch:\njobs:\n  contract:\n    runs-on: ubuntu-latest\n",
            encoding="utf-8",
        )
        profile = json.loads(
            (source / ".github-delivery/ci-publication/profile.json").read_text(encoding="utf-8")
        )
        contract = json.loads(
            (source / ".github-delivery/ci-publication/verification-contract.json")
            .read_text(encoding="utf-8")
        )
        if mutate is not None:
            mutate(root, profile, contract)
        (root / ".github-delivery/ci-publication/profile.json").write_text(
            json.dumps(profile, indent=2) + "\n", encoding="utf-8"
        )
        (root / ".github-delivery/ci-publication/verification-contract.json").write_text(
            json.dumps(contract, indent=2) + "\n", encoding="utf-8"
        )
        return root

    def refuse(name: str, mutate, fragment: str) -> None:
        with tempfile.TemporaryDirectory(prefix=f"pubprofile-{name}.") as raw:
            root = build(Path(raw), mutate)
            try:
                check_profile(root)
            except ProfileError as error:
                if fragment not in str(error):
                    raise ProfileError(
                        f"selftest {name}: refused for the wrong reason: {error}"
                    ) from error
                return
            raise ProfileError(f"selftest {name}: planted defect was not caught")

    with tempfile.TemporaryDirectory(prefix="pubprofile-base.") as raw:
        # The baseline has to pass, or every mutation below is refused before it
        # is even applied and proves nothing.
        check_profile(build(Path(raw)))

    refuse("wrong-repository-id",
           lambda root, p, c: p["repository"].__setitem__("repository_id", 42),
           "repository identity mismatch")
    refuse("public-repository",
           lambda root, p, c: p["repository"].__setitem__("private", False),
           "private repository")
    refuse("mutable-check-name",
           lambda root, p, c: p["check"].__setitem__("name", "${{ matrix.skill }}"),
           "is a template")
    refuse("unresolved-check-name",
           lambda root, p, c: p["check"].__setitem__("name", "no-such-job"),
           "declares no job named")
    refuse("fourth-intent",
           lambda root, p, c: p["intents"].append("checkpoint"),
           "must be exactly")
    refuse("missing-intent",
           lambda root, p, c: p.__setitem__("intents", ["initial-pr", "ready-for-review"]),
           "must be exactly")
    refuse("billing-rerun",
           lambda root, p, c: p["billing"].__setitem__("on_blocked", "rerun"),
           "pays for no observation")
    refuse("shell-string-command",
           lambda root, p, c: c["commands"][0].__setitem__(
               "argv", ["bash", "-c", "make test"]),
           "may not execute shell strings")
    refuse("unsafe-inherited-env",
           lambda root, p, c: c["inherit_env"].append("GITHUB_TOKEN"),
           "unadmitted inherited env names")
    refuse("contract-repository-drift",
           lambda root, p, c: c.__setitem__("repository_id", 42),
           "repository identity mismatch")
    refuse("absolute-host-path",
           lambda root, p, c: c["commands"][0].__setitem__(
               "cwd", "/Users/someone/checkout"),
           "machine-local path")
    refuse("tracked-generated-path",
           lambda root, p, c: p.__setitem__("generated_paths", ["evals/receipt.json"]),
           "neither under .git/ nor ignored")
    # The offender second, behind a legitimate entry. With every fixture holding
    # one path, "check each generated path" and "check the first one" are the
    # same program -- the shape #16 reports as making a real guard
    # unfalsifiable.
    refuse("tracked-generated-path-behind-a-good-one",
           lambda root, p, c: p.__setitem__(
               "generated_paths", [".git/github-delivery/ok.json", "evals/receipt.json"]),
           "neither under .git/ nor ignored")
    refuse("absent-contract",
           lambda root, p, c: p.__setitem__("verification_contract", "nowhere.json"),
           "verification contract is absent")

    def commit_live_receipt(root: Path, profile: dict, contract: dict) -> None:
        (root / ".github-delivery/ci-publication/receipt.json").write_text(
            json.dumps({"schema": "github-delivery-local-verification/v1"}) + "\n",
            encoding="utf-8",
        )

    refuse("committed-live-receipt", commit_live_receipt, "carries a live")

    print("SELFTEST GREEN: publication profile refuses every shape #54 names")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    try:
        if args.selftest:
            selftest()
            return 0
        commands, intents = check_profile(args.repo_root.resolve())
        print(
            f"CI PUBLICATION PROFILE GREEN: {commands} fixed local command(s), "
            f"{intents} admitted intent(s), billing stop rule present"
        )
        return 0
    except ProfileError as error:
        print(f"CI PUBLICATION PROFILE RED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
