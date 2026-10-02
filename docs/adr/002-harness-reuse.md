# ADR-002 Reuse `harness_imperial`; no second orchestration layer

- **Status**: Accepted 2026-10-02. Operational readiness confirmed by H1 (harness_imperial#1: a full real
  `/run-task` loop on `harness-scratch`, 2026-10-02).
- **Source:** [docs/phase0/01-existing-systems.md](../phase0/01-existing-systems.md) §1, §7; [02](../phase0/02-project-architecture.md) §1, §4; user decision U6

## Context

`harness_imperial` already does what this project needs from a process:
- task contracts and `/run-task`;
- an implementer runner that resumes a pushed branch, under watchdogs;
- a reviewer runner that never uses the implementer's model family;
- provider fallback that never retries over work a failed run left behind;
- labels as state;
- a lesson admission rule.

IC2 built an orchestrator and retired it within a day (its incident 13). Three review lineages already
exist (IC2, harness_imperial, malpaco's harness r4).

## Decision

- Every repository in this project adopts `harness_imperial` by copying its template, pinned in
  `harness.lock`.
- The archaeology repositories contain **no** orchestration code of their own.
- Process gaps are fixed **upstream**, each with a lesson from a real failure. The demonstrated gaps
  are five changes:
  - H2: agent env allowlist;
  - H3: preflight;
  - H4: atomic claims;
  - H5: `/run-task` wiring;
  - H6: version lock and bump.
- The research task kinds and their review blocks live in this repo's method first. They go upstream
  only after the toy and Isle Wars repositories have used them.
- A harness update reaches a project only through a deliberate *harness bump* task.

## Consequences

- Process lessons stay in one place (harness `docs/lessons.md`); archaeology-only lessons go to this
  repo; game-only lessons stay in the game repo.
- Local edits to copied harness files are not allowed. Where the harness is wrong, the fix is a
  harness issue.
