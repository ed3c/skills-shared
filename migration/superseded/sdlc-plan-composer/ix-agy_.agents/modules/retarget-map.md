# Module: sdlc-plan-composer — northstar → antigravity retarget 映射 + 誠實帳本

> 屬 [`sdlc-plan-composer`](../SKILL.md)。本檔 = port 的命門與誠實帳本：哪些機制一對一映到
> antigravity、哪些沒基座被拿掉/降級、為何不是簡化。
> 命門：northstar 版 = **平台無關的六階段 SDLC 協議骨架**（S-1 brownfield 前置 + S0-S5 委派表 +
> 稀疏 gate）疊加 **northstar 專屬治理基座引用**（skill-conformance-hub liveness/grounding、
> hallucination_audit.py 機器閘、`provenance.yaml`/`cross-repo-topology.yaml`/`registry.yaml`、
> encd-infrastructure-hub 路由、skill-cycle Phase 2 銜接、`task-graph-decomposer` 模型路由、編號
> ADR、`autoresearch-composer` 優化迴圈委派）。協議骨架本身乾淨映；治理基座**無/未-wire 已拿掉並
> 記錄**。

---

## 1. 為何多數委派目標不用換——它們本來就是全局的

`grill-with-docs` / `to-prd` / `to-issues` / `tdd` / `diagnose` / `design-an-interface` /
`improve-codebase-architecture` / `handoff` 都是 **mattpocock/skills 經 `~/.agents/skills/` 全局目錄**
提供，與 project 無關——northstar 引用得到，antigravity 也引用得到。**這些列不需要 retarget**，本檔
只記真正有落差的幾格。`superpowers:subagent-driven-development` / `superpowers:dispatching-parallel-agents`
是 Claude Code plugin 級 skill，理論上同樣全局可用（未在 antigravity session 現場驗證，SKILL.md 已載
此保留意見）。

---

## 2. 逐機制 retarget 映射表

