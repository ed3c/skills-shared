---
name: sdlc-plan-composer
description: |
  計劃階段 SDLC 編排器 —— 規劃一個多階段任務時，把 Matt Pocock 六階段 AI 原生 SDLC 紀律編進計劃
  文件骨架，序列委派既有 atomic skill（不重寫）：S-1 brownfield 前置委派 repo-agent-native（antigravity
  本地 fork）抽既有系統真相 → S0 Premise Disproof Challenge（否證此需求是否該存在）→ S1 意圖對齊
  （grill-with-docs）→ S2 任務分解（to-prd/to-issues，曳光彈垂直切片）→ S3 介面設計
  （design-an-interface + 決策記錄稀疏三條件，非編號 ADR）→ S4 子代理分治計劃（Claude Code 原生
  Agent/Workflow 工具，人工三選一派 Opus/Sonnet/Haiku 原生、codex exec GPT-5.5/5.4/5.4-mini、
  或 agy Gemini Pro/Flash，非自動觸發）→
  S5 執行契約 + judge-loop-chooser（antigravity 本地 fork）驗證標準。recipe-not-engine：只把工程紀律
  編進計劃文件骨架，不執行任務、不重寫被委派的 atomic skill。
  何時用：要規劃一個多階段任務、要先把所有任務計劃好再動手、希望計劃文件本身就帶工程紀律（意圖對齊／
  垂直切片／介面深模組／TDD／交接／長期維護）時。
  NOT for：執行任務／寫程式碼（`implement`／`tdd`）、單步或探索性需求未成形（先
  `unknown-discovery-composer` 收斂到「能寫計劃」）、判產物驗證標準本身（`judge-loop-chooser`）。
---

# sdlc-plan-composer

> **Role**：規劃一個**多階段任務**、要「先把所有任務計劃好再動手」時調用。是一個**單一線性協議**：把
> 計劃文件的每一節對映到 Matt Pocock 六階段 SDLC 的一個階段，每階段**委派既有 atomic skill**（不重寫），
> 輸出是**結構化計劃文件骨架** + **意圖/why 單獨檔**。
> **結構**：本檔 = S-1..S5 階段協議表 + 不變量 + Gotchas；port 的命門與誠實帳本（northstar 有什麼被拿掉/
> 換掉/誠實留白）→ [modules/retarget-map.md](modules/retarget-map.md)。
> **SSOT**：路由目標的真實性以 `~/.agents/skills/`（mattpocock 全局 skill 目錄）與本 repo
> `.agents/skills/` 現存目錄為準——委派前先確認目標真在 disk，缺席就誠實標「不在」給替代，禁偽委派。
> **Lineage**：port 自 northstar `sdlc-plan-composer`（`.claude/skills/sdlc-plan-composer/skill.md`
> v0.1.0，empirical source：northstar
> `docs/research/基於 Matt Pocock 原子技能庫的 AI 原生軟體開發生命週期（SDLC）深度架構報告.md`——該文檔
> 是 northstar 內部研究文檔，非本 repo 基座，僅供追溯脈絡，不引用其路徑為依賴）。**填補**
> `unknown-discovery-composer` port 當時（cc-20260704）誠實記錄的缺口——當時無基座、U1 出口退化到裸
> `superpowers:writing-plans`；本 skill 落地後 `unknown-discovery-composer` 已改指回本 skill（見其
> modules/retarget-map.md）。非原樣搬；northstar 專屬治理基座（hallucination_audit.py 機器閘／
> `provenance.yaml` Schema-A cards／`cross-repo-topology.yaml`／encd-infrastructure-hub／skill-cycle／
> task-graph-decomposer／編號 ADR／skill-conformance-hub 治理欄位）**無/未-wire 已拿掉並記錄** →
> retarget-map.md。

## 🚩 STOP — 你在合理化（違反即停）

