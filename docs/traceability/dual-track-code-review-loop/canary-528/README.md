# #528 consumer canary — bounded evidence set (2026-08-22)

One real bounded consumer canary of the DTCR loop, run by a Worker session
against `bettor-arena` (the four-repository system's designated
Integration/Acceptance Plane; selection admitted under the Human goal
directives of 2026-08-22 — publication/merge of the consumer change remains
`HUMAN_ADMIT_REQUIRED`).

## Subjects

```text
consumer origin      /Users/neon/bettor-arena (local clone; never pushed, no remote contacted)
rollback subject     13ff9840fc5683b33670fa191591035bc96292dc
canary commit        8a21426751c0fec3c99450cdb00294e843a9d950 (clone-local only)
method plane         skills/dual-track-code-review-loop at this repository's wave head (read-only)
```

## What ran

- **Violation** `DTCR-VC-001`: two delivery operators import the gates lane's
  private `_gate_common` through injected `sys.path`
  (`scripts/delivery_status.py:33-34`, `scripts/delivery_sync.py:31-32`),
  against `docs/architecture/DOMAIN_DECOUPLING.md:199-206` and
  `_gate_common.py`'s own declared consumer set. Surfaced by sqlite-ledger
  IMPORTS edges (8 → 6 after the fix; the removed 2 are exactly the
  `SYS_PATH_INJECTION ∧ private_target ∧ crosses_directory` rows).
- **Fix**: +18/−8 in the consumer clone; each operator resolves its root from
  its own layer. Gates lane untouched.
- **Oracle, three runs**: BEFORE exit 0, AFTER exit 0, deliberately broken
  exit 1 (red proven). A first, vacuous oracle was caught by the planted
  control and rebuilt (`oracle/red-controls.txt`). A second planted control's
  measured blindness is recorded as the coverage ceiling.
- **Fact planes**: tree-sitter EXERCISED (provider-pinned receipts, before and
  after), sqlite-ledger EXERCISED (canary-local AST scan declared as the
  symbol producer, `PARTIAL_LOWER_BOUND`), semantic-context KEYWORD EXERCISED
  (`NON_AUTHORITATIVE_CANDIDATE` rows only), buf NOT_APPLICABLE (no contract
  surface), scip NOT_EXERCISED — the attempt crashed uncontracted, defect
  filed as `#595` (`facts/scip-live.stderr`). Note: that crash and #595 were
  against the adapter implementation this canary ran, which has since been
  superseded by the canonical `adapters/scip/` landed via PR #604; the
  canonical adapter has no pyrightconfig.json dependency, and the fact-plane
  receipts under `facts/` bind the superseded implementation's run.
- **R1 protocol**: `compile_r1.py` compile + check exit 0, terminal `BLOCKED`
  (`SEMANTIC_INDEX_NOT_REBUILT`, `TYPECHECK_NOT_RUN`); the change was applied
  by hand per the compiler's own refusal — `applied_on_real_codebase` stays
  compiler-pinned false. 20/20 artifacts validate against the frozen schemas.
  Compiler gate holes found on first real use are filed as `#596`.

## Evidence ceiling

The receipt is `dtcr/consumer-canary-receipt/v0-draft` — no frozen in-tree
receipt type can carry a canary result yet, and the receipt says so rather
than forcing a schema it does not satisfy. Exit tokens are `NOT_CLAIMED`.
Residuals: R2 real migration NOT_EXERCISED, independent Shadow NOT_EXERCISED,
scip fact plane NOT_EXERCISED (#595), vector lane BLOCKED_ON_PROVIDER,
typecheck lane NOT_RUN, merge/publication/upstream-admission/legal
HUMAN_ADMIT_REQUIRED.

## Files here

`canary-receipt.json` is the binding artifact (its sha256 is recorded in
`canary-receipt.sha256`, regenerated whenever the receipt's evidence paths are
re-rooted); `artifact-validation.txt`, `r1/`, `oracle/`, `facts/`,
`semantic/` and `cross-module-imports.json` are its named evidence, and
`check_paths.py` asserts every relative evidence path the receipt cites
resolves against the committed set. The full working set (consumer clone,
sqlite databases, raw observation dumps, runner scripts) lived in the Worker
session's scratch area and is NOT reproducible: the canary commit
`8a214267…` was never pushed and exists only in that clone — only the durable
core committed here survives.
