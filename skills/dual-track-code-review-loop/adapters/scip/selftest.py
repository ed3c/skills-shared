#!/usr/bin/env python3
"""Execute the SCIP adapter against the frozen DTCR schemas.

Three lanes, and the numbers each one counts are printed so a run can never
report a green it did not measure:

    replay     every fixture under `fixtures/` is emitted from a recorded
               `index.scip` -- the bytes a real `scip-python` run wrote --
               with no indexer on the machine, and every emitted symbol fact,
               exact source subject, coverage ceiling and fact-plane receipt is
               validated against the read-only schemas in
               `../../references/schemas/`.
    falsifiers each of the ten refusal codes issue #547 names is planted and
               must be refused *by its own guard*. A defect that dies on an
               unrelated `required` proves nothing about the guard it was
               written for, so every row asserts `refusal.reason` equals the
               code it planted. Schema-side rows also perform a knockout:
               delete exactly the keyword the row names from a copy of the
               schema, change nothing else, and require the mutated instance to
               validate. A control still refused after its own guard is gone is
               refused by something else and the row naming it is wrong.
    live       the committed receipt is checked against this tree with no
               provider needed, because a receipt whose digests drifted
               describes a run over sources that are no longer here and reads
               exactly like one that still matches. The absent-provider path is
               then exercised on purpose -- `DTCR_SCIP_BIN` pointed at nothing
               -- and must exit 70 as NOT_EXERCISED rather than 2 as a failure.
               Finally, if the indexer is on the host, the adapter runs it for
               real against the current HEAD and must reproduce what the receipt
               recorded once the subject and the host-local index digest are
               factored out. A missing indexer is start-readiness, not a
               failure: the lane prints NOT_EXERCISED, stays green, and says
               plainly that what it could not check is whether the run
               reproduces.

Exit 0 green, 2 a lane failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "DTCR-SCIP-SELFTEST-UNUSABLE: jsonschema is required. This suite executes the frozen "
        "schemas as deciding gates; skipping them would report the same green as running them.",
        file=sys.stderr,
    )
    raise SystemExit(70)

ADAPTER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ADAPTER_DIR))
import adapter as A  # noqa: E402

SCHEMAS = A.SCHEMAS
FIXTURES = ADAPTER_DIR / "fixtures"
RECORDED = FIXTURES / "recorded"
PACKAGE = FIXTURES / "python-package"
RECEIPTS = ADAPTER_DIR / "receipts"

SUBJECT_SCHEMA = "dtcr/exact-source-subject/v1"
SCHEMA_BY_ID = {
    A.FACT_SCHEMA: "symbol-fact.schema.json",
    SUBJECT_SCHEMA: "exact-source-subject.schema.json",
    A.CEILING_SCHEMA: "coverage-ceiling.schema.json",
    A.RECEIPT_SCHEMA: "fact-plane-receipt.schema.json",
}
# The fifth schema the issue's input list names. It states which module may
# depend on which; a symbol/occurrence importer neither produces nor consumes
# one, and emitting a fabricated invariant to make a checklist go green would
# be the exact overclaim the rest of this file exists to refuse.
ARCHITECTURE_INVARIANT_STATE = (
    "NOT_APPLICABLE: architecture-invariant.schema.json records a layering rule between modules. "
    "This adapter emits index facts and a coverage ceiling and asserts no layering rule, so it "
    "produces no instance of that class and validates none."
)

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


def records_of(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return bundle["facts"] + [bundle["exact_source_subject"], bundle["coverage_ceiling"], bundle["receipt"]]


# --------------------------------------------------------------------------
# lane 1: replay
# --------------------------------------------------------------------------
def lane_replay() -> tuple[dict[str, dict[str, Any]], int, int]:
    print("replay")
    bundles: dict[str, dict[str, Any]] = {}
    validations = 0
    facts = 0
    requests = sorted(FIXTURES.glob("*/request.json"))
    if not requests:
        fail("no fixture requests on the tree; the replay lane would be green over nothing")
    for request in requests:
        name = request.parent.name
        emitted = A.run_replay(request)
        bundles[name] = emitted
        for record in records_of(emitted):
            errors = validate(record, load_schema(SCHEMA_BY_ID[record["schema"]]))
            validations += 1
            if errors:
                fail(f"{name}: {record['schema']} refused by the frozen schema: {errors[0].message}")
        facts += len(emitted["facts"])
        kinds = {kind: sum(1 for f in emitted["facts"] if f["fact_kind"] == kind) for kind in ("SYMBOL", "OCCURRENCE", "RELATIONSHIP")}
        ceiling = emitted["coverage_ceiling"]
        print(
            f"  {name}: {kinds['SYMBOL']} symbols, {kinds['OCCURRENCE']} occurrences, "
            f"{kinds['RELATIONSHIP']} edges, {ceiling['analysed']['numerator']}/"
            f"{ceiling['analysed']['denominator']} declared blobs indexed, "
            f"completeness={ceiling['completeness']}, "
            f"{len(emitted['index_summary']['unresolved_symbols'])} unresolved of "
            f"{emitted['index_summary']['referenced_symbols']} referenced"
        )

        # Every edge is a lower bound, and the provider resolved none of them.
        for fact in emitted["facts"]:
            if any(fact["establishes"].values()):
                fail(f"{name}: {fact['fact_id']} promoted an establishes constant")
            if not fact["omissions"]:
                fail(f"{name}: {fact['fact_id']} carries an empty omission list, which claims nothing was skipped")
            if fact["fact_kind"] == "RELATIONSHIP":
                evidence = fact["relationship"]["graph_evidence"]
                if evidence["provenance"] != "OCCURRENCE_ENCLOSING_RANGE_HEURISTIC":
                    fail(f"{name}: {fact['fact_id']} claims provenance {evidence['provenance']}")
                if evidence["completeness"] != "PARTIAL_LOWER_BOUND":
                    fail(f"{name}: {fact['fact_id']} is an inferred edge recorded as {evidence['completeness']}")
                if fact["relationship"]["relationship_kind"] == "CALLS":
                    fail(f"{name}: {fact['fact_id']} calls a range-nesting edge a call")
        if emitted["index_summary"]["provider_relationships"]:
            fail(f"{name}: the provider emitted relationships this adapter never reads")
        if not emitted["index_summary"]["unresolved_symbols"]:
            fail(
                f"{name}: the unresolved denominator is zero, so nothing in this fixture exercises "
                "the code path that reports unresolved symbols and the number is untested"
            )

        # The digest has to cover the row it is attached to, and two emissions
        # of one fixture have to be the same bytes -- otherwise every digest
        # downstream is a digest of when the pass ran.
        first = emitted["facts"][0]
        if A.sha256_hex(A.canonical({k: v for k, v in first.items() if k != "output_digest"})) != first["output_digest"]:
            fail(f"{name}: output_digest does not cover the record it is attached to")
        if A.canonical(A.run_replay(request)) != A.canonical(emitted):
            fail(f"{name}: two emissions of one fixture differ; the output is not deterministic")
    return bundles, validations, facts


# --------------------------------------------------------------------------
# lane 2: falsifiers
# --------------------------------------------------------------------------
def mutated_tree(mutate: Callable[[Path], None]) -> Path:
    work = Path(tempfile.mkdtemp(prefix="dtcr-scip-")) / "scip"
    shutil.copytree(ADAPTER_DIR, work, ignore=shutil.ignore_patterns("__pycache__"))
    mutate(work)
    return work


def expect_adapter_refusal(name: str, mutate: Callable[[Path], None], fixture: str = "recorded") -> bool:
    """Plant the defect in a copy of this adapter's own tree, replay it, and
    require the refusal to carry the planted code."""
    work = mutated_tree(mutate)
    try:
        A.run_replay(work / "fixtures" / fixture / "request.json")
    except A.Refusal as refusal:
        if refusal.reason != name:
            fail(f"{name}: refused, but by {refusal.reason} -- the planted defect never reached its own guard")
            return False
        print(f"  {name}: refused by adapter guard {refusal.reason}")
        return True
    except Exception as error:  # noqa: BLE001 - any other exception is still not the named guard
        fail(f"{name}: raised {type(error).__name__} rather than its named refusal")
        return False
    finally:
        shutil.rmtree(work.parent, ignore_errors=True)
    fail(f"{name}: the planted defect was emitted without refusal")
    return False


def expect_guard_refusal(name: str, guard: Callable[[], None]) -> bool:
    """The post-condition half. These guards run over what was already emitted,
    so the plant is a mutation of the emitted artifact rather than of the input,
    and the guard is called directly on it."""
    try:
        guard()
    except A.Refusal as refusal:
        if refusal.reason != name:
            fail(f"{name}: refused, but by {refusal.reason} -- the planted defect never reached its own guard")
            return False
        print(f"  {name}: refused by adapter guard {refusal.reason}")
        return True
    except Exception as error:  # noqa: BLE001
        fail(f"{name}: raised {type(error).__name__} rather than its named refusal")
        return False
    fail(f"{name}: the planted defect passed the guard without refusal")
    return False


def expect_schema_refusal(
    name: str,
    schema_file: str,
    instance: dict[str, Any],
    keyword: str,
    knockout_at: str | None = None,
) -> bool:
    """`keyword` is the guard as the validator reports it. `knockout_at` is
    where that guard is written when the two differ, which they do behind a
    `$ref`: the error names the path through the referring property and the
    keyword itself lives once, under `$defs`."""
    schema = load_schema(schema_file)
    errors = validate(instance, schema)
    if not errors:
        fail(f"{name}: the frozen schema admitted the planted defect")
        return False
    paths = {schema_path_of(error) for error in errors}
    if keyword not in paths:
        fail(f"{name}: refused by {sorted(paths)}, not by the named guard {keyword}")
        return False
    if len(paths) > 1:
        fail(f"{name}: refused by more than the named guard ({sorted(paths)}); the row is not discriminating")
        return False
    where = knockout_at or keyword
    if validate(instance, knockout(schema, where)):
        fail(f"{name}: still refused after {where} was removed, so that keyword is not what refuses it")
        return False
    print(f"  {name}: refused by {schema_file}#{keyword}, admitted once {where} is knocked out")
    return True


def edit_json(path: Path, mutate: Callable[[dict[str, Any]], None]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def without(record: dict[str, Any], *path: str) -> dict[str, Any]:
    out = copy.deepcopy(record)
    node = out
    for key in path[:-1]:
        node = node[key]
    del node[path[-1]]
    return out


def with_value(record: dict[str, Any], value: Any, *path: str) -> dict[str, Any]:
    out = copy.deepcopy(record)
    node = out
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return out


def lane_falsifiers(bundles: dict[str, dict[str, Any]]) -> int:
    print("falsifiers")
    clean = bundles["recorded"]
    ceiling = clean["coverage_ceiling"]
    referenced = clean["index_summary"]["referenced_symbols"]
    unresolved = len(clean["index_summary"]["unresolved_symbols"])
    edge = next(fact for fact in clean["facts"] if fact["fact_kind"] == "RELATIONSHIP")
    symbol = next(fact for fact in clean["facts"] if fact["fact_kind"] == "SYMBOL")
    rows = 0

    # ---- input guards: the defect is in what the adapter was handed --------
    def mutable_subject(work: Path) -> None:
        edit_json(
            work / "fixtures" / "recorded" / "request.json",
            lambda data: data["subject"].update({"commit": "main"}),
        )

    def strip_index_digest(work: Path) -> None:
        edit_json(
            work / "fixtures" / "recorded" / "request.json",
            lambda data: data["provider"].pop("index_sha256"),
        )

    def unbind_version(work: Path) -> None:
        edit_json(
            work / "fixtures" / "recorded" / "request.json",
            lambda data: data["provider"].update({"version": ""}),
        )

    def edit_source_after_indexing(work: Path) -> None:
        """The literal shape of the falsifier: the source moves on, the index
        stays behind, and the request still declares the blob the indexer read."""
        target = work / "fixtures" / "python-package" / "dtcr_fixture" / "core.py"
        target.write_bytes(target.read_bytes() + b"\n\nEXTRA = 1\n")

    def metadata_only_index(work: Path) -> None:
        """Reproduce the provider trap exactly: an index carrying Metadata and
        no Document at all, which is what scip-python writes -- exit 0, no
        warning -- when --cwd reaches the project through a symlink."""
        path = work / "fixtures" / "recorded" / "index.scip"
        metadata = next(value for number, _wire, value in A.wire_fields(path.read_bytes()) if number == 1)
        truncated = bytes([1 << 3 | 2]) + varint(len(metadata)) + bytes(metadata)
        path.write_bytes(truncated)
        edit_json(
            work / "fixtures" / "recorded" / "request.json",
            lambda data: data["provider"].update({"index_sha256": A.sha256_hex(truncated)}),
        )

    def rename_an_indexed_identifier(work: Path) -> None:
        """Same byte length, so every recorded range still lands inside the
        blob and still decodes. Only the text at the offsets changes, which is
        the one failure a well-formed range cannot show on its own."""
        target = work / "fixtures" / "python-package" / "dtcr_fixture" / "core.py"
        text = target.read_bytes().replace(b"def surcharge(", b"def surchargX(", 1)
        target.write_bytes(text)
        edit_json(
            work / "fixtures" / "recorded" / "request.json",
            lambda data: data["documents"]["dtcr_fixture/core.py"].update({"blob": A.git_blob_sha1(text)}),
        )

    adapter_rows = [
        ("SCIP_INDEX_WRONG_SUBJECT", mutable_subject),
        ("SCIP_INDEX_DIGEST_ABSENT", strip_index_digest),
        ("INDEXER_VERSION_OR_CONFIG_UNBOUND", unbind_version),
        ("STALE_INDEX_REUSED_AFTER_SOURCE_CHANGE", edit_source_after_indexing),
        ("SCIP_INDEX_EMPTY_OVER_DECLARED_SUBJECT", metadata_only_index),
        ("OCCURRENCE_RANGE_OUT_OF_SOURCE", rename_an_indexed_identifier),
    ]
    for name, mutate in adapter_rows:
        rows += 1
        expect_adapter_refusal(name, mutate)

    # ---- post-condition guards: the defect is in what was emitted ----------
    guard_rows = [
        (
            "PARTIAL_COVERAGE_PROMOTED_TO_COMPLETE",
            lambda: A.guard_ceiling(
                with_value(ceiling, "COMPLETE_FOR_ANALYSED_INPUTS", "completeness"), unresolved, referenced
            ),
        ),
        (
            "UNRESOLVED_SYMBOL_OMITTED_FROM_DENOMINATOR",
            lambda: A.guard_ceiling(
                with_value(
                    ceiling,
                    [w for w in ceiling["warnings"] if "unresolved denominator" not in w],
                    "warnings",
                ),
                unresolved,
                referenced,
            ),
        ),
        (
            "OCCURRENCE_NESTING_PROMOTED_TO_CALL_GRAPH",
            lambda: A.guard_relationships([with_value(edge, "CALLS", "relationship", "relationship_kind")]),
        ),
        (
            "RELATIONSHIP_WITHOUT_SOURCE_RANGE",
            lambda: A.guard_relationships([without(edge, "occurrence")]),
        ),
        (
            "PROVIDER_ID_PROMOTED_TO_UNIVERSAL_ID",
            lambda: A.guard_identities(
                [with_value(symbol, symbol["symbol"]["identity"]["provider_scoped_id"], "symbol", "identity")]
            ),
        ),
        (
            "SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS",
            lambda: A.guard_receipt(with_value(clean["receipt"], True, "grants", "task_pass")),
        ),
    ]
    for name, guard in guard_rows:
        rows += 1
        expect_guard_refusal(name, guard)

    # ---- the frozen schemas, refusing the same classes independently -------
    schema_rows = [
        (
            "PROVIDER_ID_PROMOTED_TO_UNIVERSAL_ID (schema half)",
            "symbol-fact.schema.json",
            with_value(symbol, symbol["symbol"]["identity"]["provider_scoped_id"], "symbol", "identity"),
            "properties.symbol.properties.identity.type",
            "$defs.provider_scoped_identity.type",
        ),
        (
            "SCIP_INDEX_WRONG_SUBJECT (schema half)",
            "symbol-fact.schema.json",
            without(symbol, "index_binding", "indexed_commit"),
            "properties.index_binding.required",
        ),
        (
            "OCCURRENCE_NESTING_PROMOTED_TO_CALL_GRAPH (schema half)",
            "symbol-fact.schema.json",
            with_value(edge, "COMPLETE_FOR_RESOLVED_EDGES", "relationship", "graph_evidence", "completeness"),
            "properties.relationship.allOf[0].then.properties.graph_evidence.properties.completeness.enum",
            "$defs.relationship_record.allOf[0].then.properties.graph_evidence.properties.completeness.enum",
        ),
        (
            "SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS (fact half)",
            "symbol-fact.schema.json",
            with_value(symbol, True, "establishes", "complete_call_graph"),
            "properties.establishes.properties.complete_call_graph.const",
        ),
        (
            "PARTIAL_COVERAGE_PROMOTED_TO_COMPLETE (schema half)",
            "coverage-ceiling.schema.json",
            with_value(ceiling, "COMPLETE_FOR_ANALYSED_INPUTS", "completeness"),
            "allOf[0].then.properties.completeness.enum",
        ),
        (
            "UNANALYSED_INPUTS_CLEARED",
            "coverage-ceiling.schema.json",
            with_value(ceiling, True, "authority_ceiling", "unanalysed_inputs_cleared"),
            "properties.authority_ceiling.properties.unanalysed_inputs_cleared.const",
        ),
        (
            "SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS (receipt half)",
            "fact-plane-receipt.schema.json",
            with_value(clean["receipt"], True, "grants", "task_pass"),
            "properties.grants.properties.task_pass.const",
        ),
        (
            "SCIP_INDEX_WRONG_SUBJECT (subject half)",
            "exact-source-subject.schema.json",
            with_value(clean["exact_source_subject"], "main", "commit"),
            "properties.commit.pattern",
        ),
    ]
    for row in schema_rows:
        rows += 1
        expect_schema_refusal(*row)
    return rows


# --------------------------------------------------------------------------
# lane 3: live
# --------------------------------------------------------------------------
def check_receipt_offline(receipt: dict[str, Any], name: str, bundle: dict[str, Any]) -> None:
    """What a committed live receipt must hold with no indexer on the machine.

    It cannot prove the run happened -- only the run proves that -- but it can
    prove the receipt is about the sources and the recorded index this tree
    carries. A receipt whose digests drifted describes a run over bytes that are
    no longer here, and it reads exactly like one that still matches."""
    for key in ("subject_blobs", "facts_digest_modulo_subject", "establishes", "coverage_ceiling_omissions"):
        if key not in receipt:
            fail(f"{name}: no {key}; a receipt this suite cannot compare against a run is not evidence")
            return
    recorded = json.loads((RECORDED / "request.json").read_text(encoding="utf-8"))
    if receipt["index"]["index_digest"] != recorded["provider"]["index_sha256"]:
        fail(f"{name}: the receipt's index digest is not the index committed under fixtures/recorded")
    expected = {
        entry["path"]: entry["blob"]
        for entry in bundle["exact_source_subject"]["blobs"]
    }
    if receipt["subject_blobs"] != expected:
        fail(f"{name}: records different subject blobs than the recorded fixture declares")
    if receipt["facts_digest_modulo_subject"] != A.facts_digest_modulo_subject(bundle["facts"]):
        fail(
            f"{name}: replaying the committed index does not reproduce the digest the receipt recorded; "
            "the receipt and the fixture are no longer about the same run"
        )
    if not A.HEX40.match(receipt["subject"]["commit"]):
        fail(f"{name}: subject.commit is not an exact commit")
    if any(receipt["establishes"].values()):
        fail(f"{name}: a live provider run recorded itself as establishing something")
    if receipt["completeness"] != "PARTIAL_LOWER_BOUND" or not receipt["coverage_ceiling_omissions"]:
        fail(f"{name}: a python-only, edge-derived run recorded itself without a ceiling")


def check_absent_provider_path(repo: Path) -> None:
    """A provider that is not installed is start-readiness, not a failure. The
    contract is an exit code, so it is proven by reading one, not by asserting
    the sentence."""
    previous = os.environ.get("DTCR_SCIP_BIN")
    os.environ["DTCR_SCIP_BIN"] = str(ADAPTER_DIR / "no-such-scip-python")
    try:
        if A.find_cli() is not None:
            fail("absent-provider control: find_cli resolved a binary that is not there")
            return
        code = A.main(["live", "--package", str(PACKAGE), "--repo", str(repo), "--out", os.devnull])
    finally:
        if previous is None:
            del os.environ["DTCR_SCIP_BIN"]
        else:
            os.environ["DTCR_SCIP_BIN"] = previous
    if code != 70:
        fail(f"absent-provider control: exit {code}, not 70; an uninstalled indexer read as a result")
        return
    print("  absent-provider control: exit 70 NOT_EXERCISED, not 2 REFUSED and not 0")


def lane_live(bundle: dict[str, Any]) -> str:
    print("live")
    repo = Path(A.git(ADAPTER_DIR, "rev-parse", "--show-toplevel"))
    receipts = sorted(RECEIPTS.glob("*.json")) if RECEIPTS.is_dir() else []
    if not receipts:
        fail("no committed live receipt; #547 refuses a fixture-only pass and this lane would be vacuous")
    for path in receipts:
        check_receipt_offline(json.loads(path.read_text(encoding="utf-8")), path.name, bundle)
        print(f"  {path.name}: digests bind the committed index and sources (checked without the provider)")

    check_absent_provider_path(repo)

    if A.find_cli() is None:
        print(
            "  NOT_EXERCISED: no scip-python on PATH and DTCR_SCIP_BIN unset. A missing provider is "
            "start-readiness, not a failure. Unchecked here: whether a live run reproduces the receipt."
        )
        return "NOT_EXERCISED"

    try:
        emitted = A.run_live(repo=repo, package_dir=PACKAGE, omissions=[], warnings=[])
    except A.Refusal as refusal:
        fail(f"live run refused: {refusal}")
        return "FAILED"

    run = emitted["receipt"]["provider_runs"][0]
    print(
        f"  ran scip-python {run['version']} over "
        f"{emitted['coverage_ceiling']['analysed']['numerator']} blobs at "
        f"{emitted['receipt']['subject']['commit'][:12]}: {len(emitted['facts'])} facts, exit {run['exit_code']}"
    )
    for record in records_of(emitted):
        if validate(record, load_schema(SCHEMA_BY_ID[record["schema"]])):
            fail(f"live: {record['schema']} does not validate against the frozen schema")

    observed = A.facts_digest_modulo_subject(emitted["facts"])
    for path in receipts:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        for key, seen in (
            ("version", run["version"]),
            ("indexer_sha256", run["executable_sha256"]),
            ("config_digest", run["config_digest"]),
            ("provider_binding_id", run["provider_binding_id"]),
        ):
            if receipt["provider"][key] != seen:
                fail(f"live: {path.name} records {key}={receipt['provider'][key]}, this host observed {seen}")
        if receipt["facts_digest_modulo_subject"] != observed:
            fail(
                f"live: {path.name} and this host disagree on what the same indexer, config and bytes "
                "determine; one of the two identities is not what it says"
            )
        else:
            print(f"  {path.name}: this host reproduces the recorded emission over the same sources")
        if receipt["index"]["index_digest"] == emitted["facts"][0]["index_binding"]["index_digest"]:
            fail(
                f"live: {path.name} reports the same index digest as a run from a different directory; "
                "the digest was supposed to carry the machine-local project root and does not"
            )
    return "EXERCISED"


def main() -> int:
    bundles, validations, facts = lane_replay()
    rows = lane_falsifiers(bundles) if bundles else 0
    live = lane_live(bundles["recorded"]) if "recorded" in bundles else "FAILED"
    print(f"\n  architecture-invariant: {ARCHITECTURE_INVARIANT_STATE}")
    print(
        "\nDTCR-SCIP denominators: "
        f"fixtures={len(bundles)} facts={facts} schema_validations={validations} "
        f"falsifier_rows={rows} live={live} failures={len(failures)}"
    )
    if failures:
        print("DTCR-SCIP SELFTEST RED")
        return 2
    print("DTCR_SCIP_ADAPTER_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
