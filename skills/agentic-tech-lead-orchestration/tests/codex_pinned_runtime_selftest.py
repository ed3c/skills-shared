#!/usr/bin/env python3
"""Planted-defect controls for the new executor-provenance states (#464).

Folded in from the #464 apply lane's out-of-tree probe by the integration owner.
Every one must turn red for its own reason.
"""
import copy, json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import codex_v2_fixture as fx  # noqa: E402

check = fx.load("check_codex_worker_result")
from jsonschema import Draft202012Validator as V  # noqa: E402

SCHEMA = json.loads((ROOT / "references/contracts/codex-worker-result-v2.schema.json").read_text())
V.check_schema(SCHEMA)

positives = controls = 0

with tempfile.TemporaryDirectory(prefix="codex-464-probe-") as td:
    root = Path(td)
    case = fx.build_case(root)
    BASE = case["worker_result"]

    def shape(d):
        return sorted(e.message for e in V(SCHEMA).iter_errors(d))

    def red(label, mutate, expect):
        global controls
        d = copy.deepcopy(BASE)
        mutate(d)
        try:
            check.check_result(d)
        except check.ResultContractError as error:
            assert expect in str(error), f"{label}: expected {expect!r} in {error}"
            controls += 1
            print(f"RED {label}: {error}")
            return
        raise AssertionError(f"{label}: control did not turn red")

    def green(label, mutate, expect_verdict):
        global positives
        d = copy.deepcopy(BASE)
        mutate(d)
        assert not shape(d), f"{label}: shape red {shape(d)}"
        v = check.check_result(d)
        assert v["executor_provenance"] == expect_verdict, f"{label}: {v}"
        positives += 1
        print(f"GREEN {label}: executor_provenance={v['executor_provenance']}")

    # A pinned-runtime binary sitting in a sibling package tree is admissible.
    runtime = root / "site-packages" / "codex_cli_bin"
    (runtime / "bin").mkdir(parents=True)
    binary = runtime / "bin" / "codex"
    binary.write_bytes(b"#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)

    def as_pinned(d):
        d["executor_provenance"].update(
            codex_binary_source="SDK_PINNED_RUNTIME",
            runtime_module_dir=str(runtime),
            codex_binary_path=str(binary),
            codex_binary_sha256=fx.sha256_file(binary),
        )

    green("P1 SDK_PINNED_RUNTIME inside its runtime tree", as_pinned, "PASS")

    def pinned_outside(d):
        as_pinned(d)
        d["executor_provenance"].update(runtime_module_dir=str(root / "site-packages" / "elsewhere"))

    red("R1 SDK_PINNED_RUNTIME claimed outside runtime_module_dir",
        pinned_outside, "outside the pinned runtime tree")

    def pinned_without_dir(d):
        as_pinned(d)
        d["executor_provenance"].update(runtime_module_dir=None)

    red("R2 SDK_PINNED_RUNTIME without a resolved runtime tree",
        pinned_without_dir, "requires a resolved runtime_module_dir")

    # UNRESOLVED is not an executor identity: it must fail closed at BOTH the
    # shape layer and the semantic layer (two independent arrivals).
    unresolved = copy.deepcopy(BASE)
    unresolved["executor_provenance"].update(codex_binary_source="UNRESOLVED")
    assert shape(unresolved), "R3a: schema accepted UNRESOLVED"
    controls += 1
    print(f"RED R3a UNRESOLVED rejected by schema: {shape(unresolved)[0]}")
    # check_result validates shape first, so the semantic gate is probed
    # directly — the point is that it is an INDEPENDENT arrival, not that it
    # runs second.
    try:
        check.validate_executor_provenance(unresolved["executor_provenance"])
    except check.ResultContractError as error:
        assert "is not a resolved executor identity" in str(error), error
        controls += 1
        print(f"RED R3b UNRESOLVED rejected by the semantic gate: {error}")
    else:
        raise AssertionError("R3b: semantic gate accepted UNRESOLVED")

    # The fail-open this issue is about: the binary is gone, so the digest is
    # not recomputable, and the verdict must say so instead of claiming PASS.
    gone = root / "site-packages" / "codex_cli_bin" / "bin" / "vanished"
    def as_absent_binary(d):
        as_pinned(d)
        d["executor_provenance"].update(codex_binary_path=str(gone))

    green("P2 executing binary no longer on disk", as_absent_binary, "UNVERIFIABLE_BINARY_ABSENT")

    v = check.check_result(copy.deepcopy(BASE), recompute_executor=False)
    assert v["executor_provenance"] == "NOT_RECOMPUTED", v
    positives += 1
    print("GREEN P3 --no-recompute-executor: executor_provenance=NOT_RECOMPUTED")

    # The binder must refuse every non-PASS verdict.
    compile_mod = fx.load("compile_codex_live_acceptance")
    for label, mutate in (("absent binary", as_absent_binary),):
        worker = copy.deepcopy(BASE)
        payload = {"worker_result": worker,
                   "controller": fx.controller_for(worker),
                   "carrier_bundle_path": str(case["bundle_path"])}
        mutate(payload["worker_result"])
        try:
            compile_mod.compile_receipt(payload)
        except compile_mod.ContractError as error:
            assert "executor provenance not recomputable" in str(error), error
            controls += 1
            print(f"RED R4 live acceptance refused on {label}: {error}")
        else:
            raise AssertionError("R4: binder compiled a receipt on an unverifiable executor")

print(f"pinned-runtime probe: PASS (positive={positives} controls={controls} live=NOT_EXERCISED)")
