#!/usr/bin/env python3
"""Run the private-lineage mode against a real local Forgejo instance.

#262 keeps three lanes open that no hermetic test can close: a live local
Forgejo canary, a real private consumer extraction, and a provider cleanup
disposition. Each needs a live subject, so this producer creates one instead of
borrowing a real private tree: the private source is a synthetic fixture built
here, sealed to Forgejo, pushed over the wire, read back, extracted through the
clean-room boundary, and finally deleted with the deletion asserted rather than
claimed.

Every Forgejo mutation is a repository this run created and this run deletes.
Existing repositories and their branches are never touched. `--keep` leaves the
throwaway repository behind and the receipt records it as outstanding.

Credentials are read from the existing Git credential helper in memory, exactly
as capture_origin_ref.py does. Nothing here writes, prints, or receipts them.

Usage:
  run_private_lineage_canary.py --owner OWNER --out DIR [--forge-url URL]
                                [--dry-run] [--keep]

--dry-run runs the whole chain except the three provider mutations (create,
push, delete), so the local half can be verified before anything is created.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture_origin_ref import LOOPBACK_FORGES, atomic, credentials  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
MODE = SKILL / "modes" / "forgejo-private-repository-loop"
SCHEMA = "dual-forge-repository-loop/private-lineage-canary-receipt/v1"
SUBSTRATE_SCHEMA = "dual-forge-repository-loop/forgejo-substrate-receipt/v1"

CHAIN = [
    "forgejo-substrate-probe",
    "credential-helper-auth-lane",
    "private-repository-created",
    "private-source-audited",
    "forgejo-only-bound",
    "private-main-sealed",
    "cleanroom-requirements-exported",
    "fresh-root-verified",
    "provider-cleanup-disposition",
    "local-retirement-inventory",
]

# The private literal exists only inside this run's synthetic fixture. It is the
# subject the audit and the clean-room boundary have to catch on real bytes.
PRIVATE_LITERAL = "ACME-PRIVATE-LINEAGE-CANARY-262"
PRIVATE_PROSE = (
    "The settlement ledger reconciles every provisional hold against the "
    "acquirer statement before the nightly capture window closes, and refuses "
    "any hold whose acquirer reference was never observed on the statement."
)
PUBLIC_PROSE = (
    "A bounded action reads state, acquires one fresh observation, and derives "
    "its terminal result mechanically from that observation."
)


class CanaryError(RuntimeError):
    pass


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Absolute host paths make a committed receipt unresolvable the moment the
# worktree or the temporary workspace is gone. Commands are receipted against
# stable roots instead.
PORTABLE: list[tuple[str, str]] = []


def portable(value: str) -> str:
    for prefix, token in PORTABLE:
        value = value.replace(prefix, token)
    return value


def run(argv: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    """Run a command and record argv plus exit code. Never records output bytes."""
    done = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        env={**os.environ, **(env or {})} if env else None,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    return {
        "argv": [portable(item) for item in argv],
        "exit_code": done.returncode,
        "stdout_tail": [portable(line) for line in done.stdout.strip().splitlines()[-1:]],
        "stderr_tail": [portable(line) for line in done.stderr.strip().splitlines()[-2:]],
    }


def expect(record: dict[str, Any], code: int, label: str) -> dict[str, Any]:
    if record["exit_code"] != code:
        raise CanaryError(
            f"{label}: expected exit {code}, observed {record['exit_code']} "
            f"({record['stderr_tail']})"
        )
    return record


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if done.returncode:
        raise CanaryError(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout.strip()


def api(
    forge_url: str,
    endpoint: str,
    *,
    auth: str | None = None,
    method: str = "GET",
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One typed Forgejo request. Records method, endpoint, status and digest."""
    url = f"{forge_url}/api/v1/{endpoint}"
    payload = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json"}
    if auth:
        headers["Authorization"] = f"Basic {auth}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=payload, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310 - loopback only
            raw = response.read()
            status = response.status
    except HTTPError as error:
        raw = error.read()
        status = error.code
    except (URLError, TimeoutError) as error:
        raise CanaryError(f"{method} /api/v1/{endpoint} did not reach the forge: {error}") from error
    try:
        parsed = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        parsed = None
    return {
        "method": method,
        "endpoint": f"/api/v1/{endpoint}",
        "http_status": status,
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
        "_body": parsed,
    }


