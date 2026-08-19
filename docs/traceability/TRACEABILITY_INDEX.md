# Traceability index — document routing and proof-carrying delivery

## Trace model

```text
source / incident
→ repository decision
→ parent issue
→ molecular issue
→ sibling / true-child / convergence PR
→ eval + negative controls
→ immutable or exact GitHub-read subject
→ receipt / current evidence state
→ Human Admit
```

Mutable open PR heads are read from GitHub immediately before decision use. This document records immutable merged/rejected/integration ancestors and current observed snapshots, but never self-embeds its own mutable final head. A convergence ancestry edge proves consumed bytes, not admission of an unmerged sibling.

## Proof-carrying Skill refactor Stack

Detailed human trace: [`SKILL_REFACTOR_PROOF_STACK.md`](SKILL_REFACTOR_PROOF_STACK.md). Machine authority remains:

```text
skills/skill-refactor-proof-loop/references/refactor-proof-stack.json
skills/skill-refactor-proof-loop/references/refactor-proof-stack.schema.json
skills/skill-refactor-proof-loop/scripts/check_refactor_proof_stack.py
```

```text
#307/#309 → PR #308  root causal repair
└─ #312 → PR #315    production-shaped hermetic proof
   └─ #319 → PR #323 portable proof contract/registry
      └─ #320 → PR #324 Agent routes + directory State Machines/DAG
         └─ #321 → PR #325 Molecular convergence/index
            └─ #322  process follow-up/adoption audit after admission
```

#231 scheduler-live, #232 independent Shadow/global objective, #234 real Git Town/dual-forge delivery and #256 exact-subject adapter evidence remain independent evidence/process lanes, not fake Git children. The cross-Skill adoption ledger and generated audit remain canonical for per-Skill migration state.

## Codex SDK Tech Lead control plane — current epoch

Canonical programme trace: [`CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`](CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md). Portable law remains `skills/agentic-tech-lead-orchestration/SKILL.md`.

Current common base observed for this sibling epoch:

```text
main@4ca9417b1da5ff32f1d4d3e7af64a15908749024
```

| Atom | Issue / PR | Relation | Current selected exact head | Mechanism state | Remaining ceiling |
|---|---|---|---|---|---|
| Codex SDK controller/session | `#375 / #451` | `SIBLING / UNMERGED CANDIDATE` | `86f9e8d940b76cb71b713c098ff09cb68eb4e0c1` | exact worktree HEAD/tree/clean preflight + post-turn path-lease readback; selftest `4/14` | live SDK `NOT_EXERCISED`; independent source/diff/test acceptance still required |
| GitHub Issue DAG projection | `#376 / #452` | `SIBLING / UNMERGED CANDIDATE` | `426fb6f6f548f71572d4402e73e0b05ecf6f8aa8` | completion-edge projection + repo/default-branch/visibility + issue-state + closing-PR-reference preflight; selftest `6/17` | live mutation/readback `NOT_EXERCISED`; generic development-link ownership beyond closing refs residual |
| Herdr observer | `#377 / #456` | `SIBLING / UNMERGED CANDIDATE` | `6a2ebcbe87078cecaf67f82f3c9c10643bcc9123` | exact Git/worktree/process/session identity + PID-start/freshness/liveness + cleanup/residue; selftest `4/18` | live Herdr `NOT_EXERCISED`; `DONE_CANDIDATE` remains advisory |
| Problem closure | `#378 / #457` | `SIBLING / UNMERGED CANDIDATE` | `ac5ddc0287eb4e4156a7c7eef178b7be8bbd1d34` | frozen denominator/source manifest + exact repo/evidence subjects + supersession validation; selftest `6/22` | real source/provider closure `EVIDENCE_DEPENDENT` |
| Documentation foundation | `#379 refs / #380` | `DOCUMENTATION SIBLING` | `7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5` | original traceability design bytes | navigation only |
| Shared convergence | `#379 / #455` | `CONVERGENCE CANDIDATE` | read live from GitHub | selected sibling bytes + shared tests/routes/Shadow/Git Town/trace | final exact head must pass full hosted denominator; sibling/merge admission remains Human-owned |

### Current dependency integration

The repaired Herdr candidate is consumed by this immutable convergence ancestor:

```text
fc40cf833609328ded0141dd8d9629c9a727a159
parents:
  d52ab2aad8e20be0c738e77356f75633813ad444  prior #455 route/index head
  6a2ebcbe87078cecaf67f82f3c9c10643bcc9123  repaired #456 candidate
```

The rejected predecessor integration remains visible:

