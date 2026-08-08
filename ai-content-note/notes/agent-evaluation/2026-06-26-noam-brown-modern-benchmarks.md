---
id: "no-priors:noam-brown-benchmark-test-time-compute"
title: "Why Traditional Benchmarks Fail Modern AI Models with Noam Brown"
source_name: "No Priors"
source_type: "podcast-transcript"
source_url: "https://podcasts.apple.com/gb/podcast/why-traditional-benchmarks-fail-modern-ai-models-with/id1668002688?i=1000774329129"
canonical_url: "https://podcasts.apple.com/gb/podcast/why-traditional-benchmarks-fail-modern-ai-models-with/id1668002688?i=1000774329129"
published_at: "2026-06-26"
monetization_score: 100
monetization_modes: "Capability-curve evaluation service; budget-aware safety benchmark; long-running research Agent harness; inference economics newsletter."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["agent-evaluation", "test-time-compute"]
mapping_targets: ["llm-model", "data", "trajectory"]
github_path: "ai-content-note/notes/agent-evaluation/2026-06-26-noam-brown-modern-benchmarks.md"
legacy_google_doc_id: "1CRMrS9603thE0hc3fFP_emlArImWpl90DNZdYkznKcs"
legacy_google_doc_url: "https://docs.google.com/document/d/1CRMrS9603thE0hc3fFP_emlArImWpl90DNZdYkznKcs/edit"
citation_mapping_status: pending
---

\#\#\# N1：Benchmark 的固定預算假設已經失效  
\- \*\*核心衝突\*\*：傳統 benchmark 在固定 token、固定時間與單次回答下比較模型；現代 reasoning system 的能力會隨 test-time compute、scaffolding、memory 與多代理協作持續上升。  
\- \*\*關鍵人物/實體\*\*：Noam Brown 與長推理模型研究路線 vs 固定預算 leaderboard、短時安全測試與一次性產品 demo。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- 節目發布：\*\*2026-06-26\*\*。  
  \- 訪談以 \*\*US$10、US$10,000、US$10 million\*\* 的推論預算對照模型能力。  
  \- AI Security Institute 的測試顯示，能力在 \*\*100 million tokens\*\* 時仍持續改善。  
  \- Poker solver 先取得 \*\*5×\*\* speedup，之後再取得 \*\*10×\*\* speedup。  
  \- 一個 \*\*US$100 pot\*\* 的案例中，系統曾錯誤回報 \*\*US$92\*\*。  
  \- Frontier model release cycle 約 \*\*2–3 months\*\*。  
  \- Brown 推測某些 Erdős 問題可能在 \*\*US$1,000–US$100,000\*\* scaffold budget 下被突破。  
\- \*\*劇情轉折\*\*：早期 benchmark 把模型視為固定函式。Reasoning model 將能力變成 compute-budget curve。當 Agent 能運行數週或數月、累積 memory、使用工具與互相驗證時，「模型得分」不再是單點，而是受資源與 harness 影響的函數。  
\- \*\*生態背景\*\*：安全評估、採購與研究競賽仍常以單一 benchmark score 決策。這低估了高預算攻擊者，也低估了低延遲產品與長期研究 Agent 的差異。  
\- \*\*連結\*\*：→ \[\[D1\]\]–\[\[D9\]\], → \[\[G1\]\], ≈ \[\[N2：演算法複雜度的 time-space trade-off\]\]

\#\#\# Q1：一個模型到底有沒有「固定能力」？  
\- \*\*核心疑問 (The Doubt)\*\*：當同一 checkpoint 在不同 budget 下可能呈現完全不同能力，發布方應公布哪個數字？  
\- \*\*現狀反差 (Reality Gap)\*\*：Leaderboard 提供單一分數；真實使用者可能給模型幾秒、幾小時、數週或數百萬 token。  
\- \*\*思維實驗 (Simulation)\*\*：如果低預算 eval 顯示模型無法完成 cyber task，但攻擊者願意投入 100M tokens、多代理搜尋與外部工具，原安全結論還成立嗎？  
\- \*\*連結\*\*：← \[\[D1\]\], \[\[D6\]\], → \[\[S1\]\], \[\[G1\]\]

