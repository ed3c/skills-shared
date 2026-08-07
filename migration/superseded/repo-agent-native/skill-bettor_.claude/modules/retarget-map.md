# Module: repo-agent-native — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`repo-agent-native`](../SKILL.md)。本檔＝移植的命門與誠實帳本：哪些機制一對一映到 skill-bettor、
> 哪些因為架構前提不同被拿掉/降級、為何拿掉不是簡化。**這是 northstar→antigravity→skill-bettor 鏈的
> 第三環**——antigravity 版本身已對 northstar 版做過一次 retarget(見 antigravity 版自己的
> `modules/retarget-map.md`，記錄 northstar→antigravity 那一環，本檔不重抄，只承接 antigravity→
> skill-bettor 這一段)。

---

## 0. 本次 port 的起點事實(誠實記錄，非事後包裝)

寫本檔前，`ls /Users/neon/skill-bettor/.claude/skills/repo-agent-native/` 已存在但**空目錄**(只有一個
`modules/` 空資料夾)——本次 port 是首次填入內容，非覆蓋既有版本。同時，`sdlc-plan-composer` 的 S-1 章節
與其 `modules/retarget-map.md` 已經**明確記錄** skill-bettor「沒有 `repo-agent-native` 這類自動不變量
抽取工具，是真實能力差距」，並把 S-1 降為手動盤點程序當暫代——本次 port 的目的正是把那個暫代升級為
真委派對象。這代表本檔完成後，`sdlc-plan-composer` 與另外三個已落地 skill
(`unknown-discovery-composer`／`harness-wiki`／`path-b-reduction`)裡「repo-agent-native 在 skill-bettor
無本地基座」的敘述**會變成過期陳述**。這段只保留首次 port 的時間性 receipt；現行能力以 §5 為準，
不得拿本段歷史快照覆蓋今天的 live checks。

## 1. 為何多數推理內容能逐字映(而非像 loop-harness-standard 那樣大改)

antigravity 版 `repo-agent-native` 本身已經是 northstar 版的一次 retarget，**核心推理紀律(9 階段／
三類不變量／破盒推論五步／OPBE／Evidence Level／source_ref 鐵律／8 條 implicit-design probe／
evaluator-first／RIP 封頂)在那一環就已經被驗證為「與平台無關」**，antigravity 版把它們原樣映過去了。
這次 skill-bettor port 面對的情況相同：這些是純推理框架，不依賴任何特定 KG／索引平台／host 矩陣，
`modules/extraction-methodology.md` 與 `modules/codebase-mastery-methodology.md` 因此**近乎逐字映**，
現況相較首次 port 已再演進：本地 `indexing.ingest_repodoc_cli`、`repo-wiki-converge`、
`gemini-conversation-research`、grepai index 與 Serena project 都已存在。`repo-fullstack-debugger` 仍無本地
port，runtime-only 問題路由通用 `diagnose`／`diagnosing-bugs`。因此本檔記錄的是「恢復本地完整 L1→L2/L3
→KG 能力、MCP 僅作可選導航」的新基線，不再沿用首次 port 的缺口快照。

---