```text
ed852502437570c7c86bae12c07c16a3f5d37ea8
parents:
  c306b3b4cea797f5f4d1323f8ec7fcd94a94f3ec  prior #455 convergence head
  23b03826b1bf8fe66bd731716466a9349d3242d6  corrupted #456 candidate
  ac5ddc0287eb4e4156a7c7eef178b7be8bbd1d34  #457 selected candidate
```

`ed852502...` is `HISTORICAL / REJECTED_BY_SHARED_SUITE`: the shared ATL gate reached the Herdr selftest and failed Python import on non-printable source corruption. Its predecessor green evidence is not reused.

Before these checkpoints, #451/#452 hardening had already been integrated through:

```text
5d21ecab137cb26586ef1636dc279ee29733e913
parents:
  35874af7a6d04783983b05c8f1b1e402471b4451  prior #455 epoch
  86f9e8d940b76cb71b713c098ff09cb68eb4e0c1  #451 selected head
  426fb6f6f548f71572d4402e73e0b05ecf6f8aa8  #452 selected head
```

The earlier `35874af7...` hosted-green/Shadow result is `HISTORICAL` because selected parent heads moved. It is not reused as current evidence.

### Historical convergence and rejected candidates

```text
c0f6979f80038394350aea724c598c8dba5ac338  epoch-1 union
  historical #451 339ae874...
  historical #452 b5295df6...
  #453 5b6e58d1...
  #454 32c5425d...

af427a13a7096df91d74a48c0a4ca6ce3f3e2ac9  epoch-1 + PR #380 docs
35874af7a6d04783983b05c8f1b1e402471b4451  historical hosted-green convergence
ed852502437570c7c86bae12c07c16a3f5d37ea8  rejected corrupted-Herdr integration

#444 → #451
#445 → #452
#446 → #453 → #456
#447 → #454 → #457
```

#446/#447 are rejected provenance candidates. #453/#454 are provenance-correct replacements later closed unmerged. The first #456 v3 head is retained as a rejected source-corruption subject; current #456 is `6a2ebcbe...`. All remain denominator history, not alternate merge candidates.

### Current convergence gate

The exact final #455 head must execute, not merely contain:

```text
6 Draft-2020-12 control-plane schemas
Codex selftest        4 positive / 14 mutations
GitHub DAG selftest   6 positive / 17 mutations
Herdr selftest        4 positive / 18 mutations
closure selftest      6 positive / 22 mutations
problem-closure example + checker + non-authority Markdown projection
existing ATL suite
```

At repaired ancestor `fc40cf83...`, synchronize-triggered hosted gates are:

```text
Skill Suites                         PASS
Shared Skills Infra                  PASS
Git Town Stacked PR Worker           PASS
```

The ATL log explicitly records all four selected control-plane selftests PASS at the denominators above. The final documentation/index head must rerun those workflows. `Skill Eval Contract` is triggered only by `ready_for_review`; after the final head stabilizes it must be explicitly retriggered and pass at that exact head. Missing execution is not PASS.

No earlier green head follows a moving parent automatically. Only a new exact-head run plus independent Shadow readback can make the static/deterministic convergence `READY_FOR_HUMAN_ADMIT`. That state still does not admit or merge #451/#452/#456/#457 and cannot raise any live evidence lane.

## Four-repository documentation stack

The established documentation-plane relationship remains:

| Plane | Issue / PR | Relation | Current known terminal state |
|---|---|---|---|
| Instruction / Method | `skills-shared #84/#85` | independent sibling | merged historical |
| Runtime Contract | `runtime-env #29/#30` | independent sibling | merged historical |
| Domain Product / Consumer | `agent-shield-monorepo #77/#78` | terminal sibling | merged historical |
| Integration / Acceptance | `bettor-arena #36/#37` | independent sibling | merged historical |
| Exact merged index / cold-start audit | `bettor-arena #38` | convergence | closed historical |

The parent Bettor integration contract remains separately owned. Consumer snapshots here are navigation only; current consumer state must be read in that repository.

## Intent-Bound Constraint line

