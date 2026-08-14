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
# The linter is copied in because this file exercises it directly, not
# because `check` needs it: `check` no longer runs it.
cp "$(dirname "${real_script}")/check_dead_assertions.py" \
   "${shared}/skills/shared-skills-infra/scripts/"
# `check` now runs the two #1 gates as subprocesses, so the fixture has to carry
# them. Leaving one out makes every later assertion pass or fail for a reason
# that has nothing to do with what it is testing -- the same defect that had
# check_publication_boundary.py reporting five killed mutations while killing
# none.
cp "$(dirname "${real_script}")/check_body_neutrality.py" \
   "$(dirname "${real_script}")/check_binding_stale.py" \
   "${shared}/skills/shared-skills-infra/scripts/"
mkdir -p "${shared}/evals"
printf '{\n  "schema": "body-neutrality/v1",\n  "owed": {}\n}\n' \
  > "${shared}/evals/body-neutrality.json"
printf -- '---\nname: demo-skill\n---\nbody\n' > "${shared}/skills/demo-skill/SKILL.md"
# the tool is itself a registered skill, so its fixture needs the same shape
printf -- '---\nname: shared-skills-infra\n---\nbody\n' \
  > "${shared}/skills/shared-skills-infra/SKILL.md"

cat > "${shared}/registry.json" <<'JSON'
{
  "schema": "shared-skills-registry/v2",
  "canonical_root": "skills",
  "shared": [
    {"name": "demo-skill", "admitted": "2026-08-07", "why": "fixture"},
    {"name": "shared-skills-infra", "admitted": "2026-08-07",
     "why": "the tool itself sits in canonical, so it needs an entry like anything else"}
  ],
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
# One assertion per line: in `test A && test B` only B runs under `set -e`, so a
# failing A short-circuits and the script sails past it. That is how the old
# `test ! -e "${adoptee}" && test ! -e "${rival}"` survived here while being
# flatly false -- adopt moves the winner to canonical and sweeps the rival to
# the backup, and then `link` re-points both project surfaces at canonical. So
# what must hold is "no project keeps a copy", not "nothing is here"; the copy
# going to the backup is asserted two lines down.
test -L "${adoptee}"
test -L "${rival}"
test -f "${moved_probe:-${shared}}/skills/adopt-me/SKILL.md"
test -f "${world}/swept/adopt-me/repoA_.claude/SKILL.md"   # swept, not deleted
test -L "${world}/surfaces/codex/adopt-me"                 # user surface untouched by sweep
run check | grep -q "PASS shared skills hold"

# 5e. dead-assertion sweep -- the gate that keeps every other gate honest.
#     Each gate's only positive control is a verify.sh, so an assertion that
#     physically cannot fail is an unguarded gate wearing a green badge: it
#     passes review under the name "tests are green". The fixtures below are
#     written at runtime rather than committed, because a committed hollow
#     fixture would be swept by the linter itself and turn this repo red forever.
linter="${shared}/skills/shared-skills-infra/scripts/check_dead_assertions.py"
fixture="${shared}/tests/swept/verify.sh"
mkdir -p "$(dirname "${fixture}")"
lint() { python3 "${linter}" --root "${shared}" >"${world}/lint.out" 2>"${world}/lint.err"; }

# good fixture: the live forms, including the ones a careless rule would flag
cat > "${fixture}" <<'GOOD'
#!/usr/bin/env bash
set -eEuo pipefail
test -d /tmp
test ! -e /nonexistent
if grep -q "Traceback" "${err}"; then echo "FAIL: a stack, not a sentence" >&2; exit 1; fi
until grep -q ready "${log}"; do sleep 1; done
mkdir -p "${d}" || true
grep "expected" "${out}" > /dev/null
set +e
run_it
status=$?
set -e
test "${status}" -eq 3
GOOD
lint
grep -q "PASS no dead assertions" "${world}/lint.out"
# the count is asserted, not just the word PASS: a glob that matched no file
# would also print PASS, and an absent sweep must not read as a clean one

# a glob that matched nothing must exit 3, not 0. An absent sweep and a clean
# sweep have to look different, or pointing the linter at the wrong root reads
# as a pass forever.
mkdir -p "${world}/empty-root"
set +e
python3 "${linter}" --root "${world}/empty-root" \
  >"${world}/lint-empty.out" 2>"${world}/lint-empty.err"
empty_status=$?
set -e
test "${empty_status}" -eq 3
grep -q "^NOTHING-TO-DO no shell test file matched" "${world}/lint-empty.err"

# hollow (1): a line-leading `!` -- bash exempts inverted commands from set -e
cat > "${fixture}" <<'HOLLOW1'
#!/usr/bin/env bash
set -eEuo pipefail
! grep -q "Traceback" "${err}"
HOLLOW1
if lint; then
  echo "FAIL: linter passed a dead '!' assertion" >&2
  exit 1
fi
grep -q "DEAD-NEGATION tests/swept/verify.sh:3" "${world}/lint.err"
grep -q 'write: if grep -q "Traceback"' "${world}/lint.err"   # names the correct form
# `check` deliberately stays green with a dead assertion in the tree: the linter
# is its own tool, not a precondition of the governance gate. Wiring it in meant
# a missing or broken linter also took out the shadowing check and the symlink
# check -- a blast radius larger than the class of bug being caught. The sweep's
# own refusal is asserted three lines up, where it belongs.
run check | grep -q "PASS shared skills hold"

# hollow (2): `test A && test B` -- only B is under set -e
cat > "${fixture}" <<'HOLLOW2'
#!/usr/bin/env bash
set -eEuo pipefail
test ! -e "${a}" && test ! -e "${b}"
HOLLOW2
if lint; then
  echo "FAIL: linter passed a dead '&&' chain" >&2
  exit 1
fi
grep -q "DEAD-AND-CHAIN tests/swept/verify.sh:3" "${world}/lint.err"
grep -q "put each assertion on its own line" "${world}/lint.err"

# hollow (3): `|| true` swallows the status. The second line is the control --
# mkdir runs for its effect, and flagging it would be the noise that gets a
# linter switched off.
cat > "${fixture}" <<'HOLLOW3'
#!/usr/bin/env bash
set -eEuo pipefail
grep -q "expected" "${out}" || true
mkdir -p "${d}" || true
HOLLOW3
if lint; then
  echo "FAIL: linter passed an assertion swallowed by '|| true'" >&2
  exit 1
fi
grep -q "DEAD-SWALLOW tests/swept/verify.sh:3" "${world}/lint.err"
if grep -q "DEAD-SWALLOW tests/swept/verify.sh:4" "${world}/lint.err"; then
  echo "FAIL: 'mkdir ... || true' is best-effort, not a dead assertion" >&2
  exit 1
fi

# hollow (4): `grep >/dev/null` with no -q, inside a set +e region where its
# status goes nowhere. Line 6 is the control: the identical line under set -e
# does kill the script (probed on bash 5.3.3), so calling it dead would be false.
cat > "${fixture}" <<'HOLLOW4'
#!/usr/bin/env bash
set -eEuo pipefail
set +e
grep "expected" "${out}" > /dev/null
set -e
grep "expected" "${out}" > /dev/null
HOLLOW4
if lint; then
  echo "FAIL: linter passed a grep whose status is discarded" >&2
  exit 1
fi
grep -q "DEAD-DISCARD tests/swept/verify.sh:4" "${world}/lint.err"
if grep -q "DEAD-DISCARD tests/swept/verify.sh:6" "${world}/lint.err"; then
  echo "FAIL: a redirected grep under set -e is live, not dead" >&2
  exit 1
fi

# inverse control: `!` in an if/while/until CONDITION is legitimate and
# load-bearing. Flagging it would make the linter a noise source, and a noisy
# linter gets switched off -- worse than having none.
cat > "${fixture}" <<'LEGIT'
#!/usr/bin/env bash
set -eEuo pipefail
if ! grep -q "expected" "${out}"; then echo "FAIL: line missing" >&2; exit 1; fi
while ! test -e "${flag}"; do sleep 1; done
until ! grep -q pending "${log}"; do sleep 1; done
if ! grep -q a "${out}" \
   && ! grep -q b "${out}"; then echo "FAIL: neither" >&2; exit 1; fi
if grep -q x "${out}"; then :; elif ! grep -q y "${out}"; then echo "FAIL: no y" >&2; exit 1; fi
[[ ! -e "${out}" ]] && printf 'a [[ ]] test operator is not command negation\n'
LEGIT
lint
grep -q "PASS no dead assertions" "${world}/lint.out"
run check | grep -q "PASS shared skills hold"


# fixtures done; the world must be clean before section 6 relocates it
mv "${shared}/tests" "${world}/fixture-attic"

# 5d. A directory nobody registered can sit in canonical and be reachable from
#     every project while the gate reports PASS -- that is how gitlab-delivery-loop
#     went live unruled on 2026-08-07 (#13). The gate has to ask the question in
#     both directions, not only "is each registered skill in order?".
run check | grep -q "PASS shared skills hold"          # clean before
mkdir -p "${shared}/skills/snuck-in"
printf -- '---\nname: snuck-in\n---\nnobody ruled on me\n' \
  > "${shared}/skills/snuck-in/SKILL.md"
if run check >"${world}/5d.out" 2>"${world}/5d.err"; then
  echo "FAIL: an unregistered canonical skill passed the gate" >&2
  exit 1
fi
grep -q "UNREGISTERED snuck-in" "${world}/5d.err"
# a file, and a dotted directory, are not skills and must not be reported
printf 'loose\n' > "${shared}/skills/stray-note.md"
mkdir -p "${shared}/skills/.cache"
# Caught by this branch's own linter after #14 landed carrying it: `|| true`
# discarded the status and nothing afterwards read $?, so this line could not
# have failed however `check` behaved.
set +e; run check 2>"${world}/5d2.err"; noise_status=$?; set -e
test "${noise_status}" -ne 0        # still refusing -- snuck-in has not gone away
grep -q "UNREGISTERED snuck-in" "${world}/5d2.err"
if grep -qE "UNREGISTERED (stray-note|\.cache)" "${world}/5d2.err"; then
  echo "FAIL: a loose file or dotted directory was reported as a skill" >&2
  exit 1
fi
mv "${shared}/skills/snuck-in" "${world}/snuck-in-parked"      # moved, not deleted
mv "${shared}/skills/stray-note.md" "${world}/stray-note.md"
run check | grep -q "PASS shared skills hold"          # clean again

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

# 7. the real checkout, read-only. The fixtures above prove each rule in a
#    synthetic world; this proves the rules hold where they are load-bearing,
#    over every tests/**/verify.sh and tests/run-all.sh actually shipped.
#    It is also the only thing that puts *this* file under the linter -- its
#    heredocs included, whose bodies must be skipped or every hollow fixture
#    above would be read as live code and reported against this gate.
python3 "$(dirname "${real_script}")/check_dead_assertions.py" > "${world}/7.out"
grep -q "^PASS no dead assertions" "${world}/7.out"

# 8. the two #1 gates are folded into `check` with different weights, and the
#    difference is the point. A shared body naming a host repository FAILS,
#    because it reaches four other repositories as if it were true there; a
#    binding pinned to an older body SURFACES, because it means "re-retarget",
#    not "broken". Wired-but-never-exercised would leave both indistinguishable
#    from absent.
printf '# Demo\n\nRun this inside skill-bettor.\n' \
  > "${moved}/skills/shared-skills-infra/BOUND.md"
set +e
python3 "${moved_script}" check --sites "${sites}" \
  > "${world}/8.out" 2> "${world}/8.err"
neutrality_rc=$?
set -e
[ "${neutrality_rc}" -eq 1 ] || {
  echo "FAIL: a host-bound shared body exited ${neutrality_rc}, expected 1" >&2
  exit 1; }
grep -q "names a host repository" "${world}/8.err"
rm "${moved}/skills/shared-skills-infra/BOUND.md"

# 9. a stale binding surfaces and `check` still passes. Nothing follows, so the
#    planted slot stays in the discarded temp world rather than being cleaned up.
mkdir -p "${moved}/.skill-bindings/shared-skills-infra"
zeros="$(python3 -c 'print("0" * 64)')"
{
  printf -- '---\n'
  printf 'skill: shared-skills-infra\n'
  printf 'upstream: antigravity-shared-skills-infra@shared\n'
  printf 'retargeted_at: 2026-08-14\n'
  printf 'body_version: %s\n' "${zeros}"
  printf -- '---\n\nplanted\n'
} > "${moved}/.skill-bindings/shared-skills-infra/binding.md"
python3 "${moved_script}" check --sites "${sites}" \
  > "${world}/9.out" 2> "${world}/9.err"
grep -q "^SURFACE" "${world}/9.out"
grep -q "re-retarget" "${world}/9.out"
grep -q "^PASS shared skills hold" "${world}/9.out"

echo "PASS shared-skills gate"
