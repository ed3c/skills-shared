---
name: html-for-decisions
description: |
  在 LAND-DECISION（人閘）節點產出/更新自包含 HTML 決策面（決策儀表板＋理解 quiz）時使用 —
  C04 媒介矩陣第 03 階的操作 SSOT：markdown＝源、HTML＝可再生投影、quiz 全對才 admit、
  approve 永遠人。何時用 HTML 何時用 Markdown（防 HTML 稅）、產出結構、調色盤驗證、
  hook 擋 Artifact 的交付 fallback、人裁後回填與事件式重生。
  觸發詞：決策儀表板、HTML for decisions、人閘視覺化、決策密度、plan dashboard、quiz 閘。
  know-why＋northstar（viz-sync／solo-pipeline）retarget 映射在 modules/media-know-why.md。
---

# Skill: html-for-decisions — LAND-DECISION 節點的 HTML 決策面

> **Role**：C04 三受眾媒介矩陣（代理自身=Markdown for itself／人類協作者=Markdown for you／決策節點=HTML for decisions）中**第 03 階的操作 SSOT**。只管「怎麼產、怎麼驗、怎麼更新」；哪個節點算 LAND-DECISION 由計劃/迴圈自己的人閘定義。
> **結構**：SKILL.md＝確定性程序＋不變量；為何這樣設計、northstar viz-sync／solo-pipeline 借了什麼拿掉什麼 → [modules/media-know-why.md](modules/media-know-why.md)。
> **範例（真實案例非模板）**：[reference/loop-panorama-decisions.html](reference/loop-panorama-decisions.html)——loop-harness-panorama 計劃的 v0.1 決策儀表板（2026-07-09 dogfood：v0 產出→人裁 5 項→回填重生一輪真跑）。
> **Lineage**：06 §A C03/C04 卡＋計劃 slice `docs/plans/2026-07-09-loop-harness-panorama/10-media-and-boundary.md`（plan-scoped 判定 M1-M4；durable 操作規則在本 skill，該 slice 指針過來不重述）。

## When to Use
- 一個計劃/迴圈走到**人閘節點**（多項裁決、跨 slice 張力、開跑閘），要把已知/未知、判定帳本、決策佇列做成高決策密度的 HTML 給人裁。
- 人裁完落定，要**回填並重生**既有決策面。
- merge/畢業前要出**理解 quiz**（C07/P2：全對才 admit）。
- 要看 **session 底層**（逐 turn token 經濟／cache 命中／工具軌跡／D7 oracle）→ 走**觀測面** `scripts/context_trace.py`（零 LLM 機械投影，與決策面語義隔離，見不變量 7）。

## Not For
- ❌ 過程性報告/進度更新 → Markdown（HTML 只給決策節點——防 HTML 稅）。
- ❌ 運行時雙向狀態同步視覺化（daemon＋watch＋拖拽寫回）→ 那是 northstar `viz-sync` 的 live-draw-mcp 基座，antigravity 無此基座，**誠實不做**（見 modules retarget 表）。
- ❌ 標註式 plan-review long-poll session → 那是 northstar `solo-pipeline` 的 lavish-axi 基座；antigravity 回饋通道＝對話＋md 回填。
- ❌ 產物該用哪個驗證標準/tier → [judge-loop-chooser](../judge-loop-chooser/SKILL.md)。
- ❌ 圖表設計細節 → 全局 `dataviz` skill（本 skill 只固定「必跑 validator」這一步）。

## 不變量（違反即停）
1. **HTML 只給 LAND-DECISION 節點**；過程產物一律 Markdown。判準：這頁存在的目的是「等人裁」，不是「給人讀進度」。
2. **markdown＝源、HTML＝投影**：頁面必帶「本頁為投影非 SSOT」宣告＋快照日期；**禁在 HTML 側改判定內容不回寫 md**（回寫順序：先改 md SSOT → 再重生 HTML 同路徑覆蓋）。
3. **自包含**：零外部請求（inline CSS/JS、無 CDN）；CJK 用系統字型堆疊（**別**把 CJK 字型 data-URI 內嵌——體積不可行）。
4. **quiz 全對才 admit；approve 永遠人**：agent 永不對自己的產出發 approve、永不把「沒回饋」視同通過（solo-pipeline §2.5 同款紀律）。
5. **語意真相標態**：預判／已 admit／已鎖 分開標，預判不冒充定案；狀態變更只來自 md SSOT 的人裁記錄。
6. **狀態色過 validator**：`node <dataviz-skill>/scripts/validate_palette.js "<hex,...>" --mode light`——注意**分段相鄰順序**影響 CVD 判定（實測：紫緊鄰藍 FAIL，重排分段序即 PASS）。
7. **決策面與觀測面語義隔離**（northstar viz-adapter／mf-adapter 同款 D3 先例）：決策面＝LLM 從 md 萃取判定（有 quiz、有人閘語義）；觀測面＝腳本從 session JSONL 機械投影（**零 LLM、無 quiz、無判定**）。**永不混同一頁、永不共用 schema**——把觀測數據塞進決策面＝用機器帳偽裝判定，反之＝給觀測報表掛假人閘。

