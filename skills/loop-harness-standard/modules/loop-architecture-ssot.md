# Module: loop-architecture-ssot — 迴圈架構與提示詞單一真相來源 (SSOT)

> 屬 [`loop-harness-standard`](../SKILL.md)。本模組為迴圈工程的「資料流歸屬 ＋ 迴圈判斷邏輯 ＋ 全部原始提示詞」單一真相來源，用於防止開發者在修改某階段 Skill 或驗證器時，誤改或簡化閉環架構，導致自動化迴圈退化或退回到無聲失敗狀態。

---

## 1. 資料流歸屬與拓撲 (Data Flow Attribution)

在 Antigravity 迴圈中，資料流遵循嚴格的閉環路由，禁止產生未被監控或未被驗證的副作用。以下為資料流的歸屬關係：

```
                    [ 1. 目標輸入 (PROMPT.md) ]
                                │
                                ▼
               [ 2. 核心執行器 (agy --project) ] <─── [ 8. 常駐規則 (AGENTS.md) ]
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
[ 3. 變更目標 (data.txt) ]              [ 4. 狀態更新 (IMPLEMENTATION_PLAN.md) ]
        │                                               │
        ▼                                               ▼
[ 5. 硬性校驗 (validate_primes.py) ] <───┐   [ 6. 生命週期監控 (hooks.json) ]
        │                                 │             │
        ▼                                 │             ▼
[ 7. 判定出口 (Success / Fail) ] ────────┘   [ 6.1 寫入攔截日誌 (hook_run.log) ]
```

### 📋 元件資料流契約：
* **輸入源 (Inputs)**：由 `PROMPT.md` 宣告目標，`AGENTS.md` 約束邊界。執行器每次啟動必須完整讀取這兩者。
* **輸出源 (Outputs)**：
  - **業務資料**：寫入 `data.txt`（必須被校驗器或 `verify.sh` 腳本嚴格校驗）。
  - **狀態帳本**：寫入 `IMPLEMENTATION_PLAN.md`（必須包含 `STATUS: done/executing/failed` 狀態以供調度器 and 下次迭代 Plan 使用）。
    > **F-16 正名**（05-ssot-drift-convergence.md §2.5 方案 A）：沙盒可採**狀態檔＋帳本分離**形態——
    > `IMPLEMENTATION_PLAN.md` 退化為單行機器可讀狀態檔（`STATUS: done/executing/failed/blocked-on-triage`），
    > 迭代分析與失敗歷史改落 `docs/plans/<bundle>/00` 執行帳本（D2 迴圈為 worked instance）。
    > 分離形態下調度器可整檔覆寫（`>`）狀態檔；合體形態（`loop_demo` 原型）則禁 `>` 整檔覆寫。
* **控制流 (Control Flow)**：由 `run_loop_demo.sh` 或本地 `run_loop.sh` 驅動，透過對驗證腳本的 Exit Code 進行硬性判定，控制 `sed` 替換狀態檔並決定是否終止或迭代。
* **審查流 (Audit Flow)**：由 `.agents/hooks.json` 監控 Tool 調用，觸發 Hook 腳本將紀錄寫入 `data/log/hook_run.log`。
* **小迴圈沙盒化資料流拓撲 (Mini-Loop Sandboxed Data Flow)**：
  透過 CWD 切換命令進入 `loop_wiki/[loop_name]` 後，所有輸入輸出流完全閉鎖於該目錄內。`data.txt` 在此作為本地變更的業務目標數據（對應 wiki 條目）；`IMPLEMENTATION_PLAN.md` 則記錄該沙盒內高頻修正的自癒狀態，防範跨迴圈的全局變更污染。

---

## 2. 迴圈判斷邏輯與驗證器隔離 (Loop Decision Logic & Validator Isolation)

為了防止迴圈退化為「無聲失敗空轉」，每個步驟都必須有明確的技術等價判定：

1. **Discover (探索階段)**：
   * **動作**：讀取 `PROMPT.md` 與 `data.txt`。
   * **防退化不變量**：必須由 CLI 調度器動態向 AI 發出明確指令，告知讀取這兩個檔案的路徑，不可依賴 AI 自發性尋找。
