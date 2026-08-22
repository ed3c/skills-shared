#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
python3 "${root}/skills/shared-skills-infra/tests/consumer-bootstrap-cadg/verify.py"
