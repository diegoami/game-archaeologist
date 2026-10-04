#!/usr/bin/env python3
"""Regression tests for tools/register_artifact.py. Stdlib only, no network and no game files.

They drive the library functions and the CLI over a temporary set whose runtime writes (*.sav,
*.bin) and excluded files (*.txt) are real files, so the U21 split, the sha256 comparison, the
--strict rule, the malformed-input errors and the manifest layout are each observed. Every failure
names its case. Exit 0 when every case holds, 1 otherwise."""
import json
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


def case(problems, label, ok, detail=""):
    if not ok:
        problems.append(f"{label}: {detail}" if detail else label)


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


def main():
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        d = write_tree(tmp / "set")
        m = ra.build_manifest(d, "demo", "Demo", "1", "generated", "1970-01-01",
                              note="a note", runtime_writes=["*.sav", "*.bin"],
                              excludes=["*.txt"])
        paths = [f["path"] for f in m["files"]]

        # build_manifest: the U21 split, the id, the recorded acquisition and safe paths.
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
        case(problems, "manifest paths are relative and stay inside the directory",
             all(not Path(p).is_absolute() and ".." not in Path(p).parts for p in paths),
             f"paths {paths}")
        case(problems, "manifest records the acquisition and note",
             m["acquired"] == {"how": "generated", "when": "1970-01-01", "note": "a note"},
             f"acquired {m['acquired']}")

        # hash_tree: an unlisted runtime write is left out; a listed file is always observed.
        (d / "new.sav").write_bytes(b"new\n")
        observed = ra.hash_tree(d, m)
        case(problems, "hash_tree ignores an unlisted runtime write",
             "new.sav" not in observed and "MANUAL.md" in observed,
             f"observed {sorted(observed)}")
        (d / "new.sav").unlink()

        # compare: sha256, size, missing, unlisted and runtime writes.
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

        # read_listing: a line that is not parseable or has a non-integer size is a named error.
        observed, errors = ra.read_listing(_write(tmp / "good-listing.txt", m))
        case(problems, "read_listing parses well-formed lines", errors == [] and "MANUAL.md" in observed,
             f"errors {errors}")
        observed, errors = ra.read_listing(_write(tmp / "bad-listing.txt", m, bad=True))
        case(problems, "read_listing names a non-integer size",
             any(e.startswith("line ") and "is not an integer" in e for e in errors),
             f"errors {errors}")

        # CLI: manifest prints the same id, accepts --writes, and defaults --when to today.
        known = tmp / "known.json"
        known.write_text(json.dumps({"sets": [{"manifest": m}]}), encoding="utf-8")
        set_id = m["id"]
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

        # CLI: check a directory.
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
        (d / "game.pyz").write_bytes(original)
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

        # CLI: check a listing.
        proc = run(["check", "--list", tmp / "good-listing.txt", set_id, "--known", known])
        case(problems, "CLI check accepts a matching listing",
             proc.returncode == 0 and "ok:" in proc.stdout,
             f"exit {proc.returncode} {proc.stdout!r}")
        proc = run(["check", "--list", tmp / "bad-listing.txt", set_id, "--known", known])
        no_traceback(problems, "CLI check bad listing", proc)
        case(problems, "CLI check names a bad listing line and exits 1",
             proc.returncode == 1 and "is not an integer" in proc.stdout,
             f"exit {proc.returncode} {proc.stdout!r}")

        # R1: check refuses a manifest whose own canonical identity does not hold (PR #24 R1), for a
        # directory and for a listing, naming the id it was asked for.
        forged_id = "forged-00000000"
        forged = dict(m)
        forged["id"] = forged_id
        forged_known = tmp / "forged-known.json"
        forged_known.write_text(json.dumps({"sets": [{"manifest": forged}]}), encoding="utf-8")
        for label, args in (("directory", ["check", d, forged_id, "--known", forged_known]),
                            ("listing", ["check", "--list", tmp / "good-listing.txt", forged_id,
                                         "--known", forged_known])):
            proc = run(args)
            no_traceback(problems, f"CLI check forged manifest {label}", proc)
            case(problems, f"CLI check refuses a forged manifest id for a {label}",
                 proc.returncode == 1 and forged_id in proc.stdout,
                 f"exit {proc.returncode} {proc.stdout!r}")

        # R2: a listing that names the same path twice is an error naming the line, whatever the order
        # (PR #24 R2): a later line never silently replaces an earlier observation.
        first = m["files"][0]
        listing_line = f"{first['sha256']}  {first['bytes']}  {first['path']}"
        zero = "0" * 64
        for order, text in (("wrong then right", f"{zero}  {first['bytes']}  {first['path']}\n{listing_line}\n"),
                            ("right then wrong", f"{listing_line}\n{zero}  {first['bytes']}  {first['path']}\n")):
            duplicate = tmp / f"dup-{order.split()[0]}.txt"
            duplicate.write_text(text, encoding="utf-8")
            _, errors = ra.read_listing(duplicate)
            case(problems, f"read_listing names a duplicate path ({order})",
                 any("line 2" in e and "duplicate" in e for e in errors), f"errors {errors}")
            proc = run(["check", "--list", duplicate, set_id, "--known", known])
            no_traceback(problems, f"CLI check duplicate listing {order}", proc)
            case(problems, f"CLI check rejects a duplicate listing path ({order})",
                 proc.returncode == 1 and "line 2" in proc.stdout and "duplicate" in proc.stdout,
                 f"exit {proc.returncode} {proc.stdout!r}")

        # Sweep of the same two classes: no input is accepted unvalidated, and no later value
        # silently replaces an earlier one. A known.json with a duplicate JSON key would keep
        # whichever value the reader chose; a manifest that lists one path twice keys its files by
        # path, so later entries would replace earlier ones.
        dup_keys = tmp / "dup-keys.json"
        dup_keys.write_text('{"sets": [], "sets": [{"manifest": ' + json.dumps(m) + "}]}",
                            encoding="utf-8")
        proc = run(["validate", "--known", dup_keys])
        no_traceback(problems, "CLI validate duplicate json key", proc)
        case(problems, "CLI validate rejects a known.json with a duplicate key",
             proc.returncode == 1 and "duplicate key" in proc.stdout,
             f"exit {proc.returncode} {proc.stdout!r}")
        twice = dict(m)
        twice["files"] = [m["files"][0], dict(m["files"][0])]
        twice["id"] = f"demo-{ra.canonical_set_hash(twice)[:8]}"
        twice_known = tmp / "twice-known.json"
        twice_known.write_text(json.dumps({"sets": [{"manifest": twice}]}), encoding="utf-8")
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

        # CLI: validate and bad input.
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
        case(problems, "CLI usage error exits 2 and prints no traceback",
             run(["check"]).returncode == 2 and "Traceback" not in run(["check"]).stderr, "")

    if problems:
        print("\n".join(problems))
        return 1
    print("ok: register_artifact.py manifest, check, validate and malformed input hold")
    return 0


def _write(path, manifest, bad=False):
    lines = [f"{f['sha256']}  {f['bytes']}  {f['path']}" for f in manifest["files"]]
    if bad:
        lines.append("a" * 64 + "  notanint  x.txt")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    sys.exit(main())
