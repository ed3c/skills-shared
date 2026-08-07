---
name: loop-harness-review-handoff
description: |
  把一次大小迴圈 harness 的架構 review／audit／優化**交接**給獨立 fresh-session reviewer 時使用——
  設計零上下文自足的交接提示詞,讓一個新 session 的高推理 reviewer（Fable 5 設計評審／Opus 裁決;
  agy 不當判官因 Gemini only）獨立審計並優化八大基座（scripts↔tests 結構／執行效率度量／passive-context 混雜／
  AGENTS.md·CLAUDE.md 差異／N×M 覆蓋／效益疊加／Goodhart 逃逸＋fold-back／驗證器經濟學）。
  findings-only、每 claim 帶確定性錨、admit 永遠是人。fresh-session＝評審隔離（同家族靠新 session 零上下文達獨立、跨家族天然）。
  何時用：要把 loop-harness 的一次架構 review/audit/優化派給獨立新 session reviewer 時。
  觸發詞：交接架構評審、reviewer handoff、fresh-session 獨立審計、八大基座 review、loop-harness 優化交接、
  審計維度 checklist、loop-harness-review-handoff。
  NOT for：跑迴圈/診斷（dr-research-loop）、選驗證 tier（judge-loop-chooser）、未知路由（unknown-discovery-composer）、
  查外部 claim（external-verify）。完整 know-why 在 modules/handoff-know-why.md。
---

# Skill: loop-harness-review-handoff — 大小迴圈架構 review/audit 交接方法論

> **Role**：設計一份**零上下文自足**的交接提示詞,派給獨立 **fresh-session reviewer**（Fable 5＝設計/高推理架構評審／Opus＝裁決;agy 不當判官[Gemini only]）獨立審計與優化大小迴圈八大基座。輸出 **findings-only**,**admit＝人**。
> **結構**：SKILL.md ＝ 6 步確定性程序＋5 條不變量＋Gotchas;為何 fresh-session＝隔離、reviewer tier 選型 rationale、anti-sycophancy/anchored-claims 為何、session-adjustment 方法在 [modules/handoff-know-why.md](modules/handoff-know-why.md);八大基座已知審計維度 checklist＋逼未知在 [modules/audit-dimensions.md](modules/audit-dimensions.md)。
> **活實例（本方法論的一個 worked instance,泛化它別重造）**：[`docs/plans/2026-07-09-loop-harness-panorama/REVIEW-HANDOFF-fable5.md`](../../../docs/plans/2026-07-09-loop-harness-panorama/REVIEW-HANDOFF-fable5.md)（Fable 5 交接提示詞實例）;可複用骨架在 [reference/handoff-template.md](reference/handoff-template.md)。
> **設計 SSOT（交接指向的權威,只指針不抄）**：[`loop-harness-standard`](../loop-harness-standard/SKILL.md)＋`modules/harness-spec.md`（八大基座設計規範）·[`antigravity-harness-wiki`](../antigravity-harness-wiki/SKILL.md)`modules/loop-architecture-ssot.md`（全景 SSOT）·canonical 範例 `loop_demo/{agy,claude_agy}`·pilot 證據 `loop_wiki/design_governance/`·引擎 `loop_wiki/engine.sh`。

## When to Use
- 要把一次 loop-harness 的**架構 review／audit／優化**交接到新 session（獨立 reviewer 零上下文審計）時。
- 已有一批八大基座實作/決策要被獨立高推理評審點名「效益疊加 vs 冗餘可砍」＋逼出未想到的優化時。

## Not For
- ❌ 跑迴圈／診斷管線失敗 → [dr-research-loop](../dr-research-loop/SKILL.md)。
- ❌ 選某 deliverable 的驗證標準＋獨立性 tier → [judge-loop-chooser](../judge-loop-chooser/SKILL.md)。
- ❌ 未知路由／發掘編排 → [unknown-discovery-composer](../unknown-discovery-composer/SKILL.md)。
- ❌ 查證外部/post-cutoff claim → [external-verify](../external-verify/SKILL.md)。
- ❌ 建/改一條新迴圈的工程規範本體 → [loop-harness-standard](../loop-harness-standard/SKILL.md)（本 skill 是**把它的 review 交接出去**,不是定義基座）。

