#!/usr/bin/env python3
"""Matched hermetic A/B over the three frozen knowledge-continuity entrypoints.

What is being compared, and why it is not a rewrite of history
--------------------------------------------------------------
Two arms are real bytes out of this repository's history, frozen under
`fixtures/` at the blob identity git already recorded:

    A  as admitted        blob 99b9af12  (commit 4bfdb08)
    B0 refactor as landed blob 8c095d34  (commit 9fd4c49)

`9fd4c49` took the host names out of the lines that decide whether a Skill
applies, and said so: "Prose further down keeps its wording; that was the agreed
scope." That scope is the finding. The routing lines were de-hosted while the
one line a reader is told to *execute* -- step 1 of the deterministic procedure
-- kept pointing at `.agents/skills/knowledge-continuity/scripts/...`, a
consumer-host projection path that does not exist in this repository. The same
body names the same script twice more, correctly, from the Skill root. No gate
caught it because no gate ever ran the command the document tells a human to
run.

B1 is the live body after this issue repaired that, and after the counts the
body asserts about itself (五條 rules, 六件事 human lane) were made to match the
implementation instead of trailing it by one and two.

So the arms do not differ in the mechanism -- there is one checker, and every
executing arm runs those same bytes. They differ in whether the entrypoint's
own claims bind to it. The report keeps those two lanes apart on purpose:
`functional_output` is what the corpus measured, `claim_closure` is how much of
what the body says about itself is true.

Hermetic: fixtures only, no network, no model, no provider. L4 live runtime and
L5 delivery stay NOT_EXERCISED / HUMAN_ADMIT_REQUIRED and no assertion here can
move them.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import check_knowledge_continuity as kc  # noqa: E402

CHECKER = ROOT / "scripts/check_knowledge_continuity.py"
GATE = ROOT / "scripts/assert_continuity_audit.py"
LIVE_BODY = ROOT / "SKILL.md"

# role, path relative to the Skill root, and the blob git recorded for it.
FROZEN = {
    "A_ADMITTED_HOST_BOUND": (
        "OLD_CANONICAL",
        "tests/refactor-ab/fixtures/old-canonical-SKILL.txt",
        "99b9af12b421f781688bba02ba9f0ccf69eaca26",
    ),
    "B0_DEHOSTED_AS_LANDED": (
        "REFACTOR_AS_LANDED",
        "tests/refactor-ab/fixtures/refactor-as-landed-SKILL.txt",
        "8c095d34607dc0aa45df12fcdf4cef5dd0778129",
    ),
}
LIVE_ARM = "B1_AUDIT_ROUTE_REPAIRED"
ARMS = (*FROZEN, LIVE_ARM)

DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
COMMAND = re.compile(r"python3\s+(\S*check_knowledge_continuity\.py)")
# The count has to sit against the lane it counts. A looser "any number on a
# line that mentions rules" reading swallows 「每修一條就重跑」, which counts
# repair steps, not rules -- and a claim extractor that reports phantom claims
# cannot be used to refuse a treatment.
RULE_CLAIM = re.compile(r"([一二三四五六七八九十]|\d+)\s*條(?:可機械檢查的規則|機械規則|規則|全綠)")
HUMAN_CLAIM = re.compile(r"([一二三四五六七八九十]|\d+)\s*(?:件事|個問題|項)")

# Behaviours the as-admitted body guaranteed. A cleaner structure is not proof
# that they survived, so each one is re-measured against the current rules
# rather than being asserted in prose. Every entry is (document, rule, breaks).
OLD_STRENGTHS: dict[str, tuple[str, str, int]] = {
    "OS-01_table_first_cell_defines_a_code": (
        "# t\n\n## 1. 表\n\n| 代號 | 意義 |\n|---|---|\n| NEG-101 | 不變量 |\n\n照 NEG-101 辦。\n",
        "KC-01",
        0,
    ),
    "OS-02_fenced_labels_are_not_references": (
        "# t\n\n## 1. 圖\n\n```text\n① 判斷 → §7 分支 → NEG-101 風險點\n約 3 條路徑\n```\n",
        "KC-01",
        0,
    ),
    "OS-03_quoted_examples_are_shown_not_used": (
        "# t\n\n## 1. 反例\n\n壞引用長這樣：「NEG-101 也適用」，不要學。\n",
        "KC-01",
        0,
    ),
    "OS-04_iso_dates_are_not_document_codes": (
        "---\nverified_at: 2026-08-06\n---\n\n# t\n\n## 1. 盤點\n\n上次盤點是 2026-08-05，這次是 2026-08-06。\n",
        "KC-01",
        0,
    ),
    "OS-05_well_known_names_are_not_document_codes": (
        "# t\n\n## 1. 交付\n\n每份來源進 SHA-256 manifest，文字用 UTF-8，時間依 ISO-8601。\n",
        "KC-01",
        0,
    ),
    "OS-06_local_section_refs_are_not_breaks": (
        "# t\n\n## 1. 開頭\n\n## 2. 內容\n\n詳見 §1 的說明。\n",
        "KC-02",
        0,
    ),
    "OS-07_external_shorthand_still_fires": (
        "# t\n\n## 1. 開頭\n\n這段照 §7 的裁決辦，NEG-101 也適用。\n",
        "KC-01",
        1,
    ),
    "OS-08_approximate_counts_still_fire": (
        "# t\n\n## 1. 開頭\n\n去重後約 14 列，另有約 10 條。\n",
        "KC-03",
        1,
    ),
}
# Rules that were written, measured against real prose, and refused. A refactor
# that quietly reinstates one of them is a regression, not a feature.
REFUSED_RULES = ("圖必須從輸入節點開始", "每個斷言都要有出處", "禁止被動語態")


class CanaryError(RuntimeError):
    """A matched-task invariant did not hold. Never a soft warning."""


def blob(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def implemented() -> tuple[list[str], int]:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as handle:
        probe = Path(handle.name)
        handle.write("# probe\n")
    try:
        return [rule.rule_id for rule in kc.evaluate(probe)], len(kc.HUMAN_LANE)
    finally:
        probe.unlink(missing_ok=True)


def claimed_counts(text: str, pattern: re.Pattern[str]) -> set[int]:
    """Every number the body asserts about one of its own lanes."""
    return {DIGITS[hit] if hit in DIGITS else int(hit) for hit in pattern.findall(text)}


def features(text: str, rules: list[str], human: int) -> dict[str, Any]:
    """Score one treatment body against the mechanism it claims to drive."""
    command = COMMAND.search(text)
    declared = command.group(1) if command else None
    resolves = bool(declared) and (ROOT / declared).is_file()
    rule_claims = claimed_counts(text, RULE_CLAIM)
    human_claims = claimed_counts(text, HUMAN_CLAIM)
    bound = {
        "declared_command_resolves": resolves,
        "rule_count_matches_implementation": rule_claims == {len(rules)},
        "human_lane_count_matches_implementation": human_claims == {human},
    }
    return {
        "treatment_blob": blob(text),
        "declared_command": declared,
        "rule_counts_claimed": sorted(rule_claims),
        "human_counts_claimed": sorted(human_claims),
        "audit_route": "assert_continuity_audit.py" in text,
        **bound,
        "claim_closure": f"{sum(bound.values())}/3",
    }


def build_corpus(temp: Path) -> dict[str, str]:
    """One corpus, copied once, used by every arm. Digests make that checkable."""
    corpus = temp / "corpus"
    corpus.mkdir(parents=True)
    source = ROOT / "tests/check-knowledge-continuity/fixtures"
    shutil.copy2(source / "good/doc.md", corpus / "good.md")
    shutil.copy2(source / "hollow/doc.md", corpus / "hollow.md")
    return {name: digest(corpus / f"{name}.md") for name in ("good", "hollow")}


def run_arm(arm: str, script: Path, temp: Path, corpus: dict[str, str]) -> dict[str, Any]:
    """Execute the arm's own declared command against the shared corpus."""
    out: dict[str, Any] = {}
    for name in sorted(corpus):
        record = temp / f"{arm}-{name}.json"
        done = subprocess.run(
            [sys.executable, str(script), f"corpus/{name}.md", "--quiet", "--audit-json", str(record)],
            cwd=temp, capture_output=True, text=True, check=False,
        )
        if not record.is_file():
            raise CanaryError(f"{arm}:{name} produced no audit record")
        gate = subprocess.run(
            [sys.executable, str(GATE), "--audit", str(record), "--subject-root", str(temp)],
            capture_output=True, text=True, check=False,
        )
        value = json.loads(record.read_text(encoding="utf-8"))
        out[name] = {
            "exit_code": done.returncode,
            "total_breaks": value["mechanical"]["total_breaks"],
            "failing_rules": sorted(
                row["rule_id"] for row in value["mechanical"]["rules"] if row["state"] == "FAIL"
            ),
            "convergence": value["convergence"],
            "audit_gate": "PASS" if gate.returncode == 0 else f"FAIL {gate.stderr.strip()}",
        }
    return out


