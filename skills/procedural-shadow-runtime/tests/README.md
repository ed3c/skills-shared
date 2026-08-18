# Tests

Deterministic controls. `run-all.sh` discovers every `tests/verify*.py`, so it is
the authority on what runs; this list was a second one and had already drifted.

```bash
bash run-all.sh
python3 verify_refactor_ab.py   # frozen refactor treatments (issue #350)
```

`verify_refactor_ab.py` is the entrypoint
`skills/skill-refactor-proof-loop/references/golden-proof-registry.json` names
for this Skill, and `run-all.sh` refuses to pass if the discovery loop stops
finding it.

The suites include:

- valid runtime and architecture receipts;
- a fully observed Vibe-Coder receipt that closes at a low score;
- missing, duplicate, contradictory, prose-only, digest, authority, and score-tampering mutations;
- an executable e-commerce reference adapter;
- an unsafe adapter that attempts to bypass the high-value HITL gate;
- malformed and absent input controls.

Static fixture success does not prove live Claude, Codex, external registry, browser/device, or production behavior.
