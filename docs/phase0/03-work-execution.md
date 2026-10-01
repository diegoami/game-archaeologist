# 03 · Work execution architecture

Baseline: `harness_imperial` as it is. This document states only what is **kept**, what is
**added** (and where), and why. Additions marked **[H]** are upstream harness changes; **[M]** live
in the meta repo's method docs; **[G]** in each game repo.

## 1. Roles

| Role | Who (default) | Does | Must not |
| --- | --- | --- | --- |
| **Architect / main session** | Claude, the session the user talks to — one per machine | architecture, decomposition, task contracts, dependencies, claims, dispatch, triage, merge, promotion of reviewed findings into the spec, escalation to the user | work inside an agent's worktree; review its own contract-tier change; decide a design/research question the user owns |
| **Implementer** | OpenCode via `implement.mjs` (Claude fallback) | one bounded code/env task on one branch, one PR | invent missing architecture; weaken a Done-when; touch files outside Owns (stop and report instead) |
| **Researcher** **[H/M]** | Claude agent (Sonnet) by default; OpenCode only for mechanical sweeps | one bounded question or experiment: runs it, pushes raw evidence **before** writing interpretation, drafts a finding with status `proposed` | promote its own finding; edit `spec/`; widen the question; report an inference as an observation |
| **Implementation reviewer** | Claude agent or OpenCode, never the implementer's family | harness §5 gates at an exact SHA | review another tree; relay a subset |
| **Research reviewer** **[M]** | Claude agent (Opus for first findings of a game), never the researcher's family where possible | attempts to falsify: identity, reproduction of selected runs, alternative explanations, scope (§6.2) | accept prose without raw evidence; rerun only the runs the researcher picked |
| **User** | Diego | design and research-direction decisions, artifact acquisition and licensing, repo creation, machine provisioning, human visual confirmation | — |

Why researchers default to Claude: a research task's core work is judgment (choosing what not to
conclude). IC2's corrections came from reviewers and research, not implementers (incident 1). This
is a provisional default; the harness's measurement rule (§9, L13) decides later.

## 2. Task contract

### 2.1 Mandatory core (every kind)

The harness template, unchanged, plus **one** line (`Runs on`) and an optional **Why**:

```markdown
# T<nn> <Title>
- **Kind**: architecture | feature | correction | infrastructure | environment | runtime | research | research-review
- **Issue**: #<n> · **Branch**: `task/T<nn>-<slug>` · **Start after**: … · **Merge after**: T<nn>, owner/repo#<n>
- **Implementer**: … · **Reviewer**: … (never the implementer's family)
- **Why**: one or two sentences — what this unblocks.
- **Evidence**: the excerpts this task rests on, PASTED with source@commit (not links alone).
- **Owns**: directories or files.
- **Scope**: what to do. **Not in scope**: what it is easy to confuse with it.
- **Done when**: numbered; each line one command-checkable assertion with its expected result.
- **Hazards**: the likeliest mistake and how to avoid it.
- **Runs on**: <requirement tokens> · cloud: <class> · network: <class> · GitHub: <scopes>
```

`Runs on: base` is the default and expands to: `tool:git tool:gh tool:node@>=20 gh:push gh:pr
net:github net:provider` · cloud: `C0` · network: `N2`. **Most tasks write `Runs on: base` and
nothing else.** This keeps normal implementation boring (principle 18).

What was deliberately *not* made mandatory: hardware, external-service lists, artifact sections,
reviewer-requirement prose, merge conditions. They are either implied by `Runs on`, uniform (merge
= approving review + green CI, harness rule 7), or only meaningful for some kinds (below).

### 2.2 Kind extensions

**`research`** adds:

```markdown
- **Question**: one falsifiable question.
- **Hypotheses**: H0 (null) and H1…Hn, each with the observation that would distinguish it.
- **Artifact**: <artifact-set id> (sha256 of the set manifest) and the variant actually run.
- **Runtime**: driver@commit, platform, max intervention level allowed (I0–I3), and why.
- **Design**: start state (id + sha256), control, arms/treatments, n per arm, stopping rule.
- **Measurements**: the raw quantities, how each is read, and its source (screen/save/memory/static).
- **Outputs**: run records, evidence bundle id, `findings/F<nnn>-*.md` with status `proposed`.
```

