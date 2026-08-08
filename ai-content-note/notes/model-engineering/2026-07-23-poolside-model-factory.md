---
id: "latent-space:poolside-model-factory"
title: "Inside the Model Factory — Eiso Kant, Poolside AI"
source_name: "Latent Space"
source_type: "podcast-transcript"
source_url: "https://www.latent.space/p/poolside"
canonical_url: "https://www.latent.space/p/poolside"
published_at: "2026-07-23"
monetization_score: 100
monetization_modes: "Model-factory operating system; training preflight audit; experiment registry blueprint; model-harness co-design consulting."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["model-engineering", "training-operations"]
mapping_targets: ["code", "llm-model", "data", "trajectory"]
github_path: "ai-content-note/notes/model-engineering/2026-07-23-poolside-model-factory.md"
legacy_google_doc_id: "1UDv-nNjL9aA_ThDsDy1qRKxwaJuE18jXwGPQlyfsTtA"
legacy_google_doc_url: "https://docs.google.com/document/d/1UDv-nNjL9aA_ThDsDy1qRKxwaJuE18jXwGPQlyfsTtA/edit"
citation_mapping_status: pending
---

\#\#\# N1：Model Factory 的核心不是一次訓練，而是實驗吞吐量  
\- \*\*核心衝突\*\*：市場把 frontier model 視為一次大型 training run；Poolside 把競爭力定義成持續產生、篩選、合併數千個實驗的工廠系統。  
\- \*\*關鍵人物/實體\*\*：Eiso Kant、Poolside AI 與小型研究團隊 vs 依賴明星研究者、半年週期與單一大賭注的模型開發模式。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- 節目發布：\*\*2026-07-23\*\*。  
  \- Laguna S：\*\*118B parameters\*\* 的 Mixture-of-Experts，約 \*\*8B active parameters per token\*\*。  
  \- Context length：\*\*1 million tokens\*\*。  
  \- 每月執行 \*\*10,000–20,000 experiments\*\*。  
  \- 核心研究人員少於 \*\*70\*\*。  
  \- Model cycle 從約 \*\*6 months\*\* 壓縮到 \*\*5–8 weeks\*\*。  
  \- Eiso 表示約 \*\*90%\*\* 工作是 engineering。  
  \- 約 \*\*95%\*\* model-building improvements 來自 data 或 compute efficiency。  
  \- 公司完成 \*\*US$500 million\*\* 融資。  
  \- 早期投入 \*\*US$12 million\*\* 的訓練曾失敗。  
\- \*\*劇情轉折\*\*：早期大額失敗迫使團隊停止迷信單次 scale。Poolside 轉向 experiment factory：小實驗、嚴格測量、自動化基礎設施、資料與 compute efficiency、短週期迭代。模型本身變成工廠的輸出，不是唯一資產。  
\- \*\*生態背景\*\*：Frontier labs 面臨 GPU 排程、資料品質、eval leakage、distributed training failure 與研究結論無法重現。單次成功可產生新聞，但不能穩定產生下一代模型。  
\- \*\*連結\*\*：→ \[\[D1\]\]–\[\[D10\]\], → \[\[G1\]\], ≈ \[\[N2：Toyota Production System 的小批量持續改善\]\]

\#\#\# Q1：模型公司的護城河是 checkpoint，還是製造 checkpoint 的作業系統？  
\- \*\*核心疑問 (The Doubt)\*\*：若 competitor 能取得相近 compute 與公開架構，差異是否主要來自 experiment velocity、failure memory、data flywheel 與 harness？  
\- \*\*現狀反差 (Reality Gap)\*\*：外界用 parameter count 比模型；內部真正的決策依賴每月 10,000–20,000 次實驗如何被追蹤、淘汰與合併。  
\- \*\*思維實驗 (Simulation)\*\*：兩家公司每季 compute 相同。一家做三次大型 run；另一家做一萬次小型因果實驗並只把通過門檻的變更送入大 run。十二個月後，誰更容易持續進步？  
\- \*\*連結\*\*：← \[\[D2\]\], \[\[D4\]\], → \[\[S1\]\]

