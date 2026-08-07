---
name: gemini-conversation-research
description: |
  研究 Gemini 對話（不是 YouTube 影片）時使用 — 給定一個 Gemini/AI Studio 對話 URL 或一個研究主題，
  把對話的隱性知識結構化、只把真缺口送 Deep Research、迭代到知識點全覆蓋。11 階段 rigid pipeline
  （S0 抽取 → S1 脈絡分析 → S1.5 同對話追問 → S2 分診 → S3 DR → S4 存檔 → S7 覆蓋比對 → S8 multi-DR → S9 落地）
  ＋ 雙模式（Mode A URL 抽取 / Mode B 主動 Context-QA）。DR 投遞與抽取複用 antigravity 既有引擎，不重造。
  觸發詞：研究這個 Gemini 對話、分析 Gemini 對話脈絡、用 Gemini 研究某主題、Gemini DR、對話知識全覆蓋、
  exhaustive extraction、對話知識萃取。
---

# Skill: Gemini 對話研究管線（antigravity 版；port 自 northstar `gemini-conversation-research`）

> **Role**: 把一個 Gemini 對話（高密度認知結晶：主題脈絡 / 認知遞進 / Q&A 邏輯 / 結論框架 / 知識缺口）結構化，
>   **只把缺口送 DR**、其餘直接存檔，迭代到知識點全覆蓋。與 [dr-research-loop](../dr-research-loop/SKILL.md) **正交**——
>   那條是 YouTube 影片 → 卡片盒 → DR，本條是**既有 Gemini 對話 URL / 主動 Q&A** → 分析 → 缺口 → DR。
> **結構**: SKILL.md = 11 階段架構 + 每階段編排 know-how（1-2 行 + 指針）；逐階段 how-to / checkpoint / 子代理模板在 `modules/`。
> **SSOT / 活基座（每個都真存在，這是本 port「非 husk」的鐵錨）**:
>   - DR 投遞 + 抽取引擎 = `automate.js` 的 `runDrOnce`(256) + `ui.js` 的 `runGeminiDeepResearch`(906) / `runGeminiDeepResearchAttempt`(924) + `data.js` 的 `extractReportHtmlInBrowser`(24) / `htmlToMarkdown`(17)（cc-20260712 核實：舊引註「automate.js:1364/1383/2287/43」是 state.js／data.js／ui.js 拆分前的殘留行號，automate.js 現僅 290 行、純調度層——已修正）。**gcr 不重造 DR monitor+retry**（northstar 曾重造 = 滯後複製，實證間歇卡；見 [retarget-map §DR-reuse](modules/retarget-map.md)）。
>   - DR 報告 → 保真 Markdown = [gemini-deep-research-extract](../gemini-deep-research-extract/SKILL.md)（S3 抽取步驟就是委派它）。
>   - 反幻覺 / 外部查證 = [external-verify](../external-verify/SKILL.md)（S2 DR prompt 硬化 + 事後逐 claim 查證）。
>   - Path B 精煉 = [path-b-reduction](../path-b-reduction/SKILL.md)。
>   漂移時以 `automate.js` 程式碼為權威。
> **retarget 誠實帳本**（northstar → antigravity 拿掉了什麼、為何不是簡化）→ [modules/retarget-map.md](modules/retarget-map.md)。
>   ⚠ **別把 northstar 原檔的 KG 入庫（`kg_fast_write`）/ `dr-governance-router` / Bug Scar #NNN 編號 / `gemini-aup-guard.sh` hook / `execution/scripts/*.sh` wrapper 搬回來**——antigravity 無此基座 = 死 husk（見 [fold-in](../fold-in/SKILL.md) 反模式）。

## When to Use
- 有一個 **Gemini 對話 URL**（`gemini.google.com/app/<id>` 或 `aistudio.google.com/prompts/<id>`）要萃取知識 + 補缺口研究。
- 有一個**研究主題 + 上下文**，要**主動開新 Gemini 對話**做多輪 Q&A 再萃取（Mode B）。
- 要對一個對話做「知識點覆蓋率」比對，迭代 DR 到全覆蓋。

