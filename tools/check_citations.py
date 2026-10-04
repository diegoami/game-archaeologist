#!/usr/bin/env python3
"""Check a finding's citations.

`python3 tools/check_citations.py <finding.md>` fails (exit 1) when a run id anywhere in the
finding has no record under `runs/E<nnn>/`, or when a bullet in `## Answer` or `## Inferences`
cites no run id. Exit 0 otherwise. `--runs <dir>` checks against another records directory; without
it the records live in `runs/` under the working directory, never under this script's directory, so
a game repository that fetches this file into a cache folder still checks its own records (ADR-009).

A bullet's indented continuation lines belong to it, so a run id on a wrapped line counts
(toy-archaeology#12). Any input that cannot be read is a named error, never a traceback.

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


def section_lines(lines: list[str], heading: str) -> list[str] | None:
    start = next((i for i, line in enumerate(lines) if line.strip() == heading), None)
    if start is None:
        return None
    body = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        body.append(line)
    return body


def bullets(lines: list[str]) -> list[str]:
    """Each bullet together with its indented continuation lines, not a new bullet."""
    found: list[str] = []
    current: list[str] | None = None
    for line in lines:
        if line.lstrip().startswith(("- ", "* ")):
            if current is not None:
                found.append("\n".join(current))
            current = [line]
        elif current is not None and line.strip() and line[:1] in (" ", "\t"):
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
        body = section_lines(lines, heading)
        if body is None:
            problems.append(f"{finding}: missing section '{heading}'")
            continue
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
