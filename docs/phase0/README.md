# Game archaeology — Phase 0 architecture package

Status: **proposal for review**. Nothing here has been implemented; no repository was created or
migrated. Written 2026-10-02 from fresh clones of `imperial-conquest-2-research`, `ic2-conquest`,
`imp_conquest_fixtures`, `imperial_conquest_2`, `harness_imperial`, plus `imp_conquest_original`,
`ic2-test-fixtures` (private stores) and `malpaco` (the earlier Isle Wars attempt).

| File | Contents |
| --- | --- |
| [01-existing-systems.md](01-existing-systems.md) | What each existing repo does, what to reuse, what stays specific, what not to repeat |
| [02-project-architecture.md](02-project-architecture.md) | Concerns A–D, topology options, recommended topology, dependency direction, versioning, generalization register |
| [03-work-execution.md](03-work-execution.md) | Roles, task contract, lifecycle, handoff, durability, implementation vs research review, escalation, multi-machine claims |
| [04-environment.md](04-environment.md) | Requirement/declaration/verification, capability tokens, preflight, bootstrap, cloud and network classes, GitHub scopes, providers, secrets, security |
| [05-artifacts.md](05-artifacts.md) | Artifact classes, identity, acquisition, stores, reproducibility |
| [06-research.md](06-research.md) | Run records, interventions, claim lifecycle, raw vs semantic, experiments, static analysis, spec, toy target, future-game tests |
| [07-delivery-plan.md](07-delivery-plan.md) | ADRs, milestones, dependency graph, initial backlog, Isle Wars first milestone, risks |
| [08-example-contracts.md](08-example-contracts.md) | Six complete task contracts, and what they showed about the schema |

## Summary in ten lines

1. **Adopt `harness_imperial`** for all task orchestration. The archaeology project contains **no**
   orchestration code. Five bounded upstream harness changes cover the demonstrated gaps: agent env
   allowlist, preflight, atomic claims, `/run-task` wiring, a harness version lock.
2. **Topology:** harness (process) · this repo as a small **meta repo** (method, formats, ADRs, toy
   target) · **one repo per game** (driver + experiments + findings + spec together; IC2's three-repo
   split with hand-relayed findings is not repeated) · **private stores per game**.
3. **Generic now = formats and vocabularies** (they already converged twice in IC2). **Generic code
   only after two real uses.** No runtime adapter interface, no DSL, no scheduler, no ontology.
4. **Task contract** = the harness format + one `Runs on` line (default `base`) + kind extensions
   for research, review, environment and architecture tasks.
5. **Environment:** a task's requirements, a machine's declarations, and capabilities *verified now
   by preflight* are three different things. Cloud suitability (C0–C4) and network needs (N0–N4)
   are properties of tasks.
6. **Claims across machines** use an atomic Git ref (`claim/T<nn>`), mirrored by IC2's
   `machine:<id>` label and a lease comment. All state needed to resume is pushed.
7. **Artifacts** are identified by manifest hash. Patched variants have recipes. Originals never
   enter a repository. Where they may go is a **per-game rights decision**. For Isle Wars there is
   no licence, so the originals stay on the user's own machines, and no cloud session or store
   ever receives them (U2).
8. **Evidence:** run records are immutable and raw-only, and stamped with interventions (I0–I3).
   Interpretations live in findings. Decoding raw values needs a cited *representation claim*.
9. **Review:** research review tries to falsify the finding. The reviewer chooses which runs to
   rerun and checks alternative explanations. The verdict has two axes: is the record sound, and
   what does it establish? Only the main session promotes reviewed claims into `spec/`.
10. **Order:** walking skeleton on a hidden-rule toy target before fan-out. The Isle Wars bring-up
    runs in parallel because it needs no generic code. It covers two artifacts, DOS *Isle Wars* and
    Win9x *Isle Wars Pro*. The first experiment, run on each, asks whether new-game setup is
    deterministic.

## Decision log

### Decided from evidence

| # | Decision | Evidence |
| --- | --- | --- |
| D1 | Reuse `harness_imperial`; no second orchestration layer | IC2 built and retired an orchestrator in a day (incident 13); the harness is its tested distillate |
| D2 | Status only in GitHub labels | L2; IC2 incident 10 |
| D3 | Briefs paste the contract, never point to it | L18; IC2 incident 14 (~85k tokens to reach ~1.45k) |
| D4 | Reviewer is another model family, proves the tree at an exact SHA, re-runs every check | L3, L8; IC2 incident 5 |
| D5 | Owns at directory/file granularity | L5; 11 "grant Owns" plan PRs |
| D6 | Implementers never weaken a contract; the main session amends it on `main` with the reason | L6, L7 |
| D7 | A pushed task branch is resumed, never recreated | `implement.mjs`; IC2 App A |
| D8 | Original binaries never in a repository; CI gets a minimal private subset via a read-only token | harness L17; `ic2-test-fixtures` design |
| D9 | Findings use Question / Answer / Method / Observations / Inferences / What this does not establish / Reproduction | converged independently in the research repo and `ic2-conquest` |
| D10 | Every run and finding names the exact binary hash, including patched variants | IC2: seed build only in prose; implicit exe identity; unexplained `.cnt`/`WAVS` |
| D11 | Walking skeleton before fan-out | L1 |
| D12 | A finding is a claim; it is promoted only after review | `retrieve-findings`; IC2's unledgered intake path |
| D13 | "Installed" is not "usable"; readiness must be verified | Go login listing nothing; `pip … \|\| true`; `wineboot`; WSL shim |
| D14 | Default to game-specific | `ic2-conquest`'s driver has one consumer; IC2 process churn |

