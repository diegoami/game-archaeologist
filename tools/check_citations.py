#!/usr/bin/env python3
"""Check a finding's citations.

`python3 tools/check_citations.py <finding.md>` fails (exit 1) when a run id (`E<nnn>-r<nnnn>`)
anywhere in the finding has no record under `runs/E<nnn>/`, or when a claim in `## Answer` or
`## Inferences` cites no run id. Exit 0 otherwise. `--runs <dir>` checks against another records
directory; without it the records live in `runs/` under the working directory, never under this
script's directory, so a game repository that fetches this file into a cache folder still checks
its own records (ADR-009).

A static claim cites its evidence as `static:<path>[:<line>]` anywhere in the finding (U26), and
such a token counts as a citation in `## Answer` and `## Inferences` exactly as a run id does. The
path must be a tracked file (or a directory with tracked files under it), resolve inside the
repository root, and, with `:line`, be a file with at least that many lines. `--root <dir>` names
the repository root, default the working directory, never this script's directory. A root that is
not a git repository, or a `git` that is missing, is one named error and exit 1.

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
error. Two more errors hold for every heading anywhere in the file (the owner's decisions U27 and
U28, 2026-10-04). A heading is a line starting with `#` after any blockquote `>`s, list markers and
whitespace, or a setext heading (the run of non-blank lines above a `=` or `-` underline). Its raw
text is entity-decoded (`html.unescape`), NFKC-normalised, casefolded and reduced to its letters (`str.isalpha`); nothing else is removed and no rendering is modelled. The
heading is the named error when its letters contain `answer` or `inferences` and its line is not
exactly `## Answer` or `## Inferences`, and when its letters come from more than one Unicode script
(the first word of each letter's `unicodedata.name`), as look-alike letters do (#28). Lines are split
only where Markdown splits them (`\n`, `\r\n`, `\r`), never at the other separators
`str.splitlines` knows.

HTML headings are banned in findings (the owner's decision U30, 2026-10-04, replacing U29): any line
containing `<h1` to `<h6`, in any case, anywhere in the file (a fenced code block included), is the
named error. Nothing is parsed or matched across lines.

Any ATX or setext heading, anywhere in the file, whose text contains `<`, `[` or `$` is the named
error too (the owner's decision U31, 2026-10-04). Tags, links, images, autolinks, comments and math
all start with one of them, so no markup can add letters that split a section's name past U28.

Any input that cannot be read is a named error, never a traceback.

Adapted from diegoami/toy-archaeology tools/check_citations.py at a3056ff through
diegoami/goal2-archaeology's copy.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

# A run id, bounded by anything but a letter or digit: `_E001-r0001_` (emphasis) is one, which a
# `\b` pattern missed because `_` is a word character.
RUN_ID = re.compile(r"(?<![A-Za-z0-9])E[0-9]{3,}-r[0-9]{4,}(?![A-Za-z0-9])")
# A static citation (U26), starting at the beginning of a line or after a character that is not a
# letter, a digit or `_`, as a run id is. Its argument is the run of non-space characters after the
# colon; trailing punctuation and backticks are not part of it.
STATIC = re.compile(r"(?<![A-Za-z0-9_])static:(?P<arg>\S*)")
STATIC_TRAILING = "`.,;:)]}'\"*"
# The argument in full: one or more `[A-Za-z0-9_.-]` segments joined by `/`, an optional trailing
# `/`, and an optional `:<line>` with no leading zero. `.`/`..` segments and a leading `/` are
# checked after the match, because the segment character class admits them.
STATIC_ARG = re.compile(
    r"(?P<path>(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+/?)"
    r"(?::(?P<line>0|[1-9][0-9]*))?")
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
# U27/U28: the heading lines. An ATX heading is a line whose first character after blockquote `>`s,
# list markers and whitespace is `#`; a setext underline is a line of `=` or `-` after the same
# prefixes. U30: any line containing `<h1` to `<h6`, in any case, is an error on its own.
ATX_START = re.compile(r"^[ \t>]*(?:(?:[-*+]|\d{1,9}[.)])[ \t]+[ \t>]*)*#")
SETEXT_UNDERLINE = re.compile(r"^[ \t>]*(?:=+|-+)[ \t]*$")
H_OPEN = re.compile(r"<h[1-6]", re.IGNORECASE)
# U31: what a heading's text may not contain, as every kind of inline markup that adds letters
# (a tag, a comment, an autolink, a link, an image, math) starts with one of them.
MARKUP = re.compile(r"[<\[$]")
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


def heading_letters(text: str) -> str:
    """The letters of a heading's raw text (U28): entities decoded, NFKC-normalised, casefolded,
    and only the characters `str.isalpha` keeps. Nothing else is removed."""
    text = unicodedata.normalize("NFKC", html.unescape(text)).casefold()
    return "".join(c for c in text if c.isalpha())


def script(letter: str) -> str:
    """A letter's script: the first word of its Unicode name (`LATIN`, `CYRILLIC`, `GREEK`)."""
    return unicodedata.name(letter, "UNNAMED").split()[0]


