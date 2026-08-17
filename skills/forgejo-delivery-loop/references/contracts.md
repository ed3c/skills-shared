# Forgejo loop contracts

## 分工

| 層 | owner | 可以做 | 不可以做 |
|---|---|---|---|
| 大迴圈 | 本 skill 的操作層（`modules/forgejo-operations.md`） | 優先序、WIP、降級、下一個小迴圈提示 | 批次 mutation、repo 寫入、admission |
| 小迴圈外部操作 | 本 skill 的操作層（`modules/forgejo-operations.md`） + existing Chrome | 單一 issue／PR／merge 的預檢、操作、回讀 | 改 source、跳 gate、複製私密語料 |
| repo 末端實作 | output repo 的 `repo-terminal-operator` | terminal slice、CQ、production-use、commit | Forgejo／GitHub／cloud admission |
| 終態契約 | 本 skill 的 `contracts/`＋`scripts/issue_state.py` | request／observation／receipt 的形狀與跨欄語義 | UI 操作、admission 推斷 |

## 資料流

```text
grill／DR／GCR decision
  -> large-loop queue projection
  -> one typed Forgejo request
  -> existing Chrome auth or read-only API preflight
  -> one repo-local terminal operator
  -> focused CQ + production-use + molecular commit
  -> issue／PR／merge readback
  -> canonical readback receipt
  -> human admission
  -> next-mode prompt
```

## 正式契約

- `contracts/forgejo-terminal-issue-state-request.v2.schema.json`
- `contracts/forgejo-issue-state-observation.v1.schema.json`
- `contracts/forgejo-issue-state-readback-receipt.v1.schema.json`
- `scripts/issue_state.py`

這些契約與驗證器放在實際執行 mutation 的 skill 裡，避免索引指向不存在的中央 runtime。
schema 守序列化邊界；驗證器守跨欄不變量，並直接執行 authenticated GitHub／Forgejo read。
因此不能只做 JSON Schema 驗證或提交自填 observation 就執行 UI mutation／鑄造 verified receipt。

## 從 local_stack 經驗保留與拒絕的部分

來源（絕對路徑與 repo 身分見 `.skill-bindings/forgejo-delivery-loop/`）：

- 上游封存版 `forgejo-ops` skill 說明檔
- 上游 `forgejo-ops.sh` 執行腳本

保留：loopback version check、HTTP credential helper、API／UI 操作後回讀、錯誤快速失敗。

拒絕：硬編碼專案、改寫 `origin`、主工作樹切 branch、force push、
`--allow-unrelated-histories`、匿名 API 當登入、`SKIP_PUSH_GATE`、無界重試與 secret echo。

舊 Skill 已標為 `CONSOLIDATED`，因此它是 provenance，不是 runtime dependency。
