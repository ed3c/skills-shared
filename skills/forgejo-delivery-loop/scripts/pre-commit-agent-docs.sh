#!/bin/sh
# pre-commit ride: the CLAUDE.md / AGENTS.md about to be committed must match
# their source in agent-docs/. Zero network, no repo state touched.
#
# Judged against the *index*, not the worktree: `git add -p` can stage an edit
# while leaving a worktree that still matches, and a worktree comparison would
# wave that through. Same rule bettor-arena's fast-quality ride already follows.
#
# Blast radius is one repo. The gate resolves its target from `git rev-parse`,
# never from sites.local.json, so a fresh clone without that (gitignored) file
# still works and one repo's drift can never block another repo's commit.
#
# Exit: 0 pass or cannot-evaluate (named on stderr, never silent) · 1 drift.
#
# The four repos carry a six-line forwarder that calls this file. Logic lives
# here once -- four copies of a checker is the shape this whole gate exists to
# remove.
set -eu

ROOT=$(git rev-parse --show-toplevel)
GATE="$(dirname "$0")/agent_docs.py"

set +e
python3 "$GATE" check --key "$(basename "$ROOT")" --target-dir "$ROOT" --staged
RC=$?
set -e

# 64 is "I could not evaluate this" -- this repo is not a manifest target, or
# the manifest itself is unreadable. Blocking an unrelated repo's commit over
# that is wrong; so is passing quietly. Say it and let the commit through.
if [ "$RC" -eq 64 ]; then
  echo "pre-commit SKIP: agent-docs gate could not evaluate $(basename "$ROOT") (see above) --" \
       "the docs were NOT checked" >&2
  exit 0
fi
exit "$RC"
