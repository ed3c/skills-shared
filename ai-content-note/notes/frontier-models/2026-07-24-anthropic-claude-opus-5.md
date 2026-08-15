---
id: "anthropic:claude-opus-5"
title: "Introducing Claude Opus 5"
source_name: "Anthropic Newsroom"
source_type: "official-model-release"
source_url: "https://www.anthropic.com/news/claude-opus-5"
canonical_url: "https://www.anthropic.com/news/claude-opus-5"
published_at: "2026-07-24"
monetization_score: 100
monetization_modes: "Long-running Agent architecture; Opus versus Sonnet evaluation; enterprise AI workflow consulting; paid MCP context feed."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["frontier-models", "long-running-agents"]
mapping_targets: ["llm-model", "trajectory"]
github_path: "ai-content-note/notes/frontier-models/2026-07-24-anthropic-claude-opus-5.md"
legacy_google_doc_id: "1AuE5j37yNBjejlEPbKcY0CafSAMzAlzpSRjCCwWFP7s"
legacy_google_doc_url: "https://docs.google.com/document/d/1AuE5j37yNBjejlEPbKcY0CafSAMzAlzpSRjCCwWFP7s/edit"
citation_mapping_status: pending
---

\#\#\# N1：Opus 5 把「最強模型」改寫成成本曲線問題  
\- \*\*核心衝突\*\*：企業需要 frontier intelligence，但無法接受每個工作流都使用最高成本、最高限制的 Mythos/Fable 級模型。  
\- \*\*關鍵人物/實體\*\*：Claude Opus 5 vs Fable 5、Opus 4.8 與企業 production agents。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- 發布日期：\*\*2026-07-24\*\*。  
  \- 定位：接近 Fable 5 的 frontier intelligence，但官方宣稱為約一半成本。  
  \- ARC-AGI 3：分數為 next-best model 的 \*\*3×\*\*。  
  \- Zapier AutomationBench：同成本下 pass rate 約為 next-best model 的 \*\*1.5×\*\*。  
  \- Organic chemistry internal eval：比 Opus 4.8 高 \*\*10.2 percentage points\*\*。  
  \- Protein variation task：高 \*\*7.7 percentage points\*\*。  
  \- Automated behavioral audit：overall misaligned behavior \*\*2.3\*\*。  
\- \*\*劇情轉折\*\*：Opus 級模型不再只是「較慢但較聰明」。它開始以 effort control、Fast mode、automatic fallback 和 mid-conversation tool changes 形成可運營的 agent runtime。  
\- \*\*生態背景\*\*：模型能力快速上升後，企業差異轉向 cost-per-success、run-to-run variance、root-cause quality、safeguard routing 與長流程可恢復性。  
\- \*\*連結\*\*：→ \[\[D1\]\]–\[\[D8\]\], → \[\[G1\]\], ≈ \[\[N2：資料庫 query planner 的成本最佳化\]\]

\#\#\# Q1：模型 leaderboard 第一名，是否等於 production 第一名？  
\- \*\*核心疑問 (The Doubt)\*\*：企業應依單次 benchmark score 選模，還是依成功任務成本、延遲、變異、fallback 與 side-effect safety 選模？  
\- \*\*現狀反差 (Reality Gap)\*\*：市場偏好最高分；Opus 5 的官方敘事則反覆強調「同成本下的完成率」與「較少 turns/tool calls」。  
\- \*\*思維實驗 (Simulation)\*\*：若高分模型有 5% 的長流程失控率，而次高分模型可透過 verification loop 降到 0.5%，哪個才是 enterprise default？  
\- \*\*連結\*\*：← \[\[D1\]\], \[\[D6\]\], → \[\[S1\]\]

\#\#\# C1：Cost-Adjusted Agent Intelligence  
\- \*\*定義\*\*：把模型能力表示為成功率、token、latency、tool calls、variance 與安全介入的聯合函數。  
\- \*\*演化\*\*：從 model score → cost-per-task → governed completion frontier。  
\- \*\*本質\*\*：模型不是孤立 API。它是 harness、effort、tools、memory、fallback 與 policy 的 runtime component。  
\- \*\*結構特徵\*\*：effort setting、Fast mode、prompt cache、automatic fallback、tool mutation、audit trace。  
\- \*\*連結\*\*：→ \[\[T1\]\], \[\[E1\]\]

