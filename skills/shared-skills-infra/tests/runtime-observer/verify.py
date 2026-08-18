#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile

from support import (
    clone,
    commit_all,
    make_world,
    mutate_shared_requirements,
    refresh_consumer,
    resign_bootstrap,
    run,
    run_observer,
)


def expect_red(result, label: str, needle: str | None = None) -> None:
    if result.returncode == 0:
        raise AssertionError(f"mutation survived: {label}")
    output = result.stdout + result.stderr
    if needle and needle not in output:
        raise AssertionError(
            f"mutation {label} failed for the wrong reason; expected {needle!r}\n{output}"
        )


def main() -> None:
    positives = 0
    mutations = 0
    with tempfile.TemporaryDirectory(prefix="runtime-observer-") as tmp:
        world = Path(tmp)
        module, selected, shared, consumer = make_world(world)
        receipt_path = world / "runtime-receipt.json"

        before = run("git", "status", "--porcelain", "--untracked-files=all", cwd=consumer).stdout
        first = run_observer(shared, consumer, receipt_path)
        assert "TASK_EXECUTION_ADMITTED" in first.stdout
        after = run("git", "status", "--porcelain", "--untracked-files=all", cwd=consumer).stdout
        assert before == after == ""
        positives += 1

        receipt = json.loads(receipt_path.read_text())
        assert receipt["runtime_identity"] == "GITHUB_ACTIONS"
        assert receipt["selected_skills"][0]["name"] == "shared-skills-infra"
        assert len(receipt["selected_skills"]) == 1
        assert len(receipt["rejected_candidates"]) == 5
        assert all(
            row["state"] == "PASS"
            for row in receipt["environment"]["capability_probes"]
        )
        assert receipt["bootstrap_states"][-1] == "TASK_EXECUTION_ADMITTED"
        positives += 1

        original = receipt_path.read_bytes()
        run_observer(shared, consumer, receipt_path)
        assert receipt_path.read_bytes() == original
        positives += 1

        checker = shared / "skills/shared-skills-infra/scripts/check_skill_bootstrap.py"
        checked = run(
            __import__("sys").executable,
            str(checker),
            str(receipt_path),
            "--schema-root",
            str(shared / "skills/shared-skills-infra/references"),
            cwd=consumer,
        )
        assert "SKILL-BOOTSTRAP-GREEN" in checked.stdout
        positives += 1

        counter = 0

        def pair() -> tuple[Path, Path, Path]:
            nonlocal counter
            counter += 1
            s = clone(shared, world / f"shared-{counter}")
            c = clone(consumer, world / f"consumer-{counter}")
            return s, c, world / f"receipt-{counter}.json"

        s, c, out = pair()
        expect_red(
            run_observer(s, c, out, expected_sha="0" * 40, check=False),
            "wrong-consumer-head",
            "consumer head moved",
        )
        mutations += 1

        s, c, out = pair()
        p = c / ".agents/control-plane/source.json"
        value = json.loads(p.read_text())
        value["source"]["commit"] = "0" * 40
        p.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        expect_red(run_observer(s, c, out, check=False), "source-commit", "source pin")
        mutations += 1

        s, c, out = pair()
        p = c / ".agents/control-plane/source.json"
        value = json.loads(p.read_text())
        value["source"]["tree"] = "1" * 40
        p.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        expect_red(run_observer(s, c, out, check=False), "source-tree", "source pin")
        mutations += 1

        # probe.binding-readback exercised through the aggregate probe path, not
        # through validate_binding()/validate_bootstrap_receipt()'s own cascading
        # raises: regenerate a fully self-consistent (correctly signed) document
        # set against a shared root that has since moved (a trivial extra commit,
        # same pinned file content), then observe it against the *original*
        # shared root. Every internal cross-document check still agrees with
        # itself, so only the live readback against the real shared root can
        # catch the drift -- this is what makes the FAIL branch reachable.
        s, c, out = pair()
        stale_shared = clone(s, world / "stale-shared")
        stale_consumer = clone(c, world / "stale-consumer")
        (stale_shared / "NOOP.md").write_text("noop\n")
        commit_all(stale_shared, "noop bump")
        expected = refresh_consumer(module, selected, stale_shared, stale_consumer)
        expect_red(
            run_observer(s, stale_consumer, out, expected_sha=expected, check=False),
            "stale-shared-root-readback",
            "probe.binding-readback",
        )
        mutations += 1

        s, c, out = pair()
        p = c / ".agents/bindings/repository-control-plane.json"
        value = json.loads(p.read_text())
        value["content_sha256"] = "0" * 64
        p.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        expect_red(run_observer(s, c, out, check=False), "binding-digest", "aggregate digest")
        mutations += 1

        s, c, out = pair()
        p = c / ".agents/bindings/repository-control-plane.json"
        value = json.loads(p.read_text())
        value["skills"] = [
            row for row in value["skills"] if row["name"] != "shared-skills-infra"
        ]
        unsigned = dict(value)
        unsigned.pop("content_sha256")
        value["content_sha256"] = module.sha256(module.canonical(unsigned))
        p.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        expect_red(run_observer(s, c, out, check=False), "selected-skill-absent")
        mutations += 1

        s, c, out = pair()
        copied = c / ".agents/skills/shared-skills-infra"
        copied.mkdir(parents=True)
        (copied / "SKILL.md").write_text("copied body\n")
        expect_red(run_observer(s, c, out, check=False), "shadow-copy", "shadows canonical")
        mutations += 1

        s, c, out = pair()
        p = c / ".agents/control-plane/bootstrap-receipt.json"
        value = json.loads(p.read_text())
        value["evidence"]["agent_runtime_execution"] = "PASS"
        resign_bootstrap(module, value)
        p.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        expect_red(run_observer(s, c, out, check=False), "runtime-laundering", "promoted")
        mutations += 1

        s, c, out = pair()
        p = c / ".agents/control-plane/bootstrap-receipt.json"
        value = json.loads(p.read_text())
        value["private_reasoning"] = "hidden"
        resign_bootstrap(module, value)
        p.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        expect_red(run_observer(s, c, out, check=False), "private-reasoning")
        mutations += 1

        s, c, out = pair()
        expected = mutate_shared_requirements(module, selected, s, c, remove=True)
        expect_red(
            run_observer(s, c, out, expected_sha=expected, check=False),
            "requirements-absent",
            "runtime requirements are absent",
        )
        mutations += 1

        s, c, out = pair()
        expected = mutate_shared_requirements(
            module,
            selected,
            s,
            c,
            lambda v: v.__setitem__(
                "supported_runtime_identities", ["CODEX_CLI_LOCAL"]
            ),
        )
        expect_red(
            run_observer(s, c, out, expected_sha=expected, check=False),
            "unsupported-runtime",
            "exact GitHub Actions",
        )
        mutations += 1

        s, c, out = pair()
        def network(v):
            v["network_policy"] = {"mode": "ALLOWLIST", "allowed_hosts": ["example.com"]}
        expected = mutate_shared_requirements(module, selected, s, c, network)
        expect_red(
            run_observer(s, c, out, expected_sha=expected, check=False),
            "network-widening",
            "cannot admit network access",
        )
        mutations += 1

        s, c, out = pair()
        def writable(v):
            v["filesystem"] = {
                "needs_writable_worktree": True,
                "writable_subpaths": [".agents/control-plane"],
            }
            v["isolation"] = {
                "requires_isolated_worktree": True,
                "sandbox": "BOUNDED_WRITE",
            }
        expected = mutate_shared_requirements(module, selected, s, c, writable)
        expect_red(
            run_observer(s, c, out, expected_sha=expected, check=False),
            "write-widening",
            "cannot admit repository writes",
        )
        mutations += 1

        s, c, out = pair()
        expected = mutate_shared_requirements(
            module,
            selected,
            s,
            c,
            lambda v: v.__setitem__("secret_variable_names", ["PROVIDER_TOKEN"]),
        )
        expect_red(
            run_observer(s, c, out, expected_sha=expected, check=False),
            "secret-requirement",
            "cannot require secrets",
        )
        mutations += 1

        s, c, out = pair()
        expected = mutate_shared_requirements(
            module,
            selected,
            s,
            c,
            lambda v: v.__setitem__("setup_entrypoints", ["runtime.setup"]),
        )
        expect_red(
            run_observer(s, c, out, expected_sha=expected, check=False),
            "setup-entrypoint",
            "cannot execute setup entrypoints",
        )
        mutations += 1

        s, c, out = pair()
        expected = mutate_shared_requirements(
            module,
            selected,
            s,
            c,
            lambda v: v["probe_entrypoints"].append("probe.unknown"),
        )
        expect_red(
            run_observer(s, c, out, expected_sha=expected, check=False),
            "unknown-probe",
            "unregistered probe",
        )
        mutations += 1

        s, c, out = pair()
        expected = mutate_shared_requirements(
            module,
            selected,
            s,
            c,
            lambda v: v["probe_entrypoints"].append("rm -rf /"),
        )
        expect_red(
            run_observer(s, c, out, expected_sha=expected, check=False),
            "shell-shaped-probe",
            "schema-invalid",
        )
        mutations += 1

        s, c, out = pair()
        expect_red(
            run_observer(
                s,
                c,
                c / ".agents/control-plane/runtime-receipt.json",
                check=False,
            ),
            "repository-output",
            "outside both repositories",
        )
        mutations += 1

        mutated = copy.deepcopy(receipt)
        mutated["selected_skills"][0]["access_mode"] = "LOCAL_CANONICAL_USER_SURFACE"
        local_surface = world / "local-surface.json"
        local_surface.write_text(json.dumps(mutated, indent=2, sort_keys=True) + "\n")
        result = run(
            __import__("sys").executable,
            str(checker),
            str(local_surface),
            "--schema-root",
            str(shared / "skills/shared-skills-infra/references"),
            cwd=consumer,
            check=False,
        )
        expect_red(result, "gha-as-local-surface", "access-mode-not-observable")
        mutations += 1

    assert positives == 4
    assert mutations == 19
    print(
        f"CONSUMER-RUNTIME-TESTS-GREEN positive={positives} "
        f"mutations={mutations} selected=1 rejected=5 shadow=PASS"
    )


if __name__ == "__main__":
    main()
