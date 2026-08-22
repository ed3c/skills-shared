# References

Host-neutral contracts. Nothing here names a product, a provider, a repository
or a machine. Every schema is Draft 2020-12, every object is closed at every
level, and every positive example and refusal control travels inside the schema
that judges it.

| File | Owns |
|---|---|
| [`contracts/controlled-vocabulary.md`](contracts/controlled-vocabulary.md) | the fifteen closed terms, their producer, their consumer, and what each can never become |
| [`contracts/public-private-capability.md`](contracts/public-private-capability.md) | which plane owns which content, and why the split is ownership rather than redaction |
| [`schemas/source-packet.schema.json`](schemas/source-packet.schema.json) | one immutable external artifact, identified by content and never by location |
| [`schemas/candidate-record.schema.json`](schemas/candidate-record.schema.json) | one external technology, its nine independent rights planes, and its observed-targets ceiling |
| [`schemas/violation-candidate.schema.json`](schemas/violation-candidate.schema.json) | one suspected invariant breach, its evidence basis, and how its graph edges were obtained |
| [`schemas/refactor-proposal.schema.json`](schemas/refactor-proposal.schema.json) | one bounded remedy, and the three blacklisted mechanism-to-property pairs out of fifty-four |
| [`schemas/change-unit.schema.json`](schemas/change-unit.schema.json) | one applied change, its complete path denominator, and its single-valued merge admission |
| [`schemas/verification-receipt.schema.json`](schemas/verification-receipt.schema.json) | what one arrival observed, with a denominator behind every ratio |
| [`schemas/closure-record.schema.json`](schemas/closure-record.schema.json) | the terminal statement, its two independent arrivals, and every lane including the empty ones |
| [`schemas/source-disposition.schema.json`](schemas/source-disposition.schema.json) | the shape of a source adjudication and its mandatory replayable control |
| [`source-disposition/refused-claims.json`](source-disposition/refused-claims.json) | the seven refused claims from the admitted source packet, each with a negative control |

### Deterministic fact plane

The frozen interface the fact-plane adapter lanes implement. Nothing here names
a parser, an indexer, a database or a compatibility checker; a provider appears
only as an opaque binding identifier plus the digests that make its run
replayable.

| File | Owns |
|---|---|
| [`schemas/exact-source-subject.schema.json`](schemas/exact-source-subject.schema.json) | the one subject every fact is about, and a diff with no key for a head of its own |
| [`schemas/syntax-match.schema.json`](schemas/syntax-match.schema.json) | one matched region, the range vocabulary, and the query and grammar digests that make it replayable |
| [`schemas/symbol-fact.schema.json`](schemas/symbol-fact.schema.json) | symbols, occurrences and relationships, each identity scoped to a named normalization |
| [`schemas/coverage-ceiling.schema.json`](schemas/coverage-ceiling.schema.json) | how much one provider reached, with omissions that force the completeness value down |
| [`schemas/architecture-invariant.schema.json`](schemas/architecture-invariant.schema.json) | the admission ledger row behind a violation candidate's `invariant_ref` |
| [`schemas/blast-radius-path.schema.json`](schemas/blast-radius-path.schema.json) | one traversal, its admitted edge set, and the bounds that stopped it |
| [`schemas/contract-compatibility-result.schema.json`](schemas/contract-compatibility-result.schema.json) | one interface comparison against a pinned baseline, and the deployments it does not clear |
| [`schemas/fact-plane-receipt.schema.json`](schemas/fact-plane-receipt.schema.json) | one normalized provider bundle, its ledger row, and the task pass it is not |

### Semantic context plane

Optional by construction. Every contract here can express `NOT_APPLICABLE`, and
no object in this group has a key for a locator, a body or a private identity.

| File | Owns |
|---|---|
| [`schemas/semantic-document.schema.json`](schemas/semantic-document.schema.json) | one registered document, its visibility, and the plane it is allowed to be stored in |
| [`schemas/source-back-reference.schema.json`](schemas/source-back-reference.schema.json) | the exact blob, ledger event or packet a stored row points at, and never a second row |
| [`schemas/projection-receipt.schema.json`](schemas/projection-receipt.schema.json) | one embedding call, its provider and model binding, and the correctness it does not establish |
| [`schemas/retrieval-query.schema.json`](schemas/retrieval-query.schema.json) | one bounded query, including the lane that was never entered |
| [`schemas/retrieval-result.schema.json`](schemas/retrieval-result.schema.json) | rows with exact back references, and a not-applicable outcome that cannot carry rows |
| [`schemas/consumed-context-row.schema.json`](schemas/consumed-context-row.schema.json) | one manifest entry for context actually read, fixed at candidate grade and context-only influence |
| [`schemas/semantic-freshness-ceiling.schema.json`](schemas/semantic-freshness-ceiling.schema.json) | how old one document is, what superseded it, and the four things it never becomes |
| [`schemas/semantic-index-lifecycle-receipt.schema.json`](schemas/semantic-index-lifecycle-receipt.schema.json) | rebuild, delete and compact, and the task state none of them moves |

### Synthesis plane

The X1 output half. These three contracts are what
[`../synthesis/compile_synthesis.py`](../synthesis/compile_synthesis.py)
emits and refuses against; the compiler ships beside its own selftest and is
routed through the suite entrypoint.

| File | Owns |
|---|---|
| [`schemas/review-card.schema.json`](schemas/review-card.schema.json) | one synthesized review verdict, bound to the immutable result tree, with recommendation never promoted to decision |
| [`schemas/synthesis-packet.schema.json`](schemas/synthesis-packet.schema.json) | the full dual-track projection over one exact subject, every measurement carrying its method and denominator |
| [`schemas/problem-closure-row.schema.json`](schemas/problem-closure-row.schema.json) | one claim's closure state and the arrivals that support it, with the empty lanes still written out |