def assert_oracles(arm: str, measured: dict[str, Any], rules: list[str]) -> None:
    """The acceptance oracles every executing arm must reproduce, unchanged."""
    good, hollow = measured["good"], measured["hollow"]
    if good["total_breaks"] != 0 or good["exit_code"] != 0:
        raise CanaryError(f"{arm} good-corpus oracle failed {good}")
    if hollow["total_breaks"] <= 0 or hollow["exit_code"] != 2:
        raise CanaryError(f"{arm} hollow-corpus oracle failed {hollow}")
    if hollow["failing_rules"] != sorted(rules):
        raise CanaryError(f"{arm} hollow corpus did not turn every rule red {hollow}")
    for name in ("good", "hollow"):
        if measured[name]["audit_gate"] != "PASS":
            raise CanaryError(f"{arm}:{name} audit record refused: {measured[name]['audit_gate']}")
        if measured[name]["convergence"] != "MECHANICAL_ONLY":
            raise CanaryError(f"{arm}:{name} machine record claimed more than a mechanical lane")


def old_strength_matrix(strengths: dict[str, tuple[str, str, int]]) -> dict[str, str]:
    """Re-measure each named old strength against the current rules."""
    out: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="kc-old-strength-") as raw:
        temp = Path(raw)
        for name, (document, rule_id, expected) in strengths.items():
            path = temp / f"{name}.md"
            path.write_text(document, encoding="utf-8")
            rules = {rule.rule_id: rule for rule in kc.evaluate(path)}
            got = len(rules[rule_id].findings)
            out[name] = "PASS" if got == expected else f"FAIL {rule_id} expected {expected} got {got}"
    refused = kc.REJECTED_RULES
    for phrase in REFUSED_RULES:
        out[f"OS-09_refused_rule_stays_refused:{phrase}"] = (
            "PASS" if phrase in refused else "FAIL rule no longer recorded as refused"
        )
    return out


