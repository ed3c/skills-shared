# Module: loop-harness-review-handoff — Layer B know-why

> 屬 [`loop-harness-review-handoff`](../SKILL.md) skill。SKILL.md ＝ 6 步確定性程序＋不變量;本檔 ＝ 為何這樣設計。
> worked instance ＝ [`REVIEW-HANDOFF-fable5.md`](../../../../docs/plans/2026-07-10-d2-evidence-pair-evals/REVIEW-HANDOFF-fable5.md);骨架 ＝ [reference/handoff-template.md](../reference/handoff-template.md)。

## 1. 為何 fresh-session＝評審隔離（零上下文獨立，同家族亦成立）

交接的核心目的是**獨立審計**——reviewer 不能是「建這套東西的同一個 context」,否則它會替自己的決策辯護（sycophancy 的結構版）。獨立性的技術實現有兩個層次：

- **跨家族天然隔離**：Opus 審 Gemini 產物（或反之）——不同模型家族,無共享 context、無共同訓練近似偏見,獨立性白吃。這與 harness 的「驗證器與執行者隔離」同源（[`loop-harness-standard` 鐵律 3](../../loop-harness-standard/SKILL.md)、[`harness-spec §1❶`](../../loop-harness-standard/modules/harness-spec.md)）。
- **同家族靠 fresh-session 達獨立**：Opus 審 Opus 建的東西、或 Fable 審另一 Fable session 的產物時,**新 session 的零上下文**就是隔離手段——它看不到建置過程的 rationalization、只看 curate 給它的入口與真檔。**關鍵：必須是 fresh session,不能是 fork**。fork 帶著母 session 的完整上下文＝把「要被獨立審的思路」原封搬進 reviewer＝獨立性歸零。這正是 harness 側「同家族（Claude×Claude）必落地 fresh zero-context subagent（**禁 fork**）」的評審交接鏡像（[`loop-architecture-ssot §2.4`](../../loop-harness-standard/modules/loop-architecture-ssot.md)「嚴禁 Same-Context 自我審查」、[§8❸ fresh-context 子代理律](../../loop-harness-standard/modules/loop-architecture-ssot.md)）。

**推論**：交接提示詞必須設計成**零上下文自足**——因為 fresh session 沒有任何背景,提示詞本身要 curate 足夠入口 + 明訂紀律,否則 reviewer 要嘛淹死在整個 repo（違反不變量 4）、要嘛憑空瞎猜（無錨散文）。

## 2. reviewer tier 選型 rationale

| reviewer | 適用 | 為何 | 錨 |
|---|---|---|---|
| **Fable 5** | 設計/高推理架構評審（效益疊加審計、逼出未想到的優化、廣角架構問題） | 高推理 tier 才抓得到跨基座的疊加 vs 冗餘、才逼得出「哪維度沒被審」的 completeness gap;低 tier 抓不到隱蔽 Goodhart/結構性冗餘 | worked instance 選 Fable 5;tier 匹配推理需求 |
| **Opus** | 裁決型（判 HOLD/PASS、對 finding 下定論、當畢業 semantic 判官） | Opus-tier 隔離判官抓得到機械層＋author 皆未抓的 Goodhart（D2 金絲雀反轉逮「判定真空」為活證——引擎綠但反轉仍綠＝真空,唯高推理審計會逼問） | [`loop-harness-standard` 鐵律 3](../../loop-harness-standard/SKILL.md)＋D2 pilot 金絲雀 `canary.py` |
| **agy 不當判官** | ——（排除） | agy ＝ Gemini only;判官/裁決角色永遠用主 session 的 Opus,別在 agy 指定 Claude 模型。agy 是**小迴圈 driver/author** 角色,不是評審角色 | [`antigravity-harness-wiki` 不變量 5](../../antigravity-harness-wiki/SKILL.md)「判官永遠 session 內 Opus」 |