## 確定性程序
1. **判節點**：不是人閘節點 → 出 Markdown，停。
2. **萃取**：從計劃/迴圈的 md SSOT 收集——決策佇列（每項：裁什麼/選項/出處 slice）、判定分佈、已知/未知象限、待驗命門。**只投影不新增判定**。
3. **產出**：用 [prompts/decision-report.prompt.md](prompts/decision-report.prompt.md)（schema v1：S0-S10 section 物理邊界＋槽位表＋固定狀態色 tokens＋checker 自驗迴圈）——親寫或交執行 LLM（Sonnet 級即可，代入 `{{PLAN_DIR}}`/`{{SNAPSHOT_DATE}}`/`{{OUTPUT_PATH}}`）。骨架照 reference 範例複用、**判定資料一字不留**；「必」槽缺料顯式 N/A 禁靜默省略。
4. **驗證（T0 機械）**：`python3 <本skill>/scripts/check_decision_html.py <file>`——五檢查（投影宣告/快照日期/自包含/quiz 閘/title）exit 0 全過、2 任一 FAIL（首次用或改 checker 先跑 `--selftest` 正控）；狀態色過 dataviz validator（不變量 6）；`open <file>` 本地目檢一次（label 碰撞/溢出——validator 不管版面）。
5. **交付**：Artifact 發佈可能被 hook 白名單擋（live 實測 2026-07-09）→ fallback：`open <file>` 直接開本地檔。檔位：計劃期放計劃目錄或 session scratchpad；要跨 session 存活放計劃目錄（投影可再生，預設不入 git，人裁）。
6. **人裁後回填**：人的裁決先寫進 md SSOT（如 00 已鎖決策/§7 人閘）→ 依 md 重生 HTML（同路徑覆蓋＋快照標記 vN）。
7. **更新觸發**＝事件式（人閘裁決落定/判定表變動/總閘狀態變化），**非定期重生**；頻率低於價值時降級為里程碑式（每 slice 收口一次），人裁並記 implementation-notes。

## Gotchas
- **Artifact 被 PreToolUse hook 擋**（`auto-approve.sh` 白名單，實測）：別重試原樣調用；直接走本地 `open` fallback，或人把 Artifact 加白名單後再發佈。
- **quiz 題庫隨載荷更新**：題目對準「載荷最重的判定」（完成率來源/快取 gotcha/判官分頻這類），不是形式題；出不出得了好題本身就是理解訊號。
- **範例檔是真實案例**：reference/ 那份帶著 loop-harness-panorama 的真判定與人裁記錄——複用時取其**骨架與不變量落法**，資料層全換。
- **分段順序即 CVD 命門**：堆疊條的相鄰段決定 validator 過不過；語義順序（採納→借形→待裁→僅記錄→husk）恰好也是 CVD-safe 序，別隨手重排。

## Modules / Reference / Scripts
- [modules/media-know-why.md](modules/media-know-why.md) — C04 三受眾矩陣、為何 md=源/HTML=投影、HTML 稅、northstar `viz-sync`／`solo-pipeline` retarget 映射表（借什麼/拿掉什麼/為何不是簡化）。
- [reference/loop-panorama-decisions.html](reference/loop-panorama-decisions.html) — **決策面**真實範例 v0.1（dogfood 過一輪人裁回填；同時是 checker 的正控 good fixture）。
- [reference/context-trace-example.html](reference/context-trace-example.html) — **觀測面**真實範例（2026-07-09 本計劃 session 的 `context_trace.py` 輸出：82 calls／202k out／命中 98.1%）。**它是輸出樣品非模板**——任何 session 一行命令重生同構報告，schema 的物理邊界在腳本代碼裡，不需 prompt 契約；schema 演化＝改 `render_html()`＋selftest，改後以真實 session 重生此範例。
- [prompts/decision-report.prompt.md](prompts/decision-report.prompt.md) — **生成契約（schema v1）**：S0-S10 section 物理邊界＋槽位表＋投影者鐵律（禁發明判定）＋固定色 tokens＋checker 自驗迴圈——讓不同計劃產同構報告。schema 演化＝改此檔＋同步 checker；骨架只由真實案例替換。
- [scripts/check_decision_html.py](scripts/check_decision_html.py) — 不變量 T0 機械驗證（五檢查，exit 0/2/1；`--selftest`＝good/hollow 正控鑑別，防 placebo checker）。**只驗不產**——HTML 生成走 prompt 契約由 LLM 親寫（無轉換器）；確定性生成腳本＝slice 10 M2 判的 follow-up，等真需求。
- [scripts/context_trace.py](scripts/context_trace.py) — **觀測面（零 LLM 全路徑）**：`context_trace.py <session.jsonl> [-o out.html]` 讀 Claude Code session transcript → 逐 call token 經濟（in/out/cache_read/cache_creation 5m·1h 桶）＋context 成長曲線＋**D7 oracle 判定**（cache_read>0 逐 call＋驟降事件=疑 prefix miss）＋工具調用分佈＋去重（同 message.id 串流分片）。確定性渲染器在此是對的（資料=結構化機器真相非散文 md，零幻覺、同輸入同輸出）；`--selftest`＝合成 fixture 正控。dogfood 錨：2026-07-09 本計劃 session（82 calls／202k out／cache 命中 98.1%／驟降 0）。session JSONL 位置＝`~/.claude/projects/<project-slug>/<session-id>.jsonl`。
