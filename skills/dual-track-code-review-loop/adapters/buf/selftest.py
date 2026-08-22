#!/usr/bin/env python3
"""Execute the Buf adapter against the frozen DTCR schemas.

Three lanes, and the numbers each one counts are printed so a run can never
report a green it did not measure:

    replay     both committed fixtures (`breaking-pair`, a real field
               deletion; `not-applicable`, a zero-.proto task) are emitted
               with no provider on the machine, from bytes and stdout a real
               `buf` run produced, and both the emitted
               `contract-compatibility-result` and `fact-plane-receipt` are
               validated against the read-only schemas in
               `../../references/schemas/`.
    falsifiers all ten planted defects named by issue #549 are run through the
               code path that owns each one and must be refused *by that
               guard*. A defect that dies on an unrelated check proves nothing
               about the guard it was written for. Two of the ten
               (BUF_WRONG_BASELINE, BUF_PASS_PROMOTED_TO_DEPLOYMENT_OR_MERGE_PASS)
               are already enforced by the frozen schema itself and are
               counted in `cases.json`; this lane still exercises them here,
               by knockout, so a run of this file alone proves all ten without
               reading a second file to believe the other two are covered.
    live       if the buf CLI is on `PATH` or named by `DTCR_BUF_BIN`, the
               adapter runs for real against the committed fixture sources and
               its observed provider identity and findings are compared with
               what the committed fixtures recorded, with the subject commit
               factored out (a second host's HEAD differs from the one this
               fixture was recorded at; what has to agree is what the same
               binary, the same config and the same bytes determine).
               A missing provider is start-readiness, not a failure: the lane
               prints NOT_EXERCISED and stays green.

Exit 0 green, 2 a lane failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "DTCR-BUF-SELFTEST-UNUSABLE: jsonschema is required. This suite executes the frozen "
        "schemas as deciding gates; skipping them would report the same green as running them.",
        file=sys.stderr,
    )
    raise SystemExit(70)

ADAPTER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ADAPTER_DIR))
import adapter as A  # noqa: E402

SCHEMAS = A.SCHEMAS
FIXTURES = ADAPTER_DIR / "fixtures"

SCHEMA_FILES = {
    A.COMPAT_SCHEMA: "contract-compatibility-result.schema.json",
    A.RECEIPT_SCHEMA: "fact-plane-receipt.schema.json",
}

failures: list[str] = []


def fail(message: str) -> None:
    failures.append(message)
    print(f"  FAIL {message}")


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def validate(instance: dict[str, Any], schema: dict[str, Any]) -> list[Any]:
    return sorted(Draft202012Validator(schema).iter_errors(instance), key=str)


def schema_path_of(error: Any) -> str:
    out = ""
    for part in error.absolute_schema_path:
        out += f"[{part}]" if isinstance(part, int) else (f".{part}" if out else str(part))
    return out


def knockout(schema: dict[str, Any], path: str) -> dict[str, Any]:
    """Delete exactly the keyword `path` names from a copy of `schema`."""
    node: Any = copy.deepcopy(schema)
    parts: list[Any] = []
    for chunk in path.split("."):
        while "[" in chunk:
            head, _, rest = chunk.partition("[")
            index, _, chunk = rest.partition("]")
            if head:
                parts.append(head)
            parts.append(int(index))
        if chunk:
            parts.append(chunk)
    root = node
    for part in parts[:-1]:
        node = node[part]
    del node[parts[-1]]
    return root


def validate_emission(name: str, emitted: dict[str, Any]) -> None:
    compat_schema = load_schema(SCHEMA_FILES[A.COMPAT_SCHEMA])
    receipt_schema = load_schema(SCHEMA_FILES[A.RECEIPT_SCHEMA])
    for label, record, schema in (
        ("contract_compatibility_result", emitted["contract_compatibility_result"], compat_schema),
        ("fact_plane_receipt", emitted["fact_plane_receipt"], receipt_schema),
    ):
        errors = validate(record, schema)
        if errors:
            fail(f"{name}: {label} refused by the frozen schema: {errors[0].message}")


# --------------------------------------------------------------------------
# lane 1: replay
# --------------------------------------------------------------------------
def lane_replay() -> dict[str, dict[str, Any]]:
    print("replay")
    emissions: dict[str, dict[str, Any]] = {}
    requests = sorted(FIXTURES.glob("*/request.json"))
    if not requests:
        fail("no fixture requests on the tree; the replay lane would be green over nothing")
    for request in requests:
        name = request.parent.name
        emitted = A.run_replay(request)
        emissions[name] = emitted
        validate_emission(name, emitted)
        compat = emitted["contract_compatibility_result"]
        print(f"  {name}: outcome={compat['outcome']} findings={len(compat['findings'])} " f"provider={compat['provider']['version']}")
        second = A.run_replay(request)
        if A.canonical(second) != A.canonical(emitted):
            fail(f"{name}: two emissions of one fixture differ; the output is not deterministic")
        if any(compat["grants"].values()) or any(emitted["fact_plane_receipt"]["grants"].values()):
            fail(f"{name}: a grants block was non-false; nothing this adapter emits may promote itself")
    breaking_pair = emissions.get("breaking-pair", {}).get("contract_compatibility_result", {})
    if breaking_pair.get("outcome") != "BREAKING_CHANGE_DETECTED":
        fail("breaking-pair: the committed fixture is a real field deletion and must report BREAKING_CHANGE_DETECTED")
    not_applicable = emissions.get("not-applicable", {}).get("contract_compatibility_result", {})
    if not_applicable.get("outcome") != "NOT_APPLICABLE":
        fail("not-applicable: the committed fixture declares zero .proto blobs and must report NOT_APPLICABLE")
    return emissions


# --------------------------------------------------------------------------
# lane 2: falsifiers
# --------------------------------------------------------------------------
rows = 0


def row(name: str, ok: bool, extra: str = "") -> None:
    global rows
    rows += 1
    if ok:
        print(f"  {name}: refused{(' ' + extra) if extra else ''}")
    else:
        fail(f"{name}: the planted defect was not refused by its own guard")


def expect_refusal(name: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except A.Refusal as refusal:
        row(name, refusal.reason == name, f"by adapter guard {refusal.reason}" if refusal.reason == name else f"by {refusal.reason} instead")
        return
    except Exception as error:  # noqa: BLE001 - any other exception is still not the named guard
        fail(f"{name}: raised {type(error).__name__} rather than its named refusal")
        rows_bump()
        return
    row(name, False)


def rows_bump() -> None:
    global rows
    rows += 1


def mutated_tree() -> Path:
    work = Path(tempfile.mkdtemp(prefix="dtcr-buf-")) / "buf"
    shutil.copytree(ADAPTER_DIR, work, ignore=shutil.ignore_patterns("__pycache__", ".tools"))
    return work


def expect_schema_refusal(
    name: str,
    schema_file: str,
    instance: dict[str, Any],
    keyword: str,
    knockout_at: str | None = None,
) -> None:
    schema = load_schema(schema_file)
    errors = validate(instance, schema)
    if not errors:
        fail(f"{name}: the frozen schema admitted the planted defect")
        rows_bump()
        return
    paths = {schema_path_of(error) for error in errors}
    if keyword not in paths:
        fail(f"{name}: refused by {sorted(paths)}, not by the named guard {keyword}")
        rows_bump()
        return
    where = knockout_at or keyword
    if validate(instance, knockout(schema, where)):
        fail(f"{name}: still refused after {where} was removed, so that keyword is not what refuses it")
        rows_bump()
        return
    row(name, True, f"by {schema_file}#{keyword}, admitted once {where} is knocked out")


def lane_falsifiers(emissions: dict[str, dict[str, Any]]) -> int:
    print("falsifiers")
    breaking_pair = emissions["breaking-pair"]
    compat = breaking_pair["contract_compatibility_result"]
    receipt = breaking_pair["fact_plane_receipt"]
    identity = {"version": compat["provider"]["version"], "executable_sha256": compat["provider"]["executable_sha256"], "probe_exit_code": 0}

    # 1. BUF_WRONG_BASELINE -- schema-enforced (baseline.commit pattern,
    # DTCR-XC-CK-001, already counted in cases.json). Exercised here too by
    # knockout so a run of this file alone proves it.
    expect_schema_refusal(
        "BUF_WRONG_BASELINE",
        "contract-compatibility-result.schema.json",
        {**compat, "baseline": {**compat["baseline"], "commit": "main"}},
        "properties.baseline.properties.commit.pattern",
    )

    # 2. MUTABLE_BASELINE_ALIAS -- adapter-level, refused before git/buf ever run.
    expect_refusal("MUTABLE_BASELINE_ALIAS", lambda: A.check_baseline_ref("main"))

    # 3. SOURCE_SCHEMA_DIGEST_ABSENT -- the applicable lane entered with no declared blobs.
    expect_refusal("SOURCE_SCHEMA_DIGEST_ABSENT", lambda: A.check_declared_blobs(True, []))

    # 4. BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING -- proven against this
    # repo's own fixture: `except: [FIELD_NO_DELETE]` is the exact config that
    # turned the real breaking-pair candidate's field deletion invisible to a
    # live `buf breaking` run during fixture capture (recorded exit 0, no
    # findings, against the same binary and the same artifacts that otherwise
    # report exit 100 with one FIELD_NO_DELETE finding).
    expect_refusal(
        "BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING",
        lambda: A.check_breaking_config({"version": "v2", "breaking": {"use": ["FILE"], "except": ["FIELD_NO_DELETE"]}}),
    )
    expect_refusal(
        "BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING",
        lambda: A.check_breaking_config({"version": "v2", "breaking": {"use": ["WIRE_JSON"]}}),
    )

    # 5. GENERATED_ARTIFACT_USED_WITHOUT_SOURCE_BINDING -- a pre-built image
    # supplied with no source blob list to bind it back to text.
    expect_refusal("GENERATED_ARTIFACT_USED_WITHOUT_SOURCE_BINDING", lambda: A.check_artifact_source_binding(True, []))

    # 6. BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED -- an identity block built
    # without a real, successful `buf --version` probe behind it (PATH
    # presence alone, no `probe_exit_code`).
    expect_refusal(
        "BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED",
        lambda: A.provider_block({"version": "found-on-path"}, "0" * 64, "0" * 64),
    )

    # 7. NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE -- proven by
    # calling the shared emitter directly with zero declared blobs, bypassing
    # the dispatcher-level guard entirely: the emitter's own outcome
    # computation must never be reached for a zero-source compare.
    expect_refusal(
        "NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE",
        lambda: A.emit_applicable(
            subject=compat["subject"],
            baseline_commit=compat["baseline"]["commit"],
            baseline_artifact_name="baseline",
            candidate_artifact_name="candidate",
            baseline_bytes=b"\x00",
            candidate_bytes=b"\x00",
            breaking_run={
                "config": {"version": "v2", "breaking": {"use": ["FILE"]}},
                "config_digest": "0" * 64,
                "findings": [],
                "exit_code": 0,
                "stdout": "",
            },
            lint_run={"exit_code": 0, "stdout": ""},
            identity=identity,
            declared_blobs=[],
            baseline_cached_digest=None,
        ),
    )
    prove_no_protobuf_guard_disabled_is_red()

    # 8. BUF_PASS_PROMOTED_TO_DEPLOYMENT_OR_MERGE_PASS -- schema-enforced
    # (grants block hard-const false, DTCR-XC-CK-003, already counted in
    # cases.json). Exercised here too by knockout.
    expect_schema_refusal(
        "BUF_PASS_PROMOTED_TO_DEPLOYMENT_OR_MERGE_PASS",
        "contract-compatibility-result.schema.json",
        {**compat, "grants": {**compat["grants"], "deployment": True}},
        "properties.grants.properties.deployment.const",
    )
    expect_schema_refusal(
        "BUF_PASS_PROMOTED_TO_DEPLOYMENT_OR_MERGE_PASS (task_pass)",
        "fact-plane-receipt.schema.json",
        {**receipt, "grants": {**receipt["grants"], "task_pass": True}},
        "properties.grants.properties.task_pass.const",
    )

    # 9. BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS -- the closed
    # subcommand set. `push`, `registry` and `login` are refused before any
    # subprocess is started.
    for forbidden in ("push", "registry", "login", "beta"):
        expect_refusal("BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS", lambda f=forbidden: A.check_no_bsr_intent(f))

    # 10. STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE -- a cached digest that
    # belongs to a different baseline (this repo's own `not-applicable`
    # fixture digest, standing in for "some other baseline") reused against
    # the `breaking-pair` baseline's freshly recomputed digest.
    stale = emissions["not-applicable"]["contract_compatibility_result"]["baseline"]["artifact_digest"]
    fresh = compat["baseline"]["artifact_digest"]
    if stale == fresh:
        fail("STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE: the two fixtures' baseline digests coincide; the row proves nothing")
        rows_bump()
    else:
        expect_refusal("STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE", lambda: A.check_stale_baseline(stale, fresh))

    return rows


def prove_no_protobuf_guard_disabled_is_red() -> None:
    """The repair note for #549 requires more than a guard that fires: it
    requires proof that *without* the guard, the exact code path this falls
    through to would default to a clean pass. `emit_applicable`'s guard is a
    single `if not declared_blobs: raise ...` immediately above the outcome
    computation; disabling exactly that line in a private copy of the module
    and re-running the same call must produce `NO_BREAKING_CHANGE_DETECTED`
    for a zero-source compare -- proving the guard is load-bearing, not
    decorative."""
    work = mutated_tree()
    try:
        source = (work / "adapter.py").read_text(encoding="utf-8")
        anchor = (
            "    if not declared_blobs:\n"
            "        raise Refusal(\n"
            '            "NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE",\n'
        )
        if anchor not in source:
            fail("NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE: the guard's source anchor moved; the red-proof mutation no longer targets it")
            rows_bump()
            return
        # Replace the guard with a no-op `if False:` so the raise beneath it,
        # and everything else in the function, is untouched -- this disables
        # exactly one guard rather than restructuring the function.
        mutated = source.replace("    if not declared_blobs:\n", "    if False:  # ponytail-mutated: guard disabled for the red-proof\n", 1)
        (work / "adapter.py").write_text(mutated, encoding="utf-8")
        import importlib.util

        spec = importlib.util.spec_from_file_location("adapter_mutated_549", work / "adapter.py")
        mutated_module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mutated_module)
        # The mutated copy lives one directory shallower than the real
        # adapter (no `../../references/schemas` beside it); point its
        # SCHEMAS constant back at the real, frozen schemas rather than
        # reconstructing the whole skill tree just for this one mutation.
        mutated_module.SCHEMAS = A.SCHEMAS
        result = mutated_module.emit_applicable(
            subject={"repository_binding_id": "DTCR-RB-0000000000000000", "commit": "0" * 40, "tree": "0" * 40},
            baseline_commit="0" * 40,
            baseline_artifact_name="baseline",
            candidate_artifact_name="candidate",
            baseline_bytes=b"\x00",
            candidate_bytes=b"\x00",
            breaking_run={
                "config": {"version": "v2", "breaking": {"use": ["FILE"]}},
                "config_digest": "0" * 64,
                "findings": [],
                "exit_code": 0,
                "stdout": "",
            },
            lint_run={"exit_code": 0, "stdout": ""},
            identity={"version": "found-on-path", "executable_sha256": "0" * 64, "probe_exit_code": 0},
            declared_blobs=[],
            baseline_cached_digest=None,
        )
        outcome = result["contract_compatibility_result"]["outcome"]
        row(
            "NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE (red proof)",
            outcome == "NO_BREAKING_CHANGE_DETECTED",
            f"with the guard disabled, a zero-source compare emitted outcome={outcome!r} -- "
            "proving the guard is what stood between this input and a false pass" if outcome == "NO_BREAKING_CHANGE_DETECTED" else "",
        )
        if outcome != "NO_BREAKING_CHANGE_DETECTED":
            fail(f"NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE: disabling the guard produced {outcome!r}, not the expected false pass; the red proof did not fire as designed")
    finally:
        shutil.rmtree(work.parent, ignore_errors=True)


# --------------------------------------------------------------------------
# lane 3: live
# --------------------------------------------------------------------------
def lane_live(emissions: dict[str, dict[str, Any]]) -> str:
    print("live")
    binary = A.find_cli()
    if binary is None:
        print("  NOT_EXERCISED: no buf executable on PATH and DTCR_BUF_BIN unset. A missing provider is start-readiness, not a failure.")
        return "NOT_EXERCISED"

    repo = Path(A.git(ADAPTER_DIR, "rev-parse", "--show-toplevel"))
    baseline_dir = str((ADAPTER_DIR / "fixtures/breaking-pair/baseline").relative_to(repo))
    candidate_dir = str((ADAPTER_DIR / "fixtures/breaking-pair/candidate").relative_to(repo))
    baseline_commit = A.git(repo, "rev-parse", "HEAD")

    identity = A.cli_identity(binary)
    baseline_bytes = A.build_artifact(binary, repo / baseline_dir)
    candidate_bytes = A.build_artifact(binary, repo / candidate_dir)
    breaking_run = A.run_breaking(binary, repo, repo / candidate_dir, repo / baseline_dir, use=["FILE"], excepts=[])
    lint_run = A.run_lint(binary, repo, repo / candidate_dir)
    declared = A.declared_proto_blobs(repo, candidate_dir)

    live_emitted = A.emit_applicable(
        subject=A.live_subject(repo),
        baseline_commit=baseline_commit,
        baseline_artifact_name="baseline",
        candidate_artifact_name="candidate",
        baseline_bytes=baseline_bytes,
        candidate_bytes=candidate_bytes,
        breaking_run=breaking_run,
        lint_run=lint_run,
        identity=identity,
        declared_blobs=declared,
        baseline_cached_digest=None,
    )
    validate_emission("live", live_emitted)
    compat = live_emitted["contract_compatibility_result"]
    print(f"  ran buf {identity['version']} over {baseline_dir} vs {candidate_dir}: outcome={compat['outcome']}, exit {breaking_run['exit_code']}")

    if not breaking_run["findings"]:
        fail("live: the committed candidate fixture is a real field deletion; a live run finding no breaking change means the fixture or the binding drifted")

    # BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED, the half only meaningful
    # with a real binary present: prove that `find_cli()` returning a path
    # (found on PATH) is not, by itself, enough to build a provider block --
    # only the real `--version` probe this lane just ran is.
    found_only = {"version": "unknown", "executable_sha256": identity["executable_sha256"]}
    try:
        A.provider_block(found_only, "0" * 64, "0" * 64)
    except A.Refusal as refusal:
        if refusal.reason == "BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED":
            print("  BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED (live half): PATH presence alone is refused; only the real probe this lane ran was accepted")
        else:
            fail(f"BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED (live half): refused by {refusal.reason} instead")
    else:
        fail("BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED (live half): a PATH-only identity with no real probe was accepted")

    fixture = emissions["breaking-pair"]["contract_compatibility_result"]
    if compat["baseline"]["artifact_digest"] != fixture["baseline"]["artifact_digest"]:
        fail("live: this host's baseline build digest does not match the committed fixture's; the same binary, config and bytes should agree")
    elif compat["candidate"]["artifact_digest"] != fixture["candidate"]["artifact_digest"]:
        fail("live: this host's candidate build digest does not match the committed fixture's; the same binary, config and bytes should agree")
    else:
        print("  this host reproduces the committed fixture's artifact digests byte-for-byte")
    if [f["rule_id"] for f in compat["findings"]] != [f["rule_id"] for f in fixture["findings"]]:
        fail("live: this host's breaking findings (by rule_id) differ from the committed fixture's")

    return "EXERCISED"


def main() -> int:
    emissions = lane_replay()
    lane_falsifiers(emissions)
    live = lane_live(emissions)
    print(
        "\nDTCR-BUF denominators: "
        f"fixtures={len(emissions)} falsifier_rows={rows} live={live} failures={len(failures)}"
    )
    if failures:
        print("DTCR-BUF SELFTEST RED")
        return 2
    print("DTCR-BUF SELFTEST GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
