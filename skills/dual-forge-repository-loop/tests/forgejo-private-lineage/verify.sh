#!/usr/bin/env bash
set -euo pipefail

tests_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_root="$(cd "${tests_dir}/../.." && pwd)"
mode_root="${skill_root}/modes/forgejo-private-repository-loop"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT
export HOME="${tmp}/home"
export GIT_CONFIG_NOSYSTEM=1
mkdir -p "${HOME}"

total=0
failures=0
pass() { total=$((total + 1)); echo "PASS $1"; }
fail() { total=$((total + 1)); failures=$((failures + 1)); echo "FAIL $1" >&2; }
expect_zero() {
  local name="$1"; shift
  if "$@" >"${tmp}/stdout" 2>"${tmp}/stderr"; then pass "${name}"; else cat "${tmp}/stdout" "${tmp}/stderr" >&2; fail "${name}"; fi
}
expect_exit() {
  local expected="$1" name="$2"; shift 2
  set +e
  "$@" >"${tmp}/stdout" 2>"${tmp}/stderr"
  local actual=$?
  set -e
  if [ "${actual}" -eq "${expected}" ]; then pass "${name}"; else cat "${tmp}/stdout" "${tmp}/stderr" >&2; echo "expected=${expected} actual=${actual}" >&2; fail "${name}"; fi
}
init_repo() {
  local repo="$1" text="${2:-neutral content}"
  mkdir -p "${repo}"
  git -C "${repo}" init -q
  git -C "${repo}" config user.name Test
  git -C "${repo}" config user.email test@invalid.local
  printf '%s\n' "${text}" > "${repo}/README.md"
  git -C "${repo}" add README.md
  git -C "${repo}" commit -q -m "initial"
}

patterns="${tmp}/private-patterns.txt"
printf '%s\n' 'private-literal' > "${patterns}"

# All-history producer: clean control, then metadata/config/tag/LFS/worktree findings.
audit_repo="${tmp}/audit"
init_repo "${audit_repo}"
expect_zero "history audit clean" python3 "${mode_root}/scripts/audit_git_history.py" \
  --repo "${audit_repo}" --patterns "${patterns}" --output "${tmp}/audit-clean.json"
printf 'next\n' >> "${audit_repo}/README.md"
git -C "${audit_repo}" add README.md
git -C "${audit_repo}" commit -q -m "private-literal metadata"
git -C "${audit_repo}" tag -a evidence-tag -m "private-literal tag"
git -C "${audit_repo}" config test.private "private-literal config"
mkdir -p "${audit_repo}/.git/lfs/objects/aa/bb"
printf '%s\n' 'private-literal lfs object' > "${audit_repo}/.git/lfs/objects/aa/bb/object"
printf '%s\n' 'private-literal worktree' > "${audit_repo}/untracked.txt"
expect_exit 2 "history audit planted surfaces" python3 "${mode_root}/scripts/audit_git_history.py" \
  --repo "${audit_repo}" --patterns "${patterns}" --output "${tmp}/audit-red.json"
if grep -Fq 'private-literal' "${tmp}/audit-red.json"; then fail "history receipt does not expose matched bytes"; else pass "history receipt does not expose matched bytes"; fi
python3 - "${tmp}/audit-red.json" <<'PY'
import json, sys
surfaces={item['surface'] for item in json.load(open(sys.argv[1]))['matches']}
required={'commit-metadata','annotated-tag','git-config','lfs-object-content','worktree-content'}
missing=required-surfaces
if missing: raise SystemExit(f'missing surfaces: {sorted(missing)}')
PY
pass "history audit records all planted surface classes"

# Forgejo-only remote sealing and exact pre-push destination.
sealed="${tmp}/sealed"
init_repo "${sealed}"
git -C "${sealed}" remote add origin https://github.com/example/private.git
git -C "${sealed}" remote add backup ssh://git@backup.invalid/team/private.git
forgejo_url='ssh://git@forge.local/team/private.git'
expect_zero "configure Forgejo-only repository" bash "${mode_root}/scripts/configure_forgejo_only.sh" "${sealed}" "${forgejo_url}"
expect_zero "verify Forgejo-only repository" env PYTHONPATH="${mode_root}/scripts" python3 "${mode_root}/scripts/check_forgejo_only.py" "${sealed}"
hook="${sealed}/.git/hooks/pre-push"
expect_zero "pre-push exact Forgejo destination" bash -c 'cd "$1" && "$2" forgejo "$3" </dev/null' _ "${sealed}" "${hook}" "${forgejo_url}"
expect_exit 72 "pre-push GitHub destination refused" bash -c 'cd "$1" && "$2" origin https://github.com/example/private.git </dev/null' _ "${sealed}" "${hook}"
git -C "${sealed}" config --add remote.forgejo.pushurl https://github.com/example/private.git
expect_exit 2 "hidden GitHub pushurl refused" env PYTHONPATH="${mode_root}/scripts" python3 "${mode_root}/scripts/check_forgejo_only.py" "${sealed}"
git -C "${sealed}" config --unset-all remote.forgejo.pushurl
git -C "${sealed}" config remote.forgejo.pushurl "${forgejo_url}"
git -C "${sealed}" remote add extra ssh://git@forge.local/team/extra.git
expect_exit 2 "second remote refused" env PYTHONPATH="${mode_root}/scripts" python3 "${mode_root}/scripts/check_forgejo_only.py" "${sealed}"
git -C "${sealed}" remote remove extra
mkdir -p "${sealed}/.git/objects/info"
printf '%s\n' "${audit_repo}/.git/objects" > "${sealed}/.git/objects/info/alternates"
expect_exit 2 "alternate object store refused" env PYTHONPATH="${mode_root}/scripts" python3 "${mode_root}/scripts/check_forgejo_only.py" "${sealed}"
rm -f "${sealed}/.git/objects/info/alternates"
cat > "${sealed}/.gitmodules" <<'EOF'
[submodule "bad"]
  path = vendor/bad
  url = https://github.com/example/bad.git
