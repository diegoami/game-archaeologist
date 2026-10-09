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
| T05 | Formats corrections before formats-v1 (#14 items 1–8) | #15 | T04 |
| T06 | Walking-skeleton retrospective: the score, the method amendments, formats-v1 (A6) | #16 | T05 |
| T07 | A record validator game repositories can call (#10, ADR-009) | #10 | T06 |
| T08 | Harness bump 74e53ae → c6ef85c (L31–L46) | #21 | T03 |
| T09 | register_artifact.py: one artifact registration tool game repositories can call (#23, ADR-009) | #23 | T07 |
| T10 | verify_evidence.py and check_citations.py: shared research tools (#25, ADR-009) | #25 | T09 |
| T11 | check_citations: `static:<path>[:line]` citations (#29, U26) | #29 | T10 |
| T13 | Harness bump 48b788d → 6caba7b (L58, L59, alibaba quota) | #37 | T08 |
| T14 | A7 milestone 1: the two-machine claim race test | #39 | T13 |
| T15 | Harness bump 6caba7b → b8c6cde (minimax quota gate, brief by file L60) | #40 | T13 |
| T16 | Harness bump b8c6cde → ebc5558 (L61, L63, the chooser, readReview #108, --copy folders) | #42 | T15 |
| T17 | Harness bump ebc5558 → b05e0d8 (claim.mjs H4; ADR-005 amendment; T14 reopen) | #44 | T16 |
| T18 | Harness bump b05e0d8 → 467809b (L64, /recommend-driven chooser) | #46 | T17 |
| T19 | Harness bump 467809b → 8b1642c (L65: Luna on OpenAI's main quota) | #48 | T18 |
| T20 | Harness bump 8b1642c → c8d62a7 (/recommend pair field; L51 correction note) | #50 | T19 |
| T21 | Harness bump c8d62a7 → d7ddd48 (L66a per-run scratch, L67 DeepSeek → MiMo, #147, #149) | #52 | T20 |
