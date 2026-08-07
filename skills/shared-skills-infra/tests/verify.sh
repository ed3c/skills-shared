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

cat > "${shared}/registry.json" <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [{"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"}],
  "repo_owned": []
}
JSON

# The registry must carry no machine paths: a clone has to work anywhere, so
# every path arrives by flag or by the gitignored sites file.
if grep -q "${world}" "${shared}/registry.json"; then
  echo "FAIL: registry contains machine paths" >&2
  exit 1
fi

sites="${world}/sites.local.json"
run() { python3 "${script}" "$1" --sites "${sites}" "${@:2}"; }
paths=(--codex-surface "${world}/surfaces/codex"
       --claude-surface "${world}/surfaces/claude"
       --project "${world}/repoA")

# 1. unlinked: registered as shared but no user-level symlink yet -> FAIL
if run check "${paths[@]}" >"${world}/1.out" 2>"${world}/1.err"; then
  echo "FAIL: missing symlinks passed the gate" >&2
  exit 1
fi
grep -q "NOT-A-SYMLINK demo-skill" "${world}/1.err"

# 2. install wires the machine from flags, persists them, and links
run install "${paths[@]}" > "${world}/2.out"
grep -q "^WIRED" "${world}/2.out"
grep -q "^LINKED" "${world}/2.out"
test -f "${sites}"
grep -q "repoA" "${sites}"

# from here on the flags are unnecessary: the sites file supplies them
run check | grep -q "PASS shared skills hold"
run link demo-skill > /dev/null            # idempotent
run check | grep -q "PASS shared skills hold"
test -f "${world}/surfaces/claude/demo-skill/SKILL.md"   # readable through both surfaces
test -f "${world}/surfaces/codex/demo-skill/SKILL.md"

# 3. shadowing: a subscriber keeps its own copy of a shared name -> FAIL.
#    This is the load-bearing case: both hosts prefer the project copy, so the
#    shared one is silently replaced and nothing else would report it.
# install left a project symlink here; writing through it would land inside
# canonical, so the link has to go before the rival copy is planted.
rm -f "${world}/repoA/.claude/skills/demo-skill"
mkdir -p "${world}/repoA/.claude/skills/demo-skill"
printf -- '---\nname: demo-skill\n---\nlocal fork\n' \
  > "${world}/repoA/.claude/skills/demo-skill/SKILL.md"
printf 'second file so it is a copy, not a forwarder\n' \
  > "${world}/repoA/.claude/skills/demo-skill/notes.md"
if run check >"${world}/3.out" 2>"${world}/3.err"; then
  echo "FAIL: shadowing copy passed the gate" >&2
  exit 1
fi
grep -q "SHADOWED demo-skill: repoA/.claude" "${world}/3.err"

# 4. a symlink at project level is a pointer, not a shadow -> still passes
rm -rf "${world}/repoA/.claude/skills/demo-skill"
ln -s "${shared}/skills/demo-skill" "${world}/repoA/.claude/skills/demo-skill"
run check | grep -q "PASS shared skills hold"

# 5. report surfaces an unruled duplicate without calling it a failure
for repo_surface in "${world}/repoA/.agents/skills" "${world}/repoA/.claude/skills"; do
  mkdir -p "${repo_surface}/unruled-skill"
  printf -- '---\nname: unruled-skill\n---\n%s\n' "${repo_surface}" \
    > "${repo_surface}/unruled-skill/SKILL.md"
  printf 'body\n' > "${repo_surface}/unruled-skill/extra.md"
done
set +e
run report > "${world}/5.out" 2>&1
report_status=$?
set -e
test "${report_status}" -eq 3          # unruled != violation
grep -q "unruled-skill" "${world}/5.out"
run check | grep -q "PASS shared skills hold"

# 5b. adopt must sweep every rival entry, or it creates the shadowing it exists
#     to remove. Dry-run first; the user surfaces must never be swept.
adoptee="${world}/repoA/.agents/skills/adopt-me"
rival="${world}/repoA/.claude/skills/adopt-me"
mkdir -p "${adoptee}" "${rival}"
printf -- '---\nname: adopt-me\n---\nwinner\n' > "${adoptee}/SKILL.md"
printf 'x\n' > "${adoptee}/extra.md"
printf -- '---\nname: adopt-me\n---\nrival\n' > "${rival}/SKILL.md"
printf 'y\n' > "${rival}/extra.md"