\#\#\# C1：Model Factory  
\- \*\*定義\*\*：將模型研發編譯成資料、compute、experiments、evals、training、deployment 與 feedback 的持續生產系統。  
\- \*\*演化\*\*：research project → training platform → high-throughput model factory。  
\- \*\*本質\*\*：把不可預測的研究轉為統計可管理的 portfolio。單一實驗可以失敗，工廠必須從失敗中提取可重用訊號。  
\- \*\*結構特徵\*\*：experiment registry、dataset lineage、compute scheduler、automated eval、failure taxonomy、checkpoint promotion、harness feedback。  
\- \*\*連結\*\*：→ \[\[D2\]\], \[\[D3\]\], \[\[E1\]\]

\#\#\# D1：Laguna S 的稀疏模型配置  
\- \*\*操作手法\*\*：採用 Mixture-of-Experts，使總參數規模達 \*\*118B\*\*，每 token 約啟用 \*\*8B\*\*。  
\- \*\*獨特特徵\*\*：以稀疏 activation 在能力與 serving cost 間取平衡。  
\- \*\*影子證據\*\*：\*\*118B total / 8B active per token\*\* 不可縮寫成「百億級 MoE」。  
\- \*\*連結\*\*：↔ \[\[D2\]\], ⟨S2⟩

\#\#\# D2：每月 10,000–20,000 次實驗  
\- \*\*操作手法\*\*：把架構、資料 mixture、optimizer、curriculum、tokenization、eval 與 harness 改動拆成大量小實驗。  
\- \*\*獨特特徵\*\*：研究吞吐量遠高於核心研究人數，表示 automation 與 standardized experiment contract 是必要條件。  
\- \*\*影子證據\*\*：每月 \*\*10,000–20,000\*\*；核心研究人員 \*\*\<70\*\*。  
\- \*\*連結\*\*：↔ \[\[D3\]\], \[\[D4\]\], → \[\[P1\]\]

\#\#\# D3：模型週期從六個月降至五到八週  
\- \*\*操作手法\*\*：縮短 data preparation、infrastructure validation、training、eval 與 decision loop。  
\- \*\*獨特特徵\*\*：速度提升不是只靠更多 GPU，而是提前淘汰錯誤方向、重用 infra 與自動化 launch readiness。  
\- \*\*影子證據\*\*：由約 \*\*6 months\*\* 降為 \*\*5–8 weeks\*\*。  
\- \*\*連結\*\*：↔ \[\[D2\]\], \[\[D4\]\], → \[\[R1\]\]

\#\#\# D4：90% Engineering 的反直覺比例  
\- \*\*操作手法\*\*：將研究想法轉成穩定資料管線、分散式訓練、觀測、回復、eval 與 deployment。  
\- \*\*獨特特徵\*\*：模型研究的主要工作不是提出新名稱，而是讓因果實驗可信且可重跑。  
\- \*\*影子證據\*\*：Eiso 的估計是約 \*\*90% engineering\*\*。  
\- \*\*連結\*\*：↔ \[\[D3\]\], \[\[D5\]\], ⟨S1⟩

\#\#\# D5：95% 改善來自 Data 或 Compute Efficiency  
\- \*\*操作手法\*\*：改善資料選擇、合成、品質、curriculum、利用率、kernel、parallelism 與 training stability。  
\- \*\*獨特特徵\*\*：反駁「突破主要來自全新 architecture」的公開敘事。  
\- \*\*影子證據\*\*：約 \*\*95%\*\* model-building improvements 由 data 或 compute efficiency 驅動。  
\- \*\*連結\*\*：↔ \[\[D4\]\], \[\[D6\]\], → \[\[T1\]\]

\#\#\# D6：US$12M 失敗訓練的組織記憶  
\- \*\*操作手法\*\*：早期投入 \*\*US$12 million\*\* 的 run 失敗後，團隊把 root cause、preflight checks、stage gates 與 rollback 編入後續系統。  
\- \*\*獨特特徵\*\*：大失敗不是品牌故事的雜訊，而是 model factory governance 的起點。  
\- \*\*影子證據\*\*：金額 \*\*US$12 million\*\* 必須原樣保留。  
\- \*\*連結\*\*：↔ \[\[D7\]\], → \[\[G1\]\], \[\[P2\]\]

\#\#\# D7：US$500M 融資與資本紀律  
\- \*\*操作手法\*\*：用大額資本取得 compute、人才與長期 runway，同時以短週期實驗降低單次 capital-at-risk。  
\- \*\*獨特特徵\*\*：融資規模很大，但 operating model 強調小批量驗證，而不是用資金掩蓋研究不確定性。  
\- \*\*影子證據\*\*：融資額 \*\*US$500 million\*\*。  
\- \*\*連結\*\*：↔ \[\[D6\]\], → \[\[G2\]\]

