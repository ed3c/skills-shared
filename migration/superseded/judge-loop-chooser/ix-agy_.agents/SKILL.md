---
name: judge-loop-chooser
description: |
  把一個可判的 deliverable 路由到它該用的驗證標準與獨立性 tier —— 在 antigravity 這代表
  DR 報告／Path B 精煉／COMPLETENESS 覆蓋矩陣（不是代碼／沙盒,那條 branch 在本 repo 無基座,已誠實拿掉）。
  recipe-not-engine：只路由＋SURFACE,不執行、不自動串接、不自動接受任何 judge／reviewer 判決,人出閘最終。
  三態 grounding（技術實現等價物／candidate／[推論]）＋四層獨立性階梯（誰的權重）＋意圖漂移探針。
  何時用：一輪 DR 完成／一份覆蓋矩陣／一段 Path B 精煉要選驗證標準＋獨立性 tier 時。
  NOT for：自動改 automate.js／auto-accept 判決（human-exit-gate 紅線）;跑或診斷管線（dr-research-loop）;
  查證單一外部 claim（external-verify）。完整 know-why 在 modules/。
---

# Skill: judge-loop-chooser — 把可判 deliverable 路由到驗證標準 + 獨立性 tier

> **Role**: 給一個**可判的 deliverable**（antigravity＝DR 報告／Path B 精煉／COMPLETENESS 覆蓋矩陣）,選它該用的**驗證標準**（三態 grounding + 意圖漂移探針）與**獨立性 tier**（T0/T1/T2/T3）。**只路由 + SURFACE,不執行、不自動接受任何判決** —— 人出閘是結構性的（recipe-not-engine）。
> **結構**: SKILL.md = 路由決策樹 + 不變量 + Gotchas;兩軸為何正交／各 tier 破什麼的 know-why 在 [modules/grounding-and-independence.md](modules/grounding-and-independence.md);零存取意圖審查 payload 在 [modules/intent-drift-review.md](modules/intent-drift-review.md)。
> **SSOT**: 三態 grounding 的**活基座**＝`automate.js` 的 `COMPLETENESS_RUBRIC`（`automate.js:199`,固定 14 維度,每維度須有「可追溯的技術實現等價物」;覆蓋矩陣格式 `automate.js:233`）＋ AGENTS.md「輸出／研究風格 Path B」。獨立性驗證的活基座＝[`external-verify`](../external-verify/SKILL.md) + [`path-b-reduction`](../path-b-reduction/SKILL.md)。漂移時以 `automate.js` / AGENTS.md 為準。
> **Lineage**: port 自 northstar `judge-loop-chooser`。northstar 的 code/sandbox 判決表（`execution/lib/judge_chooser.yaml` → design-judge 沙盒）在 antigravity **無基座,已誠實拿掉**;逐機制映射 + 拿掉了什麼 → [modules/retarget-map.md](modules/retarget-map.md)。**非原樣搬**（原樣搬 = 引用不存在基座的死 husk）。

## 🚩 STOP — 你在合理化（違反即停）
| 念頭 | 現實 |
|---|---|
| 「reviewer 給了 ALIGNED,直接收下當完成」 | ❌ 無 auto-accept;分數是給人的證據,非放行令（human-exit-gate / 鐵律 4） |
| 「Gemini 自己審 Gemini DR,夠獨立了」 | ❌ Same-Weights：同家族同盲點 → 非 packet-reproducible → needs_diamond（T2/T3） |
| 「覆蓋矩陣有勾就算驗到了」 | ❌ 空心勾（bespoke grep／散文,不判真實現）= 空心-T0 placebo → 降 [推論] |
| 「這條 code/sandbox 判決表要不要也搬進來」 | ❌ antigravity 無 design-judge 沙盒／execution/lib;搬＝死 husk（見 retarget-map） |
| 「報告夠長、過了所有下游門檻,就是好的」 | ❌ 長度不是 grounding;剪貼簿污染案就是「夠長、過門檻、換了問題」的 negative-space 漂移（SI7） |

## When to Use
- 一輪 DR 完成,要判「這份報告忠實服務了原卡片盒問題／原 thesis,還是漂了（換了問題／靜默省略／污染）」。
- 一份 COMPLETENESS 覆蓋矩陣要判「每個維度的『已覆蓋』是真技術實現等價物,還是 [推論]」。
- 一段 Path B 精煉要判「每個 claim 真約分到確定性鐵錨,還是 Half-Bridge 散文」。
- 要決定某個判決該靠 **T0 確定性 / T1 零存取 / T2 跨家族 external-verify / T3 人**。

