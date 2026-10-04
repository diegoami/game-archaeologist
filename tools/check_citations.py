#!/usr/bin/env python3
"""Check a finding's citations.

`python3 tools/check_citations.py <finding.md>` fails (exit 1) when a run id (`E<nnn>-r<nnnn>`)
anywhere in the finding has no record under `runs/E<nnn>/`, or when a bullet in `## Answer` or
`## Inferences` cites no run id. Exit 0 otherwise. `--runs <dir>` checks against another records
directory; without it the records live in `runs/` under the working directory, never under this
script's directory, so a game repository that fetches this file into a cache folder still checks
its own records (ADR-009).

A bullet is any list item, however it is written (PR #27 round 2): a `-`, `*`, `+` or numbered
`1.`/`1)` marker, followed by a space, a tab, or the end of its line (a lone marker's text is the
indented lines that follow), written plainly or inside a blockquote (`> - claim`), or an HTML
`<li>`. A bullet's indented continuation lines belong to it, so a run id on a wrapped line counts
(toy-archaeology#12); a blank or unindented line ends it, and a quoted bullet's continuation stays
at its quote depth and is neither blank, a heading, a fence nor a thematic break. A thematic break
(`- - -`) is not a bullet. **Every** occurrence of `## Answer` and `## Inferences` is checked, so
repeating a heading cannot move a claim out of the guard, and the heading is recognised however it
is spelt (closing `#`s, a tab, any case, or a setext `Answer` over `---`).

Everything this file guesses about how a finding renders fails closed: a guess that is wrong makes
the check stricter, never lets a claim through. A fenced code block or an HTML comment only stops a
`## ` line inside it from ending a section; it never hides a bullet, and a heading inside it still
starts a section. A fence is taken to run until a line that would close it in CommonMark (the same
character, at least as long, nothing after it), or to the end of the file.

Any input that cannot be read is a named error, never a traceback.

Adapted from diegoami/toy-archaeology tools/check_citations.py at a3056ff through
diegoami/goal2-archaeology's copy.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# A run id, bounded by anything but a letter or digit: `_E001-r0001_` (emphasis) is one, which a
# `\b` pattern missed because `_` is a word character.
RUN_ID = re.compile(r"(?<![A-Za-z0-9])E[0-9]{3,}-r[0-9]{4,}(?![A-Za-z0-9])")
SECTIONS = ("## Answer", "## Inferences")
# Every Markdown list marker: `-`, `*`, `+`, or up to nine digits with `.` or `)`, then a space, a
# tab, or the end of the line; or an HTML `<li>`. `1.5 million` is not a marker: what follows the
# digit run must end the marker, and `-foo`/`*emphasis*` are not either: the marker needs its
# whitespace.
MARKER = re.compile(r"(?:[-*+]|\d{1,9}[.)])(?:[ \t]+|$)|<li(?:[\s>/]|$)", re.IGNORECASE)
# A blockquote prefix, one level: up to three spaces, `>` and one optional space or tab.
QUOTE_LEVEL = re.compile(r"^ {0,3}>[ \t]?")
# A line that may open a fenced code block: ``` or ~~~ after any indentation. It is a superset of
# CommonMark's openers (which allow at most three spaces and no backtick in a backtick fence's info
# string), because a fence here only stops a section from ending.
FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})")
# A thematic break (`- - -`, `***`, `___`): a marker's shape, but not a bullet.
BREAK = re.compile(r"^([-_*])(?:[ \t]*\1){2,}[ \t]*$")
# An ATX heading (`## Text`, `## Text ##`) or a setext underline of `-`.
ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
SETEXT_2 = re.compile(r"^ {0,3}-+[ \t]*$")


def closes(line: str, fence: str) -> bool:
    """Whether `line` closes the fence opened by `fence` (its run of ` or ~), as CommonMark says:
    up to three spaces, the same character at least as many times, then only whitespace."""
    match = re.match(r"^ {0,3}(" + re.escape(fence[0]) + r"{" + str(len(fence)) + r",})[ \t]*$", line)
    return match is not None


def heading_text(lines: list[str], i: int) -> str | None:
    """The text of the level-2 heading at line `i`, case-folded, or None when it is not one: an ATX
    `## Text` (closing `#`s and tabs allowed) or a setext `Text` over a line of `-`."""
    match = ATX.match(lines[i])
    if match:
        return (match.group(2) or "").strip().casefold() if len(match.group(1)) == 2 else None
    if lines[i].strip() and i + 1 < len(lines) and SETEXT_2.match(lines[i + 1]) \
            and not MARKER.match(lines[i].lstrip()) and not ATX.match(lines[i]):
        return lines[i].strip().casefold()
    return None


def in_comment_after(line: str, comment: bool) -> bool:
    """Whether an HTML comment is still open after `line`, given whether one was open before it."""
    marker = "-->" if comment else "<!--"
    at = line.find(marker)
    while at >= 0:
        line, comment = line[at + len(marker):], not comment
        marker = "-->" if comment else "<!--"
        at = line.find(marker)
    return comment


def section_bodies(lines: list[str], heading: str) -> list[list[str]]:
    """The body lines of every occurrence of `heading`, in order; [] when it never appears.

    Every line is part of a body, fenced or commented or not. A heading starts a section wherever it
    sits; a `## ` line ends one only outside a fence and outside an HTML comment, so a claim after a
    fenced example or a comment is still under its heading and is checked."""
    want = heading[3:].casefold()
    bodies: list[list[str]] = []
    body: list[str] | None = None
    fence: str | None = None
    comment = False
    skip = 0
    for i, line in enumerate(lines):
        hidden = fence is not None or comment
        if fence is not None:
            if closes(line, fence):
                fence = None
        elif comment:
            comment = in_comment_after(line, True)
        else:
            opened = FENCE_OPEN.match(line)
            if opened:
                fence = opened.group(1)
            else:
                comment = in_comment_after(line, False)
        if skip:
            skip -= 1
            continue
        if heading_text(lines, i) == want:
            if body is not None:
                bodies.append(body)
            body = []
            if not ATX.match(line):
                skip = 1  # the setext underline
        elif body is not None:
            if line.startswith("## ") and not hidden:
                bodies.append(body)
                body = None
            else:
                body.append(line)
    if body is not None:
        bodies.append(body)
    return bodies


def dequote(line: str) -> tuple[int, str]:
    """The quote depth of `line` and its text inside the quotes."""
    depth = 0
    while True:
        match = QUOTE_LEVEL.match(line)
        if not match:
            return depth, line
        depth, line = depth + 1, line[match.end():]


def continues(line: str, depth: int) -> bool:
    """Whether `line` continues a bullet written at quote depth `depth`."""
    if not line.strip():
        return False
    if depth == 0:
        return line[:1] in (" ", "\t")
    line_depth, text = dequote(line)
    if line[:1] in (" ", "\t") and line_depth == 0:
        return True  # an indented line: the bullet's own continuation, quote markers dropped
    if line_depth != depth or not text.strip():
        return False
    if text[:1] in (" ", "\t"):
        return True
    return not (ATX.match(text) or FENCE_OPEN.match(text) or BREAK.match(text) or text.startswith("<"))


def bullets(lines: list[str]) -> list[str]:
    """Each bullet together with its continuation lines, not a new bullet.

    A bullet starts at any list marker, plainly or inside a blockquote; a line continues it when it
    is indented, or, for a quoted bullet, when it is a non-blank line at the same quote depth that
    is not a heading, fence, thematic break or HTML block. A blank or unindented line ends the
    bullet. A thematic break is not a bullet."""
    found: list[str] = []
    current: list[str] | None = None
    depth = 0
    for line in lines:
        line_depth, stripped = dequote(line.lstrip(" "))
        stripped = stripped.lstrip()
        if MARKER.match(stripped) and not BREAK.match(stripped):
            if current is not None:
                found.append("\n".join(current))
            current = [line]
            depth = line_depth
        elif current is not None and continues(line, depth):
            current.append(line)
        else:
            if current is not None:
                found.append("\n".join(current))
                current = None
    if current is not None:
        found.append("\n".join(current))
    return found


def check(finding: Path, runs: Path) -> list[str]:
    problems = []
    if not finding.is_file():
        return [f"{finding}: no such file"]
    text = finding.read_text(encoding="utf-8")
    lines = text.splitlines()

    for run_id in sorted(set(RUN_ID.findall(text))):
        experiment = run_id.split("-", 1)[0]
        if not (runs / experiment / f"{run_id}.json").is_file():
            problems.append(f"{finding}: cites missing run {run_id} (no {runs / experiment / f'{run_id}.json'})")

    for heading in SECTIONS:
        bodies = section_bodies(lines, heading)
        if not bodies:
            problems.append(f"{finding}: missing section '{heading}'")
            continue
        for body in bodies:
            for bullet in bullets(body):
                if not RUN_ID.search(bullet):
                    problems.append(f"{finding}: {heading} bullet cites no run id: {bullet.strip()}")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("finding", type=Path)
    parser.add_argument("--runs", type=Path, default=None,
                        help="the records directory (default: runs/ under the working directory)")
    args = parser.parse_args(argv)
    runs = args.runs if args.runs is not None else Path.cwd() / "runs"
    try:
        problems = check(args.finding, runs)
    except Exception as e:  # noqa: BLE001 - no input may produce a traceback
        print(f"{args.finding}: cannot check citations: {type(e).__name__}: {e}")
        return 1
    if problems:
        print("\n".join(problems))
        return 1
    print(f"ok: citations in {args.finding} resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