### Recommended

R1 the topology (02 §3) · R2 one repo per game holding the driver *and* findings · R3 generic =
formats now, code after two uses · R4 `Runs on` line with `base` default · R5 JSON for records and
config, Python for archaeology tools, Node for harness tools · R6 preflight and claims in the harness ·
R7 intervention levels I0–I3 · R8 claim status / basis / scope vocabulary · R9 verification tiers
V0–V4 · R10 a separate research-review protocol with a two-axis verdict · R11 content-addressed
evidence bundles, with raw records pushed before interpretation · R12 agent env allowlist, no
self-hosted runners on research machines, Wine prefix without `Z:` · R13 Claude researchers and
OpenCode implementers by default.

### Provisional (validated by the walking skeleton or the first Isle Wars finding)

P1 toy target design and its blindness arrangement · P2 `run/1` and the other schema fields ·
P3 claim-ref name, 24 h lease, takeover rule (H4 race test) · P4 `harness.lock` propagation ·
P5 spec as Markdown claim tables per area · P6 the first Isle Wars question (setup determinism) ·
P7 the capability token list and network host lists · P8 Claude as default researcher.

### Decided by the user (2026-10-02)

| # | Decision | Consequence in this package |
| --- | --- | --- |
| U1 | **Make `imp_conquest_fixtures` private.** | Recorded; **deliberately not yet executed** (user, 2026-10-02: fix the IC2 consumers first, then flip). Flipping it breaks anonymous access in three places: `ic2-conquest/setup/setup.sh:32` (plain `https://` clone), `ic2-conquest/docs/opening-prompt.md:23` (`curl` release downloads in cloud sessions), and the research repo's `evidence-index.md` release links. It has 0 forks, so going private removes all public copies. Fixing those IC2 consumers is IC2 work, outside this project's backlog (05 §6). |
| U2 | **No licence. Isle Wars Pro is explored, never replicated.** | (a) Originals (and patched variants) never leave the user's own machines: no originals store, no GitHub upload, no cloud. Isle Wars tasks that need the artifact are **C3/C4 only**; class C2 does not exist for this game. (b) No reconstruction or reimplementation is a goal, so U9 is answered "no"; the spec stays behavioural and implementation-neutral. (c) Evidence the user generates (saves, screenshots, run records) is not the game. It goes to a private evidence store; nothing that reconstitutes the game goes anywhere (05 §1). |
| U3 | **Both** *Isle Wars* (DOS, 1994) and *Isle Wars Pro* (Win9x) are reference artifacts. | One game repo, `isle-wars-archaeology`, with two artifact families. Every claim is scoped to its artifact. Runtime spikes, drivers and the first experiment are per artifact. A claim holding for both is a cross-artifact finding (07 §4, §6). |
| U4 | **Rename the meta repo to `game-archaeologist`.** | Done as the first step of A1. It also renames the local folder, which is best done between sessions. |
| U7 | **The machine set will change.** | No machine is named anywhere in the architecture. Machines are identified only by local `machine.json` and the `machine:<id>` label. The primary role is a movable repository variable, not a fixed machine (03 §7.6, 04 §3). |
| U9 | Answered by U2: no reconstruction goal. | Spec claims stay behavioural. |
| U5 | **Isle Wars research is entirely private.** | `isle-wars-archaeology` is a private repo. Evidence bundles are release assets on that same repo, so no separate `iw-evidence` store and no second token are needed (05 §4). Cloud sessions working on its artifact-free tasks need a token that can read this private repo. Private-repo Actions minutes are metered. |
| U6 | **Harness changes go upstream** into `harness_imperial`. | H2–H6 are filed as issues there and run under its own lesson-admission rule. Archaeology repos receive them through a harness bump. |
| U8 | **A Wine-only Isle Wars Pro result needs a Windows confirmation only for timing/UI claims.** | Rule claims count from Wine (V2). Timing, rendering and UI claims reach `corroborated` only after a V3 rerun on Windows. |
| U10 | **Both new repos approved**, each created when its milestone starts: `toy-archaeology` (M2, A5) and private `isle-wars-archaeology` (W0). | A5 and W0 are no longer blocked on approval. |
| U11 | **The shareware/unregistered releases are the reference artifacts** for both games. | Every claim is scoped to the unregistered version. What registration unlocks is itself `unknown` (a W4x question). Nag screens and time limits, if any, are runtime facts for W3x. You supply the copies to your own machines; W1a/W1b hash and register them, and record where each came from. |

### Still open

None of the U-decisions. ADR acceptance (001–009) is pending: the user chose neither "accept as
written" option, and the details are to follow.

## Stop

This package ends Phase 0. Next: accept or amend ADR-001..009; then
approve backlog items one by one (07 §4). No implementation, repository creation or migration happens
before that. U1 is executed only after the IC2 consumers listed above are fixed.