### Bounded refactor plane

The R1 output half. These four contracts are what
[`../refactor/compile_r1.py`](../refactor/compile_r1.py) emits and refuses
against, one per state group of the bounded single-repository refactor protocol.
Nothing here names a rewrite library: a language adapter is a declared
capability class with pinned version, license, grammar and formatter behavior,
and `vendored` is const false because no adapter implementation ships behind
this contract. The compiler ships beside its own selftest and is routed through
the suite entrypoint.

| File | Owns |
|---|---|
| [`schemas/refactor-usage-signature.schema.json`](schemas/refactor-usage-signature.schema.json) | the provider members one violation actually consumes, the call sites that justify each, and the completeness an unresolved call site forces down |
| [`schemas/refactor-minimal-port.schema.json`](schemas/refactor-minimal-port.schema.json) | the Port the owning high-level module declares, with no field for a member no call site justifies |
| [`schemas/refactor-changeset-lease.schema.json`](schemas/refactor-changeset-lease.schema.json) | what the change was allowed to touch and what it touched, the frozen oracles it is measured against, and its single-valued merge admission |
| [`schemas/refactor-r1-receipt.schema.json`](schemas/refactor-r1-receipt.schema.json) | the states one run entered and its terminal, with `CANDIDATE_RECEIPT`, `BLOCKED` and `ROLLED_BACK` kept apart and applied-on-a-real-codebase pinned false |

### Cross-repository expand-contract plane

The R2 output half, landed 2026-08-22. These two contracts are what
[`../expand-contract/compile_r2.py`](../expand-contract/compile_r2.py) emits
and refuses against; their twenty-eight refusal controls are replayed by
[`../expand-contract/selftest.py`](../expand-contract/selftest.py) rather than
by the C0 harness.

| File | Owns |
|---|---|
| [`schemas/refactor-r2-binding.schema.json`](schemas/refactor-r2-binding.schema.json) | one repository binding of a multi-repository subject, with its own rollback identity and per-binding disposition |
| [`schemas/refactor-r2-receipt.schema.json`](schemas/refactor-r2-receipt.schema.json) | the C1→A1→A2→E1→C2 states one run entered, the dual-run lane closed over OBSERVED/NOT_OBSERVED/NOT_EXERCISED, the STOPPED_WITH_ROLLBACK truthful stop, and protocol_ready pinned false |

## Schema identity

Two identifiers, doing different jobs. `$id` is the file, following the sibling
convention of a prefixed bare filename. `properties.schema.const` is the
artifact identity that appears inside every instance, in the form
`dtcr/<artifact>/v1`. A consumer binds the second; the first only resolves
`$ref` inside one document, since no schema here refers to another.

## Control cases

Each schema carries its own controls rather than shipping them as separate
fixtures:

```text
examples                 the positive instance, a standard 2020-12 annotation
x-refusal-controls       instances the schema must reject, each naming the
                         keyword that rejects it
x-positive-instance      used once, where the positive instance is a file that
                         ships in the tree rather than a copy inside the schema
```

Both are ignored by validators, which is the point: they are data for whoever
replays them, and they sit beside the constraint they exercise so that removing
the constraint and leaving the control behind is visible in one diff.

One hundred and fifty-one refusal controls ship in the C0-counted surface: one
hundred and forty-four inside thirty-one of the thirty-three schemas and seven
in `refused-claims.json`; the two R2 schemas carry twenty-eight more, replayed
by `../expand-contract/selftest.py`.
A refusal nobody replays
is prose, and prose does not survive the edit that removes the guard underneath
it.

A control also has to fail for the reason it claims. Deleting the single keyword
its `refused_by` names must make that instance validate; if it stays refused,
the instance was tripping some unrelated `required` or `minItems` and the guard
it advertises was never exercised. That knockout is what a replay of these
controls checks, and it is the check that caught an accepted absence literal
matching two branches of its own `oneOf` while the control above it appeared to
work.

## Extension points

There is exactly one, `retrieval_hint` on the source packet, and it is itself
closed to a single field holding a resolver variable name. Everything else is
`additionalProperties: false` at every depth. Optionality is expressed against
an explicit absent value rather than by leaving a key out, so a missing answer
reads as `ABSENT`, `NOT_MEASURED`, `NOT_APPLICABLE`, `NEVER_REVALIDATED` or
`NOT_PUBLISHED_BY_PROVIDER` instead of reading as nothing at all. Those branches
are `oneOf` wherever the literal and the value shape are disjoint, and `anyOf`
in the one place where the absence literal is itself a string long enough to
satisfy the branch beside it.

Closed at every depth means no *new key* can be added. It does not mean the
existing free-text values are constrained: string fields carrying no `pattern`,
`enum`, `const` or length ceiling exist in every schema here — rationales,
notes, denominator definitions, tool names, references, subsystem tags, owning
decisions — and a private locator pasted into any of them validates. See
[`contracts/public-private-capability.md`](contracts/public-private-capability.md)
for what is actually enforced and for the leak-scan obligation that covers the
rest; that file's stated field and schema counts were written against the first
eight schemas and predate the sixteen added for the fact and semantic planes,
while the obligation it states applies unchanged to all of them.

These files contain no consumer path, branch, credential, provider session or
live evidence. That is a property of this review and this scan, not a property
the schemas enforce.