## Not For
- ❌ YouTube 影片 → 卡片盒 → DR 全量管線 → [dr-research-loop](../dr-research-loop/SKILL.md)（不同上游、不同閉環）。
- ❌ 只要把一份**已生成**的 DR 報告抽成保真 md → [gemini-deep-research-extract](../gemini-deep-research-extract/SKILL.md)（本 skill 的 S3 抽取就是委派它）。
- ❌ 可讀 repo 的 codebase 掌握用 DR 當主幹（漏斗倒置）——源碼 = SSOT，DR 只補外部缺口。
- ❌ 造新 skill / 改 skill 規範 → [antigravity-skill-authoring](../antigravity-skill-authoring/SKILL.md)。

## 核心原理 + 雙模式
Gemini 對話是高密度認知結晶。本 skill 把隱性知識結構化，**只把缺口送 DR**，其餘直接存檔。
- **Mode A（URL 抽取）**: 對話 URL → S0 抽取已有對話 → S1-S9。
- **Mode B（Context-QA）**: 研究主題 + 上下文 → S-1 載入 → S0-ALT 主動開新 Gemini 對話逐輪 Q&A → 併回 S1。

```
Mode A:  URL → [S0 抽取] → [S1 分析] → [S1.5 追問] → [S2 分診] → [S3 DR] → [S4 存檔]
                                                                  ↘ [S7 覆蓋比對] → [S8 multi-DR]⟲S2/S3 → [S9 落地]
Mode B:  主題+上下文 → [S-1 載入] → [S0-ALT Q&A] → (併入 S1…)
```

## 🛡 改任一階段 / prompt 前先讀全景（防誤改 SSOT）
改任一 S-stage 或任一 prompt 前，先在 [modules/loop-panorama-ssot.md](modules/loop-panorama-ssot.md) 對照：①該物歸屬哪段（別改錯地方）②會不會斷閉環 gate/loop-back ③prompt 改 canonical 原檔、禁散補 / 禁簡化。**sibling 全景**（不同管線同紀律的 worked-example）= [dr-research-loop/modules/loop-panorama-ssot.md](../dr-research-loop/modules/loop-panorama-ssot.md)——改 gcr 別去改它，反之亦然。

## AUP 內容隔離（antigravity 是**架構性天生安全**，非靠 hook）
外部對話原文（21K+）**永不進主會話 context**。antigravity 的隔離是**架構決定的**（file-based：瀏覽器抽取直接寫檔、任何 LLM 分析走子代理），**不是** northstar 的 `gemini-aup-guard.sh` marker hook——**本 repo 無此 hook，也不需要**（northstar 靠 hook 補救；antigravity 天生 file-based 就無此暴露面）。三條規則：
1. **S0/S3 抽取走瀏覽器 → 檔案**（`extractReportHtmlInBrowser` + `htmlToMarkdown` 寫 `.md`），原文不經 agent context。
2. **S1/S7/S9 分析走子代理**，只回結構化 YAML（≤5K）；主會話禁 `Read` 對話原文全文（≤50 行 spot-check 例外）。
3. ⚠ 這層是硬約束：**即使平台權限放開，外部原文跨界進主 context 仍不可約（Data Exfiltration）**——file-based 架構 mandatory。
> 完整隔離設計 + 為何 antigravity「自主只因無 guard、架構決定 autonomy 非權限」→ [modules/conversation-pipeline.md §AUP 內容隔離](modules/conversation-pipeline.md)。

