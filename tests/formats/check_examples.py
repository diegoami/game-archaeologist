#!/usr/bin/env python3
"""Check the record formats in formats/ against their examples. Stdlib only.

1. Every schema uses only the JSON Schema keywords implemented in tools/validate_records.py. Any
   other keyword fails, so a schema can never be silently under-enforced.
2. Every formats/examples/valid/<schema>--<case>.json validates, and every
   formats/examples/invalid/<schema>--<case>.json fails with the error expected for it in
   formats/examples/expected-errors.json.
3. The rules a schema cannot express: an artifact set's id ends with the first 8 hex of its canonical
   manifest's sha256, and an evidence file's asset name is <sha256[:16]>-<name>.
4. The claim statuses in vocabulary/status.md equal those in docs/phase0/06-research.md §4.

The first three are the validator's own, in tools/validate_records.py, which game repositories fetch
instead of copying (formats/README.md, ADR-009). Exit 0 when everything holds, 1 otherwise.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORMATS = ROOT / "formats"
sys.path.insert(0, str(ROOT / "tools"))
from validate_records import semantic_errors, unknown_keywords, validate  # noqa: E402


def statuses(text, heading):
    """First-column backticked tokens of the first table after a heading line."""
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(heading))
    found, in_table = [], False
    for line in lines[start + 1:]:
        if line.startswith("|"):
            in_table = True
            m = re.match(r"^\|\s*`([^`]+)`\s*\|", line)
            if m:
                found.append(m.group(1))
        elif in_table:
            break
    return found


def main():
    problems, report = [], []
    schemas = {}
    for path in sorted(FORMATS.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        bad = unknown_keywords(schema)
        if bad:
            problems.append(f"{path.name}: keywords this checker does not implement: {bad}")
        schemas[path.name[: -len(".schema.json")]] = schema
    expected = json.loads((FORMATS / "examples" / "expected-errors.json").read_text(encoding="utf-8"))
    counts = {name: [0, 0] for name in schemas}
    for kind in ("valid", "invalid"):
        for path in sorted((FORMATS / "examples" / kind).glob("*.json")):
            stem = path.name.split("--")[0]
            if stem not in schemas:
                problems.append(f"{kind}/{path.name}: no schema {stem}.schema.json")
                continue
            doc = json.loads(path.read_text(encoding="utf-8"))
            errs = validate(doc, schemas[stem]) + semantic_errors(schemas[stem]["$id"], doc)
            if kind == "valid":
                counts[stem][0] += 1
                if errs:
                    problems.append(f"valid/{path.name}: unexpected errors {errs}")
            else:
                counts[stem][1] += 1
                want = expected.get(path.name)
                if want is None:
                    problems.append(f"invalid/{path.name}: no entry in expected-errors.json")
                elif not errs:
                    problems.append(f"invalid/{path.name}: validates, but should fail with '{want}'")
                elif not any(want in e for e in errs):
                    problems.append(f"invalid/{path.name}: fails, but not with '{want}': {errs}")
    for name, (valid, invalid) in counts.items():
        report.append(f"{name}: {valid} valid and {invalid} invalid examples checked")
        if not valid or not invalid:
            problems.append(f"{name}: needs at least one valid and one invalid example")
    vocab = statuses((ROOT / "vocabulary" / "status.md").read_text(encoding="utf-8"), "## Claim status")
    package = statuses((ROOT / "docs" / "phase0" / "06-research.md").read_text(encoding="utf-8"), "**Status**")
    if sorted(vocab) != sorted(package) or not vocab:
        problems.append(f"vocabulary/status.md statuses {vocab} != docs/phase0/06-research.md §4 {package}")
    else:
        report.append(f"claim statuses match docs/phase0/06-research.md §4: {', '.join(vocab)}")
    print("\n".join(report + problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
