# PROMPT — harness-mvp MVP goal contract (八大基座 #7)
## Mission
Self-build an L0+L2+L3+L4 minimal runnable agent-loop harness that embodies all SYNTHESIS-tested invariants; design SSOT anchor = SYNTHESIS-harness.md §6+§7.1.
## Success Criteria (verify.sh is the machine gate; each SC MUST have a regression test in tests/)
- [x] SC1 Minimal tracer bullet: one envelope enters the append-only ledger, L3/L4 gates inspect it, and a deterministic exit code is emitted.
- [x] SC2 L0 thin core runs only the step loop, event emission, tool-result capture, and deterministic handoff to gates; planning/sub-agent orchestration is absent from core.
- [x] SC3 L2 ledger writes the unified envelope as append-only JSONL with DAG `parentId`, `exec.result_snapshot`, budget, freshness, and handoff fields preserved.
- [x] SC4 Resume rebuilds iteration, budget, duplicate-signature state, and parent chain by reading JSONL only.
- [x] SC5 L3 duplicate detection uses `sig_with_result`, sliding-window `W >= N`, and per-signature early kill for repeated or interleaved loops.
- [x] SC6 L3 stop reason selection follows `budget > dup > max_iterations`, with max-iteration pre-flight behavior kept as fallback.
- [x] SC7 L2 record append is one serialized line per single write, with a regression case proving split writes are rejected or impossible through the public API.
- [x] SC8 L4 hard-blocks on deterministic evidence failures while LLM-judge style evidence remains warning-only and human-admitted at graduation.
## Dual-score graduation gate
- **Design score** (before build): every golden-path element of the design SSOT is either a done SC or a
  *designed cut* justified in PLAN.md — tracked in DESIGN-SCORE.md (a MISS cell = FAIL). NOT SYNTHESIS
  vibe-approval: the DESIGN-SCORE.md table makes it mechanically visible; graduation runs a fresh
  zero-context subagent design-judge over it (never fed the big-loop's rationale).
- **Impl score** (after build): verify.sh exit 0 (LIVE/RIP — real run).
- Graduate only when a human LAND-DECISION admits both scores green — THEN home the repo out of gitignored
  /prototype/ (remote or /repo/), else it is a single-machine orphan.
## Stop-loss
- 3 no-progress rounds OR un-revertible-to-green verify.sh → STOP, write failure trace to PLAN.md, SURFACE.
