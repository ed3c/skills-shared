# Module: loop-harness-standard — 迴圈工程 Harness 技術規格與設計決策

> 屬 [`loop-harness-standard`](../SKILL.md)。SKILL.md＝組件卡＋不變量；本檔＝為何這樣設計、背景阻塞的除錯細節、資料流 Payload 剖析與可移植性。

---

## 1. 設計決策與 Know-Why (為何這樣做？)

### ❶ 為什麼將驗證器（Verify）與執行者（Execute）進行拓撲隔離與 verifier.md 驗證角色？
* **現象與退化風險**：寫代碼或寫資料的模型在自我審查時極度寬容。若將驗證邏輯與修改邏輯放在同一個 prompt 或同一個對話上下文，模型會進行「合理化」（Rationalization），容易導致 AI 在修改/新增功能時，改壞原有頁面的模組化功能而產生無聲的 Regression。
* **決策與防禦防線**：在 `run_loop_demo.sh` 中使用**硬性、純代碼或外部子代理**（如 `validate_primes.py` 或定義於 `.agents/agents/verifier.md` 的子代理人）來作為 Verify 閘門。AI 必須面對一個它無法用「花言巧語」或「修改代碼註解」討好的硬性判定閥值（Exit Code 0 vs 1）。
* **verifier.md 運作機制與職責**：
  1. **隔離驗證**：在更新功能前後，主代理人會調用並生成一個獨立於當前會話的 `verifier` 子代理人。該子代理人會以獨立、乾淨的 Context 執行小迴圈 Skill 目錄下的 `tests/[page]/[function]/verify.sh`。
  2. **行為等價判定 (Behavioral Equivalence)**：它負責檢查測試的 Exit Code 與執行輸出，驗證功能在修改前後是否行為等價，杜絕 regression 隱患。
  3. **出閘條件**：只有當所有 `verify.sh` 通過時，`verifier` 才會向主代理人回報成功，並寫入 `STATUS: done` 到 `IMPLEMENTATION_PLAN.md`。
* **子代理人規範**：子代理人採用 Markdown 與 YAML frontmatter 格式，置於 `.agents/agents/` 目錄中，藉由 Antigravity CLI 的 `/agents` 機制進行自動掃描與實例化，從而在執行期進行徹底的 Context 隔離審查，防範 Same-Context 漏洞。

### ❷ 為什麼 CLAUDE.md / AGENTS.md 常駐上下文必須限制在 300 行以內？
* **現象**：很多開發者喜歡把專案的所有細節、歷史 Bug 記錄與開發規範全部堆疊在根目錄的 `AGENTS.md` 內。這會導致每次對話在開啟時，就已經加載了數千個 token 的常駐上下文。
* **決策**：根據測量，過大的常駐上下文會使模型在定位關鍵約束（如 "Never rules"）時的注意力被稀釋，使得任務完成率從 **91.6% 暴跌至 71.3%**（**內部經驗值，primary source 未存檔——引用時禁作外部研究事實陳述，00:F-22**）。本標準規定 `AGENTS.md` 僅能宣告：
  1. 專案的簡短簡介與 stack；
  2. 核心指令；
  3. 最多 5 條的絕對禁止事項 (Never rules)。
  其餘細節必須以 **Skills**（放置於 `.agents/skills/`，並登錄於 `skills.json`）進行漸進式加載。

### ❸ 嵌套小迴圈的沙盒化轉換與八大基座分工
在巨型單體 Skill 重構為嵌套小迴圈沙盒化架構時，八大基座可分為 **「基座引擎本身 (Harness Engine Base)」** 與 **「由 Skill 轉換出的業務與狀態元件 (Converted Skill & State Components)」** 兩大類：

