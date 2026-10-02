#!/usr/bin/env python3
"""Fail if a relative link in a tracked Markdown file points at a file that does not exist, or a
tracked JSON file does not parse. Web links and in-page anchors are not checked. Exit 0 clean, 1 broken."""
import json
import re
import subprocess
import sys
from pathlib import Path

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
files = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard"], cwd=root, text=True).split()
problems = []
for name in files:
    path = root / name
    if not path.is_file():
        continue
    if name.endswith(".json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except ValueError as e:
            problems.append(f"{name}: invalid JSON: {e}")
    if not name.endswith(".md"):
        continue
    in_fence = False
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if in_fence:
            continue
        for target in LINK.findall(line):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            target = target.split("#", 1)[0]
            if target and not (path.parent / target).exists():
                problems.append(f"{name}:{n}: broken link {target}")
print("\n".join(problems) if problems else f"links and JSON ok ({len(files)} files)")
sys.exit(1 if problems else 0)
