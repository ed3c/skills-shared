---
name: truth-verify-loop
description: |
  真相驗證量測迴圈(truth-verify)的全景圖——「資料流歸屬＋迴圈判斷邏輯＋全部原始提示詞」
  的單一真相來源(SSOT 指針表,只指針不抄)。何時用：要對文章/概念跑多 tier 子代理真相驗證、
  要複用或擴充這條量測迴圈(新文章/新 config 軸/新 pin)、或改動它任一階段 skill/合約/工具前
  先讀本圖防止把閉環架構或提示詞誤改/誤簡化。引擎＝truth-verify/t0/ 工具鏈＋contracts/ 合約;
  帳本＝loop-ledger.md＋hypotheses.md。六 run 實測課(E 主成分/tier 三明治/兩結構洞)在
  modules/measurement-methodology.md。
---

# Skill: truth-verify-loop — 真相驗證量測迴圈全景圖(SSOT 指針)

> **Role**: 這條迴圈的防誤改地圖。任何人(含未來的你)改它的階段/合約/工具/慣例前,先對照本圖的組件卡+不變量——**本檔只指針,永不抄內容**(抄=製造會漂的第二份,husk 之源)。
> **引擎 SSOT**: `truth-verify/t0/*.{sh,py}`(機械閘+計分+聚合+計量)· `truth-verify/contracts/`(standing 合約)· `truth-verify/contracts/dispatch/`(實跑 dispatch 逐字模板)。
> **帳本 SSOT**: `truth-verify/hypotheses.md`(pre-registered 判定式+落帳)· `truth-verify/loop-ledger.md`(run 帳+per-hypothesis 判定+holdout)· `docs/plans/2026-07-05-truth-verify-loop/`(計劃+EXECUTION-TIERING 建造帳)。
> **Lineage**: 收斂原語承 kb-ingest judge-loop(T0 左移/判官只裁機械檢不了的/≥90 精神),播錯集=reverse-mutant eval 的量測等價;完整技術等價物映射 → [modules/measurement-methodology.md](modules/measurement-methodology.md)。誕生路徑=經 [unknown-discovery-composer](../unknown-discovery-composer/SKILL.md) 全程編排(U0 四象限→U1 交棒計劃→U2 三次顯式棄跑→U3 quiz+交棒,2026-07-05/06)——**換 domain 移植而範疇/播錯集設計仍在霧裡時,回它做 U0 盤點**;迴圈已成形的複用不需回。

## When to Use
- 對 session 內文章/概念跑多 tier(Fable 編排+Opus/Sonnet/agy-Gemini)真相驗證。
- 要複用這套量測迴圈:換文章(重生 fixtures/mut-config/sealed ledger)、加 config 軸、開新 pin。
- **改任何階段前**(合約/工具/慣例/判官 dispatch)——先讀組件卡+不變量,確認不打破閉環。

## Not For
- ❌ 驗證標準/獨立性 tier 的**選擇** → `judge-loop-chooser`(本迴圈是它語彙的一個實例)。
- ❌ 外部 claim 單點查證 → `external-verify`(本迴圈的 TYPE_A worker 內嵌其紀律)。
- ❌ 約分/落帳誠實紀律的規範 → `path-b-reduction`(本迴圈全程執行它)。

## 組件卡(階段:in → artifact → out · 閘 · SSOT)
| 階段 | in → artifact → out | 閘 | SSOT |
|---|---|---|---|
| 抽取 | mutated article → `runs/<id>/<sr>/claims.jsonl` | **T0 --claims**(schema/type/逐字性,FAIL 整份退回) | 合約 `contracts/tv-extract.prompt.md`;dispatch `contracts/dispatch/tv-extract.dispatch.md`;閘 `t0/tv-preverify.sh` |
| 切批 | claims → `batches/b-ad.jsonl`(A+D)/`b-c.jsonl`(C)/`b-b`(B 若有) | type 過濾(機械) | 編排行內(type→批映射) |
| worker 驗證 | 批+article → `cl-<tier>-*.jsonl` shard | 四值 verdict/逐字引文/禁 repo 存取 | 合約 `contracts/tv-verify.prompt.md`;dispatch `contracts/dispatch/tv-verify-{ad,c}.dispatch.md`;路由=config `MODEL_MATRIX` |
| agy cross(gm 側) | C 批+fixture 路徑 → `gm-*.jsonl` | agy 三要件(--sandbox+EAGER+host CWD) | `t0/tv-gm-worker.sh`;記憶 agy-execution-sandbox-human-fired |
| 聚合 | 全 shard → `verdicts.jsonl`+`split-queue.jsonl` | AGG_RULE;**TYPE_C 跨家族必開**(缺家族=dispatch-fail) | `t0/tv-aggregate.py` |
| 判官 | verdicts+article → `judge-verdicts.jsonl`+`judge-report.md` | step-0 T0;**僅三項裁決範圍**;fresh opus | 合約 `contracts/tv-judge.prompt.md`;dispatch `contracts/dispatch/tv-judge.dispatch.md` |
| bounce | T0 退件 → `bounce-N.jsonl` | 引文紀律(無撇號片段/text_quote 照抄);兩敗升 tier | dispatch `contracts/dispatch/tv-bounce.dispatch.md` |
| fold+終驗 | verdicts⊕bounce⊕judge(同 claim_id 覆蓋/追加)→ 最終 `verdicts.jsonl` | **最終 T0 必 PASS** | 編排行內 fold;閘 `t0/tv-preverify.sh` |
| 計分 | verdicts vs sealed ledger → `score.json` | **純腳本;G1-G5;盲性**(orchestrator/判官永不讀 `_sealed/`/`mut-config/`) | `t0/tv-score.py`;真值 `fixtures/_sealed/*.ledger.jsonl` |
| 計量 | transcript+tokens-raw → `tokens.json`(E) | C1-C6 慣例;E 公式鎖定 | `t0/tv-tokens.py`(抽取)+`t0/tv-tokens-agg.py`(聚合);權重 `capability-matrix.weights.json` |
| 落帳 | score+tokens → ledger 行+hypotheses 判定段 | **判定式先於 run 落檔,不事後改** | `loop-ledger.md`+`hypotheses.md` |

