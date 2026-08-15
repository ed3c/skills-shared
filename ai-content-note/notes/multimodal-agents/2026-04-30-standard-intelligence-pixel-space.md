---
id: "sequoia:standard-intelligence-pixel-space"
title: "Standard Intelligence: Training General Intelligence in Pixel Space"
source_name: "Sequoia Capital"
source_type: "venture-analysis"
source_url: "https://sequoiacap.com/article/standard-intelligence-training-general-intelligence-in-pixel-space/"
canonical_url: "https://sequoiacap.com/article/standard-intelligence-training-general-intelligence-in-pixel-space"
published_at: "2026-04-30"
monetization_score: 99
monetization_modes: "Video-tokenization audit; petabyte storage blueprint; world-model intervention eval; behavioral-data governance service."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["multimodal-agents", "video-world-models"]
mapping_targets: ["llm-model", "data", "trajectory"]
github_path: "ai-content-note/notes/multimodal-agents/2026-04-30-standard-intelligence-pixel-space.md"
legacy_google_doc_id: "1rZlhpaj5Fe76wVzocmBNh6p2DKZ5n1u7N05MAu2vR58"
legacy_google_doc_url: "https://docs.google.com/document/d/1rZlhpaj5Fe76wVzocmBNh6p2DKZ5n1u7N05MAu2vR58/edit"
citation_mapping_status: pending
---

\#\#\# N1：通用智能的資料入口從文字切換到像素  
\- \*\*核心衝突\*\*：文字與離散 action logs 容易處理，卻只記錄人類活動的一小部分；原始影片包含規模龐大的行為資料，但成本、token density 與儲存需求曾讓它無法成為主訓練介面。  
\- \*\*關鍵人物/實體\*\*：Standard Intelligence 六人團隊 vs 依賴文字、模擬器或昂貴 hyperscaler 儲存的既有路線。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- 發布日期：\*\*2026-04-30\*\*。  
  \- 行為資料集規模：\*\*11 million hours\*\*。  
  \- Video encoder 相較常見方案約 \*\*50× token efficient\*\*。  
  \- 在 \*\*1 million-token context\*\* 內，可表示接近 \*\*2 hours、30 FPS\*\* 的影片。  
  \- \*\*30 PB\*\* 儲存成本低於 \*\*US$500,000\*\*，約為 hyperscaler 方案的 \*\*1/20\*\*。  
  \- 團隊規模：\*\*6 人\*\*；兩位創辦人年齡為 \*\*21\*\* 與 \*\*20\*\*。  
\- \*\*劇情轉折\*\*：團隊沒有先建立更複雜的文字標註系統，而是把 raw pixel stream 壓縮成模型可學習的 token，直接訓練 Foundation Dynamics Model（FDM-1）。資料瓶頸從「缺少標註」轉成「如何高效率編碼、儲存與驗證真實世界行為」。  
\- \*\*生態背景\*\*：網路文字已被大量使用。Robot data、game traces 與模擬環境具體但昂貴。全球影片則包含操作、因果、物理互動與人類策略，卻長期因序列過長而被低估。  
\- \*\*連結\*\*：→ \[\[D1\]\]–\[\[D7\]\], → \[\[G1\]\], ≈ \[\[N2：ImageNet 將視覺資料標準化\]\]

\#\#\# Q1：資料 moat 是否從擁有內容，轉成能否把內容壓成可訓練狀態？  
\- \*\*核心疑問 (The Doubt)\*\*：當公開影片人人可取得，真正稀缺的是資料所有權、encoder、清理管線、action inference，還是 evaluation environment？  
\- \*\*現狀反差 (Reality Gap)\*\*：市場把大資料集視為護城河；本案例顯示 encoding efficiency 與 storage architecture 可直接改變可訓練資料的經濟邊界。  
\- \*\*思維實驗 (Simulation)\*\*：若競爭者擁有相同 11 million hours，但 tokenization 成本高 50×，兩者實際可進行的 experiment count 會差多少？  
\- \*\*連結\*\*：← \[\[D1\]\], \[\[D2\]\], → \[\[S1\]\]

\#\#\# C1：Foundation Dynamics Model  
\- \*\*定義\*\*：從 pixel-space observation 學習環境狀態、行動後果與時間動態的通用模型，而非只預測文字 token。  
\- \*\*演化\*\*：video representation learning → world model → 可接受 action、預測 dynamics 並支援控制的 foundation model。  
\- \*\*本質\*\*：將 perception、temporal compression、action inference 與 rollout prediction 合併到可擴展訓練介面。  
\- \*\*結構特徵\*\*：pixel encoder、latent tokens、action-conditioned dynamics、long context、behavior dataset、interactive evaluation。  
\- \*\*連結\*\*：→ \[\[D3\]\], \[\[D4\]\], \[\[E1\]\]

