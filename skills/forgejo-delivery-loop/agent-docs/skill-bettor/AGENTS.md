# AGENTS.md — skill-bettor 跨 host 工程原則 SSOT(種子)

> **狀態**:種子檔(2026-07-20 起)。skill 內容仍以 Claude Code 路徑為 canonical，Codex
> 透過 `.agents/skills/` 同名 symlink 發現同一份內容；這只完成 skill surface 的 dual-host，完整 SSOT
> 仍暫由 `ARCHITECTURE.md` 擔(設計事實)+ `CLAUDE.md`(Claude-tier 派生)。本檔先落
> **跨 host 通用的工程原則**——一旦 dual-runnable,本檔升為 cross-host SSOT,ARCHITECTURE.md
> 的 SSOT 角色併入(拓撲鏡像 antigravity CLAUDE.md⟷AGENTS.md)。**唯一刻意分歧=主權
> Claude-anchored**(admit/裁決權在人+Claude 主 session)。

## 工程原則(所有 host/agent 遵守)

### 重複組件禁字面推論等價(2026-07-20 人裁,實撞後立)
遇到「這個是不是已有等價物」時,唯一合法解法二選一:
1. **審計既有代碼實際功能 + 真跑一次**——確認它真做那件事,才可宣稱 technical_equivalent。
2. **直接重建後比較**——兩版哪個好;若各有所長則**整合/重構**成一版,不並存兩份。

**禁止**:只憑名字/描述推論「已有技術等價物」就不重建。
- 反面實例(本次實撞):宣稱「gcr llm_judge → judge.py 已有等價」,但沒讀
  `judge.py:_run_llm_judge`——實際審計後發現它只解析 PASS/FAIL,**缺 XML shield
  + double-lock override**,是真 gap 非等價。「runner.py=validator」這種名對名推論=
  [推論]-grade 冒充 technical_equivalent(judge-loop-chooser 三態 grounding 的違反)。
- 判等價=讀碼+跑,不是猜。無審計無真跑的「已有等價物」一律當**未證**,預設重建/比較。

### 「審計＋跑」不足;load-bearing 組件必真重建並列量測(2026-07-20 升級)
「審計既有代碼」只答**做什麼**,不答**做得多好**——只有 Y 存在時「X 等價 Y」不可證偽。
**LLM 用既有組件必偷懶,機制**(推理):
1. **局部成本梯度**:重建耗 token、復用近零成本,「已有等價物」是抄捷徑的現成藉口。
2. **現狀錨定**:讀了既有碼它就成參照系,替代方案顯得多餘;從不生成反事實(fresh build
   長什麼樣),故看不見它可能更好。
3. **審計≠比較**:品質比較需**兩個 artifact 並列量測**,宣稱等價跳過這步。
4. **自建偏袒**:既有物若 LLM 自己建的,護短偏誤加劇。

**解法**:load-bearing ＋ 等價性不確定 ＋ 判錯有代價,三者占任一 → **真重建替代版、
兩版並列量測**才可下等價/取捨結論。校準(防另一極端):門檻是「load-bearing 且判錯有代價」,
非「一律重建」;瑣碎復用(stdlib/明顯 helper)不需,存疑就偏重建。

**實例(本原則的活證,2026-07-20)**:git_gate 上輪「只審計就宣稱 compare_with_baseline 等價」。
真重建 `check_difficulty_gate.py` 並列跑同一難度稀釋場景(加 5 易 case,aggregate 0.60→0.80,
舊 case 沒退)——既有版 G1/G2/G3 **全 PASS 放行**(對稀釋盲),重建版 **REJECT**(錨集仍 0.60=
灌水)。**不重建就看不到盲點**;結論=非等價、是互補缺口→整合(difficulty_gate 補進防禦,
與 compare_with_baseline 各守一半)。對照帳=`families/pinescript-audit/evals/check_difficulty_gate.py` 頭注。

> 此原則的 Claude-tier 派生同載於全局 `~/.claude/CLAUDE.md` 工程偏好段(跨項目通用);
> 本檔為 skill-bettor 專屬 SSOT 的落點。判等價的 tier 詞彙(technical_equivalent/
> candidate/[推論])定義=`.claude/skills/judge-loop-chooser/`。
