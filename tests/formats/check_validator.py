#!/usr/bin/env python3
"""Regression tests for tools/validate_records.py: malformed documents are errors, not crashes.

A schema-invalid structure must never reach the semantic rules, which read fields the schema
guarantees (a file's `path`, `sha256`, `name`). `validate_document` returns the structural errors;
the CLI names the file, prints no traceback, and keeps processing the files after it. Guards R1
(review of PR #20): {"schema": "artifact-set/1", "files": [{}]} crashed with KeyError: 'path'.
Exit 0 when every check holds, 1 otherwise."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "validate_records.py"
sys.path.insert(0, str(ROOT / "tools"))
from validate_records import validate_document  # noqa: E402

MALFORMED = [
    {"schema": "artifact-set/1", "files": [{}]},
    {"schema": "evidence-manifest/1", "files": [None]},
]


def main():
    problems = []
    # Library: a malformed structure is an error, not an exception.
    for doc in MALFORMED:
        try:
            errors = validate_document(doc)
        except Exception as e:  # noqa: BLE001 - the point is that no exception escapes
            problems.append(f"validate_document({doc!r}) raised {type(e).__name__}: {e}")
            continue
        if not errors:
            problems.append(f"validate_document({doc!r}) returned no errors")
    # CLI: the malformed file is named, no traceback, and the next file still runs.
    scratch = ROOT / "scratch"
    scratch.mkdir(exist_ok=True)
    bad = scratch / "malformed-artifact-set.json"
    good = scratch / "valid-run.json"
    try:
        bad.write_text(json.dumps(MALFORMED[0]), encoding="utf-8")
        good.write_text(
            (ROOT / "formats" / "examples" / "valid" / "run-1--aborted-no-observations.json")
            .read_text(encoding="utf-8"), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(VALIDATOR), str(bad), str(good)],
                              capture_output=True, text=True)
        if proc.returncode != 1:
            problems.append(f"CLI on a malformed file exited {proc.returncode}, want 1")
        if str(bad) not in proc.stdout:
            problems.append("CLI did not name the malformed file on stdout")
        if "Traceback" in proc.stdout or "Traceback" in proc.stderr or proc.stderr:
            problems.append(f"CLI printed a traceback: {(proc.stdout + proc.stderr)!r}")
        if f"ok: {good}" not in proc.stdout:
            problems.append("CLI did not process the file after the malformed one")
    finally:
        bad.unlink(missing_ok=True)
        good.unlink(missing_ok=True)
        try:
            scratch.rmdir()
        except OSError:
            pass
    if problems:
        print("\n".join(problems))
        return 1
    print("ok: malformed documents are errors, not crashes; later files still run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