#### 1. 基座引擎本身 (Harness Engine Base)
這類檔案/目錄屬於底層基礎設施，負責控制 AI 的執行權限、生命週期監控與自動化調度：
* **工作目錄 (CWD) 物理隔離與調度**：大迴圈不直接調用子模組，而是透過 CWD 切換 `(cd loop_wiki/subproject-ixsecurity-e2e/android_e2e_loop && bash run.sh)` 執行 `run.sh`。
* **`run.sh` / `scripts/run_loop.sh` (調度引擎)**：驅動「計劃-執行-驗證-迭代」的本地 Orchestrator，確保背景無聲執行且自動重試。
* **`.agents/settings.json` (專案設定)**：配置 `"autoExecutionPolicy": "EAGER"` 進行自動化授權，防範背景 Stdin 阻塞。
* **`.agents/hooks.json` (生命週期鉤子)**：註冊 `PostToolUse` 等攔截機制，將操作日誌寫入 `data/log/hook_run.log` 防退化。
* **`.agents/skills.json` (技能註冊表)**：聲明本地加載或繼承的技能 Metadata 清單。

#### 2. 由 Skill 轉換出的業務與狀態元件 (Converted Skill & State Components)
這類檔案是由原單體 Skill 的知識、測試與歷史轉換而來，攜帶了該沙盒特有的業務邏輯與驗證指標：
* **`AGENTS.md` (常駐規則與 nevers 限制)**：由原 Skill 的基本行為限制轉換而來，定義專屬 Standing Context 與路徑邊界（維持在 300 行以內）。
* **`PROMPT.md` (目標規範合約)**：由原 Skill 的具體功能需求與 Success Criteria 轉換而來，定義每次迭代的 Goal Spec。
* **`IMPLEMENTATION_PLAN.md` (狀態與 PLAN 帳本)**：由原 CLAUDE.md 的歷史踩坑與進度轉換而來，記錄該小迴圈專屬的變更項目與 `STATUS: done/executing/failed`。
  > **F-16 正名**（05-ssot-drift-convergence.md §2.5 方案 A）：沙盒可採**狀態檔＋帳本分離**形態——單行狀態檔
  > `STATUS` 與迭代分析/失敗歷史分離，後者落 `docs/plans/<bundle>/00` 執行帳本；分離形態允許調度器整檔
  > 覆寫（`>`）狀態檔，合體形態（`loop_demo` 原型）則禁 `>` 整檔覆寫。
* **`.agents/skills/[skill-name]/` (特化技能與 Domain 知識)**：
  - `SKILL.md`：原單體 Skill 的觸發詞與檢索索引。
  - `modules/`：原單體 Skill 分拆出的**業務不變量與架構設計決策**文檔。
  - `scripts/`：原單體 Skill 分拆出的**實體執行 Levers 與工具腳本**。
* **`.agents/skills/[skill-name]/tests/[page]/[function]/verify.sh` (獨立硬性驗證器)**：
  - 由原 Skill 測試套件重構為頁面/功能級的等價測試。這作為獨立的 **Verify 驗證閘**，是防範 AI regression 的最核心防線。
* **`.agents/agents/verifier.md` (獨立審查角色)**：定義 `verifier` 子代理人，用以在乾淨的獨立 Context 中執行上述 `verify.sh`，杜絕 Same-Context 自我欺騙。


---

## 2. 踩坑排除：背景程序阻塞 (The Stdin Hang Fix)

在本地執行 `./run.sh` 時，我們發現了 `agy` CLI 在背景環境執行時的重大特性：

### ⚠️ 卡死現象
當腳本執行 `agy -p "..."` 時，程序會無聲卡死（Hanging），CPU 佔用率為 0，且不輸出 any stdout 或 stderr，甚至連 `cli.log` 都不會生成。此時使用 `ps` 可查看到 `agy` 進程處於 `T` (stopped) 或阻塞讀取狀態。

### 🔍 根本原因 (Root Cause)
`agy` CLI 預設為 interactive TUI 開發設計。當它被啟動時，底層的 Go/C 執行緒會嘗試連接與監聽標準輸入 (`stdin`)。在背景執行的進程（沒有實體 TTY 連接）若其 `stdin` 依然被 shell 保持在 open 狀態，`agy` 會在嘗試讀取 `stdin` 時進入**阻塞等待（blocking read）**。因為它不知道輸入何時結束，導致程式無限期卡住。

