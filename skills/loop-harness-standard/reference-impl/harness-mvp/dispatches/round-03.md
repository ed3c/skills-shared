# dispatch round-03 — 關 SC5（L3 重複偵測完整面）

- driver: codex gpt-5.4 + effort medium（整合級）
- 前情: SC1 已綠 commit（round-01 骨架 + round-02 conftest）；gates.py 已有 sig_with_result/W≥N 校驗/交錯測試

## 給 driver 的逐字 brief
你是 harness-mvp round-03 fresh driver。工作目錄 /Users/neon/antigravity/prototype/2026-07-19-ai-engineer-dr/harness-mvp/。
1. 讀 PROMPT.md（本輪**只關 SC5**）、PLAN.md（round 01-02 軌跡）、src/gates.py、tests/test_sc1.py（既有覆蓋）。
2. SC5 完整判準（對照 DESIGN-SCORE 行 16-18 錨）：`sig_with_result` 為預設簽名；滑動視窗 `W>=N` 校驗；**per-signature early kill 對「連續重複」與「交錯重複」兩型都在門檻步準時殺**；合法輪詢（結果遞變）與合法重試（結果不同）**零誤殺**。
3. 差距分析後補齊：缺的行為補進 src/gates.py（最小改動），缺的回歸測試新增 `tests/test_sc5.py`（連續重複殺/交錯殺/輪詢零誤殺/重試零誤殺，至少 4 case）。**不改既有測試、不弱化 verify.sh、不動 DESIGN-SCORE.md。**
4. 真跑 `bash verify.sh --fast` 與 `bash verify.sh`，兩者 exit 0 才算完；PROMPT.md 勾 SC5；PLAN.md 追加 `- round 03 outcome: <一句話+兩 exit code>`。
完成回報：兩真實 exit code、gates.py 改了什麼（或「已覆蓋無需改」）、新測試 case 清單。紅了原樣回報不硬修。
