# GitHub Delivery Traceability Index

This index traces design intent to repository decisions, implementation changes, evals, and current evidence. It complements the repository-wide live handoff in [`../../../docs/AGENT_INTEGRATION_STATE.md`](../../../docs/AGENT_INTEGRATION_STATE.md); it is not a replacement for GitHub, `evals.json`, scripts, verifiers, or receipts.

## 1. Trace model

```text
Source / incident
→ repository decision
→ parent issue
→ molecular issue
→ Stacked or sibling PR
→ eval IDs and negative controls
→ immutable implementation subject
→ execution evidence
→ Human Admit
```

A missing link is named explicitly. Similar content or a later branch does not silently fill the gap.

## 2. Source and incident register

| ID | Source | Classification | Supports | Does not prove |
|---|---|---|---|---|
| `SRC-001` | External attachment `科技巨頭開源授權與AI框架v2.pdf`, 41 pages | `SOURCE_PROPOSAL` | candidate cloud/local runtimes, E2B/Firecracker, tmux, synchronization, mobile, wallet/security, cost and repository-shape ideas | current license truth, latency, security, runtime readiness, GitHub Actions policy, live provider evidence |
| `INC-042` | GitHub PR [#42](https://github.com/ed3c/skills-shared/pull/42) | physical delivery incident | rapid PR-head publication caused many private Actions attempts; later account annotation prevented runner allocation | repository test failure, current billing health, provider recovery |
| `REG-001` | [`../../../registry.json`](../../../registry.json) | repository authority | `github-delivery-loop` and `git-town-stacked-pr-worker` are shared Skills | consumer-specific branch graph, config, remotes or receipts |
| `DOC-079` | PR [#79](https://github.com/ed3c/skills-shared/pull/79) | repository-wide live handoff | current integrated Skill Eval state machine, active stack, data flow and continuation protocol | per-skill delivery script semantics or live provider evidence |

## 3. Repository decisions

| Decision | Statement | Owner / implementation |
|---|---|---|
| `DEC-DELIVERY-01` | Local commit cadence, remote publication cadence, Actions cadence, and merge cadence are separate. | [`github-actions-cost-control.md`](github-actions-cost-control.md) |
| `DEC-DELIVERY-02` | Private repositories admit only initial draft, ready-for-review, and one batched repair publication. | `ci_publish_gate.py` |
| `DEC-DELIVERY-03` | A no-runner billing/spending observation opens a circuit; it is not repository-test `FAIL`. | `github_actions_snapshot.py`, `ci_publish_gate.py` |
| `DEC-DELIVERY-04` | Publication requires exact-HEAD local verification from a fixed consumer-owned command contract. | `local_verification.py` |
| `DEC-DELIVERY-05` | GitHub live capture and zero-network policy evaluation are separate producers. | `github_actions_snapshot.py`, `ci_publish_gate.py` |
| `DEC-DELIVERY-06` | Git Town synchronizes branch hierarchy; it does not own push, merge, promotion, or semantic conflict repair. | [`../../git-town-stacked-pr-worker/README.md`](../../git-town-stacked-pr-worker/README.md) |
| `DEC-DELIVERY-07` | Independent path-disjoint work uses sibling branches; only true byte dependencies form a stack. | Git Town README and task packets |
| `DEC-DELIVERY-09` | An absent open pull request does not prove an absent remote branch; the initial boundary requires an independently observed `refs/heads/<exact>`. | `github_actions_snapshot.py --strict`, issue #70 |
| `DEC-DELIVERY-08` | Documentation explains state and ownership but cannot become a second API or evidence authority. | [`../README.md`](../README.md), issues #78 and PR #80 |

## 4. Canonical publication-policy line

| Step | GitHub subject | Result | Evals / evidence |
|---|---|---|---|
| Parent issue | [#43](https://github.com/ed3c/skills-shared/issues/43) | closed as completed | acceptance criteria define exact-HEAD gate, three intents, billing circuit and negative controls |
| Policy PR | [#44](https://github.com/ed3c/skills-shared/pull/44) | merged to `main` | `DELIVERY-5`, focused local selftests, evidence-producer tests |
| Main mechanism | [`../scripts/ci_publish_gate.py`](../scripts/ci_publish_gate.py) | present | exact policy input validation and stable ALLOW/BLOCK reasons |
| Local producer | [`../scripts/local_verification.py`](../scripts/local_verification.py) | present | fixed argv, exact clean HEAD, bounded output, safe environment |
| GitHub producer | [`../scripts/github_actions_snapshot.py`](../scripts/github_actions_snapshot.py) | present | capture/replay, one PR, exact check identity, billing annotation classification, independently observed branch ref under `--strict` |
| Method document | [`github-actions-cost-control.md`](github-actions-cost-control.md) | present | workflow pattern and evidence boundary |
| Current live billing state | external | `NOT_EXERCISED` in repository docs | requires fresh trusted snapshot |
| GitHub/Forgejo equivalence | external | `NOT_EXERCISED` | requires exact commit/tree/release equivalence receipt |

## 5. Historical Skill Eval foundation stack

The following is the reviewed logical dependency chain recorded by PR bases and descriptions. Post-merge history may be flattened by merge strategy.

| Order | PR | Purpose | Dependency role |
|---:|---|---|---|
| 1 | [#32](https://github.com/ed3c/skills-shared/pull/32) | Skill Eval Contract v1 and first gold replay | stack root |
| 2 | [#33](https://github.com/ed3c/skills-shared/pull/33) | autoresearch-composer outcome evals | child of #32 |
| 3 | [#34](https://github.com/ed3c/skills-shared/pull/34) | cross-harness run/evidence contracts | child of #33 |
| 4 | [#35](https://github.com/ed3c/skills-shared/pull/35) | sealed holdouts and mutation lineage | child of #34 |
| 5 | [#36](https://github.com/ed3c/skills-shared/pull/36) | capability scorecards and unlock gates | child of #35 |
| 6 | [#39](https://github.com/ed3c/skills-shared/pull/39) | pinned skill-up physical runtime bridge | runtime child |
| 7 | [#42](https://github.com/ed3c/skills-shared/pull/42) | deterministic verifier authority | security/evidence child |
| 8 | [#46](https://github.com/ed3c/skills-shared/pull/46) | draft-aware Actions cadence | terminal workflow leaf |

Issue [#45](https://github.com/ed3c/skills-shared/issues/45) defined the draft-aware workflow evals before PR #46. The current `.github/workflows/skill-eval-contract.yml` on `main` contains the reviewed trigger, concurrency, permission, pinning, and timeout pattern.

## 6. Active Skill Eval molecular stack

The repository-wide live handoff currently identifies:

```text
main
└── #73 verifier calibration
    └── #74 mutation admission
        └── #76 verified-capability release boundary
```

Landing order is `#73 → #74 → #76`. Each child must be reconstructed/rebased onto the actual landed parent/main tree after squash merges and rerun the owning gates. Old green CI does not transfer across changed ancestry.

Separate hardening/cost/publication workstreams must not be flattened into that stack without checking their base and authority boundary. Current branch/PR metadata remains the source of truth; this index is a navigation snapshot.

## 7. Git Town method line

| Subject | Path | State |
|---|---|---|
| Shared method | [`../../git-town-stacked-pr-worker/SKILL.md`](../../git-town-stacked-pr-worker/SKILL.md) | implemented portable law |
| Worker system prompt | [`../../git-town-stacked-pr-worker/SYSTEM_PROMPT.md`](../../git-town-stacked-pr-worker/SYSTEM_PROMPT.md) | implemented prompt surface |
| Publication policy | [`../../git-town-stacked-pr-worker/PUBLICATION_POLICY.md`](../../git-town-stacked-pr-worker/PUBLICATION_POLICY.md) | implemented method document |
| Eval inventory | [`../../git-town-stacked-pr-worker/evals.json`](../../git-town-stacked-pr-worker/evals.json) | present |
| Consumer `.git-town.toml` | consumer repository | not owned here |
| Exact Git Town executable/version/SBOM | host environment | `NOT_EXERCISED` here |
| Live unattended rebase receipt | consumer environment | `NOT_EXERCISED` here |
| Semantic conflict resolution | Human/recovery Agent | never delegated to unattended Worker |

## 8. Documentation convergence line

| Subject | Status |
|---|---|
| PR [#79](https://github.com/ed3c/skills-shared/pull/79) | merged repository-wide integration state and active stack index |
| Issue [#78](https://github.com/ed3c/skills-shared/issues/78) | open; defines per-skill/directory documentation evals and boundaries |
| PR [#80](https://github.com/ed3c/skills-shared/pull/80) | draft; adds `AGENTS.md`, nearest READMEs, delivery state machines and traceability details |
| Branch `docs/github-delivery-state-machine-index` | PR #80 implementation subject |
| Product/runtime code changes | excluded |
| Automated README/link checker | deferred to a separate child issue/PR |

PR #80 is based on current `main` and extends PR #79 rather than replacing it. It is an independent documentation leaf because it consumes merged bytes only.

## 9. Eval map

The machine inventory is [`../evals.json`](../evals.json). Key families:

| Eval family | Mechanism | Positive control | Negative/hollow control |
|---|---|---|---|
| `DELIVERY-1` | delivery receipt | complete artifact/receipt/publication | missing artifact is `UNMATERIALIZED` |
| `DELIVERY-2` | Codex merge rule | narrow repo-scoped rule | unsafe target rejected |
| `DELIVERY-3` | merge gate | owner-admitted exact head | forged/stale admit and blocking hook rejected |
| `DELIVERY-4` | canonical link | identical copy converts and remains readable | diverged copy refused and preserved |
| `DELIVERY-5` | CI publication | exact-HEAD local receipt and admitted intent | draft checkpoint, stale SHA, reused feedback, billing circuit rejected |
| evidence producers | local receipt and GitHub snapshot | fixed commands / one PR / exact check | shell strings, unsafe env, multiple PRs, stale check, malformed billing rejected |
| reference causality | source/evidence binding | exact implementation subject | reference-only or stale evidence rejected |

## 10. Current status summary

```text
Repository-wide integration handoff     IMPLEMENTED / PR #79 merged
Canonical publication policy            IMPLEMENTED / merged
Draft-aware Skill Eval workflow         IMPLEMENTED / on main
Local verification producer             IMPLEMENTED
GitHub capture/replay producer           IMPLEMENTED
Publication gate                         IMPLEMENTED
Merge preflight                          IMPLEMENTED
Git Town shared method                   IMPLEMENTED
Active contract stack                    #73 → #74 → #76
Current host billing availability        NOT_EXERCISED here
GitHub/Forgejo equivalence               NOT_EXERCISED
Physical model/provider execution        NOT_EXERCISED unless a receipt exists
Human merge/promotion authority          external and explicit
Per-skill documentation PR #80           IN_PROGRESS / draft
```

## 11. Updating this index

Update this document when:

- the repository-wide active stack changes;
- a new state machine appears;
- an issue/PR changes the delivery dependency graph;
- a terminal leaf moves;
- an eval family is added or removed;
- a current evidence boundary changes;
- a GitHub/Forgejo equivalence receipt is admitted;
- a source proposal becomes an implemented and exercised provider.

Do not update `NOT_EXERCISED` to `PASS` based only on prose, package presence, a skipped workflow, an old SHA, another environment's receipt, or a PR body.