| northstar 機制 | antigravity 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| S-1 委派 `repo-agent-native`（northstar：跨 repo 引用自己的 skill，產 3 個 boundary artifact：`invariants.yaml`/`cross-repo-topology.yaml`/`hallucination-ledger.yaml`，由 `registry.yaml` 追蹤 commit_hash） | **retarget 為 antigravity 本地 fork**（cc-20260703 已 port），消費**單一**不變量頁（frontmatter `commit_hash`，內嵌 `INV-*`/`NEG-*`/`IMPL-*` 三類條目） | 本地 fork 更乾淨（非跨 repo），但 schema 不同：三個分散 YAML → 一頁三類條目；STALE 判定從讀 `registry.yaml` 改成讀頁面自己的 `commit_hash` frontmatter。 |
| S-1(f) Provenance Binding：`provenance.yaml`（Schema-A cards, `card_id`/`evidence_level`/`links`）+ `hallucination_audit.py` 道1 污染矩陣 + 道2 D-stage 互斥 lint，兩道皆 exit-code 機器 BLOCK | **拿掉**，換成 repo-agent-native 自己的 **S4 AUDIT SURFACE**（`a_ratio`/`unverified_count` 一行，人裁，無 exit-code 閘） | antigravity 無 `hallucination_audit.py` 這類確定性污染矩陣 CLI。repo-agent-native 的 antigravity 版本身就是 SURFACE-only（其 SKILL.md 已明言「無機器閘」），本 skill 順著消費，不另造一層機器閘（那會引用不存在的 `execution/scripts/hallucination_audit.py`）。 |
| S-1 GATE 表 `G-S2` 消費 `cross-repo-topology.yaml` 的 `shared_state_couplings`（`SSC-*` ID） | **拿掉 `SSC-*`**，G-S2 改消費不變量頁內嵌的 `IMPL-*` 條目 | antigravity repo-agent-native 無獨立 typed `cross-repo-topology.yaml`；共享狀態耦合是 S2.5 `IMPL-*` 條目裡的散文欄位（`silent_failure_chain` 等），非另一份機器可讀 YAML。 |
| S-1 引用慣例 `skill-name:ID`（northstar 含 `HL-*` hallucination-ledger、`SSC-*`、`IMPL-DB-*`） | **保留格式，砍掉 `HL-*`/`SSC-*` 兩類**（antigravity 無對應 artifact），只留 `INV-*`/`NEG-*`/`IMPL-*` | 跟著 artifact schema 走：northstar 三檔案三前綴，antigravity 一頁三類條目。 |
| S0「查 `docs/adr/` 是否有已否決的同類設計」 | **retarget 為「查既有決策記錄」**（`docs/decisions/` 或計劃目錄內散文記錄，非編號 ADR 系統） | antigravity 無編號 ADR/DDR 系統（同 `repo-agent-native`/`unknown-discovery-composer` retarget-map 已定調：「拿掉編號，保留紀律散文」）。 |
| S0「搜既有 modules + `skill_match` 找是否已有零件」（northstar：rag-local MCP 語義搜索） | **retarget 為「掃 `~/.agents/skills/` + 本 repo `.agents/skills/`」**（人工 disk 掃描，非語義搜索） | antigravity 無 `mcp__rag-local__skill_match`（northstar 專屬 rag-local infra）。同 `unknown-discovery-composer` retarget-map §4 已定調的「路由前先確認目標真在 disk」鐵錨，本 skill 沿用同一手法做 S0 查重。 |
| S3「決策記錄稀疏三條件 → 寫 `docs/adr/00NN-<slug>.md`」（northstar：編號 ADR，落全域 registry） | **retarget 為 `docs/decisions/<slug>.md`**（散文決策記錄，無編號、無 registry） | 同上，拿掉編號系統；三條件判準本身（難逆轉/缺脈絡顯突兀/真實權衡）平台無關，原樣保留。 |
| S5「執行契約」委派 `fidelity-handoff`（northstar：形態決策 fork/handoff/cold-start + `fidelity-handoff-lint` 覆蓋閘，防裸交接漏 load-bearing negative） | **拿掉，退化到裸 `handoff`/`claude-handoff`** | antigravity 無 fidelity-handoff fork、無覆蓋閘腳本（同 `unknown-discovery-composer` retarget-map 已記錄的同一格落差）。裸 handoff 無覆蓋閘防漏——真實能力差距，非簡化；交接前建議人工複查有無漏 negative。 |
| S5 Judge/evals：`execution/lib/judge_chooser.py` `route(target_type)` → macro/micro design-judge 沙盒 + `tier_for(scope)` 模型路由（`task-graph-decomposer` 傳遞） | **retarget 為 antigravity 本地 fork** `judge-loop-chooser`（DR/absorption・COMPLETENESS 覆蓋矩陣・Path B 精煉・技術選型 fit-to-plan 四分支）+ **四層獨立性階梯**（T0-T3）取代 macro/micro 模型路由 | 本地已 port。northstar 的 code/sandbox 判決表、macro→Opus/micro→Sonnet 模型路由、`task-graph-decomposer` 在 antigravity **無基座**（judge-loop-chooser 自己的 retarget-map 已載明拿掉 Branch B + `tier_for`）；本 skill 順著消費新分支表，**新增**「代碼產物 → 直接 `code-review`」這條分流（同 `unknown-discovery-composer` U3 表已有的先例）。 |
| S5「S5 優化迴圈委派 `autoresearch-composer`」 | **拿掉，誠實留白**（無替代 composer，改 inline 寫 Iteration-Loop Contract） | antigravity 無 `autoresearch-composer` 或對應 `/autoresearch:*` 命令基座。搜過 antigravity 現有 `.agents/skills/`（含 `ds-workflow-loop` — 該 skill 是資料科學管線的地圖/方法論，非通用優化迴圈委派層，語義不符，不可誤用頂替）。誠實記為缺口，不現造替代 skill。 |
| 「被 `encd-infrastructure-hub` 路由（已接）」+「接 `skill-cycle` Phase 2 前置（已接）」整合接點段 | **整段拿掉** | antigravity 無 ENCD/skill-cycle 這類中介 dispatch 層（同 `unknown-discovery-composer` Not For 已載明：「antigravity 無 skill-cycle 這類編排層」）。計劃輸出直接交 `implement`/`tdd`，不經任何中介。 |
| YAML frontmatter（northstar：`liveness`/`liveness_evidence`/`functional_type`/`hub_modifier`/`deterministic_tests`/`core_docs_refs`/`sunset_window_cycles`/`model_assumption` 等 skill-conformance-hub 治理欄位） | **拿掉**，換 antigravity 慣例 `name` + `description`（`|` block scalar）極簡 frontmatter | antigravity 無 skill-conformance-hub、無 WIRED/LIVE 追蹤系統、無 grounding.yaml 申報機制；硬填這些欄位 = 引用不存在的治理基座（同全部既有 port 的一致做法）。 |
| `docs/adr/0012` glossary/notation-reference 引用（northstar `architecture/glossary.md` + `notation-reference.md`） | **拿掉** | antigravity 無這套 SSOT；術語直接展開在 body 內，不外指不存在的解析檔。 |
| `evals.json` + `tests/test_stub.py`（northstar：`deterministic_tests: false` 的 stub，本來就非真測試） | **拿掉** | 佔位 stub，非真實可執行覆蓋；antigravity 其他 port（`repo-agent-native`/`judge-loop-chooser`/`unknown-discovery-composer`）皆未帶等價 stub 過來，保持一致。 |
| footnote 記憶連結（northstar `[[feedback-step-0-audit-before-design]]` 等，northstar 內部 Claude 記憶系統） | **拿掉** | antigravity 無此記憶系統，連結對象在本 repo 語境下無意義。紀律本身（S0 先審既有再設計）已折進本文散文，不靠外部連結。 |

