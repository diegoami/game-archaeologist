#!/usr/bin/env python3
"""Regression tests for tools/register_artifact.py. Stdlib only, no network and no game files.

They drive the library functions and the CLI over a temporary set whose runtime writes (*.sav,
*.bin) and excluded files (*.txt) are real files, so the U21 split, the sha256 comparison, the
--strict rule, the malformed-input errors and the manifest layout are each observed. Every guard at
the acceptance boundary (manifest, listing, observation, directory walk, known.json) has a case that
fails when only that guard is removed (PR #24 round 3). Every failure names its case. Exit 0 when
every case holds, 1 otherwise."""
import json
import os
import socket
import subprocess
import sys
import tempfile
from datetime import date
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import register_artifact as ra  # noqa: E402

TOOL = TOOLS / "register_artifact.py"

# Path forms a set path must refuse, each with the reason path_error must give for it alone.
BAD_PATHS = (
    ("/outside/a", "absolute path"),
    ("C:/a", "drive letter"),
    ("c:a", "drive letter"),
    ("a\\b", "backslash"),
    ("../a", "'..' segment"),
    ("a/../b", "'..' segment"),
    ("./a", "'.' segment"),
    ("a/./b", "'.' segment"),
    ("a//b", "empty segment"),
    ("a/", "empty segment"),
    ("", "not a non-empty string"),
    ("a\udcff", "not encodable as UTF-8"),
)
GOOD_PATHS = ("a", "dir/a.txt", "a..b", ".hidden", "a b", "...")


def case(problems, label, ok, detail=""):
    if not ok:
        problems.append(f"{label}: {detail}" if detail else label)


