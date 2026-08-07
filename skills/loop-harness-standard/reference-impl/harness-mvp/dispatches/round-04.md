# dispatch round-04 — 修 SC5 語義回歸：test_sc1 與 test_sc5 必須同時綠

- driver: codex gpt-5.4 + effort medium
- 判官診斷：round-03 對 gates.py 的 window/count 重構讓 test_sc1.py::test_sc1_l3_interleaved_duplicate_uses_per_signature_window 的參數組合不再觸發 dup kill（回歸）。SC5 判準（門檻步準時殺）與 SC1 既有測試語義**必須統一滿足**。

## 給 driver 的逐字 brief
你是 harness-mvp round-04 fresh driver。工作目錄 /Users/neon/antigravity/prototype/2026-07-19-ai-engineer-dr/harness-mvp/。
1. 讀 PLAN.md round 03 verdict、src/gates.py、tests/test_sc1.py（尤其 :76 交錯測試的參數與期望）、tests/test_sc5.py。
2. 修 src/gates.py：讓 **test_sc1 全部 + test_sc5 全部（10/10）同時綠**。**絕不改任何測試檔**（兩份測試都是已接受判準；若你認為兩者數學上不可同時滿足，停下來在回報裡證明給判官，不要改測試）。
3. 真跑 `venv/bin/python -m pytest tests -q`，**把尾行原文（"N passed"）逐字貼進回報**；再跑 `bash verify.sh --fast` 與 `bash verify.sh` 各貼真實 exit code。
4. PLAN.md 追加 `- round 04 outcome: <一句話+pytest 尾行原文+兩 exit code>`。
完成回報：pytest 尾行原文、兩 exit code、gates.py 改動一句話。紅了原樣回報。
