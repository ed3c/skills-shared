# dispatch round-07 — 關 SC6（停損歸因優先序完整面）
- driver: codex gpt-5.4-mini + effort medium（既有覆蓋大半，差距補齊型）
## 給 driver 的逐字 brief
你是 harness-mvp round-07 fresh driver。工作目錄 /Users/neon/antigravity/prototype/2026-07-19-ai-engineer-dr/harness-mvp/。
1. 讀 PROMPT.md（本輪只關 SC6）、PLAN.md、src/gates.py、src/loop.py、既有 tests（test_sc1 已有 budget>dup tie case）。
2. SC6 判準（DESIGN-SCORE 行 20 錨 §7 UK2）：事後歸因優先序 **budget > dup > max_iterations**；`max_iterations` 是 pre-flight 兜底（呼叫前檢查，不參與事後 tie）；三閘各自單獨觸發時歸因正確。
3. 差距分析後補齊 src（最小改或「已覆蓋無需改」）＋tests/test_sc6.py（≥3 case：三閘 tie 全順序驗證、max_iter pre-flight 單獨觸發歸因、dup 單獨觸發歸因）。不改既有測試、不弱化 verify.sh、不動 DESIGN-SCORE.md。
4. 真跑 pytest（貼尾行原文）+ verify.sh --fast + full（兩真實 exit code）；PROMPT.md 勾 SC6；PLAN.md 追加 round 07 outcome（含尾行原文）。
完成回報：pytest 尾行原文、兩 exit code、src 是否需改、新 case 清單。紅了原樣回報。
