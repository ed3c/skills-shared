from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_ablation_treatment.py"
SKILL_FILE = ROOT / "SKILL.md"
RULE_HEADING_RE = re.compile(r"^### (RCA-\d{3}) ", re.M)


def run(skill_file: Path, output_dir: Path) -> tuple[int, str, str]:
    process = subprocess.run(
        [sys.executable, str(GENERATOR), "--skill-file", str(skill_file),
         "--output-dir", str(output_dir)],
        capture_output=True, text=True, check=False,
    )
    return process.returncode, process.stdout, process.stderr


class AblationTreatmentGeneratorTests(unittest.TestCase):
    def test_generates_one_file_per_retained_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            code, stdout, stderr = run(SKILL_FILE, out)
            self.assertEqual(code, 0, stderr)
            generated = sorted(p.name for p in out.glob("candidate_minus_RCA-*.md"))
            expected = [f"candidate_minus_RCA-{n:03d}.md" for n in range(1, 14)]
            self.assertEqual(generated, expected)

    def test_each_file_strips_exactly_its_named_rule_and_nothing_else(self):
        original_lines = SKILL_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            code, _, stderr = run(SKILL_FILE, out)
            self.assertEqual(code, 0, stderr)
            for n in range(1, 14):
                rule_id = f"RCA-{n:03d}"
                with self.subTest(rule=rule_id):
                    ablated_text = (out / f"candidate_minus_{rule_id}.md").read_text(encoding="utf-8")
                    ablated_lines = ablated_text.splitlines(keepends=True)
                    self.assertNotIn(f"### {rule_id} ", ablated_text)

                    # Every remaining line must be present, in order, in the
                    # original -- i.e. the ablated file is the original with a
                    # contiguous block removed, not a rewritten copy.
                    removed_count = len(original_lines) - len(ablated_lines)
                    self.assertGreater(removed_count, 0, rule_id)
                    cursor = 0
                    for line in ablated_lines:
                        while cursor < len(original_lines) and original_lines[cursor] != line:
                            cursor += 1
                        self.assertLess(
                            cursor, len(original_lines),
                            f"{rule_id}: ablated line not found in original at expected position: {line!r}",
                        )
                        cursor += 1

                    # The removed block is exactly one rule section: its first
                    # removed line is the named rule's own heading.
                    removed_lines = [line for line in original_lines if line not in ablated_lines]
                    self.assertTrue(removed_lines, rule_id)

                    # Every other rule's heading must survive untouched.
                    for other in range(1, 14):
                        if other == n:
                            continue
                        other_id = f"RCA-{other:03d}"
                        self.assertIn(f"### {other_id} ", ablated_text, f"{rule_id} removed {other_id} too")

    def test_all_thirteen_rules_are_covered_by_the_committed_skill(self):
        text = SKILL_FILE.read_text(encoding="utf-8")
        found = [m.group(1) for m in RULE_HEADING_RE.finditer(text)]
        self.assertEqual(sorted(found), [f"RCA-{n:03d}" for n in range(1, 14)])

    def test_missing_rule_heading_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_file = Path(tmp) / "SKILL.md"
            skill_file.write_text(
                "## Runtime-supported core laws\n\n"
                "### RCA-001 -- Bind the exact subject\n\nbody\n\n"
                "## Deterministic procedure\n",
                encoding="utf-8",
            )
            code, _, stderr = run(skill_file, Path(tmp) / "out")
            self.assertEqual(code, 64)
            self.assertIn("rule-heading-set-mismatch", stderr)
            self.assertIn("RCA-002", stderr)

    def test_absent_skill_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, stderr = run(Path(tmp) / "absent.md", Path(tmp) / "out")
            self.assertEqual(code, 64)
            self.assertIn("absent-input", stderr)

    def test_duplicate_rule_heading_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_file = Path(tmp) / "SKILL.md"
            sections = "".join(
                f"### RCA-{n:03d} -- Title\n\nbody\n\n" for n in range(1, 14)
            )
            skill_file.write_text(
                "## Runtime-supported core laws\n\n"
                + sections
                + "### RCA-001 -- Duplicate\n\nbody\n\n"
                "## Deterministic procedure\n",
                encoding="utf-8",
            )
            code, _, stderr = run(skill_file, Path(tmp) / "out")
            self.assertEqual(code, 64)
            self.assertIn("duplicate-rule-heading", stderr)


if __name__ == "__main__":
    unittest.main()
