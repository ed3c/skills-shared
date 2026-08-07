# 方法論：「codebase 完全掌握」可複用配方 (Codebase Mastery Recipe)

> 屬 [`repo-agent-native`](../SKILL.md)。Layer B know-why。**這是 northstar `repo-agent-native/modules/codebase-mastery-methodology.md` 的 antigravity retarget**——配方(4 步 ＋ 8 probe ＋ evaluator-first ＋ RIP 封頂)一對一映；北極星專屬基座(serena／hybrid_retrieve／hallucination_audit／knowledge-intake-hub 9-Stage／sandcastle worked-example／PG 編號)換成 antigravity 對應物或拿掉(見 [`retarget-map.md`](retarget-map.md))。配套提示詞 → [`specs-as-code-prompt.md`](specs-as-code-prompt.md)；入口 command → `/specs-as-code`。

> **適用對象**：要對一個**可讀的 repo**(源碼可 clone、可 grep)建立「完全掌握」型知識庫。
> **核心命題**：對可讀 repo，**SOURCE 是 SSOT，DR 只是補外部缺口的支流**；把 DR 當主幹去「研究」一個能直接讀的 codebase ＝ **漏斗倒置**(funnel inversion)，既貴又會吞掉 README 行銷語當事實。

---

## 0. 為什麼 DR-as-primary 是漏斗倒置 (the funnel inversion)

功能漏斗鐵律：**最便宜、最確定的 Tier 起**。對一個能 clone 的 repo：

| Tier | 工具(antigravity 實base) | 對「掌握一個可讀 repo」的角色 | 成本／確定性 |
|------|--------------------------|------------------------------|--------------|
| **Tier 0** | clone ＋ Glob／ripgrep／Read 源碼 | **SSOT**——每條事實附 `file:line`，可逐字複驗 | 0 token、最高確定性 |
| Tier 1 | `grepai_search`／`grepai_trace_*`(`.grepai` live) | 在已 clone 的源碼上做符號／語義／call-graph 導航 | 低、高 |
| Tier 3 | `gemini-conversation-research` 多 DR | **只補外部缺口**(生態譜系、上游契約、跨 repo 對比) | 高、method-dependent(post-cutoff 須 external-verify) |

**倒置的代價**：
- DR／README 只給**宣稱層**——真正的 gotcha(host-side 行為、平台條件 no-op、確定性 vs agent-judged 邊界)只能從源碼 ＋ CHANGELOG 浮現，**永不在 README**。
- DR-as-primary 會把「合理但錯誤的推測」寫進知識庫；只有回源碼逐 `file:line` 驗才會**推翻**它(最高價值點)。
- 把確定性編排器誤讀成 agentic 自評迴圈：DR 看不出「gate 是 exit-code 還是 LLM judge」，源碼一眼定生死。

> **判據(何時可反過來用 DR 當主幹)**：repo **不可讀**時——閉源、只有 SDK、runtime-only 黑盒行為、或要的是「這東西在生態裡的位置／上游 wire protocol」而非「它自己怎麼寫」。此時 SOURCE Tier 0 無料可吃，DR 才升主幹(並仍須 external-verify)。**可讀 repo 用 DR 當主幹 ＝ 反模式。**

---

## 1. 配方四步 (the four-step recipe)

### Step 1 — SOURCE ＝ SSOT 漏斗：先 clone、先讀源碼，確認 canonical repo
1. **確認 canonical repo**：npm `repository` 欄／`package.json`／README 連結對齊(版本錨在 `package.json`)。別對 fork／鏡像／過時 tag 讀。
2. **clone 到中性工作區**(如 `<OUT>/src/<slug>`；全歷史，never `--depth 1`)，所有後續 `file:line` 都指這裡。
3. **Tier 0 起**：`package.json`(stack／entry／deps 性質)→ entry barrel(`index.ts`／`bin`)→ 核心 façade → seam → provider。**禁跳層**到語義檢索之前先把骨架讀出來。第三方 target 要跑 `grepai` 前先對 target 目錄建索引(antigravity 主 `.grepai/` 只索引自身源)。
4. **每條進 KB 的事實必附 `source_ref`(path ＋ line)**。不能附 line 的(外部生態、上游假定)標 **⚠ 需人工二次確認**——誠實邊界，非失敗。

### Step 2 — 通用 IMPLICIT-DESIGN PROBE checklist(把靜態 catalog 變成真掌握)
> 配方的**靈魂**。naive 三檔模板(architecture／data-flow／security 問 SQLi/XSS/N+1)只抓 API 表面 ＋ 漏洞清單，**系統性漏掉隱含設計決策**。下面 8 條 probe 是**通用**的，對任何 codebase 都把「長得像讀過」逼成「真的掌握合約」。

