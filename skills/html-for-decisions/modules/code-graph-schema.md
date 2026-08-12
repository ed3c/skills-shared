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

若 bundle 的主要工作面就是 Code Graph，可在 bundle config 設
`"default_view": "codegraph"`。這只改首頁投影，不改 Markdown／graph 的真相順位。

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

#### Review-grade metadata（可選 extension）

需要逐 node code review 時，producer 可在 `metadata` 加入下列呈現欄位；缺席欄位會顯示
UNKNOWN，renderer 不自行補結論：

```json
{
  "comparison_status": "MISSING_IN_IOS",
  "review": {
    "summary": "這個節點在決策中的角色",
    "observation": "source 直接可見的事",
    "inference": "由觀察推導、仍可能被推翻的事",
    "proves": ["此證據能證明什麼"],
    "does_not_prove": ["不能證明 runtime／deployment"],
    "risks": ["反證條件或旁路"],
    "recommendation": "下一個可證偽動作",
    "counterpart": "android:peer-node"
  },
  "reach_assessment": {
    "state": "ASSERTED",
    "settled": false,
    "independent_reaches": ["STATIC"],
    "next_reach": "SANDBOX"
  }
}
```

`comparison_status` 是 producer domain vocabulary；常見值為 `MISSING_IN_ANDROID`、
`MISSING_IN_IOS`、`SHARED_GAP`、`PARITY`。它是比較鏡頭，不是安全等級。例如 Android 缺少
PIN payload parity，不代表 iOS 已具備 AccountKey rotation authorization。

`reach_assessment.settled=true` 仍須符合宿主方法論的獨立抵達判準；renderer 只呈現，不替
producer 裁決。`review.counterpart` 若指向另一 node，Code Review 視窗會提供一跳比較。

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
- `decision_queue[]`：`id`／`question`／`owner`／`default`／`status`，把未裁決項目顯示在 graph
  狀態區；它仍須來自 Markdown SSOT；
- `review_paths[]`：`id`／`label`／`node_ids[]`，提供不依賴工作記憶的 guided traversal；
- `invariant_events[]`：`invariant_id`／`state` 或 `prior_state`＋`next_state`／`reach`／`at`／`basis`／必填 `graph_delta.{added_edges,invalidated_edges}`，另可帶 `note`。同一 invariant 的事件時間與 state chain 必須單調且閉合，delta 只能引用已存在的 edge。事件只 append、不覆寫；全域 slider 用它重建可見 edge revision，node review 則顯示該 invariant 的局部時間線；
- `view.primary_node_ids[]`（可選）：把大型 evidence graph 的指定節點投影成第一閱讀面；每個 primary node 都必須存在且具有 `view.positions`。filter、時間軸與 review 仍直接操作這些 canonical nodes，不得另造 project-only canvas。
- `communities`、`closure`、`build_report`、`manifest` 等 producer extension。

## Layout 與互動

有完整 `view.positions` 時照 producer layout；缺 layout 時先用 `metadata.visual_stage`，沒有
stage 再用 edge topology depth，節點 ID 排序確保 deterministic。這個 fallback 是可讀投影，
不是 AST 控制流宣稱。

原生桌面頁面使用 `250px / minmax(500px,1fr) / 340px` 三欄：directory／symbol tree 是灰階
導航，中央是 Reach-aware graph，右側是 node／edge evidence。全文搜尋、Agent overlay、Critical
slice、lane/stage、雙向 comparison 與 guided path 位於同一 toolbar；Refutation history slider
位於 graph 下方。線型／粗細只編碼 STATIC／SANDBOX／PROD，顏色只編碼 UNKNOWN／survived／
refuted，node 光暈只編碼 reach 集合大小；agent-session overlay 是預測子，不得改變 evidence 或
truth state。

點 node／edge 先更新右欄，讓 reviewer 不離開圖就能比較 observation、inference、能證明、不能
證明與 reach assessment；明確點 `Open full Code Review` 才開 modal 深讀。選中 guided path 時，
上下步與進度仍必須在 modal 內，不能被 backdrop 隔在背景。背景捲動會鎖住，避免 sticky／長內容
互相覆蓋。窄畫面三欄降成單欄，手機版 review 視窗使用全螢幕；整頁不得水平 overflow，大 graph
只在自己的 panel 內捲動。

## 驗證輸出

verification report 固定列出 schema version、node／edge／critical edge／evidence／invariant 數、
各 reach edge 數、agent scope、deployment 與 errors。`ok=false` 時 CLI 退出 1，不得寫 HTML、
ZIP、EML 或 outer manifest。