\#\#\# D8：一百萬 token 的 Coding Context  
\- \*\*操作手法\*\*：讓 Laguna S 處理 repository、長期任務與大型 code context。  
\- \*\*獨特特徵\*\*：長 context 對 coding model 的價值取決於 retrieval、compaction、tool state 與 edit verification，不是只看最大輸入長度。  
\- \*\*影子證據\*\*：Context window 為 \*\*1 million tokens\*\*。  
\- \*\*連結\*\*：↔ \[\[D1\]\], \[\[D9\]\], → \[\[P3\]\]

\#\#\# D9：Model 與 Harness 的共同最佳化  
\- \*\*操作手法\*\*：把模型訓練與 coding-agent harness 一起評估；工具、context、execution、verification 會回饋到資料與 post-training。  
\- \*\*獨特特徵\*\*：Model benchmark 高分不保證 Agent 完成 repository task。  
\- \*\*影子證據\*\*：訪談反覆區分 model capability 與 product/harness capability。  
\- \*\*連結\*\*：↔ \[\[D8\]\], \[\[D10\]\], ⟨S2⟩

\#\#\# D10：對 MCP 的批判性定位  
\- \*\*操作手法\*\*：把 MCP 視為工具整合協議，而非自動解決 context quality、tool semantics 或 long-running state 的萬用層。  
\- \*\*獨特特徵\*\*：連接成功不等於 Agent 知道何時、為何、以何種權限使用工具。  
\- \*\*影子證據\*\*：完整訪談將 MCP 放入 model–harness–tool 的更大系統，而非單獨當作 intelligence layer。  
\- \*\*連結\*\*：↔ \[\[D9\]\], → \[\[G3\]\], \[\[P4\]\]

\#\#\# S1：Experiment Throughput 優先  
\- \*\*策略邏輯\*\*：最大化每單位時間內可被可信評估的假設數，而不是最大化同時啟動的 jobs。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：\<70 researchers 支撐 10,000–20,000 experiments/month。  
  \- \*\*環境/競對參照\*\*：沒有 lineage 與自動 eval 的高 job count 只會製造不可比較結果。  
