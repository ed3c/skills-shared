---
id: "langchain:deep-agents-v0-7"
title: "Deep Agents v0.7"
source_name: "LangChain"
source_type: "official-blog"
source_url: "https://www.langchain.com/blog/deep-agents-v0-7"
canonical_url: "https://www.langchain.com/blog/deep-agents-v0-7"
published_at: "2026-07-29"
monetization_score: 100
monetization_modes: "Harness Diet CI; prompt-debt audit; adaptive summarization middleware; Deep Agents migration consulting."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["agent-harness", "context-engineering"]
mapping_targets: ["code", "trajectory"]
github_path: "ai-content-note/notes/agent-harness/2026-07-29-deep-agents-v0-7-harness-diet.md"
legacy_google_doc_id: "1T931T72lf27-h-V13-VZdyXQHq0Gk9eecGuh_GcZYPw"
legacy_google_doc_url: "https://docs.google.com/document/d/1T931T72lf27-h-V13-VZdyXQHq0Gk9eecGuh_GcZYPw/edit"
citation_mapping_status: pending
---

\#\#\# N1：Deep Agents v0.7 把「更多 Prompt」反向編譯成「更少 Harness」  
\- \*\*核心衝突\*\*：Agent framework 長期靠增加 system prompt、tool prose、todo scaffolding 來補模型能力；模型變強後，舊 scaffolding 反而成為 token tax 與 behavior conflict。  
\- \*\*關鍵人物/實體\*\*：LangChain Deep Agents v0.7 vs v0.6.12；OpenAI、Anthropic、Google prompting guidance；四個 evaluation models。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- Base input tokens 約從 \*\*\~6k → \~2k\*\*，下降 \*\*65%\*\*。  
  \- Built-in tool descriptions 被裁減 \*\*43%\*\*。  
  \- `gpt-5.6-luna`：tokens \*\*-34%\*\*、cost \*\*-15%\*\*、reward \*\*+4%\*\*。  
  \- Anthropic 對 modern models 的 Claude Code system prompt 報告顯示可削減 \*\*80%+\*\* 且 coding eval 無 measurable drop。  
\- \*\*劇情轉折\*\*：LangChain 移除 base system prompt、縮短 tool descriptions、將 `TodoListMiddleware` 改為 opt-in。結果不是能力下降，而是同等 performance 下顯著減少 context 與成本。  
\- \*\*生態背景\*\*：Prompt engineering 正從「增加 instruction」進入「context engineering \+ interface design \+ eval-driven deletion」。  
\- \*\*連結\*\*：→ \[\[D1\]\], \[\[D2\]\], \[\[D3\]\], → \[\[G1\]\], ≈ \[\[E1\]\]

\#\#\# Q1：Agent Harness 何時從 Feature 變成 Technical Debt？  
\- \*\*核心疑問 (The Doubt)\*\*：如果模型已能從 tool schema 理解操作方式，舊的 few-shot、重複說明、planning middleware 是否只是昂貴的歷史補丁？  
\- \*\*現狀反差 (Reality Gap)\*\*：團隊通常害怕刪 prompt，因為「多寫總比少寫安全」；v0.7 的實驗顯示多餘 prompt 可能只增加 tokens、conflict 與 context rot。  
\- \*\*思維實驗 (Simulation)\*\*：如果每次模型升級都只加 prompt 不刪 prompt，兩年後你的 agent system prompt 會不會變成 legacy monolith？  
\- \*\*連結\*\*：← \[\[D1\]\], \[\[D2\]\], → \[\[S1\]\]

\#\#\# C1：Context Engineering Budget  
\- \*\*定義\*\*：Prompt、tools、middleware、memory summaries、filesystem metadata 都在消耗同一 context budget。  
\- \*\*演化\*\*：舊思維把 prompt 當免費文字；Agent runtime 把每個固定 token 視為每一 turn 都要支付的 recurring tax。  
\- \*\*本質\*\*：Base harness 越肥，留給 task-specific context、retrieval、files 與 reasoning 的空間越少。  
\- \*\*結構特徵\*\*：base prompt size、tool schema size、middleware injection、summary trigger、cacheability、token/cost per turn。  
\- \*\*連結\*\*：→ \[\[D1\]\], \[\[D3\]\], → \[\[E1\]\]

