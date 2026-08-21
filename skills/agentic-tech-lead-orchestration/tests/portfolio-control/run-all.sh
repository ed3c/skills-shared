#!/bin/sh
# #566: repository-portfolio control C1 core (snapshot/acceptance/multigraph/dispatch).
# Composes ghpc (skills/github-portfolio-control) for one-shot-CI and subagent-join;
# does not restate either. See ../../references/REPOSITORY_PORTFOLIO_CONTROL.md.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
python3 "$ROOT/tests/portfolio-control/selftest.py"