| # | Probe | 問句(對源碼提問 ＋ 回證偽) |
|---|-------|------------------------------|
| 1 | **Seam(接縫)** | 哪些是可抽換的擴展點？dispatch on 什麼(tag? name? 型別?)？新增後端要不要碰 core？ |
| 2 | **Determinism boundary(確定性邊界)** | 每個 gate／判定是 exit-code／字串掃描(確定性)還是 LLM-judge／heuristic？畫出確定性 vs agent-judged 的線。 |
| 3 | **Platform conditional(平台條件碼)** | grep `platform`／`win32`／`darwin`／`process.platform`：哪些行為依平台分叉？no-op 是 bug 還是「正確地什麼都不做」？ |
| 4 | **Bounded loop(有界迴圈)** | 迴圈上限／終止信號／timeout 的**預設值**是什麼？引擎內建還是呼叫端組合？ |
| 5 | **Trust boundary(信任邊界)** | 哪些輸入不可信？信任邊界劃在哪(容器? 進程? host?)？哪個開關會讓邊界塌陷？ |
| 6 | **Ergonomics(人因／DX 合約)** | 有沒有「方便但危險」的語法糖？它同時是 DX 合約也是攻擊面嗎？偽造防禦擋得住嗎？ |
| 7 | **Typed errors(型別化錯誤)** | 錯誤是 typed 還是裸 throw？error channel 怎麼設計？失敗時丟不丟副作用／上下文？ |
| 8 | **Framework idiom(框架慣用法)** | 整棧建在哪個框架慣用法上(DI? Layer? Actor?)？load-bearing 還是裝飾？用硬數據釘住(如 grep 某 idiom 排 test 剛好 N 個)。 |

**probe 為何系統性贏**：8 條共同根因 ＝ **隱含設計決策／宣稱 vs 實測落差／跨平台條件分支／確定性邊界**。這些**不在任何漏洞清單，也不在任何 API 表面**，只能由「對設計意圖提問 ＋ 回源碼證偽」觸及。關鍵手法：**把 brief／README 假設當待證命題，回源碼逐 `file:line` 證偽**(推翻 brief 即最高回報)。

### Step 3 — 多 DR 只對「真外部缺口」(multi-DR for genuine external gaps ONLY)
Step 1+2 跑完後，剩下的 ⚠ 待確認項若是**外部**的(生態譜系／上游契約／跨 repo 對比)才升 Tier 3。**路徑(複用既有治理，禁造新引擎)**：
1. **`gemini-conversation-research` 迭代多 DR**：S7 gap(源碼 dimension × DR 覆蓋，過濾 CRITICAL/HIGH uncovered)→ S8 multi-DR(gap 合併、跑額外 DR、回 S7 重算 coverage，收斂上限 3 輪)→ 直到知識點覆蓋。
   - **post-cutoff(2026) 框架／能力／perf claim 必過 `external-verify`**(非 LLM 訓練知識 ＝ 幻覺源)；事後逐條查 claim 真假走 bibliography-anchored `stealth_fetch`(錨定 source 自己的 bibliography ＋ 引用源，**禁盲搜 WebSearch**——盲搜在 post-cutoff 會 confabulate)。
   - ⚠ Gemini DR `.md` 常把公式／數字渲染成 base64 PNG(`![][imageN]`)，純文本 coverage 比對會**假 100%**；比對前先解碼(`gemini-deep-research-extract` 已處理保真)。
2. **多 DR 合併成單一 KG**：把多份 DR 經 antigravity **`indexing/` 匯入管線**(`ingest_repodoc_cli`／`ingest_conversation`)落成 KG 節點。**紀律(非機器閘)**：每份 DR 先抽 STATED core thesis(same-problem ＋ solution-difference)；只列周邊方法的 DR 過不了「thesis 覆蓋」門檻。跑 INDEPENDENT adversarial frontier pass 找漏掉的 branch，loop-until-dry；**禁 breadth-count**(數量 ＝ placebo)。

> **守住紅線**：DR 是支流不是主幹。對可讀 repo，若 Step 1+2 已把 answer-key 覆滿就**不該**為了「完整」去 mass-research(＝ supply-push catalog 墳場)。多 DR 是 demand-pull 的：只為一個具名的外部缺口拉。