\#\#\# D1：11 million hours 行為影片資料  
\- \*\*操作手法\*\*：蒐集大規模真實世界影片，聚焦具有可辨識行為、操作與環境回饋的序列。  
\- \*\*獨特特徵\*\*：不是只追求畫面多樣性，而是把影片視為 action-observation trajectory。  
\- \*\*影子證據\*\*：資料規模為 \*\*11 million hours\*\*，不可泛化為「數百萬小時」。  
\- \*\*連結\*\*：↔ \[\[D2\]\], ⟨S1⟩

\#\#\# D2：50× token-efficient video encoder  
\- \*\*操作手法\*\*：使用高壓縮 video encoder，降低每秒影片需要的 token 數。  
\- \*\*獨特特徵\*\*：token efficiency 直接決定 context 長度、training throughput 與推論成本。  
\- \*\*影子證據\*\*：官方宣稱相較常見 encoder 約 \*\*50×\*\* 更有效率。  
\- \*\*連結\*\*：↔ \[\[D1\]\], \[\[D3\]\], → \[\[P1\]\]

\#\#\# D3：1M context 中容納接近兩小時 30 FPS 影片  
\- \*\*操作手法\*\*：把長影片映射到 compact latent sequence，使模型在單一 context 中追蹤長時間行為。  
\- \*\*獨特特徵\*\*：長 context 不再只意味更多文字，而是可持續觀察多步 physical interaction。  
\- \*\*影子證據\*\*：\*\*1 million-token context\*\*、接近 \*\*2 hours\*\*、\*\*30 FPS\*\* 三個參數必須同時保留。  
\- \*\*連結\*\*：↔ \[\[D2\]\], \[\[D4\]\], → \[\[P2\]\]

\#\#\# D4：FDM-1 的 pixel-space training  
\- \*\*操作手法\*\*：直接在 pixel representation 上訓練 Foundation Dynamics Model，而不是先把每個事件轉成人工標註文字。  
\- \*\*獨特特徵\*\*：模型可學習文字難以完整描述的接觸、速度、空間關係與操作時序。  
\- \*\*影子證據\*\*：模型代號為 \*\*FDM-1\*\*。  
\- \*\*連結\*\*：↔ \[\[D3\]\], \[\[D5\]\], ⟨S2⟩

\#\#\# D5：30 PB 低成本儲存架構  
\- \*\*操作手法\*\*：採用自建或 commodity-oriented storage design，避免 hyperscaler 的長期高單價。  
\- \*\*獨特特徵\*\*：把 exabyte-scale 路線的初始資本需求壓低到新創可承受範圍。  
\- \*\*影子證據\*\*：\*\*30 PB\*\* 低於 \*\*US$500,000\*\*，約 \*\*20× cheaper\*\* than hyperscaler storage。  
\- \*\*連結\*\*：↔ \[\[D4\]\], \[\[D6\]\], → \[\[P3\]\]

\#\#\# D6：六人團隊的垂直整合  
\- \*\*操作手法\*\*：小團隊同時處理資料、encoder、storage、model training 與 evaluation。  
\- \*\*獨特特徵\*\*：傳統做法通常需要分散式 data platform、ML infra、research 與 robotics 團隊。  
\- \*\*影子證據\*\*：團隊人數為 \*\*6\*\*。  
\- \*\*連結\*\*：↔ \[\[D5\]\], \[\[D7\]\], ⟨S1⟩

\#\#\# D7：20 與 21 歲創辦人的反常組合  
\- \*\*操作手法\*\*：以高度技術化、低組織負擔的團隊挑戰資本密集型 world-model research。  
\- \*\*獨特特徵\*\*：年齡不是技術證據，但它暴露出工具與基礎設施已讓小團隊進入過去只屬於大型實驗室的區域。  
\- \*\*影子證據\*\*：創辦人年齡為 \*\*20\*\* 與 \*\*21\*\*。  
\- \*\*連結\*\*：↔ \[\[D6\]\], → \[\[Q2：小團隊是否能守住資料治理\]\]

\#\#\# Q2：低成本基礎設施會放大哪一種治理 Glitch？  
\- \*\*核心疑問 (The Doubt)\*\*：當六人團隊能管理 30 PB 行為資料，privacy、consent、copyright、bias 與 harmful-action filtering 是否也能同速擴張？  
\- \*\*現狀反差 (Reality Gap)\*\*：硬體成本下降可量化；資料權利與 downstream behavior risk 不會自動下降。  
\- \*\*思維實驗 (Simulation)\*\*：若模型從公開影片學到危險操作流程，而 dataset 沒有 action-level policy labels，部署時如何阻止 capability leakage？  
\- \*\*連結\*\*：← \[\[D1\]\], \[\[D5\]\], → \[\[G1\]\], \[\[G2\]\]