2. **Plan (計劃階段)**：
   * **動作**：讀取 `IMPLEMENTATION_PLAN.md` 了解前次失敗歷史，讀取 `AGENTS.md` 了解 nevers 規則。
   * **防退化不變量**：AI 必須在 `IMPLEMENTATION_PLAN.md` 中先寫出「分析」段落，說明自己理解本次失敗原因，才能動手寫入。
3. **Execute (執行階段)**：
   * **動作**：AI 修改 `data.txt` 或業務代碼，並更新 `IMPLEMENTATION_PLAN.md` 中的變更紀錄。
   * **防退化不變量**：此時生命週期鉤子（Hooks）必須被觸發，實體日誌必須寫入 `data/log/hook_run.log`。
4. **Verify (驗證階段 - ⚠️ 核心防線 & verifier.md)**：
   * **動作**：調度器調用外部獨立驗證腳本（如 `validate_primes.py` 或由 `verifier.md` 定義的子代理人執行 `tests/[page]/[function]/verify.sh`）。
   * **防自我合理化不變量**：**嚴禁 Same-Context 自我審查**。`verifier` 必須在獨立、乾淨的 Context 中運行，校驗 Exit Code（0 代表 Success，1 代表 Fail）。這防止寫程式碼的模型在同一對話會話中「自己說測試通過」或「修改代碼註解」自欺欺人。
5. **Iterate (迭代階段)**：
   * **動作**：若 Verify 失敗且未達最大迭代次數，調度器寫入 failure 軌跡至 `IMPLEMENTATION_PLAN.md`，重置狀態為 `executing`，重新啟動 CLI；若全部通過，則標記 `STATUS: done` 並退出。

---

## 3. 全部原始提示詞與合約 (Original Prompts SSOT)

為避免開發者誤簡化或破壞閉環，在此封存所有關鍵元件的原始提示詞與合約：

### ❶ 核心 CLI 調度提示詞 (Runner Instruction Prompt)
封存於 `run_loop_demo.sh`，用於驅動 `agy` 的指令串：
```text
Read the goal specification in $WORKSPACE/PROMPT.md, check the rules in $WORKSPACE/AGENTS.md, inspect the current content of $WORKSPACE/data.txt and the validation script at $WORKSPACE/scripts/validate_primes.py. Write the correct primes to $WORKSPACE/data.txt. Update $WORKSPACE/IMPLEMENTATION_PLAN.md to document iteration $ITERATION, logging what you analyzed, what you changed, and setting STATUS to 'done' if completed.
```

### ❷ 目標規範合約 (`PROMPT.md` 原始內容)
```markdown
# Goal Specification: Prime Numbers Generation

Write exactly the first 5 prime numbers separated by commas to the file `data.txt`.

## Rules
- File `data.txt` must contain exactly: `2, 3, 5, 7, 11`.
- No additional whitespace, lines, or explanatory text is allowed in `data.txt`.
- Do not modify `validate_primes.py` or the runner script.
```

### ❸ 子代理人審查合約 (`verifier.md` 原始內容)
封存於 `.agents/agents/verifier.md`，用於執行獨立審查：
```markdown
---
name: verifier
description: Reviews the content of data.txt. Invoke when you need to check if the data matches the criteria.
tools:
  - read_file
  - run_command
model: inherit
---
# Verifier Agent
You are the Verifier agent. Review the content of `data.txt`.
Your task is to report whether the file contains exactly the first 5 prime numbers separated by commas: `2, 3, 5, 7, 11`.
If it matches, output "PASS". If not, output "FAIL" and explain why.
```

### ❹ 特化技能合約 (`calculator/SKILL.md` 原始內容)
封存於 `.agents/skills/calculator/SKILL.md`：
```markdown
---
name: calculator
description: Reusable skill to calculate prime numbers.
---
# Calculator Skill
Use this skill when you need to calculate prime numbers mathematically.
The first 5 prime numbers are 2, 3, 5, 7, and 11.
Format: Comma-separated without other characters.
```

### ❺ 子項目小迴圈特屬合約與範本 (Subproject Loop Specific Prompts & Templates)