| 念頭 | 現實 |
|---|---|
| 「這個需求想都不用想，直接進 S1」 | ❌ S0 Premise Disproof 必先跑：≥3 個「此需求是偽需求」的可證偽理由未列 = 未完成 S0 |
| 「brownfield 但懶得跑 repo-agent-native，憑印象寫前提」 | ❌ 前提建立在 D 級腦補上；brownfield 判定成立必先過 S-1（或顯式記 N/A 理由） |
| 「design-an-interface 太重，這裡直接寫一個方案就好」 | ❌ S3 至少 2 個截然不同抽象方案 + 權衡分析，委派 design-an-interface 產出，不可單方案跳過比較 |
| 「這個決策記錄反正沒人會查，隨便寫兩句」 | ❌ 稀疏三條件全滿足才寫決策記錄，但寫了就是後續開發不可逾越的約束——隨便寫 = 誤導後人 |
| 「S4 分治先講好就好，衝突到時候再說」 | ❌ BS #420 三角互斥必須啟動前二選一告知用戶，事後才發現 = 協作失敗 |
| 「judge-loop-chooser 沒有 code-branch，那我自己編一套代碼判準」 | ❌ 代碼產物直接交棒 `code-review`，不現造 judge 分支（antigravity 版明言無此基座） |
| 「計劃裡用了 agy／`claude -p`／外部工具，到時候能跑就好」 | ❌ **外部工具依賴必須在用它的步驟前加預檢步（tracer）**；silent no-op／額度枯竭／stdin hang 都是 **exit-0 假成功**，不先驗計劃執行到一半才炸。判成敗看**輸出檔生成否**非 exit code（fold-in 2026-07-09，autoresearch A3：agy 額度枯竭 silent no-op 白燒一次 run；見記憶 [[agy-quota-silent-noop]]） |

## When to Use

規劃一個**多階段任務**、要「先計劃好再動手」，且希望**計劃文件本身就承載工程紀律**時調用。核心契約：
- **先計劃好** → S0-S5 全部在動手前完成；計劃文件是交付物，不是程式碼。
- **原始意圖與 know-how/why 單獨紀錄** → `00-intent-and-knowhow.md`（SSOT，與分階段計劃檔分離）。
- **分階段輸出計劃文件** → 每個垂直切片一個 `NN-<stage>.md`。
- **子代理分治** → 每階段計劃細節由獨立子代理撰寫，主會話只持指針（避免上下文膨脹）。
- **不簡化** → 子代理 full-detail 寫 outcome，禁止壓縮資訊量。

## Not For

- ❌ **執行任務 / 寫程式碼**：本 skill 只產計劃文件。執行走 `implement` / `tdd`（antigravity 無
  skill-cycle/ENCD 這類編排層，計劃寫完直接交執行，不經中介 dispatch）。
- ❌ **重寫六階段 atomic skill**：`grill-with-docs` / `to-prd` / `to-issues` / `tdd` / `diagnose` /
  `design-an-interface` / `improve-codebase-architecture` 皆已在 `~/.agents/skills/` 全局可用，本 skill
  只序列委派，不複製。
- ❌ **取代 `to-prd`+`implement`**：`to-prd`+`implement` 是通用輕量 spec→build 鏈；本 skill 是**在其之上**
  疊加 SDLC 階段語義 + atomic-skill 路由的厚層（單階段/需求已很清楚時，直接用 `to-prd`+`implement` 更省）。
- ❌ **單步 / 探索性需求未成形**：需求還在霧裡，先走 `unknown-discovery-composer`（U0-U1 收斂到「能寫
  計劃」）或 `grilling`，收斂後才用本 skill。
- ❌ **決定一個需求該不該存在**：那是 S0 Premise Disproof 的人類判斷，本 skill 只提供否定性評估的提問
  框架，不替你做 go/no-go。
- ❌ **產物驗證標準/tier 選擇本身** → `judge-loop-chooser`（本 skill 的 S5 只委派過去，不重複其路由邏輯）。

## S-1 — Repo Invariant Extraction（brownfield 前置）

> brownfield 規劃若不先取得既有系統真相，產出的垂直切片會「看似完整實則破隱含合約」。本節把
> `repo-agent-native`（antigravity 本地 fork）的真相提取 shift-left 到規劃階段之前。

