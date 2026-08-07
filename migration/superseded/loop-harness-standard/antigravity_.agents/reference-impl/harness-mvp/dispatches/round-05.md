# dispatch round-05 — 關 SC3（L2 帳本 envelope 欄位完整保存）

- driver: codex gpt-5.4 + effort medium

## 給 driver 的逐字 brief
你是 harness-mvp round-05 fresh driver。工作目錄 /Users/neon/antigravity/prototype/2026-07-19-ai-engineer-dr/harness-mvp/。
1. 讀 PROMPT.md（本輪**只關 SC3**）、PLAN.md、src/envelope.py、src/ledger.py、既有 tests。
2. SC3 判準（對照 DESIGN-SCORE 行 9-11 錨）：帳本寫入的統一 envelope **九欄完整**（id/parentId/loop_layer/task_ref/event/exec{command,exit_code,result_snapshot,error_snapshot}/handoff/budget/freshness）；append-only + DAG parentId 譜系可重讀；大物件不進帳本（URI/hash 指針欄位語義）。
3. 差距分析後補齊 src（最小改）＋新增 tests/test_sc3.py（≥4 case：九欄 round-trip 完整、parentId 鏈重讀、append-only 不覆寫、缺欄 fail-fast 拒收）。**不改既有測試、不弱化 verify.sh、不動 DESIGN-SCORE.md。**
4. 真跑 pytest（貼尾行原文）+ verify.sh --fast + full（貼兩真實 exit code）；PROMPT.md 勾 SC3；PLAN.md 追加 round 05 outcome（含尾行原文）。
完成回報：pytest 尾行原文、兩 exit code、src 改動一句話、新 case 清單。紅了原樣回報。
