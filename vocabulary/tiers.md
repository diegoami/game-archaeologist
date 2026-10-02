# Verification tiers

Source: [docs/phase0/03-work-execution.md](../docs/phase0/03-work-execution.md) §6.4; [ADR-004](../docs/adr/004-execution-environment.md); user decision U8.

## Legend

| Tier | Where | Example |
| --- | --- | --- |
| `V0` | ordinary CI | toy target tests, schema validation, synthetic save parsing |
| `V1` | CI with a private fixture subset | real-save parser tests (the IC2 `ic2-test-fixtures` pattern) |
| `V2` | headless original artifact (Wine or an emulator, cloud or local) | an automated experiment rerun |
| `V3` | original on the reference platform | a Win9x game on Windows. For Isle Wars Pro it is required only for timing, rendering and UI claims (U8). |
| `V4` | human confirmation | visual or audio behaviour, UI legibility |

## Rules

- A task's Done-when names the tier it requires.
- Every review states the highest tier it reached. Nothing silently skips.
- A review that cannot reach the required tier says so. The main session then routes the remainder
  to a machine that can, as a follow-up review task.
- A finding records its tier in its header (`Tier reached`).
