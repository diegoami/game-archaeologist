#!/usr/bin/env python3
"""Verify an experiment's evidence bundle.

`python3 tools/verify_evidence.py E<nnn>` reads `evidence/E<nnn>/*.manifest.json`, validates every
manifest with `validate_records.validate_document` (schema and the schema's asset-name rule), then
fetches release `E<nnn>` in one `gh release download E<nnn> -D <dir>`
call and checks each listed asset in that directory by sha256. An asset the bulk call left out is
retried once, by name, with `gh release download ... -p <asset>`, and is reported by name when it is
still absent. With `--local <dir>` a directory is checked instead of the release (the bundle already
downloaded).

The download directory is made fresh for every run: it is removed and re-created before the bulk
call, so a file left there by an earlier run is never accepted in place of this run's download
(toy-archaeology#11). A symlink there is removed, not followed, and a removal that fails is an
error. The experiment must be an id (`E<nnn>`), never a path, because it names that directory.
Every `*.manifest.json` must be an `evidence-manifest/1` document. The release is never downloaded one asset at a time: one bulk call covers every
asset, however many manifests share it.

Exit 0 when every file matches, 1 otherwise. `--evidence-dir` defaults to `evidence/` under the
working directory. `--repo` defaults to the working directory's GitHub repository, from `gh repo
view`. Paths are relative to the working directory, never to this script: a game repository fetches
this file beside `validate_records.py` and `formats/*.schema.json` and runs it from the repository it
serves (ADR-009). Any input that cannot be checked is a named error, never a traceback.

Adapted from diegoami/toy-archaeology tools/verify_evidence.py at a3056ff through
diegoami/goal2-archaeology's copy.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_records  # noqa: E402
from validate_records import validate_document  # noqa: E402


EXPERIMENT = re.compile(r"^E[0-9]{3,}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_files(manifest: dict) -> list[tuple[str, str]]:
    """The (asset, sha256) pairs of a manifest already accepted by ``validate_document``.

    The asset name is not recomputed here: ``validate_document`` enforces the evidence-manifest rule
    that names each asset from its sha256 and name, so this file must never slice a hash to build it."""
    return [(entry["asset"], entry["sha256"]) for entry in manifest["files"]]


def check_local(manifest: dict, local: Path) -> list[str]:
    problems = []
    for asset, want in manifest_files(manifest):
        path = Path(local) / asset
        if not path.is_file():
            problems.append(f"{asset}: missing from {local}")
            continue
        actual = sha256_file(path)
        if actual != want:
            problems.append(f"{asset}: sha256 {actual}, manifest says {want}")
    return problems


def gh(*args: str) -> subprocess.CompletedProcess:
    """Run ``gh`` with the given arguments; OSError becomes a named RuntimeError."""
    try:
        return subprocess.run(["gh", *args], check=False, capture_output=True, text=True)
    except OSError as e:  # gh is not installed, or is not executable
        raise RuntimeError(f"cannot run gh: {e.strerror or e}") from None


def default_repo() -> str:
    """The working directory's GitHub repository, from ``gh repo view``."""
    result = gh("repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner")
    repo = result.stdout.strip()
    if result.returncode != 0 or not repo:
        raise RuntimeError("cannot find the working directory's GitHub repository (gh repo view)")
    return repo


def check_release(manifests: list[tuple[str, dict]], release: str, repo: str,
                  cache: Path) -> list[str]:
    """Problems for every manifest against the release: one bulk download, then one retry per asset
    the bulk call left out, then a local sha256 check of every listed asset.

    ``manifests`` is a list of (manifest file name, parsed manifest) pairs already validated."""
    wanted = [(name, asset, sha) for name, manifest in manifests
              for asset, sha in manifest_files(manifest)]
    # A fresh directory every run: remove whatever an earlier run left, so a stale cached file can
    # never stand in for this run's download (toy-archaeology#11).
    # A failed removal is an error, never ignored, and a symlink is removed, not followed: either
    # would leave the earlier files in place. `exist_ok=False` proves the directory is new.
    if cache.is_symlink() or cache.is_file():
        cache.unlink()
    elif cache.exists():
        shutil.rmtree(cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.mkdir()
    gh("release", "download", release, "--repo", repo, "-D", str(cache))
    missing = sorted({asset for _, asset, _ in wanted if not (cache / asset).is_file()})
    for asset in missing:
        gh("release", "download", release, "--repo", repo, "-p", asset, "-D", str(cache))
    problems = []
    for name, asset, want in wanted:
        path = cache / asset
        if not path.is_file():
            problems.append(f"{name}: {asset}: missing from release {release}")
            continue
        actual = sha256_file(path)
        if actual != want:
            problems.append(f"{name}: {asset}: sha256 {actual}, manifest says {want}")
    return problems


def run(args) -> int:
    if not EXPERIMENT.match(args.experiment):
        # The id names a directory this tool removes and re-creates, so it may not be a path.
        print(f"{args.experiment}: not an experiment id (E<nnn>)")
        return 1
    evidence_dir = args.evidence_dir if args.evidence_dir is not None else Path.cwd() / "evidence"
    manifests = sorted((evidence_dir / args.experiment).glob("*.manifest.json"))
    if not manifests:
        print(f"no manifest under {evidence_dir / args.experiment}")
        return 1

    loaded: list[tuple[str, dict]] = []
    problems: list[str] = []
    for path in manifests:
        try:
            document = validate_records.load_file(path)
        except (OSError, ValueError) as e:
            problems.append(f"{path}: {e}")
            continue
        if not isinstance(document, dict) or document.get("schema") != "evidence-manifest/1":
            problems.append(f"{path.name}: not an evidence-manifest/1 document")
            continue
        errors = validate_document(document)
        if errors:
            problems.extend(f"{path}: {error}" for error in errors)
            continue
        loaded.append((path.name, document))
    if problems:
        print("\n".join(problems))
        return 1

    if args.local is not None:
        for name, manifest in loaded:
            problems.extend(f"{name}: {p}" for p in check_local(manifest, args.local))
    else:
        repo = args.repo if args.repo is not None else default_repo()
        cache = Path.cwd() / ".cache" / "evidence" / args.experiment
        problems = check_release(loaded, args.experiment, repo, cache)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"ok: {len(manifests)} manifest(s) verified")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", help="experiment id, e.g. E001")
    parser.add_argument("--local", type=Path, help="check this directory instead of the release")
    parser.add_argument("--evidence-dir", type=Path, default=None,
                        help="where the manifests live (default: evidence/ under the working directory)")
    parser.add_argument("--repo", default=None,
                        help="OWNER/NAME of the release's repository (default: gh repo view)")
    args = parser.parse_args(argv)
    try:
        return run(args)
    except Exception as e:  # noqa: BLE001 - no input may produce a traceback
        print(f"verify_evidence.py: internal error: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
