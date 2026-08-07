---
name: truth-verify-loop
description: |
  真相驗證量測迴圈——對文章/概念/重大 claim 集跑「抽取 claims→分批多 tier worker 驗證→跨家族
  聚合→fresh 語意判官→純腳本計分→人類裁決與落帳」的閉環方法論。skill-bettor 已有本地實跑
  `loop_wiki/tv-dual-loop-context/`;該實例的程式、測試與 receipts 是執行證據 SSOT,本 Skill 只持有
  共通方法、路由規則與新題目實例化契約。agy/Codex 只提供 findings,不得取代獨立判官或 Human LAND。
  觸發詞:truth-verify、真相驗證迴圈、claims 逐字驗證、多 tier 事實查核、跨家族聚合驗證。
  NOT for:驗證標準/獨立性 tier 的選擇(judge-loop-chooser);單一外部 claim 查證不必開迴圈
  (external-verify);產品功能輸出或使用者服務足夠性驗收;skill 變現情報批次(dr-research-loop)。
---

# Skill: truth-verify-loop — 真相驗證量測迴圈

> **Role**:把「查詢真相」從單點查證升級為可量測閉環:claims 抽取→worker 驗證(多 tier+跨家族)→
> 聚合→判官→**純腳本計分 vs sealed 真值**→人類落帳。本檔只放共通程序與不可簡化不變量。
> **本地執行 SSOT**:`loop_wiki/tv-dual-loop-context/` 是已真跑的獨立 Git root;其程式、測試、
> input hash、worker/judge receipts 與 LAND decision 才能證明能力。先讀
> [modules/local-instance.md](modules/local-instance.md) 確認已實作範圍與紅燈。
> **歷史 Lineage**:方法論 2026-07-17 自 antigravity port;上游只保留為歷史 know-why 指針,
> 不得作為本地 runtime/evidence dependency。逐機制取捨見
> [modules/retarget-map.md](modules/retarget-map.md)。

## When to Use
- 一份文章/概念集/重大 proposal 的 claims 需要**可計分**的多 tier 驗證(不只 findings,要 vs sealed
  真值的檢出率),或同一驗證要跨家族(Claude×Gemini×GPT)聚合抗單模型盲區。
- 要複用/擴充這條量測迴圈:換題目(重生 claim inventory、正負控制與 sealed truth)、加 config 軸、
  開新 pin。
- 改它任一階段(合約/工具/判官 dispatch)前——先讀本檔不變量,防閉環被誤簡化。

## Not For
- ❌ 「這個 deliverable 該用什麼驗證標準/tier」→
  [judge-loop-chooser](../judge-loop-chooser/SKILL.md)
  (本迴圈是其語彙的一個實例)。
- ❌ 單點外部 claim 查證 →
  [external-verify](../external-verify/SKILL.md)
  (本迴圈 worker 內嵌其紀律;沒有量測需求就別開迴圈)。
- ❌ 約分/落帳誠實紀律的規範本體 →
  [path-b-reduction](../path-b-reduction/SKILL.md)
  (本迴圈全程執行它)。
- ❌ 驗收產品功能輸出、使用者旅程、SLO 或「服務是否足夠」——這些需要 requirement-bound
  acceptance scenarios、物理 E2E/負控制、runtime evidence 與人類 acceptance;truth verdict 不能代替。
- ❌ 原樣複製 antigravity 檔案進本 repo
  (其 `AGENTS.md` Resolved 指針/KB ingest 鐵律/實測數字=該 repo 自己的基座與證成,
  搬過來=死 husk;取捨帳見 retarget-map)。

## 階段拓撲

```mermaid
graph LR
  A[抽取 atomic claims] --> B[正負控制與反例]
  B --> C[跨家族 worker findings]
  C --> D[blind aggregation]
  D --> E[fresh 語意判官]
  E --> F[純腳本計分]
  F --> G[Human amendment / LAND]
```

1. 抽取(T0 schema 閘)
2. 切批(type 過濾)
3. worker 驗證(多 tier;四值 claim 標籤 SUPPORTED/REFUTED/UNVERIFIABLE/…——
   **per-claim 機械可聚合輸出,非裁決**,裁決權仍受判官地板約束;+逐字引文)
4. 跨家族側(agy/Codex,只 findings)
5. 聚合(TYPE_C 跨家族必開)
6. 判官(fresh Opus,僅限定裁決範圍,step-0 T0)
7. bounce(T0 退件兩敗升 tier)
8. fold+終驗(最終 T0 必 PASS)
9. 計分(純腳本 vs `fixtures/_sealed/`)
10. 計量
11. 落帳。

