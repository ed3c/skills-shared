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

# Where a real deployment keeps it: inside the checkout, gitignored. `bind` only
# trusts the sites file `check` reads by default, which is this path derived from
# the script's own location -- so the synthetic world has to put it there too.
sites="${shared}/sites.local.json"
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

# 6. binding: a repo that retargeted the shared body records which body it
#    retargeted against. The good case -- a binding whose `body_version` still
#    matches the body -- has to pass, or the mechanism would just be a nag.
binding_dir="${world}/repoA/.skill-bindings/demo-skill"
binding="${binding_dir}/binding.md"
run bind demo-skill --repo "${world}/repoA" --upstream demo-skill@fixture > "${world}/6-bound.out"
grep -q "^BOUND" "${world}/6-bound.out"
for field in skill upstream retargeted_at body_version; do
  grep -q "^${field}: ." "${binding}" || { echo "FAIL: binding lacks ${field}" >&2; exit 1; }
done
run check > "${world}/6-good.out"
grep -q "PASS shared skills hold" "${world}/6-good.out"
# adopt-me is registered too and has no binding: current and absent coexist, and
# the tally is what tells them apart in the output.
grep -q "BINDINGS 1 current, 0 stale, 1 not retargeted" "${world}/6-good.out"
# the prose under the frontmatter is the retarget ledger -- the reason a binding
# exists at all. Plant a line only this repo could have written, so a restamp
# that rewrites the file instead of restamping it stops being invisible.
printf '\nLEDGER: 本 repo retarget 當下的三個取捨。\n' >> "${binding}"
run check | grep -q "PASS shared skills hold"     # extra prose must not disturb the gate

# 6a2. a refused bind must leave no write behind. `--upstream` carrying a line
#      that closes the frontmatter early produces a record missing two fields;
#      if the file is written before that is asserted, the refusal still destroys
#      the ledger it declined to stamp. Rejected means untouched, byte for byte.
cp "${binding}" "${world}/6a2-before.md"
set +e
run bind demo-skill --repo "${world}/repoA" --upstream $'x\n---' \
  >/dev/null 2>"${world}/6a2.err"
malformed_bind_status=$?
set -e
test "${malformed_bind_status}" -eq 1
if ! cmp -s "${world}/6a2-before.md" "${binding}"; then
  echo "FAIL: a refused bind overwrote the binding it refused to write" >&2
  exit 1
fi
# nor may a staging copy survive as a second, unread record in the slot
test "$(find "${binding_dir}" -type f | wc -l)" -eq 1
run check | grep -q "PASS shared skills hold"

# 6b. the body moves -> every binding pinned to the old body is stale. This is
#     the whole point of `body_version`: rework becomes one listed batch instead
#     of five repos each rediscovering it. Stale is SURFACE, never FAIL --
#     nothing is broken, a re-retarget is owed.
printf 'a module the binding was never retargeted against\n' \
  > "${shared}/skills/demo-skill/modules.md"
set +e
run check > "${world}/6-stale.out" 2>"${world}/6-stale.err"
stale_status=$?
set -e
test "${stale_status}" -eq 3            # owed work, not a violation
grep -q "SURFACE BINDING-STALE demo-skill" "${world}/6-stale.out"
grep -q "BINDINGS 0 current, 1 stale" "${world}/6-stale.out"
test ! -s "${world}/6-stale.err"        # nothing on stderr: it did not fail

# 6b2. `install` ends with the gate and returns its code. Nothing else in this
#      suite runs install while a binding is stale, so without this case the
#      wiring could report 0 over a gate that says 3 -- the disagreement is the
#      silent state again, one level up.
set +e
run install > "${world}/6-install-stale.out" 2>&1
install_stale_status=$?
set -e
test "${install_stale_status}" -eq 3
grep -q "^WIRED" "${world}/6-install-stale.out"
grep -q "SURFACE BINDING-STALE demo-skill" "${world}/6-install-stale.out"

run bind demo-skill --repo "${world}/repoA" > /dev/null   # restamp; upstream is remembered
grep -q "^upstream: demo-skill@fixture" "${binding}"
# the ledger is the payload; the frontmatter is only the pin. A restamp that
# rewrote the file would destroy the record while claiming to maintain it.
grep -q "^LEDGER: " "${binding}"
run check | grep -q "PASS shared skills hold"

