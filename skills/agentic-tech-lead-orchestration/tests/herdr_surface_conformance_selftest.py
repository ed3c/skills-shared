#!/usr/bin/env python3
"""Fail whenever the Herdr observer or its fixtures name a field herdr does not publish.

This is the control that #466 lacked. The 2026-08-21 pass froze the observer
contract against AgentInfo alone, never checked the sibling API objects of the
same schema document, and then recorded the resulting gaps as an upstream
blocker. Nothing mechanical could catch that, because no check ever compared the
names the observer reads against the names herdr actually publishes.

EVIDENCE CEILING. The frozen snapshot at
`references/contracts/herdr-agent-surface.observed.json` is STATIC evidence: a
green run proves the contract matches a captured schema document, never that a
live herdr socket returns these fields, and never that a lifecycle ran. `--live`
raises that to a read-only comparison against the installed herdr's own schema;
it still proves nothing about a running agent.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
OBSERVER = SKILL / "scripts" / "herdr_runtime_observer.py"
SURFACE = SKILL / "references" / "contracts" / "herdr-agent-surface.observed.json"
RECEIPT_SCHEMA = SKILL / "references" / "contracts" / "herdr-observer-receipt.schema.json"
FIXTURE_MODULE = HERE / "herdr_observer_selftest.py"
FIXTURE_FUNCTIONS = (
    "running_agent", "running_explain", "done_agent", "done_explain", "blocked_agent",
)
SOURCE_FIELDS = ("observation_time_source", "process_facts_source", "cleanup_source")


def normalise(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def published_names(surface: dict[str, Any]) -> set[str]:
    """Every field name herdr 0.8.0 publishes, plus the typed substitution keys."""
    names: set[str] = set()
    for key in (
        "agent_info_properties",
        "agent_session_info_properties",
        "pane_process_info_properties",
        "pane_process_info_process_properties",
        "agent_explain_root_keys",
        "success_envelope_properties",
    ):
        names.update(surface[key])
    names.update(surface["typed_substitutions"])
    return {normalise(name) for name in names}


def observer_call_sites(path: Path) -> list[tuple[int, tuple[str, ...]]]:
    """Every `_find(value, *names)` call site in the observer, as alias groups.

    A call site is the unit, not the name: `_find` returns the first alias that
    resolves, so carrying a non-herdr alias next to a herdr one is correct. The
    #466 defect was a call site where NO name resolved anywhere.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    # `_find`'s own two recursive calls forward the caller's alias group; they
    # name no herdr field of their own and are not call sites.
    finder = next((f for f in functions if f.name == "_find"), None)
    recursive = {id(n) for n in ast.walk(finder)} if finder is not None else set()
    sites: list[tuple[int, tuple[str, ...]]] = []
    for function in [f for f in functions if f.name != "_find"]:
        literal_tuples: dict[str, list[str]] = {}
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, (ast.Tuple, ast.List))
                and node.value.elts
                and all(
                    isinstance(e, ast.Constant) and isinstance(e.value, str)
                    for e in node.value.elts
                )
            ):
                literal_tuples[node.targets[0].id] = [e.value for e in node.value.elts]
        for node in ast.walk(function):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_find"
            ):
                continue
            names: list[str] = []
            for arg in node.args[1:]:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    names.append(arg.value)
                elif (
                    isinstance(arg, ast.Starred)
                    and isinstance(arg.value, ast.Name)
                    and arg.value.id in literal_tuples
                ):
                    names.extend(literal_tuples[arg.value.id])
            if names:
                sites.append((node.lineno, tuple(names)))
    total = sum(
        1
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "_find"
        and id(n) not in recursive
    )
    if len(sites) != total:
        raise SystemExit(
            f"FATAL: {len(sites)} of {total} `_find` call sites in {path.name} yielded an "
            "extractable alias group; an unreadable call site is an unchecked contract, "
            "not a pass"
        )
    return sites


