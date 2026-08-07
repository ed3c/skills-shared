---
name: repo-agent-native
description: |
  對一個可讀 code repo 做 source-anchored 業務不變量抽取 —— 9 階段(SCOPE→INGEST→INVARIANT→IMPLICIT-DEP→INDEX→AUDIT→SSOT→FEEDBACK)。
  用 grepai(trace／call-graph) ＋ ripgrep ＋ git 從源碼提三類不變量(Message／State／API Contract)＋負向不變量(確認不存在的假設)，
  並以「破盒推論」從 outgoing call 推導隱含依賴(未索引服務／共享狀態耦合／靜默失敗鏈／逾時鏈)。每個事實帶 Evidence Level(A／B／C／D)＋source_ref(檔：行)，
  無錨的散文不寫進 KB。產 source-anchored 不變量頁 → 經 indexing/ingest_repodoc_cli 進 antigravity KG(kind＝invariants)，
  與 repo-wiki-converge 的 Opus-judge 理解 wiki 正交(那條產散文理解、這條產確定性 typed 事實)。
  Use when：要把某 code repo 的真實契約／隱含依賴／失敗模式源碼級抽出並進 KB，而非只要一份理解 wiki。
  NOT for：產 repo 理解 wiki(用 repo-wiki-converge)、診斷反覆失敗的黑盒(用 repo-fullstack-debugger)。
---

> **這是 northstar `repo-agent-native` 的 antigravity retarget，不是原樣搬。** 命門＝抽取核心(9 階段／三類不變量／破盒推論／Evidence Level／source_ref 鐵律)一對一映；北極星專屬基座(rag-local KG／Serena(**連著但未 wire→條件式**，見 retarget-map)／hallucination_audit.py／ixsecurity／PG 編號)**無/未-wire 基座已拿掉並記錄** → [`modules/retarget-map.md`](modules/retarget-map.md)。know-why(破盒推論五步／OPBE／Evidence Level 分級細節) → [`modules/extraction-methodology.md`](modules/extraction-methodology.md)。
> **Source Code＝SSOT 鐵律**：任何進入 KB 的事實必須附帶 `source_ref`(檔案路徑 ＋ 行號)，否則視為幻覺、不寫入。無錨的「效率提升／已優化」＝ Half-Bridge 散文(Path B 紀律，錨 `path-b-reduction`)。

# repo-agent-native(antigravity)

## When to Use
- 有一個**可讀 code repo**(本地 clone；全歷史，never `--depth 1`)，要把它的**真實契約／隱含依賴／失敗模式源碼級**抽出來，比 repo-wiki-converge 的理解 wiki 更接地。
- 要回答「這服務的訊息契約／狀態機／API 分支到底是什麼、哪些假設其實不存在、哪個外呼會靜默失敗」——每個答案釘在 `檔：行`。

## Not For
1. **產 repo 理解 wiki／宏觀地圖** → `repo-wiki-converge`(Opus-judge 散文理解，非 typed 事實)。
2. **診斷反覆失敗的黑盒**(瀏覽器 DOM／repo 動態執行) → `repo-fullstack-debugger`。當靜態源碼**無法** A 級解析(runtime-only 行為)時，本 skill 交棒過去(見 §Handoff)。
3. **外部框架／版本能力 claim 的查證** → `external-verify`(非訓練記憶)。

## Evidence Level 分級(retarget 到 antigravity 真實工具)

| 等級 | 定義 | 抽取方式(antigravity 實base) | 範例 |
|------|------|------------------------------|------|
| **A** | 直接讀源碼 body | `git show`／Read 源檔 body | pubsub 函數 body 讀到 topic 常數 |
| **A-** | 追蹤路徑但非完整讀 body | `grepai_trace_callers` / `grepai_trace_graph` | 確認 handler 呼叫 publish |
| **B+** | 語義搜索命中 | `grepai_search` 命中片段 | 文件中找到 `nats.Publish` |
| **B** | 官方文檔／間接聲明 | README／`go.mod`／`package.json` | 依賴聲明 |
| **C** | 推測性類比 | 從其他服務類比(未讀本服務源碼) | 「可能用 NATS，因為別的服務用」 |
| **D** | 無來源猜測 | 現有假設、無源碼支撐 | 未讀源碼的 config 名 |