## S0-S9 階段編排（逐階段 how-to → [modules/conversation-pipeline.md](modules/conversation-pipeline.md)）
| 階段 | 一句話 | 委派 / 複用 |
|------|--------|-------------|
| **S0 EXTRACT** | 抽取 Gemini/AI Studio 對話原文 → 寫檔（逐字元完整，**禁摘要/重組**，摘要是 S1 產物）；若對話內含已完成的 Deep Research 報告（`deep-research-immersive-panel`），citation/bibliography 一併保真抽出附加在 QA 之後 | **repo 根目錄** `scripts/extract-gemini-conversation.mjs`（⚠ 非 skill 目錄下同名檔，見下方 Gotcha）（CDP 連 :9333、turn HTML→md、**只印 metadata**）；LIVE ✓ |
| **S1 ANALYZE** | 子代理讀對話檔，6 步框架 → `conversation_analysis` YAML（維度 / 認知遞進 / Q&A 邏輯 / 密度 / echo-back 橫向挑戰 / vision→roadmap） | **子代理隔離** |
| **S1.5 PROBE** | knowledge_gap 維度先**同對話追問**（≤2 輪，比 DR 便宜兩數量級）；`knowledge_gap=0` 跳過 | 追問構造 → [first-principles-probe.md](modules/first-principles-probe.md) |
| **S2 TRIAGE** | 只把 research-gap 送 DR、合併最少查詢；DR prompt 過 **external-verify** 硬化，寫 `/tmp/dr-prompts/<slug>-<ts>.txt` file-only | [external-verify](../external-verify/SKILL.md) |
| **S3 DEEP** | DR 投遞 + 抽取 | **複用 `automate.js --dr-once`(runDrOnce) + [gemini-deep-research-extract](../gemini-deep-research-extract/SKILL.md)**，**不重造** |
| **S4 HARVEST** | 雙文件存檔（`.md` 完整含 bibliography / `.txt` 結構化）；回應**必給絕對路徑**（AUP 下主會話不讀全文，路徑是使用者唯一線索） | — |
| **S7 GAP** | 子代理交叉比對 S1 維度 × DR 覆蓋 → 過濾 CRITICAL/HIGH uncovered → `gap_list` | **子代理隔離** |
| **S8 MULTI-DR** | `gap_list` 合併 → 複用 S2/S3 跑額外 DR → 回 S7 重算覆蓋（**≤3 輪收斂**） | 複用 S3 引擎 |
| **S9 INGEST** | 全知識點**入 antigravity KG**：`Conversation` 節點 + `DISCUSSES→Concept`（複用 `concepts.py` 引擎）+ 真 repo `MENTIONS→Library`（帶 repo_url，JOINS 既有 lib）；跨源 join 既有 Video/RepoDoc | `indexing/ingest_conversation.py`（子代理隔離 + KG ingest）；LIVE ✓ |

> **S9 後下游落地驗證（SURFACE-gated，人 admit，非 auto-chain）**：DR 存檔 ≠ 可信 ≠ 可落地。四段定序＝**D1 DR 落地驗證**（多模型分工 + external-verify + 🔴 HTTP 確定性錨打實體存在性，別信 LLM grounding）→ **D2 架構設計合成**（真實度計分卡 + 等價物矩陣）→ **D3 可行度 gap 收斂**（unknown-discovery-composer 四象限 → repo-wiki-converge/repo-agent-native；真實作常**反證** DR 論點）→ **D4 prototype 端到端**（`kb-ingest/setup-prototype.sh`，推導→實測）。完整 how-to/血淚 → [modules/downstream-landing.md](modules/downstream-landing.md)。

