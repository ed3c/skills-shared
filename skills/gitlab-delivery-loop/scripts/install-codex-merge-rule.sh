#!/usr/bin/env bash
# Install a narrow Codex execpolicy prefix rule that allows `glab mr merge` in
# exactly one GitLab project on exactly one host. It does not override
# PreToolUse hooks, GitLab permissions, or the human merge gate.
set -euo pipefail

usage() {
  echo "Usage: $0 --project GROUP[/SUBGROUP]/PROJECT --rules-dir ABSOLUTE_PATH" >&2
  echo "          [--host HOSTNAME] [--codex-bin COMMAND]" >&2
}

project=""
rules_dir=""
host="gitlab.com"
codex_bin="codex"

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --project)
      project="${2:-}"
      shift 2
      ;;
    --host)
      host="${2:-}"
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

# GitLab projects live under nested groups, so the path has two or more
# segments; a single-slash assumption copied from GitHub rejects valid projects.
if [[ ! "${project}" =~ ^[A-Za-z0-9_.][A-Za-z0-9_.-]*(/[A-Za-z0-9_.][A-Za-z0-9_.-]*)+$ ]]; then
  echo "ERROR: --project must be an exact GROUP[/SUBGROUP]/PROJECT path" >&2
  exit 64
fi
if [[ "${project}" == *".."* ]]; then
  echo "ERROR: --project must not contain '..'" >&2
  exit 64
fi
if [[ ! "${host}" =~ ^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?(:[0-9]{1,5})?$ ]]; then
  echo "ERROR: --host must be a hostname" >&2
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

reference="https://${host}/${project}"
slug="${host}-${project}"
slug="${slug//\//-}"
slug="${slug//./-}"
# `gitlab-merge-` prefix, never `github-merge-`: the two forges must not share a
# rule namespace, or a stale GitHub rule reads as coverage for a GitLab merge.
rule_file="${rules_dir}/gitlab-merge-${slug}.rules"
backup_file="${rule_file}.bak"

umask 077
mkdir -p "${rules_dir}"
temporary="$(mktemp "${rules_dir}/.${slug}.XXXXXX")"
trap 'rm -f "${temporary}"' EXIT

printf '%s\n' \
  'prefix_rule(' \
  "    pattern = [\"glab\", \"mr\", \"merge\", \"-R\", \"${reference}\"]," \
  '    decision = "allow",' \
  "    justification = \"Allow Codex to merge MRs only in ${reference}\"," \
  '    match = [' \
  "        \"glab mr merge -R ${reference} 1 --squash --sha \
0000000000000000000000000000000000000000 --auto-merge=false --yes\"," \
  '    ],' \
  '    not_match = [' \
  "        \"glab mr merge 1 -R ${reference} --squash\"," \
  "        \"glab mr merge -R https://${host}/other/project 1 --squash\"," \
  "        \"glab repo delete ${project}\"," \
  '    ],' \
  ')' > "${temporary}"

chmod 600 "${temporary}"
if [[ -f "${rule_file}" ]]; then
  cp -p "${rule_file}" "${backup_file}"
fi
mv "${temporary}" "${rule_file}"
trap - EXIT

# Smoke-test the *real* land shape, not a shorter convenience form: the
# GitHub-side lesson was that a rule verified against `... 1 --merge` says
# nothing about the argv the lander actually builds.
"${codex_bin}" execpolicy check --pretty \
  --rules "${rule_file}" \
  -- glab mr merge -R "${reference}" 1 --squash \
     --sha 0000000000000000000000000000000000000000 --auto-merge=false --yes

echo "Installed: ${rule_file}"
echo "Restart Codex completely to load the rule."
echo "This rule does not override PreToolUse hooks, GitLab permissions, or human gates."
echo "It also cannot constrain trailing flags: --auto-merge lives after the MR id and"
echo "is outside any prefix contract. That one is guarded in merge_command() instead."
