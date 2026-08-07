---
name: unknown-discovery-composer
description: |
  未知發掘編排器 —— 把「地圖 ≠ 真實疆域」的落差（unknowns）按四象限（KK/KU/UK/UU）×三時段
  （實作前/中/後）路由到既有 skill（mattpocock 全局 skills + antigravity 本地 fork）。
  recipe-not-engine：只盤點未知 + 路由 + SURFACE，不執行被路由的 skill、不 auto-chain，
  每段路由結果由人 admit。實作前收斂到「能寫計劃」→ 交棒 `superpowers:writing-plans`
  （antigravity 無 northstar 的 `sdlc-plan-composer`，已誠實退化，見 retarget-map）；
  實作後人理解閘（quiz 全對才 merge）；產物判準 → DR/Path-B/覆蓋矩陣類交棒本地
  `judge-loop-chooser`，代碼類直接 `code-review`（judge-loop-chooser 本 repo 無 code-branch）。
  何時用：任務起點在霧裡——不知道該問什麼、品味類需求說不出標準、需求太模糊還不能寫計劃、
  或實作後 merge 前要出小測驗確認真懂了這次變更。
  （cc-20260705 更新：`sdlc-plan-composer` 已落地本地 fork，U1 多階段任務出口改指回它，
  不再退化到裸 `writing-plans`；見下方與 retarget-map。）
---

# Skill: unknown-discovery-composer — 未知發掘編排（地圖≠疆域 → 四象限×三時段路由）

> **Role**：任務起點在霧裡時，先把「我不知道什麼」盤點成四象限（KK/KU/UK/UU），按時段（實作前/中/後）
> 路由到對應的既有 skill。只**盤點 + 路由 + SURFACE**，不執行被路由的 skill、不 auto-chain 整條鏈、
> 不替人決定「哪個未知值得解」——每段路由結果人 admit 後才進下一段（recipe-not-engine）。
> **結構**：本檔 = U0-U3 路由決策表 + 不變量 + Gotchas；逐機制 retarget 帳本（northstar 有什麼被拿掉/換掉/
> 誠實留白）→ [modules/retarget-map.md](modules/retarget-map.md)。
> **SSOT**：路由目標的真實性以 `~/.claude/skills/`(mattpocock 全局符號連結) 與本 repo `.agents/skills/`
> 現存目錄為準——路由前先確認目標真在 disk，缺席就誠實標「不在」給替代，禁偽路由。
> **Lineage**：port 自 northstar `unknown-discovery-composer`（`.claude/skills/unknown-discovery-composer/skill.md`
> v0.1.1）。**（cc-20260705 更新）** 當時記錄為無基座的下游 Integrator `sdlc-plan-composer` 已落地本地
> fork（`.agents/skills/sdlc-plan-composer/`），U1 多階段任務出口已改指回它；
> `judge-loop-chooser`／`gemini-conversation-research`／`repo-agent-native` 三個下游交棒點 antigravity
> **已各自有本地 fork**，本 port 直接指向本地版（比 northstar 原版的跨 repo 引用更乾淨）。非原樣搬；
> 逐機制映射 → modules/retarget-map.md。

## 🚩 STOP — 你在合理化（違反即停）
| 念頭 | 現實 |
|---|---|
| 「U0→U3 一路做完再跟人講」 | ❌ 每段出口都要人 admit；auto-chain 整條 = 違 recipe-not-engine |
| 「這個未知隨便挑一格湊數」 | ❌ 四象限每格要嘛 ≥1 條真實條目、要嘛顯式 N/A；湊數 = 盤點品質造假 |
| 「單階段小需求也丟給 sdlc-plan-composer 走六階段」 | ❌ 本 skill 只路由不造 skill；`sdlc-plan-composer` 是多階段 SDLC 協議，單階段/需求已清楚仍走輕量 `superpowers:writing-plans`——別用重協議處理輕需求 |
| 「這是代碼產物，也丟 judge-loop-chooser 判」 | ❌ antigravity 版 judge-loop-chooser 明言無 code/sandbox 判決表基座；代碼產物直接 `code-review` |
| 「quiz 隨便出幾題應付」 | ❌ quiz 測人真懂與否，不是形式；出不出得了好題本身就是「你懂了沒」的訊號 |

## When to Use
任務起點在霧裡，你要先搞清楚「我不知道什麼」再動手：
- 陌生 codebase 區塊 / 全新領域，**不知道該問什麼**（unknown-unknowns）。
- 「我一看到就知道要不要，但寫不出標準」的品味類需求（unknown-knowns）。
- 需求太模糊，**還不能寫計劃**。
- 實作完成後，要確認**人**真的理解了這次變更（quiz/pitch 的人理解半）。

