---
name: fold-in
description: |
  把一段已完成的工作經驗（automate.js 修法／偵測邏輯／操作鐵律／某階段血淚）fold 進
  antigravity 既有的 skill 或 AGENTS.md「Resolved」帳本,而非為每段經驗造新 skill 時使用 —
  怎麼選 owner、Layer A（SKILL.md 事實＋程序）/ Layer B（modules/ know-why）分層、
  防回退帳本落哪、確定性邏輯的 husk 防護。選 owner 前先讀 antigravity-harness-wiki 全景圖當活系統邊界（別憑硬數字）;
  跨迴圈 fold 完回同步全景圖組件卡＋不變量（只指針不抄,fold-in 是最大漂移源）。actuator 委派 antigravity-skill-authoring。
  完整 know-why 在 modules/fold-in-know-why.md。
---

# Skill: fold-in — 把經驗吸收進既有 skill / AGENTS.md（非造新 skill）

> **Role**: 把一段**已完成**的工作經驗 fold 進 antigravity 的既有結構,而非造新 skill。**預設不造新** —— actuator 是 [`antigravity-skill-authoring`](../antigravity-skill-authoring/SKILL.md)（它判「該不該新建」）。
> **結構**: SKILL.md = 確定性程序 + 不變量;為何這樣分層、northstar lineage、retarget 映射表在 [modules/fold-in-know-why.md](modules/fold-in-know-why.md)。
> **SSOT**: 吸收的 durable home 是 [`AGENTS.md`](../../../AGENTS.md) 的「Resolved」防回退帳本 + owner SKILL.md 的 Gotchas;確定性邏輯的權威在 `automate.js`。漂移時以程式碼／帳本為準。
> **Lineage**: port 自 northstar `/fold-in`（`.claude/commands/fold-in.md`, DDR-205 Layer A/B）。northstar 的 skill-conformance-hub / problem-graph / M70 / materializer 機制**已 retarget 成 antigravity 對應物**（映射表在 module）,**非原樣搬**（原樣搬 = 引用不存在基座的 husk）。

## When to Use
- 剛修好 `automate.js` 某階段（偵測／自癒／重試／防回退）,要把「根因＋修法＋禁回退鐵錨」沉澱進 durable 結構。
- 一段操作鐵律／血淚（活 UI 漂移、額度枯竭判別、剪貼簿污染…）要吸收,而不是散在對話裡蒸發。
- 想加能力但**不確定該不該造新 skill** —— 先來這裡走「選 owner → 多半 fold 進既有」。

## Not For
- ❌ 判「這到底該不該新建 skill／新 skill 怎麼寫」的規範細節 → [antigravity-skill-authoring](../antigravity-skill-authoring/SKILL.md)（本 skill 的 actuator）。
- ❌ 跑管線／診斷管線失敗 → [dr-research-loop](../dr-research-loop/SKILL.md)。
- ❌ 查證外部 claim → [external-verify](../external-verify/SKILL.md)。
- ❌ 把 northstar 的 `/fold-in` 原檔複製進本 repo（引用 skill-conformance-hub / problem-graph / .northstar/run-all-tests.sh 等不存在基座 = 死 husk）。

## 不變量（違反即停）
1. **先選 owner,預設 fold 不造新**（Slop #2 / anti-inflation）。owner 候選＝**讀 [`antigravity-harness-wiki`](../antigravity-harness-wiki/SKILL.md) 組件卡當活系統邊界**（別憑記憶的「N 個 skill」硬數字——會 stale 且對新迴圈結構性失明;真值隨迴圈增長）—— 有語義貼近的 owner 就 fold 進它;真無 owner 且是操作鐵律／防回退 → 進 `AGENTS.md`「Resolved」或最貼近階段 skill 的 Gotchas。**只有真未覆蓋 niche + 人核** 才走 antigravity-skill-authoring 新建。
2. **SKILL.md 不胖**：know-why 一律進 owner 的 `modules/`;SKILL.md 只增**確定性事實／程序／Gotcha 一行**。
3. **frontmatter description 不含 ASCII `": "`**（冒號＋空格 → YAML 解析成 mapping → skill 被靜默跳過,連自己名字都 recall 不到）。多行一律 `|` block scalar、用全形「：」。
4. **確定性邏輯必有 automate.js 真實實現 ＋ 禁回退鐵錨**,否則只是散文 husk。吸收「某修法」時,該修法必須真在 `automate.js` 落地,且 `AGENTS.md`「Resolved」記一條 **`禁回退用 X`** ＋ live 實測紀錄。無鐵錨的「效率提升／已優化」= Half-Bridge 散文,不可宣稱吸收成立（Path B 紀律）。
5. **load-bearing 課畢業到 durable home,不留對話**。行為／操作鐵律 → `AGENTS.md`「Resolved」或 SKILL Gotchas;跨階段方法論 → dr-research-loop。**別**只記在對話或隨手筆記等它留 —— 對話是 ephemeral,不畢業 = 經驗蒸發。
6. **跨迴圈 fold 必回同步全景圖（掌握系統邊界）**：若 fold 動到某迴圈的**收斂閘／資料流歸屬／不變量／prompt-SSOT 指針**,fold 完必回頭核並更新 [`antigravity-harness-wiki`](../antigravity-harness-wiki/SKILL.md) 的組件卡＋不變量清單（**只改指針,永不抄內容**）—— 否則全景圖靜默漂成 husk（正是它要防的雙圖漂移;而 fold-in 是最主要的變異操作＝最大漂移源）。方法論／路由類 fold 無 automate.js 錨,其反-husk 錨＝**指向的 SSOT 是真檔案**（技術等價物判斷反身版,§5）。**動到大小迴圈八大基座（run.sh／被動上下文 AGENTS.md·CLAUDE.md／verify／driver 調用）時,fold 前先對 [`loop-harness-standard`](../loop-harness-standard/SKILL.md) 的 N×M 全景圖＋設計規範/實作差異表（`modules/harness-spec.md` §1-§2/§9）核對,防 fold 時把八大基座設計規範飄移**（指針對照永不抄;canonical 範例＝`loop_demo/{agy,claude_agy}`）。

