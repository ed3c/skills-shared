#!/usr/bin/env python3
"""Shape + semantic gate for the Codex v2 worker result — issue #508.

`references/contracts/codex-worker-result-v2.schema.json` owns the shape
(Draft 2020-12, `additionalProperties: false`). This script owns the semantics
that a schema cannot express: the executor identity must be recomputable, the
claimed binary source must agree with where the binary actually lives, the
durable carrier manifest must name this exact tree/repository/base, and a
historical v1 receipt must never arrive here at all.

Exit codes follow the skill's shared contract: 0 pass, 2 contract violation,
64 unusable input, 70 validator mechanism unavailable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE.parent / "references" / "contracts" / "codex-worker-result-v2.schema.json"
ADAPTER_PATH = HERE / "run_codex_sdk_worker.py"
# Executor sources that name an actual executable. Anything else (UNRESOLVED,
# or a state added later) is an observation, not an identity, and fails closed.
RESOLVED_BINARY_SOURCES = {"SDK_PINNED_RUNTIME", "SDK_BUNDLED", "PATH", "ABSENT"}

sys.path.insert(0, str(HERE))
from codex_result_carrier import (  # noqa: E402
    CarrierError,
    carrier_id_for,
    replay_carrier,
    validate_manifest,
)


class ResultContractError(ValueError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_shape(result: Any) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as error:  # pragma: no cover - environment failure
        print(f"WORKER-RESULT-MECHANISM-UNAVAILABLE {error}")
        raise SystemExit(70)
    schema = _load_schema()
    Draft202012Validator.check_schema(schema)
    errors = [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in Draft202012Validator(schema).iter_errors(result)
    ]
    if errors:
        raise ResultContractError("worker result violates codex-worker-result-v2 schema: " + "; ".join(sorted(errors)))


def _inside(child: str, parent: str) -> bool:
    c = PurePosixPath(Path(child).resolve().as_posix()).parts
    p = PurePosixPath(Path(parent).resolve().as_posix()).parts
    return len(c) > len(p) and c[: len(p)] == p


def validate_executor_provenance(provenance: dict[str, Any], *, recompute: bool = True) -> str:
    """Return the executor-provenance verdict, or raise on a contract violation.

    The verdict is a state, not a boolean: an absent binary is not the same
    observation as a recomputed one. Returning "PASS" for both is how a Shadow
    machine that no longer holds the executable silently inherits the executing
    machine's claim about it.
    """

    source = provenance["codex_binary_source"]
    path = provenance["codex_binary_path"]
    sha = provenance["codex_binary_sha256"]
    module_dir = provenance["sdk_module_dir"]

    if source not in RESOLVED_BINARY_SOURCES:
        # UNRESOLVED and any future non-identity state fail closed here rather
        # than reaching the containment checks, which would pass them silently.
        raise ResultContractError(
            f"codex_binary_source={source} is not a resolved executor identity"
        )
    if source == "ABSENT":
        if path is not None or sha is not None:
            raise ResultContractError("codex_binary_source=ABSENT cannot carry a binary path or digest")
    else:
        if not path:
            raise ResultContractError(f"codex_binary_source={source} requires codex_binary_path")
        if module_dir is None:
            raise ResultContractError(f"codex_binary_source={source} requires a resolved sdk_module_dir")
        bundled = _inside(path, module_dir)
        if source == "SDK_BUNDLED" and not bundled:
            raise ResultContractError(
                f"SDK_BUNDLED claimed but {path} is outside the SDK package tree {module_dir}"
            )
        if source == "SDK_PINNED_RUNTIME":
            # The SDK runs codex_cli_bin.bundled_codex_path(), which lives in a
            # sibling distribution, not inside the openai_codex package tree.
            runtime_dir = provenance.get("runtime_module_dir")
            if not runtime_dir:
                raise ResultContractError(
                    "codex_binary_source=SDK_PINNED_RUNTIME requires a resolved runtime_module_dir"
                )
            if not _inside(path, runtime_dir):
                raise ResultContractError(
                    f"SDK_PINNED_RUNTIME claimed but {path} is outside the pinned runtime tree {runtime_dir}"
                )
        if source == "PATH" and bundled:
            raise ResultContractError(
                f"PATH codex claimed but {path} is the executable bundled inside {module_dir}"
            )

    if not recompute:
        return "NOT_RECOMPUTED"

    observed_adapter = _sha256_file(ADAPTER_PATH)
    if provenance["adapter_blob_sha256"] != observed_adapter:
        raise ResultContractError(
            "adapter_blob_sha256 does not match the adapter that would execute: "
            f"receipt {provenance['adapter_blob_sha256']} observed {observed_adapter}"
        )
    if path and sha:
        binary = Path(path)
        if not binary.is_file():
            return "UNVERIFIABLE_BINARY_ABSENT"
        observed_binary = _sha256_file(binary)
        if observed_binary != sha:
            raise ResultContractError(
                f"codex_binary_sha256 drift for {path}: receipt {sha} observed {observed_binary}"
            )
    return "PASS"


def validate_carrier_binding(result: dict[str, Any]) -> None:
    manifest = result["result_carrier"]
    validate_manifest(manifest)
    expected_id = carrier_id_for(result["task_id"], result["attempt_id"])
    if manifest["carrier_id"] != expected_id:
        raise ResultContractError(
            f"carrier_id {manifest['carrier_id']!r} does not belong to this task/attempt ({expected_id!r})"
        )
    for result_field, manifest_field in (
        ("repo", "repo"),
        ("base_sha", "base_sha"),
        ("base_tree_sha", "base_tree_sha"),
        ("tree_sha", "result_tree_sha"),
    ):
        if result[result_field] != manifest[manifest_field]:
            raise ResultContractError(
                f"carrier manifest {manifest_field}={manifest[manifest_field]!r} "
                f"does not name the worker {result_field}={result[result_field]!r}"
            )
    if manifest["changed_paths"] != sorted(result["changed_files"]):
        raise ResultContractError(
            f"carrier denominator {manifest['changed_paths']} does not match worker changed_files "
            f"{sorted(result['changed_files'])}"
        )


def check_result(result: Any, *, recompute_executor: bool = True) -> dict[str, Any]:
    validate_shape(result)
    if result["changed_files"] and result["tree_sha"] == result["base_tree_sha"]:
        raise ResultContractError("changed files were claimed but the result tree is the unchanged base tree")
    executor_provenance = validate_executor_provenance(
        result["executor_provenance"], recompute=recompute_executor
    )
    validate_carrier_binding(result)
    return {
        "worker_result_shape": "PASS",
        "executor_provenance": executor_provenance,
        "carrier_binding": "PASS",
        "carrier_replay": "NOT_EXERCISED",
        "evidence_ceiling": "SHAPE_AND_BINDING_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("result", nargs="?", help="worker result JSON emitted by run_codex_sdk_worker.py --execute")
    parser.add_argument("--carrier-bundle", help="also replay the durable carrier from this bundle")
    parser.add_argument(
        "--no-recompute-executor",
        action="store_true",
        help="skip on-disk executor digest recomputation (shape/consistency only)",
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        selftest = HERE.parent / "tests" / "codex_worker_result_selftest.py"
        import subprocess

        return subprocess.run([sys.executable, str(selftest)], check=False).returncode
    if not args.result:
        print("usage: check_codex_worker_result.py <worker-result.json>")
        return 64

    try:
        result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"WORKER-RESULT-INPUT-FAIL {error}")
        return 64

    try:
        verdict = check_result(result, recompute_executor=not args.no_recompute_executor)
        if args.carrier_bundle:
            replay_carrier(result["result_carrier"], Path(args.carrier_bundle))
            verdict["carrier_replay"] = "PASS"
            verdict["evidence_ceiling"] = "SHAPE_BINDING_AND_OFFLINE_REPLAY_ONLY"
    except (ResultContractError, CarrierError) as error:
        print(f"WORKER-RESULT-FAIL {error}")
        return 2

    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
