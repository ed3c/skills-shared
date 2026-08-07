# Module: 八大基座已知審計維度 checklist（＋逼未知）

> 屬 [`loop-harness-review-handoff`](../SKILL.md) skill。SKILL.md 6 步程序的第 ③ 步引用本檔。
> **用法**：交接時把下列**已知維度**逐項放進 reviewer 的審計任務,再帶 §逼未知 的 completeness-critic 提問。維度可複用、可依 session-adjustment（[handoff-know-why §4](handoff-know-why.md)）刪去已答項。
> 每維度指向的設計 SSOT 只**指針**（漂移時以真檔為準）：[`harness-spec`](../../loop-harness-standard/modules/harness-spec.md)、[`evals-design-method`](../../loop-harness-standard/modules/evals-design-method.md)、[`loop-architecture-ssot`](../../antigravity-harness-wiki/modules/loop-architecture-ssot.md)、pilot `loop_wiki/design_governance/`、引擎 `loop_wiki/engine.sh`。

## 已知審計維度（known dimensions；逐項掃）

### ① scripts/ vs tests/ 設計目的與最佳結構
- 小迴圈裡 `scripts/<checker>`＝checker 邏輯本體、`tests/<checker>/verify.sh`＝該 checker 的 wrapper＋good/hollow fixtures。**問**：兩者設計目的差異？scripts↔tests 1:1 拆分是否最優？wrapper 層必要嗎？fixtures 位置對嗎？`evals.json` 該不該吸收其中一層？**要求 reviewer 給結構建議**。
- 錨：`loop_wiki/design_governance/{scripts/,tests/,evals.json}`、[`loop-harness-standard` 分層驗證基座](../../loop-harness-standard/SKILL.md)（D8①成對）。

### ② 執行效率度量＋instrument
- **具體度量**：收斂輪數 iterations-to-converge／每次收斂 token 成本／wall-clock／planted-defect 檢出率／cache 命中率／driver 失敗/壞包率／**Goodhart 逃逸率**（＝機械綠但畢業判官 HOLD 的比例）。**問**：哪些是虛榮指標、哪些真反映效率？
- **如何 instrument**：引擎 `_engine-run/trajectory.log`、cache oracle `cache_read_input_tokens`（D7② CONFIRMED）、`_engine-run/`。
- 錨：`loop_wiki/engine.sh`、[`evals-design-method §engine-driven slice`](../../loop-harness-standard/modules/evals-design-method.md)（slice-1 HOLD／slice-2 R8 leak）。

### ③ passive-context 的 domain/路由/規則混雜是否稀釋注意力＋最優切分
- 小迴圈 AGENTS.md/CLAUDE.md（≤300 行）目前把 **domain 知識＋路由指針＋standing rules** 混在一起。**問**：這種混雜是否稀釋注意力、傷完成率（對照 [`harness-spec §3❷`](../../loop-harness-standard/modules/harness-spec.md) 記的 **91.6%→71.3%** 上下文腐化）？
- **最優切分建議**：domain 知識→`.agents/skills/`、路由/成功判準→`PROMPT.md`、少量鐵律→passive-context。**要求論證 + 含它對 D7 cache prefix 穩定性的影響**（切分若動搖 prefix 字元級穩定＝cache miss）。
- 錨：[`harness-spec §3❷`](../../loop-harness-standard/modules/harness-spec.md)、[`loop-harness-standard` 基座 1](../../loop-harness-standard/SKILL.md)（≤300 行/prefix 穩定）。

### ④ AGENTS.md / CLAUDE.md 差異是否最優
- 現行雙被動上下文設計（[`harness-spec §2`](../../loop-harness-standard/modules/harness-spec.md);agy 認 AGENTS.md、`claude -p` 認 subdir CLAUDE.md＋cascade、混家族單一 SSOT 派生）。**問**：是否最優？有無冗餘/漂移風險/可簡化處？
- 錨：[`loop-harness-standard` 基座 1](../../loop-harness-standard/SKILL.md)（D5 tracer）、記憶 `claude-p-loads-claude-md-not-agents`。

