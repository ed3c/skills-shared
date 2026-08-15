# RANK.md — 開源技術資產排名 / Open-Source Asset Ranking

> 排名是決策入口，不是跨層級的絕對優劣。Serving engine、workflow runtime、telemetry 與 model library 必須先按 stack role 比較，再看總分。
>
> The rank is a triage surface, not a universal comparison across layers. Compare serving engines, workflow runtimes, telemetry systems, and model libraries within their stack role before using the overall score.

## License gate / 授權閘門

**Default allow / 預設通過**：`Apache-2.0`, `MIT`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`。  
**Manual review / 人工審查**：`MPL-2.0`, custom community model licenses, mixed-license repositories。  
**Default hold / 預設暫停**：`GPL`, `AGPL`, `SSPL`, `BSL`, `Commons Clause`, `Elastic-2.0`, research-only, non-commercial, no-derivatives。

`code license != model weights license != dataset license != trajectory/data consent`。四者不可互相代替。

## Scoring / 評分

每項 0–20，總分 100：

1. **Hackathon MVP** — install speed, examples, local path, demo latency.
2. **Commercial** — integration surface, vendor neutrality, supportability, monetizable extension points.
3. **Research** — reproducibility, experimental control, benchmark fit, extensibility.
4. **Production use** — reliability, security controls, observability, scale, upgrade discipline.
5. **Stack compatibility** — fit with Python, Kubernetes, cloud, OpenTelemetry, model/data/trajectory pipelines.

## Initial verified candidates / 初始已驗證候選

| Rank | Asset | Role | License | MVP | Commercial | Research | Production | Compatibility | Total | Status |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | [Hugging Face Transformers](https://github.com/huggingface/transformers) | model library | Apache-2.0 | 20 | 19 | 20 | 17 | 20 | **96** | adopt-candidate |
| 2 | [vLLM](https://github.com/vllm-project/vllm) | inference serving | Apache-2.0 | 17 | 20 | 19 | 19 | 19 | **94** | adopt-candidate |
| 3 | [LangGraph](https://github.com/langchain-ai/langgraph) | Agent state/runtime | MIT | 19 | 19 | 18 | 18 | 19 | **93** | adopt-candidate |
| 4 | [OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector) | traces/metrics/logs | Apache-2.0 | 15 | 20 | 17 | 20 | 20 | **92** | adopt-candidate |
| 5 | [MLflow](https://github.com/mlflow/mlflow) | experiment/model registry | Apache-2.0 | 18 | 19 | 19 | 18 | 18 | **92** | adopt-candidate |
| 6 | [SGLang](https://github.com/sgl-project/sglang) | inference serving/programming | Apache-2.0 | 18 | 18 | 20 | 17 | 18 | **91** | test-candidate |
| 7 | [Temporal](https://github.com/temporalio/temporal) | durable workflow runtime | MIT | 14 | 20 | 15 | 20 | 19 | **88** | production-candidate |
| 8 | [Firecracker](https://github.com/firecracker-microvm/firecracker) | microVM isolation | Apache-2.0 | 10 | 18 | 17 | 20 | 15 | **80** | security-specialist |

License evidence was read from each repository's official `LICENSE`/`LICENSE.txt` file on 2026-08-08. Scores are repository-fit judgments for this knowledge system, not vendor claims.

## New discovery row / 新發現模板

| Discovered at | Asset | URL | Role | Code license | Model/data license | MVP | Commercial | Research | Production | Compatibility | Total | Evidence note | Decision |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| YYYY-MM-DD | name | URL | role | SPDX/TBD | SPDX/TBD | 0 | 0 | 0 | 0 | 0 | 0 | note path + claim IDs | test/hold/adopt/reject |

## Ranking update protocol / 更新協議

**繁體中文**：先通過 license gate；再建立最小可執行實驗；分數必須引用 benchmark、issue/commit、production evidence 或本庫 trajectory。沒有 evidence 的分數標記 `provisional`。  
**English**: Pass the license gate first, then run a minimum executable experiment. Scores must cite a benchmark, issue/commit, production evidence, or a trajectory stored in this repository. Scores without evidence are `provisional`.
