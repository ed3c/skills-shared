#!/usr/bin/env bash
# Positive control for the shared-skills gate, in a fully synthetic world:
# its own shared repo, its own user surfaces, its own subscriber repos. Nothing
# here touches this machine's real skill tree. Zero network.
set -eEuo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(dirname "${test_dir}")"
real_script="${skill_dir}/scripts/shared_skills.py"
world="$(mktemp -d)"
trap 'rm -rf "${world}"' EXIT
# A failing assertion used to abort with an empty log, which reads exactly like
# the tool refusing -- the reviewer's own battery went red on a mutant and could
# not tell which of the two had happened. Name the line before the shell dies.
trap 'echo "FAIL verify.sh line ${LINENO}: the assertion there did not hold" >&2' ERR

# Runs a command that is expected to fail, and leaves its exit code in
# ${last_status}. A `set +e` block would silence the ERR trap for everything
# after it too, and would report the same "non-zero" for a refusal and for an
# absence -- the distinction several cases below exist to pin down.
last_status=0
attempt() {         # attempt <stdout-file> <stderr-file> <command...>
  local out="$1" err="$2"; shift 2
  last_status=0
  "$@" >"${out}" 2>"${err}" || last_status=$?
}

# Every guard below is exercised by a planted defect, because a guard with no
# fixture is one nobody has ever seen fire. A patch that changed no bytes would
# "prove" the guard works while proving nothing, so an inert patch is fatal.
mutant() {          # mutant <name> <sed-expr> -> path of the patched copy
  local out="${shared}/skills/shared-skills-infra/scripts/$1.py"
  sed "$2" "${script}" > "${out}"
  if cmp -s "${script}" "${out}"; then
    echo "FAIL: the $1 patch matched nothing, so it proves nothing" >&2
    exit 1
  fi
  printf '%s' "${out}"
}

fingerprint() { find "$1" -type f | sort | xargs shasum | shasum | cut -d' ' -f1; }

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
attempt "${world}/5.out" "${world}/5.err" run report
test "${last_status}" -eq 3            # unruled != violation
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
# One statement each, never `test A && test B`: bash exempts the left operand of
# a && list from set -e and from the ERR trap, so the first half could fail and
# the suite would walk straight past it. It did -- the chain here asserted that
# both paths were *absent*, which has never been true, because adopt sweeps the
# rival and `link` then immediately re-points both project surfaces at
# canonical. A dead assertion cannot report that it is also a wrong one. What
# actually has to hold is that no real copy survives at either path: a pointer
# is not a shadow, a directory full of bytes is.
for swept_entry in "${adoptee}" "${rival}"; do
  if test ! -L "${swept_entry}"; then
    echo "FAIL: ${swept_entry} is not a symlink -- adopt left a real copy standing" >&2
    exit 1
  fi
done
test -f "${shared}/skills/adopt-me/SKILL.md"
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

# a source that is not on disk is a broken request, not an empty one: exit 1,
# with its own message, never a silently smaller union
attempt "${world}/6.absent.out" "${world}/6.absent.err" \
  python3 "${script}" merge merge-me --from "${world}/absent" --from "${world}/v1"
test "${last_status}" -eq 1
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

# 6b. two --from paths that resolve to one directory are one version, not two.
#     Counting a single lineage twice is precisely what manufactured the majority
#     that deleted a module, so the dedup is load-bearing and gets its own case.
#     Nothing to fold is nothing to do: exit 3, never the refusal code, or the
#     caller goes hunting for a violated rule that does not exist.
ln -s "${world}/v1" "${world}/v1-alias"
attempt "${world}/6b.out" "${world}/6b.err" python3 "${script}" merge dupe \
  --from "${world}/v1" --from "${world}/v1-alias" --backup-dir "${world}/superseded"
test "${last_status}" -eq 3                    # absence
test "${last_status}" -ne 1                    # and specifically not refusal
grep -q "nothing to fold" "${world}/6b.err"
grep -q "adopt" "${world}/6b.err"              # names the verb that does apply
test ! -e "${shared}/skills/dupe"              # a lone lineage is never materialized

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
attempt "${world}/6.dest" "${world}/6.dest.err" python3 "${script}" merge merge-me \
  "${sources[@]}" --backup-dir "${world}/superseded"
