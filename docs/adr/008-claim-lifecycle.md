# ADR-008 Claim lifecycle, research review, and promotion to the specification

- **Status**: Accepted 2026-10-02
- **Source:** [docs/phase0/03-work-execution.md](../phase0/03-work-execution.md) §6; [06-research.md](../phase0/06-research.md) §4, §9; user decision U8

## Context

IC2 used two tag schemes with no legend in the research repo, and five styles of correction. Findings
reached its canonical reports through an unledgered path that skipped independent review. Its research
intake did treat each draft as "a claim, not evidence", and that worked.

## Decision

- **Claim status**, one of:
  - `unknown` (the explicit default);
  - `documented`;
  - `hypothesis`;
  - `supported` (one reviewed method);
  - `corroborated` (two independent methods);
  - `refuted`;
  - `contested`;
  
  plus a `superseded-by` link.
- **Basis**: `doc`, `observed`, `parsed`, `static:*`, `intervened`, `quantified: N of N`.
- **Scope**: the artifact set and variant, settings, and preconditions.
- **Findings**:
  - `inconclusive` is a finding outcome, not a claim status;
  - each finding carries a one-line `Confidence:` statement (outcome, basis, agreement, alternatives
    excluded), not a number;
  - corrections use one style, `> **Correction (date, finding):**`.
- **Research review** tries to falsify. Its gates:
  0. the tree at the named SHA, and the record hashes;
  1. artifact identity;
  2. environment identity;
  3. reruns the *reviewer* selects;
  4. raw versus interpretation;
  5. at least two alternative explanations;
  6. the intervention level;
  7. the scope.
- **The verdict has two axes**: the record verdict (harness vocabulary) and the claim outcome
  (`supported`, `supported, narrowed`, `inconclusive`, `refuted`). A refuted or inconclusive finding
  with a sound record is merged.
- **Defect classes** each have a route:
  - an implementation defect goes to rework;
  - a contract defect means the main session amends the task on `main`;
  - architectural uncertainty becomes a user decision and an `architecture` issue here;
  - research uncertainty means an inconclusive finding plus a new question.
- **Promotion**: only the main session writes `spec/`, after review. The spec is Markdown claim tables
  per knowledge-map area, with no ontology.

## Consequences

Unknown stays visible. Every specification claim traces to reviewed findings and, through them, to
raw evidence.
