#!/usr/bin/env python3
"""Render a checked problem-closure ledger to deterministic Markdown.

The Markdown is a human projection only. The JSON ledger remains machine truth.
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path

HERE=Path(__file__).resolve().parent
CHECKER=HERE/"check_problem_closure.py"
spec=importlib.util.spec_from_file_location("closure_checker",CHECKER)
checker=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(checker)

def render(data:dict)->str:
    summary=checker.check_ledger(data)
    lines=[
      "# Problem Closure Projection",
      "",
      "> Generated projection. Machine truth remains the checked JSON ledger; this Markdown is not closure authority.",
      "",
      f"Problems: **{summary['problem_count']}**  ",
      f"Residual: **{len(summary['residual_problem_ids'])}**",
      "",
      "| Problem | Source | Repo subject | Issues | Shadow | Closure | Residual gaps |",
      "|---|---|---|---|---|---|---|",
    ]
    for p in data["problems"]:
        src=p["source"]
        source=f"{src['kind']} `{src['identity']}` @ `{src['location']}`"
        rs=p["repo_subject"]
        repo=f"`{rs['repo']}@{rs['commit']}` tree `{rs['tree']}`"
        issues=", ".join(f"#{n}" for n in p["issue_nodes"]) or "—"
        gaps="; ".join(p["residual_gaps"]) or "—"
        claim=p["claim"].replace("|","\\|").replace("\n"," ")
        lines.append(f"| `{p['problem_id']}` — {claim} | {source} | {repo} | {issues} | `{p['shadow_verdict']}` | `{p['closure']}` | {gaps} |")
    lines.extend(["", "## Residual problem IDs", ""])
    if summary["residual_problem_ids"]:
        lines.extend(f"- `{pid}`" for pid in summary["residual_problem_ids"])
    else:
        lines.append("- none")
    lines.extend(["", f"Evidence ceiling: `{summary['evidence_ceiling']}`", ""])
    return "\n".join(lines)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("ledger"); ap.add_argument("--output")
    a=ap.parse_args(); data=json.loads(Path(a.ledger).read_text())
    text=render(data)
    if a.output: Path(a.output).write_text(text,encoding="utf-8")
    else: print(text,end="")
    return 0
if __name__=="__main__":raise SystemExit(main())