def call(problems, label, fn, *args, **kwargs):
    """fn(*args, **kwargs), or None with a named failure when it raises."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:  # noqa: BLE001 - a raise is the case failing, not the suite crashing
        problems.append(f"{label}: raised {type(e).__name__}: {e}")
        return None


def run(args, cwd=None):
    return subprocess.run([sys.executable, str(TOOL)] + [str(a) for a in args],
                          capture_output=True, text=True, cwd=cwd, errors="replace")


def no_traceback(problems, label, proc):
    out = proc.stdout + proc.stderr
    case(problems, label, "Traceback" not in out, f"traceback: {out[-300:]!r}")


def write_tree(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / "MANUAL.md").write_bytes(b"manual\n")
    (root / "game.pyz").write_bytes(b"payload\n")
    (root / "save.sav").write_bytes(b"save\n")
    (root / "state.bin").write_bytes(b"state\n")
    (root / "notes.txt").write_bytes(b"notes\n")
    return root


def with_files(manifest, files):
    """A copy of manifest with these files and its id recomputed by the canonical rule, so only a
    guard other than the id check can refuse it."""
    out = dict(manifest)
    out["files"] = files
    out["id"] = f"demo-{ra.canonical_set_hash(out)[:8]}"
    return out


def known_file(path, *manifests):
    path.write_text(json.dumps({"sets": [{"manifest": m} for m in manifests]}), encoding="utf-8")
    return path


def listing_of(path, manifest, extra=()):
    lines = [f"{f['sha256']}  {f['bytes']}  {f['path']}" for f in manifest["files"]]
    path.write_text("\n".join(lines + list(extra)) + "\n", encoding="utf-8")
    return path


def main():
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        d = write_tree(tmp / "set")
        m = ra.build_manifest(d, "demo", "Demo", "1", "generated", "1970-01-01",
                              note="a note", runtime_writes=["*.sav", "*.bin"],
                              excludes=["*.txt"])
        known = known_file(tmp / "known.json", m)
        check_build(problems, d, m)
        check_paths(problems)
        check_manifest_boundary(problems, tmp, m)
        check_compare(problems, d, m)
        check_listing(problems, tmp, m)
        check_walk(problems, tmp, m)
        check_known(problems, tmp, m)
        check_cli(problems, tmp, d, m, known)
    if problems:
        print("\n".join(problems))
        return 1
    print("ok: register_artifact.py manifest, check, validate and malformed input hold")
    return 0


def check_build(problems, d, m):
    """build_manifest: the U21 split, the id, the recorded acquisition and safe paths."""
    paths = [f["path"] for f in m["files"]]
    case(problems, "manifest lists the shipped files",
         paths == ["MANUAL.md", "game.pyz"], f"files {paths}")
    case(problems, "manifest excludes runtime_writes from files",
         not any(fnmatch(p, "*.sav") or fnmatch(p, "*.bin") for p in paths)
         and m["runtime_writes"] == ["*.sav", "*.bin"],
         f"files {paths} runtime_writes {m['runtime_writes']}")
    case(problems, "manifest excludes --exclude files and does not record them",
         not any(fnmatch(p, "*.txt") for p in paths) and "*.txt" not in m["runtime_writes"],
         f"files {paths} runtime_writes {m['runtime_writes']}")
    case(problems, "manifest id is the label plus the canonical hash prefix",
         m["id"] == f"demo-{ra.canonical_set_hash(m)[:8]}", f"id {m['id']}")
    case(problems, "manifest paths pass path_error",
         all(ra.path_error(p) is None for p in paths), f"paths {paths}")
    case(problems, "manifest records the acquisition and note",
         m["acquired"] == {"how": "generated", "when": "1970-01-01", "note": "a note"},
         f"acquired {m['acquired']}")
    case(problems, "manifest_errors accepts a built manifest", ra.manifest_errors(m) == [],
         f"errors {ra.manifest_errors(m)}")

    # hash_tree: an unlisted runtime write is left out; a listed file is always observed.
    (d / "new.sav").write_bytes(b"new\n")
    observed, walk_problems = ra.hash_tree(d, m)
    case(problems, "hash_tree ignores an unlisted runtime write",
         "new.sav" not in observed and "MANUAL.md" in observed and walk_problems == [],
         f"observed {sorted(observed)} problems {walk_problems}")
    (d / "new.sav").unlink()


def check_paths(problems):
    """path_error: each refused form gives its own reason, so each test is needed alone."""
    for path, reason in BAD_PATHS:
        error = ra.path_error(path)
        case(problems, f"path_error refuses {path!r} ({reason})",
             error is not None and reason in error, f"error {error!r}")
    for path in GOOD_PATHS:
        case(problems, f"path_error accepts {path!r}", ra.path_error(path) is None,
             f"error {ra.path_error(path)!r}")


def check_manifest_boundary(problems, tmp, m):
    """A manifest is accepted only through manifest_errors, by every entry point."""
    rest = m["files"][1:]
    first = m["files"][0]
    for path, reason in BAD_PATHS:
        if not path or reason == "not encodable as UTF-8":
            continue  # validate_document refuses these first (minLength; unencodable strings)
        bad = with_files(m, [dict(first, path=path)] + rest)
        errors = ra.manifest_errors(bad)
        case(problems, f"manifest_errors refuses a file path {path!r}",
             any(reason in e for e in errors), f"errors {errors}")
        observed = {f["path"]: (f["bytes"], f["sha256"]) for f in bad["files"]}
        probs, unlisted = call(problems, f"compare {path!r}", ra.compare, observed, bad,
                               strict=True) or ([], [])
        case(problems, f"compare refuses a manifest whose file path is {path!r}",
             any(reason in p for p in probs), f"problems {probs} unlisted {unlisted}")
        known_probs = ra.known_errors({"sets": [{"manifest": bad}]})
        case(problems, f"known_errors refuses a manifest whose file path is {path!r}",
             any(reason in p for p in known_probs), f"problems {known_probs}")

    # A forged id: the library refuses it as the CLI does (PR #24 R1).
    forged = dict(m, id="forged-00000000")
    listed = {f["path"]: (f["bytes"], f["sha256"]) for f in m["files"]}
    probs, _ = ra.compare(dict(listed), forged)
    case(problems, "compare refuses a forged manifest id",
         any("hash suffix" in p for p in probs), f"problems {probs}")
    observed, walk_problems = ra.hash_tree(tmp / "set", forged)
    case(problems, "hash_tree refuses a forged manifest id without reading the directory",
         observed == {} and any("hash suffix" in p for p in walk_problems),
         f"observed {sorted(observed)} problems {walk_problems}")
    manifest, errors = ra.select_set({"sets": [{"manifest": forged}]}, "forged-00000000")
    case(problems, "select_set refuses a forged manifest id",
         manifest is None and any("hash suffix" in e for e in errors), f"errors {errors}")

    # A path named twice, through the library: conflicting entries, both orders, each observation
    # (PR #24 round 2 R2). Keyed by path, a later entry would silently replace an earlier one.
    conflict = dict(first, sha256="0" * 64)
    for order, files in (("right then wrong", [first, conflict]),
                         ("wrong then right", [conflict, first])):
        twice = with_files(m, files + rest)
        for seen, entry in (("the right bytes", first), ("the wrong bytes", conflict)):
            observed = {f["path"]: (f["bytes"], f["sha256"]) for f in rest}
            observed[first["path"]] = (entry["bytes"], entry["sha256"])
            probs, _ = ra.compare(observed, twice)
            case(problems, f"compare refuses a manifest path named twice ({order}, {seen})",
                 any("duplicate path" in p for p in probs), f"problems {probs}")


def check_compare(problems, d, m):
    """compare: sha256, size, missing, unlisted, runtime writes and each observation's form."""
    listed = {f["path"]: (f["bytes"], f["sha256"]) for f in m["files"]}
    probs, unlisted = ra.compare(dict(listed), m)
    case(problems, "compare accepts a matching tree", probs == [] and unlisted == [],
         f"problems {probs} unlisted {unlisted}")
    changed = dict(listed)
    size, digest = changed["game.pyz"]
    changed["game.pyz"] = (size, "0" * 64)
    probs, _ = ra.compare(changed, m)
    case(problems, "compare detects a changed sha256",
         any("game.pyz" in p and "sha256" in p for p in probs), f"problems {probs}")
    changed["game.pyz"] = (size + 1, digest)
    probs, _ = ra.compare(changed, m)
    case(problems, "compare detects a changed size",
         any("game.pyz" in p and "bytes" in p for p in probs), f"problems {probs}")
    missing = {k: v for k, v in listed.items() if k != "game.pyz"}
    probs, _ = ra.compare(missing, m)
    case(problems, "compare reports a missing file",
         any("game.pyz" in p and "missing" in p for p in probs), f"problems {probs}")
    extra = dict(listed)
    extra["x.txt"] = (2, "1" * 64)
    probs, unlisted = ra.compare(extra, m)
    case(problems, "compare marks an extra file unlisted, not a problem",
         probs == [] and unlisted == ["x.txt"], f"problems {probs} unlisted {unlisted}")
    probs, _ = ra.compare(extra, m, strict=True)
    case(problems, "compare fails an unlisted file with strict",
         any("unlisted: x.txt" in p for p in probs), f"problems {probs}")
    extra["later.sav"] = (3, "2" * 64)
    probs, unlisted = ra.compare(extra, m)
    case(problems, "compare ignores a runtime write",
         probs == [] and unlisted == ["x.txt"], f"problems {probs} unlisted {unlisted}")

    # Each observation is validated before it is compared; a bad one is a problem, never matched.
    good_size, good_digest = listed["MANUAL.md"]
    for label, rel, value, reason in (
            ("an escaping path", "../MANUAL.md", (good_size, good_digest), "'..' segment"),
            ("an absolute path", "/MANUAL.md", (good_size, good_digest), "absolute path"),
            ("a value that is not a pair", "x.dat", [good_size, good_digest], "is not (bytes, sha256)"),
            ("a negative size", "x.dat", (-1, good_digest), "not a non-negative integer"),
            ("a boolean size", "x.dat", (True, good_digest), "not a non-negative integer"),
            ("an upper-case sha256", "x.dat", (good_size, good_digest.upper()), "64 lower-case hex"),
            ("a short sha256", "x.dat", (good_size, good_digest[:63]), "64 lower-case hex")):
        observed = dict(listed)
        observed[rel] = value
        probs, unlisted = call(problems, f"compare {label}", ra.compare, observed, m) or ([], [])
        case(problems, f"compare refuses an observation with {label}",
             any(reason in p for p in probs) and rel not in unlisted,
             f"problems {probs} unlisted {unlisted}")