### ⑤ N×M（host×driver）覆蓋
- 完整矩陣 [`harness-spec §9❼`](../../loop-harness-standard/modules/harness-spec.md)：Claude Code host 兩格端到端已證（design_governance／agy_demo）、**Antigravity CLI（Gemini）host 兩格僅設計未證**。**問**：未證兩格的風險？補證的最小實驗？
- 錨：`harness-spec §9❼` 矩陣表（列 3/4「僅設計未證」）、canonical `loop_demo/{agy,claude_agy}`。

### ⑥ 效益疊加 vs 冗餘
- 對每個主要實作（八大基座、D1-D12 決策、引擎 slice-1/2、R7/R8 fold-back、semantic 判官 backstop、`--feedback`、隔離翻面、no-progress/exhausted stop-loss、cache 五不變量、tier 分派、slice-1.1 綁 target）：具體效益是**疊加(compound)還是重疊/冗餘**？**依價值排序 + 點名可砍的儀式性/冗餘/過度工程**（反膨脹,別客氣）。
- 錨：worked instance `REVIEW-HANDOFF-fable5.md` 任務 A、[`loop-architecture-ssot`](../../antigravity-harness-wiki/modules/loop-architecture-ssot.md)。

### ⑦ Goodhart 逃逸＋fold-back 閉環（R7/R8）
- **Goodhart 三級譜系**（[`evals-design-method`](../../loop-harness-standard/modules/evals-design-method.md) 定名）：① 路徑缺席（裸 ID）② 路徑存在但檔無關（M15）③ 路徑+節名 resolvable 但節內容不 govern（slice-1 misattributed）。**問**：fold-back（判官 finding→收緊 runnable checker,R7 精化／R8 leak）閉環是否常態?機械層永遠關不完 → semantic 判官是否永遠必要 backstop?`--feedback` 前置判準能否主動壓制（非被動追趕）?
- 錨：`loop_wiki/design_governance/scripts/{r7-dangling-id.py,r8-no-tool-syntax-leak.py}`、[`evals-design-method §engine-driven slice-1/slice-2`](../../loop-harness-standard/modules/evals-design-method.md)。

### ⑧ 驗證器設計/隔離/tier 經濟學
- **問**：驗證器隔離（跨家族天然 vs 同家族 fresh subagent 禁 fork,D6.1）是否落地正確?判官經濟學（Opus 做機械＝浪費、低 tier 裁決抓不到 Goodhart）tier 分派是否最優?畢業一次性 semantic 判官 vs 機械閘的分工是否清?
- 錨：[`harness-spec §9❻ tier-dispatch`](../../loop-harness-standard/modules/harness-spec.md)、[`loop-harness-standard` 鐵律 3/基座 6](../../loop-harness-standard/SKILL.md)。

## 逼未知（completeness-critic；每次交接必帶）

已知維度掃完只是 floor,不是 ceiling。交接提示詞必令 reviewer 額外回答：

1. **哪個維度沒被審?** ——上列八項之外,還有哪個基座/決策/資料流沒進任何維度的視野。
2. **哪個 claim 沒被驗?** ——建置者宣稱成立、但無確定性錨、reviewer 也未 read-only ground 的 claim,逐條標出。
3. **哪個基座沒 pilot?** ——僅設計未跑過真實例的基座/決策（如 Antigravity CLI host、某 checker 從未被真 target 觸發）。
4. **哪格 N×M 未證?** ——host×driver 矩陣哪格只有設計沒有端到端證據,補證的最小實驗是什麼。
5. **哪條不變量可能已悄悄漂移?** ——設計 SSOT 宣稱的不變量,對照真檔（`loop_demo`／`design_governance`／`engine.sh`）是否還成立,或已在某 slice 被打破而未同步。

> **紀律**：逼未知的回答同樣受 anchored-claims 約束——「我覺得可能還有 X 沒審」若不能落到具體維度/檔案,標為未錨推測,不算 finding（[handoff-know-why §3](handoff-know-why.md)）。
