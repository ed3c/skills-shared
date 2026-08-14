---
id: "openai:arc-agi-3-retained-reasoning-compaction"
title: "How enabling two settings tripled our scores on the ARC-AGI-3 benchmark"
source_name: "OpenAI Newsroom"
source_type: "official-research"
source_url: "https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/"
canonical_url: "https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores"
published_at: "2026-07-29"
monetization_score: 99
monetization_modes: "Agent harness audit; Responses API memory and compaction course; benchmark reproduction service; long-horizon context SDK."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["agent-harness", "memory-compaction"]
mapping_targets: ["code", "trajectory"]
github_path: "ai-content-note/notes/agent-harness/2026-07-29-arc-agi-3-retained-reasoning-compaction.md"
legacy_google_doc_id: "18qVcoQaromqyDen4wMyoRil5nsTnV57CmMzh4ryAi8w"
legacy_google_doc_url: "https://docs.google.com/document/d/18qVcoQaromqyDen4wMyoRil5nsTnV57CmMzh4ryAi8w/edit"
citation_mapping_status: pending
---

\#\#\# N1：ARC-AGI-3 的真正失敗點不是模型，而是 Harness  
\- \*\*核心衝突\*\*：表面敘事是「Frontier model 在新 benchmark 上突然變笨」；實際 Glitch 是 evaluation harness 丟掉模型推理狀態與舊行動。  
\- \*\*關鍵人物/實體\*\*：GPT‑5.6 Sol vs ARC-AGI-3 official harness vs OpenAI Responses API harness。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- GPT‑5.6 Sol 在初始 ARC-AGI-3 測試只得到 \*\*7.8%\*\*；GPT‑5.5 只有 \*\*0.4%\*\*。  
  \- Public set 上，official harness 為 \*\*13.3%\*\*；保留 reasoning \+ compaction 後為 \*\*38.3%\*\*。  
  \- OpenAI 估算 average human tester 為 \*\*48%\*\*。  
  \- 改 Harness 後，score 約 \*\*3x\*\*，output tokens 約降低 \*\*6x\*\*。  
\- \*\*劇情轉折\*\*：模型不是無法理解遊戲。每個 action 後 private reasoning 被丟棄，加上 rolling truncation，模型必須反覆重新理解世界。保留 reasoning 後，策略開始連續；加入 compaction 後，長期記憶不再被粗暴刪除。  
\- \*\*生態背景\*\*：Benchmark 常宣稱比較「模型能力」，但實際測的是 model × API × harness × prompt × context policy 的乘積。  
\- \*\*連結\*\*：→ \[\[D1\]\], \[\[D2\]\], → \[\[G1\]\], ≈ \[\[E1\]\]

\#\#\# Q1：Benchmark 到底是在測 Model，還是在測整個 Agent System？  
\- \*\*核心疑問 (The Doubt)\*\*：如果只換兩個 runtime settings 就能讓分數從 13.3% 變 38.3%，單一 benchmark score 還能被視為純模型能力嗎？  
\- \*\*現狀反差 (Reality Gap)\*\*：排行榜通常把模型名放在最前面；但 ARC-AGI-3 案例顯示，context retention policy 足以改寫結論。  
\- \*\*思維實驗 (Simulation)\*\*：如果企業用 generic harness 評估不同模型，是否會錯誤淘汰最適合 production 的模型，只因 evaluation runner 沒有啟用該模型在真實產品中的 memory/context 機制？  
\- \*\*連結\*\*：← \[\[D1\]\], \[\[D2\]\], → \[\[S1\]\]

\#\#\# C1：Harness-Sensitive Capability  
\- \*\*定義\*\*：模型表現不是靜態常數；它取決於 runtime 是否提供模型訓練時預期的 reasoning persistence、context lifecycle 與 tool-loop semantics。  
\- \*\*演化\*\*：傳統 benchmark 假設「prompt → answer」；Agent benchmark 必須建模「state → action → observation → retained state → next action」。  
\- \*\*本質\*\*：Harness 是能力放大器，也是能力破壞器。  
\- \*\*結構特徵\*\*：reasoning retention、history policy、compaction、tool loop、API semantics、prompt scaffolding。  
\- \*\*連結\*\*：→ \[\[D1\]\], \[\[D2\]\], → \[\[E1\]\]