### (a) Brownfield 偵測判據

| 條件（OR — 任一成立即 brownfield） | 偵測方式 |
|---|---|
| 計劃任務會 **touch 一個既有 repo** 的源碼 | 任務描述含既有 repo 絕對路徑，或計劃會修改/呼叫既有服務 |
| 計劃涉及 **整合層代碼**（跨服務 message / shared state / API 合約） | 任務需穿過既有 message queue / 共享 DB / 既有 API endpoint |
| 計劃的垂直切片會 **依賴一個未由本團隊撰寫的執行前提** | 切片貫穿到一個既有服務的 timeout / 驗證邏輯 / DB routing |

**greenfield → S-1 N/A**：全新 repo / 無既有源碼依賴 / 純文檔或純新建 skill。N/A 時在
`00-intent-and-knowhow.md` 記一行 `S-1: N/A (greenfield)` 後直接進 S0，**不委派 repo-agent-native**
（無輸入的空稅）。

### (b) 委派 repo-agent-native（不重寫、不合併）

brownfield 成立 → **委派** `.agents/skills/repo-agent-native/SKILL.md`（S0-S8：SCOPE→INGEST→
INVARIANT→IMPLICIT-DEP(S2.5 破盒推論)→INDEX→AUDIT→SSOT→FEEDBACK）對目標 repo 提取真相。本 skill
只**消費**其產物，提取邏輯（四層精準度 ripgrep→grepai→Serena(條件式)→Read body、破盒推論五步驟、
Evidence Level 認識論）全在 repo-agent-native，本 skill 不複製。

### (c) 消費的 Boundary Artifact（路徑為 SSOT，禁臆造）

repo-agent-native 產出**單一**不變量頁 `<OUT>/invariants/<slug>/<page>.md`（frontmatter
`kind: invariants` + `commit_hash`），本 skill 唯讀消費其三類條目：

| 條目類型 | 內容 | 餵入規劃哪一層 |
|---|---|---|
| `INV-*`（Message/State/API Contract） | 三類業務不變量，每筆帶 Evidence Level(A/A-/B+/B/C/D) + `source_ref` | S0（前提否證）+ S1（grill 對真實合約）+ S3（介面不撞合約） |
| `NEG-*`（負向不變量） | 確認某假設**不存在**（grepai 空結果 = A 級 absence） | S0（計劃前提不建立在錯誤假設上） |
| `IMPL-*`（S2.5 破盒推論隱含依賴） | 未索引服務/共享狀態耦合/靜默失敗鏈，各帶 `resolution_status` | S2（垂直切片必須穿過相關隱含依賴） |

> ⚠️ **無 northstar 的 `cross-repo-topology.yaml`/`hallucination-ledger.yaml`/`registry.yaml`**——三者在
> antigravity 無基座，已拿掉（見 retarget-map.md）。上表三類條目全部內嵌在同一張不變量頁裡，非分散
> 三個 YAML。

**空提取防護（繼承 repo-agent-native Empty-Output Contract）**：若委派後不變量頁出現
`extraction_failure_reason`，**S-1 視為失敗**，不得進 S0；計劃須記錄缺口並停（fail-loud，禁 silent
Half-Bridge）。

### (d) TCC 守門：何時新跑、何時重用快取

`repo-agent-native` 是重流程。守門條件（讀不變量頁自己的 frontmatter，**無**獨立 registry.yaml）：

```bash
repo_path=<目標 repo 絕對路徑>
page=<OUT>/invariants/<slug>/<page>.md
current=$(git -C "$repo_path" rev-parse HEAD 2>/dev/null)
registered=$(grep '^commit_hash:' "$page" 2>/dev/null | awk '{print $2}')
[ -n "$registered" ] && [ "$current" = "$registered" ] && echo "REUSE (cached page fresh)" || echo "STALE → fresh repo-agent-native extraction required"
```

### (e) S-1 完成條件（gate 進 S0）

