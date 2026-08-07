---
name: autoresearch-composer
description: |
  autoresearch 迭代迴圈計劃編排器（薄層 router+composer）—— 把外部 autoresearch（uditgoenka
  v2.1.0：全局裝於 `~/.claude/commands/autoresearch/`，`/autoresearch` 核心 + 12 個
  `/autoresearch:<sub>` slash 命令）的自主迭代能力路由成 repo-conformant 的「計劃階段」入口，並在
  「優化/迭代迴圈」類計劃切片裡把 autoresearch 的有界迴圈契約（Goal/Scope/Metric/Direction/Verify/
  Guard/Iterations）編入計劃文件骨架。平行於 `sdlc-plan-composer`：後者編 Matt Pocock 六階段通用
  SDLC，本 skill 只負責「有界 modify→verify→keep/discard 對某指標迭代」這一垂直切片，是
  `sdlc-plan-composer` S5「該 task 是優化迴圈」分支的委派目標。帶讓位優先級規則——debug/security/
  TDD/brainstorm 等已有原生治理 skill 的需求讓位給原生，只有真正的指標迭代迴圈才路由外部 slash 命令。
  本身不執行迴圈，只把迭代紀律與命令路由編進計劃。
  port 自 northstar `autoresearch-composer` v0.3.0（2026-07-17）；逐機制 retarget 帳本 →
  modules/retarget-map.md。
---

# autoresearch-composer

> **Role**：規劃一個含「優化/迭代迴圈」的任務時調用——某個垂直切片是「針對一個可量測指標，反覆
> `modify → verify → keep/discard`，直到收斂或耗盡迭代預算」。單一線性協議：判定是否為真迭代迴圈
> （§1 Gate）→ 選 autoresearch slash 命令（§2 讓位路由表）→ 把 Iteration-Loop Contract block 編入計劃
> 切片（§3）。輸出仍是**計劃文件**，不是程式碼、不是迴圈執行本身。
> **結構**：本檔 = Gate + 路由表 + Contract block + 不變量；port 的命門與誠實帳本 →
> [modules/retarget-map.md](modules/retarget-map.md)。

## When to Use

規劃一個任務時，其中某個垂直切片是「對某指標反覆 modify→verify→keep/discard，直到收斂或迭代預算耗盡」。
核心契約：
- **路由 + 受治理** → 外部 autoresearch slash 命令透過本 skill 的讓位規則被選用，而非裸 `/autoresearch:X` 直呼。
- **迴圈紀律編入計劃** → 每個迭代切片帶一個填好的 Iteration-Loop Contract block（§3），缺欄位即 INCOMPLETE。
- **本身不執行** → 與 `sdlc-plan-composer` 同邊界：只到「計劃寫好」為止，執行交回 `/autoresearch:<sub>` slash 命令。

## Not For

- ❌ **執行迭代迴圈**：本 skill 只產計劃。執行走 `/autoresearch` 或 `/autoresearch:<sub>` slash 命令
  （已全局裝於 `~/.claude/commands/autoresearch/`，antigravity 無 ENCD/`cycle-dispatch` 這類中介層，
  執行完直接交 `implement`/`tdd` 消化，見 modules/retarget-map.md）。
- ❌ **通用多階段計劃**：非迭代迴圈的多階段任務用 `sdlc-plan-composer`（六階段 SDLC）。本 skill 只覆蓋其
  優化迴圈垂直切片，是它 S5 的特化委派，非替代。
- ❌ **路由已有原生治理 skill 的需求**（核心 anti-duplication，見 §2 讓位規則）：
  - 通用 bug/排錯、難復現/效能回歸 → `diagnose` / `diagnosing-bugs`（**不**路由 `/autoresearch:debug`）。
  - 寫碼/修錯 → `tdd`（**不**路由 `/autoresearch:fix`，除非是「錯誤計數歸零」型有界量測迴圈且 TDD 不適用）。
  - 安全審計 → `/security-review` + `sast-validator`（**不**路由 `/autoresearch:security`）。
  - 需求澄清/設計辯論 → `grilling` / `grill-with-docs` / `grill-me`（**不**路由 `/autoresearch:predict`
    `:reason` `:probe`）。
  - 只有當需求是 autoresearch **唯一**獨有的「有界 metric-driven keep/discard 迴圈 + Guard」時才路由外部
    slash 命令。