> **F-15 硬化**（`05-ssot-drift-convergence.md` §2.4 方案 B，2026-07-11）：下列兩份合約原為「封存
> 全文快照」，但快照隨實檔演進必然 stale（已實證：封存的 verifier 舊約寫 `STATUS: done`，現行
> `verifier.md` 已改為唯讀不寫——封存檔自己成了過期副本）。改為**指針＋凍結不變量摘要**：全文
> 以實檔為準，此處只留防簡化的合約錨（防的是不變量被簡化，不是實作快照被改動）。

#### 1. 小迴圈 Orchestrator 遞迴掃描合約 (`run_loop.sh`)
**實檔**：`loop_wiki/subproject-ixsecurity-e2e/d2_e2e_loop/scripts/run_loop.sh`——**以實檔為準**，
本節不再封存快照全文。

**凍結不變量摘要**（違反即視為基座退化；不隨實作演進而改寫，只隨用戶 admit 增修）：
- 分層鏈（Layer 0 錨點 pre-flight → static tests → build → evidence-pair E2E → behavior evals →
  Layer 4b UU 掃描/triage 閘）只能新增層或新增子閘，禁刪除既有層或繞過其判定。
- Exit code 語義凍結：`0`＝全鏈通過；`1`＝有紅（任一層判定失敗）；`2`＝blocked-on-triage
  （UU 掃描命中未分類條目，非判定失敗，等待人工分類）——三值語義禁增改。

**防簡化對照**：不再以本檔內嵌快照比對——改由 `git log -p -- scripts/run_loop.sh` 取代
（實作真實演進史即比對基準；快照本身已被實證會 stale，見上）。

#### 2. 小迴圈特屬獨立校驗代理人合約 (`.agents/agents/verifier.md`)
**實檔**：`loop_wiki/subproject-ixsecurity-e2e/d2_e2e_loop/.agents/agents/verifier.md`——**以實檔為準**，
本節不再封存快照全文。

**凍結不變量摘要**：
- **唯讀**：verifier 只證不修——絕不寫入任何檔案（`IMPLEMENTATION_PLAN.md`／`triage.md`／configs 皆禁）。
- **不改分類**：不得重新分類 triage 條目，不得編輯白名單/註冊表條目。
- **不寫 STATUS**：`STATUS` 欄位由 orchestrator（`run_loop.sh`/`run_loop_harness.sh`）依 exit code 寫入，
  verifier 不得代寫。
- **exit code 透傳**：verifier 覆核 `bash scripts/run_loop.sh` 的 exit code 並原樣轉譯為
  PASS(0)/FAIL(1)/BLOCKED-ON-TRIAGE(2)，不得自行改判。

**防簡化對照**：不再以本檔內嵌快照比對——改由 `git log -p -- .agents/agents/verifier.md` 取代。

---

## 4. 防修改/防簡化黃金守則

* **禁止移除 `validate_primes.py`**：任何將驗證改為「讓 LLM 閱讀 `data.txt` 後回答是否正確」的簡化，均視為基座退化，會引發 AI 自動化軟卡死。
* **禁止合併 `PROMPT.md` 與 `IMPLEMENTATION_PLAN.md`**：目標與狀態必須物理隔離，否則 AI 會在迭代過程中自我改寫 `PROMPT.md` 中的目標以求測試通過。
* **重導向 `/dev/null` 禁止刪除**：在 CLI 自動化中，調用 `agy` 時必須保持 `< /dev/null` 重導向，否則背景進程必然卡死掛起。

---

## 5. 大大小迴圈組合與疊加執行架構 (Harness & Sandbox Composition)

當專案擴展為多個子專案或多層級任務時，採用「大迴圈主導全域，小迴圈特化沙盒，組件式疊加遞迴」的組合拓撲，以防止全域狀態污染與生命週期鉤子（Hook）死鎖。

