# Module: grounding 三態 + 四層獨立性階梯 — know-why（Layer B）

> 屬 [`judge-loop-chooser`](../SKILL.md)。SKILL.md 有路由決策樹 + 快查表;本檔 = **兩條正交軸的 know-why**（為何是三態不是二元、為何獨立性看權重不看強度、為何兩軸不可塌成一軸）。
> 查證外部 claim → [`external-verify`](../../external-verify/SKILL.md);Path B 四步驟 → [`path-b-reduction`](../../path-b-reduction/SKILL.md)。

---

## 軸一：grounding／anchor-reality（技術實現等價物,三態）

### 問的問題與取值
> 驗證方法的判決**底下到底有沒有真實技術實現**？取值＝ `technical_equivalent` / `candidate` / `[推論]`（三態,不是二元）。

這條軸**不是**在問「被驗的維度是 runnable 還是 semantic」——一個看似 runnable 的維度,其驗證方法可能是**空心 grep**（結構保留卻沒驗到真東西）。dim-kind 看不到這個空心,grounding 軸才抓得到。

### 為何三態,不二元（命門）
```
[推論](無真 impl) ─── candidate(真 impl,覆蓋未掙) ─── technical_equivalent(完整覆蓋,已判讀)
```
- **technical_equivalent**：判決約分到「判讀一個真實／already-have 實現的**完整**自動化測試覆蓋結果」。合格錨（antigravity）＝開源可商用庫的 `test`/`pytest` exit-code、physical oracle（`val_bpb`）。**覆蓋是掙來的、非假設**——真實庫不一定已有完整測試覆蓋。
- **candidate**：真實庫**存在**但覆蓋未掙（`automate.js` COMPLETENESS_RUBRIC 的「覆蓋狀態：已覆蓋／部分／未覆蓋」對應 full/partial/none）。**candidate ≠ [推論]**——把「真庫未覆蓋」判成「沒庫」會低估真件、扭曲覆蓋率真相。
- **[推論]**：無真實現。誠實標三種來源：
  1. bespoke 結構 grep/AST/presence —— 不判任何真實現的測試 ＝ **空心-T0 placebo**。
  2. LLM 判斷（reviewer 的 `drift_score`）—— 是給人的證據,**非放行令**。
  3. `external_primary`（`stealth_fetch` 抓的 post-cutoff 官方事實）—— 相鄰**事實**錨,**非方法-執行等價物**,另列。

### 這條軸在 antigravity 早已被實踐（demand-pull,非外來 import）
`automate.js:199` 的 `COMPLETENESS_RUBRIC` 逐維度要求「可追溯的技術實現等價物：優先開源可商用庫（附套件名／repo／授權）,無則標 [推論]+可推論來源」;`automate.js:233` 的覆蓋矩陣格式＝`維度 | 覆蓋狀態 | 技術實現等價物（開源可商用庫,附 repo） | 來源／[推論]`。**三態語意（已覆蓋／部分／未覆蓋 × 技術實現等價物／[推論]）已經在 automate.js 的 prompt 模板裡跑。** 本 skill 不是新增紀律,是把散在 prompt 裡的紀律**升格成可判標準**——判「Gemini 吐回的覆蓋矩陣,那些勾是真的還是空心」。

### release ≠ 一個綠勾（antigravity 版三級）
northstar 有「green anchor → fold_in_sandbox_gate → 人 admit」三級閘。antigravity 無沙盒 gate,但同精神：
1. **證據**：該維度真指到一個開源可商用庫 + 它自己的測試綠（或 `val_bpb` physical oracle）。
2. **provenance**：來源可追溯（repo/授權/逐字稿行,非「模型說有」）。
3. **人 admit**：把覆蓋矩陣交人收下。綠勾是**證據**,不是**授權**——消費一個「模型自稱已覆蓋」但無 repo 錨的維度當 technical_equivalent＝placebo。

---

## 軸二：四層獨立性階梯（whose-weights）

### Same-Weights 陷阱有兩個可分離的成分
驗「輸出有沒有服務意圖」而 producer 與 verifier 都是 LLM 時：
- **脈絡／路徑相關**——verifier 繼承 producer 的框架、既定假設、對話史。
- **權重相關**——同權重對同輸入有**同系統性盲點**（共享幻覺、重疊訓練分佈缺口）。

多數「修法」只碰**一個**。persona 多樣化 / 換更強的**同家族** tier / 多迭代都**破不了任一個完整**（仍同權重）。**Gemini 審 Gemini DR ＝ Gemini-on-Gemini**（antigravity 版的 Claude-on-Claude）。

### 四層（cheapest first;每層抓下層抓不到的）
- **T0 確定性**（exit-code / grep / AST / physical oracle `val_bpb`）→ 無權重 ⇒ 破**兩半**。最大化這份額。
- **T1 零存取**（fresh context + 封裝包＝intent + artifact + rubric,**無 drafting 史**）→ 只破**脈絡**相關。成本禁跨家族**且**判決可單憑封裝包重現時用。意圖漂移 reviewer 跑這層。
- **T2 跨家族 Diamond**（[`external-verify`](../../external-verify/SKILL.md) 官方 doc / 不同家族模型 / Path B 確定性,**≥2 同意**）→ 唯一**觸**權重相關,且**僅靠三角測,非「解決」**（共享網路語料盲點仍在）。
- **T3 人**→ 最終權威（LAND-DECISION）。

