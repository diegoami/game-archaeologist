# Architecture decision records

Accepted on 2026-10-02 by the user, after two independent reviews by other model families (DeepSeek V4
Pro and GLM-5.3) whose findings were applied
([docs/phase0/README.md](../phase0/README.md), "Independent review"). Each ADR transcribes the
accepted text of the Phase 0 package and names its source section. The package stays as the full record.

| ADR | Decision | Provisional part |
| --- | --- | --- |
| [001](001-repository-topology.md) | Repository topology and dependency direction | — |
| [002](002-harness-reuse.md) | Reuse `harness_imperial`; no second orchestration layer | — (readiness confirmed by H1) |
| [003](003-task-contract.md) | Task contract: harness core + `Runs on` + kind extensions | — |
| [004](004-execution-environment.md) | Execution environment: requirement, declaration, verification | token list, until A6 |
| [005](005-multi-machine-claims.md) | Multi-machine claims: atomic ref, label, lease | mechanism, until H4's race test |
| [006](006-artifact-identity.md) | Artifact identity, derived variants, per-game rights | — |
| [007](007-evidence-provenance.md) | Evidence provenance: raw records, interventions, representation claims | record fields, until A6 |
| [008](008-claim-lifecycle.md) | Claim lifecycle, research review, promotion to the specification | — |
| [009](009-generalization-policy.md) | Generalization policy: game-specific by default | — |

A new ADR is written only for a decision that constrains future work. Superseding one means a new ADR
that names the old one; the old file gets a `Superseded by` line and is otherwise left as it is.
