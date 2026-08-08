# Citation and Technical Asset Mapping / 引用與技術資產 Mapping

## Goal / 目標

Convert Google Deep Research Markdown and citations into a stable evidence graph that connects each technical claim to commercially usable, non-forced-open assets across `code`, `llm-model`, `data`, and `trajectory`.

將 Google 深度研究的 Markdown 與 cite 轉為穩定證據圖，讓每個技術觀點可連到 `code / llm-model / data / trajectory` 技術資產。

## Stable claim block / 穩定觀點區塊

```yaml
claim_id: CLM-<note-id>-NNN
claim: "Atomic technical statement"
source_url: "stable source URL"
source_title: "source title"
source_locator: "section / timestamp / page / commit"
retrieved_at: "ISO-8601"
evidence_type: "quote | metric | code | experiment | incident | specification"
asset_targets: [code, llm-model, data, trajectory]
confidence: "high | medium | low"
```

Ephemeral UI citation tokens such as `turn...` are never the only stored reference. Preserve the stable URL, title, locator, retrieval date, and the factual payload.

## Asset mapping record / 資產映射記錄

```yaml
asset_id: AST-NNN
asset_type: code | llm-model | data | trajectory
name: "project/model/dataset/trace"
url: "canonical URL"
version_or_commit: "immutable version"
license_spdx: "Apache-2.0 / MIT / ..."
license_evidence_url: "official LICENSE or model/data license"
commercial_use: pass | review | hold
forced_open_obligation: none | weak | strong | custom
claim_ids: [CLM-...]
implementation_role: "runtime / serving / eval / data / security / observability"
verification_artifact: "test, benchmark, trace, or report path"
```

## Four-license separation / 四層授權分離

1. **Code**: repository source license.
2. **LLM model**: weights and model-use license.
3. **Data**: dataset terms, consent, privacy, redistribution.
4. **Trajectory**: prompts, tool calls, logs, secrets, user/customer data, and retention policy.

A permissive code license does not authorize model weights, datasets, or captured trajectories.

## Mapping workflow / Mapping 流程

1. Parse Markdown headings, links, footnotes, and cite markers.
2. Split atomic claims and allocate `claim_id`.
3. Resolve stable source URLs and locators.
4. Detect triggers using [`../CONTEXT.md`](../CONTEXT.md).
5. Discover candidate assets.
6. Verify license evidence from the official repository/model/dataset source.
7. Score candidates through [`../RANK.md`](../RANK.md).
8. Attach executable proof and trajectory.
9. Link the result back to the note.
