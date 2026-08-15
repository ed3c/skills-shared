---
id: "openai:gpt-live-realtime-architecture"
title: "How we built a realtime system for responsive voice AI in six months"
source_name: "OpenAI Newsroom"
source_type: "official-engineering"
source_url: "https://openai.com/index/continuous-voice-interaction-with-gpt-live/"
canonical_url: "https://openai.com/index/continuous-voice-interaction-with-gpt-live"
published_at: "2026-08-03"
monetization_score: 100
monetization_modes: "Realtime voice agent architecture course; WebRTC/WARP engineering brief; full-duplex agent SDK; enterprise voice workflow consulting."
note_status: completed
note_version: v6.6-cyberpunk
language: zh-Hant
technical_terms_language: en
categories: ["multimodal-agents", "realtime-voice"]
mapping_targets: ["code", "trajectory"]
github_path: "ai-content-note/notes/multimodal-agents/2026-08-03-openai-realtime-voice-system.md"
legacy_google_doc_id: "1wRyA2Q6dH5fn4KVYllQn3HsMF_ACRFQw22dAEA5qqks"
legacy_google_doc_url: "https://docs.google.com/document/d/1wRyA2Q6dH5fn4KVYllQn3HsMF_ACRFQw22dAEA5qqks/edit"
citation_mapping_status: pending
---

