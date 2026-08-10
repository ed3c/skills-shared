#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 (--repo OWNER/REPOSITORY | --owner LOGIN --gate ABSOLUTE_PATH) --rules-dir ABSOLUTE_PATH [--codex-bin COMMAND]" >&2
}

repository=""
owner_auto=""
gate=""
rules_dir=""
codex_bin="codex"

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --repo)
      repository="${2:-}"
      shift 2
      ;;
    --owner)
      owner_auto="${2:-}"
      shift 2
      ;;
    --gate)
      gate="${2:-}"
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

if [[ -n "${repository}" && -n "${owner_auto}" ]] || [[ -z "${repository}" && -z "${owner_auto}" ]]; then
  echo "ERROR: choose exactly one of --repo or --owner" >&2
  exit 64
fi
if [[ -n "${repository}" ]]; then
  owner="${repository%%/*}"
  name="${repository#*/}"
  if [[ ! "${repository}" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] \
    || [[ "${owner}" == "." || "${owner}" == ".." ]] \
    || [[ "${name}" == "." || "${name}" == ".." ]]; then
    echo "ERROR: --repo must be an exact OWNER/REPOSITORY name" >&2
    exit 64
  fi
else
  if [[ ! "${owner_auto}" =~ ^[A-Za-z0-9_.-]+$ ]] || [[ "${gate}" != /* ]] || [[ ! -f "${gate}" ]]; then
    echo "ERROR: --owner needs a valid login and --gate must be an existing absolute file" >&2
    exit 64
  fi
fi
if [[ -z "${rules_dir}" || "${rules_dir}" != /* ]]; then
  echo "ERROR: --rules-dir must be an absolute path" >&2
  exit 64
fi
if [[ -z "${codex_bin}" ]]; then
  echo "ERROR: --codex-bin must not be empty" >&2
  exit 64
fi

if [[ -n "${repository}" ]]; then
  slug="${repository//\//-}"
  rule_file="${rules_dir}/github-merge-${slug}.rules"
else
  slug="owner-${owner_auto}"
  rule_file="${rules_dir}/github-merge-${slug}.rules"
fi
backup_file="${rule_file}.bak"

umask 077
mkdir -p "${rules_dir}"
temporary="$(mktemp "${rules_dir}/.${slug}.XXXXXX")"
trap 'rm -f "${temporary}"' EXIT

if [[ -n "${repository}" ]]; then
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
else
  printf '%s\n' \
    'prefix_rule(' \
    "    pattern = [\"python3\", \"${gate}\", \"land\", \"--repo\"]," \
    '    decision = "allow",' \
    "    justification = \"Allow the identity-gated merge wrapper; runtime owner must be ${owner_auto}\"," \
    '    match = [' \
    "        \"python3 ${gate} land --repo ${owner_auto}/future-repository\"," \
    '    ],' \
    '    not_match = [' \
    "        \"python3 ${gate} preflight --repo ${owner_auto}/future-repository\"," \
    '        "gh api graphql",' \
    '    ],' \
    ')' > "${temporary}"
fi

chmod 600 "${temporary}"
if [[ -f "${rule_file}" ]]; then
  cp -p "${rule_file}" "${backup_file}"
fi
mv "${temporary}" "${rule_file}"
trap - EXIT

if [[ -n "${repository}" ]]; then
  probe=(gh pr merge --repo "${repository}" 1 --merge)
else
  probe=(python3 "${gate}" land --repo "${owner_auto}/future-repository")
fi
"${codex_bin}" execpolicy check --pretty --rules "${rule_file}" -- "${probe[@]}"

echo "Installed: ${rule_file}"
echo "Restart Codex completely to load the rule."
echo "This rule does not override PreToolUse hooks, runtime identity checks, or GitHub branch rules."
