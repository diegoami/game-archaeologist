# ADR-003 Task contract: harness core + `Runs on` + kind extensions

- **Status**: Accepted 2026-10-02
- **Source:** [docs/phase0/03-work-execution.md](../phase0/03-work-execution.md) §2–4; [08-example-contracts.md](../phase0/08-example-contracts.md) §7

## Context

A cold agent must be able to execute a task without rereading the project (IC2 incident 14: a pointer
cost ~85k tokens to reach ~1.45k of contract). Tasks here range from code to environment set-up to
behavioural experiments to research reviews, and must say where they can run.

## Decision

- **Core**, every task: the harness template fields, plus:
  - an optional `Why`;
  - an `Evidence` section with excerpts *pasted* with their source and commit;
  - one mandatory **`Runs on`** line.
- `Runs on: base` is the default. It expands to `tool:git tool:gh tool:node@>=20 gh:push gh:pr
  gh:issues gh:labels net:github net:provider`, cloud `C0`, network `N2`.
- **Line grammar**: fields are separated by ` · `.
  - The first field is the requirement tokens.
  - `cloud:` takes one class.
  - `network:` takes one class, or a list of `<class> for <purpose>`; preflight checks the union.
  - `GitHub:` lists `gh:*` tokens.
- **Kind extensions**:
  - `research` adds Question, Hypotheses, Artifact, Runtime, Design, Measurements and Outputs. Its
    Done-when lines test *records*, never the truth of a hypothesis.
  - `research-review` adds the finding under review, reruns chosen by the reviewer, and the machine.
  - `environment` / `runtime` add a target capability, proved by a preflight run.
  - `architecture` adds Decisions and Escalate.
- **Dependencies**: Merge after (hard), Start after (soft, may name evidence), and "never in flight
  with". Cross-repo dependencies are written `owner/repo#<n>`.
- **Owns** is directories or files. No task but a promotion task owns `spec/`.
- A task whose Evidence is "pasted when X merges" stays `blocked` until it is pasted.
- Task ids are per repository (`T<nn>`); the plan label (A1, H3, …) is in the issue title.

## Consequences

Most implementation tasks write `Runs on: base` and nothing else. Machine-specific work states its
needs where preflight can check them.
