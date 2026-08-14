# Output Contract

## Canonical subject

A run produces a source-anchored invariant report plus a machine-readable assertion subject. The report may be Markdown; the assertion subject is JSON.

Suggested output location:

```text
docs/plans/<date>-<topic>/invariants/<scope>/
├── invariants.md
└── invariants.json
```

The consumer may choose another repository-local path in the task packet. The Skill must not invent an absolute output path.

## JSON shape

```json
{
  "schema": "repo-agent-native/invariant-report/v2",
  "subject": {
    "repository": "owner/name-or-local-id",
    "observed_commit": "40-hex-or-null",
    "observed_tree": "tree-or-null",
    "scope": ["repository-relative paths"],
    "task": "short task identity"
  },
  "routes": [],
  "tools": [],
  "facts": [
    {
      "id": "INV-001",
      "class": "api-contract",
      "claim": "One precise claim",
      "predicate": {
        "id": "domain.contract-name",
        "operator": "equals",
        "value": "independently-observable-scalar"
      },
      "evidence_level": "A",
      "source_refs": [
        {
          "path": "src/example.ts",
          "start_line": 10,
          "end_line": 18,
          "blob_sha256": "optional"
        }
      ],
      "verification": ["source-read"],
      "depends_on": [],
      "exclusions": []
    }
  ],
  "negative_invariants": [],
  "implicit_dependencies": [],
  "open_questions": [],
  "named_exclusions": [],
  "state": "PASS"
}
```

`predicate` is the machine comparison surface. Its ID is preregistered by the fixture contract, its value is a scalar, and its source is independently re-observed from the exact Git subject. `claim` remains human-readable explanation; wording or concept aliases cannot satisfy the predicate.

`verification` uses a closed vocabulary: `source-read`, `document-read`, `manifest-read`, `test-executed`, `runtime-observed`, and `inference`. Every `A`/`A-` source claim or candidate-provider promotion must contain the exact token `source-read`. Put descriptive detail in the claim or tool observation; do not invent synonymous tokens that force a hard assertion to guess.

## Markdown shape

```text
Subject and source identity
Scope and named exclusions
Repository document routes consulted
Tool health and fallbacks
Positive invariants
Negative invariants
Implicit dependencies and failure chains
Open questions
Assertion summary
```

Each invariant contains claim, fact class, evidence level, and source refs. Avoid paragraphs that combine several independently testable claims under one anchor.

## Hard assertions

- `schema` is recognized.
- subject repository/scope is non-empty.
- accepted state uses the common evidence vocabulary.
- every accepted fact has at least one repository-relative source ref.
- every scored record has one unique, preregistered structured predicate whose value and declared source match independent source observation.
- line numbers are positive and ordered.
- referenced files exist in the exact source subject.
- ranges are inside the file.
- optional recorded digests match.
- `B+`, `C`, and memory-derived candidates cannot appear as accepted `A` facts without an explicit read-back lane.
- `D` hypotheses appear only in `open_questions`.
- no absolute host path, secret-shaped value, browser/device session, mutable credential, or raw memory record is present.
- named exclusions and unexercised lanes remain visible.

## Procedure receipt

The scorer emits evidence in three non-interchangeable lanes:

```text
verifier_observed       subject/source/absence checks executed by deterministic code
artifact_asserted       required output groups exist in the produced artifact
model_reported_advisory routes/tools/fallback prose reported by the model
```

Only the first two participate in the bounded procedure contract. `model_reported_advisory` and lexical alias matching have `admission_effect: none`; neither proves that a tool ran nor that the portable procedure generalized.

## Exit semantics

```text
0   all hard assertions pass
2   report is well-formed enough to evaluate but one or more assertions fail
64  usage, schema, source subject, or required input is absent/invalid
70  internal assertion mechanism error
124 timeout
```

The Agent must not loop without a bound. The task packet defines a maximum repair count. When exhausted, return the failed assertion report and named blockers.

## Mechanism identity

Per-run output, timestamps, temporary paths, model prose, and volatile tool caches do not enter the Skill mechanism digest. Versioned scripts, schemas, fixtures, module contracts, and the canonical `SKILL.md` do.