test "${last_status}" -eq 3
grep -q "^CONFLICT notes.md" "${world}/6.dest"
grep -q "canonical wrote a line of its own" "${shared}/skills/merge-me/notes.md"

# 6c. two merges of one name on one day are two records. Without the collision
#     guard the second snapshot lands *inside* the first, so the older canonical
#     is still on disk but under a path no recovery would think to look in.
test "$(find "${world}/superseded/merge-me" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')" -eq 2
for snapshot in "${world}/superseded/merge-me"/*; do
  test -f "${snapshot}/SKILL.md"               # a record, not a record nested in a record
done

# 7. hollow: a merger that walks only the first version drops every file the
#    other versions alone hold. The guarantee has to be mechanical, so the run
#    itself must fail -- a union that shrank silently is the whole failure this
#    verb exists to prevent.
hollow="$(mutant hollow_shared_skills 's/for label, root in sources:/for label, root in sources[:1]:/')"
attempt "${world}/7.out" "${world}/7.err" python3 "${hollow}" merge merge-hollow \
  "${sources[@]}" --backup-dir "${world}/superseded"
test "${last_status}" -eq 1                    # dropping a file is broken, not pending
grep -q "DROPPED modules/port-map.md: held by B" "${world}/7.err"
test ! -e "${shared}/skills/merge-hollow"      # the lossy union was never promoted
test -d "${shared}/skills/.merge-hollow.merging"   # and the partial union is where FAIL says

# 7b. the same lossy merger against a name that already HAS a canonical. "Never
#     promoted over canonical" is a promise about an incumbent, and the only
#     failing merge above had no incumbent to protect, so the promise was
#     printed in the FAIL message and tested nowhere.
incumbent="$(fingerprint "${shared}/skills/merge-me")"
snapshots_before="$(find "${world}/superseded/merge-me" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')"
attempt "${world}/7b.out" "${world}/7b.err" python3 "${hollow}" merge merge-me \
  "${sources[@]}" --backup-dir "${world}/superseded"
test "${last_status}" -eq 1
grep -q "DROPPED modules/port-map.md: held by B" "${world}/7b.err"
test "$(fingerprint "${shared}/skills/merge-me")" = "${incumbent}"      # byte-for-byte untouched
test "$(find "${world}/superseded/merge-me" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')" \
     -eq "${snapshots_before}"                 # and it was not swept aside either
grep -q "is untouched and the partial union is at" "${world}/7b.err"
test -d "${shared}/skills/.merge-me.merging"   # the message names a real place

# 8. same name, different bytes: report both sides and refuse to pick one.
#    Choosing between two authored paragraphs is a human's call, so the exit is
#    "nothing ruled yet", which must not read the same as the hollow failure.
mkdir -p "${world}/c1" "${world}/c2"
printf -- '---\nname: merge-conflict\n---\nversion one wrote this paragraph\n' \
  > "${world}/c1/SKILL.md"
printf -- '---\nname: merge-conflict\n---\nversion two rewrote that paragraph\n' \
  > "${world}/c2/SKILL.md"
printf 'only version one has this\n' > "${world}/c1/solo.md"
attempt "${world}/8.out" "${world}/8.err" python3 "${script}" merge merge-conflict \
  --from "${world}/c1" --from "${world}/c2" --backup-dir "${world}/superseded"
conflict_status="${last_status}"
test "${conflict_status}" -eq 3
test "${conflict_status}" -ne 1                         # pending != broken
cat "${world}/8.err" >> "${world}/8.out"
grep -q "^CONFLICT SKILL.md" "${world}/8.out"
# the sizes have to be the real ones. Counting lines that contain the word
# "bytes" passed just as happily when the number printed was a constant 0, which
# is a report a human would rule on without ever seeing what they were ruling on.
c1_size="$(wc -c < "${world}/c1/SKILL.md" | tr -d ' ')"
c2_size="$(wc -c < "${world}/c2/SKILL.md" | tr -d ' ')"
test "${c1_size}" -ne "${c2_size}"                      # else this proves nothing
test "$(grep -c 'bytes' "${world}/8.out")" -eq 2        # exactly two sides, no more
grep -qE "^ +A +${c1_size} bytes +[0-9a-f]{8} +.*/c1/SKILL\.md$" "${world}/8.out"
grep -qE "^ +B +${c2_size} bytes +[0-9a-f]{8} +.*/c2/SKILL\.md$" "${world}/8.out"
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
printf 'two \xfd\xfc' > "${world}/b2/blob.bin"          # deliberately a different length
attempt "${world}/8b.out" "${world}/8b.err" python3 "${script}" merge merge-binary \
  --from "${world}/b1" --from "${world}/b2" --backup-dir "${world}/superseded"
