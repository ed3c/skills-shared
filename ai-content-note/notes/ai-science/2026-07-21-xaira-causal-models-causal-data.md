---
id: "latent-space:xaira-x-cell"
title: "Causal Models Need Causal Data — Xaira X-Cell"
source_name: "Latent Space"
source_type: "podcast-transcript"
source_url: "https://www.latent.space/p/xaira"
canonical_url: "https://www.latent.space/p/xaira"
published_at: "2026-07-21"
monetization_score: 100
monetization_modes: "Causal-data flywheel playbook; scientific dataset strategy; active-learning lab architecture; drug-discovery research briefing."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["ai-science", "causal-data"]
mapping_targets: ["llm-model", "data", "trajectory"]
github_path: "ai-content-note/notes/ai-science/2026-07-21-xaira-causal-models-causal-data.md"
legacy_google_doc_id: "1lnYWL6XFqKJTUqSBzUadi2Dc5iAdua7tkR1Ga6HMQOI"
legacy_google_doc_url: "https://docs.google.com/document/d/1lnYWL6XFqKJTUqSBzUadi2Dc5iAdua7tkR1Ga6HMQOI/edit"
citation_mapping_status: pending
---

\#\#\# N1：Scaling Wall 不是參數不夠，是資料沒有新資訊  
\- \*\*核心衝突\*\*：Model training loss 繼續下降，不代表 real-world generalization 還能提升。當 biological dataset 主要描述 correlation，而缺乏 intervention evidence，增加 parameters/compute 只會更精準地記住同一組資訊。  
\- \*\*關鍵人物/實體\*\*：Xaira Therapeutics / Ci Chu / Bo Wang / X-Atlas / X-Cell vs. correlation-heavy virtual-cell datasets。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- Latent Space 記錄：test loss 在約 \*\*1.5B parameters\*\* 後開始 flatline，但 training loss 仍繼續改善。  
  \- \*\*3.1B\*\* model 明顯掉出 scaling trend。  
  \- 團隊加入約 \*\*30x information\*\* 後，parameter/compute scaling 再度有效。  
\- \*\*劇情轉折\*\*：解法不是再堆 GPU，而是建新的 causal data factory：用 CRISPR-based perturbation 產生 intervention data，再訓練 X-Cell。  
\- \*\*生態背景\*\*：生命科學 AI 長期依賴自然觀察資料；自然資料容易揭示 correlation，卻難回答「如果我改變 gene X，cell 會怎樣」。  
\- \*\*連結\*\*：→ \[\[D1.1\]\], \[\[D1.2\]\], \[\[D1.3\]\], \[\[R1\]\]

\#\#\# Q1：如果模型已經吃完 dataset 的資訊量，下一美元應該花在 GPU 還是實驗？  
\- \*\*核心疑問 (The Doubt)\*\*：Scaling law 的 bottleneck 是 compute、parameters，還是 information entropy？  
\- \*\*現狀反差 (Reality Gap)\*\*：training metric 還在變好，容易讓團隊誤判「scale 還有效」；test curve 已經告訴你 information wall 出現。  
\- \*\*思維實驗 (Simulation)\*\*：如果 10x compute 只能讓 training loss 更低，但 intervention prediction 不變；而 30x 新 causal data 讓 test curve重新跟上，資本配置就該從 GPU budget 轉向 experiment budget。  
\- \*\*連結\*\*：← \[\[D1.1\]\], \[\[D1.3\]\]；→ \[\[S1\]\], \[\[T1\]\]

