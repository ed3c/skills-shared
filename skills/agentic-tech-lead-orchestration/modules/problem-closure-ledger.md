# Problem closure ledger

A GitHub issue, pull request, commit, or document link is evidence routing, not proof that the source problem is closed.

## Source-to-closure route

```text
source identity + exact location
  -> problem_id
  -> applicability
  -> repo subject (repo/commit/tree)
  -> task nodes
  -> GitHub issue nodes
  -> implementation evidence
  -> verification evidence lanes
  -> Shadow verdict
  -> residual gaps
  -> closure state
```

The ledger denominator retains unresolved, superseded, and `NOT_APPLICABLE` claims. Duplicate IDs and missing source locations fail closed.

## Closure vocabulary

- `OPEN`: no admitted implementation evidence yet;
- `PARTIAL`: implementation exists but residual gaps or Shadow failure/partial verdict remain;
- `IMPLEMENTED_UNVERIFIED`: implementation exists but admitted verification is absent/incomplete;
- `VERIFIED_LOCAL`: local or CI verification plus Shadow PASS, with no residual gaps;
- `VERIFIED_LIVE`: provider-live verification plus Shadow PASS, with no residual gaps;
- `NOT_APPLICABLE`: explicitly justified as outside the repository contract;
- `HUMAN_ADMIT_REQUIRED`: policy says human authority is still required.

Issue closure and PR merge are not verification lanes. A merge may be recorded as implementation provenance, but cannot promote a claim to `VERIFIED_LIVE`.

## Evidence lanes

Verification lanes remain explicit: `LOCAL`, `CI`, `PROVIDER_LIVE`, `HUMAN`, and `RELEASE`. Navigation links, source prose, model summaries, issue labels, or UI status are not verification evidence.

## Implementation

`../scripts/check_problem_closure.py` validates the full problem denominator and independently recomputes every declared closure state. Declared state must equal recomputed state or the checker rejects the ledger as closure laundering/drift.

`../tests/problem_closure_selftest.py` covers local/live/partial/human-positive cases and mutations for missing source location, invalid merge-as-verification, local-to-live promotion, residual-gap laundering, unjustified `NOT_APPLICABLE`, and duplicate problem IDs.

Deterministic checker PASS proves only ledger consistency. Real article/PDF/consumer claims can legitimately remain `OPEN`, `PARTIAL`, or `HUMAN_ADMIT_REQUIRED` until stronger evidence exists.