- ❌ **取代 `to-prd`+`implement`**：那是通用計劃骨架；本 skill 在其之上疊加迭代迴圈契約。
- ❌ **決定一個迭代需求該不該存在**：那是人類 go/no-go，本 skill 只提供契約骨架。
- ❌ **無 Verify 可量化的「優化」**：若指標無法用一條輸出數字的 shell 命令量測，不是 autoresearch 迴圈——
  退回 `grilling`/`grill-with-docs` 先把成功準則量化。

## §1 — Iteration-Loop Gate（進路由前的判據）

一個計劃切片要走本 skill，必須**全部**成立（任一不成立 → 退回 `sdlc-plan-composer` / 原生 skill）：

| 判據 | 問句 | 不成立 → 路由去向 |
|------|------|------------------|
| **可量測** | 是否有一條**輸出單一數字**的 `Verify` shell 命令？ | 無 → `grilling` 先把成功準則量化 |
| **有方向** | `Direction` 是 higher_is_better 還是 lower_is_better（明確）？ | 模糊 → 釐清後再進 |
| **可守護** | 有沒有一條**永遠必須 pass** 的 `Guard`（測試/build）防止迴圈把系統改壞？ | 無 Guard → 標風險，迴圈前必須補 |
| **有界** | `Iterations` 是有限 N（預設見 §2），還是明確 opt-in `unlimited`？ | 預設有界，unlimited 需顯式理由 |
| **keep/discard 語義** | 每次迭代是否「改一處 → 量測 → 變好則留、變差則丟」？ | 否（是線性多階段）→ `sdlc-plan-composer` |

## §2 — slash 命令路由表（帶讓位優先級，antigravity 版）

外部 autoresearch 13 slash 命令（`/autoresearch` 核心 + `/autoresearch:<sub>` ×12，已全局裝於
`~/.claude/commands/autoresearch/`）→ 計劃切片需求映射。**讓位規則優先**：標 ⚠️ 者本 repo 有更治理的
原生 skill，預設讓位，僅當需求嚴格是「有界量測迴圈」且原生 skill 不適用時才路由外部。

| slash 命令 | 計劃切片需求 | 預設迭代 | 路由判定（antigravity 讓位對象） |
|---|---|---|---|
| `/autoresearch`（核心） | 對某指標 modify→verify→keep/discard | 25 | ✅ **獨有**——repo 無一級對應，路由 |
| `/autoresearch:evals` | 分析迭代結果（趨勢/高原/回歸） | N/A | ✅ **獨有**——迴圈後分析，路由 |
| `/autoresearch:improve` | 研究 ICP 挑戰 → 發現改進 → 生 PRD | 15 | ✅ 配 `to-prd`（PRD 落地走 mattpocock 原生 to-prd） |
| `/autoresearch:scenario` | 跨 12 維度生邊界案例 | 20 | ✅ 大量邊界生成屬迭代型，路由；但測試設計諮詢用 `tdd` |
| `/autoresearch:learn` | 掃 codebase → 生文檔 → 驗證 → 修迴圈 | 10 | ⚠️ 文檔生成讓位 `improve-codebase-architecture`（mattpocock 全局 skill）；純迭代驗證迴圈才路由 |
| `/autoresearch:ship` | 8 階段 ship（checklist→dry-run→deploy→verify） | N/A | **無讓位對象**——antigravity 無 devops-hub/ship 管線治理層，本專案本質是自動化腳本+skill harness 非部署型產品；誠實留白，需要時直接路由，不硬造假讓位 |
| `/autoresearch:debug` | hypothesize→test→falsify 獵 bug | 15 | ⚠️ **讓位** `diagnose` / `diagnosing-bugs` |
| `/autoresearch:fix` | 逐一清零錯誤 | 20 | ⚠️ **讓位** `tdd`；僅「錯誤計數歸零」有界量測迴圈例外 |
| `/autoresearch:security` | STRIDE+OWASP 紅隊審計 | 15 | ⚠️ **讓位** `/security-review` + `sast-validator` |
| `/autoresearch:predict` | 5 專家人格實作前辯論 | N/A | ⚠️ **讓位** `grilling` |
| `/autoresearch:reason` | 盲評審對抗辯論至收斂 | 8 | ⚠️ **讓位** `grilling` / `grill-with-docs` |
| `/autoresearch:probe` | 8 人格審問需求至飽和 | 15 | ⚠️ **讓位** `grill-with-docs` / `grill-me` |
| `/autoresearch:plan` | 把 goal 轉成 validated Scope/Metric/Direction/Verify 配置 | N/A | ✅ 路由——**正是 §3 契約欄位的產出器**（見 §3） |

