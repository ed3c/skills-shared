# dispatch round-08 — 關 SC2（L0 薄核心純度）
- driver: codex gpt-5.4 + effort medium
## 給 driver 的逐字 brief
你是 harness-mvp round-08 fresh driver。工作目錄 /Users/neon/antigravity/prototype/2026-07-19-ai-engineer-dr/harness-mvp/。
1. 讀 PROMPT.md（本輪只關 SC2）、PLAN.md、src/loop.py 全文、既有 tests。
2. SC2 判準（DESIGN-SCORE 行 7-8 錨 §1 L0:36-43）：L0 核心**只做**步進迴圈/工具執行狀態管理/錯誤重試/事件流發射/每步後確定性交還閘——**不含** Plan Mode、不含 sub-agent 編排、不含任何 LLM 決策內嵌；輸入=dispatch 封包+ledger 指標、輸出=事件流+工具結果。錯誤重試語義：executor 拋異常→記錄→按 maxAttempts 重試→耗盡則以非零 exit_code envelope 進帳本（讓 L4 裁）。
3. 差距分析後補齊 src/loop.py（最小改；重試語義若缺補上）＋tests/test_sc2.py（≥4 case：事件流順序完整、executor 異常重試後成功、重試耗盡走 L4 阻斷、L0 模組零 planning/orchestration 符號〔用 import/屬性斷言驗純度〕）。不改既有測試、不弱化 verify.sh、不動 DESIGN-SCORE.md。
4. 真跑 pytest（貼尾行原文）+ verify.sh --fast + full（兩真實 exit code）；PROMPT.md 勾 SC2；PLAN.md 追加 round 08 outcome（含尾行原文）。
完成回報：pytest 尾行原文、兩 exit code、src 改動一句話、新 case 清單。紅了原樣回報。