\#\#\# C1：Capability–Compute Curve  
\- \*\*定義\*\*：模型在特定任務上的能力是 test-time compute、token budget、wall-clock time、tools、memory、parallel attempts 與 verification 的函數。  
\- \*\*演化\*\*：固定 forward pass → chain-of-thought sampling → search、self-play、multi-agent、long-horizon research。  
\- \*\*本質\*\*：推論資源不是純成本項，而是演算法的一部分。  
\- \*\*結構特徵\*\*：budget tiers、best-of-N、tree search、persistent memory、tool use、verifier、stopping rule。  
\- \*\*連結\*\*：→ \[\[D1\]\], \[\[D2\]\], \[\[E1\]\]

\#\#\# D1：US$10 到 US$10 million 的能力跨度  
\- \*\*操作手法\*\*：用不同推論預算比較同一模型或同類系統，而非只跑一次標準設定。  
\- \*\*獨特特徵\*\*：預算差距達六個數量級，代表「模型能力」必須附帶資源條件。  
\- \*\*影子證據\*\*：\*\*US$10、US$10,000、US$10 million\*\* 三個層級不可改寫成「低、中、高預算」。  
\- \*\*連結\*\*：↔ \[\[D2\]\], ⟨S1⟩

\#\#\# D2：100 million tokens 仍未飽和  
\- \*\*操作手法\*\*：AI Security Institute 在高 token budget 下持續量測能力曲線。  
\- \*\*獨特特徵\*\*：若曲線在 100M tokens 還上升，短 benchmark 不能提供 capability ceiling。  
\- \*\*影子證據\*\*：\*\*100 million tokens\*\*。  
\- \*\*連結\*\*：↔ \[\[D1\]\], \[\[D3\]\], → \[\[G1\]\]

\#\#\# D3：Poker solver 的 5× 與 10× speedup  
\- \*\*操作手法\*\*：透過演算法、搜尋與系統改進先取得 \*\*5×\*\*，後續再取得 \*\*10×\*\* speedup。  
\- \*\*獨特特徵\*\*：能力進步不只來自更大模型，也來自推論程序本身。  
\- \*\*影子證據\*\*：兩次 speedup 必須分開記錄，不可合併成「大幅加速」。  
\- \*\*連結\*\*：↔ \[\[D4\]\], ⟨S2⟩

\#\#\# D4：US$100 pot 被錯算為 US$92  
\- \*\*操作手法\*\*：案例顯示即使系統在策略層很強，簡單 arithmetic 或 state accounting 仍可出錯。  
\- \*\*獨特特徵\*\*：高階 reasoning 與基礎 correctness 不同步。  
\- \*\*影子證據\*\*：\*\*US$100\*\* 與錯誤的 \*\*US$92\*\*。  
\- \*\*連結\*\*：↔ \[\[D3\]\], → \[\[P2\]\], \[\[G2\]\]

\#\#\# D5：GPT-5.5 接近 zero-shot solver  
\- \*\*操作手法\*\*：模型開始在沒有大量 task-specific scaffolding 的情況下接近 solver 能力。  
\- \*\*獨特特徵\*\*：若 base model 吸收更多搜尋模式，過去依賴專用 solver 的能力可能被一般模型內化。  
\- \*\*影子證據\*\*：訪談描述為接近 zero-shot solver，而非完全取代 solver。  
\- \*\*連結\*\*：↔ \[\[D6\]\], ⟨S2⟩

\#\#\# D6：安全框架忽略推論預算  
\- \*\*操作手法\*\*：現有安全評估通常固定短時間、固定 token 與單 Agent。  
\- \*\*獨特特徵\*\*：這可能低估有資源攻擊者、長期 autonomous system 與平行搜尋。  
\- \*\*影子證據\*\*：Brown 明確指出 safety frameworks 尚未充分納入 compute budget。  
\- \*\*連結\*\*：↔ \[\[D2\]\], \[\[D7\]\], → \[\[G1\]\]