\- \*\*反面教材 (Pre-mortem)\*\*：實驗數量上升，但 config 漂移、資料重疊、選擇性報告與 false positive 同步增加。  
\- \*\*理論基礎\*\*：← \[\[D2\]\]–\[\[D6\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\], \[\[P2\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[R1\]\], \[\[G1\]\]

\#\#\# S2：Model–Harness Co-Design  
\- \*\*策略邏輯\*\*：以 end-to-end coding task 的成功率，反向決定 pretraining、post-training、context 與 tool design。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：Laguna S 的能力需透過 coding Agent 產品與工具鏈釋放。  
  \- \*\*環境/競對參照\*\*：只優化 isolated benchmark 容易產生會答題、不會完成軟體工作的模型。  
\- \*\*反面教材 (Pre-mortem)\*\*：模型 context 擴到 1M，但 harness 不做 compaction 與 file relevance，成本增加而成功率下降。  
\- \*\*理論基礎\*\*：← \[\[D1\]\], \[\[D8\]\], \[\[D9\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P3\]\], \[\[P4\]\]  
\- \*\*支撐框架\*\*：← \[\[G3\]\]

\#\#\# T1：Model Factory 控制面  
\- \*\*用途\*\*：把模型研發的每層輸入、輸出與 gate 明確化。  
\- \*\*結構內容\*\*：  
  | Layer | 核心輸出 | Promotion Gate |  
  |---|---|---|  
  | Data | versioned mixture、quality report | contamination、license、utility |  
  | Compute | reproducible runtime | utilization、stability、cost |  
  | Experiment | comparable delta | hypothesis、control、run count |  
  | Training | checkpoint \+ telemetry | loss health、failure recovery |  
  | Evaluation | capability/safety slices | statistical significance |  
  | Harness | end-to-end artifacts | task success、side-effect safety |  
  | Deployment | served model | canary、rollback、cost ceiling |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[S2\]\], \[\[P1\]\]

\#\#\# R1：模型工廠建立路線圖  
\- \*\*總體目標\*\*：從手工作坊升級為高吞吐、低相關失敗、可追溯的模型製造系統。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Experiment Contract\*\*：每個實驗固定 hypothesis、base、delta、dataset、budget、eval。  
  \- \*\*Phase 2 Automated Small Runs\*\*：自動排程、監控、終止與報告。  
  \- \*\*Phase 3 Data/Compute Efficiency Loop\*\*：把改善拆成可歸因指標。  
  \- \*\*Phase 4 Checkpoint Promotion\*\*：只合併跨多次重跑與多 slice 成立的變更。  
  \- \*\*Phase 5 Full Training Preflight\*\*：小規模 scaling law、fault injection、I/O 與 recovery rehearsal。  
  \- \*\*Phase 6 Model–Harness Replay\*\*：用真實 coding tasks 驗證 serving checkpoint。  
\- \*\*系統風險 (Glitches)\*\*：experiment p-hacking、shared dataset leakage、metric gaming、silent hardware fault、researcher knowledge 不進系統、昂貴 run 無法回復。  
\- \*\*連結\*\*：→ \[\[G1\]\], \[\[G2\]\], \[\[G3\]\]

\#\#\# G1：High-Cost Training Launch Protocol  
\- \*\*核心協議 (Protocol)\*\*：大型 run 必須像 production change 一樣具備 preflight、owner、abort condition 與 recovery plan。  
\- \*\*具體條款/機制\*\*：  
  \- 驗證 data manifest、checksum、token counts。  
  \- 進行小規模 loss/throughput scaling rehearsal。  
  \- 模擬 node、network、storage failure。  
  \- 設定 loss spike、NaN、utilization 與 checkpoint abort thresholds。  
  \- 建立多區 checkpoint 與 restart drill。  
\- \*\*決策流程\*\*：technical readiness → independent review → capital-at-risk sign-off → staged launch → continuous gate。  
\- \*\*違規後果\*\*：缺少 recovery rehearsal 的 run 不得獲得完整 compute allocation。  
\- \*\*連結\*\*：← \[\[D6\]\], \[\[R1\]\], → \[\[S1\]\]

\#\#\# G2：Experiment Portfolio Governance  
\- \*\*核心協議 (Protocol)\*\*：研究資源配置依 evidence strength 與 option value，而非 seniority 或敘事吸引力。  
\- \*\*具體條款/機制\*\*：  
  \- 所有 negative result 入 registry。  
  \- 同一 hypothesis 需 independent rerun。  
  \- 重大變更不得只依單一 benchmark promotion。  
  \- 記錄 compute spend 與 expected information gain。  
\- \*\*決策流程\*\*：proposal → cheap falsification → replicated evidence → scale decision。  
\- \*\*違規後果\*\*：未預註冊 success criteria 的結果只能列為 exploratory。  
\- \*\*連結\*\*：← \[\[D2\]\], \[\[D7\]\], \[\[R1\]\], → \[\[S1\]\]

\#\#\# G3：Tool Protocol 不等於 Tool Governance  
\- \*\*核心協議 (Protocol)\*\*：MCP 或其他工具協議只負責 transport/schema；權限、context、intent、verification 與 audit 另行治理。  
\- \*\*具體條款/機制\*\*：  
  \- 每個 tool 定義最小權限與 side-effect class。  
  \- Tool response 標記 freshness、source 與 confidence。  
  \- Mutation 需要 preview、approval 或 idempotency。  
  \- Harness 記錄模型為何選用工具。  
\- \*\*決策流程\*\*：tool discovery → policy check → context injection → execution → artifact verification。  
\- \*\*違規後果\*\*：只完成連接、沒有 verification contract 的工具不得進入 autonomous loop。  
\- \*\*連結\*\*：← \[\[D10\]\], \[\[R1\]\], → \[\[S2\]\]

\#\#\# P1：十萬級實驗 Registry  
\- \*\*場景 (Scenario)\*\*：模型團隊需要管理每月 10,000–20,000 次實驗。  
\- \*\*價值 (Value)\*\*：防止結果丟失、重複工作與無法歸因。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 為每次 run 產生 immutable experiment ID。  
  2\. 記錄 code commit、data manifest、container、hardware、seed、budget。  
  3\. 將 hypothesis 與 success criteria 存入 manifest。  
  4\. 自動上傳 telemetry、checkpoint、eval 與 failure reason。  
  5\. 建立 lineage graph，顯示每個 promoted change 的祖先。  
  6\. 對重複 hypothesis 與 dataset overlap 自動告警。  
\- \*\*工具集 (Toolset)\*\*：MLflow/W\&B、Git、artifact store、data catalog、scheduler、SQL warehouse。  
\- \*\*影子技巧\*\*：將「停止原因」視為一等欄位，避免失敗 run 只留下 incomplete。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[D2\]\]

