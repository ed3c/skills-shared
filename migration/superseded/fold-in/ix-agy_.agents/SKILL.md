---
name: fold-in
description: |
  把一段已完成的工作經驗（代碼邏輯／防退化檢測／操作鐵律／踩坑記錄）fold 進既有的 skill 或主文檔帳本（如 AGENTS.md / CLAUDE.md / README.md 等）—
  定義了 owner 選擇程序、Layer A（SKILL.md 事實＋程序）/ Layer B（modules/ know-why）分層、
  防退化帳本落地、確定性邏輯的 husk 防護（必須有代碼實現或測試守護）。
  本規範已進行通用化設計，不限於特定專案或 Domain 領域，以適用於各種自動化與開發系統。
---

# Skill: fold-in — 把經驗吸收進既有結構（非造新 skill）

> **Role**: 把一段**已完成**的工作經驗 fold 進既有結構（既有 skill、專案主文檔或不變量測試中）,而非隨意造新 skill。**預設不造新** —— 決策應由 skill 創建規範（如 `antigravity-skill-authoring`）判定。
> **結構**: SKILL.md = 確定性程序 + 不變量;為何這樣分層、設計決策溯源在 `modules/fold-in-know-why.md` 中。
> **SSOT (唯一事實來源)**: 吸收的 durable home 是 **owner modules 的 Resolved 帳本**（主文檔如 `AGENTS.md` / `CLAUDE.md` / `README.md` 僅留一行指針，不存副本全文） ＋ owner SKILL.md 的 Gotchas；確定性邏輯的權威在真實代碼實現與回歸測試中。

## When to Use
- 剛修好代碼或自動化腳本某階段（偵測／自癒／重試／防回退），要把「根因＋修法＋禁回退鐵錨」沉澱進持久結構。
- 一段操作鐵律／痛點（界面漂移、限額枯竭判別、環境污染等）要吸收，而非任由其在對話歷史中蒸發。
- 想新增能力但不確定是否應建立新 skill —— 先走本流程「選定 owner → 多半 fold 進既有結構」。

## Not For
- ❌ 判定「是否應新建一個獨立的 skill 以及如何設計新 skill」→ 交由 skill 創建規範處理。
- ❌ 執行或診斷運行管線中的具體失敗問題。
- ❌ 驗證未確認 of 外部框架/技術聲稱。

## 不變量（違反即停）
1. **優先選擇 owner，預設 fold 不造新（防膨脹）**：優先閱讀專案架構 wiki / 模組全景圖以獲取系統邊界（以 [antigravity-harness-wiki](../antigravity-harness-wiki/SKILL.md) 作為 Antigravity 本地案例，其整合了大小迴圈八大基座、非同步 Subagents 框架、Workspace 分支隔離、Tool Scoping 限縮 以及 DevOps & QA 雙防線自癒之全境拓撲）。有語意贴近的 owner 即 fold 進該 owner ；若無，則進入主文檔的「Resolved」防回退帳本或最貼近模組的 Gotchas。
2. **SKILL.md 不胖**：知其然（know-why）一律進入 owner 的 `modules/` 目錄下；SKILL.md 本身只增加**確定性事實／程序／Gotcha 一行描述**。
3. **frontmatter description 不含 ASCII `": "`**（冒號＋空格將導致 YAML 解析失敗使 skill 無法被識別，多行敘述請用 `|` block scalar，或用全形「：」）。
4. **確定性邏輯必有真實代碼實現或測試守護 (No Prose Husks)**：吸收的修復方案或運作規律，必須確實在代碼庫或自動化腳本中落地（以 `automate.js` 作為 Antigravity 本地案例），且在防回退帳本/回歸測試（如 unit tests、測試腳本 `test_*.sh`）中留有檢測鐵錨，否則僅視為無錨的散文，不能宣稱吸收成立。
5. **durable home，不留對話**： ephemeral 對話不及時畢業到持久檔案，經驗便會蒸發。
6. **同步系統全景圖與不變量**：若 fold 動到核心收斂閘、資料流或不變量指針，必須同步更新專案全景圖/架構文檔（以 [antigravity-harness-wiki](../antigravity-harness-wiki/SKILL.md) 作為本地同步與防簡化目標），確保地圖與疆域高度一致，並於 `modules/fold-in-know-why.md` 的 sitemap 節區登錄變更。
7. **防領域知識污染全域標準不變量 (⚠️ 核心鐵律)**：在進行 fold-in 時，嚴禁將特定子專案的本地業務/領域知識（如特定的 UI 元件屬性、特定代幣規格或特定 API 欄位邏輯）污染到全域的共享標準技能（如 `loop-harness-standard` 或 `fold-in` 本體）。共享標準技能必須保持 100% 泛用，而具體專案領域的知識一律解耦並 fold 進其沙盒當地的 `modules/` 或特化 Skill 中。
8. **大小迴圈四層分層架構與分流不變量 (⚠️ 核心鐵律)**：在進行經驗折疊時，必須嚴格依照以下四層架構進行分流放置：
   - **第一層：全域標準大迴圈（Harness Standard - Layer 1，如 `loop-harness-standard` / `fold-in`）**：僅允許收錄 100% 通用的迴圈引擎調度、超時自癒、快取失效及靜態/動態驗證分工等「純架構方法論」 Gotchas 與 resolved 條目，嚴禁寫入任何與特定自動測試工具（如 WDA / Maestro 屬性）、真機/模擬器除錯、Mock 後端或特定專案業務相關的知識。
   - **第二層：領域特化整合大迴圈（Domain Integration & Testing - Layer 2，如 `subproject-ixsecurity-e2e`）**：收錄專案層級的通用自動測試與環境除錯技術（如 UDP 日誌捕捉、背景 Port 爭用佔用清理、實機/模擬器主機私網連線邊界、WDA WKWebView content opacity UILabel bypass 等）。
   - **第三層：子專案/小迴圈特化技能（Specialized Skills - Layer 3，如 `.agents/skills/` 下的 `ios-simulator-automation` 等）**：各子專案或小迴圈所特有、需要獨立建檔或包裝之特化技能，存放該小迴圈專屬之平台與工程 Gotchas、不變量與輔助腳本。
   - **第四層：特化沙盒小迴圈配置（Sandbox Configurations & Ledgers - Layer 4，如 `loop_wiki/[sandbox]/AGENTS.md`）**：各沙盒的 `AGENTS.md` 或本機 `verify.sh` 測試檔，收錄具體頁面 UI 元件、特定 Mock 域名與 Egypt 端口、Nile 鏈上等待、PostgreSQL Int4 溢出限制、APNs 憑證注入 plist 等特化業務/參數踩坑。
