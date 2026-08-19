#!/usr/bin/env python3
"""Render a checked problem-closure ledger to deterministic Markdown."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
CHECKER=HERE/"check_problem_closure.py"
spec=importlib.util.spec_from_file_location("closure_checker",CHECKER)
checker=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(checker)

def _cell(value:object)->str:
    return str(value).replace("\\","\\\\").replace("|","\\|").replace("\r"," ").replace("\n"," ")

def render(data:dict)->str:
    summary=checker.check_ledger(data)
    problems={item["problem_id"]:item for item in data["problems"]}
    lines=[
        "# Problem Closure Projection","",
        "> Generated projection. Machine truth remains the checked JSON ledger; this Markdown is not closure authority.","",
        f"Problems: **{summary['problem_count']}**  ",
        f"Residual: **{len(summary['residual_problem_ids'])}**  ",
        f"Source manifest: `{summary['source_manifest_sha256']}`","",
        "| Problem | Source | Repo subject | Issues | Shadow | Closure | Residual gaps |",
        "|---|---|---|---|---|---|---|",
    ]
    for pid in data["denominator"]["problem_ids"]:
        problem=problems[pid]; source=problem["source"]; rs=problem["repo_subject"]
        source_text=f"{_cell(source['kind'])} `{_cell(source['identity'])}` @ `{_cell(source['location'])}`"
        repo_text=f"`{_cell(rs['repo'])}@{rs['commit']}` tree `{rs['tree']}`"
        issues=", ".join(f"#{n}" for n in problem["issue_nodes"]) or "—"
        gaps="; ".join(_cell(v) for v in problem["residual_gaps"]) or "—"
        lines.append(f"| `{_cell(pid)}` — {_cell(problem['claim'])} | {source_text} | {repo_text} | {issues} | `{problem['shadow_verdict']}` | `{problem['closure']}` | {gaps} |")
    lines.extend(["","## Residual problem IDs",""])
    lines.extend([f"- `{pid}`" for pid in summary["residual_problem_ids"]] or ["- none"])
    lines.extend(["",f"Evidence ceiling: `{summary['evidence_ceiling']}`",""])
    return "\n".join(lines)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("ledger"); ap.add_argument("--output")
    a=ap.parse_args(); data=json.loads(Path(a.ledger).read_text(encoding="utf-8"))
    text=render(data)
    if a.output: Path(a.output).write_text(text,encoding="utf-8")
    else: print(text,end="")
    return 0

if __name__=="__main__": raise SystemExit(main())