## Not For
- ❌ **需求已成形、可直接寫計劃**：多階段任務且要 SDLC 級紀律 → `sdlc-plan-composer`（antigravity 本地 fork，S-1..S5 序列委派）；單階段/需求已很清楚 → `superpowers:writing-plans`。
- ❌ **產物驗證標準/tier 選擇** → `judge-loop-chooser`（DR/Path-B/覆蓋矩陣類）或 `code-review`（代碼類）。
- ❌ **執行本體** → 直接 `implement` / `tdd`（antigravity 無 skill-cycle 這類編排層）。
- ❌ **純 mattpocock skill 導航（不帶未知象限視角）** → `ask-matt`（mattpocock repo 自帶的 router）。
- ❌ **auto-chain**：把 U0→U3 硬串成一條無人閘的管線 = 違 recipe-not-engine；每段出口人 admit。
- ❌ **重複委派**：同一意圖的 grill 不重複問（防雙稅精神，簡化版——antigravity 無 sdlc-plan-composer S1 可比對）。

## 不變量（違反即停）
1. **recipe-not-engine**：只盤點 + 路由 + SURFACE，不執行被路由的 skill。
2. **四象限非二元**：每格獨立判準，不可用「反正都要做」跳過分類。
3. **LAND-DECISION 永遠人**：哪個未知值得解、何時進下一段，人 admit。
4. **pivot 迴路合法**：U2 發現象限誤判可回 U0 重分類，這是紀律內建的修正，不是失敗。
5. **目標存在性**：路由前確認目標 skill 真在 disk（`~/.claude/skills/` 符號連結或本 repo `.agents/skills/`），缺席就誠實標「不在」給替代。

## Instructions（單一線性協議：U0 盤點 → 按時段路由 → 出口交棒）

### U0 — 未知四象限盤點（動手前 5 分鐘，寫進對話不寫檔）

**第 0 步——起跑點披露**：盤點任務的未知**之前**，先披露**人**的起跑點——目前思考進度、對問題與 codebase 的熟悉程度、期望引擎作為 thought-partner 的協作方式。並持具體度平衡：說得太具體 → 引擎盲從、該轉向時不轉；太模糊 → 引擎套行業 best-practice 假設、未必合身。未知盤點的品質上限由起跑點披露決定。

對當前任務問四格，每格 ≥1 條或顯式 N/A：

| 象限 | 判別問句 | 收斂手段（原則） |
|---|---|---|
| **KK** known knowns | 我能直接寫進 prompt 的 | 直接寫，不路由 |
| **KU** known unknowns | 我知道我還沒想透的 | 訪談/研究（問對問題就收斂） |
| **UK** unknown knowns | 我一看就認得、但寫不出來的（品味） | 原型/多方案（做出來給我看） |
| **UU** unknown unknowns | 我完全沒考慮過的 | 盲點審查（讓引擎替我掃疆域） |

### U1 — 實作前路由表（收斂到「能寫計劃」為止）

| 未知情境 | 路由 skill | 象限 |
|---|---|---|
| 陌生 code 區塊，要上一層抽象的地圖 | `zoom-out`（模組+callers 地圖） | UU |
| 全新領域要**學** | `teach`（stateful 教學工作區：MISSION/lessons/learning-records） | UU |
| 需要外部一手資料背景研究 | `research`（一般背景研究）；研究一個 Gemini 對話 或 post-cutoff 框架/能力 claim → `gemini-conversation-research`（**antigravity 本地 fork**，非跨 repo；External-Verify，禁訓練知識） | UU/KU |
| 想法太大、路線不明（一個 session 裝不下的霧） | `wayfinder`（investigation-ticket 共享地圖，逐票收斂到路線清晰） | UU 規模化 |
| 範疇還沒界定（怕定太窄/太寬）、要腦暴介入點 | `superpowers:brainstorming`（Claude Code 全局 plugin） | UU→KU |
| 意圖模糊要逼問清楚 | `grilling` / `grill-me`（一次一問+推薦答案）；要沉澱決策記錄/glossary → `grill-with-docs`（antigravity **無編號 ADR/DDR 系統**，產出為散文決策記錄，非 northstar 式編號 ADR）；workflow spec 專用 → `loop-me` | KU |
| 無法言語化但有現成範例可指（缺術語/太複雜） | **inline 紀律（無對應 skill，本 skill 補位）**：指認**參考源碼**——資料夾 / vendor 模組 / 喜歡的網站底層模組，告知「注意什麼」，跨語言亦可 | KU |
| 品味類：一看才知道好不好 | `prototype`（throwaway 原型答一個設計問題）；介面形狀 → `design-an-interface`（並行子代理產 ≥2 截然不同方案） | UK |
| 架構深化機會掃描 | `improve-codebase-architecture`（掃描 → HTML 報告 → 逐項 grill） | UU |
| 既有 repo 的真相（合約/隱含依賴） | 本地 `repo-agent-native`（源碼=SSOT，evidence-tagged；DR 禁當可讀 repo 主幹——漏斗倒置）；要 Opus 級理解散文而非 typed 不變量 → 正交的 `repo-wiki-converge` | KU |
| 要對文章/概念做**真相驗證**，或對某 config/引擎做 **token-efficiency 量測** | 先讀本地 `truth-verify-loop`（現成量測迴圈：t0 工具鏈＋合約＋播錯集方法可複用，換 domain 只重生 fixtures 四件套）——**別把「怎麼量」當 UU 重新發明**；該迴圈本身即經本 skill 從 UU 收斂誕生（2026-07-05），是「未知發掘的產物可以是 durable 迴圈」的實測錨 | KK（引擎已存在） |