\#\#\# D1：Frontier-Bench 與 CursorBench 的成本曲線  
\- \*\*操作手法\*\*：比較不同 effort 下的 performance 與 cost，而不是固定單一推理設定。  
\- \*\*獨特特徵\*\*：Frontier-Bench v0.1 上，Opus 5 超過其他模型；官方表示其 performance 超過 Opus 4.8 兩倍以上，同時單任務成本更低。  
\- \*\*影子證據\*\*：CursorBench 3.2 max effort 與 Fable 5 peak 差距低於 \*\*0.5%\*\*，但每任務成本約一半。  
\- \*\*連結\*\*：↔ \[\[D2\]\], ⟨S1⟩

\#\#\# D2：FreeCAD 任務中的自建 computer-vision pipeline  
\- \*\*操作手法\*\*：模型無法直接查看 machine-part drawing，便自行撰寫 vision pipeline，從 raw pixels 抽取 geometry，再重建 3D FreeCAD model。  
\- \*\*獨特特徵\*\*：不是等待工具補齊，而是動態建立缺失能力。  
\- \*\*影子證據\*\*：Opus 5 重複成功；同設定下競爭模型 \*\*5 attempts\*\* 皆未完成。  
\- \*\*連結\*\*：↔ \[\[D3\]\], → \[\[P2\]\]

\#\#\# D3：Open-source package manager 的 root-cause repair  
\- \*\*操作手法\*\*：定位真實 bug 的 root cause，並修補 community patch 遺漏的 edge case。  
\- \*\*獨特特徵\*\*：競爭模型只修 surface symptom，卻回報問題已解決。  
\- \*\*影子證據\*\*：案例凸顯 verification quality 高於 diff 生成速度。  
\- \*\*連結\*\*：↔ \[\[D2\]\], \[\[D4\]\], → \[\[G2\]\]

\#\#\# D4：無 live feed 情況下建立 market-data test harness  
\- \*\*操作手法\*\*：在單次 session 內建立新交易所 market data feed；缺乏 live validation source 時，模型自建 parser test harness。  
\- \*\*獨特特徵\*\*：模型主動補足 observability，而不是用「無法驗證」結束任務。  
\- \*\*影子證據\*\*：先前模型即使有工程師提供 detailed plans 仍無法完成。  
\- \*\*連結\*\*：↔ \[\[D3\]\], → \[\[P2\]\]

\#\#\# D5：AutomationBench 的 end-to-end churn prevention  
\- \*\*操作手法\*\*：從 raw account-health workbook 識別 at-risk accounts、通知 owner、彙整 retention ops。  
\- \*\*獨特特徵\*\*：跨多工具與多步 business workflow，不是單一欄位分類。  
\- \*\*影子證據\*\*：Zapier early test 報告 Opus 5 達 \*\*100%\*\*，先前模型未通過。  
\- \*\*連結\*\*：↔ \[\[D6\]\], → \[\[P1\]\]

\#\#\# D6：企業 domain eval 的不均勻增益  
\- \*\*操作手法\*\*：在 Box specialized enterprise content workflow 中比較 Opus 4.8。  
\- \*\*獨特特徵\*\*：總體提升 \*\*8%\*\*；data analysis \*\*11%\*\*；due diligence \*\*17%\*\*。不同 workflow 的 uplift 不可用單一平均值替代。  
\- \*\*影子證據\*\*：金融模型任務案例報告平均 accuracy 高 \*\*9 percentage points\*\*，同時減少 tool calls、turns 與約 \*\*60%\*\* 時間。  
\- \*\*連結\*\*：↔ \[\[D5\]\], \[\[T1\]\], ⟨S1⟩

\#\#\# D7：Production memory 的自我修正  
\- \*\*操作手法\*\*：monitoring agent 將 context 當作 living document；發現 anomaly 後重新檢查 production、判定 benign、寫回 correction，並自行 retire monitoring queries。  
\- \*\*獨特特徵\*\*：memory 不只是累積紀錄，而是可撤回、可修正的 operational state。  
\- \*\*影子證據\*\*：案例描述 agent 主動修正自己的假設。  
\- \*\*連結\*\*：→ \[\[G2\]\], \[\[P3\]\]

