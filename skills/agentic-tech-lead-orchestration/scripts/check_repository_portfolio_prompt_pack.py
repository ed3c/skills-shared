#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/"references/repository-portfolio-control/prompt-manifest.json"
COORD="Use subagents. Wait for all agents and consolidate their findings."
REQUIRED_KINDS={"contract","controller","roles","codex-agents","readme","agents-route"}

def validate(value):
    errors=[];kinds=set();combined=[];paths=set()
    if value.get("schema_version")!="agentic-tech-lead/repository-portfolio-prompt-manifest/v1":
        errors.append("schema_version drift")
    if value.get("required_coordinator_instruction")!=COORD:
        errors.append("coordinator instruction drift")
    for item in value.get("files",[]):
        rel=item.get("path","");kind=item.get("kind","");path=ROOT/rel
        if rel in paths:errors.append(f"duplicate path: {rel}")
        paths.add(rel);kinds.add(kind)
        if not path.is_file():errors.append(f"missing file: {rel}");continue
        text=path.read_text(encoding="utf-8");combined.append(text)
        if "/Users/neon/" in text:errors.append(f"machine-local path leaked: {rel}")
    if REQUIRED_KINDS-kinds:errors.append(f"required kinds absent: {sorted(REQUIRED_KINDS-kinds)}")
    text="\n".join(combined)
    if COORD not in text:errors.append("coordinator instruction absent")
    for role in set(value.get("required_roles",[])):
        if role not in text:errors.append(f"role absent: {role}")
    agents=ROOT/"references/repository-portfolio-control/codex-agent-templates.md"
    if agents.is_file():
        body=agents.read_text(encoding="utf-8")
        expected=value.get("expected_sandbox_counts",{})
        if body.count('sandbox_mode = "read-only"')!=expected.get("read-only"):
            errors.append("read-only agent count drift")
        if body.count('sandbox_mode = "workspace-write"')!=expected.get("workspace-write"):
            errors.append("workspace-write agent count drift")
    return errors

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--manifest",type=Path,default=DEFAULT);a=ap.parse_args()
    try:value=json.loads(a.manifest.read_text(encoding="utf-8"))
    except Exception as exc:print(f"FATAL: {exc}",file=sys.stderr);return 64
    errors=validate(value)
    for error in errors:print(f"FAIL: {error}")
    if errors:return 2
    digests={item["path"]:hashlib.sha256((ROOT/item["path"]).read_bytes()).hexdigest() for item in value["files"]}
    print(f"PASS: repository portfolio prompt foundation files={len(value['files'])}")
    print(json.dumps(digests,sort_keys=True))
    return 0
if __name__=="__main__":raise SystemExit(main())