test "${last_status}" -eq 3
cat "${world}/8b.err" >> "${world}/8b.out"
grep -q "^CONFLICT blob.bin" "${world}/8b.out"
grep -q "binary content" "${world}/8b.out"
b1_size="$(wc -c < "${world}/b1/blob.bin" | tr -d ' ')"
b2_size="$(wc -c < "${world}/b2/blob.bin" | tr -d ' ')"
test "${b1_size}" -ne "${b2_size}"
test "$(grep -c 'bytes' "${world}/8b.out")" -eq 2
grep -qE "^ +A +${b1_size} bytes +[0-9a-f]{8} +.*/b1/blob\.bin$" "${world}/8b.out"
grep -qE "^ +B +${b2_size} bytes +[0-9a-f]{8} +.*/b2/blob\.bin$" "${world}/8b.out"

# 8c. a planner that swallows a disagreement instead of surfacing it. Auto-
#     selecting a side is the one thing this verb must never do, and the recount
#     is the only thing standing between that and a silent ruling -- it has to
#     catch it from the source bytes, because the plan it would otherwise be
#     checked against is exactly what lied.
swallow="$(mutant swallow_conflicts 's/conflicts\[relpath\] = versions/take[relpath] = versions[0]/')"
attempt "${world}/8c.out" "${world}/8c.err" python3 "${swallow}" merge merge-swallowed \
  --from "${world}/c1" --from "${world}/c2" --backup-dir "${world}/superseded"
test "${last_status}" -eq 1
grep -q "UNREPORTED SKILL.md" "${world}/8c.err"
test ! -e "${shared}/skills/merge-swallowed"

# 8d. a planner that writes something other than the bytes the versions carry.
#     A union that keeps every path and corrupts the contents passes any check
#     that only counts files, and would read as a successful merge forever.
tamper="$(mutant tamper_bytes 's/shutil\.copy2(chosen, target)/target.write_bytes(b"corrupted")/')"
attempt "${world}/8d.out" "${world}/8d.err" python3 "${tamper}" merge merge-tampered \
  "${sources[@]}" --backup-dir "${world}/superseded"
test "${last_status}" -eq 1
grep -q "^FAIL ALTERED " "${world}/8d.err"
test ! -e "${shared}/skills/merge-tampered"

# 8e. a planner that loses a `--from` while parsing it. The recount must start
#     from what the caller named, not from the planner's own parse: handed the
#     shortened list, it would agree with the defect and report a full union.
#     This is the case where the tool has to refuse by itself -- a suite that
#     merely notices a missing file afterwards is not the hard guarantee.
narrow="$(mutant narrow_sources 's/    for path in paths:/    for path in paths[:-1]:/')"
attempt "${world}/8e.out" "${world}/8e.err" python3 "${narrow}" merge merge-narrowed \
  "${sources[@]}" --backup-dir "${world}/superseded"
test "${last_status}" -eq 1
grep -q "DROPPED notes.md: held by C" "${world}/8e.err"
test ! -e "${shared}/skills/merge-narrowed"

