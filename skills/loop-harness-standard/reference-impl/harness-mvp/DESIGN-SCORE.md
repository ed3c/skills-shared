# DESIGN-SCORE — harness-mvp (Fable-5: design score mechanized, not SYNTHESIS vibe-approval)
Fill from the design SSOT's golden path. A MISS cell = design-score FAIL. Graduation runs a fresh
zero-context subagent design-judge over THIS table (not fed the big-loop's rationale).

| golden-path element | status: done SC-id | designed-cut @ PLAN line | MISS |
|---|---|---|---|
| Self-build L0 thin runtime core: a `while(task_not_complete)` loop that only manages tool execution state, retry, and event streaming; it must not bake in Plan Mode or sub-agent orchestration. Anchor: SYNTHESIS-harness.md §1 L0:36-43; §6:280-282 | SC2 |  |  |
| L0 accepts a dispatch task packet plus L2 ledger pointer, emits event stream and tool execution results, and hands control back to deterministic code after each step. Anchor: SYNTHESIS-harness.md §1 L0:38-40; §6:282 | SC1, SC2 |  |  |
| L2 ledger is append-only JSONL with DAG `parentId` lineage and external URI/hash pointers for large objects, not rewritten free text. Anchor: SYNTHESIS-harness.md §1 L2:56-69; §6:292-305 | SC3 |  |  |
| Unified envelope records `id`, `parentId`, `loop_layer`, `task_ref`, `event`, `exec`, `handoff`, `budget`, and `freshness` as the cross-layer SSOT. Anchor: SYNTHESIS-harness.md §6:292-303; §7:315-317 | SC1, SC3 |  |  |
| Envelope `exec` includes a separate `result_snapshot` field so result-hash signatures do not overload `error_snapshot`. Anchor: SYNTHESIS-harness.md §6:299; §7 UK3:323 | SC3 |  |  |
| Every JSONL record is serialized as one complete line including newline and appended with a single write; split writes are forbidden. Anchor: SYNTHESIS-harness.md §7.1 UK6:335 | SC7 |  |  |
| Resume reconstructs state by purely reading JSONL from disk: iteration, tokens, duplicate streak, and `parentId` chain must be rebuilt without hidden in-memory state. Anchor: SYNTHESIS-harness.md §7 UK4:325 | SC4 |  |  |
| Nonzero `exit_code` with no handled handoff automatically blocks through L3/L4 instead of continuing silently. Anchor: SYNTHESIS-harness.md §1 L2:64; §6:305 | SC1, SC8 |  |  |
| L3 hard limits start from configurable `max_iterations`, `maxMessages`, and `maxAttempts`; threshold values must be calibrated in real MVP iteration rather than treated as proven constants. Anchor: SYNTHESIS-harness.md §6:284-287; §6:309 | SC6 |  |  |
| L3 duplicate detection defaults to `sig_with_result` so the signature covers tool, args, and result hash; no-result signatures are not the default. Anchor: SYNTHESIS-harness.md §7 UK1:319 | SC5 |  |  |
| L3 duplicate kill is per signature: any one signature reaching the configured repeat threshold stops the loop, including interleaved loops. Anchor: SYNTHESIS-harness.md §7 UK1:319; §7.1 UK5:333 | SC5 |  |  |
| L3 sliding window size `W` must be greater than or equal to the expected maximum interleaving arity `N`; conservative defaults may use `max_tools` or `8+`. Anchor: SYNTHESIS-harness.md §7.1 UK5:333 | SC5 |  |  |
| L3 budget ladder is configurable and evaluated as a real stop gate input, not a hard-coded copied vendor number. Anchor: SYNTHESIS-harness.md §6:288-309; §7 UK2:321 | SC6 |  |  |
| When multiple stop gates are satisfied after a run, the post-facto reason priority is `budget > dup > max_iterations`; `max_iterations` remains the pre-flight fallback. Anchor: SYNTHESIS-harness.md §7 UK2:321 | SC6 |  |  |
| L4 hard gate blocks on deterministic evidence such as `exit_code`, lint, or type results; LLM judge output is warning-only, and graduation or merge remains human-admitted. Anchor: SYNTHESIS-harness.md §1 L4:83-94; §6:290 | SC8 |  |  |
| L4 keeps Generator-Evaluator separation with zero shared context, a heterogeneous Validator, and hidden 80/20-style anti-cheat tests where applicable. Anchor: SYNTHESIS-harness.md §1 L4:87-93; §6:290. NOTE (Opus 核): 「零共享上下文」是本 MVP 的**設計選擇**（比 Factory 嚴格），非已證業界慣例——§5 #4 D1 裁決半反證該事實宣稱（Factory validators 讀 trajectory）；勿在文檔宣稱「業界皆然」 |  | PLAN DC-5 |  |
| Control flow belongs to deterministic code in L0/L3/L4; the LLM only emits structured choices at L1 routing and L0 tool choice. Anchor: SYNTHESIS-harness.md §6:282 | SC2 |  |  |
| Context-water and other numeric thresholds stay configurable; no single cluster number is treated as settled because the threshold evidence conflicts. Anchor: SYNTHESIS-harness.md §4:233-236; §6:287-309 | SC6 (config); ctx-water cut | PLAN DC-6 |  |
| Designed-cut candidate: L1 gateway is not self-built in this MVP; external LiteLLM/Bifrost-style gateway adoption is deferred and reason must be recorded in PLAN. Anchor: SYNTHESIS-harness.md §2:146-148; §6:280 |  | PLAN DC-1 |  |
| Designed-cut candidate: L6 sandbox is not self-built in this MVP; external E2B/gVisor/Tetragon-style sandbox adoption is deferred and reason must be recorded in PLAN. Anchor: SYNTHESIS-harness.md §2:163-166; §6:280 |  | PLAN DC-2 |  |
| Designed-cut candidate: L5 concurrent-writer lock repo is not self-built in this MVP; grite/Switchman-style lock adoption is deferred because current scope has no concurrent writer, and reason must be recorded in PLAN. Anchor: SYNTHESIS-harness.md §2:155-156; §2:175; §6:280; §7.1 UK6:335 |  | PLAN DC-3 |  |
| Designed-cut candidate: L7 fold-in/system-loop is not self-built in this MVP; reuse antigravity `fold-in` later with human admit, and reason must be recorded in PLAN. Anchor: SYNTHESIS-harness.md §1 L7:118-123; §6:280 |  | PLAN DC-4 |  |
