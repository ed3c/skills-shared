# Strict compact-receipt ↔ evidence-sidecar binding

`local_verification.py` writes two artifacts:

```text
compact receipt
  → small policy input

detailed evidence sidecar
  → exact tree, contract digest, command argv/cwd, exit, timeout, duration,
    stream byte counts/hashes and truncation state
```

A compact receipt alone is insufficient. `ci_publish_bound_gate.py` is the admitted publication entrypoint: it validates the sidecar before delegating intent and billing decisions to `ci_publish_gate.py`.

## Invocation

```bash
python3 skills/github-delivery-loop/scripts/ci_publish_bound_gate.py evaluate \
  --repo-root /absolute/path/to/repo \
  --snapshot /path/to/github-state.snapshot.json \
  --verification /path/to/local-verification.receipt.json \
  --verification-evidence /path/to/local-verification.evidence.json \
  --intent ready-for-review \
  --json
```

## Binding checks

The strict gate recomputes and compares:

1. actual local `HEAD` against compact and detailed evidence;
2. actual `HEAD^{tree}` against `evidence.tree_sha`;
3. immutable repository ID across snapshot, receipt and sidecar;
4. sidecar self-digest over canonical JSON without `content_sha256`;
5. compact `evidence_sha256` over the complete canonical sidecar;
6. ordered compact command IDs against detailed command IDs;
7. every command exit/timeout/spawn/truncation field;
8. stream hashes, path safety, argv shape and timestamps.

Any mismatch returns exit `64` with `invalid-policy-input` before a publication operation exists. Policy-level outcomes such as `billing-circuit-open` remain exit `2`. Only a fully bound subject can reach `ALLOW`.

## Compatibility boundary

`ci_publish_gate.py` remains the reusable v1 policy module and its original fixtures remain useful for testing publication-intent and billing logic. Consumers must invoke `ci_publish_bound_gate.py`; direct compact-only invocation is compatibility/test surface, not the admitted private-repository publication entrypoint.

## Negative controls

The zero-network test plants:

- missing sidecar;
- changed sidecar byte;
- forged compact digest;
- wrong HEAD/tree/repository;
- FAIL status;
- timeout/nonzero/truncated/spawn-error command;
- duplicate or reordered command IDs;
- machine-local path or malformed stream hash.

No control performs a push, rerun, PR transition, billing change, merge or permission mutation.
