# Module: unknown-discovery-composer — northstar → antigravity retarget 映射 + 誠實帳本

> 屬 [`unknown-discovery-composer`](../SKILL.md)。本檔 = port 的命門與誠實帳本：哪些機制一對一映到
> antigravity、哪些沒基座被拿掉/降級、為何不是簡化。
> 命門：northstar 版 = **平台無關的路由紀律（四象限×三時段）** 疊加 **三個 northstar 專屬下游 Integrator
> 引用**（`sdlc-plan-composer` / `judge-loop-chooser` / `gemini-conversation-research`）+ **一個 northstar
> 專屬跨階段 skill 引用**（`fidelity-handoff`）。路由紀律本身乾淨映；下游中三個
> （judge-loop-chooser、gemini-conversation-research、repo-agent-native）antigravity **已有本地
> fork**，映得比 northstar 原版更乾淨（本地非跨 repo）；**`sdlc-plan-composer` 已於 cc-20260705 落地
> 本地 fork（`.agents/skills/sdlc-plan-composer/`），本表原記錄的「無基座退化」已改為「本地 fork 直
> 指」——見 §2 第一行**；`fidelity-handoff` 仍**無基座**，誠實拿掉並降級記錄。

---

## 1. 為何多數路由目標不用換——它們本來就是全局的

northstar 表格裡引用的多數 skill（`zoom-out`/`teach`/`research`/`wayfinder`/`grilling`/`grill-me`/
`grill-with-docs`/`loop-me`/`prototype`/`design-an-interface`/`improve-codebase-architecture`/
`diagnose`/`diagnosing-bugs`/`to-prd`/`writing-shape`/`edit-article`/`qa`/`ask-matt`）都是
**mattpocock/skills@latest 經 `~/.claude/skills/` 全局符號連結**，與 project 無關——northstar 引用得到，
antigravity 也引用得到。**這些列不需要 retarget**，本檔只記真正有落差的幾格。

---

## 2. 逐機制 retarget 映射表