### ❶ 大迴圈與小迴圈的沙盒化分工 (Harness vs. Sandbox)
* **大迴圈（主基座，根目錄）**：負責全域生命週期監控（根目錄 `hooks.json`）、外部 MCP 服務註冊、跨子專案的目標與進度追蹤（根目錄 `PROMPT.md` 與 `IMPLEMENTATION_PLAN.md`）。禁止在大迴圈根目錄下直接執行單一子任務的高頻修改迭代。
* **小迴圈（特化沙盒，位於 `loop_wiki/[loop_name]` 與 `/Users/neon/ix-agy/loop_demo/`）**：沙盒化隔離。每個特化小迴圈擁有獨立的啟動腳本、專屬的 `PROMPT.md`/`IMPLEMENTATION_PLAN.md` 狀態記錄與特化設定（如 `settings.json` 的 `"autoExecutionPolicy": "EAGER"` 自適應授權）。高頻修正與精修在沙盒內部隔離運行，收斂後結束控制並 Ingest。其中，`/Users/neon/ix-agy/loop_demo/` 作為 8-Harness 沙盒鏡像結構的基準參照（Baseline Reference），包含完整的自包含運行與校驗腳本。

### ❷ 疊加執行方式 (Stacked Pipeline Composition)
小的迴圈工程可以疊加組合成更複雜的工程鏈。典型的疊加方式是「前一個小迴圈的產物，作為後一個小迴圈的 Scope 與輸入」：
* **第一層（L1 語義理解，`repo_wiki_converge`）**：分析代碼庫並生成散文 wiki（標記 `kind: repodoc`），列出關鍵模組。
* **第二層（L2 不變量 facts，`repo-agent-native`）**：讀取 L1 的 wiki 作為 `SCOPE` 種子，精準進入源碼抽取 invariants 契約事實（標記 `kind: invariants`）。
* **第三層（L3 規格 mastery，`codebase-mastery`）**：在 L1 和 L2 的事實基礎上，生成 formal spec 並執行測試校驗。
* 各迴圈產物寫入各自隔離路徑，保證邊界清晰，Ingest 至 Knowledge Graph 時標記不重疊。

### ❸ 已收斂跳過優化 (Skip-if-Converged)
在大迴圈調度多個小迴圈時，各小迴圈的啟動器必須支援「已收斂跳過」機制。在進入高頻修復 loop 前，先讀取 gaps 檔案：
```bash
if [ -f "$GAP_FILE" ] && grep -q "CONVERGED=true" "$GAP_FILE"; then
  echo ">>> [SUCCESS] $SLUG is already converged! Skipping loop execution."
  exit 0
fi
```
此機制防止大迴圈重複執行已達標的小迴圈，節省計算資源與 Token 消耗。


---

## 6. Monolithic-to-Sandboxes Conversion Spec (單體 Skill 拆分沙盒化映射)

在進行單體巨大 Skill（如 `subproject-ixsecurity-e2e`）拆分與沙盒化移植時，必須對齊以下 **8-Harness 映射關係**以防功能與驗證退化：

| 原單體 Skill 組件 | 拆分後沙盒實體元件 | 職責轉換與防退化要求 |
| :--- | :--- | :--- |
| **原 `SKILL.md` 規則性內容** | **`AGENTS.md` & `PROMPT.md`** | 原本的 nevers 規則與絕對限制寫入 **`AGENTS.md`**（保持在 300 行內以防注意力稀釋）；任務目標與驗證指標（Success Criteria）寫入 **`PROMPT.md`**，實現目標與規則解耦。 |
| **原 `modules/` 領域知識文檔** | **`.agents/skills/[skill]/modules/`** | 將各小迴圈專屬的 Domain 知識與架構設計文檔（例如 `step-parity.shared.md`）集中放置於該沙盒特化技能的 `modules/` 中，防止全局知識庫污染。 |
| **原 `scripts/` 工具與執行腳本** | **`.agents/skills/[skill]/scripts/` 或 `scripts/`** | 業務執行 Levers（如 `audit-parity.py`）移至沙盒技能的 `scripts/`，並由調度器或驗證器引用。 |
| **原 `tests/` 功能與防退化測試** | **`.agents/skills/[skill]/tests/[page]/[function]/`** | 將原有的頁面級/功能級自動化校驗腳本移至沙盒特化技能的 `tests/` 中。這作為獨立的 **Verify 驗證閘**，是防範 AI 誤改與功能退化的最核心防線。 |
| **原 `CLAUDE.md` 歷史踩坑與進度** | **`IMPLEMENTATION_PLAN.md`** | 每個小迴圈沙盒維護獨立的 `IMPLEMENTATION_PLAN.md` 狀態帳本，追蹤該沙盒的迭代進度與失敗歷史，使狀態記錄完全自包含。 |
| **專案執行設定與授權** | **`.agents/settings.json` & `.agents/hooks.json`** | 顯式配置 `"autoExecutionPolicy": "EAGER"` 進行自動化授權，並在 `hooks.json` 中配置該沙盒專屬的 Tool 攔截監控。 |
| **大迴圈調度入口** | **`run.sh` & `scripts/run_loop.sh`** | 每個小迴圈擁有獨立 of `run.sh` 作為 Orchestrator 入口。在大迴圈中，使用 `(cd loop_wiki/[loop_name] && bash run.sh)` 進行 CWD 切換執行，確保環境與設定完全隔離。 |


