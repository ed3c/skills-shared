#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --repo OWNER/REPOSITORY --rules-dir ABSOLUTE_PATH [--codex-bin COMMAND]" >&2
}

repository=""
rules_dir=""
codex_bin="codex"

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --repo)
      repository="${2:-}"
      shift 2
      ;;
    --rules-dir)
      rules_dir="${2:-}"
      shift 2
      ;;
    --codex-bin)
      codex_bin="${2:-}"
      shift 2
      ;;
    *)
      usage
      exit 64
      ;;
  esac
done

owner="${repository%%/*}"
name="${repository#*/}"
if [[ ! "${repository}" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] \
  || [[ "${owner}" == "." || "${owner}" == ".." ]] \
  || [[ "${name}" == "." || "${name}" == ".." ]]; then
  echo "ERROR: --repo must be an exact OWNER/REPOSITORY name" >&2
  exit 64
fi
if [[ -z "${rules_dir}" || "${rules_dir}" != /* ]]; then
  echo "ERROR: --rules-dir must be an absolute path" >&2
  exit 64
fi
if [[ -z "${codex_bin}" ]]; then
  echo "ERROR: --codex-bin must not be empty" >&2
  exit 64
fi

slug="${repository//\//-}"
rule_file="${rules_dir}/github-merge-${slug}.rules"
backup_file="${rule_file}.bak"

umask 077
mkdir -p "${rules_dir}"
temporary="$(mktemp "${rules_dir}/.${slug}.XXXXXX")"
trap 'rm -f "${temporary}"' EXIT

printf '%s\n' \
  'prefix_rule(' \
  "    pattern = [\"gh\", \"pr\", \"merge\", \"--repo\", \"${repository}\"]," \
  '    decision = "allow",' \
  "    justification = \"Allow Codex to merge PRs only in ${repository}\"," \
  '    match = [' \
  "        \"gh pr merge --repo ${repository} 1 --merge\"," \
  '    ],' \
  '    not_match = [' \
  "        \"gh pr merge 1 --repo ${repository} --merge\"," \
  '        "gh repo delete owner/repository",' \
  '    ],' \
  ')' > "${temporary}"

chmod 600 "${temporary}"
if [[ -f "${rule_file}" ]]; then
  cp -p "${rule_file}" "${backup_file}"
fi
mv "${temporary}" "${rule_file}"
trap - EXIT

"${codex_bin}" execpolicy check --pretty \
  --rules "${rule_file}" \
  -- gh pr merge --repo "${repository}" 1 --merge

echo "Installed: ${rule_file}"
echo "Restart Codex completely to load the rule."
echo "This rule does not override repository PreToolUse hooks or human merge gates."