def check_listing(problems, tmp, m):
    """read_listing: every field and every path is validated, and no line replaces another."""
    observed, errors = ra.read_listing(listing_of(tmp / "good-listing.txt", m))
    case(problems, "read_listing parses well-formed lines",
         errors == [] and observed == {f["path"]: (f["bytes"], f["sha256"]) for f in m["files"]},
         f"errors {errors} observed {observed}")
    first = m["files"][0]
    sha, size, path = first["sha256"], first["bytes"], first["path"]
    for label, line, reason in (
            ("a line of two fields", f"{sha}  {size}", "cannot parse"),
            ("a non-integer size", f"{sha}  notanint  x.txt", "is not an integer"),
            ("a negative size", f"{sha}  -1  x.txt", "is not an integer"),
            ("a signed size", f"{sha}  +5  x.txt", "is not an integer"),
            ("an underscored size", f"{sha}  1_000  x.txt", "is not an integer"),
            ("a short sha256", f"{sha[:63]}  {size}  x.txt", "is not 64 hex digits"),
            ("a long sha256", f"{sha}0  {size}  x.txt", "is not 64 hex digits"),
            ("a non-hex sha256", f"{'g' * 64}  {size}  x.txt", "is not 64 hex digits"),
            ("an absolute path", f"{sha}  {size}  /etc/passwd", "absolute path"),
            ("an escaping path", f"{sha}  {size}  ../x.txt", "'..' segment"),
            ("a dot segment", f"{sha}  {size}  ./x.txt", "'.' segment"),
            ("an empty segment", f"{sha}  {size}  a//x.txt", "empty segment"),
            ("a backslash", f"{sha}  {size}  a\\x.txt", "backslash"),
            ("a drive letter", f"{sha}  {size}  C:x.txt", "drive letter")):
        listing = tmp / "bad-listing.txt"
        listing.write_text(line + "\n", encoding="utf-8")
        result = call(problems, f"read_listing {label}", ra.read_listing, listing)
        if result is None:
            continue
        observed, errors = result
        case(problems, f"read_listing names {label}",
             observed == {} and any(e.startswith("line 1: ") and reason in e for e in errors),
             f"errors {errors} observed {observed}")

    # An upper-case sha256 is the same digest: it is read lower-cased and matches.
    listing = tmp / "upper-listing.txt"
    listing.write_text(f"{sha.upper()}  {size}  {path}\n", encoding="utf-8")
    observed, errors = ra.read_listing(listing)
    case(problems, "read_listing reads an upper-case sha256 as the same digest",
         errors == [] and observed == {path: (size, sha)}, f"errors {errors} observed {observed}")
    # A huge size is an integer: it is read, and compare reports it as a size mismatch.
    listing.write_text(f"{sha}  {10 ** 30}  {path}\n", encoding="utf-8")
    observed, errors = ra.read_listing(listing)
    probs, _ = ra.compare(observed, m)
    case(problems, "read_listing reads a huge size and compare reports the mismatch",
         errors == [] and any(f"{path}: {10 ** 30} bytes" in p for p in probs),
         f"errors {errors} problems {probs}")

    # A path named on two lines is an error naming the later line, whatever the order (PR #24 R2).
    zero = "0" * 64
    right = f"{sha}  {size}  {path}"
    wrong = f"{zero}  {size}  {path}"
    for order, text in (("wrong then right", f"{wrong}\n{right}\n"),
                        ("right then wrong", f"{right}\n{wrong}\n")):
        duplicate = tmp / f"dup-{order.split()[0]}.txt"
        duplicate.write_text(text, encoding="utf-8")
        _, errors = ra.read_listing(duplicate)
        case(problems, f"read_listing names a duplicate path ({order})",
             any("line 2" in e and "duplicate" in e for e in errors), f"errors {errors}")