### 操作判準
1. **「能單憑封裝包重現」＝閘**。無脈絡可重現 ⇒ 騎在可勾稽的斷言上 ⇒ 逃出權重 ⇒ 信 T1。不可重現（要整體語感）⇒ `needs_diamond` ⇒ T2/T3。
2. **斷言化 rubric 有自己的盲點**——它抓它斷言的,漏 **negative-space**（被靜默省略的,SI7）,那既抗斷言又抗 packet-reproduce ⇒ 不可約 T2/T3。空心保結構的 overfit 會過所有結構斷言（＝ hollow-T0）。**把線往下壓,永不到零。**
3. **對抗式跨模型 > 獨立 eval,只在**其輸出＝可證偽的攻擊向量、由確定性 oracle 裁決,**不是**辯論到共識（兩模型辯到 consensus collapse 無效）。
4. **tier-by-role**：便宜 tier（Gemini flash）OK,若有確定性 oracle 兜底;**強 tier + 人**用在無 oracle 處（方向 / 局部最小 / negative-space）。

### 為何「strategic」不是一個模型 tier
macro（架構尺度戰術）/ micro（代碼尺度戰術）是**戰術 lens**,可配模型。但「**strategic ＝ 決定 WHAT / 收下 FINAL ＝ 人的 LAND-DECISION,永不是模型 tier**」。戰略意圖**驗證**也塌回人／獨立知識論,永不是更便宜的同家族 tier——這就是 T1 單獨不夠、Diamond（T2）+ 人（T3）是結構性的原因。

---

## 兩軸為何正交（不可塌成一軸;誤改命門）

| 軸 | 問題 | 取值 |
|---|---|---|
| ① grounding | 判決底下有沒有真實現？ | technical_equivalent / candidate / [推論] |
| ② 獨立性 | 驗證者誰的權重？ | T0 / T1 / T2 / T3 |

一個 check 可以 **T0-independent 但 HOLLOW**：獨立性軸判它 T0 可信,grounding 軸判它 placebo（空心 grep 沒驗真東西）。**hollow-T0 cell 正是獨立性軸單獨漏、grounding 軸才補的格。** 把 grounding 寫成「T0/runnable＝等價物」的簡單 mapping ＝ 塌軸 ＝ 丟掉 anchor-reality 判別力（＝這條紀律在防的扭曲）。兩軸各自升旗：`needs_diamond`（獨立性）與 grounding `[推論]` 獨立。negative-space residue ＝ 兩軸都不可約 ⇒ T3 人。

---

## Sources / Lineage
- 活基座（antigravity）：`automate.js:199` COMPLETENESS_RUBRIC、`automate.js:233` 覆蓋矩陣、`automate.js:130` PATH_B_TEMPLATE / `:134` val_bpb;AGENTS.md「輸出／研究風格 Path B」。
- northstar 源：`.claude/skills/judge-loop-chooser/modules/grounding-axis-panorama-ssot.md`（三態 SSOT + 管線 + 機器閘）+ `four-tier-independence-ladder.md`（whose-weights 階梯）。**retarget 拿掉了什麼 → [retarget-map.md](retarget-map.md)。**

## truth-verify 實測錨(2026-07-05/06 六 run;帳本 SSOT=`truth-verify/loop-ledger.md`+`hypotheses.md`,本段只記課不抄數字)

一條完整 judge-loop 的實測(pinned fresh-Opus 判官、sealed 播錯集、純腳本計分、盲性分離)對本 skill 兩條軸的回饋:

**獨立性階梯的實測邊界——「一致性≠正確性」兩結構洞**:
- **共識盲區(G2 形態)**:holdout c-020,subtle 語義偷換(「缺全量相關集」→「未標記已檢索 chunk」)騙過 claude-opus 與 gm-pro **雙家族一致 SUPPORTED**;`cross-family-agree` 直通聚合,判官只觸發於分歧/機械退件,從未複核。跨家族異構冗餘擋得住「單家族慣性」擋不住「共識概念混淆」。
- **棄權盲區(G3 形態)**:H2b haiku 對可判 claim 大面積標 UNVERIFIABLE——無 evidence 可機械檢(T0 過)、不在判官三項裁決範圍(語義層不裁)、一路穿透到 sealed 計分器。
- 推論:**agreement-gated review 的獨立性再高也只覆蓋「有分歧」的子空間**;兩洞的唯一可見性來源是 ground truth(播錯集),補洞是對 agreement 條目抽樣複核,不是加驗證者(NV=2 A/B 實測:Δrecall=0、E +7%,加同構驗證者=純成本)。
- 判官獨立性正例:holdout ghi 判官識破 c-010 尺度反轉為單點突變、c-012/013 為其下游偽影,**同時推翻 claude 與 gemini**——「重新推導,不讀 worker 散文」的合約款是實質防線;邊界 claim(dev c-005 四 run 四判)判官逐 run 獨立裁決是唯一穩定器。

**判官協議兩形態(操作課)**:①「gap→退回 re-verify(bounce)」——判官零裁決成本但多付一整輪編排;②「自修證據+自驗同管線 T0(零懸置)」——判官貴但 H3/holdout 實測消滅 bounce 輪。取捨:退件量小或證據可逐字重錨時,形態②總成本更低;形態②必須「改裁後 re-pass 同一機械閘」否則是無錨自宣。

**成本結構課(tier 選擇的判官面)**:「便宜 worker + 貴判官救援」總成本高於「中 tier 一次做對」(H2b:判官 29 條改裁+升級 bounce,E 反升)——judge-loop 的降本靶在 worker 一次做對率與編排輪次,不在判官 tier(判官下限 opus 不可降,見量測迴圈不變量)。