| northstar 機制 | antigravity 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| U1 出口 `sdlc-plan-composer`（northstar 專屬多段 Integrator：S-1..S5，序列委派 grill-with-docs/to-prd/to-issues/tdd/diagnose/fidelity-handoff/design-an-interface+ADR-gate） | **（cc-20260705 更新）已落地 antigravity 本地 fork** `.agents/skills/sdlc-plan-composer/SKILL.md`——多階段任務出口直指本地版；單階段/需求已清楚改走 `to-prd`+`implement`（2026-07-17 更新，見下） | 本地 fork 的 S-1..S5 已 retarget（S-1 消費 antigravity `repo-agent-native` 單頁 artifact、決策記錄非編號 ADR、`fidelity-handoff` 段退化裸 handoff、S5 委派本地 `judge-loop-chooser`）；逐機制映射見 `sdlc-plan-composer/modules/retarget-map.md`（本表不重複，指針即可）。`to-prd`+`implement` 仍是單階段的合理輕量出口，兩者並存、按任務規模分流。 |
| U1 表「單階段輕量出口」`superpowers:writing-plans`（Claude Code plugin 級 skill，理論上跨 project 全局可用） | **2026-07-17 retarget**：superpowers 從未在本專案掛號（`installed_plugins.json` 查證，只掛在 `local_stack`/`TrueMe_Android`/`northstar` 三個其他專案）——拿掉理論性 fallback，改指 mattpocock 真實技術等價物 `to-prd`（無需訪談、直接把對話 synthesis 成 PRD）+ `implement`（消化 PRD/issue 直接執行，內建 tdd/code-review） | 查證方式：讀 `~/.agents/.skill-lock.json` + `gh api repos/mattpocock/skills/git/trees/main` 確認 mattpocock/skills 目前完整目錄，無 `writing-plans` 這個名字，但 `to-prd`→`implement` 是同一問題（單階段輕量 spec→build）的真實可用鏈；差異：mattpocock 版發布到 issue tracker，非獨立 markdown 計劃檔（媒介不同，機制對應）。原始 superpowers 版文字已封存 `.archive/superpowers-skills-v6.1.1/writing-plans/`。 |
| U2 `fidelity-handoff`（northstar：形態決策 fork/handoff/cold-start + `fidelity-handoff-lint` 覆蓋閘，防裸交接漏 load-bearing negatives） | **拿掉，退化到裸 `handoff` / `claude-handoff`** | antigravity 無 fidelity-handoff fork、無覆蓋閘腳本。裸 handoff 無覆蓋閘防漏——這是真實能力差距，非文字簡化；交接後建議人工複查有無漏 negative。 |
| U1 KU 列 `repo-agent-native`（northstar 原版：跨 repo 引用 northstar 自己的 skill） | **retarget 為 antigravity 本地 fork** `.agents/skills/repo-agent-native/SKILL.md`（cc-20260703 已 port） | 比 northstar 原版更乾淨：本地 skill 而非跨 repo 引用。順帶掛上正交項 `repo-wiki-converge`（antigravity 特有，northstar 無對應）。 |
| U1 KU/UU 列「外部一手資料」`gemini-conversation-research` | **retarget 為 antigravity 本地 fork** | 同上，本地已 port（cc-20260628），非跨 repo。 |
| U3 產物判準 `judge-loop-chooser` | **retarget 為 antigravity 本地 fork**，且**新增代碼產物分流**：本地版明言「無 code-branch」，故本 port 在 U3 表新增一行「代碼產物 → 直接 `code-review`」 | 本地已 port（antigravity `judge-loop-chooser` 的 retarget-map 明載此拿掉）；本 skill 的路由表必須誠實反映下游能力縮水，不能假裝地端 judge-loop-chooser 跟 northstar 一樣廣。 |
| U1 表「grill-with-docs 沉澱 ADR/glossary」 | **retarget 措辭**：拿掉「ADR」字面，改「決策記錄」（散文，非編號） | 同 `repo-agent-native` retarget-map 已定調：「拿掉編號，保留紀律散文」——antigravity 無編號 ADR/DDR 系統。 |
| U1 表「範疇腦暴」原引註「sdlc-plan-composer:70 Not For」 | **拿掉該引註**（引註對象已不存在） | 2026-07-17 更新：`superpowers:brainstorming` 本身也已 retarget 為 `grilling`（mattpocock 全局 skill，技術上一致——一次一問+推薦答案+先探 codebase+確認前不動手，見 SKILL.md U1 表）；本行原始「拿掉引註」決策不受影響，只是路由目標從 superpowers 換成 grilling。 |
| YAML frontmatter（northstar：`liveness`/`functional_type`/`core_docs_refs`/`deterministic_tests` 等 skill-conformance-hub 治理欄位） | **拿掉**，換 antigravity 慣例 `name` + `description` 極簡 frontmatter | antigravity 無 skill-conformance-hub、無 WIRED/LIVE 追蹤系統、無 grounding.yaml 申報機制；硬填這些欄位 = 引用不存在的治理基座。 |
| `docs/adr/0012` glossary/notation-reference 引用 | **拿掉** | antigravity 無 `architecture/glossary.md`、無 `notation-reference.md` 這套 SSOT。 |
| `evals.json` + `tests/test_stub.py`（northstar：`deterministic_tests: false` 的 stub，本來就非真測試） | **拿掉** | 本來就是佔位 stub，非真實可執行覆蓋；antigravity 其他 port（`repo-agent-native`/`judge-loop-chooser`）也未帶等價 stub 過來，保持一致。 |

---

## 3. 拿掉的東西不是「簡化」，而是「不引入不存在的基座」/ 真實能力差距誠實記錄