Historical IBC delivery remains traceable as `#98→#104`, `#99→#105`, `#100→#106`, `#101→#111`, and `#102→#107`. Two historical merged heads (#105/#106) had no owning workflow run at their exact heads; that absence remains recorded as absence, not retroactive PASS. Current details stay in `docs/AGENT_INTEGRATION_STATE.md` and the owning IBC contracts.

## Controlled Technical Language line

Parent programme `#115`; architecture/evidence law remains [`../architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md`](../architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md). Merged leaves #117/#125/#126/#127/#137/#139/#130/#138/#143/#131/#140/#152 retain their owning exact-head checks. Consumer CTL 07/07A/07B state belongs to `bettor-arena`; CTL 08 remains a convergence concern only when its prerequisites are actually admitted.

## Spatial-loop systems engineering

Issue #128 / PR #136 remains an independent terminal leaf for the substrate-bound method. Static/deterministic contracts do not prove privileged root/KVM/cgroup/seccomp/network/hardware/chaos/security execution. Destructive testing, security acceptance, merge, promotion and rollback remain Human/trusted-operator boundaries.

## Method lineage

- `knowledge-continuity` — every hop leaves in-place summaries; no unexplained redirect-only evidence.
- `github-delivery-loop` — issue/PR/receipt/publication-state separation.
- `forgejo-delivery-loop` — local authoring/routing/outbox/recovery separation.
- `git-town-stacked-pr-worker` — SIBLING/TRUE_CHILD/CONVERGENCE/PROCESS/EXTERNAL/HISTORICAL branch semantics and Molecular traceability.
- `skill-refactor-proof-loop` — treatment freeze, old-strength preservation, proof layers, golden registry, complete denominator, no evidence promotion.
- `agentic-tech-lead-orchestration` — task/capability/dual-DAG ownership, worktree/session contracts, current Codex control-plane convergence.
- `procedural-shadow-runtime` — independent same-subject applicability/contradiction/evidence-ceiling review.
- `spatial-loop-systems-engineering` — exact-subject capability/invariant/teardown/performance gates for substrate-bound work.

## Evidence boundary

PR presence, ancestry and mergeability prove neither admission nor implementation correctness nor live execution. Documentation completion, deterministic fixtures, hosted workflow success, terminal `done`, issue close, PR merge, model agreement or an external link cannot substitute for live Codex/Herdr/GitHub effects, real source/provider closure, Human Admit, release or production readiness.

## Codex control-plane Wave 3 — live-evidence infrastructure

Canonical Wave-3 trace: [`WAVE3_LIVE_EVIDENCE.md`](WAVE3_LIVE_EVIDENCE.md). It extends #455 without modifying the provider-neutral core.

```text
#455 / #379 static convergence
├─ #464 / PR #469  Codex live acceptance carrier        TRUE_CHILD
├─ #465 / PR #470  GitHub dependency reversible canary TRUE_CHILD
├─ #466 / PR #471  Herdr lifecycle carrier             TRUE_CHILD
└─ #467 / PR #472  immutable source-claim compiler     TRUE_CHILD
          ↓ exact selected bytes
#468 / PR #473     Wave-3 convergence
```

Selected exact leaf heads for the current integration epoch:

```text
#469 d239d17d1d718f3e5e8c1975307665cae43d3b09
#470 f4c3215b6c52c2e6106070eaa1121dee1dbd48e3
#471 9eb70b2b62193b62a28f243de91e51337f1906b3
#472 44d779a02e1749aa88a502d946646c22af38a026
```

Immutable integration checkpoint:

```text
691b342c44c9c6c4e61a9997e778ae4ed6e920d5
parents:
  847e56c3418fce920c42d983e84ee44fdc6e8971  #455 true parent
  d239d17d1d718f3e5e8c1975307665cae43d3b09  #469
  f4c3215b6c52c2e6106070eaa1121dee1dbd48e3  #470
  9eb70b2b62193b62a28f243de91e51337f1906b3  #471
  44d779a02e1749aa88a502d946646c22af38a026  #472
```

Wave-3 deterministic evidence denominator:

```text
4 new Draft-2020-12 contracts
Codex live acceptance       1 positive / 12 mutations
GitHub reversible canary    1 / 6
Herdr lifecycle             2 / 7
source-claim compiler       4 source kinds / 11 mutations
source compiler → existing problem-closure checker integration
Local Handoff Queue schema + semantic assertion
```

The queue is bound to the immutable integration checkpoint, not to a mutable PR head. It sequences runtime-only work as Codex live execution → Herdr observation → GitHub reversible canary and requires a durable receipt before each next item.

Current evidence ceiling before live execution:

```text
Codex live carrier mechanism             IMPLEMENTED_CANDIDATE / runtime NOT_EXERCISED
GitHub reversible canary mechanism       IMPLEMENTED_CANDIDATE / remote NOT_EXERCISED
Herdr lifecycle carrier                  IMPLEMENTED_CANDIDATE / runtime NOT_EXERCISED
source compiler                          IMPLEMENTED_CANDIDATE / source truth EVIDENCE_DEPENDENT
#473 deterministic convergence           pending exact-head hosted validation
Human Admit / merge / release            NOT_PERFORMED
```

A future runtime receipt must bind the exact subject it observed. It cannot inherit PASS from #455/#473 CI, and #473 ancestry cannot admit #455 or any leaf. Mutable #473 state is always read live from GitHub.