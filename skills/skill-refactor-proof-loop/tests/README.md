# Test controls

`run-all.sh` validates the positive refactor packet, golden registry, molecular Stack, and cross-Skill adoption ledger, then runs `selftest.py`, `stack_selftest.py` and `adoption_selftest.py`.

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

The adoption selftest plants and refuses, each by its own error code:

```text
in-scope Skill dropped from the audit
duplicate or non-existent audited Skill
evidence path that does not exist
Markdown-only route counted as an executable gate
PASS with no evidence, or ABSENT with evidence
unregistered golden proof claimed, or a registered one understated
frozen treatment not bound to a registry blob
evidence layer above or disagreeing with the registered proof
fixture evidence promoted to a live or delivery PASS
gap with no owning issue, or owned by an invented issue number
```

A green test suite proves the portable mechanisms and current registry/Stack/ledger connections only. The adoption ledger's classifications are offline inventory: they do not prove live runtime, issue/PR state, merge, or Human admission of the standard.
