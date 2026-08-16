#!/usr/bin/env bash
set -euo pipefail

[ "$#" -eq 2 ] || {
  echo "usage: assert_no_shared_lineage.sh CLEAN_REPO PRIVATE_REPO" >&2
  exit 64
}
clean="$(git -C "$1" rev-parse --show-toplevel)"
private="$(git -C "$2" rev-parse --show-toplevel)"

resolve_common() {
  local repo="$1" value
  value="$(git -C "${repo}" rev-parse --git-common-dir)"
  case "${value}" in
    /*) printf '%s\n' "$(cd "${value}" && pwd -P)" ;;
    *) printf '%s\n' "$(cd "${repo}/${value}" && pwd -P)" ;;
  esac
}

for repo in "${clean}" "${private}"; do
  git -C "${repo}" rev-parse --is-inside-work-tree >/dev/null
  [ -z "${GIT_ALTERNATE_OBJECT_DIRECTORIES:-}" ] || {
    echo "LINEAGE ERROR: alternate object environment is active." >&2
    exit 65
  }
  common="$(resolve_common "${repo}")"
  [ ! -s "${common}/objects/info/alternates" ] || {
    echo "LINEAGE ERROR: alternate object file is active." >&2
    exit 65
  }
done

clean_common="$(resolve_common "${clean}")"
private_common="$(resolve_common "${private}")"
[ "${clean_common}" != "${private_common}" ] || {
  echo "LINEAGE RED: repositories share the same Git common directory." >&2
  exit 2
}

root_count="$(git -C "${clean}" rev-list --max-parents=0 --all | wc -l | tr -d ' ')"
[ "${root_count}" = 1 ] || {
  echo "LINEAGE RED: clean repository does not have exactly one root." >&2
  exit 2
}

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT
git init -q --bare "${tmp}/graph.git"
git -C "${tmp}/graph.git" fetch -q --no-tags "${clean}" HEAD:refs/heads/clean
git -C "${tmp}/graph.git" fetch -q --no-tags "${private}" '+refs/*:refs/private/*'
clean_head="$(git -C "${tmp}/graph.git" rev-parse refs/heads/clean)"
while IFS= read -r private_tip; do
  [ -n "${private_tip}" ] || continue
  if git -C "${tmp}/graph.git" merge-base "${clean_head}" "${private_tip}" >/dev/null 2>&1; then
    echo "LINEAGE RED: a common merge base exists." >&2
    exit 2
  fi
done < <(git -C "${tmp}/graph.git" for-each-ref --format='%(objectname)' refs/private)

git -C "${clean}" rev-list --objects --all | awk '{print $1}' | sort -u > "${tmp}/clean.objects"
git -C "${private}" rev-list --objects --all | awk '{print $1}' | sort -u > "${tmp}/private.objects"
comm -12 "${tmp}/clean.objects" "${tmp}/private.objects" > "${tmp}/shared.objects"
grep -v '^e69de29bb2d1d6434b8b29ae775ad8c2e48c5391$' "${tmp}/shared.objects" > "${tmp}/shared.nonempty" || true
if [ -s "${tmp}/shared.nonempty" ]; then
  count="$(wc -l < "${tmp}/shared.nonempty" | tr -d ' ')"
  echo "LINEAGE RED: shared non-empty Git objects detected count=${count}." >&2
  exit 2
fi

echo "LINEAGE GREEN no-merge-base no-alternates no-shared-nonempty-objects"
