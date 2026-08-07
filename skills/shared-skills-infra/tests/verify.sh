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

# 6. relocatable: the checkout carries no absolute path of its own, so moving it
#    anywhere and re-running install re-wires it. Symlinks store paths, so the
#    stale ones must fail loudly first rather than silently resolve elsewhere.
moved="${world}/moved-clone"
mv "${shared}" "${moved}"
moved_script="${moved}/skills/shared-skills-infra/scripts/shared_skills.py"
if python3 "${moved_script}" check --sites "${sites}" >"${world}/6.out" 2>"${world}/6.err"; then
  echo "FAIL: stale symlinks to the old checkout passed the gate" >&2
  exit 1
fi
grep -q "WRONG-TARGET demo-skill" "${world}/6.err"
python3 "${moved_script}" install --sites "${sites}" > /dev/null
python3 "${moved_script}" check --sites "${sites}" | grep -q "PASS shared skills hold"
# realpath both sides: macOS resolves /var to /private/var, which is a path
# alias, not a difference in where the link points.
test "$(realpath "${world}/surfaces/codex/demo-skill")" = "$(realpath "${moved}/skills/demo-skill")"

# 7. body-not-neutral: the shared body is only shared if it survives being
#    copied verbatim into another repo. A paragraph that names one repo, or a
#    home-anchored path, is binding wearing body's clothes -- it becomes false
#    in place the moment a second repo reads it. Enforcement is per skill on
#    purpose: today's tree is mostly unmigrated, and a gate that is red on day
#    one is a gate that gets switched off.
shared="${moved}"                  # section 6 left the live clone here
script="${moved_script}"           # `run` resolves both at call time

mkdir -p "${shared}/skills/neutral-skill/modules" \
         "${shared}/skills/private-skill" \
         "${shared}/skills/queued-skill/modules" \
         "${shared}/skills/queued-home-skill" \
         "${shared}/skills/bound-skill" \
         "${shared}/skills/broken-skill"

printf -- '---\nname: neutral-skill\n---\nMethod and contract only; every path arrives by flag.\n' \
  > "${shared}/skills/neutral-skill/SKILL.md"
printf -- '# method\n\nAsk of each line: copied into another repo, is it still true?\n' \
  > "${shared}/skills/neutral-skill/modules/method.md"

printf -- '---\nname: private-skill\n---\nOwned by ix-agy; the device surface lives under ~/Library.\n' \
  > "${shared}/skills/private-skill/SKILL.md"

# three offending lines over two files, every one of them a repo name alone
printf -- '---\nname: queued-skill\n---\nUpstream is the antigravity skill of the same name.\nRetargeting into ix-agy changes the paths.\n' \
  > "${shared}/skills/queued-skill/SKILL.md"
printf -- '# retarget\n\nSource: bettor-arena\n' \
  > "${shared}/skills/queued-skill/modules/retarget-map.md"

# three more lines in one file, mixing the two rules on purpose: line 4 leads
# with a repo name and ends with an absolute path, line 5 the other way round, 6
# is a path alone. The subtotals below only come out right if every token on a
# line is counted under its own rule; counting one token per line, or hardcoding
# the path subtotal, lands on numbers this file names and would reject.
printf -- '---\nname: queued-home-skill\n---\nThe antigravity operator installs it under ~/.agents/skills.\n~/.claude/skills mirrors whatever ix-agy publishes.\n~/Library holds the device cache and binds nothing else.\n' \
  > "${shared}/skills/queued-home-skill/SKILL.md"

# lines 4, 6 and 7 offend; line 5 does not, so the gate has to name three
printf -- '---\nname: bound-skill\n---\nThe pipeline standard here follows skill-bettor.\nA sentence that binds nothing.\nInstalled under ~/.agents/skills.\nThe same holds in ts-skill-bettor.\n' \
  > "${shared}/skills/bound-skill/SKILL.md"

# a body that cannot be decoded at all: not neutral, not bound -- unjudgeable
printf -- '---\nname: broken-skill\n---\nbinding? \xff\xfe nobody can tell\n' \
  > "${shared}/skills/broken-skill/SKILL.md"

write_registry() { cat > "${shared}/registry.json"; }
for fixture in neutral-skill private-skill queued-skill queued-home-skill \
               bound-skill broken-skill; do
  run link "${fixture}" > /dev/null
