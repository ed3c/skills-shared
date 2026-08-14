#!/usr/bin/env python3
"""Validate this repository's checked-in Git Town profile.

The failure this exists to catch is silent: Git Town ignores a key it does not
recognise, so a misspelled setting reads exactly like a setting that is in
force. That is not hypothetical -- writing `sync-tags` instead of `tags` while
building this profile produced a file that looked correct, parsed cleanly, and
left tag syncing on.

So every key must appear in ADMITTED_KEYS, and a key gets into ADMITTED_KEYS
only after it was observed taking effect in a real `git-town config` run against
the admitted release. An unrecognised key is refused rather than passed through,
because passing it through is how the defect stays invisible.

The profile is repository *policy*, not an enforcement boundary: a clone-local
`git config git-town.*` overrides it. That distinction is recorded here and in
the profile reference rather than being left for someone to discover.

Exits: 0 valid, 2 invalid, 64 usage or unreadable input.
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import Any

# section -> key -> observed effect in `git-town config` at 24.0.0.
# Every entry below was confirmed by running the admitted binary against a
# disposable repository carrying that key. Adding a key without doing that
# reintroduces exactly the defect this file guards.
ADMITTED_KEYS: dict[str, dict[str, str]] = {
    "branches": {
        "main": "main branch",
        "perennials": "perennial branches",
    },
    "sync": {
        "feature-strategy": "feature sync strategy",
        "perennial-strategy": "perennial sync strategy",
        "auto-resolve": "auto-resolve phantom conflicts",
        "push-branches": "push branches",
        "tags": "sync tags",
    },
    "ship": {
        "strategy": "ship strategy",
        "delete-tracking-branch": "delete tracking branch",
    },
}

MUTABLE_SELECTORS = ("latest", "current", "newest", "rolling", "head")

# Values this repository requires, with why, so a change has to argue with the
# reason rather than only with the value.
REQUIRED = {
    ("sync", "auto-resolve"): (
        False,
        "an unattended Worker must not resolve a conflict it cannot judge; a "
        "silently resolved semantic conflict is indistinguishable from one that "
        "never happened",
    ),
    ("sync", "push-branches"): (
        False,
        "background synchronisation must not publish",
    ),
    ("sync", "tags"): (
        False,
        "tags are release identity and a background sync must not move them",
    ),
}


class Invalid(Exception):
    pass


def load_profile(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise Invalid(
            f"{path.name} is absent. An absent profile is not a default "
            f"profile -- Git Town would fall back to whatever each clone "
            f"happens to have configured"
        )
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise Invalid(f"{path.name} is not valid TOML: {error}") from error


def check_keys(profile: dict[str, Any]) -> None:
    for section, body in profile.items():
        if section not in ADMITTED_KEYS:
            raise Invalid(
                f"section [{section}] is not admitted. Add it only after "
                f"observing its keys take effect in a real `git-town config` run"
            )
        if not isinstance(body, dict):
            raise Invalid(f"[{section}] must be a table")
        for key in body:
            if key not in ADMITTED_KEYS[section]:
                raise Invalid(
                    f"[{section}] {key!r} is not an admitted key. Git Town "
                    f"ignores keys it does not recognise, so a misspelling here "
                    f"reads exactly like a setting that is in force. Confirm the "
                    f"key takes effect against the admitted binary, then add it "
                    f"to ADMITTED_KEYS"
                )


def check_values(profile: dict[str, Any], default_branch: str) -> None:
    branches = profile.get("branches")
    if not branches or "main" not in branches:
        raise Invalid("[branches] main must be declared")
    main = branches["main"]
    if not isinstance(main, str) or not main:
        raise Invalid("[branches] main must be a non-empty string")
    if main.lower() in MUTABLE_SELECTORS:
        raise Invalid(
            f"[branches] main is {main!r}, a mutable selector; the trunk must "
            f"name one branch"
        )
    if main != default_branch:
        raise Invalid(
            f"[branches] main is {main!r} but the repository default branch is "
            f"{default_branch!r}; a Worker would sync against the wrong trunk"
        )

    if "perennials" not in branches:
        raise Invalid(
            "[branches] perennials must be declared. An empty list states that "
            "there are no long-lived release lines, which is a different claim "
            "from leaving the key out"
        )
    perennials = branches["perennials"]
    if not isinstance(perennials, list):
        raise Invalid("[branches] perennials must be a list")
    if main in perennials:
        raise Invalid(
            f"[branches] perennials repeats the trunk {main!r}; the main branch "
            f"is already perennial by type"
        )

    for (section, key), (expected, why) in REQUIRED.items():
        actual = profile.get(section, {}).get(key)
        if actual is None:
            raise Invalid(f"[{section}] {key} must be declared: {why}")
        if actual != expected:
            raise Invalid(f"[{section}] {key} must be {expected!r}: {why}")

    for section, body in profile.items():
        for key, value in body.items():
            if isinstance(value, str) and value.lower() in MUTABLE_SELECTORS:
                raise Invalid(
                    f"[{section}] {key} is {value!r}, a mutable selector"
                )


def check_reference(reference: Path) -> None:
    """The profile's meaning lives next to it, or it is only a set of values."""
    if not reference.is_file():
        raise Invalid(f"{reference.name} is absent")
    text = reference.read_text(encoding="utf-8")
    required_sections = (
        "## Lease roots",
        "## Publication gate",
        "## What this profile does not enforce",
    )
    for heading in required_sections:
        if heading not in text:
            raise Invalid(
                f"{reference.name} has no {heading!r} section; a profile without "
                f"declared lease roots, publication state, and its own limits is "
                f"a set of values with no boundary"
            )


