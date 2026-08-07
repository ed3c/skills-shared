# Module: html-for-decisions — know-why ＋ northstar retarget 映射

> 屬 [`html-for-decisions`](../SKILL.md)。SKILL.md 有確定性程序＋不變量；本檔＝為何這樣、lineage、viz-sync/solo-pipeline 逐機制映射。

## 1. C04 三受眾媒介矩陣（為何 HTML 只給決策節點）

| 受眾 | 媒介 | 資訊特徵 | antigravity 落點 |
|---|---|---|---|
| 代理自身 | Markdown for itself | 帳本/計劃步驟/implementation-notes | slice 檔、loop-ledger、trajectories digest |
| 人類協作者 | Markdown for you | 表格/代碼塊，快速掃描 | slice 文件、勘察報告、失敗模式表 |
| 關鍵決策節點 | **HTML for decisions** | 富交互＋quiz，高決策密度 | 決策儀表板、畢業 quiz、LAND-DECISION 佇列 |

**HTML 稅**：HTML 產出/維護成本高於 Markdown 一個量級。只有「等人裁」的節點，決策密度才值回這個稅——過程報告用 HTML＝把稅付在沒有決策的地方。這是判準不是偏好：頁面目的是「裁」→ HTML；是「讀」→ Markdown。

## 2. 為何 md＝源、HTML＝投影（Markdown-as-Code 自反）

C03 卡的核心形＝「markdown 檔是系統源代碼、其餘皆生成物」。決策面套用同形：判定/裁決的 SSOT 永遠在計劃 md（如 00 已鎖決策），HTML 是事件式重生的投影。反向（在 HTML 側改判定）＝製造會漂的第二真相——與 antigravity-harness-wiki「只指針不抄」防的是同一種雙圖漂移。頁面自帶「非 SSOT」宣告＋快照日期＝投影的誠實標記。

**dogfood 錨（2026-07-09）**：loop-harness-panorama 儀表板 v0 產出 → 人裁 5 項 → 裁決先回填 00（D10/D11/§7）→ 再改 HTML 佇列狀態為 v0.1。順序正確走過一輪＝本 skill 的「吸收成立」錨（方法論類 fold 的反-husk 錨＝指向的 SSOT 是真檔案：00 檔、reference 範例、slice 10 皆真在 disk）。

## 3. quiz 閘（C07/P2）為何綁在決策面上

quiz 測「人」的理解就緒度——merge/admit 前全對才過，強制人腦留在知識環內（unknown-discovery-composer U3 的人理解半）。放進決策面而非獨立文件，是因為兩者服務同一個節點：裁決需要理解，理解閘與裁決佇列同頁＝一次交互完成。題庫對準載荷最重的判定（完成率來源、快取命門、判官分頻），形式題＝假閘。

## 4. northstar → antigravity retarget 映射表

| northstar 機制 | antigravity 對應 | 為何這樣映／拿掉了什麼 |
|---|---|---|
| `viz-sync`：live-draw-mcp daemon（chokidar watch＋ajv＋WebSocket viz.patch）雙向運行時同步 | **拿掉**——事件式重生投影（人裁落定才重生），無 daemon | antigravity 無 live-draw-mcp 基座；決策面的節奏是「裁決事件」（小時/天級）非「運行時拖拽」（毫秒級），daemon＝為不存在的頻率付基建稅 |
| `viz-sync`：拖拽 writeback 原子寫回 viz-state.json＋suppressWatch 防環 | **拿掉**——人的回饋走對話，裁決回填 md SSOT 由 agent 做 | 寫回目標不同：viz-state 是渲染狀態；我們的「狀態」是判定/裁決，其寫回必過人閘語義（先 md 後 HTML），不可自動 |
| `viz-sync`：零 token（LLM 只 Edit json 欄位，不輸出渲染碼） | **借精神、換形**——重生時只改資料段不重寫骨架（Edit 局部），骨架穩定 | 我們必須產 HTML 本體（無 daemon 代渲染）；token 節約靠「骨架複用＋局部 Edit」而非資料/渲染分離基建 |
| `solo-pipeline`：agent 親寫 plan-review.html（「HTML 是 agent 的輸出，無轉換器」） | **借用（核心哲學）** | 同判斷：不引入 md→HTML 轉換器工具鏈，agent 直接寫自包含 HTML——轉換器＝多一個會漂的中間層 |
| `solo-pipeline`：lavish-axi long-poll 標註 session（text-range annotation＋queued prompts） | **拿掉**——回饋通道＝對話＋md 回填 | antigravity 無 lavish-axi；且本 skill 的回饋粒度是「裁決項」非「文字範圍標註」 |
| `solo-pipeline`：**approve＝human-only**（agent 永不對自己的 plan 發 approve、poll timeout ≠ 通過） | **原樣採納**（不變量 4） | 與 LAND-DECISION 永遠人同源；跨平台不變 |
| `solo-pipeline`：fail-loud 前置（缺 node/npx → 顯式錯誤＋人讀 markdown，禁降級偽 session） | **借形**——Artifact 被 hook 擋 → 顯式改走 `open` fallback 並記錄，禁靜默假裝已發佈 | 同一條「前置不滿足禁偽完成」紀律；我們的前置是發佈通道非 node |
| `solo-pipeline`：C2 DCI `` !`cmd` `` runtime 狀態注入 | **拿掉** | Antigravity `.agents/skills` 無 DCI preprocessor 基座 |
| viz-sync `pg/PG-VIZ-*` skill-local 問題圖譜 | **拿掉**（暫）——坑記 SKILL.md Gotchas | antigravity PG 基座尚未落地（計劃 09 I4-I6 已判採納但未執行）；落地後本 skill 的 Gotchas 可 formalize 為 `pg/` 條目 |
| live-draw-mcp **mf-adapter**（read-only observability 路徑，與 viz-adapter 語義隔離 D3、永不混用同一份 state） | **借形＝觀測面 `scripts/context_trace.py`**：session JSONL→HTML 機械投影（零 LLM），與決策面隔離（SKILL 不變量 7） | 隔離判準原樣平移：觀測資料（機器帳）與判定資料（語義流）混同一面＝互相污染。差異：mf-adapter 讀 `MEGA_FLOW.ast.json` 且掛 daemon；我們讀 Claude Code transcript、一次性渲染無 daemon（事件節奏不同，同 viz-sync 列的判斷） |

**拿掉≠簡化**：viz-sync 的 daemon/writeback 在 northstar 是活的（有 live-draw-mcp）；這裡沒有基座，保留＝引用跑不動的東西＝死 husk（與 fold-in know-why §5 同判準）。

## 5. 與計劃 slice 10 的分工（防雙圖）

`docs/plans/2026-07-09-loop-harness-panorama/10-media-and-boundary.md` 是 plan-scoped 判定（M1-M4：媒介層要注入 02 spec 什麼、judge-loop-chooser 邊界裁決）；**本 skill 是媒介操作規則的 durable home**。10 的 M2（再生規則）操作細節以本 skill 為準，slice 指針過來不重述；02 spec 注入時同樣指針本 skill。

## Sources / Lineage
- 06 §A C03（Markdown-as-Code）/C04（媒介決策密度矩陣）——卡片庫 verbatim SSOT。
- northstar：`.claude/skills/viz-sync/skill.md`、`sandboxes/solo-pipeline/SKILL.md`（2026-07-09 唯讀快照；活 repo 會漂，引用時回讀）。
- dogfood：`reference/loop-panorama-decisions.html`（v0.1）＋人裁回填記錄（00 D10/D11）。
