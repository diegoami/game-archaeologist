# 05 · Artifact architecture

IC2's artifact failures were identity and provenance failures, not storage failures (01 §7.3). So
this architecture is mostly **manifests and hashes**, with storage chosen per game.

## 1. Artifact classes and default policy

| # | Class | Examples | Default store | In a public repo? |
| --- | --- | --- | --- | --- |
| 1 | **Original** executable/ROM/data | `IWP.EXE`, data files, help, ROM dumps | private originals store, or only on the owner's machine | **never** (not even "freeware") |
| 2 | **Derived binaries** | patched EXEs, seed builds, modified saves used as inputs | regenerated locally from (1) + committed patch script + recipe | **never** the bytes; recipe + expected hash yes |
| 3 | **User-generated saves** | saves produced by playing or by experiments | evidence store (private) | small, selected ones only if the game's rights decision allows (they embed game data) |
| 4 | **Screenshots / recordings** | PNG, mp4 | evidence store (private) | a few illustrative screenshots in findings, per game decision (U5) |
| 5 | **Research reports** | findings, spec, knowledge map | game repo | yes (if the game repo is public) |
| 6 | **Generated experimental evidence** | run records, raw measurements, memory dumps, traces, logs | records (JSON) in the game repo; bulky raw bundles in the evidence store | records yes; bundles per class 3/4 |

Automatic downloading of class 1 is **not assumed acceptable**. IC2 was a freeware repack; Isle Wars
Pro is, per malpaco's research, sold today by Soleau Software. Each game has a **rights decision**
that sets: may the original live in a private GitHub store? may it be sent to cloud machines? may
saves/screenshots be published?

**Isle Wars (DOS) and Isle Wars Pro — decided 2026-10-02 (U2, U3):** no licence; explored, never
replicated.

| Class | Isle Wars policy |
| --- | --- |
| 1 Original | the user's own machines only. Never in any repository, store, release or cloud session. Machines are registered by hash, not given a copy. |
| 2 Derived binaries | built locally from the user's copy by committed recipe; never stored or uploaded anywhere |
| 3 Saves / 4 screenshots, recordings | release assets on the private `isle-wars-archaeology` repo (U5: the whole repo is private) |
| 5 Reports / 6 run records | game repo |
| Reimplementation | not a goal; the spec is behavioural only |
| Reference copies | the **shareware/unregistered** releases (U11). Claims are scoped to them; what registration unlocks is `unknown`. |

## 2. Identity

**Artifact set** = the files a runtime needs, as a manifest:

```json
{
  "schema": "artifact-set/1",
  "id": "iwp-<version-label>-<first 8 hex of manifest sha256>",
  "title": "Isle Wars Pro", "version": "as stated by the artifact itself, else 'unknown'",
  "acquired": { "how": "purchased download | user-supplied install | archive item <url> | generated",
                "when": "YYYY-MM-DD", "note": "free text, no personal data" },
  "files": [ { "path": "IWP.EXE", "bytes": 123456, "sha256": "…" } ],
  "runtime_writes": [ "SAVE*.DAT", "IWP.INI" ]
}
```

- The **set id** embeds the hash of the canonical manifest (files sorted by path, without `acquired`).
  Two copies are the same artifact iff their set ids match.
- `artifacts/known.json` in the game repo lists every set ever used, with notes ("demo",
  "registered 1.x", "repack — `.cnt` differs, see F012"). Hashes are committed; bytes are not.
- **Derived variants** get a recipe:

  ```json
  { "schema": "variant/1", "id": "iwp-…-seed", "base": "<set id>", "replaces": "IWP.EXE",
    "recipe": { "script": "patches/seed_patch.py", "commit": "<sha>", "options": ["seed_from_file"] },
    "output_sha256": "…", "interventions": [ { "level": "I3", "what": "Randomize reads SEED.TXT" } ] }
  ```

  The build script asserts input bytes at each patch site (IC2 `patch_exe.py` discipline) and the
  output hash against the recipe; setup **fails** on mismatch (IC2 printed it and moved on).
- Every run record, finding Method section and evidence manifest names the **set id and variant
  id**. A finding cannot be promoted without them (research review gate 1).

## 3. Acquisition and registration

```
user obtains artifact (purchase / own install / archive)        ← manual, C4, documented in W1a/W1b
        ↓
register:  python3 tools/register_artifact.py <dir>             ← per game repo (copied, ~50 lines)
        ↓  computes manifest; matches artifacts/known.json?
        ├─ match → writes the local path into machine.json `artifacts`
        └─ no match → prints the new manifest; a research task decides whether it is a new version
        ↓
preflight token artifact:<set-id> now verifies on this machine
```

Acquisition mechanisms, per game: user-supplied local install (always possible); private
originals store (when the game's rights decision allows; not for Isle Wars); private release asset (same); generated (toy target, crafted
saves); official/archival download (only if its terms permit and U2 says so). Unacceptable: silent
download from an unofficial mirror inside a setup script.

## 4. Stores

| Store | Content | Visibility | Who reads | Who writes |
| --- | --- | --- | --- | --- |
| `<game>-originals` (repo or releases), **optional, and only where the rights decision allows** (not for Isle Wars) | class 1 | private | the owner's machines; C2 cloud only if allowed | user |
| `<game>-evidence` (releases on a private repo; **for a private game repo, its own releases** — Isle Wars) | class 3/4/6 bundles, content-addressed | private | research reviewers, resuming machines (read-only token) | research tasks (release-write token) |
| `<game>-test-fixtures`, **only when CI needs real bytes** | the *whole* subset a test project reads, with `manifest.json` | private | CI via read-only token scoped to it | main session |
| game repo | records, findings, spec, manifests, recipes | public or private (U5) | everyone with access | tasks via PR |

Evidence bundles are uploaded as release assets named by content: `<sha256[:16]>-<name>` in a
release per experiment (`E007`). GitHub's release digests give free server-side sha256. Downloads
are **verified against the manifest** (IC2's fetch script verified nothing). An evidence index is
not hand-maintained: the evidence manifests *are* the index (`evidence/E007/<run>.manifest.json`).

## 5. Cross-machine reproducibility

A capable machine reproduces a run from: the game repo at the run record's commit → bootstrap
profile → preflight (artifact set id verified by hash) → variant rebuilt from recipe (hash
asserted) → start state fetched by hash from the evidence store → the experiment script with the
recorded seed/arm → new run record → compare raw measurements. Every step fails loudly on a hash
mismatch. What legitimately stays manual: acquiring the original, one-time logins, human visual
confirmation.

## 6. The existing IC2 stores

**U1 decided (2026-10-02): `imp_conquest_fixtures` becomes private.** It has 0 forks, so going
private removes every public copy. Not yet executed, because anonymous consumers break:
- `ic2-conquest/setup/setup.sh:32` clones it over plain `https://` → needs an authenticated clone
  (`gh repo clone`, or a read-only token in cloud sessions);
- `ic2-conquest/docs/opening-prompt.md:23` downloads release assets with plain `curl` → `gh release
  download` with a read-only token;
- `imperial-conquest-2-research/docs/evidence-index.md` links release assets → links work only for
  the owner; the index stays correct as a name → release map.

Those fixes are IC2 work, outside this project's backlog; the flip itself is one command
(`gh repo edit diegoami/imp_conquest_fixtures --visibility private --accept-visibility-change-consequences`),
run when the user says so.
