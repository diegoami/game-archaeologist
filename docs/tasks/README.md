# Tasks

One file per task, `T<nn>.md`, from [`TEMPLATE.md`](TEMPLATE.md). This index carries no status:
the issue's `status:*` label is the status (`gh issue list --label task --label status:ready`).
Each title ends with the task's plan label (A1, A2, …) from
[`docs/phase0/07-delivery-plan.md`](../phase0/07-delivery-plan.md) §4.

| Task | Title | Issue | Merge after |
| --- | --- | --- | --- |
| T01 | Adopt the harness, record the ADRs, rename the repository (A1) | #1 | — |
| T02 | Formats and vocabularies v1 (A2) | #3 | T01 |
| T03 | Harness bump to 74e53ae (the reviewer without git -C) | #6 | T01 |
| T04 | The research protocol: researcher brief, research review, promotion (A3) | #11 | T02 |
