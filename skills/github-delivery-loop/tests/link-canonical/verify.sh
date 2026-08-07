#!/usr/bin/env bash
# Positive control for the canonical linker. The load-bearing property is the
# refusal: a diverged copy must never be moved aside, because that is how work
# silently disappears. Zero network.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
linker="${skill_dir}/scripts/link-canonical.sh"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

backup="${scratch}/backup"

# good: an identical copy converts, and the link is usable
good="${scratch}/repo-good/.agents/skills/github-delivery-loop"
mkdir -p "$(dirname "${good}")"
rsync -a --exclude __pycache__ "${skill_dir}/" "${good}/"

bash "${linker}" --target "${good}" --backup-dir "${backup}" > "${scratch}/dry.out"
grep -q "^DRY-RUN move" "${scratch}/dry.out"
test -d "${good}" && test ! -L "${good}"        # dry-run changed nothing

bash "${linker}" --target "${good}" --backup-dir "${backup}" --apply > "${scratch}/apply.out"
test -L "${good}"
test "$(readlink "${good}")" = "${skill_dir}"
grep -q "^LINKED" "${scratch}/apply.out"
grep -q "name: github-delivery-loop" "${good}/SKILL.md"   # readable through the link
test -f "${backup}/github-delivery-loop.nogit/SKILL.md"   # old copy preserved, not deleted

# idempotent: re-running on an already-linked target is a no-op success
bash "${linker}" --target "${good}" --backup-dir "${backup}" --apply > "${scratch}/again.out"
grep -q "^OK      already a symlink" "${scratch}/again.out"

# hollow: a diverged copy must be refused and named, never moved aside
hollow="${scratch}/repo-hollow/.agents/skills/github-delivery-loop"
mkdir -p "$(dirname "${hollow}")"
rsync -a --exclude __pycache__ "${skill_dir}/" "${hollow}/"
printf 'local edit that only exists here\n' >> "${hollow}/SKILL.md"

if bash "${linker}" --target "${hollow}" --backup-dir "${backup}" --apply \
  >"${scratch}/hollow.out" 2>"${scratch}/hollow.err"; then
  echo "FAIL: diverged copy was converted" >&2
  exit 1
fi
grep -q "has diverged from canonical" "${scratch}/hollow.err"
test -d "${hollow}" && test ! -L "${hollow}"    # untouched
grep -q "local edit that only exists here" "${hollow}/SKILL.md"

# refuse pointing the canonical directory at itself
if bash "${linker}" --target "${skill_dir}" --apply >/dev/null 2>"${scratch}/self.err"; then
  echo "FAIL: self-link was accepted" >&2
  exit 1
fi
grep -q "canonical directory itself" "${scratch}/self.err"

echo "PASS canonical linker"