## Gotchas（跑前必知）
- **DR reliability 命門 = 復用 `automate.js --dr-once`，別在本 skill 重造 monitor+retry**：northstar 實證滯後複製間歇卡 plan/submit（0/N）；同 prompt 經 `automate.js` 硬化引擎一次跑完 22.8K 字（RIP）。批次 DR 走序列 → bridge → 引擎，別加 monitor+retry（= 重造）。
- **一帳號 DR 序列、脫鉤才投下一個**：DR 槽只在 ~2-3min init 期被佔，研究脫鉤（~210s）後釋放；太早投搶槽餓死前者。**不可與 dr-research-loop 影片管線同跑同一 :9333 帳號**（跑前 `pgrep -fl automate.js` 確認無）。
- **`verifyStarted` 是假陽性**（秒級 Start 鈕消失 ≠ 會跑完）：真完成 = 字數 ≥3000 ∧ 0 計劃殘留（`开始研究`/`修改方案`/`只需要几分钟`）∧ `deep-research-source-lists`。投 DR 後 ~8min 跑 metadata-only 探針看 `hasPanel` 判「卡 plan」vs「健康」。
- **簡繁陷阱**：開始研究鈕含**簡體「开始研究」**（开≠開），matcher 須認簡繁，否則卡計劃階段。
- **DR prompt ≤~1200 字單段**：長 / 多問 → soft-decline 或 `start_button_not_found`；多問拆 **S8 multi-DR**，勿塞一個長 prompt。
- **CDP fallback**：research profile `auth_required` 且使用者拒新登入 → 連使用者既有已登入 `:9333`（`puppeteer-core.connect({browserURL:'http://127.0.0.1:9333'})`，用 antigravity 已裝的 `node_modules/puppeteer-core`）；目標對話已開分頁則零導航直讀。**turndown ESM 陷阱**：`import` 走 `.../lib/turndown.cjs.js` build（`.es.js` 內部 `require()` 會炸 ES module scope）。
- **S0 腳本同名異義陷阱（cc-20260712 實測）**：repo 根目錄 `scripts/extract-gemini-conversation.mjs`（turn-structured 多輪 QA，S0 真正使用的版本）與 `.agents/skills/gemini-conversation-research/scripts/extract-gemini-conversation.mjs`（單一最大面板抓法，only 給「已完成 DR 報告」單獨抽取用，**非**多輪對話）同名並存——相對路徑 `scripts/extract-gemini-conversation.mjs` 在 skill 目錄脈絡下會誤解析到後者。**一律用根目錄絕對路徑**；後者已加棄用註記指回根目錄版。
- **turn 選擇器重複抓取（已修，cc-20260712）**：根目錄腳本原把 `model-response` 與其巢狀子元素 `.response-container` 塞進同一個 `querySelectorAll('qSel, rSel')` OR-list，導致每個 Model 回合被抓兩次（實測：87 turns 應為 29 user+29 model=58，逐位元組重複）。已修成每個角色只用「命中的那一個」selector（`pickSel` 回傳 selector 字串而非 NodeList），非把整個 OR-list 塞進同一個 query。**禁回退**：合併多個候選 selector 到同一個 `querySelectorAll` 呼叫（巢狀元素會被 OR-list 的不同分支各命中一次）。
- **背景分頁 timer 節流 → CDP timeout（已修，cc-20260712）**：根目錄腳本原缺 `page.bringToFront()`，多個 gemini.google.com 分頁同開時，非前景分頁的 `sleep()` 被 Chrome 節流，scroll-wait 迴圈實測連續兩次撞 puppeteer `Runtime.callFunctionOn timed out`（180s protocolTimeout）。加回 `bringToFront()` 後同一對話即時成功（14 turns / 24658 chars）。**禁回退**：拿掉 `bringToFront()` 呼叫。
- **agy `-p` 對 question/辯論型 prompt silent-no-op（0 bytes）**：命令式 trivial prompt（如 `PONG`）可跑,但問句/架構辯論型 prompt 靜默產 0 bytes（根因未診斷）。**cc-20260711 擴充**：從 Claude Code **非互動 session** 內 agy 更是 5 模式全敗（accept-edits 需 TTY／PTY 包裹不完成寫檔／`--print` no-op 且**無視 `--model`**，指 Pro3.1 仍跑 Flash）→ D1 獨立第二意見同樣別靠 agy，改 GitHub API 等確定性錨。**Mode B（E 軸架構辯論）禁回退用 `agy -p` 起 Gemini,走瀏覽器 CDP `:9333`**（`scripts/extract-gemini-conversation.mjs` 同引擎）。多分頁**必用確切對話 conv-id 鎖定**,別選「最後一個匹配 gemini 分頁」——會打到使用者其他對話（實測污染風險,turn count 是查污染的鐵錨）。**cc-20260712 擴充（根因補上,非單純 0 bytes）**：`--model` 無視的實際成因是呼叫語法錯——`agy --help` 確認 `--print`/`--prompt` 是互為別名的**吃值旗標**（`Run a single prompt non-interactively and print the response`），prompt 須緊跟 `--print` 之後；`dr-research-loop` 側 `runAgyFallback` 原本寫成 `--print --model <值> <prompt>`，讓 `--model` 卡位吃掉本該給 `--print` 的值，agy 收不到提示詞、回自我介紹交差。修正語法（`--print <prompt> --model <值>`）後，簡單問句能正確回應，但**對複雜生成任務（如完整卡片盒知識架構）agy 是當 agent 執行**：真內容寫進它自己的 `~/.gemini/antigravity-cli/brain/<session-id>/*.md` scratch 檔，`--print` 的 stdout 只回一份摘要 + `file://` 連結 + 反問後續動作，並非把生成內容整份吐回來（live 實測：5413 chars 完整卡片盒 prompt → stdout 摘要僅 1253 chars，解析摘要中的 `file://` 路徑讀真檔驗證為 16533 chars 合格全文）。**這解釋了為何「命令式 trivial prompt 可跑,問句/辯論型靜默 0 bytes」的舊觀察不完整**：agy 對複雜任務不是單純靜默失敗，而是把真輸出藏進 stdout 看不到的地方——若下游程式碼直接把 `output.trim()` 當正文，會誤判為「內容過短失敗」或更糟、悄悄存下摘要當正文。**若真要用 `agy -p` 起 Gemini 處理複雜生成任務，禁回退成只看 stdout 長度判斷成敗——須解析 stdout 內 `file://` 路徑讀真檔**；但本 skill 既有結論（走瀏覽器 CDP）對 Mode B 架構辯論這類即時互動場景仍優先，agy 檔案輸出模式較適合單次批次生成（如 dr-research-loop 的卡片盒 fallback）。

