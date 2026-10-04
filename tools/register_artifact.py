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

Nothing is accepted unvalidated. Every manifest, from ``known.json`` or a library caller, goes
through ``manifest_errors`` (schema, canonical id, path form, no path twice); a ``known.json`` names
each id once; every listing line and every observation is checked field by field; a path is a set
path only if ``path_error`` accepts it (relative, POSIX, inside the directory); and a directory walk
reports, never follows, a symbolic link out of the directory.

``known.json`` defaults to ``artifacts/known.json`` relative to the working directory, never to this
script. Errors are named lines on stdout and exit 1; usage errors exit 2; no input causes a
traceback.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from fnmatch import fnmatch
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_records  # noqa: E402
from validate_records import canonical_set_hash, validate_document  # noqa: E402

DEFAULT_KNOWN = "artifacts/known.json"


LISTING_SHA256 = re.compile(r"[0-9a-fA-F]{64}")
LISTING_BYTES = re.compile(r"[0-9]+")
MANIFEST_SHA256 = re.compile(r"[0-9a-f]{64}")
DRIVE = re.compile(r"[A-Za-z]:")


class SetError(ValueError):
    """A directory that cannot be registered; ``problems`` holds one named line per cause."""

    def __init__(self, problems):
        super().__init__("; ".join(problems))
        self.problems = list(problems)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def matches_any(path, patterns):
    return any(fnmatch(path, pattern) for pattern in patterns)


def path_error(path):
    """Why ``path`` is not a set path, or None. The one path-form rule for manifests, listings and
    directory walks: a set path is relative to the set's directory and stays inside it.

    It is a non-empty string, encodable as UTF-8, POSIX (no backslash), not absolute, with no drive
    letter, and every ``/``-separated segment is non-empty and neither ``.`` nor ``..``. Each test is
    separate, so each one earns its own regression test (PR #24 round 2, R1)."""
    if not isinstance(path, str) or not path:
        return "not a non-empty string"
    try:
        path.encode("utf-8")
    except UnicodeEncodeError:
        return "not encodable as UTF-8"
    if path.startswith("/"):
        return "absolute path"
    if DRIVE.match(path):
        return "drive letter"
    if "\\" in path:
        return "backslash in path"
    segments = path.split("/")
    if ".." in segments:
        return "'..' segment leaves the directory"
    if "." in segments:
        return "'.' segment"
    if "" in segments:
        return "empty segment"
    return None


def manifest_errors(manifest):
    """Errors for a manifest; [] when it may be accepted. The one acceptance boundary: ``check``,
    ``validate``, ``manifest``, ``known_errors``, ``hash_tree`` and ``compare`` all go through it.

    ``validate_document`` checks the schema and that ``id`` is the canonical manifest's sha256
    prefix (PR #24 R1). Then every ``files[].path`` must pass ``path_error`` (round 2 R1), and no
    path may be named twice: ``hash_tree`` and ``compare`` key files by path, so which entry counted
    would depend on their order (round 1 R2)."""
    errors = list(validate_document(manifest))
    if isinstance(manifest, dict) and isinstance(manifest.get("files"), list):
        seen = set()
        for index, entry in enumerate(manifest["files"]):
            path = entry.get("path") if isinstance(entry, dict) else None
            if not isinstance(path, str):
                continue
            error = path_error(path)
            if error:
                errors.append(f"$.files[{index}].path: {error}: {path!r}")
            if path in seen:
                errors.append(f"$.files[{index}].path: duplicate path {path!r}")
            seen.add(path)
    return errors


