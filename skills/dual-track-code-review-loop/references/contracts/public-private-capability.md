# Public and private capability contract

Two planes, and the split is by what the content *is*, never by which tool
happened to produce it. A private carrier that emits a technical delta has
emitted technical procedure; a public tree that records why a decision was
commercially attractive has published private intent. The carrier is not the
classifier.

## What each plane owns

```text
private carrier
  intent, strategy, commercial and market hypotheses
  private roadmap and sequencing
  private source locations and account identities
  employer, business-overlap and sensitive decisions
  projections that would be harmful or misleading if published

public tree
  reusable technical procedure
  schemas, contracts and controlled vocabulary
  adapter interfaces and evidence law
  opaque binding identifiers and resolver variable names

consumer repository
  its own requirements, source and architecture
  its own task graph, branches and review surfaces
  its own runtime receipts and product specifics
```

## Laws

- No private URL, private account identity, private file name or private content
  appears in a public issue, pull request, tree, workflow, log or receipt. This
  holds for content that is merely inconvenient as well as content that is
  sensitive, because the person who decides which is which is not the person who
  later reads the repository.

- A public artifact may carry a *resolver variable name* and an *opaque binding
  identifier*. It may never carry the value either one resolves to. The source
  packet's extension point is closed to exactly one field for this reason: there
  is no key in it where a resolved locator would fit.

- A private carrier may emit a redacted technical delta, and that delta is
  ordinary technical procedure once it lands. It never satisfies public
  completion evidence. Work is closed by artifacts a reviewer without private
  access can read and re-run.

- A local file path is not a locator. Identity of an external artifact is its
  content digest and byte count; the path a copy sits at describes one machine
  and reads as evidence on every other.

- The private plane cannot grant an admission the public plane owes. Reading a
  private roadmap does not clear a licence, and a private decision to proceed is
  not an independent review.

## Why the split is stated as ownership rather than as redaction

Redaction is a step somebody performs on the way out, and it fails in one
direction: the omission looks exactly like absence. Ownership is a property of
the artifact from the moment it is created, so an artifact in the wrong plane is
wrong immediately rather than at publication time.

## What the schemas actually enforce, and what they do not

The schemas are not a containment boundary and must not be read as one. Two
different populations of field live in them:

- **Identity fields are pattern-closed.** Packet identifiers, commit hashes,
  digests, case identifiers, schema identities, repository-relative paths and
  the one extension point's resolver variable are each pinned to an anchored
  regular expression, an `enum` or a `const`. A private URL does not fit these,
  and `additionalProperties: false` at every level means no new key can be
  introduced to hold one. `retrieval_hint` in particular admits exactly one key
  matching `^[A-Z][A-Z0-9_]*$`, which cannot spell a locator.

- **Free-text fields are not shape-protected at all.** Thirty-six string fields
  across the eight original schemas carry no `pattern`, `enum`, `const` or
  length ceiling — rationales, corrections, notes, denominator definitions,
  tool names, references, `out_of_scope` entries, measurement environments —
  and the sixteen interface schemas added by the D1/M1 freeze carry the same
  class of field under the same obligation. Four of the original fields carry
  a `not` pattern that refuses one shape and leaves the rest of the string
  space open. A locator pasted into any of these validates.

This was probed rather than reasoned about. A drive URL placed in a candidate
record's `replacement_path.note` was accepted by the schema, and a
`file:///Users/...` URI placed in a source packet's `disposition_ref` was
accepted by the schema. Both instances are valid `dtcr/*` documents. The
ownership split above is therefore a rule people follow, not a shape that
enforces itself.

## The leak-scan obligation

Because the shape does not hold, the obligation is explicit and it is not
optional:

- Every publication subject — every commit reachable from the head being
  published, not only the tip tree — is scanned for real locators before it is
  pushed: absolute home paths, `file://` URIs, cloud-drive and other private
  service URLs, private account identities and private file names. History is
  in scope because a repaired tip does not repair an ancestor that still
  carries the value.

- A finding is not fixed by amending the tip. The subject is rebuilt from the
  admitted base so that no reachable object carries the locator, and the
  superseded chain is recorded as superseded rather than treated as gone.

- Synthetic values that exist to exercise a refusal are named in the receipt so
  a scan can tell a deliberate probe from a real leak. Anything not on that
  named list is a leak until someone shows otherwise.

A shape that cannot hold the thing would not need a reviewer to notice it.
These schemas are not that shape, so a reviewer and a scan are both load-bearing
here, and the review lane cannot be marked satisfied by the schema lane being
green.

## Boundary

This contract governs where content lives. It does not authorise private account
use, does not accept service or SDK terms on anyone's behalf, and does not decide
employment, intellectual-property or business-overlap questions. Those remain
`HUMAN_ADMIT_REQUIRED` in
[`controlled-vocabulary.md`](controlled-vocabulary.md) and no accumulation of
technical evidence moves them.