\#\#\# D7：2–3 個月模型發布週期  
\- \*\*操作手法\*\*：Frontier labs 快速迭代 checkpoint，使 benchmark、policy 與 deployment assumption 很快過期。  
\- \*\*獨特特徵\*\*：安全評估完成時，下一個模型可能已接近發布。  
\- \*\*影子證據\*\*：\*\*2–3 months\*\*。  
\- \*\*連結\*\*：↔ \[\[D6\]\], → \[\[R1\]\]

\#\#\# D8：Erdős 問題的 US$1,000–US$100,000 scaffold 假設  
\- \*\*操作手法\*\*：用長程搜尋、工具、驗證與多次嘗試處理開放數學問題。  
\- \*\*獨特特徵\*\*：突破門檻可能不是下一代 base model，而是對現有模型投入更高 inference budget。  
\- \*\*影子證據\*\*：\*\*US$1,000–US$100,000\*\*。  
\- \*\*連結\*\*：↔ \[\[D9\]\], → \[\[P3\]\]

\#\#\# D9：Research taste 成為新瓶頸  
\- \*\*操作手法\*\*：人類選擇值得研究的問題、判斷中間結果價值、決定何時停止與如何驗證。  
\- \*\*獨特特徵\*\*：當生成候選解的成本下降，problem selection 與 evaluation judgment 反而更稀缺。  
\- \*\*影子證據\*\*：訪談將 research taste 描述為重要限制，而非宣稱 AI 已自動化完整科學流程。  
\- \*\*連結\*\*：↔ \[\[D8\]\], → \[\[S3\]\], \[\[P3\]\]

\#\#\# S1：用曲線取代單點 Benchmark  
\- \*\*策略邏輯\*\*：至少在多個 budget tier 報告 success、cost、latency 與 variance。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：以 $10、$10k、$10M 與 100M-token 情境揭示能力曲線。  
  \- \*\*環境/競對參照\*\*：傳統 benchmark 固定單次 token limit，易被當成 capability ceiling。  
\- \*\*反面教材 (Pre-mortem)\*\*：只測高預算，忽略產品延遲；只測低預算，低估高資源攻擊者。  
\- \*\*理論基礎\*\*：← \[\[D1\]\], \[\[D2\]\], \[\[D6\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[G1\]\]

\#\#\# S2：把推論 Harness 視為模型的一部分  
\- \*\*策略邏輯\*\*：Search、solver、memory、verifier 與 tools 必須和 checkpoint 一起版本化與評估。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：Poker solver speedup 與 zero-shot solver 能力顯示 base model、algorithm、scaffold 共同決定結果。  
  \- \*\*環境/競對參照\*\*：只報 model name，卻不報 best-of-N、tool access 或 verifier，會造成不可重現比較。  
\- \*\*反面教材 (Pre-mortem)\*\*：Harness 在 benchmark 中使用 privileged information，production 無法重現。  
\- \*\*理論基礎\*\*：← \[\[D3\]\], \[\[D5\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P2\]\]  
\- \*\*支撐框架\*\*：← \[\[G2\]\]

\#\#\# S3：Research Taste Routing  
\- \*\*策略邏輯\*\*：模型大規模探索前，先用人類與 Agent 協作評估問題價值、可驗證性與 information gain。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：Brown 強調真正稀缺的是判斷哪些問題值得追。  
  \- \*\*環境/競對參照\*\*：暴力生成大量候選結果會形成驗證債務。  
\- \*\*反面教材 (Pre-mortem)\*\*：投入 US$100,000 解出低影響問題，或產生無法獨立驗證的 claim。  
\- \*\*理論基礎\*\*：← \[\[D8\]\], \[\[D9\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P3\]\]  
\- \*\*支撐框架\*\*：← \[\[R2\]\]

\#\#\# T1：Capability–Budget 評估矩陣  
\- \*\*用途\*\*：在產品、安全與研究三種情境下選擇不同測試預算。  
\- \*\*結構內容\*\*：  
  | Budget Tier | 典型情境 | 必測指標 |  
  |---|---|---|  
  | 秒級 / 低 token | 互動產品 | latency、first-pass accuracy |  
  | 分鐘級 | coding/analysis | cost-per-success、tool recovery |  
  | 小時級 | deep research | memory、verification、drift |  
  | 天/週級 | autonomous research | checkpointing、goal integrity、human oversight |  
  | 100M-token / 高資源 | safety ceiling | dangerous capability、parallel search、novel exploits |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[P1\]\], \[\[G1\]\]

