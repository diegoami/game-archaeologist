#!/usr/bin/env python3
"""Check a finding's citations.

`python3 tools/check_citations.py <finding.md>` fails (exit 1) when a run id (`E<nnn>-r<nnnn>`)
anywhere in the finding has no record under `runs/E<nnn>/`, or when a bullet in `## Answer` or
`## Inferences` cites no run id. Exit 0 otherwise. `--runs <dir>` checks against another records
directory; without it the records live in `runs/` under the working directory, never under this
script's directory, so a game repository that fetches this file into a cache folder still checks
its own records (ADR-009).

A bullet is any Markdown list item, however it is written (PR #27 round 2): a `-`, `*`, `+` or
numbered `1.`/`1)` marker, followed by a space, a tab, or the end of its line (a lone marker's
text is the indented lines that follow), written plainly or inside a blockquote (`> - claim`).
A bullet's indented continuation lines belong to it, so a run id on a wrapped line counts
(toy-archaeology#12); a blank or unindented line ends it. A thematic break (`- - -`) is not a
bullet. However the sections sit, **every** occurrence of `## Answer` and `## Inferences` is
checked, so repeating a heading cannot move a claim out of the guard, and fenced code is neither
heading nor bullet: a `## ` line inside a fence cannot end a section, and an example bullet inside
a fence is not a claim.

Any input that cannot be read is a named error, never a traceback.

Adapted from diegoami/toy-archaeology tools/check_citations.py at a3056ff through
diegoami/goal2-archaeology's copy.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RUN_ID = re.compile(r"\bE[0-9]{3,}-r[0-9]{4,}\b")
SECTIONS = ("## Answer", "## Inferences")
# Every Markdown list marker: `-`, `*`, `+`, or up to nine digits with `.` or `)`, then a space, a
# tab, or the end of the line. `1.5 million` is not a marker: what follows the digit run must end
# the marker, and `-foo`/`*emphasis*` are not either: the marker needs its whitespace.
MARKER = re.compile(r"(?:[-*+]|\d{1,9}[.)])(?:[ \t]+|$)")
# A blockquote prefix, possibly repeated (`> > - claim`) or indented, stripped before the test.
QUOTE = re.compile(r"^\s*(?:>[ \t]*)+")
# A fenced code block: ``` or ~~~ at the start of a line, after any indentation.
FENCE = re.compile(r"^\s*(?:```+|~~~+)")
# A thematic break (`- - -`, `***`, `___`): a marker's shape, but not a bullet.
BREAK = re.compile(r"^([-_*])(?:[ \t]*\1){2,}[ \t]*$")


def section_bodies(lines: list[str], heading: str) -> list[list[str]]:
    """The body lines of every occurrence of `heading`, in order; [] when it never appears.

    A fenced code block is neither heading nor body: a `## ` line inside a fence cannot end the
    section, so a claim after a fenced example is still under its heading and is checked."""
    bodies: list[list[str]] = []
    body: list[str] | None = None
    fence = False
    for line in lines:
        if fence:
            if FENCE.match(line):
                fence = False
            continue
        if FENCE.match(line):
            fence = True
            continue
        if line.strip() == heading:
            if body is not None:
                bodies.append(body)
            body = []
        elif body is not None:
            if line.startswith("## "):
                bodies.append(body)
                body = None
            else:
                body.append(line)
    if body is not None:
        bodies.append(body)
    return bodies


def bullets(lines: list[str]) -> list[str]:
    """Each bullet together with its continuation lines, not a new bullet.

    A bullet starts at any list marker, plainly or inside a blockquote; a line continues it when it
    is indented, or, for a quoted bullet, when it is quoted too. A blank or unindented line ends
    the bullet. A thematic break is not a bullet."""
    found: list[str] = []
    current: list[str] | None = None
    quoted = False
    for line in lines:
        stripped = QUOTE.sub("", line).lstrip()
        if MARKER.match(stripped) and not BREAK.match(stripped):
            if current is not None:
                found.append("\n".join(current))
            current = [line]
            quoted = line.lstrip().startswith(">")
        elif current is not None and line.strip() and (
                line[:1] in (" ", "\t") or (quoted and line.lstrip().startswith(">"))):
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