# 8f. one version keeps `modules` as a file, another keeps it as a directory --
#     exactly the kind of fork this verb exists to fold, and no tree can hold
#     both spellings. It used to raise a bare FileExistsError halfway through the
#     copy and leave a staging directory that blocked every later retry of that
#     name until a human moved it aside. Refuse before anything is written.
mkdir -p "${world}/t1" "${world}/t2/modules"
printf 'this fork kept modules as a single file\n' > "${world}/t1/modules"
printf 'this fork kept modules as a directory\n' > "${world}/t2/modules/port-map.md"
attempt "${world}/8f.out" "${world}/8f.err" python3 "${script}" merge typeclash \
  --from "${world}/t1" --from "${world}/t2" --backup-dir "${world}/superseded"
test "${last_status}" -eq 1
grep -q "^FAIL versions disagree about what 'modules' is" "${world}/8f.err"
grep -q "rename one side" "${world}/8f.err"             # says what to do next
# `! grep -q ...` cannot turn this suite red: bash exempts a !-inverted command
# from both set -e and the ERR trap, so the assertion that the refusal is a
# sentence rather than a stack trace was decorative for as long as it stood.
if grep -q "Traceback" "${world}/8f.err"; then
  echo "FAIL: the type-clash refusal was a stack trace, not a sentence" >&2
  exit 1
fi
test ! -e "${shared}/skills/.typeclash.merging"         # no wreckage
test ! -e "${shared}/skills/typeclash"
# and the refusal is repeatable: the first attempt must not poison the name
attempt "${world}/8f.out2" "${world}/8f.err2" python3 "${script}" merge typeclash \
  --from "${world}/t1" --from "${world}/t2" --backup-dir "${world}/superseded"
test "${last_status}" -eq 1
grep -q "versions disagree about what 'modules' is" "${world}/8f.err2"

# 8g. every file conflicts and the name has no canonical yet, so the union would
#     be empty. Creating the directory anyway publishes a skill that holds
#     nothing while every file is still waiting on a human, and leaves a staging
#     directory that blocks the retry the ruling is meant to unblock.
mkdir -p "${world}/x1" "${world}/x2"
printf 'left side wrote this\n'  > "${world}/x1/SKILL.md"
printf 'right side wrote that\n' > "${world}/x2/SKILL.md"
attempt "${world}/8g.out" "${world}/8g.err" python3 "${script}" merge allconflict \
  --from "${world}/x1" --from "${world}/x2" --backup-dir "${world}/superseded"
test "${last_status}" -eq 3
grep -q "^CONFLICT SKILL.md" "${world}/8g.out"
grep -q "left untouched" "${world}/8g.out"
test ! -e "${shared}/skills/allconflict"
test ! -e "${shared}/skills/.allconflict.merging"

# 8h. a directory only one version carries, holding no file. The union is over
#     files -- git cannot record an empty directory -- so it is not carried, and
#     the run has to say so rather than let a version's directory disappear
#     under exit 0 while the docs promise a union.
mkdir -p "${world}/e1/emptydir" "${world}/e2"
printf -- '---\nname: emptydir\n---\nsame\n' > "${world}/e1/SKILL.md"
printf -- '---\nname: emptydir\n---\nsame\n' > "${world}/e2/SKILL.md"
python3 "${script}" merge emptydir --from "${world}/e1" --from "${world}/e2" \
  --backup-dir "${world}/superseded" > "${world}/8h.out"
grep -q "^NOTE .*emptydir/ is an empty directory in A" "${world}/8h.out"
test -f "${shared}/skills/emptydir/SKILL.md"
test ! -e "${shared}/skills/emptydir/emptydir"

# 8i. a version whose subtree hangs off a DIRECTORY SYMLINK. The file walk starts
#     at the version root and does not descend one; the empty-directory notice
#     starts its walk AT the link and does. Two walkers, one tree, opposite
#     answers -- and the loser was silence: every file under the link vanished
#     under exit 0 with no NOTE, no CONFLICT and no FAIL, which refutes the one
#     guarantee this verb sells. Refuse instead of following the link, because
#     following it is itself a ruling (carry the link, or copy its target?).
mkdir -p "${world}/s1" "${world}/s2" "${world}/s-target"
printf -- '---\nname: symdir\n---\nsame\n' > "${world}/s1/SKILL.md"
printf -- '---\nname: symdir\n---\nsame\n' > "${world}/s2/SKILL.md"
printf 'only reachable through the directory symlink\n' > "${world}/s-target/port-map.md"
ln -s "${world}/s-target" "${world}/s1/modules"
attempt "${world}/8i.out" "${world}/8i.err" python3 "${script}" merge symdir \
  --from "${world}/s1" --from "${world}/s2" --backup-dir "${world}/superseded"