## 迴圈判斷邏輯(SSOT=hypotheses.md,此處只列拓撲)
- **pre-registered 掃描鏈**:BATCH→MODEL_MATRIX→NV×AGG→EXTRACTOR;每假設 keep 出的 pin 是下一假設的 E_pin 錨;判定式(門檻+條件)先於 run 落檔。
- **keep/discard**:先過 gates 全過濾網,再比 E;FAIL/PARTIAL/SKIPPED 皆合法產出(Path B);顯式棄跑須人核+落帳理由,不改判定式。
- **停機**:假設耗盡/連續 2 輪無 keep/token 預算;停機後 dev-best 進 holdout **只跑一次禁迭代**,背離=回退記錄。

## 不可簡化的不變量(改任一階段時這些不准被簡化掉)
1. **同 pin 唯一變因**:假設檢定只認同 pin(commit hash)A/B;mid-run 禁改工具/合約;dispatch 措辭同 pin 內凍結。
2. **盲性拓撲**:orchestrator 與判官**永不讀** `fixtures/_sealed/`+`fixtures/mut-config/`;判官另禁 `fixtures/mutated/`(article 由 dispatch inline);計分=純腳本;scorer 側稽核由獨立子代理代查,orchestrator 只收結論。
3. **G1-G5 質量閘不可簡化**:G2 false-SUPPORTED=0 硬條件;G3 UNVERIFIABLE 濫用、G4 型別逃逸、G5 injection 由 sealed 計分器判——**兩結構洞(共識盲區/棄權盲區)只有播錯集看得見**,播錯集不可拿掉。
4. **判官紀律**:fresh context、下限 opus、**永不經 agy**;僅三項裁決範圍;重新推導不讀 worker 散文;改裁必 re-pass 同管線 T0。
5. **E 公式鎖定**:E=Σ(w_tier×tokens_tier)/n_correct;fable_main=C1 transcript 差值含 cache、50/50 分攤兩密度;分母懲罰質量崩=設計行為;壞包/棄用/救援成本**全額入帳**;跨密度禁直比(C2)。
6. **量測產物不 ingest 進 KB**(鐵律 7);量測慣例 C1-C6 SSOT 在 hypotheses.md。
7. **agy = Gemini only**、三要件缺一即 silent no-op;gm 側 token 記支數+秒數副軸,永不入 E 分子(C3)。

## Gotchas
- **WebFetch 是二手**:摘要化+標點正規化 → 逐字驗證一律 raw fetch(T0 內建 curl+HTMLParser);弱模型會把 fetch 摘要當頁面原文(→ external-verify Gotchas 同課)。
- **U+2019 撇號累犯**:worker 引直撇號 → T0 假陰性;bounce 紀律=無撇號片段優先/text_quote 照抄;根治(norm 摺疊)列下一 pin 工具佇列。
- **harness 壞包**:秒死+0 tool+樣板殘片=壞包非拒答;處置協議 → AGENTS.md Resolved。
- **判官兩協議形態**:gap→bounce(多付一輪)vs 自修+自驗 T0(零懸置);取捨 → judge-loop-chooser modules。
- **fixture 節選邊界**:判官 coverage 抽查對真源整頁,受測文是節選 → dispatch 註明邊界,否則 coverage-miss 誤報。
- 換文章複用:重生 `fixtures/{articles,mutated,mut-config,_sealed}` 四件套+dev/holdout 切割(`t0/tv-split.py`);工具鏈/合約/慣例不動(= 新 pin 只在合約變更時)。

## Modules
- [modules/measurement-methodology.md](modules/measurement-methodology.md) — 技術等價物完整映射(kb-ingest/northstar 機制→本迴圈對應)+ 六 run 落地經驗與方法論 know-why(E 主成分/tier 三明治/兩結構洞/混因披露/慣例 rationale/可移植性)。
