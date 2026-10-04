# Game archaeology — Phase 0 architecture package

Status: **accepted 2026-10-02** (ADR-001..009, after two independent reviews). Nothing here has been
implemented; no repository was created or migrated. Written 2026-10-02 from fresh clones of `imperial-conquest-2-research`, `ic2-conquest`,
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
| D9 | Findings use Answer / Method / Observations / Inferences / What this does not establish / Reproduction (the converged core), headed by the Question as title or first line | converged independently in the research repo and `ic2-conquest` |
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
| U2 | **No licence. Isle Wars Pro is explored, never replicated.** | (a) Originals (and patched variants) never leave the user's own machines: no originals store, no GitHub upload, no cloud. Isle Wars tasks that need the artifact are **C3/C4 only**; class C2 does not exist for this game. (b) No reconstruction or reimplementation is a goal, so U9 is answered "no"; the spec stays behavioural and implementation-neutral. (c) Evidence the user generates (saves, screenshots, run records) is not the game. It goes to a private evidence store; nothing that reconstitutes the game goes anywhere (05 §1). (b) is amended by U22. |
| U3 | **Both** *Isle Wars* (DOS, 1994) and *Isle Wars Pro* (Win9x) are reference artifacts. | One game repo, `isle-wars-archaeology`, with two artifact families. Every claim is scoped to its artifact. Runtime spikes, drivers and the first experiment are per artifact. A claim holding for both is a cross-artifact finding (07 §4, §6). |
| U4 | **Rename the meta repo to `game-archaeologist`.** | Done in A1 (T01): GitHub renamed on 2026-10-02, and links to the old name redirect. The local folder `games_revival_framework` is renamed by the user between sessions. |
| U7 | **The machine set will change.** | No machine is named anywhere in the architecture. Machines are identified only by local `machine.json` and the `machine:<id>` label. The primary role is a movable repository variable, not a fixed machine (03 §7.6, 04 §3). |
| U9 | Answered by U2: no reconstruction goal. Amended by U22: an original game inspired by the originals, never a copy. | Spec claims stay behavioural. |
| U5 | **Isle Wars research is entirely private.** | `isle-wars-archaeology` is a private repo. Evidence bundles are release assets on that same repo, so no separate `iw-evidence` store and no second token are needed (05 §4). Cloud sessions working on its artifact-free tasks need a token that can read this private repo. Private-repo Actions minutes are metered. |
| U6 | **Harness changes go upstream** into `harness_imperial`. | H2–H6 are filed as issues there and run under its own lesson-admission rule. Archaeology repos receive them through a harness bump. |
| U8 | **A Wine-only Isle Wars Pro result needs a Windows confirmation only for timing/UI claims.** | Rule claims count from Wine (V2). Timing, rendering and UI claims reach `corroborated` only after a V3 rerun on Windows. |
| U10 | **Both new repos approved**, each created when its milestone starts: `toy-archaeology` (M2, A5) and private `isle-wars-archaeology` (W0). | A5 and W0 are no longer blocked on approval. |
| U12 | **Private `toy-target` repo approved**, created when M2 starts (by A4). It holds the toy game's source and sealed rules, out of the researcher's reach (review finding R1). | A4 creates it at M2; A5 copies the built `.pyz` by hash into `toy-archaeology`'s release. |
| ADRs | **ADR-001..009 accepted** (2026-10-02), after both independent reviews and their applied fixes. | The provisional parts named in 07 §1 stay provisional until their validating task: ADR-002 until H1, ADR-005 until H4's race test, the ADR-004 token list and the ADR-007 fields until A6. |
| U11 | **The shareware/unregistered releases are the reference artifacts** for both games. | Every claim is scoped to the unregistered version. What registration unlocks is itself `unknown` (a W4x question). Nag screens and time limits, if any, are runtime facts for W3x. You supply the copies to your own machines; W1a/W1b hash and register them, and record where each came from. |

### Decided by the user (2026-10-03)

