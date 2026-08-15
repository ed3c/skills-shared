---
id: "sequoia:cyera-oasis-agent-security"
title: "Cyera and Oasis: Stronger Together"
source_name: "Sequoia Capital"
source_type: "venture-analysis"
source_url: "https://sequoiacap.com/article/cyera-and-oasis-stronger-together/"
canonical_url: "https://sequoiacap.com/article/cyera-and-oasis-stronger-together"
published_at: "2026-07-28"
monetization_score: 100
monetization_modes: "Agent identity security graph audit; non-human IAM playbook; data and identity control plane; CISO workshop."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["security-governance", "non-human-identity"]
mapping_targets: ["code", "data", "trajectory"]
github_path: "ai-content-note/notes/security-governance/2026-07-28-cyera-oasis-agent-security-graph.md"
legacy_google_doc_id: "1gBSQUUivGyb1Sgc-V6BoXGYLUemr8QlALjjjWoikEtI"
legacy_google_doc_url: "https://docs.google.com/document/d/1gBSQUUivGyb1Sgc-V6BoXGYLUemr8QlALjjjWoikEtI/edit"
citation_mapping_status: pending
---

\#\#\# N1：AI Security 的兩半拼在一起：Data × Identity × Agent  
\- \*\*核心衝突\*\*：上一代 enterprise security 把 human identity 與 data security 分開治理；Agentic AI 讓非人類 identity 直接讀寫敏感資料，傳統邊界失效。  
\- \*\*關鍵人物/實體\*\*：Cyera vs Oasis Security；Yotam Segev、Tamar Bar-Ilan、Yonatan Itai vs Danny Brickman、Amit Zimerman；enterprise CISO。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- Oasis 在成立後 \*\*under three years\*\* 建立出 enterprises 使用的 non-human identity / agentic access management 產品。  
  \- Sequoia 指出每個 AI agent 都會建立或使用 API keys、service accounts、OAuth tokens、agent-to-agent credentials，具有 real permissions 與 real blast radius。  
  \- 兩家公司從 Series A 起都獲 Sequoia 支持，最終在 \*\*July 28, 2026\*\* 宣布結合。  
\- \*\*劇情轉折\*\*：Cyera 從「敏感資料在哪裡、誰能碰」切入；Oasis 從「非人類 identity 是誰、它能做什麼」切入。Agent 時代把兩條問題鏈接成同一攻擊路徑。  
\- \*\*生態背景\*\*：AI adoption 把 machine identity 從 niche IAM subcategory 推到 board-level CISO conversation。  
\- \*\*連結\*\*：→ \[\[D1\]\], \[\[D2\]\], → \[\[T1\]\], \[\[G1\]\], ≈ \[\[E1\]\]

\#\#\# Q1：你的 Agent 是 User、Service Account，還是新的 Security Principal？  
\- \*\*核心疑問 (The Doubt)\*\*：如果 Agent 能自主選 tool、取得 OAuth token、跨 SaaS 執行操作，傳統 IAM 是否還能用「人 vs service account」二分法描述它？  
\- \*\*現狀反差 (Reality Gap)\*\*：企業已大量導入 Agent，但權限模型往往仍把它當 application integration，而不是具行為、記憶、決策能力的 principal。  
\- \*\*思維實驗 (Simulation)\*\*：一個 Agent 同時拿到 Salesforce OAuth、warehouse service account 與 GitHub token。哪個 team 能回答它「現在正在以誰的名義碰哪一筆 sensitive data」？  
\- \*\*連結\*\*：← \[\[D1\]\], \[\[D2\]\], → \[\[S1\]\]

\#\#\# C1：Agentic Access Management  
\- \*\*定義\*\*：針對 AI agents 與其他 non-human identities 的 access discovery、permission governance、credential control 與 behavioral monitoring。  
\- \*\*演化\*\*：Secrets management → machine identity management → agentic access management。  
\- \*\*本質\*\*：Agent identity 不只是 credential string；它是 credential \+ delegated authority \+ runtime behavior \+ data path。  
\- \*\*結構特徵\*\*：API keys、OAuth tokens、service accounts、agent-to-agent credentials、permission graph、behavior baseline、revocation。  
\- \*\*連結\*\*：→ \[\[D1\]\], \[\[P1\]\], → \[\[E1\]\]

