---
id: "langchain:how-we-benchmark-deep-agents"
title: "How We Benchmark Deep Agents"
source_name: "LangChain"
source_type: "official-blog"
source_url: "https://www.langchain.com/blog/how-we-benchmark-deep-agents"
canonical_url: "https://www.langchain.com/blog/how-we-benchmark-deep-agents"
published_at: "2026-07-23"
monetization_score: 100
monetization_modes: "Agent benchmark package; Agent CI regression suite; trajectory failure taxonomy; eval engineering consulting."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["agent-evaluation", "trajectory-benchmarks"]
mapping_targets: ["code", "data", "trajectory"]
github_path: "ai-content-note/notes/agent-evaluation/2026-07-23-benchmarking-deep-agents.md"
legacy_google_doc_id: "1U3far14wAc8QBKRgnic_t1yo3EEmJAk7Jt_poE1esI4"
legacy_google_doc_url: "https://docs.google.com/document/d/1U3far14wAc8QBKRgnic_t1yo3EEmJAk7Jt_poE1esI4/edit"
citation_mapping_status: pending
---

\#\#\# N1：Agent benchmark 從答題榜變成可執行環境  
\- \*\*核心衝突\*\*：傳統 benchmark 評估單次輸出；Deep Agent 必須在多檔案、長時間、可變工具與真實副作用中完成工作。  
\- \*\*關鍵人物/實體\*\*：LangChain Deep Agents 團隊 vs 靜態 QA benchmark 與只測 final answer 的排行榜。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- 發布日期：\*\*2026-07-23\*\*。  
  \- Harbor-Index 從 \*\*超過 6,000 個任務、54 個 benchmarks\*\* 中整理出 \*\*82 個任務\*\*。  
  \- τ³ suite：\*\*30 個任務\*\*。  
  \- ContextBench：\*\*30 個任務\*\*。  
  \- Lite evaluation 約 \*\*8× faster\*\*、\*\*6× cheaper\*\*。  
  \- Deep Agents v0.7 實驗移除 todo middleware，並縮減 system prompt。  
\- \*\*劇情轉折\*\*：團隊先發現單一總分無法指出 Agent 為何失敗。於是把 benchmark 拆成 task environment、instruction、sandbox、grader、capability suite 與多次重跑。評估從「模型答對了嗎」轉成「Agent 在可重現環境中如何完成、在哪個 subsystem 崩潰」。  
\- \*\*生態背景\*\*：Agent product 的錯誤可能來自 planning、context、tool use、filesystem、browser、memory 或 harness，而非 base model 本身。  
\- \*\*連結\*\*：→ \[\[D1\]\]–\[\[D8\]\], → \[\[G1\]\], ≈ \[\[N2：分散式系統的故障注入測試\]\]

\#\#\# Q1：平均分數是否正在隱藏 Agent 的真實 Bug？  
\- \*\*核心疑問 (The Doubt)\*\*：若兩個 Agent 總分相同，一個擅長長上下文但不會恢復工具錯誤，另一個相反，單一 leaderboard 能支持產品決策嗎？  
\- \*\*現狀反差 (Reality Gap)\*\*：靜態 benchmark 提供易比較數字；production failure 卻高度依賴環境與任務軌跡。  
\- \*\*思維實驗 (Simulation)\*\*：若新版本總分增加 2%，但 browser task 的不可逆 mutation failure 翻倍，是否仍應發布？  
\- \*\*連結\*\*：← \[\[D1\]\], \[\[D5\]\], → \[\[S1\]\]

\#\#\# C1：Environment-Complete Agent Evaluation  
\- \*\*定義\*\*：評估單位不只是 prompt 與 answer，而是 instruction、container、files、services、tools、time budget、grader 與 execution trace 的完整封裝。  
\- \*\*演化\*\*：問答 dataset → tool-use benchmark → reproducible task environment。  
\- \*\*本質\*\*：Agent 是 model × harness × tools × environment × policy。任何一項未版本化，結果就不可比較。  
\- \*\*結構特徵\*\*：Dockerfile/Docker Compose、Markdown instruction、test.sh、sandbox、trace、multi-run aggregation。  
\- \*\*連結\*\*：→ \[\[D2\]\], \[\[D3\]\], \[\[E1\]\]

