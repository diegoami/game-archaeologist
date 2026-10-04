#!/usr/bin/env python3
"""Register an artifact set by hash, and check a copy against artifacts/known.json.

Artifact identity is the artifact-set/1 rule no schema can express (formats/README.md, "Two rules
no schema can express"): id is ``<label>-<h8>``, the first 8 hex of the sha256 of the *canonical
manifest*: the manifest without ``id`` and ``acquired``, ``files`` sorted by ``path``, serialised as
JSON with sorted keys, separators ``(",", ":")``, UTF-8, no ASCII escaping.

This tool never re-implements that rule: it imports ``canonical_set_hash``, ``validate_document``
and the schema loading from ``validate_records.py`` beside it (ADR-009). A game repository fetches
both files with ``formats/*.schema.json`` at a pinned commit and keeps that layout, so the tool runs
from its cache folder, not from the repository it serves. Only hashes and sizes are written; the
bytes stay on the registering machine (U2).

Commands:
    manifest <dir> --label --title --version --how [--when] [--note]
             [--runtime-write GLOB]... [--exclude GLOB]... [--writes GLOB]...
        Print the artifact-set/1 manifest for <dir>. ``--when`` defaults to today. Files matching
        a ``runtime_writes`` glob or an ``--exclude`` glob are left out of ``files``; ``--exclude``
        is not recorded. ``--writes`` is an alias of ``--runtime-write``.
    check (<dir> | --list <file>) <set-id> [--strict] [--known PATH]
        Re-hash <dir> (or read ``<sha256>  <bytes>  <path>`` listing lines) and compare it with the
        ``known.json`` entry for <set-id>. Exit 1 on any mismatch or missing file. A file outside
        the manifest that matches no ``runtime_writes`` glob is printed as ``unlisted: <path>``;
        that is a failure only with ``--strict``.
    validate [--known PATH]
        Check every ``known.json`` entry against the schema and recompute its id.

``known.json`` defaults to ``artifacts/known.json`` relative to the working directory, never to this
script. Errors are named lines on stdout and exit 1; usage errors exit 2; no input causes a
traceback.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from fnmatch import fnmatch
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_records  # noqa: E402
from validate_records import canonical_set_hash, validate_document  # noqa: E402

DEFAULT_KNOWN = "artifacts/known.json"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def matches_any(path, patterns):
    return any(fnmatch(path, pattern) for pattern in patterns)


def build_manifest(directory, label, title, version, how, when, note=None,
                   runtime_writes=(), excludes=()):
    """The artifact-set/1 manifest for <directory>, id computed by the imported canonical rule.

    Every regular file under <directory> is listed by its path relative to <directory>, so a listed
    path is never absolute and never leaves it. Files matching a runtime_writes or excludes glob are
    left out of ``files``; only runtime_writes is recorded."""
    directory = Path(directory)
    runtime_writes = list(runtime_writes)
    excludes = list(excludes)
    files = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(directory).as_posix()
        if matches_any(rel, runtime_writes) or matches_any(rel, excludes):
            continue
        files.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    acquired = {"how": how, "when": when}
    if note:
        acquired["note"] = note
    manifest = {
        "schema": "artifact-set/1",
        "title": title,
        "version": version,
        "acquired": acquired,
        "files": files,
        "runtime_writes": runtime_writes,
    }
    manifest["id"] = f"{label}-{canonical_set_hash(manifest)[:8]}"
    return manifest


def manifest_errors(manifest):
    """Errors for a manifest against the artifact-set/1 schema and semantic rules.

    ``validate_document`` checks the schema and that ``id`` is the canonical manifest's sha256
    prefix. A manifest that names one path twice is invalid too: ``hash_tree`` and ``compare`` key
    files by path, so which entry counts would depend on their order (PR #24 R2, swept)."""
    errors = list(validate_document(manifest))
    if isinstance(manifest, dict) and isinstance(manifest.get("files"), list):
        seen = set()
        for index, entry in enumerate(manifest["files"]):
            path = entry.get("path") if isinstance(entry, dict) else None
            if not isinstance(path, str):
                continue
            if path in seen:
                errors.append(f"$.files[{index}].path: duplicate path {path!r}")
            seen.add(path)
    return errors


def hash_tree(directory, manifest):
    """Observed ``{path: (bytes, sha256)}`` under <directory>, honouring the manifest's writes.

    A file not listed in ``files`` whose path matches a ``runtime_writes`` glob is a runtime write,
    not part of the set, and is left out (U21). A file that is listed is always observed, even when
    it also matches a glob."""
    directory = Path(directory)
    runtime_writes = manifest.get("runtime_writes", [])
    listed = {f["path"] for f in manifest.get("files", [])}
    observed = {}
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(directory).as_posix()
        if rel not in listed and matches_any(rel, runtime_writes):
            continue
        observed[rel] = (path.stat().st_size, sha256_file(path))
    return observed


def read_listing(path):
    """Parse ``<sha256>  <bytes>  <relative/path>`` lines into ``({path: (bytes, sha256)}, errors)``.

    A line that is not three whitespace-separated fields, or whose byte count is not an integer, is
    an error naming the line number; the rest of the file is still read. A path named on two lines is
    an error naming the later line: a later observation never silently replaces an earlier one
    (PR #24 R2)."""
    observed = {}
    problems = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 2)
        if len(parts) != 3:
            problems.append(f"line {number}: cannot parse {line!r}")
            continue
        digest, size, rel = parts
        try:
            size = int(size)
        except ValueError:
            problems.append(f"line {number}: bytes {parts[1]!r} is not an integer")
            continue
        if rel in observed:
            problems.append(f"line {number}: duplicate path {rel!r}, already listed on an earlier line")
            continue
        observed[rel] = (size, digest.lower())
    return observed, problems


