# Problem closure ledger

A GitHub issue, pull request, workflow, document link, or generated projection is evidence routing, not proof that the source problem is closed.

## Source-to-closure route

```text
frozen source manifest + digest
  → complete problem denominator
  → problem_id + exact source location + claim digest
  → applicability
  → exact repo commit/tree
  → task / DAG / issue lineage
  → session / attempt / portable worktree identity
  → current + historical implementation evidence
  → exact-subject verification evidence + matching receipts
  → Shadow verdict
  → residual gaps
  → recomputed closure state
```

The denominator is explicit and content-bound. Deleting a problem row without changing the frozen denominator turns red. A changed source claim, source location, or source manifest digest also turns red.

## Closure vocabulary

- `OPEN`: no current implementation evidence;
- `PARTIAL`: residual gaps, Shadow dissent, or a superseded problem remains;
- `IMPLEMENTED_UNVERIFIED`: current implementation exists but verification/Shadow is incomplete;
- `VERIFIED_LOCAL`: exact-subject LOCAL/CI evidence plus Shadow PASS and no residual gaps;
- `VERIFIED_LIVE`: exact-subject PROVIDER_LIVE evidence plus Shadow PASS and no residual gaps;
- `NOT_APPLICABLE`: explicit rationale says the claim is outside repository scope;
- `HUMAN_ADMIT_REQUIRED`: the declared policy still requires Human evidence.

`SUPERSEDED` is applicability, not a terminal success. It must reference another denominator problem and recomputes to `PARTIAL`, preserving the historical item.

## Exact-subject and portability laws

Repository commit/tree identities are full 40-hex Git subjects. Verification evidence and matching receipts must bind the current repo subject. Historical implementation evidence can remain in the ledger, but only `CURRENT` evidence for the exact current subject counts as implementation.

The portable ledger stores a worktree identity, not a machine-local filesystem path. Runtime-specific physical paths belong in consumer/runtime receipts.

## Evidence lanes

`LOCAL`, `CI`, `PROVIDER_LIVE`, `HUMAN`, and `RELEASE` remain distinct. Issue close, PR merge, labels, UI status, source prose, navigation URLs, or generated Markdown cannot substitute for a verification receipt.

## Implementation

`../scripts/check_problem_closure.py` validates the frozen denominator and independently recomputes every closure state. `../scripts/render_problem_closure.py` creates a deterministic human projection only after the ledger passes.

`../tests/problem_closure_selftest.py` covers positive closure states and planted denominator loss, source drift, stale-subject, supersession, evidence-laundering, machine-local-path, duplicate and extra-field mutations.

Deterministic checker PASS proves only the exact ledger contract. Real article/PDF/consumer claims can remain `OPEN`, `PARTIAL`, or `HUMAN_ADMIT_REQUIRED` until stronger external evidence exists.