\#\#\# N1：Voice AI 從輪流發言切換到連續串流  
\- \*\*核心衝突\*\*：傳統 voice AI 必須先由 turn detector 判斷使用者是否說完，才啟動大型模型。判斷太早會打斷；太晚會延遲。自然對話需要同時聽、同時說、同時委派深度推理。  
\- \*\*關鍵人物/實體\*\*：OpenAI GPT-Live、GPT-5.5、ChatGPT Voice、WebRTC、Go media frontend、IETF WebRTC community vs turn detector、串行 STT→LLM→TTS、網路抖動與 stateful session。  
\- \*\*衝擊力錨點 (Impact Anchors)\*\*：  
  \- 工程文章發布於 \*\*2026-08-03\*\*。  
  \- 團隊在 \*\*6 個月\*\*內重構 inference、context management 與 media transport。  
  \- 新 Go 系統的 \*\*p95\*\* frame delivery 達到舊 Python \`asyncio\` 系統的 \*\*p50\*\*。  
  \- WARP 將 media/data startup 從 \*\*6 個 network round trips\*\*縮短到 \*\*1 個\*\*。  
\- \*\*劇情轉折\*\*：GPT-Live 移除 audio path 上的獨立 turn detector。Voice model 掌控即時媒體迴路；frontier model、工具與持久化改走非同步旁路。系統不再把「說話」與「深度思考」綁在同一條 critical path。  
\- \*\*生態背景\*\*：Realtime AI 的瓶頸不是單一模型 latency。任何 transport、queue、state migration、context compaction、tool call 或 geographic routing 都可能成為可聽見的停頓。  
\- \*\*連結\*\*：  
  \- 證據支撐：→ \[\[D1\]\], \[\[D2\]\], \[\[D3\]\], \[\[D4\]\], \[\[D5\]\], \[\[D6\]\]  
  \- 歷史鏡像：≈ \[\[VoIP fast path\]\], \[\[Event-loop architecture\]\], \[\[CQRS\]\]  
  \- 治理建立：→ \[\[G1\]\]

\#\#\# Q1：即時系統的「答案品質」是否應讓位給「對話流動」？  
\- \*\*核心疑問 (The Doubt)\*\*：若深度模型需要更久，voice agent 應等待、填充對話、先回覆部分結果，還是降低 reasoning effort？  
\- \*\*現狀反差 (Reality Gap)\*\*：文字 Agent 可以接受數秒甚至數分鐘；口語互動中，數百毫秒的停頓就會破壞節奏。  
\- \*\*思維實驗 (Simulation)\*\*：若工具結果正確但晚 5 秒回來，使用者已轉換話題，系統是否應捨棄結果、插入結果，或建立新的 conversational branch？  
\- \*\*連結\*\*：← \[\[D3\]\], \[\[D4\]\], → \[\[S1\]\], \[\[P1\]\]

\#\#\# C1：Full-Duplex Voice Agent  
\- \*\*定義\*\*：能同時接收與產生音訊，維持連續 inference，並把深度 reasoning 與 tool use 委派到非同步路徑的 agent。  
\- \*\*演化\*\*：從 STT→LLM→TTS 串行管線，演化為 stateful speech model \+ async frontier delegation \+ speculative transcript。  
\- \*\*本質\*\*：將不可延遲的 media flow 與可延遲的 business logic 分離。  
\- \*\*結構特徵\*\*：dedicated media path、stateful inference、session handoff、context compaction、async RPC、turn derivation、WebRTC startup optimization。  
\- \*\*連結\*\*：  
  \- 實例展開：→ \[\[D1\]\], \[\[D2\]\], \[\[D3\]\], \[\[D4\]\], \[\[D5\]\]  
  \- 支撐法則：→ \[\[E1\]\]

\#\#\# D1：Dedicated Media Fast Path  
\- \*\*操作手法\*\*：  
  1\. 音訊在 client 與 voice model 間使用專用 fast path。  
  2\. Tool use、delegation 與 application logic 放在 async RPC boundary 後方。  
  3\. Media frontend 與 inference logic 使用 Go。  
  4\. WebRTC 處理 packet loss、clock drift 與 client connection changes。  
\- \*\*獨特特徵\*\*：慢工具只能延遲自己的結果，不能阻塞 audio frames。  
\- \*\*影子證據\*\*：新 Go 系統的 \*\*p95\*\* 等同舊 Python \`asyncio\` 系統的 \*\*p50\*\*；目標為 sub-second responsiveness。  
\- \*\*連結\*\*：↔ \[\[D2\]\], \[\[D3\]\] ⟨S1⟩

\#\#\# D2：Stateful Instance Handoff 與 Context Compaction  
\- \*\*操作手法\*\*：  
  1\. Voice session 長時間保持 active。  
  2\. 需要切換時，在舊 instance 旁預熱 replacement instance。  
  3\. 以現有 session context 進行 prefill。  
  4\. 兩個 instances 暫時平行 inference。  
  5\. 新 instance ready 後無縫 cutover。  
  6\. Context 超限時，把 compaction 當成同一種 managed transition。  
\- \*\*獨特特徵\*\*：compaction 不在 live instance 上停機執行；新 instance 在背景重建 KV cache。  
\- \*\*影子證據\*\*：文章明確指出 compaction 會使過去 context 改變，並 invalidate key-value cache。  
\- \*\*連結\*\*：↔ \[\[D1\]\], \[\[D3\]\] ⟨P1⟩

\#\#\# D3：GPT-Live 與 Frontier Model 的非同步委派  
\- \*\*操作手法\*\*：  
  1\. GPT-Live 維持自然對話。  
  2\. GPT-5.5 執行 search、reasoning 或 tools。  
  3\. Session 啟動時提前建立 frontier inference session。  
  4\. 預先 prefill 初始 conversation context。  
  5\. 使用 stable session affinity 與 prompt caching。  
  6\. 調整 reasoning effort、output limits、tool schemas 與 model-tool round trips。  
\- \*\*獨特特徵\*\*：「talking」與「thinking」由兩個模型路徑協作，但對使用者呈現為同一個 agent。  
\- \*\*影子證據\*\*：文章以 GPT-Live \+ \*\*GPT-5.5\*\*作為 delegation 範例。  
\- \*\*連結\*\*：↔ \[\[D1\]\], \[\[D2\]\], \[\[D4\]\] ⟨S1⟩

\#\#\# D4：從連續語音推導離散訊息  
\- \*\*操作手法\*\*：  
  1\. 使用 partial transcripts 與 timing signals 判斷 speaker floor。  
  2\. 最新 message 保持 provisional。  
  3\. Speaker attribution 足夠穩定後 finalize。  
  4\. 過濾短促 acknowledgement，保留 substantive interjection。  
  5\. 同時維護 speculative view 與 authoritative record。  
\- \*\*獨特特徵\*\*：UI 可接受持續更新，analytics 與 safety pipeline 則需要 final transcript。  
\- \*\*影子證據\*\*：每種 segmentation policy 都在 freshness 與 certainty 間交換。  
\- \*\*連結\*\*：→ \[\[G1\]\], \[\[P1\]\]

\#\#\# D5：WARP 與 Instant Connect  
\- \*\*操作手法\*\*：  
  1\. 以 WARP 合併 WebRTC startup 的重複 handshake。  
  2\. 透過 SPED 將 DTLS handshake piggyback 到 ICE。  
  3\. 使用 DTLS 1.3。  
  4\. 以 SNAP 預協商 SCTP。  
  5\. 預協商 data channels，避免 DCEP critical path。  
  6\. 使用 Instant Connect 預協商 SDP parameters。  
\- \*\*獨特特徵\*\*：保持 backward-compatible，並推進至 IETF TSVWG。  
\- \*\*影子證據\*\*：startup 從 \*\*6 round trips\*\*降到 \*\*1 round trip\*\*；client 可用\*\*單一 UDP packet\*\*啟動 session；WARP 已加入 \*\*libwebrtc\*\*與 \*\*Pion\*\*。  
\- \*\*連結\*\*：→ \[\[P1\]\], \[\[E1\]\]

\#\#\# D6：Production Shadow Test 揭露的容量 Bug  
\- \*\*操作手法\*\*：  
  1\. 將小比例 production Voice sessions 同時送入既有系統與新系統。  
  2\. 舊系統照常服務；新系統 read-only shadow inference。  
  3\. 漸進提高流量。  
  4\. 觀察真實 client、network、session length 與 geography。  
\- \*\*獨特特徵\*\*：測試不改變使用者聽到的內容，但使用真實 workload 暴露 lifecycle 與 capacity 問題。  
\- \*\*影子證據\*\*：  
  \- CPU-side stream handlers、queues 與 network path 必須與 GPU inference 一起擴展。  
  \- 支援元件比預估更早飽和，導致 latency compound。  
  \- 長 session 暴露 memory/persistence pressure；reconnects 測到 compaction/state restoration；disconnects 暴露 shutdown race。  
\- \*\*連結\*\*：→ \[\[R1\]\], \[\[G1\]\]

\#\#\# T1：GPT-Live Critical Path 矩陣  
\- \*\*用途\*\*：把可阻塞與不可阻塞工作分離。  
\- \*\*結構內容\*\*：  
  | 工作 | 路徑 | State | 延遲容忍 | Failure Patch |  
  |---|---|---|---|---|  
  | Audio frames | Media fast path | Stateful | 極低 | WebRTC concealment |  
  | Voice inference | Continuous inference | Stateful | 極低 | instance handoff |  
  | Deep reasoning | Async delegation | Session-affine | 中 | prefill \+ cache |  
  | Tool call | Async application path | 外部 | 高 | timeout / cancel |  
  | Transcript UI | Speculative view | 可更新 | 低 | provisional message |  
  | Analytics | Authoritative record | Finalized | 中 | delayed commit |  
  | Context compaction | Background transition | Stateful | 高 | parallel prefill |  
\- \*\*連結\*\*：→ \[\[S1\]\], \[\[P1\]\], \[\[G1\]\]

\#\#\# S1：Keep the Voice Flowing  
\- \*\*策略邏輯\*\*：任何可能變慢、重試、阻塞或失敗的工作，都不得直接放在 live media critical path。  
\- \*\*生態位對照 (Ecological Context)\*\*：  
  \- 主角表現：media、delegation、persistence、tool use 分離；voice model 持續輸出。  
  \- \*\*環境/競對參照\*\*：串行 STT→LLM→TTS 與 turn detector 架構，把所有延遲加總成使用者可感知停頓。  
\- \*\*反面教材 (Pre-mortem)\*\*：將工具呼叫或資料庫寫入放入 audio loop，單一慢依賴會造成整段對話卡頓。  
\- \*\*理論基礎\*\*：← \[\[D1\]\], \[\[D2\]\], \[\[D3\]\], \[\[D4\]\], \[\[D5\]\], \[\[D6\]\]  
\- \*\*實踐路徑\*\*：→ \[\[P1\]\]  
\- \*\*支撐框架\*\*：← \[\[T1\]\], \[\[R1\]\], \[\[G1\]\]

\#\#\# R1：Realtime Voice 系統導入路線圖  
\- \*\*總體目標\*\*：建立可長時間運行、可委派、可恢復、可在 production 漸進發布的 full-duplex voice agent。  
\- \*\*階段劃分\*\*：  
  \- \*\*Phase 1 Media Baseline\*\*：WebRTC、frame timing、packet loss、jitter buffer。  
  \- \*\*Phase 2 Continuous Inference\*\*：stateful model session 與 streaming audio。  
  \- \*\*Phase 3 Async Delegation\*\*：frontier model session、prefill、tool RPC。  
  \- \*\*Phase 4 Session Mobility\*\*：instance handoff、KV cache rebuild、context compaction。  
  \- \*\*Phase 5 Transcript Dual View\*\*：speculative UI 與 authoritative log。  
  \- \*\*Phase 6 Startup Optimization\*\*：WARP、Instant Connect、regional routing。  
  \- \*\*Phase 7 Shadow Production\*\*：read-only dual run、staged ramp、path isolation。  
\- \*\*系統風險 (Glitches)\*\*：state pinning、regional capacity drift、context corruption、tool result arriving after topic change、transcript attribution error、metrics aggregation hiding unhealthy engines。  
\- \*\*連結\*\*：→ \[\[G1\]\]

\#\#\# G1：Realtime Agent Rollout Protocol  
\- \*\*核心協議 (Protocol)\*\*：即時性、語意正確性與安全性必須分別量測；平均 latency 不得掩蓋單一 engine、region 或 session lifecycle 的失效。  
\- \*\*具體條款/機制\*\*：  
  \- \*\*Shadow First\*\*：新 path 先 read-only。  
  \- \*\*Staged Ramp\*\*：按 region、client version、session type 漸進放量。  
  \- \*\*Path Kill Switch\*\*：可隔離 media、delegation、tool 或 persistence path。  
  \- \*\*Transcript Integrity\*\*：speculative 與 authoritative record 分離。  
  \- \*\*Capacity SLO\*\*：以 concurrent sessions 與 frame schedule 衡量，不只看 requests/GPU。  
  \- \*\*Data Review\*\*：真實 production shadow data 需有 retention 與 access control。  
\- \*\*決策流程\*\*：synthetic load → lifecycle test → shadow traffic → regional validation → staged ramp → SLO review → general availability。  
\- \*\*違規後果\*\*：停止 ramp、切回舊 path、隔離 unhealthy engine、保存 session trace 並啟動 incident review。  
\- \*\*連結\*\*：← \[\[R1\]\], → \[\[S1\]\], \[\[P1\]\]

\#\#\# P1：Full-Duplex Voice Architecture Patch  
\- \*\*場景 (Scenario)\*\*：建立可在對話中同時聽、說、搜尋與呼叫工具的 voice agent。  
\- \*\*價值 (Value)\*\*：降低 interruption 與 dead air，讓深度任務不阻塞自然對話。  
\- \*\*漏洞利用 (Exploit/How)\*\*：  
  1\. 使用 WebRTC 建立音訊 transport。  
  2\. 建立專用 Go media frontend，只做 frame routing、timing 與 backpressure。  
  3\. 將 voice model session 設為 stateful continuous inference。  
  4\. 透過 async RPC 委派 frontier model 與 tools。  
  5\. Session start 時預建 frontier inference session 與 prompt cache。  
  6\. 實作 replacement instance warmup、parallel prefill 與 atomic cutover。  
  7\. 維護 provisional transcript queue 與 finalized transcript store。  
  8\. 以 WARP/Instant Connect 或同等 protocol optimization 縮短 startup。  
  9\. 使用 shadow production traffic 測試 long sessions、reconnects、disconnects、regional routing。  
\- \*\*工具集 (Toolset)\*\*：  
  \- WebRTC、Go、Pion/libwebrtc、DTLS 1.3、SCTP、QUIC concepts、distributed tracing、session store、load generator。  
\- \*\*影子技巧\*\*：將容量單位從「requests/sec」改為「可在每一 frame deadline 內維持的 concurrent sessions」。  
\- \*\*連結\*\*：← \[\[S1\]\], \[\[G1\]\]

\#\#\# E1：Critical Path Purity 法則  
\- \*\*法則內容\*\*：即時系統的可靠性，取決於 critical path 上最慢且最不可控的依賴。  
\- \*\*推論/啟示\*\*：模型越強不代表 voice experience 越自然。真正的 moat 是 stateful inference、媒體傳輸、session migration、protocol optimization 與 production rollout 的整體協作。  
\- \*\*支撐證據\*\*：← \[\[N1\]\], \[\[D1\]\], \[\[D2\]\], \[\[D3\]\], \[\[D5\]\], \[\[D6\]\], \[\[T1\]\], \[\[G1\]\]
