#!/usr/bin/env python3
"""Hermetic canary + planted-and-killed negative controls for the
dual-track-code-review-loop consumer bootstrap (issue #527, as repaired).

Everything below runs against a synthetic `shared` world and two throwaway
consumer git repos in a temp dir -- one EMPTY, one BROWNFIELD already governed
by the default profile. No network, no dependency on this real checkout's
history, no provider.

Every mutation below is planted AND killed: the run is proven to fail for its
own named reason (a `BootstrapError`, or a distinct non-zero CLI exit code for
the three collision cases), never merely "not green".
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from support import (
    DOMAIN_BEGIN, DOMAIN_END, DROPPED_SURFACES, FOREIGN_WORKFLOW, PROMPT_CATALOGUE,
    files, foreign_snapshot, make_consumer_brownfield, make_consumer_empty,
    make_shared, working_tree_hash,
)

EMPTY_ID = "example/empty-repo"
BROWNFIELD_ID = "example/brownfield-repo"


def clone(source: Path, target: Path) -> Path:
    shutil.copytree(source, target, symlinks=True)
    return target


def red(module, consumer: Path, profile_path: Path, label: str, expect: str, *, shared: Path,
        repository_id: str = BROWNFIELD_ID, apply: bool = False) -> None:
    """Plant a mutation and prove it dies for its OWN named reason -- a refusal
    that fires for some other reason is not evidence for this control."""
    try:
        module.bootstrap_consumer_dtcr(
            consumer=consumer, repository_id=repository_id, profile_path=profile_path,
            apply=apply, shared_root=shared,
        )
    except module.BootstrapError as exc:
        assert expect in str(exc), f"{label} died for the wrong reason: {exc}"
        return
    raise AssertionError(f"mutation survived: {label}")


def cli(shared: Path, consumer: Path, repository_id: str, *, apply: bool,
        profile_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    script = shared / "skills/shared-skills-infra/scripts/consumer_bootstrap_dtcr.py"
    args = [
        sys.executable, str(script), "--consumer", str(consumer),
        "--repository-id", repository_id, "--shared-root", str(shared),
        "--apply" if apply else "--check",
    ]
    if profile_path is not None:
        args += ["--profile", str(profile_path)]
    return subprocess.run(args, text=True, capture_output=True, check=False)


def variant(profile_path: Path, world: Path, name: str, mutate) -> Path:
    doc = json.loads(profile_path.read_text())
    mutate(doc)
    target = world / f"profile-{name}.json"
    target.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    return target


def main() -> None:
    positives = 0
    mutations = 0
    with tempfile.TemporaryDirectory(prefix="dtcr-bootstrap-") as tmp:
        world = Path(tmp)
        shared = world / "shared"
        empty = world / "consumer-empty"
        brownfield = world / "consumer-brownfield"
        module, profile_path, _selected = make_shared(shared)
        make_consumer_empty(empty)
        make_consumer_brownfield(brownfield)

        catalogue_blob = subprocess.run(
            ["git", "-C", str(shared), "rev-parse", f"HEAD:{PROMPT_CATALOGUE}"],
            text=True, capture_output=True, check=True,
        ).stdout.strip()

        # === positives: empty fixture ==========================================

        # -- P1: apply against a repository with nothing but an initial commit.
        assert not (empty / "AGENTS.md").exists()
        module.bootstrap_consumer_dtcr(
            consumer=empty, repository_id=EMPTY_ID, profile_path=profile_path,
            apply=True, shared_root=shared,
        )
        positives += 1

        # -- P2: exactly the declared surface exists, and none of the four
        #    surfaces the #527 repair dropped was created.
        for relative in module.generated_paths():
            assert (empty / relative).is_file(), f"missing declared output: {relative}"
        for dropped in DROPPED_SURFACES:
            assert not (empty / dropped).exists(), f"dropped surface was generated: {dropped}"
        positives += 1

        # -- P3: the managed block ROUTES to the canonical prompt catalogue by
        #    exact commit and blob, and carries no prompt body.
        block = module.observed_block(empty / "AGENTS.md", module.DTCR_BEGIN, module.DTCR_END)
        assert PROMPT_CATALOGUE in block and catalogue_blob in block
        assert "CANONICAL_BODY_MARKER" not in block
        assert (empty / "AGENTS.md").read_text().count(module.DTCR_BEGIN) == 1
        positives += 1

        # -- P4: the receipt carries every absence lane as an absence, never PASS.
        receipt = json.loads((empty / module.DTCR_RECEIPT_REL).read_text())
        assert receipt["evidence"]["runtime"] == "NOT_EXERCISED"
        assert receipt["evidence"]["registry_admission"] == "ABSENT"
        assert receipt["evidence"]["hosted_workflow"] == "NOT_EXERCISED"
        assert receipt["evidence"]["real_consumer"] == "NOT_SELECTED"
        assert receipt["evidence"]["consumer_canary"] == "NOT_EXERCISED"
        assert receipt["evidence"]["composition_target_430"] == "ABSENT"
        assert receipt["evidence"]["language_build_provider_capability"] == "NOT_IMPLEMENTED"
        assert receipt["evidence"]["completion_dependency_525"] == "OPEN"
        assert receipt["evidence"]["merge"] == "HUMAN_ADMIT_REQUIRED"
        assert receipt["evidence"]["terminal"] == "NOT_EMITTED"
        assert receipt["declared_boundaries"] == module.DECLARED_BOUNDARIES
        assert all(value is False for value in receipt["authority"].values())
        requirements = json.loads((empty / module.DTCR_REQUIREMENTS_REL).read_text())
        assert requirements["egress"] == {"policy": "DENY_BY_DEFAULT", "allowed_hosts": []}
        positives += 1

        # -- P5: `--check` is green and re-applying is a byte-identical no-op.
        module.bootstrap_consumer_dtcr(
            consumer=empty, repository_id=EMPTY_ID, profile_path=profile_path,
            apply=False, shared_root=shared,
        )
        before = files(empty)
        module.bootstrap_consumer_dtcr(
            consumer=empty, repository_id=EMPTY_ID, profile_path=profile_path,
            apply=True, shared_root=shared,
        )
        assert files(empty) == before
        positives += 1

        # -- P6: no canonical Skill/AGENTS/README/prompt body byte-marker leaked
        #    anywhere into the generated consumer tree.
        generated_text = "\n".join(
            (empty / relative).read_text(encoding="utf-8") for relative in module.generated_paths()
        )
        assert "CANONICAL_BODY_MARKER" not in generated_text
        positives += 1

        # === positives: brownfield fixture =====================================

        foreign_before = foreign_snapshot(brownfield)
        readme_before = (brownfield / "README.md").read_bytes()
        agents_foreign_before = module.observed_block(
            brownfield / "AGENTS.md", DOMAIN_BEGIN, DOMAIN_END
        )
        agents_prose_before = (brownfield / "AGENTS.md").read_text().split(DOMAIN_BEGIN)[0]

        module.bootstrap_consumer_dtcr(
            consumer=brownfield, repository_id=BROWNFIELD_ID, profile_path=profile_path,
            apply=True, shared_root=shared,
        )
        positives += 1

        # -- P7: every foreign generated authority and the foreign workflow are
        #    byte-identical; the foreign managed block and the unmanaged prose
        #    around it survive byte-for-byte; README.md was never touched.
        assert foreign_snapshot(brownfield) == foreign_before, "a foreign authority changed"
        assert (brownfield / "README.md").read_bytes() == readme_before
        assert module.observed_block(brownfield / "AGENTS.md", DOMAIN_BEGIN, DOMAIN_END) == agents_foreign_before
        assert (brownfield / "AGENTS.md").read_text().startswith(agents_prose_before)
        for dropped in DROPPED_SURFACES:
            assert not (brownfield / dropped).exists(), f"dropped surface was generated: {dropped}"
        positives += 1

        # -- P8: both managed pairs coexist, and `--check` re-derives every
        #    generated document byte-for-byte through the CLI (exit 0).
        agents_text = (brownfield / "AGENTS.md").read_text()
        assert agents_text.count(DOMAIN_BEGIN) == 1 and agents_text.count(module.DTCR_BEGIN) == 1
        result = cli(shared, brownfield, BROWNFIELD_ID, apply=False)
        assert result.returncode == 0, result.stderr
        assert "DTCR-BOOTSTRAP-GREEN" in result.stdout
        positives += 1

        # === negative controls: planted AND killed ==============================

        # NC1 MUTABLE_REF: a mutable ref instead of an exact commit.
        c = clone(brownfield, world / "nc-mutable-ref")
        bad = variant(profile_path, world, "mutable-ref",
                      lambda d: d["subject_pin"].__setitem__("main_commit", "main"))
        red(module, c, bad, "MUTABLE_REF-main", "is not an exact commit/tree SHA", shared=shared, apply=True)
        bad = variant(profile_path, world, "mutable-latest",
                      lambda d: d["subject_pin"].__setitem__("candidate_commit", "latest"))
        red(module, c, bad, "MUTABLE_REF-latest", "is not an exact commit/tree SHA", shared=shared, apply=True)
        mutations += 1

        # NC2 STALE_PIN: the pinned owned_tree does not match the pinned commit.
        c = clone(brownfield, world / "nc-stale-pin")
        bad = variant(profile_path, world, "stale-tree",
                      lambda d: d["subject_pin"].__setitem__("owned_tree", "0" * 40))
        red(module, c, bad, "STALE_PIN-owned-tree", "pinned owned_tree does not match", shared=shared, apply=True)
        mutations += 1

        # NC3 UNMERGED_CANDIDATE: this profile declares no candidate source, so a
        # candidate_commit that differs from main_commit is refused.
        c = clone(brownfield, world / "nc-candidate-drift")
        bad = variant(
            profile_path, world, "candidate-drift",
            lambda d: d["subject_pin"].__setitem__("candidate_commit", "c" * 40),
        )
        red(module, c, bad, "UNMERGED_CANDIDATE", "candidate_commit must equal main_commit", shared=shared, apply=True)
        mutations += 1

        # NC4 CAPABILITY_CLAIM_WITHOUT_EVIDENCE (two fields, one case each).
        c = clone(brownfield, world / "nc-capability")
        bad = variant(
            profile_path, world, "git-town-implemented",
            lambda d: d["runtime_capabilities"]["git_town"].__setitem__("installer_state", "IMPLEMENTED"),
        )
        red(module, c, bad, "CAPABILITY_git_town_IMPLEMENTED", "installer_state=IMPLEMENTED has no evidence path", shared=shared, apply=True)
        mutations += 1
        bad = variant(
            profile_path, world, "forgejo-pass",
            lambda d: d["runtime_capabilities"]["forgejo"].__setitem__("service_state", "PASS"),
        )
        red(module, c, bad, "CAPABILITY_forgejo_PASS", "service_state=PASS has no evidence path", shared=shared, apply=True)
        mutations += 1

        # NC5 AUTHORITY_WIDENING: the profile tries to grant automatic merge.
        c = clone(brownfield, world / "nc-authority")
        bad = variant(profile_path, world, "authority",
                      lambda d: d["authority"].__setitem__("automatic_merge", True))
        red(module, c, bad, "AUTHORITY_WIDENING", "widened automatic authority", shared=shared, apply=True)
        mutations += 1

        # NC6 PRIVATE_VALUE_IN_TRACKED_BINDING: a machine-local absolute path.
        c = clone(brownfield, world / "nc-private-value")
        bad = variant(
            profile_path, world, "private-value",
            lambda d: d["subject_pin"].__setitem__(
                "candidate_repin_policy", "sourced from /Users/someone/private/checkout"
            ),
        )
        red(module, c, bad, "PRIVATE_VALUE_IN_TRACKED_BINDING", "machine-local absolute path", shared=shared, apply=True)
        mutations += 1

        # NC7 DUPLICATE_TASK_STATE_OWNER: a binding at this profile's path whose
        # `binding` field names a different owner.
        c = clone(brownfield, world / "nc-duplicate-owner")
        squatter = c / module.DTCR_BINDING_REL
        squatter.parent.mkdir(parents=True, exist_ok=True)
        squatter.write_text(json.dumps(
            {"schema": module.BINDING_SCHEMA, "binding": "some-other-program"}, indent=2) + "\n")
        red(module, c, profile_path, "DUPLICATE_TASK_STATE_OWNER", "duplicate task-state owner", shared=shared, apply=True)
        mutations += 1

        # NC8 FOREIGN_AUTHORITY_CLAIM: the generated set is mutated to claim an
        # authority owned by the default profile.
        c = clone(brownfield, world / "nc-foreign-claim")
        original_rel = module.DTCR_BINDING_REL
        module.DTCR_BINDING_REL = Path(".agents/bindings/repository-control-plane.json")
        try:
            red(module, c, profile_path, "FOREIGN_AUTHORITY_CLAIM", "claims a foreign profile's authority", shared=shared, apply=True)
        finally:
            module.DTCR_BINDING_REL = original_rel
        assert foreign_snapshot(c) == foreign_before, "the refused run still touched a foreign authority"
        mutations += 1

        # NC9 COLLISION_MARKER_PAIR (exit 65): an existing marker pair contained
        # by this profile's pair.
        c = clone(brownfield, world / "nc-collision-marker")
        agents = c / "AGENTS.md"
        agents.write_text(
            agents.read_text().replace(module.DTCR_BEGIN, "<!-- BEGIN DUAL TRACK CODE REVIEW -->")
            .replace(module.DTCR_END, "<!-- END DUAL TRACK CODE REVIEW -->")
        )
        result = cli(shared, c, BROWNFIELD_ID, apply=True)
        assert result.returncode == module.EXIT_COLLISION_MARKER, (result.returncode, result.stderr)
        assert "DTCR-BOOTSTRAP-COLLISION" in result.stderr
        mutations += 1

        # NC10 COLLISION_UNRECOGNIZED_AUTHORITY (exit 66): a target authority path
        # already present carrying an unrecognized `schema`.
        c = clone(brownfield, world / "nc-collision-authority")
        target = c / module.DTCR_PROFILE_REL
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"schema": "someone-elses/thing/v1"}, indent=2) + "\n")
        result = cli(shared, c, BROWNFIELD_ID, apply=True)
        assert result.returncode == module.EXIT_COLLISION_AUTHORITY, (result.returncode, result.stderr)
        mutations += 1

        # NC11 COLLISION_WORKFLOW (exit 67): a workflow claiming this profile's
        # generated marker, which this profile never generates.
        c = clone(brownfield, world / "nc-collision-workflow")
        forged = c / ".github/workflows/dual-track-code-review-bootstrap.yml"
        forged.write_text(f"{module.DTCR_WORKFLOW_MARKER}\nname: forged\non: push\njobs: {{}}\n")
        result = cli(shared, c, BROWNFIELD_ID, apply=True)
        assert result.returncode == module.EXIT_COLLISION_WORKFLOW, (result.returncode, result.stderr)
        assert (c / FOREIGN_WORKFLOW).read_bytes() == foreign_before[FOREIGN_WORKFLOW]
        mutations += 1

        # NC12 BOOTSTRAP_COPIES_CANONICAL_PROMPT_BODY: the whole canonical prompt
        # catalogue is pasted into a generated route; `--check` must refuse.
        c = clone(brownfield, world / "nc-copied-body")
        catalogue_body = (shared / PROMPT_CATALOGUE).read_text()
        target = c / "AGENTS.md"
        target.write_text(target.read_text() + "\n" + catalogue_body)
        red(module, c, profile_path, "BOOTSTRAP_COPIES_CANONICAL_PROMPT_BODY", "embeds canonical body bytes copied from", shared=shared, apply=False)
        mutations += 1

        # NC13 READBACK_DRIFT: one byte of a generated authority is edited after
        # apply; `--check` must refuse rather than re-derive silently.
        c = clone(brownfield, world / "nc-readback-drift")
        binding_path = c / module.DTCR_BINDING_REL
        binding_path.write_text(binding_path.read_text().replace('"repo_owned": []', '"repo_owned": ["x"]'))
        red(module, c, profile_path, "READBACK_DRIFT", "generated artifact drifted", shared=shared, apply=False)
        mutations += 1

        # NC14a RECEIPT_TAMPERED: any edited byte breaks the receipt's self digest.
        c = clone(brownfield, world / "nc-receipt-tampered")
        receipt_path = c / module.DTCR_RECEIPT_REL
        receipt_path.write_text(
            receipt_path.read_text().replace('"runtime": "NOT_EXERCISED"', '"runtime": "PASS"')
        )
        red(module, c, profile_path, "RECEIPT_TAMPERED", "self digest is stale", shared=shared, apply=False)
        mutations += 1

        # NC14b RECEIPT_PROMOTED_UNEXERCISED_LANE: the adversarial version -- the
        # forger promotes the runtime lane to PASS AND re-signs the receipt, so
        # the digest check passes and only the lane-vocabulary guard can catch it.
        c = clone(brownfield, world / "nc-receipt-promoted")
        receipt_path = c / module.DTCR_RECEIPT_REL
        forged = json.loads(receipt_path.read_text())
        forged["evidence"]["runtime"] = "PASS"
        unsigned = dict(forged)
        unsigned.pop("receipt_sha256")
        forged["receipt_sha256"] = module.sha256(module.canonical(unsigned))
        receipt_path.write_text(module.json_text(forged))
        red(module, c, profile_path, "RECEIPT_PROMOTED_UNEXERCISED_LANE",
            "promoted an unexercised or Human-owned lane", shared=shared, apply=False)
        mutations += 1

        # NC15 ROLLBACK_NOT_ATOMIC: a downstream write fails partway through apply
        # on a not-yet-bootstrapped brownfield repo; every pre-bootstrap byte must
        # come back, and the generated directories must be gone again.
        c = world / "nc-rollback-atomic"
        make_consumer_brownfield(c)
        before_hash = working_tree_hash(c)
        original_write_full = module.write_full
        calls = {"n": 0}

        def flaky_write_full(consumer_root, relative, text):
            calls["n"] += 1
            original_write_full(consumer_root, relative, text)
            if calls["n"] == 2:
                raise module.BootstrapError("planted downstream failure after partial writes")

        module.write_full = flaky_write_full
        try:
            red(module, c, profile_path, "ROLLBACK_NOT_ATOMIC", "planted downstream failure", shared=shared, apply=True)
        finally:
            module.write_full = original_write_full
        assert calls["n"] >= 2, "the planted failure never actually fired mid-pipeline"
        after_hash = working_tree_hash(c)
        assert after_hash == before_hash, f"rollback was not atomic: {before_hash} -> {after_hash}"
        assert not (c / ".agents/control-plane/profiles").exists()
        assert not (c / module.DTCR_BINDING_REL).exists()
        mutations += 1

        assert positives == 9, positives
        assert mutations == 17, mutations

        terminal = {
            "terminal": "DTCR_GENERIC_CONSUMER_BOOTSTRAP_READY",
            "positives": positives,
            "mutations": mutations,
            "fixtures": ["empty", "brownfield"],
            "runtime": "NOT_EXERCISED",
            "registry_admission": "ABSENT",
            "hosted_workflow": "NOT_EXERCISED",
            "real_consumer": "NOT_SELECTED",
            "consumer_canary": "NOT_EXERCISED",
            "composition_target_430": "ABSENT",
            "completion_dependency_525": "OPEN",
            "merge": "HUMAN_ADMIT_REQUIRED",
        }
        digest = hashlib.sha256(
            json.dumps(terminal, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    print(
        f"DTCR-BOOTSTRAP-TESTS-GREEN positive={positives} mutations={mutations} "
        "mutable_ref=RED->REFUSED stale_pin=RED->REFUSED unmerged_candidate=RED->REFUSED "
        "capability_claim=RED->REFUSED authority_widening=RED->REFUSED private_value=RED->REFUSED "
        "duplicate_owner=RED->REFUSED foreign_authority_claim=RED->REFUSED "
        "collision_marker=RED->65 collision_authority=RED->66 collision_workflow=RED->67 "
        "copied_prompt_body=RED->REFUSED readback_drift=RED->REFUSED "
        "receipt_promotion=RED->REFUSED rollback_atomic=RED->RESTORED"
    )
    print(
        f"DTCR-BOOTSTRAP-TERMINAL DTCR_GENERIC_CONSUMER_BOOTSTRAP_READY sha256={digest} "
        "runtime=NOT_EXERCISED registry_admission=ABSENT hosted_workflow=NOT_EXERCISED "
        "real_consumer=NOT_SELECTED consumer_canary=NOT_EXERCISED composition_target_430=ABSENT "
        "completion_dependency_525=OPEN merge=HUMAN_ADMIT_REQUIRED"
    )


if __name__ == "__main__":
    main()