def compare(observed, manifest, strict=False):
    """``(problems, unlisted)`` for observed files against a manifest.

    A listed file whose size or sha256 differs is a problem; a listed file that is absent is
    ``missing``; an observed file that is neither listed nor a runtime write is ``unlisted`` and is
    a problem only with ``strict``. A manifest that names one path twice is a problem: keying files by
    path would let a later entry replace an earlier one (PR #24 R2, swept)."""
    listed = {}
    problems = []
    for entry in manifest.get("files", []):
        path = entry["path"]
        if path in listed:
            problems.append(f"{path}: duplicate path in the manifest")
        listed[path] = (entry["bytes"], entry["sha256"])
    runtime_writes = manifest.get("runtime_writes", [])
    unlisted = []
    for rel, (size, digest) in sorted(observed.items()):
        if rel in listed:
            want_size, want_digest = listed[rel]
            if size != want_size:
                problems.append(f"{rel}: {size} bytes, expected {want_size}")
            if digest != want_digest:
                problems.append(f"{rel}: sha256 {digest}, expected {want_digest}")
        elif matches_any(rel, runtime_writes):
            continue
        else:
            unlisted.append(rel)
    for rel in sorted(set(listed) - set(observed)):
        problems.append(f"{rel}: missing")
    if strict and unlisted:
        problems.extend(f"unlisted: {rel}" for rel in unlisted)
    return problems, unlisted


def known_errors(known):
    """Errors for every entry of a parsed known.json document, as named lines; [] when all hold."""
    if not isinstance(known, dict):
        return ["known.json: document is not a JSON object"]
    sets = known.get("sets")
    if not isinstance(sets, list):
        return ["known.json: missing 'sets' list"]
    problems = []
    for index, entry in enumerate(sets):
        manifest = entry.get("manifest") if isinstance(entry, dict) else None
        if not isinstance(manifest, dict):
            problems.append(f"sets[{index}]: no manifest object")
            continue
        errors = manifest_errors(manifest)
        problems.extend(f"sets[{index}] ({manifest.get('id', '?')}): {error}" for error in errors)
    return problems


def find_set(known, set_id):
    for entry in known.get("sets", []):
        if isinstance(entry, dict):
            manifest = entry.get("manifest")
            if isinstance(manifest, dict) and manifest.get("id") == set_id:
                return entry
    return None