\#\#\# C2：Data–Identity–Agent Security Graph  
\- \*\*定義\*\*：把「Sensitive Data」「Principal」「Agent Runtime」視為同一條 attack path 的三個節點。  
\- \*\*演化\*\*：Data Security Posture Management 與 IAM 原本各自最佳化；Agent 把它們在 runtime 重新耦合。  
\- \*\*本質\*\*：只知道 data sensitivity 不夠；只知道 credential owner 也不夠。必須知道哪個 Agent 透過哪個 identity 對哪份 data 做什麼。  
\- \*\*結構特徵\*\*：data classification、identity mapping、agent session、tool call、permission scope、behavior anomaly。  
\- \*\*連結\*\*：→ \[\[D2\]\], \[\[T1\]\], → \[\[E1\]\]

\#\#\# D1：Oasis — Non-Human Identity 先於 Agent Boom  
\- \*\*操作手法\*\*：Oasis 從 enterprise machine identities 快速成長的趨勢切入，管理 service accounts、API keys、OAuth tokens 與 Agent credentials。  
\- \*\*獨特特徵\*\*：不是把 Agent 當 human user，也不是只管理 static secrets；重點是誰/什麼正在用 credential，以及其 access behavior 是否合理。  
\- \*\*影子證據\*\*：Sequoia 將其定位為 \*\*agentic access management\*\*；公司在 \*\*under three years\*\* 從零走到 enterprise-scale trust。  
\- \*\*連結\*\*：↔ \[\[D2\]\] ⟨S1⟩

\#\#\# D2：Cyera — 從 Data Security 反推 Agent Risk  
\- \*\*操作手法\*\*：Cyera 先回答「敏感資料在哪裡、誰能到達、實際 exposure 是什麼」，再延伸到 Agent 讀寫資料的完整路徑。  
\- \*\*獨特特徵\*\*：Data context 讓 identity risk 有 business impact。相同 token 若只碰 public dataset 與碰 PII / financial records，blast radius 完全不同。  
\- \*\*影子證據\*\*：Sequoia 的核心描述是：Cyera 知道「what is inside the vault」，Oasis 知道「who or what is approaching」。  
\- \*\*連結\*\*：↔ \[\[D1\]\] ⟨S1⟩

\#\#\# D3：GTM Combination 是 Security Platform Strategy，不只是 M\&A  
\- \*\*操作手法\*\*：將 Oasis 的 agentic identity product 接入 Cyera 已建立的 enterprise GTM engine。  
\- \*\*獨特特徵\*\*：安全平台競賽的時間窗短。先形成完整 Data \+ Identity \+ Agent 控制面者，可能成為 enterprise default layer。  
\- \*\*影子證據\*\*：Sequoia 指出 Cyera 的 GTM scale 通常需要 startup \*\*a decade\*\* 才能建立；Oasis 可直接進入既有 enterprise accounts。  
\- \*\*連結\*\*：→ \[\[S2\]\], \[\[E2\]\]

\#\#\# T1：AI Agent Security Control Matrix  
\- \*\*用途\*\*：把 Agent 的 blast radius 拆成可檢查的控制面。  
\- \*\*結構內容\*\*：  
  | 維度 | 問題 | Control |  
  |---|---|---|  
  | Agent | 哪個 runtime / session 在執行？ | Agent identity \+ session provenance |  
  | Credential | 使用哪個 API key/OAuth/service account？ | Credential inventory \+ rotation |  
  | Permission | 能做哪些 action？ | Least privilege \+ scoped delegation |  
  | Data | 正在讀寫什麼敏感資料？ | Classification \+ access path graph |  
  | Behavior | 行為是否偏離 baseline？ | Runtime anomaly detection |  
  | Revocation | 出事能否立即停權？ | Kill switch \+ token revoke |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[P1\]\]

