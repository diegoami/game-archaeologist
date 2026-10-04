"""A finding whose citations exist passes; a missing run or an uncited bullet fails (DW4).

A bullet's continuation lines are the indented lines that follow it, not a new bullet; a blank or
unindented line ends it (toy-archaeology#12). `--runs` defaults to `runs/` under the working
directory, never under the script's directory.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "tools" / "fixtures"


def run_check(finding: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "tools/check_citations.py",
         str(FIXTURES / "citations" / finding), "--runs", str(FIXTURES / "runs")],
        cwd=REPO_ROOT, capture_output=True, text=True)


def finding_text(answer: str, inferences: str | None = "- Rests on E900-r0001.",
                 after: str = "") -> str:
    """A minimal finding with the given `## Answer` and `## Inferences` bodies; `None` drops the
    Inferences section. `after` is the body of a later section."""
    parts = ["# F990 A fixture finding", "", "## Answer", "", answer, ""]
    if inferences is not None:
        parts += ["## Inferences", "", inferences, ""]
    parts += ["## Alternatives considered", "", after, ""]
    return "\n".join(parts)


def run_check_text(text: str) -> subprocess.CompletedProcess:
    """Check a finding written from `text` into a temporary file."""
    with tempfile.TemporaryDirectory() as tmp:
        finding = Path(tmp) / "finding.md"
        finding.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, "tools/check_citations.py", str(finding),
             "--runs", str(FIXTURES / "runs")],
            cwd=REPO_ROOT, capture_output=True, text=True)


class CheckCitationsTest(unittest.TestCase):
    def test_missing_run_id_exits_1(self):
        result = run_check("finding-missing.md")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("E900-r9999", result.stdout)

    def test_all_citations_exist_exits_0(self):
        result = run_check("finding-good.md")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_citation_on_a_bullet_second_line_exits_0(self):
        # toy-archaeology#12: the only citation sits on a bullet's continuation line.
        result = run_check("finding-wrapped.md")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_wrapped_bullet_without_any_citation_exits_1(self):
        result = run_check("finding-wrapped-empty.md")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("cites no run id", result.stdout)

    def test_unindented_line_after_a_bullet_does_not_continue_it(self):
        # The run id sits on the next line, but that line is not indented: the bullet cites nothing.
        result = run_check_text(finding_text("- An answer bullet without a citation\nE900-r0001 here."))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id", result.stdout)

    def test_whitespace_only_line_ends_a_bullet(self):
        # A line of spaces ends the bullet; the indented line after it is not part of the bullet.
        result = run_check_text(finding_text("- An answer bullet without a citation\n   \n  E900-r0001"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id", result.stdout)

    def test_tab_indented_continuation_belongs_to_the_bullet(self):
        result = run_check_text(finding_text("- An answer bullet whose citation is on\n\tE900-r0001."))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_new_bullet_is_not_a_continuation(self):
        # An indented `- ` line is a new bullet, so it does not lend its citation to the one above.
        result = run_check_text(finding_text("- An uncited answer bullet\n  - E900-r0001 nested"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: - An uncited answer bullet", result.stdout)

    def test_star_bullet_is_checked(self):
        result = run_check_text(finding_text("* An uncited star bullet"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: * An uncited star bullet", result.stdout)

    def test_uncited_inferences_bullet_exits_1(self):
        result = run_check_text(finding_text("- Cites E900-r0001.", "- An uncited inference"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Inferences bullet cites no run id", result.stdout)

    def test_bullets_after_the_checked_sections_need_no_citation(self):
        result = run_check_text(finding_text("- Cites E900-r0001.", after="- An uncited alternative"))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_missing_section_exits_1(self):
        result = run_check_text(finding_text("- Cites E900-r0001.", inferences=None))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("missing section '## Inferences'", result.stdout)

    def test_bullet_ending_its_section_without_a_blank_line_is_checked(self):
        result = run_check_text("## Answer\n- An uncited last bullet\n## Inferences\n- E900-r0001")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: - An uncited last bullet", result.stdout)

    def test_runs_default_to_the_working_directory_runs(self):
        # Without --runs a citation must resolve under this working directory's runs/, which holds
        # no E900 record.
        result = subprocess.run(
            [sys.executable, "tools/check_citations.py", str(FIXTURES / "citations" / "finding-good.md")],
            cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(f"cites missing run E900-r0001 (no {REPO_ROOT / 'runs' / 'E900' / 'E900-r0001.json'})",
                      result.stdout)

    def test_missing_finding_file_exits_1(self):
        result = run_check("no-such-finding.md")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("no-such-finding.md: no such file", result.stdout)


if __name__ == "__main__":
    unittest.main()
