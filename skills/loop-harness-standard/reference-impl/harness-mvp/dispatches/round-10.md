# dispatch round-10 — 關 SC8（L4 確定性硬阻斷 + 代理節點 warning-only）
- driver: codex gpt-5.4 + effort medium
## 給 driver 的逐字 brief
你是 harness-mvp round-10 fresh driver。工作目錄 /Users/neon/antigravity/prototype/2026-07-19-ai-engineer-dr/harness-mvp/。
1. 讀 PROMPT.md（本輪只關 SC8，最後一個）、PLAN.md、src/gates.py（L4 現況）、既有 tests。
2. SC8 判準（DESIGN-SCORE 行 21 錨 §1 L4:83-94 + §6:290）：L4 對**確定性證據**（exit_code/機械檢查結果）失敗→**硬阻斷**；**代理節點（LLM-judge 型）證據→僅 warning 記錄、絕不硬阻斷**；畢業/merge 級判定保留人 admit（L4 不自動放行終局）。envelope 需能承載 judge-warning 事件（event.kind 或 handoff 欄語義，沿用既有 schema 不加欄）。
3. 差距分析後補齊 src/gates.py（最小改：加 proxy-evidence warning 路徑）＋tests/test_sc8.py（≥4 case：確定性失敗硬斷、proxy warning 不斷且留痕帳本、warning 與 hard-block 並存時硬斷贏、無 warning 通過）。不改既有測試、不弱化 verify.sh、不動 DESIGN-SCORE.md。
4. 真跑 pytest（貼尾行原文）+ verify.sh --fast + full（兩真實 exit code）；PROMPT.md 勾 SC8；PLAN.md 追加 round 10 outcome（含尾行原文）。
完成回報：pytest 尾行原文、兩 exit code、src 改動一句話、新 case 清單。紅了原樣回報。
