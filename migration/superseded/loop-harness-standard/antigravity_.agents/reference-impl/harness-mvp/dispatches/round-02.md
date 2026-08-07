# dispatch round-02 — SC1 收尾：修 pytest import 路徑，verify 轉綠

- driver: codex gpt-5.4-mini + effort medium（機械/單檔級）
- 判官已診斷根因（見 PLAN round 01 verdict）：tests 缺 conftest.py，`from src.envelope import ...` collection 炸

## 給 driver 的逐字 brief
你是 harness-mvp round-02 fresh driver。工作目錄 /Users/neon/antigravity/prototype/2026-07-19-ai-engineer-dr/harness-mvp/。
1. 讀 PLAN.md 的 round 01 verdict（失敗根因已診斷）。
2. 最小修：新增 `tests/conftest.py`（把 repo root 插入 sys.path，讓 `from src.x import ...` 可解析）。**不改 src/ 任何檔、不改既有 test 內容、不弱化 verify.sh。**
3. 真跑 `bash verify.sh --fast`，**必須 exit 0**；再真跑 `bash verify.sh`（full），回報兩個真實 exit code。
4. PLAN.md 追加一行 `- round 02 outcome: <一句話+兩個 exit code>`。
完成回報：兩個 exit code + 新增檔案。若修後仍紅，原樣回報 pytest 輸出，不得為過閘改測試或 src。