\#\#\# S1：把 encoding economics 當第一級研究指標  
\- \*\*策略邏輯\*\*：資料規模只有在 tokenization、storage、training throughput 與 experiment velocity 可負擔時才有價值。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：50× token efficiency 與 20× storage savings 同時改寫成本曲線。  
  \- \*\*環境/競對參照\*\*：只宣布 dataset hours，卻不報告有效 token、清理率與可重跑成本，容易形成虛假 moat。  
\- \*\*反面教材 (Pre-mortem)\*\*：資料量巨大，但 encoder 丟失 action-critical detail；storage 便宜，training I/O 成為新瓶頸。  
\- \*\*理論基礎\*\*：← \[\[D1\]\], \[\[D2\]\], \[\[D5\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\], \[\[P3\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[R1\]\]

\#\#\# S2：用互動任務驗證 world model  
\- \*\*策略邏輯\*\*：影片 reconstruction quality 不能證明模型理解 dynamics。必須在 action-conditioned rollout 與 closed-loop control 中測試。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：FDM-1 以 dynamics 為定位。  
  \- \*\*環境/競對參照\*\*：video benchmark 常偏重 perceptual similarity，忽略 intervention correctness。  
\- \*\*反面教材 (Pre-mortem)\*\*：模型生成視覺上合理的未來，但物理因果錯誤，導致 Agent 產生危險 action。  
\- \*\*理論基礎\*\*：← \[\[D3\]\], \[\[D4\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P2\]\]  
\- \*\*支撐框架\*\*：← \[\[G2\]\]

\#\#\# T1：Pixel-Space Intelligence 成本矩陣  
\- \*\*用途\*\*：識別每個 scaling layer 的成本與 failure mode。  
\- \*\*結構內容\*\*：  
  | Layer | 核心指標 | 主要 Glitch |  
  |---|---|---|  
  | Acquisition | usable hours、rights coverage | consent/copyright 缺口 |  
  | Encoding | tokens/sec、action detail retention | 過度壓縮 |  
  | Storage | US$/PB/year、read throughput | I/O bottleneck |  
  | Training | effective tokens/FLOP | 重複或低資訊畫面 |  
  | Context | hours/context、state retention | 長程因果遺失 |  
  | Evaluation | intervention success、safety | 只測畫面相似度 |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[S2\]\], \[\[P1\]\]

\#\#\# R1：行為影片模型落地路線圖  
\- \*\*總體目標\*\*：建立可驗證、權利清楚、可擴展的 pixel-to-action model pipeline。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Rights Inventory\*\*：建立來源、license、consent、地區與刪除權 metadata。  
  \- \*\*Phase 2 Encoder Audit\*\*：量測 action-critical detail、temporal fidelity 與 compression artifacts。  
  \- \*\*Phase 3 Storage/I/O Pilot\*\*：用 1 PB subset 驗證 cost、throughput、failure recovery。  
  \- \*\*Phase 4 FDM Training\*\*：版本化 dataset、encoder、checkpoint 與 compute budget。  
  \- \*\*Phase 5 Interactive Evals\*\*：在可控 simulator 與 real-world proxy 測 intervention。  
  \- \*\*Phase 6 Restricted Deployment\*\*：先部署 low-impact planning 或 prediction，逐步開放 control。  
\- \*\*系統風險 (Glitches)\*\*：資料權利不完整、action inference 錯誤、encoder 不可逆遺失、長 context hallucinated dynamics、危險行為 imitation。  
\- \*\*連結\*\*：→ \[\[G1\]\], \[\[G2\]\]

\#\#\# G1：Behavioral Video Data Governance  
\- \*\*核心協議 (Protocol)\*\*：每一段可訓練影片必須可追溯來源、權利、人物敏感度與允許用途。  
\- \*\*具體條款/機制\*\*：  
  \- 保存 source URL、capture date、license、consent status。  
  \- 對臉部、兒童、住址、醫療與私人場景建立敏感標籤。  
  \- 支援 deletion request 與 checkpoint impact tracking。  
  \- 禁止以「公開可見」等同「可任意訓練」。  
\- \*\*決策流程\*\*：source ingest → rights classifier → sensitive-content review → allow/quarantine/delete。  
\- \*\*違規後果\*\*：來源不明資料不得進入 production dataset；已訓練 checkpoint 需進行 influence assessment。  
\- \*\*連結\*\*：← \[\[R1\]\], → \[\[S1\]\]

\#\#\# G2：World-Model Action Safety Protocol  
\- \*\*核心協議 (Protocol)\*\*：模型的 action capability 必須按可逆性與傷害範圍分級。  
\- \*\*具體條款/機制\*\*：  
  \- 區分 passive prediction、recommendation、simulated action、physical action。  
  \- 高風險 action 必須有 simulator verification 與人類 approval。  
  \- 保存 observation、predicted outcome、selected action 與 actual outcome。  
  \- 對 dangerous imitation 建立拒絕與 red-team suite。  
\- \*\*決策流程\*\*：capability classification → sandbox → intervention eval → staged access。  
\- \*\*違規後果\*\*：未通過 intervention safety 的模型只能用於離線分析。  
\- \*\*連結\*\*：← \[\[R1\]\], → \[\[S2\]\]

\#\#\# P1：Video Encoder Fidelity Audit  
\- \*\*場景 (Scenario)\*\*：團隊要確認 50× compression 沒有抹除行為關鍵訊號。  
\- \*\*價值 (Value)\*\*：避免 token efficiency 以犧牲 action understanding 為代價。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 建立包含細微手勢、快速接觸、遮擋與長延遲因果的測試集。  
  2\. 對原始影片與 latent representation 執行 event detection。  
  3\. 比較 action boundary、object state 與 temporal ordering。  
  4\. 測不同 bitrate、FPS、resolution 與 context 長度。  
  5\. 對失真案例建立不可壓縮白名單。  
\- \*\*工具集 (Toolset)\*\*：video decoder、event annotator、representation probe、latency profiler。  
\- \*\*影子技巧\*\*：不以 reconstruction PSNR 作唯一指標；加入 downstream control success。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[D2\]\]