def compare(
    strengths: dict[str, tuple[str, str, int]] | None = None,
    frozen: dict[str, tuple[str, str, str]] | None = None,
) -> dict[str, Any]:
    frozen = FROZEN if frozen is None else frozen
    rules, human = implemented()
    bodies: dict[str, str] = {}
    for arm, (_role, relative, expected) in frozen.items():
        path = ROOT / relative
        if not path.is_file():
            raise CanaryError(f"frozen treatment missing {arm}")
        text = path.read_text(encoding="utf-8")
        if blob(text) != expected:
            raise CanaryError(f"frozen treatment drift {arm}: {blob(text)} != {expected}")
        bodies[arm] = text
    bodies[LIVE_ARM] = LIVE_BODY.read_text(encoding="utf-8")
    if bodies[LIVE_ARM] == bodies["B0_DEHOSTED_AS_LANDED"]:
        raise CanaryError("live body is byte-identical to B0; there is no repaired candidate")

    matrix = old_strength_matrix(strengths if strengths is not None else OLD_STRENGTHS)
    lost = sorted(name for name, state in matrix.items() if state != "PASS")
    if lost:
        raise CanaryError(f"old strength lost: {lost}")

    results: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="kc-refactor-ab-") as raw:
        temp = Path(raw)
        corpus = build_corpus(temp)
        for arm in ARMS:
            scored = features(bodies[arm], rules, human)
            declared = scored["declared_command"]
            script = ROOT / declared if declared else None
            if script is None or not script.is_file():
                results[arm] = {
                    **scored,
                    "execution_state": "BLOCKED_DECLARED_COMMAND_ABSENT",
                    "functional_output": "NOT_EXERCISED",
                    "measured": None,
                }
                continue
            measured = run_arm(arm, script, temp, corpus)
            assert_oracles(arm, measured, rules)
            results[arm] = {
                **scored,
                "execution_state": "PASS",
                "functional_output": "PASS",
                "measured": measured,
            }

    blocked = sorted(a for a, row in results.items() if row["execution_state"] != "PASS")
    if blocked != ["A_ADMITTED_HOST_BOUND", "B0_DEHOSTED_AS_LANDED"]:
        raise CanaryError(f"unexpected blocked set {blocked}")
    if results["A_ADMITTED_HOST_BOUND"]["declared_command"] != results["B0_DEHOSTED_AS_LANDED"]["declared_command"]:
        raise CanaryError("A and B0 no longer share the inherited command; the finding changed shape")
    if results[LIVE_ARM]["claim_closure"] != "3/3":
        raise CanaryError(f"repaired candidate does not close its own claims {results[LIVE_ARM]}")
    for arm in FROZEN:
        if results[arm]["claim_closure"] == "3/3":
            raise CanaryError(f"frozen treatment {arm} scored as repaired; identity drift")

    return {
        "schema": "knowledge-continuity/refactor-ab/v1",
        "task": {
            "id": "knowledge-continuity-entrypoint-claim-closure",
            "corpus_sha256": corpus,
            "same_corpus_budget_carrier": True,
            "implemented_rules": rules,
            "human_lane_items": human,
        },
        "treatments": {arm: {"role": frozen[arm][0] if arm in frozen else "REPAIRED_CANDIDATE",
                             "path": frozen[arm][1] if arm in frozen else "SKILL.md"} for arm in ARMS},
        "results": results,
        "old_strength_matrix": matrix,
        "denominator": {"arms": list(ARMS), "blocked_retained": blocked},
        "inherited_defect": {
            "declared_command": results["A_ADMITTED_HOST_BOUND"]["declared_command"],
            "survived_the_landed_refactor": True,
            "repaired_in": LIVE_ARM,
        },
        "cleanup": "CLEAN",
        "live_model_runtime": "NOT_EXERCISED",
        "delivery_and_human_admit": "HUMAN_ADMIT_REQUIRED",
    }