\#\#\# C2：Interfaces Beat Examples  
\- \*\*定義\*\*：高品質 tool schema / API interface 能直接教模型「可做什麼、參數是什麼」，不必用大量 few-shot examples 教使用模式。  
\- \*\*演化\*\*：早期模型依賴 examples；modern models 對 typed interfaces 的泛化能力更強。  
\- \*\*本質\*\*：Examples 容易把搜索空間縮窄；interface 提供 constraints，但不預先鎖死 strategy。  
\- \*\*結構特徵\*\*：clear names、typed parameters、concise descriptions、non-duplicated semantics。  
\- \*\*連結\*\*：→ \[\[D1\]\], \[\[S1\]\], → \[\[E1\]\]

\#\#\# D1：Base Harness 減重實驗  
\- \*\*操作手法\*\*：移除 hidden base system prompt；tool descriptions 縮短 43%；`TodoListMiddleware` 不再預設加入。  
\- \*\*獨特特徵\*\*：不是單純壓縮文字，而是逐項用 eval 驗證「這段 scaffolding 是否仍有 marginal value」。  
\- \*\*影子證據\*\*：Default-agent base input 約 \*\*\~6k → \~2k\*\*，下降 \*\*65%\*\*。  
\- \*\*連結\*\*：↔ \[\[D2\]\], \[\[D3\]\] ⟨S1⟩

\#\#\# D2：TodoListMiddleware 被降級為 Conditional Feature  
\- \*\*操作手法\*\*：v0.7 預設移除 `write_todos` tool 與 planning prompt。  
\- \*\*獨特特徵\*\*：不是宣判 todo 無用。LangChain 明確保留三類例外：long multi-step tasks、less capable models、需要可視化進度的 UI-facing flows。  
\- \*\*影子證據\*\*：三類 benchmark 中，todos disabled 的 reward 略高、cost 較低，因此 default 被移除。  
\- \*\*連結\*\*：↔ \[\[D1\]\], \[\[D3\]\] ⟨S1⟩

\#\#\# D3：四模型 Eval Matrix  
\- \*\*操作手法\*\*：以 Autonomous、Conversational、Long-context 三類 benchmark，比較 v0.7 與 v0.6.12；models 為 `gpt-5.6-luna`、`gemini-3.6-flash`、`claude-sonnet-4-6`、`claude-opus-4-8`。  
\- \*\*獨特特徵\*\*：不是只測單一 coding benchmark，避免 harness optimization 對單一 task overfit。  
\- \*\*影子證據\*\*：`gpt-5.6-luna` tokens \*\*-34%\*\*、cost \*\*-15%\*\*、reward \*\*+4%\*\*；`claude-sonnet-4-6` 是例外，其 cost increase 主要來自兩個 challenging autonomous tasks。Reward confidence intervals 對所有 models 都跨過 zero；Luna 與 Opus token reductions 有統計上較明確的信號。  
\- \*\*連結\*\*：↔ \[\[D1\]\], \[\[D2\]\] ⟨S1⟩

\#\#\# D4：SummarizationMiddleware 變成 First-Class Override  
\- \*\*操作手法\*\*：v0.7 允許用同名 middleware instance 覆寫 built-in defaults；例如將 summarization trigger 從 default \*\*85%\*\* context window 改為 \*\*50%\*\*。  
\- \*\*獨特特徵\*\*：過去需要 hacky removal；現在 prompt、threshold、model 都能被顯式控制。  
\- \*\*影子證據\*\*：官方示例使用 `SummarizationMiddleware(model="fireworks:accounts/fireworks/models/kimi-k3", trigger=("fraction", 0.5), ...)`。  
\- \*\*連結\*\*：→ \[\[P1\]\], \[\[G1\]\]

