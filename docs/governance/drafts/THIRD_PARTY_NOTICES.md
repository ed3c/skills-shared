# Third-party notices (draft)

**Status: draft, not activated.** This file documents what `skills-shared`
actually depends on today, scanned from the tree on 2026-08-18. It ships
alongside whichever `LICENSE` the copyright owner activates; it is not a
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
with the package and is unaffected by whichever license `skills-shared`
activates.

## Verification caveat

The license values above were read from locally installed package metadata
in the worker's environment on 2026-08-18 (`pip show` / `importlib.metadata`
`License-Expression` and `License` fields), not fetched from each project's
canonical repository or PyPI project page. Package metadata self-reports its
license and is generally reliable, but before this file is activated the
Human owner should re-confirm current license terms directly from each
project's PyPI page or upstream `LICENSE` file, since a package can relicense
between versions and the version actually resolved in a given environment
can drift from the pins recorded above.

## Generated output and content boundary

This repository's Python scripts are verification/CI tooling; none trains,
fine-tunes, or bundles a model, dataset, or model weights, so there is no
model/dataset license question in scope. Skill bodies (`SKILL.md`, `modules/`,
`references/`) are original prose and code authored for this repository; no
third-party prose, proprietary standards text, or scraped content was found
during this scan. If any Skill later incorporates external
text/code/standards content, that Skill's own directory must record its
source and license separately — this file only covers repository-wide
Python tooling dependencies.
