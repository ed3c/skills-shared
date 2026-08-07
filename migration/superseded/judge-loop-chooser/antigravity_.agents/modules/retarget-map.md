# Module: judge-loop-chooser — northstar → antigravity retarget 映射 + 誠實拿掉了什麼

> 屬 [`judge-loop-chooser`](../SKILL.md)。本檔 = port 的**命門與誠實帳本**：哪些機制一對一映到 antigravity、哪些**沒有基座被拿掉、為何拿掉不是簡化**。
> 命門：northstar `judge-loop-chooser` 的**核心是 code/sandbox 判決表**（`execution/lib/judge_chooser.yaml` → design-judge 沙盒）。**antigravity 無此基座**。原樣搬 = 引用一堆跑不動的東西 = 死 husk（antigravity `fold-in.md` 反模式明文禁）。

---

## 1. 為何這個 port 比 fold-in 更需要「拿掉一整條 branch」

northstar 的 judge-loop-chooser 是**雙 branch**：
- **Branch A（absorption/landing）**：DR 落地物 → strategic-intent reviewer + flywheel gates + external-verify。→ **這條 retarget 得乾淨**（antigravity 的 DR 產物本就是 absorption）。
- **Branch B（code/sandbox）**：`judge_chooser.route(target_type)` → ai-era-design-judge / fullstack-design-judge / self-correcting-loop 沙盒 → `tier_for(scope)` → loop。→ **這條在 antigravity 無任何基座**。

antigravity 是**瀏覽器自動化執行器**（YouTube→AI Studio→Gemini DR,`automate.js`）。它的可判物是 **DR 報告 / Path B 精煉 / 覆蓋矩陣**,**不是代碼樹或 design-judge 沙盒**。所以 Branch B 的判決表、macro/micro design-judge、`tier_for` 模型路由、self-correcting-loop **全部拿掉**——保留它們 = 讓 skill 引用不存在的 `execution/lib/`、不存在的沙盒、不存在的 loop kernel。

---

## 2. 逐機制 retarget 映射表

| northstar 機制 | antigravity 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| Claude 斜線命令 `.claude/commands/judge-loop-chooser.md`（`$ARGUMENTS`） | 保留為**薄轉發層** `.claude/commands/judge-loop-chooser.md`（指向 `.agents/skills/` SSOT）+ Antigravity 原生 skill `.agents/skills/judge-loop-chooser/SKILL.md` | 本 repo 雙平台：Claude Code 走 command 轉發、Google Antigravity 走 activate_skill,同一 SSOT。 |
| **Branch B** `execution/lib/judge_chooser.yaml`（target_type → judge/scope/tier/loop 決策表) | **拿掉** —— 換成「DR/Path B/覆蓋矩陣 三型」路由 | antigravity 無 design-judge 沙盒、無 `execution/lib`。決策表的基座不存在。 |
| ai-era-design-judge / fullstack-design-judge 沙盒 | **拿掉** | antigravity 無 `sandboxes/`。 |
| self-correcting-loop（loop kernel `decide=ITERATING`） | **拿掉** | antigravity 的 loop 是 [`dr-research-loop`](../../dr-research-loop/SKILL.md)（DR 管線閉環,非代碼迭代 kernel）。 |
| `tier_for(scope)` 模型路由（macro→Opus / micro→Sonnet;task-graph-decomposer 傳遞等價） | **拿掉** —— 換成獨立性 tier（T0-T3） | antigravity 不做代碼尺度模型路由;它要的是「驗證用哪個獨立性 tier」。 |
| strategic-intent reviewer payload（`strategic-intent-review-prompt.md`,SI1-SI8） | 保留,retarget → [modules/intent-drift-review.md](intent-drift-review.md)（intent=卡片盒問題;SI5→SOURCE-INTEGRITY;SI6→EQUIVALENT-FIT） | **這是 Branch A 的核心,乾淨映射**。 |
| grounding 三態 SSOT（`grounding-axis-panorama-ssot.md` + `validate_grounding` 機器閘） | 保留 know-why → [modules/grounding-and-independence.md](grounding-and-independence.md);**活基座換成 `automate.js:199` COMPLETENESS_RUBRIC**;機器閘 → **拿掉,SURFACE-only** | 三態語意 antigravity 早已在 automate.js prompt 跑;但無 `judge_chooser.py:validate_grounding` 確定性閘,改人 VERIFY。 |
| 四層獨立性階梯（`four-tier-independence-ladder.md`） | 保留,T2 工具換成 [`external-verify`](../../external-verify/SKILL.md) + 跨家族 Gemini | whose-weights 軸與平台無關;只換 T2 的具體工具。 |
| flywheel absorption gates（`_bridge_thesis_validator` / `_mirror_finding_validator`,PG-159/161） | **拿掉／降級** —— 併入 intent-drift reviewer 的 SI1/SI7 + external-verify | antigravity 無 flywheel 引擎、無這些 standing validator 腳本。紀律（thesis 覆蓋 / mirror 自欺）折進 reviewer 探針。 |
| `sdlc-plan-composer §S5` 委派來源 | **（cc-20260705 更新）已落地 antigravity 本地 fork**（`.agents/skills/sdlc-plan-composer/`）,是本 skill 合法的 S5 觸發源之一 | 落地時本表原記為「無此 skill」——已補。本 skill 路由邏輯**不因此改動**：sdlc-plan-composer 只委派過來,不重複其判準;本 skill 仍以「一輪 DR 完成 / 一份覆蓋矩陣 / 一段 Path B 精煉 / 一次技術選型」為觸發點,無論呼叫者是誰。 |
| `mega-flow-harness-hub` post-hoc 觀察 | **拿掉** | antigravity 無此 skill;本 skill 的觸發源改成「一輪 DR 完成 / 一份覆蓋矩陣要判」。 |
| `intent-drift-detector` DriftReport schema / `task-graph-decomposer` 模型路由 SSOT | **拿掉** —— reviewer 直接吐自描述 drift 報告 | antigravity 無這些 schema/腳本;drift 報告改成自由格式的 SURFACE。 |
| global `problem-graph/`（PG-001/103/156/158/210 路由）+ ADR-0010/0011/0014 | **拿掉編號,保留紀律散文** | antigravity 無 PG/ADR 系統。硬造 = 引入不存在的雙圖。紀律（recipe-not-engine / placebo / auto-DECISION 禁）以散文錨在 automate.js 行為上。 |
| Pattern Card #1 materializer（P0 檔禁直接 Edit） | **拿掉** —— SKILL.md / AGENTS.md 直接 Edit | antigravity 無 auto-approve.sh P0 保護。無護欄 → 自審更嚴補償。 |
| `.northstar/run-all-tests.sh` + `execution/lib/test_judge_chooser.py`(15 綠) | **拿掉／換** —— `node --check automate.js` + 人審 | antigravity 無 test runner / 無 judge_chooser.py。驗證錨換成 syntax check + live。 |
| RIP 實例 sandcastle #7 boundedTail | **拿掉** —— 換成 antigravity 自己的 grounding 實例（COMPLETENESS 覆蓋矩陣的真/空心勾） | northstar 沙盒實例在 antigravity 不存在;grounding 的 RIP 錨在 automate.js 覆蓋矩陣真跑。 |

