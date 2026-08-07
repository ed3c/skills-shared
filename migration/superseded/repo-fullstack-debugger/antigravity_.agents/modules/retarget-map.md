# Module: repo-fullstack-debugger — northstar → antigravity retarget 映射 + 誠實拿掉了什麼

> 屬 [`repo-fullstack-debugger`](../SKILL.md)。本檔 = port 的**命門與誠實帳本**：哪些機制一對一映到 antigravity、哪些**沒有基座被拿掉、為何拿掉不是簡化**。
> 命門：northstar `repo-fullstack-debugger` 的**核心是 L0-L4 trace-driven 診斷紀律 ＋ 一整套 L1 Self-Mutation Mode(M0-M5，北極星 skill 自優化引擎)**。**L0-L4 診斷紀律乾淨映(且回到它源自的瀏覽器代理 domain)；L1 Self-Mutation Mode 全套在 antigravity 無基座**——原樣搬 = 引用一堆跑不動的 `execution/scripts/*.py`＋telemetry＋PG/ADR = 死 husk。

---

## 1. 為何這個 port 必須「整條 L1 Self-Mutation Mode 拿掉」

northstar 的 repo-fullstack-debugger 是**雙層**：
- **外層 L0-L4 診斷閉環**(反過度設計閘／trace 觀測／四象限診斷／strategy 棘輪／畢業 playbook)：**與平台無關的診斷紀律，且本就源自 Autobrowse／site-debugger 瀏覽器代理研究** → 乾淨映，而且**回到原生 domain**(antigravity 的 automate.js 正是這類瀏覽器黑盒的溫床)。
- **內層 L1 Self-Mutation Mode**(M0-M5：讀自己 evals → GraphRAG DR-seed → subagent 生成 skill.md diff → `skill_optimizer.py` 確定性選擇 → writeback／reject → 收斂)：**一整套北極星 skill 自優化引擎**，依賴 `execution/scripts/skill_optimizer.py`／`demand_gate.py`／`cold_start_floor.py`／`placebo_guard`／`evals.json` 機制／`data/production/telemetry/*.jsonl`／Pattern Card #1 materializer／PG-158／ADR-0005。**antigravity 全無這些基座。**

保留 L1 Self-Mutation Mode = 讓 skill 引用一堆不存在的 `.py`／ledger／PG 編號 = 死 husk。而且它的**目的**(meta-優化 skill 自己的 eval pass_rate)在 antigravity 不是本 skill 該管的事——antigravity 的 skill 優化沒有這套機制。**整條拿掉。**

---

## 2. 逐機制 retarget 映射表

| northstar 機制 | antigravity 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| Claude 斜線命令 `.claude/commands/repo-fullstack-debugger.md`(`$ARGUMENTS`) | 保留為**薄轉發層** ＋ Antigravity 原生 skill `.agents/skills/repo-fullstack-debugger/SKILL.md` | 雙平台，同一 SSOT。 |
| L0 反過度設計閘 ＋ STOP 鐵則(≤3-5 輪／plateau abort) | **保留一對一** | 平台無關的反過度設計紀律；瀏覽器 domain 尤其需要(避免對一次 DOM 抓取就能解的事開 5 輪迴圈)。 |
| L1 Trace Observability(消費失敗 trace) | 保留，trace 源換：ixsecurity-e2e MCP trace → **stealth-browser console／截圖 ＋ automate.js 失敗簽名**；repo → build/test/run 輸出 ＋ grepai | trace 觀測紀律不變，只換來源。 |
| L2 診斷(S2.5 破盒推論四象限) | 保留，**擴成雙象限**：新增瀏覽器 Bot/Timing/Selector/Auth(site-debugger 原生) ＋ 保留 repo 執行 S2.5 四象限 | 北極星 debugger 也提過瀏覽器版 L2(在 gcr modules)；antigravity 讓它成主象限之一。→ `modules/l2-quadrants.md`。 |
| L3 Strategy Scratchpad ＋ 記憶棘輪(退步→revert) | **保留一對一** | 平台無關的跨 session 棘輪。 |
| L4 Graduation(畢業 tested playbook) | 保留，**交棒改成 `fold-in`**(北極星是散文 pointer 回協作者) | antigravity 有 `fold-in` skill 作為 durable 沉澱 actuator；畢業 playbook 正是它要的「已完成經驗」輸入。 |
| **L1 Self-Mutation Mode 全套(M0-M5)** | **整條拿掉** | `skill_optimizer.py`／`demand_gate.py`／`cold_start_floor.py`／`placebo_guard`／`evals.json`機制／telemetry ledger／materializer 在 antigravity 全無基座。 |
| `mutation_admission` demand-gate ＋ PG-RFD-005 route hook(`execution/hooks/*.sh`) | **拿掉** | antigravity 無 hook 系統、無 `execution/`。 |
| `execution/scripts/hallucination_audit.py`(L4 畢業前污染矩陣) | **拿掉** → Evidence Level SURFACE(C/D 不寫進 playbook) ＋ git-cite ＋ fold-in discrimination gate | antigravity 無此 CLI；反幻覺改人裁 ＋ fold-in 擋純散文。 |
| 上游協作者 `subproject-ixsecurity-e2e`(takeover-on-failure) | **拿掉** → 換 antigravity 協作者：`automate.js`／`gemini-conversation-research`／`dr-research-loop`(瀏覽器) ＋ `repo-agent-native`(repo 執行) | ixsecurity-e2e 在 antigravity 不存在；真實反覆失敗源是瀏覽器自動化。 |
| 上游協作者 `repo-agent-native`(northstar 版) | 換成 antigravity retarget 的 `repo-agent-native`(sibling skill) | 同 repo 內的 retarget 版。 |
| `data/production/repo-fullstack-debugger/<target>/` 輸出根 | 中性 `<OUT>/debug/<target>/`(對齊 repo-wiki-converge `<OUT>` 慣例) | antigravity 無 `data/production/` 基座。 |
| `deterministic_tests`(`run_l1_mutation_once.py` 42 tests)／`pg/PG-RFD-001..005`／ADR-0004/0005 | **拿掉編號與測試** → `node --check`(N/A，純 md)／人審 | antigravity 無 pytest runner／無 PG/ADR 系統。 |
| Pattern Card #1 materializer(P0 檔禁直接 Edit) | **拿掉** → SKILL.md 直接 Edit | antigravity 無 auto-approve P0 保護。 |
| frontmatter `version`／`triggers`／`capabilities`／`liveness`／`functional_type`／`core_docs_refs` 等 | **拿掉** → 只留 `name`／`description` | antigravity-skill-authoring：官方 canonical 只 `name`／`description`，其餘 FRONTIER-CONTESTED 禁用。 |

