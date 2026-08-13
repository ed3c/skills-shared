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

## `score-ab-output.ts`

Input: a replayable exact-subject repository, one structured report, reviewed ground truth, and the fixed weights in `evals/evals.json`. It first applies `assert-output.ts`, then scores concept-alias matches, negative-invariant recall, implicit-dependency recall, source anchors, named fallback, and forbidden claims. The so-called precision field is deliberately named `anchored_nonforbidden_precision_proxy`: without exhaustive fact-level labels it is not statistical fact precision.

```bash
bun scripts/score-ab-output.ts --repo <repo> --report <report.json> \
  --expected evals/fixtures/retry-service/expected.json \
  --evals evals/evals.json --output <score.json>
```

## `run-ab.ts`

The runner creates a fresh deterministic Git fixture for each condition, installs exactly one package projection after committing the subject, invokes Claude Code or Codex CLI with an argument vector, and records raw output digests, a replayable `subject.bundle`, evaluator digests, the installed package digest, and an instruction-only digest. The four conditions are `no_skill`, `current_skill`, `candidate_skill`, and `wrong_skill`.

```bash
bun scripts/run-ab.ts --carrier <codex|claude> --condition <condition> \
  --case <case> --output <fresh-dir> [--repetitions 1-3] [--execute]
```

Without `--execute`, it writes `NOT_EXERCISED`; it never silently contacts a carrier. Output directories are append-once per run ID. Claude calls use project-only settings, an empty strict MCP set, no session persistence, a one-dollar limit, and safe mode for the `no_skill` control. Codex calls use ephemeral read-only execution, but current Codex user-level Skill isolation is not proven; receipts must retain that limitation.

Model output remains untrusted until deterministic scoring succeeds. One carrier cannot proxy another, and a schema/CLI rejection is a carrier failure rather than a Skill-quality score.

## `compare-ab.ts`

The comparator consumes four physical receipts and fails unless their carrier, scenario, exact fixture, replay bundle, and evaluator digests match. It applies the reviewed minimum quality delta and the `SKILL.md` byte-size context proxy from `evals/evals.json`.

```bash
bun scripts/compare-ab.ts --candidate <receipt.json> --current <receipt.json> \
  --no-skill <receipt.json> --wrong-skill <receipt.json> \
  --evals evals/evals.json --output <comparison.json>
```

Exit `0` is a bounded comparison PASS, not release admission. The receipt names one carrier and one scenario; missing carrier/scenario/repetition evidence stays missing.
