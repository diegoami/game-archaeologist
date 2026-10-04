"""A finding whose citations exist passes; a missing run or an uncited claim fails (DW4).

A bullet's continuation lines are the indented lines that follow it, not a new bullet; a blank or
unindented line ends it (toy-archaeology#12). `--runs` defaults to `runs/` under the working
directory, never under the script's directory. Every Markdown list marker is a bullet (`-`, `*`,
`+`, numbered `1.`/`1)`, tab-separated, a lone marker), and a run id next to `_` must have a record.

U25 (the owner, 2026-10-04): `## Answer` and `## Inferences` hold only list items with their
continuation lines, `###` sub-headings, table rows whose data rows each cite a run, and blank lines.
Every other line there is a named error, which replaces round 2's parsing of fences, HTML comments,
quoted bullets, `<li>` items and heading spellings (`U25Test`).
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


ALLOWED = """- A dash bullet, E900-r0001.
* A star bullet, E900-r0001.
+ A plus bullet whose citation is on
  its continuation line, E900-r0001.
1. A numbered bullet, E900-r0001.
2) Another numbered bullet, E900-r0001.
  - A nested bullet, E900-r0001.
-
  A lone marker's text, E900-r0001.

### A sub-heading needs no citation

| Header | needs no run id |
| :--- | ---: |
| A data row | E900-r0001 |
| Another data row, citing | `E900-r0001` |
"""


def unsupported_at(result: subprocess.CompletedProcess, number: int, line: str) -> bool:
    """Whether `result` names `line`, at line `number` of the finding, as unsupported."""
    return f":{number}: unsupported in a protected section: {line}\n" in result.stdout + "\n"


class U25Test(unittest.TestCase):
    """The owner's decision U25: a protected section holds only the allowed forms; every other line
    there is a named error, so nothing written in an unparsed construct can hide an uncited claim."""

    def test_each_allowed_form_passes(self):
        result = run_check_text(finding_text(ALLOWED, ALLOWED))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("ok: citations in", result.stdout)

    def test_each_forbidden_form_is_a_named_error(self):
        # Each body goes under `## Answer`; the line named is the first the rule refuses. Sol's
        # round-2 R1 reproductions come first: HTML list items on one line, and inside `<ul>`.
        forms = [
            ("<li>recorded E900-r0001</li><li>uncited claim</li>", 0),
            ("<ul><li>uncited claim</li></ul>", 0),
            ("<ul>\n<li>uncited claim</li>\n</ul>", 0),
            ("- Cites E900-r0001.\n<!-- a comment -->", 1),
            ("- Cites E900-r0001 <span>and an inline tag</span>.", 0),
            ("- Cites E900-r0001.\n\n```text\n- uncited claim in a fence\n```", 2),
            ("~~~\n- uncited claim in a fence\n~~~", 0),
            ("> - An uncited quoted claim", 0),
            ("> A quoted paragraph citing E900-r0001", 0),
            ("- Cites E900-r0001.\n#### A deeper heading", 1),
            ("- Cites E900-r0001.\n##\tA level-2 heading that does not end the section", 1),
            ("- Cites E900-r0001.\n # A level-1 heading", 1),
            ("- Cites E900-r0001.\n---", 1),
            ("- Cites E900-r0001.\n===", 1),
            ("- Cites E900-r0001.\n  ---", 1),
            ("- Cites E900-r0001.\n* * *", 1),
            ("A paragraph line citing E900-r0001.", 0),
            ("- Cites E900-r0001.\nE900-r0001, an unindented line after a bullet", 1),
            ("- Cites E900-r0001.\n\n    an indented code line E900-r0001", 2),
            ("- > A quote opened inside a bullet, E900-r0001", 0),
            ("- ## A heading opened inside a bullet, E900-r0001", 0),
            ("- ```fence opened inside a bullet, E900-r0001", 0),
            ("- Cites E900-r0001,\n  > and a quote on its continuation", 1),
            ("- Cites E900-r0001,\n  ```", 1),
            ("[ref]: https://example.org E900-r0001", 0),
        ]
        for body, offending in forms:
            with self.subTest(body=body):
                result = run_check_text(finding_text(body))
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                line = body.split("\n")[offending]
                self.assertTrue(unsupported_at(result, 5 + offending, line), result.stdout)

    def test_quoted_heading_and_quoted_claim_are_named_errors(self):
        # Sol's round-2 R2: a quoted `## Answer` with an uncited quoted claim, after the real
        # sections, passed. The quoted heading is another spelling of the section and is refused.
        text = ("## Answer\n\n- Cites E900-r0001.\n\n## Inferences\n\n- Cites E900-r0001.\n\n"
                "## Other\n\n> ## Answer\n> - uncited claim\n")
        result = run_check_text(text)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertTrue(unsupported_at(result, 11, "> ## Answer"), result.stdout)

    def test_every_other_spelling_of_a_section_heading_is_a_named_error(self):
        spellings = ["## ANSWER", "## answer", "## Answer ##", "##\tAnswer", "## Answer ", " ## Answer",
                     "# Answer", "### Inferences", "> > ## Inferences", "<h2>Answer</h2>"]
        for heading in spellings:
            with self.subTest(heading=heading):
                text = ("## Answer\n\n- Cites E900-r0001.\n\n## Inferences\n\n- Cites E900-r0001.\n\n"
                        f"## Notes\n\n{heading}\n\n- An uncited claim\n")
                result = run_check_text(text)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertTrue(unsupported_at(result, 11, heading), result.stdout)

    def test_setext_spelling_of_a_section_heading_is_a_named_error(self):
        text = ("## Answer\n\n- Cites E900-r0001.\n\n## Inferences\n\n- Cites E900-r0001.\n\n"
                "## Notes\n\nInferences\n----------\n\n- An uncited claim\n")
        result = run_check_text(text)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertTrue(unsupported_at(result, 11, "Inferences"), result.stdout)

    def test_a_repeated_section_is_a_named_error(self):
        # PR #27 round 2, R2 of round 1: repeating the heading must not move a claim out of the
        # guard. The repeat is refused, and its bullets are still checked.
        for heading in ("## Answer", "## Inferences"):
            with self.subTest(heading=heading):
                text = ("# F990 A fixture finding\n\n## Answer\n\n- Cites E900-r0001.\n\n"
                        f"## Inferences\n\n- Cites E900-r0001.\n\n{heading}\n\n- An uncited second claim\n")
                result = run_check_text(text)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertTrue(unsupported_at(result, 11, heading), result.stdout)
                self.assertIn(f"{heading} bullet cites no run id: - An uncited second claim", result.stdout)

    def test_table_data_row_without_a_run_id_fails(self):
        body = "| Lead | Outcome |\n| --- | --- |\n| cited | E900-r0001 |\n| uncited | supported |"
        result = run_check_text(finding_text(body))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        problems = result.stdout.splitlines()
        self.assertEqual(["## Answer table row cites no run id: | uncited | supported |"],
                         [problem.split(": ", 1)[1] for problem in problems], result.stdout)

    def test_header_row_is_exempt_only_above_a_matching_separator(self):
        # Without a separator, or with one of another cell count, GFM renders no table: the rows
        # are text, so each must cite.
        for body in ("| An uncited first row |\n| E900-r0001 |",
                     "| An uncited first row |\n| --- | --- |\n| E900-r0001 | E900-r0001 |"):
            with self.subTest(body=body):
                result = run_check_text(finding_text(body))
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn("## Answer table row cites no run id: | An uncited first row |", result.stdout)

    def test_html_in_a_table_row_is_a_named_error(self):
        body = "| Lead | Run |\n| --- | --- |\n| <ul><li>uncited</li></ul> | E900-r0001 |"
        result = run_check_text(finding_text(body))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertTrue(unsupported_at(result, 7, "| <ul><li>uncited</li></ul> | E900-r0001 |"), result.stdout)

    def test_forms_outside_the_protected_sections_are_not_checked(self):
        after = "> A quote\n\n```\ncode\n```\n\n<details>HTML</details>\n\n#### Deep\n\nA paragraph."
        result = run_check_text(finding_text("- Cites E900-r0001.", after=after))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


def spelled(heading: str) -> str:
    """A finding whose real sections cite, followed by `heading` (which starts at line 11) and an
    uncited claim under it."""
    return ("## Answer\n\n- Cites E900-r0001.\n\n## Inferences\n\n- Cites E900-r0001.\n\n"
            f"## Notes\n\n{heading}\n\n- An uncited claim\n")


class U27Test(unittest.TestCase):
    """The owner's decision U27, as revised by U28: any heading (a line starting with `#`, a setext
    heading, an HTML `<h1>`..`<h6>`) whose raw letters (entities decoded, NFKC, casefolded) contain
    `answer` or `inferences` must be exactly `## Answer` or `## Inferences`, else it is a named
    error. This replaces round 3's deny-list of decorations, which Sol's round-3 R1 got past. Round
    4's two cases that only a model of rendering caught (a comment or an unknown tag inside the
    word) were removed with that model (U28)."""

    def assert_named(self, heading: str, first: str | None = None) -> None:
        result = run_check_text(spelled(heading))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        line = first if first is not None else heading.split("\n")[0]
        self.assertTrue(unsupported_at(result, 11, line), result.stdout)

    def test_sol_round_3_r1_spellings_are_named_errors(self):
        for name in ("Answer", "Inferences"):
            for heading in (f"## `{name}`", f"## [{name}](#{name.lower()})", f"## {name} ",
                            f"## {name} "):
                with self.subTest(heading=heading):
                    self.assert_named(heading)

    def test_decorated_spellings_are_named_errors(self):
        for name in ("Answer", "Inferences"):
            spellings = [
                f"## *{name}*", f"## **{name}**", f"## _{name}_", f"## ~~{name}~~",   # emphasis
                f"# {name}", f"### {name}", f"#### {name}", f"##### {name}", f"###### {name}",
                f"##\t{name}", f"##\t{name}\t", f"## {name}  ", f"## {name}  ",
                f"<h2>{name}</h2>", f'<H2 id="x">{name}</H2>', f"<h3>{name}</h3>",
                f"## [{name}](#a \"title (x)\")", f"## [{name}][ref]", f"## ![{name}](x.png)",
                f"## {name[0]}&#{ord(name[1])};{name[2:]}",                 # an entity
                f"## {''.join(chr(ord(c) + 0xFEE0) for c in name)}",       # fullwidth, NFKC
                f"## {name[:2]}​{name[2:]}",                           # a zero-width space
                f"- ## {name}", f"1. > ## {name}", f"#{name}", f"   ## {name}",
                f"## [{name}](<a)b>)",                                     # a `<...>` destination
                f"## {name}[^note]", f"## {name} :smile:",                 # footnote, emoji
                f"## {name}<script>x</script>", f"## {name}<style>p {{}}</style>",
                f"## {name}<noscript>x</noscript>", f"## {name}<span hidden>x</span>",
                f'## {name}<span style="display: none">x</span>', f"## {name} ![x](y.png)",
                f"## {name[0]}:{name[1:]}:",                               # `:...:` that is no emoji
            ]
            for heading in spellings:
                with self.subTest(heading=heading):
                    self.assert_named(heading)

    def test_setext_headings_are_named_errors(self):
        for name in ("Answer", "Inferences"):
            for heading in (f"{name}\n===", f"{name}\n---", f"*{name}*\n------", f"> {name}\n> ---",
                            f"{name[:3]}\n{name[3:]}\n---"):
                with self.subTest(heading=heading):
                    self.assert_named(heading)

    def test_html_heading_over_several_lines_is_a_named_error(self):
        for name in ("Answer", "Inferences"):
            with self.subTest(name=name):
                self.assert_named(f"<h2>\n{name}\n</h2>", "<h2>")
                self.assert_named(f"<h2>{name}\n\n- An uncited claim inside the unclosed heading")

    def test_a_heading_split_only_by_a_separator_markdown_does_not_split_at(self):
        # `str.splitlines` splits at NEL (U+0085) and LINE SEPARATOR (U+2028); Markdown does not, so
        # the heading is one line whose letters are `answer`.
        for sep in ("\u0085", " "):
            with self.subTest(sep=repr(sep)):
                self.assert_named(f"## Ans{sep}wer")



def headed(heading: str) -> subprocess.CompletedProcess:
    """Check a finding whose real sections cite, with `heading` and a cited line after them."""
    return run_check_text("## Answer\n\n- Cites E900-r0001.\n\n## Inferences\n\n- Cites E900-r0001.\n\n"
                          f"## Notes\n\n{heading}\n\nSome notes.\n")


class U28Test(unittest.TestCase):
    """The owner's decision U28: a heading's raw letters (entities decoded, NFKC, casefolded) that
    contain `answer` or `inferences` are an error unless the line is exactly the section's heading,
    and a heading whose letters come from more than one Unicode script is an error (#28)."""

    def assert_refused(self, heading: str) -> None:
        result = headed(heading)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertTrue(unsupported_at(result, 11, heading.split("\n")[0]), result.stdout)

    def test_sol_round_4_r1_a_quoted_gt_in_an_attribute_is_refused(self):
        # R1: `<[^>]*>` stopped at the `>` inside the attribute, so the tag was not removed whole
        # and the letters were not `answer`. U28 removes nothing, so the name is contained.
        for name in ("Answer", "Inferences"):
            for heading in (f'<h2 title=">x">{name}</h2>', f'## <span title=">x">{name}</span>'):
                with self.subTest(heading=heading):
                    self.assert_refused(heading)

    def test_sol_round_4_r2_headings_that_do_not_render_as_the_name_are_refused(self):
        # R2: these do not render as `Answer`; round 4 refused them only by guessing at rendering.
        # Under U28 they are refused because their raw letters contain the name, as intended.
        for name in ("Answer", "Inferences"):
            for heading in (f"## `{name}<script>x</script>`", f'## {name}<span title="hidden">x</span>'):
                with self.subTest(heading=heading):
                    self.assert_refused(heading)

    def test_headings_whose_words_contain_a_name_are_refused(self):
        for heading in ("### Answers", "### Inferences about x", "## Reanswering the question",
                        "# The answer", "Inferences drawn\n---", "<h3>Short answer</h3>",
                        "## Inferences about the executable"):
            with self.subTest(heading=heading):
                self.assert_refused(heading)

    def test_letters_from_more_than_one_script_are_refused(self):
        # A Cyrillic `А` (U+0410) or a Greek `Α` (U+0391) in `Answer`, and a Cyrillic `е` (U+0435) in
        # a heading that names no section: their letters never reduce to a name, but they mix.
        for heading in ("## Аnswer", "## Αnswer", "## Infеrences", "## Spеed",
                        "### Αlpha and beta", "## &#1040;nswer", "Spеed\n===",
                        "<h2>Аnswer</h2>"):
            with self.subTest(heading=heading):
                self.assert_refused(heading)

    def test_ordinary_headings_pass(self):
        for heading in ("## Speed", "### The `cycles=max` arm", "## Speed → time",
                        "## ⌈x⌉ rounding", "### Café au lait", "## E900-r0001 and 0x7ABD",
                        "## Method", "Speed\n---", "<h3>Speed</h3>", "## Αθήνα"):
            with self.subTest(heading=heading):
                result = headed(heading)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
