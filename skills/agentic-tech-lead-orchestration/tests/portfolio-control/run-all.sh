#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPTS="$SKILL_ROOT/scripts"
EXAMPLES="$SKILL_ROOT/references/repository-portfolio-control/examples"

python3 -m py_compile \
  "$SCRIPTS/repository_portfolio_common.py" \
  "$SCRIPTS/check_repository_portfolio_prompt_pack.py" \
  "$SCRIPTS/assert_repository_portfolio_snapshot.py" \
  "$SCRIPTS/assert_issue_pr_acceptance.py" \
  "$SCRIPTS/assert_portfolio_multigraph.py" \
  "$SCRIPTS/assert_subagent_join.py" \
  "$SCRIPTS/assert_one_shot_ci_epoch.py"

python3 "$SCRIPTS/check_repository_portfolio_prompt_pack.py"
python3 "$SCRIPTS/assert_repository_portfolio_snapshot.py" \
  --snapshot "$EXAMPLES/good-snapshot.json"
python3 "$SCRIPTS/assert_issue_pr_acceptance.py" \
  --contract "$EXAMPLES/good-acceptance.json"
python3 "$SCRIPTS/assert_portfolio_multigraph.py" \
  --graph "$EXAMPLES/good-multigraph.json"
python3 "$SCRIPTS/assert_subagent_join.py" \
  --receipt "$EXAMPLES/good-join-receipt.json" \
  --dispatches "$EXAMPLES/good-dispatches.json"
python3 "$SCRIPTS/assert_one_shot_ci_epoch.py" \
  --epoch "$EXAMPLES/good-ci-epoch.json"
python3 "$SKILL_ROOT/tests/portfolio-control/selftest.py"

echo "PORTFOLIO CONTROL FOUNDATION GREEN"
