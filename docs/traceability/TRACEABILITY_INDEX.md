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

## Codex SDK Tech Lead control plane — Wave-2 epoch (HISTORICAL)

Canonical programme trace: [`CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`](CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md). Portable law remains `skills/agentic-tech-lead-orchestration/SKILL.md`.

This whole section is the Wave-2 sibling epoch as it stood when it was compiled. Every PR in it has since reached a terminal state; none is an open candidate. Current admitted `main` at the 2026-08-22 readback is `5341885f26b5e8e7baf5087a4d661e324f878242` (tree `a18e12507f9e621efd5354f58384eded1f1e2a9a`).

Common base observed for this sibling epoch at compile time — historical, 364 commits behind current `main`:

```text
main@4ca9417b1da5ff32f1d4d3e7af64a15908749024
```

| Atom | Issue / PR | Terminal relation (2026-08-22) | Selected exact head at the epoch | Mechanism state | Remaining ceiling |
|---|---|---|---|---|---|
| Codex SDK controller/session | `#375 / #451` | `SIBLING / CLOSED_UNMERGED / CONSUMED` by #379 / PR #455 | `86f9e8d940b76cb71b713c098ff09cb68eb4e0c1` | exact worktree HEAD/tree/clean preflight + post-turn path-lease readback; selftest `4/14` | live SDK `NOT_EXERCISED`; independent source/diff/test acceptance still required |
| GitHub Issue DAG projection | `#376 / #452` | `SIBLING / CLOSED_UNMERGED / CONSUMED` by #379 / PR #455 | `426fb6f6f548f71572d4402e73e0b05ecf6f8aa8` | completion-edge projection + repo/default-branch/visibility + issue-state + closing-PR-reference preflight; selftest `6/17` | live mutation/readback `NOT_EXERCISED`; generic development-link ownership beyond closing refs residual |
| Herdr observer | `#377 / #456` | `SIBLING / CLOSED_UNMERGED / CONSUMED` by #379 / PR #455 | `6a2ebcbe87078cecaf67f82f3c9c10643bcc9123` | exact Git/worktree/process/session identity + PID-start/freshness/liveness + cleanup/residue; selftest `4/18` | live Herdr `NOT_EXERCISED`; `DONE_CANDIDATE` remains advisory |
| Problem closure | `#378 / #457` | `SIBLING / CLOSED_UNMERGED / CONSUMED` by #379 / PR #455 | `ac5ddc0287eb4e4156a7c7eef178b7be8bbd1d34` | frozen denominator/source manifest + exact repo/evidence subjects + supersession validation; selftest `6/22` | real source/provider closure `EVIDENCE_DEPENDENT` |
| Documentation foundation | `#379 refs / #380` | `DOCUMENTATION SIBLING / CLOSED_UNMERGED / CONSUMED` | `7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5` | original traceability design bytes | navigation only |
| Shared convergence | `#379 / #455` | `MERGED / HUMAN_ADMITTED` — merge `ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c` | candidate `847e56c3418fce920c42d983e84ee44fdc6e8971` | selected sibling bytes + shared tests/routes/Shadow/Git Town/trace | admission of #455 did not raise any live evidence lane |

The terminal classifications above are the ones recorded in [`AGENTS.md`](AGENTS.md) (Wave-2 control-plane admission block). Consumption through the #455 convergence is not an individual merge of any sibling.

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

No earlier green head follows a moving parent automatically. Only a new exact-head run plus independent Shadow readback could make the static/deterministic convergence `READY_FOR_HUMAN_ADMIT`. That gate is historical: #455 was admitted and merged (`ca31e0b1…`), and #451/#452/#456/#457 closed unmerged as consumed siblings rather than being merged individually. Neither outcome raised any live evidence lane.

## Git at any scale — source / contract / canary / Shadow line

Detailed human trace: [`git-at-any-scale/README.md`](git-at-any-scale/README.md); nearest rules [`git-at-any-scale/AGENTS.md`](git-at-any-scale/AGENTS.md); terminal delivery topology [`../../skills/git-town-stacked-pr-worker/molecular-indexes/git-at-any-scale/README.md`](../../skills/git-town-stacked-pr-worker/molecular-indexes/git-at-any-scale/README.md). Machine authority remains:

```text
data/handoff/source-evidence/sources/cursor-git-at-any-scale.html
data/handoff/source-evidence/git-at-any-scale-claims.json
data/handoff/source-evidence/git-at-any-scale-closure-ledger.json
skills/git-hosting-scale-assurance/references/hosting-assurance.schema.json
skills/git-hosting-scale-assurance/scripts/check_hosting_assurance.py
data/handoff/git-at-any-scale/**
skills/agentic-tech-lead-orchestration/runtime-handoff/git-at-any-scale-local-handoff-queue.json
```

Every issue in this line is `OPEN` at the 2026-08-22 readback; only the carrier PRs reached a terminal state. A merged PR closes its own path lease, never its issue's denominator.

```text
#512/#531  immutable article packet     bytes MERGED   864322 bytes, sha256 25f59fc6…f00447cab9
#531       28-claim denominator          OPEN          26 OPEN / 2 NOT_APPLICABLE, 0 VERIFIED_*
├─ #532 / PR #542  portable contract     OPEN    PR MERGED, SIBLING (path-disjoint)
├─ #536 / PR #539  preparation surface   OPEN    PR MERGED, SIBLING (path-disjoint)
├─ #534  physical canary                 OPEN    PROCESS_DEPENDENCY + EXTERNAL_EVIDENCE
└─ #535  independent Shadow              OPEN    EXTERNAL_EVIDENCE / read-only
                ↓ selected admitted prerequisites
#536       shared route/index convergence         one writer, this epoch
```

| Atom | Issue / PR | Terminal relation (2026-08-22) | Deterministic evidence at this subject | Live / physical evidence |
|---|---|---|---|---|
| immutable source packet | `#512 / #531` | bytes `MERGED`, both issues stay `OPEN` | `check_problem_closure.py` exit 0, `problem_count 28` | none; the checker never re-derives the digest from the persisted bytes |
| portable assurance contract | `#532 / PR #542` | `SIBLING / MERGED`, issue stays `OPEN` | `tests/run-all.sh` → `PASS positive=1 mutations=20/20`; registered in `evals/skill-entry-routes.json` and `evals/skill-core-boundaries.json` on 2026-08-22, both `--skill` checkers exit 0 | none. Receipt `data/handoff/git-at-any-scale/issue-532-portable-contract-receipt.json` `ABSENT`; per-family schemas/fixtures `NOT_IMPLEMENTED`; hosted suite readback `SKIPPED_BY_POLICY` |
| preparation surface | `#536 / PR #539` | `SIBLING / MERGED`, issue stays `OPEN` | traceability skeleton + Local Handoff queue on `main` | none |
| physical hosting canary | `#534` | `PR_ABSENT` / `EXTERNAL_EVIDENCE` | contract validation only | bounded **CLEAN_ROOM single-node** run on 2026-08-22; receipts under `data/handoff/git-at-any-scale/`, `SHA256SUMS` 21/21. Gossip loss, matched-scale matrix and Shadow replay `NOT_EXERCISED`. Not a distributed-hosting or scale result |
| independent Shadow | `#535` | `PR_ABSENT` / `EXTERNAL_EVIDENCE` | independent digest/ledger readback | `data/handoff/git-at-any-scale/issue-535-shadow-receipt.json`, verdict `HOLD`, `HUMAN_ADMIT_REQUIRED`; reviewer identity independence unmet, advisory only |
| shared convergence | `#536` | `CONVERGENCE`, `PR_ABSENT` until publication | root `README.md`/`AGENTS.md`, `docs/INDEX.md`, this index, `TECH_LEAD_SHADOW_CLOSURE.md`, the Git Town README and both Molecular indexes converged in this epoch; `check_document_routes.py`, `check_skill_entry_routes.py` and `assert_local_handoff_queue.py` green | no new live claim |

Current Local Handoff: `GIT-SCALE-H1` (#532) `ACTIVE`, bound to `5341885f…` / tree `a18e1250…` / rollback `9fe3c6da…`. #539 and #542 were path-disjoint siblings before merge and stayed siblings after: merging both into the same `main` does not create ancestry between them.

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