- **能一對一映的映**：U0 四象限盤點紀律、起跑點披露、U1/U2/U3 的骨架結構、pivot 迴路、quiz 人理解閘、
  防雙稅精神、所有 mattpocock 全局 skill 引用（見 §1）。
- **有本地基座可換的換**（比 northstar 原版更乾淨）：`repo-agent-native` / `gemini-conversation-research` /
  `judge-loop-chooser` / `sdlc-plan-composer`（cc-20260705 補齊）四個下游交棒點，從「跨 repo 引用
  northstar」換成「引用 antigravity 本地 fork」。
- **無基座、真實能力差距、誠實拿掉並記錄**（本表核心）：`fidelity-handoff`（退化裸 `handoff`/
  `claude-handoff`）、ADR 編號系統（退化散文決策記錄）、skill-conformance-hub 治理欄位、
  glossary/notation-reference SSOT。

---

## 4. 判別「retarget 成立」的鐵錨

本 skill 引用的每個路由目標都真存在：
- mattpocock 全局 skill：經 `~/.claude/skills/<name>` 符號連結解析到 `/Users/neon/.agents/skills/<name>/`
  （本次驗證：`zoom-out`/`teach`/`research`/`wayfinder`/`grilling`/`grill-me`/`grill-with-docs`/`loop-me`/
  `prototype`/`design-an-interface`/`improve-codebase-architecture`/`diagnose`/`diagnosing-bugs`/`to-prd`/
  `writing-shape`/`edit-article`/`qa`/`ask-matt`/`code-review` 均存在於 disk）。
- antigravity 本地 fork：`.agents/skills/{repo-agent-native,gemini-conversation-research,judge-loop-chooser,sdlc-plan-composer}/SKILL.md`
  （`code-review` 是 mattpocock 全局 skill，非本地 fork——澄清避免與上一行混淆）。
- **2026-07-17 retarget**：`superpowers:brainstorming` / `superpowers:writing-plans` 兩處理論性 fallback
  已拿掉——查證 `installed_plugins.json` 確認 superpowers 從未在 antigravity 掛號（只掛在其他三個專案），
  不再假設「理論上全局可用」。改指 mattpocock 真實已驗證存在的 skill：`grilling`（brainstorming 等價，
  一次一問+推薦答案技術一致）、`to-prd`+`implement`（writing-plans 等價，無需訪談直接 synthesis PRD→
  執行）。原始 superpowers 版文字封存於 `.archive/superpowers-skills-v6.1.1/{brainstorming,writing-plans}/`
  （唯讀參考，非路由目標）。

若哪天有人往 SKILL.md 塞回 `fidelity-handoff` 形態決策+lint 閘 / 編號 ADR / skill-conformance-hub
的 `liveness`/`grounding` 欄位 / `superpowers:*` 引註，那就是把死 husk 搬回來——擋下（`sdlc-plan-composer`
已合法落地，不在此禁列）。

---

## Sources / Lineage
- northstar 源：`/Users/neon/northstar/.claude/skills/unknown-discovery-composer/skill.md`（v0.1.1）。
- antigravity 慣例／同型 port 先例：[`repo-agent-native/modules/retarget-map.md`](../../repo-agent-native/modules/retarget-map.md)、
  [`judge-loop-chooser/modules/retarget-map.md`](../../judge-loop-chooser/modules/retarget-map.md)、
  [`gemini-conversation-research/modules/retarget-map.md`](../../gemini-conversation-research/modules/retarget-map.md)、
  [`sdlc-plan-composer/modules/retarget-map.md`](../../sdlc-plan-composer/modules/retarget-map.md)（
  cc-20260705 補齊，填本表原記錄的缺口）、[`AGENTS.md`](../../../../AGENTS.md)。
- 下游本地 fork：`.agents/skills/repo-agent-native/`、`.agents/skills/gemini-conversation-research/`、
  `.agents/skills/judge-loop-chooser/`、`.agents/skills/sdlc-plan-composer/`。
