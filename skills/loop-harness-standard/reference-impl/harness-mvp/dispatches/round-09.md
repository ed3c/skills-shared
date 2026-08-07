# dispatch round-09 — 關 SC7（單 write 公開 API 回歸完整面）
- driver: codex gpt-5.4-mini + effort medium
## 給 driver 的逐字 brief
你是 harness-mvp round-09 fresh driver。工作目錄 /Users/neon/antigravity/prototype/2026-07-19-ai-engineer-dr/harness-mvp/。
1. 讀 PROMPT.md（本輪只關 SC7）、PLAN.md、src/ledger.py、tests/test_sc1.py（:95 已有單 write monkeypatch case）。
2. SC7 判準（DESIGN-SCORE 行 12 錨 §7.1 UK6）：每 record 序列化整行（含 \n）後**單次 write**；**公開 API 結構上不可能分段寫**（呼叫端拿不到「寫半行」的入口）。
3. 差距分析後補齊（最小改或「已覆蓋無需改」）＋tests/test_sc7.py（≥3 case：多 record 各恰一次 os.write 且各含結尾 \n、Ledger 公開介面無 partial-write 方法〔inspect 斷言〕、超長 record 仍單次 write）。不改既有測試、不弱化 verify.sh、不動 DESIGN-SCORE.md。
4. 真跑 pytest（貼尾行原文）+ verify.sh --fast + full（兩真實 exit code）；PROMPT.md 勾 SC7；PLAN.md 追加 round 09 outcome（含尾行原文）。
完成回報：pytest 尾行原文、兩 exit code、src 是否需改、新 case 清單。紅了原樣回報。
