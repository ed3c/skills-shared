#!/usr/bin/env python3
"""Mechanically verify self-contained decision HTML invariants."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# `(https?:)?//` also catches protocol-relative references such as
# `src="//cdn.example/x.js"`, which load externally but carry no scheme.
EXTERNAL_RES = re.compile(
    r'(src|href)\s*=\s*["\'](https?:)?//|@import\s+["\']?(https?:)?//|'
    r'url\(\s*["\']?(https?:)?//',
    re.IGNORECASE,
)

GOOD_FIXTURE = (
    "<title>決策面 selftest 樣本</title>\n"
    '<div class="mast">\n'
    "  <p>本頁為投影非 SSOT。快照 2026-01-01。</p>\n"
    "</div>\n"
    "<section>\n"
    '  <form id="quiz">\n'
    '    <label><input type="radio" name="q1" value="a"> A</label>\n'
    '    <label><input type="radio" name="q1" value="b"> B</label>\n'
    '    <button onclick="grade()">交卷</button>\n'
    "    <p>全對才算通過。</p>\n"
    "  </form>\n"
    "</section>\n"
    "<script>function grade(){return true}</script>\n"
)


def run_checks(text: str) -> list[tuple[str, bool, str]]:
    """Return invariant check results for an HTML string."""
    results: list[tuple[str, bool, str]] = []

    def add(name: str, ok: bool, evidence: str) -> None:
        results.append((name, ok, evidence))

    match = re.search(r"本頁為投影非 SSOT|投影非 SSOT", text)
    add("declare", bool(match), match.group(0) if match else "缺投影非 SSOT 宣告")

    match = re.search(r"快照[^\n<]{0,40}?(20\d{2}-\d{2}-\d{2})", text)
    evidence = f"快照日期 {match.group(1)}" if match else "缺快照日期"
    add("snapshot", bool(match), evidence)

    external = EXTERNAL_RES.findall(text)
    evidence = "無外部資源載入" if not external else f"外部資源 {len(external)} 處"
    add("selfhost", not external, evidence)

    has_radio = 'type="radio"' in text
    has_grade = re.search(r"function\s+grade|grade\s*=\s*\(", text) is not None
    has_criterion = "全對" in text
    quiz_ok = has_radio and has_grade and has_criterion
    evidence = (
        "radio＋判卷函式＋全對判準齊"
        if quiz_ok
        else f"quiz 缺件 radio={has_radio}, grade={has_grade}, 全對={has_criterion}"
    )
    add("quiz", quiz_ok, evidence)

    match = re.search(r"<title>([^<]{1,120})</title>", text)
    add("title", bool(match), match.group(1) if match else "缺 title")
    return results


def report(results: list[tuple[str, bool, str]], label: str) -> bool:
    """Print check results and return true only when all pass."""
    all_ok = True
    print(f"check_decision_html — {label}")
    for name, ok, evidence in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:8s} {evidence}")
        all_ok = all_ok and ok
    return all_ok


def selftest() -> int:
    """Run synthetic good and hollow positive controls."""
    if not report(run_checks(GOOD_FIXTURE), "good synthetic fixture"):
        print("SELFTEST FAIL: good fixture should pass", file=sys.stderr)
        return 2
    hollow = GOOD_FIXTURE.replace("本頁為投影非 SSOT", "")
    hollow = hollow.replace('type="radio"', 'type="_x"')
    failed = [name for name, ok, _ in run_checks(hollow) if not ok]
    if "declare" in failed and "quiz" in failed:
        print("  [PASS] hollow   declare and quiz defects detected")
        print("SELFTEST PASS")
        return 0
    print("SELFTEST FAIL: hollow fixture was not distinguished", file=sys.stderr)
    return 2


def main(argv: list[str]) -> int:
    """CLI entrypoint."""
    if len(argv) == 2 and argv[1] == "--selftest":
        return selftest()
    if len(argv) != 2:
        print(
            "usage: check_decision_html.py <decision.html> | --selftest",
            file=sys.stderr,
        )
        return 1
    target = Path(argv[1])
    if not target.is_file():
        print(f"ERROR: file does not exist: {target}", file=sys.stderr)
        return 1
    ok = report(run_checks(target.read_text(encoding="utf-8")), str(target))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
