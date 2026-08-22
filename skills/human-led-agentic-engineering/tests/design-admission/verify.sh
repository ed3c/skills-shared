#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
python3 "${root}/skills/human-led-agentic-engineering/tests/design-admission/verify.py"
