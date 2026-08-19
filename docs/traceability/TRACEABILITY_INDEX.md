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

Mutable open PR heads are read from GitHub immediately before decision use. This document records immutable merged/rejected/integration ancestors and current observed snapshots, but never self-embeds its own mutable final head.

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

Current common base observed for the hardened sibling epoch:

```text
main@4ca9417b1da5ff32f1d4d3e7af64a15908749024
```

| Atom | Issue / PR | Relation | Current exact sibling head | Mechanism state | Remaining ceiling |
|---|---|---|---|---|---|
| Codex SDK controller/session | `#375 / #451` | `SIBLING` | `86f9e8d940b76cb71b713c098ff09cb68eb4e0c1` | exact worktree HEAD/tree/clean preflight + post-turn path-lease readback; selftest `4/14` | live SDK `NOT_EXERCISED`; independent source/diff/test acceptance still required |
| GitHub Issue DAG projection | `#376 / #452` | `SIBLING` | `426fb6f6f548f71572d4402e73e0b05ecf6f8aa8` | completion-edge projection + repo/default-branch/visibility + issue-state + closing-PR-reference preflight; selftest `6/17` | live mutation/readback `NOT_EXERCISED`; generic development-link ownership beyond closing refs residual |
| Herdr observer | `#377 / #453` | `SIBLING` | `5b6e58d1e7e9e127123dbb4a9189b98e5ff973cf` | optional worktree/session observer + fallback; selftest `4/9` | live Herdr `NOT_EXERCISED` |
| Problem closure | `#378 / #454` | `SIBLING` | `32c5425de1cf4f083bd998e81873a86af8771e1e` | source→task/DAG→session/evidence closure checker/renderer; selftest `4/11` | real source/provider closure `EVIDENCE_DEPENDENT` |
| Documentation foundation | `#379 refs / #380` | `DOCUMENTATION SIBLING` | `7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5` | original traceability design bytes | navigation only |
| Shared convergence | `#379 / #455` | `CONVERGENCE` | read live from GitHub | current sibling bytes + shared tests/routes/Shadow/Git Town/trace | current final head must pass full hosted denominator before new Shadow admission |

### Current dependency integration

Concurrent hardening moved #451/#452 after the first all-green convergence. #379 therefore created a new immutable parent refresh:

```text
5d21ecab137cb26586ef1636dc279ee29733e913
parents:
  35874af7a6d04783983b05c8f1b1e402471b4451  prior #455 convergence head
  86f9e8d940b76cb71b713c098ff09cb68eb4e0c1  current #451
  426fb6f6f548f71572d4402e73e0b05ecf6f8aa8  current #452
```

The earlier `35874af7...` hosted-green/Shadow-admitted result is now `HISTORICAL` because consumed parents moved. It is not reused as current evidence.

### Historical convergence epoch 1

```text
c0f6979f80038394350aea724c598c8dba5ac338
parents:
  ccef97dedd7ea8b1873e3afa130ca82b8eabb413
  339ae874b070fb3a8a5fa89b0241d90434257e99  historical #451
  b5295df681d6471b19775db38860b2d151339879  historical #452
  5b6e58d1e7e9e127123dbb4a9189b98e5ff973cf
  32c5425de1cf4f083bd998e81873a86af8771e1e
union tree 37cb2c56e7dfc939cacaa0f65cf8f9b0f8318b22
```

`af427a13...` then consumed PR #380 documentation. `35874af7...` refreshed current-main-at-that-time and passed Skill Suites, Shared Skills Infra, Skill Eval Contract and Git Town Stacked PR Worker before it was superseded by the parent movement above.

Rejected first candidates remain explicit:

```text
#444 → #451
#445 → #452
#446 → #453
#447 → #454
```

Those first candidates are closed-unmerged provenance failures, not alternate merge candidates.

### Current convergence gate

The exact final #455 head must execute, not merely contain:

```text
6 Draft-2020-12 schemas
Codex selftest        4 positive / 14 mutations
GitHub DAG selftest   6 positive / 17 mutations
Herdr selftest        4 positive / 9 mutations
closure selftest      4 positive / 11 mutations
problem-closure example + checker + non-authority Markdown projection
existing ATL suite
```

Hosted denominator:

```text
Skill Suites
Shared Skills Infra
Skill Eval Contract
Git Town Stacked PR Worker
```

No earlier green head follows a moving parent automatically. Only a new exact-head run plus independent Shadow readback can restore `ELIGIBLE_FOR_HUMAN_ADMIT` for the static/deterministic scope. Live Codex/GitHub/Herdr/source-provider evidence and merge/release remain separate.

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

PR presence and mergeability prove neither implementation correctness nor live execution. Documentation completion, deterministic fixtures, hosted workflow success, terminal `done`, issue close, PR merge, model agreement or an external link cannot substitute for live Codex/Herdr/GitHub effects, real source/provider closure, Human Admit, release or production readiness.