\#\#\# C2：Retained Reasoning  
\- \*\*定義\*\*：跨 tool calls / turns 保留模型先前的 private reasoning state，使後續 action 不必從零重新推導。  
\- \*\*演化\*\*：official harness 每次 action 後丟棄 reasoning；Responses API harness 透過 previous response chain 保留歷史 reasoning。  
\- \*\*本質\*\*：不是增加更多 prompt，而是避免把模型剛建立的 latent plan 清空。  
\- \*\*結構特徵\*\*：turn continuity、plan persistence、lower repeated thinking、higher strategy coherence。  
\- \*\*連結\*\*：→ \[\[D1\]\], \[\[P1\]\], → \[\[E1\]\]

\#\#\# C3：Compaction 不是 Truncation  
\- \*\*定義\*\*：Compaction 將長歷史壓縮為可繼續工作的狀態；rolling truncation 直接刪除最舊內容。  
\- \*\*演化\*\*：ARC harness 在超過 \*\*175,000 characters\*\* 後丟棄最舊 messages；OpenAI 實作使用約 \*\*175,000 tokens\*\* 的 context management 與 compaction。  
\- \*\*本質\*\*：Truncation 是 memory deletion；compaction 是 memory transformation。  
\- \*\*結構特徵\*\*：保留關鍵 observation、actions、learned rules、降低 context saturation。  
\- \*\*連結\*\*：→ \[\[D2\]\], \[\[P1\]\], → \[\[E1\]\]

\#\#\# D1：13.3% → 38.3% 的 Harness Delta  
\- \*\*操作手法\*\*：以相同 GPT‑5.6 Sol 與同一 public task set，比較 official harness 與 retained reasoning \+ compaction harness。  
\- \*\*獨特特徵\*\*：模型權重不變。主要變數是 execution context policy。  
\- \*\*影子證據\*\*：official harness \*\*13.3%\*\*；改良 harness \*\*38.3%\*\*；average human tester 約 \*\*48%\*\*；效果約 \*\*3x score / 6x fewer output tokens\*\*。  
\- \*\*連結\*\*：↔ \[\[D2\]\] ⟨S1⟩

\#\#\# D2：Rolling Truncation 導致 Agent 失憶  
\- \*\*操作手法\*\*：official harness 超過 \*\*175,000 characters\*\* 後刪除最舊 messages；同時 action 後不保留 private reasoning。  
\- \*\*獨特特徵\*\*：模型同時失去「為什麼這樣做」與「之前做過什麼」。  
\- \*\*影子證據\*\*：OpenAI 觀察到保留 reasoning 後，模型每一步 thinking 變短，且能跨時間形成 coherent strategies。  
\- \*\*連結\*\*：↔ \[\[D1\]\] ⟨S1⟩

\#\#\# T1：Agent Benchmark Harness 對照矩陣  
\- \*\*用途\*\*：在評估模型前先審計 Harness，避免把 infrastructure bug 當成 model weakness。  
\- \*\*結構內容\*\*：  
  | 維度 | Generic Harness | Production-like Harness |  
  |---|---|---|  
  | Reasoning state | 每步丟棄 | 跨 turn 保留 |  
  | Context overflow | Rolling truncation | Compaction |  
  | Long-horizon learning | 容易重置 | 可累積策略 |  
  | Token efficiency | 重複推理 | 減少重算 |  
  | Benchmark interpretation | 偏向 model-only | model \+ runtime system |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[P1\]\]

\#\#\# S1：Production-Parity Evaluation  
\- \*\*策略邏輯\*\*：Benchmark runner 必須盡可能重現 production runtime 的 context lifecycle，否則比較結果不具 deployment validity。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：OpenAI 用 Responses API、retained reasoning、compaction 重建 evaluation harness。  
  \- \*\*環境/競對參照\*\*：generic benchmark 為了公平常刻意簡化 harness，但簡化可能移除 frontier model 依賴的 runtime semantics。  
