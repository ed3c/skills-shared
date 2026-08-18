# Repository License Decision — Apache-2.0 Active

<!--
  Governance SSOT for repository-level licensing.
  Issue: #360
  Decision activated: 2026-08-18
-->

**Status:** `ACTIVE_WITH_FOLLOW_UP_GOVERNANCE`

**Selected repository license:** Apache License 2.0  
**SPDX identifier:** `Apache-2.0`  
**Effective date:** 2026-08-18  
**Decision authority:** repository owner (`ed3c`)

This document records the active license policy for `skills-shared`. It is no
longer a pending decision packet. The repository root now contains the exact
Apache License 2.0 text in `LICENSE`, owner attribution in `NOTICE`, and active
third-party dependency facts in `THIRD_PARTY_NOTICES.md`.

## 1. Authoritative policy

1. Repository-authored source code, documentation, Skills, schemas, examples,
   tests, workflows, and governance material are licensed under Apache-2.0
   unless a file or subtree carries a more specific valid notice.
2. Third-party source, binaries, packages, datasets, models, standards text,
   trademarks, and other externally governed material retain their original
   licenses and terms. Apache-2.0 does not overwrite those rights.
3. Third-party provenance must remain traceable through
   `THIRD_PARTY_NOTICES.md`, Skill-local `sources.json` files, source ledgers,
   or equivalent evidence records.
4. The repository is not dual-licensed by default. Any future additional
   license requires an explicit owner decision and a copyright/compatibility
   review.
5. Repository visibility, ownership, access rights, and contribution authority
   are unchanged by this license activation.

## 2. Why Apache-2.0 was selected

Apache-2.0 fits this repository's intended use as reusable Agent Skills and
engineering infrastructure because it provides:

- permissive commercial use, modification, and redistribution;
- an explicit contributor patent grant and patent-termination condition;
- clear redistribution, attribution, modified-file, and NOTICE obligations;
- broad compatibility with enterprise adoption and downstream tooling; and
- a standard SPDX identifier understood by GitHub, package registries, SBOM
  tooling, scanners, and policy engines.

The license is permissive; it is not copyleft. Downstream users may combine the
Work with proprietary systems while continuing to satisfy Apache-2.0 and all
applicable third-party terms.

## 3. Historical pre-activation state

Before 2026-08-18 the repository had no root `LICENSE`, so GitHub reported no
repository license. Issue #360 therefore requested a decision packet rather
than an autonomous license selection. The owner subsequently selected
Apache-2.0, resolving that authority boundary.

Historical comparison retained for traceability:

| Candidate | Main benefit | Main limitation | Decision |
|---|---|---|---|
| MIT | Very short and broadly familiar | No explicit patent grant or NOTICE mechanism | Not selected |
| Apache-2.0 | Permissive plus patent and NOTICE terms | More compliance text than MIT | **Selected** |
| MPL-2.0 | File-level copyleft | Adds reciprocal obligations not required here | Not selected |
| GPL-3.0 | Strong copyleft | Too restrictive for intended reusable infrastructure | Not selected |
| AGPL-3.0 | Network copyleft | Too restrictive for intended service integration | Not selected |
| Proprietary/custom | Maximum control | Conflicts with open-source interoperability goals | Not selected |

This table explains the decision; it does not create alternate licenses.

## 4. Asset and boundary classification

### Repository-authored material

The Apache-2.0 grant covers repository-authored material, including:

- `SKILL.md` files and associated modules/references;
- Python and shell verification tooling;
- schemas, fixtures, workflows, tests, and examples;
- architecture, governance, and operating documentation; and
- generated artifacts only to the extent the repository owns the relevant
  copyright and no generator/output-specific terms apply.

### Third-party material

The repository license does not grant rights the project does not own. The
following remain under their own terms:

- Python packages and other dependencies installed by CI or operators;
- external repositories, tools, APIs, datasets, models, and standards;
- copied or vendored components, if introduced later;
- names, logos, service marks, and other trademarks; and
- user-provided or externally generated content.

A new vendored or redistributed third-party component must be admitted only
with source, version, license, notice, and compatibility evidence.

## 5. Activated repository files

| File | Active role |
|---|---|
| `LICENSE` | Exact Apache License 2.0 legal text and repository-wide license anchor |
| `NOTICE` | Repository attribution: `skills-shared`, Copyright 2026 ed3c |
| `THIRD_PARTY_NOTICES.md` | Active inventory and scope statement for direct third-party dependencies |
| `docs/governance/LICENSE_DECISION.md` | Decision history, policy boundary, and governance SSOT |

Draft copies under `docs/governance/drafts/` are historical preparation
artifacts. They do not override the active root files.

## 6. Contribution policy

Unless a contributor explicitly states otherwise, an intentional contribution
submitted for inclusion in the Work is accepted under Apache-2.0 section 5,
without additional terms. No separate Contributor License Agreement is active
at this time.

Before adopting a CLA or Developer Certificate of Origin, the repository owner
must define the operational need, contributor workflow, identity/evidence
requirements, and compatibility with existing contributions.

## 7. Metadata requirements

- Any package manifest or release metadata that exposes a project license must
  use the SPDX value `Apache-2.0`.
- GitHub's repository license detector must resolve the root `LICENSE` as
  Apache-2.0.
- SBOM, provenance, and release receipts must distinguish the repository's
  Apache-2.0 license from dependency-specific licenses.
- README links or badges may be added for discoverability, but their absence
  does not weaken or replace the active root license.

## 8. Change control

A future license change requires all of the following:

1. explicit approval from the repository owner;
2. identification of all relevant copyright holders and contributions;
3. compatibility analysis for third-party and previously distributed material;
4. updates to `LICENSE`, `NOTICE`, metadata, governance docs, and release
   evidence in one traceable change set; and
5. preservation of the terms that applied to versions already distributed.

Agents must not infer permission to relicense third-party material, change
repository visibility, transfer ownership, or alter access rights from this
policy.

## 9. Verification checklist

- [x] Root `LICENSE` contains the exact Apache License 2.0 text.
- [x] SPDX identifier is `Apache-2.0`.
- [x] Root `NOTICE` preserves owner attribution.
- [x] `THIRD_PARTY_NOTICES.md` is active and distinguishes consumption from redistribution.
- [x] Third-party license records remain intact.
- [x] No repository visibility, ownership, or access-right change was made.
- [ ] Add automated CI validation for root license text and exposed manifest metadata.
- [ ] Re-check third-party licenses whenever dependency versions or redistribution behavior change.

## 10. Traceability

- Decision request: issue #360
- Activation date: 2026-08-18
- License identifier: `Apache-2.0`
- Repository attribution: `NOTICE`
- Third-party evidence: `THIRD_PARTY_NOTICES.md` and Skill-local source records

This document is the current repository-level licensing decision record.
Where it conflicts with historical draft wording, this active record and the
root legal files govern the current repository state.
