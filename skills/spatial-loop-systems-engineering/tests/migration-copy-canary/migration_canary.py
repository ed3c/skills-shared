#!/usr/bin/env python3
"""Two oracles over one migration/copy pair, so their disagreement is the proof.

`compat`  the legacy caller surface only: `PASS` / `FAIL` / `ABSENT` plus the
          human-admit override and the unknown-input rejection. This is what a
          "compatibility test passed, the migration is done" claim rests on.
`parity`  a differential over the source's whole declared input domain. It is
          the only one of the two that can see a dropped decision branch.

Both arms receive identical inputs and one attempt each. No network, no model,
no clock. `--target` points the same oracles at a mutated copy of the target so
`verify.sh` can prove, on one set of bytes, that `compat` stays green while
`parity` goes red.

Exit: 0 the oracle held, 2 the oracle found a named mismatch, 64 unusable input.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import importlib.util  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Callable  # noqa: E402

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "fixtures" / "source_decide.py"
TARGET = HERE / "fixtures" / "target_decide.py"

UNKNOWN_INPUT = "NOT_A_DECLARED_EVIDENCE_STATE"


class OracleError(Exception):
    """Input could not be loaded at all. Not an oracle result."""


def load(path: Path, name: str) -> Any:
    if not path.is_file():
        raise OracleError(f"module absent: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise OracleError(f"module not importable: {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - any import failure is unusable input
        raise OracleError(f"module failed to import: {path}: {exc}") from exc
    for attribute in ("decide",):
        if not callable(getattr(module, attribute, None)):
            raise OracleError(f"module {path} does not expose {attribute}()")
    return module


def observe(decide: Callable[..., str], state: str, admit: bool) -> str:
    """One observation, with a raised exception recorded rather than swallowed."""
    try:
        return f"RETURN:{decide(state, admit)}"
    except ValueError as exc:
        return f"RAISE:ValueError:{exc}"


def differential(
    source: Any, target: Any, states: tuple[str, ...], label: str
) -> list[str]:
    findings: list[str] = []
    for state in states:
        for admit in (False, True):
            want = observe(source.decide, state, admit)
            got = observe(target.decide, state, admit)
            if want != got:
                findings.append(
                    f"{label}_MISMATCH state={state} human_admit_required={admit} "
                    f"source={want} target={got}"
                )
    return findings


def unknown_input_parity(source: Any, target: Any) -> list[str]:
    want = observe(source.decide, UNKNOWN_INPUT, False)
    got = observe(target.decide, UNKNOWN_INPUT, False)
    if not want.startswith("RAISE:ValueError"):
        return [f"SOURCE_ACCEPTS_UNKNOWN_INPUT {want}"]
    if want != got:
        return [f"UNKNOWN_INPUT_MISMATCH source={want} target={got}"]
    return []


def compat(source: Any, target: Any) -> tuple[list[str], int]:
    states = tuple(source.LEGACY_COMPATIBILITY_STATES)
    findings = differential(source, target, states, "COMPAT")
    findings += unknown_input_parity(source, target)
    return findings, len(states) * 2 + 1


def parity(source: Any, target: Any) -> tuple[list[str], int]:
    states = tuple(source.KNOWN_EVIDENCE_STATES)
    findings = differential(source, target, states, "PARITY")
    findings += unknown_input_parity(source, target)
    return findings, len(states) * 2 + 1


ORACLES = {"compat": compat, "parity": parity}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", choices=(*ORACLES, "both"), default="both")
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--target", type=Path, default=TARGET)
    args = parser.parse_args(argv)

    try:
        source = load(args.source.resolve(), "canary_source_decide")
        target = load(args.target.resolve(), "canary_target_decide")
        for attribute in ("KNOWN_EVIDENCE_STATES", "LEGACY_COMPATIBILITY_STATES"):
            if not getattr(source, attribute, None):
                raise OracleError(f"source does not declare {attribute}")
    except OracleError as exc:
        print(f"MIGRATION-CANARY-UNUSABLE {exc}", file=sys.stderr)
        return 64

    selected = tuple(ORACLES) if args.oracle == "both" else (args.oracle,)
    findings: list[str] = []
    for name in selected:
        oracle_findings, observations = ORACLES[name](source, target)
        verdict = "RED" if oracle_findings else "GREEN"
        print(f"{name.upper()} {verdict} observations={observations}")
        findings.extend(oracle_findings)

    if findings:
        for finding in findings:
            print(f"MIGRATION-CANARY-RED {finding}", file=sys.stderr)
        return 2
    print(
        f"MIGRATION-CANARY-GREEN oracles={','.join(selected)} "
        f"target={args.target.name}; fixture evidence only, no live runtime claim"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
