#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
contract="$root/references/runtime-identity-contract.md"
skill="$root/SKILL.md"
for needle in \
  'CHATGPT_GITHUB_CONNECTOR' \
  'GITHUB_ACTIONS' \
  'CLAUDE_CODE_LOCAL' \
  'CODEX_CLI_LOCAL' \
  'CHATGPT_DESKTOP_WORKTREE' \
  'UNKNOWN'; do
  grep -Fq "$needle" "$contract"
done
grep -Fq '`CHATGPT_GITHUB_CONNECTOR` is not a GitHub Actions runner' "$contract"
grep -Fq 'Opening the Desktop app or pre-filling a deep link is insufficient' "$contract"
grep -Fq 'Runtime identity is based on observed capabilities/provenance, not model family' "$skill"
grep -Fq 'RUNTIME_BOUND' "$skill"
echo 'PASS runtime identity planes remain distinct'
