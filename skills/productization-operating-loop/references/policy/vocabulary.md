# POL-P policy-lane vocabulary

One page, no more: `pol/policy-lane/v1` is a leaf record the productization-program's
`policy` lane (`pol/productization-program/v1`) points at. It never redefines that
program's `lane_state`, `rung_name`, `receipt.kind` or `authority` vocabulary; it
adds one closed vocabulary of its own for tracking a single official source over
time.

| Term | Meaning | Producer | Consumer | Never becomes |
|---|---|---|---|---|
| `policy_ref` | The one canonical URL this record tracks, plus the evidence class of that URL claim itself. | The worker who located the source. | The next revalidation pass; the program's `policy` lane reader. | A rights or legal statement — it is a source identity only. |
| `observed_revision` / `policy_receipt.kind` | What was actually read at that URL and how: `POLICY_URL_VISITED` (the URL resolved) vs. `INDEPENDENT_POLICY_READBACK` (the content was read and diffed). | The revalidation worker. | The `terminal` and `decision` rules, which only accept the readback kind as evidence of currency. | Interchangeable — a visit is never filed as a readback. |
| `evidence_class` (`HYPOTHESIS` / `SOURCE_STATEMENT` / `VERIFIED_READBACK`) | How sure this record is that a free-text value is true: a guess, a claim the source makes, or a claim independently read back. | Whoever fills in `evidenced_string` fields (`changed_section`, `semantic_delta`, `capability`, `rights_note`, `adapter`). | Human Admit and any downstream capability/rights review deciding how much weight to put on the note. | A verdict — `evidence_class` says how a claim was obtained, never whether it is legally or commercially correct. |
| `change` | Whether this revalidation pass detected a semantic difference from the prior observation, and if so, where and what. | The revalidation worker, comparing two `observed_revision` values. | `affected_impact.capability_review` and the `decision` pair, both gated on `changed`. | A capability or rights decision by itself — `change` only says something moved. |
| `affected_impact.capability_review` | Whether the capability/rights/adapter surface touched by a detected change has actually been looked at. | The worker or reviewer who reads the change against the affected surface. | The program's `technical`/`rights` lanes deciding whether retest is owed. | An admission that the capability is now cleared — `REVIEWED` means looked at, not approved. |
| `decision.previous_decision` / `decision.new_decision` | The prior and current terminal-plus-receipt pair, kept side by side. | The revalidation worker. | Anyone auditing whether a change silently reused old evidence. | A single mutable "current decision" field — both subjects are preserved, never overwritten in place. |
| `required_tests_or_reopen` | What must happen before this change is considered handled: a named test suite, a named issue reopen, or nothing. | The revalidation worker, from `affected_impact`. | The team or process that owns the named test/issue ref. | A closure claim — this field routes work, it does not certify the work is done. |
| `terminal` | `CURRENT \| STALE \| SUPERSEDED \| REVOKED \| BLOCKED` — this record's own status, distinct from the program's `lane_state`. | The revalidation pass. | The program's `policy` lane, which reads this as its evidence. | `MERGED`/`RELEASED` or any operation a person performs — there is no such value here, matching `lane_state`'s own omission. |
| `authority` | Four constants, all `false`: `rights_admission`, `legal_clearance`, `platform_feature_grants_rights`, `affected_capability_admission`. | Fixed by the schema; no instance sets any of them. | Human Admit, legal, and rights owners, who this record routes to but never substitutes for. | `true` — a field that can be set to true is a field somebody eventually sets to true, so none of them can be. |

Evidence boundary this vocabulary respects: policy provenance and revalidation
routing only. No demand/PMF/user/payment truth and no product choice are
represented here — those live in the other eleven lanes of
`pol/productization-program/v1`. No rights, legal or platform-approval verdict
is representable here either — that is what the four `authority` constants and
the `x-refusal-controls` in `policy-lane.schema.json` exist to keep out.