# 6c. a binding that lost a field is broken, not "not yet retargeted": the record
#     no longer says what it was pinned to, and only a human can restore that.
mv "${binding}" "${world}/binding.bak"
grep -v '^body_version:' "${world}/binding.bak" > "${binding}"
set +e
run check > /dev/null 2>"${world}/6-missing-field.err"
broken_status=$?
set -e
test "${broken_status}" -eq 1
grep -q "FAIL BINDING-INCOMPLETE demo-skill" "${world}/6-missing-field.err"
grep -q "lacks body_version" "${world}/6-missing-field.err"
# and `bind` must not quietly restamp it back to green: "only a human can restore
# that" is a claim about the tool too, or the FAIL lasts exactly one command.
set +e
run bind demo-skill --repo "${world}/repoA" >/dev/null 2>"${world}/6-norepair.err"
norepair_status=$?
set -e
test "${norepair_status}" -eq 1
grep -q "never repairs one" "${world}/6-norepair.err"
! grep -q "^body_version:" "${binding}"          # left exactly as found

# 6c2. all four fields are present but the block never closes. The parser sees no
#      closed block, so without a distinct signal the verdict names four missing
#      fields that are all sitting right there -- a FAIL nobody can act on.
{ printf -- '---\n'
  grep -E '^(skill|upstream|retargeted_at|body_version):' "${world}/binding.bak"; } > "${binding}"
set +e
run check > /dev/null 2>"${world}/6-unclosed.err"
unclosed_status=$?
set -e
test "${unclosed_status}" -eq 1
grep -q "never closes" "${world}/6-unclosed.err"
if grep -q "lacks skill" "${world}/6-unclosed.err"; then
  echo "FAIL: the diagnosis named fields that are all present" >&2
  exit 1
fi

# 6d. a binding copied from another skill's slot keeps the original `skill:` and
#     goes on pinning that skill's hash: the record is false in place, which is
#     how retarget ledgers rotted before they were slotted. Complete but wrong is
#     still broken, not stale.
sed 's/^skill: .*/skill: adopt-me/; s/^upstream: .*/upstream: FOREIGN@another-repo/' \
  "${world}/binding.bak" > "${binding}"
set +e
run check > /dev/null 2>"${world}/6-mismatch.err"
mismatch_status=$?
set -e
test "${mismatch_status}" -eq 1
grep -q "declares skill: adopt-me while sitting in the slot for demo-skill" "${world}/6-mismatch.err"
# 6d2. restamping this one would clear the FAIL and adopt `upstream` from the
#      retarget it was copied from: a record that reads green while claiming a
#      provenance that was never this repo's. Worse than the failure it replaced.
set +e
run bind demo-skill --repo "${world}/repoA" >/dev/null 2>"${world}/6-launder.err"
launder_status=$?
set -e
test "${launder_status}" -eq 1
grep -q "never repairs one" "${world}/6-launder.err"
grep -q "^skill: adopt-me" "${binding}"                 # untouched, both lines
grep -q "^upstream: FOREIGN@another-repo" "${binding}"
set +e
run check > /dev/null 2>&1
still_broken_status=$?
set -e
test "${still_broken_status}" -eq 1                     # still the FAIL it was

# 6e. the slot exists but carries no binding.md -- same verdict, different cause,
#     so the message has to name that cause rather than the missing field.
mv "${binding}" "${binding_dir}/legacy-snapshot.md"
set +e
run check > /dev/null 2>"${world}/6-no-binding.err"
empty_slot_status=$?
set -e
test "${empty_slot_status}" -eq 1
grep -q "no binding.md" "${world}/6-no-binding.err"
# 6e2. the refusal in 6c/6d is about a record that reads false, not about a slot
#      that merely holds other files. Bindings are multi-file by nature, so a
#      slot carrying only a legacy snapshot must still be bindable -- otherwise
#      "never repairs" would have quietly become "never writes".
run bind demo-skill --repo "${world}/repoA" --upstream demo-skill@fixture > "${world}/6-recreate.out"
grep -q "^BOUND" "${world}/6-recreate.out"
run check | grep -q "PASS shared skills hold"
mv "${binding}" "${world}/recreated.md"
mv "${world}/binding.bak" "${binding}"
# the leftover snapshot stays: bindings are multi-file by nature (retarget ledger,
# legacy snapshots), so extra files must not disturb the gate.
run check | grep -q "PASS shared skills hold"

