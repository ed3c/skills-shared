<!-- 新專案骨架。由 forgejo-delivery-loop 管理；納管後 SSOT = agent-docs/<repo>/。
     寫法判準與可跑的自檢 → agent-docs/_template/agents-md-template.md
     `<...>` 是必填佔位符：留著它比留空好，留空與「已填完」在讀者眼中同形。 -->

# AGENTS.md - `<repo>`（跨 host SSOT／空間‧基座軸）

> **Format**: Vercel AGENTS.md Standard v3.0 (Antigravity Adapted) · **Purpose**: Passive context injection for AI coding agents (Antigravity CLI)

> **本檔按「基座路由專案管理」排列**：八大基座是空間骨架（§1），Harness 是掛在基座上的實例（§2），
> skill 是可調用的能力（§3），法則的實證歸屬是知識指針（§4），repo 自身的事在最後（§5）。
> 找東西＝先問「它屬於哪個基座」。這與全局 `~/.claude/CLAUDE.md` 的**資料流軸**（入料→構形→閘門→觀測→判定→落帳）互為經緯：
> 那邊管「一次工作怎麼流動」，這邊管「東西住在哪個結構位置」。

---

## §0 座標系 — 四層分工，缺一層就斷

| 層 | 檔案 | 軸 | 職責 | 不做什麼 |
|---|---|---|---|---|
| **法則層** | 全局 `~/.claude/CLAUDE.md` | 時間／資料流 | 跨專案通用判準，**不放實例**、不寫死目錄 | 不指向任何迴圈目錄 |
| **路由層** | **本檔**（每個 repo 一份） | 空間／基座 | 法則主題 → 擁有實證的 Harness；基座 → 實體位置 | 不存實證副本 |
| **編排層** | [`.claude/CLAUDE.md`](.claude/CLAUDE.md) | 觸發／編排 | 階段 × 時機、讓位規則、開不開迴圈、風格與邊界 | 不記結構位置、不抄能力清單 |
| **實證層** | 各 Harness 的 `modules/`／`domain/` | — | 完整方法論、逐案實證、可觸發的動作清單 | 不重述法則 |

判斷歸屬：**判準**寫全局、**位置**寫本檔、**時機與取捨**寫編排層、**實例**寫 Harness。

> **各 host 看它該看的那一面，這是刻意的選擇性擺放**：Codex 讀 `AGENTS.md`（空間／基座軸），
> Claude 讀 `CLAUDE.md`（觸發／編排軸）——錨：`forgejo-delivery-loop/agent-docs/HOST-SURFACES.md` §1。
> **不追求「每個 host 都看到全部」**：每個平台拿到的是為它的工作方式排過的那一面，
> 而不是同一份內容抄兩遍。要完整全景時走 Harness `modules/`，那是兩者按需共用的實證層。

法則層 grep `工程法則的實證歸屬` 即可落到本檔 §4，本檔再指到 Harness。**迴圈改名、法則改寫都不會讓出處斷掉**——
因為法則不記路徑、Harness 不記法則，只有中間這一層記兩者的對應。

---

## §1 八大基座 — 目錄結構資料流圖

大小迴圈**成對**存在：Macro control plane 是這個 repo 的根，Small execution loop 是 `<沙盒根>/` 下的每個沙盒。
同一個基座編號在兩層各有實體，`python3 scripts/check_dual_loop_eight_base.py` 物理驗證兩層各恰好八項。

```
                    Macro control plane                Small execution loop
                    （`<repo>` 根）                        （<沙盒根>/<harness>/）
                    ─────────────────────              ──────────────────────
   契約   B7 ──►  versioned intent/acceptance  ◄──►   PROMPT.md target/success/stop-loss
    │
   入料   B1 ──►  AGENTS.md / CLAUDE.md        ◄──►   sandbox CLAUDE.md + AGENTS.md pointer
    │              ARCHITECTURE.md
    ▼
   閘門   B2 ──►  repo hook 與 gate layer      ◄──►   run.sh 單發 dispatch、explicit
    │              policy                              permission、stdin EOF
    ▼
   路由   B4 ──►  Skill/actor/validator        ◄──►   ROUTES.md（只列 capability，
    │              capability catalog                   不存 concrete DAG）
    ▼
   特化   B5 ──►  composer/judge 的            ◄──►   typed exchange packet 與
    │              bounded node selection               domain-local adapter
    ▼
   觀測   B3 ──►  commit/message/push          ◄──►   logs/、anti/、engine trajectory
    │              transition
    ▼
   驗證   B6 ──►  check_all_skills.py +        ◄──►   verify.sh + good/hollow selftest.sh
    │              plan-package gates
    ▼
   落帳   B8 ──►  execution topology/          ◄──►   PLAN.md iteration/Human edge
                   evolution/receipt state
```

| Base | Macro control plane | Small execution loop |
|---|---|---|
| B1 rules/context | root `AGENTS.md`/`CLAUDE.md`/`ARCHITECTURE.md` | sandbox `CLAUDE.md` + `AGENTS.md` pointer |
| B2 settings/authorization | repo hook 與 gate layer policy | `run.sh` 單發 dispatch、explicit permission、stdin EOF |
| B3 lifecycle/observation | commit/message/push transition | local `logs/`、`anti/`、engine trajectory |
| B4 route discovery | Skill/actor/validator capability catalog | `ROUTES.md`，只列 capability，不存 concrete DAG |
| B5 specialization | composer/judge 的 bounded node selection | typed exchange packet 與 domain-local adapter |
| B6 independent verification | `check_all_skills.py` + plan-package gates | `verify.sh` + good/hollow `selftest.sh` |
| B7 goal contract | versioned intent/requirements/acceptance/budget | `PROMPT.md` target/success/stop-loss |
| B8 state ledger | execution topology/evolution/receipt state | `PLAN.md` iteration/Human edge |