9. **跨 scope 查重先行**：fold 進任一 Resolved 帳本／Gotchas 前，必先 grep 其他 scope（根主文檔／沙盒 AGENTS.md／owner skill modules）是否已有同一教訓；已有 → 更新原條目或改留指針，禁在第二 scope 另立副本（副本必分叉＝鐵律三違反態）。


## 確定性程序
1. **定 owner**：讀專案架構文檔或 wiki（如 `antigravity-harness-wiki`），選最貼近的 owner。
   - 代碼/操作踩坑血淚 → 該模組/頁面/階段的 Gotchas ＋ Resolved 帳本。
   - 跨階段操作方法論 → 專屬方法論/流程控制模組。
   - 橫切多 owner → 列出 ownership 拆分表，分別進行 fold 寫入，仍不造新。
2. **Layer A — owner SKILL.md（事實＋程序）**：在 `## 確定性程序` / `## Gotchas` / `## 已知失敗模式` 中加 row 或條目 —— 只寫**事實／特徵／處置**，不寫 why，並建立指針連往 `modules/<topic>.md`。
3. **Layer B — owner `modules/<topic>.md`（why）**：根因、設計背景、為何如此修復、不變式論證寫在這裡。
4. **防回退帳本登記**：於主文檔「Resolved」中加一條記錄：`<症狀>（<根因＋實測>）→ 已解：<修法>。禁回退用 <舊法/舊斷言>。`——此記錄為增量（additive），不可覆蓋既有歷史（以 `AGENTS.md` 作為本地Resolved實體）。
5. **shared infra**：helper 腳本放入 `scripts/`；具體執行邏輯留在實際代碼庫中，skill 只做指針指向。
6. **discrimination gate**：確認確定性邏輯有實質代碼與測試套件守護，否則退回（拒絕無實體 anchor 的散文）。
7. **actuate ＋ verify**：
   - 透過語法檢查、編譯器與測試套件（如 `test_*.sh` 或編譯打包）驗證修改。
   - 檢查 frontmatter 格式，確保無冒號半形空格衝突。
   - 自審變更日誌，提交 commit 訊息解釋變更 rationale。

## Gotchas（吸收時的鐵律）
- **造新是例外**：多個小經驗隨意新建 skill 會造成混亂，預設應進行 fold。
- **主文檔防回退帳本 additive**：主帳本變更應是增量小步，避免大面積覆蓋歷史。
- **無自動 materializer 保護時自審更嚴**：若沒有自動化工具審核 frontmatter 或 syntax，開發者必須手動且嚴謹地檢查每一行 invariant 與格式。
- **信來源自證 = 幻覺源**：吸收外部框架規則或系統邏輯前，必須查閱第一方官方文檔或源代碼，勿憑藉猜測。
- **指向的指針必須是真實存在的檔案**：方法論或路由類 fold 若無代碼實現錨，其反-husk 錨即為「指向的 SSOT 必須是物理存在的真實文檔」。
- **全域技能防領域知識污染**：在折疊新經驗時，務必分辨該經驗是「泛用的工具鏈與迴圈規範（放入全域標準）」還是「特定的專案業務細節（放入沙盒當地）」。混淆兩者會導致全域技能膨脹並失去通用性。
- **暴露 folded skill 給 slash 調用** → 建 `.claude/commands/<name>.md` 薄 router（三律：讀 skill 當 SSOT／不複述／零新引擎；frontmatter `name`＋`description`＋`argument-hint`；描述禁 ASCII `": "`；轉發指針須指真實檔）。ix-agy 是 Antigravity skills ＋ Claude Code 混合環境，command 與 skill 並存。詳見 `modules/fold-in-know-why.md` §8。

## Modules
- `modules/fold-in-know-why.md` — 深入解釋為何預設 fold、Layer A/B 分層設計原則、durable home 與 Ephemeral 對話區隔、防 husks 鐵錨驗證，以及各個自動化測試機制與 Mappings 對映表。
