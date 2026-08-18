#!/usr/bin/env python3
"""Find places where a document forces the reader to supply missing knowledge.

Why these four rules and not more
---------------------------------
Each rule here fired on a real document and was confirmed by a human reader as a
genuine break. Rules that produced a false positive on real prose were dropped,
not softened: a gate that cries wolf trains people to ignore it, which is worse
than no gate. The rejected ones are listed in REJECTED_RULES below so nobody
re-derives them.

What this cannot do
-------------------
It checks the SHAPE of references, not whether the surrounding explanation is
actually sufficient. A document can pass all four rules and still be unreadable.
The rules catch the mechanical breaks; a human still reads for the rest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# Shapes that mean nothing to a reader who has not memorised the document family.
# "§7" / "NEG-101" / "08-05" identify something, but only to someone who already
# knows what that something is.
SHORTHAND = re.compile(
    r"§\s*\d+"  # § 7
    r"|\b[A-Z]{2,6}-\d{2,4}\b"  # NEG-101, INV-OOBE-011, AK-32
    r"|(?<!\d{4}-)\b\d{2}-\d{2}\b(?!\d)"  # 08-05（但 2026-08-06 是日期，不是代號）
)
# Standard names that merely LOOK like document codes. `SHA-256` is an algorithm,
# not a cross-reference, and demanding a filename beside it is noise. Found by
# running this checker on a sibling skill's own SKILL.md.
WELL_KNOWN = frozenset(
    {
        "SHA-1",
        "SHA-256",
        "SHA-512",
        "MD-5",
        "UTF-8",
        "UTF-16",
        "ISO-8601",
        "RFC-822",
        "RFC-2822",
        "RFC-5322",
        "AES-128",
        "AES-256",
        "HTTP-2",
        "BASE-64",
        "P-256",
        "K-256",
    }
)
# A reference is grounded when the same paragraph also names a real artefact.
ARTEFACT = re.compile(r"[\w./-]+\.(?:md|py|sh|json|swift|js|kt|java|yaml|yml)\b")
# Phrases that explicitly hand the reader off to somewhere else.
OFFLOAD = re.compile(
    r"不在此複製|不再贅述|同前述|見上文|如前所述|參照上節|沿用[^，。\n]{0,12}的?§"
)
# Approximations where a count is being asserted.
APPROX = re.compile(r"[~約]\s*\d+\s*(?:列|條|項|個|筆|處|張)|大約\s*\d+")
# A sentence asserting what the code does TODAY, as opposed to what it should do.
CURRENT_CLAIM = re.compile(r"現況|目前的程式碼|現行碼|現存的")
# 把舉證責任推給另一節的寫法。
SECTION_HANDOFF = re.compile(r"(?:見|詳見|參見)\s*§\s*\d")
# Something a reader can open and check: a code anchor, or a pointer to an
# evidence block that contains one.
TERMINAL_EVIDENCE = re.compile(
    r"[\w./-]+\.(?:js|swift|kt|java|py|sh|go|sql)\s*:\s*\d+"  # file.js:380
    r"|附錄\s*[A-Z]\s*的?\s*\*{0,2}E-\d+"  # 附錄 A 的 E-5
    r"|\bE-\d+\b"  # E-5
)

# Content inside 「」 or backticks is being SHOWN, not USED. A document that
# explains what a bad reference looks like must be able to quote one without
# being accused of writing one. Found by running this checker on its own SKILL.md.
QUOTED = re.compile(r"「[^」]*」|`[^`]*`")


def strip_quoted(text: str) -> str:
    """Blank out quoted spans so demonstrated examples are not counted as usage."""
    return QUOTED.sub(" ", text)


AUDIT_SCHEMA = "knowledge-continuity/continuity-audit/v1"

# The half of this Skill no script can judge. It lives here as data, not only as
# prose in SKILL.md §4, for one reason: a machine run that emits nothing about
# this lane reads as convergence, and "機械層綠 = 收斂" is the exact inference
# SKILL.md forbids. Emitting the lane as HUMAN_ADMIT_REQUIRED makes the missing
# half visible in the artefact instead of only in the document nobody reopens.
# The wording is bound to the document by tests/refactor-ab/refactor_ab.py, so a
# body that renumbers this lane without renumbering the tool turns red.
HUMAN_LANE = (
    ("H-1", "圖是不是從輸入開始畫的？"),
    ("H-2", "圖用到的符號有沒有解釋過？"),
    ("H-3", "未裁決的事有沒有被畫成已裁決？"),
    ("H-4", "有沒有過度宣稱？"),
    ("H-5", "索引跳轉會不會把讀者送到另一個索引？"),
    ("H-6", "一個沒讀過前置文件的人，讀得完嗎？"),
)

REJECTED_RULES = """
Rules written, tested against real prose, and deliberately NOT shipped:

  "圖必須從輸入節點開始"  — a diagram that opens on a conclusion is a real
      defect, but no reliable text signal distinguishes it from a diagram whose
      first line is a legitimate title. Left to human review.
  "每個斷言都要有出處"    — matched every ordinary sentence. Useless.
  "禁止被動語態"          — style, not a knowledge break. Out of scope.