run adopt adopt-me --from "${adoptee}" --why fixture --dry-run > "${world}/5b.out"
grep -q "^DRY-RUN adopt adopt-me" "${world}/5b.out"
grep -q "sweep copy .*repoA/.claude" "${world}/5b.out"
test -d "${adoptee}"        # dry-run moved nothing

run adopt adopt-me --from "${adoptee}" --why fixture \
  --backup-dir "${world}/swept" > "${world}/5c.out"
grep -q "^SWEPT" "${world}/5c.out"
test ! -e "${adoptee}" && test ! -e "${rival}"
test -f "${moved_probe:-${shared}}/skills/adopt-me/SKILL.md"
test -f "${world}/swept/adopt-me/repoA_.claude/SKILL.md"   # swept, not deleted
test -L "${world}/surfaces/codex/adopt-me"                 # user surface untouched by sweep
run check | grep -q "PASS shared skills hold"

# 6. merge is a union, not a vote: three versions, each holding one file the
#    other two lack. This is the case the first convergence attempt got wrong --
#    a hash majority deleted a module that only one version ever had.
mkdir -p "${world}/v1/modules" "${world}/v2/modules" "${world}/v3"
for version in v1 v2 v3; do
  printf -- '---\nname: merge-me\n---\nidentical body\n' > "${world}/${version}/SKILL.md"
done
printf 'only version one has this\n' > "${world}/v1/modules/local-instance.md"
printf 'only version two has this\n' > "${world}/v2/modules/port-map.md"
printf 'only version three has this\n' > "${world}/v3/notes.md"
sources=(--from "${world}/v1" --from "${world}/v2" --from "${world}/v3")

# a source that is not on disk is an error with its own message, never a
# silently smaller union
if python3 "${script}" merge merge-me --from "${world}/absent" --from "${world}/v1" \
     >"${world}/6.absent.out" 2>"${world}/6.absent.err"; then
  echo "FAIL: merging from a source that does not exist reported success" >&2
  exit 1
fi
grep -q "source is not a directory" "${world}/6.absent.err"

python3 "${script}" merge merge-me "${sources[@]}" --dry-run > "${world}/6.dry"
grep -q "^DRY-RUN merge merge-me" "${world}/6.dry"
test ! -e "${shared}/skills/merge-me"          # a dry run writes nothing

python3 "${script}" merge merge-me "${sources[@]}" \
  --backup-dir "${world}/superseded" > "${world}/6.out"
grep -q "^UNION" "${world}/6.out"
test -f "${shared}/skills/merge-me/modules/local-instance.md"
test -f "${shared}/skills/merge-me/modules/port-map.md"
test -f "${shared}/skills/merge-me/notes.md"
test -f "${shared}/skills/merge-me/SKILL.md"   # identical everywhere, so taken once

# re-merging is idempotent because the destination counts as a version of
# itself: what it already holds can never be overwritten by a same-named file
python3 "${script}" merge merge-me "${sources[@]}" \
  --backup-dir "${world}/superseded" > "${world}/6.again"
grep -q "^SUPERSEDED" "${world}/6.again"
test -f "${shared}/skills/merge-me/modules/local-instance.md"
test -f "$(find "${world}/superseded/merge-me" -name SKILL.md | head -1)"  # moved, not deleted

# what canonical already holds is a version too. A same-named file arriving from
# elsewhere must be diffed against it, never written over it: a merge that
# overwrites destroys exactly the content the union exists to protect.
printf 'canonical wrote a line of its own\n' >> "${shared}/skills/merge-me/notes.md"
set +e
python3 "${script}" merge merge-me "${sources[@]}" \
  --backup-dir "${world}/superseded" >"${world}/6.dest" 2>&1
destination_status=$?
set -e
test "${destination_status}" -eq 3
grep -q "^CONFLICT notes.md" "${world}/6.dest"
grep -q "canonical wrote a line of its own" "${shared}/skills/merge-me/notes.md"