---

## 3. 拿掉的東西不是「簡化」，而是「不引入不存在的基座」

northstar 的 L1 Self-Mutation Mode、`skill_optimizer.py` 選擇引擎、demand-gate hook、`hallucination_audit.py` 機器閘、pytest 42-test gate、PG-RFD/ADR、materializer 在 northstar 是**活的**。在 antigravity 它們**沒有基座**——保留＝引用一堆跑不動的東西＝死 husk。

retarget 的正確姿勢：
- **能一對一映的映**：轉發層、L0 反過度設計閘、STOP 鐵則、L1 trace 觀測紀律、L2 四象限、L3 棘輪、L4 畢業。
- **活基座換掉**：trace 源 → stealth-browser／automate.js 簽名；協作者 → automate.js/gcr/dr-research-loop/repo-agent-native；L4 交棒 → fold-in；輸出根 → 中性 `<OUT>`。
- **沒對應物的誠實拿掉並記錄**(本表)：L1 Self-Mutation Mode 全套、demand-gate hook、機器污染閘、pytest gate、PG-RFD/ADR、materializer、ixsecurity-e2e 協作者。

---

## 4. 判別「retarget 成立」的鐵錨

本 skill 引用的每個 antigravity 基座都**真存在**：
- `stealth-browser` MCP(`read_console_messages`／DOM 抓取)✅ — `.mcp.json` 唯一宣告的 MCP。
- `automate.js` ＋ AGENTS.md「Resolved」失敗簽名帳本 ✅ — `/Users/neon/antigravity/automate.js` ＋ AGENTS.md:28-42。
- grepai／ripgrep／git ✅。
- sibling skill 真在 `.agents/skills/`：`gemini-conversation-research` ✅ `dr-research-loop` ✅ `repo-agent-native` ✅ `fold-in` ✅ `external-verify` ✅。

**若哪天有人往 SKILL.md／modules 塞回** L1 Self-Mutation Mode / `execution/scripts/skill_optimizer.py`／`demand_gate.py`／`cold_start_floor.py`／`placebo_guard` / `execution/hooks/*route*.sh` / `hallucination_audit.py` / `data/production/telemetry/*.jsonl` / `subproject-ixsecurity-e2e` / `PG-RFD-NNN` / `ADR-000N` / Pattern Card materializer，那就是把死 husk 搬回來——**擋下**。

---

## Sources / Lineage
- northstar 源：`/Users/neon/northstar/.claude/skills/repo-fullstack-debugger/`(skill.md v0.1.0 ＋ modules ＋ `execution/scripts/skill_optimizer.py` 等)。北極星 empirical source＝`docs/research/…Autobrowse 工程實踐…`(site-debugger 4 層 ＋ 167-line-static 反例)。
- antigravity 慣例：[`antigravity-skill-authoring`](../../antigravity-skill-authoring/SKILL.md)、[`fold-in`](../../fold-in/SKILL.md)、[`judge-loop-chooser/modules/retarget-map.md`](../../judge-loop-chooser/modules/retarget-map.md)(同型 port 先例)、[`AGENTS.md`](../../../../AGENTS.md)。
- 活基座：`automate.js` ＋ AGENTS.md「Resolved」帳本(瀏覽器 L2 實據)、`stealth-browser` MCP、`repo-agent-native`(repo 執行協作者)、`fold-in`(L4 沉澱 actuator)。