def public(call: dict[str, Any]) -> dict[str, Any]:
    """The receipt-safe view of a request: no response body, only its digest."""
    return {key: value for key, value in call.items() if not key.startswith("_")}


def container_evidence() -> dict[str, Any]:
    """What is actually serving the forge, or ABSENT when it cannot be observed.

    A port answering 200 does not say which process owns it, and the runtime
    that cannot see the container has no business naming one.
    """
    done = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"],
        capture_output=True, text=True, check=False,
    )
    if done.returncode != 0:
        return {"state": "ABSENT", "detail": done.stderr.strip().splitlines()[-1:] or ["docker unavailable"]}
    rows = [line.split("|") for line in done.stdout.splitlines() if "forgejo" in line]
    return {
        "state": "PASS" if rows else "ABSENT",
        "containers": [
            {"name": row[0], "image": row[1], "status": row[2], "ports": row[3] if len(row) > 3 else ""}
            for row in rows
        ],
    }


def build_private_source(root: Path) -> str:
    root.mkdir(parents=True)
    (root / "README.md").write_text(
        f"# {PRIVATE_LITERAL} consumer\n\n{PRIVATE_PROSE}\n", encoding="utf-8"
    )
    (root / "src").mkdir()
    (root / "src" / "settlement.py").write_text(
        f'"""{PRIVATE_PROSE}"""\n\nPROJECT = "{PRIVATE_LITERAL}"\n\n\n'
        "def reconcile(holds, statement):\n"
        "    observed = {item.acquirer_reference for item in statement}\n"
        "    return [hold for hold in holds if hold.acquirer_reference in observed]\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    git(root, "config", "user.name", "Private Lineage Canary")
    git(root, "config", "user.email", "private-lineage@invalid.local")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "Initialize private settlement consumer")
    return git(root, "rev-parse", "HEAD")


def build_public_source(root: Path) -> None:
    root.mkdir(parents=True)
    (root / "README.md").write_text(
        f"# Bounded action contract\n\n{PUBLIC_PROSE}\n", encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    git(root, "config", "user.name", "Clean Room Author")
    git(root, "config", "user.email", "clean-room@invalid.local")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "Author the public contract independently")


def cleanroom_packet(digest: str) -> dict[str, Any]:
    return {
        "schema": "forgejo-private-cleanroom-packet/v1",
        "packet_id": "settlement-reconciliation-contract",
        "private_subject_digest": digest,
        "items": [
            {
                "id": "observation-before-terminal-result",
                "kind": "state-machine",
                "statement": PUBLIC_PROSE,
                "assertions": [
                    "A transport acknowledgement cannot create a terminal result by itself.",
                    "A provisional record without a matching observed reference is refused.",
                ],
                "public_references": [
                    {"label": "Git documentation", "url": "https://git-scm.com/docs"}
                ],
            },
            {
                "id": "denied-reference-negative-control",
                "kind": "synthetic-negative-control",
                "statement": (
                    "A synthetic record naming a reference absent from the observation "
                    "set must be refused rather than reconciled."
                ),
                "assertions": ["The control fails closed when the observation set is empty."],
                "public_references": [],
            },
        ],
    }


def disposition_document(identity: str, deleted: bool) -> dict[str, Any]:
    created = "REMOVED" if deleted else "PROVIDER_DISPOSITION_REQUIRED"
    return {
        "schema": "provider-retention-disposition/v1",
        "repository_identity_digest": identity,
        "surfaces": {
            # Surfaces this run actually created on the provider.
            "branches": created,
            "code_search_indexes": "PROVIDER_DISPOSITION_REQUIRED",
            "backups_replicas": "NOT_AVAILABLE",
            # Surfaces that never existed on a throwaway repository created with
            # auto_init=false and a single pushed branch.
            "tags": "CLEAN",
            "pull_request_refs": "CLEAN",
            "review_diffs": "CLEAN",
            "actions_logs": "CLEAN",
            "actions_artifacts": "CLEAN",
            "actions_caches": "CLEAN",
            "releases": "CLEAN",
            "packages": "CLEAN",
            "pages": "CLEAN",
            "wiki": "CLEAN",
            "lfs": "CLEAN",
            "forks": "CLEAN",
            "mirrors": "CLEAN",
            "webhooks": "CLEAN",
            "deploy_keys": "CLEAN",
            "apps": "CLEAN",
            "environments": "CLEAN",
            "secrets_metadata": "CLEAN",
        },
    }