\#\#\# P2：US$12M Failure Preflight Harness  
\- \*\*場景 (Scenario)\*\*：準備高成本 distributed training。  
\- \*\*價值 (Value)\*\*：在花費主要 compute 前捕捉 configuration、data、network 與 checkpoint Bug。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 用 1/1000 規模完成 end-to-end dry run。  
  2\. 驗證 data sharding 與 sample uniqueness。  
  3\. 注入 worker crash、network partition、storage timeout。  
  4\. 從 checkpoint 重新啟動並比對 loss continuity。  
  5\. 執行 24 小時 soak test。  
  6\. 由非原作者 reviewer 檢查 launch manifest。  
\- \*\*工具集 (Toolset)\*\*：Kubernetes/Slurm、fault injector、checkpoint verifier、telemetry dashboard。  
\- \*\*影子技巧\*\*：preflight 必須使用 production code path，不能另寫一套簡化 script。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[D6\]\], \[\[G1\]\]

\#\#\# P3：One-Million-Token Coding Harness  
\- \*\*場景 (Scenario)\*\*：在大型 repository 使用 Laguna S。  
\- \*\*價值 (Value)\*\*：讓 1M context 成為可控資源，而非一次塞滿所有檔案。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 建立 repository map 與 symbol graph。  
  2\. 先檢索高相關檔案，再分層載入 context。  
  3\. 使用 rolling summary 與 decision log。  
  4\. 每次 edit 後執行 targeted tests。  
  5\. 對長任務保存 checkpoints 與 resumable plan。  
  6\. 計算 context utility：每千 token 帶來的成功率增益。  
\- \*\*工具集 (Toolset)\*\*：code indexer、AST/LSP、test runner、context cache、trace store。  
\- \*\*影子技巧\*\*：保留 rejected hypotheses，避免 compaction 後重複走死路。  
\- \*\*連結\*\*：← \[\[S2\]\], \[\[D8\]\], \[\[D9\]\]

\#\#\# P4：MCP Tool Quality Gate  
\- \*\*場景 (Scenario)\*\*：把新的 MCP server 接入 coding Agent。  
\- \*\*價值 (Value)\*\*：阻止 schema 可用但語意不可靠的工具污染 Agent。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 建立 read-only、reversible、irreversible 分級。  
  2\. 為每個 tool 準備 golden calls 與 malformed inputs。  
  3\. 測試 auth expiry、timeout、partial response 與 stale data。  
  4\. 對 mutation 實作 dry-run 與 idempotency key。  
  5\. 把 tool success 與 task success 分開量測。  
\- \*\*工具集 (Toolset)\*\*：MCP inspector、contract tests、policy engine、sandbox、audit log。  
\- \*\*影子技巧\*\*：Agent 選對工具但輸入錯誤，不能計為 tool integration success。  
\- \*\*連結\*\*：← \[\[S2\]\], \[\[D10\]\], \[\[G3\]\]

\#\#\# E1：模型公司首先是實驗系統公司  
\- \*\*法則內容\*\*：Checkpoint 的持續品質取決於假設吞吐量、可重現性、資料效率與失敗記憶。  
\- \*\*推論/啟示\*\*：可變現產品包括 experiment OS、data lineage、training preflight、model–harness evaluation。  
\- \*\*支撐證據\*\*：← \[\[D2\]\]–\[\[D6\]\], \[\[T1\]\], \[\[R1\]\]

\#\#\# E2：Scale 不能修復因果不清  
\- \*\*法則內容\*\*：當實驗無 control、資料 lineage 不明或 evaluator 污染時，增加 compute 只會更昂貴地重複錯誤。  
\- \*\*推論/啟示\*\*：大型 run 前最值得購買的不是更多 GPU，而是更強的 falsification 與 recovery infrastructure。  
\- \*\*支撐證據\*\*：← \[\[D6\]\], \[\[G1\]\], \[\[G2\]\], \[\[P2\]\]
