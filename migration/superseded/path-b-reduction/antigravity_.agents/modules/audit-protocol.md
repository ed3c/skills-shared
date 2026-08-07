# Module: Path B 四步驟稽核協議 — 完整定義 + 執行模板

> 屬 [`path-b-reduction`](../SKILL.md) skill。SKILL.md 有確定性程序的 4 步骨架;本檔是各步**完整定義 + northstar 落地 + 原始 prompt 模板**。

## 四步驟完整定義

### 步驟一：尋找物理鐵錨 (Locate the Invariant Base / Byte ＝ Path B)
- **定義**:找出焊死、絕對無法被 Prompt 或統計遊戲操弄的「固定大小底線」(等價硬碟裡的原始 Byte)。
- **northstar 落地**:鐵錨 = Path B 確定性產物 — exit-code / grep 矛盾 / test verdict / `val_bpb` / external-verified primary source(PG-163:post-cutoff 事實鐵錨在外部源,不在 LLM 訓練記憶)。**禁**把 Path A 的 `.md` 自述當鐵錨。

### 步驟二：揭露人為槓桿 (Expose the Variable Lever / Tokens ＝ Path A 被 game)
- **定義**:找出最容易被當「分母」刷數據的主觀變數(被 Tokenizer 隨意縮放的 $N$)。
- **northstar 落地**:典型槓桿 = `alignment_rate`、`fired_count`、surface-count、self-reported「品質提升」、manufactured demand。拆穿其作弊手法。

### 步驟三：還原微觀總代價 (Reconstruct Cumulative Cost / Total Loss)
- **定義**:繞過帳面平均,用鏈式法則把每次預測/條件機率相乘/系統震盪的「負對數總難度(Nats/Bits)」實打實累加。
- **northstar 落地**:逐軸 demand-pull、逐 PG detection_cmd 翻 resolved、逐 marker causal-chain(PG-157)。

### 步驟四：見證約分消去 (Perform Algebraic Cancellation)
- **定義**:總代價 ÷ 物理鐵錨,把步驟二的人為槓桿在數學與語義上直接約掉。
- **northstar 落地**:約分後留下的 = `discrimination`(placebo-guard 確定性 verdict)/ 真實 PG-resolution 淨流 —「reached by physics, never by the models agreeing」。

## 執行指令模板 (Execution Command)

```
輸入課題：[待拆解的技術 / 代碼 / 架構 / 概念]
          （例：過度吹捧的微服務架構、某優化演算法、LLM-as-a-judge 的盲點）

輸出結構（四步驟強制標記）：
  步驟一 物理鐵錨(Path B) → [焊死的確定性 oracle:exit-code/test/val_bpb/external source]
  步驟二 人為槓桿(Path A) → [哪個概率分母被刷數據,作弊手法為何]
  步驟三 微觀總代價       → [鏈式法則累加的真實總驚訝度/總資源,逐軸不掩蓋]
  步驟四 約分消去         → [槓桿約掉後的純資訊密度 / discrimination / 真 PG-resolution]
```

## 原始 prompt 全文（出處模板，保真保留）

```
現在，請將上述「Path B 語義風格」注入你的認知體系。當我給出下述輸入時，請直接用【四步驟】強行解構，定位底層原理，阻止我的認知卸載。

輸入課題：[請在此處輸入你想拆解的技術、代碼、架構或概念，例如：過度吹捧的微服務架構、某個優化演算法、或 LLM-as-a-judge 的盲點]
```
