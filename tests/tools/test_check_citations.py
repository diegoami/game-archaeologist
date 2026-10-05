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

import os
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
    """The owner's decision U27, as revised by U28: any heading (a line starting with `#` or a setext
    heading; an HTML `<h1>`..`<h6>` line is refused whatever it says, U30) whose raw letters (entities decoded, NFKC, casefolded) contain
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
                        "## Method", "Speed\n---", "## Αθήνα"):
            with self.subTest(heading=heading):
                result = headed(heading)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)



class U30Test(unittest.TestCase):
    """The owner's decision U30, replacing U29: HTML headings are banned in findings. Any line
    containing `<h1`..`<h6`, in any case, anywhere in the file, is the named error. Nothing is
    parsed or matched across lines."""

    def assert_refused(self, text: str, number: int, line: str) -> None:
        result = run_check_text(text)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertTrue(unsupported_at(result, number, line), result.stdout)

    def test_sol_round_6_r1_probes_are_refused(self):
        # R1: a blank line inside the heading ended U29's block before the name, and tags splitting
        # the word kept its letters from containing the name.
        for name in ("Answer", "Inferences"):
            for block in (f"<h2>\n\n{name}\n\n</h2>", f"<h2>{name[:2]}<span>{name[2]}</span>{name[3:]}</h2>"):
                with self.subTest(block=block):
                    self.assert_refused(spelled(block), 11, block.split("\n")[0])

    def test_any_html_heading_outside_a_protected_section_is_refused(self):
        # No name, no protected section: the tag alone is the error.
        for block in ("<H3 class=x>", "<H3 class=x>Speed</H3>", "<h2>Speed</h2>", "Text, then <h1>x</h1>",
                      "<h6>", "<h3>Café</h3>"):
            with self.subTest(block=block):
                self.assert_refused(spelled(block), 11, block)

    def test_an_html_heading_inside_a_fence_is_refused(self):
        # U30 says anywhere: a fenced code block is not exempt.
        text = ("## Answer\n\n- Cites E900-r0001.\n\n## Inferences\n\n- Cites E900-r0001.\n\n"
                "## Notes\n\n```html\n<h6>Speed</h6>\n```\n")
        self.assert_refused(text, 12, "<h6>Speed</h6>")

    def test_each_html_heading_line_is_named(self):
        result = run_check_text(spelled("<h2>Speed</h2>\n<h3>Timing</h3>"))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertTrue(unsupported_at(result, 11, "<h2>Speed</h2>"), result.stdout)
        self.assertTrue(unsupported_at(result, 12, "<h3>Timing</h3>"), result.stdout)

    def test_tags_that_are_not_headings_pass_outside_protected_sections(self):
        for block in ("<hr>", "<header>x</header>", "<h7>x</h7>", "<html>", "h2 in prose"):
            with self.subTest(block=block):
                result = headed(block)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)


class U31Test(unittest.TestCase):
    """The owner's decision U31: any ATX or setext heading, anywhere in a finding, whose text
    contains `<`, `[` or `$` is the named error. Tags, links, images, autolinks, comments and math
    all start with one of them, so no markup can add letters that split a word past U28."""

    def assert_refused(self, heading: str) -> None:
        result = run_check_text(spelled(heading))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertTrue(unsupported_at(result, 11, heading.split("\n")[0]), result.stdout)

    def test_sol_round_7_r1_and_r2_are_refused(self):
        # R1: a tag split the word, so the raw letters were `answpanspanwer`, not `answer`.
        # R2: links split it the same way, with no HTML at all.
        for name in ("Answer", "Inferences"):
            for heading in (f"## {name[:2]}<span>{name[2]}</span>{name[3:]}",
                            f"## [{name[:2]}](x){name[2]}[{name[3:]}](y)",
                            f"## [{name[:2]}][x]{name[2:]}\n\n[x]: https://example.org"):
                with self.subTest(heading=heading):
                    self.assert_refused(heading)

    def test_a_bracket_or_angle_heading_outside_any_protected_section_is_refused(self):
        # No section name: the character alone is the error.
        for heading in ("## Speed [see x](y)", "### a < b", "# [Speed]", "> ## Quoted <b>x</b>",
                        "- ### Listed [x]"):
            with self.subTest(heading=heading):
                self.assert_refused(heading)

    def test_a_setext_heading_with_a_bracket_or_angle_is_refused(self):
        for heading in ("Speed [x](y)\n---", "Speed <i>x</i>\n===", "First line\n[x](y) second\n==="):
            with self.subTest(heading=heading):
                self.assert_refused(heading)

    def test_an_image_and_an_autolink_in_a_heading_are_refused(self):
        for heading in ("## ![x](y)", "## Speed ![x](y)", "## <https://x>", "## See <https://x>"):
            with self.subTest(heading=heading):
                self.assert_refused(heading)

    def test_math_that_splits_a_section_name_is_refused(self):
        # The main session's sweep of round 8: GitHub math renders `An$\mathrm{s}$wer` as Answer.
        for heading in ("## An$\\mathrm{s}$wer", "## Infer$e$nces"):
            with self.subTest(heading=heading):
                self.assert_refused(heading)

    def test_a_dollar_heading_outside_any_protected_section_is_refused(self):
        for heading in ("## Speed $x$", "### Costs $5", "> ## Quoted $y$", "- ### Listed $$z$$"):
            with self.subTest(heading=heading):
                self.assert_refused(heading)

    def test_a_setext_heading_with_a_dollar_is_refused(self):
        for heading in ("Speed $x$\n---", "An$\\mathrm{s}$wer\n===", "First line\n$y$ second\n==="):
            with self.subTest(heading=heading):
                self.assert_refused(heading)

    def test_headings_with_parentheses_backticks_or_stars_pass(self):
        for heading in ("## Speed (in cycles)", "### The `cycles` arm", "## *Speed* and **time**",
                        "## (x) `y` *z*", "Speed (x)\n---"):
            with self.subTest(heading=heading):
                result = headed(heading)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)


# The environment of the static tests' own `git` calls: nothing that points git at another
# repository, and no user or system configuration (hooks, templates, `safe.directory`).
GIT_TEST_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
GIT_TEST_ENV.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)


class StaticCitationTest(unittest.TestCase):
    """The owner's decision U26: `static:<path>[:<line>]` counts as a citation wherever a run id
    does, and `check_citations.py` checks the path against `git ls-files`. Each test builds its own
    temporary git repository, so the tracked, containment and line checks are exercised for real.

    Isolation (Sol's round-1 R2): the temporary directory may lie inside another repository (a
    reviewer's TMPDIR in its worktree). The tool itself refuses a root that is not its repository's
    top level, so no test depends on where TMPDIR is; the test's own `git` calls run without the
    variables that redirect git or load the user's and the system's configuration. Only the test of
    a root outside every repository sets `GIT_CEILING_DIRECTORIES`, so that it exercises the
    no-repository branch wherever it runs; the test of a root inside a repository sets none."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.git("init", "-q")
        self.git("config", "user.email", "t11@example.org")
        self.git("config", "user.name", "T11")

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args: str, root: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(root if root is not None else self.root), *args],
                              capture_output=True, text=True, check=True, env=GIT_TEST_ENV)

    def write(self, rel: str, content: str, tracked: bool = True) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if tracked:
            self.git("add", "--", rel)
        return path

    def check_text(self, text: str, root: Path | None = None,
                   env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        """Check a finding written into the temporary repository from `text`."""
        finding = self.root / "finding.md"
        finding.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools/check_citations.py"), str(finding),
             "--runs", str(FIXTURES / "runs"), "--root", str(root if root is not None else self.root)],
            cwd=REPO_ROOT, capture_output=True, text=True,
            env=env if env is not None else GIT_TEST_ENV)

    def check(self, answer: str, inferences: str = "- Rests on E900-r0001.",
              root: Path | None = None, env: dict[str, str] | None = None
              ) -> subprocess.CompletedProcess:
        """A finding whose `## Answer` holds `answer`; line 5 is the first body line. The Inferences
        default cites a fixture run, so a test isolates the Answer's static token."""
        return self.check_text(f"# F990 Static fixture\n\n## Answer\n\n{answer}\n\n"
                               f"## Inferences\n\n{inferences}\n", root=root, env=env)

    def assert_named(self, answer: str, expected: str, env: dict[str, str] | None = None) -> None:
        """The finding whose Answer is `answer` exits 1, `expected` is on its output, no traceback."""
        result = self.check(answer, env=env)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(expected, result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_tracked_file_passes(self):
        self.write("data.txt", "one\ntwo\nthree\n")
        result = self.check("- Rests on static:data.txt.")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("ok: citations in", result.stdout)

    def test_tracked_directory_passes(self):
        self.write("code/a.txt", "one\ntwo\n")
        result = self.check("- Rests on static:code/.")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("ok: citations in", result.stdout)
        # A directory without the trailing slash names the same tracked directory.
        result = self.check("- Rests on static:code.")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_line_within_the_file_passes(self):
        self.write("data.txt", "one\ntwo\nthree\n")
        result = self.check("- Rests on static:data.txt:3.")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_a_bullet_holding_only_a_static_citation_is_cited(self):
        self.write("data.txt", "one\n")
        result = self.check("- Rests on static:data.txt.", "- Rests on static:data.txt.")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_a_table_row_holding_only_a_static_citation_is_cited(self):
        self.write("data.txt", "one\n")
        body = "| Lead | Evidence |\n| --- | --- |\n| Rests on | static:data.txt |"
        result = self.check(body, body)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_backticks_and_trailing_punctuation_pass(self):
        self.write("data.txt", "one\ntwo\n")
        answer = "- Rests on `static:data.txt`,\n- Rests on static:data.txt:2."
        result = self.check(answer)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_a_missing_path_is_a_named_error(self):
        result = self.check("- Rests on static:no/such.txt.")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(":5: static citation static:no/such.txt: no tracked path no/such.txt",
                      result.stdout)

    def test_an_untracked_file_is_a_named_error(self):
        self.write("data.txt", "one\n", tracked=False)
        result = self.check("- Rests on static:data.txt.")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(":5: static citation static:data.txt: no tracked path data.txt", result.stdout)

    def test_line_zero_is_a_named_error(self):
        self.write("data.txt", "one\ntwo\n")
        result = self.check("- Rests on static:data.txt:0.")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(":5: static citation static:data.txt:0: line 0 is outside data.txt",
                      result.stdout)

    def test_a_line_past_the_end_is_a_named_error(self):
        self.write("data.txt", "one\ntwo\n")
        result = self.check("- Rests on static:data.txt:3.")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(":5: static citation static:data.txt:3: line 3 is outside data.txt (1..2)",
                      result.stdout)

    def test_a_line_on_a_directory_is_a_named_error(self):
        self.write("code/a.txt", "one\n")
        result = self.check("- Rests on static:code:1.")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(":5: static citation static:code:1: code is a directory", result.stdout)

    def test_a_dot_or_dotdot_segment_is_malformed(self):
        self.write("data.txt", "one\n")
        for token in ("static:.", "static:..", "static:a/../b", "static:a/./b"):
            with self.subTest(token=token):
                result = self.check(f"- Rests on {token}.")
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn(f":5: malformed static citation: {token}", result.stdout)

    def test_an_absolute_path_is_malformed(self):
        result = self.check("- Rests on static:/etc/passwd.")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(":5: malformed static citation: static:/etc/passwd", result.stdout)

    def test_a_tracked_symlink_leaving_the_root_is_a_named_error(self):
        os.symlink(str(REPO_ROOT / "README.md"), str(self.root / "escape"))
        self.git("add", "--", "escape")
        result = self.check("- Rests on static:escape.")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(":5: static citation static:escape: escape resolves outside the repository root",
                      result.stdout)

    def test_a_bare_static_token_is_malformed(self):
        result = self.check("- Rests on static: .")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(":5: malformed static citation: static:", result.stdout)

    def test_a_double_slash_is_malformed(self):
        result = self.check("- Rests on static:a//b.")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(":5: malformed static citation: static:a//b", result.stdout)

    def test_a_root_that_is_not_a_git_repository_is_one_named_error(self):
        self.write("data.txt", "one\n")
        with tempfile.TemporaryDirectory() as other:
            # The ceiling stops git's discovery at the temporary folder, so this visits the
            # no-repository branch even when TMPDIR lies inside a repository.
            other = Path(other).resolve()
            (other / "data.txt").write_text("one\n", encoding="utf-8")
            env = dict(GIT_TEST_ENV, GIT_CEILING_DIRECTORIES=str(other.parent))
            result = self.check("- Rests on static:data.txt.", root=other, env=env)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(1, len(result.stdout.splitlines()), result.stdout)
        self.assertIn(f"{other}: not a git repository", result.stdout)

    def test_a_finding_without_a_static_token_needs_no_repository(self):
        with tempfile.TemporaryDirectory() as other:
            other = Path(other).resolve()
            env = dict(GIT_TEST_ENV, GIT_CEILING_DIRECTORIES=str(other.parent))
            result = self.check("- Rests on E900-r0001.", root=other, env=env)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            result = self.check("- Rests on E900-r0001.", root=self.root / "absent", env=env)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_a_root_inside_another_repository_is_one_named_error(self):
        # Sol's round-1 R2: a folder inside a repository is no repository's top level; git would
        # answer for the enclosing one. No ceiling here: the tool alone must refuse it.
        self.write("sub/data.txt", "one\n")
        sub = self.root / "sub"
        result = self.check("- Rests on static:data.txt.", root=sub)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(1, len(result.stdout.splitlines()), result.stdout)
        self.assertIn(f"{sub}: not a git repository (it lies inside {self.root})", result.stdout)

    def test_git_variables_that_name_another_repository_are_ignored(self):
        # A `GIT_DIR` from the caller's environment would make `git -C <root>` read another
        # repository's index, where the cited path is tracked although it is not in the root's.
        self.write("data.txt", "one\n", tracked=False)
        with tempfile.TemporaryDirectory() as other:
            other = Path(other).resolve()
            self.git("init", "-q", root=other)
            (other / "data.txt").write_text("one\n", encoding="utf-8")
            self.git("add", "--", "data.txt", root=other)
            for name, value in (("GIT_DIR", str(other / ".git")),
                                ("GIT_INDEX_FILE", str(other / ".git" / "index"))):
                with self.subTest(variable=name):
                    self.assert_named("- Rests on static:data.txt.",
                                      ":5: static citation static:data.txt: no tracked path data.txt",
                                      env=dict(GIT_TEST_ENV, **{name: value}))

    def test_a_tracked_file_deleted_from_disk_is_a_named_error(self):
        # Sol's round-1 R1: in the index but not on disk, with and without `:line`.
        self.write("data.txt", "one\n")
        (self.root / "data.txt").unlink()
        for token in ("static:data.txt", "static:data.txt:1"):
            with self.subTest(token=token):
                self.assert_named(f"- Rests on {token}.",
                                  f":5: static citation {token}: data.txt is tracked but missing on disk")

    def test_a_tracked_dangling_symlink_is_a_named_error(self):
        # Sol's round-1 R1: a symlink to an absent file inside the root.
        os.symlink("absent.txt", str(self.root / "link"))
        self.git("add", "--", "link")
        self.assert_named("- Rests on static:link.",
                          ":5: static citation static:link: link is tracked but missing on disk")

    def test_a_tracked_file_the_disk_holds_a_directory_for_is_a_named_error(self):
        self.write("data.txt", "one\n")
        (self.root / "data.txt").unlink()
        (self.root / "data.txt").mkdir()
        (self.root / "data.txt" / "inner").write_text("one\n", encoding="utf-8")
        self.assert_named("- Rests on static:data.txt.",
                          ":5: static citation static:data.txt: data.txt is not a file on disk")

    def test_a_directory_whose_tracked_files_are_all_gone_is_a_named_error(self):
        self.write("code/a.txt", "one\n")
        self.write("code/b.txt", "two\n")
        (self.root / "code" / "a.txt").unlink()
        (self.root / "code" / "b.txt").unlink()
        (self.root / "code" / "untracked.txt").write_text("three\n", encoding="utf-8")
        for token in ("static:code/", "static:code"):
            with self.subTest(token=token):
                self.assert_named(f"- Rests on {token}.",
                                  f":5: static citation {token}: no tracked file under code is on"
                                  " disk inside the repository root")

    def test_a_directory_removed_from_disk_is_a_named_error(self):
        self.write("code/a.txt", "one\n")
        (self.root / "code" / "a.txt").unlink()
        (self.root / "code").rmdir()
        self.assert_named("- Rests on static:code/.",
                          ":5: static citation static:code/: code is tracked but missing on disk")

    def test_a_directory_whose_only_tracked_file_leaves_the_root_is_a_named_error(self):
        (self.root / "code").mkdir()
        os.symlink(str(REPO_ROOT / "README.md"), str(self.root / "code" / "escape"))
        self.git("add", "--", "code/escape")
        self.assert_named("- Rests on static:code/.",
                          ":5: static citation static:code/: no tracked file under code is on disk"
                          " inside the repository root")

    def test_a_tracked_directory_replaced_by_a_symlink_is_a_named_error(self):
        # The index tracks code/a.txt; on disk `code` is a symlink to another folder in the root
        # holding an a.txt that git does not track there.
        self.write("code/a.txt", "one\n")
        (self.root / "code" / "a.txt").unlink()
        (self.root / "code").rmdir()
        (self.root / "other").mkdir()
        (self.root / "other" / "a.txt").write_text("one\n", encoding="utf-8")
        os.symlink("other", str(self.root / "code"))
        self.assert_named("- Rests on static:code/a.txt.",
                          ":5: static citation static:code/a.txt: code is a symlink on disk,"
                          " not a tracked directory")

    def test_a_line_past_python_s_int_conversion_limit_is_a_named_error(self):
        # Sol's round-1 R3: 4,301 digits and more exceed `int()`'s default limit of 4,300.
        self.write("data.txt", "one\ntwo\n")
        for digits in ("1" * 4301, "9" * 20000):
            with self.subTest(length=len(digits)):
                self.assert_named(f"- Rests on static:data.txt:{digits}.",
                                  f":5: static citation static:data.txt:{digits}: line {digits} is"
                                  " outside data.txt (1..2)")

    def test_a_line_with_as_many_digits_as_the_count_is_compared_by_value(self):
        # The length comparison only short-cuts longer lines; equal lengths still compare values.
        self.write("data.txt", "".join(f"{i}\n" for i in range(12)))
        result = self.check("- Rests on static:data.txt:12.")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assert_named("- Rests on static:data.txt:13.",
                          ":5: static citation static:data.txt:13: line 13 is outside data.txt (1..12)")

    def test_a_token_outside_a_protected_section_is_checked(self):
        result = self.check_text("# F990 Static fixture\n\n## Answer\n\n- Rests on static:data.txt.\n\n"
                                 "## Method\n\nA malformed static:a//b token.\n\n## Inferences\n\n"
                                 "- Rests on static:data.txt.\n")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("malformed static citation: static:a//b", result.stdout)

    def test_a_boundary_not_a_letter_digit_or_underscore_is_required(self):
        # `mystatic:...` and `_static:...` are not tokens; only the word `static:` after a boundary is.
        self.write("data.txt", "one\n")
        result = self.check_text("# F990 Static fixture\n\n## Answer\n\n- Rests on static:data.txt.\n\n"
                                 "## Method\n\nmystatic:a//b and _static:a//b here.\n\n## Inferences\n\n"
                                 "- Rests on static:data.txt.\n")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_a_thirty_digit_line_is_a_named_error_not_a_crash(self):
        self.write("data.txt", "one\ntwo\n")
        digits = "1" + "0" * 29
        result = self.check(f"- Rests on static:data.txt:{digits}.")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(f"line {digits} is outside data.txt", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_a_nul_in_a_path_is_a_named_error_not_a_crash(self):
        self.write("data.txt", "one\n")
        result = self.check("- Rests on static:a\x00b.")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("malformed static citation", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_a_finding_that_is_not_utf8_is_a_named_error_not_a_crash(self):
        self.write("data.txt", "one\n")
        finding = self.root / "finding.md"
        finding.write_bytes(b"# F990\n\n## Answer\n\n- static:data.txt \xff\xfe\n")
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools/check_citations.py"), str(finding),
             "--runs", str(FIXTURES / "runs"), "--root", str(self.root)],
            cwd=REPO_ROOT, capture_output=True, text=True, env=GIT_TEST_ENV)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("cannot check citations", result.stdout)
        # Round 2: the named line of the first byte that is not UTF-8.
        self.assertIn(f"{finding}:5: cannot check citations: not UTF-8 (byte 0xff at offset 37)",
                      result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    # Round 3 (Sol's round-2 R1-R3): every rule of the token grammar has a test that fails when the
    # rule is deleted. The PR body's mutation table maps each grammar element to its tests.

    def test_a_leading_zero_line_is_malformed(self):
        # Twelve lines, so `01`, `09` and `012` are inside the file: only the grammar rejects them.
        self.write("data.txt", "".join(f"line {n}\n" for n in range(1, 13)))
        for token in ("static:data.txt:01", "static:data.txt:09", "static:data.txt:012"):
            with self.subTest(token=token):
                result = self.check(f"- Rests on {token}.")
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn(f":5: malformed static citation: {token}", result.stdout)

    def test_repeated_trailing_slashes_are_malformed(self):
        # `code` is a tracked directory, so only the single optional trailing `/` rejects these.
        self.write("code/a.txt", "one\n")
        for token in ("static:code//", "static:code///"):
            with self.subTest(token=token):
                result = self.check(f"- Rests on {token}")
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn(f":5: malformed static citation: {token}", result.stdout)

    def test_a_segment_character_outside_the_ascii_alphabet_is_malformed(self):
        # Each path is a tracked file, so only the `[A-Za-z0-9_.-]` alphabet rejects it.
        # Each bad character is tried in the file segment and in a directory segment.
        for bad in ("é", "+", ")", "@", "~", "`", ":"):
            for path in (f"a{bad}b.txt", f"dir/a{bad}b.txt", f"d{bad}r/a.txt"):
                with self.subTest(path=path):
                    self.write(path, "one\n")
                    result = self.check(f"- Rests on static:{path} here.")
                    self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                    self.assertIn(f":5: malformed static citation: static:{path}", result.stdout)

    def test_every_segment_character_passes_in_every_segment(self):
        # Each of A-Z, a-z, 0-9, `_`, `.` and `-` in a directory segment and in the file segment,
        # three segments deep.
        self.write("Ab_9.-c/Dz_0.-e/Xy_5.-z.txt", "one\n")
        for token in ("static:Ab_9.-c/Dz_0.-e/Xy_5.-z.txt", "static:Ab_9.-c/Dz_0.-e/",
                      "static:Ab_9.-c/Dz_0.-e", "static:Ab_9.-c/"):
            with self.subTest(token=token):
                result = self.check(f"- Rests on {token} here.")
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_every_line_digit_passes(self):
        # 120 lines: single, two and three digits, every digit 0-9 in some place, both bounds.
        self.write("data.txt", "".join(f"line {n}\n" for n in range(1, 121)))
        tokens = ["static:data.txt:1", "static:data.txt:9", "static:data.txt:10",
                  "static:data.txt:23", "static:data.txt:45", "static:data.txt:67",
                  "static:data.txt:89", "static:data.txt:99", "static:data.txt:100",
                  "static:data.txt:120"]
        for token in tokens:
            with self.subTest(token=token):
                result = self.check(f"- Rests on {token} here.")
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_each_trailing_character_is_stripped(self):
        # Each of `` ` . , ; : ) ] } ' " * `` alone after a valid token, with and without a line.
        self.write("data.txt", "one\ntwo\n")
        for char in "`.,;:)]}'\"*":
            for token in ("static:data.txt", "static:data.txt:2"):
                with self.subTest(token=token + char):
                    result = self.check(f"- Rests on {token}{char} here.")
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_a_valid_prefix_followed_by_other_characters_is_malformed(self):
        # The whole argument must match: a valid path or line followed by anything else fails,
        # including a non-ASCII digit (`\u0660`, which Python's `\d` and `int()` accept).
        self.write("data.txt", "one\ntwo\n")
        for token in ("static:data.txt)x", "static:data.txt`x", "static:data.txt:1x",
                      "static:data.txt:1:2", "static:data.txt::1", "static::1",
                      "static:data.txt:1\u0660"):
            with self.subTest(token=token):
                result = self.check(f"- Rests on {token} here.")
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn(f":5: malformed static citation: {token}", result.stdout)

    def test_a_token_at_the_start_of_a_line_or_after_punctuation_is_checked(self):
        # The boundary before `static:` is any character but a letter, digit or `_`, or none.
        # Letters and digits are ASCII, as in a run id's boundary: after `é` the token is checked
        # (Python's Unicode `\b` would skip it).
        for line in ("static:a//b", "(static:a//b", "x-static:a//b", "*static:a//b",
                     "\u00e9static:a//b"):
            with self.subTest(line=line):
                result = self.check_text("# F990 Static fixture\n\n## Answer\n\n- Rests on E900-r0001.\n\n"
                                         f"## Method\n\n{line}\n\n## Inferences\n\n- Rests on E900-r0001.\n")
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn(":9: malformed static citation: static:a//b", result.stdout)

    def test_a_letter_digit_or_underscore_before_static_is_no_token(self):
        # One case per class of the boundary: upper, lower, digit and `_`.
        for prefix in ("A", "z", "0", "9", "_"):
            with self.subTest(prefix=prefix):
                result = self.check_text("# F990 Static fixture\n\n## Answer\n\n- Rests on E900-r0001.\n\n"
                                         f"## Method\n\n{prefix}static:a//b\n\n## Inferences\n\n"
                                         "- Rests on E900-r0001.\n")
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
