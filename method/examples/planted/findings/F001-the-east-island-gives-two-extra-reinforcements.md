# F001 Holding the whole east island gives two extra reinforcements

- **Status**: proposed
- **Question**: Does holding every province of the east island change the reinforcements a player
  receives at the start of a turn?
- **Tests claims**: C-REI-01
- **Experiment and runs**: E001; runs E001-r0001 … E001-r0004
- **Artifact**: set `example-1.0-…` (fabricated), variant none
- **Max intervention**: I0
- **Tier reached**: V2
- **Confidence**: supported — observed, 2 of 2 per arm, alternatives excluded

## Answer

- A player holding the whole east island always receives exactly 2 more reinforcements than one
  holding the same number of provinces without a whole island, in Example 1.0 and 1.1
  (E001-r0003, E001-r0004, E001-r0005).

## Method

Artifact `example-1.0-…`, driver `runtime/example.py@0000000`. Control: a new game with default
settings and seed 7. Treatment: a crafted save giving the player the east island, loaded in a fresh
process. Two runs per arm.

## Observations

| Run | Arm | Prompt | Save bytes 0x20–0x21 |
| --- | --- | --- | --- |
| E001-r0001 | control | You receive 3 armies. | 0300 |
| E001-r0002 | control | You receive 3 armies. | 0300 |
| E001-r0003 | treatment | You receive 5 armies. | 0500 |
| E001-r0004 | treatment | You receive 5 armies. | 0500 |

## Inferences

- The treatment adds 2 reinforcements (E001-r0003, E001-r0004 against E001-r0001, E001-r0002).
- The bonus is fixed: both treatment runs give the same count (E001-r0003, E001-r0004).

## Alternatives considered

- The UI prompt might misreport the count: excluded, because the save bytes agree with the prompt in
  every run.
- The count might depend on the number of provinces held: excluded, because both arms hold 3 provinces.

## What this does not establish

- Islands other than the east island.

## Where the evidence is

The run records in `runs/E001/`.

## Reproduction

`python3 experiments/E001-east-island/run.py --arm control` and `--arm treatment`.