def walk(directory):
    """``(files, problems)`` for <directory>: ``files`` is ``[(relative path, Path)]`` of every
    regular file in walk order, ``problems`` names what cannot be observed safely.

    Symbolic links are never followed out of <directory>: a link whose target resolves outside it,
    or that is broken, is a problem. A link to a regular file inside it is observed at the link's
    path; a link to a directory inside it is not descended (its files are observed at their own
    paths). A name that fails ``path_error`` (a backslash, say) and anything that is neither a
    regular file nor a directory (a FIFO, a socket) is a problem, never read."""
    root = Path(directory)
    root_real = Path(os.path.realpath(root))
    files, problems = [], []

    def visit(folder, prefix):
        try:
            entries = sorted(os.scandir(folder), key=lambda e: e.name)
        except OSError as e:
            problems.append(f"{prefix or './'}: cannot read the directory: {e.strerror}")
            return
        for entry in entries:
            rel = prefix + entry.name
            error = path_error(rel)
            if error:
                problems.append(f"{rel!r}: {error}")
                continue
            if entry.is_symlink():
                target = Path(os.path.realpath(entry.path))
                if not target.is_relative_to(root_real):
                    problems.append(f"{rel}: symbolic link to outside the directory, not followed")
                elif target.is_dir():
                    continue
                elif target.is_file():
                    files.append((rel, Path(entry.path)))
                else:
                    problems.append(f"{rel}: symbolic link to nothing or to a special file")
            elif entry.is_dir(follow_symlinks=False):
                visit(entry.path, rel + "/")
            elif entry.is_file(follow_symlinks=False):
                files.append((rel, Path(entry.path)))
            else:
                problems.append(f"{rel}: not a regular file or a directory")

    visit(root, "")
    return files, problems


def _hash(rel, path, problems):
    try:
        return path.stat().st_size, sha256_file(path)
    except OSError as e:
        problems.append(f"{rel}: cannot read: {e.strerror}")
        return None


def build_manifest(directory, label, title, version, how, when, note=None,
                   runtime_writes=(), excludes=()):
    """The artifact-set/1 manifest for <directory>, id computed by the imported canonical rule.

    Every regular file ``walk`` finds is listed by its path relative to <directory>. Files matching a
    runtime_writes or excludes glob are left out of ``files``; only runtime_writes is recorded.
    Raises ``SetError`` naming every problem ``walk`` reports (a link to outside, say): a directory
    that cannot be observed safely is never registered."""
    runtime_writes = list(runtime_writes)
    excludes = list(excludes)
    found, problems = walk(directory)
    files = []
    for rel, path in found:
        if matches_any(rel, runtime_writes) or matches_any(rel, excludes):
            continue
        hashed = _hash(rel, path, problems)
        if hashed:
            files.append({"path": rel, "bytes": hashed[0], "sha256": hashed[1]})
    if problems:
        raise SetError(problems)
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


def hash_tree(directory, manifest):
    """``(observed, problems)``: observed ``{path: (bytes, sha256)}`` under <directory>.

    The manifest is accepted first (``manifest_errors``); a manifest that is not accepted gives
    ``({}, its errors)`` and the directory is not read. A file not listed in ``files`` whose path
    matches a ``runtime_writes`` glob is a runtime write, not part of the set, and is left out (U21).
    A file that is listed is always observed, even when it also matches a glob. ``walk``'s problems
    (a link to outside the directory, say) are returned, never followed."""
    errors = manifest_errors(manifest)
    if errors:
        return {}, errors
    runtime_writes = manifest["runtime_writes"]
    listed = {f["path"] for f in manifest["files"]}
    found, problems = walk(directory)
    observed = {}
    for rel, path in found:
        if rel not in listed and matches_any(rel, runtime_writes):
            continue
        hashed = _hash(rel, path, problems)
        if hashed:
            observed[rel] = hashed
    return observed, problems


def read_listing(path):
    """Parse ``<sha256>  <bytes>  <relative/path>`` lines into ``({path: (bytes, sha256)}, errors)``.

    Each error names its line; the rest of the file is still read and the bad line is not observed.
    A line must be three whitespace-separated fields: a sha256 of 64 hex digits (upper case is read
    as the same digest, lower-cased), a byte count of decimal digits only (no sign), and a path that
    passes ``path_error``. A path named on two lines is an error naming the later line: a later
    observation never silently replaces an earlier one (PR #24 R2)."""
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
        if not LISTING_SHA256.fullmatch(digest):
            problems.append(f"line {number}: sha256 {digest!r} is not 64 hex digits")
            continue
        if not LISTING_BYTES.fullmatch(size):
            problems.append(f"line {number}: bytes {size!r} is not an integer")
            continue
        error = path_error(rel)
        if error:
            problems.append(f"line {number}: path {rel!r}: {error}")
            continue
        if rel in observed:
            problems.append(f"line {number}: duplicate path {rel!r}, already listed on an earlier line")
            continue
        observed[rel] = (int(size), digest.lower())
    return observed, problems