---

## 3. 拿掉的東西不是「簡化」，而是「不引入不存在的基座」/ 真實能力差距誠實記錄

- **能一對一映的映**：S-1..S5 六階段骨架、S0 Premise Disproof Challenge 四步驟、S3 決策記錄稀疏三條件、
  S4 BS #420 三角互斥、Output Contract 目錄結構、所有全局 mattpocock skill 引用（見 §1）。
- **有本地基座可換的換**（比 northstar 原版更乾淨）：`repo-agent-native`（S-1）、`judge-loop-chooser`
  （S5），從「跨 repo 引用 northstar」換成「引用 antigravity 本地 fork」；連帶 artifact schema 從
  northstar 的多檔案 YAML 改成 antigravity 的單頁多條目。
- **無基座、真實能力差距、誠實拿掉並記錄**（本表核心）：`hallucination_audit.py` 機器閘（降 SURFACE）、
  `cross-repo-topology.yaml`/`registry.yaml`（併入單頁）、`fidelity-handoff`（退化裸 handoff）、
  `autoresearch-composer`（無替代）、encd-infrastructure-hub/skill-cycle 整合接點（無此編排層）、
  `task-graph-decomposer` 模型路由（改獨立性 tier）、編號 ADR 系統（改散文決策記錄）、
  skill-conformance-hub 治理欄位、glossary/notation-reference SSOT。

---

## 4. 判別「retarget 成立」的鐵錨

本 skill 引用的每個委派目標都真存在：
- mattpocock 全局 skill：`/Users/neon/.agents/skills/{grill-with-docs,grill-me,to-prd,to-issues,tdd,
  diagnose,design-an-interface,improve-codebase-architecture,handoff}` 均存在於 disk（本次 port 時
  `ls` 驗證）。
- antigravity 本地 fork：`.agents/skills/{repo-agent-native,judge-loop-chooser}/SKILL.md` 存在。
- `superpowers:subagent-driven-development` / `superpowers:dispatching-parallel-agents` /
  `superpowers:writing-plans` / `superpowers:brainstorming`：Claude Code plugin 級 skill（
  `~/.claude/plugins/marketplaces/superpowers-marketplace` 確認已裝），**未在 antigravity session
  現場驗證**——若失效見 SKILL.md 內的降級說明。

若哪天有人往 SKILL.md 塞回 `execution/lib/judge_chooser.py` / `hallucination_audit.py` /
`provenance.yaml` / `cross-repo-topology.yaml` / 編號 ADR / skill-conformance-hub 的
`liveness`/`grounding` 欄位 / `encd-infrastructure-hub` / `skill-cycle` / `task-graph-decomposer`，
那就是把死 husk 搬回來——擋下。

---

## Sources / Lineage

- northstar 源：`/Users/neon/northstar/.claude/skills/sdlc-plan-composer/skill.md`（v0.1.0）。
- antigravity 慣例／同型 port 先例：
  [`repo-agent-native/modules/retarget-map.md`](../../repo-agent-native/modules/retarget-map.md)、
  [`judge-loop-chooser/modules/retarget-map.md`](../../judge-loop-chooser/modules/retarget-map.md)、
  [`unknown-discovery-composer/modules/retarget-map.md`](../../unknown-discovery-composer/modules/retarget-map.md)、
  [`AGENTS.md`](../../../../AGENTS.md)。
- 下游本地 fork：`.agents/skills/repo-agent-native/`、`.agents/skills/judge-loop-chooser/`。
- 上游 fill-gap 對象：`.agents/skills/unknown-discovery-composer/`（U1 出口原退化到 `writing-plans`，
  本 port 落地後已改指回本 skill）。
