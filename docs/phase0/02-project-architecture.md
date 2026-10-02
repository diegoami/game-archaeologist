# 02 · Project architecture

## 1. The four concerns, and where each lives

| Concern | Home | Rationale |
| --- | --- | --- |
| **A. Development/research workflow** — task contracts, `/run-task`, runners, review, labels, worktrees, provider fallback, *plus* (new) claims, preflight, env allowlist, version lock; research task kinds only after the toy and Isle Wars repos have used them | **`harness_imperial`** (existing), copied into every repo that runs tasks | Already solved and tested; the gaps are process-generic, not archaeology-specific (01 §1). |
| **B. Generic archaeology method** — record *formats* (run, evidence manifest, finding, claim), status/intervention vocabularies, research-review protocol, capability vocabulary for archaeology, the toy target, ADRs | **meta repo** (`games_revival_framework`, renamed `game-archaeologist` at A1 — U4) | Needs one owner; it is what makes two games' evidence comparable. Mostly documents and schemas; code only after two consumers. |
| **C. Game-specific archaeology** — runtime driver, patches, parsers, memory maps, experiments, findings, specification | **one repo per game** (e.g. `isle-wars-archaeology`, which covers both DOS *Isle Wars* and *Isle Wars Pro* — U3) | Different artifacts, permissions, machines and cadence per game; research must stay usable if the framework changes. |
| **D. Artifacts/evidence** — originals, private fixtures, evidence bundles | **private stores per game**, chosen per game's rights (05-artifacts) | Redistribution differs per game (IC2 freeware repack vs Isle Wars: no licence, originals never leave the user's machines — U2). |

**Decision:** the meta repo contains **no task-orchestration code** (ADR-002). Every
orchestration gap is filed against `harness_imperial`.

## 2. Topologies evaluated

| Option | For | Against | Verdict |
| --- | --- | --- | --- |
| **Monorepo** (method + all games) | one clone, atomic cross-cutting changes | one visibility for everything (IC2 is freeware, IWP is sold, research may be public); every cloud session receives every game; labels/issues mixed across games; a game's history tied to others | **Rejected** |
| **Generic library + one repo per game** | clean reuse | presumes a library before there is repeated code (01 §7.5); version coupling from day one | **Rejected for now**; becomes this once extraction is justified |
| **Harness + independent game repos, no meta repo** | minimal | formats, ADRs, toy target and research-review protocol have no owner; each game reinvents tags (IC2 already has two schemes) | **Rejected** |
| **Harness (process) + small meta repo (method) + per-game repos + per-game private stores** | each concern has one owner; visibility per game; game repos read without tooling | one more repo to keep in step | **Recommended** |
| IC2's split per game (research repo + bot repo + build repo) | separation of concerns | findings hand-relayed by pasted prompts; duplicated docs drift (01 §3, §4) | **Do not repeat** for new games |

## 3. Recommended topology

```text
                     ┌──────────────────────┐
                     │   harness_imperial   │  concern A (process)
                     │  template/ + tools/  │  versioned by commit; copied in
                     └──────────┬───────────┘
              copies (pinned)   │   copies (pinned)
          ┌─────────────────────┼─────────────────────────┐
          ▼                     ▼                         ▼
┌────────────────────┐ ┌─────────────────────┐  ┌──────────────────────┐
│ meta repo          │ │ toy-archaeology     │  │ isle-wars-archaeology│  concern C
│ (game-archaeologist)│ │ (walking skeleton) │  │ DOS IW + IW Pro      │
│ ADRs, formats,     │ │ driver, experiments,│  │ driver, experiments, │
│ schemas, toy hashes│ │ findings, spec      │  │ findings, spec       │
└─────────┬──────────┘ └──────────┬──────────┘  └──────────┬───────────┘
          │ formats@tag            │ pins formats@tag       │ pins formats@tag
          └──────────────►─────────┘◄───────────────────────┘
                                                            │ hash-referenced
                                                ┌───────────▼────────────┐
                                                │ originals: user's own  │ concern D
                                                │ machines only (U2)     │
                                                │ evidence: releases on  │
                                                │ the private game repo  │
                                                └────────────────────────┘
```

