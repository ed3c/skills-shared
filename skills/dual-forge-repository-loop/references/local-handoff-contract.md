# Repository-native local handoff contract

This contract governs any handoff intended for `CLAUDE_CODE_LOCAL`, `CODEX_CLI_LOCAL`, or `CHATGPT_DESKTOP_WORKTREE`.

## Hard law

A local handoff MUST be executable from a fresh Git checkout using only repository-tracked bytes plus exact Git identity and runtime/environment bindings. Archive files and opaque external artifacts are never required inputs.

```text
CANONICAL_LOCAL_HANDOFF
  = exact repository identity
  + exact Git ref/commit/tree
  + Git-tracked source/contracts
  + Git-tracked verifier/assertions
  + content digests
  + runtime/environment binding

OPTIONAL_EXPORT_ONLY
  = .zip/.tar/.tgz/.gz archives
  + GitHub Actions artifacts
  + Release assets
  + issue-comment/base64 mirrors

FORBIDDEN_REQUIRED_INPUT
  = required archive download
  + required issue-comment reconstruction
  + required conversation/sandbox attachment
  + required opaque artifact URL
  + required non-repository-local file
```

Deleting every optional export MUST NOT change replay eligibility or verifier behavior.

## Required manifest properties

A repository-native handoff manifest declares:

- `repository`: canonical owner/name;
- `subject.commit`: exact 40-character commit SHA;
- `subject.tree`: exact 40-character tree SHA when known;
- `required_inputs[]`: repository-relative paths only;
- every required input has `git_tracked=true` and a SHA-256 digest;
- `entrypoint`: a repository-relative executable/script path that is itself a required input;
- `runtime.allowed[]`: explicit local runtime identities;
- `optional_exports[]`: optional artifacts only; every entry has `required=false`.

Required paths MUST NOT end in archive/container extensions such as `.zip`, `.tar`, `.tgz`, `.gz`, `.7z`, `.rar`, or `.b64`.

Required inputs MUST NOT be URLs, absolute paths, `sandbox:` paths, issue-comment IDs, conversation-local attachment names, or paths outside the checkout.

## #199 migration rule

The historical `repository-multi-agent-runtime-v2.1-runtime-validation.zip` and its five base64 issue comments remain provenance for the original connector receipt. They are not canonical local-runtime inputs.

Future local replay must bind repository-native tracked equivalents. Existing tracked prompt-baseline and cross-stack evals are the model: preregistration, cases, results, verifier, and runner live in the repository and can be executed without reconstructing an archive.

## Evidence states

- `PASS`: manifest is repository-native and archive-independent for its declared subject.
- `FAIL`: a required dependency is an archive/opaque external artifact, a path escapes the checkout, or a required input is not declared tracked/digested.
- `ABSENT`: manifest or required field is missing.
- `NOT_EXERCISED`: contract is structurally valid but no local runtime execution receipt exists.

A contract `PASS` does not prove the local runtime actually ran; runtime execution remains a separate receipt.