**出口 gate**：四象限各格「已收斂或顯式接受殘留」→ 人 admit → 分流交棒：**多階段任務、需要 SDLC 級紀律**
（意圖對齊/垂直切片/介面深模組/TDD/交接皆要編進計劃）→ `sdlc-plan-composer`（antigravity 本地
fork，S-1..S5 序列委派，cc-20260705 已落地，取代先前退化到裸 writing-plans 的做法）；**單階段/需求已
很清楚** → 直接 `superpowers:writing-plans`（通用 spec→plan，不需六階段協議）。交棒時對計劃形狀帶兩條
要求：① **前置最易變決策**——資料模型/型別介面/UX flows 放計劃開頭供人微調，機械式重構沉底；② 計劃含
**遇未知可靈活應變**條款（引擎遇邊緣狀況的處置規則 = U2 迴路的鉤子），不是鎖死的步驟表。

### U2 — 實作中路由表（計劃趕不上疆域時）

| 情境 | 路由 |
|---|---|
| 邊緣狀況迫使偏離計劃 | **inline 紀律（無對應 skill，本 skill 補位）**：維護 `implementation-notes.md`，偏離記「Deviations」段（保守選項 + 記錄 + 繼續），收尾時回流 U3 |
| 發現「不知道好的標準」/ 未知指向換方法 | **回 U0 重分類（pivot 迴路）**——象限誤判的中途修正：以為 UK（做幾版來選）實為 UU（不知道「好」長什麼樣）→ prototype 轉 teach |
| 預註冊步驟的**資訊價值歸零**（前置量測已定方向，端點/加碼步只會更貴不會改結論） | **顯式棄跑（人核）**：判定落帳標 PARTIAL/SKIPPED＋棄跑理由，**不改判定式遷就**（Path B）——與象限誤判 pivot 不同，這是「疆域已答完計劃還沒走完」的中途修正。實測錨：truth-verify 三例（BS1 端點/3-majority 臂/H4），`truth-verify/hypotheses.md` 落帳段 |
| 偏離變成硬 bug | `diagnose` / `diagnosing-bugs`（reproduce→minimise→instrument） |
| context 滿了要跨 session 交棒 | `handoff` / `claude-handoff`（antigravity **無** northstar `fidelity-handoff` 的形態決策 + fidelity-lint 覆蓋閘，已誠實降級——見 modules/retarget-map.md；交棒前自行檢查有無漏 load-bearing negative） |

### U3 — 實作後路由表（合併前的人理解閘）

| 情境 | 路由 | 半邊歸屬 |
|---|---|---|
| 提案/解說（爭取 buy-in） | `to-prd`（對話→綜述發佈）；散文成型 → `writing-shape` / `edit-article` | 人理解半 |
| 小測驗（我真懂這次變更嗎） | inline quiz 紀律：要求引擎產含背景+直覺+變更說明的報告 + 底部 quiz，**全對才 merge**；`teach` 的 learning-record 形態可承接 | 人理解半 |
| 對話式回報遺留問題 | `qa`（輕澄清 → 背景 Explore → 檔 domain-language issue） | 人理解半 |
| 產物本身的判準/驗證 tier（DR 報告 / Path-B 精煉 / COMPLETENESS 覆蓋矩陣） | **交棒 `judge-loop-chooser`**（**antigravity 本地 fork**：三態 grounding + 四層獨立性 tier） | 產物判別半 |
| 產物本身的判準/驗證 tier（**代碼**） | **直接 `code-review`**（judge-loop-chooser 本地版明言「無 code-branch」，見其 modules/retarget-map.md） | 產物判別半 |

> quiz 測「人」的理解就緒度，judge-loop-chooser/code-review 測「產物」的判別力——同一個「別憑感覺 merge」閘的兩半，缺一都不完整。

## 與下游交棒點的邊界

- **`sdlc-plan-composer`**：U1 出口只做「未知是否收斂完了」的判斷；計劃怎麼寫、S-1..S5 怎麼切是它的事，
  本 skill 不重跑其否證素材/防雙稅/design-an-interface+決策記錄稀疏 gate 特化。多階段任務才交棒；
  單階段仍走 `superpowers:writing-plans`（本 skill 判斷交棒哪一個，不判斷計劃內容本身）。
- **`superpowers:writing-plans`**：單階段/需求已清楚時的輕量出口，不需六階段協議。
- **`judge-loop-chooser` / `code-review`**：U3 只判「該用哪個」，不做判決本身。
- 完整逐機制映射（含 `sdlc-plan-composer` 從誠實留白到落地的沿革）→ [modules/retarget-map.md](modules/retarget-map.md)。

---

*port 自 northstar `unknown-discovery-composer` v0.1.1（2026-07-04）。antigravity 版無 skill-conformance-hub
liveness/grounding 治理系統，故不帶 northstar 那套 YAML 治理欄位——本檔以 `~/.claude/skills/` 現存符號連結 +
本 repo `.agents/skills/` 現存目錄作為路由目標真實性的鐵錨（見 modules/retarget-map.md §4）。*
