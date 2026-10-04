"""A finding whose citations exist passes; a missing run or an uncited bullet fails (DW4).

A bullet's continuation lines are the indented lines that follow it, not a new bullet; a blank or
unindented line ends it (toy-archaeology#12). `--runs` defaults to `runs/` under the working
directory, never under the script's directory.

Round 2 (PR #27 review): every Markdown list marker is a bullet (`-`, `*`, `+`, numbered `1.`/`1)`,
tab-separated, a lone marker, blockquoted), every occurrence of a protected section is checked, a
thematic break is not a bullet, and a `## ` line inside fenced code cannot end a section.

Round 2 sweep (Opus): a fence or an HTML comment never hides a bullet and only stops a `## ` line
from ending a section; every spelling of a protected heading (closing hashes, tab, case, setext)
is an occurrence; a quoted bullet takes no citation from a later quoted block; an HTML `<li>` is a
bullet; a run id next to `_` must have a record.
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

    def test_plus_bullet_is_checked(self):
        # PR #27 round 2, R1: a `+ ` bullet is as much a claim as a `- ` one.
        result = run_check_text(finding_text("+ An uncited plus bullet"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: + An uncited plus bullet", result.stdout)

    def test_numbered_dot_bullet_is_checked(self):
        result = run_check_text(finding_text("1. An uncited numbered bullet"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: 1. An uncited numbered bullet", result.stdout)

    def test_numbered_paren_bullet_is_checked(self):
        result = run_check_text(finding_text("1) An uncited numbered bullet"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: 1) An uncited numbered bullet", result.stdout)

    def test_tab_after_the_marker_is_still_a_bullet(self):
        # `-\tclaim` is a list item in Markdown; a marker followed by a tab must not escape.
        result = run_check_text(finding_text("-\tAn uncited tab-marker bullet"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: -\tAn uncited tab-marker bullet", result.stdout)

    def test_lone_marker_with_text_on_the_next_line_is_checked(self):
        # A marker alone on its line is a bullet whose text is the indented line that follows.
        result = run_check_text(finding_text("+\n  An uncited claim on the marker's own continuation"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("cites no run id", result.stdout)

    def test_thematic_break_is_not_a_bullet(self):
        # `- - -` and `* * *` are horizontal rules, not list items: flagging them would fail a good
        # finding (a round-1 false positive).
        result = run_check_text(finding_text("- Cites E900-r0001.\n- - -\n* * *"))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_blockquoted_bullet_is_checked(self):
        # `> - claim` renders as a bullet inside a quote; the quote must not hide the claim.
        result = run_check_text(finding_text("> - An uncited quoted bullet"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: > - An uncited quoted bullet", result.stdout)

    def test_blockquoted_bullet_joins_its_quoted_continuation(self):
        # The quoted bullet cites on its quoted continuation, so it passes; the numbered bullet next
        # to it cites nowhere, so it is the finding's only problem (before the fix neither was a
        # bullet and the finding wrongly passed).
        result = run_check_text(finding_text(
            "> - A quoted claim whose citation is on\n>   E900-r0001.\n1. An uncited numbered bullet"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        problems = result.stdout.splitlines()
        self.assertEqual(1, len(problems), result.stdout)
        self.assertIn("## Answer bullet cites no run id: 1. An uncited numbered bullet", problems[0])

    def test_second_answer_section_is_checked(self):
        # PR #27 round 2, R2: repeating the heading must not move a claim out of the guard.
        text = ("# F990 A fixture finding\n\n## Answer\n\n- Cites E900-r0001.\n\n"
                "## Inferences\n\n- Cites E900-r0001.\n\n## Answer\n\n- An uncited second answer\n")
        result = run_check_text(text)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: - An uncited second answer", result.stdout)

    def test_second_inferences_section_is_checked(self):
        text = ("# F990 A fixture finding\n\n## Answer\n\n- Cites E900-r0001.\n\n"
                "## Inferences\n\n- Cites E900-r0001.\n\n## Inferences\n\n- An uncited second inference\n")
        result = run_check_text(text)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Inferences bullet cites no run id: - An uncited second inference", result.stdout)

    def test_fenced_heading_cannot_end_a_section(self):
        # A `## ` line inside a fenced example must not end the Answer section: the bullet after the
        # fence still sits under Answer and is checked.
        text = ("# F990 A fixture finding\n\n## Answer\n\n- Cites E900-r0001.\n\n"
                "```text\n## Example\n```\n\n- An uncited claim after the fenced example\n\n"
                "## Inferences\n\n- Cites E900-r0001.\n")
        result = run_check_text(text)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: - An uncited claim after the fenced example",
                      result.stdout)

    def test_bullet_inside_a_fence_is_still_checked(self):
        # Round 2 review (Opus): a fence only stops a `## ` line from ending a section; it never
        # hides a bullet. Whether a line opens a fence is a guess about the renderer, so a guess
        # that is wrong must make the check stricter, never let a claim through.
        text = ("# F990 A fixture finding\n\n## Answer\n\n- Cites E900-r0001.\n\n"
                "```text\n- an uncited line inside a fence\n```\n\n"
                "## Inferences\n\n- Cites E900-r0001.\n")
        result = run_check_text(text)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: - an uncited line inside a fence", result.stdout)

    def test_backtick_line_that_is_no_fence_cannot_hide_the_rest(self):
        # A backtick info string may not hold a backtick, so this line opens no fence in Markdown:
        # the bullet after it is a rendered claim under Answer.
        text = ("## Answer\n\n- Cites E900-r0001.\n``` not `a fence`\n- An uncited claim after it\n\n"
                "## Inferences\n\n- Cites E900-r0001.\n")
        result = run_check_text(text)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: - An uncited claim after it", result.stdout)

    def test_fence_closes_only_on_its_own_kind_and_length(self):
        # `~~~` and a ```python line close no ``` fence, and ``` closes no ```` fence, so the `## `
        # lines are code and the bullet after the real closing fence is still under Answer.
        for inner in ("~~~", "```python", "```"):
            with self.subTest(inner=inner):
                fence = "````" if inner == "```" else "```"
                text = (f"## Answer\n\n- Cites E900-r0001.\n\n{fence}\n{inner}\n## Example\n{fence}\n\n"
                        "- An uncited claim after the fence\n\n## Inferences\n\n- Cites E900-r0001.\n")
                result = run_check_text(text)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn("## Answer bullet cites no run id: - An uncited claim after the fence",
                              result.stdout)

    def test_heading_inside_a_fence_still_starts_a_section(self):
        # Fail closed: a fenced `## Answer` starts a section like any other, so a claim under it is
        # checked even if the fence was a misreading of the file.
        text = ("## Answer\n\n- Cites E900-r0001.\n\n## Inferences\n\n- Cites E900-r0001.\n\n"
                "## Notes\n\n```\n## Answer\n- An uncited fenced claim\n```\n")
        result = run_check_text(text)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: - An uncited fenced claim", result.stdout)

    def test_unclosed_fence_runs_to_the_end_of_the_file(self):
        text = ("## Inferences\n\n- Cites E900-r0001.\n\n## Answer\n\n- Cites E900-r0001.\n\n"
                "```\n## Example\n\n- An uncited claim in a fence never closed\n")
        result = run_check_text(text)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: - An uncited claim in a fence never closed",
                      result.stdout)

    def test_heading_inside_an_html_comment_cannot_end_a_section(self):
        text = ("## Answer\n\n- Cites E900-r0001.\n\n<!--\n## hidden\n-->\n\n"
                "- An uncited claim after the comment\n\n## Inferences\n\n- Cites E900-r0001.\n")
        result = run_check_text(text)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: - An uncited claim after the comment",
                      result.stdout)

    def test_every_spelling_of_the_heading_is_an_occurrence(self):
        # The same `## Answer` heading written with closing hashes, a tab, other case, or as a
        # setext heading is still the Answer section, so a claim under it is checked.
        for heading in ("## Answer ##", "##\tAnswer", "## ANSWER", "Answer\n------"):
            with self.subTest(heading=heading):
                text = ("## Answer\n\n- Cites E900-r0001.\n\n## Inferences\n\n- Cites E900-r0001.\n\n"
                        f"## Notes\n\nSome notes.\n\n{heading}\n\n- An uncited claim\n")
                result = run_check_text(text)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn("## Answer bullet cites no run id: - An uncited claim", result.stdout)

    def test_quoted_bullet_does_not_take_a_citation_from_a_later_quoted_block(self):
        # `>` alone is a blank line inside the quote, `> # ...` a heading and `> > ...` a nested
        # quote: none of them continues the bullet, so the citation after them is not the bullet's.
        for tail in (">\n> E900-r0001", "> # E900-r0001", "> > E900-r0001"):
            with self.subTest(tail=tail):
                result = run_check_text(finding_text(f"> - An uncited quoted claim\n{tail}"))
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn("## Answer bullet cites no run id: > - An uncited quoted claim",
                              result.stdout)

    def test_html_list_item_is_a_bullet(self):
        result = run_check_text(finding_text("<ul>\n<li>An uncited HTML item</li>\n</ul>"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("## Answer bullet cites no run id: <li>An uncited HTML item</li>", result.stdout)

    def test_run_id_inside_emphasis_must_have_a_record(self):
        # `_E901-r0001_` renders as an emphasised run id; `_` is a word character, so a `\b` pattern
        # never saw it and a citation of a run with no record passed.
        result = run_check_text(finding_text("- Cites E900-r0001.", after="See _E901-r0001_."))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("cites missing run E901-r0001", result.stdout)

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
