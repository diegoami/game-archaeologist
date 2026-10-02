# game-archaeologist

The method for **evidence-backed behavioural specifications of old computer and arcade games**. The
original game is the ground truth. Questions become controlled experiments on the original, and
experiments become raw evidence. Findings from that evidence are independently reviewed before any of
them becomes a specification claim. Unknown stays unknown.

This repository holds the method, not any game:

- [docs/adr/](docs/adr/): the architecture decisions (ADR-001..009, accepted 2026-10-02);
- [docs/phase0/](docs/phase0/README.md): the Phase 0 architecture package these ADRs come from,
  including its analysis of the Imperial Conquest 2 projects, two independent reviews, and the
  user's decisions;
- [docs/tasks/](docs/tasks/README.md): this repository's tasks; their status is on the GitHub issues.

Work runs through [harness_imperial](https://github.com/diegoami/harness_imperial), copied here and
pinned in [harness.lock](harness.lock). The process is [docs/process.md](docs/process.md).

Game research lives in one repository per game (the first is Isle Wars / Isle Wars Pro, which is
private). Original game files never enter any repository.
