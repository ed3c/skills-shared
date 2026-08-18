#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile

from jsonschema import Draft202012Validator

from support import commit_all, fake_attach, make_consumer, make_shared, profile


def files(root: Path) -> dict[str, bytes | str]:
    result: dict[str, bytes | str] = {}
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[relative] = "LINK:" + str(path.readlink())
        elif path.is_file():
            result[relative] = path.read_bytes()
    return result


def clone(source: Path, target: Path) -> Path:
    shutil.copytree(source, target, symlinks=True)
    return target


def red(module, consumer: Path, profile_path: Path, attach, label: str, apply: bool = False) -> None:
    try:
        module.bootstrap_consumer(
            consumer=consumer, repository_id="example/new-repo", profile_path=profile_path,
            apply=apply, attach_fn=attach, shared_root=profile_path.parents[3],
        )
    except module.BootstrapError:
        return
    raise AssertionError(f"mutation survived: {label}")


def resign(module, receipt: dict) -> None:
    receipt.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = module.sha256(module.canonical(receipt))


def main() -> None:
    mutations = 0
    positives = 0
    with tempfile.TemporaryDirectory(prefix="consumer-bootstrap-") as tmp:
        world = Path(tmp)
        shared = world / "shared"
        consumer = world / "consumer"
        module, profile_path = make_shared(shared)
        selected = profile()
        attach = fake_attach(module, shared, selected)
        make_consumer(consumer)

        module.bootstrap_consumer(
            consumer=consumer, repository_id="example/new-repo", profile_path=profile_path,
            apply=True, attach_fn=attach, shared_root=shared,
        )
        positives += 1
        assert (consumer / "README.md").read_text().startswith("# Existing consumer prose\n\nKeep this line.\n")
        receipt = json.loads((consumer / module.RECEIPT_REL).read_text())
        schema = json.loads((Path(__file__).resolve().parents[2] / "references/consumer-bootstrap-receipt.schema.json").read_text())
        Draft202012Validator(schema).validate(receipt)
        positives += 1

        module.bootstrap_consumer(
            consumer=consumer, repository_id="example/new-repo", profile_path=profile_path,
            apply=False, attach_fn=attach, shared_root=shared,
        )
        positives += 1
        before = files(consumer)
        module.bootstrap_consumer(
            consumer=consumer, repository_id="example/new-repo", profile_path=profile_path,
            apply=True, attach_fn=attach, shared_root=shared,
        )
        assert files(consumer) == before
        positives += 1

        readme = consumer / "README.md"
        readme.write_text("Consumer-owned preface changed.\n\n" + readme.read_text())
        module.bootstrap_consumer(
            consumer=consumer, repository_id="example/new-repo", profile_path=profile_path,
            apply=False, attach_fn=attach, shared_root=shared,
        )
        positives += 1
        commit_all(consumer, "admit bootstrap")
        module.bootstrap_consumer(
            consumer=consumer, repository_id="example/new-repo", profile_path=profile_path,
            apply=False, attach_fn=attach, shared_root=shared,
        )
        positives += 1

        base = consumer
        counter = 0

        def candidate() -> Path:
            nonlocal counter
            counter += 1
            return clone(base, world / f"mutation-{counter}")

        c = candidate(); (c / "docs/INDEX.md").unlink(); red(module, c, profile_path, attach, "missing-route"); mutations += 1
        c = candidate(); p = c / "AGENTS.md"; p.write_text(p.read_text().replace("machine authority", "mutable guess", 1)); red(module, c, profile_path, attach, "route-drift"); mutations += 1
        c = candidate(); p = c / module.WORKFLOW_REL; p.write_text(p.read_text() + "# drift\n"); red(module, c, profile_path, attach, "workflow-drift"); mutations += 1
        c = candidate(); p = c / module.SOURCE_REL; value = json.loads(p.read_text()); value["source"]["commit"] = "0" * 40; p.write_text(module.json_text(value)); red(module, c, profile_path, attach, "stale-source"); mutations += 1
        c = candidate(); p = c / module.BINDING_REL; value = json.loads(p.read_text()); value["source"]["tree"] = "1" * 40; p.write_text(module.json_text(value)); red(module, c, profile_path, attach, "stale-binding"); mutations += 1
        c = candidate(); copied = c / ".agents/skills/shared-skills-infra"; copied.mkdir(parents=True); (copied / "SKILL.md").write_text("copy\n"); red(module, c, profile_path, attach, "copied-body"); mutations += 1
        c = candidate(); p = c / module.BINDING_REL; p.unlink(); p.symlink_to(c / "README.md"); red(module, c, profile_path, attach, "symlink-authority"); mutations += 1
        c = candidate(); p = c / module.RECEIPT_REL; value = json.loads(p.read_text()); value["authority"]["automatic_merge"] = True; resign(module, value); p.write_text(module.json_text(value)); red(module, c, profile_path, attach, "auto-merge"); mutations += 1
        c = candidate(); p = c / module.RECEIPT_REL; value = json.loads(p.read_text()); value["evidence"]["agent_runtime_execution"] = "PASS"; resign(module, value); p.write_text(module.json_text(value)); red(module, c, profile_path, attach, "runtime-promotion"); mutations += 1
        c = candidate(); p = c / module.RECEIPT_REL; value = json.loads(p.read_text()); value.pop("rollback"); resign(module, value); p.write_text(module.json_text(value)); red(module, c, profile_path, attach, "missing-rollback"); mutations += 1
        c = candidate(); p = c / module.RECEIPT_REL; value = json.loads(p.read_text()); value["private_reasoning"] = "hidden"; resign(module, value); p.write_text(module.json_text(value)); red(module, c, profile_path, attach, "private-reasoning"); mutations += 1
        c = candidate(); p = c / ".agents/control-plane/source.json"; p.write_text(p.read_text() + " "); red(module, c, profile_path, attach, "stale-artifact"); mutations += 1
        c = candidate(); p = c / "README.md"; p.write_text(p.read_text().replace(module.BEGIN, module.BEGIN + "\n" + module.BEGIN, 1)); red(module, c, profile_path, attach, "duplicate-marker"); mutations += 1

        human = world / "human-workflow"; make_consumer(human); workflow = human / module.WORKFLOW_REL; workflow.parent.mkdir(parents=True); workflow.write_text("name: Human workflow\n"); red(module, human, profile_path, attach, "human-workflow-overwrite", apply=True); mutations += 1

        failed = world / "attach-failure"; make_consumer(failed); original = files(failed)
        def broken(profile_path: Path, consumer_root: Path, check: bool) -> None:
            path = consumer_root / module.PROFILE_REL; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("partial\n")
            raise module.BootstrapError("planted downstream failure")
        red(module, failed, profile_path, broken, "atomic-rollback", apply=True)
        assert files(failed) == original
        mutations += 1

    print(f"CONSUMER-BOOTSTRAP-TESTS-GREEN positive={positives} mutations={mutations} shadow=PASS")


if __name__ == "__main__":
    main()