EOF
expect_exit 2 "GitHub submodule refused" env PYTHONPATH="${mode_root}/scripts" python3 "${mode_root}/scripts/check_forgejo_only.py" "${sealed}"
rm -f "${sealed}/.gitmodules"
expect_zero "Forgejo-only repository recovers after planted controls" env PYTHONPATH="${mode_root}/scripts" python3 "${mode_root}/scripts/check_forgejo_only.py" "${sealed}"

# Clean-room packet contract.
good_packet="${tmp}/packet-good.json"
cat > "${good_packet}" <<'JSON'
{
  "schema": "forgejo-private-cleanroom-packet/v1",
  "packet_id": "permission-transaction-contract",
  "private_subject_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "items": [
    {
      "id": "transaction-state-machine",
      "kind": "state-machine",
      "statement": "Read state before a bounded action, acquire a fresh observation, and derive the terminal result mechanically.",
      "assertions": [
        "A transport acknowledgement cannot create a successful terminal result by itself.",
        "An unchanged observed state after an acknowledged action is a silent no-op."
      ],
      "public_references": [
        {"label": "Git documentation", "url": "https://git-scm.com/docs"}
      ]
    }
  ]
}
JSON
expect_zero "clean-room packet positive" python3 "${mode_root}/scripts/check_cleanroom_packet.py" "${good_packet}" --private-patterns "${patterns}"
python3 - "${good_packet}" "${tmp}/packet-field.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); p['items'][0]['source_path']='private/file.md'
json.dump(p,open(sys.argv[2],'w'),indent=2)
PY
expect_exit 2 "clean-room source field refused" python3 "${mode_root}/scripts/check_cleanroom_packet.py" "${tmp}/packet-field.json" --private-patterns "${patterns}"
python3 - "${good_packet}" "${tmp}/packet-literal.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); p['items'][0]['statement']='private-literal copied into a neutral packet'
json.dump(p,open(sys.argv[2],'w'),indent=2)
PY
expect_exit 2 "clean-room private literal refused" python3 "${mode_root}/scripts/check_cleanroom_packet.py" "${tmp}/packet-literal.json" --private-patterns "${patterns}"
if grep -Fq 'private-literal' "${tmp}/stderr"; then fail "clean-room diagnostics do not expose private literal"; else pass "clean-room diagnostics do not expose private literal"; fi
private_text="${tmp}/private-text.txt"
printf '%s\n' 'Copper orchard relays rotate amber witnesses beneath the silent north bridge every winter morning.' > "${private_text}"
expect_zero "private fingerprint producer" python3 "${mode_root}/scripts/build_private_fingerprints.py" --source "${private_text}" --output "${tmp}/fingerprints.json" --shingle-size 7
python3 - "${good_packet}" "${tmp}/packet-copy.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); p['items'][0]['statement']='Copper orchard relays rotate amber witnesses beneath the silent north bridge every winter morning.'
json.dump(p,open(sys.argv[2],'w'),indent=2)
PY
expect_exit 2 "distinctive copied prose refused" python3 "${mode_root}/scripts/check_cleanroom_packet.py" "${tmp}/packet-copy.json" --private-fingerprints "${tmp}/fingerprints.json"

# Provider retention disposition.
python3 - "${tmp}/provider-good.json" <<'PY'
import json,sys
surfaces=['branches','tags','pull_request_refs','review_diffs','actions_logs','actions_artifacts','actions_caches','releases','packages','pages','wiki','lfs','forks','mirrors','code_search_indexes','backups_replicas','webhooks','deploy_keys','apps','environments','secrets_metadata']
doc={'schema':'provider-retention-disposition/v1','repository_identity_digest':'b'*64,'surfaces':{name:'CONFIRMED' for name in surfaces}}
json.dump(doc,open(sys.argv[1],'w'),indent=2)
PY
expect_zero "provider disposition complete inventory" python3 "${mode_root}/scripts/check_provider_retention.py" "${tmp}/provider-good.json"
python3 - "${tmp}/provider-good.json" "${tmp}/provider-bad.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); p['surfaces']['backups_replicas']='ERASED'; json.dump(p,open(sys.argv[2],'w'),indent=2)
PY
expect_exit 2 "provider global erasure overclaim refused" python3 "${mode_root}/scripts/check_provider_retention.py" "${tmp}/provider-bad.json"

