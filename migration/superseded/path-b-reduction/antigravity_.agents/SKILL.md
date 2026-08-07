---
name: path-b-reduction
description: |
  寫作、評估某架構/概念、或產出研究綜述時使用 — 把每個 claim 約分到它的
  Path B 確定性鐵錨（exit-code / test / val_bpb / external-verified source），
  阻止認知卸載。當出現「平均 / 效率提升 / 優化 / 品質改善」等平滑抽象敘事時觸發。
---

# Skill: Path B 底層原理解構引擎 (Semantic Reduction Engine)

> **Role**: 把任何 claim 約分到它的 Path B 確定性鐵錨,阻止認知卸載(語義表面化 / 平均值幻覺)。
> **結構**: SKILL.md = 確定性程序 + pointer;domain know-why 在 `modules/`(SKILL 不複述)。
> ⚠ 此「Path B」= Path A/B 執行模式軸(`.md` 概率 → `.py` 確定),**非** Layer A/B 抽象軸 — 詳 [modules/know-why.md](modules/know-why.md)。
> 本檔是 Path B **方法論通則**。antigravity DR 管線**實際在用的** Path B 模板(`PATH_B_TEMPLATE` / `PATH_B_REFINE_TEMPLATE` 四階段量規版)逐字 SSOT 在 [dr-research-loop/modules/loop-panorama-ssot.md §3.2/§3.7](../dr-research-loop/modules/loop-panorama-ssot.md);別在本檔留簡化副本。

## When to Use
- 評估/吹捧某架構、演算法、概念(「微服務」「優化」「模組化」「效率提升」)。
- 寫研究綜述 / DR 落地說明 / faithful-absorption 輸出。
- claim 帶「平均」「整體提升」「品質改善」等平滑指標。
- 比較兩方案/兩實體優劣;解釋某機制「做了什麼」。

## Not For
- ❌ 純執行指令、檔案操作、聊天確認、已 external-verified 的事實複述(套四步驟 = 違反 TCC,能便宜就不貴)。
- ❌ 重定義 northstar 的 Path B — 本 skill 只**應用**,SSOT 在 northstar(見 modules/know-why.md 的錨)。

## 確定性程序 — Path B 四步驟稽核協議
評估某架構/概念、或寫研究解構時,**嚴格執行並在輸出中清晰標記四步驟**:

1. **物理鐵錨 (Byte = Path B)** → 指出焊死、不可被 prompt/統計操弄的確定性底線(exit-code / test / val_bpb / external-verified primary source)。
2. **人為槓桿 (Tokens = Path A 被 game)** → 指出哪個主觀分母被拿來刷數據(alignment_rate / fired_count / surface-count …),拆穿作弊手法。
3. **微觀總代價 (Total Loss)** → 用鏈式法則逐項累加真實總驚訝度,繞過帳面平均,不准用一個總分掩蓋微觀缺口。
4. **約分消去** → 總代價 ÷ 物理鐵錨,把人為槓桿約掉,給不帶水分的純資訊密度真相(discrimination / 真 PG-resolution)。

> 各步驟完整定義 + 原始 prompt 模板 → [modules/audit-protocol.md](modules/audit-protocol.md)

## Gotchas
- frontmatter `description` 一律用 `|` block scalar;**任何 `": "`(冒號+空格)會讓 YAML 解析失敗 → skill 被靜默跳過**(連自己名字都 recall 不到)。
- 「反認知卸載」≠ 堆長度。能短則短(TCC):重點是寫出底層**移動了什麼資料、改了什麼約束、付了什麼物理代價**,而非字數。
- 鐵錨 ≠ 訓練記憶。post-cutoff 事實的鐵錨在外部 primary source(配 external-verify skill),不在 LLM 自述。
- **判定式機械過 ≠ 因果成立**:量測值受環境混因污染時,照樣機械判 PASS 但**判定帶星號+混因全文披露、因果宣稱明文不成立**——不改門檻、不護航、也不把 PASS 說成「已證明」。教科書案例(降本假設全滅/PARTIAL/SKIPPED 顯式落帳/compaction 混因披露)→ [modules/know-why.md](modules/know-why.md) §truth-verify 案例錨。

## Modules
- [modules/audit-protocol.md](modules/audit-protocol.md) — 四步驟完整定義 + 執行指令模板(原始 Path B prompt)
- [modules/know-why.md](modules/know-why.md) — 核心哲學 + 語義流風格約束(4 條)+ northstar Path B 錨定(axis 消歧 / val_bpb / PG 映射)