# 7. hollow: a merger that walks only the first version drops every file the
#    other versions alone hold. The guarantee has to be mechanical, so the run
#    itself must fail -- a union that shrank silently is the whole failure this
#    verb exists to prevent.
hollow="${shared}/skills/shared-skills-infra/scripts/hollow_shared_skills.py"
sed 's/for label, root in sources:/for label, root in sources[:1]:/' "${script}" > "${hollow}"
if cmp -s "${script}" "${hollow}"; then
  echo "FAIL: the hollow patch matched nothing, so it proves nothing" >&2
  exit 1
fi
set +e
python3 "${hollow}" merge merge-hollow "${sources[@]}" \
  --backup-dir "${world}/superseded" >"${world}/7.out" 2>"${world}/7.err"
hollow_status=$?
set -e
test "${hollow_status}" -eq 1                  # dropping a file is broken, not pending
grep -q "DROPPED modules/port-map.md" "${world}/7.err"
test ! -e "${shared}/skills/merge-hollow"      # the lossy union was never promoted

# 8. same name, different bytes: report both sides and refuse to pick one.
#    Choosing between two authored paragraphs is a human's call, so the exit is
#    "nothing ruled yet", which must not read the same as the hollow failure.
mkdir -p "${world}/c1" "${world}/c2"
printf -- '---\nname: merge-conflict\n---\nversion one wrote this paragraph\n' \
  > "${world}/c1/SKILL.md"
printf -- '---\nname: merge-conflict\n---\nversion two rewrote that paragraph\n' \
  > "${world}/c2/SKILL.md"
printf 'only version one has this\n' > "${world}/c1/solo.md"
set +e
python3 "${script}" merge merge-conflict --from "${world}/c1" --from "${world}/c2" \
  --backup-dir "${world}/superseded" >"${world}/8.out" 2>&1
conflict_status=$?
set -e
test "${conflict_status}" -eq 3
test "${conflict_status}" -ne "${hollow_status}"        # pending != broken
grep -q "^CONFLICT SKILL.md" "${world}/8.out"
test "$(grep -c 'bytes' "${world}/8.out")" -eq 2        # both sides sized
grep -qE '^ +@@ ' "${world}/8.out"                      # and diffed hunk by hunk
grep -q "version one wrote this paragraph" "${world}/8.out"
grep -q "version two rewrote that paragraph" "${world}/8.out"
test -f "${shared}/skills/merge-conflict/solo.md"       # the union still landed
test ! -e "${shared}/skills/merge-conflict/SKILL.md"    # nothing was auto-selected

# 8b. every file disagrees, and one of them is binary. Two separate ways to end
#     in wreckage instead of a ruling: a union that takes nothing has no files
#     to create it with, and a diff of bytes nobody can read would invite a
#     human to rule on a file they never actually saw.
mkdir -p "${world}/b1" "${world}/b2"
printf 'version one \xff\xfe' > "${world}/b1/blob.bin"
printf 'version two \xfd\xfc' > "${world}/b2/blob.bin"
set +e
python3 "${script}" merge merge-binary --from "${world}/b1" --from "${world}/b2" \
  --backup-dir "${world}/superseded" >"${world}/8b.out" 2>&1
binary_status=$?
set -e
test "${binary_status}" -eq 3
grep -q "^CONFLICT blob.bin" "${world}/8b.out"
grep -q "binary content" "${world}/8b.out"
test "$(grep -c 'bytes' "${world}/8b.out")" -eq 2

# 9. relocatable: the checkout carries no absolute path of its own, so moving it
#    anywhere and re-running install re-wires it. Symlinks store paths, so the
#    stale ones must fail loudly first rather than silently resolve elsewhere.
moved="${world}/moved-clone"
mv "${shared}" "${moved}"
moved_script="${moved}/skills/shared-skills-infra/scripts/shared_skills.py"
if python3 "${moved_script}" check --sites "${sites}" >"${world}/9.out" 2>"${world}/9.err"; then
  echo "FAIL: stale symlinks to the old checkout passed the gate" >&2
  exit 1
fi
grep -q "WRONG-TARGET demo-skill" "${world}/9.err"
python3 "${moved_script}" install --sites "${sites}" > /dev/null
python3 "${moved_script}" check --sites "${sites}" | grep -q "PASS shared skills hold"
# realpath both sides: macOS resolves /var to /private/var, which is a path
# alias, not a difference in where the link points.
test "$(realpath "${world}/surfaces/codex/demo-skill")" = "$(realpath "${moved}/skills/demo-skill")"

echo "PASS shared-skills gate"
