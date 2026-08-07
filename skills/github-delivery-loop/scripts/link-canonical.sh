#!/usr/bin/env bash
# Replace a repository's copy of this skill with a symlink to the canonical one,
# so there is structurally only one place the content can live.
#
# Never deletes: the old copy is MOVED to a backup directory, so the operation is
# reversible with a single `mv` back and needs no irreversible-delete approval.
# Refuses outright when the copy has diverged -- converging is the caller's
# decision, and silently discarding a diverged copy is how work disappears.
#
# Dry-run by default; --apply performs the move.
set -euo pipefail

usage() {
  echo "Usage: $0 --target ABSOLUTE_PATH [--backup-dir ABSOLUTE_PATH] [--apply]" >&2
}

target=""
backup_dir=""
apply=0

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --target) target="${2:-}"; shift 2 ;;
    --backup-dir) backup_dir="${2:-}"; shift 2 ;;
    --apply) apply=1; shift ;;
    *) usage; exit 64 ;;
  esac
done

canonical="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/.." && pwd)"
if [[ -z "${target}" || "${target}" != /* ]]; then
  echo "ERROR: --target must be an absolute path" >&2
  exit 64
fi
if [[ -n "${backup_dir}" && "${backup_dir}" != /* ]]; then
  echo "ERROR: --backup-dir must be an absolute path" >&2
  exit 64
fi
backup_dir="${backup_dir:-${TMPDIR:-/tmp}/github-delivery-loop-superseded}"

if [[ -e "${target}" ]] && [[ "$(realpath "${target}")" == "${canonical}" ]]; then
  if [[ -L "${target}" ]]; then
    echo "OK      already a symlink to canonical: ${target}"
    exit 0
  fi
  echo "ERROR: --target resolves to the canonical directory itself" >&2
  exit 64
fi
if [[ -L "${target}" ]]; then
  echo "ERROR: ${target} is a symlink to $(readlink "${target}"), not to ${canonical}" >&2
  exit 1
fi

if [[ -d "${target}" ]]; then
  if ! divergence="$(diff -r --exclude __pycache__ "${canonical}" "${target}" 2>&1)"; then
    echo "ERROR: ${target} has diverged from canonical -- refusing to move it." >&2
    echo "Converge first (rsync from canonical, or fold the differences in), then re-run." >&2
    echo "${divergence}" | head -40 >&2
    exit 1
  fi
  action="move ${target} -> ${backup_dir}/, then symlink to ${canonical}"
elif [[ -e "${target}" ]]; then
  echo "ERROR: ${target} exists and is neither a directory nor a symlink" >&2
  exit 1
else
  action="create symlink ${target} -> ${canonical}"
fi

if [[ "${apply}" -ne 1 ]]; then
  echo "DRY-RUN ${action}"
  echo "        re-run with --apply to perform it"
  exit 0
fi

if [[ -d "${target}" ]]; then
  mkdir -p "${backup_dir}"
  stamp="$(basename "${target}").$(git -C "$(dirname "${target}")" rev-parse --short HEAD 2>/dev/null || echo nogit)"
  destination="${backup_dir}/${stamp}"
  if [[ -e "${destination}" ]]; then
    echo "ERROR: backup already exists: ${destination}" >&2
    exit 1
  fi
  mv "${target}" "${destination}"
  echo "MOVED   ${target} -> ${destination}"
fi

ln -s "${canonical}" "${target}"

# Assert the shape actually changed before claiming success.
test -L "${target}" || { echo "ERROR: ${target} is not a symlink after linking" >&2; exit 1; }
test "$(readlink "${target}")" = "${canonical}" || {
  echo "ERROR: ${target} points at $(readlink "${target}")" >&2; exit 1; }
test -f "${target}/SKILL.md" || { echo "ERROR: SKILL.md unreadable through ${target}" >&2; exit 1; }

if repo_root="$(git -C "$(dirname "${target}")" rev-parse --show-toplevel 2>/dev/null)"; then
  git -C "${repo_root}" add -A "${target}"
  echo "STAGED  git add -A ${target} (in ${repo_root})"
fi
echo "LINKED  ${target} -> ${canonical}"
echo "        old copy kept at the backup path above; remove it yourself when satisfied."
