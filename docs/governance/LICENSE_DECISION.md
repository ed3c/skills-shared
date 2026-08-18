# License decision — skills-shared

**Status: `HUMAN_ADMIT_REQUIRED`.** This document is a decision-complete
packet for issue #360. It compares candidate licenses against this
repository's actual facts and ends in a recommendation, but it does not
activate anything: no root `LICENSE` file exists in this repository and this
document does not create one. License selection, copyright assertion,
contributor policy, dual-licensing and trademark policy remain the
copyright owner's decision, per #360's own "Human boundary" section.

## 1. Problem

GitHub reports `license: null` for `skills-shared`. The repository is
consumed by public and private Agent projects, but absent license metadata
grants no one — including the four integrated repositories described in
[`../integration/CROSS_REPO_INTEGRATION.md`](../integration/CROSS_REPO_INTEGRATION.md)
— any right to commercial use, modification, redistribution, hosted use, or
derivative Skills. This is #360's framing and this document does not
relitigate it.

## 2. What this document is and is not

- **Is:** a comparison of MIT and Apache-2.0 against this repository's real
  dependency graph, integration shape, and the nine-item decision packet
  #360 requires, plus ready-to-activate drafts and a recommendation.
- **Is not:** a license activation. `closeable=false` on #360 until the
  owner makes and records this decision.

## 3. Facts gathered from this repository

### 3.1 Dependency inventory (scanned 2026-08-18, tree at `306f75c`)

