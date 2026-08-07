# Module: fold-in — know-why + Cross-Platform Retargeting Mapping

> 屬 [`fold-in`](../SKILL.md) skill。SKILL.md 有確定性程序與不變量；本檔深入闡述其設計決策、方法論背景、以及跨平台遷移（以 Northstar → Antigravity 為案例）的對應映射表。

---

## §1. The Principle of Fold-in over Creation (Catalog Anti-inflation)

在任何程式庫或自動化工程中，**能力並非是「收集」出來的，而是被「調用與執行」出來的**（即：不影響 Runtime 行為與檢查的能力等於不存在）。
如果為了解決每一個新修好的 Bug 或每一條操作經驗，都隨手新建一個獨立的 Skill 或獨立的指導文件，會迅速造成**目錄膨脹（Catalog Cemetery）**：
* 產生大量重疊、描述模糊且彼此爭奪語義觸發的空殼（Husks）。
* **Fold-in 的核心防線**：預設任何新經驗均能被既有的 Owner（模組/階段/Skill）所吸收。只有在經過嚴格判定並證明該經驗屬於全新的技術領域（Niche）時，才啟動新建流程。
* **Grounding 原則**：一條確定性的修復邏輯，如果直接折疊寫入既有 Owner 的 Gotchas 或代碼中，是實質顆粒度的前進；而隨意新增說明性文檔，則是無效的文字增殖。

---

## §2. Layer A (Slim Checklist) & Layer B (Know-why Module) Split

大型系統為了優化上下文負載（Token / Context Efficiency）與精準執行，普遍採用漸進載入（Lazy-loading）機制：
* **Layer A (SKILL.md / 主入口)**：僅包含確定性程序、操作 checklist 與 gotcha 一行流。保證開發者或 Agent 在被觸發時，能立刻照著執行，不被長篇大論的原理干擾。
* **Layer B (modules/)**：存放 Lazy-loaded 的深度 know-why、設計溯源、根因分析與取代歷史，僅在需要追查或重構時才進行讀取。

---

## §3. Durable Homes vs. Ephemeral Conversations

對話歷史（Chat Logs）與短期記憶是 **Ephemeral (臨時性的)**：在下一次對話中不保證被加載，血汗換來的操作教訓會隨之蒸發。
因此，Fold-in 要求所有實質性的規則必須畢業（Graduate）到一個 **Durable Home (持久性歸宿)**：
* 系統行為/操作鐵律 → 專案主文檔帳本（如 `AGENTS.md` / `CLAUDE.md` / `README.md` 的「Resolved」防回退區塊）或 Owner Skill 的 Gotchas。
* 跨階段方法論 → 專屬流程控制模組。
* 任何留在對話記錄中而不落地持久檔案的經驗，皆被視為「未完成吸收」。

---

## §4. Codebase Anchoring & Invariant Assertions (No Prose Husks)

吸收一段修復經驗時，最常見的幻覺是寫下空泛的散文描述（例如「優化了某某流程的穩定性」），但在代碼庫中卻沒有具體的實作，也沒有任何回歸檢測。這種不對稱被稱為 **Half-Bridge (半橋，只有描述沒有錨)**。
為防止 Half-Bridge 墮落為 Prose Husk (文字空殼)，必須建立雙重鐵錨：
1. **代碼庫錨點**：修復或防禦邏輯必須確實在代碼庫、自動化腳本中落地（並通過語法與編譯器檢測）。
2. **回歸檢測鐵錨**：必須在防退化帳本中登記「禁回退對象」，並在回歸測試中（如 `test_*.sh` 或 unit tests 斷言）建立自動化檢查。

---

## §5. Cross-Platform Retargeting Mapping (Case Study: Northstar → Antigravity)

在將一套標準工具或平台命令移植（Port）至目標平台時，必須遵循**「技術等價物判斷通則」**：
* 識別源平台機制，映射至目標平台的等價實作。
* 對於目標平台不存在的底層基礎設施（Infrastructure），**必須誠實地拿掉並記錄，不可保留半橋或空殼指針**（例如引用一個不存在的測試執行器）。

### 映射案例：Northstar → Antigravity 對應映射表
以下展示如何將 Northstar 平台概念，實質 retarget 至當前的 Antigravity 本地基座：