\- \*\*反面教材 (Pre-mortem)\*\*：Glitch 是「為了公平而做成不真實」，最後公平比較的是錯誤部署方式。  
\- \*\*理論基礎\*\*：← \[\[D1\]\], \[\[D2\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[G1\]\]

\#\#\# P1：Agent Eval Harness Audit  
\- \*\*場景 (Scenario)\*\*：評估長流程 coding/research/browser agent。  
\- \*\*價值 (Value)\*\*：判斷低分來自 model capability 還是 harness design。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 建立 baseline：固定 model、task set、temperature/tool permissions 與 scoring。  
  2\. 記錄每 turn 是否保留 reasoning state、tool output、observation 與 plan。  
  3\. 建立第二條 runner：使用 Responses-style response chaining，讓前一 response ID 成為下一 turn 的狀態根。  
  4\. 將 context overflow policy 從「刪最舊訊息」改成「保留任務狀態的 compaction」。  
  5\. 同時記錄 score、output tokens、wall-clock、actions per task、failure trajectory。  
  6\. 只在 model 不變時比較 Harness Delta；再跨模型比較。  
  7\. 對重大排名變化執行 trace review，確認差異來自 memory/context，而不是 prompt leakage。  
\- \*\*工具集 (Toolset)\*\*：Responses API、evaluation runner、trace store、token accounting、task replay。  
\- \*\*影子技巧\*\*：把 Harness Delta 本身列為 benchmark metric，而不是隱藏 implementation detail。  
\- \*\*連結\*\*：← \[\[S1\]\]

\#\#\# G1：Benchmark Governance Protocol  
\- \*\*核心協議 (Protocol)\*\*：任何 Agent benchmark 報告都必須同時發布 model config 與 harness config。  
\- \*\*具體條款/機制\*\*：  
  \- 條款 1：揭露 reasoning retention、context overflow policy、tool loop、prompt scaffolding。  
  \- 條款 2：至少提供 generic harness 與 production-parity harness 的 sensitivity test。  
  \- 條款 3：若 score 對 harness 高敏感，不得把差異單獨歸因於 model weights。  
  \- 條款 4：保留可重播 traces，讓第三方能檢查 failure mode。  
\- \*\*決策流程\*\*：低分 → Harness Audit → State-retention A/B → Trace Review → 才能下模型能力結論。  
\- \*\*違規後果\*\*：排行榜會產生 model selection bias，進而造成錯誤採購與錯誤安全判斷。  
\- \*\*連結\*\*：← \[\[R1\]\], → \[\[S1\]\]

\#\#\# R1：從 Chat-Style Eval 遷移到 Agent-System Eval  
\- \*\*總體目標\*\*：讓 evaluation 與 production runtime 對齊。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Baseline Capture\*\*：凍結目前 runner，保存 score、tokens、traces。  
  \- \*\*Phase 2 State Preservation\*\*：加入 retained reasoning / response chaining。  
  \- \*\*Phase 3 Context Lifecycle\*\*：將 rolling truncation 換成 compaction。  
  \- \*\*Phase 4 Sensitivity Matrix\*\*：跨不同 models 與 tasks 測 Harness Delta。  
  \- \*\*Phase 5 Governance\*\*：把 harness config 納入 benchmark artifact 與 release gate。  
\- \*\*系統風險 (Glitches)\*\*：過度針對單一模型調 harness 可能變成 vendor-specific overfitting；必須同時保留 generic baseline。  
\- \*\*連結\*\*：→ \[\[G1\]\]

\#\#\# E1：Agent Capability \= Model × Harness × Memory  
\- \*\*法則內容\*\*：長流程 Agent 的能力不是模型權重單獨決定；Harness 與 memory policy 可以把同一模型從失憶狀態切換到有效策略學習。  
\- \*\*推論/啟示\*\*：未揭露 Harness 的 Agent benchmark，只提供了半個實驗。  
\- \*\*支撐證據\*\*：← \[\[N1\]\], \[\[D1\]\], \[\[D2\]\], \[\[T1\]\], \[\[S1\]\]
