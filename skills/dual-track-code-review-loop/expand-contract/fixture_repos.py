#!/usr/bin/env python3
"""Build the disposable two-repository fixture the R2 protocol runs over.

Two local git repositories -- one provider, one consumer -- created in a
throwaway directory, each with a base commit and one expansion commit. Nothing
is fetched, nothing is pushed, and no repository outside the temporary directory
is read or written. The repositories are deleted by the caller; nothing here is
ever committed, which is why the builder is a function and not a checked-in
`.git`.

Why real repositories rather than synthetic hex: the one law this lane adds with
no precedent in the tree is FALSE_CROSS_REPO_GIT_PARENT, and a synthetic commit
string cannot be asked whether it exists in the other repository. Real objects
can: `git cat-file -e` in the consumer repository, given the provider's commit,
exits non-zero, and that exit code is the physical fact the schema's typing and
the compiler's refusal are two independent restatements of.

Determinism is a requirement, not a nicety, because the compiled projections are
byte-compared. Every input to git's object hash is pinned here -- author and
committer identity, both dates, the timezone, the file bytes and the paths --
and the process environment is stripped of the user's git configuration, so the
same commit SHAs come out on every host. `--selftest` prints them.

Exits: 0 green, 2 the rebuild did not reproduce the recorded SHAs, 70 git is
absent (a typed absence, never a pass).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SUBJECT = HERE / "fixtures" / "two-repo-git-subject.json"

# Pinned to the epoch with an explicit offset. A local timezone or a real clock
# would make the commit SHA a property of the host that ran the build.
PINNED_ENV = {
    "GIT_AUTHOR_NAME": "dtcr-fixture",
    "GIT_AUTHOR_EMAIL": "dtcr-fixture@example.invalid",
    "GIT_COMMITTER_NAME": "dtcr-fixture",
    "GIT_COMMITTER_EMAIL": "dtcr-fixture@example.invalid",
    "GIT_AUTHOR_DATE": "1700000000 +0000",
    "GIT_COMMITTER_DATE": "1700000000 +0000",
    # The user's own git configuration is not an input to a fixture SHA.
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_TERMINAL_PROMPT": "0",
    "TZ": "UTC",
    "LC_ALL": "C",
}

PROVIDER_BASE = {
    "proto/order_service.proto": (
        "syntax = \"proto3\";\n"
        "package order.v1;\n"
        "service OrderService {\n"
        "  rpc GetOrder (GetOrderRequest) returns (GetOrderResponse);\n"
        "}\n"
    ),
    "provider/handler_legacy.ext": (
        "handler GetOrder:\n"
        "  read order by id\n"
        "  return legacy shape\n"
    ),
}
PROVIDER_EXPANSION = {
    "proto/order_service.proto": (
        "syntax = \"proto3\";\n"
        "package order.v1;\n"
        "service OrderService {\n"
        "  rpc GetOrder (GetOrderRequest) returns (GetOrderResponse);\n"
        "  rpc GetOrderDetail (GetOrderDetailRequest) returns (GetOrderDetailResponse);\n"
        "}\n"
    ),
    "provider/handler_v2.ext": (
        "handler GetOrderDetail:\n"
        "  read order by id\n"
        "  return detail shape beside the legacy handler, which is untouched\n"
    ),
}
CONSUMER_BASE = {
    "consumer/order_client_legacy.ext": (
        "client OrderClientLegacy:\n"
        "  call OrderService.GetOrder\n"
    ),
}
CONSUMER_INVERSION = {
    "consumer/order_port.ext": (
        "port OrderPort:\n"
        "  get_order_detail(order_id)\n"
    ),
    "consumer/order_detail_adapter.ext": (
        "adapter OrderDetailAdapter implements OrderPort:\n"
        "  call OrderService.GetOrderDetail\n"
        "  on transport error or unimplemented: fall back to OrderClientLegacy\n"
    ),
}

REPOSITORIES = (
    ("provider", (("expand the contract with a second rpc beside the first", PROVIDER_BASE, PROVIDER_EXPANSION),)),
    ("consumer", (("invert the consumer onto a port with a legacy fallback", CONSUMER_BASE, CONSUMER_INVERSION),)),
)


class GitAbsent(Exception):
    """git is not on this host. A typed absence, not a pass and not a failure."""


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update(PINNED_ENV)
    return env


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env=_env(),
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} in {repo.name}: {result.stderr.strip()}")
    return result.stdout.strip()


def git_available() -> bool:
    return shutil.which("git") is not None


def _write(repo: Path, files: dict[str, str]) -> None:
    for relative, body in files.items():
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")


def _commit(repo: Path, message: str) -> dict[str, str]:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return {
        "commit": _git(repo, "rev-parse", "HEAD"),
        "tree": _git(repo, "rev-parse", "HEAD^{tree}"),
    }


def build(destination: Path) -> dict[str, Any]:
    """Create both repositories under `destination` and return their identities."""
    if not git_available():
        raise GitAbsent("git is not on PATH")
    built: dict[str, Any] = {}
    for name, steps in REPOSITORIES:
        repo = destination / name
        repo.mkdir(parents=True)
        # --template= (empty) keeps the fixture hermetic: no host hook/template
        # directory is read, so a runner whose git templates are unreadable
        # (sandboxed macOS, minimal containers) builds the same repository.
        _git(repo, "init", "-q", "-b", "main", "--template=")
        for message, base_files, expansion_files in steps:
            _write(repo, base_files)
            base = _commit(repo, f"base: {name} before the expansion")
            _write(repo, expansion_files)
            head = _commit(repo, message)
        built[name] = {
            "path": str(repo),
            "base_commit": base["commit"],
            "base_tree": base["tree"],
            "head_commit": head["commit"],
            "head_tree": head["tree"],
        }
    return built


def object_absent(repo: Path, oid: str) -> bool:
    """True when `oid` is not an object of `repo`.

    This is the arrival behind FALSE_CROSS_REPO_GIT_PARENT: the provider's commit
    is not reachable, not resolvable and not present in the consumer repository,
    so an ancestry claim spanning the two names an object one of them does not
    have. Reported as a boolean over a real exit code, not as a belief.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{oid}^{{commit}}"],
        capture_output=True,
        text=True,
        env=_env(),
    )
    return result.returncode != 0


