# E001 east-island (fabricated)

- **Task**: none (calibration case)
- **Question**: Does holding every province of the east island change the reinforcements a player
  receives at the start of a turn in Example?
- **Hypotheses**:
  - H0: no; the count depends only on what the treatment does not change. Distinguished by equal
    counts in both arms.
  - H1: holding the whole east island adds a fixed bonus. Distinguished by a constant difference
    between the arms.
- **Artifact**: set `example-1.0-…` (see `artifacts/known.json`), variant none
- **Runtime**: `runtime/example.py@0000000`; maximum intervention level I3, because crafting a save
  is the only way to give the player the whole east island.
- **Design**:
  - control: a new game, default settings; the player holds 3 provinces, none of them a whole island;
  - treatment: a crafted save in which the player holds the whole east island (3 provinces);
  - n per arm: 2. Stop after 2 runs per arm.
- **Measurements**: the reinforcement count shown in the turn-start prompt (ui-text), and bytes
  0x20–0x21 of the save (save).
- **Outputs**: `runs/E001/`, `findings/F001-*.md`
