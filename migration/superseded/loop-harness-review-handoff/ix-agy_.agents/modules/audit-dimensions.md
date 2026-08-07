# Module: 八大基座已知審計維度 checklist（＋逼未知）

> 屬 [`loop-harness-review-handoff`](../SKILL.md) skill。SKILL.md 6 步程序的第 ③ 步引用本檔。
> **用法**：交接時把下列**已知維度**逐項放進 reviewer 的審計任務,再帶 §逼未知 的 completeness-critic 提問。維度可複用、可依 session-adjustment（[handoff-know-why §4](handoff-know-why.md)）刪去已答項。
> 每維度指向的設計 SSOT 只**指針**（漂移時以真檔為準）：[`harness-spec`](../../loop-harness-standard/modules/harness-spec.md)、[`loop-architecture-ssot`](../../loop-harness-standard/modules/loop-architecture-ssot.md)、[`e2e-evidence-pairing-methodology`](../../subproject-ixsecurity-e2e/modules/e2e-evidence-pairing-methodology.md)、pilot `loop_wiki/subproject-ixsecurity-e2e/d2_e2e_loop/`、canonical `loop_demo/`、各小迴圈引擎 `run_loop.sh`/`run.sh`。

## 已知審計維度（known dimensions；逐項掃）

### ① scripts/ vs tests/ 設計目的與最佳結構
- 小迴圈裡 `scripts/<checker>`＝checker 邏輯本體（如 D2 的 `evidence_eval.py`／`uu_scan.py`）、`tests/<page>/<fn>/verify.sh`＝該功能的獨立 Verify 閘＋fixtures。**問**：兩者設計目的差異？scripts↔tests 拆分是否最優？per-page verify.sh vs 集中式引擎的邊界對嗎？宣告式 `configs/*.yaml`（eval SSOT）該吸收哪一層、不該吸收哪一層？**要求 reviewer 給結構建議**。
- 錨：D2 `d2_e2e_loop/scripts/{evidence_eval.py,uu_scan.py}`、`.agents/skills/d2-e2e-loop/tests/<page>/<fn>/verify.sh`、`configs/d2-behavior-evals.yaml`、[`loop-harness-standard` 分層驗證基座](../../loop-harness-standard/SKILL.md)（八大基座組件卡 · 頁面/功能等價測試隔離）。

### ② 執行效率度量＋instrument
- **具體度量**：收斂輪數 iterations-to-converge／每次收斂 token 成本／wall-clock／planted-defect 檢出率（＝金絲雀反轉是否必轉紅）／cache 命中率／driver 失敗/壞包率／**Goodhart 逃逸率**（＝機械綠但判定真空/畢業判官 HOLD 的比例）。**問**：哪些是虛榮指標、哪些真反映效率？
- **如何 instrument**：run_loop 尾端 summary block（SKIPPED/PENDING/BROKEN 計數）、退出碼 0/1/2、金絲雀 `canary.py` 的紅/綠翻面、cache oracle `cache_read_input_tokens`。
- 錨：D2 `run_loop.sh`（Layer 1-5＋UU 第 4b 閘、三值 STATUS）、`evidence_eval.py` summary、[`loop-architecture-ssot §8❶`](../../loop-harness-standard/modules/loop-architecture-ssot.md)（退出碼 0/1/2）、[方法論 §9.6 缺席語意分級](../../subproject-ixsecurity-e2e/modules/e2e-evidence-pairing-methodology.md)。

### ③ passive-context 的 domain/路由/規則混雜是否稀釋注意力＋最優切分
- 小迴圈 AGENTS.md/CLAUDE.md（≤300 行）目前把 **domain 知識＋路由指針＋standing rules** 混在一起。**問**：這種混雜是否稀釋注意力、傷完成率（對照 [`harness-spec §1❷`](../../loop-harness-standard/modules/harness-spec.md) 記的 **91.6%→71.3%** 上下文腐化）？
- **最優切分建議**：domain 知識→`.agents/skills/*/modules/`、路由/成功判準→`PROMPT.md`、少量鐵律→passive-context。**要求論證 + 含它對 cache prefix 穩定性的影響**（切分若動搖 prefix 字元級穩定＝cache miss,見 [`loop-architecture-ssot §7❷` 前綴穩定性鐵律](../../loop-harness-standard/modules/loop-architecture-ssot.md)）。
- 錨：[`harness-spec §1❷`](../../loop-harness-standard/modules/harness-spec.md)、[`loop-architecture-ssot §7`](../../loop-harness-standard/modules/loop-architecture-ssot.md)（≤300 行/prefix 穩定/觸發詞路由）。

### ④ AGENTS.md / CLAUDE.md 差異是否最優
- 現行雙被動上下文設計（agy 認 AGENTS.md、`claude -p` 認 subdir CLAUDE.md＋cascade;混家族單一 SSOT 派生）。**問**：是否最優？有無冗餘/漂移風險/可簡化處？大迴圈根 `AGENTS.md`（全域邊界）vs 小迴圈本地 `AGENTS.md`（沙盒鐵律）的分工是否清？
- 錨：[`loop-architecture-ssot §1/§4`](../../loop-harness-standard/modules/loop-architecture-ssot.md)（PROMPT/PLAN 物理隔離、AGENTS.md 常駐規則）、[`harness-spec §1❸`](../../loop-harness-standard/modules/harness-spec.md)。