## 2. 逐機制 retarget 映射表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣映／拿掉了什麼 |
|---|---|---|
| S3 INDEX：RepoDoc lane，`kind: invariants`，可選 `--embed` | **恢復本地完整能力**：S3 寫 `<out>/invariants/<slug>/`，S4＋人裁後由 S5 dry-run／live ingest | 本地 `indexing.ingest_repodoc_cli` 已真存在；2026-07-29 補 kind-aware RepoDoc ID，L1/L2/L3 同名頁不再互覆。基本 graph ingest 不需 MCP／chromadb，只有 `--embed` 需要 chromadb/Ollama。 |
| `<OUT>`＝durable artifact root | 外部 repo 用 `repo/<repo_name>/`；本 repo 計畫用 `docs/plans/<date>-<topic>/` | 兩者都保留 `<out>/invariants/<slug>/` 契約並可 ingest；不再把所有產物硬綁 plan-scoped。 |
| Codebase Mastery 三檔輸出 `<TARGET>/.knowledge_base/{architecture_map,data_flow_and_api,security_and_bottlenecks}.md`(寫進 target repo 自己) | **依 target 類型二選一**：target 是 skill-bettor 家族 → `families/<family>/specs/{同三檔}.md`(family-local 常駐資產)；target 不是家族 → `<out>/invariants/<slug>/specs/{同三檔}.md`(out-scoped) | antigravity 原版把 mastery 規格寫進 target 自己，因為那是 target 的常駐資產。skill-bettor 沒有「target 自己的 repo」這個概念可寫(target 常常就是 skill-bettor 自己的一部分)，`families/<family>/` 是最貼近的等價物(家族架構規格是會被反覆諮詢的資產，理應跟著家族走)；非家族 target 跟 L2 共用呼叫者提供的 durable `<out>`。目錄名從 `.knowledge_base/`(dot-prefixed)改成 `specs/`(plain)，對齊 skill-bettor 沒有 dot-prefixed 內容目錄的既有習慣。 |
| `repo-wiki-converge`(S0 wiki seed) | 本地 `.claude/skills/repo-wiki-converge/`＋`kb-ingest/agy-pass.sh`＋RepoDoc ingest | L1 能完整收斂並進 KG；仍只作 L2 scope seed，load-bearing facts 回 source。 |
| `repo-fullstack-debugger`(Handoff on Persistent Black-Box) | **拿掉，改為指向內建 `diagnose`／`diagnosing-bugs`**，並明確標註「交棒後紀律會變」(通用重度除錯迴圈 vs 本 skill 的源碼級隱含依賴推導框架，兩者不是同一件事的改名) | skill-bettor **無此 skill**(`test -e` 確認不存在，見 §5)。全局可用的 `diagnose`／`diagnosing-bugs` 是最近替代，但誠實記錄：那是「heisenbug/性能回歸/反覆失敗」的重度診斷迴圈，不是「用已知事實破盒推論隱含依賴」的框架——交棒不是無縫升級，是換了一套完全不同的方法論。 |
| Specs-as-Code Step 3 外部缺口 | demand-pull 路由 `external-verify`／`research`／條件式 `gemini-conversation-research` | GCR 本地 port 已存在；若 receipt 是 `external_engine_required`，只可記外部執行需求，不能宣稱 browser／DR engine 本地 runnable。 |
| S2/S2.5：grepai／Serena | **可選導航加速**；完整能力主路仍是 `rg`／git／Read | 2026-07-29 真跑：grepai canary 命中本 repo，Serena 啟用 `skill-bettor` 並回 Python symbols；grepai trace 也出現同名符號誤連，故 MCP 命中最高 B+，必回 source。 |
| Evidence Level A/B/C/D 分級語意 | **原樣映**(語意與底層工具無關) | 抽取工具換了(northstar→antigravity 那環已換過一次)，等級語意本身通用，不需要再改。 |
| S2.5 破盒推論五步／OPBE 三步／8 條 implicit-design probe | **原樣映**(純推理框架) | 平台無關，見 §1。範例從 ixsecurity/nats/gopush 換成 skill-bettor 本地可指的對象(`runner.py`／`engine.sh`／`agy` quota)，方法論字句不變。 |
| Empty-Output fail-loud contract(`extraction_failure_reason`＋SURFACE 標 `EMPTY_FAILED`) | **原樣映** | 純紀律，與 KG／host 矩陣無關。 |
| S4 AUDIT SURFACE(`a_ratio`／`unverified_count`，無機器閘) | **原樣映** | skill-bettor 同 antigravity 皆無 `hallucination_audit.py` 這類機器污染矩陣，人裁一致。 |
| S6/S8 漂移偵測(`git rev-parse HEAD` vs 頁面 `commit`) | **原樣映** | 純 git 機制，不需要 KG 才能做。 |
| 雙平台(`.agents/skills/`＋`.claude/commands/` 薄轉發層)、`/specs-as-code` 薄 router command | **拿掉，單一 `.claude/skills/repo-agent-native/`**，Codebase Mastery 層直接是本 skill 的一部分，不另立第二入口 | skill-bettor 是 Claude-Code-only 單 host(CLAUDE.md 明文)，無 Antigravity CLI/Gemini host 需要雙平台轉發——與 `loop-harness-standard`／`judge-loop-chooser` 已定案的單 host 事實一致，不是本 skill 新拿掉的維度。 |
| antigravity 慣例引用「antigravity-skill-authoring」(見 antigravity 版 retarget-map 的 Sources/Lineage) | **改指向 Claude Code 內建 `write-a-skill`** | 同批次其他 port 的一致做法(sdlc-plan-composer/loop-harness-standard 等皆已改用內建 `write-a-skill`)；skill-bettor 是 Claude Code 平台自己的 skill 格式規範，非 Antigravity CLI 的 `.agents/skills/` 規範，兩者 frontmatter/封裝不同不可混用。 |
| `external-verify`／`path-b-reduction` cross-reference | **保留，指向本地 sibling** `.claude/skills/external-verify/`／`.claude/skills/path-b-reduction/` | 兩者本批次均已落地(`test -e` 確認，見 §5)，路由不需要改，只是指標從 antigravity 路徑換成本地路徑。 |
| `sdlc-plan-composer` brownfield delegate | 已接 G-1：優先委派本 skill，失敗才走 source-linked fallback | 本 skill 契約提供 `target`／`out`／`slug`、typed IDs、SURFACE 與 ingest receipt。 |

