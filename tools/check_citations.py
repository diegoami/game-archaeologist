#!/usr/bin/env python3
"""Check a finding's citations.

`python3 tools/check_citations.py <finding.md>` fails (exit 1) when a run id (`E<nnn>-r<nnnn>`)
anywhere in the finding has no record under `runs/E<nnn>/`, or when a claim in `## Answer` or
`## Inferences` cites no run id. Exit 0 otherwise. `--runs <dir>` checks against another records
directory; without it the records live in `runs/` under the working directory, never under this
script's directory, so a game repository that fetches this file into a cache folder still checks
its own records (ADR-009).

The two protected sections hold only these lines (the owner's decision U25, 2026-10-04), so the
check fails closed instead of parsing ever more Markdown:

- list items (`-`, `*`, `+`, `1.` or `1)` markers, followed by a space, a tab or the end of the
  line) and their indented continuation lines; each item, with its continuation lines, must cite a
  run id on one of its lines (toy-archaeology#12). A blank or unindented line ends the item;
- `###` sub-headings;
- table rows (lines starting with `|`); every data row must cite a run id. The header row and the
  `|---|` separator under it are exempt, and only when the separator has the header's cell count;
- blank lines.

Every other line there is the named error `<file>:<line>: unsupported in a protected section:
<line>`: HTML of any kind (`<` before a letter, `/`, `!` or `?`, anywhere on the line), a
blockquote, a fence, any heading but `###`, a setext underline, a thematic break, a paragraph line,
or a list item or continuation line whose text opens one of these. A section's heading is exactly
`## Answer` or `## Inferences` and runs to the next line starting with `## `; a second one is an
error, and so is any other spelling of it anywhere in the file: any line that reads `Answer` or
`Inferences` once HTML tags and the `#`s, `>`s, list markers, emphasis and whitespace around it are
removed (`##\tAnswer`, `## ANSWER`, `> ## Answer`, `<h2>Answer</h2>`, a setext `Answer`).

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
# A list marker after any indentation: `-`, `*`, `+`, or up to nine digits with `.` or `)`, then a
# space, a tab or the end of the line. `1.5 million`, `-foo` and `*emphasis*` are not markers.
MARKER = re.compile(r"[ \t]*(?:[-*+]|\d{1,9}[.)])(?:[ \t]+|$)")
# A thematic break (`- - -`, `***`, `___`): a marker's shape, but not a list item.
BREAK = re.compile(r"^[ \t]*([-_*])(?:[ \t]*\1){2,}[ \t]*$")
SUBHEADING = re.compile(r"^### +\S")
# What may not open the text of a list item or a continuation line: a blockquote, a heading, a
# fence or a setext underline (HTML anywhere on the line is refused on its own).
BLOCK = re.compile(r"^(?:>|#|`{3}|~{3}|=+[ \t]*$|-+[ \t]*$)")
# HTML of any kind, anywhere on a protected line.
HTML = re.compile(r"<[A-Za-z/!?]")
# A table's delimiter row: cells of dashes with optional alignment colons.
SEPARATOR = re.compile(r"^\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")
# A line that only names a protected section once HTML tags and its decoration are removed: `#`s,
# quote `>`s, list markers, emphasis, underline characters, digits and whitespace.
TAG = re.compile(r"<[^>]*>")
DECORATION = " \t#>*+-_=.)0123456789"
NAMES = {heading[3:].casefold() for heading in SECTIONS}


def cells(row: str) -> int:
    """The number of cells in a table row: its unescaped `|`-separated parts, outer pipes dropped."""
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return len(re.split(r"(?<!\\)\|", row))


def item_text(line: str) -> str:
    """The text of a list item once every leading marker is removed (`- 1. text` is `text`)."""
    match = MARKER.match(line)
    while match and match.end() > 0:
        line = line[match.end():]
        match = MARKER.match(line)
    return line.strip()


def misspelt(line: str) -> bool:
    """Whether `line` names a protected section without being exactly its heading."""
    text = TAG.sub("", line).strip(DECORATION).casefold()
    return text in NAMES and line not in SECTIONS


def check_body(finding: Path, heading: str, body: list[tuple[int, str]]) -> list[str]:
    """The problems of one protected section's body, given as (line number, line) pairs."""
    problems = []

    def unsupported(number: int, line: str) -> None:
        problems.append(f"{finding}:{number}: unsupported in a protected section: {line}")

    item: list[str] | None = None

    def close_item() -> None:
        nonlocal item
        if item is not None and not RUN_ID.search("\n".join(item)):
            problems.append(f"{finding}: {heading} bullet cites no run id: {chr(10).join(item).strip()}")
        item = None

    table_row = 0  # the position of this line in its run of table rows, 0 outside a table
    for i, (number, line) in enumerate(body):
        if line.startswith("|"):
            close_item()
            table_row += 1
            if HTML.search(line):
                unsupported(number, line)
                continue
            header = table_row == 1 and i + 1 < len(body) and body[i + 1][1].startswith("|") \
                and bool(SEPARATOR.match(body[i + 1][1])) and cells(line) == cells(body[i + 1][1])
            separator = table_row == 2 and bool(SEPARATOR.match(line)) and cells(line) == cells(body[i - 1][1])
            if not (header or separator or RUN_ID.search(line)):
                problems.append(f"{finding}: {heading} table row cites no run id: {line}")
            continue
        table_row = 0
        if not line.strip():
            close_item()
            continue
        if HTML.search(line) or BREAK.match(line):
            close_item()
            unsupported(number, line)
            continue
        if MARKER.match(line):
            close_item()
            if BLOCK.match(item_text(line)):
                unsupported(number, line)
            else:
                item = [line]
            continue
        if item is not None and line[:1] in (" ", "\t"):
            if BLOCK.match(line.strip()):
                close_item()
                unsupported(number, line)
            else:
                item.append(line)
            continue
        close_item()
        if not SUBHEADING.match(line):
            unsupported(number, line)
    close_item()
    return problems


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

    bodies: dict[str, list[list[tuple[int, str]]]] = {heading: [] for heading in SECTIONS}
    body: list[tuple[int, str]] | None = None
    for number, line in enumerate(lines, start=1):
        if misspelt(line):
            problems.append(f"{finding}:{number}: unsupported in a protected section: {line}")
        if line in SECTIONS:
            if bodies[line]:
                problems.append(f"{finding}:{number}: unsupported in a protected section: {line}")
            body = []
            bodies[line].append(body)
        elif line.startswith("## "):
            body = None
        elif body is not None:
            body.append((number, line))

    for heading in SECTIONS:
        if not bodies[heading]:
            problems.append(f"{finding}: missing section '{heading}'")
        for section in bodies[heading]:
            problems += check_body(finding, heading, section)
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