### What each repository holds, and what it must not

**`harness_imperial`** (exists, public)
- Holds: the process template, runners and lessons. After M3 it also holds the five upstream changes
  (H2–H6: env allowlist, `preflight.mjs` with the generic capability tokens, `claim.mjs`, `/run-task`
  wiring, `harness.lock`). The research task-kind brief/review blocks follow later: they go upstream
  only after the toy and Isle Wars repos have used them (§5).
- Never: anything naming a game, emulator, artifact or archaeology concept beyond "a research task
  produces evidence and a finding".

**Meta repo** (exists empty, public: `diegoami/games_revival_framework`, to be renamed `game-archaeologist`)
- Holds: this package; ADRs; `formats/` (JSON Schemas + Markdown templates for run record, evidence
  manifest, finding, spec claim table); `vocabulary/` (claim status, basis, intervention levels,
  verification tiers, archaeology capability tokens); the toy target's *description* and its released
  artifact hashes, but not its source or sealed rules, which live in the private `toy-target` repo (06 §10);
  a small validator once two games use the formats; a cross-game `lessons.md` starting at L200 for
  archaeology-specific lessons (harness lessons stay in the harness).
- Never: game-specific code, original artifacts, a scheduler, an emulator adapter, a generic runtime
  interface before two games implement one.

**`toy-archaeology`** (created at M2 by A5; approved, U10)
- Holds: what a real game repo holds, for the toy target. It exists to rehearse the topology and to
  keep the toy's source out of the researcher's worktree (blindness).
- Never: the toy target's source or sealed rules.

**`toy-target`** (private; created at M2 by A4 — needs approval, U12)
- Holds: the toy game's source, `SEALED.md`, the tests for each hidden rule, and the release build.
- Never: anything a researcher's credentials can reach.

**Per-game repo, e.g. `isle-wars-archaeology`** (created by W0; private, approved — U5, U10)
- Holds: `runtime/` (launch, input, observe, reset, state restore), `patches/` (with manifests),
  `parsers/`, `experiments/E<nnn>-*/`, `runs/` (run records), `evidence/` (manifests only),
  `findings/F<nnn>-*.md`, `spec/<area>.md`, `knowledge-map.md`, `artifacts/known.json` (hashes of
  known artifact sets — hashes are not copyrighted), `capabilities.json` (game-specific capability
  tokens and their check commands), `docs/tasks/`, the copied harness.
- Never: original binaries, ROMs, data files, or anything derived from them that reconstitutes them
  (patched executables); raw evidence bundles unless redistributable (05-artifacts); credentials;
  machine paths.