"""


@dataclass
class Finding:
    """One place a reader is asked to supply knowledge the document withheld."""

    rule: str
    line: int
    excerpt: str
    detail: str


@dataclass
class Rule:
    """A checkable property of the prose."""

    rule_id: str
    title: str
    why: str
    findings: list[Finding] = field(default_factory=list)


def paragraphs(lines: list[str]) -> list[tuple[int, list[str]]]:
    """Split into paragraphs, returning (1-based start line, lines).

    Fenced blocks are one unit: a diagram's internal blank lines must not split
    it, or a label at the top would lose the context below it.
    """
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] = []
    start = 1
    in_fence = False
    for index, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            if not current:
                start = index
            current.append(line)
            continue
        if not line.strip() and not in_fence:
            if current:
                blocks.append((start, current))
                current = []
            continue
        if not current:
            start = index
        current.append(line)
    if current:
        blocks.append((start, current))
    return blocks


def local_sections(lines: list[str]) -> set[str]:
    """Section numbers that exist as headings in this document."""
    found = set()
    for line in lines:
        match = re.match(r"^#{2,4}\s+(?:§\s*)?(\d+(?:\.\d+)*)[.、．\s]", line.strip())
        if match:
            found.add(match.group(1))
    return found


def local_symbols(lines: list[str]) -> set[str]:
    """Identifiers this document defines for itself.

    Three ways a document can define its own shorthand, all mechanical:
      - a table's FIRST cell (`| AK-01 | ... |` defines AK-01)
      - any table row that also carries a filename (a reference table entry)
      - a heading
    An identifier defined this way is not a knowledge break: the reader can find
    it without leaving the document. Only genuinely external shorthand must be
    grounded in its own paragraph.
    """
    defined: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [c.strip().strip("*` ") for c in stripped.strip("|").split("|")]
            if cells:
                defined.update(SHORTHAND.findall(cells[0]))
            if ARTEFACT.search(stripped):
                defined.update(SHORTHAND.findall(stripped))
        elif stripped.startswith("#"):
            defined.update(SHORTHAND.findall(stripped))
    return defined


def rule_kc01(lines: list[str]) -> Rule:
    """KC-01 — an EXTERNAL shorthand reference must be grounded in its paragraph.

    A `§N` that resolves to a heading in this same document is not a break: the
    reader can scroll. Only references that leave the document need an artefact
    name, so `§N` is excluded when N exists locally.
    """
    rule = Rule(
        rule_id="KC-01",
        title="外部記憶式引用必須就地落地",
        why="「NEG-101」「08-05」只對記得整個文件家族的人有意義。"
        "同一段落內必須出現真實檔名，讀者才知道去哪裡查。"
        "指向本文自己章節的「§N」不算——讀者捲動即可。",
    )
    local = local_sections(lines)
    defined = local_symbols(lines)
    for start, block in paragraphs(lines):
        text = "\n".join(block)
        if text.lstrip().startswith("```"):
            continue  # 圖與程式碼裡的代號是標籤，不是引用
        hits = [
            hit
            for hit in SHORTHAND.findall(strip_quoted(text))
            if not (hit.startswith("§") and hit.lstrip("§ ") in local)
            and hit not in defined
            and hit not in WELL_KNOWN
        ]
        if not hits:
            continue
        if ARTEFACT.search(text):
            continue
        rule.findings.append(
            Finding(
                rule="KC-01",
                line=start,
                excerpt=text.strip().splitlines()[0][:72],
                detail=f"出現 {sorted(set(hits))[:4]} 但同段沒有任何檔名",
            )
        )
    return rule


def rule_kc02(lines: list[str], text: str) -> Rule:
    """KC-02 — an internal section reference must point at a section that exists."""
    rule = Rule(
        rule_id="KC-02",
        title="內部章節引用必須指到存在的章節",
        why="指錯章節比不指更糟：讀者會照著跳過去，發現內容不對，"
        "然後開始懷疑整份文件。",
    )
    present = set()
    for line in lines:
        match = re.match(r"^#{2,4}\s+(?:§\s*)?(\d+(?:\.\d+)*)[.、．\s]", line.strip())
        if match:
            present.add(match.group(1))
    if not present:
        return rule  # 文件沒有編號章節，這條不適用
    for index, line in enumerate(lines, start=1):
        if line.strip().startswith("#"):
            continue
        # 「見 `別的檔.md` §10.1」指的是那份文件的章節，不是本文的。
        # 剝引號會把中間的檔名抹掉、讓它看起來像內部引用，所以要先看原始行。
        if ARTEFACT.search(line):
            continue
        # 與其他規則一致：引號內是被展示的範例，不是真的引用。
        # 一份解釋「章節錯引長什麼樣」的文件必須能舉例。
        for match in re.finditer(
            r"(?:見|詳見|參見|回到)\s*§\s*(\d+(?:\.\d+)*)", strip_quoted(line)
        ):
            target = match.group(1)
            if target in present:
                continue
            rule.findings.append(
                Finding(
                    rule="KC-02",
                    line=index,
                    excerpt=line.strip()[:72],
                    detail=f"指向 §{target}，但本文沒有這個章節（有的是 "
                    f"{sorted(present)[:6]}…）",
                )
            )
    return rule


def rule_kc03(lines: list[str]) -> Rule:
    """KC-03 — a count must be exact."""
    rule = Rule(
        rule_id="KC-03",
        title="計數不得用約數",
        why="「約 14 列」讓實作者無法重建驗收集合，也讓審查者無法判斷有沒有漏。"
        "數得出來就數，數不出來就不要宣稱有這個數。",
    )
    in_fence = False
    for index, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = APPROX.search(strip_quoted(line))
        if match:
            rule.findings.append(
                Finding(
                    rule="KC-03",
                    line=index,
                    excerpt=line.strip()[:72],
                    detail=f"約數「{match.group(0)}」——請改成實際數字",
                )
            )
    return rule


def rule_kc04(lines: list[str]) -> Rule:
    """KC-04 — offloading核心知識 must come with an inline summary."""
    rule = Rule(
        rule_id="KC-04",
        title="把知識外包出去時必須留下就地摘要",
        why="「不在此複製」「沿用 §5」會讓讀者被迫中斷閱讀去翻另一份文件，"
        "回來時已經忘記讀到哪。外包可以，但要留一句話讓人不必離開。",
    )
    in_fence = False
    for index, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = OFFLOAD.search(strip_quoted(line))
        if match:
            rule.findings.append(
                Finding(
                    rule="KC-04",
                    line=index,
                    excerpt=line.strip()[:72],
                    detail=f"外包語句「{match.group(0)}」——請在原地補一句話摘要",
                )
            )
    return rule


def rule_kc05(lines: list[str]) -> Rule:
    """KC-05 — a claim about today's code must reach the code in ONE hop.

    Found the hard way: a plan said "現況這個刪除失敗時完全無聲（詳見 §11）".
    The evidence existed, but the reader had to hop twice — §9 to §11, then §11
    to the appendix. Every hop is a place a reader gives up. KC-01 cannot catch
    this: the reference IS grounded, it is just grounded one level too far away.
    """
    rule = Rule(
        rule_id="KC-05",
        title="現況主張不得靠「指向另一節」代替實碼",
        why="讀者看到「現況是 X」時的下一個問題永遠是「你怎麼知道」。"
        "把答案推給另一節，等於要求讀者跳兩次：先跳到那節，再從那節找到證據。"
        "每一跳都是讀者放棄的地方。實碼錨點要寫在提出主張的同一段。",
    )
    # 刻意只抓一種形狀：現況主張 ＋ 指向另一節 ＋ 同段沒有實碼。
    # 「現況 X」但完全沒指向任何地方，那是散文或 KC-01 的範圍，不是兩跳問題；
    # 把那種也抓進來會在「目前沒有裁決」（講決策）、「實測會擋下」（講測試）
    # 這類句子上誤報，而會誤報的規則比沒有規則更糟。
    for start, block in paragraphs(lines):
        text = "\n".join(block)
        if text.lstrip().startswith("```"):
            continue
        scan = strip_quoted(text)
        if not CURRENT_CLAIM.search(scan):
            continue
        if not SECTION_HANDOFF.search(scan):
            continue
        if TERMINAL_EVIDENCE.search(text):
            continue
        rule.findings.append(
            Finding(
                rule="KC-05",
                line=start,
                excerpt=text.strip().splitlines()[0][:72],
                detail="宣稱了現況，但同段沒有「檔案:行號」也沒有指向實碼的證據代號",
            )
        )
    return rule


def evaluate(path: Path) -> list[Rule]:
    """Run every rule against one document."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    return [
        rule_kc01(lines),
        rule_kc02(lines, text),
        rule_kc03(lines),
        rule_kc04(lines),
        rule_kc05(lines),
    ]