- brownfield 判定已記入 `00-intent-and-knowhow.md`（brownfield: yes/no + 理由）。
- 若 brownfield：不變量頁已存在且非空（無 `extraction_failure_reason`），STALE 判定已執行。
- 每個將被 S0–S3 引用的事實都可回指頁面中帶 Evidence Level + `source_ref` 的條目。

### (f) 反幻覺 = SURFACE，非機器閘（誠實能力差距）

northstar 版靠 `provenance.yaml`（Schema-A cards）+ `hallucination_audit.py` 兩道污染矩陣 CLI 做**機器
BLOCK**。**antigravity 無此基座**——反幻覺改由 repo-agent-native 自己的 S4 AUDIT SURFACE 承接：
`a_ratio=<A級/總>`、`unverified_count=<n>` 一行交人裁。D 級事實禁止當計劃前提是**人的自律**，不是
exit-code 擋下。若計劃引用了標記 `unverified`/`inferred` 的條目當前提，S0 否證段必須顯式標注「此前提
未過 A 級驗證，風險自負」。

### (g) 外部-currency lane（S-1 補 2026-07-19：repo-internal 檢索不夠）

(c) 的 `INV-*/IMPL-*` 只錨 **repo-internal** 事實（`source_ref` grep 得到＝當下最新）。但計劃常需**外部／
post-cutoff 事實**（框架版本／API 能力／庫行為／「X 工具支不支援 Y」）——這類 **repo 裡 grep 不到、模型會
從訓練記憶補＝過時**。每個計劃前提**先分三態**，交 S0-S4 前完成升級：
- **repo-internal** → (c) repo-agent-native grep（`source_ref` 錨，最新）。
- **external／post-cutoff** → **委派 [`external-verify`](../external-verify/SKILL.md)（官方 primary
  doc）＋ agy（Gemini web／DR）＋ stealth_fetch**，非訓練記憶；附查證日期（快照會過期）。
- **[推論]**（模型推測、無錨） → **不可當計劃前提交執行**（同 (f) D 級腦補 STOP；須先升級到前兩態）。

派工紀律（誰檢索、Judge 放哪、agy 用在何處、指針非散文 handoff）見
modules/multi-model-subagent-dispatch.md 原則五。

### S-1 GATE 規則（artifact → S 階段，violation = INCOMPLETE）

| Gate | 消費條目 | S 階段 | PASS 條件 | violation（INCOMPLETE） |
|---|---|---|---|---|
| G-S0 | `NEG-*` + `INV-*` | S0 | 否證理由引用的條目皆有 Evidence Level ≥ C 且有 `source_ref` | 用未驗證的 D 級腦補當否證理由 |
| G-S1 | `INV-*`（Message/State/API） | S1 | grill 對齊的合約皆回指 `INV-*`(A/A-/B+) | 對臆想需求 grill / 對齊到不存在的合約 |
| G-S2 | `IMPL-*`（S2.5 隱含依賴） | S2 | 每個跨既有服務的垂直切片 account for 所有相關 `IMPL-*`（穿過或顯式 N/A+理由） | 切片未提相關 `IMPL-*` → 不穿過隱含依賴 |
| G-S3 | `INV-*`（API/State） | S3 | 新介面不撞既有 `INV-API-*` | 改既有 API 合約卻無決策記錄 |

**引用慣例**：跨 skill 階段引用前綴 skill 名（`sdlc-plan-composer §S-1` / `repo-agent-native S2.5`）；
不變量引用用 `repo-agent-native:INV-001` 冒號前綴格式（machine-parseable）。

## SDLC 計劃編排協議（單一線性流程）

每階段格式固定：**委派哪個 atomic skill → 寫進計劃文件哪個 artifact → 該階段的工程紀律 gate**。

