# CONTEXT.md — 技術觸發詞與等價落地堆疊 / Trigger Terms and Equivalent Implementation Stacks

本檔是 research-to-implementation router。出現觸發詞時，不只產生概念摘要；必須建立可驗證的 code、model、data、trajectory mapping。

This file routes research language to implementation evidence. A trigger must produce verifiable mappings to code, model, data, and/or trajectory assets—not only a conceptual summary.

## Trigger matrix / 觸發矩陣

| Trigger / 觸發詞 | 技術含義 / Meaning | 等價落地堆疊 / Equivalent implementation stack | Required evidence / 必要證據 |
|---|---|---|---|
| `Agent Runtime`, `durable execution`, `long-running agent`, `managed agents` | 可恢復、可暫停、可重播的 Agent 執行控制面 / recoverable and replayable Agent control plane | LangGraph state machine + Temporal durable workflow + PostgreSQL checkpoint + object storage + OpenTelemetry | workflow state schema, retry policy, idempotency test, replay trace |
| `Context Engineering`, `compaction`, `retained reasoning`, `memory` | 上下文選擇、壓縮、持久化與重建 / context selection, compression, persistence, reconstruction | LangGraph checkpoint + structured memory store + compaction policy + semantic retrieval + trace-linked snapshots | before/after token budget, retention test, lost-fact eval, trajectory diff |
| `Agent Harness`, `scaffolding`, `prompt debt`, `Harness Diet` | 模型外部控制邏輯與工具介面 / external control logic and tool interfaces | declarative tool schema + policy layer + model adapter + benchmark CI + configuration diff | harness manifest, prompt/tool diff, cost/quality regression |
| `Sandbox`, `isolation`, `cyber range`, `risky action` | 將文字授權轉成 runtime 可執行邊界 / executable runtime boundary | Firecracker microVM or gVisor + default-deny egress + ephemeral credentials + OPA/Cedar policy + OpenTelemetry audit | negative egress test, credential scope, syscall/network trace, stop-condition evidence |
| `Agent Evaluation`, `benchmark`, `trajectory`, `test-time compute` | 評估完整行動序列，而非只評 final answer / evaluate action sequence, not only final output | deterministic task fixture + trajectory schema + budget sweeps + MLflow experiment tracking + trace viewer | task seed, model/config hash, tool-call trace, cost/latency, pass/fail artifact |
| `LLM Gateway`, `provider fallback`, `spend cap`, `rate limit` | 多模型路由與執行治理 / multi-provider routing and runtime governance | gateway proxy + policy engine + quota store + secret broker + OTel metrics/traces | routing decision log, failover test, quota violation test, redaction evidence |
| `Inference`, `KV cache`, `throughput`, `serving` | 生產推論效能與容量管理 / production inference performance and capacity | vLLM or SGLang + Kubernetes + autoscaling + model registry + Prometheus/OpenTelemetry | tokens/s, TTFT, p95 latency, memory profile, load-test configuration |
| `Model Factory`, `training pipeline`, `experiment registry` | 模型訓練與實驗的可重現供應鏈 / reproducible training and experiment supply chain | Transformers + distributed runtime + MLflow + versioned object storage + dataset lineage | code commit, config, dataset hash, model hash, eval artifact, lineage graph |
| `Open Model Supply Chain`, `model SBOM`, `teacher model`, `synthetic data` | 權重、資料與衍生模型依賴治理 / governance of weights, data, and derived models | SPDX/CycloneDX manifest + Sigstore signing + OCI artifact registry + model registry + provenance ledger | license evidence, base-model ID, data provenance, signature, dependency graph |
| `Causal Data`, `active learning`, `autonomous lab` | 由干預產生高訊息密度資料 / intervention-driven high-information data | orchestrator + instrument adapters + Arrow/Parquet data layer + experiment registry + causal evaluation | intervention ID, instrument calibration, sample lineage, outcome distribution |
| `Realtime Voice`, `full duplex`, `WebRTC` | 低延遲、多模態連續 Agent / low-latency continuous multimodal Agent | WebRTC media path + streaming inference + VAD/turn detection + session state + trace correlation | latency budget by stage, packet/media telemetry, interruption test, state-handoff trace |
| `Non-Human Identity`, `Agent credentials`, `service account` | Agent 與工具身份、憑證與最小權限 / Agent identity, credentials, least privilege | SPIFFE/SPIRE + short-lived token broker + Vault/KMS + policy engine + audit trace | identity chain, token TTL, authorization decision, credential rotation test |
| `MCP`, `tool registry`, `Agent tools` | 模型與外部能力的標準化工具邊界 / standardized model-to-tool boundary | MCP SDK + typed tool schemas + OAuth 2.1 + policy proxy + sandbox + trace exporter | tool schema, auth scopes, argument validation, response provenance, replay trace |

## Trigger protocol / 觸發協議

**繁體中文**

1. 偵測 trigger 與同義詞。
2. 建立 `claim_id`，禁止只有自然語言段落。
3. 在四類資產中選擇 mapping：`code / llm-model / data / trajectory`。
4. 查驗 LICENSE；code license、model weights license、dataset license 必須分開。
5. 產出最小可執行驗證：command、config、test、trace 或 benchmark artifact。
6. 將候選庫送入 [`RANK.md`](RANK.md) 的 license gate 與五維評分。

**English**

1. Detect the trigger and aliases.
2. Allocate a stable `claim_id`; prose-only output is invalid.
3. Map the claim to `code / llm-model / data / trajectory` assets.
4. Verify licenses independently for code, model weights, and datasets.
5. Produce a minimum executable proof: command, config, test, trace, or benchmark artifact.
6. Send candidate repositories through the license gate and five-dimensional score in [`RANK.md`](RANK.md).