def check_walk(problems, tmp, m):
    """walk: links out of the directory, broken links, special files and bad names are reported and
    never read; a link to a directory inside is not descended."""
    outside = tmp / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_bytes(b"outside bytes\n")
    w = tmp / "walk"
    (w / "sub").mkdir(parents=True)
    (w / "a.txt").write_bytes(b"a\n")
    (w / "sub" / "b.txt").write_bytes(b"b\n")
    os.symlink("a.txt", w / "link_in")
    os.symlink("sub", w / "dirlink")
    os.symlink(outside / "secret.txt", w / "out_file")
    os.symlink("../outside", w / "out_dir")
    os.symlink("nothing", w / "broken")
    # A UNIX socket, not a FIFO: if the special-file guard is removed, hashing a socket fails by
    # name where reading a FIFO would hang the suite.
    sock = socket.socket(socket.AF_UNIX)
    sock.bind(str(w / "sock"))
    (w / "back\\slash").write_bytes(b"c\n")
    files, walk_problems = ra.walk(w)
    rels = [rel for rel, _ in files]
    case(problems, "walk observes regular files and a link to a file inside",
         rels == ["a.txt", "link_in", "sub/b.txt"], f"files {rels}")
    for name, reason in (("out_file", "symbolic link to outside the directory"),
                         ("out_dir", "symbolic link to outside the directory"),
                         ("broken", "symbolic link to nothing"),
                         ("sock", "not a regular file"),
                         ("back\\\\slash", "backslash")):
        case(problems, f"walk reports {name} ({reason})",
             any(p.lstrip("'").startswith(name) and reason in p for p in walk_problems),
             f"problems {walk_problems}")
    case(problems, "walk does not descend or report a link to a directory inside",
         not any("dirlink" in p for p in walk_problems) and not any("dirlink" in r for r in rels),
         f"files {rels} problems {walk_problems}")
    sock.close()

    # Unreadable entries are named problems, not crashes. Permissions do not bind root, so these two
    # cases run only for an ordinary user (as in CI).
    if os.geteuid() != 0:
        u = tmp / "unreadable"
        (u / "locked").mkdir(parents=True)
        (u / "secret.dat").write_bytes(b"x\n")
        os.chmod(u / "locked", 0)
        os.chmod(u / "secret.dat", 0)
        files, walk_problems = ra.walk(u)
        case(problems, "walk names a directory it cannot read",
             any(p.startswith("locked/: cannot read the directory") for p in walk_problems),
             f"problems {walk_problems}")
        try:
            ra.build_manifest(u, "u", "U", "1", "generated", "1970-01-01")
            raised = []
        except ra.SetError as e:
            raised = e.problems
        except Exception as e:  # noqa: BLE001 - a crash is this case failing
            raised = [f"raised {type(e).__name__}: {e}"]
        case(problems, "build_manifest names a file it cannot read",
             any(p.startswith("secret.dat: cannot read") for p in raised), f"problems {raised}")
        os.chmod(u / "locked", 0o755)
        os.chmod(u / "secret.dat", 0o644)

    try:
        ra.build_manifest(w, "w", "W", "1", "generated", "1970-01-01")
        raised = []
    except ra.SetError as e:
        raised = e.problems
    case(problems, "build_manifest refuses a directory with a link to outside",
         any(p.startswith("out_file: symbolic link to outside") for p in raised), f"problems {raised}")

    # check: a copy holding a link to outside is a failure that names it; its target is never read.
    c = write_tree(tmp / "linked")
    os.symlink(outside / "secret.txt", c / "extra.dat")
    observed, walk_problems = ra.hash_tree(c, m)
    case(problems, "hash_tree reports a link to outside and does not hash its target",
         "extra.dat" not in observed
         and any(p.startswith("extra.dat: symbolic link to outside") for p in walk_problems),
         f"observed {sorted(observed)} problems {walk_problems}")
    proc = run(["check", c, m["id"], "--known", known_file(tmp / "linked-known.json", m)])
    no_traceback(problems, "CLI check link to outside", proc)
    case(problems, "CLI check fails a copy holding a link to outside, naming it",
         proc.returncode == 1 and "extra.dat: symbolic link to outside" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    proc = run(["manifest", c, "--label", "d", "--title", "T", "--version", "1", "--how", "generated"])
    no_traceback(problems, "CLI manifest link to outside", proc)
    case(problems, "CLI manifest refuses a directory holding a link to outside, naming it",
         proc.returncode == 1 and "extra.dat: symbolic link to outside" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")


def check_known(problems, tmp, m):
    """known_errors and select_set: structure, every manifest, and an id named once."""
    for label, doc, reason in (("a list", [], "not a JSON object"),
                               ("no sets", {}, "missing 'sets' list"),
                               ("a set without a manifest", {"sets": [1]}, "no manifest object")):
        errors = call(problems, f"known_errors {label}", ra.known_errors, doc) or []
        case(problems, f"known_errors names {label}", any(reason in e for e in errors),
             f"errors {errors}")
    twice = {"sets": [{"manifest": m}, {"manifest": dict(m)}]}
    errors = ra.known_errors(twice)
    case(problems, "known_errors refuses a set id that appears twice",
         any("duplicate id" in e and "sets[1]" in e for e in errors), f"errors {errors}")
    manifest, errors = ra.select_set(twice, m["id"])
    case(problems, "select_set refuses a set id that appears twice",
         manifest is None and any("2 known.json entries" in e for e in errors), f"errors {errors}")
    manifest, errors = ra.select_set({"sets": [{"manifest": m}]}, m["id"])
    case(problems, "select_set returns an accepted manifest", manifest == m and errors == [],
         f"errors {errors}")
    dup_known = known_file(tmp / "dup-id-known.json", m, m)
    proc = run(["validate", "--known", dup_known])
    case(problems, "CLI validate rejects a known.json whose set id appears twice",
         proc.returncode == 1 and "duplicate id" in proc.stdout, f"exit {proc.returncode} {proc.stdout!r}")
    proc = run(["check", tmp / "set", m["id"], "--known", dup_known])
    case(problems, "CLI check refuses a set id that appears twice",
         proc.returncode == 1 and "2 known.json entries" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")


def check_cli(problems, tmp, d, m, known):
    set_id = m["id"]
    # manifest prints the same id, accepts --writes, and defaults --when to today.
    proc = run(["manifest", d, "--label", "demo", "--title", "Demo", "--version", "1",
                "--how", "generated", "--when", "1970-01-01", "--note", "a note",
                "--runtime-write", "*.sav", "--runtime-write", "*.bin", "--exclude", "*.txt"])
    no_traceback(problems, "CLI manifest", proc)
    case(problems, "CLI manifest prints the library id",
         proc.returncode == 0 and json.loads(proc.stdout)["id"] == set_id,
         f"exit {proc.returncode} {proc.stdout[:200]}")
    proc = run(["manifest", d, "--label", "demo", "--title", "Demo", "--version", "1",
                "--how", "generated", "--when", "1970-01-01", "--note", "a note",
                "--writes", "*.sav", "--writes", "*.bin", "--exclude", "*.txt"])
    case(problems, "CLI manifest accepts --writes as the alias of --runtime-write",
         proc.returncode == 0 and json.loads(proc.stdout)["id"] == set_id,
         f"exit {proc.returncode} {proc.stdout[:200]}")
    proc = run(["manifest", d, "--label", "d", "--title", "T", "--version", "1",
                "--how", "generated"])
    case(problems, "CLI manifest defaults --when to today",
         proc.returncode == 0 and json.loads(proc.stdout)["acquired"]["when"] == date.today().isoformat(),
         f"exit {proc.returncode} {proc.stdout[:200]}")
    case(problems, "CLI manifest rejects a missing directory by name",
         run(["manifest", tmp / "nope", "--label", "d", "--title", "T", "--version", "1",
              "--how", "generated"]).returncode == 1, "")

    # check a directory.
    proc = run(["check", d, set_id, "--known", known])
    no_traceback(problems, "CLI check ok", proc)
    case(problems, "CLI check accepts a matching directory",
         proc.returncode == 0 and "ok:" in proc.stdout, f"exit {proc.returncode} {proc.stdout!r}")
    original = (d / "game.pyz").read_bytes()
    (d / "game.pyz").write_bytes(b"Z" + original[1:])
    proc = run(["check", d, set_id, "--known", known])
    case(problems, "CLI check catches a changed file by name",
         proc.returncode == 1 and "game.pyz" in proc.stdout and "sha256" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    (d / "game.pyz").unlink()
    proc = run(["check", d, set_id, "--known", known])
    case(problems, "CLI check catches a missing file",
         proc.returncode == 1 and "missing" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    (d / "game.pyz").write_bytes(original)
    (d / "x.sav").write_bytes(b"runtime\n")
    proc = run(["check", d, set_id, "--known", known])
    case(problems, "CLI check ignores an extra runtime write",
         proc.returncode == 0 and "ok:" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    (d / "x.sav").unlink()
    (d / "x.txt").write_bytes(b"extra\n")
    proc = run(["check", d, set_id, "--known", known])
    no_traceback(problems, "CLI check unlisted", proc)
    case(problems, "CLI check prints an unlisted file and exits 0",
         proc.returncode == 0 and "unlisted: x.txt" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    proc = run(["check", d, set_id, "--known", known, "--strict"])
    no_traceback(problems, "CLI check strict", proc)
    case(problems, "CLI check fails an unlisted file with --strict",
         proc.returncode == 1 and "unlisted: x.txt" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    (d / "x.txt").unlink()

    # check a listing.
    good = listing_of(tmp / "cli-good-listing.txt", m)
    proc = run(["check", "--list", good, set_id, "--known", known])
    case(problems, "CLI check accepts a matching listing",
         proc.returncode == 0 and "ok:" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    bad = listing_of(tmp / "cli-bad-listing.txt", m, extra=["a" * 64 + "  notanint  x.txt"])
    proc = run(["check", "--list", bad, set_id, "--known", known])
    no_traceback(problems, "CLI check bad listing", proc)
    case(problems, "CLI check names a bad listing line and exits 1",
         proc.returncode == 1 and "is not an integer" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    escaping = listing_of(tmp / "cli-escaping-listing.txt", m,
                          extra=[f"{m['files'][0]['sha256']}  1  ../x.txt"])
    proc = run(["check", "--list", escaping, set_id, "--known", known])
    case(problems, "CLI check names an escaping listing path and exits 1",
         proc.returncode == 1 and "'..' segment" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    latin = tmp / "cli-latin1-listing.txt"
    latin.write_bytes(b"\xff\xfe not utf-8\n")
    proc = run(["check", "--list", latin, set_id, "--known", known])
    no_traceback(problems, "CLI check listing not UTF-8", proc)
    case(problems, "CLI check names a listing that is not UTF-8",
         proc.returncode == 1 and str(latin) in proc.stdout, f"exit {proc.returncode} {proc.stdout!r}")

    # check refuses a manifest whose canonical identity does not hold (PR #24 R1).
    forged_id = "forged-00000000"
    forged_known = known_file(tmp / "forged-known.json", dict(m, id=forged_id))
    for label, args in (("directory", ["check", d, forged_id, "--known", forged_known]),
                        ("listing", ["check", "--list", good, forged_id, "--known", forged_known])):
        proc = run(args)
        no_traceback(problems, f"CLI check forged manifest {label}", proc)
        case(problems, f"CLI check refuses a forged manifest id for a {label}",
             proc.returncode == 1 and forged_id in proc.stdout,
             f"exit {proc.returncode} {proc.stdout!r}")

    # A listing that names one path twice, whatever the order (PR #24 R2).
    first = m["files"][0]
    right = f"{first['sha256']}  {first['bytes']}  {first['path']}"
    wrong = f"{'0' * 64}  {first['bytes']}  {first['path']}"
    for order, text in (("wrong then right", f"{wrong}\n{right}\n"),
                        ("right then wrong", f"{right}\n{wrong}\n")):
        duplicate = tmp / f"cli-dup-{order.split()[0]}.txt"
        duplicate.write_text(text, encoding="utf-8")
        proc = run(["check", "--list", duplicate, set_id, "--known", known])
        no_traceback(problems, f"CLI check duplicate listing {order}", proc)
        case(problems, f"CLI check rejects a duplicate listing path ({order})",
             proc.returncode == 1 and "line 2" in proc.stdout and "duplicate" in proc.stdout,
             f"exit {proc.returncode} {proc.stdout!r}")

    # A known.json with a duplicate JSON key; a manifest that lists one path twice.
    dup_keys = tmp / "dup-keys.json"
    dup_keys.write_text('{"sets": [], "sets": [{"manifest": ' + json.dumps(m) + "}]}",
                        encoding="utf-8")
    proc = run(["validate", "--known", dup_keys])
    no_traceback(problems, "CLI validate duplicate json key", proc)
    case(problems, "CLI validate rejects a known.json with a duplicate key",
         proc.returncode == 1 and "duplicate key" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    twice = with_files(m, [first, dict(first)] + m["files"][1:])
    twice_known = known_file(tmp / "twice-known.json", twice)
    proc = run(["validate", "--known", twice_known])
    no_traceback(problems, "CLI validate duplicate manifest path", proc)
    case(problems, "CLI validate rejects a manifest that lists a path twice",
         proc.returncode == 1 and "duplicate" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    proc = run(["check", d, twice["id"], "--known", twice_known])
    no_traceback(problems, "CLI check duplicate manifest path", proc)
    case(problems, "CLI check refuses a manifest that lists a path twice",
         proc.returncode == 1 and "duplicate" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")

    # The round-2 reproduction: a manifest path that is absolute or escapes, id recomputed, is
    # refused by validate and by check --list --strict.
    for path in ("/outside/a", "../a"):
        bad_m = with_files(m, [dict(first, path=path)] + m["files"][1:])
        bad_known = known_file(tmp / "bad-path-known.json", bad_m)
        proc = run(["validate", "--known", bad_known])
        no_traceback(problems, f"CLI validate manifest path {path}", proc)
        case(problems, f"CLI validate rejects a manifest path {path!r}",
             proc.returncode == 1 and repr(path) in proc.stdout,
             f"exit {proc.returncode} {proc.stdout!r}")
        listing = tmp / "bad-path-listing.txt"
        listing.write_text(f"{first['sha256']}  {first['bytes']}  {path}\n", encoding="utf-8")
        proc = run(["check", "--list", listing, bad_m["id"], "--known", bad_known, "--strict"])
        no_traceback(problems, f"CLI check manifest path {path}", proc)
        case(problems, f"CLI check --strict refuses a manifest path {path!r}",
             proc.returncode == 1 and repr(path) in proc.stdout and "ok:" not in proc.stdout,
             f"exit {proc.returncode} {proc.stdout!r}")

    # validate and bad input.
    proc = run(["validate", "--known", known])
    no_traceback(problems, "CLI validate", proc)
    case(problems, "CLI validate reports the set count",
         proc.returncode == 0 and "known.json ok (1 sets)" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    for label, text in (("not JSON", "not json"),
                        ("no sets", json.dumps({"foo": 1}))):
        bad = tmp / f"known-{label}.json"
        bad.write_text(text, encoding="utf-8")
        proc = run(["validate", "--known", bad])
        no_traceback(problems, f"CLI validate {label}", proc)
        case(problems, f"CLI validate rejects a known.json that is {label}",
             proc.returncode == 1 and str(bad) in proc.stdout,
             f"exit {proc.returncode} {proc.stdout!r}")
    proc = run(["check", d, "nope-00000000", "--known", known])
    no_traceback(problems, "CLI check unknown id", proc)
    case(problems, "CLI check names an unknown set id",
         proc.returncode == 1 and "no known.json entry" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    proc = run(["check", tmp / "nope", set_id, "--known", known])
    case(problems, "CLI check names a missing directory",
         proc.returncode == 1 and "not a directory" in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")
    proc = run(["check"])
    case(problems, "CLI usage error exits 2 and prints no traceback",
         proc.returncode == 2 and "Traceback" not in proc.stderr, f"exit {proc.returncode}")
    proc = run(["check", "--list", good, set_id, "extra", "--known", known])
    case(problems, "CLI check --list with a second positional is a usage error",
         proc.returncode == 2 and "Traceback" not in proc.stderr and "ok:" not in proc.stdout,
         f"exit {proc.returncode} {proc.stdout!r}")


if __name__ == "__main__":
    sys.exit(main())
