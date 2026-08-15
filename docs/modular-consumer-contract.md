# skills-shared modular consumer contract

## One lifecycle, two transports

Canonical SSOT → registered Skills → consumer requirements → resolved binding → carrier adapter → receipt/control.

- Local host adapter: `shared_skills.py install` creates symlinks for immediate development projection.
- Immutable adapter: `shared_skills.py sync` resolves a clean exact commit into a requirements-filtered binding.
- The binding contains only credential-free repository identity, commit/tree, requirements/registry/per-Skill digests, and repo-relative surfaces.

## Consumer files

A consumer owns `.agents/shared-skills.requirements.json` and generates:

```sh
python3 skills/shared-skills-infra/scripts/shared_skills.py sync \
  --requirements <consumer>/.agents/shared-skills.requirements.json \
  --target-root <consumer> --apply
```

The result is `.agents/bindings/<binding>.json`. `--check` verifies freshness without writing; no mode is dry-run.

## Failure and rollback

Unknown names, shared/repo-owned overlap, dirty source, unsafe surfaces, and stale binding fail closed. Rollback checks out an older clean immutable source and re-runs the same sync. A symlink or mutable branch is never release identity.
