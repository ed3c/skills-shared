# Module: 技術選型 fit-to-plan 匹配度 recipe（第 4 deliverable 型的 know-why）

> 屬 [`judge-loop-chooser`](../SKILL.md) §確定性程序 step 1 的第 4 deliverable 型。SKILL.md 有路由一行;本檔 = 5 軸 rubric 的 know-why + 切入點判準 + 4 技能路由 + ≥95 認證。
> **反-husk 錨（方法論 fold,§retarget 反身版）**：本 recipe 指向的都是**真基座**——4 個真 skill（[repo-wiki-converge](../../repo-wiki-converge/SKILL.md) / [external-verify](../../external-verify/SKILL.md) / [dr-research-loop](../../dr-research-loop/SKILL.md) / [gemini-conversation-research](../../gemini-conversation-research/SKILL.md)）+ worked-example `docs/plans/2026-07-04-ds-workflow-oss-stack/FIT-JUDGMENT-FRAMEWORK.md`。**別指向不存在的基座。**

## 何時用此型

要判「一個 OSS 堆疊/repo 選型**對計劃目標 + 生產環境的匹配度**」（如：選定的 8-10 個 DS 工作流 repo 是否配得上計劃，達某分數）。**不是** repo 理解品質（那是 repo-wiki-converge 的 ≥90 wiki 分）——**匹配度是另一條軸**：`repo 真實能力（repo-wiki-converge 供）× 計劃需求（plan 供）→ 對 rubric 打分`。混淆這兩軸 = 燒錯方向的判官/DR cycles（命門）。

## 切入點（load-bearing 判準）：匹配度不在表面指標，在「每維度底層原理真相」

star 數/下載量不是匹配度。匹配度的切入點 = **每個維度的 DS（或該領域）底層原理真相，選定 repo 是否尊重它、且它與市場實作的差異是否被那條真相正當化（非任意）**。逐維度先寫出「第一性錨」（該維度不可作弊的鐵律），再問選型對它的立場。worked-example 的逐維度錨（point-in-time 防 leakage / metric 單一真相 > 裸 SQL / 不可信生成碼=外洩威脅面 / 部分失敗可重現 …）見 `FIT-JUDGMENT-FRAMEWORK.md §1`——那是 DS 專屬內容,**不搬進本 skill**（本 module 只定「切入點=底層原理真相」這個可重用判準,內容留專案）。

## 5 軸 rubric（per repo,三態 grounding,人出閘）

| 軸 | 判什麼 | grounding 錨 | 獨立性 tier |
|----|--------|-------------|-------------|
| **A 能力** | repo **真實**能力（源碼非行銷）覆蓋計劃該角色需求 | repo-wiki-converge 源碼理解 + 測試綠 | T2（Gemini 作者 × Opus 判官,跨家族） |
| **B 約束** | 授權 permissive ∧ 全本地 ∧ **生產就緒度**（alpha/proof-of-life 此軸扣分）∧ 維護 | external-verify 一手源 | T2 |
| **C 架構** | 與計劃合約/其餘堆疊無阻抗（真實 API 限制改了誰） | 計劃切片 + 合約（封裝包可重現） | T1 零存取 |
| **D 第一性** | 是否尊重該維度底層原理真相 | 底層原理錨 + 領域知識 | **needs_diamond → T3 人**（原理選擇=negative-space） |
| **E 市場-gap** | 與市場實作差異是否被真相正當化 | 架構辯論（gcr Mode B） | T2/T3 |

**分數判準（Opus 認證,必要非充分,借 [repo-wiki-converge](../../repo-wiki-converge/SKILL.md) ≥90 protocol）**：5 軸皆達標 ∧ 零事實錯 ∧ D 軸無「未被原理正當化的選擇」∧ E 軸 gap 皆有 justification;到標後跑 ≥90 protocol（meta-審計「沒查什麼」+ 對抗式再破 + 認證過獨立性 tier）。任一冒缺陷 → 續迴圈。**D/E 軸不可約人**（原理與計劃意圖是人的 LAND-DECISION）。**分數是給人的證據,非放行令**（recipe-not-engine,同 SKILL 不變量 1）。

## 4 技能路由（誰餵哪條軸；序列跑,一帳號約束）

