#!/usr/bin/env python3
"""Live-acceptance binder controls.

#505 proved that worker and controller can agree on a tree that lacks the
claimed change. #508 adds the next requirement: the bound result tree must
still resolve after the originating worktree and object store are gone. The
positive case here therefore compiles the receipt with the originating
repository **deleted**, using the durable carrier alone.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import codex_v2_fixture as fx  # noqa: E402

from jsonschema import Draft202012Validator  # noqa: E402

mod = fx.load("compile_codex_live_acceptance")
RECEIPT_SCHEMA = json.loads(
    (HERE.parent / "references" / "contracts" / "codex-live-acceptance-receipt-v2.schema.json").read_text(
        encoding="utf-8"
    )
)
Draft202012Validator.check_schema(RECEIPT_SCHEMA)

positives = 0
controls = 0


def fail(label, mutator):
    global controls
    data = copy.deepcopy(PACKET)
    mutator(data)
    try:
        mod.compile_receipt(data)
    except mod.ContractError:
        controls += 1
        return
    raise AssertionError(f"{label}: mutation passed")


with tempfile.TemporaryDirectory(prefix="codex-live-acceptance-") as td:
    root = Path(td)
    case = fx.build_case(root)
    origin = case["repo"]
    base_tree = case["base_tree"]

    # A tree carrying an undeclared extra path, published as its own carrier.
    (origin / "src/b.py").write_text("EXTRA = 1\n", encoding="utf-8")
    (origin / "src/a.py").write_text("VALUE = 1\n", encoding="utf-8")
    extra_tree = fx.snapshot_tree(origin, case["base_sha"])
    carrier = fx.load("codex_result_carrier")
    extra_manifest = carrier.create_carrier(
        origin,
        repo="ed3c/skills-shared",
        base_sha=case["base_sha"],
        base_tree_sha=base_tree,
        result_tree_sha=extra_tree,
        changed_paths=["src/a.py", "src/b.py"],
        out_dir=root / "carrier-extra",
        carrier_id=carrier.carrier_id_for(case["worker_result"]["task_id"], case["worker_result"]["attempt_id"]),
    )
    extra_bundle = (root / "carrier-extra") / extra_manifest["bundle_filename"]

    # #508's load-bearing property: the originating object store is destroyed
    # before any acceptance work happens.
    shutil.rmtree(origin)
    assert not origin.exists()

    PACKET = {
        "worker_result": case["worker_result"],
        "controller": fx.controller_for(case["worker_result"]),
        "carrier_bundle_path": str(case["bundle_path"]),
    }

    receipt = mod.compile_receipt(copy.deepcopy(PACKET))
    errors = [e.message for e in Draft202012Validator(RECEIPT_SCHEMA).iter_errors(receipt)]
    assert not errors, errors
    assert receipt["schema_version"] == 2
    assert receipt["base_tree_sha"] == base_tree
    assert receipt["tree_sha"] == case["result_tree"]
    assert receipt["result_tree_readback"] == "PASS"
    assert receipt["result_tree_replay"] == "PASS"
    assert receipt["result_carrier"]["bundle_sha256"] == case["manifest"]["bundle_sha256"]
    assert receipt["executor_identity"]["codex_binary_source"] == "SDK_BUNDLED"
    assert receipt["acceptance_state"] == "LIVE_RUNTIME_AND_CONTROLLER_READBACK_CANDIDATE"
    assert receipt["shadow_review_required"] is True
    assert receipt["evidence_ceiling"] == "LIVE_EXECUTION_OBSERVED_SHADOW_PENDING"
    positives += 1

    fail("M1 sdk not exercised", lambda x: x["worker_result"].update(sdk_execution="NOT_EXERCISED"))
    fail("M2 lease readback failed", lambda x: x["worker_result"].update(lease_readback="FAIL"))
    fail("M3 static adapter state", lambda x: x["worker_result"].update(adapter_state="STATIC_VALIDATED"))
    fail("M4 nonterminal turn", lambda x: x["worker_result"].update(turn_status="failed"))
    fail("M5 controller attempt drift", lambda x: x["controller"].update(attempt_id="A2"))
    fail("M6 controller denominator drift", lambda x: x["controller"].update(changed_files=["src/b.py"]))
    fail("M7 controller diff readback failed", lambda x: x["controller"].update(source_diff_readback="FAIL"))
    fail("M8 controller tests readback failed", lambda x: x["controller"].update(tests_readback="FAIL"))
    fail("M9 no verification commands", lambda x: x["controller"].update(commands=[]))
    fail("M10 verification command failed", lambda x: x["controller"]["commands"][0].update(exit_code=1))
    fail("M11 malformed base sha", lambda x: x["worker_result"].update(base_sha="abc"))
    fail("M12 raw model prose persisted", lambda x: x["worker_result"].update(final_response="raw model prose"))

    # M13: the exact false-PASS found by the first real #464 run. Worker and
    # controller agree with each other, but their bound tree is the unchanged
    # pre-turn tree and therefore does not contain the claimed path.
    def missing_claimed_change(x):
        x["worker_result"]["tree_sha"] = base_tree
        x["controller"]["tree_sha"] = base_tree
    fail("M13 bound tree lacks the claimed change", missing_claimed_change)

    # M14: a result tree with an additional undeclared change must not pass just
    # because worker and controller repeat the same incomplete changed_files.
    def hidden_extra_change(x):
        x["worker_result"]["tree_sha"] = extra_tree
        x["worker_result"]["result_carrier"] = copy.deepcopy(extra_manifest)
        x["worker_result"]["result_carrier"]["changed_paths"] = ["src/a.py"]
        x["controller"]["tree_sha"] = extra_tree
        x["carrier_bundle_path"] = str(extra_bundle)
    fail("M14 hidden extra path omitted from the denominator", hidden_extra_change)

    # M15: a syntactically valid SHA that is in no carried object store.
    def missing_tree_object(x):
        missing = "1" * 40
        x["worker_result"]["tree_sha"] = missing
        x["worker_result"]["result_carrier"]["result_tree_sha"] = missing
        x["controller"]["tree_sha"] = missing
    fail("M15 tree sha absent from the carrier", missing_tree_object)

    # M16: base commit and declared base tree must agree, otherwise the result
    # comparison has no reproducible pre-turn denominator.
    def base_tree_drift(x):
        x["worker_result"]["base_tree_sha"] = "2" * 40
        x["worker_result"]["result_carrier"]["base_tree_sha"] = "2" * 40
    fail("M16 base tree drift", base_tree_drift)

    # #508 controls -------------------------------------------------------
    fail("M17 no durable carrier at all", lambda x: x["worker_result"].pop("result_carrier"))
    fail("M18 carrier bundle absent", lambda x: x.update(carrier_bundle_path=str(root / "nope.bundle")))
    fail("M19 carrier bundle path empty", lambda x: x.update(carrier_bundle_path=""))
    fail("M20 carrier names another repository", lambda x: x["worker_result"]["result_carrier"].update(repo="someone/else"))
    fail("M21 historical v1 worker result", lambda x: x["worker_result"].update(schema_version=1))
    fail("M22 unschematized worker field", lambda x: x["worker_result"].update(session_signed_in=True))
    fail("M23 missing executor provenance", lambda x: x["worker_result"].pop("executor_provenance"))
    fail("M24 executor blob differs from the bound adapter",
         lambda x: x["worker_result"]["executor_provenance"].update(adapter_blob_sha256="0" * 64))
    fail("M25 PATH codex claimed while the bundled executable was used",
         lambda x: x["worker_result"]["executor_provenance"].update(codex_binary_source="PATH"))
    fail("M26 packet carries an extra top-level key", lambda x: x.update(shadow_verdict="PASS"))

print(
    f"codex-live-acceptance selftest: PASS (positive={positives} mutations={controls} "
    "origin_deleted=True live=NOT_EXERCISED)"
)