> antigravity **無 hallucination_audit.py 確定性污染閘**(北極星基座)。反幻覺改由三重人可核 SURFACE：① 每事實標 Evidence Level(C／D → 標記，不當事實寫)；② post-cutoff 外部 claim 過 `external-verify`；③ git-cite 或標 `unverified`(對齊 repo-wiki-converge 硬門檻)。**污染判定是 SURFACE 給人裁，非機器閘**——誠實記錄這個能力差距。

## 9 階段程序(確定性)

### S0 SCOPE
- 確認 target repo 路徑 ＋ `git -C <repo> rev-parse HEAD`(記 commit_hash，供 S8 漂移偵測)。
- 選 `<OUT>`＝中性 scratch 目錄(**非** TARGET 內，對齊 repo-wiki-converge)；產物落 `<OUT>/invariants/<slug>/`。
- 種子概念清單(要抽哪些契約／哪個子系統)——**可由 [repo-wiki-converge](../repo-wiki-converge/SKILL.md) 收斂 wiki 的子系統圖/`covers` 種子**(L1→L2 handoff)。**但 facts 仍源碼 A 級 + `source_ref`,wiki 散文不當事實源**(funnel 不倒置)。階梯 SSOT → [`kb-ingest/mastery-ladder.md`](../../../kb-ingest/mastery-ladder.md)。

### S1 INGEST(雙軌)
- **軌 A 語義／符號**：`grepai_index_status` 確認 target 在 grepai 索引內；不在則**先對 target 目錄跑 grepai 索引**(per-dir `config.yaml`)——antigravity 主 `.grepai/` 只索引自身源，第三方 target 須自建索引，否則 `grepai_search`／trace 打到 antigravity 自己的碼(污染)。
- **軌 B 全文**：`find <repo> -name '*.<ext>' -not -path '*/vendor/*' -not -path '*/node_modules/*'` 列檔；按需 Read。
- **分塊**：符號邊界 > 檔案邊界 > 固定行數。每函數／struct 一單位，附 `檔：行`。

### S2 INVARIANT-EXTRACT(三遍掃描 ＋ 負向不變量)
四層精準度**從 Tier 0 起，禁跳層**：`ripgrep/find`(T0 找候選) → `grepai_search`(T1 語義) → `grepai_trace_callers/graph`(T1 call-graph；**或條件式 Serena `find_referencing_symbols`＝LSP T1，需 allowlist+activate+LSP+`swift build` 索引——未 build 的 Swift target references 回空、僅剩 document-symbol，見 retarget-map 實測**) → Read body(A 級定案)。
- **Pass 1 Message Contract**：ripgrep 找 `Publish|Subscribe|emit|nats\.|topic` → `grepai_trace_graph` 追 trigger→handler→state→publish → Read publish body 讀 topic／payload(A 級)。
- **Pass 2 State Machine**：ripgrep `state|Status|transition|FSM|session` → 讀 handler chain 找狀態轉移。
- **Pass 3 API Contract ＋ OPBE**：讀 route handler 提 endpoint／params／timeout；**必跑 OPBE**(Optional Param Branch Exhaustion)——枚舉 request body 所有 optional param 及其 if/switch 分支效果(某 optional param 常是 routing key，觸發完全不同路徑／DB lookup)。細節 → `modules/extraction-methodology.md`。
- **Pass 4 Outgoing Call Inventory**：ripgrep 對外呼叫(`http\.|axios|fetch(|DynamoDB|_URL|_HOST|_ENDPOINT`)→ 列 `indexed: false` 的 callee ⇒ 觸發 S2.5。
- **負向不變量**：確認某假設**不存在**(如 `grepai_search "nats.subscribe"` 對某服務空結果)＝ **A 級 absence**，明確記錄(debug 時省一整條錯路)。