def recorded() -> dict[str, Any]:
    return json.loads(SUBJECT.read_text(encoding="utf-8"))


def main() -> int:
    if not git_available():
        print(
            "DTCR-R2-FIXTURE-UNUSABLE: git is absent, so the two-repository subject "
            "cannot be built. This is PROVIDER_UNAVAILABLE for the fixture lane and "
            "is never reported as a pass.",
            file=sys.stderr,
        )
        return 70
    with tempfile.TemporaryDirectory(dir=str(HERE), prefix=".r2-scratch-") as scratch:
        built = build(Path(scratch))
        provider = Path(built["provider"]["path"])
        consumer = Path(built["consumer"]["path"])
        cross = {
            "provider_head_absent_in_consumer": object_absent(
                consumer, built["provider"]["head_commit"]
            ),
            "consumer_head_absent_in_provider": object_absent(
                provider, built["consumer"]["head_commit"]
            ),
        }
    emitted = {
        "provider": {key: value for key, value in built["provider"].items() if key != "path"},
        "consumer": {key: value for key, value in built["consumer"].items() if key != "path"},
        "cross_repository_object_absence": cross,
    }
    if "--selftest" not in sys.argv:
        json.dump(emitted, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    expected = recorded()
    drift = [
        f"{repo}.{key}: rebuilt {emitted[repo][key]} against recorded {expected[repo][key]}"
        for repo in ("provider", "consumer")
        for key in sorted(emitted[repo])
        if emitted[repo][key] != expected[repo].get(key)
    ]
    for key, value in cross.items():
        if value is not True:
            drift.append(f"{key} is {value!r}: the two repositories share an object")
    if drift:
        for row in drift:
            print(f"DTCR-R2-FIXTURE-RED {row}", file=sys.stderr)
        return 2
    print(
        f"DTCR-R2-FIXTURE-GREEN two repositories rebuilt to the recorded subject "
        f"(provider {emitted['provider']['head_commit'][:12]}, "
        f"consumer {emitted['consumer']['head_commit'][:12]}), "
        f"neither head is an object of the other"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
