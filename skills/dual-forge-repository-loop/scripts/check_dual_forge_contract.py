#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

SHA40 = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
EVIDENCE = {"PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED", "SKIPPED_BY_POLICY", "HUMAN_ADMIT_REQUIRED"}
EXPECTED_HISTORY = [
    "GITHUB_BOUND",
    "LOCAL_SYNCED",
    "FORGEJO_ISSUES_BOUND",
    "WORKTREES_VERIFIED",
    "FORGEJO_PRS_MERGED",
    "LOCAL_MAIN_MERGED",
    "GITHUB_RECONCILED",
    "GITHUB_ACTIONS_VERIFIED",
    "GITHUB_PUBLICATION_READY",
]
REQUIRED_PUBLICATION_EVIDENCE = [
    "github_ingress",
    "forgejo_runtime",
    "local_worktrees",
    "local_main_merge",
    "github_reconciliation",
    "github_actions",
]
PR_CLASSIFICATIONS = {
    "UNAFFECTED",
    "CLEANLY_REBASEABLE",
    "SUPERSEDED_BY_LOCAL_MAIN",
    "PUBLICATION_SUBJECT",
}
PR_TERMINAL_ROUTES = {
    "UNAFFECTED": {"NO_ACTION"},
    "CLEANLY_REBASEABLE": {"REBASED_OR_MERGED"},
    "SUPERSEDED_BY_LOCAL_MAIN": {"CLOSED_OR_RETARGETED"},
    "PUBLICATION_SUBJECT": {"WIP_CAPTURED"},
}
ISSUE_TERMINAL_ROUTES = {
    "CLOSED",
    "IMPLEMENTED",
    "SUPERSEDED",
    "ROUTED_SEPARATE_ISSUE",
    "OWNER_HANDOFF_NONBLOCKING",
    "NO_ACTION",
}
DECISION_MANIFEST_SCHEMA = "github-actions-publish-decision-manifest/v1"
MAX_GIT_PROOF_BYTES = 64 * 1024 * 1024


def fail(msg: str) -> int:
    print(f"FAIL {msg}", file=sys.stderr)
    return 2


def obj(v, name: str):
    if not isinstance(v, dict):
        raise ValueError(f"{name} must be an object")
    return v


def sha(v, name: str):
    if not isinstance(v, str) or not SHA40.fullmatch(v):
        raise ValueError(f"{name} must be a lowercase 40-hex commit SHA")
    return v


def digest(v, name: str):
    if not isinstance(v, str) or re.fullmatch(r"[0-9a-f]{64}", v) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256")
    return v


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def timestamp(value, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be ISO-8601")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load canonical verifier {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_bound_bytes(root: Path, value, label: str) -> bytes:
    binding = obj(value, label)
    if set(binding) != {"path", "sha256"}:
        raise ValueError(f"{label} must contain path and sha256 only")
    relative = binding["path"]
    expected = binding["sha256"]
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"{label}.path must be safe and receipt-relative")
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        raise ValueError(f"{label}.sha256 must be a lowercase SHA-256")
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label}.path escapes the receipt directory") from exc
    try:
        payload = target.read_bytes()
    except OSError as exc:
        raise ValueError(f"{label} is unreadable: {exc}") from exc
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError(f"{label} content digest mismatch")
    return payload


def load_bound(root: Path, value, label: str):
    payload = load_bound_bytes(root, value, label)
    try:
        body = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {exc}") from exc
    return obj(body, label)


def git(repo: Path, *args: str, payload: bytes | None = None) -> str:
    result = subprocess.run(
        ["git", f"--git-dir={repo}", *args],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=15,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).decode(errors="replace").strip()
        raise ValueError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.decode().strip()


def verify_pr_inventory(value, label: str) -> None:
    if not isinstance(value, list):
        raise ValueError(f"reconciliation {label} must be an inventory array")
    for index, item_value in enumerate(value):
        item = obj(item_value, f"reconciliation {label}[{index}]")
        if set(item) != {
            "number", "head_sha", "base_branch", "wip", "classification",
            "terminal_route", "receipt",
        }:
            raise ValueError(f"reconciliation {label}[{index}] fields drifted")
        number = item["number"]
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ValueError(f"reconciliation {label}[{index}] number is invalid")
        sha(item["head_sha"], f"reconciliation {label}[{index}].head_sha")
        if not isinstance(item["base_branch"], str) or not item["base_branch"]:
            raise ValueError(f"reconciliation {label}[{index}] base branch is invalid")
        if not isinstance(item["wip"], bool):
            raise ValueError(f"reconciliation {label}[{index}] WIP state is invalid")
        classification = item["classification"]
        if classification not in PR_CLASSIFICATIONS:
            raise ValueError(f"reconciliation {label}[{index}] remains blocking or unclassified")
        if item["terminal_route"] not in PR_TERMINAL_ROUTES[classification]:
            raise ValueError(f"reconciliation {label}[{index}] lacks a compatible terminal route")
        if not isinstance(item["receipt"], str) or not item["receipt"]:
            raise ValueError(f"reconciliation {label}[{index}] lacks a receipt identity")