| # | Decision | Consequence |
| --- | --- | --- |
| U13 | **The model pair follows the task's difficulty**, as in isle-wars-archaeology. Easy: GLM-5.3 Flash implements, GPT-6 Luna reviews. Hard: DeepSeek V4.1 Flash implements, GPT-6.1 Sol reviews. Game rules, formulas or constants implemented from evidence count as hard. | CLAUDE.md rule 20, `docs/models.md`, `harness.json` in every repository of this session. Jev's `task-hard` decision makes the clear hard calls; easy stays the main session's. |
| U14 | **A third target: GOAL2**, "goal (version 2)" by New Era Software (1993), a DOS text-mode international football team-management game. The user owns the full version. The end product is a behavioural spec, then a **faithful rebuild**, then a **bot**. | Unlike Isle Wars (U2, U9), reconstruction is a goal here. The spec feeds a rebuild, as IC2's did. |
| U15 | **The bot maximises the World Cup win rate**, for every country, ranked. | The rebuild must simulate the match engine and the competitions fast enough for search or learning. Each strategy is confirmed on the original. |
| U16 | **Behavioural and static methods**: running it in DOSBox-X, and unpacking (LZEXE) and decompiling `GOAL.EXE`. | `corroborated` is reachable by behavioural plus static. |
| U17 | **GOAL2 is treated as abandonware.** Its files may be attached to a release of the private `goal2-archaeology`, and derived extracts (data tables, decompiled listings) may be committed there. | An exception to rule 19 and ADR-006 for GOAL2 only, and only in private repositories. Isle Wars stays under U2. |
| U18 | **Python** for the rebuild and the bot; **DOSBox-X in WSL** for the original. | GOAL2 runs the DOSBox-X spike first; Isle Wars' DOS lane (W3b) can reuse it (ADR-009: two uses → extraction). |
| U19 | **Two private repositories**: `goal2-archaeology` now, and `goal2` (rebuild and bot) when the spec covers the match engine. | G0 creates the first, with the harness and `formats-v1`. |
| U20 | **Modern GOAL2 databases**: current national teams and players, written into GOAL2's own data format. Facts come from open data only (Wikidata, CC0; openfootball, public domain). Skill ratings are computed by our own documented formula, never copied from a commercial game or database (EA, Football Manager, Transfermarkt). | Private repositories only, never published. It needs the `GOAL.DAT` format specified first (a representation claim set), and lives in `goal2` beside the rebuild. |

### Decided by the user (2026-10-04)