def load_known(path):
    """The parsed known.json at path. Raises OSError or ValueError naming a malformed document.

    Uses the validator's ``load_file``, so a duplicate JSON key (which value counts would depend on
    the reader) or a NaN/Infinity is a named error, exactly as for every other record document
    (PR #24 sweep: no later value silently replaces an earlier one)."""
    doc = validate_records.load_file(path)
    if not isinstance(doc, dict) or not isinstance(doc.get("sets"), list):
        raise ValueError("missing 'sets' list")
    return doc


def cmd_manifest(args):
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"{directory}: not a directory")
        return 1
    manifest = build_manifest(
        directory, args.label, args.title, args.version, args.how, args.when,
        note=args.note, runtime_writes=args.runtime_write, excludes=args.exclude,
    )
    errors = manifest_errors(manifest)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def cmd_check(args):
    set_id = args.source if args.list_path else args.set_id
    try:
        known = load_known(args.known)
    except (OSError, ValueError) as e:
        print(f"{args.known}: {e}")
        return 1
    entry = find_set(known, set_id)
    if entry is None:
        print(f"no known.json entry for {set_id}")
        return 1
    manifest = entry["manifest"]
    # Never trust the entry's own id: recompute the canonical identity before accepting a copy
    # (PR #24 R1). A forged id is a named error, not a pass.
    identity_errors = manifest_errors(manifest)
    if identity_errors:
        for error in identity_errors:
            print(f"{set_id}: {error}")
        return 1
    if args.list_path:
        try:
            observed, problems = read_listing(args.list_path)
        except (OSError, ValueError) as e:
            print(f"{args.list_path}: {e}")
            return 1
    else:
        if not Path(args.source).is_dir():
            print(f"{args.source}: not a directory")
            return 1
        observed, problems = hash_tree(args.source, manifest), []
    compared, unlisted = compare(observed, manifest, strict=args.strict)
    problems = problems + compared
    if not args.strict:
        for rel in unlisted:
            print(f"unlisted: {rel}")
    for problem in problems:
        print(problem)
    failed = bool(problems) or (args.strict and bool(unlisted))
    if not failed:
        print(f"ok: {set_id}")
    return 1 if failed else 0


def cmd_validate(args):
    try:
        known = load_known(args.known)
    except (OSError, ValueError) as e:
        print(f"{args.known}: {e}")
        return 1
    problems = known_errors(known)
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print(f"known.json ok ({len(known['sets'])} sets)")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="register_artifact.py", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest", help="print the artifact-set/1 manifest for a directory")
    manifest.add_argument("directory")
    manifest.add_argument("--label", required=True)
    manifest.add_argument("--title", required=True)
    manifest.add_argument("--version", required=True)
    manifest.add_argument("--how", required=True)
    manifest.add_argument("--when", default=datetime.date.today().isoformat())
    manifest.add_argument("--note")
    manifest.add_argument("--runtime-write", "--writes", dest="runtime_write", action="append",
                          default=[], metavar="GLOB",
                          help="a glob of files the runtime creates or changes; repeatable")
    manifest.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                          help="a glob of files to leave out of files and not record; repeatable")
    manifest.set_defaults(func=cmd_manifest)

    check = commands.add_parser("check", help="check a directory or listing against a known set")
    check.add_argument("--list", dest="list_path", metavar="FILE",
                       help="read a '<sha256>  <bytes>  <path>' listing instead of a directory")
    check.add_argument("--strict", action="store_true", help="an unlisted file is a failure")
    check.add_argument("--known", default=DEFAULT_KNOWN, metavar="PATH")
    check.add_argument("source", help="<dir>, or <set-id> when --list is given")
    check.add_argument("set_id", nargs="?", help="<set-id> when a <dir> is given")
    check.set_defaults(func=cmd_check)

    validate = commands.add_parser("validate", help="validate every known.json entry")
    validate.add_argument("--known", default=DEFAULT_KNOWN, metavar="PATH")
    validate.set_defaults(func=cmd_validate)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check" and not args.list_path and args.set_id is None:
        parser.error("check needs (<dir> | --list <file>) <set-id>")
    try:
        return args.func(args)
    except Exception as e:  # noqa: BLE001 - no input may produce a traceback
        print(f"internal error: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
