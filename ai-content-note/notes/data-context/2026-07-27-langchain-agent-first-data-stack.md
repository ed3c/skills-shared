---
id: "langchain:agent-data-stack"
title: "How we built LangChain's agent-first data stack"
source_name: "LangChain"
source_type: "official-blog"
source_url: "https://www.langchain.com/blog/agent-data-stack"
canonical_url: "https://www.langchain.com/blog/agent-data-stack"
published_at: "2026-07-27"
monetization_score: 99
monetization_modes: "Agent-first data stack implementation; dbt and semantic context audit; enterprise data Agent course; MCP integration consulting."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["data-context", "semantic-layer"]
mapping_targets: ["code", "data", "trajectory"]
github_path: "ai-content-note/notes/data-context/2026-07-27-langchain-agent-first-data-stack.md"
legacy_google_doc_id: "1131kZibOah3uyYR-TiQQd5dtSr-9mLmo40PGeSa75P4"
legacy_google_doc_url: "https://docs.google.com/document/d/1131kZibOah3uyYR-TiQQd5dtSr-9mLmo40PGeSa75P4/edit"
citation_mapping_status: pending
---

\#\#\# N1：資料團隊從答題員轉為 Context 系統工程師  
\- \*\*核心衝突\*\*：傳統 BI stack 能回答預先定義的問題，但探索式分析仍依賴資料團隊翻譯需求、找模型、寫 SQL、驗證與回覆。Agent 能生成 SQL，卻可能選錯表、錯解 metric 或給出技術正確但商業無用的答案。  
\- \*\*關鍵人物/實體\*\*：LangChain 三人 data team、Hex、dbt、Slack、CLI、MCP、LangSmith Fleet、business users vs BI bottleneck、context gap、source ambiguity 與 trust drift。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- 文章發布於 \*\*2026-07-27\*\*。  
  \- Data agent 處理約為三人 data team 可直接承接量的 \*\*40x\*\*。  
  \- 過去 \*\*30 天\*\*約有 \*\*2,200 次 agent conversations\*\*。  
  \- Provisioned users 中接近 \*\*100%\*\*使用；這些人約占公司 \*\*三分之一\*\*。  
  \- 平均每位使用者每月 \*\*23 次 conversations\*\*。  
\- \*\*劇情轉折\*\*：團隊沒有只加一個 chatbot。它在 \*\*6 週\*\*內 100% 移除舊 BI tool，將 Hex、dbt、semantic model、workspace guides、endorsements、GitHub context 與 observability 組成 agent-first stack。  
\- \*\*生態背景\*\*：Data agent 的長期價值不是讓每個人寫 SQL，而是讓組織把 metric definition、business rules、trust signals 與 escalation criteria 編譯成可被 agent 使用的 context。  
\- \*\*連結\*\*：  
  \- 證據支撐：→ \[\[D1\]\], \[\[D2\]\], \[\[D3\]\], \[\[D4\]\], \[\[D5\]\], \[\[D6\]\], \[\[D7\]\]  
  \- 歷史鏡像：≈ \[\[Self-service BI\]\], \[\[Data Catalog\]\], \[\[Semantic Layer\]\]  
  \- 治理建立：→ \[\[G1\]\]

\#\#\# Q1：Agent 能查到資料，是否等於能理解業務？  
\- \*\*核心疑問 (The Doubt)\*\*：若 agent 具有所有 table access，但不知道 ARR 定義、canonical dashboard、deployment type 與 customer-health filter，它的答案是否比沒有答案更危險？  
\- \*\*現狀反差 (Reality Gap)\*\*：理想敘事是「NL-to-SQL democratizes data」；真實情況是資料意義、來源權威與使用邊界比 SQL generation 更難。  
\- \*\*思維實驗 (Simulation)\*\*：公司同時存在三個 ARR tables。兩個歷史上曾正確，但現在只有一個 endorsed。沒有 trust signal 的 agent 應如何選？  
\- \*\*連結\*\*：← \[\[D3\]\], \[\[D4\]\], \[\[D5\]\], \[\[D6\]\], → \[\[S1\]\], \[\[G1\]\]

