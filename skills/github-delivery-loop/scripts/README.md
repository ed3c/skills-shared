# `github-delivery-loop/scripts/`

This directory contains the executable mechanisms for delivery evidence, GitHub Actions publication admission, canonical projection, and merge preflight. Scripts may share internal libraries, but their public state-machine responsibilities remain separate.

## Executable map

| Script | State machine | Network | Mutation | Primary outputs |
|---|---|---|---|---|
| [`github_delivery.py`](github_delivery.py) | delivery-line check/sync | check: none; live sync: GitHub | receipt/publication/metrics/dashboard during sync | line result and derived delivery artifacts |
| [`delivery_sync.py`](delivery_sync.py) | sync public/compatibility adapter | depends on mode | delegates | normalized sync result |
| [`delivery_sync_impl.py`](delivery_sync_impl.py) | delivery derivation implementation | snapshot or trusted GitHub lane | writes bounded outputs | receipt, publication attestation, metrics, dashboard |
| [`local_verification.py`](local_verification.py) | exact-HEAD local verification | none | receipt/evidence output only | `github-delivery-local-verification/v1` |
| [`github_actions_snapshot.py`](github_actions_snapshot.py) | GitHub raw transport capture/derivation/replay | capture: read-only GitHub; replay: none | transport/observation/snapshot files only | admitted absolute `gh` path/realpath/binary-digest/version plus raw argv/stdout/exit transport and `github-actions-publish-snapshot/v4`, binding the policy workflow path to one provider workflow/run/job/check identity and exact initial branch-ref absence |
| [`ci_publish_gate.py`](ci_publish_gate.py) | CI publication admission | none | none | one ALLOW operation or stable BLOCK reason |
| [`ci_publish.py`](ci_publish.py) | enforced publication wrapper | dry run: none; execute: GitHub capture/publication | git-dir receipts; execute may push/create/update PR | content-addressed `github-actions-publish-decision-manifest/v1`, rendered or executed operation |
| [`merge_gate.py`](merge_gate.py) | merge authority preflight/landing | preflight/land: GitHub and host policy planes | land may request merge after Human Admit | preflight result or merge result |
| [`reference_causality.py`](reference_causality.py) | reference/evidence causality | none | none | causal validation result |
| [`link-canonical.sh`](link-canonical.sh) | canonical Skill projection | none | optional backup + symlink | linked target or divergence refusal |
| [`install-codex-merge-rule.sh`](install-codex-merge-rule.sh) | consumer Codex rule bootstrap | none | user rules directory | narrow repo-scoped rule + backup |

## Public data flow

```text
consumer fixed command contract
→ local_verification.py
→ exact-HEAD local receipt

trusted GitHub raw transport
→ github_actions_snapshot.py capture/replay-transport
→ derived observation
→ normalized snapshot

local receipt + snapshot + intent
→ ci_publish_gate.py
→ ALLOW one operation / BLOCK reason

canonical policy + exact gate inputs + ALLOW operation
→ ci_publish.py
→ git-dir decision manifest binding raw input digests and required check name

owner merge-admit + host/GitHub state
→ merge_gate.py preflight
→ checked-head land request
```

The output of one script is not permission to skip the next state machine.

## Script laws

- Use explicit argv arrays rather than shell strings for untrusted command data.
- Keep environment inheritance allowlisted and bounded.
- Pin every decision to an exact commit/head when the contract requires identity.
- Reject absolute consumer-host paths in portable receipts and shared fixtures.
- Separate zero-network replay/check from trusted network capture.
- Preserve exit semantics; do not map absence, policy skip, or no-runner state to success.
- Do not place secrets, tokens, browser profiles, device sessions, or credential-bearing remote URLs in output.
- Use atomic writes for multi-file derived outputs.
- Never let an Agent-written JSON field self-assert verification authority.

## Exit semantics

Each script documents its exact exits. At the integrated level:

```text
0   owning operation completed or policy ALLOW
1/2 owning verifier rejected or policy BLOCK, according to script contract
3   may represent explicit absence such as no merge-admit in merge preflight
64  malformed/missing input, unsafe state, or inability to determine truth
```

Do not normalize these into a single boolean across scripts.

## Network boundaries

### Zero-network

```text
local_verification.py
github_actions_snapshot.py replay
ci_publish_gate.py
github_delivery.py check
reference_causality.py
link-canonical.sh
focused tests
```

### Trusted network lane

```text
github_actions_snapshot.py capture
github_delivery.py sync --github
merge_gate.py preflight/land
```

Network access does not imply mutation permission. Capture operations are read-only. Merge remains separately admitted.

## Consumer-owned inputs

The shared scripts require consumer-generated inputs such as:

```text
local verification command contract
repository numeric ID
GitHub branch and stable check name
registry lines
artifact and receipt paths
merge-admit label
consumer host policy configuration
```

These values must not be baked into the shared Skill.

## Verification

Run the complete Skill harness:

```bash
bash ../tests/run-all.sh
```

Focused checks:

```bash
python3 ci_publish_gate.py --selftest
python3 local_verification.py --selftest
python3 github_actions_snapshot.py --selftest
```

See [`../tests/README.md`](../tests/README.md) for the mapping between scripts, eval IDs, and negative controls.

## Change rules

When a script adds a state, input, output, effect, exit, or network boundary:

1. update [`../modules/state-machines.md`](../modules/state-machines.md);
2. update [`../evals.json`](../evals.json) before implementation;
3. add positive and hollow/mutation controls;
4. update [`../modules/traceability-index.md`](../modules/traceability-index.md) with the issue and PR;
5. keep the PR molecular and identify its Stacked PR parent or sibling relationship.
