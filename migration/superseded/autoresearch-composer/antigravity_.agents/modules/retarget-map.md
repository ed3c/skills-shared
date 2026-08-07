# Module: autoresearch-composer — northstar → antigravity retarget 映射 + 誠實帳本

> 屬 [`autoresearch-composer`](../SKILL.md)。本檔 = port 的命門與誠實帳本：哪些機制一對一映到
> antigravity、哪些沒基座被拿掉/降級、為何不是簡化。
> 命門：northstar 版 = **平台無關的迭代迴圈路由紀律**（§1 Gate + §2 讓位路由表 + §3 Contract block）
> 疊加 **northstar 專屬治理基座引用**（`encd-infrastructure-hub` 路由、liveness/grounding YAML
> 治理欄位、`skill-cycle` Phase 2 銜接、`cycle-dispatch`、`code-refactor-operator-reviewer`/
> `/refactor-loop` 重構特化工具鏈）+ **northstar 專屬「讓位對象」清單**（northstar 自己的
> `superpowers:systematic-debugging`/`superpowers:test-driven-development`/`superpowers:brainstorming`/
> `devops-hub`）。路由紀律骨架乾淨映；治理基座**無/未-wire 已拿掉並記錄**；讓位對象**全部換成
> antigravity 實際存在的 skill**（非直接沿用 northstar 的清單，因為 northstar 的原生 skill 生態本來就
> 跟 antigravity 不同）。

---

## 1. 為什麼要填這個缺口

`sdlc-plan-composer` port 落地時（cc-20260703 起）就誠實記錄了一格缺口：S5「優化迴圈委派
`autoresearch-composer`」在 antigravity **無對應基座**，改成「誠實留白，改 inline 寫 Iteration-Loop
Contract」（見 `sdlc-plan-composer/modules/retarget-map.md` 該行歷史記錄）。2026-07-17 這個缺口被
**填補**：northstar 的 `autoresearch-composer` 本身港進來，`sdlc-plan-composer` S5 該行從「誠實留白」
改為「已落地委派」。

**為什麼現在可以填**：northstar 版的核心依賴（外部 `uditgoenka/autoresearch` v2.1.0，13 個
`/autoresearch:<sub>` slash 命令）是**全局裝**（`~/.claude/commands/`），不是 project-scoped 資源——
確認 `~/.claude/commands/autoresearch/`（12 個 sub 檔）+ `~/.claude/commands/autoresearch.md`（核心）
現場存在（2026-07-17 `ls` 驗證）。這條能力對 antigravity 而言從一開始就是可用的，缺的只是 northstar
自己寫的那層路由/讓位/契約注入邏輯——這正是本次 port 的內容。

---

## 2. 逐機制 retarget 映射表

| northstar 機制 | antigravity 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| §1 Iteration-Loop Gate（5 判據：可量測/有方向/可守護/有界/keep-discard 語義） | **原樣保留** | 平台無關的迭代迴圈判準，不依賴任何 northstar 專屬基座。 |
| §2 讓位路由表的「原生治理 skill」欄 | **全部換成 antigravity 實際存在的 skill**：`superpowers:systematic-debugging`→`diagnose`/`diagnosing-bugs`；`superpowers:test-driven-development`→`tdd`；`superpowers:brainstorming`→`grilling`；`/security-review`+`sast-validator` 兩邊都有故不變 | northstar 讓位表指向的是 northstar 自己裝的 superpowers plugin——2026-07-17 已確認 superpowers 從未在 antigravity 掛號（見 `sdlc-plan-composer`/`unknown-discovery-composer` 同日 retarget 帳本），直接照抄會指向不存在的 skill。改用 antigravity 這幾天剛驗證過的真實對應（`diagnose`/`diagnosing-bugs`/`tdd`/`grilling` 皆為 mattpocock 全局 skill，現場 `ls ~/.agents/skills/` 確認存在）。 |
| `/autoresearch:ship` 讓位 `devops-hub` | **拿掉，誠實留白（無讓位對象）** | antigravity 沒有部署/CI 治理層——本專案是瀏覽器自動化腳本 + skill harness，不是要 ship 的產品化服務；沒有等價物可讓位，硬造一個會是假接線（Slop）。§2 表已明記「誠實留白，需要時直接路由」。 |
| §3 Iteration-Loop Contract block（YAML：goal/scope/metric/direction/verify/guard/iterations/evals/route/executor） | **原樣保留** | 平台無關；`executor` 欄位語意微調（見下一行）。 |
| `executor` 槽的 `cycle-dispatch`（northstar：ENCD gated 路徑，迴圈含並行檔案變更時用） | **拿掉，改指主會話手動用 `Agent`/`Workflow` 工具**（見 `sdlc-plan-composer/modules/multi-model-subagent-dispatch.md`） | antigravity 無 ENCD/`cycle-dispatch` 這類中介 dispatch 層（`sdlc-plan-composer`/`unknown-discovery-composer` 已一致記錄此缺口）。含並行檔案變更的迭代改由主會話直接派工，不假裝有一層自動 dispatch 機制。 |
| §3.5 重構特化（`radon cc/mi`、`code-refactor-operator-reviewer` Phase -1 schema 閘、`/refactor-loop` 命令、CCI 判準） | **整段拿掉** | 這整套是 northstar 專屬的重構工具鏈（`code-refactor-operator-reviewer`、`/refactor-loop` 命令、pydantic/dataclass schema 偵測），antigravity 沒有這些工具、沒有這類多 schema 服務型代碼庫的重構治理需求。假設「Guard=功能測試綠+簽名不變+lint、Metric=可插拔單一數字」這個**概念**本身平台無關，但具體落地工具鏈不存在——不硬留半殘引用，整段拿掉比留一半更誠實。 |
| §3.6 rejection_log / edit_budget 選填槽 | **原樣保留** | 平台無關，無 northstar 專屬依賴。 |
| §4 與 `sdlc-plan-composer` 的組合關係 | **原樣保留，且今日已實際 wiring**（`sdlc-plan-composer` SKILL.md S5 row 已改指本 skill） | antigravity 本來就有本地 fork `sdlc-plan-composer`（northstar 同源 port），Output Contract 目錄結構相同（`docs/plans/<date>-<topic>/`），組合關係零改動即可對齊。 |
| 整合接點：`encd-infrastructure-hub` 路由 + S1 signal table | **拿掉** | antigravity 無 ENCD hub 這類編排層（一致的既有拿掉紀律，見所有其他 port 的 retarget-map）。 |
| 整合接點：`skill-cycle` Phase 2 plan.yaml 消費 | **拿掉** | antigravity 無 skill-cycle；計劃輸出直接交 `implement`/`tdd`，不經中介（同 `sdlc-plan-composer` 既有記錄）。 |
| 整合接點：`mega-flow-harness-hub` post-hoc trace 觀測 | **拿掉** | antigravity 無 mega-flow-harness-hub 這類 cac-trace 自動觀測系統。 |
| YAML frontmatter（`liveness`/`liveness_evidence`/`functional_type`/`hub_modifier`/`deterministic_tests`/`sunset_window_cycles`/`model_assumption`/`inflation_justification`/`core_docs_refs` 等 skill-conformance-hub 治理欄位） | **拿掉**，換 antigravity 慣例 `name` + `description`（`\|` block scalar）極簡 frontmatter | antigravity 無 skill-conformance-hub、無 WIRED/LIVE 追蹤系統（同全部既有 port 的一致做法）。 |
| `evals.json` + `tests/test_routing_contract.py`（northstar：`deterministic_tests: false` 的 stub） | **拿掉** | 佔位 stub，非真實可執行覆蓋；antigravity 其他 port 皆未帶等價 stub 過來，保持一致。 |
| body 內 `docs/adr/0012` glossary/notation-reference 引用 | **拿掉** | antigravity 無這套 SSOT；術語直接展開在 body 內。 |

