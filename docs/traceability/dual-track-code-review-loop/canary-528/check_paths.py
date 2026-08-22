#!/usr/bin/env python3
"""Assert every relative evidence path the canary receipt cites resolves.

The receipt is a v0-draft with no frozen schema, so nothing else validates it;
this gate closes exactly the hole a draft leaves open: citing evidence that was
never committed. Zero network. Exits 0 green, 2 red, 64 unusable.

--selftest plants a missing-path mutation in a copy and requires the red.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECEIPT = HERE / "canary-receipt.json"
SHA_SIDECAR = HERE / "canary-receipt.sha256"
PATH_RE = re.compile(r"\b(?:r1|oracle|facts|semantic)/[A-Za-z0-9._-]+")


def cited_paths(text: str) -> set[str]:
    return set(PATH_RE.findall(text))


def run(receipt_path: Path, base: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = receipt_path.read_text(encoding="utf-8")
        json.loads(text)
    except (OSError, ValueError) as error:
        print(f"CANARY-PATHS-INVALID {error}")
        raise SystemExit(64)
    if "/private/tmp/" in text or "/scratchpad/" in text:
        errors.append("receipt still cites a session-scratch absolute path")
    for rel in sorted(cited_paths(text)):
        if rel.endswith("."):
            # the receipt cites a glob family (e.g. live-before-status.*);
            # require at least one committed member of that family
            parent = (base / rel).parent
            stem = rel.rsplit("/", 1)[-1]
            if not (parent.is_dir() and any(p.name.startswith(stem) for p in parent.iterdir())):
                errors.append(f"cited evidence family has no committed member: {rel}*")
        elif not (base / rel).is_file():
            errors.append(f"cited evidence missing from the committed set: {rel}")
    if receipt_path == RECEIPT:
        if not SHA_SIDECAR.is_file():
            errors.append("canary-receipt.sha256 sidecar absent")
        else:
            recorded = SHA_SIDECAR.read_text(encoding="utf-8").split()[0]
            actual = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            if recorded != actual:
                errors.append(f"sha256 sidecar drifted: recorded {recorded[:16]}… actual {actual[:16]}…")
    return errors


def selftest() -> int:
    with tempfile.TemporaryDirectory() as scratch:
        base = Path(scratch)
        mutated = base / "canary-receipt.json"
        doc = json.loads(RECEIPT.read_text(encoding="utf-8"))
        doc["_planted"] = "oracle/this-file-does-not-exist.lanes"
        mutated.write_text(json.dumps(doc), encoding="utf-8")
        if not run(mutated, base):
            print("CANARY-PATHS-SELFTEST-RED planted missing path was not refused")
            return 2
    print("CANARY-PATHS-SELFTEST-GREEN planted missing path refused")
    return 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        code = selftest()
        if code:
            return code
    errors = run(RECEIPT, HERE)
    if errors:
        for error in errors:
            print(f"CANARY-PATHS-RED {error}")
        return 2
    n = len(cited_paths(RECEIPT.read_text(encoding="utf-8")))
    print(f"CANARY-PATHS-GREEN {n} cited evidence path(s) resolve; sha256 sidecar matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