| Source (Northstar) | Target (Antigravity) 對應物 | 映射決策 rationale / 拿掉了什麼 |
|---|---|---|
| Claude Code 命令 `.claude/commands/fold-in.md`（帶 `$ARGUMENTS`） | Antigravity skill `.agents/skills/fold-in/SKILL.md`（Skill 調用） | 轉換為 Antigravity 固有的 Skill 體系，無命令列 flag，改以語義進行啟動與參照。 |
| M70 / `skill_match` 語義選擇器 | 閱讀架構 wiki/全景圖手動選擇 | Antigravity 本地 Skill 規模小，手動閱讀 sitemap 即可，避免過度設計的自動化。 |
| Actuator (自動 Skill 創建器) | `antigravity-skill-authoring` | 平台專屬 Skill 規範 SSOT。對齊命名與模板。 |
| Layer A/B 目錄分層 | `SKILL.md` ＋ `modules/` | 結構完全一致，直接沿用。 |
| 經驗吸收 Home (`CLAUDE.md-slim`) | **`AGENTS.md`「Resolved」防回退帳本** ＋ Gotchas | 皆為頂層、每 session 自動載入的 durable index，僅檔名與專案慣例不同。 |
| 全域 `problem-graph/` ＋ `pg/` 路由 | **拿掉** —— 改進 `AGENTS.md`「Resolved」或 Gotchas | 當前環境無 PG 自動路由基座，強行保留只會產生不存在的 phantom references。 |
| 測試套件 `.northstar/run-all-tests.sh` | 語法檢查（`node --check`、`swift`）＋ `test_*.sh` 靜態檢測 ＋ live 實測 | 無 unified test runner，將驗證錨點改為本地編譯器、靜態 check 腳本與實機 runtime 驗證。 |
| Materializer (P0 檔案寫入保護) | **拿掉** —— 直接進行 Markdown / Code 編輯 | 本地無寫入攔截守護。因此自審與 Code Review 必須更加嚴格。 |

---

## §6. Boundary-Aware Sitemap Sync (防止地圖漂移)

在遞迴式的迴圈架構中（例如結合了理解、不變量提取、規格生成等多重小迴圈），任何一個 fold-in 動作都是對系統的「變異操作」，也是最大的漂移源。
因此，設計上必須保證**邊界感知（Boundary-Aware）**：
* **動態閱讀 sitemap 掌握系統邊界**：尋找 Owner 候選時， Agent 必須強制閱讀與掌握整合了「大小迴圈八大基座、非同步 Subagents 框架、Workspace 分支隔離、Tool Scoping 限縮 以及 DevOps & QA 雙防線自癒」的 [antigravity-harness-wiki](../../antigravity-harness-wiki/SKILL.md) 整合全境圖，以獲得最新的系統邊界與資料流向，禁止盲目修改。
* **指針同步（不對稱複製）**：如果 fold-in 變更了任何階段 of 收斂閘、資料流或指針，必須同步更新 [antigravity-harness-wiki](../../antigravity-harness-wiki/SKILL.md) 主全景圖的對應指針，且**僅更新指針，永不抄寫內容**（抄寫即製造了雙圖，必將導致地圖與疆域的二次漂移）。
* **方法論/路由類的反-husk 錨**：若該 fold 屬於不帶實體程式碼的方法論（如決策邏輯、架構全景），其驗證錨點即為「其指向的 SSOT 必須物理存在於磁碟上，且指向的檔案路徑不得為空（如與 AGENTS.md 完成關聯引用）」，拒絕無實體 anchor 散文。

---

## §7. Domain Decoupling & Sovereignty Boundaries (領域知識解耦與通用標準邊界)

* **概念污染的危害**：全域共享技能（如 `loop-harness-standard` 或 `fold-in`）代表了整個系統的底層基座架構與工程紀律規範。如果將特定專案的本地業務細節（如特定的 D2 錢包介面樣式、USDT/J Point 代幣邏輯）折疊寫入全域標準，會導致全域技能迅速退化、膨脹，並使其他無關子專案的小迴圈產生嚴重的上下文噪音。
* **解耦與分層原則**：
  - **全域/共享技能**：僅保留「技術等價的結構性規範」（例如：規定所有小迴圈執行時必須強制執行其編譯與 UI 實機驗證流程）。
  - **沙盒/特化技能**：具體專案的領域知識（Domain Knowledge）、業務規格、API 欄位、UI 佈局樣式，必須完全移出全域標準，並折疊寫入該子專案沙盒內部的 `modules/`（如 `d2-wallet-history-parity.md`）或特化 Skill 中。
* **判定與路由決策**：在定 Owner 時，如果踩坑經驗帶有強烈的業務關聯，優先將其導流至該業務專屬沙盒的 Gotchas 或 Invariants 檔案，保持全域 Harness 架構的純淨泛用。
* **大小迴圈四層分層架構分流方法論 (4-Layer Hierarchy Separation Methodology)**：於 2026-07-14 進行 BNS 實體真機測試自癒實戰與重構中，我們確立並落地了「四層分層架構」，以維護大迴圈全域標準之純潔性並實行領域知識的完全解耦與歸位：
  1. **第一層：全域標準大迴圈（Harness Standard - Layer 1，如 `loop-harness-standard` / `fold-in`）**：僅限收錄「100% 通用之工程技術與架構方法論」（例如：自癒引擎執行超時自癒、快取 skip-build 失效檢測、靜態 regex grep 與運行時實機驗證之主次防線分工等抽象模式）。嚴禁寫入任何與特定自動測試工具（如 Maestro/WDA）、特定平台/真機/模擬器日誌除錯（如 UDP 日誌捕捉、Port 殘留佔用與 cleanups）或專案業務領域知識。
  2. **第二層：領域特化整合大迴圈（Domain Integration & Testing - Layer 2，如 `subproject-ixsecurity-e2e`）**：收錄專案/領域層級的通用自動測試與環境除錯技術（例如：UDP 監聽器與無緩衝落盤捕捉、背景 Port 爭用佔用與進程清理自癒、實機與主機的私網網段連線落差與代理隧道、WKWebView 動態 HTML 文字對 WDA 不透明之 native UILabel bypass 機制）。
  3. **第三層：子專案/小迴圈特化技能（Specialized Skills - Layer 3，如 `.agents/skills/` 下的 `ios-simulator-automation`、`ios-realdevice-automation` 等）**：各子專案或小迴圈專屬且需要獨立建檔之特化技能，存放該小迴圈專屬之平台與工程 Gotchas、不變量與輔助腳本，不與全域標準混合。
  4. **第四層：特化沙盒小迴圈配置（Sandbox Configurations & Ledgers - Layer 4，如 `loop_wiki/[sandbox]/AGENTS.md`）**：各沙盒當地的 `AGENTS.md` 或本機 `verify.sh` / 測試腳本，收錄具體頁面 UI 元件、特定 Mock 域名與 Egypt 端口、Nile 鏈上等待、PostgreSQL Int4 溢出限制、APNs 憑證注入 plist 等特化業務/參數踩坑。



