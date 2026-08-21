#!/usr/bin/env python3
"""Replay the DTCR C0 contract from the tree, not from a recorded result.

The C0 merge left this lane ABSENT on purpose: the schema, positive-instance
and refusal denominators were run once from an uncommitted scratch harness and
re-derived once by an independent Shadow, and then nothing in this repository
could replay either. Issue #537 owns closing that, and the load-bearing rule it
sets is that the denominator is *counted from the bytes at run time*. A suite
that hard-codes `32` reports the same green after a sibling lands a ninth schema
as it did before, which is the failure the scratch harness could not have.

So every number this file prints is counted from `references/` on the run, and
every number it checks is checked against what it counted:

    schemas    every references/schemas/*.json, each a valid Draft 2020-12 doc
    positives  every in-schema `examples` entry plus every `x-positive-instance`
    controls   every in-schema `x-refusal-control` plus every negative_control
               carried by a disposition in a source-disposition instance
    knockouts  one per control: remove exactly the keyword(s) its `refused_by`
               names, change nothing else, and require the instance to validate

The knockout is the half that makes a control mean something. A control that
stays refused after its own named guard is gone is refused by something else,
and the record naming that guard is wrong. Two granularity traps are handled
explicitly because both produce a *passing* knockout for the wrong reason:

  * multi-keyword `refused_by` ("A and B") must remove both, or the instance is
    still refused by the half that was left standing;
  * a guard written as `not: {pattern: ...}` must lose the whole `not`. Removing
    only `pattern` leaves `not: {}`, which refuses every instance, so the
    knockout would report the guard as load-bearing no matter what it said.

Three further control classes come from the C0 receipt rather than from the
schemas' own `x-refusal-controls`, and #537 requires them executable here:
a private-locator leak scan over every reachable reference byte, mutable-subject
probes against every exact-commit field, and promotion probes against every
const-pinned field. Those three are also counted from the tree.

Exit 0 green, 2 a control or count failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterator

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "DTCR-SELFTEST-UNUSABLE: jsonschema is required. This suite executes the "
        "committed schemas as deciding gates; skipping them would report the "
        "same green as running them.",
        file=sys.stderr,
    )
    raise SystemExit(70)

SKILL = Path(__file__).resolve().parents[1]
# The subject is the committed tree by default. The override exists so a copy
# carrying one planted defect can be run through the identical code path; it is
# printed with the denominators so a run can never hide which bytes it read.
REFERENCES = Path(os.environ.get("DTCR_REFERENCES") or (SKILL / "references"))

SOURCE_DISPOSITION_ID = "dtcr/source-disposition/v1"

# The C0 receipt's leak-scan law, executable. Its denominator is deliberately
# every reachable reference byte and not the schemas alone: finding C-2 got
# through because a clean tip tree was read as a clean subject.
LOCATOR_SHAPES = re.compile(r"/Users/|~/|Downloads|drive\.google|file://")
# Every byte sequence admitted, longest first so a specific literal is consumed
# before a shorter one inside it. The receipt records the first two; the other
# three are the guard that refuses locators and the prose describing the probe
# that found the guard was needed, which the receipt's author adjudicated by eye
# and which this scan has to carry explicitly to reach the same result.
#
# The list is literals, not shapes, and that is the point: a class-shaped
# exemption ("anything in a description") would swallow a real locator written
# into a description. A reword that breaks one of these entries turns this scan
# red and asks a person to re-adjudicate it, which is the law working.
PERMITTED_LOCATORS = (
    ("~/example-local-folder/example-source.pdf",
     "DTCR-XC-SP-002 shows file_name refuses a machine-local location, so it holds one"),
    ("/Users/example/checkout/domain/order.go",
     "DTCR-XC-CU-003 shows changed_paths refuses an absolute path, same reason"),
    ("^(?:file:|/Users/|/home/|~/)",
     "candidate-record locator.identity: the guard that does the refusing"),
    ("file:///Users/...",
     "public-private-capability.md: the elided probe that showed the guard was needed"),
    ("`file://` URIs",
     "public-private-capability.md: the leak-scan obligation naming the shape it scans for"),
)

MUTABLE_SUBJECTS = ("main", "HEAD", "latest", "refs/heads/main", "origin/main")
EXACT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
PROMOTED_STRING = "PROMOTED_BY_CONTROL"


class Red(Exception):
    """A control failed. Carries the reason it failed, never a bare status."""


# --------------------------------------------------------------------------
# tree discovery -- everything downstream counts what this returns
# --------------------------------------------------------------------------

def load_schemas() -> dict[str, dict[str, Any]]:
    """schema_id -> schema document, for every schema file in the tree."""
    files = sorted((REFERENCES / "schemas").glob("*.json"))
    if not files:
        raise Red(f"no schemas found under {REFERENCES / 'schemas'}")
    schemas: dict[str, dict[str, Any]] = {}
    for path in files:
        document = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(document)
        identity = document.get("properties", {}).get("schema", {}).get("const")
        if not isinstance(identity, str):
            raise Red(f"{path.name}: no properties.schema.const, so nothing can name it")
        if identity in schemas:
            raise Red(f"two schemas claim the identity {identity}")
        schemas[identity] = document
    return schemas


def positive_instances(schemas: dict[str, dict[str, Any]]) -> list[tuple[str, str, Any]]:
    """(schema_id, label, instance) for every positive case the tree declares.

    Two shapes exist and are counted as one denominator: an `examples` array
    inside the schema, and an `x-positive-instance` pointing at a file. A suite
    that knew only about the first would silently count 7 where the tree holds 8.
    """
    found: list[tuple[str, str, Any]] = []
    for identity, document in schemas.items():
        for index, example in enumerate(document.get("examples", [])):
            found.append((identity, f"{identity}#examples[{index}]", example))
        external = document.get("x-positive-instance")
        if external:
            path = (REFERENCES / "schemas" / external).resolve()
            found.append((identity, str(path.name), json.loads(path.read_text(encoding="utf-8"))))
    return found


def refusal_controls(
    schemas: dict[str, dict[str, Any]], positives: list[tuple[str, str, Any]]
) -> list[dict[str, Any]]:
    """Every control the tree declares, from both places it declares them."""
    controls: list[dict[str, Any]] = []
    for identity, document in schemas.items():
        for control in document.get("x-refusal-controls", []):
            controls.append({
                "case_id": control["case_id"],
                "schema_id": identity,
                "refused_by": control["refused_by"],
                "instance": control["instance"],
                "origin": "x-refusal-controls",
            })
    for identity, label, instance in positives:
        if identity != SOURCE_DISPOSITION_ID or not isinstance(instance, dict):
            continue
        for disposition in instance.get("dispositions", []):
            control = disposition.get("negative_control")
            if control is None:
                continue
            controls.append({
                "case_id": control["case_id"],
                "schema_id": control["schema_id"],
                "refused_by": control["refused_by"],
                "instance": control["instance"],
                "origin": f"{label}:{disposition['disposition_id']}",
            })
    seen: set[str] = set()
    for control in controls:
        key = f"{control['schema_id']}/{control['case_id']}"
        if key in seen:
            raise Red(f"two controls share the identity {key}; a failure could not name one")
        seen.add(key)
    return controls


# --------------------------------------------------------------------------
# knockout
# --------------------------------------------------------------------------

def parse_keyword_path(path: str) -> list[str | int]:
    segments: list[str | int] = []
    for token in path.split("."):
        head, *indices = re.split(r"\[(\d+)\]", token)
        if head:
            segments.append(head)
        segments.extend(int(value) for value in indices if value != "")
    return segments


def remove_keyword(document: Any, path: str) -> None:
    """Delete exactly the keyword `path` names, and nothing else.

    The one licensed extra deletion is the `not: {}` trap: emptying a `not`
    turns it from one guard into a refusal of everything, so the knockout would
    stay red and credit the guard it was trying to disprove.
    """
    segments = parse_keyword_path(path)
    trail: list[tuple[Any, str | int]] = []
    node = document
    for segment in segments:
        trail.append((node, segment))
        try:
            node = node[segment]
        except (KeyError, IndexError, TypeError) as exc:
            raise Red(f"refused_by names {path!r}, which does not resolve in the schema") from exc
    parent, key = trail[-1]
    del parent[key]
    if parent == {} and len(trail) >= 2:
        grandparent, parent_key = trail[-2]
        if parent_key == "not":
            del grandparent[parent_key]


def knock_out(schema: dict[str, Any], refused_by: str) -> dict[str, Any]:
    mutated = copy.deepcopy(schema)
    for path in refused_by.split(" and "):
        remove_keyword(mutated, path.strip())
    return mutated


# --------------------------------------------------------------------------
# the three receipt-derived control classes
# --------------------------------------------------------------------------

def const_pinned_keys(document: Any) -> dict[str, Any]:
    """Property name -> pinned value, for every `{"const": x}` in the schema.

    Derived rather than listed so a lane a sibling adds is probed on the run it
    lands, not on the run somebody remembers to extend a constant.
    """
    pinned: dict[str, Any] = {}

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "properties" and isinstance(value, dict):
                    for name, subschema in value.items():
                        if (
                            isinstance(subschema, dict)
                            and set(subschema) == {"const"}
                            and not isinstance(subschema["const"], (dict, list))
                        ):
                            pinned[name] = subschema["const"]
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(document)
    return pinned


def locations(instance: Any, prefix: str = "") -> Iterator[tuple[str, list[Any], Any, Any]]:
    """(pointer, container, key, value) for every scalar-bearing slot."""
    if isinstance(instance, dict):
        for key, value in instance.items():
            yield f"{prefix}/{key}", instance, key, value
            yield from locations(value, f"{prefix}/{key}")
    elif isinstance(instance, list):
        for index, value in enumerate(instance):
            yield f"{prefix}/{index}", instance, index, value
            yield from locations(value, f"{prefix}/{index}")


def probe(validator: Draft202012Validator, instance: Any, pointer: str, replacement: Any) -> bool:
    """True when replacing the value at `pointer` makes the schema refuse it."""
    mutated = copy.deepcopy(instance)
    node = mutated
    parts = [part for part in pointer.split("/") if part != ""]
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    last = parts[-1]
    if isinstance(node, list):
        node[int(last)] = replacement
    else:
        node[last] = replacement
    return not validator.is_valid(mutated)


def leak_scan() -> tuple[int, list[str]]:
    """Scan every reachable reference byte, permitting only the declared values."""
    findings: list[str] = []
    files = sorted(path for path in REFERENCES.rglob("*") if path.is_file())
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for permitted, _why in PERMITTED_LOCATORS:
            text = text.replace(permitted, "")
        for match in LOCATOR_SHAPES.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                f"{path.relative_to(REFERENCES)}:{line}: private-locator shape "
                f"{match.group(0)!r} is not on the permitted synthetic list"
            )
    return len(files), findings


# --------------------------------------------------------------------------

def main() -> int:
    failures: list[str] = []
    try:
        schemas = load_schemas()
        positives = positive_instances(schemas)
        controls = refusal_controls(schemas, positives)
    except (Red, KeyError, json.JSONDecodeError) as exc:
        print(f"DTCR-SELFTEST-RED tree is unreadable: {exc}", file=sys.stderr)
        return 2

    validators = {identity: Draft202012Validator(doc) for identity, doc in schemas.items()}

    # 1. positives. Run first and reported first: a refusal credited to a suite
    #    that was already red proves nothing about the guard it names.
    for identity, label, instance in positives:
        errors = sorted(validators[identity].iter_errors(instance), key=str)
        if errors:
            failures.append(f"positive instance {label} does not validate: {errors[0].message}")

    # 2. every declared control is refused, by the schema its record names.
    # 3. and refused by the keyword that record names, not by something else.
    knockouts_discriminating = 0
    for control in controls:
        identity, case_id = control["schema_id"], control["case_id"]
        validator = validators.get(identity)
        if validator is None:
            failures.append(f"control {case_id} names schema {identity}, which is not in the tree")
            continue
        if validator.is_valid(control["instance"]):
            failures.append(f"control {case_id} is not refused by {identity} at all")
            continue
        try:
            mutated = knock_out(schemas[identity], control["refused_by"])
        except Red as exc:
            failures.append(f"control {case_id}: {exc}")
            continue
        errors = sorted(Draft202012Validator(mutated).iter_errors(control["instance"]), key=str)
        if errors:
            failures.append(
                f"control {case_id} is still refused after {control['refused_by']!r} was "
                f"removed, so it does not discriminate the guard it names: {errors[0].message}"
            )
            continue
        knockouts_discriminating += 1

    # 4. private-locator leak controls over every reachable reference byte.
    scanned, leaks = leak_scan()
    failures.extend(leaks)

    # 5/6. mutable-subject and promotion probes, over the in-schema examples.
    # The external positive instance is excluded on purpose: it carries the
    # deliberately unconstrained `negative_control.instance` payloads, where a
    # mutation reaches no keyword and a passing probe would mean nothing.
    subject_probes = promotion_probes = 0
    for identity, document in schemas.items():
        validator = validators[identity]
        pinned = const_pinned_keys(document)
        for index, example in enumerate(document.get("examples", [])):
            label = f"{identity}#examples[{index}]"
            for pointer, _, key, value in locations(example):
                if (
                    isinstance(key, str)
                    and key.endswith("_commit")
                    and isinstance(value, str)
                    and EXACT_COMMIT.match(value)
                ):
                    for mutable in MUTABLE_SUBJECTS:
                        subject_probes += 1
                        if not probe(validator, example, pointer, mutable):
                            failures.append(
                                f"{label}{pointer}: mutable subject {mutable!r} accepted where "
                                f"an exact commit is required"
                            )
                if isinstance(key, str) and key in pinned and pinned[key] == value:
                    promotion_probes += 1
                    promoted = (not value) if isinstance(value, bool) else PROMOTED_STRING
                    if not probe(validator, example, pointer, promoted):
                        failures.append(
                            f"{label}{pointer}: pinned value {value!r} was promoted to "
                            f"{promoted!r} and the schema accepted it"
                        )

    if subject_probes == 0 or promotion_probes == 0:
        failures.append(
            "the mutable-subject or promotion denominator is zero, so those lanes "
            "reported green without probing anything"
        )

    # 7. the inventory in cases.json cannot drift from what actually ran.
    inventory = json.loads((SKILL / "cases.json").read_text(encoding="utf-8"))
    for field, executed_names in (
        ("controls", sorted(f"{c['schema_id']}/{c['case_id']}" for c in controls)),
        ("positives", sorted(label for _, label, _ in positives)),
    ):
        declared = sorted(inventory[field])
        if declared != executed_names:
            for name in sorted(set(declared) - set(executed_names)):
                failures.append(f"cases.json declares a {field[:-1]} that did not run: {name}")
            for name in sorted(set(executed_names) - set(declared)):
                failures.append(f"a {field[:-1]} ran that cases.json does not declare: {name}")

    # 8. The probe denominators are derived, which means a guard that is removed
    #    also removes its own probe: the lane reports the same green over a
    #    smaller denominator. Growth is expected and needs no edit here; shrink
    #    is HARNESS_DENOMINATOR_SHRUNK and is refused against a recorded floor.
    for field, counted in (
        ("mutable_subject_probes", subject_probes),
        ("promotion_probes", promotion_probes),
        ("leak_scan_files", scanned),
    ):
        floor = inventory["denominator_floors"][field]
        if counted < floor:
            failures.append(
                f"{field} counted {counted} against a floor of {floor}: a guard was removed "
                f"along with the probe that would have caught it"
            )

    print(
        f"subject={REFERENCES} schemas={len(schemas)} positives={len(positives)} "
        f"controls={len(controls)} knockouts={knockouts_discriminating} "
        f"leak_scan_files={scanned} mutable_subject_probes={subject_probes} "
        f"promotion_probes={promotion_probes}"
    )
    if failures:
        for failure in failures:
            print(f"DTCR-SELFTEST-RED {failure}", file=sys.stderr)
        return 2
    print(
        f"DTCR-SELFTEST-GREEN {len(positives)} positive instances validate, "
        f"{len(controls)} controls refused, {knockouts_discriminating} of {len(controls)} "
        f"discriminating under knockout of their own named keyword"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