### Step 4 — EVALUATOR-FIRST 驗證：對 answer-key 計分 ＋ 迭代提示詞
> **driver 前先有 evaluator**。先有「對不對」的硬尺，才知道提示詞要不要再 harden。
1. **建 answer-key**：用**既有吸收**(prior DR／repo-wiki-converge 輸出)或一份 held-out fact set 當答案鑰匙。
2. **逐條判 `yes/partial/no`**，證據**必須來自 KB 本身**(`file:line`)——防自洽幻覺。
3. **load-bearing 條目回源碼複驗**(KB 說對 ≠ 自洽，要對 clone 源逐字核)。
4. **算 coverage_pct** ＋ 標 MISSES ＋ beyond-key surfaced。
5. **迭代提示詞**：哪條 answer-key 被漏 → 對映到 Step 2 哪條 probe 不夠硬 → 補進 file spec → 重跑。**fresh-context 稽核**(非作者跑 evaluator，避免自我背書)。
6. **收斂判據**：answer-key 全 `yes` ＋ KB 在 beyond-key 處有 surface ＋ 每條 load-bearing 回源碼複驗屬實。**收斂由人接受(engine-locus：WHAT 是人 LAND-DECISION，禁 auto-DECISION 自動接受 KB)。**

### Step 4.5 — RIP 封頂：behavioral／runtime claim 只能真跑定案
> **evaluator-first 對_靜態_事實(結構／設計合約／型別)有效；對 _runtime 行為_(某操作在某平台是否可用、perf 數字、是否真隔離)不夠**——**源碼讀 ＋ 窄 probe 都會 over-reach**。

北極星實證(sandcastle merge-back)：(a) 源碼讀證 prior 歸因錯 → (b) 窄 probe 據此推「merge-back works on macOS」**並 committed** → (c) 但完整 `run()` RIP 才證 macOS @0.10.0 **reproduced-broken**(worktree-id mismatch，零 commit)→ 推翻 (b)。

**鐵律**：任何 behavioral／perf claim 進 KB 前，跑一次**完整 RIP**(真跑該操作的端到端路徑，不是窄 probe)定案。**Evidence A 僅當 runtime 真跑過該完整路徑；源碼推論／窄 probe 最高 B**(且必標「未 RIP」)。RIP 載具 ＝ 目標 repo 自己的 run／test 路徑。

---

## 2. 一句話精華
對**可讀** repo，**SOURCE 漏斗(Tier 0 源碼＝SSOT)＋ 通用 implicit-design probe(8 條)** 就能重發現 README-level 吸收的全部 answer-key 並超越它；**DR 只補真外部缺口**(多 DR → `indexing/` 合一)，**evaluator-first 對 answer-key 計分並回頭硬化提示詞**，**behavioral claim 完整 RIP 定案**。把 DR 當主幹去研究一個能直接讀的 codebase ＝ 漏斗倒置，貴且吞行銷語當事實。

---

## 與 repo-wiki-converge 的邊界(勿混)
兩者都對可讀 repo 產 source-grounded 理解物，但：
- **repo-wiki-converge** ＝ **Gemini 作者 × Opus 判官 judge-loop** → 廣度**理解 wiki**(macro 架構散文，judge 認證收斂)。問「這 repo 是什麼、怎麼運作」。
- **specs-as-code(本配方)** ＝ repo-agent-native 的 **8-probe ＋ evaluator-first answer-key mastery** → `.knowledge_base/` 三檔**正式規格**，focus 在 wiki／漏洞清單**系統性漏掉的隱含設計合約**(seam／determinism／platform／typed-errors…)。問「這 repo 的隱含設計合約精確是什麼，每條回 file:line 證偽並過 answer-key」。
- 引擎不同(Gemini-author vs Claude-agent probe-driven)、focus 不同(廣度理解 vs 隱含合約掌握 ＋ 可量測覆蓋)。specs-as-code 是 repo-agent-native 抽取棧的**掌握＋規格頂點**，非與 repo-wiki-converge 競爭的第二個 wiki。

---

## Sources / Lineage
- northstar 源：`/Users/neon/northstar/.claude/skills/repo-agent-native/modules/codebase-mastery-methodology.md`(fold cc-20260624，實證錨 ＝ `sandboxes/sandcastle-orchestration/.knowledge_base/00-validation-scorecard.md`，9/9 answer-key 覆蓋 ＋ 3 處更正 README 吸收)。**該 sandcastle worked-example 是 northstar 專屬產物，antigravity 尚無**——首個 antigravity `/specs-as-code` run 產出即為本地 worked-example。
- 活基座：`grepai`、`gemini-conversation-research`、`external-verify`、`gemini-deep-research-extract`(base64 解碼)、`indexing/`(DR 合併)。