# Local retirement inventory: what still reaches private objects after sealing.
python3 - "${tmp}/retire-good.json" <<'PY'
import json,sys
surfaces=['clones','worktrees','mirrors','bundles','caches','forks','credentials']
doc={'schema':'private-retirement-inventory/v1','repository_identity_digest':'c'*64,
     'observed_at_head':'d'*40,'surfaces':{name:'RETIRED' for name in surfaces}}
json.dump(doc,open(sys.argv[1],'w'),indent=2)
PY
expect_zero "retirement inventory complete" python3 "${mode_root}/scripts/check_retirement_inventory.py" "${tmp}/retire-good.json" --receipt "${tmp}/retire-receipt.json"
if grep -Fq '"overall_state": "TERMINAL"' "${tmp}/retire-receipt.json"; then pass "retired inventory receipt is terminal"; else fail "retired inventory receipt is terminal"; fi
for mutation in drop-surface erased outstanding unbound-head; do
  python3 - "${tmp}/retire-good.json" "${tmp}/retire-${mutation}.json" "${mutation}" <<'PY'
import json,sys
doc=json.load(open(sys.argv[1])); mutation=sys.argv[3]
if mutation=='drop-surface': del doc['surfaces']['bundles']
elif mutation=='erased': doc['surfaces']['caches']='ERASED'
elif mutation=='outstanding': doc['surfaces']['clones']='PRESENT'
elif mutation=='unbound-head': doc['observed_at_head']='HEAD'
json.dump(doc,open(sys.argv[2],'w'),indent=2)
PY
done
expect_exit 2 "retirement inventory missing surface refused" python3 "${mode_root}/scripts/check_retirement_inventory.py" "${tmp}/retire-drop-surface.json"
expect_exit 2 "retirement erasure overclaim refused" python3 "${mode_root}/scripts/check_retirement_inventory.py" "${tmp}/retire-erased.json"
expect_exit 2 "retirement inventory unbound to a head refused" python3 "${mode_root}/scripts/check_retirement_inventory.py" "${tmp}/retire-unbound-head.json"
expect_zero "surviving local copy stays in the inventory" python3 "${mode_root}/scripts/check_retirement_inventory.py" "${tmp}/retire-outstanding.json" --receipt "${tmp}/retire-outstanding-receipt.json"
if grep -Fq '"overall_state": "OUTSTANDING"' "${tmp}/retire-outstanding-receipt.json"; then pass "surviving local copy refuses a terminal receipt"; else fail "surviving local copy refuses a terminal receipt"; fi

# Fresh-root production and no-shared-lineage proof.
public_source="${tmp}/public-source"
init_repo "${public_source}" "independently authored public contract"
fresh="${tmp}/fresh"
expect_zero "fresh public root producer" bash "${mode_root}/scripts/create_fresh_root_snapshot.sh" "${public_source}" "${fresh}" --patterns "${patterns}" --receipt "${tmp}/fresh-receipt.json"
expect_zero "fresh root has no shared private lineage" bash "${mode_root}/scripts/assert_no_shared_lineage.sh" "${fresh}" "${audit_repo}"
copied="${tmp}/copied"
git clone -q "${audit_repo}" "${copied}"
expect_exit 2 "copied private lineage refused" bash "${mode_root}/scripts/assert_no_shared_lineage.sh" "${copied}" "${audit_repo}"
shared_blob="${tmp}/shared-blob"
init_repo "${shared_blob}" "neutral content"
expect_exit 2 "shared non-empty Git object refused" bash "${mode_root}/scripts/assert_no_shared_lineage.sh" "${shared_blob}" "${audit_repo}"

# The producer already refuses these tracked paths. Without a control the refusal
# branch is a claim: nothing proves it goes red, and a widened glob would not
# report anything either.
plant_and_reject() {
  local name="$1" file="$2" body="$3" repo="${tmp}/public-${1// /-}"
  init_repo "${repo}" "independently authored public contract"
  printf '%s\n' "${body}" > "${repo}/${file}"
  git -C "${repo}" add "${file}"
  git -C "${repo}" commit -q -m "track ${file}"
  expect_exit 67 "${name}" bash "${mode_root}/scripts/create_fresh_root_snapshot.sh" \
    "${repo}" "${tmp}/fresh-${1// /-}" --patterns "${patterns}"
}
plant_and_reject "committed private denylist refused" "private-denylist.txt" "private-literal"
plant_and_reject "committed runtime evidence refused" "run.log" "runtime line"

# Syntax and executable inventory.
expect_zero "Python sources compile" python3 -m compileall -q "${mode_root}/scripts"
for executable in "${mode_root}"/scripts/*.sh "${mode_root}"/hooks/*; do
  expect_zero "bash syntax $(basename "${executable}")" bash -n "${executable}"
done

printf 'TOTAL=%s FAILED=%s\n' "${total}" "${failures}"
[ "${total}" -ge 20 ]
[ "${failures}" -eq 0 ]
