#!/usr/bin/env bash
set -eEuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"
python3 -m py_compile \
  skills/shared-skills-infra/scripts/consumer_bootstrap.py \
  skills/shared-skills-infra/scripts/consumer_bootstrap_common.py \
  skills/shared-skills-infra/scripts/consumer_bootstrap_receipt.py \
  skills/shared-skills-infra/scripts/consumer_bootstrap_routes.py \
  skills/shared-skills-infra/tests/consumer-bootstrap/support.py \
  skills/shared-skills-infra/tests/consumer-bootstrap/verify.py \
  skills/shared-skills-infra/tests/consumer-bootstrap/verify_real_attach.py
python3 -m json.tool skills/shared-skills-infra/references/consumer-bootstrap-receipt.schema.json >/dev/null
python3 skills/shared-skills-infra/scripts/consumer_bootstrap.py --help >/dev/null
python3 skills/shared-skills-infra/tests/consumer-bootstrap/verify.py
# SSM-3: fake_attach above proves the orchestration; this proves the real
# repository_control_plane.attach() -> shared_skills.py sync seam it stands
# in for actually agrees with what consumer_bootstrap_receipt expects.
python3 skills/shared-skills-infra/tests/consumer-bootstrap/verify_real_attach.py

# #559: the github-portfolio-control profile is a second, profile-namespaced
# bootstrap sharing this module family's primitives -- unconditional, no
# existence guard, so it cannot silently fall out of this already-CI-wired step.
bash "$(dirname "${BASH_SOURCE[0]}")/../consumer-bootstrap-ghpc/verify.sh"

# #527: the dual-track-code-review-loop profile is the third profile-namespaced
# bootstrap on the same primitives -- chained unconditionally for the same
# reason: the hosted workflow enumerates sub-suites by name.
bash "$(dirname "${BASH_SOURCE[0]}")/../consumer-bootstrap-dtcr/verify.sh"