---

## §8. /command 薄 router 作為 skill 的 slash landing 層（ix-agy 混合環境）

§5 的映射表把 `.claude/commands` 列為 northstar → antigravity port 時「拿掉」的基座——那是**純 Antigravity 環境**的判斷，作為歷史 case study 保留不動。但 **ix-agy 是混合環境：Antigravity `.agents/skills/` 慣例 ＋ Claude Code 驅動**。在此，`.claude/commands/<name>.md` 薄 router 與 `.agents/skills/<name>/` **並存**，command 作為 skill 的 slash 調用 landing 層（`/fold-in`、`/ship-testflight`、`/author-skill` 皆實體存在於 `/Users/neon/ix-agy/.claude/commands/`）。故「port 時一律刪 .claude/commands」的舊斷言在 ix-agy 不適用。

**薄 router 三律**（違反即造引擎重複／雙圖漂移）：
1. **讀 skill 當 SSOT**：command body 用 `Read <skill 的 SKILL.md／module 絕對路徑>` 把 skill 讀進來執行，別憑記憶。
2. **不複述**：command 內絕不展開／抄寫 skill 的紀律內容（抄＝雙圖，漂移時真相在 skill）。
3. **零新引擎**：能力全在既有 skill 層，command 只轉發。

**格式**：frontmatter `name` ＋ `description` ＋ `argument-hint`（Claude Code slash 選單靠它發現）；`$ARGUMENTS` 取參；描述**禁 ASCII `": "`**（同 skill frontmatter 的 YAML 靜默跳過陷阱）。

**反-husk 錨（方法論類 fold 的鐵律，承 §6）**：command 的轉發指針（Read 的路徑）**必須指向物理存在的真實檔**——建後驗證 `test -f <SKILL.md／module>` 存在且 frontmatter YAML 可解析，否則死指針＝husk。實體錨＝`/Users/neon/ix-agy/.claude/commands/{fold-in,ship-testflight,author-skill}.md`（三支，frontmatter 已驗、指針指真實檔）。

---

## §9. D2 Resolved 雙圖收斂 Case（2026-07-10，引 00:F-13/F-17）
→ `docs/plans/2026-07-10-d2-review-hardening/00-intent-and-knowhow.md`

## §10. 大小迴圈自動化測試模組化經驗 fold Case（2026-07-11，引 00 WP-1..4 + F-28 + 三遺留）
06 D2 review-hardening bundle 經驗按本 skill 7 步程序 fold 進三 owner（分流嚴守 §7 防領域污染——泛用歸全域標準、iOS 領域歸特化 skill）：
- **泛用迴圈教訓**（agy `--print-timeout` 孿生鐵律／source-grep 靜態層系統性盲點→runtime backstop／skip-build 陷阱）→ [`loop-harness-standard`](../../loop-harness-standard/SKILL.md) 不變量 1/8 加註 + Gotcha + [`modules/resolved-harness.md`](../../loop-harness-standard/modules/resolved-harness.md)（查重更新既有 timeout 條非另立副本）；反-husk 錨＝`d2_e2e_loop/.agents/skills/d2-e2e-loop/tests/Harness/verify_harness_agy_invocation`。
- **iOS 領域方法論**（idb/simctl/OOBE/權限彈窗/螢幕校驗 + agy+Claude Code 執行）→ 委派 antigravity-skill-authoring 判定後**立新特化 skill** [`ios-simulator-automation`](../../ios-simulator-automation/SKILL.md)（判為 iOS 三支柱之一，非 fold 進 subproject-ixsecurity-e2e 以免污染其領域整合器定位）。
- **設計/實作差異 + 效益疊加 + 前瞻優化分析** → [`antigravity-harness-wiki/modules/loop-modularization-benefit-map.md`](../../antigravity-harness-wiki/modules/loop-modularization-benefit-map.md)（wiki 全景組件卡加 Driver 層指針同步）。
→ 源事實帳本 `docs/plans/2026-07-10-d2-review-hardening/00-intent-and-knowhow.md`。