def verify_issue_inventory(value) -> None:
    if not isinstance(value, list):
        raise ValueError("reconciliation open_issues must be an inventory array")
    for index, item_value in enumerate(value):
        item = obj(item_value, f"reconciliation open_issues[{index}]")
        if set(item) != {"forge", "number", "scope", "terminal_route", "receipt"}:
            raise ValueError(f"reconciliation open_issues[{index}] fields drifted")
        if item["forge"] not in {"github", "forgejo"}:
            raise ValueError(f"reconciliation open_issues[{index}] forge is invalid")
        number = item["number"]
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ValueError(f"reconciliation open_issues[{index}] number is invalid")
        if item["scope"] not in {"AFFECTED", "UNAFFECTED"}:
            raise ValueError(f"reconciliation open_issues[{index}] scope is invalid")
        if item["scope"] == "UNAFFECTED" and item["terminal_route"] != "NO_ACTION":
            raise ValueError(f"reconciliation open_issues[{index}] unrelated route is invalid")
        if item["scope"] == "AFFECTED" and item["terminal_route"] == "NO_ACTION":
            raise ValueError(f"reconciliation open_issues[{index}] affected issue is unrouted")
        if item["terminal_route"] not in ISSUE_TERMINAL_ROUTES:
            raise ValueError(f"reconciliation open_issues[{index}] is not terminally routed")
        if not isinstance(item["receipt"], str) or not item["receipt"]:
            raise ValueError(f"reconciliation open_issues[{index}] lacks a receipt identity")


def verify_forgejo_delivery(
    receipt_path: Path,
    implementation,
    forgejo_repository: str,
    default_branch: str,
    forgejo_main: str,
    local_main: str,
    linked_issue_numbers: set[int],
) -> tuple[int, set[int]]:
    implementation = obj(implementation, "implementation")
    if set(implementation) != {"forgejo_delivery"}:
        raise ValueError("implementation receipt fields drifted")
    delivery = load_bound(
        receipt_path.parent, implementation["forgejo_delivery"], "Forgejo delivery observation"
    )
    required = {
        "schema", "forgejo_repository", "forgejo_repository_id", "default_branch",
        "captured_at", "transport", "issues", "recovery_worktree", "merged_prs",
        "local_main_merge", "verification",
    }
    if set(delivery) != required:
        raise ValueError("Forgejo delivery observation fields drifted")
    if delivery["forgejo_repository"] != forgejo_repository or delivery["default_branch"] != default_branch:
        raise ValueError("Forgejo delivery repository/default branch mismatch")
    transport = load_bound(receipt_path.parent, delivery["transport"], "Forgejo delivery transport")
    producer = load_module(
        "dual_forge_delivery_capture", Path(__file__).resolve().parent / "capture_forgejo_delivery.py"
    )
    producer.verify_observation(transport, delivery)
    issues = delivery["issues"]
    observed_issue_numbers = set()
    for index, value in enumerate(issues):
        item = obj(value, f"Forgejo delivery issues[{index}]")
        if set(item) != {
            "number", "state", "title_sha256", "body_sha256", "comments_sha256",
            "comment_count", "context_state", "desktop_submission_state",
            "recovery_receipt_sha256", "desktop_receipt_sha256", "desktop_thread_url",
            "desktop_prompt_sha256", "desktop_observer_id", "desktop_observer_login",
            "desktop_response_started_at", "receipt",
        } or item["state"] != "closed":
            raise ValueError(f"Forgejo delivery issues[{index}] is not a closed issue receipt")
        if item["context_state"] != "PASS" or item["desktop_submission_state"] != "PASS":
            raise ValueError(
                f"Forgejo delivery issues[{index}] lacks full recovery context or submitted Desktop receipt"
            )
        for field in (
            "title_sha256", "body_sha256", "comments_sha256", "recovery_receipt_sha256",
            "desktop_receipt_sha256", "desktop_prompt_sha256",
        ):
            digest(item[field], f"Forgejo delivery issues[{index}].{field}")
        if (
            not isinstance(item["desktop_thread_url"], str)
            or not item["desktop_thread_url"].startswith("https://chatgpt.com/")
            or not isinstance(item["desktop_observer_id"], int)
            or isinstance(item["desktop_observer_id"], bool)
            or item["desktop_observer_id"] <= 0
            or not isinstance(item["desktop_observer_login"], str)
            or not item["desktop_observer_login"]
        ):
            raise ValueError(f"Forgejo delivery issues[{index}] Desktop identity is malformed")
        if not isinstance(item["comment_count"], int) or isinstance(item["comment_count"], bool) or item["comment_count"] < 1:
            raise ValueError(f"Forgejo delivery issues[{index}] lacks provider-derived comments")
        if not isinstance(item["receipt"], str) or not item["receipt"]:
            raise ValueError(f"Forgejo delivery issues[{index}] lacks receipt identity")
        observed_issue_numbers.add(item["number"])
    if not linked_issue_numbers or not linked_issue_numbers.issubset(observed_issue_numbers):
        raise ValueError("Forgejo linked issues lack provider-derived issue receipts")
    recovery_worktree = obj(delivery["recovery_worktree"], "Forgejo recovery worktree")
    if set(recovery_worktree) != {
        "issue_number", "branch", "head_sha", "base_sha", "created_at",
        "observed_at", "creation_receipt_sha256", "writer_lease", "receipt",
    }:
        raise ValueError("Forgejo recovery worktree fields drifted")
    if recovery_worktree["issue_number"] not in linked_issue_numbers:
        raise ValueError("Forgejo recovery worktree is not bound to a linked issue")
    sha(recovery_worktree["head_sha"], "Forgejo recovery worktree head_sha")
    sha(recovery_worktree["base_sha"], "Forgejo recovery worktree base_sha")
    digest(recovery_worktree["creation_receipt_sha256"], "Forgejo recovery worktree creation receipt")
    lease = obj(recovery_worktree["writer_lease"], "Forgejo recovery worktree writer lease")
    if set(lease) != {"kind", "branch_ref", "holders", "reason"} or lease.get("kind") != "git-branch-lock" or lease.get("holders") != 1 or lease.get("branch_ref") != f"refs/heads/{recovery_worktree['branch']}" or not isinstance(lease.get("reason"), str) or not lease["reason"]:
        raise ValueError("Forgejo recovery worktree lacks exactly one Git writer lease")
    if not isinstance(recovery_worktree["receipt"], str) or not recovery_worktree["receipt"]:
        raise ValueError("Forgejo recovery worktree lacks receipt identity")
    merged_prs = delivery["merged_prs"]
    if not isinstance(merged_prs, list) or not merged_prs:
        raise ValueError("Forgejo delivery lacks a provider-derived merged PR receipt")
    closed_by_merged_prs: set[int] = set()
    for index, value in enumerate(merged_prs):
        item = obj(value, f"Forgejo delivery merged_prs[{index}]")
        if set(item) != {
            "number", "state", "merged", "head_sha", "merge_commit_sha", "base_branch",
            "body_sha256", "merged_at", "closes_issues", "receipt",
        }:
            raise ValueError(f"Forgejo delivery merged_prs[{index}] fields drifted")
        digest(item["body_sha256"], f"Forgejo delivery merged_prs[{index}].body_sha256")
        timestamp(item["merged_at"], f"Forgejo delivery merged_prs[{index}].merged_at")
        if not isinstance(item["closes_issues"], list) or any(
            not isinstance(number, int) or isinstance(number, bool) or number <= 0
            for number in item["closes_issues"]
        ):
            raise ValueError(f"Forgejo delivery merged_prs[{index}] closure links are malformed")
        closed_by_merged_prs.update(item["closes_issues"])
    if not linked_issue_numbers.issubset(closed_by_merged_prs):
        raise ValueError("Forgejo merged PR bodies do not close every linked implementation issue")
    if not any(
        isinstance(item, dict)
        and item.get("merged") is True
        and item.get("state") == "closed"
        and item.get("merge_commit_sha") == local_main
        for item in merged_prs
    ):
        raise ValueError("no Forgejo merged PR produced admitted local main")
    local_merge = obj(delivery["local_main_merge"], "local-main merge receipt")
    if set(local_merge) != {"sha", "parents", "tree_sha", "receipt"}:
        raise ValueError("local-main merge receipt fields drifted")
    if local_merge["sha"] != local_main or forgejo_main not in local_merge["parents"]:
        raise ValueError("local-main merge receipt does not contain Forgejo main")
    verification_bundle = obj(delivery["verification"], "Forgejo verification bundle")
    if set(verification_bundle) != {"receipt", "evidence", "contract"}:
        raise ValueError("Forgejo verification bundle fields drifted")
    verification = load_bound(
        receipt_path.parent, verification_bundle["receipt"], "Forgejo verification receipt"
    )
    verification_evidence = load_bound(
        receipt_path.parent, verification_bundle["evidence"], "Forgejo verification evidence"
    )
    verification_contract = load_bound(
        receipt_path.parent, verification_bundle["contract"], "Forgejo verification contract"
    )
    gate = load_module(
        "dual_forge_local_verification_gate",
        Path(__file__).resolve().parents[2]
        / "github-delivery-loop"
        / "scripts"
        / "ci_publish_gate.py",
    )
    try:
        gate.validate_verification(
            verification, delivery["forgejo_repository_id"], local_main
        )
        gate.validate_evidence(
            verification_evidence,
            verification,
            verification_contract,
            delivery["forgejo_repository_id"],
            local_main,
            local_merge["tree_sha"],
        )
    except gate.InputError as exc:
        raise ValueError(f"Forgejo verification does not prove exact local main: {exc}") from exc
    if timestamp(verification["verified_at"], "Forgejo verified_at") > timestamp(
        delivery["captured_at"], "Forgejo delivery captured_at"
    ):
        raise ValueError("Forgejo verification occurs after its provider capture")
    return delivery["forgejo_repository_id"], observed_issue_numbers


