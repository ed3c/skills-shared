# dispatch round-06 — 關 SC4（resume 純讀 JSONL 重建）
- driver: codex gpt-5.4 + effort medium
## 給 driver 的逐字 brief
你是 harness-mvp round-06 fresh driver。工作目錄 /Users/neon/antigravity/prototype/2026-07-19-ai-engineer-dr/harness-mvp/。
1. 讀 PROMPT.md（本輪只關 SC4）、PLAN.md、src/（loop/ledger/gates）、既有 tests。
2. SC4 判準（DESIGN-SCORE 行 13 錨 §7 UK4）：resume **純從磁碟 JSONL** 重建 iteration 計數／budget tokens 累計／duplicate-signature 視窗狀態／parentId 鏈——無隱藏記憶體狀態；重建後迴圈可續跑且閘行為與 kill 前一致（閘閾值由呼叫端重傳，重建須校驗一致性或顯式接受傳入值）。
3. 補齊 src（最小改）＋tests/test_sc4.py（≥4 case：中途硬斷後純讀重建續跑完、重建的 dup 視窗狀態使「斷點前+斷點後合計達門檻」的重複被準時殺、budget 累計不歸零、parentId 鏈完整）。不改既有測試、不弱化 verify.sh、不動 DESIGN-SCORE.md。
4. 真跑 pytest（貼尾行原文）+ verify.sh --fast + full（兩真實 exit code）；PROMPT.md 勾 SC4；PLAN.md 追加 round 06 outcome（含尾行原文）。
完成回報：pytest 尾行原文、兩 exit code、src 改動一句話、新 case 清單。紅了原樣回報。
