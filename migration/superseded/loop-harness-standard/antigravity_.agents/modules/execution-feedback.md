# Module: execution-feedback — 執行反哺迴圈（N-diverse-variant → 判官挑最佳 + 飄移偵測 → SURFACE）

> 屬 [`loop-harness-standard`](../SKILL.md)（D12 引擎家族的一員，掛既有 skill 的 module，非獨立 skill——
> `anti-inflation-is-discriminator` 記憶）。**一句話**：執行 N 個版本 → Opus 判官挑最佳＋逐斷言比對軌跡
> 偵測隱式飄移 → SURFACE 二分流：改執行方式（迴圈自主）或改計劃（人 admit plan-delta）。
> **來源**：`docs/plans/2026-07-19-composer-integration-oracle-completion/02-execution-feedback-loop.md`
> （THE 規格，S3 選型與各節設計）＋ `05-integration-and-judge-findings.md`（B-1/B-2/B-3 綁定解）；統一語言
> 承其 `CONTEXT.md`。本檔只落地不重抄——設計理由/權衡分析回原計劃檔查，此處只留執行時要遵守的規則與機制。

## 定位（承 `harness-spec.md` §9❶ 三類編排 skill）
本模組是「路由型＋機械層」的混合：SURFACE 分流本體不執行被路由的動作（同 `unknown-discovery-composer`
不變量 1），但飄移偵測的**查證半**有真機械 checker（下方 §3），不是純心證路由。

## 0. 鐵律（違反即停，承 02 §0.2，不擅自降級）
1. **迴圈不可自動改計劃**——改計劃前提＝人 admit plan-delta（recipe-not-engine）；只「改執行方式」可
   迴圈自主。與 `harness-spec.md` §9❶「LAND-DECISION／畢業判／merge 永遠人」同類條款。
2. **N 隨 oracle**：dense（有 T0）→ N=1，`harness-spec.md` §5.1 iterate-until-T0-green 本身就是挑選器，
   多版是浪費；sparse/blind → N 版（默認 3）+ 判官挑。
3. **N 版必真多樣**：不同 approach（MVP-first／risk-first／既有慣例-first）或跨家族（codex/agy/claude -p），
   **禁同 prompt 同家族重複 N 次**（NV=2≈0 實測）。
4. **並行必 worktree 隔離**：N 版同時寫同一 repo 檔會互撞；判官挑完唯一勝者才落主 tree（原生 `EnterWorktree`，
   禁自製 `.session-worktrees/`）。
5. **飄移偵測＝確定機制、非心證**：判官逐條比對「計劃 load-bearing 斷言」×「執行軌跡事實」，證不了或被
   證偽＝飄移候選，非「應該沒問題」的印象打分。

## 1. 資料面：斷言表 schema（B-1 統一，SSOT owner = 01）
```
| id | 斷言(load-bearing 假設) | expected-observation(該在軌跡看到什麼) | 對軌跡勾稽方式(grep/檔/exit) | verdict(HELD/REFUTED/UNOBSERVED) |
```
schema 定義權在 `01-oracle-aware-completion-contract.md`（pre-register 時必產 `expected-observation` 欄）；
本模組**只消費**，不重定義。N 版執行軌跡＝`_engine-run/variant-<A|B|C>/driver.iterN.json` + 該 worktree
內實測輸出；每版另附 `variant-<X>/APPROACH.md`（≤10 行，含 `approach:`／`family:` 兩欄，判官讀這個定位，
不通讀全軌跡）。

## 2. 邏輯面：六步
```
① oracle-gate 定 N（dense=1 / sparse·blind=N，默認 N=3）
② dispatch N 版（§4 派工：codex×worktree×diverse approach；跨家族可換 agy/claude -p）
③ 收攏軌跡（variant-X/driver.iterN.json + 實測輸出 + APPROACH.md）
④ Opus judge：挑最佳（按 01 完成契約判準）＋逐斷言勾稽（HELD/REFUTED/UNOBSERVED，每條必附軌跡引用）
⑤ SURFACE 分流：
   - 全 HELD + 有勝者 → 勝者落主 tree，迴圈結束，交 01 完成契約
   - REFUTED/UNOBSERVED 標「改執行」→ 迴圈自主換 approach/家族重跑（回②）；
     stop-loss：同一斷言 2 輪重跑仍非 HELD → 升格 plan-delta 候選交人（先驗值，未跑過 3 個真計劃前不調）
   - 有 plan-delta 候選 → STOP，SURFACE 交人 admit；人裁後改計劃 → 斷言表更新 → 重入①
⑥ 人 admit 後收尾：勝者 merge（人閘）、durable 課走 01 條件 fold-in
```

