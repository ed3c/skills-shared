---
id: "sequoia:americas-open-model-paradox"
title: "America's Open-Model Paradox"
source_name: "Sequoia Capital"
source_type: "venture-analysis"
source_url: "https://sequoiacap.com/?media=text#americas-open-model-paradox"
canonical_url: "https://sequoiacap.com/?media=text#americas-open-model-paradox"
published_at: "2026-07-24"
monetization_score: 100
monetization_modes: "Open-model supply-chain audit; model SBOM service; synthetic-data provenance consulting; sovereign AI dependency report."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["open-model-supply-chain", "model-provenance"]
mapping_targets: ["llm-model", "data"]
github_path: "ai-content-note/notes/open-model-supply-chain/2026-07-24-americas-open-model-paradox.md"
legacy_google_doc_id: "1CrKKv-7YQWwLMAbt8xb16u0Q133JXKEi-WrdzHFm8A8"
legacy_google_doc_url: "https://docs.google.com/document/d/1CrKKv-7YQWwLMAbt8xb16u0Q133JXKEi-WrdzHFm8A8/edit"
citation_mapping_status: pending
---

\#\#\# N1：美國贏 Closed Frontier，卻可能輸掉 Open Foundation  
\- \*\*核心衝突\*\*：美國 labs 在 closed frontier model 領先，但 downstream builders、fine-tuners、synthetic-data pipelines 越來越依賴中國 open-weight model family。  
\- \*\*關鍵人物/實體\*\*：US frontier labs / Alibaba Qwen、DeepSeek、Kimi、GLM / Western AI startups。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- ATOM Report：Qwen 在 Hugging Face 新 derivative/fine-tuned models 的月度占比，從 \*\*2024-01 的 1% 升到 2026-02 的 69%\*\*。  
  \- 2026-03：Qwen 累積 Hugging Face downloads \*\*942.1M\*\*；Meta Llama \*\*476.0M\*\*。  
  \- 2026-03：中國 open models 累積 downloads \*\*1.15B\*\*，美國約 \*\*723M\*\*。  
\- \*\*劇情轉折\*\*：依賴已不只在 serving。Western labs 也開始用中國 open models 作 teacher / synthetic-data source；Sequoia 以 Thinking Machines 的 Inkling 使用 Kimi K2.5 synthetic data 作為例子。  
\- \*\*生態背景\*\*：open-weight model 一旦成為 adapter、fine-tune、eval、inference toolchain 的預設 foundation，就形成類似 CPU ISA 或 cloud API 的 ecosystem gravity。  
\- \*\*連結\*\*：→ \[\[D1.1\]\], \[\[D1.2\]\], \[\[D1.3\]\], \[\[G1\]\]

\#\#\# Q1：Model Sovereignty 的真正單位是「誰訓練 frontier model」，還是「誰擁有 downstream ecosystem」？  
\- \*\*核心疑問 (The Doubt)\*\*：如果西方應用、fine-tune、teacher data、eval harness 都建立在外部 open model family 上，closed frontier 領先能否抵銷 supply-chain dependency？  
\- \*\*現狀反差 (Reality Gap)\*\*：headline 常比較最高 benchmark；developer adoption 卻由 license、size coverage、tooling、cost、derivative ecosystem 決定。  
\- \*\*思維實驗 (Simulation)\*\*：若明天新一代 Qwen/Kimi 權重延遲或限制海外取得，企業仍能下載舊權重，但下一代 fine-tune、distillation、synthetic-data pipeline 是否會逐季落後？  
\- \*\*連結\*\*：← \[\[D1.1\]\], \[\[D1.2\]\]；→ \[\[S1\]\], \[\[R1\]\]