Its Done-when lines are about **records, not conclusions**: "N run records validate against
`run/1`", "the evidence manifest's hashes match the uploaded bundle", "the finding's Answer cites
only run ids present in `runs/`". A research task cannot have "H1 is true" as a Done-when line.

**`research-review`** adds: `Finding under review` (path@sha), `Reruns` (which runs the *reviewer*
selects, with a minimum, e.g. ≥1 control and ≥1 treatment), `Machine` (independent machine or
session where the tier requires it).

**`environment` / `runtime`** add: `Target capability` (the tokens this task makes verifiable) and
a Done-when line that is a **preflight run proving it** on the stated machine class.

**`architecture`** adds: `Decisions` (what the task decides) and `Escalate` (questions that go to
the user, not decided by the task).

### 2.3 Dependencies and Owns

Kept from IC2/harness: **Merge after** (hard), **Start after** (soft, may reference evidence
— "after W04's state inventory is merged"), **never in flight with**. Cross-repo dependencies are
written `owner/repo#<issue>` and checked by the main session (the harness checks same-repo T-ids).
Owns at directory/file granularity (L5). Research tasks own their `experiments/E<nnn>-*/`,
`runs/E<nnn>-*`, `evidence/E<nnn>-*` and `findings/F<nnn>-*` paths; **no task but a promotion
task owns `spec/`**.

## 3. Task lifecycle

```
blocked ──deps merged──► ready ──preflight ok + claim won──► in-progress ──PR──► in-review
   ▲                                   │ stop & report                         │
   │                                   ▼                                       ▼
   └──── contract amended on main ◄── (main session) ◄── rework ◄──── approved | rework | user decision
                                                                               │
                                                     green CI + squash ──► merged ──► (research) promote
```

Labels: the harness set unchanged (`status:*`, `review-round:{1,2}`, `task`, `bug`, `fix`,
`triage:needed`) plus **[H]** `machine:<id>` (IC2) and **[M]** `kind:research` (filter only). No
capability labels: the task file's `Runs on` line is authoritative and machine-checkable; IC2's
`local-only`/`single-instance` become tokens (`artifact:…`, `exclusive:…`).

## 4. Self-contained handoff (the brief)

The main session writes the brief to a temp file; the brief **contains**:

1. the task file **pasted in full** (L18), whose Evidence section already holds the pasted
   excerpts of architecture/contracts/evidence the task needs;
2. the role block (harness §4 implementer block, or the research/review blocks in §6);
3. **[H]** the identity block: repo, branch, base SHA, worktree path, claim id, machine id;
4. **[H]** the preflight summary for this task on this machine (tokens and verdicts, no paths, no
   secret values);
5. on rework: the **full** prior review comment(s), pasted (rule 8), and any contract amendment
   commit with its reason;
6. for research review: the finding at its SHA, the run records, the evidence manifest.

Budget: the whole brief < ~20k tokens (rule 16). If the necessary excerpts do not fit, the task is
too big — split it; do not send pointers.

## 5. Durability and resumability

**Invariant: nothing needed to continue lives only on one machine.** Local state (Wine prefix,
calibration caches, Ghidra project) must be *reproducible by bootstrap*, never *essential to
continue*.

| Checkpoint | Persisted as | Lets another machine… |
| --- | --- | --- |
| Claim | claim ref + `machine:<id>` label + claim comment (preflight summary, lease) | see who holds it and since when |
| Each meaningful step (each Done-when line, IC2 App A) | commit **pushed** to the task branch | resume from the last push (`implement.mjs` already resumes) |
| Research: each run | run record committed + raw bundle uploaded **before** interpretation | rerun or reinterpret without the original machine |
| Stop & report | issue comment with the report; branch pushed | decide amendment vs re-dispatch |
| PR | PR body (scope, Done-when evidence) | review |
| Review | one PR comment + label | rework or merge |
| Rework | `review-round:N` label + review URL | resume the same branch |
| Escalation | `status:escalated` + issue comment with options | user decides from GitHub alone |
| Release / takeover | claim comment + ref change | resume |