| 技能 | 餵軸 | 條件 |
|------|------|------|
| [repo-wiki-converge](../../repo-wiki-converge/SKILL.md) | A 能力 + C 架構（源碼 ground-truth） | 每 repo Opus 級理解 wiki |
| [external-verify](../../external-verify/SKILL.md) | B 約束（授權/本地/維護一手源） | 常態 |
| [dr-research-loop](../../dr-research-loop/SKILL.md) | D 第一性 | **僅** DS/領域理解不足時（補隱式知識） |
| [gemini-conversation-research](../../gemini-conversation-research/SKILL.md) Mode B | E 市場-gap | **僅** 市場-vs-計劃 gap 理解不足時（多輪 QA 架構辯論） |

> **Same-Weights 注意**：A 軸走 Gemini 作者 × Opus 判官（跨家族,對）;E 軸 gcr Mode B 是 Gemini QA——堆疊為 OSS 時 Google-bias 低,但架構辯論結論仍須 Opus/跨家族裁（別 Gemini 審 Gemini 定案）。
> **一帳號序列**：repo-wiki-converge/dr-loop/gcr 全搶同一 Gemini :9333 → 序列跑、脫鉤才投下一個（跑前 `pgrep -fl automate.js`）。
> **範圍紀律**：別 N repo 盲跑;先跑風險/新/承重的（alpha / 剛換入 / 逆向腿脆弱 / 改了架構的）。成熟穩的 B 軸 external-verify 過即可抽驗。

## worked-example 教訓（2026-07-04 DS 堆疊選型跑,可重用判準）

> 只收**可重用 meta-pattern**;DS 專屬內容留專案（同上節範圍紀律）,下列 repo 僅作指向真檔的例示。

1. **計劃自陳的風險軸常錨錯 → B/D 軸必獨立重錨在源碼真相,別照抄計劃**（load-bearing）:
   - OpenShell:計劃寫「alpha 不可行」→ 源碼真相=真成本是**運維重量**(gateway 部署),alpha 本身非否決點;D 軸因它形式化 policy 能力反而最強。
   - MetricFlow:計劃關切「server-less?」→ 源碼真相=真風險是**綁 dbt**(要 metric `label` + DAY time-spine),非 server 模式。
   - notebooklm-py:計劃寫「逆向脆弱」→ 源碼真相=真成本是**資料主權**(送 Google);逆向脆弱可收斂、主權違反不可逆。
   - 鐵律:計劃文檔的自我風險診斷 = **待驗假設非事實**。B(生產就緒)/D(第一性)軸先獨立重錨源碼,對不上以源碼為準並 SURFACE「計劃錨錯哪條」。照抄計劃自陳風險 = 燒錯判官/DR cycles（同 §切入點命門）。

2. **running-code 印證 = 高於 wiki/judge 的證據級,fit 分只是選型前預測**:真落地 build 時,預測會被 running code 印證或反駁。有後續 build 時**把印證回填 fit artifact 並標「預測 vs 已印證」**,已印證軸升最高信心;預測翻車則回大迴圈人閘重議選型。（例:MetricFlow「dbt 耦合=真整合成本」被真 dbt build 印證——config 未含 `label`+time-spine、補後才通。）

3. **D/E 軸結論翻計劃寫定預設 → 跨家族辯論從建議升硬要求**（§Same-Weights 落地機制）:單模型心證不足以翻計劃。例:D4 預設 adapter 翻轉(notebooklm-py→LlamaIndex,主權)走 Opus×真 Gemini 跨家族辯論 2 輪 + Opus 裁落地,非我單方定案。

> 錨（皆真檔）:`docs/plans/2026-07-04-ds-workflow-oss-stack/FIT-JUDGMENT-FRAMEWORK.md §1`(逐維度第一性)、同目錄 `CONTEXT.md` D4/C1(翻轉落地)、`gemini_research/c1-default-debate.md`(跨家族辯論記錄)。running-code 印證留 product repo `/Users/neon/ds-workflow` + memory `ds-stack-risk4-fit-outcomes`（**產品經驗不進 skill**——選型方法論才進,產品堆疊留 CONTEXT.md/memory）。

## 為何是 judge-loop-chooser 的型,不是新 skill

匹配度判斷 = 把一個可判 deliverable（選型 fit-to-plan）路由到驗證標準 + 獨立性 tier + SURFACE 給人——**逐字就是 judge-loop-chooser 的定義**。只是 deliverable 型從「DR報告/覆蓋矩陣/Path B」擴一個「選型 fit」。故 fold 進既有 chooser（+ 本 module）,非造新 skill（anti-inflation）。
