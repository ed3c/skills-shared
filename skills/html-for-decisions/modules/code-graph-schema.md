# 原生 Code Graph schema

## 目的與邊界

`code_graph` 是決策包的一級可選輸入：它讓 reviewer 搜尋 symbol／payload／endpoint、沿 edge
看 evidence 與 reach，並從 node 回到 SHA／path／line。它是 **review index**，不是裁決來源；
Markdown SSOT 沒寫的 invariant 狀態，Graph 不得自行新增或改寫。

```text
Markdown SSOT ──► 裁決／因果／UNKNOWN ───────────────┐
                                                     ├──► package_markdown_email.py
Code Graph JSON ─► node／edge／evidence review index ─┘              │
                                                                    ├──► self-contained HTML
validator ───────► ID／端點／evidence／critical closure              ├──► ZIP＋manifest
                                                                    └──► EML＋verification report
```

Graph 可以索引 STATIC、SANDBOX、PROD 等 evidence，但不能把「有 node」升格成 runtime 已發生，
也不能把 synthetic session 算成真實 agent coverage。沒有 deployment receipt 時仍是
`Deployed=UNKNOWN`。

## Bundle config

```json
{
  "code_graph": {
    "path": "code-graph/review-graph.json",
    "label": "Code Review Graph",
    "as": "code-graph/review-graph.json",
    "verification_report": "code-graph/review-graph.verification.json",
    "verification_as": "code-graph/review-graph.verification.json"
  }
}
```

| 欄位 | 必要 | 意義 |
|---|---:|---|
| `path` | 是 | JSON source；相對於 config。 |
| `label` | 否 | HTML tab 標籤，預設 `Code Graph`。 |
| `as` | 否 | ZIP 內 graph 路徑，預設 `code-graph/<原檔名>`。 |
| `verification_report` | 否 | 把 deterministic report 另寫到此路徑。即使省略，report 仍進 ZIP。 |
| `verification_as` | 否 | ZIP 內 report 路徑。 |

`as`／`verification_as` 禁止 absolute path、`..` 與目錄結尾；兩者不得碰撞，也不得與
`extras` 同名。Graph 與 extras 一起進 redaction preflight。

## 穩定 v1 seam

renderer 接受 `schema_version: "1.x"` 家族目前共同的穩定面；producer-specific 欄位會保留在
內嵌 JSON 與 ZIP，但共用 renderer 不替它們發明語意。

### 必要 top-level

| 欄位 | 形狀 | Fail-closed 規則 |
|---|---|---|
| `schema_version` | string | 缺席或非 string 即拒絕。 |
| `title` | non-empty string | Graph 分頁標題。 |
| `nodes` | object array | 不得為空；node ID 唯一。 |
| `edges` | object array | edge ID 唯一；source／target 必須存在。 |
| `evidence` | object array | evidence ID 唯一；所有引用必須存在。 |

### Node

`id`、`kind`、`label`、`critical`、`reach[]`、`evidence_ids[]`、`location`、`metadata`。
`location` 可為 `null` 表示 virtual／negative node；若非 null，至少含
`repo`、`sha`、`path`、`start_line`、`end_line`。review excerpt 放
`metadata.snippet`；它是節錄，不能宣稱完整原文。

### Edge

`id`、`kind`、`source`、`target`、`critical`、`reach[]`、`evidence_ids[]`。
critical edge 的 evidence 不得為空。唯一例外是 `AFFECTS_INVARIANT` 結構邊：target 必須是
`business_invariant`，且 source node 已掛 evidence；這兼容 v1.1 producer 把「subject 屬於哪個
invariant」表成結構邊，而不把它冒充新的觀測證據。renderer 以 source／target 建可選取的方向邊；
`MISSING`／`VIOLATE`／`REFUTE` 類 kind 會用缺口線型，但顏色不替代文字 label。

### Evidence

穩定欄位是 `id`、`reach`、`method`、`status`、`summary`、`source`、`authority`、
`environment_class`。producer 可另帶 `details`／`observed_at`；共用面只展示，不提升權威。

### 可選 top-level

- `scope.business_boundary`／`scope.exclusions`／`scope.synthetic`；
- `snapshot`；
- `invariants[]` 與 `diagnostics[]`；
- `agent_sessions[]`：若 key 缺席顯示 `UNKNOWN`，synthetic scope 顯示 `SYNTHETIC_ONLY`；
- `view.positions`／`view.width`／`view.height`；
- `invariant_events`、`communities`、`closure`、`build_report`、`manifest` 等 producer extension。

## Layout 與互動

有完整 `view.positions` 時照 producer layout；缺 layout 時先用 `metadata.visual_stage`，沒有
stage 再用 edge topology depth，節點 ID 排序確保 deterministic。這個 fallback 是可讀投影，
不是 AST 控制流宣稱。

原生頁面提供：critical-only、全文搜尋、lane/stage filter、agent-session overlay、directory／
symbol tree、node source detail、edge evidence detail。手機版把三欄堆疊；整頁不得水平 overflow，
大 graph 只在自己的 panel 內捲動。

## 驗證輸出

verification report 固定列出 schema version、node／edge／critical edge／evidence／invariant 數、
各 reach edge 數、agent scope、deployment 與 errors。`ok=false` 時 CLI 退出 1，不得寫 HTML、
ZIP、EML 或 outer manifest。