done

# 7a. good fixture: a neutral body under enforcement passes, and a private
#     skill naming its own owner is not the rule's business at all.
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "neutral-skill", "admitted": "2026-08-07", "why": "fixture", "body_neutral": true},
    {"name": "private-skill", "admitted": "2026-08-07", "why": "fixture",
     "scope": "private", "body_neutral": true}
  ],
  "repo_owned": []
}
JSON
run check > "${world}/7a.out"
grep -q "PASS shared skills hold" "${world}/7a.out"
! grep -q "BODY-NOT-NEUTRAL" "${world}/7a.out"

# 7b. unmigrated: the same offending body is a queue entry, not a violation.
#     Absence of a ruling must not read as breakage, so it exits 3 like every
#     other unruled state here and names its own count.
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "neutral-skill", "admitted": "2026-08-07", "why": "fixture", "body_neutral": true},
    {"name": "private-skill", "admitted": "2026-08-07", "why": "fixture",
     "scope": "private", "body_neutral": true},
    {"name": "queued-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "queued-home-skill", "admitted": "2026-08-07", "why": "fixture"}
  ],
  "repo_owned": []
}
JSON
set +e
run check > "${world}/7b.out" 2> "${world}/7b.err"
queue_status=$?
set -e
test "${queue_status}" -eq 3                    # queued != violated
grep -q "PASS shared skills hold" "${world}/7b.out"
! grep -qE "^(FAIL|REFUSE)" "${world}/7b.err"
grep -q "SURFACE BODY-NOT-NEUTRAL 6 lines in 3 files" "${world}/7b.out"
grep -qE "queued-skill +3 lines in 2 files" "${world}/7b.out"
grep -qE "queued-home-skill +3 lines in 1 files" "${world}/7b.out"
# the two subtotals are what makes the issue's baseline reproducible, and they
# overlap by design: 5 + 3 > 6 because two lines bind through both rules at
# once. Each has to be the count grep would give for that rule on its own.
grep -q "repo names 5 lines/3 files, absolute paths 3 lines/1 files" "${world}/7b.out"
! grep -q "private-skill" "${world}/7b.out"     # private scope never enters the queue
! grep -q "neutral-skill" "${world}/7b.out"

# the count is the migration's baseline, so it has to be a measurement and not
# a mood: same tree, byte-identical report.
set +e
run check > "${world}/7b2.out" 2>/dev/null
set -e
diff "${world}/7b.out" "${world}/7b2.out"

# 7b3. Two guards no fixture tree can express, so they are asserted directly
#      against the module: the gate's jurisdiction, and the fact that the report
#      is ordered by a sort rather than by whatever order the filesystem hands
#      files back. Running the same tree twice cannot see the second one -- one
#      filesystem returns one order -- so the probe supplies the disorder.
cat > "${world}/probe.py" <<'PY'
import importlib.util
import sys
from pathlib import Path

script = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("shared_skills_under_test", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
failures = []

# The token set is issue #4's ruling, pinned literally: it decides which bodies
# the gate can ever speak about, and widening or narrowing it silently moves the
# recorded migration baseline underneath everyone reading the burn-down.
expected = {"skill-bettor", "ts-skill-bettor", "bettor-arena", "antigravity",
            "ix-agy", "~/", "/Users/"}
actual = set(module.BINDING_REPOS) | set(module.BINDING_PATHS)
if actual != expected:
    failures.append(f"binding tokens drifted: {sorted(actual)} != {sorted(expected)}")

# A hit must be filed under the whole repo name it matched. Alternation is
# first-match-wins at each position, so a token that prefixes another there
# would shadow it and send whoever works the queue to the wrong repo.
shadowed = module.binding_pattern(("bettor", "bettor-arena")).findall("uses bettor-arena today")
if shadowed != ["bettor-arena"]:
    failures.append(f"a prefix token shadowed the whole repo name: {shadowed}")

# ...and the property is structural, not an ordering somebody has to preserve:
# every way of writing the tuples has to compile to the same pattern, or the
# comment saying the order is inert is a claim nobody can check.
if module.binding_pattern(tuple(sorted(actual))).pattern != module.BINDING.pattern:
    failures.append("the pattern depends on the order its tokens are written in")

real_rglob = Path.rglob
Path.rglob = lambda self, pattern: reversed(list(real_rglob(self, pattern)))
try:
    order = [(hit.file, hit.line) for hit in module.body_hits(module.REPO / "skills" / "queued-skill")]
finally:
    Path.rglob = real_rglob
if len(order) < 2 or order != sorted(order):
    failures.append(f"body_hits reports in filesystem order, not sorted: {order}")

for line in failures:
    print(f"FAIL probe: {line}", file=sys.stderr)
sys.exit(1 if failures else 0)
PY
python3 "${world}/probe.py" "${script}"

# 7c. hollow fixture: the same content under enforcement fails, naming every
#     offending line and nothing else.
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "neutral-skill", "admitted": "2026-08-07", "why": "fixture", "body_neutral": true},
    {"name": "private-skill", "admitted": "2026-08-07", "why": "fixture",
     "scope": "private", "body_neutral": true},
    {"name": "queued-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "queued-home-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "bound-skill", "admitted": "2026-08-07", "why": "fixture", "body_neutral": true}
  ],
  "repo_owned": []
}
JSON
set +e
run check >"${world}/7c.out" 2>"${world}/7c.err"
bound_status=$?
set -e
test "${bound_status}" -eq 1                    # a violated ruling, and nothing else
grep -q "FAIL BODY-NOT-NEUTRAL bound-skill: skills/bound-skill/SKILL.md:4" "${world}/7c.err"
grep -q "skills/bound-skill/SKILL.md:6" "${world}/7c.err"
grep -q "skills/bound-skill/SKILL.md:7" "${world}/7c.err"
test "$(grep -c "FAIL BODY-NOT-NEUTRAL" "${world}/7c.err")" -eq 3
grep -q "ts-skill-bettor" "${world}/7c.err"     # filed under the whole repo name it found
grep -q "queued-skill" "${world}/7c.out"        # an unruled skill stays a queue entry

# 7d. an unrecognised scope is a configuration error, not a default: guessing
#     would silently exempt a shared body from the only rule that binds it.
#     It gets its own exit code because `check` now legitimately answers 3 --
#     "16 bodies await migration" and "your registry is broken so I judged
#     nothing" must not arrive at a caller as the same number.
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture", "scope": "public"}
  ],
  "repo_owned": []
}
JSON
set +e
run check >"${world}/7d.out" 2>"${world}/7d.err"
scope_status=$?
set -e
test "${scope_status}" -eq 4                    # refused != violated, refused != unruled
grep -q "^REFUSE demo-skill: unknown scope 'public'" "${world}/7d.err"
! grep -q "^FAIL" "${world}/7d.err"

# 7e. a refusal must not eat the verdicts already reached. Both refusal paths
#     used to raise out of the accumulating loop, so a typo -- or one body that
#     would not decode -- deleted every real violation found before it: the gate
#     printed a single complaint and the broken symlink behind it was never
#     named. All three findings have to survive each other, in one run.
mv "${world}/surfaces/codex/demo-skill" "${world}/surfaces/codex/demo-skill.aside"
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "bound-skill", "admitted": "2026-08-07", "why": "fixture", "scope": "publik"},
    {"name": "broken-skill", "admitted": "2026-08-07", "why": "fixture"}
  ],
  "repo_owned": []
}
JSON
set +e
run check >"${world}/7e.out" 2>"${world}/7e.err"
mixed_status=$?
set -e
test "${mixed_status}" -eq 1                    # a real violation outranks a refusal
grep -q "FAIL NOT-A-SYMLINK demo-skill" "${world}/7e.err"
grep -q "REFUSE bound-skill: unknown scope 'publik'" "${world}/7e.err"
grep -q "REFUSE unreadable body: .*broken-skill" "${world}/7e.err"
mv "${world}/surfaces/codex/demo-skill.aside" "${world}/surfaces/codex/demo-skill"

# 7f. `body_neutral` is a ruling, so it is read as strictly as `scope` is.
#     false means "not migrated" -- the same queue absence means -- and a
#     misspelt key is refused rather than read as absence, or a body somebody
#     already migrated would sit in the queue forever with nobody able to see
#     why the gate never looked at it.
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "bound-skill", "admitted": "2026-08-07", "why": "fixture", "body_neutral": false}
  ],
  "repo_owned": []
}
JSON
set +e
run check >"${world}/7f.out" 2>"${world}/7f.err"
false_status=$?
set -e
test "${false_status}" -eq 3                    # explicit "not yet" == queue, not enforcement
grep -qE "bound-skill +3 lines in 1 files" "${world}/7f.out"
! grep -qE "^(FAIL|REFUSE)" "${world}/7f.err"

