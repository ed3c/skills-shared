# Module: repo-agent-native — northstar → antigravity retarget 映射 + 誠實拿掉了什麼

> 屬 [`repo-agent-native`](../SKILL.md)。本檔 = port 的**命門與誠實帳本**：哪些機制一對一映到 antigravity、哪些**沒有基座被拿掉、為何拿掉不是簡化**。
> 命門：northstar `repo-agent-native` 的**核心價值一半是抽取紀律(9 階段／破盒推論／Evidence Level／source_ref)、一半是北極星 KG＋審計基座**(rag-local `kg_fast_write`／Serena LSP／`hallucination_audit.py` 污染矩陣／`cross-repo-topology.yaml`／ixsecurity target)。**抽取紀律乾淨映；KG＋審計基座在 antigravity 不存在**——原樣搬 = 引用一堆跑不動的東西 = 死 husk(antigravity `fold-in.md` 反模式明文禁)。

---

## 1. 為何這個 port 必須「換掉整條 KG＋審計基座」，而非簡化

northstar 的 repo-agent-native 是**抽取層 ＋ 北極星專屬 sink/audit 層**的耦合：
- **抽取層**(9 階段／三類不變量／S2.5 破盒推論／OPBE／負向不變量／Evidence Level／source_ref 鐵律)：**與平台無關的推理紀律** → 乾淨映。
- **sink 層**(`mcp__rag-local__index_document`／`kg_fast_write` 雙集合寫入 ＋ YAML KG edges)：antigravity 用**自己的 `indexing/` GraphStore**(Mechanism C：`.cache/kg/graph.json` ＋ ChromaDB，`store.py:4` 明言「completely isolated from northstar's rag-local MCP」)。rag-local 在 antigravity **刻意不存在**。
- **audit 層**(`execution/scripts/hallucination_audit.py` 污染矩陣 ＋ `hallucination-ledger.yaml` ＋ D→any BLOCK 機器閘)：antigravity **無 `execution/`、無此 CLI**。反幻覺改成 Evidence Level SURFACE ＋ `external-verify` ＋ git-cite(人裁，無機器閘)。

保留 sink/audit 層 = 讓 skill 引用不存在的 rag-local MCP、不存在的 `hallucination_audit.py`、不存在的 `cross-repo-topology.yaml`——正是 antigravity `fold-in.md` 反模式禁的「原檔搬進本 repo 引用不存在基座 = 死 husk」，也是 northstar 自己反的 supply-push husk(RIP：不被調用的能力不是能力)。

**KG sink 深度決策(cc-20260703)**：選 **RepoDoc prose lane(現有 `ingest_repodoc_cli`)＋ `kind＝invariants` 標記**，非現在就加 typed `Invariant` 節點。理由 = ① antigravity KG schema(`indexing/models.py:80-96`)無 invariant 節點型別、加型別要動 SSOT 4 處 ＋ schema-drift test；② 無證據有 consumer 會語義查詢不變量節點 → 現在加 = WIRED-never-queried husk(違反 index≠bridge)。typed 節點留作 **lazy-bridge**：真出現查詢 demand 時鏡像 gcr `Conversation`＋`ingest_conversation.py` 先例升級。

---

## 2. 逐機制 retarget 映射表

| northstar 機制 | antigravity 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| Claude 斜線命令 `.claude/commands/repo-agent-native.md`(`$ARGUMENTS`) | 保留為**薄轉發層** `.claude/commands/repo-agent-native.md`(指向 `.agents/skills/` SSOT) ＋ Antigravity 原生 skill `.agents/skills/repo-agent-native/SKILL.md` | 雙平台：Claude Code 走 command 轉發、Google Antigravity 走 activate_skill，同一 SSOT。 |
| 9 階段抽取管線 ＋ 三類不變量 ＋ 負向不變量 | **保留一對一** | 平台無關的抽取紀律，直接映。 |
| S2.5 破盒推論五步 ＋ OPBE ＋ Empty-Output fail-loud contract | **保留一對一** → `modules/extraction-methodology.md` | 核心推理，antigravity 的 repo-fullstack-debugger L2 也重用它。 |
| Evidence Level A/B/C/D 分級 | 保留，抽取工具換：Serena→Read body(A)、GrepAI trace(A-)、gitingest→grepai_search(B+) | 等級語意不變，只換底層工具。 |
| **四層精準度** Glob/Grep(T0)＋Serena LSP(T1a)＋GrepAI(T1b)＋triple_mapping(T1c) | ripgrep/find(T0)＋**grepai_search／trace(T1)** ＋(可選)**Serena LSP(T1，條件式)**＋Read body(A 定案) | **Serena MCP server 連著但未 wire-for-use**(activate 需在 hook allowlist、**LSP references 需 built index**——見下實測)→ 當「未現用基座」不引用(non-husk)。**條件式升級（實測校準）**：需 allowlist+activate+LSP+**built index**，`find_referencing_symbols`／`find_implementations` 才 ＝ T1 **LSP call-graph 工具**（reference 精度 > grepai_search）。⚠ **實測 2026-07-03（repoprompt-ce Swift，未 build）**：activate ✓、swift 偵測 ✓、`get_symbols_overview`（document-symbol，免 build）✓，但 `find_referencing_symbols` **回空 `{}`**（連同檔引用也空）——sourcekit-lsp 的 references 需 `swift build`（index-while-building）才建；Swift build 要 macOS 26+Xcode 26。**故未 build 的 Swift target：Serena 只給 document-symbols（≈ripgrep+Read 已有）、無 call-graph 增量，ripgrep+Read(A) 仍主路。**`triple_mapping`＝rag-local、**拿掉**。grepai 是目前唯一 wired 的 call-graph 工具。 |
| `mcp__rag-local__index_document`／`kg_fast_write`(雙集合 ＋ YAML KG edges) | **拿掉** → 換 `python3 -m indexing.ingest_repodoc_cli`(RepoDoc lane，`kind＝invariants`) | antigravity 用自己的 `indexing/` GraphStore；rag-local 刻意隔離(`store.py:4`)。 |
| `execution/scripts/hallucination_audit.py` 污染矩陣(D→any BLOCK 機器閘) | **拿掉** → Evidence Level SURFACE ＋ `external-verify` ＋ git-cite(人裁) | antigravity 無 `execution/`、無此 CLI；無機器閘(誠實記錄能力差距)。 |
| `data/agent-native/registry.yaml`／`cross-repo-topology.yaml`／`hallucination-ledger.yaml`(local_stack 路徑) | **拿掉** → 中性 `<OUT>/invariants/<slug>/` scratch(對齊 repo-wiki-converge `<OUT>` 慣例) | 這些 SSOT 檔在 antigravity 無路徑基座。 |
| ixsecurity target(`/Users/neon/ixsecurity` auth/auth52/api/gopush) | **拿掉** → 任意可讀 clone repo | ixsecurity 在 antigravity 不存在；本 skill 對任意 target。 |
| S6 TEST-SPEC 兩層 T4(pytest `t4-specs.py` ＋ rag-local runtime) | **拿掉／換** → git commit_hash 漂移偵測 ＋ grep re-verify(S8) | antigravity 無 pytest T4 基座；漂移偵測降級成 commit 比對。 |
| Auto-Patch Pipeline(`/tmp/` staging → `.claude/skills/` 搬入) ＋ Pattern Card #1 materializer | **拿掉** | antigravity 無 P0 auto-approve 保護、無 materializer 慣例；skill 直接 Edit。 |
| S7 minibatch feedback(`skill_optimizer.py` 反思) | **拿掉** | antigravity 無 `skill_optimizer.py`；收斂判定降級成 SURFACE。 |
| Codebase Design Mastery 配方(4 步 ＋ 8 probe ＋ evaluator-first ＋ RIP 封頂) ＋ Specs-as-Code 提示詞 ＋ `/specs-as-code` command | **保留(cc-20260703 fork 過來)** → `modules/codebase-mastery-methodology.md` ＋ `modules/specs-as-code-prompt.md` ＋ 薄 router `.claude/commands/specs-as-code.md` | 配方＋提示詞是平台無關的規格生成紀律；活基座 repo-agent-native(本 skill)＋gemini-conversation-research 都在 antigravity。 |
| Step 3 多 DR 合併 `knowledge-intake-hub` zk-kg-bridge 9-Stage(PG-159/161/212 機器 gate) | **拿掉 9-Stage 引擎＋PG 編號** → 換 antigravity `indexing/`(ingest_repodoc/ingest_conversation) 合併；thesis 覆蓋／mirror／窮盡紀律折成散文(人裁) | antigravity 無 knowledge-intake-hub、無 PG standing gate；合併基座 ＝ 自己的 `indexing/`。 |
| Specs-as-Code worked-example(sandcastle `sandboxes/.../.knowledge_base/` ＋ scorecard) | **拿掉** → 留 lineage 註；首個 antigravity `/specs-as-code` run 產出即本地 worked-example | sandcastle 沙盒 KB 是 northstar 專屬產物，antigravity 無。 |
| global `problem-graph/`(PG-RAN-NNN)＋ADR 編號 | **拿掉編號，保留紀律散文** | antigravity 無 PG/ADR 系統；硬造 = 引入不存在雙圖。 |

---

## 3. 拿掉的東西不是「簡化」，而是「不引入不存在的基座」

northstar repo-agent-native 的 rag-local sink、`hallucination_audit.py` 機器閘、`cross-repo-topology.yaml` SSOT、Serena LSP、pytest T4、materializer、PG/ADR 在 northstar 是**活的**(有對應基座)。在 antigravity 它們**沒有基座**——保留＝讓 skill 引用一堆跑不動的東西＝死 husk。

retarget 的正確姿勢：
- **能一對一映的映**：轉發層、9 階段抽取、S2.5 破盒推論、OPBE、負向不變量、Evidence Level 語意、source_ref 鐵律、8 probe、**Codebase Mastery 配方 ＋ Specs-as-Code 提示詞 ＋ `/specs-as-code` router**(cc-20260703 fork)。
- **活基座換掉**：Serena/triple_mapping → grepai；rag-local index → `indexing/ingest_repodoc_cli`；`hallucination_audit.py` → Evidence Level SURFACE＋external-verify＋git-cite；`knowledge-intake-hub` zk-kg-bridge 9-Stage → antigravity `indexing/` 合併；local_stack 路徑 → 中性 `<OUT>`。
- **沒對應物的誠實拿掉並記錄**(本表)：rag-local 雙集合寫入、機器污染閘、cross-repo-topology SSOT、pytest T4、Auto-Patch、materializer、PG/ADR、ixsecurity target、knowledge-intake-hub 9-Stage 引擎＋PG standing gate、sandcastle worked-example。

---

## 4. 判別「retarget 成立」的鐵錨

本 skill 引用的每個 antigravity 基座都**真存在**：
- `indexing/ingest_repodoc_cli`(`python3 -m indexing.ingest_repodoc_cli <dir>`) ✅ — 真在 `indexing/ingest_repodoc_cli.py`，repo-wiki-converge 同 lane。
- grepai MCP(`grepai_search`／`grepai_trace_callers`／`grepai_trace_graph`／`grepai_index_status`) ✅ — `.grepai/`(index.gob ＋ symbols.gob，trace live)。
- ripgrep／find／git ✅ — Bash 恆在。
- sibling skill 真在 `.agents/skills/`：`external-verify` ✅ `path-b-reduction` ✅ `repo-wiki-converge` ✅ `fold-in` ✅ `repo-fullstack-debugger` ✅。
- KB store：`.cache/kg/graph.json`(RepoDoc 節點) ＋ ChromaDB `.cache/vector_db/`(`antigravity_repodocs` 集，`--embed` 才建) ✅。

**若哪天有人往 SKILL.md／modules 塞回** `mcp__rag-local__index_document`／`kg_fast_write`／`hybrid_retrieve`／`triple_mapping` / `execution/scripts/hallucination_audit.py` / `hallucination-ledger.yaml` / `cross-repo-topology.yaml`(local_stack) / `mcp__serena__*`(**連著但未 wire**——真要用先 allowlist+activate+Swift-LSP，見 §2 條件式升級；別當現用基座硬塞) / `data/agent-native/registry.yaml` / `PG-RAN-NNN` / `/Users/neon/ixsecurity` / Pattern Card materializer / `skill_optimizer.py`，那就是把死 husk 搬回來——**擋下**。

---

## Sources / Lineage
- northstar 源：`/Users/neon/northstar/.claude/skills/repo-agent-native/`(skill.md v1.2.0 ＋ modules ＋ `execution/scripts/hallucination_audit.py` ＋ `data/agent-native/*.yaml`)。
- antigravity 慣例：[`antigravity-skill-authoring`](../../antigravity-skill-authoring/SKILL.md)、[`fold-in`](../../fold-in/SKILL.md)、[`judge-loop-chooser/modules/retarget-map.md`](../../judge-loop-chooser/modules/retarget-map.md)、[`gemini-conversation-research/modules/retarget-map.md`](../../gemini-conversation-research/modules/retarget-map.md)(同型 port 先例)、[`AGENTS.md`](../../../../AGENTS.md)。
- 活基座：`/Users/neon/antigravity/indexing/`(GraphStore Mechanism C ＋ `ingest_repodoc_cli`)、`.grepai/`、`repo-wiki-converge`(非重疊對照)。
- KG schema／ingestion 對賬 provenance：`indexing/models.py:73-96`(node/edge SSOT)、`indexing/repodoc.py`(RepoDoc lane)、`indexing/ingest_conversation.py`(gcr typed-節點 lazy-bridge 先例)。
