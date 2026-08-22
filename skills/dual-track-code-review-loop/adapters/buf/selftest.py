#!/usr/bin/env python3
"""Execute the Buf/contract-compatibility adapter against the frozen DTCR
schemas and issue #549's own falsifier list.

Four lanes:

    fixtures   the two committed fixtures are run through the two closable
               lanes -- NOT_APPLICABLE over a subject with no declared
               contract artifact, PROVIDER_UNAVAILABLE over a subject that
               declares one and finds no buf binary -- and every emitted
               result and receipt is validated against the read-only schemas
               in `../../references/schemas/`.
    falsifiers every adapter-level guard is reached through the code path
               that owns it and must be refused *by that guard*, the same
               discipline `adapters/tree-sitter/selftest.py` and
               `adapters/sqlite-ledger/selftest.py` use: a defect that dies on
               an unrelated exception proves nothing about the guard it was
               planted for.
    schema     every `x-refusal-controls` entry the two frozen schemas
               already carry is replayed generically: the baked-in instance
               must be refused at exactly the path the schema names, and a
               copy of the schema with that one keyword deleted must admit
               the same instance -- so a row that stopped discriminating
               would be caught by its own knockout, not just read as still
               green.
    live       committed receipts are checked against their paired result
               files with no provider needed (a receipt whose digest drifted
               from its result is not evidence of that result any more, and
               reads exactly like one that still is). Then the adapter runs
               for real against this tree's own HEAD: this repository
               carries no Protobuf/Buf contract artifact anywhere, so the
               live NOT_APPLICABLE lane is exercised against genuine current
               state, not a fixture standing in for it. buf's absence on this
               host is checked and reported as NOT_EXERCISED, never faked.

Exit 0 green, 2 a lane failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import os
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
RECEIPTS = ADAPTER_DIR / "receipts"

RESULT_SCHEMA_FILE = "contract-compatibility-result.schema.json"
RECEIPT_SCHEMA_FILE = "fact-plane-receipt.schema.json"

# The ten falsifiers issue #549 names, plus the three this lane's brief adds
# on top of them. `covered` is filled in as each row actually runs, and
# `main` refuses to report green if any name in this set was never planted --
# so a row silently dropped in a later edit fails loudly instead of just
# shrinking the printed count.
REQUIRED_FALSIFIERS = {
    "BUF_WRONG_BASELINE",
    "MUTABLE_BASELINE_ALIAS",
    "SOURCE_SCHEMA_DIGEST_ABSENT",
    "BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING",
    "GENERATED_ARTIFACT_USED_WITHOUT_SOURCE_BINDING",
    "BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED",
    "NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE",
    "BUF_PASS_PROMOTED_TO_DEPLOYMENT_OR_MERGE_PASS",
    "BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS",
    "STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE",
}
EXTRA_FALSIFIERS = {
    "PROTOBUF_CONTRACTS_PRESENT_BUT_CLAIMED_NOT_APPLICABLE",
    "PROVIDER_UNAVAILABLE_CLAIMED_WHILE_BINARY_PRESENT",
    "RECEIPT_DIGEST_TAMPERED",
}

failures: list[str] = []
cases = 0
covered: set[str] = set()


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


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# lane 1: fixtures
# --------------------------------------------------------------------------
def lane_fixtures() -> None:
    print("fixtures")
    result_schema = load_schema(RESULT_SCHEMA_FILE)
    receipt_schema = load_schema(RECEIPT_SCHEMA_FILE)

    no_contracts = load_fixture("no-contracts.json")
    result = A.emit_not_applicable(subject=no_contracts["subject"], declared_paths=no_contracts["declared_paths"])
    errors = validate(result, result_schema)
    if errors:
        fail(f"no-contracts: NOT_APPLICABLE result refused by the frozen schema: {errors[0].message}")
    else:
        print(f"  no-contracts.json: outcome={result['outcome']}, {len(no_contracts['declared_paths'])} declared path(s), 0 in scope")
    if result["outcome"] != "NOT_APPLICABLE" or result["findings"]:
        fail("no-contracts: expected a clean NOT_APPLICABLE with no findings")

    receipt = A.emit_receipt(
        subject=no_contracts["subject"],
        result=result,
        provider_runs=[A.applicability_provider_run(declared_paths=no_contracts["declared_paths"], applicable=False, basis=[])],
        summary="no-contracts fixture: no declared path matches the Protobuf/Buf contract glob.",
    )
    if validate(receipt, receipt_schema):
        fail("no-contracts: receipt refused by the frozen fact-plane-receipt schema")
    A.verify_receipt(receipt=receipt, result=result)

    contracts_present = load_fixture("contracts-present.json")
    applicable, basis = A.detect_applicability(contracts_present["declared_paths"])
    if not (applicable and basis == ["api/order.proto", "buf.yaml"]):
        fail(f"contracts-present: expected applicable with basis ['api/order.proto', 'buf.yaml'], got {applicable}, {basis}")
    else:
        print(f"  contracts-present.json: applicability basis={basis}")

    if A.find_cli() is None:
        pu_result = A.emit_provider_unavailable(subject=contracts_present["subject"], declared_paths=contracts_present["declared_paths"])
        if validate(pu_result, result_schema):
            fail("contracts-present: PROVIDER_UNAVAILABLE result refused by the frozen schema")
        elif pu_result["outcome"] != "PROVIDER_UNAVAILABLE" or pu_result["findings"]:
            fail("contracts-present: expected a clean PROVIDER_UNAVAILABLE with no findings")
        else:
            print(f"  contracts-present.json: outcome={pu_result['outcome']} (buf genuinely absent on this host)")
        pu_receipt = A.emit_receipt(
            subject=contracts_present["subject"],
            result=pu_result,
            provider_runs=[
                A.applicability_provider_run(declared_paths=contracts_present["declared_paths"], applicable=True, basis=basis),
                A.absent_provider_run(declared_paths=contracts_present["declared_paths"], basis=basis),
            ],
            summary="contracts-present fixture: a contract artifact is declared and no buf binary resolved.",
        )
        if validate(pu_receipt, receipt_schema):
            fail("contracts-present: receipt refused by the frozen fact-plane-receipt schema")
        A.verify_receipt(receipt=pu_receipt, result=pu_result)
    else:
        print(f"  contracts-present.json: buf resolved at {A.find_cli()} on this host; PROVIDER_UNAVAILABLE demonstration skipped here, see the falsifier lane's planted-fake-buf row for the guard proof")


# --------------------------------------------------------------------------
# lane 2: falsifiers (adapter-level)
# --------------------------------------------------------------------------
def refuses(name: str, mechanism: str, thunk: Callable[[], None]) -> None:
    global cases
    cases += 1
    covered.add(name)
    try:
        thunk()
    except A.Refusal as refusal:
        if refusal.reason != name:
            fail(f"{name}: refused, but by {refusal.reason} -- the planted defect never reached its own guard")
            return
        print(f"  {name}: refused by adapter guard ({mechanism})")
        return
    except Exception as error:  # noqa: BLE001 - any other exception is still not the named guard
        fail(f"{name}: raised {type(error).__name__} rather than its named refusal")
        return
    fail(f"{name}: the planted defect was emitted without refusal")


def with_fake_buf(script: str, thunk: Callable[[str], None]) -> None:
    """Plant an executable named `buf` and point DTCR_BUF_BIN at it, so
    `find_cli`/`cli_identity` see it exactly as they would see a real
    resolved binary, restoring the environment afterward either way."""
    work = Path(tempfile.mkdtemp(prefix="dtcr-buf-fake-"))
    fake = work / "buf"
    fake.write_text(script, encoding="utf-8")
    fake.chmod(0o755)
    original = os.environ.get("DTCR_BUF_BIN")
    os.environ["DTCR_BUF_BIN"] = str(fake)
    try:
        thunk(str(fake))
    finally:
        if original is None:
            os.environ.pop("DTCR_BUF_BIN", None)
        else:
            os.environ["DTCR_BUF_BIN"] = original
        import shutil as _shutil

        _shutil.rmtree(work, ignore_errors=True)


def lane_falsifiers() -> None:
    print("falsifiers")
    no_contracts = load_fixture("no-contracts.json")
    contracts_present = load_fixture("contracts-present.json")

    refuses(
        "MUTABLE_OR_WRONG_SOURCE_SUBJECT",
        "check_subject requires an exact 40-hex commit",
        lambda: A.check_subject({"repository_binding_id": "DTCR-RB-3749864dfe3e2f36", "commit": "main", "tree": "b" * 40}),
    )
    refuses(
        "MUTABLE_BASELINE_ALIAS",
        "resolve_baseline_commit refuses a moving name before it is ever pinned",
        lambda: A.resolve_baseline_commit("main"),
    )
    refuses(
        "SOURCE_SCHEMA_DIGEST_ABSENT",
        "require_source_bytes refuses an empty backing artifact",
        lambda: A.require_source_bytes("candidate", b""),
    )

    def config_weakened() -> None:
        strict = b"version: v1\nbreaking:\n  use:\n    - WIRE_JSON\n    - FILE\n"
        weakened = b"version: v1\nbreaking:\n  use: []\n"
        A.resolve_config(config_bytes=weakened, claimed_ruleset_digest=A.sha256_hex(strict))

    refuses(
        "BREAKING_CHANGE_BYPASSED_BY_CONFIG_WEAKENING",
        "resolve_config re-hashes the config bytes actually supplied",
        config_weakened,
    )

    refuses(
        "GENERATED_ARTIFACT_USED_WITHOUT_SOURCE_BINDING",
        "bind_candidate refuses a path outside the declared subject",
        lambda: A.bind_candidate(artifact_path="gen/order.pb.go", artifact_bytes=b"package gen", declared_paths=["api/order.proto"]),
    )

    def stale_baseline() -> None:
        current = b'syntax = "proto3";\nmessage Order { string id = 1; }\n'
        stale_claim = A.sha256_hex(b'syntax = "proto3";\nmessage Order {}\n')
        A.bind_baseline(commit="a" * 40, artifact_name="order.proto", artifact_bytes=current, claimed_digest=stale_claim)

    refuses(
        "STALE_BASELINE_REUSED_AFTER_CONTRACT_CHANGE",
        "bind_baseline re-hashes the baseline bytes actually read",
        stale_baseline,
    )

    def unresponsive_buf(binary: str) -> None:
        A.cli_identity(binary)

    with_fake_buf(
        "#!/bin/sh\nexit 1\n",
        lambda binary: refuses(
            "BUF_BINARY_AVAILABLE_PROMOTED_TO_EXERCISED",
            "cli_identity requires a usable --version, not just a resolvable path",
            lambda: unresponsive_buf(binary),
        ),
    )

    refuses(
        "NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE",
        "emit_provider_unavailable refuses when nothing is in scope to be blocked on",
        lambda: A.emit_provider_unavailable(subject=no_contracts["subject"], declared_paths=no_contracts["declared_paths"]),
    )
    refuses(
        "PROTOBUF_CONTRACTS_PRESENT_BUT_CLAIMED_NOT_APPLICABLE",
        "emit_not_applicable re-runs detect_applicability before it will claim the outcome",
        lambda: A.emit_not_applicable(subject=contracts_present["subject"], declared_paths=contracts_present["declared_paths"]),
    )

    def blocked_while_present(binary: str) -> None:
        A.emit_provider_unavailable(subject=contracts_present["subject"], declared_paths=contracts_present["declared_paths"])

    with_fake_buf(
        '#!/bin/sh\necho "1.99.0-fake"\nexit 0\n',
        lambda binary: refuses(
            "PROVIDER_UNAVAILABLE_CLAIMED_WHILE_BINARY_PRESENT",
            "emit_provider_unavailable calls find_cli itself rather than trusting the caller",
            lambda: blocked_while_present(binary),
        ),
    )

    def tampered_receipt() -> None:
        result = A.emit_not_applicable(subject=no_contracts["subject"], declared_paths=no_contracts["declared_paths"])
        receipt = A.emit_receipt(
            subject=no_contracts["subject"],
            result=result,
            provider_runs=[A.applicability_provider_run(declared_paths=no_contracts["declared_paths"], applicable=False, basis=[])],
            summary="tamper probe",
        )
        tampered = copy.deepcopy(receipt)
        tampered["bundle_digest"] = "0" * 64
        A.verify_receipt(receipt=tampered, result=result)

    refuses(
        "RECEIPT_DIGEST_TAMPERED",
        "verify_receipt recomputes the digest of the result rather than trusting the stored field",
        tampered_receipt,
    )


# --------------------------------------------------------------------------
# lane 3: schema (generic x-refusal-controls replay)
# --------------------------------------------------------------------------
# `refused_by` in the schema's own metadata names where the guard is
# *authored*. For a plain keyword that is also where the validator reports
# it, but a conditional's consequence (`allOf[i].then`) is reported one or
# more leaf keywords deeper inside that `then`, and a keyword that lives
# behind a `$ref` (provider_run's `$defs` entry, reused under
# `provider_runs.items`) is reported through the referring property instead
# of through `$defs`. Where the two differ, the override below carries both:
# the prefix the validator actually reports, and the path the keyword is
# authored at, which is where the knockout has to cut.
SCHEMA_CONTROL_OVERRIDES: dict[str, tuple[str, str]] = {
    "DTCR-XC-FR-003": ("properties.provider_runs.items.allOf[0].then", "$defs.provider_run.allOf[0].then"),
}


def run_schema_controls(schema_file: str, schema: dict[str, Any], name_by_case: dict[str, str]) -> int:
    rows = 0
    for control in schema.get("x-refusal-controls", []):
        rows += 1
        case_id = control["case_id"]
        instance = control["instance"]
        refused_by = control["refused_by"]
        match_prefix, knockout_at = SCHEMA_CONTROL_OVERRIDES.get(case_id, (refused_by, refused_by))
        errors = validate(instance, schema)
        paths = {schema_path_of(error) for error in errors}
        label = name_by_case.get(case_id, case_id)
        matched = any(path == match_prefix or path.startswith(match_prefix + ".") or path.startswith(match_prefix + "[") for path in paths)
        if not matched:
            fail(f"{schema_file}#{case_id}: refused by {sorted(paths)}, not under the named guard {match_prefix}")
            continue
        mutated = knockout(schema, knockout_at)
        if validate(instance, mutated):
            fail(f"{schema_file}#{case_id}: still refused after {knockout_at} was removed, so that keyword is not what refuses it")
            continue
        if case_id in name_by_case:
            covered.add(name_by_case[case_id])
        print(f"  {label} ({schema_file}#{case_id}): refused by {match_prefix}, admitted once {knockout_at} was knocked out")
    return rows


def lane_schema() -> int:
    print("schema")
    result_schema = load_schema(RESULT_SCHEMA_FILE)
    receipt_schema = load_schema(RECEIPT_SCHEMA_FILE)
    rows = 0
    rows += run_schema_controls(
        RESULT_SCHEMA_FILE,
        result_schema,
        {
            "DTCR-XC-CK-001": "BUF_WRONG_BASELINE",
            "DTCR-XC-CK-002": "CLEAN_VERDICT_WITH_BREAKING_FINDING (bonus)",
            "DTCR-XC-CK-003": "BUF_PASS_PROMOTED_TO_DEPLOYMENT_OR_MERGE_PASS",
            "DTCR-XC-CK-004": "NOT_APPLICABLE_WITH_UNWARRANTED_FINDINGS (bonus)",
        },
    )
    rows += run_schema_controls(
        RECEIPT_SCHEMA_FILE,
        receipt_schema,
        {
            "DTCR-XC-FR-001": "PROVIDER_PASS_PROMOTED_TO_TASK_PASS (bonus)",
            "DTCR-XC-FR-002": "LEDGER_EVENT_MUTABLE_POINTER (bonus)",
            "DTCR-XC-FR-003": "PROVIDER_RUN_PASS_WITHOUT_EXIT_CODE (bonus)",
            "DTCR-XC-FR-004": "RECEIPT_SUMMARY_OVERCLAIM (bonus)",
            "DTCR-XC-FR-005": "LEDGER_EVENT_ADDITIONAL_MUTABLE_POINTER (bonus)",
        },
    )

    # BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS has no baked-in x-refusal-
    # controls entry in the frozen schema (BSR is out of scope for this
    # deterministic adapter), so this row is authored the same way the two
    # sibling adapters author their own schema-side plants: mutate a real,
    # valid instance by exactly the one keyword it is meant to prove, then
    # knock that keyword out and require it to be admitted.
    global cases
    cases += 1
    covered.add("BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS")
    clean = copy.deepcopy(result_schema["examples"][0])
    clean["outcome"] = "NO_BREAKING_CHANGE_DETECTED"
    clean["findings"] = []
    clean["grants"]["registry_access_content_rights"] = True
    errors = validate(clean, result_schema)
    paths = {schema_path_of(error) for error in errors}
    target = "properties.grants.additionalProperties"
    if target not in paths:
        fail(f"BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS: refused by {sorted(paths)}, not by the named guard {target}")
    elif validate(clean, knockout(result_schema, target)):
        fail(f"BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS: still refused after {target} was removed")
    else:
        rows += 1
        print(f"  BSR_ACCOUNT_ACCESS_PROMOTED_TO_CONTENT_RIGHTS ({RESULT_SCHEMA_FILE}): refused by {target}, admitted once knocked out")
    return rows


# --------------------------------------------------------------------------
# lane 4: live
# --------------------------------------------------------------------------
def lane_live() -> str:
    print("live")
    result_schema = load_schema(RESULT_SCHEMA_FILE)
    receipt_schema = load_schema(RECEIPT_SCHEMA_FILE)

    receipts = sorted(RECEIPTS.glob("*-receipt.json")) if RECEIPTS.is_dir() else []
    for receipt_path in receipts:
        result_path = receipt_path.parent / receipt_path.name.replace("-receipt.json", "-result.json")
        if not result_path.is_file():
            fail(f"{receipt_path.name}: no paired {result_path.name} committed beside it")
            continue
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if validate(result, result_schema):
            fail(f"{result_path.name}: does not validate against the frozen result schema")
        if validate(receipt, receipt_schema):
            fail(f"{receipt_path.name}: does not validate against the frozen receipt schema")
        try:
            A.verify_receipt(receipt=receipt, result=result)
            print(f"  {receipt_path.name}: digest binds the committed {result_path.name} (checked without any provider)")
        except A.Refusal as refusal:
            fail(f"{receipt_path.name}: {refusal}")

    repo = Path(A.git(ADAPTER_DIR, "rev-parse", "--show-toplevel"))
    try:
        bundle = A.run_check(repo=repo, paths=None)
    except A.Unusable as unusable:
        print(f"  NOT_EXERCISED: {unusable}")
        return "NOT_EXERCISED (buf present, exercised lane not implemented)"

    result, receipt = bundle["result"], bundle["receipt"]
    if validate(result, result_schema):
        fail("live: the real-repo result does not validate against the frozen schema")
    if validate(receipt, receipt_schema):
        fail("live: the real-repo receipt does not validate against the frozen schema")
    print(
        f"  ran the deterministic applicability scan over {len(bundle['declared_paths'])} tracked "
        f"path(s) at {result['subject']['commit'][:12]}: outcome={result['outcome']}"
    )
    if result["outcome"] == "NOT_APPLICABLE" and bundle["basis"]:
        fail("live: NOT_APPLICABLE reported alongside a non-empty applicability basis")
    if result["outcome"] != "NOT_APPLICABLE":
        print(f"  note: this tree now declares a Protobuf/Buf contract artifact ({bundle['basis']}); outcome tracked it, not a failure")

    binary = A.find_cli()
    if binary is None:
        print("  NOT_EXERCISED: no buf executable on DTCR_BUF_BIN or PATH; identity is not probed for real")
        return "NOT_EXERCISED (buf absent)"
    identity = A.cli_identity(binary)
    print(f"  identify: real buf resolved at {binary}, version {identity['version']}")
    return "EXERCISED (identify only, no breaking-change invocation on this host)"


def main() -> int:
    lane_fixtures()
    lane_falsifiers()
    schema_rows = lane_schema()
    live = lane_live()

    missing = (REQUIRED_FALSIFIERS | EXTRA_FALSIFIERS) - covered
    if missing:
        fail(f"falsifiers required by this lane were never planted: {sorted(missing)}")

    print(
        "\nDTCR-BUF denominators: "
        f"cases={cases} schema_rows={schema_rows} "
        f"required_falsifiers_covered={len(REQUIRED_FALSIFIERS & covered)}/{len(REQUIRED_FALSIFIERS)} "
        f"extra_falsifiers_covered={len(EXTRA_FALSIFIERS & covered)}/{len(EXTRA_FALSIFIERS)} "
        f"live={live} failures={len(failures)}"
    )
    if failures:
        print("DTCR-BUF SELFTEST RED")
        return 2
    print("DTCR-BUF SELFTEST GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