### S2.5 IMPLICIT-DEP-INFER(破盒推論)
對每個 `indexed: false` 的 outgoing call 跑五步：① 未索引服務分類(INTERNAL_SERVICE 可再索引／EXTERNAL_INFRA 用協議規格推論) → ② 共享狀態耦合偵測(找 DB **read**，誰寫的？temporal constraint／failure_mode) → ③ 靜默失敗鏈(200 但實際沒成功→哪個 timeout 先觸發、可觀測嗎) → ④ 逾時鏈(timeout 常數由什麼外部 SLA 隱性決定) → ⑤ 循環依賴檢查。每條隱含依賴標 Evidence Level ＋ `source_ref` ＋ `resolution_status`(UNRESOLVED 需索引 callee 才升 CONFIRMED)。框架細節 → `modules/extraction-methodology.md`。

### S3 INDEX(→ antigravity KB，RepoDoc lane)
把 S2/S2.5 產出寫成一份 **source-anchored 不變量頁**(markdown ＋ YAML frontmatter)，落 `<OUT>/invariants/<slug>/<page>.md`：
```
---
repo: <repo>
title: <repo> invariants & contracts
kind: invariants                # ← 與 repo-wiki-converge 的理解 wiki 區隔標記
commit_hash: <sha>
covers: [message-contract, state-machine, api-contract, implicit-deps]
libraries: [...]
---
# <repo> — 不變量與契約(source-anchored)
## Message Contracts
- INV-001 [A] auth respond 後 publish topic=<實值> — src: `natsutil/pubsub.go:NN`
## Negative Invariants
- NEG-001 [A] api-service 不直接 nats.subscribe() — grepai 空結果確認
## Implicit Dependencies (S2.5)
- IMPL-001 [B] gopush reads BundleId from DynamoDB r2PushTokens — silent_failure_chain: ...
```
進 KB：`python3 -m indexing.ingest_repodoc_cli <OUT>/invariants/<slug>/ [--embed]`(RepoDoc 節點 ＋ Library/Concept；`--embed` 才進 `antigravity_repodocs` 向量集)。
> **typed 節點是 lazy-bridge，不現在建**：真出現「要語義查詢不變量節點」的 demand 時，才鏡像 gcr `Conversation`＋`ingest_conversation.py` 加 typed `Invariant` 節點型別(動 `indexing/models.py` SSOT 4 處 ＋ schema-drift test)。在那之前 = RepoDoc prose lane(index≠bridge)。

### S4 AUDIT(SURFACE，非機器閘)
- 每 card 檢查 `evidence_level` 存在(缺 → 補或標)。C／D 級事實**不寫成事實**(標 `unverified`／`inferred`)。
- post-cutoff 外部 claim → `external-verify`。
- 產一行 SURFACE：`a_ratio=<A級/總>`、`unverified_count=<n>` 交人裁。**無 exit-code 閘**(誠實記錄：北極星的 `hallucination_audit.py` 污染矩陣在此無基座)。

### S5 SSOT
per-repo 一張表(行為→源檔→行號→Evidence Level→驗證日) ＋ 跨服務 flow(from→to→transport→topic→Evidence Level)，併入不變量頁。

### S6/S8 FEEDBACK ＋ 漂移偵測
- 收斂判定(SURFACE)：`a_ratio ≥ 0.80` ∧ `unverified` 清零 ∧ 該輪新事實趨零 → GRADUATED(人確認)。
- 漂移：每次 S0 比對 `git rev-parse HEAD` vs 頁面 `commit_hash`；不同 → STALE → 重跑 S1。

### Empty-Output Contract(fail-loud，禁 Half-Bridge)
S2 產 0 不變量 ＋ 0 負向不變量時 **禁**留空頁。**必**在頁面寫 `extraction_failure_reason：<why>`(Pass 1-4 哪環空／源路徑對不對／commit 是否最新／是否需 S2.5)，並在 SURFACE 標 `EMPTY_FAILED`。空殼靜默進 KB ＝ 灌毒(比沒有更糟)。

