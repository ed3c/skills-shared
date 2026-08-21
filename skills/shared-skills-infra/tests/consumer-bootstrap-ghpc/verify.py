#!/usr/bin/env python3
"""Hermetic canary + planted-and-killed negative controls for the
github-portfolio-control consumer bootstrap (issue #559).

Everything below runs against a synthetic `shared` world and a throwaway
`consumer` git repo in a temp dir -- no network, no dependency on this real
checkout's history. `support.make_shared` builds the synthetic world's own
main/candidate commits so STALE_PIN can be planted and killed without racing
this repository's real history.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile

from support import (
    CODEX_ROLES, commit_all, files, make_consumer, make_shared, working_tree_hash,
)


def clone(source: Path, target: Path) -> Path:
    shutil.copytree(source, target, symlinks=True)
    return target


def red(module, consumer: Path, profile_path: Path, label: str, apply: bool = False, shared: Path | None = None) -> None:
    try:
        module.bootstrap_consumer_ghpc(
            consumer=consumer, repository_id="example/portfolio-repo", profile_path=profile_path,
            apply=apply, shared_root=shared,
        )
    except module.BootstrapError:
        return
    raise AssertionError(f"mutation survived: {label}")


def main() -> None:
    positives = 0
    mutations = 0
    with tempfile.TemporaryDirectory(prefix="ghpc-bootstrap-") as tmp:
        world = Path(tmp)
        shared = world / "shared"
        consumer = world / "consumer"
        module, profile_path, selected_profile = make_shared(shared)
        make_consumer(consumer)

        repository_id = "example/portfolio-repo"

        # -- positive 1: apply against a fresh consumer succeeds and preserves
        #    pre-existing unmanaged prose.
        module.bootstrap_consumer_ghpc(
            consumer=consumer, repository_id=repository_id, profile_path=profile_path,
            apply=True, shared_root=shared,
        )
        positives += 1
        assert (consumer / "README.md").read_text().startswith("# Existing consumer prose\n\nKeep this paragraph.\n")
        positives += 1

        # -- positive 2: every declared output exists.
        for relative in module.generated_paths():
            assert (consumer / relative).is_file(), f"missing declared output: {relative}"
        positives += 1

        # -- positive 3: egress deny-by-default is declared in the requirements output.
        requirements = json.loads((consumer / module.GHPC_REQUIREMENTS_REL).read_text())
        assert requirements["egress"] == {"policy": "DENY_BY_DEFAULT", "allowed_hosts": []}
        positives += 1

        # -- positive 4: the hosted-evidence field in the receipt is literally NOT_EXERCISED.
        receipt = json.loads((consumer / module.GHPC_RECEIPT_REL).read_text())
        assert receipt["evidence"]["hosted_evidence"] == "NOT_EXERCISED"
        positives += 1

        # -- positive 5: no canonical Skill/AGENTS/README body byte-marker appears
        #    anywhere in the generated consumer tree. Codex agent templates are the
        #    one artifact family allowed to carry pinned upstream bytes verbatim,
        #    and none of them contain a CANONICAL_BODY_MARKER.
        all_generated_text = "\n".join(
            (consumer / relative).read_text(encoding="utf-8") for relative in module.generated_paths()
        )
        assert "CANONICAL_BODY_MARKER" not in all_generated_text
        positives += 1

        # -- positive 6: the seven Codex agent bindings are thin -- generated,
        #    pinned to the candidate blob, and their model/effort remain
        #    unresolved ALIAS_ONLY placeholders (never a faked exercised identity).
        for role in CODEX_ROLES:
            text = (consumer / module.codex_agent_rel(role)).read_text()
            assert text.startswith(module.CODEX_MARKER)
            assert "${MODEL_ID}" in text and "${REASONING_EFFORT}" in text
            assert f"ROLE: {role} (fixture)." in text
        positives += 1

        # -- positive 7: `--check` on an unmodified tree is green, and re-applying
        #    is a byte-identical no-op (idempotent).
        module.bootstrap_consumer_ghpc(
            consumer=consumer, repository_id=repository_id, profile_path=profile_path,
            apply=False, shared_root=shared,
        )
        positives += 1
        before = files(consumer)
        module.bootstrap_consumer_ghpc(
            consumer=consumer, repository_id=repository_id, profile_path=profile_path,
            apply=True, shared_root=shared,
        )
        assert files(consumer) == before
        positives += 1

        # === negative controls: planted AND killed ================================

        # NC1 STALE_PIN (variant a): pinned main_commit is not an ancestor of the
        # running skills-shared checkout.
        c = world / "nc-stale-pin-non-ancestor"
        clone(consumer, c)
        bogus_main = clone(shared, world / "bogus-main-source")
        (bogus_main / "unrelated.txt").write_text("unrelated history\n")
        unrelated_commit = commit_all(bogus_main, "unrelated commit, not an ancestor of shared's HEAD")
        bad_profile = json.loads(profile_path.read_text())
        bad_profile["subject_pin"]["main_commit"] = unrelated_commit
        bad_path = world / "bad-main-pin.json"
        bad_path.write_text(json.dumps(bad_profile))
        red(module, c, bad_path, "STALE_PIN-non-ancestor-main", apply=True, shared=shared)
        mutations += 1

        # NC1 STALE_PIN (variant b): pinned candidate_commit is absent from the
        # object database entirely.
        c = world / "nc-stale-pin-absent-candidate"
        clone(consumer, c)
        bad_profile = json.loads(profile_path.read_text())
        bad_profile["subject_pin"]["candidate_commit"] = "f" * 40
        bad_path = world / "bad-candidate-pin.json"
        bad_path.write_text(json.dumps(bad_profile))
        red(module, c, bad_path, "STALE_PIN-absent-candidate", apply=True, shared=shared)
        mutations += 1

        # NC2 BOOTSTRAP_COPIES_CANONICAL_SKILL_BODY: a generated file is corrupted
        # post-apply to carry the entire canonical AGENTS.md body verbatim (a real
        # copy-paste, not just a fragment); --check must refuse.
        c = world / "nc-copied-body"
        clone(consumer, c)
        canonical_body = (shared / "skills/github-portfolio-control/AGENTS.md").read_text()
        target = c / module.GHPC_DOC_ROUTES[2]  # docs/traceability/github-portfolio-control.md
        target.write_text(target.read_text() + "\n" + canonical_body)
        red(module, c, profile_path, "BOOTSTRAP_COPIES_CANONICAL_SKILL_BODY", apply=False, shared=shared)
        mutations += 1

        # NC3 AUTHORITY_WIDENING: the profile tries to grant automatic merge authority.
        c = world / "nc-authority-widening"
        clone(consumer, c)
        widened = json.loads(profile_path.read_text())
        widened["authority"]["automatic_merge"] = True
        widened_path = world / "widened-authority.json"
        widened_path.write_text(json.dumps(widened))
        red(module, c, widened_path, "AUTHORITY_WIDENING", apply=True, shared=shared)
        mutations += 1

        # NC4 ROLLBACK_NOT_ATOMIC: a downstream write step fails partway through
        # apply; the consumer must be restored byte-identically (tree hash equal).
        c = world / "nc-rollback-atomic"
        clone(consumer, c)
        before_hash = working_tree_hash(c)
        original_write_full = module.write_full
        calls = {"n": 0}

        def flaky_write_full(consumer_root, relative, text):
            calls["n"] += 1
            if calls["n"] == 3:
                original_write_full(consumer_root, relative, text)
                raise module.BootstrapError("planted downstream failure after partial writes")
            original_write_full(consumer_root, relative, text)

        module.write_full = flaky_write_full
        try:
            red(module, c, profile_path, "ROLLBACK_NOT_ATOMIC", apply=True, shared=shared)
        finally:
            module.write_full = original_write_full
        after_hash = working_tree_hash(c)
        assert after_hash == before_hash, (
            f"rollback was not atomic: tree {before_hash} -> {after_hash}"
        )
        mutations += 1

        assert calls["n"] >= 3, "the planted failure never actually fired mid-pipeline"

    assert positives == 9, positives
    assert mutations == 5, mutations
    print(
        f"GHPC-BOOTSTRAP-TESTS-GREEN positive={positives} mutations={mutations} "
        "stale_pin=RED->REFUSED copied_body=RED->REFUSED authority_widening=RED->REFUSED "
        "rollback_atomic=RED->RESTORED"
    )


if __name__ == "__main__":
    main()
