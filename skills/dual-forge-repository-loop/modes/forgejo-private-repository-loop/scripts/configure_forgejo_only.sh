#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: configure_forgejo_only.sh REPO_ROOT FORGEJO_URL [REMOTE_NAME]" >&2
  exit 64
}
[ "$#" -ge 2 ] && [ "$#" -le 3 ] || usage

repo_root="$1"
forgejo_url="$2"
remote_name="${3:-forgejo}"
case "${remote_name}" in
  ''|*[!A-Za-z0-9._-]*) echo "ERROR: unsafe remote name." >&2; exit 64 ;;
esac

script_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readarray -t url_fields < <(PYTHONPATH="${script_root}/scripts" python3 - "${forgejo_url}" <<'PY'
import sys
from url_policy import is_github, parse
item = parse(sys.argv[1])
print(item.host)
print("1" if item.has_http_credentials else "0")
print("1" if is_github(item.host) else "0")
print("1" if item.relative else "0")
PY
)
forgejo_host="${url_fields[0]:-}"
has_credentials="${url_fields[1]:-1}"
is_github="${url_fields[2]:-1}"
is_relative="${url_fields[3]:-1}"
[ -n "${forgejo_host}" ] && [ "${has_credentials}" = 0 ] && [ "${is_github}" = 0 ] && [ "${is_relative}" = 0 ] || {
  echo "ERROR: Forgejo URL must be an absolute credential-free non-GitHub remote." >&2
  exit 65
}

git -C "${repo_root}" rev-parse --is-inside-work-tree >/dev/null
repo_root="$(git -C "${repo_root}" rev-parse --show-toplevel)"
common_dir="$(git -C "${repo_root}" rev-parse --git-common-dir)"
case "${common_dir}" in
  /*) ;;
  *) common_dir="${repo_root}/${common_dir}" ;;
esac

if [ -n "${GIT_ALTERNATE_OBJECT_DIRECTORIES:-}" ] || [ -s "${common_dir}/objects/info/alternates" ]; then
  echo "ERROR: alternate object stores must be removed before Forgejo-only admission." >&2
  exit 66
fi

backup="${common_dir}/config.before-forgejo-only.$(date -u +%Y%m%dT%H%M%SZ)"
cp "${common_dir}/config" "${backup}"

while IFS= read -r remote; do
  [ -n "${remote}" ] || continue
  git -C "${repo_root}" remote remove "${remote}"
done < <(git -C "${repo_root}" remote)

git -C "${repo_root}" remote add "${remote_name}" "${forgejo_url}"
git -C "${repo_root}" remote set-url --push "${remote_name}" "${forgejo_url}"

git -C "${repo_root}" config --local repository.classification LOCAL_ONLY
git -C "${repo_root}" config --local repository.localOnlyVersion 1
git -C "${repo_root}" config --local repository.localOnlyRemote "${remote_name}"
git -C "${repo_root}" config --local repository.localOnlyURL "${forgejo_url}"
git -C "${repo_root}" config --local repository.localOnlyHost "${forgejo_host}"
git -C "${repo_root}" config --local remote.pushDefault "${remote_name}"
git -C "${repo_root}" config --local push.default current
git -C "${repo_root}" config --local push.followTags false
git -C "${repo_root}" config --local push.autoSetupRemote true
git -C "${repo_root}" config --local fetch.fsckObjects true
git -C "${repo_root}" config --local transfer.fsckObjects true
git -C "${repo_root}" config --local receive.fsckObjects true

while IFS= read -r branch; do
  [ -n "${branch}" ] || continue
  git -C "${repo_root}" config --local "branch.${branch}.pushRemote" "${remote_name}"
done < <(git -C "${repo_root}" for-each-ref --format='%(refname:short)' refs/heads)

hooks_setting="$(git -C "${repo_root}" config --local --get core.hooksPath || true)"
if [ -n "${hooks_setting}" ]; then
  case "${hooks_setting}" in
    /*) hooks_dir="${hooks_setting}" ;;
    *) hooks_dir="${repo_root}/${hooks_setting}" ;;
  esac
else
  hooks_dir="$(git -C "${repo_root}" rev-parse --git-path hooks)"
  case "${hooks_dir}" in
    /*) ;;
    *) hooks_dir="${repo_root}/${hooks_dir}" ;;
  esac
fi
mkdir -p "${hooks_dir}"
install -m 0755 "${script_root}/hooks/pre-push.local-only-guard" \
  "${hooks_dir}/pre-push.local-only-guard"
# The installed hook imports the URL parser from the mode directory. Record a
# stable absolute local path, but never commit it.
git -C "${repo_root}" config --local repository.localOnlyModeRoot "${script_root}"

if [ -e "${hooks_dir}/pre-push" ] && ! grep -q 'BEGIN PRIVATE-LINEAGE DISPATCHER' "${hooks_dir}/pre-push" 2>/dev/null; then
  [ ! -e "${hooks_dir}/pre-push.user" ] || {
    echo "ERROR: pre-push and pre-push.user both exist; refusing overwrite." >&2
    exit 67
  }
  mv "${hooks_dir}/pre-push" "${hooks_dir}/pre-push.user"
fi

cat > "${hooks_dir}/pre-push" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
# BEGIN PRIVATE-LINEAGE DISPATCHER
hook_dir="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp "${TMPDIR:-/tmp}/tmp.XXXXXXXX")"
trap 'rm -f "${tmp}"' EXIT
cat > "${tmp}"
if [ -x "${hook_dir}/pre-push.user" ]; then
  "${hook_dir}/pre-push.user" "$@" < "${tmp}"
fi
mode_root="$(git config --local --get repository.localOnlyModeRoot || true)"
PYTHONPATH="${mode_root}/scripts" "${hook_dir}/pre-push.local-only-guard" "$@" < "${tmp}"
# END PRIVATE-LINEAGE DISPATCHER
EOF
chmod 0755 "${hooks_dir}/pre-push"

guard_sha="$(python3 - "${hooks_dir}/pre-push.local-only-guard" <<'PY'
import hashlib, pathlib, sys
print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())
PY
)"
git -C "${repo_root}" config --local repository.localOnlyGuardSha256 "${guard_sha}"

cat > "${common_dir}/LOCAL_ONLY_CLASSIFICATION" <<EOF
classification=LOCAL_ONLY
version=1
admitted_remote=${remote_name}
admitted_host=${forgejo_host}
configured_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
config_backup_sha256=$(python3 - "${backup}" <<'PY'
import hashlib, pathlib, sys
print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())
PY
)
EOF
chmod 0600 "${common_dir}/LOCAL_ONLY_CLASSIFICATION"

echo "FORGEJO-ONLY CONFIGURED remote=${remote_name} host=${forgejo_host}"