def audit(path: Path, rules: list[Rule]) -> dict:
    """Build the machine-readable audit record for one document.

    A machine can only ever emit `MECHANICAL_ONLY`: the human lane it carries is
    unanswered by construction, and `scripts/assert_continuity_audit.py` refuses
    a `CONVERGED` record whose lane nobody admitted.
    """
    total = sum(len(rule.findings) for rule in rules)
    return {
        "schema": AUDIT_SCHEMA,
        "subject": {
            "path": path.as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        },
        "mechanical": {
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "state": "PASS" if not rule.findings else "FAIL",
                    "breaks": len(rule.findings),
                    "lines": [item.line for item in rule.findings],
                }
                for rule in rules
            ],
            "total_breaks": total,
            "exit_code": 0 if total == 0 else 2,
        },
        "human_lane": [
            {
                "id": rule_id,
                "question": question,
                "state": "HUMAN_ADMIT_REQUIRED",
                "admitted_by": None,
            }
            for rule_id, question in HUMAN_LANE
        ],
        "convergence": "MECHANICAL_ONLY",
    }


def report(path: Path, rules: list[Rule], verbose: bool) -> int:
    """Print findings; return 0 only when the document has no breaks."""
    total = sum(len(r.findings) for r in rules)
    print(f"knowledge-continuity — {path}")
    print("=" * 72)
    for rule in rules:
        count = len(rule.findings)
        state = "PASS" if count == 0 else "FAIL"
        print(f"\n[{state}] {rule.rule_id}  斷點 {count}   {rule.title}")
        if count and verbose:
            print(f"       為什麼：{rule.why}")
        for item in rule.findings:
            print(f"       - :{item.line}  {item.detail}")
            print(f"         「{item.excerpt}」")
    print("\n" + "=" * 72)
    print(f"合計 {total} 個知識斷點")
    return 0 if total == 0 else 2