## Not For
- ❌ 自動改 automate.js / auto-accept 判決 → human-exit-gate 紅線（本 skill 只 SURFACE）。
- ❌ 跑 / 診斷整條管線（啟動、里程碑、失敗簽名） → [dr-research-loop](../dr-research-loop/SKILL.md)。
- ❌ 查證單一外部 claim 的真假 → [external-verify](../external-verify/SKILL.md)（它是本 skill 的 T2 工具,不是替代）。
- ❌ 把報告抽成保真 markdown → [gemini-deep-research-extract](../gemini-deep-research-extract/SKILL.md)。
- ❌ 搬 northstar 的 code/sandbox 判決表 → 無基座 husk（retarget-map.md）。

## 不變量（違反即停）
1. **recipe-not-engine**：只路由 + SURFACE。reviewer 評分 / 跨家族同意 / 覆蓋勾都**不可** auto-accept 一個 FINAL —— 人出閘結構性（兩道人閘：ENTRY 選標的+標準、EXIT 收下 FINAL;模型階梯只活在兩閘之間）。
2. **三態 grounding,不二元化**：technical_equivalent（判讀真實現的**完整**自動化測試覆蓋）/ candidate（真件存在、覆蓋未掙,full/partial/none）/ [推論]（無真實現）。**candidate ≠ [推論]**（真庫未覆蓋≠沒庫）。
3. **獨立性看「誰的權重」,不是「誰更強」**：Gemini 審 Gemini＝Same-Weights;只有 packet-reproducible 的判決才信 T1,否則 needs_diamond。強 tier ≠ 獨立 tier。
4. **negative-space 不可約人**：被靜默省略的（SI7）既抗斷言又抗 packet-reproduce → 不可約 T2/T3。把線往下壓,永不壓到零。
5. **無 code-branch**：antigravity 的可判物是 DR/Path B/覆蓋矩陣,不是代碼/沙盒。別引入 `judge_chooser.yaml` / design-judge 沙盒 / `execution/lib`（本 repo 無基座）。

## 確定性程序（路由決策樹）
1. **判 deliverable 型**（load-bearing,寫在路由開頭）：
   - **DR 報告 / 卡片盒吸收物** → 意圖漂移審查（[modules/intent-drift-review.md](modules/intent-drift-review.md),intent＝原卡片盒問題 / 原 DR thesis / 逐字稿源頭鐵錨）＋ external-verify（post-cutoff 事實）。
   - **COMPLETENESS 覆蓋矩陣** → 三態 grounding **逐維度**（每維度各判一次,別用同一套硬套每條——會扭曲真相）。
   - **Path B 精煉** → 每 claim 約分鐵錨（path-b-reduction）;無鐵錨＝Half-Bridge 散文＝[推論]。
   - **技術選型 fit-to-plan**（OSS 堆疊/repo 選型對計劃+生產環境的匹配度）→ **5-axis 匹配度 rubric**（A 能力 / B 約束 / C 架構 / D 第一性 / E 市場-gap）× 三態 grounding × 獨立性 tier;各軸路由 repo-wiki-converge（A/C 源碼真相）/ external-verify（B 約束）/ dr-research-loop（D 第一性,理解不足時）/ gcr Mode B（E 市場-gap,理解不足時）。**切入點＝每維度底層原理真相**（選型是否尊重它 + 與市場差異是否被那條真相正當化）。詳 [modules/fit-scoring-recipe.md](modules/fit-scoring-recipe.md)。
2. **對每個選定的驗證方法,判 grounding 三態**（下方快查 / modules 決策樹）→ 標 anchor + provenance,或降 [推論]。
3. **判獨立性 tier**：verdict 能單憑封裝包（intent + artifact + rubric）在 zero-access 重現嗎?
   - yes → **T1 零存取**（fresh Gemini/Claude context,只破脈絡相關）。
   - no → **needs_diamond** → **T2 跨家族**（external-verify 官方源 / 不同家族模型 / Path B 確定性,≥2 同意）/ **T3 人**。
4. **SURFACE 輸出**（別自動接受,同構 `automate.js:233` 覆蓋矩陣）：
   `可判維度 | 驗證方法 | grounding 三態(anchor kind+ref) | 獨立性 tier | [推論]/不可約 T3`
5. **人出閘**：把矩陣 + needs_diamond 升旗交人 admit。**永不自動 chain 下一步**。

## grounding 三態快查（操作;完整決策樹 → modules）
```
驗證方法的判決能約分到「判讀真實/already-have 實現的【完整】自動化測試覆蓋」嗎?
  ├─ yes → technical_equivalent,CITE anchor(kind + ref + provenance)
  │        antigravity 合格錨：開源可商用庫的 test/pytest exit-code；physical oracle(val_bpb)
  ├─ 真實庫存在但覆蓋未掙(部分/未覆蓋,automate.js 的「覆蓋狀態」) → candidate,標覆蓋狀態 + 來源;
  │        路由去掙覆蓋(SURFACE only,不跑、不自動升級)
  └─ 無真實現 → [推論]-grade,誠實標：
       · bespoke grep/AST/presence      —— 不判任何真實現 = 空心-T0 placebo
       · LLM 判斷(reviewer drift_score) —— 給人證據,非放行令
       · external_primary(stealth_fetch 官方事實) —— 相鄰事實錨,非方法-執行等價物,另列
negative-space（被靜默省略的）→ 既無真錨又抗 assertion → 不可約 T3 人
```
> 這正是 `automate.js:199` COMPLETENESS_RUBRIC 逐維度要的「技術實現等價物：優先開源可商用庫,無則 [推論]」——
> 本 skill 把散在 prompt 模板裡的紀律**升格成可判標準**（判「覆蓋矩陣的勾是真的還是空心」）。