def retirement_document(identity: str, head: str, retired: bool) -> dict[str, Any]:
    return {
        "schema": "private-retirement-inventory/v1",
        "repository_identity_digest": identity,
        "observed_at_head": head,
        "surfaces": {
            "clones": "RETIRED" if retired else "PRESENT",
            "worktrees": "RETIRED" if retired else "PRESENT",
            "mirrors": "ABSENT",
            "bundles": "ABSENT",
            "caches": "ABSENT",
            "forks": "ABSENT",
            # The Forgejo token stays in the runtime owner's credential helper by
            # design: this loop never owns it and cannot retire it.
            "credentials": "ACCEPTED_LIMITATION",
        },
    }


def main() -> int:  # noqa: C901 - one linear canary, split would hide the order
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--forge-url", default="http://127.0.0.1:3000")
    parser.add_argument("--issue", type=int, default=262)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    if args.forge_url not in LOOPBACK_FORGES:
        print("CANARY ERROR: forge URL must be the allowlisted loopback forge", file=sys.stderr)
        return 64

    started = time.time()
    chain: list[dict[str, Any]] = []
    mutations: list[dict[str, Any]] = []
    workspace = Path(tempfile.mkdtemp(prefix="private-lineage-canary."))
    PORTABLE.extend([
        (str(workspace), "<workspace>"),
        (str(args.out.resolve()), "<receipts>"),
        (str(args.out), "<receipts>"),
        (str(SKILL), "<skill>"),
    ])
    private_root = workspace / "private-consumer"
    public_root = workspace / "public-implementation"
    fresh_root = workspace / "fresh-root"
    patterns = workspace / "private-patterns.txt"
    repo_name = f"canary-262-private-{int(started)}"
    full_name = f"{args.owner}/{repo_name}"
    remote_url = f"{args.forge_url}/{full_name}.git"
    identity = sha256_text(f"forgejo://{args.forge_url}/{full_name}")

    def link(name: str, state: str, **fields: Any) -> None:
        chain.append({"link": name, "state": state, **fields})

    try:
        # 1. Substrate probe: unauthenticated, so it separates "the forge is up"
        #    from "this runtime is admitted to it".
        version = api(args.forge_url, "version")
        if version["http_status"] != 200 or not isinstance(version["_body"], dict):
            raise CanaryError("Forgejo /api/v1/version did not answer 200 with an object")
        forge_version = str(version["_body"].get("version", ""))
        containers = container_evidence()
        link(
            "forgejo-substrate-probe",
            "PASS",
            detail=f"unauthenticated version read answered 200 with version {forge_version}",
            request=public(version),
            container_evidence=containers,
        )

        # 2. Credential lane: the existing helper, in memory, never on disk.
        username, password = credentials(args.forge_url)
        auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        whoami = api(args.forge_url, "user", auth=auth)
        if whoami["http_status"] != 200 or not isinstance(whoami["_body"], dict):
            raise CanaryError("authenticated /api/v1/user read failed")
        actor = str(whoami["_body"].get("login", ""))
        if actor != args.owner:
            raise CanaryError(f"credential helper identity {actor!r} is not the requested owner")
        link(
            "credential-helper-auth-lane",
            "PASS",
            detail=(
                "git credential fill supplied an in-memory credential for the forge host; "
                f"authenticated identity is {actor}"
            ),
            credential_source="git credential fill (existing helper)",
            request=public(whoami),
        )

        # 3. Write lane: a new throwaway PRIVATE repository, never an existing one.
        if args.dry_run:
            link(
                "private-repository-created",
                "NOT_EXERCISED",
                detail="--dry-run: no provider mutation was attempted",
            )
            repository_id = None
        else:
            created = api(
                args.forge_url,
                "user/repos",
                auth=auth,
                method="POST",
                body={
                    "name": repo_name,
                    "private": True,
                    "auto_init": False,
                    "description": "skills-shared #262 private-lineage canary; deleted by the same run",
                },
            )
            if created["http_status"] != 201 or not isinstance(created["_body"], dict):
                raise CanaryError(f"repository creation answered {created['http_status']}")
            if created["_body"].get("private") is not True:
                raise CanaryError("created repository is not private")
            repository_id = created["_body"].get("id")
            mutations.append(
                {
                    "kind": "forgejo-repository",
                    "subject": full_name,
                    "repository_id": repository_id,
                    "private": True,
                    "purpose": "live private-lineage canary subject for issue #262",
                    "cleanup": "delete-in-this-run",
                }
            )
            link(
                "private-repository-created",
                "PASS",
                detail=f"created private repository {full_name} id={repository_id}",
                request=public(created),
            )

        # 4. Audit the real private source: the literal must be found, and a
        #    clean control must not be, or the audit proves nothing.
        head = build_private_source(private_root)
        patterns.write_text(f"{PRIVATE_LITERAL}\n", encoding="utf-8")
        audit_script = str(MODE / "scripts" / "audit_git_history.py")
        red = expect(
            run(["python3", audit_script, "--repo", str(private_root),
                 "--patterns", str(patterns), "--output", str(workspace / "audit-private.json")]),
            2,
            "private source audit",
        )
        build_public_source(public_root)
        green = expect(
            run(["python3", audit_script, "--repo", str(public_root),
                 "--patterns", str(patterns), "--output", str(workspace / "audit-public.json")]),
            0,
            "public source audit",
        )
        matches = json.loads((workspace / "audit-private.json").read_text())["match_count"]
        link(
            "private-source-audited",
            "PASS",
            detail=(
                f"real worktree/object audit found {matches} denied-literal surfaces in the "
                "private source and none in the independently authored public source"
            ),
            head=head,
            commands=[red, green],
        )

        # 5. Seal the private checkout to the exact Forgejo destination.
        configure = expect(
            run(["bash", str(MODE / "scripts" / "configure_forgejo_only.sh"),
                 str(private_root), remote_url]),
            0,
            "configure_forgejo_only.sh",
        )
        check = expect(
            run(["python3", str(MODE / "scripts" / "check_forgejo_only.py"), str(private_root)],
                env={"PYTHONPATH": str(MODE / "scripts")}),
            0,
            "check_forgejo_only.py",
        )
        hook = private_root / ".git" / "hooks" / "pre-push"
        refused = expect(
            run(["bash", str(hook), "origin", "https://github.com/example/private.git"],
                cwd=private_root),
            72,
            "pre-push GitHub destination",
        )
        admitted = expect(
            run(["bash", str(hook), "forgejo", remote_url], cwd=private_root),
            0,
            "pre-push admitted destination",
        )
        link(
            "forgejo-only-bound",
            "PASS",
            detail=(
                "the live checkout carries exactly one admitted remote pointing at the real "
                "forge; the installed guard admitted it and refused a GitHub destination"
            ),
            admitted_remote_url=remote_url,
            commands=[configure, check, admitted, refused],
        )

        # 6. Push over the wire and read the head back from the provider.
        if args.dry_run:
            link("private-main-sealed", "NOT_EXERCISED",
                 detail="--dry-run: nothing was pushed")
        else:
            push = expect(
                run(["git", "-C", str(private_root), "push", "forgejo", "HEAD:refs/heads/main"]),
                0,
                "git push forgejo",
            )
            mutations.append(
                {
                    "kind": "forgejo-branch",
                    "subject": f"{full_name}@refs/heads/main",
                    "purpose": "prove the sealed checkout reaches the real forge through the guard",
                    "cleanup": "removed-with-repository",
                }
            )
            # The forge answers 404 for a branch it has accepted but not yet
            # indexed, so a single read turns a live timing gap into a false
            # negative. Bounded retries; the count is receipted.
            attempts = 0
            while attempts < 10:
                attempts += 1
                branch = api(args.forge_url, f"repos/{full_name}/branches/main", auth=auth)
                observed = (branch["_body"] or {}).get("commit", {}).get("id")
                if branch["http_status"] == 200 and observed == head:
                    break
                time.sleep(0.5)
            if branch["http_status"] != 200 or observed != head:
                raise CanaryError(
                    f"provider readback did not confirm the pushed head (status "
                    f"{branch['http_status']}, observed {observed!r}, local {head!r})"
                )
            link(
                "private-main-sealed",
                "PASS",
                detail=(
                    "push traversed the installed pre-push guard and the authenticated "
                    "readback returned the exact local head"
                ),
                head=head,
                readback_attempts=attempts,
                commands=[push],
                request=public(branch),
            )

        # 7. Extraction: fingerprint the real private source, then prove the
        #    clean-room packet is admitted and a leaking one is refused.
        fingerprints = workspace / "private-fingerprints.json"
        built = expect(
            run(["python3", str(MODE / "scripts" / "build_private_fingerprints.py"),
                 "--source", str(private_root), "--output", str(fingerprints)]),
            0,
            "build_private_fingerprints.py",
        )
        packet = workspace / "cleanroom-packet.json"
        packet.write_text(json.dumps(cleanroom_packet(sha256_text(head)), indent=2), encoding="utf-8")
        leak = workspace / "cleanroom-packet-leaking.json"
        leaking = cleanroom_packet(sha256_text(head))
        leaking["items"][0]["statement"] = PRIVATE_PROSE
        leak.write_text(json.dumps(leaking, indent=2), encoding="utf-8")
        checker = str(MODE / "scripts" / "check_cleanroom_packet.py")
        admitted_packet = expect(
            run(["python3", checker, str(packet), "--private-patterns", str(patterns),
                 "--private-fingerprints", str(fingerprints)]),
            0,
            "clean-room packet",
        )
        refused_packet = expect(
            run(["python3", checker, str(leak), "--private-patterns", str(patterns),
                 "--private-fingerprints", str(fingerprints)]),
            2,
            "leaking clean-room packet",
        )
        link(
            "cleanroom-requirements-exported",
            "PASS",
            detail=(
                "fingerprints built from the live private worktree admit the generalized "
                "packet and refuse a packet carrying the private source prose"
            ),
            private_fingerprints_sha256=sha256_file(fingerprints),
            packet_sha256=sha256_file(packet),
            commands=[built, admitted_packet, refused_packet],
        )

        # 8. Fresh root and separate lineage against the live private repository.
        snapshot = expect(
            run(["bash", str(MODE / "scripts" / "create_fresh_root_snapshot.sh"),
                 str(public_root), str(fresh_root), "--patterns", str(patterns),
                 "--receipt", str(workspace / "fresh-root-receipt.json")]),
            0,
            "create_fresh_root_snapshot.sh",
        )
        lineage = expect(
            run(["bash", str(MODE / "scripts" / "assert_no_shared_lineage.sh"),
                 str(fresh_root), str(private_root)]),
            0,
            "assert_no_shared_lineage.sh",
        )
        link(
            "fresh-root-verified",
            "PASS",
            detail=(
                "the public snapshot has exactly one root, no remotes and no alternates, and "
                "shares no merge base or non-empty object with the pushed private repository"
            ),
            fresh_root_head=git(fresh_root, "rev-parse", "HEAD"),
            commands=[snapshot, lineage],
        )

        # 9. Provider cleanup: delete what this run created, then prove it is gone.
        deleted = False
        if args.dry_run:
            link("provider-cleanup-disposition", "NOT_EXERCISED",
                 detail="--dry-run: nothing was created, so nothing is owed deletion")
        elif args.keep:
            link("provider-cleanup-disposition", "HUMAN_ADMIT_REQUIRED",
                 detail=f"--keep: {full_name} is still on the forge and is owed deletion")
        else:
            removal = api(args.forge_url, f"repos/{full_name}", auth=auth, method="DELETE")
            if removal["http_status"] != 204:
                raise CanaryError(f"repository deletion answered {removal['http_status']}")
            absent = api(args.forge_url, f"repos/{full_name}", auth=auth)
            if absent["http_status"] != 404:
                raise CanaryError(
                    f"deleted repository still answers {absent['http_status']}; deletion is a claim"
                )
            deleted = True
            for record in mutations:
                record["cleanup"] = "DELETED"
            link(
                "provider-cleanup-disposition",
                "PASS",
                detail="repository deleted and the absence confirmed by an authenticated 404",
                requests=[public(removal), public(absent)],
            )

        disposition = args.out / "private-lineage-provider-disposition.json"
        atomic(disposition, disposition_document(identity, deleted))
        disposition_check = expect(
            run(["python3", str(MODE / "scripts" / "check_provider_retention.py"), str(disposition)]),
            0,
            "check_provider_retention.py",
        )
        chain[-1]["disposition_document"] = disposition.name
        chain[-1]["disposition_sha256"] = sha256_file(disposition)
        chain[-1]["disposition_check"] = disposition_check

        # 10. Local retirement: the copies this run made must go too.
        shutil.rmtree(workspace, ignore_errors=True)
        retired = not private_root.exists() and not fresh_root.exists()
        inventory = args.out / "private-lineage-retirement-inventory.json"
        atomic(inventory, retirement_document(identity, head, retired))
        inventory_check = expect(
            run(["python3", str(MODE / "scripts" / "check_retirement_inventory.py"), str(inventory)]),
            0,
            "check_retirement_inventory.py",
        )
        link(
            "local-retirement-inventory",
            "PASS" if retired else "FAIL",
            detail=(
                "the canary workspace holding the private clone and worktrees was removed and "
                "its absence observed; the runtime owner's credential is an accepted limitation"
            ),
            inventory_document=inventory.name,
            inventory_sha256=sha256_file(inventory),
            commands=[inventory_check],
        )

        states = {item["link"]: item["state"] for item in chain}
        receipt = {
            "schema": SCHEMA,
            "issue": args.issue,
            "started_at": int(started),
            "duration_ms": int((time.time() - started) * 1000),
            "forge": {
                "url": args.forge_url,
                "version": forge_version,
                "authenticated_identity": actor,
            },
            "subject": {
                "repository": full_name,
                "repository_id": repository_id,
                "private": True,
                "identity_digest": identity,
                "head": head,
            },
            "chain_declared": CHAIN,
            "chain": chain,
            "coverage": {
                "pass": sorted(k for k, v in states.items() if v == "PASS"),
                "not_exercised": sorted(k for k, v in states.items() if v == "NOT_EXERCISED"),
                "other": {k: v for k, v in states.items() if v not in {"PASS", "NOT_EXERCISED"}},
            },
            "mutations_performed": mutations,
            "declared_non_claims": [
                "the private source is a fixture built by this run, so no real private tree was audited",
                "reaching this forge says nothing about any other Forgejo instance or provider",
                "provider-side search indexes and backups are not observable from this API and stay limited",
                "the Forgejo credential remains in the runtime owner's helper; this run cannot retire it",
                "no GitHub surface was contacted and no GitHub evidence is claimed here",
            ],
            "dry_run": args.dry_run,
        }
        atomic(args.out / "private-lineage-canary.receipt.json", receipt)
        atomic(
            args.out / "forgejo-substrate.receipt.json",
            {
                "schema": SUBSTRATE_SCHEMA,
                "host": "claude-code-local",
                "observed_at": int(started),
                "forge_url": args.forge_url,
                "version": forge_version,
                "version_request": public(version),
                "authenticated_identity_request": public(whoami),
                "container_evidence": containers,
                "state": "PASS",
                "detail": (
                    "a local Forgejo answers this host on the allowlisted loopback forge and "
                    "admits the existing Git credential helper; the substrate is present, not ABSENT"
                ),
                "probe_note": (
                    "an agent command sandbox that intercepts loopback connections refuses "
                    "127.0.0.1:3000 with ECONNREFUSED while lsof still shows the listener, so a "
                    "sandboxed probe observes exactly what an absent forge looks like; ABSENT is "
                    "only honest once the probe has run outside that sandbox"
                ),
                "declared_non_claims": [
                    "this is substrate evidence only: it admits no delivery, issue, or PR transition",
                    "it is scoped to this host and this loopback URL and travels to no other runtime",
                    "the act_runner container is observed, not exercised: no Forgejo Actions job ran",
                ],
            },
        )
        print(
            f"PRIVATE-LINEAGE CANARY GREEN forge={forge_version} subject={full_name} "
            f"deleted={deleted} pass={len(receipt['coverage']['pass'])}/{len(CHAIN)}"
        )
        return 0
    except (CanaryError, OSError, ValueError) as error:
        print(f"PRIVATE-LINEAGE CANARY RED: {error}", file=sys.stderr)
        if mutations and not args.dry_run:
            print(
                "OUTSTANDING FORGEJO MUTATIONS: "
                + ", ".join(f"{item['kind']}:{item['subject']}" for item in mutations),
                file=sys.stderr,
            )
        return 2
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
