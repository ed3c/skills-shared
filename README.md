# skills-shared — 跨 repo 共用的基礎設施 skills

所有 Claude Code 與 Codex CLI 專案共用的 skill 本體住在這裡，**一個名稱只有一份**。
治理規則、指令與 why 全在 [`skills/shared-skills-infra/SKILL.md`](skills/shared-skills-infra/SKILL.md)；裁決帳在 [`registry.json`](registry.json)。

> **Agent entrypoint:** 修改 eval、mutation、runtime、release、CI 或 promotion 前，先讀 [`docs/AGENT_INTEGRATION_STATE.md`](docs/AGENT_INTEGRATION_STATE.md)，再讀 [`docs/SKILL_EVAL_ROADMAP.md`](docs/SKILL_EVAL_ROADMAP.md)。前者記錄「現在真的整合到哪裡」，後者記錄目標 Phase。

## Repository topology → State Machine ownership

```text
skills-shared/
├── skills/                         # CANONICAL ARTIFACT state
│   └── shared-skills-infra/        # distribution/drift governance state machine
├── registry.json                   # canonical/deferred admission ledger
│
├── evals/                          # EVALUATION state machine
│   ├── cases/                      # public dev + gold replay contracts
│   ├── holdout/                    # sealed post-selection contracts; optimizer不可讀 outcome
│   ├── fixtures/                   # replay + verifier calibration inputs
│   ├── verifiers/                  # deterministic outcome authority
│   ├── runtime/                    # executor/model/harness/environment identity
│   ├── adapters/                   # external harness -> canonical evidence normalization
│   ├── capability-unlocks.json     # held-out cross-harness capability state
│   ├── releases.json               # Phase 5 release registry（PR #76 stack）
│   └── scorecards/                 # Ecosystem Quality / Verified Capability 分離
│
├── mutations/                      # EVOLUTION state machine
│   ├── lineage*.jsonl              # hypothesis -> candidate -> evidence -> terminal state
│   ├── schema/                     # mutation/eval/promotion contracts
│   └── promotions.json             # only recomputed winners may enter
│
├── scripts/                        # deterministic control-plane transitions
├── tests/                          # regression + mutation-kill proofs
├── .github/workflows/              # CI orchestration; not semantic authority by itself
└── docs/
    ├── AGENT_INTEGRATION_STATE.md   # live handoff / current integration truth
    └── SKILL_EVAL_ROADMAP.md        # Phase 1–5 target architecture
```

### Integrated State Machine

```text
CANONICALIZED
    |
    v
CLAIM_REGISTERED
    |
    v
CASE_BOUND -------------------- stale implementation target --> BLOCKED
    |
    v
VERIFIER_CALIBRATED ----------- insensitive verifier ---------> BLOCKED
    |
    v
EXECUTABLE
    |
    v
EVIDENCE_COLLECTED
    |
    +--> MUTATION_EVALUATED ---- lost/tie/reverted -----------> PRESERVED
    |          |
    |          `-- won + recomputed evidence --> PROMOTION_ELIGIBLE
    |
    `--> post-selection sealed holdout
                    |
                    v
             CAPABILITY_UNLOCKED
                    |
                    v
              RELEASE_ADMITTED
                    |
                    v
             CANONICAL_RELEASED
                    |
                    `-- regression/drift --> ROLLBACK / NEW MUTATION
```

Authority separation is intentional: canonical distribution does not prove capability; an LLM judge does not create hard-gate truth; mutation search does not see holdout outcomes; documentation/popularity cannot compensate for failed capability gates; release requires real evidence plus human admit.

## Data flow

```text
skills/<name>/SKILL.md + implementation
       |
       +--> registry.json + shared-skills-infra --> canonical projection/drift evidence
       |
       `--> evals/cases + sealed evals/holdout
                    |
                    +--> live implementation-target gate
                    +--> verifier calibration gate
                    v
             runtime / harness adapters
                    |
                    v
                run trace
                    |
                    +--> deterministic verifier receipt
                    v
               evidence bundle
                    |
           +--------+---------+
           |                  |
           v                  v
 mutation dev/control     sealed holdout
 evaluation               post-selection
           |                  |
           v                  v
 mutation lineage       capability unlock
           |                  |
           v                  v
 promotion registry ---> release receipt
                              |
                              +--> separate scorecards
                              +--> rollback artifact
                              `--> human admit -> canonical release