**Per-game private stores** (05-artifacts): originals only where the game's rights decision allows
(for Isle Wars: nowhere but the user's own machines), evidence bundles (releases or a private repo), a minimal CI fixture subset only when CI
needs one.

### Dependency direction

```
game repo ──pins──► meta repo formats@tag ──► (nothing)
game repo ──copies─► harness@commit
meta repo ──copies─► harness@commit
toy-archaeology ──consumes──► its own release asset: the toy .pyz, copied by hash from the
                               private toy-target repo's release (A5)
game repo ──references by hash──► private stores
```

Nothing depends on a game repo. The meta repo never imports game code. The harness never knows
about archaeology.

## 4. Versioning and propagation

- **Formats** are versioned by a `schema` field in every record (`"schema": "run/1"`) and by tags on
  the meta repo (`formats-v1`). A game repo records the tag it follows in `archaeology.json`.
  A breaking format change ships a new schema id; old records stay valid under their own id and are
  never rewritten. Findings are Markdown and readable without any tooling, so **game research remains
  usable even if the framework changes or is abandoned.**
- **Harness** is copied, not imported. Each repo records the harness commit it copied in a
  `harness.lock` (provisional, H6). Propagation is a deliberate *harness bump* task in the consuming
  repo: diff `template/` between the locked and new commits, apply, re-run `npm test` in the harness
  and the repo's own first-session check. No submodules, no package manager: the harness's own
  design is copy-in, and IC2 shows local divergence is real and sometimes right.
- **Process changes** originate where the lesson occurred: a harness lesson goes upstream to
  `harness_imperial` through its own admission rule (L14); an archaeology method lesson goes to the
  meta repo's `lessons.md`; a game-only lesson stays in the game repo.

## 5. Generalization register

Every proposed generic element, tested against the threshold. **Default is game-specific.**

| Candidate | Required by | Second use? | Why generic now | Harm if left specific | Verdict |
| --- | --- | --- | --- | --- | --- |
| Task claim + machine identity | IC2 (used, §8) | toy/IWP multi-machine; harness has no game | process, not archaeology; already repeated | each repo reinvents a race-prone claim | **Generic now → harness** |
| Task requirements line + preflight | IC2 `local-only`/`single-instance`; harness hook; IC2 "installed ≠ usable" failures | every repo with machine-specific tasks | must exist before claiming across machines | silent wrong-machine runs | **Generic core → harness; game tokens stay in game repo** |
| Research task kinds + research-review brief | IC2 `retrieve-findings` + ic2-conquest findings | toy, IWP | the walking skeleton needs it to test review | review of findings stays informal (IC2 unledgered path) | **Meta repo first; upstream to harness after toy + IWP use it** |
| Finding template | IC2 research dated reports; ic2-conquest findings (converged independently) | already two | already repeated | a third scheme | **Generic now (format)** |
| Claim status / basis / intervention vocabularies | IC2 (two inconsistent schemes) | toy, IWP | cross-game comparability; reviewers need a fixed vocabulary | repeat of IC2's undefined tags | **Generic now (vocabulary)** |
| Run record + evidence manifest schema | IC2 lacked one (overwritten results, unstamped builds) | toy, IWP | the raw-vs-interpretation invariant needs a shape | the IC2 failures recur | **Generic now (schema); provisional fields** |
| Artifact manifest + verify (sha256 per file) | `ic2-test-fixtures/manifest.json`, `pins.txt` | IWP, toy | ~40 lines; identical need | none serious | **Format generic now; code copied into the first consumer, moved to the meta repo when a second consumer copies it** |
| Validator for records | toy + IWP | after M2 | — | reviewers check by hand meanwhile | **Defer to after W-M2** |
| Runtime adapter interface (launch/input/observe/reset) | ic2-conquest only | IWP will have one; Nether Earth/Gain Ground would differ radically | — | none; a premature interface would fit only Wine | **Game-specific. Revisit after two real drivers** |
| Wine/Xvfb toolkit (window discovery, control enumeration, X input) | ic2-conquest | IWP *if* it runs under Wine | — | some copy-paste | **Game-specific; extract when IWP's driver repeats it** |
| Seed/RNG control | ic2-conquest (patch) | toy (flag), IWP unknown | — | — | **Concept generic (intervention record), mechanism specific** |
| Branching experiment runner | ic2-conquest (serial, manual) | toy | — | — | **Experiment *format* supports arms now; runner game-specific** |
| Spec ontology | — | — | — | — | **Not built. Markdown claim tables per area** |
| Scheduler / orchestrator service | — (IC2 built and retired one) | — | — | — | **Never, absent a new demonstrated failure** |

## 6. Language and representation

- **Harness tooling: Node** (existing; runs on Windows, WSL and cloud).
- **Archaeology tooling: Python 3** — every existing IC2 archaeology tool is Python (`sav.py`,
  `driver.py`, `patch_exe.py`, `seed_patch.py`, `ic2disk.py`), stdlib-first.
- **Records: JSON** (+ JSON Schema). Both runtimes parse it natively; the harness already uses
  `harness.json`; no YAML dependency is justified by any requirement found.
- **Human documents: Markdown.** Findings and spec are read by people and agents first.