No `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, or
`package.json` exists anywhere in the tree — there is no packaged Python or
Node dependency manifest. No `vendor/`, `node_modules/`, or `third_party/`
directory exists, and no `SPDX-License-Identifier` header or embedded
`Apache License` / `MIT License` / `BSD License` text was found in any
tracked source file. **Nothing third-party is vendored into this
repository's tracked tree.** The repository's own runtime is Python
stdlib plus four externally-installed packages, all consumed at CI or dev
time and never redistributed:

| Package | License (verified) | How it enters |
|---|---|---|
| `jsonschema` | MIT | Pinned `==4.26.0`, `pip install`ed in 5 GitHub Actions workflows |
| `PyYAML` | MIT | Pinned `==6.0.3`, `pip install`ed in 2 workflows |
| `pytest` | MIT | Imported by test files under `skills/loop-harness-standard/reference-impl/`; not pinned in any workflow (ambient-environment assumption) |
| `playwright` (Python) | Apache-2.0 | Imported by 2 scripts under `skills/repository-capability-audit/` and `skills/procedural-shadow-runtime/`; not pinned in any workflow |

Full evidence and per-file citations are in
[`drafts/THIRD_PARTY_NOTICES.md`](drafts/THIRD_PARTY_NOTICES.md). The
license values were read from installed package metadata
(`importlib.metadata` `License-Expression` / `pip show License`) in this
worker's environment, not fetched from each upstream project — the draft
carries an explicit caveat asking the owner to re-confirm before activation.

Because nothing is vendored, **there is no copyleft-contamination risk from
redistributed third-party source** under either candidate license. The only
question either candidate has to answer is what obligations attach to
*this repository's own* Markdown Skill bodies and Python scripts when
someone else copies or redistributes them.

### 3.2 Four-repository integration and existing precedent

Per [`../integration/CROSS_REPO_INTEGRATION.md`](../integration/CROSS_REPO_INTEGRATION.md),
`skills-shared` is the Instruction/Method plane; `runtime-env`,
`bettor-arena`, and `agent-shield-monorepo` consume its releases downstream
through "immutable Skill release → requirements/binding → resolved
runtime → composition → product." This is not a packaging/`import`
relationship — consumers pull an exact commit/tree, not an installed
library — but it is a redistribution relationship: Skill bodies and scripts
are copied or symlinked into each consumer's own checkout.

`runtime-env`'s own `LICENSE` (read read-only at `/Users/neon/runtime-env/LICENSE`,
not modified) is:

```text
MIT License
Copyright (c) 2026 ed3c
```

— byte-identical in structure to the MIT draft in this packet. This is a
real precedent for MIT inside the same four-repository stack, and any
Apache-2.0 recommendation below has to be weighed against that existing
choice, not made in isolation.

### 3.3 No prior release to migrate

`git tag` on this worktree returns no tags, and no root `LICENSE` file has
ever existed. There is no "existing release" whose terms a new license
would have to be reconciled against, and no rollback case where a later
license contradicts an earlier one distributed to someone already relying
on it (see §6 for what changes once a license *is* activated).

### 3.4 What this repository actually is

The tree is `SKILL.md` procedural bodies, `modules/`/`references/`
know-how, and Python verification scripts (schema checkers, gates,
receipt validators) — a **methods-and-contracts repository**, not a
data/model/content repository. There is no model weight, dataset, or
generated-output artifact in scope (confirmed in the dependency scan,
§3.1). The patent-grant question in #360's decision packet is about
whether the *procedures themselves* — e.g. the closure-law and
mutation-lineage checking methods this repository documents — could later
be read as practicing a patent claim, not about any bundled dataset.

### 3.5 Signal already present about private extensions

`skill-bettor` and `ts-skill-bettor` are excluded from this worker's scope
by the repository owner and were not read or touched to produce this
document. Their mere existence as separate, non-`skills-shared` checkouts
is itself evidence that the owner already operates a private-extension
model alongside this shared repository. That is exactly the fact pattern
#360's "private extension and dual-license policy, if any" packet item asks
about; this document surfaces it and does not resolve it (§7).

## 4. The nine-item decision packet, against these facts

| # | Packet item | What the facts say | Still open |
|---|---|---|---|
| 1 | Copyright owner and contributor provenance | `evals/commit-roles.json` treats every commit as `human` or one of several `machine` drivers under one repository identity; there is no multi-party CLA/DCO history. Task-supplied copyright line: `ed3c`, 2026. | Whether external (non-owner) contributions will ever be accepted, and under what provenance terms — not yet the case today. |
| 2 | Intended commercial/open-source rights | #360 states public and private Agent projects, including commercial products (`bettor-arena`, `agent-shield-monorepo`), must be able to use, modify, redistribute, and host derivative Skills. Both MIT and Apache-2.0 grant this; a copyleft license would not (see §5). | — |
| 3 | Patent-grant requirement | This is a methods/contracts repository (§3.4). Apache-2.0 §3 grants an explicit, irrevocable (except on litigation) patent license from every Contributor; MIT is silent on patents — any patent license is at best implied and untested in this repository's jurisdiction. | Whether the owner considers patent exposure from procedural-method claims a real risk worth the extra license weight (see §6). |
| 4 | Copyleft/network-copyleft tolerance | #360's own framing (commercial use, hosted use, private extensions) is incompatible with GPL/AGPL-style copyleft. Neither MIT nor Apache-2.0 is copyleft, which is why both remain candidates and GPL/AGPL are excluded outright (§5). | — |
| 5 | Trademark and hosted-service boundary | MIT's text does not mention trademarks at all. Apache-2.0 §6 explicitly withholds any trademark license except for descriptive/NOTICE use. If "skills-shared" or "ed3c" is ever asserted as a mark, Apache-2.0 states the boundary in the license text itself; MIT leaves it entirely to a separate policy. | A standalone trademark policy is listed in #360 as a required repository output, separate from the LICENSE file itself, and is not drafted here. |
| 6 | Third-party content and generated-output treatment | §3.1: four externally-installed packages, all permissively licensed (MIT ×3, Apache-2.0 ×1), none vendored. §3.4: no model/dataset artifact in scope. Draft: [`drafts/THIRD_PARTY_NOTICES.md`](drafts/THIRD_PARTY_NOTICES.md). | Re-verify the four license values against each upstream project directly before activation (caveat already in the draft). |
| 7 | Consumer redistribution requirements | MIT requires only that copies retain the copyright + permission notice. Apache-2.0 additionally requires stating what files a redistributor changed (§4(b)) and passing through NOTICE contents (§4(d)). Given §3.2's actual redistribution pattern (consumers copy/symlink Skill bodies into their own checkouts), Apache-2.0 is a small but real extra compliance step for `bettor-arena`/`agent-shield-monorepo`; MIT is close to friction-free. | Whether the owner wants that extra passthrough discipline enforced on downstream consumers, or wants MIT's lower friction instead. |
| 8 | Private extension and dual-license policy, if any | §3.5: the excluded sibling repos are evidence such a model may already exist informally. Neither MIT nor Apache-2.0 by itself blocks the owner from *also* keeping other repositories fully private/unlicensed — a public permissive license on `skills-shared` says nothing about `skill-bettor`/`ts-skill-bettor`'s status. | Whether the owner wants an explicit written dual-license or private-extension statement alongside the public LICENSE. Not drafted here — out of this document's scope per the CROSS-REPO RULE excluding those repos. |
| 9 | Rollback/migration effect on existing releases | §3.3: no tags, no prior `LICENSE`, nothing to migrate away from. Once a license is activated and published, copies already distributed under it keep those rights permanently (neither MIT nor Apache-2.0 is revocable) — activation is a one-way grant for whatever has already gone out, even if the owner later swaps the license going forward. | None — this is a fact about how licensing works, not an open question. |

## 5. Candidates excluded from this packet, briefly

#360 names only MIT and Apache-2.0 as candidates; this document does not
introduce new candidates on its own initiative. For completeness against
packet item 4 (copyleft tolerance): GPL/AGPL-style copyleft is
incompatible with #360's explicit commercial/private-consumption goal and
is excluded on that basis alone, not compared further. Public-domain-style
options (Unlicense/CC0) were not named by the issue and are not evaluated
here; they would also forfeit the patent-grant and NOTICE-passthrough
properties that motivate the Apache-2.0 side of this comparison.

## 6. Recommendation

**Recommend Apache-2.0**, with the tradeoff stated plainly rather than
hidden:

- **For:** explicit patent grant (§3.4, packet item 3) matters more here
  than in an average repository, because the tree's actual content is
  *procedures* — verification methods, closure laws, mutation-lineage
  checks — and Apache-2.0 is the only one of the two candidates that says
  anything about patent claims at all. Its trademark carve-out (packet
  item 5) also gives a cleaner starting boundary than MIT's silence, ahead
  of the separate trademark-policy document #360 requires.
- **Against:** it imposes a real, if small, extra obligation
  (§4(b) changed-files notice, §4(d) NOTICE passthrough) on the exact
  redistribution pattern this repository's own consumers already use
  (§3.2), and it breaks precedent with `runtime-env`'s existing MIT choice
  inside the same four-repository stack — a licensing seam at exactly the
  boundary where these repositories are otherwise deliberately kept
  consistent.

If the owner weighs stack-wide consistency with `runtime-env` and
near-zero redistribution friction for `bettor-arena`/`agent-shield-monorepo`
more heavily than patent-grant language for a procedures repository, **MIT
is the defensible other choice** and its draft is equally ready to
activate. This is a judgment call between two legitimate permissive
licenses, not a case where one candidate fails a hard constraint — which is
exactly why #360 reserves it for Human/Legal admission rather than treating
it as automatic.

## Activation record

**2026-08-18 — the owner selected Apache-2.0** (decision given interactively
in the delivery session). `LICENSE`, `NOTICE` and `THIRD_PARTY_NOTICES.md`
were activated at the repository root from the drafts below, byte-identical.
The MIT draft remains staged as the record of the road not taken. From this
commit on, statements above saying no root `LICENSE` exists describe the
pre-activation state this decision was made in, not the current tree.

## 7. Left explicitly to the human owner

Per #360's own "Human boundary": license selection, copyright assertion,
contributor policy (CLA/DCO), dual-licensing across the excluded private
repos, and trademark policy are not decided here. Also unresolved by this
document, listed so the omission does not read as completeness:

- Re-verifying the four dependency license values directly against
  upstream (§3.1 caveat, already written into the draft).
- Whether external contributions will ever be accepted, and under what
  provenance terms (packet item 1).
- A standalone trademark policy document (packet item 5) — this document
  only notes what each candidate license text does or does not say about
  trademarks.
- A `CONTRIBUTING.md` / DCO / CLA decision, SPDX + CycloneDX SBOM
  generation for released bundles, and a release-blocking checker for
  missing/unknown/forbidden license state — all listed in #360 as
  "Required repository outputs after admission," downstream of this
  decision and not drafted in this packet.

## 8. Ready-to-activate drafts and one-command activation

Everything below is a **draft**, staged under `docs/governance/drafts/`.
None of it has been copied to the repository root. No root `LICENSE` file
exists in this worktree.

| File | Purpose |
|---|---|
| [`drafts/LICENSE.mit`](drafts/LICENSE.mit) | Full MIT text, `Copyright (c) 2026 ed3c`, byte-identical in structure to `runtime-env`'s activated `LICENSE`. |
| [`drafts/LICENSE.apache-2.0`](drafts/LICENSE.apache-2.0) | Full unmodified Apache License 2.0 text (with its own standard boilerplate appendix), preceded by a `Copyright 2026 ed3c` header. |
| [`drafts/NOTICE`](drafts/NOTICE) | Apache-2.0-only attribution file; not applicable if MIT is activated. |
| [`drafts/THIRD_PARTY_NOTICES.md`](drafts/THIRD_PARTY_NOTICES.md) | Real dependency scan with evidence citations, usable under either candidate. |

Activation is one copy command per candidate, run by the owner — this
worker does not run either:

```bash
# If MIT is admitted:
cp docs/governance/drafts/LICENSE.mit LICENSE
cp docs/governance/drafts/THIRD_PARTY_NOTICES.md THIRD_PARTY_NOTICES.md
```

```bash
# If Apache-2.0 is admitted:
cp docs/governance/drafts/LICENSE.apache-2.0 LICENSE
cp docs/governance/drafts/NOTICE NOTICE
cp docs/governance/drafts/THIRD_PARTY_NOTICES.md THIRD_PARTY_NOTICES.md
```

After either copy, the remaining "Required repository outputs after
admission" items in #360 (README/registry license metadata, SPDX/CycloneDX
SBOM, the release-blocking checker, `CONTRIBUTING.md`/CLA policy) are
follow-on work, not covered by this packet.