### 💡 解決方案
在調用指令時，顯式將 `stdin` 重導向至 `/dev/null`：
```bash
agy -p "prompt" < /dev/null
```
這會立即向 `agy` 的 stdin 傳送一個 `EOF` 訊號，促使 CLI 得知輸入端已關閉，進而直接以一期（One-Shot）的 Print Mode 執行，並在完成後立即退出。

---

## 3. Hook 系統資料流與 Payload 解析

當 `hooks.json` 的 Matcher 匹配到 Tool 執行時，它會將當前會話狀態封裝成 JSON 格式，並透過 `stdin` 送入配置的腳本中。

### 📋 實測 JSON Payload 結構
在 2026-07-06 的實測中，`on_write.py` 接收到的真實 `stdin` 結構如下：
```json
{
  "artifactDirectoryPath": "/Users/neon/.gemini/antigravity-cli/brain/1bc20061-e4b9-4855-955a-d98f40d1182b",
  "conversationId": "1bc20061-e4b9-4855-955a-d98f40d1182b",
  "modelName": "gemini-3-flash-agent",
  "stepIdx": 167,
  "toolCall": {
    "args": {
      "CommandLine": "find /Users/neon/.gemini/antigravity-cli/brain/ -name \"transcript.jsonl\" -mmin -10",
      "Cwd": "/Users/neon/ix-agy",
      "WaitMsBeforeAsync": 5000
    },
    "name": "run_command"
  },
  "transcriptPath": "/Users/neon/.gemini/antigravity-cli/brain/1bc20061-e4b9-4855-955a-d98f40d1182b/.system_generated/logs/transcript_full.jsonl",
  "workspacePaths": [
    "/Users/neon/ix-agy"
  ]
}
```

### ⚠️ 防崩潰解析邏輯
撰寫 Hook 程式時，**切勿使用扁平欄位**。必須照以下方式提取參數：
1. **Tool Name**：應存取 `data["toolCall"]["name"]`。
2. **Tool Args**：應存取 `data["toolCall"]["args"]`。
3. **防無聲錯誤 (Quiet Exit 0)**：Hook 腳本不論執行成功與否，若非刻意要阻斷（Block）Tool 的執行，在 `except` 區塊中**一律回傳 Exit Code 0**。若因 Hook 程式自身的語意解析錯誤 (如 JSON Key 遺失) 導致 Exit 1，會使得原本正常的 IDE Tool 調用被無故中斷。
4. **目標輸出路徑**：正式的攔截日誌應寫入當前沙盒的 **`data/log/hook_run.log`**。在 Hook 程式中需使用 `os.makedirs(os.path.dirname(log_file), exist_ok=True)` 確保路徑目錄完整。
5. **小迴圈本地 Hook 配置規範 (Mini-Loop Local Hook Configuration)**：
   - 每個小迴圈必須在 `.agents/hooks.json` 中配置特化 matcher，篩選 `write_to_file|create_file|edit_file|replace_file_content|multi_replace_file_content` 工具。
   - 執行命令（`command`）必須使用絕對路徑指向本地沙盒的 `.agents/hooks/on_write.py`，不得依賴全域 Hook 腳本。
   - `on_write.py` 內部的 `log_file` 路徑必須寫死為該沙盒自身的 `data/log/hook_run.log`，以達成物理結構上的執行期隔離。


---

## 4. 自動化移植指南 (Scaling & Migration)

若要將此迴圈與基座標準移植到本專案關聯的子項目（例如 `TrueMe_iOS`、`TrueMe_Android` 或 `ix-spec-runner`）：

### ❶ 基座複製
1. 將根目錄的 `AGENTS.md` 複製到子項目根目錄，並根據該子項目的 stack（如 Swift / Xcode 或 Kotlin / Gradle）修改常駐規則。
2. 在子項目中建立 `.agents/` 資料夾。
3. 建立 `.agents/settings.json`（配置沙盒）、`.agents/mcp.json`（配置該平台特屬 MCP，如 `ios-test-automation`）。
4. 建立 `.agents/skills.json`、`.agents/skills/` 與 `.agents/agents/` 存放特化技能與子代理人。

