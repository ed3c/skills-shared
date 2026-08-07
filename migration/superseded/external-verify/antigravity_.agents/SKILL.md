---
name: external-verify
description: |
  當 claim 涉及 post-cutoff 框架、工具設定檔約定、模型預設、版本支援、
  或任何沒附可點 URL 的「官方規範」斷言時使用 — 用官方 primary source
  （docs / 原始碼 / repo issue）查到鐵錨,而非靠訓練記憶或 SEO 摘要。
---

# Skill: 官方文件查證真相 — 執行步驟 (External-Verify Runbook)

> **Role**: 對 post-cutoff/不可錨 claim,用官方 primary source 查到鐵錨,阻止「拿訓練記憶/SEO 摘要當事實」。
> **結構**: SKILL.md = 確定性程序 + pointer;已查證真相快照在 `modules/`。
> 這是 [`path-b-reduction`](../path-b-reduction/SKILL.md) 步驟一(尋找物理鐵錨)的執行化;錨念同 northstar External-Verify / PG-163(訓練=幻覺源)。

## When to Use
- claim 涉及「讀哪個檔 / 預設哪個模型 / 哪個版本支援 X / 設計規範是什麼」。
- claim 提到「官方規範」「[必備]」卻**沒附可點 URL**。
- 自信 × 具體 × 不可查證 = 幻覺指紋 → 強制查證,別採信、也別反向臆斷。
- **推薦技術堆疊（tool/lib/model）且下游要商用+不強制開源**：查授權/專利鐵錨（code 授權 + **model card 分開查** + codec 專利）→ [modules/license-patent-compliance.md](modules/license-patent-compliance.md)（開源可商用零 copyleft 判準 + 科技巨頭 permissive 選＝OTIO/ASWF）。

## Not For
- ❌ 確定性可 grep 的矛盾(如 air-gapped ↔ 外部 URL)— 直接驗,不需外部查證。
- ❌ 已 external-verified 且未過期的事實 — 別重複燒查證成本(TCC)。

## 確定性程序(6 步)
1. **三角搜索** — WebSearch ×3 不同切角,蒐集候選 primary URL;優先官方域名(`*.google.dev` / `developers.googleblog.com` / `codelabs.developers.google.com` / 官方 `github.com/<org>/<repo>`)。
2. **拉 primary** — WebFetch 官方 docs/API/codelab,要求逐字引用檔名/路徑/欄位。**禁**靠 WebSearch 合成摘要定案(那是二手)。JS-app docs 渲染不出內文 → 改抓對應 codelab(靜態 HTML 可靠)。
3. **逐 claim 記分** — 每條 → {primary 證實 / hard-secondary(官方 issue·codelab) / 未證}。**單一可驗證 claim 撞牆 = 整段降級**。
4. **信心分層** — primary 多源一致 = 可當定局;只在二手出現 = frontier-contested,禁當定局。
5. **雙向自我修正** — 推翻原 claim 要記;推翻**自己先前的反向臆斷**也要記。
6. **附來源** — 列官方 URL(markdown link),標哪條 primary、哪條 secondary。

## Gotchas
- WebSearch 回傳的「答案摘要」是 LLM 合成的二手,**不是鐵錨** — 一定走 step 2 拉 primary 才定案。
- **WebFetch 也是二手**:它經小模型改寫——會摘要化(bullet 卡片非原文)、正規化標點(彎撇號 ’ U+2019 → 直撇號 ')。**逐字引文/string-match 級驗證必須 raw fetch**(curl+HTML tag-strip),否則兩類假象:①逐字比對假陰性(truth-verify 五 run 撇號累犯);②弱模型把 fetch 摘要當頁面原文,對「摘要沒提的真內容」發缺席式誤判(H2b haiku 大面積 false-REFUTED 主因)。案例錨 → `truth-verify/loop-ledger.md`。
- **子代理轉述的「引文」可整句捏造**:claude-code-guide 代理曾回傳官方 doc 原文不存在的引句並據以判 CONTRADICTED,raw fetch 原文裁決推翻(該頁真句 hooks.md:1181 反而支持原 claim,2026-07-20)——引文級 verdict 一律 raw fetch 覆核,代理/WebFetch 摘要只當線索非錨。
- **數字對 ≠ 機制對**:二手轉述最典型的走樣是百分比全數正確、機制/對象漂掉(superpowers-6 案:「合併 reviewer」實為 spec-compliance×code-quality 被轉成「安全×style」;tiering 實為 orchestrator prompt guidance 被轉成 keyword router)→ step 3 逐 claim 記分時把「數字 claim」與「機制 claim」拆開各自對 primary;要照著落地的,承重的是機制 claim。案例錨 → [token-efficiency-anchors](../antigravity-harness-wiki/modules/token-efficiency-anchors.md)。
- 官方 JS-app docs(`antigravity.google/docs/*`)WebFetch 常只回標題 → 改抓對應 codelab。
- 本 skill 產出的「已查證真相」是**會過期的快照**,復用前重跑 step 1-2。

- **授權≠功能對、code 授權≠model 授權、開源≠免專利**：推薦堆疊時「開源可用」不等於「可商用零義務」。code MIT 的 lib 其 model 可能 CC-BY/gated（實測 pyannote：code MIT、diarization model CC-BY-4.0 gated）；開源 codec 實作不免 H.264/265 專利費（Via LA，encode≫decode 風險）。→ [modules/license-patent-compliance.md](modules/license-patent-compliance.md)。

## Modules
- [modules/verified-truth.md](modules/verified-truth.md) — Google Antigravity 設定檔 / skill 規範「已查證真相表」+ 信心層 + Sources(cc-20260625 快照)
- [modules/license-patent-compliance.md](modules/license-patent-compliance.md) — 授權/專利合規查證軸（code+model 雙授權分開查、copyleft 分類、codec 專利、科技巨頭 permissive 選 OTIO/ASWF；LIVE 錨 cutplan `LICENSES.md`）。