| 階段 | 委派 atomic skill | 計劃 artifact | 工程紀律 gate |
|------|------------------|--------------|--------------|
| **S0 Premise Disproof** | （inline，無對應 skill） | `00-intent-and-knowhow.md` §否定性評估 | 至少 3 個理由嘗試證明此需求是「偽需求」+ 掃 `~/.agents/skills/` 與本 repo `.agents/skills/` 找是否已有零件能解 + 查既有決策記錄有無已否決的同類設計。無法否證才進 S1。**（brownfield: ⟵ `NEG-*`/`INV-*` — 前提不建立在已否決/未驗證假設上）** |
| **S1 意圖對齊** | `grill-with-docs`（或 `grill-me`） | `CONTEXT.md`（統一語言）+ `00-intent-and-knowhow.md`（原始意圖 + know-how + why，**單獨檔**） | 蘇格拉底式追問消歧義；canonical terms 壓低語義熵。沉澱的是**散文決策記錄**，非編號 ADR。**（brownfield: ⟵ `INV-*` — grill 對真實合約，非臆想需求）** |
| **S2 任務分解** | `to-prd` → `to-issues` | 分階段 `NN-<stage>.md`（每檔一垂直切片）+ 依賴圖 | **曳光彈垂直切片**：每 task 貫穿資料→邏輯→介面→test，禁水平分層。**（brownfield: ⟵ `IMPL-*` — 每切片穿過相關隱含依賴或顯式 N/A）** |
| **S3 介面設計** | `design-an-interface` | `docs/decisions/<slug>.md`（散文決策記錄，非編號 ADR） | 委派產 ≥2 個截然不同的抽象介面 + 權衡分析（並行子代理）；**決策記錄稀疏三條件**（見下）全滿足才寫。**（brownfield: ⟵ `INV-*` API/State — 新介面不可撞既有合約）** |
| **S4 子代理分治計劃** | Claude Code 原生 `Agent`/`Workflow` 工具（人工三選一派工，見 modules/multi-model-subagent-dispatch.md） | 每階段 plan 細節（子代理 full-detail 撰寫） | 主會話只持指針；**不簡化**；遵守 BS #420 三角互斥（見下） |
| **S5 執行契約 + 驗證標準** | `tdd` + `diagnose` + `handoff`（或 `claude-handoff`）+ `improve-codebase-architecture` + `judge-loop-chooser`（S5 驗證標準委派，見下） | 每 task 的「執行契約」段 | TDD 紅綠重構 + diagnose 先建確定反饋閉環 + handoff 前自查有無漏 load-bearing negative（antigravity 無 `fidelity-handoff` 的形態決策+lint 覆蓋閘，裸 handoff 靠自律，見 retarget-map.md）+ 維護期刪除測試找淺模組 |

> S4 分治派工的三個 backend（Claude Code 原生 Agent/Workflow 的 Opus/Sonnet/Haiku、`codex exec` 的
> GPT-5.5/5.4/5.4-mini、`agy` 的 Gemini Pro/Flash）**皆非自動觸發**——主會話逐 task 人工決定用哪個，
> 完整派工語法 + 2026-07-17 external-verify 查證見 modules/multi-model-subagent-dispatch.md。

### S0 Premise Disproof Challenge

1. 寫下 ≥3 個「此需求是偽需求」的可證偽理由。
2. 掃 `~/.agents/skills/` + 本 repo `.agents/skills/` 找是否已有零件能解（避免重造）。
3. 查既有決策記錄（`docs/decisions/` 或計劃目錄內散文記錄）是否有已否決的同類設計。
4. 三者皆無法否證 → 通過，進 S1。任一成立 → 標 `wontfix` 並寫入 `.out-of-scope/` 理由，不進計劃。

### S3 委派 design-an-interface + 決策記錄稀疏三條件

`design-an-interface`（`~/.agents/skills/design-an-interface`，mattpocock「Design It Twice」多方案介面
設計）全局可用。S3 介面設計**委派該 skill**（requirements 蒐集 → 並行子代理產截然不同方案 → 權衡比較）；
skill 缺席（罕見）→ fail-loud 退回 inline checklist（設計 ≥2 截然不同抽象介面 + 權衡分析）。