## Modules
- [modules/conversation-pipeline.md](modules/conversation-pipeline.md) — S0-S9 逐階段 how-to / checkpoint / 子代理 dispatch / AUP 隔離規則（Mode A 主線）
- [modules/mode-b-contextqa.md](modules/mode-b-contextqa.md) — Mode B（S-1 CONTEXT-LOAD + S0-ALT CONTEXT-QA + 資料主權過濾 + Mode B 啟動提示）
- [modules/first-principles-probe.md](modules/first-principles-probe.md) — 追問怎麼鑽到底（引用-鑽入 + 反向自陳 + first-principles 約分，抗放水；S1.5 + Mode B R2-4）
- [modules/loop-panorama-ssot.md](modules/loop-panorama-ssot.md) — 閉環全景 + 迴圈判斷邏輯 + prompt 錨點（**改階段/prompt 前先讀**）
- [modules/retarget-map.md](modules/retarget-map.md) — northstar → antigravity retarget 映射 + 誠實拿掉了什麼
- [modules/downstream-landing.md](modules/downstream-landing.md) — **S9 後**下游落地驗證方法論（D1 DR 落地驗證→D2 架構設計→D3 gap 收斂→D4 prototype；多模型分工 + 確定性錨 + recipe-not-engine）

---
*port 自 northstar `.claude/skills/gemini-conversation-research/` v3.7.0（skill.md + 12 modules + 5 PG + playbook + evals，~2168 行）。**retarget 非原樣搬**：DR 引擎接 `automate.js`、反幻覺接 `external-verify`、Path B 接 `path-b-reduction`；KG 入庫 / dr-governance / Bug Scar 編號 / aup-guard hook / execution 腳本 **拿掉（無基座）**。完整帳本 → [modules/retarget-map.md](modules/retarget-map.md)。*