def load_fixtures() -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("herdr_observer_fixtures", FIXTURE_MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(module)
    return {name: getattr(module, name)() for name in FIXTURE_FUNCTIONS}


def fixture_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(fixture_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(fixture_keys(child))
    return keys


def check_observer(known: set[str], sites: list[tuple[int, tuple[str, ...]]]) -> list[str]:
    failures = []
    for lineno, group in sites:
        if not any(normalise(name) in known for name in group):
            failures.append(
                f"{OBSERVER.name}:{lineno}: no name in alias group {list(group)} exists on any "
                "herdr surface or in the typed substitution table"
            )
    return failures


def check_fixtures(known: set[str], fixtures: dict[str, Any]) -> list[str]:
    failures = []
    for name, value in fixtures.items():
        for key in fixture_keys(value):
            if normalise(key) not in known:
                failures.append(
                    f"{FIXTURE_MODULE.name}:{name}(): key {key!r} is an invented herdr field"
                )
    return failures


def check_enums(surface: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """The receipt enums and the substitution table may not drift apart."""
    failures = []
    for field in SOURCE_FIELDS:
        declared = surface["receipt_source_enums"][field]
        partitioned = set(
            declared["herdr_published"] + declared["substituted"] + declared["not_observed"]
        )
        in_schema = set(schema["properties"][field]["enum"])
        if partitioned != in_schema:
            failures.append(
                f"{field}: frozen partition {sorted(partitioned)} != receipt schema enum "
                f"{sorted(in_schema)}"
            )
        substituted = {
            entry["value"]
            for entry in surface["typed_substitutions"].values()
            if entry["receipt_field"] == field
        }
        if substituted and substituted != set(declared["substituted"]):
            failures.append(
                f"{field}: typed_substitutions values {sorted(substituted)} != declared "
                f"substituted set {sorted(declared['substituted'])}"
            )
        unreachable = surface["receipt_source_values_unreachable_against_captured_version"].get(
            field, []
        )
        for value in unreachable:
            if value not in declared["herdr_published"]:
                failures.append(
                    f"{field}: {value!r} is declared unreachable against herdr "
                    f"{surface['provenance']['herdr_version']} but is not a herdr-published value"
                )
    return failures


def check_snapshot(surface: dict[str, Any]) -> list[str]:
    """process_id is published by herdr 0.8.0 — only AgentInfo lacks it."""
    failures = []
    absent = {normalise(name) for name in surface["absent_from_every_surface"]}
    for name in ("process_id", "pid"):
        if name in absent:
            failures.append(
                f"absent_from_every_surface carries {name!r}; herdr 0.8.0 publishes it on "
                "PaneProcessInfoProcess. This exact false entry froze the 2026-08-21 contract."
            )
    if "process_id" not in surface["absent_from_agent_info_but_published_elsewhere"]:
        failures.append(
            "absent_from_agent_info_but_published_elsewhere lost its process_id anchor"
        )
    return failures


def check_live(surface: dict[str, Any]) -> list[str]:
    proc = subprocess.run(
        ["herdr", "api", "schema", "--json"], text=True, capture_output=True
    )
    if proc.returncode:
        return [f"herdr api schema failed ({proc.returncode}): {proc.stderr.strip()[:200]}"]
    defs = json.loads(proc.stdout)["schemas"]["success_response"]["$defs"]
    expected = {
        "AgentInfo.properties": surface["agent_info_properties"],
        "AgentInfo.required": surface["agent_info_required"],
        "AgentStatus.enum": surface["agent_status_enum"],
        "AgentSessionInfo.properties": surface["agent_session_info_properties"],
        "PaneProcessInfo.properties": surface["pane_process_info_properties"],
        "PaneProcessInfoProcess.properties": surface["pane_process_info_process_properties"],
    }
    live = {
        "AgentInfo.properties": sorted(defs["AgentInfo"]["properties"]),
        "AgentInfo.required": defs["AgentInfo"]["required"],
        "AgentStatus.enum": defs["AgentStatus"]["enum"],
        "AgentSessionInfo.properties": sorted(defs["AgentSessionInfo"]["properties"]),
        "PaneProcessInfo.properties": sorted(defs["PaneProcessInfo"]["properties"]),
        "PaneProcessInfoProcess.properties": sorted(defs["PaneProcessInfoProcess"]["properties"]),
    }
    failures = []
    for label, frozen in expected.items():
        if set(live[label]) != set(frozen):
            drifted = sorted(set(live[label]) ^ set(frozen))
            failures.append(f"{label} drifted: {drifted}")
    return failures


def selftest(surface: dict[str, Any], schema: dict[str, Any], fixtures: dict[str, Any]) -> None:
    """Planted defects. A conformance test with only a positive leg certifies its own fixture."""
    known = published_names(surface)

    invented = check_observer(known, [(999, ("totally_not_a_herdr_field",))])
    assert invented, "an invented herdr field passed the observer check"

    fake_fixture = copy.deepcopy(fixtures)
    fake_fixture["running_agent"]["result"]["agent"]["invented_herdr_field"] = 1
    assert check_fixtures(known, fake_fixture), "an invented fixture key passed the fixture check"

    removed = copy.deepcopy(surface)
    removed["agent_info_properties"] = [
        name for name in removed["agent_info_properties"] if name != "pane_id"
    ]
    removed["pane_process_info_properties"] = [
        name for name in removed["pane_process_info_properties"] if name != "pane_id"
    ]
    assert check_fixtures(published_names(removed), fixtures), (
        "removing pane_id from the frozen surface did not turn the fixture check red"
    )

    renamed = copy.deepcopy(surface)
    renamed["agent_info_properties"] = [
        "agentStatusRenamed" if name == "agent_status" else name
        for name in renamed["agent_info_properties"]
    ]
    renamed["agent_explain_root_keys"] = [
        name for name in renamed["agent_explain_root_keys"] if name != "state"
    ]
    assert check_observer(
        published_names(renamed), observer_call_sites(OBSERVER)
    ), "renaming agent_status on the frozen surface did not turn the observer check red"

    drifted = copy.deepcopy(surface)
    drifted["typed_substitutions"]["cleanup_state"]["value"] = "HERDR_PUBLISHED"
    assert check_enums(drifted, schema), "a substitution claiming HERDR_PUBLISHED was accepted"

    refrozen = copy.deepcopy(surface)
    refrozen["absent_from_every_surface"] = refrozen["absent_from_every_surface"] + ["process_id"]
    assert check_snapshot(refrozen), "re-adding process_id to absent_from_every_surface passed"

    live_leg = "live=NOT_AVAILABLE"
    if shutil.which("herdr") is not None:
        assert not check_live(surface), "the frozen snapshot already disagrees with this herdr"
        stale = copy.deepcopy(surface)
        stale["agent_info_properties"] = stale["agent_info_properties"] + ["not_a_herdr_property"]
        assert check_live(stale), "the live leg accepted a property the installed herdr lacks"
        live_leg = "live=RED_ON_DRIFT"

    print(
        "SELFTEST GREEN: surface conformance goes red on an invented herdr field, an invented "
        "fixture key, a removed or renamed frozen property, a promoted substitution value, and "
        f"a re-frozen process_id ({live_leg})"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    fixtures = load_fixtures()

    if args.selftest:
        selftest(surface, schema, fixtures)
        return 0

    known = published_names(surface)
    sites = observer_call_sites(OBSERVER)
    keys = sorted({key for value in fixtures.values() for key in fixture_keys(value)})
    failures = (
        check_observer(known, sites)
        + check_fixtures(known, fixtures)
        + check_enums(surface, schema)
        + check_snapshot(surface)
    )

    live = "NOT_EXERCISED"
    if args.live:
        if shutil.which("herdr") is None:
            live = "NOT_AVAILABLE"
        else:
            drift = check_live(surface)
            failures += drift
            live = "DRIFTED" if drift else f"OK_{surface['provenance']['herdr_version']}"

    if failures:
        print("herdr-surface-conformance: FAIL")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print(
        f"herdr-surface-conformance: PASS (observer_call_sites={len(sites)} "
        f"observer_names={sum(len(group) for _, group in sites)} fixture_keys={len(keys)} "
        f"substitutions={len(surface['typed_substitutions'])} live={live})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