## 本地使用與新題目契約

1. 使用既有實例時,先在其獨立 Git root 執行 `sh verify.sh --fast`;不得以本 Skill 的敘述代替 exit code。
2. 只在 claim input、claims inventory、worker/judge receipts 與 ledger SHA 全部相符時復用結論。
   新題目或 source drift 必須建立新 input/claims/receipts,不得沿用舊 verdict。
3. 新建 `tv-<topic>` 時可用本 repo `loop_wiki/_template/` 起手,但只移植
   `tv-dual-loop-context/` 已審計且物理比較過的必要機制;不得直接讀取或複製 antigravity runtime。
4. 每個新實例先落 atomic claims、正負控制、盲性拓撲、判定式與安全閘,再允許外部 worker call。
5. agy/Codex worker 必須隔離、可判活、輸出 schema-validated artifact;模型名稱以 runner/receipt 為準,
   不信模型自報。外部 call 每個新 input 重新取得安全批准。
6. 判官保持 fresh、blind、tools-disabled 與無 session persistence;agy/Codex 永不當 final verdict。
7. 先通過機械 gate、獨立判官與人類 amendment/LAND,才可 promote 指定且 hash-bound 的 artifact。
8. 若目標是 production repo 或 AI Agent,另建 outcome-validation/admission 線;本迴圈只驗技術 claims。

## 不變量(承上游 7 條,retarget 後;改任一階段時不准被簡化)
1. **同 pin 唯一變因**:假設檢定只認同 pin A/B;mid-run 禁改工具/合約/dispatch 措辭。
2. **盲性拓撲**:編排者與判官永不讀 `_sealed/`+`mut-config/`;計分=純腳本;判官另禁 mutated 原檔。
3. **質量閘不可簡化**:false-SUPPORTED=0 硬條件;共識盲區/棄權盲區只有播錯集看得見——播錯集不可拿掉。
4. **判官紀律**:fresh context、下限 Opus、永不 agy/codex;僅限定裁決範圍;改裁必 re-pass 同管線 T0。
   worker(含 agy/codex 家族)的四值標籤=**資料非裁決**——與 §5「只 findings 不 verdict」不衝突,
   裁決只發生在判官段與人(2026-07-17 codex 跨家族審計指出的措辭撞名,特此定界)。
5. **成本全額入帳**:壞包/棄用/救援成本入量測;跨密度禁直比。
6. **量測產物不入 `families/`**(隔離紀律同 proposals/:未經 eval 閘的東西不是資產)。
7. **agy=Gemini only 且唯讀**;silent no-op 判活看輸出檔;它的 token 記副軸不入主成本。

## Gotchas
- **WebFetch 是二手**:逐字驗證一律 raw fetch
  (上游 T0 內建 curl+HTMLParser);
  弱模型會把 fetch 摘要當原文(external-verify 同課)。
- **U+2019 直撇號**:worker 引文含直撇號→T0 假陰性;
  bounce 紀律=無撇號片段優先/text_quote 照抄。
- **模型自報不可信**(本地新增,2026-07-17 codex proof run 實測):
  worker/判官宣稱的自身 model 不作數,
  判實跑 model 看 driver session log(codex=`~/.codex/sessions/`)。
- **persona 注入**:tv 的 worker/判官若走 Task 子代理,
  受 ponytail SubagentStart 注入影響——
  判官型必須落在 `PONYTAIL_SUBAGENT_MATCHER` 之外
  (judge-loop-chooser 操作判準第 5 條)。
- **上游漂移**:本檔指針指向 antigravity 活 repo,
  其模組化/搬檔會使歷史 know-why 路徑過期;不得讓這種漂移阻斷本地 instance。

## Modules
- [modules/local-instance.md](modules/local-instance.md)
  — `tv-dual-loop-context` 實際完成、未完成、物理 probes 與 admission 邊界;執行或宣稱能力前必讀。
- [modules/retarget-map.md](modules/retarget-map.md)
  — antigravity → skill-bettor 逐機制取捨帳
  (搬了什麼/不搬什麼+why/本地新增)。
- 歷史上游 know-why(六 run 實測課/E 主成分/tier 三明治/兩結構洞)=
  `/Users/neon/antigravity/.agents/skills/truth-verify-loop/modules/measurement-methodology.md`
  (指針不抄;那是上游的證成軌跡)。