**決策記錄稀疏三條件是本 skill 治理側 gate，不隨委派外移**——只有**同時**滿足三條件才寫決策記錄：
1. **決策難以逆轉**（換 DB / 訊息佇列 / 驗證框架等高重構成本）。
2. **缺脈絡時顯得突兀**（後人易「優化」回看似顯然但錯誤的方向）。
3. **真實權衡產物**（效能/安全/合規導致的非對稱選擇）。

決策記錄落 `docs/decisions/<slug>.md`（**非編號 ADR**——antigravity 無編號 ADR/DDR 系統），一旦寫入即成
後續開發不可逾越的約束。

### S4 子代理分治約束（BS #420 三角互斥）

分治計劃撰寫時，「autonomous + 主會話輕量 + per-task fresh-context 子代理」三者不可兼得：
- per-task fresh-context 子代理隔離 ⟹ 主會話編排（context 必漲）。
- 主會話輕量 ⟹ 單一背景 runner（無 per-task 隔離）。

啟動前二選一並告知用戶，不可事後才發現衝突。並行寫多個階段計劃時用 git worktree 隔離或
specific-file-only `git add`。

### S5 Judge/evals 標準 + 驗證 tier（委派 judge-loop-chooser，antigravity 本地 fork）

deliverable 可判的計畫，S5 執行契約**按 deliverable 類型分流**選驗證標準 + tier（**委派**
`.agents/skills/judge-loop-chooser/SKILL.md`——本 skill 不重複其路由邏輯）：

- **DR 報告 / 卡片盒吸收物**（若計劃的產出經 antigravity DR 管線落地）→ judge-loop-chooser 的意圖漂移
  審查分支（intent = 原卡片盒問題）。
- **COMPLETENESS 覆蓋矩陣** → judge-loop-chooser 逐維度三態 grounding 分支。
- **技術選型 fit-to-plan**（S3 design-an-interface 若涉及選 OSS 堆疊/repo）→ judge-loop-chooser 的
  5-axis 匹配度 rubric 分支——與 S3「≥2 截然不同方案 + 權衡分析」天然銜接。
- **代碼產物** → **直接 `code-review`**（judge-loop-chooser antigravity 版明言「無 code-branch」，見其
  modules/retarget-map.md；不現造代碼判準分支）。
- 驗證 tier = judge-loop-chooser 的**四層獨立性階梯**（T0 確定性 / T1 零存取 / T2 跨家族 / T3 人）——
  **非** northstar 的 macro/micro 模型路由（antigravity 無 `task-graph-decomposer` 這類模型路由 SSOT，
  已拿掉，見 retarget-map.md）。

**S5 優化迴圈**（2026-07-17 已港補齊，取代先前誠實留白）：若某 task 本質是「有界
modify→verify→keep/discard 對某可量測指標迭代」，**委派** `.agents/skills/autoresearch-composer/SKILL.md`
（antigravity 本地 fork）——其 §1 Gate 判定是否為真迭代迴圈、§2 讓位路由表選 `/autoresearch:<sub>`
slash 命令（已全局裝於 `~/.claude/commands/autoresearch/`）或讓位本地原生 skill（`diagnose`/`tdd`/
`grilling`/`/security-review` 等）、§3 把 Iteration-Loop Contract block 嵌入該 `NN-slice.md`。本 skill
不重複其 Gate/路由邏輯。

### S6′ 執行反哺（指針，執行後）

S5 執行契約消化完（各 `NN-<slice>.md` 進 `implement`/`tdd` 執行後），**執行本身可能揭露計劃斷言不成立**
——這半交棒 `loop-harness-standard` 的 [execution-feedback 模組](../loop-harness-standard/modules/execution-feedback.md)：
N-diverse-variant 執行（oracle-aware：dense=1 iterate／sparse-blind=N+判官）→ 判官逐斷言比對軌跡 → SURFACE
（改執行方式迴圈自主／plan-delta 人 admit）。**只指針不內嵌**——迴圈六步/verdict 格式/checker 機制的
SSOT 在該模組，本檔不重抄。

