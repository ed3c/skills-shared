# Module: truth-verify-loop — 技術等價物映射 + 落地經驗 + 方法論 know-why

> 屬 [`truth-verify-loop`](../SKILL.md)。SKILL.md=組件卡+不變量;本檔=為何這樣設計、機制從哪裡等價移植、六 run 學到什麼。數字 SSOT 永遠在 `truth-verify/loop-ledger.md`+`hypotheses.md`,本檔只記課與指針。

## 1. 技術等價物映射(這條迴圈的每個機制從哪裡來、等價於什麼)

| 既有機制(來源) | truth-verify 對應物 | 等價判斷/差異 |
|---|---|---|
| kb-ingest T0 pre-verifier(`verify-claims.sh`) | `t0/tv-preverify.sh`(--claims/--verdicts 雙模式) | 同一「執法左移」:機械可檢格式先於訓誡,FAIL 零判官成本退回。差異=verdicts 模式對 live 真源 fetch+string-match(kb-ingest 對 repo 檔案) |
| kb-ingest 判官(≥90 protocol,評分+認證同體) | pinned fresh-opus 判官 + **sealed 純腳本計分器分離** | 結構性升級:kb-ingest 判官 Same-Weights 風險靠 protocol 緩解;本迴圈把「認證正確率」整個抽離給 ground-truth 腳本,判官只產有據裁決——獨立性從 protocol 級升到拓撲級 |
| northstar reverse-mutant eval(判別力測試) | **播錯集**(mut-config 突變+sealed ledger) | 同一判別力思想:防「連接但不判別」的假驗證。差異=突變施加在受測物(article)而非評測器;盲性紀律(誰不能看什麼)是新增拓撲 |
| 訓誡衰減定律(kb-ingest A/B 實測) | claim/verdict 合約全機械欄位+四值枚舉 | 直接沿用:prompt 禁令擋不住違反,合約改機械可檢+T0 執法。本迴圈再證:worker 發明 PARTIALLY_SUPPORTED 被 T0/bounce 硬性擋回 |
| engine-baseline 三假設 A/B 法(pre-registered) | hypotheses.md 判定式先於 run 落檔+Path B 落帳 | 同法放大:單 run 三假設 → 六 run 四軸掃描鏈(E_pin 鏈式錨)。兩次獨立實測同構結論:降本假設全滅、真收益在質量軸 |
| external-verify(官方一手錨) | w_tier 牌價 pin(`capability-matrix.weights.json`)+TYPE_A worker 的 fetch 紀律 | 內嵌:量測權重與事實裁決都禁訓練記憶填數 |
| judge-loop-chooser 獨立性階梯 | cross-family(claude×gemini)+judge+sealed scorer 三層 | 本迴圈是它語彙的實例,並實測出其邊界(兩結構洞,§3) |

**可移植判準(反身)**:上表每行都是「有真基座才映」——移植這條迴圈到新 domain 時同法:T0 可檢格式、判官/計分分離、播錯集、pre-registered 判定式四件是可移植核;文章 fixtures 四件套是 per-domain 重生物。

## 2. 量測方法論 know-why(慣例 C1-C6 與 E 公式的設計理由)

- **C1(fable_main=transcript 起訖差值含 cache,50/50 分攤)**:編排成本的誠實計法——不含 cache 會把「大 context 重讀」成本藏掉,而那正是編排側主成分。實測後果:mid-run compaction 成為混因(H2a),處置=披露+同條件錨(H2b/H3 對 H2a 比,不對 pre-compaction 的 BSf 比)。
- **C2(同密度比值、跨密度禁直比)**:lo 密度分母 3-7,高變異;E_lo 是方向性數字。兩密度比值一致(如 H2a 0.5997/0.6005、H3 1.0703/1.0679)是內部一致性的強訊號。
- **C5(claims 重用 baseline+extract 常數搬運)+C6(編排對稱性)**:同 pin A/B 的變因純度——連「判官照常全跑」都保留,只為 fable_main 可比。holdout 例外(新文章無 baseline 抽取,全鏈自跑,E 絕對值不與 dev 直比)。
- **E 分母=n_correct(sealed 交集)**:把質量閘內生進成本——質量崩則分母塌、E 自動暴漲(H2b E_hi ×1.48 的主因是 16→11 非 token 增),無需外掛懲罰項。**這是「省 token 但答錯更貴」的公式化。**
- **壞包/棄用/救援全額入帳**:剔除「不是 config 的錯」的成本=製造無法復現的美化數字(Path B)。

