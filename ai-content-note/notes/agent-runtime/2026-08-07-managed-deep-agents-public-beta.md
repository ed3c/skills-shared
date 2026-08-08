---
id: "langchain:managed-deep-agents-public-beta"
title: "Managed Deep Agents is now in Public Beta"
source_name: "LangChain"
source_type: "official-blog"
source_url: "https://www.langchain.com/blog/introducing-managed-deep-agents"
canonical_url: "https://www.langchain.com/blog/introducing-managed-deep-agents"
published_at: "2026-08-07"
monetization_score: 100
monetization_modes: "Managed Agent Runtime migration lab; durable-thread architecture; sandbox/MCP governance; production Agent platform consulting."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["agent-runtime", "managed-runtime"]
mapping_targets: ["code", "trajectory"]
github_path: "ai-content-note/notes/agent-runtime/2026-08-07-managed-deep-agents-public-beta.md"
legacy_google_doc_id: "1WkxvFyszLLWk6hRhrLegy6H5neCvWUAyM8axbwmtTKU"
legacy_google_doc_url: "https://docs.google.com/document/d/1WkxvFyszLLWk6hRhrLegy6H5neCvWUAyM8axbwmtTKU/edit"
citation_mapping_status: pending
---

\#\#\# N1：Deep Agents 從 harness 進入 managed runtime  
\- \*\*核心衝突\*\*：Agent prototype 越來越容易；production operation 仍被 durable execution、state、sandbox、tool auth、context、observability 拖住。  
\- \*\*關鍵人物/實體\*\*：Open-source Deep Agents harness / LangSmith Managed Deep Agents / enterprise platform teams。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- 2026-05-13：Managed Deep Agents 以 private beta 形式發布。  
  \- 2026-08-07：LangChain Blog 將其標記為 \*\*Public Beta\*\*。  
  \- API surface 採 \`/v1/deepagents\`；agent project 可包含 \`AGENTS.md\`, \`skills/\`, \`subagents/\`, \`tools.json\`。  
\- \*\*劇情轉折\*\*：Agent definition 留在 developer-controlled project；runtime ownership 被抽成 hosted control plane。從「框架」轉為「Agent PaaS」。  
\- \*\*生態背景\*\*：長任務需要 pause/resume、checkpoint、files、memory、human approval、sandbox、trace；這些不是單次 LLM call 能解決的。  
\- \*\*連結\*\*：→ \[\[D1.1\]\], \[\[D1.2\]\], \[\[D1.3\]\], \[\[R1\]\]

\#\#\# Q1：Agent 的真正產品邊界到底在 prompt、harness，還是 runtime？  
\- \*\*核心疑問 (The Doubt)\*\*：若一個 agent 的可靠性取決於 thread state、tool credentials、filesystem、sandbox snapshot、human approval 與 trace，為什麼 deployment artifact 仍只被想像成「一段 prompt \+ model」？  
\- \*\*現狀反差 (Reality Gap)\*\*：framework 解決 orchestration abstraction；production agent 還要處理 durable work 與 governance。  
\- \*\*思維實驗 (Simulation)\*\*：同一套 \`AGENTS.md\` 與 skills，在無 checkpoint 的 stateless server 與有 durable runtime 的環境中，是否仍是「同一個 agent」？行為可靠性顯然不同。  
\- \*\*連結\*\*：← \[\[D1.1\]\], \[\[D1.2\]\]；→ \[\[C1\]\], \[\[G1\]\]

\#\#\# C1：Agent Runtime as Operating System  
\- \*\*定義\*\*：Managed runtime 提供 agent 長時間工作的 execution substrate：threads、checkpoint、streaming、context、files、sandbox、tool policy、observability。  
\- \*\*演化\*\*：\`LLM App \-\> Agent Framework \-\> Agent Harness \-\> Managed Agent Runtime\`。  
\- \*\*本質\*\*：模型負責 inference；harness 負責策略；runtime 負責 durable state 與 execution guarantees；governance 負責限制 agent 可以做什麼。  
\- \*\*結構特徵\*\*：API control plane、persistent thread、Context Hub、sandbox、MCP/tool registry、HITL、trace/eval loop。  
\- \*\*連結\*\*：→ \[\[T1\]\], \[\[P1\]\], \[\[G1\]\]；→ \[\[E1\]\]

\#\#\# D1.1：Managed Deep Agents API control plane  
\- \*\*操作手法\*\*：透過 \`/v1/deepagents\` 建立、更新、列出、執行 agents；runtime 支援 durable threads、streaming runs、checkpointing、human-in-the-loop。  
\- \*\*獨特特徵\*\*：不需要為每個 deep agent 自建 custom server。  
\- \*\*影子證據\*\*：LangChain docs 的 list API 位於 \`https://api.smith.langchain.com/v1/deepagents/agents\`；pagination \`page\_size\` 最大 100；agent runtime 可綁定 model id。  
\- \*\*連結\*\*：← \[\[C1\]\]；→ \[\[P1\]\]

\#\#\# D1.2：Context 被升級成 versioned production artifact  
\- \*\*操作手法\*\*：Managed Deep Agents 保留 Deep Agents project shape：\`AGENTS.md\`、\`skills/\`、\`subagents/\`、\`tools.json\`；Context Hub 負責儲存、版本化、更新跨 runs 的 operating context。  
\- \*\*獨特特徵\*\*：Memory 不再只是 chat history。它可以是 user preference、project notes、operating procedure、policy、skill definition。  
\- \*\*影子證據\*\*：LangChain 明確把長期 agent improvement 連到 production traces → issue detection → context/code change。  
\- \*\*連結\*\*：↔ \[\[D1.3\]\]；→ \[\[G1\]\], \[\[E1\]\]

\#\#\# D1.3：Sandbox \+ Tool Registry 把 agency 變成可管控 execution  
\- \*\*操作手法\*\*：Agent 可使用 sandbox 進行 code、shell、file I/O、artifact generation；tools 由 \`tools.json\` 定義，可對個別 tool 開啟 human-in-the-loop。Managed Deep Agents 也提供 MCP server registration surface。  
\- \*\*獨特特徵\*\*：Tool connection 與 credential placement 進入 control plane，而不是散落在 prompt 或 process environment。  
\- \*\*影子證據\*\*：MCP server registration 使用 workspace-level server URL 與 credential headers；agent execution 可透過 registered MCP endpoint 自動取得授權資訊。  
\- \*\*連結\*\*：↔ \[\[D1.2\]\]；→ \[\[G1\]\], \[\[P2\]\]

\#\#\# S1：Thin Agent Definition, Thick Runtime  
\- \*\*策略邏輯\*\*：Agent repo 保留可移植 definition；把 durability、sandbox、trace、secret、approval 等重 operational concerns 下沉到 runtime。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：Deep Agents harness open source；Managed Deep Agents 提供 hosted operational layer。  
  \- \*\*環境/競對參照\*\*：自建 Temporal \+ sandbox \+ tracing \+ secret broker 可取得最高控制力，但每個 team 重建一次會形成 platform duplication。  
\- \*\*反面教材 (Pre-mortem)\*\*：Bug \= 把 managed runtime 當黑盒，結果 agent definition、context、credentials、policy 都被 provider lock-in。  
\- \*\*理論基礎\*\*：← \[\[D1.1\]\], \[\[D1.2\]\], \[\[D1.3\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\], \[\[P2\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[R1\]\], \[\[G1\]\]

\#\#\# T1：Agent Production Stack Ownership Matrix  
\- \*\*用途\*\*：決定什麼要放 repo、什麼交給 managed runtime。  
\- \*\*結構內容\*\*：  
  | 層 | Repo-owned | Runtime-owned |  
  |---|---|---|  
  | Behavior | AGENTS.md / skills / subagents | version distribution |  
  | Tool schema | tools.json / MCP contracts | credential injection / policy |  
  | State | data model | durable threads / checkpoints |  
  | Execution | task logic | sandbox / shell / files |  
  | Safety | approval rules | HITL enforcement / audit |  
  | Quality | eval definitions | traces / production feedback |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[G1\]\], \[\[P1\]\]

\#\#\# R1：Local Harness → Managed Production Migration  
\- \*\*總體目標\*\*：保留 agent definition portability，同時獲得 durable runtime。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Freeze Contract\*\*：固定 \`AGENTS.md\`, \`skills/\`, \`subagents/\`, \`tools.json\` schema；建立 baseline eval。  
  \- \*\*Phase 2 Register\*\*：透過 managed API 建 agent，設定 model、tools、context。  
  \- \*\*Phase 3 Durable Test\*\*：測試 checkpoint/resume、stream reconnect、duplicate request、long-running thread。  
  \- \*\*Phase 4 Sandbox Test\*\*：測 file persistence、package install、network boundary、secret isolation。  
  \- \*\*Phase 5 HITL Test\*\*：對高影響 tool call 強制 approval。  
  \- \*\*Phase 6 Trace Loop\*\*：production traces 轉成 regression evals，context/code 變更必須重新跑 baseline。  
\- \*\*系統風險 (Glitches)\*\*：只測 happy-path answer quality，沒有測 resume、retry、idempotency、secret lifecycle。  
\- \*\*連結\*\*：→ \[\[G1\]\]

\#\#\# G1：Managed Agent Runtime Governance  
\- \*\*核心協議 (Protocol)\*\*：任何可持續工作的 Agent，都必須有 identity、version、policy、state、tool authorization、trace lineage。  
\- \*\*具體條款/機制\*\*：  
  \- Agent identity：每個 deployment 有 immutable id \+ version metadata。  
  \- Context provenance：任何 \`AGENTS.md\` / skill / policy 更新可追溯、可 rollback。  
  \- Tool authorization：tool schema 與 credential 分離；高風險 tool 要 HITL 或 policy gate。  
  \- Sandbox boundary：network、filesystem、secrets、snapshot 都要有環境級 policy。  
  \- Run lineage：thread → run → model/tool calls → artifacts → human approvals 全鏈追蹤。  
\- \*\*決策流程\*\*：Code/Context Change → Offline Eval → Staging Run → Policy Check → Deploy → Trace → Regression Dataset。  
\- \*\*違規後果\*\*：缺 lineage 的 run 不可作為 production evidence；credential scope 不明的 MCP/tool 不能註冊到 production agent。  
\- \*\*連結\*\*：← \[\[R1\]\]；→ \[\[S1\]\], \[\[P1\]\], \[\[P2\]\]

\#\#\# P1：Managed Deep Agent 最小部署流程  
\- \*\*場景 (Scenario)\*\*：把本地 deep agent 變成可恢復、可觀測的 hosted service。  
\- \*\*價值 (Value)\*\*：避免自己先造一套 durable runtime 才能驗證產品。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. Repo 建立 \`AGENTS.md\`, \`skills/\`, \`subagents/\`, \`tools.json\`。  
  2\. 用 \`LANGSMITH\_API\_KEY\` 作 workspace credential；禁止硬編碼到 repo。  
  3\. 呼叫 \`/v1/deepagents/agents\` 建立 agent，記錄回傳 agent id。  
  4\. 建 thread，啟動 streaming run；人工 kill process 後驗證 resume/checkpoint。  
  5\. 讓 agent 產生 file/artifact，驗證跨 run context 與 filesystem semantics。  
  6\. LangSmith trace 中確認每個 tool call、intermediate state、approval event 可定位。  
\- \*\*工具集 (Toolset)\*\*：LangSmith Managed Deep Agents API、Context Hub、Sandboxes、LangSmith tracing、offline eval dataset。  
\- \*\*影子技巧\*\*：production readiness 的第一個 test 不應是「答案正不正確」，而是「中斷後是否能無歧義恢復」。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[G1\]\]

\#\#\# P2：MCP Credential Isolation Patch  
\- \*\*場景 (Scenario)\*\*：Agent 需要呼叫外部 MCP server，但不希望 secret 出現在 prompt、context 或 sandbox filesystem。  
\- \*\*價值 (Value)\*\*：把 tool capability 與 secret custody 解耦。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 在 workspace control plane 註冊 MCP server URL。  
  2\. credential 由 platform secret store 掛載，不寫入 \`tools.json\` plaintext。  
  3\. tool definition 只引用 server identity / capability。  
  4\. 每次 invocation 記錄 server id、agent id、user identity、policy decision，不記 raw secret。  
  5\. rotate credential 後跑 canary invocation，確認 agent 不需重建 context。  
\- \*\*工具集 (Toolset)\*\*：MCP registry、secret manager、policy engine、audit log。  
\- \*\*影子技巧\*\*：如果 agent 可以把 credential echo 到 context，代表 secret boundary 放錯層。  
\- \*\*連結\*\*：← \[\[D1.3\]\], \[\[G1\]\]

\#\#\# E1：Agent Reliability Is a Runtime Property  
\- \*\*法則內容\*\*：長任務 Agent 的可靠性，不是 model benchmark 的附屬值；它由 runtime durability、context versioning、tool policy、sandbox 與 traceability 共同決定。  
\- \*\*推論/啟示\*\*：下一階段 Agent platform 的競爭，不只是誰有更好的 agent loop，而是誰能把「可持續工作」變成可部署、可治理、可回溯的基礎設施。  
\- \*\*支撐證據\*\*：← \[\[D1.1\]\], \[\[D1.2\]\], \[\[D1.3\]\], \[\[R1\]\], \[\[G1\]\], \[\[P1\]\], \[\[P2\]\]
