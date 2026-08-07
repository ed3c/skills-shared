# AGENTS.md - ix-agy (Antigravity Meta-Repository)

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

大小迴圈**成對**存在：Macro control plane 是這個 repo 的根，Small execution loop 是 `loop_wiki/` 下的每個沙盒。
同一個基座編號在兩層各有實體，`python3 scripts/check_dual_loop_eight_base.py` 物理驗證兩層各恰好八項。

```
                    Macro control plane                Small execution loop
                    （ix-agy repo 根）                  （loop_wiki/<harness>/）
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

> 完整責任、正負控制、P0-P10 模組化測試經驗與資料流 → [loop-harness-standard modules/dual-loop-eight-base.md](.agents/skills/loop-harness-standard/modules/dual-loop-eight-base.md)
> 泛用執行程序（設定 Prompt→啟動 Harness→驗證狀態→經驗折疊）→ [loop-harness-standard modules/harness-spec.md §6](.agents/skills/loop-harness-standard/modules/harness-spec.md)

**Harness Configuration 實體位置**（本 repo 的基座落點）：

- **B1 rules/context 三件**：`AGENTS.md`（本檔，路由層）＋[`.claude/CLAUDE.md`](.claude/CLAUDE.md)（編排層）＋`ARCHITECTURE.md`。
  三件缺一件，該職責就只能靠記憶補。
- **Config Path**: `.agents/mcp.json` — B4
- **Skills Path**: `.agents/skills/` — B4
- **Claude Skill Forwarders**: `.claude/skills/<name>/SKILL.md`（零邏輯，只指向同名 canonical skill）；
  `.claude/commands/delivery.md` 僅保留 `/delivery` 相容別名。 — B4
- **Mini-Loop Sandboxes**: Each workspace subproject or loop in `loop_wiki/` implements the 8-Harness standard with its own CWD isolation, EAGER execution rules, and page-specific tests in `.agents/skills/[skill_name]/tests/[page]/[function]/verify.sh` to prevent functional regression. — B6

> **Modularized Section**: Please refer to `.agents/modules/harness-config.md` for the single source of truth regarding MCP servers, Skills, and Problem Graph directory structures.
> **Loop Composite Map & Anti-Simplification Gate**: Please refer to [antigravity-harness-wiki](file:///Users/neon/ix-agy/.agents/skills/antigravity-harness-wiki/SKILL.md) for the overarching Loop Engineering roadmap (Big Loop vs. Mini-Loops). **任何變更皆嚴禁簡化已實裝的閉環架構，且嚴禁拷貝/複製 prompt 以免造成双图漂移（提示詞 SSOT 單一真源守則）。**

---

## §2 Harness 註冊表 — 本 repo 的全部迴圈

**七個，全部登記在此**。新建 Harness 未登記 = 沒有人找得到它，等同不存在。

| Harness | 位置 (`loop_wiki/`) | 觸發詞 | 領域 |
|---|---|---|---|
| **invariant-reach-graph** | `invariant-reach-graph/` | `抵達方式`、`業務不變量真相`、`靜態綠燈但實際壞掉`、`invariant 被推翻`、`invariant-reach-graph` | 方法論：抵達分級／推翻歷史／靜默推論 |
| **repo_wiki_converge** | `repo_wiki_converge/` | `wiki 收斂`、`Gemini 判官`、`Opus 收斂` | 任意 repo → Opus 級理解 wiki |
| **android_e2e_loop** | `subproject-ixsecurity-e2e/android_e2e_loop/` | `android-e2e-loop` | Android OOBE／REOOBE／email-voip 儀式 |
| **d2_e2e_loop** | `subproject-ixsecurity-e2e/d2_e2e_loop/` | `d2-e2e-loop` | D2 模式端到端 |
| **no_free_coffee_loop** | `subproject-ixsecurity-e2e/no_free_coffee_loop/` | `no-free-coffee-loop` | Agora room 場景 |
| **apns_ecdsa_loop** | `subproject-ixsecurity-e2e/apns_ecdsa_loop/` | `apns-ecdsa-loop` | APNs／ECDSA |
| **parity_check_loop** | `subproject-ixsecurity-e2e/parity_check_loop/` | `parity-check-loop` | iOS ↔ Android 對等性 |

**分層觸發詞**：

* **全域大迴圈 (Big Loop)**: `"run global composite loop"`, `"執行全域大迴圈"`, `"harness 全景"`, `"執行大迴圈"`
* **特化沙盒小迴圈 (Small Loops)**: `"run subproject sandbox loop"`, `"執行子項目沙盒小迴圈"`, `"d2-e2e-loop"`, `"no-free-coffee-loop"`, `"apns-ecdsa-loop"`, `"android-e2e-loop"`, `"parity-check-loop"`
* **方法論迴圈 (Methodology Loops)**: `"抵達方式"`, `"業務不變量真相"`, `"靜態綠燈但實際壞掉"`, `"invariant 被推翻"`, `"invariant-reach-graph"`

---

## §3 MCP Tools Index
> SSOT = [.agents/modules/harness-config.md](.agents/modules/harness-config.md)（MCP servers／Skills／Problem Graph 目錄結構規範，本節不存副本）。

---

## §4 工程法則的實證歸屬 (Rule → Evidence Routing)

全局 `~/.claude/CLAUDE.md` 的工程法則不直接指向迴圈目錄——法則層綁死在某個 repo 的目錄結構上，迴圈改名即斷。**本節是那一跳的落點**：法則指到這裡，這裡指到擁有實證的 Harness。

| 法則主題 | 實證 Harness |
|---|---|
| 多態型別要驗生產端／綠燈值多少看抵達／觀察對象與待證對象要同源／要記得的事綁到共用出口／量測工具的綠燈也是宣稱 | [invariant-reach-graph](loop_wiki/invariant-reach-graph/.agents/skills/invariant-reach-graph/SKILL.md) — 方法論在 `modules/`，逐案實證在 `domain/`，兩者由該 SKILL.md 串連且不得合併 |
| OOBE／REOOBE 金鑰素材覆寫的 Android domain 事實 | [android_e2e_loop soft-key-vault-overwrite](loop_wiki/subproject-ixsecurity-e2e/android_e2e_loop/.agents/skills/android-e2e-loop/modules/soft-key-vault-overwrite.md) |
| 送進一次性資源前先驗素材形狀／搜不到不等於不存在 | [android_e2e_loop email-voip-registration-ceremony §11](loop_wiki/subproject-ixsecurity-e2e/android_e2e_loop/.agents/skills/android-e2e-loop/modules/email-voip-registration-ceremony.md) |
| 落帳分三處／Harness 那端要寫成可觸發的形式 | [invariant-reach-graph refutation-history §7](loop_wiki/invariant-reach-graph/.agents/skills/invariant-reach-graph/modules/refutation-history.md) — **當寫法範本**：訊號→動作→為何有效的三段式，對照同檔 §1-§5（狀態機／落帳格式／收斂量化）看「敘事型」與「可觸發型」的差別 |
| 卡住時換一個變因真跑，別再往深處解釋 | [invariant-reach-graph refutation-history §7](loop_wiki/invariant-reach-graph/.agents/skills/invariant-reach-graph/modules/refutation-history.md) — 觸發訊號（連續 2 個以上假說都在解釋同一失敗／正要讀第三層碼／解釋全指向對方）、動作（列全部輸入變因、只換一個、並列 diff）、為什麼能一次掀掉整疊 |
| 靜默推論＝把窄觀察無聲擴張成強宣稱 | [invariant-reach-graph refutation-history §6](loop_wiki/invariant-reach-graph/.agents/skills/invariant-reach-graph/modules/refutation-history.md) — 三種形狀（樣本→全稱／同形兩態→單態／有回應→機制可用）各配可證偽動作，下結論前逐條過；上游是同檔 §3 的 `silent_refutation` 必須為 0 |
| 自動化操作與測試腳本住在它驗證的那個 Harness 內 | [android_e2e_loop/scripts/](loop_wiki/subproject-ixsecurity-e2e/android_e2e_loop/scripts/) — OOBE 真機驅動四支（`activate-r2-account.py`／`capture-r2token.sh`／`realdevice-oobe-drive.sh`／`realdevice-force-oobe-drive.sh`），2026-08-08 自 `ixsecurity-samples/scripts/` 遷入；`.r2tokens.env` 由 `**/.r2tokens.env` 擋在版控外 |

> 其他 repo 擁有的法則實證（不在本 repo）：`重複組件禁字面推論等價`／`「審計＋跑」不足以宣稱等價` → `skill-bettor/AGENTS.md` §工程原則。

---

## §5 本 repo 專屬

### Project Overview

**ix-agy** is the central meta-repository and Harness for the `subproject-ixsecurity-e2e` integration, fully migrated to the Antigravity CLI standard. It orchestrates the End-to-End testing and diagnostic infrastructure across multiple iOS, Android, and server components.

| Attribute | Value |
|-----------|-------|
| Tech Stack | Python 3.11+, Bash, TypeScript, Antigravity CLI |
| Primary Runtime | Apple Silicon (macOS) |
| Core Skill | `subproject-ixsecurity-e2e` |

### Sub-Project Associations

This repository is tightly coupled with and orchestrates the following workspaces:
1. **TrueMe_iOS** (`/Users/neon/TrueMe_iOS`): Main iOS Client.
2. **TrueMe_Android** (`/Users/neon/TrueMe_Android`): Main Android Client.
3. **ixsecurity** (`/Users/neon/ixsecurity`): Backend microservices.
4. **ixsecurity-samples** (`/Users/neon/ixsecurity-samples`): Sample applications.
5. **ix-spec-runner** (`/Users/neon/ix-spec-runner`): iOS SDK Living Specification (provides `ios-test-automation`).
6. **test_automation_ai** (`/Users/neon/test_automation_ai`): Android Agentic AI Testing (provides `android-test-automation`).
7. **loop_wiki/subproject-ixsecurity-e2e** (`/Users/neon/ix-agy/loop_wiki/subproject-ixsecurity-e2e`): Modularized nested loops sandboxes (D2 mode, No Free Coffee Agora room, APNs/ECDSA, Android, Parity checking).

### Sovereignty
> 主權分層架構（L2 Access Rules／Axiom Summary）→ [.agents/modules/sovereignty.md](.agents/modules/sovereignty.md)

### Resolved Issues & Gotchas
> 已依 fold-in doctrine (B) 全遷至 owner modules（00:F-13/F-17 SSOT 收斂，2026-07-10）；索引與無主教訓全文 → [.agents/modules/resolved-ledger.md](.agents/modules/resolved-ledger.md)