\#\#\# D5：Filesystem 也屬於 Context Runtime  
\- \*\*操作手法\*\*：`write_file` 改為 overwrite existing file；`read_file` pagination 回報 total / remaining lines / next offset；`grep` / `glob` 對大樹返回 partial results \+ `truncated`，`grep` 加入 \*\*1,000-match cap\*\*、streaming 與 optional context lines。  
\- \*\*獨特特徵\*\*：Agent filesystem 不是 storage accessory，而是 memory/context navigation layer。  
\- \*\*影子證據\*\*：這些變更直接來自 eval suite 與真實 `dcode` trajectories。  
\- \*\*連結\*\*：→ \[\[P2\]\], \[\[E1\]\]

\#\#\# T1：Harness Bloat Audit Matrix  
\- \*\*用途\*\*：判斷固定 prompt / tool / middleware 是否該保留。  
\- \*\*結構內容\*\*：  
  | 元件 | 問題 | 刪除/保留判準 |  
  |---|---|---|  
  | Base system prompt | 是否只是通用指南？ | 無 measurable reward → 刪 |  
  | Tool descriptions | 是否重複 system prompt？ | schema 已足夠 → 縮 |  
  | Few-shot examples | 是否限制探索？ | interface 可表達 → 減 |  
  | Todo planning | 是否所有 task 都需要？ | 只對 long/weak/UI flows 啟用 |  
  | Summarization | trigger 是否太晚？ | 依 context rot 曲線調整 |  
  | Filesystem output | 是否一次塞爆 context？ | pagination / truncation metadata |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[P1\]\], \[\[P2\]\]

\#\#\# S1：Delete-Driven Context Engineering  
\- \*\*策略邏輯\*\*：Agent harness 的升級不是持續增加規則，而是以 eval 證明哪些規則已失去 marginal value，然後刪除。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：LangChain 以 cross-model、cross-task eval 去除 hidden prompting。  
  \- \*\*環境/競對參照\*\*：OpenAI、Anthropic、Google prompting guides 都隨模型能力更新；固定 harness 若不跟著變，會把舊模型時代的補丁永久帶進新模型。  