def selftest() -> int:
    """Plant a defect against each load-bearing assertion and require it to fire.

    Nothing here edits a tracked file, not even transiently: the frozen bytes are
    the evidence, and a control that rewrites them to prove they are watched can
    leave the evidence behind if it is interrupted.
    """
    survivors: list[str] = []

    def refuses(name: str, call) -> None:
        try:
            call()
        except CanaryError:
            return
        survivors.append(name)

    weakened = copy.deepcopy(OLD_STRENGTHS)
    document, rule_id, _ = weakened["OS-03_quoted_examples_are_shown_not_used"]
    weakened["OS-03_quoted_examples_are_shown_not_used"] = (document, rule_id, 99)
    refuses("old_strength_matrix_never_fails", lambda: compare(weakened))

    original = kc.strip_quoted
    kc.strip_quoted = lambda text: text
    try:
        refuses("neutralised_quoting_rule_survived", compare)
    finally:
        kc.strip_quoted = original

    role, relative, _ = FROZEN["A_ADMITTED_HOST_BOUND"]
    drifted = {**FROZEN, "A_ADMITTED_HOST_BOUND": (role, relative, "0" * 40)}
    refuses("frozen_treatment_drift_survived", lambda: compare(None, drifted))
    absent = {**FROZEN, "A_ADMITTED_HOST_BOUND": (role, "tests/refactor-ab/fixtures/never-frozen.txt", "0" * 40)}
    refuses("frozen_treatment_absence_survived", lambda: compare(None, absent))

    rules, human = implemented()
    live = LIVE_BODY.read_text(encoding="utf-8")
    if features(live, rules, human)["claim_closure"] != "3/3":
        survivors.append("live_body_does_not_close_its_claims")
    lying = RULE_CLAIM.sub("四條機械規則", live, count=1)
    if lying == live or features(lying, rules, human)["claim_closure"] == "3/3":
        survivors.append("wrong_rule_count_scored_as_bound")
    # Re-plant the exact historical defect: the first command a reader is told
    # to run points back at the consumer-host projection path.
    moved = live.replace(
        "python3 scripts/check_knowledge_continuity.py",
        "python3 .agents/skills/knowledge-continuity/scripts/check_knowledge_continuity.py",
        1,
    )
    if moved == live or features(moved, rules, human)["declared_command_resolves"]:
        survivors.append("unresolvable_command_scored_as_resolving")

    if survivors:
        print(f"KC-REFACTOR-AB-SELFTEST-RED survived={','.join(survivors)}", file=sys.stderr)
        return 2
    print(
        "KC-REFACTOR-AB-SELFTEST-GREEN 6 planted defects refused; "
        "live body positive control closes 3/3"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    try:
        report = compare()
    except (CanaryError, OSError, KeyError, ValueError, subprocess.SubprocessError) as exc:
        print(f"KC-REFACTOR-AB-RED {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    print(
        "KC-REFACTOR-AB-GREEN A and B0 blocked on the inherited host-bound command; "
        "B1 closes 3/3 entrypoint claims on the same corpus; old strengths retained; "
        "live model runtime NOT_EXERCISED, delivery HUMAN_ADMIT_REQUIRED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
