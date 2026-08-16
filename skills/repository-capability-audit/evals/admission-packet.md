# Admission packet — repository-capability-audit (#237)

Convergence packet for the Epic #221 line. Every number in it is a pointer to a file in this Skill, not a transcription, so the packet cannot claim more than the tree holds.

## Requested decision

```text
requested tier    TIER A — DETERMINISTIC_CORE_EXPERIMENTAL
not requested     TIER B (live Agent), TIER C (production-like)
authority         Human Admit; this packet is machine eligibility, not admission
```

Failing to earn B or C does not block A. A is requested on its own evidence and is labelled as such everywhere it appears.

## Stack state

The implementation lineage (#196 → #198 / PR #201 → #202 / PR #203) is merged; no PR in this line is open. The reconciliation #237 asks for is therefore a reconciliation of merged subjects, not of an open stack:

```text
PR #201  merged   deterministic trimmed Skill and procedure ablation
PR #203  merged   held-out Agent A/B receipt harness
#224     closed   held-out corpus and independent evaluator
#226     closed   two real Agent harnesses bound to the receipt contract
```

## Evidence, by layer

| Layer | Subject | State | Where |
|---|---|---|---|
| A | 15 deterministic cases, 13 retained rules | PASS, each rule with a deciding delta | `evals/expected/effectiveness.json` |
| A | source contribution, overlap-aware | published | `evals/live-source-contribution.md` |
| A | GitHub-hosted execution of this suite | PASS at an exact head | `evals/live-evidence-state.json` → `github_hosted_execution` |
| A | replayable exact-head artifact | added by this change; receipt on #222 | `.github/workflows/skill-suites.yml` |
| B | held-out A/B matrix (#228) | INSUFFICIENT_SAMPLE — 31 of 90 sessions | `evals/live-evidence-state.json` |
| B | per-rule ablation (#230) | NOT_EXERCISED — 0 of 26 required pairs | `evals/live-evidence-state.json` |
| B | source contribution, live (#233) | LAYER_A_ONLY | `evals/live-source-contribution.json` |
| C | consumer canaries (#235) | NOT_EXERCISED — 0 canaries, 0 windows | `evals/live-evidence-state.json` |

## Candidate and rollback subjects

```text
candidate   skills/repository-capability-audit at the admitted commit
rollback    the immediately preceding commit of the same path
```

They are distinct commits by construction; a rollback target equal to the candidate is the failure #235 names, and it does not apply here because no promotion beyond A is requested.

## Explicit non-claims

- deterministic fixture pass is not live Agent effectiveness;
- one repository is not held-out generalization, and one model or harness is not portable support;
- a missing arm is not a low score: the 59 absent sessions of #228 are absent;
- on the one quality metric that varied within arms, the trimmed candidate ranked worst of three at n=4-5; that is underpowered and is recorded because it is the opposite of the intended effect, not as a finding of harm;
- no per-rule or per-source live causal claim is made;
- no production correctness, operational stability, or rollback claim is made.

## Security, privacy, provider egress

No change to repository visibility, ownership, access rights, license, billing, Actions permissions, secrets, or provider egress. The held-out corpus is three public repositories; no private data leaves the repository. Live Agent lanes that would spend provider budget remain unexecuted.

## Expiry and revalidation

A Tier A admission expires when the Skill core or module digests move, when `evals/contract.json` changes its retained set, or when the suite stops executing on a GitHub-hosted runner at the then-current head. Layer B and C states expire on any identity movement listed in `modules/measurement-limits.md`.

## Human Admit record

```text
decision     PENDING
approver     PENDING
scope        PENDING
conditions   PENDING
expiry       PENDING
```

Terminal outcomes available: `ADMITTED_TIER_A`, `ADMITTED_TIER_B`, `ADMITTED_TIER_C`, `HOLD_FOR_MORE_EVIDENCE`, `REJECTED`, `SUPERSEDED`, `REVOKED`. Creating or completing #237 does not itself authorize merge or release.
