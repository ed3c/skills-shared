#!/usr/bin/env python3
"""Execute the Tree-sitter adapter against the frozen DTCR schemas.

Three lanes, and the numbers each one counts are printed so a run can never
report a green it did not measure:

    replay     every fixture under `fixtures/` is emitted with no provider on
               the machine, from stdout a real `tree-sitter` run produced, and
               every emitted match, coverage ceiling and fact-plane receipt is
               validated against the read-only schemas in
               `../../references/schemas/`.
    falsifiers every planted defect named by issue #546 is run through the code
               path that owns it and must be refused *by that guard*. A defect
               that dies on an unrelated `required` proves nothing about the
               guard it was written for, so a schema-side row also performs a
               knockout: delete exactly the keyword the row names from a copy of
               the schema, change nothing else, and require the mutated instance
               to validate. A control still refused after its own guard is gone
               is refused by something else and the row naming it is wrong.
    live       every committed receipt is checked against this tree's bundle
               with no provider needed, because a receipt whose digests drifted
               describes a bundle that is no longer here and reads exactly like
               one that still matches. Then, if the CLI and a matching grammar
               are on the host, the adapter runs for real against the current
               HEAD, its observed provider identity is compared with the
               receipt, and it must reproduce what the receipt recorded over
               the same blobs once the subject commit is factored out -- which
               is the part of an emission a second host can be held to.
               A missing provider is start-readiness, not a failure:
               the lane prints NOT_EXERCISED and stays green, and says plainly
               that what it could not check is whether the run reproduces.

Exit 0 green, 2 a lane failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import os
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
        "DTCR-TS-SELFTEST-UNUSABLE: jsonschema is required. This suite executes the frozen "
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
BUNDLE = ADAPTER_DIR / "bundles" / "python-definitions.bundle.json"
# (root, glob). The grammar is not vendored into this repository: it carries its
# own licence, which the framework's licence does not admit, and its build is
# machine-local. So the live lane looks for one and reports NOT_EXERCISED rather
# than assuming one, and DTCR_TS_GRAMMAR_DIR overrides the search entirely.
GRAMMAR_CANDIDATES = (
    ("~/.cargo/registry/src", "*/tree-sitter-python-0.25.0"),
    ("~/.local/share/tree-sitter", "tree-sitter-python*"),
)

SCHEMA_BY_ID = {
    A.MATCH_SCHEMA: "syntax-match.schema.json",
    A.CEILING_SCHEMA: "coverage-ceiling.schema.json",
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


# --------------------------------------------------------------------------
# lane 1: replay
# --------------------------------------------------------------------------
def lane_replay() -> tuple[dict[str, dict[str, Any]], int, int]:
    print("replay")
    bundles: dict[str, dict[str, Any]] = {}
    validations = 0
    matches = 0
    requests = sorted(FIXTURES.glob("*/request.json"))
    if not requests:
        fail("no fixture requests on the tree; the replay lane would be green over nothing")
    for request in requests:
        name = request.parent.name
        emitted = A.run_replay(request)
        bundles[name] = emitted
        records = emitted["matches"] + [emitted["coverage_ceiling"], emitted["receipt"]]
        for record in records:
            schema = load_schema(SCHEMA_BY_ID[record["schema"]])
            errors = validate(record, schema)
            validations += 1
            if errors:
                fail(f"{name}: {record['schema']} refused by the frozen schema: {errors[0].message}")
        matches += len(emitted["matches"])
        ceiling = emitted["coverage_ceiling"]["analysed"]
        print(
            f"  {name}: {len(emitted['matches'])} matches, "
            f"{ceiling['numerator']}/{ceiling['denominator']} declared blobs analysed, "
            f"parse_status={emitted['matches'][0]['parse_status'] if emitted['matches'] else 'NO_MATCH'}, "
            f"completeness={emitted['coverage_ceiling']['completeness']}"
        )
        for record in emitted["matches"]:
            if record["match_class"] != "SYNTACTIC_CANDIDATE" or any(record["establishes"].values()):
                fail(f"{name}: a match left SYNTACTIC_CANDIDATE or promoted an establishes constant")
        digest_input = {k: v for k, v in emitted["matches"][0].items() if k != "output_digest"} if emitted["matches"] else {}
        if emitted["matches"] and A.sha256_hex(A.canonical(digest_input)) != emitted["matches"][0]["output_digest"]:
            fail(f"{name}: output_digest does not cover the record it is attached to")
        second = A.run_replay(request)
        if A.canonical(second) != A.canonical(emitted):
            fail(f"{name}: two emissions of one fixture differ; the output is not deterministic")
    return bundles, validations, matches


# --------------------------------------------------------------------------
# lane 2: falsifiers
# --------------------------------------------------------------------------
def mutated_tree(mutate: Callable[[Path], None]) -> Path:
    work = Path(tempfile.mkdtemp(prefix="dtcr-ts-")) / "tree-sitter"
    shutil.copytree(ADAPTER_DIR, work, ignore=shutil.ignore_patterns("__pycache__"))
    mutate(work)
    return work


def expect_adapter_refusal(name: str, fixture: str, mutate: Callable[[Path], None]) -> bool:
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


def lane_falsifiers(bundles: dict[str, dict[str, Any]]) -> int:
    print("falsifiers")
    clean = bundles["python-clean"]
    errored = bundles["python-parse-errors"]
    rows = 0

    def strip_errors(work: Path) -> None:
        target = work / "fixtures" / "python-parse-errors" / "broken.py.fixture.parse.stdout"
        text = target.read_text(encoding="utf-8")
        target.write_text(text.replace("(ERROR ", "(block ").replace("(MISSING ", "(block "), encoding="utf-8")

    def move_capture_past_eof(work: Path) -> None:
        target = work / "fixtures" / "python-clean" / "sample.py.fixture.query.stdout"
        text = target.read_text(encoding="utf-8")
        target.write_text(text.replace("start: (", "start: (900", 1).replace("end: (", "end: (900", 1), encoding="utf-8")

    def break_blob(work: Path) -> None:
        def mutate(data: dict[str, Any]) -> None:
            blob = data["declared_blobs"][0]["blob"]
            data["declared_blobs"][0]["blob"] = blob[:-1] + ("0" if blob[-1] != "0" else "1")
        edit_json(work / "fixtures" / "python-clean" / "request.json", mutate)

    def mutable_subject(work: Path) -> None:
        edit_json(
            work / "fixtures" / "python-clean" / "request.json",
            lambda data: data["subject"].update({"commit": "main"}),
        )
    def wrong_grammar(work: Path) -> None:
        def mutate(data: dict[str, Any]) -> None:
            entry = data["grammar"]["files"][0]
            entry["sha256"] = entry["sha256"][:-1] + ("0" if entry["sha256"][-1] != "0" else "1")
            # Repair the outer digest so the manifest is internally consistent
            # everywhere except the grammar binding itself. Otherwise the row
            # would die on BUNDLE_DIGEST_MISMATCH and prove nothing about the
            # grammar identity.
            data["bundle_digest"] = A.bundle_digest_of(data)
        edit_json(work / "bundles" / "python-definitions.bundle.json", mutate)

    def empty_query(work: Path) -> None:
        query = work / "bundles" / "queries" / "python-definitions.scm"
        text = "; every pattern removed; this bundle can match nothing\n"
        query.write_text(text, encoding="utf-8")

        def mutate(data: dict[str, Any]) -> None:
            data["queries"][0]["sha256"] = A.sha256_hex(text.encode())
            data["queries"][0]["patterns"] = 0
            data["query_digest"] = A.sha256_hex(text.encode())
            data["bundle_digest"] = A.bundle_digest_of(data)
        edit_json(work / "bundles" / "python-definitions.bundle.json", mutate)

    def undeclared_file(work: Path) -> None:
        def mutate(data: dict[str, Any]) -> None:
            data["declared_blobs"].append(
                {
                    "path": "skills/dual-track-code-review-loop/adapters/tree-sitter/fixtures/python-clean/second.py.fixture",
                    "blob": "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
                    "byte_count": 0,
                }
            )
        edit_json(work / "fixtures" / "python-clean" / "request.json", mutate)

    adapter_rows = [
        ("MUTABLE_OR_WRONG_SOURCE_SUBJECT", "python-clean", mutable_subject),
        ("WRONG_GRAMMAR_OR_GRAMMAR_DIGEST", "python-clean", wrong_grammar),
        ("PARSE_ERROR_HIDDEN", "python-parse-errors", strip_errors),
        ("BYTE_RANGE_OUT_OF_SOURCE", "python-clean", move_capture_past_eof),
        ("MATCH_WITHOUT_SOURCE_BLOB_BINDING", "python-clean", break_blob),
        ("EMPTY_QUERY_REPORTED_AS_EXERCISED", "python-clean", empty_query),
        ("UNDECLARED_FILE_OMITTED_FROM_DENOMINATOR", "python-clean", undeclared_file),
    ]
    for name, fixture, mutate in adapter_rows:
        rows += 1
        expect_adapter_refusal(name, fixture, mutate)

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

    match = clean["matches"][0]
    error_match = errored["matches"][0]
    schema_rows = [
        (
            "TREE_SITTER_QUERY_DIGEST_ABSENT",
            "syntax-match.schema.json",
            without(match, "provider", "query_digest"),
            "properties.provider.required",
        ),
        (
            "SYNTAX_MATCH_PROMOTED_TO_SEMANTIC_FACT",
            "syntax-match.schema.json",
            with_value(match, "SEMANTIC_FACT", "match_class"),
            "properties.match_class.const",
        ),
        (
            "SYNTAX_MATCH_PROMOTED_TO_SEMANTIC_FACT (establishes)",
            "syntax-match.schema.json",
            with_value(match, True, "establishes", "semantic_binding"),
            "properties.establishes.properties.semantic_binding.const",
        ),
        (
            "PARSE_ERROR_HIDDEN (schema half)",
            "syntax-match.schema.json",
            with_value(error_match, "COMPLETE_FOR_ANALYSED_INPUTS", "completeness"),
            "allOf[0].then.properties.completeness.enum",
        ),
        (
            "MUTABLE_OR_WRONG_SOURCE_SUBJECT (schema half)",
            "syntax-match.schema.json",
            with_value(match, "main", "subject", "commit"),
            "properties.subject.properties.commit.pattern",
            "$defs.subject_ref.properties.commit.pattern",
        ),
        (
            "PROVIDER_PASS_PROMOTED_TO_TASK_PASS",
            "fact-plane-receipt.schema.json",
            with_value(clean["receipt"], True, "grants", "task_pass"),
            "properties.grants.properties.task_pass.const",
        ),
        (
            "UNANALYSED_INPUTS_CLEARED",
            "coverage-ceiling.schema.json",
            with_value(clean["coverage_ceiling"], True, "authority_ceiling", "unanalysed_inputs_cleared"),
            "properties.authority_ceiling.properties.unanalysed_inputs_cleared.const",
        ),
    ]
    for row in schema_rows:
        rows += 1
        expect_schema_refusal(*row)
    return rows


# --------------------------------------------------------------------------
# lane 3: live
# --------------------------------------------------------------------------
def resolve_grammar() -> Path | None:
    explicit = os.environ.get("DTCR_TS_GRAMMAR_DIR")
    if explicit:
        return Path(explicit) if Path(explicit).is_dir() else None
    for root, pattern in GRAMMAR_CANDIDATES:
        base = Path(root).expanduser()
        if not base.is_dir():
            continue
        for found in sorted(base.glob(pattern)):
            if (found / "src" / "parser.c").is_file():
                return found
    return None


def receipt_shape_errors(receipt: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    """Every reason `receipt` is not usable evidence, checked with no provider
    on the machine. Returned rather than raised or appended to the global
    `failures` list, so the #575 collision falsifier below can run a planted
    defect through this exact function without polluting the suite's own
    failure count.

    `manifest_digest` is refused outright: issue #575 found that name binding
    a `manifest["bundle_digest"]` value while a sibling `bundle_digest` key on
    the same receipt bound a different digest (this run's own emitted-output
    digest) -- one name, two values. `bundle_manifest_digest` is the only
    spelling this suite accepts for the manifest's own identity digest now."""
    for key in ("subject_blobs", "matches_digest_modulo_subject", "bundle_digest", "establishes"):
        if key not in receipt:
            return [f"no {key}; a receipt this suite cannot compare against a run is not evidence"]
    errors: list[str] = []
    if "manifest_digest" in receipt:
        errors.append(
            "manifest_digest is present; #575 retired that name because it collided with "
            "bundle_digest on the same receipt (one name bound two different digests) -- "
            "the manifest's own identity digest is bundle_manifest_digest now"
        )
    for key, expected in (
        ("bundle_manifest_digest", manifest["bundle_digest"]),
        ("query_digest", manifest["query_digest"]),
        ("grammar_digest", manifest["grammar"]["grammar_digest"]),
    ):
        observed = receipt.get(key) or receipt["provider"].get(key)
        if observed != expected:
            errors.append(f"{key}={observed} is not the {expected} this tree's bundle pins")
    if not A.HEX40.match(receipt["subject"]["commit"]):
        errors.append("subject.commit is not an exact commit")
    if any(receipt["establishes"].values()):
        errors.append("a live provider run recorded itself as establishing something")
    return errors