\#\#\# C1：Agent-First Data Stack  
\- \*\*定義\*\*：以 agent 為一級使用者設計的資料平台，除 tables 外，還提供 metric semantics、business context、source trust、implementation lineage 與 feedback loop。  
\- \*\*演化\*\*：從 dashboard-centric BI，演化為 UI \+ Slack \+ CLI \+ MCP \+ agent context plane。  
\- \*\*本質\*\*：把隱性組織知識轉成 machine-readable、versioned、reviewed context。  
\- \*\*結構特徵\*\*：clean models、semantic layer、workspace guides、endorsements、GitHub lineage、observability、evals、human escalation。  
\- \*\*連結\*\*：  
  \- 實例展開：→ \[\[D2\]\], \[\[D3\]\], \[\[D4\]\], \[\[D5\]\], \[\[D6\]\], \[\[D7\]\]  
  \- 支撐法則：→ \[\[E1\]\]

\#\#\# D1：六週完成 BI Cutover  
\- \*\*操作手法\*\*：  
  1\. 評估的不只是 dashboard replacement。  
  2\. 要求產品原生支援 AI 與 notebook workflow。  
  3\. 為 technical 與 non-technical users 提供不同入口。  
  4\. 選擇 Hex 作為單一 central data workspace。  
  5\. 避免舊 BI 與新工具並存造成 usage、context、trust 分裂。  
\- \*\*獨特特徵\*\*：不是先長期雙軌，而是快速完成 platform convergence。  
\- \*\*影子證據\*\*：團隊在 \*\*6 週\*\*內 \*\*100%\*\*移除舊 BI tool；目前公司 \*\*100%\*\*以某種形式使用 Hex stack。  
\- \*\*連結\*\*：→ \[\[R1\]\], \[\[S1\]\]

\#\#\# D2：五種 Agent Access Surface  
\- \*\*操作手法\*\*：  
  1\. Hex UI：Threads 與 notebooks。  
  2\. Slack：在團隊溝通位置直接提問。  
  3\. CLI：技術操作與自動化。  
  4\. MCP：標準化工具連接。  
  5\. LangSmith Fleet：透過 MCP 與 CLI integration。  
\- \*\*獨特特徵\*\*：採用不是要求所有人遷移到同一聊天 UI，而是把同一 context plane 投射到既有工作表面。  
\- \*\*影子證據\*\*：Marketing 用於 weekly pipeline；Product 分析 usage；Sales/Deployment Engineering 查 customer health；Customer Engineering 分析 churn 與 expansion。  
\- \*\*連結\*\*：↔ \[\[D3\]\], \[\[D4\]\], \[\[D5\]\] ⟨T1⟩

\#\#\# D3：dbt Definition 從資料字典升級成 Agent Contract  
\- \*\*操作手法\*\*：  
  1\. 每個 table/column 說明資料代表什麼。  
  2\. 記錄 allowed values。  
  3\. 提供 business interpretation。  
  4\. 指定 default filters 與 edge cases。  
  5\. Table-level definition 說明 grain、適用問題與注意事項。  
