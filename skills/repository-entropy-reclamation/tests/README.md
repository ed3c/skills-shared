# Tests

`test_assert_entropy_audit.py` loads the committed Draft 2020-12 schema and semantic gate, then checks one positive exact-subject packet and planted defects for:

```text
dirty subject
unsafe path
unknown boundary
production or ambiguous consumer
unexercised dynamic reachability
protected boundary
unknown capability effect
zero or non-negative conceptual reduction
non-independent or writing Shadow
subject mismatch
unasserted delivery
false verified verdict
AUDIT mutation
missing Local Handoff Queue subject
```

`run-all.sh` also validates the schema/example JSON, executes the example through the command-line gate, and runs the gate's selftest.

These tests prove the portable contract can turn red. They do not prove a consumer repository has no hidden consumers, that a deletion is safe, that a GitHub draft received Actions, or that a Human admitted a product/API change.
