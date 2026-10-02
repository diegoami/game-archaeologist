# ADR-001 Repository topology and dependency direction

- **Status**: Accepted 2026-10-02
- **Source:** [docs/phase0/02-project-architecture.md](../phase0/02-project-architecture.md) §1–4; user decisions U4, U5, U10, U12

## Context

Four concerns need homes: the development/research workflow (A), the generic archaeology method (B),
game-specific archaeology (C), and artifacts and evidence (D). IC2 split one game across three repos
(research, bot, build), and findings travelled between them by hand-relayed prompts. A monorepo would
give every game one visibility and send every game to every cloud session, but IC2 is a freeware
repack and Isle Wars is private and unlicensed.

## Decision

| Repository | Holds | Never holds |
| --- | --- | --- |
| `harness_imperial` | the process: template, runners, lessons, and the upstream changes H2–H6 | anything naming a game, emulator or archaeology concept |
| `game-archaeologist` (this repo) | ADRs, record formats, vocabularies, the toy target's description and released hashes, archaeology lessons | game code, artifacts, its own orchestration code, the toy's source or sealed rules |
| one repo per game (`isle-wars-archaeology`) | runtime driver, patches with recipes, parsers, experiments, run records, evidence manifests, findings, spec, knowledge map, known artifact hashes | original bytes, derived binaries, credentials, machine paths |
| `toy-archaeology` | what a game repo holds, for the toy (walking skeleton) | the toy's source or sealed rules |
| `toy-target` (private) | the toy's source, `SEALED.md`, tests, release build | anything a researcher's credentials can reach |
| per-game private stores | originals only where the game's rights decision allows; evidence bundles | — |

Dependencies point one way:
- a game repo pins this repo's formats by tag and copies the harness at a commit;
- nothing depends on a game repo;
- this repo never imports game code;
- the harness knows nothing of archaeology.

## Consequences

- Each game chooses its own visibility, machines and cadence. Its research stays readable without
  any tooling, because records carry schema ids and findings are Markdown.
- The IC2 repositories are not migrated.
- The three new repos are approved, each created when its milestone starts: `toy-archaeology` (M2),
  `toy-target` (M2, private), `isle-wars-archaeology` (W0, private). This repo was renamed from
  `games_revival_framework`.
