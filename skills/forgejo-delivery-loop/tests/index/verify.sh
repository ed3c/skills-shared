#!/usr/bin/env bash
# Positive control for this skill's own index. The load-bearing property is the
# second half: a SKILL.md that never names one of its own scripts reads exactly
# like one that names them all, so omission is invisible from the outside.
# That is not hypothetical -- all three delivery loops were each hiding one
# sync-shaped script when this check was first run. Zero network.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
checker="$(realpath "${skill_dir}/../shared-skills-infra/scripts/check_index.py")"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/scratch.XXXXXXXX")"
trap 'rm -rf "${scratch}"' EXIT

# the checker itself must be able to go red before its verdict here means anything
python3 "${checker}" --selftest > /dev/null

# good: this skill's index agrees with its own tree
python3 "${checker}" "${skill_dir}/SKILL.md" \
  --root "${skill_dir}" \
  --covers "${skill_dir}/modules" \
  --covers "${skill_dir}/scripts" \
  --covers "${skill_dir}/contracts"

# hollow: a dead link and an unnamed file are both caught, through this wiring
mkdir -p "${scratch}/modules"
cp "${skill_dir}/SKILL.md" "${scratch}/SKILL.md"
cp "${skill_dir}"/modules/*.md "${scratch}/modules/"
printf '\n[gone](modules/does-not-exist.md)\n' >> "${scratch}/SKILL.md"
if python3 "${checker}" "${scratch}/SKILL.md" --root "${scratch}" >/dev/null 2>&1; then
  echo "FAIL: a dead link was accepted" >&2
  exit 1
fi

printf 'unlisted\n' > "${scratch}/modules/never-mentioned.md"
cp "${skill_dir}/SKILL.md" "${scratch}/SKILL.md"
if python3 "${checker}" "${scratch}/SKILL.md" --root "${skill_dir}" \
  --covers "${scratch}/modules" >/dev/null 2>&1; then
  echo "FAIL: an unindexed file was accepted" >&2
  exit 1
fi

echo "PASS index"