| # | Decision | Consequence |
| --- | --- | --- |
| U21 | **Runtime writes observed after registration make a successor set** (#19, option 2). `runtime_writes` stays in the canonical hash, and `formats-v1` is unchanged. | `formats/README.md` describes the procedure, which isle-wars-archaeology already followed (`iwp-2.0-3694a782`). GOAL2 registers a successor of `goal2-a949da2f` declaring the writes F001 observed. Options 1 (a formats-v2 hash without the writes) and 3 (a spike before registering) were rejected. Option 1 would not cover a shipped file the game writes, which must leave `files` anyway. Option 3 conflicts with the runs citing a set id. |

| U22 | **Isle Wars is explored, never copied** (the owner's decision of 2026-10-02, in isle-wars-archaeology 9566434; #13). The research feeds **malpaco**, an original game inspired by *Isle Wars Pro*. The originals' code, assets, text and name are never reused. Only behaviour and design learned pass to the game; no evidence ever does. | Amends U2(b) and U9. U2(a) and (c) are unchanged: originals stay on the owner's machines, and evidence stays private. The spec stays behavioural; malpaco's design is its own, informed by it. ADR-006, 05 §1 and 07 §6 now say "never copied". The rebuild part of the harness process applies to malpaco, not to the research repository. |

| U23 | **A record file with a duplicate JSON key is invalid**, at any depth and even when the values agree (T07, Sol's round-3 R1 on #20). | JSON readers disagree on which duplicate wins, so one file could mean different records in different repositories. `tools/validate_records.py` rejects it, and so do NaN/Infinity literals and lone surrogates (Sol judged those invalid input already). No example or registered manifest is affected. |

| U24 | **A game copy holding a special file or an unsafe symlink fails registration and checking**: a socket, a device, a broken link, or a link out of the folder. This holds even when the entry is unlisted, matches `runtime_writes` or `--exclude`, and `--strict` is off (T09, Sol's round-3 R1 on #24). | DOS-era games never create such entries, so one means the copy is not what it seems. `tools/register_artifact.py` names it and never follows or reads it. This is the same fail-closed choice as U23. |

| U25 | **A finding's `## Answer` and `## Inferences` sections hold only list items, `###` sub-headings and tables.** List items use `-`, `*`, `+` or numbered markers, with indented continuation lines. In a table, every data row must cite a run id, as a bullet must; the header and `---` separator rows are exempt. Blank lines are allowed. Anything else there is an error, "unsupported in a protected section": HTML, a blockquote, a code fence, any other heading level, or a repeated Answer or Inferences heading (T10, Sol's round-2 R1 and R2 on #27; tables and `###` added on 2026-10-04 so that the existing findings that use them still pass). | `check_citations.py` fails closed instead of parsing ever more Markdown. Each review round found a new construct that hid an uncited claim, as T05's code spans did. `formats/templates/finding.md` says so. On 2026-10-04 the existing findings in toy-archaeology, goal2-archaeology and isle-wars-archaeology use only these forms, except one lead-in sentence each in goal2's F002 and F004. Those two get a one-line fix when goal2 migrates. |

| U26 | **A static claim cites its evidence with `static:<tracked path>[:line]`**, which counts as a citation wherever a run id does: in a bullet or a table row of a finding's Answer or Inferences (U16: static findings are first-class). `check_citations.py` checks that the path exists in the repository, as it checks run records. Isle Wars' short-form run ids (`r0004`) are rewritten as full ids (`E001-r0004`) when it migrates; the tool gains no short form. U25's strict reading stands: a list item's second paragraph, and `<...>` inside a code span, are unsupported (the owner confirmed). | A follow-up to T10, filed as a task when T10 merges. goal2's F002 and F004 then cite static rows this way; Isle Wars' F002 and F005 join or drop their second paragraphs; goal2's F001 drops the angle brackets from `<NAME>.GL`. |

| U27 | **A heading that reduces to "answer" or "inferences" must be exactly `## Answer` or `## Inferences`.** A heading is any line starting with `#`, a setext heading, or an HTML `<h1>`–`<h6>`. Its text is NFKC-normalised, casefolded and reduced to its letters. If the result is exactly `answer` or `inferences` and the line is not exactly `## Answer` / `## Inferences`, the line is an error (T10, Sol's round-3 R1 on #27: a code span, a link or a non-breaking space in the heading switched checking off). | Finite: it replaces the deny-list of spellings. Other headings stay free. Known limit: a look-alike letter from another script (a Cyrillic А) does not reduce to `answer`. It is out of T10's scope and filed as a follow-up; only a fixed heading list would close it. |

| U28 | **U27 is matched on raw text, by containment, and a heading may not mix scripts.** This replaces U27's rendered-text reading (T10, Sol's round-4 R1 and R2 on #27). A heading line's raw text is entity-decoded, NFKC-normalised and casefolded, then reduced to its letters; nothing is deleted to model rendering. If those letters contain `answer` or `inferences`, the line must be exactly `## Answer` or `## Inferences`, or it is an error. A heading whose letters come from more than one Unicode script is also an error (#28: look-alike letters). | Finite: no rendering model to get wrong. Headings that merely mention the words become errors, by design. Of the 36 existing headings in toy, goal2 and isle-wars findings, only goal2 F002's `### Inferences about the executable` needs renaming, and none mixes scripts. |

| U29 | **An HTML heading is matched as a block, not parsed.** Any line containing `<h1`–`<h6` (case-insensitive) starts a heading block that runs to the next blank line, or to the end of the file. The whole block's raw text goes through U28: entity-decoded, NFKC, casefolded, letters only. If it contains `answer` or `inferences`, or mixes scripts, the block is an error (T10, Sol's round-5 R1 on #27: a quoted `</h2>` in an attribute, and a second `<h2>` on the same line). | No HTML parsing remains to get wrong. A paragraph of HTML that merely mentions the words next to a heading tag is refused, by design. No existing finding uses HTML headings. |

### Still open

None. U1–U29 are made, and ADR-001..009 were accepted on 2026-10-02.

## Independent review

| Reviewer | Result | Record |
| --- | --- | --- |
| DeepSeek V4 Pro (OpenCode Go), read-only, text-only evidence | `approve after named fixes`. 1 blocking and 13 non-blocking findings. ADR-005, 006 and 008 accepted as written; the other six accepted with named changes. | [reviews/2026-10-02-deepseek-v4-pro.md](reviews/2026-10-02-deepseek-v4-pro.md) |
| GLM-5.3 (OpenCode Go) | 1st run failed: OpenCode resolved `cd a && …; cd ../b` against the workspace root and auto-rejected it (a false positive, filed as harness_imperial#14). 2nd run, after the DeepSeek fixes: `approve after named fixes`, 9 non-blocking findings. ADR-002, 005 and 009 accepted as written; the other six accepted with named changes. | [reviews/2026-10-02-glm-5.3.md](reviews/2026-10-02-glm-5.3.md) |
| DeepSeek V4 Pro, fix confirmation | `approve`. R1–R14 all confirmed, including the R3 dispute. 5 new non-blocking findings N1–N5. | [reviews/2026-10-02-deepseek-v4-pro-confirmation.md](reviews/2026-10-02-deepseek-v4-pro-confirmation.md) |

Disposition of the DeepSeek findings (each was checked against the evidence before it was applied):

| # | Finding | Disposition |
| --- | --- | --- |
| R1 (blocking) | Sealed rules in the public meta repo are readable by the researcher | **Fixed, and made stronger**: the source leaks the rules too, and a Claude agent uses the owner's `gh` login. The toy source and SEALED.md move to a private `toy-target` repo (U12). The researcher runs with GitHub access limited to `toy-archaeology`, and static analysis of the `.pyz` is out of scope for Y2 (06 §10, 07 A4/A5/Y2, 08 §5). |
| R2 | Three numbers wrong | Fixed: 65 `test()` cases (56 at handover), 42-line helper, three model-routing changes plus one open. |
| R3 | Tag counts and the `[O]` scheme | **Partly wrong**: `rules-digest.md:6-9` does use `[C]/[D]/[O]/[P]`; `sav-layout-notes.md` uses `[C]/[D]/[?]`. Both are now cited, and the counting method is stated. |
| R4 | GitHub-derived counts not in the evidence dump | Fixed: 01 now states that these come from live `gh` queries on 2026-10-02. |
| R5 | Four vs five upstream changes; when research kinds go upstream | Fixed: five (H2–H6) everywhere; research kinds go upstream only after toy and Isle Wars have used them. |
| R6 | Stale repo-creation wording | Fixed (W0; approved under U10). |
| R7 | W-track said to need no generic code, yet uses `run/1` and preflight | Fixed: edges A2 → W3x and H3 → W5x, and the text names both. |
| R8 | Task IDs vs per-repo T-numbers; H3's CI ownership; "truncated hashes" | Fixed: ID convention stated (07 §4); example headings name their repo; H3 owns its CI step; the truncated hash is cited in 01. |
| R9 | `primary` in `machine.json` vs the repository variable | Fixed: removed from `machine.json`; the variable is the only mechanism. |
| R10 | W8x reviewers inherited release-write | Fixed: release-read only. |
| R11 | No confidence field; `inconclusive` not evaluated | Fixed: a required `Confidence:` line in each finding (no numeric probability); `inconclusive` is a finding outcome, not a claim status (06 §4). |
| R12 | `gh:pr` unverified; declaration-only tokens unlisted | Fixed: closed list (`facility:desktop`, `facility:audio`); `gh:pr` proved early by a draft PR at claim time (H5). |
| R13 | Generalization trigger stated three ways | Fixed: "moved when a second consumer copies it", everywhere. |
| R14 | ADR-002 "Decided" while the harness is unproven | Fixed: decided for "no second orchestration layer"; operational readiness provisional until H1. |

Disposition of the second round (GLM R1–R9, DeepSeek N1–N5), each checked against the evidence:

| # | Finding | Disposition |
| --- | --- | --- |
| GLM R1 = DS N1 | The topology diagram and the toy profile still distribute the toy through the public meta repo | Fixed: the only path is a release asset on `toy-archaeology`, copied by hash from `toy-target` (02 §3, 04 §5). |
| GLM R2 | The example confound "UI paint routines write RandSeed" is a refuted draft claim | **Confirmed and fixed.** The research repo's report says these are the peace treaty and the battle-poll form, which reset `RandSeed = winner + loser` (03 §6.2). |
| GLM R3 | A4's reviewer must read SEALED.md, and could later be dispatched as a toy researcher | Fixed: A4's implementer and reviewer sessions are recorded and barred from toy research and review (06 §10, 07 A4). |
| GLM R4 | W4x listed as owning `spec/` rows | Fixed: W4x proposes rows in its finding; promotion writes `spec/`. |
| GLM R5 | No grammar for multi-class `network:` and the `GitHub:` field | Fixed: line grammar in 03 §2.1; H3 parses it (08 §3). |
| GLM R6 | Claim needs labels and issues tokens; a ref without a claim comment can never go stale | Fixed: `base` includes `gh:issues gh:labels`; a ref with no claim comment after 10 minutes is stale at once (03 §7.4). |
| GLM R7 | Some claims rest on sources not in the reviewers' dump | Fixed: 01 names them (GitHub API for the private stores, the IC2 wiki, local working copies, checks on the author's machine). |
| GLM R8 | D9's section list; the release checklist count | **Confirmed and fixed**: Question is a title or first line (only 1 of 3 `ic2-conquest` findings has a Question section); the checklist has 20 items. |
| GLM R9 | No home for "bonuses" | Fixed: a `bonuses` area (island/continent groups, cards) in the knowledge map. |
| DS N2 | H2 (env allowlist) matched no numbered deficiency | Fixed: deficiency 7 added to 01 §1. |
| DS N3 | Stale "(user OK)" on W0 | Fixed. |
| DS N4 | Y2's network stated as N1 only | Fixed: N1, or N2 through OpenCode, never N4. |
| DS N5 | `rules-digest.md:6-9` should be 7-10 | **Rejected**: the four tag definitions are on lines 6–9 (line 4 is the heading). GLM confirmed 6–9 independently. |

**ADR outcome across both reviews:** no ADR rejected and none escalated to a user decision.
- Accepted as written by both reviewers: ADR-005.
- Accepted as written by one reviewer, and accepted after the now-applied named changes by the other: ADR-002, 006, 008 and 009.
- Accepted by both only with named changes, all now applied: ADR-001, 003, 004 and 007.

## Stop

This package ends Phase 0: the architecture is accepted. **H1 is done** (2026-10-02: a full real
`/run-task` loop, harness#1). Next: approve backlog items one by one (07 §4), starting with A1: adopt
the harness here (at `f4c49d9` or later) and write the ADRs as `docs/adr/` files, including the
rename to `game-archaeologist`. No implementation,
repository creation or migration happens before an item is approved; approved repositories are
created when their milestone starts. U1 is executed only after the IC2 consumers listed above are fixed.
