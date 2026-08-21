# Codex Project-Agent Templates

Render these blocks into consumer-owned `.codex/agents/*.toml`; they are inert while
stored here. Pin the exact `skills-shared` commit/tree and prompt digests. Rebind exact
model/provider/carrier at runtime; FABLE_5/OPUS_5/SONNET_5 remain aliases.

```toml
name = "portfolio-explorer"
description = "Read-only portfolio epoch inventory"
model = "gpt-5.6-terra"
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
developer_instructions = "Read the common envelope and portfolio-explorer role."
```

```toml
name = "acceptance-adversary"
description = "Read-only Issue/PR acceptance adversary"
model = "gpt-5.6"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = "Read the common envelope and acceptance-adversary role."
```

```toml
name = "dependency-auditor"
description = "Read-only G1-G7 auditor"
model = "gpt-5.6"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = "Read the common envelope and dependency-auditor role."
```

```toml
name = "runtime-admission-auditor"
description = "Read-only runtime/model/egress auditor"
model = "gpt-5.6-terra"
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
developer_instructions = "Read the common envelope and runtime-admission-auditor role."
```

```toml
name = "implementation-worker"
description = "One bounded implementation attempt and exclusive lease"
model = "gpt-5.6"
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"
developer_instructions = "Read the common envelope and implementation-worker role."
```

```toml
name = "consolidation-verifier"
description = "Read-only all-results join verifier"
model = "gpt-5.6"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = "Read the common envelope and consolidation-verifier role."
```

```toml
name = "release-auditor"
description = "Read-only exact-head CI/main/closure auditor"
model = "gpt-5.6"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = "Read the common envelope and release-auditor role."
```