**tier 匹配推理需求的通則**（借 harness 側）：Opus 做純機械＝浪費、低 tier 裁決＝抓不到 Goodhart。交接評審屬**高推理**任務（架構疊加分析＋逼未知）→ Fable 5 或 Opus,不下放低 tier。

## 3. anti-sycophancy 與 anchored-claims 為何（Path B 紀律）

交接評審最大的失敗模式**不是**「reviewer 找不到問題」,而是「reviewer 回一堆平滑的、聽起來對但站不住的敘事」——「這個設計很優雅」「效率提升明顯」「架構清晰」。這些是 sycophancy 的變體：**表演式同意 + 未錨斷言**。兩條紀律對治：

- **anti-sycophancy**（人的交互契約直接搬進交接提示詞）：不附和、不表演式同意、技術上站不住就反對、對「疊床架屋/儀式性/冗餘」直說該砍。reviewer 的價值在**點破**,附和的 reviewer ＝ 零信息。
- **anchored-claims（Path B）**：每個 claim 必須約分到**確定性鐵錨**——檔案:行、exit code、實測數字、官方 primary source。無錨的平滑敘事標為**未錨**、不可宣稱成立。這是 fold-in「無鐵錨的效率提升＝Half-Bridge 散文」的評審版：一個「更好」若不能落到「D2 金絲雀反轉 eval-04 令 run 轉紅、退出碼變 1」這種真事件,它就是散文。

**為何強制 read-only grounding**：交接提示詞授權 reviewer 跑 `run_loop.sh`／金絲雀 `canary.py`／`evidence_eval.py --evidence-dir …`／`git show`——不是禮貌,是**逼 claim 落地**。reviewer 能自己驗的,就不該憑印象斷。這也讓 reviewer 的獨立性有牙齒（自己 ground、不靠建置者餵結論）。

## 4. session-adjustment（差量交接方法）

交接不是每次都從零重審全量——那既浪費高 tier reviewer 的推理預算,又讓 findings 稀釋。**差量交接**：

1. **鎖定已變動 slice**：自上次交接以來,哪些基座/決策/checker 真的動了（`git log --oneline` 圈範圍;如 D2 的 01 tracer→02 全儀器化→03 UU 閘→04 去重四切片）。
2. **標記已答維度**：上次交接已被 reviewer 充分審過、且結論仍成立的維度（[audit-dimensions](audit-dimensions.md) 的某幾項）標為「已答,除非相關 slice 變動否則略過」。
3. **本次重點 ＝ 已變動 ∪ 未答維度**：把 reviewer 的注意力集中在增量 + 從未被審的維度,而非重刷全表。
4. **reviewer tier 隨重點調**：純裁決一個 finding → Opus;廣角逼一批未想到的優化 → Fable 5。

**為何**：高 tier reviewer 的邊際價值在**新增/未審**表面,不在複述上次結論;差量交接把有限的高推理預算投在真正的增量前沿。這與 unknown-discovery 的「已知略過、逼未知」同構,但作用在**交接的 scoping** 而非發掘本身。

## Sources / 錨
- worked instance：`docs/plans/2026-07-10-d2-evidence-pair-evals/REVIEW-HANDOFF-fable5.md`（本方法論的一個實例）。
- 設計 SSOT：`.agents/skills/loop-harness-standard/{SKILL.md,modules/harness-spec.md,modules/loop-architecture-ssot.md}`＋`.agents/skills/antigravity-harness-wiki/SKILL.md`。
- 隔離/tier/Goodhart 活證：D2 證據系統 `loop_wiki/subproject-ixsecurity-e2e/d2_e2e_loop/`（金絲雀反轉紅測 `canary.py`、四格矩陣 SILENT-DEGRADATION、UU 掃描 triage 閘）＋方法論 [`e2e-evidence-pairing-methodology §9`](../../subproject-ixsecurity-e2e/modules/e2e-evidence-pairing-methodology.md)。
- agy 角色邊界：[`antigravity-harness-wiki` 不變量 5](../../antigravity-harness-wiki/SKILL.md)。