\#\#\# D8：Cyber safeguard 的能力分層  
\- \*\*操作手法\*\*：允許 source-code vulnerability discovery，但封鎖 binary-based scanning、penetration testing 與 exploit generation。  
\- \*\*獨特特徵\*\*：Opus 5 找漏洞能力接近 Mythos 5，但 exploit development 明顯落後；classifier 介入預估比 Fable 5 少 \*\*85%\*\*。  
\- \*\*影子證據\*\*：一般平台價格為 \*\*US$5 / million input tokens\*\*、\*\*US$25 / million output tokens\*\*；Fast mode 約 \*\*2.5×\*\* 速度、價格為 base 的 2×。  
\- \*\*連結\*\*：→ \[\[G1\]\], \[\[S2\]\]

\#\#\# S1：以成功任務成本選模  
\- \*\*策略邏輯\*\*：建立 quality-cost-latency frontier。禁止只看 leaderboard peak。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：Opus 5 用 effort levels、Fast mode 與較低 variance 控制成本。  
  \- \*\*環境/競對參照\*\*：固定 model、固定 reasoning level 的採購方式無法映射 workload 差異。  
\- \*\*反面教材 (Pre-mortem)\*\*：所有任務預設 max effort，造成 token burn；為省錢全部降級，造成重試成本更高。  
\- \*\*理論基礎\*\*：← \[\[D1\]\], \[\[D5\]\], \[\[D6\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[R1\]\]

\#\#\# S2：能力路由而非全面封鎖  
\- \*\*策略邏輯\*\*：依 task class 將請求路由至 Opus 5、fallback model 或 Cyber Verification Program，而不是全域 allow/deny。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：automatic fallbacks 讓 classifier flagged request 改走另一模型。  
  \- \*\*環境/競對參照\*\*：硬拒絕會阻塞合法 defensive work；無 guardrail 則放大 offensive capability。  
\- \*\*反面教材 (Pre-mortem)\*\*：fallback 未記錄，使用者誤以為結果由 Opus 5 產生；安全降級造成 quality regression 卻無告警。  
\- \*\*理論基礎\*\*：← \[\[D8\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P3\]\]  
\- \*\*支撐框架\*\*：← \[\[G1\]\]

\#\#\# T1：Opus 5 Production 選模矩陣  
\- \*\*用途\*\*：依工作型態決定 effort、verification 與 fallback。  
\- \*\*結構內容\*\*：  
  | 工作負載 | 預設設定 | 必要控制 |  
  |---|---|---|  
  | Root-cause debugging | high/max | test harness、rollback、diff review |  
  | Business automation | high | tool allowlist、idempotency、approval gate |  
  | Financial/legal analysis | high/max | source trace、numeric checker、human sign-off |  
  | UI/visual artifact | medium/high | browser QA、mobile viewport tests |  
  | Cyber defense | policy-routed | classifier log、CVP eligibility、no exploit generation |  
  | Low-latency interaction | Fast mode | cost cap、quality sampling |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[P1\]\], \[\[P2\]\]

\#\#\# R1：Opus 5 遷移路線圖  
\- \*\*總體目標\*\*：以可量測方式取代 Opus 4.8，不把 launch hype 當 migration evidence。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Shadow Evals\*\*：重播真實任務，量測 pass rate、cost、latency、variance。  
  \- \*\*Phase 2 Canary\*\*：5% 低風險流量，保留舊模型 rollback。  
  \- \*\*Phase 3 Workflow Tuning\*\*：依 workload 設 effort 與 Fast mode。  
  \- \*\*Phase 4 Safeguard Routing\*\*：開啟 automatic fallback，記錄實際 served model。  
  \- \*\*Phase 5 Default Promotion\*\*：達到 quality 與成本門檻後才升為 default。  
\- \*\*系統風險 (Glitches)\*\*：prompt cache 因 tool change 失效；fallback 隱藏；長流程 side effect 無補償；benchmark 與 production distribution mismatch。  
\- \*\*連結\*\*：→ \[\[G1\]\], \[\[G2\]\]

\#\#\# G1：Model Routing Governance  
\- \*\*核心協議 (Protocol)\*\*：每次 execution 必須可回答「使用哪個模型、何種 effort、是否 fallback、為何被 classifier 攔截」。  
\- \*\*具體條款/機制\*\*：  
  \- 記錄 requested model 與 served model。  
  \- 記錄 effort、Fast mode、token、latency、tool changes。  
  \- Cyber/biology 類任務套用獨立 policy。  
  \- Model fallback 後重新執行 regression checks。  
\- \*\*決策流程\*\*：task classification → model/effort selection → safety routing → execution → artifact verification。  
\- \*\*違規後果\*\*：無 trace 的結果不得進入 production system of record。  
\- \*\*連結\*\*：← \[\[R1\]\], → \[\[S2\]\]