\#\#\# R1：Budget-Aware Safety Evaluation 路線圖  
\- \*\*總體目標\*\*：讓安全 claim 對推論資源與時間明確成立。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Baseline\*\*：標準低預算評估。  
  \- \*\*Phase 2 Scaling Curve\*\*：逐級增加 token、wall time、attempts。  
  \- \*\*Phase 3 Tool/Memory Enablement\*\*：加入真實工具與 persistent state。  
  \- \*\*Phase 4 Parallel Agents\*\*：測試多代理搜尋與資訊共享。  
  \- \*\*Phase 5 Adversarial Budget\*\*：模擬高資源攻擊者。  
  \- \*\*Phase 6 Policy Update\*\*：用 observed curve 更新 access controls。  
\- \*\*系統風險 (Glitches)\*\*：高預算測試成本過高、停止規則偏差、scaffold leakage、測試環境與現實工具不一致。  
\- \*\*連結\*\*：→ \[\[G1\]\], \[\[G2\]\]

\#\#\# R2：Long-Horizon Research Agent 路線圖  
\- \*\*總體目標\*\*：把高推論預算轉成可驗證研究，而非長時間 hallucination。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Problem Spec\*\*：定義成功、證據與停止條件。  
  \- \*\*Phase 2 Parallel Hypotheses\*\*：多 Agent 獨立探索。  
  \- \*\*Phase 3 Shared Memory\*\*：只寫入有 provenance 的中間結果。  
  \- \*\*Phase 4 Independent Verification\*\*：不同模型或專家重做關鍵步驟。  
  \- \*\*Phase 5 Value Review\*\*：判斷結果新穎性與影響。  
  \- \*\*Phase 6 Publication\*\*：公開 budget、harness、failed paths 與 artifacts。  
\- \*\*系統風險 (Glitches)\*\*：多代理共用同一錯誤、memory 污染、無限延長、研究價值低、作者歸因不清。  
\- \*\*連結\*\*：→ \[\[G2\]\], \[\[S3\]\]

\#\#\# G1：Inference Budget Disclosure Protocol  
\- \*\*核心協議 (Protocol)\*\*：任何模型能力或安全聲明必須附帶 token、time、attempts、tools、memory 與 verifier 條件。  
\- \*\*具體條款/機制\*\*：  
  \- 報告完整 capability curve，不只最佳點。  
  \- 區分平均使用者預算與 adversarial budget。  
  \- 保存每次 run 的 cost 與 stopping reason。  
  \- 模型更新或 scaffold 更新後重新測試。  
\- \*\*決策流程\*\*：budget design → repeated runs → curve fitting → threshold review → policy。  
\- \*\*違規後果\*\*：未披露推論預算的 leaderboard claim 標記為不可比較。  
\- \*\*連結\*\*：← \[\[R1\]\], → \[\[S1\]\]

\#\#\# G2：Long-Running Agent Verification Protocol  
\- \*\*核心協議 (Protocol)\*\*：運行時間越長、預算越高，驗證與中途 checkpoint 必須同步增加。  
\- \*\*具體條款/機制\*\*：  
  \- 每個 milestone 產出可檢查 artifact。  
  \- 記憶寫入需有 source、timestamp、confidence。  
  \- 關鍵數字由 deterministic tool 驗證。  
  \- 不可逆行動需要外部 approval。  
  \- 超過 budget 或無 information gain 時停止。  
