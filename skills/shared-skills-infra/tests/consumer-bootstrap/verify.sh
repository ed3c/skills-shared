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
  skills/shared-skills-infra/tests/consumer-bootstrap/verify.py
python3 -m json.tool skills/shared-skills-infra/references/consumer-bootstrap-receipt.schema.json >/dev/null
python3 skills/shared-skills-infra/scripts/consumer_bootstrap.py --help >/dev/null
python3 skills/shared-skills-infra/tests/consumer-bootstrap/verify.py