> 完整責任、正負控制、P0-P10 模組化測試經驗與資料流 → [loop-harness-standard modules/dual-loop-eight-base.md](<專案設定目錄>/skills/loop-harness-standard/modules/dual-loop-eight-base.md)
> 泛用執行程序（設定 Prompt→啟動 Harness→驗證狀態→經驗折疊）→ [loop-harness-standard modules/harness-spec.md §6](<專案設定目錄>/skills/loop-harness-standard/modules/harness-spec.md)

**Harness Configuration 實體位置**（本 repo 的基座落點）：

- **B1 rules/context 三件**：`AGENTS.md`（本檔，路由層）＋[`.claude/CLAUDE.md`](.claude/CLAUDE.md)（編排層）＋`ARCHITECTURE.md`。
  三件缺一件，該職責就只能靠記憶補。
- **Config Path**: `.agents/mcp.json` — B4
- **Skills Path**: `<專案設定目錄>/skills/` — B4
- **Claude Skill Forwarders**: `.claude/skills/<name>/SKILL.md`（零邏輯，只指向同名 canonical skill）；
  `.claude/commands/delivery.md` 僅保留 `/delivery` 相容別名。 — B4
- **Mini-Loop Sandboxes**: Each workspace subproject or loop in `<沙盒根>/` implements the 8-Harness standard with its own CWD isolation, EAGER execution rules, and page-specific tests in `<專案設定目錄>/skills/[skill_name]/tests/[page]/[function]/verify.sh` to prevent functional regression. — B6

> **Modularized Section**: Please refer to `<專案設定目錄>/modules/harness-config.md` for the single source of truth regarding MCP servers, Skills, and Problem Graph directory structures.
> **Loop Composite Map & Anti-Simplification Gate**：`<迴圈全景 skill 路徑>` 給 Big Loop vs Mini-Loops 的路線圖。**任何變更皆嚴禁簡化已實裝的閉環架構，且嚴禁拷貝/複製 prompt 以免造成雙圖漂移（提示詞 SSOT 單一真源守則）。**

---

## §2 Harness 註冊表 — 本 repo 的全部迴圈

**全部登記在此**。數量要對得上迴圈沙盒根下的 `PROMPT.md`（排除 repo 根契約、gitignored throwaway、玩具 demo）。新建 Harness 未登記＝沒有人找得到它，等同不存在。

| Harness | 位置 (`<沙盒根>/`) | 觸發詞 | 領域 |
|---|---|---|---|
| **`<name>`** | `<path>/` | `<觸發詞>` | `<這個迴圈守什麼>` |


**分層觸發詞**：

* **全域大迴圈 (Big Loop)**: `"run global composite loop"`, `"執行全域大迴圈"`, `"harness 全景"`, `"執行大迴圈"`
* **特化沙盒小迴圈 (Small Loops)**: `"run subproject sandbox loop"`, `"執行子項目沙盒小迴圈"`, `"d2-e2e-loop"`, `"no-free-coffee-loop"`, `"apns-ecdsa-loop"`, `"android-e2e-loop"`, `"parity-check-loop"`
* **方法論迴圈 (Methodology Loops)**: `"抵達方式"`, `"業務不變量真相"`, `"靜態綠燈但實際壞掉"`, `"invariant 被推翻"`, `"invariant-reach-graph"`

---

## §3 MCP Tools Index
> SSOT = [<專案設定目錄>/modules/harness-config.md](<專案設定目錄>/modules/harness-config.md)（MCP servers／Skills／Problem Graph 目錄結構規範，本節不存副本）。

---

## §4 工程法則的實證歸屬 (Rule → Evidence Routing)

全局 `~/.claude/CLAUDE.md` 的工程法則不直接指向迴圈目錄——法則層綁死在某個 repo 的目錄結構上，迴圈改名即斷。**本節是那一跳的落點**：法則指到這裡，這裡指到擁有實證的 Harness。

| 法則主題 | 實證 Harness |
|---|---|
| `<法則主題>` | `<Harness 路徑>` — `<該處的可觸發內容摘要：訊號→動作→為何有效>` |

> 本 repo 沒有的法則實證，用一行指出去，不留空白。

---

## §5 本 repo 專屬

放最後：這是本 repo 獨有的事，對其他 repo 沒有路由價值。

### Project Overview

`<一段話說這個 repo 是什麼、orchestrate 什麼>`

| Attribute | Value |
|---|---|
| Tech Stack | `<...>` |
| Primary Runtime | `<...>` |
| Core Skill | `<...>` |

### Sub-Project Associations

`<與哪些 workspace 緊耦合，逐條列路徑與角色>`

### Sovereignty
> `<主權分層 SSOT 模組路徑>`

### Resolved Issues & Gotchas
> `<已解問題帳本的 SSOT 模組路徑>`