\- \*\*決策流程\*\*：plan → milestone → artifact check → continue/branch/stop。  
\- \*\*違規後果\*\*：無中間證據的長 run 不得以「模型思考更久」作為可信度來源。  
\- \*\*連結\*\*：← \[\[D4\]\], \[\[R2\]\], → \[\[S2\]\], \[\[S3\]\]

\#\#\# P1：Capability Curve Runner  
\- \*\*場景 (Scenario)\*\*：評估模型在不同 inference budget 下的能力。  
\- \*\*價值 (Value)\*\*：找出邊際收益、飽和點與高資源安全風險。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 固定 model、task、tool set 與 evaluator。  
  2\. 設定至少五個 token/time budget tiers。  
  3\. 每 tier 執行多個 seeds。  
  4\. 記錄 success、cost、latency、attempt count、variance。  
  5\. 擬合 capability–budget curve 與 confidence interval。  
  6\. 檢查高 budget 是否產生新 failure mode。  
\- \*\*工具集 (Toolset)\*\*：eval harness、scheduler、cost ledger、trace store、statistical notebook。  
\- \*\*影子技巧\*\*：同時測最佳 scaffold 與標準使用者 scaffold，避免只展示研究版上限。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[T1\]\]

\#\#\# P2：Arithmetic與State Oracle  
\- \*\*場景 (Scenario)\*\*：Agent 執行策略、金融、遊戲或長期規劃。  
\- \*\*價值 (Value)\*\*：防止高階策略被 US$100→US$92 這類基礎錯誤破壞。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 將金額、計數、概率與 state transition 抽成 structured state。  
  2\. 所有 arithmetic 呼叫 deterministic calculator。  
  3\. 每個 action 前後比對 invariant。  
  4\. 對不一致觸發 rollback 與重新規劃。  
  5\. 將錯誤案例加入 regression suite。  
\- \*\*工具集 (Toolset)\*\*：calculator、state machine、property tests、transaction log。  
\- \*\*影子技巧\*\*：禁止模型自行用自然語言覆蓋 oracle 結果。  
\- \*\*連結\*\*：← \[\[S2\]\], \[\[D4\]\], \[\[G2\]\]

\#\#\# P3：高預算數學研究 Pipeline  
\- \*\*場景 (Scenario)\*\*：使用 US$1,000–US$100,000 推論預算探索開放問題。  
\- \*\*價值 (Value)\*\*：將 compute 轉成有 provenance 的候選證明與反例。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 由專家選題並建立 prior-art pack。  
  2\. 多 Agent 生成獨立 proof strategy。  
  3\. 使用 verifier Agent 專門證偽。  
  4\. 將 lemma DAG 與失敗路徑寫入 shared memory。  
  5\. 對候選證明使用 Lean/Coq 形式化。  
  6\. 計算每階段 information gain，低於門檻即停止。  
\- \*\*工具集 (Toolset)\*\*：Lean/Coq、CAS、search scheduler、artifact graph、expert review。  
\- \*\*影子技巧\*\*：先投資可驗證問題；避免把 budget 燒在 theorem statement 模糊的題目。  
\- \*\*連結\*\*：← \[\[S3\]\], \[\[D8\]\], \[\[D9\]\]

\#\#\# E1：模型能力是資源條件式函數  
\- \*\*法則內容\*\*：任何能力數字都必須寫成 capability(model, budget, harness, tools, time)。  
\- \*\*推論/啟示\*\*：單點 benchmark 仍可用，但不能代表安全上限或長程 Agent 上限。  
\- \*\*支撐證據\*\*：← \[\[C1\]\], \[\[D1\]\], \[\[D2\]\], \[\[T1\]\]

\#\#\# E2：推論預算越高，驗證預算也必須越高  
\- \*\*法則內容\*\*：更多思考時間會增加找到答案的機率，也會增加錯誤累積、探索危險能力與驗證債務。  
\- \*\*推論/啟示\*\*：Long-running Agent 的核心產品不是「一直跑」，而是「持續產生可驗證進展」。  
\- \*\*支撐證據\*\*：← \[\[D4\]\], \[\[D6\]\], \[\[G2\]\], \[\[P2\]\], \[\[P3\]\]
