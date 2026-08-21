# Repository Portfolio Prompt Foundation

Tracking: `#560`  
Bounded terminal: `PORTFOLIO_PROMPT_FOUNDATION_READY`

This path owns only the portable controller, role prompts, Codex project-agent
templates, manifest, deterministic prompt checker, and mutation selftest. It does not
own the later portfolio compiler, runtime execution, root routes, shared workflow,
bootstrap profile, PR convergence, merge, or Issue closure.

Data flow:

```text
controller + role prompts + Codex templates
→ manifest inventory
→ deterministic checker
→ positive + mutation selftest
→ compiler/runtime successor
```

Evidence ceiling: deterministic prompt packaging only.