test "${last_status}" -eq 1                    # a dropped subtree is broken, not pending
grep -q "reaches 'modules' through a directory symlink" "${world}/8i.err"
grep -q "cp -RL" "${world}/8i.err"             # says what to do next
if grep -q "Traceback" "${world}/8i.err"; then
  echo "FAIL: the directory-symlink refusal was a stack trace, not a sentence" >&2
  exit 1
fi
test ! -e "${shared}/skills/symdir"            # nothing published
test ! -e "${shared}/skills/.symdir.merging"   # and no wreckage to block the retry

# 8j. the recount must catch it too. Every count in the recount is content_files'
#     own answer, so a defect in the enumeration layer is invisible to a recount
#     built on it -- which is why the symlink audit uses os.walk instead and runs
#     a second time inside the recount, over the paths argv named. Neuter the
#     planner's refusal and the merge still has to fail rather than promote a
#     union that quietly lost a subtree.
blind="$(mutant blind_symlinks 's/^    _refuse_symlinked_dirs(versions)$/    pass/')"
attempt "${world}/8j.out" "${world}/8j.err" python3 "${blind}" merge symdir-blind \
  --from "${world}/s1" --from "${world}/s2" --backup-dir "${world}/superseded"
test "${last_status}" -eq 1
grep -q "^FAIL UNWALKED modules" "${world}/8j.err"
test ! -e "${shared}/skills/symdir-blind"      # the blind union was never promoted

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

# 10. the eval record is a claim about what this suite proves, so it is checked
#     against this suite. Until now nothing read evals.json at all: it could be
#     invalid, absent, or describe cases that were never written, and the gate
#     stayed green. Each claim carries the literal token that has to appear in
#     verify.sh -- an anchor, not a semantic proof, but enough that deleting a
#     case cannot leave its claim standing.
python3 -c '
import json, pathlib, sys
skill, suite_path = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
suite = suite_path.read_text(encoding="utf-8")
try:
    data = json.loads((skill / "evals.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as error:
    sys.exit(f"FAIL unreadable evals.json: {error}")
problems = []
# Against SKILL.md, never against the directory name: this checkout is portable
# by construction, so a clone into a differently named directory must not turn
# the eval record into a failure.
frontmatter = [
    line.split(":", 1)[1].strip()
    for line in (skill / "SKILL.md").read_text(encoding="utf-8").splitlines()
    if line.startswith("name:")
]
declared = data.get("skill_name")
if not frontmatter:
    problems.append("SKILL.md has no name: line to check the eval record against")
elif declared != frontmatter[0]:
    problems.append(f"skill_name is {declared}, but SKILL.md is named {frontmatter[0]}")
for entry in data.get("runnable", []):
    eid = entry.get("id", "<unnamed>")
    for field in ("checker_script", "test_verify"):
        named = entry.get(field)
        if not named or not (skill / named).is_file():
            problems.append(f"{eid}: {field} names {named}, which is not on disk")
    claims = entry.get("covers", [])
    if not claims:
        problems.append(f"{eid}: no covers entries, so it claims nothing and proves nothing")
    for claim in claims:
        token = claim.get("asserted_by") if isinstance(claim, dict) else None
        if token is None:
            problems.append(f"{eid}: a covers entry has no asserted_by token: {claim}")
        elif token not in suite:
            problems.append(f"{eid}: nothing in the suite matches asserted_by {token}")
if problems:
    sys.exit("FAIL evals.json does not match this suite:\n  " + "\n  ".join(problems))
' "${skill_dir}" "${test_dir}/verify.sh"

echo "PASS shared-skills gate"