def heading_refused(text: str, line: str) -> bool:
    """Whether a heading whose raw text is `text`, starting at `line`, is a named error (U28): its
    letters contain a section's name and the line is not exactly that section's heading, or they
    come from more than one script."""
    letters = heading_letters(text)
    if line not in SECTIONS and any(name in letters for name in NAMES):
        return True
    return len({script(c) for c in letters}) > 1


def refused_headings(lines: list[str]) -> list[int]:
    """The 0-based indexes of the lines that start a refused heading: an ATX heading or a setext
    heading, whose text is the run of non-blank lines above its underline, refused under U28; and
    every line containing `<h1`..`<h6`, refused whatever it says (U30). An ATX or setext heading
    whose text contains `<`, `[` or `$` is refused whatever its letters (U31)."""
    found: set[int] = set()
    for i, line in enumerate(lines):
        if ATX_START.match(line) and (MARKUP.search(line) or heading_refused(line, line)):
            found.add(i)
        if SETEXT_UNDERLINE.match(line) and i > 0 and lines[i - 1].strip(" \t>"):
            start = i - 1
            while start > 0 and lines[start - 1].strip(" \t>"):
                start -= 1
            text = "\n".join(lines[start:i])
            if MARKUP.search(text) or heading_refused(text, lines[start]):
                found.add(start)
        if H_OPEN.search(line):
            found.add(i)
    return sorted(found)


def has_citation(text: str) -> bool:
    """Whether a claim's text holds a run id or a static citation token (U26)."""
    return RUN_ID.search(text) is not None or STATIC.search(text) is not None


def line_count(content: str) -> int:
    """The number of lines in a file's text: Markdown's line breaks, no phantom line after a
    trailing newline."""
    if content == "":
        return 0
    lines = re.split(r"\r\n|\r|\n", content)
    if lines[-1] == "":
        lines.pop()
    return len(lines)


def load_tracked(root: Path) -> tuple[set[str], str | None]:
    """The repository's tracked paths, or a named error when `root` is no git repository or `git`
    is missing. Paths are decoded with `os.fsdecode`, so a name that is not UTF-8 is still one."""
    try:
        result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True)
    except FileNotFoundError:
        return set(), f"{root}: git is not available"
    if result.returncode != 0:
        return set(), f"{root}: not a git repository"
    return {os.fsdecode(name) for name in result.stdout.split(b"\0") if name}, None


