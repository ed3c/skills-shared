# Scripts

## `assert_entropy_audit.py`

Deterministic Draft 2020-12 and semantic gate for `repository-entropy-audit/v1`.

```bash
python3 skills/repository-entropy-reclamation/scripts/assert_entropy_audit.py \
  --audit skills/repository-entropy-reclamation/references/example-audit.json

python3 skills/repository-entropy-reclamation/scripts/assert_entropy_audit.py \
  --selftest
```

It reads local files only. It performs no network request, repository mutation, command execution from the audit packet, branch creation, PR publication, merge, release, or Human admission.

Exit codes:

```text
0   schema and semantic contract passed
2   evaluable packet violated a closure law
64  usage/file/JSON input invalid
70  schema validator or schema contract unavailable/invalid
```
