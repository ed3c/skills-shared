# Module: skill-bettor 本地 truth-verify 實例

> 本檔只做能力索引與誠實狀態表。執行證據 SSOT 永遠在
> `loop_wiki/tv-dual-loop-context/` 的程式、inputs、runs、receipts 與 Git history;不要把 receipt
> 內容複製進 Skill。

## 已實作且真跑

| 階段 | 本地實體 | 已證範圍 |
|---|---|---|
| atomic claims | `data/claims.jsonl` + `scripts/verify_claims.py` | 來源錨、唯一 ID、逐 claim coverage |
| 正負控制 | `selftest.sh` + `scripts/semantic_counterexamples.py` | good/hollow 與 universal-claim 反例 |
| Gemini worker | `scripts/run_agy_truth.py` | security gate、隔離 cwd、file canary、exact schema/coverage/SHA |
| Codex worker | `scripts/run_codex_truth.py` | ephemeral、read-only、structured output、exact coverage/SHA |
| blind aggregation | `scripts/build_aggregation.py` | sealed ledger 不進 judge input |
| semantic judge | `scripts/run_opus_judge.py` | fresh、tools-disabled、no persistence、input/output SHA |
| scoring | `scripts/score_verdicts.py` | pure-script score、false-SUPPORTED gate |
| ledger amendment | `scripts/apply_ledger_amendment.py` | before/after ledger 與人類決定 hash-bound |
| artifact LAND | `data/land-decision.json` | 只承認 `python-context-engine@0.1.0` 的指定 tree |

2026-07-28 本地重播:

```text
sh verify.sh --fast
65 truth/control-plane tests PASS
21 generated context-engine tests PASS
exit 0
```

`python3 scripts/check_production_loop.py` 同日為 `exit 2`,狀態 `blocked`,
`artifact_chain_valid=false`,`completed_items=0/16`。這是必要紅燈,不是可忽略的文件狀態。

## 已跑模型與權限邊界

- agy manifest 要求 `gemini-3.6-flash-high`,effort `high`;receipt 記錄 canary、runner rc、output SHA
  與 11-claim coverage。這證明指定 runner 路徑完成,不是 provider 的密碼學 model attestation。
- Codex runner 要求 `gpt-5.6-sol`,effort `high`,ephemeral/read-only;同樣以 runner receipt 為證,
  不接受模型正文自報。
- agy/Codex 都是 findings worker。final semantic verdict 由 blind fresh judge 提供;artifact promotion
  仍需 named human LAND。
- 每個新 input 都需要新的 claim inventory、output artifact、receipt hash 與外部 call 批准;舊 receipt
  不得替新架構或新產品需求背書。

## 未實作或未證

1. 沒有通用、已 admission 的 `truth-verify` 新題目 scaffolder;`tv-dual-loop-context` 是具體實例,
   不是任意題目的自動 compiler。
2. worker evidence schema 要求 URL/quote,但目前未把每條外部 quote 對 raw primary bytes 做可重播的
   exact-match receipt;`external-verify` 紀律主要由 prompt 與人工審查承擔。
3. 現有 11 claims 只驗原始 dual-loop context 設計,沒有驗證新跨 Domain composition、真實 LangGraph
   相容性、product seed production readiness 或使用者服務足夠性。
4. 現有 LAND 只綁 `python-context-engine@0.1.0`;`python-product-seed` 仍缺獨立 judge、人類 LAND 與
   完整 production receipt chain。
5. 尚無 Codex vs agy 對同一 implementation slice 的 pinned A/B 選型 benchmark;worker 成功不等於
   它是實作任務的最佳模型。
6. truth verification 與 outcome validation 尚未以 typed `Intent -> UserOutcome -> Scenario ->
   runtime evidence` contract 接合。

## 宣稱能力前的最小檢查

```sh
git -C loop_wiki/tv-dual-loop-context status --short
sh loop_wiki/tv-dual-loop-context/verify.sh --fast
python3 loop_wiki/tv-dual-loop-context/scripts/check_production_loop.py
```

- fast gate 綠只證既有 truth/template chain 可重播。
- production checker 紅時不得宣稱 product seed production-ready。
- 使用者服務驗收必須另跑 requirement-bound functional/E2E/adversarial/operational probes。