---

## 3. 拿掉的東西不是「簡化」,而是「不引入不存在的基座」

northstar judge-loop-chooser 的 Branch B 決策表、design-judge 沙盒、`validate_grounding` 機器閘、PG/ADR 路由、materializer、test runner 在 northstar 是**活的**（有對應基座）。在 antigravity 它們**沒有基座**——保留它們 = 讓 skill 引用一堆跑不動的東西 = 正是 antigravity `fold-in.md` 反模式禁的「原檔搬進本 repo 引用不存在基座 = 死 husk」,也是 northstar 自己反的 supply-push husk（RIP：不被調用的能力不是能力）。

retarget 的正確姿勢：
- **能一對一映的映**：轉發層、Branch A reviewer、grounding 三態語意、獨立性階梯。
- **活基座換掉**：grounding 錨 `judge_chooser.yaml` → `automate.js:199 COMPLETENESS_RUBRIC`;T2 工具 → external-verify;loop → dr-research-loop。
- **沒對應物的誠實拿掉並記錄**（本表）：Branch B 全套、機器閘、PG/ADR 編號、materializer、test runner。

**判別「retarget 成立」的鐵錨**：本 skill 引用的每個 antigravity 基座都真存在（`automate.js:199/233` grounding、`external-verify`/`path-b-reduction`/`dr-research-loop` 三 skill 真在 `.agents/skills/`）。若哪天有人往 SKILL.md 塞回 `execution/lib` / `judge_chooser.yaml` / 沙盒 / PG-NNN,那就是把死 husk 搬回來——擋下。

---

## Sources / Lineage
- northstar 源：`/Users/neon/northstar/.claude/skills/judge-loop-chooser/`（skill.md + 3 modules + strategic-intent-review-prompt.md;`execution/lib/judge_chooser.{py,yaml}` + `docs/adr/0010/0011/0014`）。
- antigravity 慣例：[`antigravity-skill-authoring`](../../antigravity-skill-authoring/SKILL.md)、[`fold-in`](../../fold-in/SKILL.md)（同型 port 先例:retarget 非原樣搬）、[`AGENTS.md`](../../../../AGENTS.md)。
- 活基座：`/Users/neon/antigravity/automate.js`（COMPLETENESS_RUBRIC / PATH_B_TEMPLATE / val_bpb）。
