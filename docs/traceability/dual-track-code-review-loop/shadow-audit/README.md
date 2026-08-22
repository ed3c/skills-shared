# E1 (#525) independent Shadow audit records

This directory is the writable lease the Human-admitted 2026-08-22
reconciliation of issue `#525` assigned to the E1 independent Shadow lane. It
holds audit records only: findings and receipts. Nothing here is an
implementation write, a branch movement, or a merge authority, and no record
here promotes any lane.

## Records

| Subject | Artifacts | Verdict |
|---|---|---|
| `8d99f2d95f06e18c4725fd506535f39d939fe679` (tree `4725c00693a146eba3c5084fe3b81f9f9c3967b1`) | [`e1-findings-8d99f2d.md`](e1-findings-8d99f2d.md), [`e1-receipt-8d99f2d.json`](e1-receipt-8d99f2d.json) | `BLOCK` — five blockers F-01..F-05 |
| `723c30238cf00839e6935b5358c7f844baf2124b` (published head, 24/24 hosted checks green) | [`e1-verify-723c302.md`](e1-verify-723c302.md) | `BLOCK_REMAINS` at check time — F-01/F-02/F-05 RESOLVED with re-run knockouts; F-03/F-04 PARTIALLY on two traceability residuals (pre-rebuild SHA pointers; the excised locator republished verbatim inside the first-round findings record). Both residuals repaired in the same change unit that lands this row: SHA pointers repointed at the publication commits, and the locator redacted from both published audit records at tip. The historical blob on the remote (pushed in `6690a5d..723c302` before the redaction) can only be excised by a Human-authorized remote history rewrite — recorded as HUMAN_ADMIT_REQUIRED, not performed. |

The receipt is a wrapper document whose `closure_record` member validates
against `references/schemas/closure-record.schema.json` (the schema's closed
root cannot carry the session-identity and dissent sidecars — E1 finding F-08);
its siblings carry the session identity, the replayed denominator and the
dissent list. `lanes.independent_review` is `HUMAN_ADMIT_REQUIRED`: the
auditor ran as a fresh-context session but was dispatched by the wave's own
session into the wave's shared worktree, and recorded that adverse evidence
verbatim rather than self-certifying independence.

## Disposition of the BLOCK (Tech Lead, same day)

- F-01 (tree-sitter crash outside a git checkout) — repaired: `lane_live()`
  now types the absence `NOT_EXERCISED (no checkout)`, mirroring the scip
  guard; proven in-repo and on a clean `git archive` export.
- F-02 (semantic-context falsifier-identity collapse) — repaired: `refuses()`
  now verifies `refusal.falsifier` against the planted code, the required-
  falsifier accounting derives from codes actually raised, and a buf-style
  mechanised red proof was added; the Shadow's all-codes-collapsed knockout
  now turns the run red.
- F-03 (indexes contradict the tree; four closures unpacketed) — the closure
  packets and index reconciliation were in-flight during the audit and land in
  the same change unit as this file.
- F-04 (machine-local locator inside the committed `index.scip`) — repaired:
  `Metadata.project_root` neutralized via the adapter's own protobuf binding
  with digests rebound and the neutralization declared in the receipt; a leak
  scan over `adapters/scip/**` was added with a planted red proof. The leaky
  blob never left this machine: publication history was rebuilt so the pushed
  history does not contain it, and the original worktree branch is retained
  locally as forensic evidence.
- F-05 (concurrent writer during the audit) — acknowledged: the writer was the
  wave's own reconciliation. Recorded as process evidence on the independence
  question; the audit re-derived every index claim from committed blobs.
- F-06..F-11 — dispositioned in the wave's final packet (receipt rewrite for
  the R2 build note, `519→525` edge retyped `START_DEPENDENCY`, stale-prose
  sweep, quotation wording); F-12 resolves at the single push; F-13 recorded
  as the falsifier-proof standard for future lanes.

A post-repair verification record, when present, appears as its own row above.

| `f2e3edf8bf10cfa43ef7a0917de4bb8180af29b6` (final head) | [`e1-final-f2e3edf.md`](e1-final-f2e3edf.md), [`e1-receipt-f2e3edf.json`](e1-receipt-f2e3edf.json) | `ADMIT_FOR_DOWNSTREAM` — both re-verification residuals resolved; all five original blockers stay resolved; 2320-file bytes sweep finds zero real machine-local locators in DTCR-owned paths beyond the contract-mandated session-identity fields; out-of-scope locators in other programs' lanes flagged for their own owners |

`#525` closed 2026-08-22 on this final verdict. The independence property was
never machine-certified: the receipts carry the adverse evidence verbatim, and
the admission recorded in the issue's closing comment is the Human's standing
wave directive applied at the stated ceiling — a genuinely foreign-dispatch
second Shadow with a real dissent lane remains transferred to `#517`.