## 3. 六 run 落地經驗(2026-07-05/06;數字→loop-ledger.md)

- **E 第一主成分=編排側**(fable_main ~99%):BATCH 拆小 ×1.77(H1);worker tier 劇變只動 E ±7%(H2/H3)。降本靶=批次做大+輪次壓少(bounce 輪是可壓項:引文紀律前置後 4 輪→1 輪→0 輪)。
- **tier 質量三明治**:TYPE_A opus→sonnet 逐項零退化(H2a);sonnet→haiku 三態崩壞——摘要當原文/濫標 UNVERIFIABLE/false-REFUTED+型別逃逸+bounce 違紀(H2b)。**路由矩陣格有硬下限;「便宜 worker+貴判官救援」總成本高於中 tier 一次做對。** haiku 僅轉錄類安全(EXECUTION-TIERING 6 次零升級),判斷類永不。
- **質量 ceiling 在抽取層**:未抽取 span 的突變對任何驗證者數不可及(H3 Δrecall=0;holdout miss 8/10 放大)。驗證冗餘=純成本;改善在抽取覆蓋工具,不在 tier(H4 SKIPPED 被 holdout 反向支持)。
- **兩結構洞(防線拓撲)**:①棄權盲區(G3)——可判卻標 UNVERIFIABLE 無證據可機械檢、不在判官三項內,穿透雙層;②共識盲區(G2)——雙家族同錯無分歧,agreement-gated 判官不觸發(holdout c-020 全計劃唯一 G2 破口)。**唯一可見性來源=播錯集;補洞=agreement 抽樣複核,非加驗證者。**
- **判官獨立性是實質防線**:「重新推導不讀 worker 散文」讓 holdout ghi 判官同時推翻 claude 與 gemini(識破單點突變 vs 下游偽影);gm 的「受測文自證」循環路徑被判官逐 run 攔截;邊界 TYPE_C(c-005 四 run 四判)判官是唯一穩定器。
- **injection 全程 100% 抵抗**(6 run×抽取/worker/判官/agy 全層,c-inj-01/02 零服從)——delimiter-as-DATA+「注入句照常抽出當 claim」的合約設計有效。
- **G2「不假背書」的韌性形狀**:dev 全 tier fs=0(haiku 亂軍下退化為棄權/漏抓而非假認證);holdout 1 例破口是共識語義偷換,非捏造——防線對「編造」極強,對「全員被騙」有洞。
- **混因兩例(量測誠實)**:mid-run compaction 壓 cache_read、bounce 紀律跨 run 學習效應——機械判定照過但「判定帶星號+因果宣稱明文不成立」(→ path-b-reduction 案例錨)。

## 4. 可移植性(換文章/換 domain 要動什麼)

- **重生**:`fixtures/articles/`(真源節選,curl 原始 HTML 保逐字)→ 播錯(`mut-config/`+盲審撰寫,claude 集由 gm 寫/gm 集由 opus 寫)→ `mutated/` 四變體(2 家族×2 密度)→ `_sealed/*.ledger.jsonl` 真值帳 → `t0/tv-split.py` 切 dev/holdout。
- **不動**:t0 工具鏈、三份 standing 合約+dispatch 模板、C1-C6 慣例、G1-G5 定義、判官紀律——動它們=新 pin。
- **下一 pin 已排佇列**(hypotheses/ledger 落帳):U+2019 norm 摺疊、抽取覆蓋工具(密突變長文)、agreement 條目抽樣複核、切批標籤腳本化、cache_read 折權分 kind 記帳。
