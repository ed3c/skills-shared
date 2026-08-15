#!/usr/bin/env bash
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"

grep -Fq './runtime-env local-env migrate-forgejo-keychain' "${skill_dir}/SKILL.md"
grep -Fq '<runtime-env-root>/runtime-env local-env migrate-forgejo-keychain' \
  "${skill_dir}/modules/forgejo-operations.md"
grep -Fq '本 skill 禁止 source、解析或複製 `.env`' \
  "${skill_dir}/modules/forgejo-operations.md"
grep -Fq 'credential.http://localhost:3000.helper' \
  "${skill_dir}/modules/commit-role.md"
grep -Fq '正常路徑只呼叫 `git credential fill`' \
  "${skill_dir}/modules/commit-role.md"

echo 'PASS credential ownership stays in runtime-env'