\#\#\# C1：Open-Model Supply Chain  
\- \*\*定義\*\*：open model 不只是 binary artifact；它包含 base weights、derivatives、adapters、training recipes、synthetic data、inference providers、evaluation assumptions、developer skills。  
\- \*\*演化\*\*：\`Open weights as alternative model\` → \`Open family as downstream platform\` → \`Model family as strategic dependency\`。  
\- \*\*本質\*\*：Ecosystem share 產生 switching cost。越多 derivative models、tooling、data pipelines 綁定同一 family，dependency 越深。  
\- \*\*結構特徵\*\*：weight provenance、license、teacher provenance、adapter compatibility、tokenizer、serving stack、eval calibration、fallback model。  
\- \*\*連結\*\*：→ \[\[T1\]\], \[\[P1\]\], \[\[G1\]\]；→ \[\[E1\]\]

\#\#\# D1.1：Qwen derivative dominance  
\- \*\*操作手法\*\*：Qwen 採 broad-spectrum release strategy，從小型模型到大型模型覆蓋多種 deployment economics，讓 downstream fine-tune/adaptation 更容易標準化在同一 family。  
\- \*\*獨特特徵\*\*：採用優勢不只來自單次 benchmark，而是 size coverage \+ permissive access \+ ecosystem momentum。  
\- \*\*影子證據\*\*：Qwen derivative share：2024-01 \*\*1%\*\* → 2026-02 \*\*69%\*\*；Meta Llama 在 ATOM 的同一觀察中降至 \*\*11%\*\*。Qwen 2026-03 cumulative downloads \*\*942.1M\*\*，Llama \*\*476.0M\*\*。  
\- \*\*連結\*\*：↔ \[\[D1.2\]\]；→ \[\[S1\]\], \[\[E1\]\]

\#\#\# D1.2：DeepSeek 的 inference-specialization 路徑  
\- \*\*操作手法\*\*：DeepSeek 不一定在 download/derivative 數量上等同 Qwen，但在 hosted open-model inference token share 曾極高。  
\- \*\*獨特特徵\*\*：open ecosystem 不能只看 download；local adaptation 與 hosted inference 是不同 adoption surface。  
\- \*\*影子證據\*\*：ATOM 分析顯示 DeepSeek V3/R1 在 2025-06 曾達 open-model inference tokens \*\*75.6%\*\* 的 peak。  
\- \*\*連結\*\*：↔ \[\[D1.1\]\]；→ \[\[T1\]\]

\#\#\# D1.3：Synthetic Teacher Dependency  
\- \*\*操作手法\*\*：Western team 可使用 open-weight foreign models 產生 synthetic examples，bootstrapping supervised fine-tuning / post-training。  
\- \*\*獨特特徵\*\*：dependency 上移到 model-development pipeline，不只是應用層 API。  
\- \*\*影子證據\*\*：Sequoia 指出 Thinking Machines 的 Inkling 雖自行 pre-train，仍使用 Moonshot Kimi K2.5 生成 synthetic data 來啟動 supervised fine-tuning 的部分流程。  
\- \*\*連結\*\*：→ \[\[G1：Teacher Provenance\]\], \[\[P1\]\]

\#\#\# S1：把 Model Family 當供應鏈，而不是 npm package  
\- \*\*策略邏輯\*\*：任何被用於 production serving、fine-tune、teacher data 或 eval baseline 的外部 model family，都必須進 dependency governance。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：中國 open model family 透過開放權重與廣泛 size coverage 取得 ecosystem gravity。  
  \- \*\*環境/競對參照\*\*：US closed model labs 可能保持 frontier quality，但 closed-output terms 常限制 competitive training use；這使 downstream builder 更傾向可訓練、可修改的 open foundation。  
\- \*\*反面教材 (Pre-mortem)\*\*：Bug \= enterprise 只做 API vendor risk review，卻沒記錄 fine-tune base、teacher model、synthetic dataset provenance。  
\- \*\*理論基礎\*\*：← \[\[D1.1\]\], \[\[D1.2\]\], \[\[D1.3\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[R1\]\], \[\[G1\]\]

\#\#\# T1：Model Dependency Surface Matrix  
\- \*\*用途\*\*：把「我們用了哪些模型」拆成真正可稽核的依賴。  
\- \*\*結構內容\*\*：  
  | Surface | Dependency Example | Exit Cost |  
  |---|---|---|  
  | Serving | hosted inference / local weights | prompt \+ performance revalidation |  
  | Fine-tune | base weights / tokenizer / adapters | retraining |  
  | Synthetic data | teacher model outputs | dataset regeneration / provenance |  
  | Eval | judge model / benchmark calibration | score discontinuity |  
  | Agent harness | tool-call behavior / context assumptions | orchestration retuning |  
  | Edge | quantization / hardware kernels | runtime rebuild |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[P1\]\], \[\[G1\]\]

\#\#\# R1：Open-Model Dependency De-risk Roadmap  
\- \*\*總體目標\*\*：在不犧牲 open-model economics 的前提下，降低 single-family systemic dependency。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Inventory\*\*：盤點 serving、fine-tune、teacher、judge、embedding、reranker、agent model。  
  \- \*\*Phase 2 Provenance\*\*：對 dataset 記錄 teacher model/version、prompt template、sampling params、license/terms。  
  \- \*\*Phase 3 Portability Eval\*\*：每個核心 workload 至少維護第二 model family baseline。  
  \- \*\*Phase 4 Data Escrow\*\*：保存可重新生成/重新標記的原始 examples，而不是只有 teacher-produced labels。  
  \- \*\*Phase 5 Dual-Stack\*\*：重要 production path 可在兩個 model families 間切換。  
  \- \*\*Phase 6 Quarterly Exit Drill\*\*：模擬一個 provider/weight family 不再可用，量測 7/30/90-day migration cost。  
\- \*\*系統風險 (Glitches)\*\*：只換 inference model，卻忘記 fine-tune tokenizer、adapter format、synthetic-data lineage 全部已鎖定。  
\- \*\*連結\*\*：→ \[\[G1\]\]

\#\#\# G1：Model & Synthetic-Data Provenance Governance  
\- \*\*核心協議 (Protocol)\*\*：所有進入模型訓練與 Agent decision path 的外部 intelligence 都要有 SBOM-like provenance。  
\- \*\*具體條款/機制\*\*：  
  \- \`model\_id \+ revision \+ provider \+ license \+ geography \+ checksum\`。  
  \- Synthetic example 記 \`teacher\_model\`, \`generation\_date\`, \`prompt\_version\`, \`temperature\`, \`review\_status\`。  
  \- Fine-tune artifact 必須能追到 base weights 與 dataset lineage。  
  \- Judge/eval model 變更不得直接與舊分數比較，必須跑 calibration bridge。  
  \- Strategic workloads 每季重跑 cross-family portability eval。  
\- \*\*決策流程\*\*：New Model/Teacher → Legal \+ Security \+ Portability Review → Approved Registry → Usage → Quarterly Revalidation。  
\- \*\*違規後果\*\*：provenance 缺失的 synthetic data 不進 gold dataset；無 exit baseline 的 single-family dependency 標記 architecture debt。  
\- \*\*連結\*\*：← \[\[R1\]\]；→ \[\[S1\]\], \[\[P1\]\]

\#\#\# P1：Model Dependency Scanner  
\- \*\*場景 (Scenario)\*\*：Repository 同時使用 closed API、open weights、fine-tunes、teacher-generated data。  
\- \*\*價值 (Value)\*\*：把隱性模型依賴變成機器可讀 inventory。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 掃描 \`requirements\`, model config、Docker image、HF repo id、API endpoint、LoRA adapter metadata。  
  2\. 對每個 dataset 加 provenance sidecar，例如 \`dataset.manifest.json\`。  
  3\. CI 生成 \`model-sbom.json\`：family、revision、license、usage surface、fallback。  
  4\. 若 \`critical=true\` 且只有單一 family，CI 輸出 architecture warning。  
  5\. 每季用相同 eval set 跑 primary/secondary family，保存 quality、cost、latency、migration blockers。  
\- \*\*工具集 (Toolset)\*\*：Hugging Face metadata API、model registry、MLflow/W\&B、SBOM-style JSON manifest、CI policy check。  
\- \*\*影子技巧\*\*：把「teacher model」列為 supply-chain dependency；它通常不出現在 production runtime，卻已寫進你的 model behavior。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[G1\]\]

\#\#\# E1：Ecosystem Gravity Law  
\- \*\*法則內容\*\*：Open model 的戰略力量來自 downstream ecosystem 的累積，而不只來自單一 frontier benchmark。  
\- \*\*推論/啟示\*\*：當某 model family 佔據 fine-tunes、adapters、synthetic data、developer knowledge 與 serving stack，它就成為供應鏈基礎設施；替換成本會遠高於下載另一組 weights。  
\- \*\*支撐證據\*\*：← \[\[D1.1\]\], \[\[D1.2\]\], \[\[D1.3\]\], \[\[R1\]\], \[\[G1\]\], \[\[P1\]\]
