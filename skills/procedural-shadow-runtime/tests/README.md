# Tests

Deterministic controls:

```bash
python3 verify.py
python3 verify_agent_architecture_eval.py
python3 verify_ecommerce_eval.py
python3 verify_meta_eval.py
```

The suites include:

- valid runtime and architecture receipts;
- a fully observed Vibe-Coder receipt that closes at a low score;
- missing, duplicate, contradictory, prose-only, digest, authority, and score-tampering mutations;
- an executable e-commerce reference adapter;
- an unsafe adapter that attempts to bypass the high-value HITL gate;
- malformed and absent input controls.

Static fixture success does not prove live Claude, Codex, external registry, browser/device, or production behavior.
