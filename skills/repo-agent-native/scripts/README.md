# Executable assertions

These Bun + TypeScript programs are deterministic hard gates for the portable Skill package and a generated invariant report. They use the JavaScript runtime and Node standard library only, perform no network calls, and do not invoke a model or optional provider.

## `validate-skill.ts`

Input: a Skill directory. Output: a JSON receipt at a caller-selected existing parent directory. It validates portable frontmatter, the line budget, required procedure sections, Markdown link closure, bundled assertion files, the four optional-provider module contracts, and the admitted module-routing case inventory. The immutable legacy baseline remains addressable by the Git identity in `evals/baseline.json` rather than a second Markdown copy.

```bash
bun scripts/validate-skill.ts --skill-root . --json <skill-receipt.json>
```

## `assert-output.ts`

Input: an exact Git repository, a `repo-agent-native/invariant-report/v2` JSON report, and a receipt path. It reads the repository's current commit and source bytes directly from `HEAD:path`, then validates subject binding, source paths/ranges/digests, non-empty success, evidence promotion, absence boundaries, and local/secret-shaped value exclusion. Uncommitted working-tree bytes therefore cannot silently become evidence for the recorded commit.

```bash
bun scripts/assert-output.ts --repo <repo> --report <report.json> --receipt <output-receipt.json>
```

The command is read-only except for the requested receipt. It passes an argument vector directly to Git; it does not evaluate a shell string. Local Git reads have a 10-second timeout and the report input is capped at 4 MiB.

## Exit contract

```text
0   declared subject passed every implemented hard assertion
2   input was evaluable and at least one hard assertion failed
64  command usage, schema, subject, or required input was invalid/absent
70  the assertion mechanism encountered an internal error
```

The JSON receipt is execution evidence for its recorded commit, Skill/report digest, and implemented assertions. It is not live truth about carrier loading, provider health, index freshness, pull-request state, or Human Admit.
