"""A local evidence bundle verifies by sha256 and asset name; a changed byte fails; the release is
fetched in one bulk download, each asset the bulk call left out is retried once by name, and a stale
cache never stands in for this run's download; a changed byte, a failed download and an asset the
release does not carry are each reported by name (DW3, toy-archaeology#11).
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "tools" / "fixtures"
EVIDENCE = FIXTURES / "evidence"
LOCAL = EVIDENCE / "local"
BULK = FIXTURES / "evidence_bulk"
BULK_RELEASE = BULK / "release"
BULK_ASSETS = ("8ed3f6ad685b959e-a.bin", "f144a6907dc4284d-b.bin",
               "b9dd960c1753459a-c.bin", "4f4a9410ffcdf895-d.bin")
C_ASSET = "b9dd960c1753459a-c.bin"
E900_ASSET = "c82cd5ca5a74f844-after.sav"
DEFAULT_REPO = "diegoami/goal2-archaeology"

# A fake `gh`: `repo view` prints FAKE_GH_REPO (the working directory's repository); one
# `release download` without `-p` copies the release's assets per FAKE_GH_MODE; a retry with `-p`
# behaves the same per asset. Every invocation is appended to FAKE_GH_LOG.
#   ok             - copy everything, exit 0
#   fail           - exit 1, producing no file
#   empty          - exit 0, producing no file (a silent drop)
#   flaky          - the bulk call drops everything; each per-asset retry copies its file
#   partial        - the bulk call copies all but c.bin and exits 1; the retry of c.bin copies it
#   fail-with-file - the bulk call copies everything and exits 1 (bytes are there, gh says failed)
FAKE_GH = """#!/usr/bin/env python3
import os
import shutil
import sys
from pathlib import Path

args = sys.argv[1:]
with open(os.environ["FAKE_GH_LOG"], "a", encoding="utf-8") as log:
    log.write(" ".join(args) + "\\n")
release = Path(os.environ["FAKE_GH_RELEASE"])
mode = os.environ.get("FAKE_GH_MODE", "ok")
if args[:2] == ["repo", "view"]:
    print(os.environ.get("FAKE_GH_REPO", "diegoami/goal2-archaeology"))
    sys.exit(0)
if args[:2] == ["release", "download"]:
    dest = Path(args[args.index("-D") + 1])
    if not dest.is_dir():
        sys.exit(1)  # the caller makes the directory
    if "-p" in args:
        asset = args[args.index("-p") + 1]
        if mode == "fail":
            sys.exit(1)
        if mode == "empty":
            sys.exit(0)
        shutil.copy(release / asset, dest / asset)
        sys.exit(0)
    # the bulk call: no -p, one call for the whole release
    if mode == "fail":
        sys.exit(1)
    if mode == "empty":
        sys.exit(0)
    if mode == "flaky":
        sys.exit(0)
    for path in sorted(release.iterdir()):
        if mode == "partial" and path.name == "b9dd960c1753459a-c.bin":
            continue
        shutil.copy(path, dest / path.name)
    sys.exit(1 if mode in ("partial", "fail-with-file") else 0)
