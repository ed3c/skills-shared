# Third-party notices

**Status: active supporting notice.** This file documents what `skills-shared`
actually depends on today, scanned from the tree on 2026-08-18. It ships
alongside the repository's active Apache License 2.0 `LICENSE`; it is not a
license itself and grants no rights.

## Scope of the scan

- No `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, or
  `package.json` exists anywhere in this repository. There is no packaged
  dependency manifest to read.
- No `vendor/`, `node_modules/`, or `third_party/` directory exists. No
  third-party source code, binary, or license text is copied into this
  repository's tracked tree.
- Dependencies were found two ways: (a) `pip install` lines pinned inside
  `.github/workflows/*.yml`, and (b) `import` statements in tracked `.py`
  files. Both are consumption at CI/dev/runtime time, never redistribution —
  this repository does not package, bundle, or ship these libraries to its
  own consumers.

## Direct third-party Python dependencies

| Package | Where it is pinned or imported | License (verified) |
|---|---|---|
| `jsonschema` | Pinned `==4.26.0` in 5 workflows: `skill-eval-contract.yml`, `intent-promotion-authority.yml`, `shared-skills-infra.yml`, `skill-suites.yml`, `forgejo-delivery-loop.yml`. Imported by 2 tracked `.py` files. | MIT — read from installed package metadata (`importlib.metadata` `License-Expression: MIT`) on 2026-08-18, not from memory. |
| `PyYAML` | Pinned `==6.0.3` in 2 workflows: `skill-eval-contract.yml`, `skill-suites.yml`. `import yaml` in `skills/repository-capability-audit/scripts/check_core.py`, `skills/procedural-shadow-runtime/scripts/observe_multimodal.py`, `skills/loop-harness-standard/reference-impl/harness-mvp/tests/test_sc{1,3,5}.py`, and their mirrored copies under `migration/superseded/`. | MIT — `pip show PyYAML` reports `License: MIT` on 2026-08-18. |
| `pytest` | Not pinned in any workflow. `import pytest` in `skills/loop-harness-standard/reference-impl/harness-mvp/tests/test_sc{1,3,5}.py` and the mirrored copies under `migration/superseded/`. Dev/test-only; no CI job installs it explicitly, so it is an ambient-environment assumption today, not a locked dependency. | MIT — `pip show pytest` reports `License: MIT` on 2026-08-18. |
| `playwright` (Python) | Not pinned in any workflow. `import` in `skills/repository-capability-audit/scripts/check_core.py` and `skills/procedural-shadow-runtime/scripts/observe_multimodal.py`. Same ambient-environment caveat as `pytest`. | Apache-2.0 — `importlib.metadata` reports `License-Expression: Apache-2.0` on 2026-08-18. |

None of these four packages' source, binaries, or license text is copied
into this repository. Each is installed independently by whatever environment
runs the script or workflow, under that package's own license, which travels
with the package and is unaffected by the repository's Apache-2.0 license.

## Method provenance for repository entropy reclamation

`skills/repository-entropy-reclamation/` records procedural-method provenance
from these MIT-licensed public sources at immutable commits:

| Source | Exact subject reviewed | Role in the generalized method |
|---|---|---|
| `Yevanchen/reclaim-code-entropy` | commit `491cbff12cdc6988dfb18dec15b2c3bc4db512f1`; `skills/reclaim-code-entropy/SKILL.md`, `README.md`, `README.zh.md` | Contract-first survey, consumer/history/ownership proof, candidate classes, ownership-boundary cuts, decisive verification, and acceptance of an empty safe-cut set. |
| `deepseek-ai/deepseek-harness` | commit `99f6f02fecdb7dff40c3fbc9470f5907c29f74ca`; `.agents/skills/dsh-find-simplifications/SKILL.md` | Broad simplification survey, trust/lifecycle ownership, dependency-substitution bar, proposal coalescing, repository-context-first review, and PR hygiene. |

No source file or source tree from either repository is vendored or copied.
The shared Skill, schema, verifier, controls, adapters, and documentation are
newly authored, domain-neutral expressions under this repository's
Apache-2.0 license. DeepSeek-specific package names, Agent Note locations,
`pnpm`/`knip`/Cordis/ACP/MCP conventions, commands, paths, and current state
remain consumer-owned adapter facts rather than portable law. The more exact
mapping, exclusions, and license boundary live in
`skills/repository-entropy-reclamation/references/UPSTREAM_LINEAGE.md`.

## Verification caveat

The package license values above were read from locally installed package
metadata in the worker's environment on 2026-08-18 (`pip show` /
`importlib.metadata` `License-Expression` and `License` fields), not fetched
from each project's canonical repository or PyPI project page. Package
metadata self-reports its license and is generally reliable. Re-confirm current
terms from each project's canonical source whenever a pinned version changes
or before a release begins redistributing third-party source or binaries.

The two method-source licenses and immutable source identities above were
reviewed from their public repository files for this integration. Re-check the
exact pinned commits and their license files before redistributing any future
verbatim source material; this repository currently redistributes none.

## Generated output and content boundary

This repository's Python scripts are verification/CI tooling; none trains,
fine-tunes, or bundles a model, dataset, or model weights, so there is no
model/dataset license question in scope. Skill bodies (`SKILL.md`, `modules/`,
`references/`) are original prose and code authored for this repository. The
repository may record attributed method provenance, as above, without copying
third-party prose or code. If any Skill later incorporates external
text/code/standards content, that Skill's own directory must record its source
and license separately — this file only covers repository-wide Python tooling
dependencies and the method provenance explicitly listed here.