\#\#\# S1：Security Graph Before Agent Scale  
\- \*\*策略邏輯\*\*：Agent rollout 前先建立 Data × Identity × Agent graph；否則每增加一個 tool 都在增加未知 blast radius。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：Cyera \+ Oasis 將 data security 與 non-human identity 合成完整 agent path。  
  \- \*\*環境/競對參照\*\*：傳統 IAM 強於 human access；DSPM 強於 data discovery；secrets managers 強於 storage。Agent security 的空白在跨三者 runtime correlation。  
\- \*\*反面教材 (Pre-mortem)\*\*：Bug 是「credential inventory 完整」卻不知道 credential 正被哪個 autonomous agent 用來碰什麼資料。  
\- \*\*理論基礎\*\*：← \[\[D1\]\], \[\[D2\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[G1\]\]

\#\#\# S2：Platform Completeness as Distribution Moat  
\- \*\*策略邏輯\*\*：Security buyer 偏好降低 vendor fragmentation；Agentic AI 讓 data、identity、agent control 逐漸收斂成 platform category。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：Oasis 技術 category \+ Cyera enterprise distribution。  
  \- \*\*環境/競對參照\*\*：Point solutions 若只解其中一段，會在 procurement 與 incident investigation 被要求和其他 systems 做 correlation。  
\- \*\*反面教材 (Pre-mortem)\*\*：合併後若資料模型與 identity graph 仍是兩套 silo，只得到 bundle，沒有 platform。  
\- \*\*理論基礎\*\*：← \[\[D3\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P2\]\]  
\- \*\*支撐框架\*\*：← \[\[T2\]\]

\#\#\# P1：Agent Access Graph 最小可行實作  
\- \*\*場景 (Scenario)\*\*：企業讓 coding/research/ops agents 存取 SaaS、cloud、databases。  
\- \*\*價值 (Value)\*\*：回答「哪個 Agent 用哪個 credential 對哪份 data 做了什麼」。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. Inventory 所有 API keys、OAuth apps、service accounts、agent-to-agent credentials。  
  2\. 為每個 credential 建立 owner、issuer、scope、expiration、rotation policy。  
  3\. Agent runtime 每次 tool call 寫入 \`agent\_id / session\_id / credential\_id / action / resource / timestamp\`。  
  4\. Data catalog 提供 sensitivity label：public、internal、confidential、regulated。  
  5\. 將 tool call 與 data access join 成 graph edge：Agent → Credential → Resource → Data class。  
  6\. 建立 least-privilege diff：實際使用 permissions vs granted permissions。  
  7\. 當 Agent 第一次存取高敏感資料、跨 region、使用未見 credential 或 action volume 突增時觸發 review。  
  8\. 預先測試一鍵 revoke credential \+ terminate agent session。  
\- \*\*工具集 (Toolset)\*\*：IAM logs、OAuth audit logs、secret inventory、data catalog、SIEM/graph store、agent traces。  
\- \*\*影子技巧\*\*：Security dashboard 不以「credential count」為核心，而以「reachable sensitive data per agent」排序。  
\- \*\*連結\*\*：← \[\[S1\]\]

\#\#\# P2：Data \+ Identity Platform Integration Test  
\- \*\*場景 (Scenario)\*\*：整合兩套 security products 或內部 control planes。  
\- \*\*價值 (Value)\*\*：驗證是完整 graph，而不是 UI bundle。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 隨機抽取 50 個 Agent sessions。  
  2\. 從 Agent trace 找 credential，再從 identity graph 找 permissions，再從 data graph找實際 touched resources。  
  3\. 要求單一 query 能返回 end-to-end path。  
  4\. 注入 expired token、overprivileged service account、sensitive dataset access 三種情境。  
  5\. 測 alert 是否包含 actor、credential、data sensitivity、blast radius、revocation action。  
  6\. 量測 mean-time-to-explain 與 mean-time-to-revoke。  
\- \*\*工具集 (Toolset)\*\*：graph query、SIEM、identity API、DSPM/data catalog、agent observability。  
\- \*\*影子技巧\*\*：Incident response 的 KPI 不只 MTTD；加入 \*\*MTTE — Mean Time To Explain\*\*。  
\- \*\*連結\*\*：← \[\[S2\]\]

\#\#\# T2：Point Solution vs Agent Security Platform  
\- \*\*用途\*\*：評估產品是否真正覆蓋 Agent attack path。  
\- \*\*結構內容\*\*：  
  | Capability | Point IAM | Data Security | Agent Security Platform |  
  |---|---|---|---|  
  | Human identity | 強 | 弱 | 強 |  
  | Non-human identity | 中 | 弱 | 強 |  
  | Sensitive-data map | 弱 | 強 | 強 |  
  | Agent runtime provenance | 弱 | 弱 | 強 |  
  | End-to-end blast radius | 弱 | 中 | 強 |  
  | Immediate revoke/contain | 中 | 弱 | 強 |  
\- \*\*連結\*\*：→ \[\[S2\]\], \[\[P2\]\]

\#\#\# G1：Agent Credential Governance  
\- \*\*核心協議 (Protocol)\*\*：Agent 不得以「共享 service account」作為永久身份模型。  
\- \*\*具體條款/機制\*\*：  
  \- 條款 1：每個 production Agent 必須有可追溯 principal / session identity。  
  \- 條款 2：Long-lived static keys 降到最低；優先短效 delegated credentials。  
  \- 條款 3：Permission scope 必須與 tool capability 一致，不可因 backend 方便而 grant admin。  
  \- 條款 4：高敏感 data action 必須有 policy gate / approval / extra telemetry。  
  \- 條款 5：所有 Agent credentials 必須支援 immediate revoke。  
\- \*\*決策流程\*\*：Register Agent → map credentials → calculate reachable data → approve scope → monitor → revoke/rotate。  
\- \*\*違規後果\*\*：Incident 無法歸因到特定 Agent；共享 credential 讓 blast radius 與 audit trail 同時失真。  
\- \*\*連結\*\*：← \[\[R1\]\], → \[\[S1\]\]

\#\#\# R1：Enterprise Agent Security Roadmap  
\- \*\*總體目標\*\*：從 secrets inventory 升級成 Agent access control plane。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Inventory\*\*：Agents、credentials、tools、data sources。  
  \- \*\*Phase 2 Graph\*\*：建立 Agent → Identity → Resource → Data 關聯。  
  \- \*\*Phase 3 Least Privilege\*\*：短效 credentials、scoped OAuth、permission pruning。  
  \- \*\*Phase 4 Runtime Detection\*\*：behavior anomaly \+ sensitive-data policy。  
  \- \*\*Phase 5 Automated Containment\*\*：revoke \+ session terminate \+ forensic replay。  
\- \*\*系統風險 (Glitches)\*\*：若只部署 dashboard 而沒有 enforcement API，仍是 observability-only；Patch 是 control plane 必須能改 permission 與終止 session。  
\- \*\*連結\*\*：→ \[\[G1\]\]

\#\#\# E1：Agent Security 的最小單位不是 User，而是「行動路徑」  
\- \*\*法則內容\*\*：安全判斷必須同時知道 Agent、credential、permission、data 與 runtime behavior。  
\- \*\*推論/啟示\*\*：未來 IAM 與 data security 會被 Agent runtime graph 強制融合。  
\- \*\*支撐證據\*\*：← \[\[N1\]\], \[\[D1\]\], \[\[D2\]\], \[\[T1\]\]

\#\#\# E2：完整性可以成為 Enterprise Security 的 Distribution Moat  
\- \*\*法則內容\*\*：當 buyer 面臨新型 Agent risk 時，能把多個控制面合成單一可解釋、可執行平台的 vendor，更有機會成為 default layer。  
\- \*\*推論/啟示\*\*：M\&A 的技術價值不在 SKU 數量，而在是否能形成一條 end-to-end security graph。  
\- \*\*支撐證據\*\*：← \[\[D3\]\], \[\[S2\]\], \[\[T2\]\]