## 確定性程序（6 步，逐步產出交接提示詞）
1. **reviewer tier 選型**：設計/高推理架構評審 → Fable 5;裁決型 → Opus;**agy 永不當判官**（Gemini only,見記憶 agy-runs-gemini-only）。**fresh-session＝評審隔離**——同家族 reviewer 靠**新 session 零上下文**達獨立（非 fork）、跨家族天然隔離。tier 邊界錨 [`evals-design-method §tier 邊界`](../loop-harness-standard/modules/evals-design-method.md)＋[`harness-spec §9❻ tier 分派表`](../loop-harness-standard/modules/harness-spec.md)。
2. **入口 curation（由淺入深別淹死；curate 非丟整 repo）**：計畫意圖（`00-intent-and-knowhow.md` D1-D9）→ 設計 SSOT（`loop-harness-standard` SKILL＋`harness-spec §1-§9`、`antigravity-harness-wiki/modules/loop-architecture-ssot.md`）→ canonical 範例（`loop_demo/{agy,claude_agy}`）→ pilot 證據（`loop_wiki/design_governance/PLAN.md §5-6` 判官逐字 findings、`loop_wiki/agy_demo/`）→ 引擎（`loop_wiki/engine.sh`）→ 執行故事（`git log`）。並**授權 reviewer 跑 read-only 驗證 ground**（`selftest.sh`／`engine.sh … --dry-run`／`_engine-run/trajectory.log`／`git show <commit>`）。
3. **套審計維度 checklist**：把 [modules/audit-dimensions.md](modules/audit-dimensions.md) 的八大基座已知審計維度逐項放進交接任務,並帶「逼未知」的 completeness-critic 提問（哪維度沒被審／哪 claim 沒驗／哪基座沒 pilot／哪格 N×M 未證）。
4. **session-adjustment（差量交接）**：依 review target 的內容、**自上次交接已變動的 slice**、reviewer tier,調整本次重點與**已答維度**——只重點審已變動＋未答維度,不每次重審全量。
5. **findings 紀律**：交接提示詞內明令——每 claim 帶**確定性錨**（檔案:行／exit code／實測數字／官方 primary source）、未錨**明標**（Path B）、不附和不表演式同意、read-only grounding、**findings-only**（不改檔、不下 admit）。
6. **輸出結構**：交接提示詞要求 reviewer 產出——① **效益疊加表**（排序＋可砍清單）② **未想到的優化**（優先序＋rationale＋錨）③ **設計問題逐一答＋推薦解** ④ 結尾 **Top-3 最高槓桿改動**。

## 不變量（違反即停）
1. **findings-only、admit 永遠是人**：reviewer 不改任何檔、不下 admit;決策權在人（交互契約 human-exit-gate）。
2. **每 claim 帶錨、未錨明標**：無確定性錨的平滑敘事（「效率提升」「更好」）＝不可宣稱成立,標為未錨（Path B 紀律）。
3. **fresh-session＝隔離＋reviewer tier 匹配**：設計/高推理→Fable/Opus、裁決→Opus、**agy 不當判官**;同家族靠新 session 零上下文達獨立（禁 fork）、跨家族天然。
4. **入口由淺入深別淹死**：curate 入口（計畫意圖→設計 SSOT→範例→pilot→引擎→git log）＋授權 read-only 驗證,**不丟整個 repo**給 reviewer（會淹死注意力,同 91.6%→71.3% 上下文腐化風險）。
5. **審計維度 checklist 必掃 known＋逼出 unknown**：八大基座已知維度逐項掃過,並用 completeness-critic 逼出「沒被審的維度/沒驗的 claim/沒 pilot 的基座/未證的 N×M 格」。

## Gotchas
- **reviewer 同家族靠 fresh-session 隔離、非 fork**（fork 帶母上下文＝污染獨立性;D6.1 禁 fork 同源）。跨家族（如 Opus 審 Gemini 產物）天然隔離。
- **別讓 reviewer 讀整個 repo**：curate 入口由淺入深,否則注意力被稀釋、findings 變泛。授權 read-only 驗證讓 reviewer 自己 ground,不預先塞滿。
- **ground claims 否則 Half-Bridge 散文**：交接提示詞若不強制「每 claim 帶錨」,reviewer 會回一堆「感覺更好」的平滑敘事（技術上站不住）;錨是 findings 可用性的命門。
- **交接是方法論類 fold 的近親——反-husk 錨＝指向的 SSOT 是真檔案**：入口 curation 列的每個路徑必真存在（loop-harness 兩 skill／loop_demo／engine／REVIEW-HANDOFF-fable5.md）,別指 phantom。

## Modules
- [modules/handoff-know-why.md](modules/handoff-know-why.md) — Layer B know-why：為何 fresh-session＝隔離（零上下文獨立,同家族亦成立）／reviewer tier 選型 rationale（Fable 設計 vs Opus 裁決 vs agy 不當判官,錨 evals-design-method §tier＋harness-spec §9 tier 表）／anti-sycophancy 與 anchored-claims 為何（Path B）／session-adjustment 差量交接方法。
- [modules/audit-dimensions.md](modules/audit-dimensions.md) — 八大基座**已知審計維度 checklist**（scripts↔tests 結構／執行效率度量＋instrument／passive-context 混雜＋最優切分／AGENTS.md·CLAUDE.md 差異／N×M 覆蓋／效益疊加 vs 冗餘／Goodhart 逃逸＋fold-back 閉環／驗證器經濟學）＋**逼未知**的 completeness-critic 提問。
- [reference/handoff-template.md](reference/handoff-template.md) — 泛化 `REVIEW-HANDOFF-fable5.md` 的可複用交接提示詞骨架（ROLE／紀律／入口 curation／審計任務 A-C／輸出格式＋佔位）,並指針到該 worked instance 當實例。
