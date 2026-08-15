#!/usr/bin/env bash
# Positive control for the canonical-drift detector, in a synthetic pair of
# repos. Zero network: the "remote" is a local bare repo, so `fetch` is real
# without leaving the machine.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
drift="${DRIFT_SCRIPT:-${skill_dir}/scripts/check_canonical_drift.py}"
world="$(mktemp -d)"
trap 'rm -rf "${world}"' EXIT

git init -q --bare "${world}/remote.git"
git clone -q "${world}/remote.git" "${world}/canonical"
cd() { :; }   # never change this shell's directory; every call is -C
git -C "${world}/canonical" -c user.name=t -c user.email=t@t.invalid \
  commit -q --allow-empty -m "base"
git -C "${world}/canonical" branch -M main
git -C "${world}/canonical" push -q -u origin main
# Keep the local bare remote deterministic across Git defaultBranch settings.
git --git-dir="${world}/remote.git" symbolic-ref HEAD refs/heads/main

run() { python3 "${drift}" --repo "${world}/canonical" "$@"; }

# 1. good: nothing moved, nothing local, nothing dirty
run | grep -q "^PASS canonical unchanged"

# 2. hollow: TWO commits that never left this machine -- family size >=2 is
#    deliberate. A detector mutated from "for each" to "only the first" must
#    now fail either the tally or one of the per-member assertions below.
base="$(git -C "${world}/canonical" rev-parse HEAD)"
printf 'a skill nobody ruled on\n' > "${world}/canonical/snuck.md"
git -C "${world}/canonical" add -A
git -C "${world}/canonical" -c user.name=other -c user.email=other@t.invalid \
  commit -q -m "written by somebody else"
printf 'a second local change\n' > "${world}/canonical/snuck-two.md"
git -C "${world}/canonical" add -A
git -C "${world}/canonical" -c user.name=second -c user.email=second@t.invalid \
  commit -q -m "second local commit"
set +e
run >"${world}/2.out" 2>"${world}/2.err"
unpushed_status=$?
set -e
test "${unpushed_status}" -eq 1
grep -q "^UNPUSHED 2 commit(s) here are not on origin:" "${world}/2.err"
grep -q "written by somebody else" "${world}/2.err"
grep -q "second local commit" "${world}/2.err"
grep -q "other" "${world}/2.err"
grep -q "second" "${world}/2.err"

# 3. --since names every commit that landed while you were not looking. The
#    count and both identities are pinned independently of the UNPUSHED heading.
set +e
run --since "${base}" >"${world}/3.out" 2>"${world}/3.err"
moved_status=$?
set -e
test "${moved_status}" -eq 1
grep -qE "^MOVED canonical advanced since .*: 2 commit\(s\)$" "${world}/3.err"
grep -E "^      [0-9a-f]+ other <other@t\.invalid>" "${world}/3.err" >/dev/null
grep -E "^      [0-9a-f]+ second <second@t\.invalid>" "${world}/3.err" >/dev/null

# 4. dirty working tree counts as drift. TWO dirty paths make a first-only
#    implementation distinguishable, and the heading tally must tell the truth.
git -C "${world}/canonical" push -q origin main
run | grep -q "^PASS canonical unchanged"       # pushed: clean again
printf 'not committed one\n' > "${world}/canonical/loose-one.md"
printf 'not committed two\n' > "${world}/canonical/loose-two.md"
set +e
run >"${world}/4.out" 2>"${world}/4.err"
dirty_status=$?
set -e
test "${dirty_status}" -eq 1
grep -q "^DIRTY 2 uncommitted path(s):" "${world}/4.err"
grep -q "loose-one.md" "${world}/4.err"
grep -q "loose-two.md" "${world}/4.err"
mv "${world}/canonical/loose-one.md" "${world}/loose-one.md"
mv "${world}/canonical/loose-two.md" "${world}/loose-two.md"

# 5. absence is its own exit: a bad --since cannot be answered, and 3 must not
#    be reachable by anything that merely found nothing
set +e
run --since deadbeef >"${world}/5.out" 2>"${world}/5.err"
unknown_status=$?
set -e
test "${unknown_status}" -eq 3
grep -q "^CANNOT-TELL deadbeef is not a commit" "${world}/5.err"

set +e
python3 "${drift}" --repo "${world}" >"${world}/6.out" 2>"${world}/6.err"
norepo_status=$?
set -e
test "${norepo_status}" -eq 3
grep -q "^CANNOT-TELL .* is not a git checkout" "${world}/6.err"

# 6. behind: origin moves by TWO commits. Again, tally plus both subjects kills
#    a detector that reports only the first/last remote member.
git clone -q "${world}/remote.git" "${world}/other"
git -C "${world}/other" -c user.name=t -c user.email=t@t.invalid \
  commit -q --allow-empty -m "landed elsewhere one"
git -C "${world}/other" -c user.name=t -c user.email=t@t.invalid \
  commit -q --allow-empty -m "landed elsewhere two"
git -C "${world}/other" push -q origin main
set +e
run >"${world}/7.out" 2>"${world}/7.err"
behind_status=$?
set -e
test "${behind_status}" -eq 1
grep -q "^BEHIND 2 origin commit(s) this checkout does not have:" "${world}/7.err"
grep -q "landed elsewhere one" "${world}/7.err"
grep -q "landed elsewhere two" "${world}/7.err"

# 7. an unreachable remote outranks whatever else was found. Without this case
#    the precedence is untested: a run that could not see the remote but did see
#    a dirty tree would report 1, claiming it looked when it did not.
git -C "${world}/canonical" remote set-url origin "${world}/no-such-remote.git"
printf 'dirty as well\n' > "${world}/canonical/also-loose.md"
set +e
run >"${world}/8.out" 2>"${world}/8.err"
offline_status=$?
set -e
test "${offline_status}" -eq 3          # not 1: the dirty tree must not outrank it
grep -q "CANNOT-TELL could not fetch origin" "${world}/8.err"
grep -q "^DIRTY" "${world}/8.err"       # still reported, just not the verdict

# The normal run proves behavior. The outer run also plants three first-only
# mutations into the checker and requires this exact fixture to turn red.
if test "${CANONICAL_DRIFT_MUTANT_RUN:-0}" != "1"; then
  python3 "${test_dir}/mutation_proof.py"
fi

echo "PASS canonical drift detector"
