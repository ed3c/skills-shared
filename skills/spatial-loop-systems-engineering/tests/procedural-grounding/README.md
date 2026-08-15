# Procedural grounding controls

This suite exercises `procedural-grounding-receipt/v1` with one valid receipt,
two input-error controls, and planted semantic defects.

The controls reject:

- mention-only substitution for required runtime execution;
- a negative control that was never run;
- unresolved assertion/probe obligations for critical novel procedures;
- unreviewed, unlicensed, script-bearing, or dynamically injected Skill sources;
- fork depth, token, fan-out, and no-progress budget violations;
- raw reasoning-trace payloads or low-quality/stale/authority-conflicted capsules;
- stale observations and execution claims based only on model prose;
- inflated coverage ratios and false model-internalization claims;
- `PASS` under an `UNKNOWN` runtime or an external/Human proof boundary.

A green suite proves the offline checker detects these contract violations. It
does not prove a live context fork, model independence, multimodal observer,
Claude Code/Codex execution, or cross-harness capability lift.