```

## Current integration status — 2026-08-12

### Landed on `main`

- **PR #77** — isolated `Shared Skills Infra` GitHub-hosted CI; also fixed portability/dead-assertion defects exposed by hosted execution.
- **PR #75** — canonical-drift assertion quality: multi-member fixtures plus three real first-only mutants killed by CI.
- **PR #72** — real-incident evals are bound to live implementation targets/anchors so stale benchmarks fail closed.
- Phase 1–3 foundation already present: eval contracts, sealed holdout metadata, run/evidence schemas, cross-harness adapters/runtime work, verifier-authority controls, mutation-lineage foundation.

### Active molecular stack

```text
main
 |
 +-- #73 agent/verifier-calibration-v1
 |      verifier positive+hollow calibration; logical child of landed #72
 |
 +-- #74 agent/mutation-admission-v1
 |      Phase 4: paired current/candidate/no-skill evidence,
 |      holdout isolation, promotion admission
 |       |
 |       +-- #76 agent/verified-capability-release-v1
 |              Phase 5: capability release receipt, immutable identities,
 |              rollback artifact, separate scorecards, human admit
```

**Landing order:** `#73 -> #74 -> #76`. Because parent PRs may be squash-merged, a child branch must be genuinely rebased/reconstructed onto the new parent/main tree before its old green CI is trusted again.

### Other terminal stacks / hardening branches

These are separate molecular workstreams and should not be flattened into the Phase 4/5 stack without checking their base and authority boundary:

- `codex/git-town-ci-publication-policy` — Git Town/publication cadence policy surface.
- `codex/github-actions-evidence-producers-v2` and `codex/github-actions-remote-ref-proof` (#71 Draft) — exact remote/ref evidence and publication preconditions.
- `codex/skill-eval-cost-tiers` (#69 Draft) — physical eval smoke vs promotion cost tiers.
- `agent/dead-assertion-single-source-v2` (#68 Draft) — canonical dead-assertion gate consolidation.

Use PR metadata as truth for current base/head relationships; branch names above are an index, not permission to merge.

## Git Town / Stack PR operating model

The repository has Git Town-oriented publication branches, but **do not assume Git Town is installed in every execution environment**. If available locally, use it to keep molecular branches synchronized; otherwise preserve the same parent graph with normal Git/GitHub operations.

```bash
# optional when git-town is installed
git town sync
git town hack <terminal-state-branch>
# implement exactly one authority/state transition
git town propose
git town sync --stack
```

Stack rules:

1. One terminal state transition or authority boundary per PR when practical.
2. Child PR base must be its real parent branch until the parent lands.
3. After a squash merge, reconstruct/rebase the child onto the new main/parent; do not treat old ancestry as proof.
4. Child workflows must be a **superset** of required parent gates; a child may not silently remove parent validation.
5. A CI job that is `skipped` is not execution evidence.
6. Physical capability claims require real runtime evidence; mocks/fixtures prove contracts, not capability unlocks.

## Clone 到任何目錄都能用

版控內容**沒有任何機器路徑**：`registry.json` 只存裁決，路徑全在 gitignored 的 `sites.local.json` 或旗標，canonical 位置由 `__file__` 推導。

```bash
git clone <this-repo> ~/.agents/skills-shared
python3 ~/.agents/skills-shared/skills/shared-skills-infra/scripts/shared_skills.py \
  install --project ~/proj-a --project ~/proj-b --claude-forwarder proj-b
```

`install` 寫路徑 → 連 user 層與各專案 → 跑 `check`。冪等；換機器或搬 checkout 後重跑即復原。

```bash
INFRA=~/.agents/skills/shared-skills-infra/scripts/shared_skills.py
python3 $INFRA check ; python3 $INFRA report
bash ~/.agents/skills-shared/skills/shared-skills-infra/tests/verify.sh
```

## Agent continuation checklist

接手的 Agent 不應從「下一個看起來能寫的 feature」開始，而應：

1. 讀 `docs/AGENT_INTEGRATION_STATE.md` 與 roadmap。
2. 查 current `main`、open PR base/head、CI 是否真的執行。
3. 找出自己負責的 State Machine transition 與上游/下游 authority。
4. 先修 stack ancestry，再改 implementation。
5. 執行該 failure domain 的 CI；不能用其他 workflow 的綠燈替代。
6. 更新 README + integration state，讓下一個 Agent 不必從聊天紀錄重建現況。

## 現況與待辦

Canonical shared-skill migration 仍由 `registry.json` 與 `shared_skills.py report` 動態重算；不要把舊的掃描數字當成永久事實。

Skill Eval 主線下一個收斂點是 **#73 -> #74 -> #76**。完成 contract landing 後，真正尚未被 contract 取代的關鍵工作是 physical execution：以至少兩個真實 model/harness stacks 對 post-selection sealed holdout 產生 deterministic evidence，才能建立第一個 `Capability Unlock`。詳細需求與禁止事項見 [`docs/AGENT_INTEGRATION_STATE.md`](docs/AGENT_INTEGRATION_STATE.md)。