\#\#\# D1：Harbor 作為 benchmark runtime  
\- \*\*操作手法\*\*：用 Harbor 統一描述 agent、dataset、sandbox 與 evaluator，讓不同 Agent 在相同 task contract 下執行。  
\- \*\*獨特特徵\*\*：不是把 dataset 轉成 API call，而是啟動完整環境並收集可驗證 artifact。  
\- \*\*影子證據\*\*：文章將 Harbor 作為 Deep Agents benchmark infrastructure 的核心。  
\- \*\*連結\*\*：↔ \[\[D2\]\], ⟨S1⟩

\#\#\# D2：Task environment 的三件式封裝  
\- \*\*操作手法\*\*：每個任務至少包含 Dockerfile 或 Docker Compose、Markdown instruction、以及以 test.sh 為入口的 evaluator。  
\- \*\*獨特特徵\*\*：instruction 與 grader 分離。Agent 看得到需求，不直接看 evaluator logic。  
\- \*\*影子證據\*\*：三個檔案角色不可模糊合併。  
\- \*\*連結\*\*：↔ \[\[D1\]\], \[\[D3\]\], → \[\[P1\]\]

\#\#\# D3：Harbor-Index 的任務篩選  
\- \*\*操作手法\*\*：從 54 個 benchmarks、超過 6,000 個任務中挑選 82 個，形成可持續執行的代表性 index。  
\- \*\*獨特特徵\*\*：不是隨機縮小。目標是覆蓋 coding、research、computer use、filesystem 與長程 reasoning 等能力。  
\- \*\*影子證據\*\*：\*\*54\*\*、\*\*6,000+\*\*、\*\*82\*\* 必須原樣保留。  
\- \*\*連結\*\*：↔ \[\[D4\]\], \[\[T1\]\], ⟨S2⟩

\#\#\# D4：τ³ 的 30 個多輪工具任務  
\- \*\*操作手法\*\*：測試 Agent 在多輪互動中選工具、維持狀態並完成任務。  
\- \*\*獨特特徵\*\*：錯誤會累積。早期錯誤 tool call 可污染後續上下文。  
\- \*\*影子證據\*\*：suite 規模為 \*\*30 tasks\*\*。  
\- \*\*連結\*\*：↔ \[\[D3\]\], \[\[D5\]\], → \[\[P2\]\]

\#\#\# D5：ContextBench 的 30 個上下文任務  
\- \*\*操作手法\*\*：專門測試 Agent 在大型或分散資訊中找到、保留並使用正確 context。  
\- \*\*獨特特徵\*\*：把「context engineering」從 prompt 技巧變成可量測 capability。  
\- \*\*影子證據\*\*：suite 規模為 \*\*30 tasks\*\*。  
\- \*\*連結\*\*：↔ \[\[D4\]\], \[\[D6\]\], ⟨S1⟩

\#\#\# D6：多次執行捕捉 variance  
\- \*\*操作手法\*\*：同一設定執行多次，避免把一次幸運成功視為穩定能力。  
\- \*\*獨特特徵\*\*：Agent trajectory 的 stochasticity 通常高於單輪模型回答。  
\- \*\*影子證據\*\*：文章明確強調 repeated runs 與 aggregate metrics。  
\- \*\*連結\*\*：↔ \[\[D5\]\], \[\[D7\]\], → \[\[G1\]\]

\#\#\# D7：Lite suite 的速度與成本 trade-off  
\- \*\*操作手法\*\*：建立較小、較快的日常 regression suite；完整 suite 用於 release gate。  
\- \*\*獨特特徵\*\*：Lite 約 \*\*8× faster\*\*、\*\*6× cheaper\*\*，但不能替代完整 coverage。  
\- \*\*影子證據\*\*：速度與成本倍率需同時保留。  
\- \*\*連結\*\*：↔ \[\[D6\]\], \[\[D8\]\], → \[\[R1\]\]

\#\#\# D8：v0.7 移除 todo middleware 的消融實驗  
\- \*\*操作手法\*\*：移除 todo middleware、縮減 system prompt，再比較 capability suite。  
\- \*\*獨特特徵\*\*：不是只測新功能；也測刪除框架元件是否改善或傷害 performance。  
\- \*\*影子證據\*\*：版本代號 \*\*v0.7\*\*；變更包含兩項：移除 todo middleware、精簡 system prompt。  
\- \*\*連結\*\*：↔ \[\[D7\]\], → \[\[S2\]\], \[\[P3\]\]

