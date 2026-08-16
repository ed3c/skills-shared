#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage: create_fresh_root_snapshot.sh SOURCE_WORKTREE DESTINATION [--patterns FILE] [--receipt FILE]
EOF
  exit 64
}
[ "$#" -ge 2 ] || usage
source_root="$1"
destination="$2"
shift 2
patterns=""
receipt=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --patterns) [ "$#" -ge 2 ] || usage; patterns="$2"; shift 2 ;;
    --receipt) [ "$#" -ge 2 ] || usage; receipt="$2"; shift 2 ;;
    *) usage ;;
  esac
done

script_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
git -C "${source_root}" rev-parse --is-inside-work-tree >/dev/null
source_root="$(git -C "${source_root}" rev-parse --show-toplevel)"
[ -z "$(git -C "${source_root}" status --porcelain --untracked-files=all)" ] || {
  echo "FRESH-ROOT ERROR: source worktree is not clean." >&2
  exit 65
}

if [ -e "${destination}" ] && [ -n "$(find "${destination}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]; then
  echo "FRESH-ROOT ERROR: destination exists and is not empty." >&2
  exit 66
fi

tracked="$(git -C "${source_root}" ls-files)"
while IFS= read -r path; do
  [ -n "${path}" ] || continue
  lower="$(printf '%s' "${path}" | tr '[:upper:]' '[:lower:]')"
  case "/${lower}/" in
    */.git/*|*/.private/*|*private-pattern*|*denylist*|*/receipts/*|*/runtime-evidence/*|*/screenshots/*|*/artifacts/*)
      echo "FRESH-ROOT ERROR: tracked private/evidence control path is forbidden." >&2
      exit 67
      ;;
  esac
  [ "${lower}" = ".env.example" ] && continue
  case "${lower}" in
    .env|.env.*|*.p8|*.mobileprovision|*.xcresult|*.log|*.jsonl)
      echo "FRESH-ROOT ERROR: tracked runtime/secret artifact is forbidden." >&2
      exit 67
      ;;
  esac
done <<< "${tracked}"

if git -C "${source_root}" ls-tree -r HEAD | awk '$1 == "160000" {found=1} END {exit !found}'; then
  echo "FRESH-ROOT ERROR: gitlinks/submodules are forbidden in the clean root." >&2
  exit 68
fi
[ ! -f "${source_root}/.gitmodules" ] || {
  echo "FRESH-ROOT ERROR: .gitmodules is forbidden in the clean root." >&2
  exit 68
}

mkdir -p "${destination}"
git -C "${source_root}" archive --format=tar HEAD | tar -xf - -C "${destination}"
git -C "${destination}" init -q
git -C "${destination}" config user.name "Fresh Root Builder"
git -C "${destination}" config user.email "fresh-root@invalid.local"
git -C "${destination}" config fetch.fsckObjects true
git -C "${destination}" config transfer.fsckObjects true
git -C "${destination}" add -A
git -C "${destination}" commit -q -m "Initialize independently authored public root"

root_count="$(git -C "${destination}" rev-list --max-parents=0 --all | wc -l | tr -d ' ')"
[ "${root_count}" = 1 ] || {
  echo "FRESH-ROOT ERROR: expected exactly one root commit." >&2
  exit 69
}
[ -z "$(git -C "${destination}" remote)" ] || {
  echo "FRESH-ROOT ERROR: fresh root unexpectedly has remotes." >&2
  exit 69
}
common_dir="$(git -C "${destination}" rev-parse --git-common-dir)"
case "${common_dir}" in /*) ;; *) common_dir="${destination}/${common_dir}" ;; esac
[ ! -s "${common_dir}/objects/info/alternates" ] || {
  echo "FRESH-ROOT ERROR: fresh root has alternates." >&2
  exit 69
}

if [ -n "${patterns}" ]; then
  audit="$(mktemp)"
  trap 'rm -f "${audit}"' EXIT
  python3 "${script_root}/audit_git_history.py" \
    --repo "${destination}" --patterns "${patterns}" --output "${audit}"
fi

head_sha="$(git -C "${destination}" rev-parse HEAD)"
tree_sha="$(git -C "${destination}" rev-parse 'HEAD^{tree}')"
if [ -n "${receipt}" ]; then
  mkdir -p "$(dirname "${receipt}")"
  python3 - "${receipt}" "${head_sha}" "${tree_sha}" "${patterns}" <<'PY'
import hashlib, json, pathlib, sys
path, head, tree, patterns = sys.argv[1:]
doc = {
    "schema": "fresh-root-receipt/v1",
    "head": head,
    "tree": tree,
    "root_count": 1,
    "remote_count": 0,
    "alternate_count": 0,
    "patterns_sha256": hashlib.sha256(pathlib.Path(patterns).read_bytes()).hexdigest() if patterns else None,
    "verdict": "PASS",
}
pathlib.Path(path).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY
fi

echo "FRESH-ROOT GREEN head=${head_sha} tree=${tree_sha}"