\#\#\# P2：Action-Conditioned Dynamics Evaluation  
\- \*\*場景 (Scenario)\*\*：驗證 FDM-1 是否真的理解介入後果。  
\- \*\*價值 (Value)\*\*：區分視覺模仿與可用 world model。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 在相同 observation 下提供多個 action。  
  2\. 比較模型 rollout 與 ground-truth transition。  
  3\. 測 unseen object、camera shift 與 delayed consequence。  
  4\. 執行 closed-loop planning，量測 goal completion 與 safety violations。  
  5\. 對高 uncertainty state 強制 abstain。  
\- \*\*工具集 (Toolset)\*\*：simulator、robotics benchmark、counterfactual dataset、trajectory scorer。  
\- \*\*影子技巧\*\*：加入 visually plausible but physically impossible negative examples。  
\- \*\*連結\*\*：← \[\[S2\]\], \[\[D3\]\], \[\[D4\]\]

\#\#\# P3：低成本 Petabyte Storage Blueprint  
\- \*\*場景 (Scenario)\*\*：AI 新創需要保存數十 PB 原始與衍生影片。  
\- \*\*價值 (Value)\*\*：把 hyperscaler 長期成本轉成可預測資本支出。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 將 hot metadata、warm encoded shards、cold raw video 分層。  
  2\. 使用 content-addressed chunks 去重。  
  3\. 建立 erasure coding、scrubbing 與 checksum repair。  
  4\. 量測 training read pattern，預先 staging 熱 shard。  
  5\. 把硬體故障率與重建時間納入有效 US$/PB/year。  
\- \*\*工具集 (Toolset)\*\*：object storage、NVMe cache、ZFS/Ceph、catalog service、checksum monitor。  
\- \*\*影子技巧\*\*：不要只報硬碟採購價；加入電力、網路、維運與資料重建成本。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[D5\]\]

\#\#\# E1：通用行為模型的瓶頸是有效時間，不是原始時數  
\- \*\*法則內容\*\*：影片小時數只有在權利清楚、行為密度足夠、encoder 保留關鍵狀態且可被模型消化時才形成訓練價值。  
\- \*\*推論/啟示\*\*：可變現資產是 verified behavioral tokens，而不是單純 PB 或 hours。  
\- \*\*支撐證據\*\*：← \[\[D1\]\], \[\[D2\]\], \[\[T1\]\], \[\[G1\]\]

\#\#\# E2：壓縮能力會重畫模型規模邊界  
\- \*\*法則內容\*\*：encoder efficiency 與 storage economics 可像 compute scaling 一樣，直接決定哪些研究問題對小團隊可行。  
\- \*\*推論/啟示\*\*：下一代 AI infra 產品可聚焦 video tokenization、rights-aware data catalog、petabyte storage 與 intervention eval。  
\- \*\*支撐證據\*\*：← \[\[D2\]\], \[\[D5\]\], \[\[D6\]\], \[\[P1\]\], \[\[P3\]\]