sys.exit(2)
"""


def cache_dir(experiment: str) -> Path:
    """The cache `verify_evidence.py` uses for an experiment."""
    return REPO_ROOT / ".cache" / "evidence" / experiment


def run_verify(local: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "tools/verify_evidence.py", "E900",
         "--local", str(local), "--evidence-dir", str(EVIDENCE)],
        cwd=REPO_ROOT, capture_output=True, text=True)


def fake_gh(tmp: Path) -> tuple[Path, Path]:
    """A directory holding the fake `gh` and the log; return (fakebin, log)."""
    fakebin = tmp / "bin"
    fakebin.mkdir()
    log = tmp / "gh.log"
    gh = fakebin / "gh"
    gh.write_text(FAKE_GH, encoding="utf-8")
    gh.chmod(0o755)
    return fakebin, log


def run_verify_release(fakebin: Path, log: Path, mode: str, release: Path = BULK_RELEASE,
                       experiment: str = "E901", evidence: Path = BULK) -> subprocess.CompletedProcess:
    """Run the release verification against the fake `gh` serving `release`, in a download mode.

    No `--repo` is passed, so the tool takes the repository from the fake `gh repo view`."""
    env = {
        **os.environ,
        "PATH": f"{fakebin}{os.pathsep}{os.environ['PATH']}",
        "FAKE_GH_LOG": str(log),
        "FAKE_GH_RELEASE": str(release),
        "FAKE_GH_MODE": mode,
        "FAKE_GH_REPO": DEFAULT_REPO,
    }
    return subprocess.run(
        [sys.executable, "tools/verify_evidence.py", experiment, "--evidence-dir", str(evidence)],
        cwd=REPO_ROOT, capture_output=True, text=True, env=env)


def download_calls(log: Path) -> list[list[str]]:
    """The words of every `release download` call in the fake `gh` log, in order."""
    calls = []
    for line in log.read_text(encoding="utf-8").splitlines():
        if line.startswith("release download"):
            calls.append(shlex.split(line))
    return calls


def bulk_downloads(log: Path) -> list[list[str]]:
    """The `release download` calls with no `-p`: one bulk call fetches the whole release."""
    return [call for call in download_calls(log) if "-p" not in call]


def per_asset_downloads(log: Path) -> list[list[str]]:
    """The `release download` calls naming one asset, as retries do."""
    return [call for call in download_calls(log) if "-p" in call]


def downloaded_assets(log: Path) -> list[str]:
    """The asset each per-asset `release download` call names, in order."""
    return [call[call.index("-p") + 1] for call in per_asset_downloads(log)]


def release_copy(tmp: Path) -> Path:
    """A writable copy of the fixture release, to corrupt or trim in one test."""
    release = tmp / "release"
    shutil.copytree(BULK_RELEASE, release)
    return release


class VerifyEvidenceTest(unittest.TestCase):
    def test_local_bundle_exits_0(self):
        result = run_verify(LOCAL)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("ok: 1 manifest(s) verified", result.stdout)

    def test_changed_byte_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp)
            for source in LOCAL.iterdir():
                shutil.copy(source, local / source.name)
            asset = next(local.iterdir())
            changed = bytearray(asset.read_bytes())
            changed[0] ^= 0xFF
            asset.write_bytes(bytes(changed))
            result = run_verify(local)
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn("sha256", result.stdout)

    def test_missing_asset_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_verify(Path(tmp))
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn(f"{E900_ASSET}: missing from", result.stdout)

    def test_experiment_without_manifests_exits_1(self):
        result = subprocess.run(
            [sys.executable, "tools/verify_evidence.py", "E999", "--local", str(LOCAL),
             "--evidence-dir", str(EVIDENCE)],
            cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("no manifest under", result.stdout)


class VerifyEvidenceBadInputTest(unittest.TestCase):
    """A malformed manifest or a bundle with no manifest is a named error, never a traceback."""

    def run_bad(self, name: str, text: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            experiment = Path(tmp) / "evidence" / "E777"
            experiment.mkdir(parents=True)
            (experiment / f"{name}.manifest.json").write_text(text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, "tools/verify_evidence.py", "E777", "--local", str(LOCAL),
                 "--evidence-dir", str(Path(tmp) / "evidence")],
                cwd=REPO_ROOT, capture_output=True, text=True)

    def test_manifest_that_is_not_json_exits_1_with_a_named_line(self):
        result = self.run_bad("E777-r0001", "this is not json")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("E777-r0001.manifest.json", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_manifest_failing_the_schema_exits_1_with_a_named_line(self):
        result = self.run_bad("E777-r0002", json.dumps({
            "schema": "evidence-manifest/1", "run_id": "E777-r0002", "experiment": "E777",
            "artifact": {"set": "goal2-a949da2f", "variant": None},
            "files": []}))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("E777-r0002.manifest.json", result.stdout)
        self.assertIn("missing required property 'store'", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_wrong_asset_name_is_a_named_error_from_the_imported_rule(self):
        # The manifest's asset does not equal <sha256 prefix>-<name>: validate_document, not a local
        # rule, must reject it.
        result = self.run_bad("E777-r0003", json.dumps({
            "schema": "evidence-manifest/1", "run_id": "E777-r0003", "experiment": "E777",
            "store": "release:E777",
            "artifact": {"set": "goal2-a949da2f", "variant": None},
            "files": [{"name": "x.bin", "bytes": 1,
                       "sha256": "c82cd5ca5a74f844fbb2f4439257b78f4ed60ac882a8216893af6a6ede4dbef8",
                       "asset": "0000000000000000-x.bin", "class": "save"}]}))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("$.files[0].asset: must be", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


class VerifyEvidenceBulkTest(unittest.TestCase):
    """The release is fetched in one bulk `gh release download` call, never one asset at a time."""

    def setUp(self):
        shutil.rmtree(cache_dir("E901"), ignore_errors=True)
        self.addCleanup(shutil.rmtree, cache_dir("E901"), True)

    def test_one_bulk_download_for_three_manifests_and_four_assets(self):
        # 3 manifests, 4 distinct assets shared between them: toy-archaeology#11.
        with tempfile.TemporaryDirectory() as tmp:
            fakebin, log = fake_gh(Path(tmp))
            result = run_verify_release(fakebin, log, "ok")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            bulk = bulk_downloads(log)
            self.assertEqual(1, len(bulk), log.read_text(encoding="utf-8"))
            self.assertEqual([], per_asset_downloads(log))
            self.assertEqual(["release", "download", "E901", "--repo", DEFAULT_REPO, "-D",
                              str(cache_dir("E901"))], bulk[0])
            self.assertIn("ok: 3 manifest(s) verified", result.stdout)

    def test_download_calls_do_not_grow_with_the_bundle(self):
        # One manifest with one asset, and three manifests with four: the same single bulk call.
        counts = {}
        for experiment, evidence in (("E900", EVIDENCE), ("E901", BULK)):
            shutil.rmtree(cache_dir(experiment), ignore_errors=True)
            self.addCleanup(shutil.rmtree, cache_dir(experiment), True)
            with tempfile.TemporaryDirectory() as tmp:
                fakebin, log = fake_gh(Path(tmp))
                result = run_verify_release(fakebin, log, "ok", experiment=experiment,
                                            evidence=evidence)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                counts[experiment] = (len(bulk_downloads(log)), len(per_asset_downloads(log)))
        self.assertEqual(1, counts["E900"][0])
        self.assertEqual(1, counts["E901"][0])
        self.assertEqual((0, 0), (counts["E900"][1], counts["E901"][1]))

    def test_bulk_leaving_one_asset_is_completed_by_exactly_one_named_retry(self):
        # toy-archaeology#11: the bulk download exits 1 with 476 of 477 files; a retry gets the rest.
        with tempfile.TemporaryDirectory() as tmp:
            fakebin, log = fake_gh(Path(tmp))
            result = run_verify_release(fakebin, log, "partial")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(1, len(bulk_downloads(log)))
            self.assertEqual([C_ASSET], downloaded_assets(log))
            self.assertIn("ok: 3 manifest(s) verified", result.stdout)

    def test_bulk_silent_drop_is_retried_once_per_asset_and_reported_by_name(self):
        # The bulk call produces nothing; each of the four assets is retried once, then reported.
        with tempfile.TemporaryDirectory() as tmp:
            fakebin, log = fake_gh(Path(tmp))
            result = run_verify_release(fakebin, log, "empty")
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertEqual(1, len(bulk_downloads(log)))
            self.assertEqual(sorted(BULK_ASSETS), sorted(downloaded_assets(log)))
            for asset in BULK_ASSETS:
                self.assertIn(f"{asset}: missing from release E901", result.stdout)

    def test_bulk_silent_drop_recovered_by_the_retries_exits_0(self):
        # The bulk call drops every file; the one per-asset retry brings each, so nothing is reported.
        with tempfile.TemporaryDirectory() as tmp:
            fakebin, log = fake_gh(Path(tmp))
            result = run_verify_release(fakebin, log, "flaky")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(1, len(bulk_downloads(log)))
            self.assertEqual(sorted(BULK_ASSETS), sorted(downloaded_assets(log)))

    def test_bulk_exiting_1_with_every_asset_still_verifies(self):
        # A bulk download that exits nonzero but leaves every correct file is a pass: the bytes
        # decide, exactly as when a bulk download exits 1 with one file missing and a retry gets it.
        with tempfile.TemporaryDirectory() as tmp:
            fakebin, log = fake_gh(Path(tmp))
            result = run_verify_release(fakebin, log, "fail-with-file")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(1, len(bulk_downloads(log)))
            self.assertEqual([], per_asset_downloads(log))

    def test_byte_flipped_in_the_release_exits_1_naming_the_asset(self):
        # The release serves c.bin with one byte changed: its sha256 no longer matches the manifests.
        with tempfile.TemporaryDirectory() as tmp:
            release = release_copy(Path(tmp))
            asset = release / C_ASSET
            changed = bytearray(asset.read_bytes())
            changed[0] ^= 0xFF
            asset.write_bytes(bytes(changed))
            fakebin, log = fake_gh(Path(tmp))
            result = run_verify_release(fakebin, log, "ok", release)
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            problems = result.stdout.splitlines()
            self.assertTrue(problems)
            for line in problems:
                self.assertIn(f"{C_ASSET}: sha256", line)

    def test_asset_absent_from_the_release_is_reported_by_name_after_one_retry(self):
        # The manifests list c.bin, but the release does not carry it: the bulk call cannot produce
        # it, the one named retry cannot either, and it is reported by name.
        with tempfile.TemporaryDirectory() as tmp:
            release = release_copy(Path(tmp))
            (release / C_ASSET).unlink()
            fakebin, log = fake_gh(Path(tmp))
            result = run_verify_release(fakebin, log, "ok", release)
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            problems = result.stdout.splitlines()
            self.assertTrue(problems)
            for line in problems:
                self.assertIn(f"{C_ASSET}: missing from release E901", line)
            self.assertEqual([C_ASSET], downloaded_assets(log))


class VerifyEvidenceFreshCacheTest(unittest.TestCase):
    """A download must produce this run's file; a stale cache is never a substitute
    (toy-archaeology#11)."""

    def setUp(self):
        shutil.rmtree(cache_dir("E901"), ignore_errors=True)
        self.addCleanup(shutil.rmtree, cache_dir("E901"), True)

    def test_stale_cache_does_not_stand_in_for_a_failed_download(self):
        # The cache already holds every asset and the current downloads exit 1: the stale copies
        # must not stand in for this run's download.
        shutil.copytree(BULK_RELEASE, cache_dir("E901"))
        with tempfile.TemporaryDirectory() as tmp:
            fakebin, log = fake_gh(Path(tmp))
            result = run_verify_release(fakebin, log, "fail")
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            for asset in BULK_ASSETS:
                self.assertIn(f"{asset}: missing from release E901", result.stdout)

    def test_stale_cache_does_not_stand_in_for_an_empty_download(self):
        # The cache already holds every asset and the current downloads exit 0 producing nothing.
        shutil.copytree(BULK_RELEASE, cache_dir("E901"))
        with tempfile.TemporaryDirectory() as tmp:
            fakebin, log = fake_gh(Path(tmp))
            result = run_verify_release(fakebin, log, "empty")
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            for asset in BULK_ASSETS:
                self.assertIn(f"{asset}: missing from release E901", result.stdout)


class VerifyEvidenceSweepTest(unittest.TestCase):
    """Round 2 sweep (Opus): the fresh directory cannot be a stale one in disguise, an experiment
    argument cannot point the fresh-directory removal elsewhere, and a manifest file that holds
    another record kind is a named error."""

    def setUp(self):
        shutil.rmtree(cache_dir("E901"), ignore_errors=True)
        self.addCleanup(shutil.rmtree, cache_dir("E901"), True)

    def test_stale_cache_behind_a_symlink_does_not_stand_in_for_an_empty_download(self):
        # `.cache/evidence/E901` is a symlink to a directory already holding every asset: removing
        # it must not fail silently and leave the stale files in place of this run's download.
        with tempfile.TemporaryDirectory() as tmp:
            stale = Path(tmp) / "stale"
            shutil.copytree(BULK_RELEASE, stale)
            cache_dir("E901").parent.mkdir(parents=True, exist_ok=True)
            cache_dir("E901").symlink_to(stale, target_is_directory=True)
            self.addCleanup(lambda: cache_dir("E901").unlink() if cache_dir("E901").is_symlink() else None)
            fakebin, log = fake_gh(Path(tmp))
            result = run_verify_release(fakebin, log, "empty")
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertNotIn("ok:", result.stdout)
            self.assertNotIn("Traceback", result.stdout + result.stderr)
            self.assertTrue(all((stale / asset).is_file() for asset in BULK_ASSETS),
                            "the symlink's target must be left alone")

    def test_experiment_that_is_not_an_id_is_a_named_error_and_removes_nothing(self):
        # `E901/../keep` names a directory of valid manifests, so without the check the tool goes on
        # to remove `.cache/evidence/E901/../keep`, a directory it does not own.
        keep = REPO_ROOT / ".cache" / "evidence" / "keep"
        keep.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, keep, True)
        (keep / "sentinel").write_text("not the tool's", encoding="utf-8")
        cache_dir("E901").mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "evidence"
            shutil.copytree(BULK / "E901", evidence / "E901")
            shutil.copytree(BULK / "E901", evidence / "keep")
            fakebin, log = fake_gh(Path(tmp))
            result = run_verify_release(fakebin, log, "ok", experiment="E901/../keep", evidence=evidence)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("not an experiment id", result.stdout)
        self.assertTrue((keep / "sentinel").is_file(), "a directory outside the tool's cache was removed")

    def test_manifest_file_holding_another_record_kind_is_a_named_error(self):
        valid = sorted((REPO_ROOT / "formats" / "examples" / "valid").glob("*.json"))
        other = next(path for path in valid
                     if json.loads(path.read_text(encoding="utf-8")).get("schema") != "evidence-manifest/1")
        with tempfile.TemporaryDirectory() as tmp:
            experiment = Path(tmp) / "evidence" / "E777"
            experiment.mkdir(parents=True)
            shutil.copy(other, experiment / "E777-r0001.manifest.json")
            result = subprocess.run(
                [sys.executable, "tools/verify_evidence.py", "E777", "--local", str(LOCAL),
                 "--evidence-dir", str(Path(tmp) / "evidence")],
                cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("E777-r0001.manifest.json: not an evidence-manifest/1 document", result.stdout)


if __name__ == "__main__":
    unittest.main()
