#!/usr/bin/env python3
"""Self-test for tools/check_links.py's code-span handling.

A backslash-escaped backtick opens no span, so a broken link immediately after it is a real link
and the checker must report it. The fixture cannot be tracked as a `.md`: `check_links.py` scans
every Markdown file, so a permanently broken link in one would fail the repo-wide check. This test
copies the fixture to `scratch/` as a `.md`, runs the checker, and asserts the report, then removes
it. Exit 0 when the checker reports the link, 1 otherwise."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "escaped-backtick.fixture"
TARGET = "missing-escaped-backtick.md"


def main():
    scratch = ROOT / "scratch"
    scratch.mkdir(exist_ok=True)
    live = scratch / "escaped-backtick.md"
    try:
        shutil.copyfile(FIXTURE, live)
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "check_links.py")],
                              cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 1 or f"broken link {TARGET}" not in proc.stdout:
            print(f"FAIL: a broken link after a backslash-escaped backtick was not reported "
                  f"(checker exit {proc.returncode})")
            print(proc.stdout, end="")
            return 1
        print(f"ok: a broken link after a backslash-escaped backtick is reported ({TARGET})")
        return 0
    finally:
        live.unlink(missing_ok=True)
        try:
            scratch.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
