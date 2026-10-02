# ADR-009 Generalization policy: game-specific by default

- **Status**: Accepted 2026-10-02
- **Source:** [docs/phase0/02-project-architecture.md](../phase0/02-project-architecture.md) §5; [06-research.md](../phase0/06-research.md) §7, §11

## Context

IC2's runtime driver has exactly one consumer. Its process grew layers that each patched a failure the
layer below had created (harness L14). Future targets differ radically:
- Wine and a patch-based seed;
- MAME with frame stepping;
- emulators with savestates and memory maps;
- an in-game programmable machine.

## Decision

- **Game-specific by default.** Something becomes generic only with **two concrete uses**. Code is
  written in its first consumer and moved here when a second consumer copies it.
- **Generic now**:
  - record formats and vocabularies, which converged independently in two IC2 repos;
  - the research-review protocol;
  - the artifact manifest format.
- **Not built until forced**:
  - a runtime adapter interface;
  - an experiment DSL;
  - a scheduler or orchestration service;
  - a specification ontology;
  - a shared experiment runner (Gain Ground's matrices are the likeliest trigger).
- Every proposed generic element is tested against the register in 02 §5:
  - which game needs it;
  - whether there is a second use;
  - why it must be generic now;
  - what leaving it specific would harm.

## Consequences

- This repository stays mostly documents and schemas until the toy and Isle Wars repositories
  repeat something.
- The first extraction review is a planned architecture task at M4.