def static_problems(lines: list[str], finding: Path, root: Path,
                    tracked: set[str]) -> list[str]:
    """The problems of every `static:` token in the finding (U26): a token that is not
    `<path>[:<line>]`, a path that is not tracked, resolves outside the root, or names a line that
    the file does not have."""
    problems = []
    root_resolved = root.resolve()

    def problem(number: int, text: str) -> None:
        problems.append(f"{finding}:{number}: {text}")

    for number, line in enumerate(lines, start=1):
        for match in STATIC.finditer(line):
            raw = match.group(0)
            argument = match.group("arg").rstrip(STATIC_TRAILING)
            parsed = STATIC_ARG.fullmatch(argument)
            if parsed is None:
                problem(number, f"malformed static citation: {raw}")
                continue
            path = parsed.group("path")
            clean = path.rstrip("/")
            if any(segment in (".", "..") for segment in clean.split("/")):
                problem(number, f"malformed static citation: {raw}")
                continue
            token = f"static:{argument}"
            under = any(t.startswith(clean + "/") for t in tracked)
            if path.endswith("/"):
                directory, tracked_here = True, under
            else:
                directory = clean not in tracked and under
                tracked_here = clean in tracked or under
            if not tracked_here:
                problem(number, f"static citation {token}: no tracked path {clean}")
                continue
            target = root / clean
            try:
                resolved = target.resolve()
            except (OSError, RuntimeError) as e:  # noqa: BLE001 - no input may traceback
                problem(number, f"static citation {token}: cannot resolve {clean}: {e}")
                continue
            if not resolved.is_relative_to(root_resolved):
                problem(number, f"static citation {token}: {clean} resolves outside the repository"
                                 " root")
                continue
            line_number = parsed.group("line")
            if line_number is None:
                continue
            if directory:
                problem(number, f"static citation {token}: {clean} is a directory")
                continue
            if not target.is_file():
                problem(number, f"static citation {token}: {clean} is not a file")
                continue
            try:
                content = target.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001 - no input may traceback
                problem(number, f"static citation {token}: cannot read {clean}:"
                                 f" {type(e).__name__}")
                continue
            count = line_count(content)
            wanted = int(line_number)
            if wanted < 1 or wanted > count:
                problem(number, f"static citation {token}: line {wanted} is outside {clean}"
                                 f" (1..{count})")
    return problems


def check_body(finding: Path, heading: str, body: list[tuple[int, str]]) -> list[str]:
    """The problems of one protected section's body, given as (line number, line) pairs."""
    problems = []

    def unsupported(number: int, line: str) -> None:
        problems.append(f"{finding}:{number}: unsupported in a protected section: {line}")

    item: list[str] | None = None

    def close_item() -> None:
        nonlocal item
        if item is not None and not has_citation("\n".join(item)):
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
            if not (header or separator or has_citation(line)):
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


def check(finding: Path, runs: Path, root: Path) -> list[str]:
    if not finding.is_file():
        return [f"{finding}: no such file"]
    text = finding.read_text(encoding="utf-8")
    tracked, git_problem = load_tracked(root)
    if git_problem is not None:
        return [git_problem]
    lines = re.split(r"\r\n|\r|\n", text)
    problems: list[str] = []

    for run_id in sorted(set(RUN_ID.findall(text))):
        experiment = run_id.split("-", 1)[0]
        if not (runs / experiment / f"{run_id}.json").is_file():
            problems.append(f"{finding}: cites missing run {run_id} (no {runs / experiment / f'{run_id}.json'})")

    problems += static_problems(lines, finding, root, tracked)

    bodies: dict[str, list[list[tuple[int, str]]]] = {heading: [] for heading in SECTIONS}
    body: list[tuple[int, str]] | None = None
    for index in refused_headings(lines):
        problems.append(f"{finding}:{index + 1}: unsupported in a protected section: {lines[index]}")
    for number, line in enumerate(lines, start=1):
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
    parser.add_argument("--root", type=Path, default=None,
                        help="the repository root (default: the working directory)")
    args = parser.parse_args(argv)
    runs = args.runs if args.runs is not None else Path.cwd() / "runs"
    root = args.root if args.root is not None else Path.cwd()
    try:
        problems = check(args.finding, runs, root)
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