\- \*\*反面教材 (Pre-mortem)\*\*：最大 Glitch 是把 prompt history 當安全資產。實際上它可能是 token debt、instruction conflict 與 context dilution。  
\- \*\*理論基礎\*\*：← \[\[D1\]\], \[\[D2\]\], \[\[D3\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[G1\]\]

\#\#\# P1：Harness Diet CI  
\- \*\*場景 (Scenario)\*\*：每次 model upgrade 或 agent framework release 前，自動尋找可刪除的 scaffolding。  
\- \*\*價值 (Value)\*\*：降低 recurring token cost，同時避免 behavior regressions。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 將 base prompt、tool descriptions、middleware prompt 分成獨立可 toggle modules。  
  2\. 建立三類 eval：autonomous、conversational、long-context。  
  3\. 對每個 module 做 ablation：ON vs OFF；固定 model、task、seed / replay trace。  
  4\. 收集 reward、input/output tokens、cost、latency、tool errors、trajectory length。  
  5\. 若 removal 無 statistically meaningful reward drop，標記為 `deprecation-candidate`。  
  6\. 再跨至少兩個不同 provider models 驗證；只對單一 model 有效的 prompt 不應成為 global default。  
  7\. Merge 前生成「context budget diff」：固定 tokens/turn 增減與 projected monthly cost。  
\- \*\*工具集 (Toolset)\*\*：LangSmith evals/traces、Deep Agents middleware toggles、CI matrix、token accounting。  
\- \*\*影子技巧\*\*：把「刪 prompt」當性能優化 PR，需要 benchmark evidence，不是 aesthetic refactor。  
\- \*\*連結\*\*：← \[\[S1\]\]

\#\#\# P2：Adaptive Summarization Middleware  
\- \*\*場景 (Scenario)\*\*：Long-running agents 在 context window 後段出現 context rot / dumb-zone behavior。  
\- \*\*價值 (Value)\*\*：在模型開始退化前主動 compact。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 以 baseline 收集 task success 對 context utilization percentage 曲線。  
  2\. 找到 failure rate 開始上升的 utilization point，例如 60%–80%。  
  3\. 將 summarization trigger 設在 degradation point 之前，而不是固定使用 85%。  
  4\. Summary prompt 強制保留 file paths、decisions、constraints、open TODOs、tool errors。  
  5\. 針對高成本 frontier model，可用較便宜專用 summarizer model，但必須做 state-loss regression tests。  
  6\. 對 summary 前後建立 replay，確認關鍵 invariant 未遺失。  
\- \*\*工具集 (Toolset)\*\*：`SummarizationMiddleware`、trace replay、context utilization telemetry。  
\- \*\*影子技巧\*\*：Summary 是 state migration，不是文章摘要。  
\- \*\*連結\*\*：← \[\[S1\]\]

\#\#\# G1：Prompt Debt Governance  
\- \*\*核心協議 (Protocol)\*\*：任何固定注入 agent context 的字串都視為 recurring infrastructure cost，必須有 owner、eval evidence、expiration review。  
\- \*\*具體條款/機制\*\*：  
  \- 條款 1：新增 system/tool prompt 必須附 token delta。  
  \- 條款 2：每次 major model upgrade 執行 harness ablation suite。  
  \- 條款 3：Global middleware default 必須跨 providers 有正向證據。  
  \- 條款 4：Hidden prompting 禁止；所有 runtime injection 可 inspect / override。  
  \- 條款 5：Breaking default changes 必須提供 migration notes 與 rollback path。  
\- \*\*決策流程\*\*：Add prompt → benchmark → cost projection → owner → periodic ablation → retain/delete。  
\- \*\*違規後果\*\*：Agent 逐年變慢、變貴、context 被 legacy instructions 填滿，且團隊不知道哪段 prompt 還在控制 behavior。  
\- \*\*連結\*\*：← \[\[R1\]\], → \[\[S1\]\]

\#\#\# R1：從 Prompt Accretion 到 Harness Minimalism  
\- \*\*總體目標\*\*：建立可持續更新的 agent runtime，而不是 prompt landfill。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Inventory\*\*：列出所有 fixed context sources。  
  \- \*\*Phase 2 Ablation\*\*：逐 module 關閉，量測 reward/token/cost。  
  \- \*\*Phase 3 Interface Upgrade\*\*：把 prose teaching 轉成 typed tool schema。  
  \- \*\*Phase 4 Adaptive Middleware\*\*：todo、summarization 等改成 task-conditioned。  
  \- \*\*Phase 5 Continuous Diet\*\*：每個 model release 自動重跑 deletion candidates。  
\- \*\*系統風險 (Glitches)\*\*：過度追求 minimalism 可能刪掉 rare-task safety constraints；Patch 是以 coverage-oriented eval suite 保護 long-tail behavior。  
\- \*\*連結\*\*：→ \[\[G1\]\]

\#\#\# E1：更強模型需要更少固定 Scaffolding，但更強的 Runtime Control  
\- \*\*法則內容\*\*：Model capability 上升時，通用 instruction 的 marginal value 下降；可觀測、可覆寫、可評估的 context runtime 價值上升。  
\- \*\*推論/啟示\*\*：下一代 Agent framework 的護城河不在最大 prompt，而在最小必要 context \+ 最強 control plane。  
\- \*\*支撐證據\*\*：← \[\[N1\]\], \[\[D1\]\], \[\[D2\]\], \[\[D3\]\], \[\[D4\]\], \[\[D5\]\]