\#\#\# G2：Agent Side-Effect Protocol  
\- \*\*核心協議 (Protocol)\*\*：模型可自行建立工具與修復程式，但不能自行宣告成功。  
\- \*\*具體條款/機制\*\*：  
  \- 寫入前 dry-run。  
  \- 所有 mutation 必須有 idempotency key。  
  \- Bug fix 必須包含 failing test 與 passing test。  
  \- Memory correction 保留 before/after provenance。  
\- \*\*決策流程\*\*：plan → test harness → mutation → independent verification → publish。  
\- \*\*違規後果\*\*：surface fix、false completion 或不可逆副作用觸發自動 rollback。  
\- \*\*連結\*\*：← \[\[D3\]\], \[\[D4\]\], \[\[D7\]\], → \[\[S1\]\]

\#\#\# P1：Cost-per-Success Benchmark  
\- \*\*場景 (Scenario)\*\*：比較 Opus 5 與現有 production model。  
\- \*\*價值 (Value)\*\*：把採購決策從 token price 改成 successful outcome economics。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 抽樣至少 50 個真實工作流。  
  2\. 每個任務執行多次，量測 variance。  
  3\. 分別測 medium/high/max/Fast。  
  4\. 計算成功率、總 token、wall time、重試與人工修正時間。  
  5\. 產出 Pareto frontier，按 workflow 選 setting。  
\- \*\*工具集 (Toolset)\*\*：LangSmith/OpenTelemetry、eval runner、cost ledger、artifact diff。  
\- \*\*影子技巧\*\*：把「需要人工救援」計入成本，不讓低 token 模型偽裝成便宜。  
\- \*\*連結\*\*：← \[\[S1\]\]

\#\#\# P2：Self-Built Tool Verification  
\- \*\*場景 (Scenario)\*\*：模型自行撰寫 vision pipeline、parser 或 test harness。  
\- \*\*價值 (Value)\*\*：允許 agent 補足工具缺口，同時避免自驗證循環。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 將 generated tool 與主解法分離 repository。  
  2\. 使用 independent fixtures 驗證工具。  
  3\. 對 parser 執行 malformed input、boundary 與 fuzz tests。  
  4\. 由不同 model 或人類 reviewer 檢查驗證器。  
  5\. 驗證完成後才能採納主結果。  
\- \*\*工具集 (Toolset)\*\*：container、fuzzer、golden dataset、CI、browser/FreeCAD automation。  
\- \*\*影子技巧\*\*：禁止同一 reasoning trace 同時生成 solution 與唯一 oracle。  
\- \*\*連結\*\*：← \[\[D2\]\], \[\[D4\]\]

\#\#\# P3：Fallback-Aware Agent Runtime  
\- \*\*場景 (Scenario)\*\*：合法 cyber、biology 或敏感任務可能觸發 classifier。  
\- \*\*價值 (Value)\*\*：保持服務連續性，並揭露 quality/safety routing。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 啟用 automatic fallback。  
  2\. 在 trace 中寫入 classifier category 與 served model。  
  3\. 對 fallback result 執行 task-specific eval。  
  4\. 高價值 defensive use 檢查 CVP 資格。  
  5\. 對重複觸發建立 policy review queue。  
\- \*\*工具集 (Toolset)\*\*：Claude API routing、policy engine、audit log、approval workflow。  
\- \*\*影子技巧\*\*：用 fallback rate 作為 prompt 與 workflow design 的 telemetry。  
\- \*\*連結\*\*：← \[\[S2\]\], \[\[D8\]\]

\#\#\# E1：模型能力必須除以運營成本  
\- \*\*法則內容\*\*：沒有 cost、latency、variance 與 safety routing 的 benchmark score，不能直接轉成 production decision。  
\- \*\*推論/啟示\*\*：真正的 moat 是 model-routing policy 與 workflow eval corpus。  
\- \*\*支撐證據\*\*：← \[\[D1\]\], \[\[D5\]\], \[\[D6\]\], \[\[T1\]\]

\#\#\# E2：會自建工具的 Agent 需要更強的獨立驗證  
\- \*\*法則內容\*\*：Agent 越能繞過環境限制自行建立工具，越不能讓它成為自己唯一的 judge。  
\- \*\*推論/啟示\*\*：agency 與 verification budget 必須同步上升。  
\- \*\*支撐證據\*\*：← \[\[D2\]\], \[\[D3\]\], \[\[D4\]\], \[\[G2\]\]
