# dispatch round-11 — OF-2 整改：W≥N 守衛測 + W<N 漏殺對照測
- driver: codex gpt-5.4-mini + effort medium（機械補測級）
## 給 driver 的逐字 brief
你是 harness-mvp round-11 fresh driver。工作目錄 /Users/neon/antigravity/prototype/2026-07-19-ai-engineer-dr/harness-mvp/。
1. 讀 PLAN.md 的 M5 design-verdict 行（OF-2 定義）、src/gates.py:22-27（L3Config __post_init__ 守衛）、tests/test_sc5.py。
2. 在 tests/test_sc5.py **新增**（不改既有 case）兩個測試：(a) `pytest.raises(ValueError)` 斷言 `L3Config(duplicate_window < max_interleaving)` 被 fail-fast 拒絕；(b) W<N 漏殺對照測——用**繞過守衛的方式不可行**，故改為：以合法最小 W=N 配置證明 N 元交錯在門檻步準時殺，再以 N+1 元交錯（超出 W=N 視窗）證明**漏殺真實發生**（跑滿步數未殺）＝UK5 失效邊界的回歸錨。**不改 src、不改既有測試、不弱化 verify.sh、不動 DESIGN-SCORE.md。**
3. 真跑 pytest（貼尾行原文）+ verify.sh --fast + full（兩真實 exit code）；PLAN.md 追加 round 11 outcome（含尾行原文）。
完成回報：pytest 尾行原文、兩 exit code、新增 case 名。紅了原樣回報。
