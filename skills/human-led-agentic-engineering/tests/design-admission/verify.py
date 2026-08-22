#!/usr/bin/env python3
from __future__ import annotations
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "SKILL.md"
MODULE = ROOT / "modules" / "domain-profile.md"
SCHEMA = ROOT / "references" / "design-admission.schema.json"

FAILS: list[str] = []

def check_design(receipt: dict, *, builder: str, adversary: str, material: bool = True, model_consensus: bool = False, claimed_lane: str = "DETERMINISTIC") -> list[str]:
    out: list[str] = []
    if material and receipt.get("disposition") != "HUMAN_DESIGN_ADMITTED": out.append("MATERIAL_DESIGN_WITHOUT_HUMAN_ADMIT")
    if builder == adversary: out.append("DESIGN_ADVERSARY_EQUALS_BUILDER")
    if model_consensus and receipt.get("disposition") == "HUMAN_DESIGN_ADMITTED" and not receipt.get("human_actor"): out.append("MODEL_CONSENSUS_AUTO_ADMITS_DESIGN")
    for item in receipt.get("unresolved_dissent", []):
        if not item.get("human_disposition"): out.append("UNRESOLVED_MATERIAL_DISSENT_DROPPED")
    subject = receipt.get("subject", "")
    if not subject.startswith("commit:") or len(subject.removeprefix("commit:")) != 40: out.append("MUTABLE_OR_WRONG_SUBJECT")
    if claimed_lane in {"LIVE", "RELEASE", "PRODUCTION"}: out.append("DETERMINISTIC_PASS_PROMOTED_TO_LIVE_OR_RELEASE")
    return out

base = {"schema_version":"human-design-admission/v1","repository":"owner/repo","subject":"commit:"+"a"*40,"problem_statement_digest":"sha256:"+"1"*64,"design_digest":"sha256:"+"2"*64,"human_actor":"human","admitted_at":"2026-08-22T00:00:00Z","adversary_receipt_digest":"sha256:"+"3"*64,"material_decisions":["keep Human authority"],"non_goals":[],"unresolved_dissent":[{"claim":"risk","human_disposition":"accepted"}],"disposition":"HUMAN_DESIGN_ADMITTED"}
if check_design(base,builder="builder",adversary="adversary"): FAILS.append("positive fixture failed")

mutations=[]
r=copy.deepcopy(base);r["disposition"]="PENDING";mutations.append((r,"builder","adversary",False,"DETERMINISTIC","MATERIAL_DESIGN_WITHOUT_HUMAN_ADMIT"))
mutations.append((copy.deepcopy(base),"same","same",False,"DETERMINISTIC","DESIGN_ADVERSARY_EQUALS_BUILDER"))
r=copy.deepcopy(base);r["human_actor"]="";mutations.append((r,"builder","adversary",True,"DETERMINISTIC","MODEL_CONSENSUS_AUTO_ADMITS_DESIGN"))
r=copy.deepcopy(base);r["unresolved_dissent"][0]["human_disposition"]="";mutations.append((r,"builder","adversary",False,"DETERMINISTIC","UNRESOLVED_MATERIAL_DISSENT_DROPPED"))
r=copy.deepcopy(base);r["subject"]="main";mutations.append((r,"builder","adversary",False,"DETERMINISTIC","MUTABLE_OR_WRONG_SUBJECT"))
mutations.append((copy.deepcopy(base),"builder","adversary",False,"RELEASE","DETERMINISTIC_PASS_PROMOTED_TO_LIVE_OR_RELEASE"))
for receipt,builder,adversary,consensus,lane,expected in mutations:
    if expected not in check_design(receipt,builder=builder,adversary=adversary,model_consensus=consensus,claimed_lane=lane): FAILS.append(f"mutation survived: {expected}")

skill=SKILL.read_text(encoding="utf-8"); module=MODULE.read_text(encoding="utf-8")
for marker in ["PORTABLE_CORE_START","PORTABLE_CORE_END","CORE-LAW-001","CORE-LAW-005","modules/domain-profile.md"]:
    if marker not in skill: FAILS.append(f"portable marker missing: {marker}")
for heading in ["## Trigger","## Non-trigger","## Assumptions","## Evidence ceiling","## Fallback","## Forbidden overrides"]:
    if heading not in module: FAILS.append(f"domain profile heading missing: {heading}")
core=skill.split("<!-- PORTABLE_CORE_START -->",1)[1].split("<!-- PORTABLE_CORE_END -->",1)[0].casefold()
for forbidden in ["roborev","kata","agentsview","ghosthub","kenn forge"]:
    if forbidden in core: FAILS.append(f"provider leaked into core: {forbidden}")
schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
if schema.get("properties",{}).get("disposition",{}).get("const")!="HUMAN_DESIGN_ADMITTED": FAILS.append("design schema lost Human disposition authority")
if FAILS:
    [print("HUMAN-DESIGN-RED",x) for x in FAILS]; raise SystemExit(2)
print("HUMAN-DESIGN-GREEN controls=7 provider_boundary=PASS evidence_ceiling=DETERMINISTIC")