# 6f. absence is its own state: no slot at all means this repo uses the shared
#     body's generic form. It must read as neither failure nor owed work, or
#     every unretargeted repo would sit permanently red for no reason.
mv "${binding_dir}" "${world}/unretargeted"
run check > "${world}/6-absent.out" 2>"${world}/6-absent.err"
grep -q "PASS shared skills hold" "${world}/6-absent.out"
grep -q "BINDINGS 0 current, 0 stale, 2 not retargeted" "${world}/6-absent.out"
test ! -s "${world}/6-absent.err"
if grep -qE "BINDING-(STALE|INCOMPLETE)" "${world}/6-absent.out"; then
  echo "FAIL: an absent binding was reported as stale or broken" >&2
  exit 1
fi

# 6g. bind refuses to write what nothing would ever verify: a repo outside the
#     governed set is never walked by `check`, and a first binding with no
#     upstream records a retarget without saying what from. Both leave no trace.
mkdir -p "${world}/ungoverned"
set +e
run bind demo-skill --repo "${world}/ungoverned" >/dev/null 2>"${world}/6-ungoverned.err"
ungoverned_status=$?
run bind adopt-me --repo "${world}/repoA" >/dev/null 2>"${world}/6-no-upstream.err"
no_upstream_status=$?
set -e
test "${ungoverned_status}" -eq 1
grep -q "not a governed project" "${world}/6-ungoverned.err"
test "${no_upstream_status}" -eq 1
grep -q "needs --upstream" "${world}/6-no-upstream.err"
test ! -e "${world}/ungoverned/.skill-bindings"
test ! -e "${world}/repoA/.skill-bindings/adopt-me"

# 6g2. and that refusal must not be reachable-around. A --project flag replaces
#      the governed set outright, so a `bind --project <target>` would let the
#      writer declare its own target governed and walk through 6g untouched.
#      `bind` therefore carries no such flag at all; argparse is the enforcement.
set +e
run bind demo-skill --repo "${world}/ungoverned" --project "${world}/ungoverned" \
  --upstream demo-skill@fixture >/dev/null 2>"${world}/6-bypass.err"
bypass_status=$?
set -e
test "${bypass_status}" -eq 2                 # argparse usage error, not a silent accept
grep -q -- "--project" "${world}/6-bypass.err"
test ! -e "${world}/ungoverned/.skill-bindings"

# 6g3. --sites is the same door, one step further out: the governed set lives in
#      that file, so a hand-written one naming the target grants a governance the
#      machine's own gate never reads. Closing --project alone leaves this open,
#      so `bind` accepts only the sites file `check` reads by default.
cat > "${world}/hand-written-sites.json" <<JSON
{"codex_surface": "${world}/surfaces/codex",
 "claude_surface": "${world}/surfaces/claude",
 "projects": ["${world}/ungoverned"]}
JSON
set +e
python3 "${script}" bind demo-skill --sites "${world}/hand-written-sites.json" \
  --repo "${world}/ungoverned" --upstream demo-skill@fixture \
  >/dev/null 2>"${world}/6-sites-bypass.err"
sites_bypass_status=$?
set -e
if test "${sites_bypass_status}" -ne 1 || test -e "${world}/ungoverned/.skill-bindings"; then
  echo "FAIL: a hand-written sites file granted a governance no gate reads" >&2
  exit 1
fi
grep -q "is not the sites file" "${world}/6-sites-bypass.err"

# 6h. a governed repo that is not on disk yet is a legitimate sites entry, so the
#     slot's mkdir -p would happily invent the repo from a typo. Refuse instead.
#     Registering it has to go through the sites file now, which is the point:
#     the governed set a write trusts is the one `check` will later walk.
set +e
run install "${paths[@]}" --project "${world}/ghost" > "${world}/6h-install.out" 2>&1
ghost_install_status=$?
set -e
# a repo nobody can look at is owed work, never "clean": it is the fourth kind of
# absence, and it used to leave the tally without a word.
test "${ghost_install_status}" -eq 3
grep -q "SURFACE UNREACHABLE-PROJECT.*ghost" "${world}/6h-install.out"
grep -q "PROJECTS 1 on disk, 1 unreachable" "${world}/6h-install.out"
test ! -e "${world}/ghost"
set +e
run bind demo-skill --repo "${world}/ghost" --upstream demo-skill@fixture \
  >/dev/null 2>"${world}/6-ghost.err"
ghost_status=$?
set -e
test "${ghost_status}" -eq 1
grep -q "no such repo" "${world}/6-ghost.err"
test ! -e "${world}/ghost"

