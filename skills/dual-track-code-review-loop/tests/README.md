# DTCR deterministic C0 suite

This directory owns only the replayable deterministic evidence for the merged C0 contract.

Run:

```bash
bash skills/dual-track-code-review-loop/tests/run-all.sh
```

The suite derives all current schemas and planted controls from committed C0 bytes, checks the frozen denominator in `../cases.json`, validates positive instances, requires every planted refusal to fail, and neutralizes each control's named schema guard(s) to prove the refusal is discriminating rather than failing for an unrelated reason.

Evidence ceiling:

```text
C0 schema/control replay       deterministic only
provider adapters              NOT_IMPLEMENTED
runtime/user/paid/legal        NOT_EXERCISED / HUMAN_ADMIT_REQUIRED
merge/release/production       HUMAN_ADMIT_REQUIRED
```

A local green run is not CI arrival. `Skill Suites` must execute this suite non-empty on the exact PR head before #537 can reach its terminal state.
