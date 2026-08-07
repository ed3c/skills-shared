#!/usr/bin/env bash
# Positive control for the shared-skills gate, in a fully synthetic world:
# its own shared repo, its own user surfaces, its own subscriber repos. Nothing
# here touches this machine's real skill tree. Zero network.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
real_script="$(dirname "${test_dir}")/scripts/shared_skills.py"
world="$(mktemp -d)"
trap 'rm -rf "${world}"' EXIT

shared="${world}/shared"
script="${shared}/skills/shared-skills-infra/scripts/shared_skills.py"
mkdir -p "${shared}/skills/shared-skills-infra/scripts" \
         "${shared}/skills/demo-skill" \
         "${world}/surfaces/codex" "${world}/surfaces/claude" \
         "${world}/repoA/.agents/skills" "${world}/repoA/.claude/skills"
cp "${real_script}" "${script}"
printf -- '---\nname: demo-skill\n---\nbody\n' > "${shared}/skills/demo-skill/SKILL.md"

cat > "${shared}/registry.json" <<JSON
{
  "schema": "shared-skills-registry/v1",
  "canonical_root": "skills",
  "surfaces": {
    "codex_user": "${world}/surfaces/codex",
    "claude_user": "${world}/surfaces/claude"
  },
  "subscribers": ["${world}/repoA"],
  "shared": [{"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"}],
  "repo_owned": []
}
JSON

# 1. unlinked: registered as shared but no user-level symlink yet -> FAIL
if python3 "${script}" check >"${world}/1.out" 2>"${world}/1.err"; then
  echo "FAIL: missing symlinks passed the gate" >&2
  exit 1
fi
grep -q "NOT-A-SYMLINK demo-skill" "${world}/1.err"

# 2. link makes it pass, and is idempotent
python3 "${script}" link demo-skill > "${world}/2.out"
grep -q "^LINKED" "${world}/2.out"
python3 "${script}" link demo-skill > /dev/null
python3 "${script}" check | grep -q "PASS shared skills hold"
test -f "${world}/surfaces/claude/demo-skill/SKILL.md"   # readable through both surfaces
test -f "${world}/surfaces/codex/demo-skill/SKILL.md"

# 3. shadowing: a subscriber keeps its own copy of a shared name -> FAIL.
#    This is the load-bearing case: both hosts prefer the project copy, so the
#    shared one is silently replaced and nothing else would report it.
mkdir -p "${world}/repoA/.claude/skills/demo-skill"
printf -- '---\nname: demo-skill\n---\nlocal fork\n' \
  > "${world}/repoA/.claude/skills/demo-skill/SKILL.md"
printf 'second file so it is a copy, not a forwarder\n' \
  > "${world}/repoA/.claude/skills/demo-skill/notes.md"
if python3 "${script}" check >"${world}/3.out" 2>"${world}/3.err"; then
  echo "FAIL: shadowing copy passed the gate" >&2
  exit 1
fi
grep -q "SHADOWED demo-skill: repoA/.claude" "${world}/3.err"

# 4. a symlink at project level is a pointer, not a shadow -> still passes
rm -rf "${world}/repoA/.claude/skills/demo-skill"
ln -s "${shared}/skills/demo-skill" "${world}/repoA/.claude/skills/demo-skill"
python3 "${script}" check | grep -q "PASS shared skills hold"

# 5. report surfaces an unruled duplicate without calling it a failure
for repo_surface in "${world}/repoA/.agents/skills" "${world}/repoA/.claude/skills"; do
  mkdir -p "${repo_surface}/unruled-skill"
  printf -- '---\nname: unruled-skill\n---\n%s\n' "${repo_surface}" \
    > "${repo_surface}/unruled-skill/SKILL.md"
  printf 'body\n' > "${repo_surface}/unruled-skill/extra.md"
done
set +e
python3 "${script}" report > "${world}/5.out" 2>&1
report_status=$?
set -e
test "${report_status}" -eq 3          # unruled != violation
grep -q "unruled-skill" "${world}/5.out"
python3 "${script}" check | grep -q "PASS shared skills hold"

echo "PASS shared-skills gate"
