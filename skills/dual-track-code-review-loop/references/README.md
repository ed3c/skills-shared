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

Thirty-two refusal controls ship here. A refusal nobody replays is prose, and
prose does not survive the edit that removes the guard underneath it.

## Extension points

There is exactly one, `retrieval_hint` on the source packet, and it is itself
closed to a single field holding a resolver variable name. Everything else is
`additionalProperties: false` at every depth. Optionality is expressed with
`oneOf` against an explicit absent value rather than by leaving a key out, so a
missing answer reads as `ABSENT` or `NOT_MEASURED` instead of reading as nothing
at all.

Closed at every depth means no *new key* can be added. It does not mean the
existing free-text values are constrained: thirty-six string fields here carry
no `pattern`, `enum`, `const` or length ceiling, and a private locator pasted
into any of them validates. See
[`contracts/public-private-capability.md`](contracts/public-private-capability.md)
for what is actually enforced and for the leak-scan obligation that covers the
rest.

These files contain no consumer path, branch, credential, provider session or
live evidence. That is a property of this review and this scan, not a property
the schemas enforce.