\#\#\# S1：按能力分解 benchmark  
\- \*\*策略邏輯\*\*：總分只做概覽。決策必須回到 planning、context、tools、recovery、artifact quality 等 capability slices。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：Harbor-Index、τ³、ContextBench 與 capability suite 並行。  
  \- \*\*環境/競對參照\*\*：一般 leaderboard 把不同失敗模式壓成單一平均值。  
\- \*\*反面教材 (Pre-mortem)\*\*：總分提升來自簡單任務，關鍵 production slice 反而退步。  
\- \*\*理論基礎\*\*：← \[\[D3\]\]–\[\[D6\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\], \[\[P2\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[G1\]\]

\#\#\# S2：用消融測試 Harness，不只測模型  
\- \*\*策略邏輯\*\*：Agent framework 的 middleware、prompt、memory 與 planning abstraction 都必須能被獨立移除或替換。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：v0.7 對 todo middleware 與 system prompt 做 ablation。  
  \- \*\*環境/競對參照\*\*：多數產品把模型升級、prompt 修改與工具改動一次發布，失去因果辨識。  
\- \*\*反面教材 (Pre-mortem)\*\*：看到分數下降卻不知道是 model、tool schema、middleware 還是 evaluator 改變。  
\- \*\*理論基礎\*\*：← \[\[D7\]\], \[\[D8\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P3\]\]  
\- \*\*支撐框架\*\*：← \[\[R1\]\]

\#\#\# T1：Deep Agent 評估矩陣  
\- \*\*用途\*\*：將 failure mode 映射到可執行測試。  
\- \*\*結構內容\*\*：  
  | 維度 | 測量方法 | 主要 Bug |  
  |---|---|---|  
  | Planning | milestone completion、replan count | 計畫漂移、無限迴圈 |  
  | Context | retrieval precision、lost-fact rate | 關鍵資訊遺失 |  
  | Tool use | valid call rate、recovery rate | schema error、錯誤重試 |  
  | Environment | test.sh、artifact checks | 只產生文字、未完成工作 |  
  | Stability | repeated-run pass rate、variance | 偶然成功 |  
  | Efficiency | tokens、time、tool calls | 成本失控 |  
  | Safety | side-effect audit、rollback | 不可逆 mutation |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[P1\]\], \[\[G1\]\]

\#\#\# R1：雙層 Agent CI 路線圖  
\- \*\*總體目標\*\*：在工程速度與完整 coverage 間建立 release protocol。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 PR Lite\*\*：每次 commit 執行低成本代表任務。  
  \- \*\*Phase 2 Nightly Full\*\*：執行完整 Harbor-Index、τ³、ContextBench。  
  \- \*\*Phase 3 Capability Diff\*\*：比較各 slice，而非只比較總分。  
  \- \*\*Phase 4 Ablation Gate\*\*：每個 framework 重大變更進行 controlled ablation。  
  \- \*\*Phase 5 Production Replay\*\*：匿名化重播真實失敗案例。  
\- \*\*系統風險 (Glitches)\*\*：benchmark overfitting、grader leakage、container drift、非決定性 external service、只保留成功 trace。  
\- \*\*連結\*\*：→ \[\[G1\]\], \[\[G2\]\]

\#\#\# G1：Agent Benchmark Governance  
\- \*\*核心協議 (Protocol)\*\*：任何 release score 必須綁定 agent version、model、prompt、tools、container digest、dataset revision 與 run count。  
\- \*\*具體條款/機制\*\*：  
  \- 每個 task 獨立版本化 instruction 與 evaluator。  
  \- 報告 mean、pass@k、variance 與 failure taxonomy。  
  \- Benchmark change 與 agent change 不得在同一 comparison 中混淆。  
  \- 保存完整 trace 與 artifacts。  
\- \*\*決策流程\*\*：environment validation → repeated runs → capability diff → regression review → release decision。  
\- \*\*違規後果\*\*：缺少版本或 trace 的分數不得用於 release claim。  
\- \*\*連結\*\*：← \[\[R1\]\], → \[\[S1\]\]

\#\#\# G2：Evaluator Integrity Protocol  
\- \*\*核心協議 (Protocol)\*\*：grader 必須驗證工作成果，不可只比對模型文字。  
\- \*\*具體條款/機制\*\*：  
  \- evaluator 不暴露給 Agent。  
  \- test.sh 使用 deterministic fixtures。  
  \- 對 evaluator 本身建立 unit tests。  
  \- 外部服務以 mock 或 recorded replay 固定。  
\- \*\*決策流程\*\*：grader test → adversarial task → leakage check → benchmark publish。  
\- \*\*違規後果\*\*：若 Agent 可從 prompt 猜答案或繞過 test，該 task 立即隔離。  
\- \*\*連結\*\*：← \[\[D2\]\], \[\[R1\]\], → \[\[S2\]\]

\#\#\# P1：建立 Harbor Task Package  
\- \*\*場景 (Scenario)\*\*：把一個真實 Agent 工作流轉成可重現 benchmark。  
\- \*\*價值 (Value)\*\*：將 failure report 轉為永久 regression test。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 建立 Dockerfile 或 docker-compose.yml，固定依賴與服務。  
  2\. 用 instruction.md 描述使用者目標與限制。  
  3\. 準備 input files、seed data 與 hidden fixtures。  
  4\. 寫 test.sh，檢查 artifact、state 與 side effects。  
  5\. 設定 timeout、resource limit 與 network policy。  
  6\. 在 clean container 重跑至少三次。  
\- \*\*工具集 (Toolset)\*\*：Harbor、Docker、pytest、shell、artifact store。  
\- \*\*影子技巧\*\*：測最終 filesystem/database state，不只測 stdout。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[D2\]\]

