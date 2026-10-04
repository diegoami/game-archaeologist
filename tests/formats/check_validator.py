#!/usr/bin/env python3
"""Regression tests for tools/validate_records.py: no input makes it raise or stop a batch.

- A schema-invalid structure never reaches the semantic rules, which read fields the schema
  guarantees (PR #20 R1: {"schema": "artifact-set/1", "files": [{}]} crashed with KeyError).
- A string holding a lone surrogate is an explicit error: the document cannot be encoded as UTF-8,
  so it has no canonical id (PR #20 R2: an artifact-set title "\\ud800" crashed canonical_set_hash).
- Any unexpected exception while checking a document becomes a named error for that document, and
  the CLI goes on to the next file (the class behind R1 and R2), shown by forcing one.
The CLI names the bad file, prints no traceback, and still reports `ok:` for a valid file after it.
Exit 0 when every check holds, 1 otherwise."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "validate_records.py"
sys.path.insert(0, str(ROOT / "tools"))
import validate_records  # noqa: E402
from validate_records import validate_document  # noqa: E402

VALID = ROOT / "formats" / "examples" / "valid"
GOOD = VALID / "run-1--aborted-no-observations.json"


def surrogate_set():
    """The valid toy artifact set with a lone-surrogate title, structurally valid."""
    doc = json.loads((VALID / "artifact-set-1--toy.json").read_text(encoding="utf-8"))
    doc["title"] = "\ud800"
    return doc


MALFORMED = {
    "files-[{}]": {"schema": "artifact-set/1", "files": [{}]},
    "files-[null]": {"schema": "evidence-manifest/1", "files": [None]},
    "surrogate-title": surrogate_set(),
    "surrogate-key": {"schema": "run/1", "\udc80": 1},
}

# Files that are not JSON a reader can take one way only: each is an error naming the file.
RAW = {
    "nan": (b'{"schema": "run/1", "x": NaN}', "NaN is not JSON"),
    "infinity": (b'{"schema": "run/1", "x": -Infinity}', "-Infinity is not JSON"),
    "duplicate-key": (b'{"schema": "nope/1", "schema": "run/1"}', "duplicate key 'schema'"),
    "deep": (b"[" * 100000 + b"]" * 100000, "nested too deeply to parse"),
}

# Runs the CLI in a child with one internal function forced to raise on its first call (the first
# file), as an unknown defect would; later calls run the real function.
FORCED = """
import sys
sys.path.insert(0, {tools!r})
import validate_records as v
real, calls = getattr(v, {name!r}), []
def boom(*a, **k):
    calls.append(1)
    if len(calls) == 1:
        raise RuntimeError("forced")
    return real(*a, **k)
setattr(v, {name!r}, boom)
sys.exit(v.main(sys.argv[1:]))
"""


def run_cli(args, code=None, env=None):
    cmd = [sys.executable, str(VALIDATOR)] if code is None else [sys.executable, "-c", code]
    return subprocess.run(cmd + [str(a) for a in args], capture_output=True, text=True,
                          env=env, errors="replace")


def check_cli(label, proc, bad, problems, want=None):
    if proc.returncode != 1:
        problems.append(f"{label}: CLI exited {proc.returncode}, want 1")
    if f"{bad}: " not in proc.stdout:
        problems.append(f"{label}: CLI did not name {bad.name} on stdout")
    if want and want not in proc.stdout:
        problems.append(f"{label}: CLI output lacks {want!r}")
    if "Traceback" in proc.stdout or proc.stderr:
        problems.append(f"{label}: CLI printed a traceback: {(proc.stdout + proc.stderr)[-300:]!r}")
    if f"ok: {GOOD}" not in proc.stdout:
        problems.append(f"{label}: CLI did not process the valid file after the bad one")


def main():
    problems = []
    # Library: malformed documents are errors, not exceptions.
    for label, doc in MALFORMED.items():
        try:
            errors = validate_document(doc)
        except Exception as e:  # noqa: BLE001 - the point is that no exception escapes
            problems.append(f"library {label}: raised {type(e).__name__}: {e}")
            continue
        if not errors:
            problems.append(f"library {label}: returned no errors")
        elif label.startswith("surrogate") and not any("lone surrogate" in e for e in errors):
            problems.append(f"library {label}: no explicit lone-surrogate error: {errors}")
    # Library: a forced unexpected exception is a named error, not an exception.
    real = validate_records.semantic_errors
    validate_records.semantic_errors = lambda *a: 1 / 0
    try:
        errors = validate_document(json.loads(GOOD.read_text(encoding="utf-8")))
        if errors != ["$: internal error on malformed input: ZeroDivisionError: division by zero"]:
            problems.append(f"library forced exception: got {errors!r}")
    except Exception as e:  # noqa: BLE001
        problems.append(f"library forced exception: raised {type(e).__name__}: {e}")
    finally:
        validate_records.semantic_errors = real

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for label, doc in MALFORMED.items():
            bad = tmp / f"{label}.json"
            bad.write_text(json.dumps(doc), encoding="utf-8")  # ASCII escapes, as json.dumps writes
            want = "lone surrogate" if label.startswith("surrogate") else None
            check_cli(f"CLI {label}", run_cli([bad, GOOD]), bad, problems, want)
            if label == "surrogate-key":
                ascii_env = dict(os.environ, PYTHONIOENCODING="ascii")
                check_cli("CLI surrogate-key on an ASCII terminal",
                          run_cli([bad, GOOD], env=ascii_env), bad, problems, "lone surrogate")
        for label, (raw, want) in RAW.items():
            bad = tmp / f"{label}.json"
            bad.write_bytes(raw)
            check_cli(f"CLI {label}", run_cli([bad, GOOD]), bad, problems, want)
        # CLI: a forced unexpected exception, inside a document's check and around a whole file.
        bad = tmp / "forced.json"
        bad.write_text(GOOD.read_text(encoding="utf-8"), encoding="utf-8")
        for name in ("semantic_errors", "load_file"):
            code = FORCED.format(tools=str(ROOT / "tools"), name=name)
            check_cli(f"CLI forced {name}", run_cli([bad, GOOD], code), bad, problems,
                      "internal error on malformed input: RuntimeError: forced")
    if problems:
        print("\n".join(problems))
        return 1
    print("ok: malformed documents are errors, not crashes; later files still run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
