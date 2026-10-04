# ADR-006 Artifact identity, derived variants, and per-game rights

- **Status**: Accepted 2026-10-02
- **Source:** [docs/phase0/05-artifacts.md](../phase0/05-artifacts.md); user decisions U1, U2, U3, U5, U11, U21, U22

## Context

IC2's artifact failures were failures of identity and provenance:
- reports with no binary hash;
- a seed build identified only by a truncated hash in prose;
- resampled audio and a `.cnt` file with no provenance;
- a fetch script that verified nothing.

IC2's own policy had the right split: private originals, a private minimal CI subset with a manifest,
public code. But a public copy of the originals then bypassed it. Isle Wars Pro is reportedly still
sold.

## Decision

- **Artifact set**: a manifest of path, bytes and sha256 for every file. Its id embeds the hash of
  the *canonical* manifest: without `id` and `acquired`, `files` sorted by path (05 §2; the exact
  serialisation is in [formats/README.md](../../formats/README.md)). `artifacts/known.json` in the
  game repo commits the hashes, never the bytes. Runtime writes observed after registration make a
  successor set (U21).
- **Derived variants** (patched binaries) carry a recipe: base set, script and commit, options,
  output sha256. The build asserts the input bytes at every patch site and fails on an output-hash
  mismatch.
- Every run record, finding and evidence manifest names its **set and variant**.
- **Original game files never enter any repository.** Automatic download is not assumed acceptable.
  An artifact is registered locally by hashing a copy the user supplied.
- **A rights decision per game** sets:
  - where the originals may live;
  - whether they may reach cloud machines;
  - what may be published.
- **Isle Wars and Isle Wars Pro** (U2, U3, U5, U11, U22):
  - no licence: they are explored, never copied;
  - the originals stay on the user's own machines;
  - the reference copies are the shareware/unregistered releases;
  - the research repo is private, and evidence bundles are release assets on it;
  - an original game inspired by them (malpaco) is a goal. Their code, assets, text and name are
    never reused. Only behaviour and design learned pass to it, never evidence.
- **Evidence bundles** are content-addressed and verified on download.
- **`imp_conquest_fixtures`** becomes private (U1), after its IC2 consumers move to authenticated
  access.

## Consequences

Reproducing a run is mechanical. Each step fails loudly on a hash mismatch:

1. game repo at the run's commit;
2. bootstrap;
3. preflight verifies the artifact by hash;
4. rebuild the variant from its recipe;
5. fetch the start state by hash;
6. run the script with the recorded arm and seed.

What stays manual: acquiring the original, one-time logins, and human confirmation.