> **TCC 守門**：讓位（⚠️）優先於路由外部。每次選用外部 slash 命令時，計劃文件須記一行
> `> autoresearch-route: /autoresearch:<sub> (原生讓位已評估: <原生 skill or N/A> — 理由)`，供人審計
> 判定不是繞過治理。

## §3 — Iteration-Loop Contract Block（編入計劃切片）

> **產出方式（extend don't duplicate）**：契約的 Goal/Scope/Metric/Direction/Verify 欄位**不手寫**——跑
> `/autoresearch:plan`（其本職正是把 goal 轉成 validated Scope/Metric/Direction/Verify 配置），本 skill
> 只把它的輸出**嵌入計劃切片** + **補 Guard/Iterations/route/讓位評估**並受治理。`/autoresearch:plan` 缺
> Guard 概念（autoresearch 的 Guard 是迴圈級安全網）→ Guard 由本 skill 依 §1 判據補齊。

通過 §1 Gate 的每個迭代切片，在其 `NN-<slice>.md` 注入以下 block（缺任一必填欄位 = INCOMPLETE）：

```yaml
# --- autoresearch iteration-loop contract (注入自 autoresearch-composer) ---
# Goal/Scope/Metric/Direction/Verify ← /autoresearch:plan 產出後填入；Guard/Iterations/route/executor ← 本 skill 補
goal:        "<要改進什麼>"                 # 必填（/autoresearch:plan）
scope:       "<file globs>"                  # 必填（/autoresearch:plan）——迴圈可改的檔案邊界
metric:      "<量測什麼>"                    # 必填（/autoresearch:plan）
direction:   higher_is_better               # 必填（/autoresearch:plan）——或 lower_is_better
verify:      "<輸出單一數字的 shell 命令>"   # 必填（/autoresearch:plan）——§1 可量測判據
guard:       "<永遠必須 pass 的 shell 命令>" # 必填（本 skill 補）——測試/build；無則顯式 `none` + 風險註記
iterations:  25                              # 有界預設見 §2；unlimited 需 justification 欄位
evals:       false                           # 是否 mid-loop checkpoint（→ /autoresearch:evals）
route:       "/autoresearch:<subcmd>"        # §2 選定的 slash 命令（裸迴圈用 /autoresearch）+ 讓位評估
executor:    "slash-command:/autoresearch:<subcmd>"  # antigravity 無 cycle-dispatch，一律 slash 命令直執行
# --- end contract ---
```

**安全不變量繼承**（外部 autoresearch SKILL.md §Safety Invariants）：迴圈**不 push/deploy 不經明示批准**；
預設有界；結果落 `autoresearch/{subcommand}-{YYMMDD}-{HHMM}/`。本 skill 把這些寫進計劃切片的「執行契約」
段，讓執行半（`/autoresearch:<sub>` slash 命令）有據可循。

## §3.5 — rejection-log + edit-budget（選填特化，通用可攜）

§3 契約骨架可選加兩個選填槽（省略 = 現狀零變化）：

