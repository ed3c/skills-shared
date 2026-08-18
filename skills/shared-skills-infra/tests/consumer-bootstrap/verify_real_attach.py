#!/usr/bin/env python3
"""SSM-3: exercise default_attach for real, not the fake_attach every other
test in this suite injects.

Every scenario in verify.py bootstraps through `fake_attach`, which hand-
reconstructs the binding document `repository_control_plane.attach()` ->
`shared_skills.py sync` would produce. Nothing pinned that the real seam
agrees with what `consumer_bootstrap_receipt.validate_binding` and
`observe_consumer_runtime.validate_binding` expect -- the two production
digest algorithms were only "hand-verified byte-identical today". This runs
the real seam against a throwaway consumer worktree instead.

`shared_skills.py sync`'s source-identity step shells out to the actual
`skills-shared` checkout (not a fixture copy: `repository_control_plane.py`
and `shared_skills.py` derive their own root from `__file__`), so it needs
this worktree to carry a credential-free HTTP(S) `github`/`origin`/`forgejo`
remote and a clean tree -- the same precondition `shared_identity()` already
enforces. That is a real repository fact, not an assumption: verified below
before spending the rest of the exercise, and failing closed with a readable
diagnosis (not silently skipped) if it does not hold.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = SKILL_ROOT / "scripts"
SHARED_ROOT = SKILL_ROOT.parent.parent
PROFILE_SOURCE = SKILL_ROOT / "references/repository-control-plane-profile.default.json"
CREDENTIAL_FREE_REMOTES = {"github", "github-archive", "origin", "forgejo"}


def run(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(f"command failed {args}:\n{result.stdout}\n{result.stderr}")
    return result.stdout


def require_real_seam_precondition() -> None:
    """default_attach's sync path binds THIS checkout, not a fixture -- verify
    its two preconditions instead of assuming the note that motivated this
    test still holds."""
    status = run("git", "-C", str(SHARED_ROOT), "status", "--porcelain", "--untracked-files=all")
    if status.strip():
        raise AssertionError(
            "default_attach real-seam exercise requires a clean skills-shared "
            "worktree (shared_skills.py sync refuses a dirty source) -- "
            "commit or stash local changes before running this suite"
        )
    remotes = set(run("git", "-C", str(SHARED_ROOT), "remote").split())
    if not (remotes & CREDENTIAL_FREE_REMOTES):
        raise AssertionError(
            "default_attach real-seam exercise requires a credential-free "
            f"HTTP(S) remote named one of {sorted(CREDENTIAL_FREE_REMOTES)}"
        )


def load_real_consumer_bootstrap():
    """Load the real, uncopied consumer_bootstrap.py so its lazy
    `from repository_control_plane import attach` resolves the real
    repository_control_plane.py/shared_skills.py, not fixture stand-ins."""
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "real_consumer_bootstrap", SCRIPTS / "consumer_bootstrap.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    # consumer_bootstrap.py does not import `canonical` for its own use (it is
    # dead there); this exercise still needs it, so bind it from its actual
    # owner, the module consumer_bootstrap.py's own import already loaded.
    module.canonical = sys.modules["consumer_bootstrap_common"].canonical
    return module


def make_consumer(root: Path) -> None:
    root.mkdir(parents=True)
    run("git", "init", "-q", "-b", "main", str(root))
    run("git", "-C", str(root), "config", "user.email", "real-attach@example.invalid")
    run("git", "-C", str(root), "config", "user.name", "real-attach-selftest")
    (root / "README.md").write_text("# real default_attach consumer fixture\n")
    run("git", "-C", str(root), "add", "README.md")
    run("git", "-C", str(root), "commit", "-q", "-m", "initial consumer")


def main() -> None:
    require_real_seam_precondition()
    module = load_real_consumer_bootstrap()
    with tempfile.TemporaryDirectory(prefix="default-attach-real-") as tmp:
        consumer = Path(tmp) / "consumer"
        make_consumer(consumer)

        # attach_fn defaults to module.default_attach -- the real
        # repository_control_plane.attach() -> shared_skills.py sync seam.
        module.bootstrap_consumer(
            consumer=consumer,
            repository_id="example/real-attach-consumer",
            profile_path=PROFILE_SOURCE,
            apply=True,
        )

        binding = json.loads((consumer / module.BINDING_REL).read_text())
        assert binding["schema"] == "shared-skills/consumer-binding/v1"
        # This is the exact byte-agreement claim SSM-3 says was never pinned:
        # consumer_bootstrap_receipt.validate_binding already ran inside
        # bootstrap_consumer() above and did not raise, so re-derive its
        # verdict here for a readable failure if it ever does.
        unsigned = dict(binding)
        claimed = unsigned.pop("content_sha256")
        assert claimed == module.sha256(module.canonical(unsigned)), (
            "shared_skills.py's real binding digest disagrees with "
            "consumer_bootstrap_receipt's expected algorithm"
        )

        receipt = json.loads((consumer / module.RECEIPT_REL).read_text())
        assert receipt["schema"] == "shared-skills/consumer-bootstrap-receipt/v1"
        assert receipt["binding"]["content_sha256"] == binding["content_sha256"]

        # Re-run in --check mode: default_attach's own idempotent readback
        # (attach(check=True) -> shared_skills.py sync --check) must also
        # agree with what apply just wrote, with nothing to change.
        module.bootstrap_consumer(
            consumer=consumer,
            repository_id="example/real-attach-consumer",
            profile_path=PROFILE_SOURCE,
            apply=False,
        )

    print("CONSUMER-BOOTSTRAP-REAL-ATTACH-GREEN default_attach exercised end-to-end (apply+check)")


if __name__ == "__main__":
    main()
