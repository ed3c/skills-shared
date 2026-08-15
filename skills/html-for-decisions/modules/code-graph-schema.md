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
  "difference_summary": "缺少 typed upload gate",
  "node_category": "ENTRY_GUARD",
  "node_tier": "FRONTEND",
  "root_cause_analysis": {
    "role": "CONTRIBUTING_FACTOR",
    "problem": "此節點在因果鏈中暴露的問題",
    "direct_mechanism": "輸入如何在此處造成或傳遞結果",
    "systemic_cause": "跨節點、跨邊界的系統層原因",
    "escape_reason": "為何既有 review／test 未攔下",
    "business_impact": "受影響的業務不變量",
    "evidence_boundary": "目前證據能到哪裡、不能到哪裡",
    "next_falsification": "下一個可推翻此分析的動作"
  },
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
  },
  "investigation_case": {
    "case_id": "CASE-001",
    "title": "由假說到實測的問題調查",
    "current_verdict": "LOCAL_SETTLEMENT_ONLY",
    "truth_scope": "只收斂被實測的 client lane",
    "truth_effect": "LOCAL_SETTLEMENT_ONLY",
    "root_cause": "已由證明鏈支持的因果機制",
    "proof_chain": [
      {
        "step": "①",
        "phase": "修正前",
        "reach": "PROD",
        "result": "FAIL",
        "observation": "原始觀測",
        "interpretation": "這一步能支持的最窄判讀",
        "evidence_ids": ["ev-prod-before"]
      }
    ],
    "self_refutation": {
      "mistaken_observation": "曾用哪個觀察推翻假說",
      "why_it_was_wrong": "觀察對象與待證對象為何不同源",
      "refuted_by": "後來由哪個獨立抵達推翻"
    },
    "fixes": ["已實施修正或現行機制"],
    "difference_from_confirmed_fix": "另一平台與已證實修正的精確差異",
    "next_falsification": "下一個會讓結論轉紅的實驗",
    "follow_up_analysis": [
      {
        "target": "下一個系統邊界",
        "node_ids": ["api:write"],
        "question": "仍待回答的問題",
        "current_answer": "目前抵達層級允許的答案"
      }
    ]
  }
}
```

`comparison_status` 是 producer domain vocabulary；常見值為 `MISSING_IN_ANDROID`、
`MISSING_IN_IOS`、`SHARED_GAP`、`PARITY`。它是比較鏡頭，不是安全等級。例如 Android 缺少
PIN payload parity，不代表 iOS 已具備 AccountKey rotation authorization。

`difference_summary` 是顯示在 node／edge 上的短提示，建議不超過 32 個字元；它只回答「這裡
有何值得注意的差異」，不得承載證據或完整裁決。點選後的 `review` 才是完整分析面。差異可以是
同平台內相對於業務契約的缺口，不要求畫成 iOS／Android 的兩欄比較。

`metadata.node_category` 是 review role，不是 source-language AST kind。建議使用穩定的有限集合：
`ENTRY_GUARD`、`DECISION_POLICY`、`CEREMONY_CALL`、`DATA_PAYLOAD`、`SERVICE_BOUNDARY`、
`STATE_STORE`、`INVARIANT_TRUTH`、`GAP_RISK`、`COVERAGE_MATRIX`、`EVIDENCE_RECEIPT`。
renderer 以右上文字標籤表示分類。`metadata.node_tier` 則只接受 `FRONTEND`、`BACKEND`、
`SHARED_ANALYSIS`，用圓角／直角／虛線外形表示部署層級；底色仍只保留給 node 的最高抵達層級。

`metadata.root_cause_analysis` 是逐節點因果分析，八個欄位必須一起出現。`role` 不代表每個 node
都是根因：允許 `ROOT_CAUSE`、`CONTRIBUTING_FACTOR`、`CONTROL_OR_BOUNDARY`、`EVIDENCE`、
`INVARIANT`、`COVERAGE_INDEX`。這個區分避免把 receipt、matrix 或待證 invariant 誤畫成故障來源。
`evidence_boundary` 與 `next_falsification` 必須保守；單一 STATIC node 不得在 RCA 內偷升格為 runtime
或 production root cause。面向繁中使用者的 producer 可另帶 `review_zh_hant`；頁面 chrome 使用繁體
中文，AST、LSP、Code Review、Payload、Store 等英文專有名詞保留英文。

`reach_assessment.settled=true` 仍須符合宿主方法論的獨立抵達判準；renderer 只呈現，不替
producer 裁決。`review.counterpart` 若指向另一 node，Code Review 視窗會提供一跳比較。

`metadata.investigation_case` 用在「結論曾被推翻，而且修正後又由新抵達收斂」的節點。它不是
`root_cause_analysis` 的同義副本：RCA 是目前因果快照；investigation case 必須保存
假說 → 反證／自我推翻 → 實驗 → 修正 → 重複驗證 → 後續系統邊界的歷史。每個 proof step
自己的 `reach`、`result`、`observation`、`interpretation` 必須分開，禁止用一個最終 `PASS`
回寫抹掉先前失敗。`current_verdict` 的 settlement 只對 `truth_scope` 生效；例如 client
`PROD×2` 不能讓仍可覆寫的 server boundary 或只有 STATIC 的另一 client 自動變成 SETTLED。
`follow_up_analysis.node_ids[]` 只提供 graph traversal，不會讓 Agent retrieval hit 成為 evidence。

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
- `view.default_graph_view`＋`view.graph_views[]`：每個 view 必含唯一 `id`、非空 `label`、
  `node_ids[]`、`edge_ids[]`、完整 `positions` 與正數 `width`／`height`。所有 edge endpoint 必須
  留在該 view 的 node 集合內；用它表示各自完整且閉合的系統圖，而不是把兩個平台塞進比較畫布；
- `view.graph_views[].routes`（可選）：以 edge ID 為 key 的折線點陣列；一旦提供就必須恰好覆蓋
  該 view 全部 `edge_ids`，每條至少兩個數值座標。producer 可用它保證 connector 不穿無關 node；
- `decision_queue[]`：`id`／`question`／`owner`／`default`／`status`，把未裁決項目顯示在 graph
  狀態區；它仍須來自 Markdown SSOT；
- `review_paths[]`：`id`／`label`／`node_ids[]`，提供不依賴工作記憶的 guided traversal；
- `invariant_events[]`：`invariant_id`／`state` 或 `prior_state`＋`next_state`／`reach`／`at`／`basis`／必填 `graph_delta.{added_edges,invalidated_edges}`，另可帶 `note`。同一 invariant 的事件時間與 state chain 必須單調且閉合，delta 只能引用已存在的 edge。事件只 append、不覆寫；全域 slider 用它重建可見 edge revision，node review 則顯示該 invariant 的局部時間線；
- `view.primary_node_ids[]`（可選）：把大型 evidence graph 的指定節點投影成第一閱讀面；每個 primary node 都必須存在且具有 `view.positions`。filter、時間軸與 review 仍直接操作這些 canonical nodes，不得另造 project-only canvas。
- `communities`、`closure`、`build_report`、`manifest` 等 producer extension。

## Layout 與互動

有 `view.graph_views[]` 時，平台／系統切換先選定一張完整 canonical subgraph；預設不得再套
critical-only 截斷。完整 `positions`／`routes` 由 renderer 原樣採用。缺 layout 時先用
`metadata.visual_stage`，沒有
stage 再用 edge topology depth，節點 ID 排序確保 deterministic。這個 fallback 是可讀投影，
不是 AST 控制流宣稱。

原生桌面頁面使用 `250px / minmax(500px,1fr) / 340px` 三欄：directory／symbol tree 是灰階
導航，中央是 Reach-aware graph，右側是 node／edge evidence。全文搜尋、Agent overlay、Critical
slice、lane/stage、named graph view 與 guided path 位於同一 toolbar；Refutation history slider
位於 graph 下方。線型／粗細只編碼 STATIC／SANDBOX／PROD，顏色只編碼 UNKNOWN／survived／
refuted，node 光暈只編碼 reach 集合大小；agent-session overlay 是預測子，不得改變 evidence 或
truth state。

節點底色固定為 reach channel：空集合＝UNKNOWN、DOCUMENT、STATIC、SANDBOX、PROD 依序提升；
同一 node 有多個 reach 時顯示最高一層，但 review detail 仍列出全集。這個顏色不能被 category、
comparison status、tier 或 invariant state 覆蓋。密圖的可見 edge 必須有獨立透明 hit-area；hover
node 時只凸顯 incident edges，hover edge 時只凸顯該 connector、source、target，且箭頭色跟隨 edge
invariant state。hover 是暫態：離開後回復先前固定狀態；點 node／edge 會固定相同 focus，只有點 SVG
圖面空白處或重設檢視才取消，不能因滑鼠離開或點 detail 內容而遺失。

`agent_sessions[]` 可由 producer 提供 `id`／`agent`／`touched_node_ids[]`；也可由使用者在頁面
本機匯入 Claude Code／Codex CLI JSONL。local importer 只以 node ID、source path、repo/path 與
足夠長的 symbol label 建 retrieval hit，session 原文不寫回 graph、不進 ZIP、不成為 evidence，
`truth_effect` 永遠是 `NONE`。MCP adapter 若存在，也必須先約分成相同 session receipt schema。

點 node／edge 先更新右欄，讓 reviewer 不離開圖就能比較 observation、inference、逐節點 RCA、
能證明、不能證明與 reach assessment；明確點「開啟完整 Code Review」才開 modal 深讀。選中 guided path 時，
上下步與進度仍必須在 modal 內，不能被 backdrop 隔在背景。背景捲動會鎖住，避免 sticky／長內容
互相覆蓋。窄畫面三欄降成單欄，手機版 review 視窗使用全螢幕；整頁不得水平 overflow，大 graph
只在自己的 panel 內捲動。

## 驗證輸出

verification report 固定列出 schema version、node／edge／critical edge／evidence／invariant 數、
各 reach edge 數、agent scope、deployment 與 errors。`ok=false` 時 CLI 退出 1，不得寫 HTML、
ZIP、EML 或 outer manifest。
