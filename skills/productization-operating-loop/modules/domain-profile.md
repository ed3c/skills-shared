# Domain profile — binding a concrete consumer

Trigger: a stage prompt in [`../prompts/README.md`](../prompts/README.md) is
about to be dispatched against a real opportunity, and the `BIND` section of
the common system envelope needs values this portable core does not carry.

[`../references/composition-manifest.json`](../references/composition-manifest.json)
already states the law this module exists to satisfy: "The portable core
carries no consumer identity. A consumer binds this method from its own
repository; naming one here would make every other consumer a special case
of the first." This file names the *shape* of a binding. It never holds an
instance of one.

## What a consumer must supply, once, at stage 0

```text
repository                consumer's own repository identity and default branch
program_id                a `pol/productization-program/v1` instance path,
                          owned by the consumer, never under skills-shared
writer identity           who has the lease for this program instance
lease paths per stage     consumer-owned paths for each lane artifact this
                          program will produce (market/user/commercial/policy/
                          closure-matrix/session-dag/dispatch-request/
                          external-projections/outcome-foldback)
evidence receipt store    where a rung's receipt (SOURCE_LOCATED through
                          REPEATED_PAYMENT_SERIES) is actually kept
rollback subject          `base_commit` the consumer can return to
Human-admission contact    who holds rights admission, merge and release for
                          this consumer's own program instance
```

Every value above is `ABSENT` until the consumer states it. A stage prompt
dispatched without one of these bound is not blocked by this module — it is
blocked by the schema's own `start_dependencies`/`completion_dependencies`
shape in
[`../references/productization-program.schema.json`](../references/productization-program.schema.json),
which this module only restates for a person filling in the envelope.

## What this module never does

- It never names a real consumer, carrier, repository or provider. Compare
  [`../references/composition-manifest.json`](../references/composition-manifest.json)'s
  `not_composed` list, which states the same refusal for the composition
  manifest itself.
- It never supplies a default for a Human-admission contact. A program with
  no named rights/merge/release owner has not been bound; it has been left
  to default to whoever runs the next command, which is exactly the
  authority-widening this method's `authority` object (eight constants, all
  `false`) exists to refuse.
- It never raises a rung or clears a lane. Binding a path is not evidence
  that anything at that path is true.