---

## 7. 小迴圈快取與動態路由優化規範 (Sub-Loop Cache & Trigger Optimization Spec)

為了在小迴圈高頻修正迭代中達到極致的 Token 節省與零退化，必須遵循以下快取（Prompt Caching）與動態觸發路由優化規範：

### ❶ Gemini API 快取執行門檻與機制
* **顯式快取門檻**：Gemini 2 最低需 2,048 Tokens，Gemini 3 最低需 4,096 Tokens 才能觸發顯式快取。若小迴圈的常駐上下文過小，未達門檻則無法顯式觸發。
* **隱式快取 (Implicit Caching)**：使用 Gemini 2.5 / 3.5 / Next 級別模型時，API 會自動在後端對同會話（Session）內多輪 Tool-Call 的 KV 狀態進行快取，無須手動介入。
* **降本實測錨點**：快取讀取（Cache Read）約 `0.1×` 成本。但經實測，它對多輪往返重載 Context 的總費用稀釋收益大約只有 **15%**（**實測記錄未存檔——內部經驗值，引用時禁作外部研究事實陳述，00:F-22**），並非「省一半」量級。因此最佳降本策略為**「批次做大、輪次壓少（單次開啟 3-5 輪內退出）」**，而非單純指望快取。

### ❷ 前綴穩定性鐵律 (Prefix Stability Invariant)
* **快取命中關鍵**：Gemini API 快取依賴**精確的前綴字元匹配**（Character-by-character）。
* **執行約束**：小迴圈的常駐上下文（`AGENTS.md`、`.agents/settings.json`、`.agents/skills.json`）在多次迭代中必須**字符級完全穩定不變**。絕對禁止在常駐提示詞中加入動態變數（如當前時間戳記、動態臨時路徑、隨機 ID）。前綴的 any 微小變更都會導致 Cache 宣告失效（Cache Invalidation），造成嚴重 Token 浪費。

### ❸ 動態觸發路由優化 (Dynamic Trigger Routing)
* **防注意力稀釋**：常駐 `AGENTS.md（file:///Users/neon/ix-agy/loop_wiki/subproject-ixsecurity-e2e/d2_e2e_loop/AGENTS.md）` 必須控制在 300 行以內。詳細業務邏輯與操作步驟（Procedural Know-How）應移至特化沙盒的 `SKILL.md` 中。
* **觸發詞精準度**：為確保 `SKILL.md` 被動態加載（0 浪費按需調用），Skill 檔案的 frontmatter `triggers` 必須豐富地註冊核心業務特徵與文件名（如 `D2WalletVC`、`btnQRCode`、`BiometricPrompt` e.g., CIBALogin, NFC reader mode），避免因 Prompt 未包含預設的 `"local validation"` 字眼而遺失關鍵不變量知識。

