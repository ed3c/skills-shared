# dispatch round-01 — SC1 曳光彈（M3 種子新鮮實現 + 首條回歸測試）

- driver: codex gpt-5.5 + effort high（設計判斷級：首輪定 L0/L2/L3/L4 骨架）
- 派工時間: 2026-07-19；判官: 主會話 Opus（跨家族）
- 種子 provenance（前提閘 2）: SYNTHESIS golden-path **新鮮實現**——非搬 Phase G 拋棄碼

## 給 driver 的逐字 brief

你是 harness-mvp 小迴圈 round-01 的 fresh driver。讀：
1. PROMPT.md（Mission + SC1–SC8；本輪**只關 SC1**）
2. PLAN.md（answer-key 已凍結；不得改 DESIGN-SCORE.md 任何格）
3. DESIGN-SCORE.md（22 格 answer-key＝設計 SSOT 對照表；你的實作必須不與任何格衝突）
4. CLAUDE.md（迴圈規則 1–4，違反即停）
5. 設計細節錨（實作時直接讀）：/Users/neon/antigravity/gemini_research/aiDotEngineer/_synthesis/SYNTHESIS-harness.md §6:292-305（統一 envelope schema 逐欄）＋§7/§7.1（UK1-6 實測裁決的實作要求）

本輪任務（SC1 曳光彈）：在 src/ 新鮮實現最小垂直鏈——
- `src/envelope.py`：統一 envelope（id/parentId/loop_layer/task_ref/event/exec{command,exit_code,result_snapshot,error_snapshot}/handoff/budget/freshness 九欄，dict 構造 + 校驗）
- `src/ledger.py`：append-only JSONL 帳本——**每 record 序列化整行（含 \n）後單次 os.write()**（UK6 鐵律；公開 API 結構上不可能分段寫）
- `src/gates.py`：L3 最小閘（max_iterations pre-flight + budget ladder + sig_with_result 滑動視窗 W≥N per-signature kill；事後歸因優先序 budget>dup>max_iterations）＋ L4 最小閘（exit_code≠0 且 handoff 未處理 → 阻斷）
- `src/loop.py`：L0 薄核心 while 迴圈——只管工具執行狀態/重試/事件流，每步後控制交還 deterministic code（L3 判續/停）；工具執行本輪用注入的假 executor（callable），無 LLM
- `tests/test_sc1.py`：SC1 回歸測試——一個 envelope 進帳本 → 閘檢查 → 確定性 exit code 出；含至少一個壞 case（exit_code≠0 未處理 handoff 被 L4 擋）
- PROMPT.md 把 SC1 勾成 `[x]`；PLAN.md 追加 `- round 01 outcome: ...` 一行

硬約束：純 stdlib；不改 tests/ 既有檔（本輪無既有測試）；不弱化 verify.sh；不動 DESIGN-SCORE.md；跑 `bash verify.sh --fast` 須 exit 0 才算完。完成回報：verify --fast exit code、新增檔案清單、SC1 實作與 answer-key 哪幾格對應。