---

## 3. 拿掉的東西不是「簡化」，而是「不引入不存在的基座」/ 真實能力差距誠實記錄

- **能一對一映的映**：§1 Gate 五判據、§3 Contract block 全部欄位、§3.6 選填特化、§4 與
  `sdlc-plan-composer` 的組合關係、Output Contract 目錄結構。
- **讓位對象換成本地真實存在的**（比照抄 northstar 清單更正確）：§2 讓位路由表七行原生 skill 全部
  retarget 為 antigravity 現場驗證存在的 `diagnose`/`diagnosing-bugs`/`tdd`/`grilling`/
  `improve-codebase-architecture`/`/security-review`+`sast-validator`/`to-prd`。
- **無基座、真實能力差距、誠實拿掉並記錄**（本表核心）：`encd-infrastructure-hub`/`skill-cycle`/
  `mega-flow-harness-hub` 整合接點、§3.5 整段重構特化工具鏈、`cycle-dispatch` executor 選項、
  `devops-hub` 讓位對象（`:ship` 改誠實留白）、skill-conformance-hub 治理 YAML 欄位。

---

## 4. 判別「retarget 成立」的鐵錨

- 外部 autoresearch 引擎：`~/.claude/commands/autoresearch/`（12 個 sub 命令檔）+
  `~/.claude/commands/autoresearch.md`（核心）現場 `ls` 確認存在（2026-07-17，全局裝，非
  project-scoped）。
- antigravity 本地讓位對象：`~/.agents/skills/{diagnose,diagnosing-bugs,tdd,grilling,grill-with-docs,
  grill-me,improve-codebase-architecture,to-prd}/SKILL.md` 現場確認存在；`/security-review` 為本 session
  bundled skill；`sast-validator` 為可用 agent type。
- antigravity 本地委派方：`.agents/skills/sdlc-plan-composer/SKILL.md`（S5 row 已改指本 skill）。

若哪天有人往 SKILL.md 塞回 `encd-infrastructure-hub`/`skill-cycle`/`cycle-dispatch`/
`code-refactor-operator-reviewer`/`/refactor-loop`/`devops-hub`/skill-conformance-hub 的
`liveness`/`grounding` 欄位，那就是把死 husk 搬回來——擋下。

---

## Sources / Lineage

- northstar 源：`/Users/neon/northstar/.claude/skills/autoresearch-composer/skill.md`（v0.3.0）。
- antigravity 慣例／同型 port 先例：
  [`sdlc-plan-composer/modules/retarget-map.md`](../../sdlc-plan-composer/modules/retarget-map.md)、
  [`unknown-discovery-composer/modules/retarget-map.md`](../../unknown-discovery-composer/modules/retarget-map.md)、
  [`AGENTS.md`](../../../../AGENTS.md)。
- 上游 fill-gap 對象：`.agents/skills/sdlc-plan-composer/`（S5「優化迴圈委派」原記「誠實留白」，本 port
  落地後已改指回本 skill）。
- 同日相關 retarget：superpowers 從未在 antigravity 掛號的查證結論（`installed_plugins.json`），已在
  `sdlc-plan-composer`/`unknown-discovery-composer` 的 retarget-map.md 記錄，本檔的讓位表直接沿用該結論。