---

## 3. 現行能力邊界

- **不引入不存在的架構前提(雙平台矩陣、`/specs-as-code` 獨立入口)**：skill-bettor 單 host 事實，
  loop-harness-standard/judge-loop-chooser 已立先例，不重新論證。
- **仍缺**：`repo-fullstack-debugger` 本地 port；runtime-only 問題換軌到通用 diagnosis skill，非等價改名。
- **已恢復**：L1 wiki、L2/L3 RepoDoc ingest、本地 KG、GCR port、grepai、Serena、sdlc G-1 接線。
- **MCP 邊界**：grepai／Serena 只加速導航；rag-local 不參與本 repo L2/L3 sink。沒有 MCP 不得縮減流程。
- **外部引擎邊界**：GCR skill 存在，但 `external_engine_required` receipt 仍是硬邊界。

---

## 4. 為何 Codebase Mastery / Specs-as-Code 層決定保留(非默認省略)

任務要求對這層做出取捨判斷，理由記錄如下(供未來覆核)：
1. **方法論本身與 KG/host 平台無關**——4 步配方(SOURCE=SSOT 漏斗→8 probe→外部缺口處理→evaluator-first
   ＋RIP 封頂)全部是推理紀律；Step 3 現已路由本地外部查證／研究能力，但仍守 external-engine receipt。
2. **skill-bettor 的 `repo-wiki-converge` 只補 L1 openwiki，不替代 L2 source-grounded extraction**：
   antigravity 語境下這層明言「不跟 repo-wiki-converge 競爭第二個 wiki」；skill-bettor 現在也維持
   這條邊界。wiki 是範圍/敘事種子，不是源碼事實裁決者。
3. **L2/L3 sink 已恢復**：legacy L1 base ID 與 kind-aware invariants／specs namespace 可安全共用 KG；
   `--embed` 仍是選配，不把向量庫誤當基本 graph ingest 前提。
4. **不保留的代價 > 保留的維護成本**：這層唯一的活躍消費場景是「高風險 family-wide 整改前的深度審計」
   ——`ARCHITECTURE.md` §10 D2 就規劃了第一條真實演化 op(`refine repaint-detection`)，這類操作前跑一輪
   本層檢查（尤其 P2 determinism/P4 bounded-loop probe 直接對應 `judge.py`/`engine.sh` 的核心合約）
   是任務背景第 3 點要求的具體使用情境，不是空想的假設用途。

