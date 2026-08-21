#!/usr/bin/env python3
"""Strict worker-result shape + executor-provenance controls for issue #508.

Shape is owned by references/contracts/codex-worker-result-v2.schema.json.
This selftest proves the schema and the semantic checker actually discriminate:
every planted mutation must turn red for its own reason, and the green case
never claims more than shape/binding. Zero Codex, zero network.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import codex_v2_fixture as fx  # noqa: E402

check = fx.load("check_codex_worker_result")
SCHEMA = json.loads(
    (HERE.parent / "references" / "contracts" / "codex-worker-result-v2.schema.json").read_text(encoding="utf-8")
)

from jsonschema import Draft202012Validator  # noqa: E402

Draft202012Validator.check_schema(SCHEMA)
assert SCHEMA["additionalProperties"] is False
assert SCHEMA["properties"]["executor_provenance"]["additionalProperties"] is False
assert SCHEMA["properties"]["result_carrier"]["additionalProperties"] is False

positives = 0
controls = 0


def red(label: str, mutate, expect: str) -> None:
    global controls
    data = copy.deepcopy(BASE)
    mutate(data)
    try:
        check.check_result(data)
    except check.ResultContractError as error:
        assert expect in str(error), f"{label}: expected {expect!r} in {error}"
        controls += 1
        return
    raise AssertionError(f"{label}: control did not turn red")


with tempfile.TemporaryDirectory(prefix="codex-v2-worker-result-") as td:
    root = Path(td)
    case = fx.build_case(root)
    BASE = case["worker_result"]

    verdict = check.check_result(BASE)
    assert verdict == {
        "worker_result_shape": "PASS",
        "executor_provenance": "PASS",
        "carrier_binding": "PASS",
        "carrier_replay": "NOT_EXERCISED",
        "evidence_ceiling": "SHAPE_AND_BINDING_ONLY",
    }, verdict
    positives += 1

    # Shape controls -------------------------------------------------------
    red("S1 unschematized top-level field",
        lambda d: d.update(session_signed_in=True),
        "Additional properties are not allowed")
    red("S2 unschematized provenance field",
        lambda d: d["executor_provenance"].update(auth_mode="chatgpt"),
        "Additional properties are not allowed")
    red("S3 historical v1 receipt promoted to v2",
        lambda d: d.update(schema_version=1),
        "schema_version: 2 was expected")
    red("S4 missing required provenance block",
        lambda d: d.pop("executor_provenance"),
        "'executor_provenance' is a required property")
    red("S5 missing required provenance field",
        lambda d: d["executor_provenance"].pop("codex_binary_sha256"),
        "'codex_binary_sha256' is a required property")
    red("S6 missing durable carrier identity",
        lambda d: d.pop("result_carrier"),
        "'result_carrier' is a required property")
    red("S7 evidence ceiling promoted",
        lambda d: d.update(evidence_ceiling="LIVE_464_COMPLETE"),
        "was expected")
    red("S8 static receipt cannot pose as a live result",
        lambda d: d.update(sdk_execution="NOT_EXERCISED"),
        "was expected")
    red("S9 out-of-enum lease readback",
        lambda d: d.update(lease_readback="MOSTLY"),
        "is not one of")
    red("S10 absolute changed path",
        lambda d: d.update(changed_files=["/etc/passwd"]),
        "does not match")

    # Executor-provenance controls ----------------------------------------
    red("E1 adapter blob differs from the adapter that would execute",
        lambda d: d["executor_provenance"].update(adapter_blob_sha256="0" * 64),
        "does not match the adapter that would execute")
    red("E2 codex binary digest drift",
        lambda d: d["executor_provenance"].update(codex_binary_sha256="1" * 64),
        "codex_binary_sha256 drift")

    outside = root / "usr-local-bin"
    outside.mkdir()
    outside_binary = outside / "codex"
    outside_binary.write_bytes(b"#!/bin/sh\nexit 0\n")
    red("E3 PATH codex claimed while the SDK-bundled executable was used",
        lambda d: d["executor_provenance"].update(codex_binary_source="PATH"),
        "PATH codex claimed but")
    red("E4 SDK_BUNDLED claimed while a PATH executable was used",
        lambda d: d["executor_provenance"].update(
            codex_binary_path=str(outside_binary),
            codex_binary_sha256=fx.sha256_file(outside_binary),
        ),
        "SDK_BUNDLED claimed but")
    red("E5 ABSENT executor still carrying a path",
        lambda d: d["executor_provenance"].update(codex_binary_source="ABSENT"),
        "cannot carry a binary path or digest")
    red("E6 executor claimed without a resolved SDK package tree",
        lambda d: d["executor_provenance"].update(sdk_module_dir=None),
        "requires a resolved sdk_module_dir")

    # Carrier-binding controls --------------------------------------------
    red("B1 carrier manifest names the wrong repository",
        lambda d: d["result_carrier"].update(repo="someone/else"),
        "does not name the worker repo")
    red("B2 carrier manifest names the wrong base commit",
        lambda d: d["result_carrier"].update(base_sha="2" * 40),
        "does not name the worker base_sha")
    red("B3 carrier manifest names the wrong result tree",
        lambda d: d["result_carrier"].update(result_tree_sha="3" * 40),
        "does not name the worker tree_sha")
    red("B4 carrier belongs to another task/attempt",
        lambda d: d.update(attempt_id="a99"),
        "does not belong to this task/attempt")
    red("B5 hidden extra path omitted from the worker denominator",
        lambda d: d["result_carrier"].update(changed_paths=["src/a.py", "src/b.py"]),
        "does not match worker changed_files")
    red("B6 claimed change against the unchanged base tree",
        lambda d: d.update(tree_sha=d["base_tree_sha"]),
        "the result tree is the unchanged base tree")

    # The checker may also replay, and then says so explicitly.
    import subprocess

    result_path = root / "worker-result.json"
    result_path.write_text(json.dumps(BASE, indent=2, sort_keys=True), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(HERE.parent / "scripts" / "check_codex_worker_result.py"),
         str(result_path), "--carrier-bundle", str(case["bundle_path"])],
        text=True, capture_output=True, check=True,
    )
    replayed = json.loads(proc.stdout)
    assert replayed["carrier_replay"] == "PASS", replayed
    assert replayed["evidence_ceiling"] == "SHAPE_BINDING_AND_OFFLINE_REPLAY_ONLY", replayed
    positives += 1

    # A deterministic fixture is not live #464 completion: the strongest verdict
    # this gate can emit is still bounded to shape/binding/offline replay.
    assert "LIVE" not in replayed["evidence_ceiling"].replace("OFFLINE", "")

print(f"codex-worker-result selftest: PASS (positive={positives} controls={controls} live=NOT_EXERCISED)")