def check_receipt_offline(receipt: dict[str, Any], name: str) -> None:
    """What a committed live receipt must hold with no provider on the machine.

    It cannot prove the run happened -- only the run proves that -- but it can
    prove the receipt is about the bundle this tree carries. A receipt whose
    digests drifted from the manifest describes a bundle that is no longer
    here, and it reads exactly like one that still matches."""
    manifest = A.load_bundle(BUNDLE)
    for error in receipt_shape_errors(receipt, manifest):
        fail(f"{name}: {error}")


def lane_live() -> str:
    print("live")
    receipts = sorted(RECEIPTS.glob("*.json")) if RECEIPTS.is_dir() else []
    for receipt_path in receipts:
        check_receipt_offline(json.loads(receipt_path.read_text(encoding="utf-8")), receipt_path.name)
        print(f"  {receipt_path.name}: digests bind the committed bundle (checked without the provider)")

    # #575 falsifier: revert a real, currently-passing receipt to the retired
    # `manifest_digest` shape and require `receipt_shape_errors` to refuse it.
    # Proves the guard fires on the exact collision that shipped, not just
    # that the new key happens to be present in today's fixture.
    if receipts:
        manifest = A.load_bundle(BUNDLE)
        collided = json.loads(receipts[0].read_text(encoding="utf-8"))
        collided["manifest_digest"] = collided.pop("bundle_manifest_digest")
        errors = receipt_shape_errors(collided, manifest)
        if not errors:
            fail(
                "DTCR-TS-RECEIPT-KEY-COLLISION: a receipt reverted to the retired manifest_digest "
                "key was accepted with no shape errors; the #575 guard that refuses it is gone"
            )
        else:
            print(f"  DTCR-TS-RECEIPT-KEY-COLLISION: refused ({errors[0]})")

    binary = A.find_cli()
    grammar = resolve_grammar()
    if binary is None or grammar is None:
        missing = "tree-sitter CLI" if binary is None else "a grammar matching the bundle"
        # #519: a missing provider is start-readiness, never a failure. The
        # receipt above is still checked against the tree, so a stale receipt
        # is caught here; what cannot be caught without the provider is whether
        # the run it records would reproduce, and this lane says so rather than
        # implying it did.
        print(f"  NOT_EXERCISED: {missing} is absent. A missing provider is start-readiness, not a failure.")
        return "NOT_EXERCISED"

    repo = Path(A.git(ADAPTER_DIR, "rev-parse", "--show-toplevel"))
    paths = [
        str(path.relative_to(repo))
        for path in sorted(FIXTURES.glob("*/*.fixture"))
    ]
    try:
        emitted = A.run_live(repo=repo, bundle_path=BUNDLE, grammar_dir=grammar, paths=paths, omissions=[])
    except A.Refusal as refusal:
        if refusal.reason == "SUBJECT_PATH_ABSENT" and not receipts:
            print(f"  NOT_EXERCISED: {refusal.detail}")
            return "NOT_EXERCISED (subject not committed)"
        fail(f"live run refused: {refusal}")
        return "FAILED"

    run = emitted["receipt"]["provider_runs"][0]
    print(
        f"  ran tree-sitter {run['version']} over {len(paths)} blobs at "
        f"{emitted['receipt']['subject']['commit'][:12]}: {len(emitted['matches'])} matches, "
        f"exit {run['exit_code']}"
    )
    for record in emitted["matches"] + [emitted["coverage_ceiling"], emitted["receipt"]]:
        if validate(record, load_schema(SCHEMA_BY_ID[record["schema"]])):
            fail(f"live: {record['schema']} does not validate against the frozen schema")
    if not emitted["matches"]:
        fail("live: the CLI ran and produced no captures; the query bundle claims patterns it does not match")

    for receipt_path in receipts:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        provider = emitted["matches"][0]["provider"]
        for key, observed in (
            ("version", provider["version"]),
            ("executable_sha256", provider["executable_sha256"]),
            ("grammar_digest", provider["grammar"]["grammar_digest"]),
            ("query_digest", provider["query_digest"]),
            ("provider_binding_id", provider["provider_binding_id"]),
        ):
            if receipt["provider"][key] != observed:
                fail(f"live: {receipt_path.name} records {key}={receipt['provider'][key]}, this host observed {observed}")
        observed_blobs = {match["blob"]["path"]: match["blob"]["blob"] for match in emitted["matches"]}
        if receipt["subject_blobs"] != observed_blobs:
            fail(f"live: {receipt_path.name} records different subject blobs than this run read")
        elif receipt["matches_digest_modulo_subject"] != A.matches_digest_modulo_subject(emitted["matches"]):
            fail(
                f"live: {receipt_path.name} and this host disagree on what the same binary, grammar, "
                "query and bytes determine; one of the two identities is not what it says"
            )
        else:
            print(f"  {receipt_path.name}: this host reproduces the recorded emission over the same blobs")
        if receipt["subject"]["commit"] == emitted["receipt"]["subject"]["commit"]:
            if receipt["bundle_digest"] != emitted["receipt"]["bundle_digest"]:
                fail(f"live: {receipt_path.name} is at this commit but its bundle digest differs from this run")
            print(f"  {receipt_path.name}: replayed at its own subject commit, whole-bundle digest agrees")
    return "EXERCISED"


def main() -> int:
    bundles, validations, matches = lane_replay()
    rows = lane_falsifiers(bundles)
    live = lane_live()
    print(
        "\nDTCR-TS denominators: "
        f"fixtures={len(bundles)} matches={matches} schema_validations={validations} "
        f"falsifier_rows={rows} live={live} failures={len(failures)}"
    )
    if failures:
        print("DTCR-TS SELFTEST RED")
        return 2
    print("DTCR-TS SELFTEST GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