write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "bound-skill", "admitted": "2026-08-07", "why": "fixture", "body_netural": true}
  ],
  "repo_owned": []
}
JSON
set +e
run check >"${world}/7g.out" 2>"${world}/7g.err"
typo_status=$?
set -e
test "${typo_status}" -eq 4
grep -q "REFUSE bound-skill: unrecognised registry key(s) 'body_netural'" "${world}/7g.err"

# a quoted "true" is the other half of the same mistake, and the dangerous
# half: every non-empty string is truthy, so it would switch enforcement on for
# a body nobody ruled on -- the exact inversion the per-skill opt-in prevents.
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "bound-skill", "admitted": "2026-08-07", "why": "fixture", "body_neutral": "true"}
  ],
  "repo_owned": []
}
JSON
set +e
run check >"${world}/7g2.out" 2>"${world}/7g2.err"
string_status=$?
set -e
test "${string_status}" -eq 4
grep -q "REFUSE bound-skill: body_neutral is 'true'" "${world}/7g2.err"
! grep -q "BODY-NOT-NEUTRAL bound-skill" "${world}/7g2.err"

# 7h. a body nobody can decode is unjudgeable, not clean and not broken: it
#     exits 4 and says what to do about it. Counting it neutral is exactly how
#     a gate decays into decoration.
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "broken-skill", "admitted": "2026-08-07", "why": "fixture"}
  ],
  "repo_owned": []
}
JSON
set +e
run check >"${world}/7h.out" 2>"${world}/7h.err"
unreadable_status=$?
set -e
test "${unreadable_status}" -eq 4
grep -q "REFUSE unreadable body: .*skills/broken-skill/SKILL.md" "${world}/7h.err"
grep -q "re-save it as UTF-8" "${world}/7h.err"   # a sentence naming the next move
! grep -q "SURFACE" "${world}/7h.out"             # never quietly counted as neutral

# 7i. an entry with no name can only crash: every verb dereferences it. The
#     top-level handler answers 4 for the same reason -- the invariant could not
#     be established from the input, which is neither a verdict nor a to-do.
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [{"admitted": "2026-08-07", "why": "somebody deleted the name"}],
  "repo_owned": []
}
JSON
set +e
run check >"${world}/7i.out" 2>"${world}/7i.err"
nameless_status=$?
set -e
test "${nameless_status}" -eq 4
grep -q "REFUSE registry 'shared'\[0\] has no usable name" "${world}/7i.err"
! grep -q "Traceback" "${world}/7i.err"

# 7j. A broken registry must not be answerable as "just some pending work".
#     `deferred_in` was the one ruling nothing type-checked, and it is the
#     ruling that suppresses shadowing reports, so a dict there read as a
#     deferral nobody wrote: the gate exempted that repo, found nothing left to
#     fail on, and reported the open migration queue -- exit 3, "PASS shared
#     skills hold". The exact code is asserted, not merely non-zero: 3 is what
#     an untouched queue answers, and "your registry is broken" arriving at a
#     caller as that same number is the whole defect.
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "queued-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "bound-skill", "admitted": "2026-08-07", "why": "fixture",
     "deferred_in": {"repoA": true}}
  ],
  "repo_owned": []
}
JSON
set +e
run check >"${world}/7j.out" 2>"${world}/7j.err"
broken_defer_status=$?
set -e
test "${broken_defer_status}" -eq 4             # refused, and distinct from the queue's 3
grep -q "REFUSE bound-skill: deferred_in is {'repoA': True}" "${world}/7j.err"
! grep -q "PASS shared skills hold" "${world}/7j.out"
grep -q "SURFACE BODY-NOT-NEUTRAL" "${world}/7j.out"    # the queue is still reported...
grep -qE "queued-skill +3 lines in 2 files" "${world}/7j.out"   # ...just not as the verdict

