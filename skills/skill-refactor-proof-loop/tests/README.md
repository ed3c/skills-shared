# Test controls

`run-all.sh` validates the positive refactor packet and golden registry, then runs `selftest.py`.

The selftest plants and refuses at least:

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

A green test suite proves the portable mechanism and current registry connection only.