def observation_error(rel, value):
    """Why one observed ``path -> (bytes, sha256)`` entry cannot be compared, or None."""
    error = path_error(rel)
    if error:
        return f"{rel!r}: {error}"
    if not (isinstance(value, tuple) and len(value) == 2):
        return f"{rel}: observation is not (bytes, sha256)"
    size, digest = value
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        return f"{rel}: observed bytes {size!r} is not a non-negative integer"
    if not isinstance(digest, str) or not MANIFEST_SHA256.fullmatch(digest):
        return f"{rel}: observed sha256 {digest!r} is not 64 lower-case hex digits"
    return None


def compare(observed, manifest, strict=False):
    """``(problems, unlisted)`` for observed files against a manifest.

    The manifest is accepted first (``manifest_errors``): one that is not accepted (a forged id, a
    path named twice, a path that leaves the directory) gives ``(its errors, [])``, never a pass.
    Each observation must have a set path, a non-negative integer size and a lower-case sha256;
    one that does not is a problem and is not compared. A listed file whose size or sha256 differs
    is a problem; a listed file that is absent is ``missing``; an observed file that is neither
    listed nor a runtime write is ``unlisted`` and is a problem only with ``strict``."""
    errors = manifest_errors(manifest)
    if errors:
        return errors, []
    listed = {entry["path"]: (entry["bytes"], entry["sha256"]) for entry in manifest["files"]}
    runtime_writes = manifest["runtime_writes"]
    problems = []
    unlisted = []
    for rel, value in sorted(observed.items(), key=lambda item: str(item[0])):
        error = observation_error(rel, value)
        if error:
            problems.append(error)
            continue
        size, digest = value
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
    """Errors for every entry of a parsed known.json document, as named lines; [] when all hold.

    Every manifest goes through ``manifest_errors``, and no id may appear twice: ``check`` selects
    a set by id, so which entry counted would depend on their order."""
    if not isinstance(known, dict):
        return ["known.json: document is not a JSON object"]
    sets = known.get("sets")
    if not isinstance(sets, list):
        return ["known.json: missing 'sets' list"]
    problems = []
    first_index = {}
    for index, entry in enumerate(sets):
        manifest = entry.get("manifest") if isinstance(entry, dict) else None
        if not isinstance(manifest, dict):
            problems.append(f"sets[{index}]: no manifest object")
            continue
        set_id = manifest.get("id", "?")
        errors = manifest_errors(manifest)
        problems.extend(f"sets[{index}] ({set_id}): {error}" for error in errors)
        if isinstance(set_id, str) and set_id in first_index:
            problems.append(f"sets[{index}] ({set_id}): duplicate id, already at sets[{first_index[set_id]}]")
        first_index.setdefault(set_id, index)
    return problems


def select_set(known, set_id):
    """``(manifest, errors)`` for <set-id> in a parsed known.json: the manifest only when exactly
    one entry has that id and ``manifest_errors`` accepts it."""
    matches = [entry["manifest"] for entry in known.get("sets", [])
               if isinstance(entry, dict) and isinstance(entry.get("manifest"), dict)
               and entry["manifest"].get("id") == set_id]
    if not matches:
        return None, [f"no known.json entry for {set_id}"]
    if len(matches) > 1:
        return None, [f"{set_id}: {len(matches)} known.json entries have this id"]
    errors = manifest_errors(matches[0])
    if errors:
        return None, [f"{set_id}: {error}" for error in errors]
    return matches[0], []


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
    try:
        manifest = build_manifest(
            directory, args.label, args.title, args.version, args.how, args.when,
            note=args.note, runtime_writes=args.runtime_write, excludes=args.exclude,
        )
    except SetError as e:
        for problem in e.problems:
            print(problem)
        return 1
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
    # Never trust the entry: select_set accepts it only through manifest_errors, which recomputes
    # the canonical id (PR #24 R1) and checks every path's form (round 2 R1).
    manifest, errors = select_set(known, set_id)
    if errors:
        for error in errors:
            print(error)
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
        observed, problems = hash_tree(args.source, manifest)
    compared, unlisted = compare(observed, manifest, strict=args.strict)
    problems = problems + compared
    if not args.strict:
        for rel in unlisted:
            print(f"unlisted: {rel}")
    for problem in problems:
        print(problem)
    failed = bool(problems)  # compare already counts an unlisted file as a problem under --strict
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
    if args.command == "check" and args.list_path and args.set_id is not None:
        parser.error("check --list <file> takes one <set-id>, not a <dir> too")
    try:
        return args.func(args)
    except Exception as e:  # noqa: BLE001 - no input may produce a traceback
        print(f"internal error: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
