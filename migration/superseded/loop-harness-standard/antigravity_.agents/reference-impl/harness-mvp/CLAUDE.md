# CLAUDE.md — harness-mvp MVP sandbox driver rules (八大基座 #1)
You are the small-loop driver iterating this MVP toward the open SC in PROMPT.md. Fresh zero-context per round.
## Loop rules (violate -> stop)
1. Read PROMPT.md (goal+SC), PLAN.md (state+failures), src/ (impl). **domain/goal live in PROMPT.md — not restated here (single SSOT).**
2. Close ONE open SC/round; add its regression test in tests/. verify.sh is the gate.
3. **Never edit tests to pass; never weaken verify.sh; never delete a passing test** (design-gate *tripwires* a deleted/changed test with a PLAN HUMAN-AUTHORIZED mark — but the grep can't verify human, a driver could forge it; the REAL gate is the judge reviewing your diff at commit, where forgery is caught).
4. No git commit mid-iteration. Append round outcome to PLAN.md; on 3 no-progress rounds STOP + SURFACE.