def selftest() -> int:
    """Both controls for every rule: a break must FAIL, clean prose must PASS."""
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "bad.md"
        bad.write_text(
            "# 標題\n\n"
            "## 1. 開頭\n\n"
            "這段照 §7 的裁決辦，NEG-101 也適用。\n\n"  # KC-01
            "## 2. 內容\n\n"
            "詳見 §9 的說明。\n\n"  # KC-02（§9 不存在）
            "去重後約 14 列，另有約 10 條。\n\n"  # KC-03
            "狀態模型沿用 §5，不在此複製。\n\n"  # KC-04
            "現況這個刪除失敗時完全無聲（詳見 §2）。\n",  # KC-05（兩跳）
            encoding="utf-8",
        )
        rules = {r.rule_id: r for r in evaluate(bad)}
        for rid, want in (
            ("KC-01", 1),
            ("KC-02", 1),
            ("KC-03", 1),
            ("KC-04", 1),
            ("KC-05", 1),
        ):
            got = len(rules[rid].findings)
            print(f"  negative {rid}: 期望 >= {want}，實得 {got}")
            if got < want:
                failures.append(f"{rid} 沒抓到植入的斷點")

        good = Path(tmp) / "good.md"
        good.write_text(
            "# 標題\n\n"
            "## 1. 開頭\n\n"
            "這段照黃金流文件（`02-golden-flow.md`）§7 的裁決辦，"
            "不變量帳本（`00-invariants.md`）的 NEG-101 也適用。\n\n"
            "## 2. 內容\n\n"
            "詳見 §1 的說明。\n\n"
            "完整討論見 `02-golden-flow.md` §10.1——跨文件引用不算本文的章節。\n\n"
            "去重後 26 列，另有 6 條。\n\n"
            "狀態模型有三個階段：待啟用、解析中、已提交；"
            "完整定義在 `08-05-plan.md`。\n\n"
            "現況這個刪除失敗時完全無聲，實碼見 `account-register-v2.js:479` "
            "的 `return resolve()` 寫在迴圈外。\n",
            encoding="utf-8",
        )
        rules = {r.rule_id: r for r in evaluate(good)}
        for rid in ("KC-01", "KC-02", "KC-03", "KC-04", "KC-05"):
            got = len(rules[rid].findings)
            print(f"  positive {rid}: 期望 0，實得 {got}")
            if got:
                detail = rules[rid].findings[0].detail
                failures.append(f"{rid} 對合規文字誤報（{detail}）")

        noise = Path(tmp) / "noise.md"
        noise.write_text(
            "# 標題\n\n"
            "## 1. 圖\n\n"
            "```text\n"
            "  ① 判斷 → §7 分支 → NEG-101 風險點\n"
            "  約 3 條路徑\n"
            "```\n",
            encoding="utf-8",
        )
        rules = {r.rule_id: r for r in evaluate(noise)}
        total = sum(len(r.findings) for r in rules.values())
        print(f"  noise    圖內的代號與數字不得誤報：期望 0，實得 {total}")
        if total:
            failures.append("圖與程式碼區塊內的標籤被當成引用")

        # 一份「解釋什麼是壞引用」的文件，必須能引用壞例子而不被判違規。
        # 這個控制是跑本 checker 檢查自己的 SKILL.md 時發現需要的。
        quoting = Path(tmp) / "quoting.md"
        quoting.write_text(
            "# 標題\n\n"
            "## 1. 反例說明\n\n"
            "| 形態 | 讀者的體驗 |\n|---|---|\n"
            "| 記憶式引用 | 「`NEG-101` 是什麼？」 |\n"
            "| 約數 | 「約 14 列」到底是哪幾列？ |\n"
            "| 知識外包 | 「沿用 §5，不在此複製」讓人中斷 |\n"
            "| 章節錯引 | 「詳見 §9」跳過去發現不是講這個 |\n",
            encoding="utf-8",
        )
        rules = {r.rule_id: r for r in evaluate(quoting)}
        total = sum(len(r.findings) for r in rules.values())
        print(f"  quoting  被展示的反例不得判成違規：期望 0，實得 {total}")
        if total:
            failures.append("引號／反引號內的示範例子被當成真正的引用")

        # ISO 日期含有 `08-06` 這種形狀，但它是日期不是文件代號。
        # 這個控制是跑本 checker 檢查 04-guard-mechanisms 時發現需要的。
        # 標準名稱長得像代號但不是引用。要求在它們旁邊附檔名只會製造雜訊。
        wellknown = Path(tmp) / "wellknown.md"
        wellknown.write_text(
            "# 標題\n\n## 1. 交付\n\n"
            "每份來源與完整 HTML 都要進 SHA-256 manifest，文字一律用 UTF-8。\n\n"
            "時間格式依 ISO-8601。\n",
            encoding="utf-8",
        )
        rules = {r.rule_id: r for r in evaluate(wellknown)}
        got = len(rules["KC-01"].findings)
        print(f"  known    SHA-256／UTF-8 這類標準名稱不得誤報：期望 0，實得 {got}")
        if got:
            failures.append("標準名稱（SHA-256 等）被當成文件代號")

        dated = Path(tmp) / "dated.md"
        dated.write_text(
            "---\nverified_at: 2026-08-06\n---\n\n"
            "# 標題\n\n## 1. 現況\n\n"
            "現況（2026-08-06 實查）：三個 repo 都乾淨。\n\n"
            "上次盤點是 2026-08-05，這次是 2026-08-06。\n",
            encoding="utf-8",
        )
        # 只看 KC-01——這個控制測的是「日期不是代號」，不是整份文件是否合規。
        # 該 fixture 的句子確實也缺 KC-05 要求的實碼錨點，那是另一條規則的正確行為。
        rules = {r.rule_id: r for r in evaluate(dated)}
        got = len(rules["KC-01"].findings)
        print(f"  dated    ISO 日期不得被當成文件代號：KC-01 期望 0，實得 {got}")
        if got:
            failures.append("2026-08-06 這種日期被當成文件代號")

    if failures:
        for item in failures:
            print(f"SELFTEST FAIL: {item}", file=sys.stderr)
        return 2
    print("SELFTEST PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", type=Path)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument(
        "--quiet", action="store_true", help="omit the why-explanations"
    )
    parser.add_argument(
        "--rejected", action="store_true", help="show rules deliberately not shipped"
    )
    parser.add_argument(
        "--audit-json",
        type=Path,
        help="write the machine audit record (schema: references/continuity-audit.schema.json)",
    )
    args = parser.parse_args(argv)

    if args.rejected:
        print(REJECTED_RULES)
        return 0
    if args.selftest:
        return selftest()
    if args.target is None:
        parser.error("需要一個 Markdown 檔，或 --selftest")
    if not args.target.is_file():
        print(f"ERROR: 檔案不存在：{args.target}", file=sys.stderr)
        return 1
    rules = evaluate(args.target)
    if args.audit_json is not None:
        args.audit_json.write_text(
            json.dumps(audit(args.target, rules), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return report(args.target, rules, not args.quiet)


if __name__ == "__main__":
    sys.exit(main())