# 7k. ...and the same broken entry must not hide its own shadowing. The defer
#     list decides which copies go unreported, so an unreadable one is read as
#     deferring nothing: the copy gets named, and the entry gets refused, in one
#     run. Both problems on that one entry surface too -- a registry that stops
#     being reported after its first complaint sends whoever fixes it back for
#     another round per typo.
mv "${world}/repoA/.claude/skills/demo-skill" "${world}/repoA/.claude/skills/demo-skill.aside"
mkdir -p "${world}/repoA/.claude/skills/demo-skill"
printf -- '---\nname: demo-skill\n---\nlocal fork\n' \
  > "${world}/repoA/.claude/skills/demo-skill/SKILL.md"
printf 'second file so it is a copy, not a forwarder\n' \
  > "${world}/repoA/.claude/skills/demo-skill/notes.md"
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture",
     "scope": "publik", "deferred_in": {"repoA": true}}
  ],
  "repo_owned": []
}
JSON
set +e
run check >"${world}/7k.out" 2>"${world}/7k.err"
hidden_shadow_status=$?
set -e
test "${hidden_shadow_status}" -eq 1            # a violation outranks a refusal, still
grep -q "FAIL SHADOWED demo-skill: repoA/.claude" "${world}/7k.err"
grep -q "REFUSE demo-skill: deferred_in is" "${world}/7k.err"
grep -q "REFUSE demo-skill: unknown scope 'publik'" "${world}/7k.err"
mv "${world}/repoA/.claude/skills/demo-skill" "${world}/7k-shadow-copy"
mv "${world}/repoA/.claude/skills/demo-skill.aside" "${world}/repoA/.claude/skills/demo-skill"

# 7l. A shape `set()` cannot iterate used to end the run in a bare TypeError
#     traceback naming neither the entry nor the key -- and it exited 1, which
#     is the code for a ruling this tool checked and found violated. Private
#     scope is asserted alongside because the crash happened before any scope
#     was consulted: an exemption from the body rule must not become an
#     exemption from being well-formed.
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "private-skill", "admitted": "2026-08-07", "why": "fixture",
     "scope": "private", "body_neutral": true, "deferred_in": 7}
  ],
  "repo_owned": []
}
JSON
set +e
run check >"${world}/7l.out" 2>"${world}/7l.err"
untyped_status=$?
set -e
test "${untyped_status}" -eq 4                  # unjudgeable, not "violated"
grep -q "REFUSE private-skill: deferred_in is 7" "${world}/7l.err"
grep -q "list of repo directory names" "${world}/7l.err"   # a sentence naming the next move
! grep -q "Traceback" "${world}/7l.err"

# `link` writes into every project the ruling does not defer, so it refuses a
# defer list it cannot read rather than acting on a guess.
set +e
run link private-skill >"${world}/7l2.out" 2>"${world}/7l2.err"
link_status=$?
set -e
test "${link_status}" -eq 4
grep -q "refusing to link against a defer list I cannot read" "${world}/7l2.err"
! grep -q "Traceback" "${world}/7l2.err"

# 8. install answers its own question. A fresh clone's first documented command
#    must not exit non-zero because somebody else's migration queue is open --
#    every `set -e` caller would stop there -- and it must still fail when the
#    wiring it just performed does not hold.
write_registry <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "queued-skill", "admitted": "2026-08-07", "why": "fixture"}
  ],
  "repo_owned": []
}
JSON
set +e
run install > "${world}/8.out" 2>"${world}/8.err"
install_status=$?
set -e
test "${install_status}" -eq 0                  # wired and linked, queue and all
grep -q "^WIRED" "${world}/8.out"
grep -q "SURFACE BODY-NOT-NEUTRAL" "${world}/8.out"   # reported, just not install's verdict

mv "${world}/repoA/.claude/skills/demo-skill" "${world}/repoA/.claude/skills/demo-skill.aside"
mkdir -p "${world}/repoA/.claude/skills/demo-skill"
printf -- '---\nname: demo-skill\n---\nlocal fork\n' \
  > "${world}/repoA/.claude/skills/demo-skill/SKILL.md"
printf 'second file so it is a copy, not a forwarder\n' \
  > "${world}/repoA/.claude/skills/demo-skill/notes.md"
set +e
run install > "${world}/8b.out" 2>"${world}/8b.err"
shadow_status=$?
set -e
test "${shadow_status}" -eq 1                   # a violation still comes straight through
grep -q "SHADOWED demo-skill" "${world}/8b.err"

echo "PASS shared-skills gate"
