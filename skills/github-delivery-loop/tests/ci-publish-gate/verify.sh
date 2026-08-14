#!/usr/bin/env bash
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(dirname "$(dirname "$test_dir")")"
checker="$skill_dir/scripts/ci_publish_gate.py"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

python3 "$checker" --selftest

git -C "$scratch" init -q -b main
git -C "$scratch" config user.email fixture@example.test
git -C "$scratch" config user.name fixture
printf 'fixture\n' > "$scratch/README.md"
git -C "$scratch" add README.md
git -C "$scratch" commit -qm fixture
head_sha="$(git -C "$scratch" rev-parse HEAD)"

render() {
  local source=$1 target=$2
  python3 - "$source" "$target" "$head_sha" <<'PY'
import pathlib, sys
source, target, head = sys.argv[1:]
text = pathlib.Path(source).read_text(encoding="utf-8").replace("__HEAD__", head)
pathlib.Path(target).write_text(text, encoding="utf-8")
PY
}

render "$test_dir/fixtures/good/snapshot.json" "$scratch/good-snapshot.json"
render "$test_dir/fixtures/good/verification.json" "$scratch/good-verification.json"
render "$test_dir/fixtures/hollow/snapshot.json" "$scratch/hollow-snapshot.json"
render "$test_dir/fixtures/hollow/verification.json" "$scratch/hollow-verification.json"

# Evidence cannot be a static fixture: its digests bind the scratch repository's
# exact head and tree.
seal() { python3 "$test_dir/seal.py" "$checker" "$scratch" "$1" "$2" "${3-}"; }
seal "$scratch/good-verification.json" "$scratch/good-evidence.json"
seal "$scratch/hollow-verification.json" "$scratch/hollow-evidence.json"

python3 "$checker" evaluate \
  --repo-root "$scratch" \
  --snapshot "$scratch/good-snapshot.json" \
  --verification "$scratch/good-verification.json" \
  --verification-evidence "$scratch/good-evidence.json" \
  --intent initial-pr \
  --json > "$scratch/good.out"
grep -q '"decision": "ALLOW"' "$scratch/good.out"
grep -q '"reason": "allow-initial-pr"' "$scratch/good.out"

set +e
python3 "$checker" evaluate \
  --repo-root "$scratch" \
  --snapshot "$scratch/hollow-snapshot.json" \
  --verification "$scratch/hollow-verification.json" \
  --verification-evidence "$scratch/hollow-evidence.json" \
  --intent initial-pr \
  --json > "$scratch/hollow.out" 2> "$scratch/hollow.err"
rc=$?
set -e
[ "$rc" -eq 2 ] || { echo "hollow expected exit 2, got $rc" >&2; exit 1; }
grep -q '"decision": "BLOCK"' "$scratch/hollow.out"
grep -q '"reason": "billing-circuit-open"' "$scratch/hollow.out"

# DELIVERY-5: the compact-only path. A receipt that is internally perfect, paired
# with evidence from a different verification run, used to be indistinguishable
# from an honest pair because nothing recomputed the digest it names.
render "$test_dir/fixtures/good/verification.json" "$scratch/foreign-verification.json"
seal "$scratch/foreign-verification.json" "$scratch/foreign-evidence.json"
python3 "$test_dir/drift_evidence.py" "$checker" "$scratch/foreign-evidence.json"

set +e
python3 "$checker" evaluate \
  --repo-root "$scratch" \
  --snapshot "$scratch/good-snapshot.json" \
  --verification "$scratch/foreign-verification.json" \
  --verification-evidence "$scratch/foreign-evidence.json" \
  --intent initial-pr \
  --json > "$scratch/foreign.out" 2> "$scratch/foreign.err"
foreign_rc=$?
set -e
[ "$foreign_rc" -eq 64 ] || {
  echo "compact-only path expected exit 64, got $foreign_rc" >&2; exit 1; }
grep -q 'evidence_sha256 does not name these evidence bytes' "$scratch/foreign.err"

echo "PASS ci-publish-gate evidence binding"