def check_worker_surface(skill_root: Path) -> None:
    """The Worker must not be handed the operations that are Human-owned.

    Only executable files are scanned. Markdown is prose: a document that says
    "`git-town ship` is merge, and merge is Human-owned" is stating the
    prohibition, not performing it, and refusing that sentence would make the
    rule impossible to write down. The risk this accepts is a copyable command
    inside a fenced block; that is a documentation review question, not one this
    checker can answer without parsing intent.
    """
    forbidden = (
        ("git-town ship", "ship is merge, and merge is Human-owned"),
        ("push --force", "force push is never exposed to the Worker"),
        ("push -f ", "force push is never exposed to the Worker"),
    )
    for path in sorted(skill_root.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".sh", ".yml", ".yaml"}:
            continue
        if path.name == "check_repository_profile.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle, why in forbidden:
            for line in text.splitlines():
                stripped = line.strip()
                if needle not in line:
                    continue
                # A comment stating the prohibition is not a use of it.
                if stripped.startswith(("#", "//")):
                    continue
                raise Invalid(
                    f"{path.relative_to(skill_root)}: {needle!r} appears in an "
                    f"executable position: {why}"
                )


def validate(repo_root: Path, default_branch: str) -> None:
    profile = load_profile(repo_root / ".git-town.toml")
    check_keys(profile)
    check_values(profile, default_branch)
    skill_root = repo_root / "skills" / "git-town-stacked-pr-worker"
    check_reference(skill_root / "references" / "REPOSITORY_PROFILE.md")
    check_worker_surface(skill_root)


def _selftest(repo_root: Path, default_branch: str) -> int:
    import copy
    import tempfile

    try:
        validate(repo_root, default_branch)
    except Invalid as error:
        print(f"SELFTEST RED: canonical profile refused: {error}", file=sys.stderr)
        return 2

    canonical = load_profile(repo_root / ".git-town.toml")
    survived: list[str] = []

    mutations: list[tuple[str, Any]] = [
        ("misspelled key silently ignored by git-town",
         lambda p: p["sync"].__setitem__("sync-tags", False)),
        ("unknown section",
         lambda p: p.__setitem__("hosting", {"platform": "github"})),
        ("mutable trunk selector",
         lambda p: p["branches"].__setitem__("main", "latest")),
        ("trunk disagrees with the repository default branch",
         lambda p: p["branches"].__setitem__("main", "trunk")),
        ("perennials undeclared",
         lambda p: p["branches"].pop("perennials")),
        ("trunk repeated as a perennial",
         lambda p: p["branches"].__setitem__("perennials", ["main"])),
        ("auto-resolve enabled for unattended sync",
         lambda p: p["sync"].__setitem__("auto-resolve", True)),
        ("auto-push enabled for background sync",
         lambda p: p["sync"].__setitem__("push-branches", True)),
        ("tag syncing enabled",
         lambda p: p["sync"].__setitem__("tags", True)),
        ("auto-resolve omitted entirely",
         lambda p: p["sync"].pop("auto-resolve")),
        ("mutable value on an admitted key",
         lambda p: p["ship"].__setitem__("strategy", "latest")),
    ]

    with tempfile.TemporaryDirectory(prefix="gt-profile.") as raw:
        work = Path(raw)
        for name, apply in mutations:
            body = copy.deepcopy(canonical)
            apply(body)
            try:
                check_keys(body)
                check_values(body, default_branch)
            except Invalid:
                continue
            survived.append(name)

        # An absent profile must be refused, not treated as defaults.
        try:
            load_profile(work / ".git-town.toml")
            survived.append("absent profile accepted")
        except Invalid:
            pass

        # An absent reference must be refused.
        try:
            check_reference(work / "REPOSITORY_PROFILE.md")
            survived.append("absent profile reference accepted")
        except Invalid:
            pass

        # A reference missing a required section must be refused.
        partial = work / "REPOSITORY_PROFILE.md"
        partial.write_text("# Profile\n\n## Lease roots\n\nsomething\n", encoding="utf-8")
        try:
            check_reference(partial)
            survived.append("reference missing publication gate accepted")
        except Invalid:
            pass

        # A Worker surface exposing ship must be refused.
        fake_skill = work / "skill"
        (fake_skill / "scripts").mkdir(parents=True)
        (fake_skill / "references").mkdir(parents=True)
        (fake_skill / "references" / "REPOSITORY_PROFILE.md").write_text(
            "## Lease roots\n## Publication gate\n## What this profile does not enforce\n",
            encoding="utf-8",
        )
        (fake_skill / "scripts" / "worker.sh").write_text(
            "#!/usr/bin/env bash\ngit-town ship --message x\n", encoding="utf-8"
        )
        try:
            check_worker_surface(fake_skill)
            survived.append("worker surface exposing ship accepted")
        except Invalid:
            pass

        (fake_skill / "scripts" / "worker.sh").write_text(
            "#!/usr/bin/env bash\ngit push --force origin HEAD\n", encoding="utf-8"
        )
        try:
            check_worker_surface(fake_skill)
            survived.append("worker surface exposing force push accepted")
        except Invalid:
            pass

    if survived:
        for name in survived:
            print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
        return 2

    print(
        f"SELFTEST GREEN: repository profile valid; "
        f"{len(mutations) + 5} mutations refused"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--default-branch", default="main")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    if not (repo_root / ".git").exists() and not (repo_root / ".git-town.toml").exists():
        print(f"FATAL: {repo_root} is not a repository root", file=sys.stderr)
        return 64

    if args.selftest:
        return _selftest(repo_root, args.default_branch)

    try:
        validate(repo_root, args.default_branch)
    except Invalid as error:
        print(f"REPOSITORY PROFILE RED: {error}", file=sys.stderr)
        return 2

    print("REPOSITORY PROFILE GREEN: checked-in Git Town profile validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