## 確定性程序
1. **定 owner**：讀 [`antigravity-harness-wiki`](../antigravity-harness-wiki/SKILL.md) 組件卡（活系統邊界的迴圈清單,別憑硬數字）＋ AGENTS.md 的 domain,選最貼近的 owner（決策樹在 module）。
   - automate.js 某階段血淚 → 該階段 skill 的 Gotchas ＋ AGENTS.md Resolved。
   - 跨階段操作方法論 → dr-research-loop。skill 規範 → antigravity-skill-authoring。查證法 → external-verify。Path B → path-b-reduction。
   - 橫切多 owner → 列 ownership 拆分表（artifact → owner → 形式：Gotcha / module / Resolved 條）,分別 fold,仍不造新 skill。
2. **Layer A — owner SKILL.md（事實＋程序）**：在 `## 確定性程序` / `## Gotchas` / `## 已知失敗模式` 加 row 或 facet —— 只寫**事實／簽名／處置**,不寫 why。加指針 → `modules/<topic>.md`。
3. **Layer B — owner `modules/<topic>.md`（why）**：根因、rationale、為何這樣修、不變式論證寫這裡。
4. **AGENTS.md「Resolved」防回退帳本**（automate.js 血淚才需）：加一條 `<症狀>（<根因＋live 實測>）→ 已解：<修法>。禁回退用 <舊法>。` —— **additive,不覆蓋既有條**。
5. **shared infra**：helper 腳本 → owner skill 的 `scripts/`;automate.js 的執行邏輯**留在 automate.js**（SSOT）,skill 只指向。
6. **discrimination gate**：確認不變量 4 —— 確定性邏輯真在 automate.js ＋ Resolved 有禁回退鐵錨,否則退回（別存 husk）。
7. **actuate ＋ verify**：
   - actuator = [antigravity-skill-authoring](../antigravity-skill-authoring/SKILL.md)（adjust owner,非 create）。
   - 動 automate.js → `node --check automate.js`（不改跑動中的 run,只對下次啟動生效,要驗得重啟 live 跑一次）。
   - 動 skill → 查 frontmatter 無 ASCII `": "`、SKILL.md 大寫、body slim（know-why 已下放 modules/）。
   - **動到迴圈閘／資料流／不變量／prompt 指針 → 回核 `antigravity-harness-wiki` 組件卡＋不變量清單沒被打破,漂移就同步（指針不抄內容）**（不變量 6）。
   - commit 訊息解釋 **why**;收手前自審 diff。

## Gotchas（吸收時的鐵律）
- **造新 skill 是例外不是預設**：antigravity 6 skill 的規模,每段經驗新建 = catalog 墳場（Slop #2）。默認 fold。
- **AGENTS.md 是頂層索引,改它保守**：Resolved 帳本 additive、增量小步;動 Skills 清單記得同步（新 skill 才需列,fold 進既有不動清單）。
- **無 P0 materializer 保護**：AGENTS.md / SKILL.md 直接 Edit 即可（不同 northstar,無 auto-approve 攔截）—— 但正因無護欄,自審更要嚴。
- **description 靜默跳過**：吸收後若 owner skill「連名字都 recall 不到」,先查 frontmatter 有沒有混進 ASCII `": "`（antigravity-skill-authoring 同 gotcha,northstar PG-151 silent-failure class）。
- **信來源自證 = 幻覺源**：吸收外部框架／能力 claim 前先 external-verify 官方 doc,別靠訓練記憶。
- **fold-in 是最主要的變異操作 → 最大全景圖漂移源**：改任一迴圈的閘／資料流／不變量／prompt 指針後沒回同步 `antigravity-harness-wiki` = 讓那張防漂移地圖自己先漂。方法論／路由類 fold（無 automate.js 錨）的反-husk 錨＝**指向的 SSOT 是真檔案**（技術等價物判斷反身版:別指向不存在的基座——同 §5 retarget 命門）。

## Modules
- [modules/fold-in-know-why.md](modules/fold-in-know-why.md) — 為何 fold 不造新 / Layer A/B 分層 rationale / 「durable home 非 ephemeral」/ discrimination gate 為何要 automate.js 鐵錨 / **northstar → antigravity retarget 完整映射表**（每個 northstar 機制對應到哪、為何這樣映、拿掉了什麼）/ **boundary-aware（為何 owner 候選＝讀全景圖、fold-in 為何是最大漂移源）＋技術等價物判斷通則**。