## 3. 輸出面：judge-verdict 三段格式
`<plan-dir>/judge-verdict-<date>.md`：
1. **挑選**：勝者 variant + 每版 3-5 行比較（依 01 完成判準打分，非自由心證）。
2. **勾稽表**：assertions 表逐條 verdict——`HELD`（軌跡證實，附引用）／`REFUTED`（軌跡證偽，附
   file:line 或軌跡行號）／`UNOBSERVED`（無版本產生觀測——本身即警訊）。
3. **SURFACE 分流**：REFUTED/UNOBSERVED 逐條標「改執行」或「plan-delta 候選」，後者**只列提議+證據，
   不改任何計劃檔**。

## 4. 機械 checker（§0 條款 1/5 的落地兜底，非只點名）
心證放水與隱形 plan-delta 是本迴圈最大風險（02 §6）；四個 checker 是查證半的機械層，位於
[`scripts/execution-feedback/`](../scripts/execution-feedback/)，good/hollow fixtures 成對驗證
（`scripts/execution-feedback/fixtures/{good,hollow}/`，anti-placebo：跑
[`verify.sh`](../scripts/execution-feedback/verify.sh) 自證 good=PASS ∧ hollow=FAIL）：

| # | checker | 擋什麼（hollow 場景） | 用法 |
|---|---|---|---|
| 1 | `held-reference-check.sh <judge-verdict.md>` | h2：判官某條填 HELD 但無軌跡引用（心證放水） | 每個 `HELD` 表格行必含 `variant-*/iter*` token，缺席 FAIL |
| 2 | `plan-dir-diff-check.sh <plan-dir>` | h1：迴圈/判官直接改了計劃檔（自動改計劃前提） | 人 admit 前 `git status --porcelain <plan-dir>` 必為空，非空 FAIL |
| 3 | `approach-diversity-check.sh <APPROACH.md...>` | h3：N 版假多樣（同 prompt 同家族） | 各 `variant-X/APPROACH.md` 的 `approach\|family` 簽章需兩兩相異，同值 FAIL，dispatch 前擋 |
| 4 | `no-smuggled-plan-delta-check.sh <prompt> <verdict> <assertions>` | **B-2**：重跑 prompt 隱形夾帶「上輪所學」實質是計劃前提修訂（繞過人閘的隱形 plan-delta） | prompt 只許逐字引 verdict 的「改執行」行；引到任何「plan-delta 候選」行或 assertions.md 斷言文字 = FAIL（機械 grep 白名單），與 checker 2 互為兜底 |

checker 2／4 兩層防「隱形改計劃」：4 攔**dispatch 前**的 prompt provenance（意圖層），2 攔**執行後**的
結果（計劃檔實際被動過）——單靠自律的殘留風險由 2 兜底。checker 4 是樸素子字串比對（ponytail：上限＝
長句改寫/同義替換可能漏抓，升級路徑＝用 B-1 統一 schema 的 `id` 欄取代文字比對，見腳本內註解）。

## 5. 派工（承 02 §3，人工三選一，非自動觸發）
N 版執行：`codex exec` 主，跨家族多樣時第二三版可換 `agy`/`claude -p`；每版獨立 worktree、codex 必
`< /dev/null`（repo 鐵律）、agy 版先查額度（判活看輸出檔非 exit code，`agy-quota-silent-noop` 記憶）。
判官：Opus fresh session（`judge-loop-chooser` 獨立性 tier；永不用 agy 當判官；判官無計劃目錄寫權——
checker 2 的機械前提）。plan-delta admit／勝者 merge／完成 admit：人，不可委派。

## 6. 介接點（本模組定義形狀；實際接線文字落哪個 slice 見下）
- **sdlc-plan-composer 執行後**：S5 執行契約完成＝本迴圈入口，sdlc 側只需一條「S6′ 執行反哺」指針
  指回本模組，不內嵌迴圈機械。
- **unknown-discovery-composer U2**：「執行揭露計劃斷言不成立」的偏離，走本模組勾稽表確認飄移／誤讀，
  飄移→ plan-delta 人閘（非目前 U2 裸 Deviations 紀律，那條留給非斷言級小偏離）。
- **unknown-discovery-composer U3**：judge-verdict 勾稽表即 U3 quiz 素材的一種——人 review「哪些斷言被
  執行推翻」比 quiz 更硬。

## 7. 完成判準（不重造）
本模組不另立完成判準——迴圈①的入口 tier 判定與⑥的收尾，消費 `harness-spec.md` §5.1 oracle-gate／
dense-sparse-blind（01 契約，SSOT owner=01，本檔不重述）。
