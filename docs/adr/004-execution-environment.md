# ADR-004 Execution environment: requirement, declaration, verification

- **Status**: Accepted 2026-10-02. The capability token list is provisional until A6.
- **Source:** [docs/phase0/04-environment.md](../phase0/04-environment.md); the verification tiers from [03-work-execution.md](../phase0/03-work-execution.md) §6.4; user decisions U7, U8

## Context

Every environment failure in IC2 and the harness was "installed is not usable":
- an OpenCode Go login that listed no models;
- `pip … || true` leaving capstone missing;
- a Wine prefix without a user profile;
- the Windows OpenCode shim on the WSL `PATH`.

Machines differ in software, artifacts and permissions, and the machine set changes over time (U7).

## Decision

- **Three distinct things**:
  - the task's *requirement*, in its `Runs on` line (committed);
  - the machine's *declaration*, in a local `machine.json` (never committed: paths and restrictions
    stay local);
  - the *verified* capability, from preflight, run now.
- **Tokens** are `<category>:<name>[@<constraint>]`. The categories are os, arch, tool, facility,
  exclusive, hw, artifact, svc, net and gh. Version constraints are used only where compatibility
  matters.
  - Generic checks live in the harness.
  - Game tokens live in the game repo's `capabilities.json` as check commands.
  - `svc:` checks reuse the harness's `prepareOpenCode()`.
- **Preflight** runs before a claim. It is cheap by default (`--deep` may spend, and says so). It
  never prints secret values or local paths.
  - Only `verified` tokens pass.
  - Exception: a closed list of declaration-only tokens (`facility:desktop`, `facility:audio`).
  - `gh:pr` is proved early, by a draft PR opened right after the claim.
- **Cloud suitability is a property of the task**:
  - C0: any cloud session;
  - C1: plus a private CI fixture subset;
  - C2: plus the original, only where a game's rights allow it (never Isle Wars);
  - C3: a local research machine;
  - C4: a human present.
- **Network is a property of the task**: N0 none, N1 GitHub, N2 GitHub plus provider, N3 package
  registries, N4 web. A host enters a class only with its source (documentation or a logged run).
- **GitHub access is least privilege by task kind**, with a separate read-only token for each
  private store.
- **Agent runs receive only the environment variables their tokens need** (H2).
- **Bootstrap profiles** are token bundles with idempotent setup scripts that end in preflight.
  Pin versions only where results depend on them.
- **Workstation security**:
  - no self-hosted Actions runners on research workstations;
  - N4 research runs on C0 machines;
  - Wine prefixes for originals have no `Z:` drive.
- **Verification tiers**:
  - V0 CI;
  - V1 private-fixture CI;
  - V2 headless original;
  - V3 reference platform; a Wine-only Isle Wars Pro result needs V3 only for timing, rendering
    and UI claims (U8);
  - V4 human.
  
  A review states the tier it reached; nothing silently skips.

## Consequences

"Can this machine run this task now?" has one answer, from one command, before any expensive work.
No shared machine inventory is kept; the claim comment records each machine's preflight summary.