\- \*\*獨特特徵\*\*：定義不只描述欄位，而是告訴 agent 如何安全使用。  
\- \*\*影子證據\*\*：文章以 \`account\_status\` 為例，明確定義 \`Active\`、\`Churned\`、\`Prospect\`，並要求 customer reporting 預設 filter \`Active\`。  
\- \*\*連結\*\*：→ \[\[C1\]\], \[\[P1\]\]

\#\#\# D4：Semantic Model 的 Metric Compiler  
\- \*\*操作手法\*\*：  
  1\. 定義 ARR、pipeline、active usage、customer health。  
  2\. 描述 models 間 relationships。  
  3\. 統一重複問題的 metric logic。  
  4\. 建立在 clean grains、models 與 documentation 上。  
\- \*\*獨特特徵\*\*：Semantic layer 不是修補糟糕 data modeling 的魔法。底層模型混亂時，上層語義也會漂移。  
\- \*\*影子證據\*\*：文章直接指出：先修 foundations，再用 semantic layer 固化最重要 metrics。  
\- \*\*連結\*\*：↔ \[\[D3\]\], \[\[D5\]\], \[\[D6\]\] ⟨S1⟩

\#\#\# D5：Workspace Guides 把 Business Rules 版本化  
\- \*\*操作手法\*\*：  
  1\. 使用 plain language 記錄 company processes 與 reporting conventions。  
  2\. 說明 weekly GTM pipeline 定義。  
  3\. 指定 canonical dashboards。  
  4\. 記錄 deployment-type usage 解釋與 customer-health filters。  
  5\. 定義何時升級到 data team 驗證。  
  6\. 將 guides 存在 GitHub repo，直接同步到 Hex。  
\- \*\*獨特特徵\*\*：不強迫所有 context 塞進 column description；使用可 review、version、sync 的文件層。  
\- \*\*影子證據\*\*：Guides 被描述為 data agent 的 skills。  
\- \*\*連結\*\*：↔ \[\[D3\]\], \[\[D4\]\], \[\[D6\]\] ⟨G1⟩

\#\#\# D6：Endorsement 建立資料信任訊號  
\- \*\*操作手法\*\*：  
  1\. 標記 authoritative dashboard 或 asset。  
  2\. Agent 優先使用 endorsed source 與其 logic。  
  3\. 只有 data team 可以 endorse。  
  4\. Endorsed dashboard 變更前需 data-team review。  
\- \*\*獨特特徵\*\*：Trust 不是由熱門度或搜尋相似度推斷，而是由明確 ownership 與 review 建立。  
\- \*\*影子證據\*\*：文章警告「如果所有東西都被 endorse，訊號就失去價值」。  
\- \*\*連結\*\*：→ \[\[G1\]\], \[\[E1\]\]

\#\#\# D7：Conversation-Driven Context Feedback Loop  
\- \*\*操作手法\*\*：  
  1\. 使用者從 Hex、Slack、CLI、MCP、Fleet 提問。  
  2\. Agent 使用 dbt、semantic model、guides、endorsements、dashboards、GitHub。  
  3\. Observability 找出 gaps、warnings、repeated topics。  
  4\. Data team review patterns。  
  5\. 更新 models、definitions、guides、metrics、endorsements 或 dashboards。  
  6\. Agent responses 改善。  
\- \*\*獨特特徵\*\*：Agent conversation 不只是一個查詢；它也是組織缺少哪些 context 的 telemetry。  
\- \*\*影子證據\*\*：團隊下一步是加入 evals，讓 context change 像 software change 一樣可測試後發布。  
\- \*\*連結\*\*：→ \[\[R1\]\], \[\[P1\]\], \[\[E1\]\]

\#\#\# T1：Agent Context Layer 矩陣  
\- \*\*用途\*\*：為每種問題配置正確的 context authority。  
\- \*\*結構內容\*\*：  
  | Layer | 解決問題 | Owner | Failure Glitch |  
  |---|---|---|---|  
  | dbt models | 資料 grain 與 transformation | Data Engineering | 技術正確、語意錯誤 |  
  | Column/Table definitions | 使用方式與 edge cases | Data Team | 錯誤 filter |  
  | Semantic model | Metric consistency | Analytics | ARR 等定義漂移 |  
  | Workspace guides | Business rules/process | Domain \+ Data | 缺少情境 |  
  | Endorsements | Source trust | Data Team | Agent 選錯 asset |  
  | GitHub repo | Implementation lineage | Engineering | 無法追溯邏輯 |  
  | Observability | Gap telemetry | Platform/Data | 問題重複發生 |  
  | Evals | Change assurance | Data \+ Domain | 改 context 後退化 |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[P1\]\], \[\[G1\]\]

\#\#\# S1：Make Context Explicit  
\- \*\*策略邏輯\*\*：不要把 data agent 當 SQL generator。先把資料意義、metric logic、business rules、trust signal 與 escalation criteria顯式化。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：把 dbt、semantic model、guides、endorsements 與 GitHub context 組成一致系統。  
  \- \*\*環境/競對參照\*\*：只給 database credentials 的 agent 會靠名稱相似度與模型先驗猜測。  
\- \*\*反面教材 (Pre-mortem)\*\*：追求 100% self-service，取消 data-team validation，導致高影響決策由未驗證答案驅動。  
\- \*\*理論基礎\*\*：← \[\[D1\]\], \[\[D2\]\], \[\[D3\]\], \[\[D4\]\], \[\[D5\]\], \[\[D6\]\], \[\[D7\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[R1\]\], \[\[G1\]\]

\#\#\# R1：Agent-First Data Stack 路線圖  
\- \*\*總體目標\*\*：讓大多數常見問題可自助完成，並將 data team 轉向模型、context、guardrails 與高槓桿分析。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Question Inventory\*\*：收集最高頻與最高價值問題。  
  \- \*\*Phase 2 Foundation Repair\*\*：清理 grains、models、transformations 與 definitions。  
  \- \*\*Phase 3 Semantic Core\*\*：固化 ARR、pipeline、usage、health。  
  \- \*\*Phase 4 Context Guides\*\*：將流程與 business rules 寫入 versioned repo。  
  \- \*\*Phase 5 Trust Controls\*\*：引入 endorsements、read-only roles、agent access approvals。  
  \- \*\*Phase 6 Multi-Surface Access\*\*：UI、Slack、CLI、MCP。  
  \- \*\*Phase 7 Feedback & Evals\*\*：從 conversations 建立 gaps，對 context change 跑 regression eval。  
\- \*\*系統風險 (Glitches)\*\*：過早平台 cutover、context owner 不清、全部 asset 都 endorse、usage 上升但 decision quality 未量測。  
\- \*\*連結\*\*：→ \[\[G1\]\]

\#\#\# G1：Data Agent Trust Protocol  
\- \*\*核心協議 (Protocol)\*\*：Agent answer 必須可回答三個問題：用了哪個 source、用了哪個 metric definition、何時需要人工驗證。  
\- \*\*具體條款/機制\*\*：  
  \- \*\*Source Authority\*\*：高影響 metric 必須使用 endorsed asset。  
  \- \*\*Definition Ownership\*\*：每個 metric 有 owner、version 與 review date。  
  \- \*\*Role Control\*\*：read-only 與 agent access 分開；權限透過 IT self-service 審核。  
  \- \*\*Escalation\*\*：財務、合約、customer health 與重大營運決策需 data-team validation。  
  \- \*\*Change Review\*\*：endorsed dashboard、semantic model 與 guide 變更需 review。  
  \- \*\*Traceability\*\*：保存 query、sources、SQL、definitions、warnings 與 user feedback。  
\- \*\*決策流程\*\*：提問 → intent/impact classification → retrieve endorsed context → generate analysis → confidence/warning → human escalation or delivery → feedback loop。  
\- \*\*違規後果\*\*：撤銷 endorsement、停用 agent route、回滾 context version、重跑受影響決策。  
\- \*\*連結\*\*：← \[\[R1\]\], → \[\[S1\]\], \[\[P1\]\]

\#\#\# P1：建立可治理的 Data Agent  
\- \*\*場景 (Scenario)\*\*：讓 GTM、Product、Sales 與 Customer Engineering 自助分析公司資料。  
\- \*\*價值 (Value)\*\*：降低 one-off queue，讓資料團隊投入模型與跨部門高價值問題。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 匯出前 100 個高頻 business questions。  
  2\. 對應 canonical models、metrics、dashboards 與 owners。  
  3\. 在 dbt 補齊 grain、allowed values、default filters、edge cases。  
  4\. 建立 semantic model。  
  5\. 用 GitHub 管理 workspace guides。  
  6\. 僅由 data team 設定 endorsements。  
  7\. 提供 Slack/UI/CLI/MCP 入口，但共用相同 context。  
  8\. Trace 每次 retrieval、SQL、warnings、answer 與 feedback。  
  9\. 將重複 failure 轉成 context patch 與 eval case。  
  10\. 先覆蓋約 \*\*80%\*\*高頻問題，再處理 long tail。  
\- \*\*工具集 (Toolset)\*\*：  
  \- Hex、dbt、GitHub、Slack、MCP、LangSmith/Fleet、semantic layer、evaluation dataset。  
\- \*\*影子技巧\*\*：不要只追蹤 answer accuracy。追蹤「agent 選了哪個 source」與「使用者是否把答案用於決策」。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[G1\]\]

\#\#\# E1：Context Is the Product 法則  
\- \*\*法則內容\*\*：Data agent 的可靠性來自資料周圍的 context 與 trust system，不是來自 SQL 生成能力本身。  
\- \*\*推論/啟示\*\*：當 agent 承接更多查詢，data team 不會消失；其工作會從逐題回答，轉為設計 definitions、semantics、guides、endorsements、evals 與治理。  
\- \*\*支撐證據\*\*：← \[\[N1\]\], \[\[D1\]\], \[\[D3\]\], \[\[D4\]\], \[\[D5\]\], \[\[D6\]\], \[\[D7\]\], \[\[T1\]\], \[\[G1\]\]