Recovery is IC2 §5's table, unchanged, plus: a claim whose lease expired with no pushes is
reclaimable (§7.4). An existing task branch is **always resumed, never recreated** (harness).

## 6. Review

### 6.1 Implementation review — harness §5, unchanged

Gate 0 tree proof at SHA; re-run every Done-when; provenance of constants; determinism; scope vs
Owns; sweep (mutation after clean rebuild, dead branches, edge comments). Added for this project:
**dependency correctness** (a Merge-after task's interface actually used as merged) and, for
`environment`/`runtime` tasks, **the reviewer runs preflight for the target tokens on a machine of
the stated class** — or records that it could not and which tier it reached (§6.4).

### 6.2 Research review — different protocol [M]

Same mechanics (detached worktree at the PR head, one comment, label), different gates:

0. **Tree and record identity.** HEAD = the named SHA; run records validate; evidence manifest
   hashes match the stored bundle (download and hash ≥1 file).
1. **Artifact identity.** The run records' artifact-set id and variant hash match `artifacts/known.json`
   and the task's Artifact line. A patched variant is named as such.
2. **Environment identity.** Runtime fingerprint (driver commit, platform, emulator/Wine version)
   recorded; differences from the reviewer's environment stated.
3. **Reproduction.** The **reviewer selects** ≥1 control and ≥1 treatment run (not those the
   researcher highlighted) and reruns them; raw measurements compared field by field. A stochastic
   claim needs a rerun of the statistic, not of one sample.
4. **Raw vs interpretation.** Every sentence in Answer/Inferences traces to a run id; observations
   contain no interpretation; semantic labels on raw values (e.g. "byte 0x8123 = target") cite the
   representation claim they rely on.
5. **Alternatives.** The reviewer writes ≥2 alternative explanations and states whether the design
   excludes each (IC2: UI paint paths writing RandSeed is the canonical confound).
6. **Intervention.** The max intervention level used is declared and justified; an I2/I3 result is
   not stated as untouched-original behaviour without the neutrality argument (06 §3).
7. **Scope.** The claim is no wider than the artifact version, settings, and states tested.

Verdict has **two axes**, so the harness machinery is reused unchanged:
- **record verdict** (line 2, harness vocabulary): `approve` | `approve after named fixes` |
  `rework` | `user decision` — is the record sound?
- **claim outcome** (line 3): `supported` | `supported, narrowed: <narrowing>` | `inconclusive` |
  `refuted` — what does the sound record establish?

A refuted or inconclusive finding with a sound record is **approved and merged**: a negative
result is a result. Only promotion (§6.3) moves claims into `spec/`.

### 6.3 Promotion

After merge, the main session (not the researcher, not the reviewer) updates `spec/<area>.md`:
adds or changes the claim row with status, scope, basis and finding links. A promotion commit on
`main` with the reason (L6 pattern) — no PR, because the review already happened; the claim row is a
transcription, checked by the next research review that touches it.

### 6.4 Verification tiers (shared by both reviews)

Every review states the highest tier it reached; nothing silently skips.

| Tier | Where | Example |
| --- | --- | --- |
| V0 | ordinary CI | toy target tests, schema validation, synthetic save parsing |
| V1 | CI with private fixture subset | real-save parser tests (IC2 `ic2-test-fixtures` pattern) |
| V2 | headless original artifact (Wine/emulator, cloud or local) | automated experiment rerun |
| V3 | original on the reference platform | Win9x game on Windows. For Isle Wars Pro, required only for timing, rendering and UI claims (U8); IC2 required it always |
| V4 | human confirmation | visual/audio behaviour, UI legibility |

A task's Done-when names the tier it requires; a review that cannot reach it says so and
the main session routes the remainder to a machine that can (a follow-up review task).

### 6.5 Defect classes and escalation

| Reviewer finds | Class | Route |
| --- | --- | --- |
| Code/record does not meet a sound contract | **implementation defect** | `rework` on the same branch (≤2 rounds, then escalate) |
| The contract is wrong, impossible, or under-specified (wrong Owns, untestable Done-when, missing evidence excerpt) | **task-contract defect** | finding labelled `C<n>` → main session amends the task on `main` with reason (L6); if the change is to Done-when semantics, the user is told; then re-dispatch |
| The task cannot be done without a decision no document makes (where code belongs, a new format field, a new capability class) | **architectural uncertainty** | verdict `user decision`; main session opens an `architecture` issue in the meta repo with options + recommendation; task `status:blocked`; never decided inside the task (principle 16) |
| The method is sound but the evidence does not decide the question | **research uncertainty** | not a defect: claim outcome `inconclusive`, finding merged; a new research-question issue (`triage:needed`) names what would decide it |

## 7. Multi-machine operation [H]

### 7.1 Identity
`HARNESS_MACHINE` env var (IC2's `IC2_MACHINE`, renamed generic) + `machine:<id>` label. Stable,
short, non-identifying (`desk`, `rogx`, `wsl-desk`, `cloud-<n>`). Same GitHub account on all
machines (as today), so assignees cannot distinguish machines.

### 7.2 Discovery
`gh issue list --label task --label status:ready` → for each, read the task file's `Runs on` →
`preflight --task T<nn>` locally → keep those that pass. A `--json` mode lets the main session sort
by dependency order. No shared inventory needed: what a machine can do is verified locally.

### 7.3 Claim transaction (provisional; validated in H4 by a two-machine race test)

Labels are not compare-and-set: two machines can both add their label, both re-read, and IC2's
"second backs off" has no defined "second". Git ref creation **is** compare-and-set:
`POST /repos/{o}/{r}/git/refs` fails with 422 if the ref exists.

1. Preflight passes for the task (fail before claiming).
2. Create `refs/heads/claim/T<nn>` at `origin/main`'s SHA via the API. **201 → won. 422 → held;
   stop.**
3. Add `machine:<id>` and `status:in-progress`; post the claim comment:
   `claim T<nn> machine=<id> at=<iso8601> lease=24h preflight=<token:verdict,…>`.
4. Work. Every push to the task branch or comment on the issue renews the lease.
5. **Release** (stop, escalation, user request): comment `release …`, remove the label, delete the
   claim ref. The task branch stays — it is the resumable state.
6. **Merge**: the claiming machine merges (IC2 rule), deletes the claim ref; the label stays as history.

### 7.4 Abandoned claims
A claim is *stale* when its lease expired with no push and no comment. Takeover requires the
primary machine's main session or the user: comment `takeover T<nn> from <old> by <new>`, delete
the claim ref, then create it (step 2 — if another taker won, stop), swap labels, **resume the pushed
branch**. Unpushed work on the old machine is, by the durability invariant, non-essential.

### 7.5 What may run concurrently
IC2 §8, unchanged: disjoint Owns (implicit ownership included), no "never in flight with", no seam
redefinition, one task per machine unless the task is `exclusive`-free and the machine declares
`concurrency>1`. `exclusive:<resource>` tokens (e.g. `exclusive:wine-display`) replace
`single-instance`: preflight fails if a process holding that resource is running.

### 7.6 Roles of machines
The machine set changes over time (U7), so no machine is named in any document. One **primary**
(triage, plan changes, takeover authority — IC2's rule) is designated by a repository variable,
`gh variable set HARNESS_PRIMARY --body <machine-id>`. It is GitHub-visible, readable by every
machine (`gh variable get HARNESS_PRIMARY`), and moved only by the user. If the primary machine is
retired, the user moves the variable; no document changes. Other machines claim and merge their own
tasks and may amend only their own claimed task's contract. Cloud sessions are full main sessions
for `C0`/`C1` tasks (unlike IC2, where they claimed nothing) once H4 exists, because the claim is
now safe.