### ❷ 獨立驗證器與目標-狀態分離
1. 在子專案中撰寫專屬驗證器（如 `validate_build.sh` 或 `run_tests.py`）。
2. 在 `PROMPT.md` 寫入當前開發階段的 Success Criteria 目標，並由 `IMPLEMENTATION_PLAN.md` 追蹤迭代狀態（STATUS: executing/done）。
3. 在迴圈調度器中調用 `agy --project <id> -p "讀取目標與狀態並修正" < /dev/null`，並將 Verify 步驟對準該驗證器。

### ❸ 啟用自動化 Hooks
1. 將 `.agents/hooks.json` 複製到子專案。
2. 配置對應的 Pre/Post Tool 執行腳本，進行自動化監控與防護。

---

## 5. 可選組件與 CI/CD 校驗 (skills.json / test_harness_configs.py)

### ❶ `skills.json` 的定位與真實用途
在 Antigravity 2.0 中，本地 Skills 的載入是由 CLI 引擎進行目錄級自動發現（Auto-Discovery）的。`.agents/skills.json` 並非原生 CLI 執行時強制要求的組件。
然而，在多團隊協作、或進行 CI/CD 靜態代碼分析時，其被作為**顯式清單註冊表**：
1. **防禦性加載**：確保只有註冊在 `entries` 內的技能可以被 IDE 側欄或流水線加載，防止本地開發環境堆積無效或過期技能。
2. **外部繼承與共用**：可透過 `inherits` 鍵引入遠端 URI 技能包。

### ❷ 靜態結構校驗的硬性保障
在 `tests/test_harness_configs.py` 中，我們新增了針對 8 大 Harness 組件的靜態測試案例 `test_eight_harness_files`：
- 這使得基座的完整性可被 `pytest` 納入測試流水線，直接回報通過率（例如本案達成了 100% 成功率）。
- 任何人修改基座或遺漏元件（例如將 `verifier.md` 誤放回 `skills/`），測試套件將直接報錯攔截，防止迴圈退化。

---

## 6. Subproject Loop 泛用執行程序（Execution Steps）

> **Migrated from**: root `AGENTS.md`「Subproject Loops Execution & Configuration Procedure」節（00:F-17 根檔瘦身，2026-07-10 D2 review-hardening bundle Step 2）。root 僅保留觸發詞表＋本節指針。

1. **設定 Prompt 與規格**：
   * 切換至對應的小迴圈沙盒目錄（例如：`loop_wiki/subproject-ixsecurity-e2e/d2_e2e_loop/`）。
   * 開啟 `PROMPT.md`，寫入該迴圈的具體目標規格與修復描述。
   * **警告**：`PROMPT.md` 與 `AGENTS.md` 的內容必須字元級穩定，嚴禁寫入時間戳記或隨機變數以防 KV Cache 失效。
2. **啟動 Harness 運作**：
   * **特化小迴圈**：在沙盒目錄下執行 `bash run.sh`（底層呼叫 `scripts/run_loop_harness.sh`，執行 TDD 校驗並引導 `agy` 自動化自癒）。
   * **全域大迴圈**：在 `ix-agy` 根目錄下執行 `bash scripts/run_global_composite_loop.sh`，進行跨沙盒的編譯與實機模擬 E2E 整合驗證。
3. **驗證狀態與結果**：
   * 腳本執行完成後，檢查沙盒目錄下的 `IMPLEMENTATION_PLAN.md` 狀態，確認其變更為 `STATUS: done`。
4. **經驗折疊 (Fold-in)**：
   * 測試通過後，遵循 `fold-in` 技能規範，將新發現的不變量、Gotchas 或修復邏輯折疊進當地的 `modules/` 知識庫及 `SKILL.md` 中，防止領域知識污染全域標準。