## Output Contract（Boundary Artifact）

計劃輸出落於 `docs/plans/<date>-<topic>/`：

```
docs/plans/<date>-<topic>/
├── 00-intent-and-knowhow.md   # SSOT：原始意圖 + 對話 know-how + why + S0 否定性評估
├── CONTEXT.md                  # 統一語言（canonical terms）
├── 01-<slice>.md ... NN-<slice>.md   # 分階段垂直切片計劃（子代理 full-detail，不簡化）
├── docs/decisions/<slug>.md    # 僅在決策記錄稀疏三條件全滿足時（非編號 ADR）
├── implementation-notes.md     # 【執行階段】滾動帳本（Deviations／裁決／證據指針）
├── implement/                  # 【執行階段】真實 repo 改動的 diff 鏡像（1:1 目錄結構，<path>.diff）
└── fold-in/                    # 【fold-in 階段】經驗 fold 回 SSOT 的 diff 鏡像（1:1 目錄結構）
```

> **執行/fold-in 階段產物約定（2026-07-11 fold-in 定；漂移安全）**——本 skill 只到「計劃寫好」為止，但計劃
> **執行後**（`implement`/`tdd` 消化各 slice）的真實 repo 改動須落計劃目錄，供精準追溯「本計劃在哪些真實
> 位置插入了什麼」：
> - **`implement/`** ＝ 1:1 鏡像 repo 目錄結構，每個被動到的真實位置放 `<repo-path>.diff`（該位置在**執行
>   階段** commit 範圍的累積 delta）。**用 diff 非全檔複製**——全檔複製＝第二份 SSOT＝正是 harness/fold-in
>   不變量 6 在防的雙圖漂移。
> - **`fold-in/`** ＝ 同形鏡像，放 fold-in commit 把經驗 fold 回既有 owner skill/module 的 diff。
> - 兩者皆 **歷史記錄非 SSOT**（SSOT＝真實 repo 檔；diff 凍結不漂）；**執行本身仍直接改真檔＋commit**，
>   `implement/` 是事後 diff 快照非執行前 staging。repo 外人域檔（如 hook）改動不入鏡像，於 slice patch-spec 記。
> - **完成判準**（2026-07-19）：`implement/`／`fold-in/` 亦為 oracle-aware 完成契約的證據面，各
>   `NN-<slice>.md` frontmatter 加 `oracle-tier: dense|sparse|blind`；完成判準與 trajectory 證據 →
>   `loop-harness-standard` harness-spec §5.1（指針，不重抄）。

## 整合接點（Wiring — 必為實接，非宣稱）

- **不經任何編排層**：antigravity 無 ENCD/skill-cycle 這類中介 dispatch。本 skill 只到「計劃寫好」為止；
  計劃寫完後直接交 `implement` / `tdd` 消化每個 `NN-<slice>.md` 的執行契約段。
- **與 `unknown-discovery-composer` 的邊界**：該 skill U1 出口在需求已收斂到「能寫計劃」後委派本
  skill（若任務多階段、需要 SDLC 級紀律）；需求單一或簡單則仍走 `to-prd`+`implement`。
- **與 `judge-loop-chooser` 的邊界**：本 skill S5 只委派，不重複其路由決策樹。

## S4 Experience Accumulation

每次調用後：若發現新的計劃反模式（如某階段委派的 atomic skill 不存在、垂直切片退化為水平分層），記錄
進本 repo 的 fold-in 帳本（`fold-in` skill 的 Resolved 累積機制），回饋 S2/S3 gate。

---

*port 自 northstar `sdlc-plan-composer` v0.1.0（2026-05-29 DEFINED-ONLY / 2026-06-25 WIRED+LIVE）。
antigravity 版無 skill-conformance-hub liveness/grounding 治理系統，故不帶 northstar 那套 YAML 治理欄位
——本檔以 `~/.agents/skills/` 現存符號連結 + 本 repo `.agents/skills/` 現存目錄作為委派目標真實性的鐵錨
（見 modules/retarget-map.md §4）。*