def verify_git_ancestry(
    receipt_path: Path,
    binding,
    github_main: str,
    forgejo_main: str,
    local_main: str,
    candidate: str,
) -> str:
    stream = load_bound_bytes(receipt_path.parent, binding, "publication git proof")
    if not stream or len(stream) > MAX_GIT_PROOF_BYTES:
        raise ValueError("publication git proof must be a non-empty bounded fast-import stream")
    with tempfile.TemporaryDirectory(prefix="dual-forge-proof.") as directory:
        repository = Path(directory) / "objects.git"
        init = subprocess.run(
            ["git", "init", "-q", "--bare", str(repository)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=15,
        )
        if init.returncode != 0:
            raise ValueError("cannot initialize disposable Git proof repository")
        git(repository, "fast-import", "--quiet", payload=stream)
        refs = {
            "refs/heads/github-main": github_main,
            "refs/heads/forgejo-main": forgejo_main,
            "refs/heads/local-main": local_main,
            "refs/heads/candidate": candidate,
        }
        actual_refs = set(
            git(repository, "for-each-ref", "--format=%(refname)", "refs/heads").splitlines()
        )
        if actual_refs != set(refs):
            raise ValueError("publication git proof must expose exactly four admitted refs")
        for ref, expected in refs.items():
            if git(repository, "rev-parse", ref) != expected:
                raise ValueError(f"publication git proof ref mismatch: {ref}")
        git(repository, "fsck", "--strict", "--no-reflogs")
        forgejo_to_local = subprocess.run(
            [
                "git", f"--git-dir={repository}", "merge-base", "--is-ancestor",
                forgejo_main, local_main,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=15,
        )
        if forgejo_to_local.returncode != 0:
            raise ValueError("admitted local main does not contain Forgejo main")
        for ancestor in (github_main, forgejo_main, local_main):
            probe = subprocess.run(
                ["git", f"--git-dir={repository}", "merge-base", "--is-ancestor", ancestor, candidate],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=15,
            )
            if probe.returncode != 0:
                raise ValueError(f"publication candidate does not contain admitted baseline {ancestor}")
        return sha(git(repository, "rev-parse", f"{candidate}^{{tree}}"), "candidate tree")


def verify_canonical_publication(
    receipt_path: Path,
    publication,
    actions,
    observation_bindings,
    reconciliation_binding,
    github_main: str,
    forgejo_main: str,
    local_main: str,
    candidate: str,
    actual_tree: str,
    repository: str,
    default_branch: str,
    forgejo_repository: str,
    forgejo_delivery_repository_id: int,
    delivered_closed_issue_numbers: set[int],
    github_remote: str,
    forgejo_remote: str,
) -> None:
    root = receipt_path.parent
    bundle = obj(publication.get("decision_bundle"), "publication.decision_bundle")
    required = {
        "manifest", "policy", "snapshot", "verification", "evidence", "contract", "recovery",
    }
    if set(bundle) != required:
        raise ValueError("publication.decision_bundle fields drifted")
    manifest = load_bound(root, bundle["manifest"], "publication decision manifest")
    if set(manifest) != {
        "schema", "evaluated_at", "required_check_name", "decision", "inputs",
    }:
        raise ValueError("publication decision manifest fields drifted")
    if manifest["schema"] != DECISION_MANIFEST_SCHEMA:
        raise ValueError("publication decision manifest schema is unsupported")
    evaluated_at = timestamp(manifest["evaluated_at"], "publication evaluated_at")

    observations = obj(observation_bindings, "observations")
    if set(observations) != {"github_main", "forgejo_main", "local_main"}:
        raise ValueError("origin observation bindings drifted")
    expected_origins = {
        "github_main": (
            "github-api", "gh-api", repository, github_main,
            f"repos/{repository}/git/ref/heads/{quote(default_branch, safe='')}",
        ),
        "forgejo_main": (
            "forgejo-api", "forgejo-api-authenticated-read", forgejo_repository, forgejo_main,
            "repos/" + "/".join(quote(part, safe="") for part in forgejo_repository.split("/", 1))
            + f"/branches/{quote(default_branch, safe='')}",
        ),
        "local_main": (
            "local-git", "git-rev-parse", repository, local_main,
            f"refs/heads/{default_branch}",
        ),
    }
    captured: list[datetime] = []
    github_repository_id: int | None = None
    forgejo_repository_id: int | None = None
    for name, (authority, source, expected_repository, expected_sha, source_identity) in expected_origins.items():
        observation = load_bound(root, observations[name], f"{name} observation")
        if set(observation) != {
            "schema", "authority", "repository", "default_branch", "ref",
            "sha", "captured_at", "repository_id", "transport",
        }:
            raise ValueError(f"{name} observation fields drifted")
        if observation["schema"] != "dual-forge-ref-observation/v1":
            raise ValueError(f"{name} observation schema is unsupported")
        if observation["authority"] != authority:
            raise ValueError(f"{name} observation authority mismatch")
        if observation["repository"] != expected_repository:
            raise ValueError(f"{name} observation repository mismatch")
        if observation["default_branch"] != default_branch:
            raise ValueError(f"{name} observation default branch mismatch")
        if observation["ref"] != f"refs/heads/{default_branch}":
            raise ValueError(f"{name} observation is not the bound default branch ref")
        if observation["sha"] != expected_sha:
            raise ValueError(f"{name} observation SHA mismatch")
        transport = load_bound(root, observation["transport"], f"{name} transport")
        if set(transport) != {
            "schema", "producer", "source", "source_identity", "authority",
            "repository", "default_branch", "ref", "sha", "captured_at",
            "remote_bindings", "repository_id", "capture",
        }:
            raise ValueError(f"{name} transport fields drifted")
        if transport["schema"] != "dual-forge-ref-transport/v1":
            raise ValueError(f"{name} transport schema is unsupported")
        if transport["producer"] != "capture_origin_ref.py" or transport["source"] != source:
            raise ValueError(f"{name} transport lacks its canonical capture producer")
        if transport["source_identity"] != source_identity:
            raise ValueError(f"{name} transport source identity mismatch")
        if name == "local_main":
            if transport["remote_bindings"] != {
                "github_remote": github_remote,
                "github_repository": repository,
                "forgejo_remote": forgejo_remote,
                "forgejo_repository": forgejo_repository,
            }:
                raise ValueError("local transport remote bindings mismatch")
        elif transport["remote_bindings"] is not None:
            raise ValueError(f"{name} remote bindings must be null")
        for field in ("authority", "repository", "default_branch", "ref", "sha", "captured_at"):
            if transport[field] != observation[field]:
                raise ValueError(f"{name} transport/observation {field} mismatch")
        if transport["repository_id"] != observation["repository_id"]:
            raise ValueError(f"{name} transport/observation repository ID mismatch")
        capture = obj(transport["capture"], f"{name} capture")
        if set(capture) != {"argv", "exit_codes", "stdout", "stdout_sha256"}:
            raise ValueError(f"{name} capture fields drifted")
        argv, exits, stdout, stdout_digests = (
            capture["argv"], capture["exit_codes"], capture["stdout"], capture["stdout_sha256"]
        )
        if not all(isinstance(value, list) for value in (argv, exits, stdout, stdout_digests)):
            raise ValueError(f"{name} capture arrays are malformed")
        if not argv or not (len(argv) == len(exits) == len(stdout) == len(stdout_digests)):
            raise ValueError(f"{name} capture arrays differ in length")
        if exits != [0] * len(argv):
            raise ValueError(f"{name} capture includes a failed command")
        if any(
            not isinstance(value, str)
            or hashlib.sha256(value.encode()).hexdigest() != digest
            for value, digest in zip(stdout, stdout_digests)
        ):
            raise ValueError(f"{name} capture stdout digest mismatch")
        if name == "github_main":
            expected_argv = [
                ["gh", "api", f"repos/{repository}"],
                ["gh", "api", source_identity],
            ]
            try:
                repo_response, ref_response = json.loads(stdout[0]), json.loads(stdout[1])
            except (IndexError, json.JSONDecodeError) as exc:
                raise ValueError("GitHub capture stdout is not replayable JSON") from exc
            repository_id = repo_response.get("id") if isinstance(repo_response, dict) else None
            ref_object = ref_response.get("object") if isinstance(ref_response, dict) else None
            if (
                argv != expected_argv
                or not isinstance(repo_response, dict)
                or repo_response.get("full_name") != repository
                or repo_response.get("default_branch") != default_branch
                or not isinstance(repository_id, int)
                or isinstance(repository_id, bool)
                or repository_id <= 0
                or not isinstance(ref_object, dict)
                or ref_object.get("sha") != expected_sha
                or observation["repository_id"] != repository_id
            ):
                raise ValueError("GitHub provider capture does not derive the observation")
            github_repository_id = repository_id
        elif name == "forgejo_main":
            root_endpoint = source_identity.rsplit("/branches/", 1)[0]
            expected_argv = [
                ["forgejo-api-authenticated-read", f"/api/v1/{root_endpoint}"],
                ["forgejo-api-authenticated-read", f"/api/v1/{source_identity}"],
            ]
            try:
                repo_response, branch_response = json.loads(stdout[0]), json.loads(stdout[1])
            except (IndexError, json.JSONDecodeError) as exc:
                raise ValueError("Forgejo capture stdout is not replayable JSON") from exc
            repository_id = repo_response.get("id") if isinstance(repo_response, dict) else None
            commit = branch_response.get("commit") if isinstance(branch_response, dict) else None
            if (
                argv != expected_argv
                or not isinstance(repo_response, dict)
                or repo_response.get("full_name") != forgejo_repository
                or repo_response.get("default_branch") != default_branch
                or not isinstance(repository_id, int)
                or isinstance(repository_id, bool)
                or repository_id <= 0
                or not isinstance(commit, dict)
                or commit.get("id") != expected_sha
                or observation["repository_id"] != repository_id
            ):
                raise ValueError("Forgejo provider capture does not derive the observation")
            forgejo_repository_id = repository_id
        else:
            expected_argv = [
                ["git", "-C", "<repo-root>", "rev-parse", "--show-toplevel"],
                [
                    "git", "-C", "<repo-root>", "remote", "get-url",
                    "--push", "--all", github_remote,
                ],
                [
                    "git", "-C", "<repo-root>", "remote", "get-url",
                    "--push", "--all", forgejo_remote,
                ],
                ["git", "-C", "<repo-root>", "rev-parse", "--verify", f"refs/heads/{default_branch}"],
                ["git", "-C", "<repo-root>", "cat-file", "-t", expected_sha],
            ]
            if (
                argv != expected_argv
                or stdout != [".", repository, forgejo_repository, expected_sha, "commit"]
                or observation["repository_id"] is not None
            ):
                raise ValueError("local Git capture does not derive the remote-bound observation")
        stamp = timestamp(observation["captured_at"], f"{name} captured_at")
        age = (evaluated_at - stamp).total_seconds()
        if age < -30 or age > 300:
            raise ValueError(f"{name} observation is stale or from the future")
        captured.append(stamp)

    reconciliation = load_bound(root, reconciliation_binding, "reconciliation observation")
    if set(reconciliation) != {
        "schema", "repository", "forgejo_repository", "repository_ids",
        "candidate_sha", "github_main_sha", "forgejo_main_sha",
        "local_main_sha", "captured_at", "transport", "publication_subject",
        "github_open_prs", "forgejo_open_prs", "open_issues", "unresolved_conflicts",
    }:
        raise ValueError("reconciliation observation fields drifted")
    if reconciliation["schema"] != "dual-forge-reconciliation-observation/v2":
        raise ValueError("reconciliation observation schema is unsupported")
    expected_reconciliation = {
        "repository": repository,
        "candidate_sha": candidate,
        "github_main_sha": github_main,
        "forgejo_main_sha": forgejo_main,
        "local_main_sha": local_main,
    }
    for field, expected in expected_reconciliation.items():
        if reconciliation[field] != expected:
            raise ValueError(f"reconciliation {field} mismatch")
    if reconciliation["forgejo_repository"] != forgejo_repository:
        raise ValueError("reconciliation Forgejo repository mismatch")
    reconciliation_transport = load_bound(
        root, reconciliation["transport"], "reconciliation transport"
    )
    reconciliation_producer = load_module(
        "dual_forge_reconciliation_capture", Path(__file__).resolve().parent / "capture_reconciliation.py"
    )
    reconciliation_producer.verify_observation(reconciliation_transport, reconciliation)
    if reconciliation["repository_ids"].get("github") != github_repository_id:
        raise ValueError("reconciliation and GitHub origin repository IDs differ")
    if (
        reconciliation["repository_ids"].get("forgejo") != forgejo_repository_id
        or forgejo_delivery_repository_id != forgejo_repository_id
    ):
        raise ValueError("Forgejo origin, delivery, and reconciliation repository IDs differ")
    verify_pr_inventory(reconciliation["github_open_prs"], "github_open_prs")
    verify_pr_inventory(reconciliation["forgejo_open_prs"], "forgejo_open_prs")
    verify_issue_inventory(reconciliation["open_issues"])
    contradictory_issues = {
        item.get("number")
        for item in reconciliation["open_issues"]
        if isinstance(item, dict) and item.get("forge") == "forgejo"
    } & delivered_closed_issue_numbers
    if contradictory_issues:
        raise ValueError(
            "Forgejo delivery-closed issues remain open in reconciliation: "
            + ", ".join(str(value) for value in sorted(contradictory_issues))
        )
    publication_subject = obj(
        reconciliation["publication_subject"], "reconciliation publication_subject"
    )
    if set(publication_subject) != {"forge", "number", "head_sha", "wip", "presence"}:
        raise ValueError("reconciliation publication subject fields drifted")
    publication_number = publication_subject["number"]
    if (
        publication_subject.get("forge") != "github"
        or not isinstance(publication_number, int)
        or isinstance(publication_number, bool)
        or publication_number <= 0
        or publication_subject.get("head_sha") != candidate
        or publication_subject.get("wip") is not True
        or publication_subject.get("presence") != "CAPTURED_OPEN_PR"
    ):
        raise ValueError("reconciliation publication subject is not exact captured WIP=1 PR")
    publication_routes = [
        item
        for item in reconciliation["github_open_prs"]
        if isinstance(item, dict)
        and item.get("number") == publication_number
        and item.get("head_sha") == candidate
        and item.get("wip") is True
    ]
    if len(publication_routes) != 1 or (
        publication_routes[0].get("classification") != "PUBLICATION_SUBJECT"
        or publication_routes[0].get("terminal_route") != "WIP_CAPTURED"
    ):
        raise ValueError("publication subject lacks one exact typed WIP inventory route")
    candidate_wip_routes = [
        item
        for item in reconciliation["github_open_prs"]
        if isinstance(item, dict)
        and item.get("head_sha") == candidate
        and item.get("wip") is True
    ]
    if candidate_wip_routes != publication_routes:
        raise ValueError("candidate has more than one captured WIP publication subject")
    if not isinstance(reconciliation["unresolved_conflicts"], list):
        raise ValueError("reconciliation unresolved_conflicts must be an inventory array")
    if reconciliation["unresolved_conflicts"]:
        raise ValueError("reconciliation still contains unresolved conflicts")
    reconciled_at = timestamp(reconciliation["captured_at"], "reconciliation captured_at")
    if reconciled_at < max(captured) or reconciled_at > evaluated_at:
        raise ValueError("reconciliation time does not close the origin observations")
    decision = obj(manifest["decision"], "publication decision")
    required_check_name = manifest["required_check_name"]
    if not isinstance(required_check_name, str) or not required_check_name:
        raise ValueError("publication manifest requires a stable check name")
    intent = decision.get("intent")
    if intent not in {"initial-pr", "ready-for-review", "batched-repair"}:
        raise ValueError("publication decision intent is unsupported")
    snapshot = load_bound(root, bundle["snapshot"], "publication snapshot")
    policy = load_bound(root, bundle["policy"], "publication policy")
    verification = load_bound(root, bundle["verification"], "publication verification")
    evidence = load_bound(root, bundle["evidence"], "publication evidence")
    contract = load_bound(root, bundle["contract"], "publication contract")
    recovery_binding = bundle["recovery"]
    recovery = (
        None
        if recovery_binding is None
        else load_bound(root, recovery_binding, "publication recovery")
    )
    inputs = obj(manifest["inputs"], "publication decision inputs")
    if set(inputs) != {
        "snapshot_sha256", "verification_sha256", "evidence_sha256",
        "contract_sha256", "policy_sha256", "recovery_sha256",
    }:
        raise ValueError("publication decision input digests drifted")
    expected_inputs = {
        "snapshot_sha256": bundle["snapshot"]["sha256"],
        "policy_sha256": bundle["policy"]["sha256"],
        "verification_sha256": bundle["verification"]["sha256"],
        "evidence_sha256": bundle["evidence"]["sha256"],
        "contract_sha256": bundle["contract"]["sha256"],
        "recovery_sha256": (
            None if recovery_binding is None else recovery_binding["sha256"]
        ),
    }
    if inputs != expected_inputs:
        raise ValueError("publication decision manifest is not bound to its exact inputs")

    scripts = Path(__file__).resolve().parents[2] / "github-delivery-loop" / "scripts"
    policy_authority = load_module(
        "dual_forge_ci_workflow_policy", scripts / "ci_workflow_policy.py"
    )
    try:
        canonical_policy = policy_authority.load_policy(
            root / bundle["policy"]["path"]
        )
    except policy_authority.PolicyError as exc:
        raise ValueError(f"publication policy is invalid: {exc}") from exc
    if canonical_policy != policy:
        raise ValueError("publication policy normalization drifted")
    if canonical_policy.get("repository") != repository:
        raise ValueError("publication policy repository mismatch")
    if canonical_policy.get("default_branch") != default_branch:
        raise ValueError("publication policy default branch mismatch")
    if canonical_policy.get("required_jobs") != [required_check_name]:
        raise ValueError("manifest check name is not the sole required policy job")
    gate = load_module("dual_forge_ci_publish_gate", scripts / "ci_publish_gate.py")
    result = gate.evaluate(
        snapshot, verification, evidence, contract, intent, candidate,
        actual_tree, recovery, evaluated_at,
    )
    if result.as_json() != decision:
        raise ValueError("publication decision does not reproduce from canonical inputs")
    if result.decision != "ALLOW" or result.head_sha != candidate:
        raise ValueError("canonical publication decision did not ALLOW the candidate")
    if snapshot.get("repository", {}).get("full_name") != repository:
        raise ValueError("publication decision repository mismatch")
    if snapshot.get("repository", {}).get("repository_id") != github_repository_id:
        raise ValueError("GitHub origin and publication repository numeric IDs differ")

    proof = obj(actions.get("proof"), "actions.proof")
    if set(proof) != {"check_name", "transport", "observation", "snapshot"}:
        raise ValueError("actions.proof fields drifted")
    check_name = proof["check_name"]
    if check_name != required_check_name:
        raise ValueError("actions proof check name differs from publication policy")
    producer = load_module("dual_forge_github_actions_snapshot", scripts / "github_actions_snapshot.py")
    transport = load_bound(root, proof["transport"], "actions transport")
    observation = load_bound(root, proof["observation"], "actions observation")
    actions_snapshot = load_bound(root, proof["snapshot"], "actions snapshot")
    if transport.get("check_name") != check_name:
        raise ValueError("actions transport check name differs from publication policy")
    if producer.observation_from_transport(transport) != observation:
        raise ValueError("actions observation does not reproduce from raw provider transport")
    if producer.build(observation, check_name) != actions_snapshot:
        raise ValueError("actions snapshot does not reproduce from canonical observation")
    if actions_snapshot.get("repository", {}).get("full_name") != repository:
        raise ValueError("actions proof repository mismatch")
    if actions_snapshot.get("repository", {}).get("repository_id") != snapshot.get("repository", {}).get("repository_id"):
        raise ValueError("prepublication and Actions repository identities differ")
    pull = obj(actions_snapshot.get("pull_request"), "actions snapshot pull_request")
    branch = obj(actions_snapshot.get("branch"), "actions snapshot branch")
    pre_branch = obj(snapshot.get("branch"), "publication snapshot branch")
    pre_pull = obj(snapshot.get("pull_request"), "publication snapshot pull_request")
    if branch.get("name") != pre_branch.get("name"):
        raise ValueError("prepublication and Actions branch subjects differ")
    if not isinstance(pull.get("number"), int) or isinstance(pull.get("number"), bool):
        raise ValueError("actions proof lacks a concrete pull request subject")
    if pull.get("number") != publication_number:
        raise ValueError("Actions pull request differs from reconciled publication subject")
    if intent == "initial-pr":
        if pre_pull.get("number") is not None or pull.get("state") != "draft":
            raise ValueError("initial publication did not create the admitted draft PR")
    else:
        if pull.get("number") != pre_pull.get("number"):
            raise ValueError("prepublication and Actions pull request subjects differ")
        if pull.get("state") != "ready":
            raise ValueError("publication transition did not leave the admitted PR ready")
    latest = obj(actions_snapshot.get("actions", {}).get("latest_check"), "actions latest_check")
    if pull.get("head_sha") != candidate or branch.get("head_sha") != candidate:
        raise ValueError("actions proof is stale for the publication candidate")
    if latest.get("head_sha") != candidate or latest.get("conclusion") != "success":
        raise ValueError("actions proof lacks exact-head successful check execution")
    completed_at = timestamp(
        producer.timestamp(latest.get("completed_at"), "actions latest_check completed_at"),
        "actions latest_check completed_at",
    )
    if completed_at < evaluated_at:
        raise ValueError("actions required check predates the publication decision")
    captured_at = timestamp(
        producer.timestamp(actions_snapshot.get("captured_at"), "actions captured_at"),
        "actions captured_at",
    )
    capture_delay = (captured_at - evaluated_at).total_seconds()
    if capture_delay < 0:
        raise ValueError("actions proof predates the publication decision")
    if capture_delay > 300:
        raise ValueError("actions proof is outside the five-minute publication window")
    published_at = timestamp(
        producer.timestamp(
            pull.get("last_published_at"), "actions pull request published_at"
        ),
        "actions pull request published_at",
    )
    if published_at < evaluated_at:
        raise ValueError("actions pull request subject predates the publication decision")
    if completed_at > captured_at:
        raise ValueError("actions required check completes after its capture")
    if published_at > captured_at:
        raise ValueError("actions pull request publication occurs after its capture")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_dual_forge_contract.py RECEIPT.json", file=sys.stderr)
        return 64
    path = Path(argv[1])
    if not path.is_file():
        print(f"INPUT_ERROR missing receipt: {path}", file=sys.stderr)
        return 64
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        obj(data, "root")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INPUT_ERROR {exc}", file=sys.stderr)
        return 64

    try:
        if data.get("schema_version") != "dual-forge-repository-loop/v3":
            raise ValueError("unsupported schema_version")

        repository_binding = obj(data.get("repository"), "repository")
        if set(repository_binding) != {"name", "default_branch"}:
            raise ValueError("repository binding fields drifted")
        repository = repository_binding.get("name")
        default_branch = repository_binding.get("default_branch")
        if not isinstance(repository, str) or REPOSITORY.fullmatch(repository) is None:
            raise ValueError("repository.name must be an exact OWNER/REPOSITORY identity")
        if (
            not isinstance(default_branch, str)
            or BRANCH.fullmatch(default_branch) is None
            or ".." in default_branch
        ):
            raise ValueError("repository.default_branch is empty or unsafe")

        authority = obj(data.get("authority"), "authority")
        if authority != {"implementation": "local-forgejo", "publication": "github", "actions": "github-actions"}:
            raise ValueError("authority planes must remain local-forgejo/github/github-actions")

        github = obj(data.get("github"), "github")
        forgejo = obj(data.get("forgejo"), "forgejo")
        local = obj(data.get("local"), "local")
        if set(github) != {"repository_full_name", "remote_name", "observed_main_sha"}:
            raise ValueError("github binding fields drifted")
        if set(forgejo) != {"repository", "remote_name", "observed_main_sha"}:
            raise ValueError("forgejo binding fields drifted")
        if set(local) != {"main_branch", "local_main_sha", "worktree_root"}:
            raise ValueError("local binding fields drifted")
        if github.get("repository_full_name") != repository:
            raise ValueError("GitHub repository identity differs from repository binding")
        if not isinstance(forgejo.get("repository"), str) or REPOSITORY.fullmatch(forgejo["repository"]) is None:
            raise ValueError("Forgejo repository must be an exact OWNER/REPOSITORY identity")
        if local.get("main_branch") != default_branch:
            raise ValueError("local main branch differs from repository default branch")
        if github.get("remote_name") == forgejo.get("remote_name"):
            raise ValueError("GitHub and Forgejo remote names must be distinct")
        for remote in (github.get("remote_name"), forgejo.get("remote_name")):
            if not isinstance(remote, str) or not remote.strip() or "@" in remote or "://" in remote:
                raise ValueError("bindings contain remote names only; credential-bearing/URL values are forbidden")

        sha(github.get("observed_main_sha"), "github.observed_main_sha")
        sha(forgejo.get("observed_main_sha"), "forgejo.observed_main_sha")
        sha(local.get("local_main_sha"), "local.local_main_sha")

        ns = obj(data.get("issue_namespaces"), "issue_namespaces")
        fp, gp = ns.get("forgejo"), ns.get("github")
        if not isinstance(fp, str) or not isinstance(gp, str) or not fp or not gp or fp == gp:
            raise ValueError("Forgejo and GitHub issue namespaces must be non-empty and distinct")
        links = data.get("issue_links", [])
        if not isinstance(links, list):
            raise ValueError("issue_links must be an array")
        linked_forgejo_issue_numbers: set[int] = set()
        for i, link in enumerate(links):
            link = obj(link, f"issue_links[{i}]")
            fref, gref = link.get("forgejo_issue"), link.get("github_issue")
            if not isinstance(fref, str) or not fref.startswith(fp):
                raise ValueError(f"issue_links[{i}].forgejo_issue must use {fp!r}")
            if not isinstance(gref, str) or not gref.startswith(gp):
                raise ValueError(f"issue_links[{i}].github_issue must use {gp!r}")
            if fref == gref:
                raise ValueError("cross-forge issue identities cannot collapse")
            suffix = fref[len(fp):]
            if not suffix.isdigit() or int(suffix) <= 0:
                raise ValueError(f"issue_links[{i}].forgejo_issue lacks a positive issue number")
            linked_forgejo_issue_numbers.add(int(suffix))

        history = data.get("history")
        if not isinstance(history, list) or any(not isinstance(x, str) for x in history):
            raise ValueError("history must be an array of state names")
        if EXPECTED_HISTORY[: len(history)] != history:
            raise ValueError("delivery history must preserve local-main-first and reconciliation-before-publication order")

        pub = obj(data.get("publication"), "publication")
        candidate = sha(pub.get("candidate_sha"), "publication.candidate_sha")
        if set(pub) != {"candidate_sha", "git_proof", "decision_bundle"}:
            raise ValueError("publication fields drifted")

        actions = obj(data.get("actions"), "actions")

        evidence = obj(data.get("evidence"), "evidence")
        if set(evidence) != set(REQUIRED_PUBLICATION_EVIDENCE) | {"final_merge"}:
            raise ValueError("evidence lane inventory drifted")
        for key, value in evidence.items():
            if value not in EVIDENCE:
                raise ValueError(f"evidence.{key} has invalid state {value!r}")

        if history and history[-1] == "GITHUB_PUBLICATION_READY":
            unproved = [k for k in REQUIRED_PUBLICATION_EVIDENCE if evidence.get(k) != "PASS"]
            if unproved:
                raise ValueError("publication allowed with unproved runtime lanes: " + ", ".join(unproved))
            if evidence.get("github_actions") != "PASS":
                raise ValueError("publication allowed without GitHub Actions PASS")
            if evidence.get("final_merge") != "HUMAN_ADMIT_REQUIRED":
                raise ValueError("publication-ready receipt cannot self-authorize final merge")
            forgejo_delivery_repository_id, delivered_closed_issue_numbers = verify_forgejo_delivery(
                path.resolve(), data.get("implementation"), forgejo["repository"],
                default_branch, forgejo["observed_main_sha"], local["local_main_sha"],
                linked_forgejo_issue_numbers,
            )
            actual_tree = verify_git_ancestry(
                path.resolve(), pub["git_proof"],
                github["observed_main_sha"], forgejo["observed_main_sha"],
                local["local_main_sha"], candidate,
            )
            verify_canonical_publication(
                path.resolve(), pub, actions, data.get("observations"),
                data.get("reconciliation"), github["observed_main_sha"],
                forgejo["observed_main_sha"], local["local_main_sha"],
                candidate, actual_tree,
                repository, default_branch, forgejo["repository"],
                forgejo_delivery_repository_id,
                delivered_closed_issue_numbers,
                github["remote_name"], forgejo["remote_name"],
            )
        else:
            print("NOT_EXERCISED dual-forge contract is only a partial state prefix")
            return 3

    except ValueError as exc:
        return fail(str(exc))

    print("PASS dual-forge contract structurally closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
