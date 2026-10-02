# ADR-007 Evidence provenance: raw records, interventions, representation claims

- **Status**: Accepted 2026-10-02. The record fields are provisional until A6.
- **Source:** [docs/phase0/06-research.md](../phase0/06-research.md) §1–3, §5–8; [05-artifacts.md](../phase0/05-artifacts.md) §4

## Context

In IC2:
- `results.json` kept 1 of 4 seeds;
- a lossy dictionary dropped units;
- results carried no build hash;
- always-on patches (instant battles) were never shown to be behaviour-neutral;
- experiment artifacts lived on one disk.

Interpretation and raw observation must stay separable, so that a wrong interpretation can be fixed
without losing evidence.

## Decision

- **Run records are immutable, raw-only, one file per run** (`run/1`). Each names:
  - the code commit, machine, artifact set and variant;
  - the runtime fingerprint;
  - its interventions;
  - the start state (id, sha256, how it was restored), the seed;
  - the action script (hash and arguments);
  - the observations and the output hashes.
  
  Raw records carry no interpretation fields.
- **Interventions**, recorded per run:
  - I0: pure observation;
  - I1: passive instrumentation;
  - I2: harness-enabling, claimed neutral;
  - I3: behaviour-altering.
  
  A finding states its maximum level. A spec claim resting on I2/I3 evidence needs corroboration at a
  lower level, or a cited neutrality argument.
- **Decoding a raw value** (for example "byte 0x8123 is the target") cites a *representation claim*,
  `R<nnn>` in `spec/representation.md`, with the same lifecycle as any other claim.
- **Raw before interpretation**: run records and bundles are pushed before the finding that
  interprets them.
- **Evidence bundles** are content-addressed in the game's evidence store. Their manifests are the
  index.
- **Static analysis** names the binary sha256 and an address or symbol, never a line number in a
  regenerated dump. Its scripts are committed.
- **Experiments are code**, with no DSL.
- **Branching experiments** declare one start state and several arms, and record each arm's restored
  state hash. Restoration is a per-game capability that names everything it reinstates.

## Consequences

If a representation claim is refuted, every finding that cites it can be found (`grep R<nnn>`) and
reinterpreted from unchanged raw evidence.