## 獨立性階梯快查（cheapest first;完整 know-why → modules）
```
T0 確定性 —— exit-code/grep/AST/physical oracle(val_bpb) → 無權重,破【脈絡+權重】兩半。最大化這份額。
T1 零存取 —— fresh context + 封裝包(intent+artifact+rubric),無 drafting 史 → 只破【脈絡】相關。
              packet-reproducible 且成本禁跨家族時用;意圖漂移 reviewer 跑這層。
T2 跨家族 —— external-verify 官方源 / 不同家族模型(非 Gemini 審 Gemini) / Path B,≥2 同意
              → 唯一【觸】權重相關(僅三角測,非解決;共享網路語料盲點仍在)。
T3 人 ——— 最終 LAND-DECISION(收下/退回 FINAL)。
```

## Gotchas
- **description 別混 ASCII `冒號+空格`**：出現在 frontmatter description 任一處 → YAML 解析成 mapping → 整個 skill 被靜默跳過（連名字都 recall 不到）。多行一律 `|` block scalar、用全形「：」。(antigravity-skill-authoring 同 gotcha)
- **長度不是 grounding**：DR 報告過了「≥3000 字 + 來源清單」的完成偵測,不代表它服務了原意圖（剪貼簿污染案：10148 字、過所有下游門檻、卻整支換成無關主題）。長度是**完成**訊號,grounding/意圖是**另一軸**。
- **external-verify 的 verdict 也要判獨立性**：它拉官方 doc（T2 事實錨,強）——但若判決要靠「整體語感」補而非單一 doc 勾稽,仍 needs_diamond。工具強 ≠ 判決 packet-reproducible。
- **覆蓋矩陣的「部分/未覆蓋」是 candidate 不是失敗**：真庫存在只是覆蓋未掙 → 路由去掙,別直接判 [推論]（那會低估真件）。
- **無機器閘**：northstar 有 `validate_grounding` 確定性閘;antigravity 這裡是 **SURFACE-only**（人 VERIFY 三態與 tier）。別假裝有自動閘擋你——判斷力靠不變量 + 自審。
- **一致性 ≠ 正確性（agreement-gated review 的兩個實測結構洞）**：①**共識盲區**——跨家族/多驗證者全體同錯時無分歧、judge 不觸發,錯誤直通（truth-verify holdout c-020:subtle 語義偷換騙過 claude+gemini 雙家族一致 SUPPORTED,全計劃唯一 G2 破口）;②**棄權盲區**——「可判卻標 UNVERIFIABLE」的棄權式錯誤無證據可機械檢、又不在 judge 裁決範圍,穿透兩層（truth-verify H2b chi）。兩洞唯一可見性來源 = **sealed ground-truth 播錯集**;補洞方向 = 對 agreement 條目抽樣複核,非加更多同構驗證者（NV=2 實測邊際質量增益 0）。案例 → [modules/grounding-and-independence.md](modules/grounding-and-independence.md) §truth-verify 實測錨。
- **選型與分析超時 (Matching Timeouts)**：進行 fit-to-plan 技術選型與深度代碼事實對照時，底層調用之 L1 `agy` 判官可能因專案規模龐大而超時（預設 5 分鐘）。必須給予調用端與被調用端充足的時長（如 `--print-timeout 30m`），防止因超時退出而導致 `fit-to-plan` 評估淪為 [推論] 級的 placebo 判決。

## Modules
- [modules/grounding-and-independence.md](modules/grounding-and-independence.md) — 兩條正交軸的 know-why：grounding 三態（錨到 COMPLETENESS_RUBRIC/Path B/external-verify）+ 四層獨立性階梯（whose-weights, Same-Weights 陷阱, packet-reproducible 判準）+ 為何正交（hollow-T0 cell）。
- [modules/intent-drift-review.md](modules/intent-drift-review.md) — 零存取戰略意圖 reviewer payload（SI1-SI8 + needs_diamond）,retarget 成「DR 報告是否服務原卡片盒意圖」;剪貼簿污染案＝canonical SI7 negative-space 實例。
- [modules/retarget-map.md](modules/retarget-map.md) — northstar → antigravity 逐機制映射表 + **誠實拿掉了什麼**（code/sandbox 判決表、PG-NNN、execution/lib、sdlc-plan-composer、materializer、.northstar test runner）+ 為何拿掉不是簡化而是「不引入不存在基座」。

