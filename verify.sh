#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$repo_root/skills/shared-skills-infra/tests/verify.sh"

for harness in "$repo_root"/skills/*/tests/run-all.sh; do
  bash "$harness"
done
