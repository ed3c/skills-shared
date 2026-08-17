# Test controls

`run-all.sh` validates the positive refactor packet, golden registry, and molecular Stack, then runs `selftest.py` and `stack_selftest.py`.

The contract/registry selftest plants and refuses at least:

```text
missing refactor-as-landed treatment
frozen treatment identity drift
old strength without an assertion
proof-layer gap or false live PASS
unfair matched-task subjects
failed/stale denominator erasure
dirty cleanup
merge/provider authority widening
duplicate golden proof ID
missing entrypoint/runner route
runner that does not invoke the entrypoint
golden treatment blob mismatch
```

The Stack selftest plants and refuses:

```text
child without a consumed unmerged parent artifact
child base that differs from the parent branch
path-disjoint sibling serialized as a fake child
multiple convergence owners
self-embedded stale open-PR head
merged state without immutable head/workflow evidence
external evidence owning Stack paths
Stack merge authority widening
duplicate issue ownership
```

A green test suite proves the portable mechanisms and current registry/Stack connections only.
