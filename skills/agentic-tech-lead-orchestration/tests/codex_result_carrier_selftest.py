#!/usr/bin/env python3
"""Durable result-carrier controls for issue #508.

The positive case is a real end-to-end round trip: a scratch repository is
created, a post-turn tree is materialized, the carrier is published, the
originating repository is **deleted**, and the result tree is then resolved
from bundle + manifest alone. Every planted control must turn red for its own
reason. Zero Codex, zero network.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import codex_v2_fixture as fx  # noqa: E402

carrier = fx.load("codex_result_carrier")
positives = 0
controls = 0


def red(label: str, call, expect: str) -> None:
    global controls
    try:
        call()
    except carrier.CarrierError as error:
        assert expect in str(error), f"{label}: expected {expect!r} in {error}"
        controls += 1
        return
    raise AssertionError(f"{label}: control did not turn red")


with tempfile.TemporaryDirectory(prefix="codex-v2-carrier-") as td:
    root = Path(td)
    case = fx.build_case(root)
    origin = case["repo"]
    bundle = case["bundle_path"]
    manifest = case["manifest"]

    # The manifest is written next to the bundle and is byte-identical to the
    # carrier identity embedded in the worker result.
    on_disk = json.loads((bundle.parent / f"{bundle.name}.manifest.json").read_text(encoding="utf-8"))
    assert on_disk == manifest, "carrier manifest sidecar drifted from the returned manifest"

    # A tree that exists only in the originating object store, never carried.
    (origin / "src/uncarried.py").write_text("HIDDEN = 1\n", encoding="utf-8")
    uncarried_tree = fx.snapshot_tree(origin, case["base_sha"])
    assert fx.git(origin, "cat-file", "-t", uncarried_tree) == "tree"
    (origin / "src/uncarried.py").unlink()

    # A result tree with an undeclared extra path, carried but under-declared.
    (origin / "src/b.py").write_text("EXTRA = 1\n", encoding="utf-8")
    (origin / "src/a.py").write_text("VALUE = 1\n", encoding="utf-8")
    extra_tree = fx.snapshot_tree(origin, case["base_sha"])
    red(
        "C4a create refuses an under-declared denominator",
        lambda: carrier.create_carrier(
            origin,
            repo="ed3c/skills-shared",
            base_sha=case["base_sha"],
            base_tree_sha=case["base_tree"],
            result_tree_sha=extra_tree,
            changed_paths=["src/a.py"],
            out_dir=root / "carrier-extra",
            carrier_id="extra-1",
        ),
        "carrier denominator mismatch",
    )
    extra = carrier.create_carrier(
        origin,
        repo="ed3c/skills-shared",
        base_sha=case["base_sha"],
        base_tree_sha=case["base_tree"],
        result_tree_sha=extra_tree,
        changed_paths=["src/a.py", "src/b.py"],
        out_dir=root / "carrier-extra",
        carrier_id="extra-1",
    )
    extra_bundle = (root / "carrier-extra") / extra["bundle_filename"]
    (origin / "src/b.py").unlink()

    # The originating object store is destroyed. Everything below runs from the
    # carrier alone.
    shutil.rmtree(origin)
    assert not origin.exists()

    replay = carrier.replay_carrier(manifest, bundle)
    assert replay["result_tree_replay"] == "PASS"
    assert replay["result_tree_sha"] == case["result_tree"]
    assert replay["changed_paths"] == ["src/a.py"]
    assert replay["replay_source"] == "BUNDLE_ONLY_SCRATCH_REPOSITORY"
    assert replay["bundle_sha256"] == manifest["bundle_sha256"]
    positives += 1

    # The replayed tree really carries the post-turn bytes, not just a matching SHA.
    scratch = root / "inspect.git"
    subprocess.run(["git", "init", "-q", "--bare", str(scratch)], check=True)
    subprocess.run(
        ["git", "-C", str(scratch), "fetch", "--no-tags", "--quiet", str(bundle),
         f"+{manifest['result_ref']}:{manifest['result_ref']}"],
        check=True,
    )
    blob = subprocess.check_output(
        ["git", "-C", str(scratch), "show", f"{manifest['result_tree_sha']}:src/a.py"], text=True
    )
    assert blob == "VALUE = 1\n", blob
    positives += 1

    def mutated(**changes):
        m = copy.deepcopy(manifest)
        m.update(changes)
        return m

    # C1 result tree existed during execution (asserted above, in the now-deleted
    # origin) but is unreachable at replay because it was never carried.
    red(
        "C1 uncarried result tree",
        lambda: carrier.replay_carrier(mutated(result_tree_sha=uncarried_tree), bundle),
        "is absent from the carrier bundle object store",
    )

    # C2 syntactically valid SHA that is in no object store at all.
    red(
        "C2 absent tree object",
        lambda: carrier.replay_carrier(mutated(result_tree_sha="1" * 40), bundle),
        "is absent from the carrier bundle object store",
    )

    # C3a manifest names the wrong base tree — a tree that is present in the
    # bundle but is not what the base evidence ref carries.
    red(
        "C3a wrong base tree",
        lambda: carrier.replay_carrier(mutated(base_tree_sha=case["result_tree"]), bundle),
        "manifest names",
    )

    # C3b manifest names the wrong evidence commit for a real ref.
    red(
        "C3b wrong evidence commit",
        lambda: carrier.replay_carrier(mutated(result_evidence_commit="3" * 40), bundle),
        "manifest names",
    )

    # C3c manifest names refs that this bundle does not carry.
    red(
        "C3c wrong carrier id / refs",
        lambda: carrier.replay_carrier(
            mutated(
                carrier_id="someone-else",
                base_ref="refs/evidence/codex-v2/someone-else/base",
                result_ref="refs/evidence/codex-v2/someone-else/result",
            ),
            bundle,
        ),
        "does not carry the declared evidence refs",
    )

    # C4b hidden extra path omitted from the replayed denominator.
    red(
        "C4b hidden extra path",
        lambda: carrier.replay_carrier({**extra, "changed_paths": ["src/a.py"]}, extra_bundle),
        "replayed denominator mismatch",
    )

    # C5 the bundle itself is not the content-addressed artifact the manifest names.
    tampered = root / "tampered.bundle"
    tampered.write_bytes(bundle.read_bytes() + b"\n")
    red(
        "C5 bundle digest drift",
        lambda: carrier.replay_carrier(manifest, tampered),
        "carrier bundle size drift",
    )
    same_size = root / "same-size.bundle"
    raw = bytearray(bundle.read_bytes())
    raw[-1] ^= 0xFF
    same_size.write_bytes(bytes(raw))
    red(
        "C5b bundle content drift at identical size",
        lambda: carrier.replay_carrier(manifest, same_size),
        "carrier bundle digest drift",
    )

    # C6 no bundle at all: a SHA without a retained object is not a receipt.
    red(
        "C6 absent bundle",
        lambda: carrier.replay_carrier(manifest, root / "nope.bundle"),
        "carrier bundle is absent",
    )

    # C7 manifest shape: unschematized field, missing field, bad ref namespace.
    red(
        "C7a unschematized manifest field",
        lambda: carrier.replay_carrier({**manifest, "signed_in": True}, bundle),
        "unschematized fields",
    )
    red(
        "C7b missing manifest field",
        lambda: carrier.replay_carrier({k: v for k, v in manifest.items() if k != "bundle_sha256"}, bundle),
        "missing fields",
    )
    red(
        "C7c denominator not normalized",
        lambda: carrier.replay_carrier(mutated(changed_paths=["./src/a.py"]), bundle),
        "must be unique, normalized and sorted",
    )

print(
    f"codex-result-carrier selftest: PASS (positive={positives} controls={controls} "
    "origin_deleted=True live=NOT_EXERCISED)"
)