\#\#\# P2：Trajectory Failure Taxonomy  
\- \*\*場景 (Scenario)\*\*：Agent final answer 失敗，需要定位 subsystem。  
\- \*\*價值 (Value)\*\*：避免用更多 token 盲目修 prompt。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 將 trace 切分為 plan、observe、act、verify、recover。  
  2\. 標記 first irreversible error。  
  3\. 分類 context loss、tool schema、planning、environment、verification。  
  4\. 建立每類最小 reproduction task。  
  5\. 修復後在 capability slice 與 full suite 雙重驗證。  
\- \*\*工具集 (Toolset)\*\*：LangSmith trace、OpenTelemetry、failure-label schema、review UI。  
\- \*\*影子技巧\*\*：先找第一個因果錯誤，不把最後一個 exception 當 root cause。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[D4\]\]

\#\#\# P3：Framework Ablation Harness  
\- \*\*場景 (Scenario)\*\*：評估 todo middleware、memory、system prompt 或 planning component。  
\- \*\*價值 (Value)\*\*：量化 framework abstraction 的真實貢獻。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 固定 model、dataset、tools 與 container。  
  2\. 每次只改一個 component。  
  3\. 多次執行，計算 confidence interval。  
  4\. 比較 capability slice、成本與 latency。  
  5\. 檢查 component removal 是否只改善簡單任務。  
\- \*\*工具集 (Toolset)\*\*：feature flags、experiment manifest、Harbor、statistical notebook。  
\- \*\*影子技巧\*\*：刪除元件也視為一等實驗，不預設框架越多越強。  
\- \*\*連結\*\*：← \[\[S2\]\], \[\[D8\]\]

\#\#\# E1：Agent 評估的原子是環境，不是問題句  
\- \*\*法則內容\*\*：沒有 sandbox、grader 與 artifact 的 Agent benchmark，只能測語言表現，不能證明工作完成。  
\- \*\*推論/啟示\*\*：高價值 benchmark 資產是可執行 task package 與 failure corpus。  
\- \*\*支撐證據\*\*：← \[\[C1\]\], \[\[D1\]\], \[\[D2\]\], \[\[G2\]\]

\#\#\# E2：Benchmark 的目的不是排名，而是定位  
\- \*\*法則內容\*\*：能指出哪個 subsystem 退步的評估，比只提供更精確總分的評估更有工程價值。  
\- \*\*推論/啟示\*\*：Agent 團隊應投資 capability slices、ablation 與 production replay。  
\- \*\*支撐證據\*\*：← \[\[S1\]\], \[\[S2\]\], \[\[T1\]\], \[\[R1\]\]