# 6i. a deferred repo runs its own copy, so there is no shared body for a binding
#     there to pin. `check` never reads its bindings on purpose -- which is
#     exactly why `bind` must not write one: it would be the unverified record of
#     6g, entered from the other side.
mkdir -p "${world}/repoDEFER/.agents/skills" "${world}/repoDEFER/.claude/skills"
cat > "${shared}/registry.json" <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture",
     "deferred_in": ["repoDEFER"]},
    {"name": "adopt-me", "admitted": "2026-08-07", "why": "fixture"}
  ],
  "repo_owned": []
}
JSON
run install "${paths[@]}" --project "${world}/repoDEFER" > /dev/null
mkdir -p "${world}/repoDEFER/.claude/skills/demo-skill" \
         "${world}/repoDEFER/.skill-bindings/demo-skill"
printf -- '---\nname: demo-skill\n---\nrepoDEFER 自己那份\n' \
  > "${world}/repoDEFER/.claude/skills/demo-skill/SKILL.md"
printf 'second file so it is a copy, not a forwarder\n' \
  > "${world}/repoDEFER/.claude/skills/demo-skill/notes.md"
printf -- '---\nskill: demo-skill\nupstream: demo-skill@elsewhere\nretargeted_at: 2026-01-01\nbody_version: 00000000\n---\n' \
  > "${world}/repoDEFER/.skill-bindings/demo-skill/binding.md"
run check > "${world}/6i.out" 2>"${world}/6i.err"
grep -q "PASS shared skills hold" "${world}/6i.out"
test ! -s "${world}/6i.err"
# repoA demo + repoA adopt-me + repoDEFER adopt-me; repoDEFER's demo binding is
# never read, so its deliberately wrong hash must not appear in the tally.
grep -q "BINDINGS 0 current, 0 stale, 3 not retargeted" "${world}/6i.out"
set +e
run bind demo-skill --repo "${world}/repoDEFER" --upstream demo-skill@elsewhere \
  >/dev/null 2>"${world}/6i-bind.err"
deferred_bind_status=$?
set -e
test "${deferred_bind_status}" -eq 1
grep -q "deferred in repoDEFER" "${world}/6i-bind.err"
grep -q "^body_version: 00000000" "${world}/repoDEFER/.skill-bindings/demo-skill/binding.md"

# 6j. `check` walks the registry, so a slot naming a skill the registry no longer
#     knows is never opened again: rename a shared skill and every subscriber's
#     ledger for it goes quiet at once, with a PASS as the last word.
mkdir -p "${world}/repoA/.skill-bindings/renamed-away"
printf -- '---\nskill: renamed-away\n---\n' \
  > "${world}/repoA/.skill-bindings/renamed-away/binding.md"
set +e
run check > "${world}/6j.out" 2>"${world}/6j.err"
orphan_status=$?
set -e
test "${orphan_status}" -eq 3
grep -q "SURFACE ORPHAN-BINDING.*renamed-away" "${world}/6j.out"
test ! -s "${world}/6j.err"             # an orphaned ledger is owed work, not a violation
mv "${world}/repoA/.skill-bindings/renamed-away" "${world}/orphan-slot"
run check | grep -q "PASS shared skills hold"

# 7. relocatable: the checkout carries no absolute path of its own, so moving it
#    anywhere and re-running install re-wires it. Symlinks store paths, so the
#    stale ones must fail loudly first rather than silently resolve elsewhere.
moved="${world}/moved-clone"
mv "${shared}" "${moved}"
moved_script="${moved}/skills/shared-skills-infra/scripts/shared_skills.py"
# the sites file lives in the checkout, so it moved too; naming the old path here
# would silently fall back to this machine's real surfaces.
moved_sites="${moved}/sites.local.json"
if python3 "${moved_script}" check --sites "${moved_sites}" >"${world}/7.out" 2>"${world}/7.err"; then
  echo "FAIL: stale symlinks to the old checkout passed the gate" >&2
  exit 1
fi
grep -q "WRONG-TARGET demo-skill" "${world}/7.err"
python3 "${moved_script}" install --sites "${moved_sites}" > /dev/null
python3 "${moved_script}" check --sites "${moved_sites}" | grep -q "PASS shared skills hold"
# realpath both sides: macOS resolves /var to /private/var, which is a path
# alias, not a difference in where the link points.
test "$(realpath "${world}/surfaces/codex/demo-skill")" = "$(realpath "${moved}/skills/demo-skill")"

echo "PASS shared-skills gate"