**優先序判斷**：核心 9 階段不變量抽取(SKILL.md 主體)是 S-1 的**主要**委派對象，日常 brownfield 判定
只需要它；Codebase Mastery 層是**選配深化**，只在高風險整改前才值得完整跑一輪——這個優先序已寫進
`../SKILL.md` 對應段落，避免被誤讀成「每次 S-1 都要跑三檔規格」。

---

## 5. 2026-07-29 現行鐵錨

- `.grepai/{config.yaml,index.gob,symbols.gob}` 存在；2026-07-29 啟動 watcher 並完成 initial scan 後，
  status＝1468 files／7501 chunks、`last_updated=2026-07-29 15:35:54`。canary 命中現行
  `mastery-ladder.md` 的 L1 legacy ID＋L2/L3 kind namespace 內容；aggregate status 仍不能取代 target canary。
  同權限層確認 watcher running；sandbox 內 `watch --status` 曾誤報 not running，故它不是 freshness SSOT。
- Serena 已註冊並真啟用 `skill-bettor`；`get_symbols_overview(indexing/repodoc.py)` 回傳正確 Python symbols。
- grepai `trace_callers(ingest_repo_wiki)` 同時出現正確 caller 與同名誤連，證明 MCP trace 只能是 B+ candidate。
- `.claude/skills/{repo-wiki-converge,gemini-conversation-research}/`、`kb-ingest/`、`indexing/`、`docs/` 均存在。
- `sdlc-plan-composer` G-1 已寫「Prefer delegating repo-agent-native」。
- RepoDoc kind isolation 由 `indexing/tests/test_repodoc_ingest.py::test_kind_namespaces_same_path_across_mastery_layers`
  保護；舊無-kind wiki ID 保持向後相容。
- `rag-local` 指向別的本地 stack；本 skill 不以它讀寫 skill-bettor KG。

## 6. 剩餘開放問題

1. Codebase Mastery 仍缺一個 skill-bettor 本地三檔 worked instance；首次高風險 family-wide 改造應產 answer-key。
2. `repo-fullstack-debugger` 仍無本地 port；通用 diagnosis route 可用，但方法論不等價。

---

## Sources / Lineage
- antigravity 源：`/Users/neon/antigravity/.agents/skills/repo-agent-native/`(SKILL.md +
  `modules/{extraction-methodology,codebase-mastery-methodology,specs-as-code-prompt,retarget-map}.md`
  ，其中 `modules/retarget-map.md` 記錄的是 northstar→antigravity 那一環，本檔不重抄，只在 §1/§0 摘要
  引用其結論)。
- skill-bettor 既有同構：`ARCHITECTURE.md`(家族/loop_wiki 目錄契約)、`CLAUDE.md`(root 被動上下文)、
  `families/pinescript-audit/`(本地 worked family 與 Evidence Level 素材)、`loop_wiki/engine.sh`
  (RIP 載具與 P2/P4 probe 範例)、`indexing/`(本地 RepoDoc/KG sink)。
- 同批移植先例(同一 rigor 要求，判斷邏輯沿用)：
  [`loop-harness-standard/modules/retarget-map.md`](../../loop-harness-standard/modules/retarget-map.md)、
  [`judge-loop-chooser/modules/retarget-map.md`](../../judge-loop-chooser/modules/retarget-map.md)、
  [`sdlc-plan-composer/modules/retarget-map.md`](../../sdlc-plan-composer/modules/retarget-map.md)
  (本檔要接線的下游消費者，§6 開放問題 1 的完整背景)、
  [`unknown-discovery-composer/modules/retarget-map.md`](../../unknown-discovery-composer/modules/retarget-map.md)
  (外部缺口路由的相鄰先例)。