\#\#\# C1：Information-Limited Scaling  
\- \*\*定義\*\*：當資料所含可泛化訊息不足，增加模型容量只會提升 fit，不會提升 out-of-distribution / causal prediction。  
\- \*\*演化\*\*：\`Compute-limited \-\> Parameter-limited \-\> Information-limited\`。不同 phase 的最佳投資完全不同。  
\- \*\*本質\*\*：\`Performance \= f(Model Capacity, Compute, Information Content, Causal Coverage)\`。  
\- \*\*結構特徵\*\*：train/test scaling divergence、dataset intervention density、condition diversity、causal identifiability、real-lab validation。  
\- \*\*連結\*\*：→ \[\[D1.1\]\], \[\[T1\]\], \[\[P1\]\]；→ \[\[E1\]\]

\#\#\# D1.1：1.5B / 3.1B Scaling Wall  
\- \*\*操作手法\*\*：比較不同 model sizes 的 train/test loss curve，而不是只看單一 checkpoint。  
\- \*\*獨特特徵\*\*：test loss 在約 1.5B parameters 後不再改善，但 training loss 仍下降；3.1B model 因此掉出原本的 scaling trend。  
\- \*\*影子證據\*\*：\`1.5B\`、\`3.1B\`、\`\~30x information\`。這三個數字共同指出 bottleneck 從 model capacity 轉成 data information。  
\- \*\*連結\*\*：← \[\[C1\]\]；→ \[\[S1\]\], \[\[P1\]\]

\#\#\# D1.2：CELLxGENE 的巨大規模仍不等於 causal coverage  
\- \*\*操作手法\*\*：CELLxGENE 收集大量 single-cell gene-expression observations，支撐 virtual-cell model ecosystem。  
\- \*\*獨特特徵\*\*：資料極大，但多數是 observational state；高 correlation 讓 upstream/downstream causal direction 難被辨識。  
\- \*\*影子證據\*\*：約 \*\*168M cells\*\*；每個 cell 約 \*\*20K–30K genes\*\*；形成約 \*\*4 trillion-entry matrix\*\*。Bo Wang 的 scGPT 是重要基礎之一。  
\- \*\*連結\*\*：↔ \[\[D1.3\]\]；→ \[\[E1\]\]

\#\#\# D1.3：X-Atlas → X-Cell 的 intervention data factory  
\- \*\*操作手法\*\*：用 CRISPR-based experiments 大規模 perturb genes，觀察 intervention 後的 downstream expression changes；X-Atlas 作 dataset，X-Cell 作 model。  
\- \*\*獨特特徵\*\*：從「看見 cell state」切換到「主動改變 cell，觀察 response」。這使 causal structure 變得可學習。  
\- \*\*影子證據\*\*：episode 描述 experiments 可 parallelize 到 \*\*millions of tests\*\*；團隊從 autoregression 轉向 diffusion；X-Cell 目標包含 generalize 到 real human-cell lab experiments，並超越此前常勝出的 linear baseline。  
\- \*\*連結\*\*：↔ \[\[D1.2\]\]；→ \[\[S1\]\], \[\[R1\]\]

\#\#\# S1：當 Test Curve Flatline，停止買更大的模型  
\- \*\*策略邏輯\*\*：先做 bottleneck diagnosis，再配置資本。如果 train/test divergence 指向 information limit，就把 budget 轉成 active data generation。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：Xaira 建自己的 experimental data pipeline，讓 data generation 與 model development co-design。  
  \- \*\*環境/競對參照\*\*：純 foundation-model 思路傾向把所有問題視為「scale compute」；生命科學卻能透過實驗主動創造新 information。  
\- \*\*反面教材 (Pre-mortem)\*\*：Bug \= 用更多 parameters 壓低 training loss，卻沒有檢查 test scaling 是否已脫鉤。  
\- \*\*理論基礎\*\*：← \[\[D1.1\]\], \[\[D1.2\]\], \[\[D1.3\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\], \[\[P2\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[R1\]\]

\#\#\# T1：Scaling Bottleneck Diagnosis Matrix  
\- \*\*用途\*\*：決定下一輪投資是 compute、architecture 還是 data generation。  
\- \*\*結構內容\*\*：  
  | 訊號 | 可能 Bottleneck | Patch |  
  |---|---|---|  
  | train↓ / test↓ | 還在正常 scaling | 增加 compute/model |  
  | train↓ / test flat | information limit / overfit | 新 data / intervention |  
  | train flat / test flat | optimization / architecture | optimizer / model redesign |  
  | observational strong / perturbation weak | causal coverage 缺失 | active experiments |  
  | lab benchmark strong / real-human-cell weak | domain shift | prospective validation |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[P1\]\], \[\[R1\]\]

\#\#\# R1：Causal Data Flywheel  
\- \*\*總體目標\*\*：讓模型自己指出最有價值的下一批實驗，持續增加 information density。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Baseline\*\*：建立 observational model 與 perturbation holdout。  
  \- \*\*Phase 2 Detect Wall\*\*：按 model size 畫 train/test scaling curve。  
  \- \*\*Phase 3 Experiment Selection\*\*：找 uncertainty 高、causal ambiguity 高的 genes/conditions。  
  \- \*\*Phase 4 Parallel Perturbation\*\*：CRISPR / lab automation 執行大批 intervention。  
  \- \*\*Phase 5 Retrain\*\*：新資料併入 X-Atlas-like dataset；重新訓練 model。  
  \- \*\*Phase 6 Prospective Validation\*\*：在未見過的 real lab settings 驗證 intervention prediction。  
\- \*\*系統風險 (Glitches)\*\*：模型選的 experiments 只增加「更多相似資料」，沒有增加 causal information。  
\- \*\*連結\*\*：→ \[\[G1\]\]

\#\#\# G1：Scientific Data Provenance Protocol  
\- \*\*核心協議 (Protocol)\*\*：每筆高價值 biological training data 必須能回溯到 perturbation、cell condition、assay、batch、instrument、processing pipeline。  
\- \*\*具體條款/機制\*\*：  
  \- Perturbation ID 與 target gene 不可只存在 notebook。  
  \- Observation 與 intervention data 分開標記。  
  \- train/validation/test 以 biological condition 做 leakage-aware split。  
  \- model version 與 dataset snapshot 互相 pin。  
  \- prospective lab result 永遠以 append-only evidence 保存，不覆寫 prediction history。  
\- \*\*決策流程\*\*：Experiment Design → Data QC → Provenance Check → Dataset Snapshot → Train → Prospective Test → Feedback。  
\- \*\*違規後果\*\*：缺 experiment provenance 的 row 不進 causal gold set；跨 batch leakage 的 benchmark 不得宣稱 causal generalization。  
\- \*\*連結\*\*：← \[\[R1\]\]；→ \[\[S1\]\], \[\[P2\]\]

\#\#\# P1：Information Wall Detector  
\- \*\*場景 (Scenario)\*\*：已經有多個 model-size checkpoints，不確定是否還值得 scale。  
\- \*\*價值 (Value)\*\*：用 curves 決定資本配置。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 固定 dataset split 與 evaluation protocol。  
  2\. 對每個 parameter scale 記錄 train loss、test loss、perturbation accuracy。  
  3\. fit scaling trend；監控 test residual 是否開始系統性偏離。  
  4\. 若 \`train\_improves=true && test\_slope≈0\`，建立 \`information\_limited\` flag。  
  5\. 下一輪 budget 至少保留一個 experiment-generation arm，與純 compute arm 做 A/B capital allocation。  
\- \*\*工具集 (Toolset)\*\*：experiment tracker、W\&B/MLflow、scaling-curve notebook、dataset registry。  
\- \*\*影子技巧\*\*：不要用單一大模型結果判斷 scaling；要看 \*\*curve shape\*\*。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[T1\]\]

\#\#\# P2：Active Causal Data Loop  
\- \*\*場景 (Scenario)\*\*：模型對 observational data 很強，但 gene perturbation 預測弱。  
\- \*\*價值 (Value)\*\*：把模型 uncertainty 轉成下一批 lab experiments。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 對 candidate perturbations 計算 uncertainty / disagreement。  
  2\. 加上 biological novelty、cost、assay feasibility，形成 experiment priority score。  
  3\. 批次送入 automated CRISPR/assay pipeline。  
  4\. 回收 result，先進 immutable raw store，再進 processed feature store。  
  5\. 比較「新增 random samples」與「新增 active-selected samples」的 test-loss 改善，量化每美元 information gain。  
\- \*\*工具集 (Toolset)\*\*：active learning scheduler、lab LIMS、feature store、dataset registry、prospective eval harness。  
\- \*\*影子技巧\*\*：核心 KPI 不是 rows/day，而是 \*\*information gain per experiment-dollar\*\*。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[G1\]\]

\#\#\# E1：Causal Information Beats Passive Scale  
\- \*\*法則內容\*\*：當資料只告訴模型「哪些東西一起發生」，模型 scale 終究會撞牆；能告訴模型「改變 X 之後 Y 怎麼變」的 intervention data 才能打開下一條 scaling curve。  
\- \*\*推論/啟示\*\*：在可實驗領域，下一代 AI moat 可能不是最大 GPU cluster，而是最強的 closed-loop data-generation machine。  
\- \*\*支撐證據\*\*：← \[\[D1.1\]\], \[\[D1.2\]\], \[\[D1.3\]\], \[\[R1\]\], \[\[P1\]\], \[\[P2\]\]