```yaml
rejection_log: "autoresearch/<run>/rejections.md"  # 選填——每次 discard 記變異+原因；下一迭代 modify 前讀，不重走已否決方向
edit_budget:   "linear-decay floor=1"              # 選填——迭代遞增收緊單次 modify 幅度；floor>0（預算永不凍結迴圈）
```

- **rejection_log** 只省 verify 成本（不重 walk 否決路徑），**不動** keep/discard 判準（Metric+Guard 仍唯一裁決）。
- **edit_budget** 只約束「一次改多大」，永不選方向、永不加迭代。
- 兩槽永不進 fitness 統計。

## §4 — 與 sdlc-plan-composer 的組合（非競爭）

本 skill 是 `sdlc-plan-composer` **S5 階段的特化委派**，不是替代：

```
sdlc-plan-composer S0..S4  →  S5 移交/維護紀律入計劃
                               └─ 若某 task 是「優化/迭代迴圈」
                                  → 委派 autoresearch-composer
                                     → §1 Gate → §2 路由 → §3 (/autoresearch:plan 產欄位 + 嵌入)
                                  → 回填該 NN-<slice>.md 的「執行契約」段
```

兩者 Output Contract 同構（落 `docs/plans/<date>-<topic>/`），本 skill 只新增/充實「優化迴圈切片」的
Iteration-Loop Contract block，不改 `sdlc-plan-composer` 的其餘骨架。獨立調用（非經 `sdlc-plan-composer`）
亦可——直接對一個已知的優化迴圈任務產出帶 contract 的計劃切片。

## Output Contract（Boundary Artifact）

複用 `sdlc-plan-composer` 的計劃目錄，新增/充實優化迴圈切片：

```
docs/plans/<date>-<topic>/
├── 00-intent-and-knowhow.md        # （若獨立調用）記迭代意圖 + §1 Gate 判定 + 讓位評估
├── NN-<optimization-slice>.md      # 含 §3 Iteration-Loop Contract block + §2 route 行
└── （其餘骨架由 sdlc-plan-composer 提供）
```

## 整合接點（Wiring — 必為實接，非宣稱）

- **接 `sdlc-plan-composer` S5**：`sdlc-plan-composer` SKILL.md 的 S5 row 已委派本 skill（見其
  modules/retarget-map.md 該格由「誠實留白」改為「已落地」）。
- **執行半委派**：Contract block `executor` = `/autoresearch:<sub>` slash 命令（全局裝於
  `~/.claude/commands/autoresearch/`）。antigravity 無 ENCD/`cycle-dispatch`，含並行檔案變更的迴圈
  直接交回主會話手動用 `Agent`/`Workflow` 工具分治（見 `sdlc-plan-composer/modules/multi-model-subagent-dispatch.md`），
  不硬造一層中介 dispatch。
- **不跨層**：本 skill 只到「計劃寫好」；執行交回 `/autoresearch:*` slash 命令 / `implement` / `tdd`。

## Experience Accumulation

每次調用後：若發現新的迭代反模式（無 Guard 的迴圈把系統改壞、Verify 不輸出數字、讓位規則被繞過直路由
已有原生 skill 的需求、unlimited 無 justification），記為候選並回饋 §1 Gate / §2 讓位表。若外部
autoresearch slash 命令集變動（升版增刪 `~/.claude/commands/autoresearch/`），更新 §2 路由表——`upstream-watch`
的 `--manual` 追蹤可掛此依賴。

*port 自 northstar `autoresearch-composer` v0.3.0（2026-06-05 設計，2026-07-17 port 進 antigravity）。
antigravity 版無 `encd-infrastructure-hub`/`skill-cycle`/liveness-grounding YAML 治理欄位，故不帶 northstar
那套治理系統——本檔以 `~/.claude/commands/autoresearch/` 現存目錄 + 本 repo `.agents/skills/` 現存目錄作為
路由目標真實性的鐵錨（見 modules/retarget-map.md）。*
