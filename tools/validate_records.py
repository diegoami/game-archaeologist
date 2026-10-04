#!/usr/bin/env python3
"""Validate record documents against the schemas in formats/. Stdlib only, Python >= 3.11.

A document names its format in its top-level `schema` field (artifact-set/1, run/1, ...), which
equals the `$id` of `formats/<name>-<v>.schema.json`. This module finds the schemas in `formats/`
beside its own parent directory, so a game repository that fetches `tools/validate_records.py` and
`formats/*.schema.json` at the pinned commit, keeping that layout, runs the same rules.

It holds the keyword whitelist, `validate`, `canonical_set_hash` and `semantic_errors`, moved
here from `tests/formats/check_examples.py` with their behaviour unchanged. Game repositories'
helpers import those names, so their signatures do not change (formats/README.md, ADR-009).

Command line: `python3 tools/validate_records.py <file.json>...`. For each file it prints `ok:
<path>`, or one line per error as `<path>: <error>`. It exits 0 when every file is valid and 1
otherwise. A file that is not JSON, or has no `schema` or an unknown one, is an error for that file,
not a crash.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

FORMATS = Path(__file__).resolve().parent.parent / "formats"
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


_SCHEMAS = None


def load_schemas():
    """The schemas in formats/, keyed by their `$id`.

    Refuses a schema that uses a keyword this validator does not implement, raising ValueError that
    names the schema file and the keyword, so a schema can never be silently under-enforced."""
    global _SCHEMAS
    if _SCHEMAS is None:
        schemas = {}
        for path in sorted(FORMATS.glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            bad = unknown_keywords(schema)
            if bad:
                raise ValueError(f"{path.name}: keywords this validator does not implement: {bad}")
            schemas[schema["$id"]] = schema
        _SCHEMAS = schemas
    return _SCHEMAS


def validate_document(doc):
    """Errors for one parsed record document, as 'path: message' strings; [] when valid.

    Picks the schema from formats/ whose `$id` equals the document's top-level `schema` field. A
    missing or unknown `schema` is an error. Raises ValueError when a schema uses a keyword this
    validator does not implement (it refuses to use it rather than under-enforce it)."""
    if not isinstance(doc, dict):
        return ["$: document is not a JSON object"]
    schema_id = doc.get("schema")
    if not isinstance(schema_id, str) or not schema_id:
        return ["$.schema: missing"]
    schema = load_schemas().get(schema_id)
    if schema is None:
        return [f"$.schema: unknown schema {schema_id!r}"]
    return validate(doc, schema) + semantic_errors(schema_id, doc)


def validate_file(path):
    """Print the result for one file; return True when it is valid."""
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"{path}: {e}")
        return False
    errors = validate_document(doc)
    if errors:
        for error in errors:
            print(f"{path}: {error}")
        return False
    print(f"ok: {path}")
    return True


def main(argv=None):
    paths = sys.argv[1:] if argv is None else list(argv)
    if not paths:
        print("usage: validate_records.py <file.json>...")
        return 2
    try:
        load_schemas()
    except ValueError as e:
        for path in paths:
            print(f"{path}: {e}")
        return 1
    valid = True
    for path in paths:
        if not validate_file(path):
            valid = False
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