### ❹ 小迴圈執行最佳實踐 (Best Execution Practice)
1. **工作目錄 (CWD) 切換**：始終使用 `(cd <loop_dir> && bash run.sh)` 執行以載入該沙盒的 `settings.json`（尤其是 `EAGER` 自動授權設定）及 `hooks.json`。
2. **重導向 `/dev/null`**：背景或自動化運行 `agy -p` 時，必須追加 `< /dev/null` 防止 interactive TUI 等待 stdin 造成無限掛起。
3. **清理孤兒進程**：啟動前查殺孤兒進程 `ps -ef | grep agy | kill -9` 釋放 SQLite DB 鎖，防止資料庫鎖定爭用（DB Lock Contention）。
4. **會話持久性 (Session Reuse)**：在同一任務的修復中復用相同的 `conversationId`，透過 Transcript 歷史自動享受會話內快取，不要每次都重新 `/clear`。

---

## 8. 證據對驗證層：Verify 階段的泛用擴充範式 (Evidence-Pairing Verify Layer)

§2.4 的 Verify 閘在最簡形態是「跑校驗腳本、看 Exit Code」。當被驗證的目標是**概率性 UI／
執行期行為**（而非確定性檔案內容如 `data.txt`）時，單一 Exit Code 無法回答「畫面對了，
但實作是否走了正確代碼路徑、是否考慮過已知未知」。此時 Verify 閘擴充為**五層證據對架構**——
這是 §2.4 的**泛用擴充範式**（非某子專案專屬），完整規範與提示詞在
`../../subproject-ixsecurity-e2e/modules/e2e-evidence-pairing-methodology.md`，
D2 迴圈為其首個 worked instance。

### ❶ 五層 Verify 拓撲（Driver→Journey→Capture→Eval→Verdict）
```
[Driver 平台原語] → [Journey 宣告式步驟+checkpoint] → [Capture 成對證據束落盤]
                                                              │
                        ┌─────────────────────────────────────┘
                        ▼
[Eval 雙通道行為判定(UI×log×state)] → [Verdict 四格矩陣 + UU 掃描 + triage]
```
* **設計規範差異（vs §2.4 基礎 Verify）**：基礎 Verify＝確定性 Exit Code；證據對 Verify＝
  同一 checkpoint 落盤 `{ui.json, log.txt, state.json}` 三視角，雙通道交叉出
  **PASS / SILENT-DEGRADATION / PRESENTATION-GAP / BROKEN** 四格——最危險的
  SILENT-DEGRADATION（畫面碰巧對但走錯路徑）正是單通道 Exit Code 永遠看不見的盲區。
* **實作差異**：新增 **UU 掃描器**（log 異常＋未預期元素）作為 run_loop 的**第 4b Verify 子閘**——
  命中不自動 FAIL 也不自動忽略，落 triage 交人 admit（承接 §2.4「嚴禁 Same-Context 自我審查」
  的人本裁決精神，退出碼擴為 0 全過／1 有紅／2 待 triage）。

### ❷ 三源去重＝Eval SSOT 律在 Verify 層的投影
預期行為易散落四處（目標規範 PROMPT.md／monolith 測試／per-page verify／執行期腳本 inline 常數），
即 §4「防雙圖漂移」在測試層的復發。收斂鐵律：靜態結構斷言留 per-page `verify.sh`、
執行期行為遷入宣告式 eval config（唯一執行期 SSOT）、PROMPT.md 保目標規範地位以 `invariant_ref` 回指。

### ❸ 大迴圈執行紀律（本次多子代理分派實跑回饋的兩條泛用教訓）
* **共享工作樹 HEAD 重驗律**：大迴圈以子代理分派切片、或與別的開發流共用同一 working tree 時，
  **源碼 HEAD 會漂移**——別的 commit 可靜默改掉本迴圈依賴的源碼錨點/元素。每個切片動手前必
  **重驗 HEAD 現況**，禁憑記憶假設沿用（本次 D2 執行的最大單一教訓：改版 commit 洗掉合約錨點，
  症狀被誤診為「時序」追了四輪，根因是 HEAD 漂移）。
* **fresh-context 子代理 per-slice**：把可獨立的驗證/修復切片派給**零上下文子代理**（非 fork），
  一片一個乾淨 context——與 §2.4 verifier 隔離同源：獨立 context 防「同會話自我合理化」。
  切片間無跨依賴才並行；有共享檔案（如同一 AGENTS.md 節）則序列化，避免並發寫衝突。
