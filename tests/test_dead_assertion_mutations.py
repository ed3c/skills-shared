from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "skills" / "shared-skills-infra" / "scripts" / "check_dead_assertions.py"

spec = importlib.util.spec_from_file_location("canonical_dead_assertions", CANONICAL)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


CASES = {
    "DEAD-NEGATION": (
        "rule_dead_negation",
        "#!/usr/bin/env bash\nset -eEuo pipefail\n! grep -q Traceback out.err\n",
    ),
    "DEAD-AND-CHAIN": (
        "rule_dead_and_chain",
        "#!/usr/bin/env bash\nset -eEuo pipefail\ntest ! -e one && test ! -e two\n",
    ),
    "DEAD-SWALLOW": (
        "rule_dead_swallow",
        "#!/usr/bin/env bash\nset -eEuo pipefail\ngrep -q expected out || true\n",
    ),
    "DEAD-DISCARD": (
        "rule_dead_discard",
        "#!/usr/bin/env bash\nset -eEuo pipefail\nset +e\ngrep expected out > /dev/null\nset -e\n",
    ),
}


class DeadAssertionMutationTests(unittest.TestCase):
    """Each rule must be load-bearing: replacing it with `return []` loses a required finding."""

    def test_each_rule_mutation_is_killed(self):
        for expected_rule, (function_name, fixture) in CASES.items():
            with self.subTest(rule=expected_rule):
                path = Path("tests/mutation-fixture/verify.sh")
                original = module.lint_text(fixture, path)
                self.assertIn(expected_rule, {finding.rule for finding in original})

                # Mutation equivalent to changing the rule predicate to `if False`:
                # the rule can no longer emit a finding. The fixture's expected
                # finding must disappear, proving the test contract detects the mutant.
                with mock.patch.object(module, function_name, return_value=[]):
                    mutated = module.lint_text(fixture, path)
                self.assertNotIn(expected_rule, {finding.rule for finding in mutated})

                # The mutation must be isolated: no unrelated rule is allowed to
                # masquerade as the expected finding.
                self.assertEqual(
                    {finding.rule for finding in original} - {expected_rule},
                    {finding.rule for finding in mutated},
                )


if __name__ == "__main__":
    unittest.main()