### ⑤ 覆蓋矩陣（host×driver / checkpoint×variant）
- **host×driver**：Claude Code host 與 Antigravity CLI（Gemini）host × 各 driver 的端到端覆蓋——哪格已證、哪格僅設計未證。
- **checkpoint×variant**（D2 實例）：D2-CP-0/1/2/3 × {default, unauthenticated 變體} 的證據束覆蓋——`identity-qr-hidden-02`／`wallet-lockdown-05` 走未認證變體 run。**問**：未證格的風險？補證的最小實驗？
- 錨：canonical `loop_demo/`、D2 `d2-evidence-pair-evals §4 checkpoint 表`（CP-1u/2u 變體）、[`loop-architecture-ssot §5 大小迴圈組合`](../../loop-harness-standard/modules/loop-architecture-ssot.md)。

### ⑥ 效益疊加 vs 冗餘
- 對每個主要實作（八大基座、D2 五層架構 Driver/Journey/Capture/Eval/Verdict、四格矩陣、UU 掃描 triage、state 通道補判、金絲雀反真空、累積擷取窗、三源去重、錨點 HEAD 重驗）：具體效益是**疊加(compound)還是重疊/冗餘**？**依價值排序 + 點名可砍的儀式性/冗餘/過度工程**（反膨脹,別客氣）。
- 錨：worked instance `REVIEW-HANDOFF-fable5.md` 任務 A、[`e2e-evidence-pairing-methodology §2-§9`](../../subproject-ixsecurity-e2e/modules/e2e-evidence-pairing-methodology.md)、[`loop-architecture-ssot §8`](../../loop-harness-standard/modules/loop-architecture-ssot.md)。

### ⑦ Goodhart 逃逸＋fold-back 閉環（UU→KK/KU 收斂）
- **判定真空譜系**：① 引擎沒讀 config（金絲雀反轉仍綠）② eval 只綁 UI 單通道（SILENT-DEGRADATION 盲區）③ log pattern 過鬆遷就無錨代碼（偽合約）。**問**：fold-back（UU triage → 真缺陷補 KK eval／規格缺口補 KU eval／良性入白名單）閉環是否常態？機械層永遠關不完 → 畢業一次性 semantic 判官是否永遠必要 backstop？金絲雀能否主動壓制真空（非被動追趕）？
- 錨：D2 `canary.py`（判定真空探測）、`uu_scan.py`＋`configs/d2-known-elements.yaml`（註冊表收斂）、[方法論 §6 UU triage 迴路／§8 白名單問責律／§9.3 金絲雀](../../subproject-ixsecurity-e2e/modules/e2e-evidence-pairing-methodology.md)。

### ⑧ 驗證器設計/隔離/tier 經濟學
- **問**：驗證器隔離（跨家族天然 vs 同家族 fresh subagent 禁 fork）是否落地正確？判官經濟學（Opus 做機械＝浪費、低 tier 裁決抓不到 Goodhart）tier 分派是否最優？畢業一次性 semantic 判官 vs 機械閘（金絲雀/UU 掃描）的分工是否清？UU triage 的**人 admit** 兩道人閘（首批分類 · monolith 除役）是否在對的位置？
- 錨：[`loop-harness-standard` 鐵律 3](../../loop-harness-standard/SKILL.md)、[`loop-architecture-ssot §2.4/§8❸`](../../loop-harness-standard/modules/loop-architecture-ssot.md)、[方法論 §6 triage 人 admit](../../subproject-ixsecurity-e2e/modules/e2e-evidence-pairing-methodology.md)。

## 逼未知（completeness-critic；每次交接必帶）

已知維度掃完只是 floor,不是 ceiling。交接提示詞必令 reviewer 額外回答：

1. **哪個維度沒被審?** ——上列八項之外,還有哪個基座/決策/資料流沒進任何維度的視野。
2. **哪個 claim 沒被驗?** ——建置者宣稱成立、但無確定性錨、reviewer 也未 read-only ground 的 claim,逐條標出。
3. **哪個基座沒 pilot?** ——僅設計未跑過真實例的基座/決策（如 Antigravity CLI host、某 checker/某變體 CP 從未被真 run 觸發）。
4. **哪格覆蓋矩陣未證?** ——host×driver 或 checkpoint×variant 矩陣哪格只有設計沒有端到端證據,補證的最小實驗是什麼。
5. **哪條不變量可能已悄悄漂移?** ——設計 SSOT 宣稱的不變量,對照真檔（`loop_demo`／D2 證據系統／`run_loop.sh`）是否還成立,或已在某 slice 被打破而未同步（如合約錨點被上游改版靜默洗除,方法論 §9.5）。

> **紀律**：逼未知的回答同樣受 anchored-claims 約束——「我覺得可能還有 X 沒審」若不能落到具體維度/檔案,標為未錨推測,不算 finding（[handoff-know-why §3](handoff-know-why.md)）。
