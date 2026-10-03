#!/usr/bin/env python3
"""Check the record formats in formats/ against their examples. Stdlib only.

1. Every schema uses only the JSON Schema keywords implemented below. Any other keyword fails, so
   a schema can never be silently under-enforced.
2. Every formats/examples/valid/<schema>--<case>.json validates, and every
   formats/examples/invalid/<schema>--<case>.json fails with the error expected for it in
   formats/examples/expected-errors.json.
3. The rules a schema cannot express: an artifact set's id ends with the first 8 hex of its canonical
   manifest's sha256, and an evidence file's asset name is <sha256[:16]>-<name>.
4. The claim statuses in vocabulary/status.md equal those in docs/phase0/06-research.md §4.

Exit 0 when everything holds, 1 otherwise.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORMATS = ROOT / "formats"
KEYWORDS = {"$schema", "$id", "title", "description", "type", "required", "properties",
            "additionalProperties", "items", "enum", "const", "pattern", "minItems", "minimum",
            "minLength", "anyOf"}
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def type_ok(value, name):
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES[name])


def unknown_keywords(schema, where="#"):
    """Keywords this validator does not implement, anywhere in the schema."""
    found = [f"{where}: {k}" for k in schema if k not in KEYWORDS]
    for k, sub in schema.get("properties", {}).items():
        found += unknown_keywords(sub, f"{where}/properties/{k}")
    for key in ("items", "additionalProperties"):
        if isinstance(schema.get(key), dict):
            found += unknown_keywords(schema[key], f"{where}/{key}")
    for i, sub in enumerate(schema.get("anyOf", [])):
        found += unknown_keywords(sub, f"{where}/anyOf/{i}")
    return found


def validate(value, schema, path="$"):
    """Errors for value against schema, as 'path: message' strings."""
    errors = []
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(type_ok(value, n) for n in names):
            return [f"{path}: expected type {'|'.join(names)}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must be {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in {schema['enum']}")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than {schema['minLength']}")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):  # `$` also matches before a trailing newline
            errors.append(f"{path}: does not match pattern {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for i, item in enumerate(value):
                errors += validate(item, schema["items"], f"{path}[{i}]")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property '{key}'")
        for key, item in value.items():
            if key in props:
                errors += validate(item, props[key], f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: additional property '{key}' not allowed")
            elif isinstance(schema.get("additionalProperties"), dict):
                errors += validate(item, schema["additionalProperties"], f"{path}.{key}")
    if "anyOf" in schema and not any(not validate(value, sub, path) for sub in schema["anyOf"]):
        errors.append(f"{path}: matches none of anyOf")
    return errors


def canonical_set_hash(manifest):
    """sha256 of the canonical manifest: without id and acquired, files sorted by path, JSON with
    sorted keys and separators (',', ':'), UTF-8."""
    body = {k: v for k, v in manifest.items() if k not in ("id", "acquired")}
    body["files"] = sorted(body.get("files", []), key=lambda f: f["path"])
    text = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def semantic_errors(schema_id, doc):
    errors = []
    if schema_id == "artifact-set/1" and isinstance(doc.get("files"), list):
        want = canonical_set_hash(doc)[:8]
        if not str(doc.get("id", "")).endswith("-" + want):
            errors.append(f"$.id: hash suffix is not {want}, the canonical manifest's sha256 prefix")
    if schema_id == "evidence-manifest/1":
        for i, f in enumerate(doc.get("files", [])):
            want = f"{f.get('sha256', '')[:16]}-{f.get('name', '')}"
            if f.get("asset") != want:
                errors.append(f"$.files[{i}].asset: must be {want}")
    return errors


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
