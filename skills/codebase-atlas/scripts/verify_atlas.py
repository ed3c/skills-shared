#!/usr/bin/env python3
"""Deterministic checks for a generated Codebase Atlas HTML artifact.

This script intentionally separates deterministic static gates from optional browser execution.
It returns 0 on PASS, 2 on verification failure, and 64 on usage/runtime dependency errors.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_TOKENS = [
    "ATLAS_DATA",
    "__ATLAS_DEBUG__",
    "WHAT IT DOES",
    "HOW IT'S BUILT",
    "TRACE ONE STEP",
    "RESET VIEW",
    "RESUME FLOW",
    "Content-Security-Policy",
    "connect-src 'none'",
]
FORBIDDEN_EXTERNAL = [
    r'<script[^>]+src=["\']https?://',
    r'<link[^>]+href=["\']https?://',
    r'<img[^>]+src=["\']https?://',
    r'@import\s+url\(["\']?https?://',
]
SENSITIVE_PATTERNS = {
    "absolute-user-path": r"/(?:Users|home)/[^/\s<]+/",
    "mount-path": r"/mnt/[^\s<]+",
    "private-url": r"https?://[^\s<]+",
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
}


def fail(msg: str, report: dict) -> None:
    report.setdefault("failures", []).append(msg)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", type=Path)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--forbid-prefix", action="append", default=[])
    args = ap.parse_args()

    if not args.html.exists():
        print(f"usage/runtime error: file not found: {args.html}", file=sys.stderr)
        return 64

    text = args.html.read_text(encoding="utf-8", errors="replace")
    report = {
        "artifact": str(args.html),
        "status": "PASS",
        "checks": {},
        "failures": [],
    }

    for tok in REQUIRED_TOKENS:
        ok = tok in text
        report["checks"][f"token:{tok}"] = ok
        if not ok:
            fail(f"missing required token: {tok}", report)

    for pat in FORBIDDEN_EXTERNAL:
        hit = bool(re.search(pat, text, re.I))
        report["checks"][f"external:{pat}"] = not hit
        if hit:
            fail(f"network-loaded dependency matched: {pat}", report)

    sample_markers = ["sample / replace-me", "not measured"]
    for marker in sample_markers:
        hit = marker in text
        report["checks"][f"sample:{marker}"] = not hit
        if hit:
            fail(f"sample/unmeasured marker remains in final artifact: {marker}", report)

    for prefix in args.forbid_prefix:
        hit = prefix in text
        report["checks"][f"forbid-prefix:{prefix}"] = not hit
        if hit:
            fail(f"forbidden prefix found: {prefix}", report)

    # Sensitive patterns are warnings unless they are clearly local/private paths. URLs may be
    # harmless inside explanatory text, so callers should review every match in a share-safety pass.
    findings = {}
    for name, pat in SENSITIVE_PATTERNS.items():
        matches = re.findall(pat, text, re.I)
        findings[name] = matches[:20]
    report["share_safety_findings"] = findings
    for hard in ("absolute-user-path", "mount-path"):
        if findings[hard]:
            fail(f"share-safety finding: {hard}", report)

    # Basic structural sanity.
    for required in ["id=\"meta\"", "id=\"groups\"", "id=\"map\"", "id=\"panel\""]:
        ok = required in text
        report["checks"][f"dom:{required}"] = ok
        if not ok:
            fail(f"missing required DOM surface: {required}", report)

    if report["failures"]:
        report["status"] = "FAIL"

    out = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(out + "\n", encoding="utf-8")
    print(out)
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