## Non-Overlap with repo-wiki-converge(硬邊界)
| | repo-wiki-converge | repo-agent-native(本skill) |
|---|---|---|
| 產物 | Opus 級**理解 wiki**(散文，`repo_wiki/<slug>/`) | source-anchored **不變量事實**(`invariants/<slug>/`) |
| 方法 | Gemini 作者 × Opus 判官迴圈 | 確定性 ripgrep／grepai／git 抽取 ＋ Evidence Level |
| 閘 | Opus 判官認證(無機器閘) | Evidence Level SURFACE ＋ git-cite(無機器閘) |
| KB | RepoDoc(prose) via ingest_repodoc_cli | RepoDoc(kind＝invariants) via ingest_repodoc_cli |
| 問的問題 | 「這 repo 是什麼、怎麼運作」 | 「精確契約／隱含依賴／確認的缺席是什麼，各釘哪行」 |
> 兩者都 sink 進 `.cache/kg/graph.json`，靠 **`kind` frontmatter ＋ 內容型別**保持不重疊。SOURCE＝SSOT 漏斗**不可倒置**(源碼為主幹，外部只補缺口——同 repo-wiki-converge 反倒置規則)。

## Handoff on Persistent Black-Box → repo-fullstack-debugger
若 S2.5 破盒推論**無法**以 A 級解析(事實是 runtime-only、不在源碼裡)且反覆燒 token → 交棒 `repo-fullstack-debugger`(消費失敗 trace → L0-L4 診斷 → 畢業 playbook → fold-in)。**靜態源碼可 A 級解析者不升級**(避免過度工程)。此交棒為 LLM 中介散文 pointer(誠實：非 hook)。

## Codebase Design Mastery / Specs-as-Code（規格生成層，入口 `/specs-as-code`）
在不變量抽取之上，本 skill 帶一層「完全掌握」規格配方——對一個**可讀 repo** 產 `.knowledge_base/` 三檔正式規格。4 步：SOURCE=SSOT 漏斗(Tier 0 源碼) → **8 條 implicit-design probe**(seam／determinism／platform／bounded-loop／trust／ergonomics／typed-errors／framework-idiom；把 brief/README 假設當待證命題回源碼證偽) → 多 DR 只補**真外部缺口**(委派 `gemini-conversation-research`) → **evaluator-first** answer-key 計分 ＋ 迭代 ＋ **RIP 封頂**(behavioral claim 完整真跑定案)。
- 方法論全文(funnel-inversion／8 probe／Step 4.5 RIP／與 repo-wiki-converge 邊界) → [`modules/codebase-mastery-methodology.md`](modules/codebase-mastery-methodology.md)
- ready-to-paste 提示詞(v1 ＋ v0→v1 diff) → [`modules/specs-as-code-prompt.md`](modules/specs-as-code-prompt.md)
- 入口 command → `/specs-as-code`（薄 router，委派本 skill ＋ gemini-conversation-research ＋ `indexing/` 合併；能力全在既有層，禁造新引擎）
> **與 repo-wiki-converge 的分工**：那條 ＝ Gemini-author × Opus-judge **理解 wiki**(廣度散文)；這層 ＝ 8-probe ＋ evaluator-first **正式規格**(隱含設計合約，wiki／漏洞清單漏掉的)。是本抽取棧的**掌握＋規格頂點**，非第二個 wiki。

## Boundary Artifacts
- `<OUT>/invariants/<slug>/<page>.md` — source-anchored 不變量頁(進 KB)
- `<OUT>/invariants/<slug>/outgoing-calls.md`、`implicit-deps.md` — S2.5 中間產物(可併頁)
- `<TARGET>/.knowledge_base/{architecture_map,data_flow_and_api,security_and_bottlenecks}.md` — /specs-as-code 完全掌握規格三檔(可經 `ingest_repodoc_cli` 進 KB)
