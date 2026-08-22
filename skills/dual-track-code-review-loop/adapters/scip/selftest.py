#!/usr/bin/env python3
"""Execute the SCIP adapter against the frozen DTCR schemas.

Five lanes, and the numbers each one counts are printed so a run can never
report a green it did not measure:

    replay      the committed `.scip` bytes -- the byte-for-byte output of a
                real `scip-python` run against the committed subject -- are
                decoded with no indexer on the machine, and every emitted
                symbol, occurrence, relationship, coverage ceiling and
                fact-plane receipt is validated against the read-only schemas
                in `../../references/schemas/`.
    falsifiers  every defect named by issue #547 is planted and must be refused
                *by the guard that owns it*. A defect that dies on an unrelated
                `required` proves nothing, so each schema-side row also performs
                a knockout: delete exactly the keyword the row names from a copy
                of the schema, change nothing else, and require the mutated
                instance to validate. A control still refused after its own
                guard is gone is refused by something else and the row naming it
                is wrong. Six of the ten are planted twice, once in the adapter
                and once against the frozen schema, because two independent
                refusals are what stops one of them being the only thing between
                the defect and a green run.
    crosscheck  the same index bytes are decoded a second time through
                protoc-compiled descriptors of the SCIP schema, and the two
                decoders must agree on tool identity, document paths, symbol
                strings, ranges and roles. The adapter's reader is hand-written
                against the wire format because no `scip` CLI exists here; this
                is where a mistake in it can show up somewhere other than in its
                own output. No protobuf runtime on the machine is
                NOT_EXERCISED, not a pass.
    live        the committed receipt is first checked against this tree with no
                indexer needed, because a receipt whose digests drifted
                describes an index that is no longer here and reads exactly like
                one that still matches. Then, if `scip-python` is on the host,
                the indexer runs for real against the current HEAD and must
                reproduce what the receipt recorded once the one absolute path
                inside a SCIP index is factored out. A missing indexer is
                start-readiness: the lane prints NOT_EXERCISED, stays green, and
                says plainly that what it could not check is whether the run
                reproduces.
    leak-scan   every file this directory commits is read as bytes and must
                carry no machine-local locator outside a short list of declared
                literals. Binaries included, because the finding this lane was
                added for was an absolute home path with an account name and a
                checkout id inside the committed `.scip` fixture, which the
                repository's own scan never saw: that scan reads `references/`
                only, and reads it as text. The lane plants the shape into a
                throwaway copy first and prints the finding, so a green here is
                a scan that was shown to go red.

Exit 0 green, 2 a lane failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import shutil
import subprocess
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
RECEIPTS = ADAPTER_DIR / "receipts"
BINDINGS = ADAPTER_DIR / "bindings"

SCHEMA_BY_ID = {
    A.FACT_SCHEMA: "symbol-fact.schema.json",
    A.CEILING_SCHEMA: "coverage-ceiling.schema.json",
    A.RECEIPT_SCHEMA: "fact-plane-receipt.schema.json",
}

failures: list[str] = []
_loaded = 0

# --------------------------------------------------------------------------
# the leak-scan law, turned on this adapter's own bytes
# --------------------------------------------------------------------------
# The same shapes the repository suite runs over `references/`
# (tests/selftest.py LOCATOR_SHAPES), plus the checkout-id shape, and run over
# bytes rather than decoded text. Both differences are what this lane is for:
# the repository scan reads `references/` only and reads it as text, and the
# locator that got through was a machine-local URI inside a committed protobuf
# fixture in this directory -- a subject that scan never opened, in a form it
# could not have read.
LEAK_SHAPES = re.compile(rb"/Users/|~/|Downloads|drive\.google|file://|\.claude/worktrees")

# The probe this lane plants to prove it can go red, assembled from pieces that
# each carry no shape on their own. Assembled rather than written out because a
# probe spelled in full here would have to be exempted from the scan of this
# very file, and an exempted probe proves the exemption rather than the scan.
# Join it back into one literal and this file's own scan turns red, which is the
# intended failure.
RED_PROOF_LOCATOR = b"file:" + b"///" + b"Users/example/checkout/" + b".claude" + b"/worktrees/wf_0/src"

# Byte sequences admitted, longest first so a specific literal is consumed
# before a shorter one inside it. Literals, not shapes: a class-shaped exemption
# ("anything in a warning field") would swallow a real locator written into a
# warning. A reword that breaks one of these turns this lane red and asks a
# person to re-adjudicate it, which is the law working.
PERMITTED_LOCATORS = (
    (LEAK_SHAPES.pattern, "this lane's own guard, written once in this file"),
    (
        A.NEUTRAL_PROJECT_ROOT_PREFIX.encode("utf-8"),
        "the declared neutral project_root scheme; it names no account, no host and no checkout",
    ),
)


def scrub(data: bytes) -> bytes:
    for permitted, _why in PERMITTED_LOCATORS:
        data = data.replace(permitted, b"")
    return data


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
        for record in emitted["facts"] + [emitted["coverage_ceiling"], emitted["receipt"]]:
            errors = validate(record, load_schema(SCHEMA_BY_ID[record["schema"]]))
            validations += 1
            if errors:
                fail(f"{name}: {record['schema']} refused by the frozen schema: {errors[0].message}")
        facts += len(emitted["facts"])
        counts = {
            kind: sum(1 for r in emitted["facts"] if r["fact_kind"] == kind)
            for kind in ("SYMBOL", "OCCURRENCE", "RELATIONSHIP")
        }
        ceiling = emitted["coverage_ceiling"]["analysed"]
        print(
            f"  {name}: {counts['SYMBOL']} symbols, {counts['OCCURRENCE']} occurrences, "
            f"{counts['RELATIONSHIP']} relationships, {ceiling['numerator']}/{ceiling['denominator']} "
            f"declared blobs indexed, completeness={emitted['coverage_ceiling']['completeness']}, "
            f"unresolved={emitted['resolution']['UNRESOLVED_IN_INDEX']}/{emitted['decoded']['occurrences']}, "
            f"read-back {emitted['readback']['checked']} matched"
        )
        for record in emitted["facts"]:
            if any(record["establishes"].values()):
                fail(f"{name}: {record['fact_id']} promoted an establishes constant")
            identity_holders = [
                record.get("symbol", {}).get("identity"),
                record.get("occurrence", {}).get("identity"),
                record.get("relationship", {}).get("from"),
                record.get("relationship", {}).get("to"),
            ]
            for holder in identity_holders:
                if holder is None:
                    continue
                if not isinstance(holder, dict) or "normalization" not in holder:
                    fail(f"{name}: {record['fact_id']} carries a bare provider identifier")
            if record["fact_kind"] == "RELATIONSHIP":
                evidence = record["relationship"]["graph_evidence"]
                if record["relationship"]["relationship_kind"] == "CALLS":
                    fail(f"{name}: {record['fact_id']} filed an occurrence-derived edge as CALLS")
                if evidence["completeness"] != "PARTIAL_LOWER_BOUND":
                    fail(f"{name}: {record['fact_id']} recorded a heuristic edge as more than a lower bound")
                if not any(warning.startswith("source range: ") for warning in record["warnings"]):
                    fail(f"{name}: {record['fact_id']} cites no source range")
        if any(emitted["receipt"]["grants"].values()):
            fail(f"{name}: the fact-plane receipt granted something")
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
    """A copy of this adapter that a planted defect can be applied to.

    Laid out as `<tmp>/adapters/scip` with `<tmp>/references` pointing at the
    real read-only schemas, because the adapter resolves them relative to
    itself. The frozen schemas are never copied and never written to: the
    symlink is what keeps a mutation run reading the same schemas the tree
    carries.
    """
    root = Path(tempfile.mkdtemp(prefix="dtcr-scip-"))
    work = root / "adapters" / "scip"
    shutil.copytree(ADAPTER_DIR, work, ignore=shutil.ignore_patterns("__pycache__"))
    (root / "references").symlink_to(A.SKILL / "references", target_is_directory=True)
    mutate(work)
    return work


def load_adapter(work: Path) -> Any:
    global _loaded
    _loaded += 1
    spec = importlib.util.spec_from_file_location(f"dtcr_scip_mutant_{_loaded}", work / "adapter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_adapter_refusal(name: str, mutate: Callable[[Path], None], fixture: str = "python-subject") -> bool:
    work = mutated_tree(mutate)
    try:
        module = load_adapter(work)
        module.run_replay(work / "fixtures" / fixture / "request.json")
    except A.Refusal as refusal:  # the copied module raises its own Refusal class
        return _judge(name, refusal.reason)
    except Exception as error:  # noqa: BLE001
        reason = getattr(error, "reason", None)
        if reason is None:
            fail(f"{name}: raised {type(error).__name__} rather than its named refusal ({error})")
            return False
        return _judge(name, reason)
    finally:
        shutil.rmtree(work.parents[1], ignore_errors=True)
    fail(f"{name}: the planted defect was emitted without refusal")
    return False


def _judge(name: str, reason: str) -> bool:
    if reason != name:
        fail(f"{name}: refused, but by {reason} -- the planted defect never reached its own guard")
        return False
    print(f"  {name}: refused by adapter guard {reason}")
    return True


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


def edit_source(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise AssertionError(f"{path.name}: the mutation anchor {old!r} occurs {text.count(old)} times, not once")
    path.write_text(text.replace(old, new), encoding="utf-8")


REQUEST = ("fixtures", "python-subject", "request.json")
SOURCE = ("fixtures", "python-subject", "src", "pricing.py")


def lane_falsifiers(bundles: dict[str, dict[str, Any]]) -> int:
    print("falsifiers")
    emitted = bundles["python-subject"]
    rows = 0

    def request_of(work: Path) -> Path:
        return work.joinpath(*REQUEST)

    def strip_index_digest(work: Path) -> None:
        edit_json(request_of(work), lambda data: data["index_binding"].update({"index_digest": None}))

    def blank_indexer_version(work: Path) -> None:
        edit_json(request_of(work), lambda data: data["index_binding"].update({"version": ""}))

    def rewrite_source(work: Path, old: str, new: str, also_indexed: bool) -> None:
        source = work.joinpath(*SOURCE)
        edit_source(source, old, new)
        blob = A.git_blob_sha1(source.read_bytes())
        path_key = None

        def mutate(data: dict[str, Any]) -> None:
            nonlocal path_key
            for entry in data["declared_blobs"]:
                if entry["local"].endswith("pricing.py"):
                    path_key = entry["path"]
                    entry["blob"] = blob
                    entry["byte_count"] = source.stat().st_size
            if also_indexed and path_key:
                data["index_binding"]["indexed_blobs"][path_key] = blob

        edit_json(request_of(work), mutate)

    def source_edited_after_indexing(work: Path) -> None:
        # The subject moved on and the index did not. Same length, so nothing
        # else about the fixture shifts.
        rewrite_source(work, "def format_total(amount):", "def format_totaX(amount):", also_indexed=False)

    def index_of_a_different_tree(work: Path) -> None:
        # The binding is repaired everywhere -- the declared blob and the blob
        # the index records reading are both updated -- so the stale guard
        # passes and the only thing left to catch it is reading the range back
        # out of the bytes.
        rewrite_source(work, "def format_total(amount):", "def format_totaX(amount):", also_indexed=True)

    def drop_the_omission(work: Path) -> None:
        edit_json(
            request_of(work),
            lambda data: data.__setitem__(
                "omissions", [entry for entry in data["omissions"] if "NOTES.md" not in entry["detail"]]
            ),
        )

    def unpinned_normalization(work: Path) -> None:
        edit_json(
            request_of(work),
            lambda data: data.__setitem__("normalization_digest", "0" * 64),
        )

    def occurrence_edge_called_a_call(work: Path) -> None:
        edit_source(work / "adapter.py", '    return "REFERENCES"', '    return "CALLS"')

    def drop_unresolved_occurrences(work: Path) -> None:
        edit_source(
            work / "adapter.py",
            "    return [(occurrence, resolve(occurrence[\"symbol\"])) for occurrence in occurrences]",
            "    return [(occurrence, resolve(occurrence[\"symbol\"])) for occurrence in occurrences\n"
            "            if resolve(occurrence[\"symbol\"]) != \"UNRESOLVED_IN_INDEX\"]",
        )

    def edge_without_its_occurrence(work: Path) -> None:
        edit_source(work / "adapter.py", '"_from_occurrence": record["_key"],', '"_from_occurrence": None,')

    def row_claims_a_task_pass(work: Path) -> None:
        edit_source(
            work / "adapter.py",
            'ESTABLISHES = {"complete_call_graph": False, "semantic_truth": False, "task_pass": False}',
            'ESTABLISHES = {"complete_call_graph": False, "semantic_truth": False, "task_pass": True}',
        )

    adapter_rows = [
        ("SCIP_INDEX_DIGEST_ABSENT", strip_index_digest),
        ("INDEXER_VERSION_OR_CONFIG_UNBOUND", blank_indexer_version),
        ("STALE_INDEX_REUSED_AFTER_SOURCE_CHANGE", source_edited_after_indexing),
        ("SCIP_INDEX_WRONG_SUBJECT", index_of_a_different_tree),
        ("PARTIAL_COVERAGE_PROMOTED_TO_COMPLETE", drop_the_omission),
        ("PROVIDER_ID_PROMOTED_TO_UNIVERSAL_ID", unpinned_normalization),
        ("OCCURRENCE_NESTING_PROMOTED_TO_CALL_GRAPH", occurrence_edge_called_a_call),
        ("UNRESOLVED_SYMBOL_OMITTED_FROM_DENOMINATOR", drop_unresolved_occurrences),
        ("RELATIONSHIP_WITHOUT_SOURCE_RANGE", edge_without_its_occurrence),
        ("SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS", row_claims_a_task_pass),
    ]
    for name, mutate in adapter_rows:
        rows += 1
        expect_adapter_refusal(name, mutate)

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

    symbol_fact = next(r for r in emitted["facts"] if r["fact_kind"] == "SYMBOL")
    relationship = next(r for r in emitted["facts"] if r["fact_kind"] == "RELATIONSHIP")
    schema_rows = [
        (
            "SCIP_INDEX_DIGEST_ABSENT (schema half)",
            "symbol-fact.schema.json",
            without(symbol_fact, "index_binding", "index_digest"),
            "properties.index_binding.required",
        ),
        (
            "PROVIDER_ID_PROMOTED_TO_UNIVERSAL_ID (schema half)",
            "symbol-fact.schema.json",
            with_value(symbol_fact, symbol_fact["symbol"]["identity"]["provider_scoped_id"], "symbol", "identity"),
            "properties.symbol.properties.identity.type",
            "$defs.provider_scoped_identity.type",
        ),
        (
            "OCCURRENCE_NESTING_PROMOTED_TO_CALL_GRAPH (schema half)",
            "symbol-fact.schema.json",
            with_value(relationship, "COMPLETE_FOR_RESOLVED_EDGES", "relationship", "graph_evidence", "completeness"),
            "properties.relationship.allOf[0].then.properties.graph_evidence.properties.completeness.enum",
            "$defs.relationship_record.allOf[0].then.properties.graph_evidence.properties.completeness.enum",
        ),
        (
            "SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS (schema half, fact)",
            "symbol-fact.schema.json",
            with_value(symbol_fact, True, "establishes", "task_pass"),
            "properties.establishes.properties.task_pass.const",
        ),
        (
            "SCIP_PASS_PROMOTED_TO_TASK_OR_MERGE_PASS (schema half, receipt)",
            "fact-plane-receipt.schema.json",
            with_value(emitted["receipt"], True, "grants", "merge"),
            "properties.grants.properties.merge.const",
        ),
        (
            "PARTIAL_COVERAGE_PROMOTED_TO_COMPLETE (schema half)",
            "coverage-ceiling.schema.json",
            with_value(emitted["coverage_ceiling"], "COMPLETE_FOR_ANALYSED_INPUTS", "completeness"),
            "allOf[0].then.properties.completeness.enum",
        ),
        (
            "UNANALYSED_INPUTS_CLEARED",
            "coverage-ceiling.schema.json",
            with_value(emitted["coverage_ceiling"], True, "authority_ceiling", "unanalysed_inputs_cleared"),
            "properties.authority_ceiling.properties.unanalysed_inputs_cleared.const",
        ),
    ]
    for row in schema_rows:
        rows += 1
        expect_schema_refusal(*row)
    return rows


# --------------------------------------------------------------------------
# lane 3: crosscheck
# --------------------------------------------------------------------------
def lane_crosscheck() -> str:
    print("crosscheck")
    descriptor = BINDINGS / "scip.desc"
    binding_file = BINDINGS / "binding.json"
    if not descriptor.is_file() or not binding_file.is_file():
        print("  NOT_EXERCISED: no committed descriptor set to decode against")
        return "NOT_EXERCISED"
    binding = json.loads(binding_file.read_text(encoding="utf-8"))
    observed = A.sha256_hex(descriptor.read_bytes())
    if observed != binding["descriptor_set"]["sha256"]:
        fail(f"crosscheck: bindings/scip.desc hashes to {observed}, binding.json pins {binding['descriptor_set']['sha256']}")
        return "FAILED"
    try:
        from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
    except ImportError:
        # #547: an absent second decoder is start-readiness. The primary decode
        # still ran in the replay lane and is still read back against the source
        # bytes; what is missing here is the independent confirmation, and this
        # lane says that rather than implying it happened.
        print("  NOT_EXERCISED: no protobuf runtime on this machine; the primary decode stands on its read-back alone")
        return "NOT_EXERCISED"

    file_set = descriptor_pb2.FileDescriptorSet()
    file_set.ParseFromString(descriptor.read_bytes())
    pool = descriptor_pool.DescriptorPool()
    for proto_file in file_set.file:
        pool.Add(proto_file)
    IndexMessage = message_factory.GetMessageClass(pool.FindMessageTypeByName("scip.Index"))

    compared = 0
    for index_path in sorted(FIXTURES.glob("*/index.scip")):
        raw = index_path.read_bytes()
        mine = A.decode_index(raw)
        theirs = IndexMessage()
        theirs.ParseFromString(raw)
        compared += 1
        name = index_path.parent.name

        def shape_mine() -> Any:
            return [
                mine["tool_info"]["name"],
                mine["tool_info"]["version"],
                mine["project_root"],
                sorted(
                    [
                        document["relative_path"],
                        sorted(info["symbol"] for info in document["symbols"]),
                        sorted(
                            [occurrence["range"], occurrence["symbol"], occurrence["symbol_roles"], occurrence["enclosing_range"]]
                            for occurrence in document["occurrences"]
                        ),
                    ]
                    for document in mine["documents"]
                ),
                sorted(info["symbol"] for info in mine["external_symbols"]),
            ]

        def shape_theirs() -> Any:
            return [
                theirs.metadata.tool_info.name,
                theirs.metadata.tool_info.version,
                theirs.metadata.project_root,
                sorted(
                    [
                        document.relative_path,
                        sorted(info.symbol for info in document.symbols),
                        sorted(
                            [list(occurrence.range), occurrence.symbol, occurrence.symbol_roles, list(occurrence.enclosing_range)]
                            for occurrence in document.occurrences
                        ),
                    ]
                    for document in theirs.documents
                ),
                sorted(info.symbol for info in theirs.external_symbols),
            ]

        if A.canonical(shape_mine()) != A.canonical(shape_theirs()):
            fail(f"crosscheck: {name}: the wire reader and the protoc-compiled schema disagree on these bytes")
        else:
            occurrences = sum(len(d["occurrences"]) for d in mine["documents"])
            symbols = sum(len(d["symbols"]) for d in mine["documents"])
            print(
                f"  {name}: two decoders agree on {len(mine['documents'])} documents, {symbols} symbols, "
                f"{occurrences} occurrences ({binding['descriptor_set']['produced_by']}, "
                f"scip.proto {binding['proto']['revision']})"
            )
    if not compared:
        fail("crosscheck: no committed index bytes to decode")
        return "FAILED"
    return "EXERCISED"


# --------------------------------------------------------------------------
# lane 4: live
# --------------------------------------------------------------------------
def neutralized_match(receipt: dict[str, Any], candidates: list[Path], name: str) -> list[Path]:
    """The one widening of "the committed index is the bytes this receipt names".

    `Metadata.project_root` is the absolute path of the directory the indexer ran
    in, so the bytes a real run emits carry an account name and a checkout id and
    committing them publishes both. The committed fixture is therefore those
    bytes with that one field rewritten, and `index.sha256` still records what the
    indexer actually emitted -- moving it would turn a receipt into a claim about
    bytes nobody produced.

    So this widens, and it is written down rather than silent. The rewritten
    fixture is accepted only while the receipt declares the rewrite, names
    `Metadata.project_root` as the only changed field, ties the record to the
    digest the receipt already carries, and the committed bytes actually decode
    to the neutral value the record names. Drop the record and this is a hard
    failure again; name a second changed field and it is a hard failure; the
    caller still holds the accepted bytes to `facts_digest_modulo_project_root`,
    which is a second tie the rewrite does not move.
    """
    record = receipt["index"].get("neutralization")
    if not isinstance(record, dict):
        fail(
            f"{name}: no committed index in this tree hashes to {receipt['index']['sha256']} and the "
            f"receipt declares no neutralization; the receipt describes bytes that are no longer here "
            f"(looked at {[str(path.relative_to(ADAPTER_DIR)) for path in candidates]})"
        )
        return []
    if record.get("changed_fields") != ["Metadata.project_root"]:
        fail(
            f"{name}: the neutralization record declares changed_fields="
            f"{record.get('changed_fields')!r}; this suite widens for Metadata.project_root and for "
            "nothing else, because that field is the only one no honest run can reproduce"
        )
        return []
    if record.get("index_digest_before") != receipt["index"]["sha256"]:
        fail(
            f"{name}: the neutralization record was written against index_digest_before="
            f"{record.get('index_digest_before')!r} and the receipt names {receipt['index']['sha256']}; "
            "the record belongs to a different index"
        )
        return []
    digest = str(record.get("fixture_digest_after_declared_neutralization", ""))
    if not A.HEX64.match(digest):
        fail(f"{name}: fixture_digest_after_declared_neutralization={digest!r} is not a sha256")
        return []
    found = [path for path in candidates if A.sha256_hex(path.read_bytes()) == digest]
    if not found:
        fail(
            f"{name}: no committed index hashes to the declared post-neutralization digest {digest} "
            f"(looked at {[str(path.relative_to(ADAPTER_DIR)) for path in candidates]})"
        )
        return []
    observed = A.decode_index(found[0].read_bytes())["project_root"]
    if observed != record.get("project_root_after"):
        fail(
            f"{name}: the record declares the rewritten project_root is "
            f"{record.get('project_root_after')!r} and the committed index decodes to {observed!r}"
        )
        return []
    if LEAK_SHAPES.search(scrub(observed.encode("utf-8"))):
        fail(f"{name}: the declared neutral project_root is itself a machine-local locator")
        return []
    print(
        f"  {name}: index.sha256 is what the indexer emitted; the committed fixture is those bytes "
        f"with Metadata.project_root alone rewritten, hashes to {digest[:12]} and decodes to the "
        "declared neutral root"
    )
    return found


def check_receipt_offline(receipt: dict[str, Any], name: str) -> None:
    """What a committed live receipt must hold with no indexer on the machine.

    It cannot prove the run happened -- only the run proves that -- but it can
    prove the receipt is about the index and the rule this tree carries."""
    for key in ("index", "facts_digest_modulo_project_root", "normalization", "establishes", "subject"):
        if key not in receipt:
            fail(f"{name}: no {key}; a receipt this suite cannot compare against a run is not evidence")
            return
    _, rule_digest = A.load_rule()
    if receipt["normalization"]["scheme_digest"] != rule_digest:
        fail(
            f"{name}: the receipt was written under normalization scheme "
            f"{receipt['normalization']['scheme_digest']} and this tree's rule hashes to {rule_digest}"
        )
    candidates = sorted(FIXTURES.glob("*/index.scip"))
    matching = [path for path in candidates if A.sha256_hex(path.read_bytes()) == receipt["index"]["sha256"]]
    if not matching:
        matching = neutralized_match(receipt, candidates, name)
    if not matching:
        return
    raw = matching[0].read_bytes()
    if A.facts_digest_modulo_project_root(raw) != receipt["facts_digest_modulo_project_root"]:
        fail(f"{name}: the committed index decodes to different facts than the receipt records")
    if not A.HEX40.match(receipt["subject"]["commit"]):
        fail(f"{name}: subject.commit is not an exact commit")
    if any(receipt["establishes"].values()):
        fail(f"{name}: a live indexer run recorded itself as establishing something")
    cross = receipt.get("decoder", {}).get("cross_check")
    if isinstance(cross, dict):
        binding_file = BINDINGS / "binding.json"
        if not binding_file.is_file() or A.sha256_hex(binding_file.read_bytes()) != cross["binding_file_sha256"]:
            fail(f"{name}: the proto binding it was written against is not the one this tree carries")


def lane_live() -> str:
    print("live")
    receipts = sorted(RECEIPTS.glob("*.json")) if RECEIPTS.is_dir() else []
    if not receipts:
        fail("no committed live receipt; the terminal for this adapter is a real indexer round-trip")
        return "FAILED"
    for receipt_path in receipts:
        check_receipt_offline(json.loads(receipt_path.read_text(encoding="utf-8")), receipt_path.name)
        print(f"  {receipt_path.name}: digests bind the committed index and rule (checked without the indexer)")

    if A.find_indexer() is None:
        print(f"  NOT_EXERCISED: no {A.EXECUTABLE_NAME} on this host. A missing indexer is start-readiness, not a failure.")
        return "NOT_EXERCISED"

    try:
        repo = Path(A.git(ADAPTER_DIR, "rev-parse", "--show-toplevel"))
    except subprocess.CalledProcessError:
        # A copy of this adapter outside a checkout has no subject commit to be
        # about. That is an absent input, not a passing run, and it is typed
        # here rather than crashing the suite two lanes after the fact.
        print("  NOT_EXERCISED: this adapter is not inside a git checkout, so there is no exact subject to index")
        return "NOT_EXERCISED (no checkout)"
    receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
    index_root = receipt["index_root"]
    try:
        emitted = A.run_live(
            repo=repo,
            index_root=index_root,
            omissions=[
                {"omission_kind": "LANGUAGE_NOT_INSTALLED", "detail": "NOTES.md is Markdown and this indexer covers Python only; it was never opened by the indexer"},
                {"omission_kind": "EXCLUDED_BY_CONFIG", "detail": "pyproject.toml is the indexer configuration for this root, not a source blob the indexer parses"},
            ],
        )
    except A.Refusal as refusal:
        if refusal.reason in ("SUBJECT_PATH_ABSENT", "STALE_INDEX_REUSED_AFTER_SOURCE_CHANGE"):
            print(f"  NOT_EXERCISED: {refusal.detail}")
            return f"NOT_EXERCISED ({refusal.reason})"
        fail(f"live run refused: {refusal}")
        return "FAILED"

    run = emitted["receipt"]["provider_runs"][0]
    print(
        f"  ran {A.EXECUTABLE_NAME} {run['version']} over {index_root} at "
        f"{emitted['receipt']['subject']['commit'][:12]}: {len(emitted['facts'])} facts, exit {run['exit_code']}"
    )
    for record in emitted["facts"] + [emitted["coverage_ceiling"], emitted["receipt"]]:
        if validate(record, load_schema(SCHEMA_BY_ID[record["schema"]])):
            fail(f"live: {record['schema']} does not validate against the frozen schema")

    observed = A.facts_digest_modulo_project_root(emitted["_index_bytes"])
    for key, seen in (
        ("version", emitted["_index_binding"]["version"]),
        ("executable_sha256", emitted["_index_binding"]["indexer_sha256"]),
        ("config_digest", emitted["_index_binding"]["config_digest"]),
        ("provider_binding_id", emitted["coverage_ceiling"]["provider_binding_id"]),
    ):
        if receipt["provider"][key] != seen:
            fail(f"live: {receipts[0].name} records {key}={receipt['provider'][key]}, this host observed {seen}")
    if receipt["facts_digest_modulo_project_root"] != observed:
        fail(
            f"live: {receipts[0].name} and this host disagree on what the same indexer, configuration "
            "and bytes determine once the one absolute path in a SCIP index is factored out"
        )
    else:
        print(f"  {receipts[0].name}: this host reproduces the recorded index over the same blobs")
    if receipt["index"]["sha256"] != emitted["_index_binding"]["index_digest"]:
        print(
            "  whole-index digest differs from the receipt, as it must from another directory: "
            "Metadata.project_root is an absolute path and is inside the bytes"
        )
    # The only place the neutralization runs against bytes an indexer really
    # just emitted, which is where the rewritten field is a different length
    # from the one it replaces. Committing what this returns is what `--record`
    # does, so the scan that guards the tree is run over it here first.
    would_commit, _machine_local, neutral = A.neutralize_project_root(emitted["_index_bytes"], index_root)
    if LEAK_SHAPES.search(scrub(would_commit)):
        fail("live: the bytes --record would commit still carry a machine-local locator")
    else:
        print(f"  the bytes --record would commit on this host carry project_root {neutral} and nothing machine-local")
    return "EXERCISED"


# --------------------------------------------------------------------------
# lane 5: leak scan
# --------------------------------------------------------------------------
def leak_scan(root: Path) -> tuple[int, list[str]]:
    """Every file under `root`, read as bytes, permitting only the declared
    literals.

    Bytes and not text, because the locator this lane exists for lived inside a
    committed protobuf fixture. `__pycache__` is skipped and named here rather
    than filtered silently: it is generated, it is not committed, and a `.pyc`
    records the absolute path of the file it was compiled from, so scanning it
    would report a leak in a file nobody publishes.
    """
    findings: list[str] = []
    files = [path for path in sorted(root.rglob("*")) if path.is_file() and "__pycache__" not in path.parts]
    for path in files:
        data = scrub(path.read_bytes())
        for match in LEAK_SHAPES.finditer(data):
            # The excerpt and not an offset: removing the permitted literals
            # shifts every position after them, and a byte number that does not
            # index the file on disk is worse than none.
            findings.append(
                f"{path.relative_to(root)}: machine-local locator shape {match.group(0)!r} is not on "
                f"the permitted list, in {data[match.start():match.start() + 64]!r}"
            )
    return len(files), findings


def lane_leak() -> int:
    print("leak-scan")
    if not LEAK_SHAPES.search(RED_PROOF_LOCATOR):
        fail("leak-scan: the probe carries no locator shape, so the red proof below would prove nothing")
        return 0
    work = mutated_tree(
        lambda tree: (tree / "fixtures" / "python-subject" / "index.scip").write_bytes(
            (tree / "fixtures" / "python-subject" / "index.scip").read_bytes() + RED_PROOF_LOCATOR
        )
    )
    try:
        _, planted = leak_scan(work)
    finally:
        shutil.rmtree(work.parents[1], ignore_errors=True)
    if planted:
        print(f"  (red proof) same scan, throwaway copy carrying the shape this lane exists to catch: {planted[0]}")
    else:
        fail("leak-scan: a planted machine-local locator was not found, so a green on this tree means nothing")

    # The producer path, executed. Re-running the neutralization over the bytes
    # it already produced has to return them unchanged: a splice that mislocates
    # Metadata.project_root or miscounts a length varint does not survive being
    # applied twice, and this runs on every host whether or not an indexer is
    # installed.
    for index_path in sorted(FIXTURES.glob("*/index.scip")):
        request = json.loads((index_path.parent / "request.json").read_text(encoding="utf-8"))
        raw = index_path.read_bytes()
        again, _, neutral = A.neutralize_project_root(raw, request["index_root"])
        if again != raw:
            fail(
                f"leak-scan: {index_path.parent.name}: the committed index is not the fixed point of "
                "the neutralization that is supposed to have produced it"
            )
        else:
            print(f"  {index_path.parent.name}: project_root is {neutral}, and re-neutralizing it changes nothing")

    files, findings = leak_scan(ADAPTER_DIR)
    for finding in findings:
        fail(f"leak-scan: {finding}")
    if not findings:
        print(
            f"  {files} files under adapters/scip scanned as bytes, binaries included: no machine-local "
            f"locator outside the {len(PERMITTED_LOCATORS)} declared literals"
        )
    return files


def main() -> int:
    bundles, validations, facts = lane_replay()
    rows = lane_falsifiers(bundles)
    cross = lane_crosscheck()
    live = lane_live()
    scanned = lane_leak()
    print(
        "\nDTCR-SCIP denominators: "
        f"fixtures={len(bundles)} facts={facts} schema_validations={validations} "
        f"falsifier_rows={rows} crosscheck={cross} live={live} leak_scan_files={scanned} "
        f"failures={len(failures)}"
    )
    if failures:
        print("DTCR-SCIP SELFTEST RED")
        return 2
    print("DTCR-SCIP SELFTEST GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
