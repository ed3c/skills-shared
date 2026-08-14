#!/usr/bin/env bash
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(dirname "$(dirname "$test_dir")")"
checker="$skill_dir/scripts/ci_publish_gate.py"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

python3 "$checker" --selftest

repo="$scratch/repo"
mkdir -p "$repo"
git -C "$repo" init -q -b main
git -C "$repo" config user.email fixture@example.test
git -C "$repo" config user.name fixture
printf 'value = 1\n' > "$repo/fixture.py"
git -C "$repo" add fixture.py
git -C "$repo" commit -qm fixture
head_sha="$(git -C "$repo" rev-parse HEAD)"

cp "$skill_dir/tests/evidence-producers/fixtures/local/contract.json" "$scratch/contract.json"
python3 "$skill_dir/scripts/local_verification.py" verify \
  --repo-root "$repo" \
  --contract "$scratch/contract.json" \
  --repository-id 1326262274 \
  --receipt "$scratch/good-verification.json" \
  --evidence "$scratch/good-evidence.json"

render() {
  local source=$1 target=$2
  python3 - "$source" "$target" "$head_sha" <<'PY'
import datetime, pathlib, sys
source, target, head = sys.argv[1:]
captured = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
text = pathlib.Path(source).read_text(encoding="utf-8").replace("__HEAD__", head).replace("__CAPTURED_AT__", captured)
pathlib.Path(target).write_text(text, encoding="utf-8")
PY
}

render "$test_dir/fixtures/good/snapshot.json" "$scratch/good-snapshot.json"
render "$test_dir/fixtures/hollow/snapshot.json" "$scratch/hollow-snapshot.json"

python3 "$checker" evaluate \
  --repo-root "$repo" \
  --snapshot "$scratch/good-snapshot.json" \
  --verification "$scratch/good-verification.json" \
  --evidence "$scratch/good-evidence.json" \
  --verification-contract "$scratch/contract.json" \
  --intent initial-pr \
  --json > "$scratch/good.out"
grep -q '"decision": "ALLOW"' "$scratch/good.out"
grep -q '"reason": "allow-initial-pr"' "$scratch/good.out"

python3 - "$scratch/good-evidence.json" "$scratch/tampered-evidence.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
value["commands"][0]["exit"] = 1
pathlib.Path(sys.argv[2]).write_text(json.dumps(value), encoding="utf-8")
PY
for evidence in "$scratch/tampered-evidence.json" "$scratch/missing-evidence.json"; do
  set +e
  python3 "$checker" evaluate \
    --repo-root "$repo" \
    --snapshot "$scratch/good-snapshot.json" \
    --verification "$scratch/good-verification.json" \
    --evidence "$evidence" \
    --verification-contract "$scratch/contract.json" \
    --intent initial-pr --json > "$scratch/evidence-hollow.out" 2> "$scratch/evidence-hollow.err"
  rc=$?
  set -e
  [ "$rc" -eq 64 ] || { echo "evidence hollow expected exit 64, got $rc" >&2; exit 1; }
  grep -q '"decision": "BLOCK"' "$scratch/evidence-hollow.err"
done

python3 - "$scratch/good-snapshot.json" "$scratch/stale-snapshot.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
value["captured_at"] = "2000-01-01T00:00:00Z"
pathlib.Path(sys.argv[2]).write_text(json.dumps(value), encoding="utf-8")
PY
set +e
python3 "$checker" evaluate \
  --repo-root "$repo" \
  --snapshot "$scratch/stale-snapshot.json" \
  --verification "$scratch/good-verification.json" \
  --evidence "$scratch/good-evidence.json" \
  --verification-contract "$scratch/contract.json" \
  --intent initial-pr --json > "$scratch/stale.out" 2> "$scratch/stale.err"
rc=$?
set -e
[ "$rc" -eq 2 ] || { echo "stale snapshot expected exit 2, got $rc" >&2; exit 1; }
grep -q '"reason": "snapshot-stale"' "$scratch/stale.out"

set +e
python3 "$checker" evaluate \
  --repo-root "$repo" \
  --snapshot "$scratch/hollow-snapshot.json" \
  --verification "$scratch/good-verification.json" \
  --evidence "$scratch/good-evidence.json" \
  --verification-contract "$scratch/contract.json" \
  --intent initial-pr \
  --json > "$scratch/hollow.out" 2> "$scratch/hollow.err"
rc=$?
set -e
[ "$rc" -eq 2 ] || { echo "hollow expected exit 2, got $rc" >&2; exit 1; }
grep -q '"decision": "BLOCK"' "$scratch/hollow.out"
grep -q '"reason": "billing-circuit-open"' "$scratch/hollow.out"

# Integration arrival: consume the live producer's exact output, not a
# hand-authored gate fixture. This is the control that catches schema/API forks.
python3 - "$skill_dir/tests/evidence-producers/fixtures/good/observation.json" "$scratch/producer-observation.json" <<'PY'
import datetime, json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
value["captured_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
pathlib.Path(sys.argv[2]).write_text(json.dumps(value), encoding="utf-8")
PY
python3 "$skill_dir/scripts/github_actions_snapshot.py" replay \
  --observation "$scratch/producer-observation.json" \
  --check-name contract \
  --output "$scratch/producer-snapshot.json"
python3 "$checker" evaluate \
  --repo-root "$repo" \
  --snapshot "$scratch/producer-snapshot.json" \
  --verification "$scratch/good-verification.json" \
  --evidence "$scratch/good-evidence.json" \
  --verification-contract "$scratch/contract.json" \
  --intent batched-repair \
  --json > "$scratch/producer-gate.out"
grep -q '"decision": "ALLOW"' "$scratch/producer-gate.out"
grep -q '"reason": "allow-batched-repair"' "$scratch/producer-gate.out"

echo 'PASS[ci-publish-gate]: fixture controls plus producer-to-gate contract'
