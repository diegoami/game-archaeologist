# 01 · Existing-system analysis

Primary evidence: fresh clones of the five repositories (2026-10-02), their process files, git
history, GitHub labels/issues/releases, and the sibling repos they reference
(`imp_conquest_original`, `ic2-test-fixtures`). File references are to those clones.
**[V]** = verified in a file, on GitHub, or by re-running something. **[I]** = inference.

---

## 1. `harness_imperial` — the process, already generalized

**What it is [V].** A copy-in template (`cp -r template/. .`) distilled from IC2: 40-line
`CLAUDE.md`, 150-line `docs/process.md`, `docs/lessons.md` (L1–L26, every rule tied to a real
failure), `/run-task`, `/delegate`, `/jev` skills, and ~1,100 lines of Node tooling with 56 tests
against fake `opencode`/`gh`. Six commits; the README says *"A full run through `implement.mjs` has
not happened yet"*, and open issue #1 is "Verify the harness on the Windows desktop, with real keys".

**What it already generalizes [V]:**

| Concern | Where | Status |
| --- | --- | --- |
| Task format (Kind, Evidence, Owns, Scope, Done when, Hazards, Implementer, Reviewer, Merge after) | `docs/tasks/TEMPLATE.md` | done |
| `/run-task` loop: ready → implement → review → approve + green CI → squash → follow-up → unblock | `.claude/skills/run-task/SKILL.md` | done |
| Implementer runner: worktree creation, **resume a pushed branch**, watched OpenCode run, handover check (PR exists, clean, pushed, detached) | `tools/harness/implement.mjs` | done, tested with fakes |
| Reviewer runner: detached worktree at PR head, never the implementer's family, review completeness check, script (not model) posts | `tools/harness/review.mjs`, `lib/chain.mjs` | done |
| Model-family independence | `excludeImplementers()`; `family` field in `harness.json` | done |
| Provider fallback: next model only on infra failure that left no commit/push/PR; same failure twice stops | `lib/chain.mjs runChain()` | done |
| Watchdog: stdin closed, startup/idle/total timeouts, process-tree kill, agent check from session record, rejected tool call = failure, export via file, WSL shim skip | `lib/opencode.mjs` | done |
| Agent sandbox: deny force-push, stash, worktree, merge, label edits; reviewer read-only | `.opencode/agents/*.md` | done |
| GitHub labels as state | `process.md §8` | done (single-machine) |
| Environment: keys, hosts for cloud network policy, cloud session-start hook (installs OpenCode 1.18 + gh, reports which keys are set, never prints values) | `docs/environment.md`, `.claude/hooks/session-start.sh` | done for *delegates*, not for task needs |
| Lessons/incident admission rule | `docs/lessons.md`, L14 | done |
| RE-project rules: one fixtures corpus, two-stage evidence, originals never in repo, CI fetches private fixtures | `process.md §11`, rules 17–20 | done (rules only) |

**What it does *not* provide [V] — the demonstrated deficiencies:**

1. **No multi-machine operation.** No machine identity, no claim, no `local-only`/`single-instance`,
   no abandoned-claim recovery. IC2 needed and used all of these (§4 below).
2. **No statement of what a task needs from its machine**, and no preflight. The session-start hook
   runs only in cloud sessions (`CLAUDE_CODE_REMOTE`) and only reports delegate keys.
3. **No research task kinds.** The brief and review blocks assume a code PR with a test suite. IC2's
   research promotion lived in a separate repo's skill (`retrieve-findings`), outside the harness.
4. **Update propagation is copy-and-forget.** No record of which harness commit a project copied;
   IC2 itself diverged (PowerShell scripts, skills hand-reinstalled from fenced blocks in docs).
5. `implement.mjs` hard-codes `--task` to `^T\d{2,3}$` and branch `task/T<nn>-<slug>` — fine, but
   it means "task" is the only unit; research runs ride the same path.
6. Not yet proven in a real run (its own README and issue #1).

**Reuse:** all of it, unchanged, as concern A. **Remain specific:** nothing game-specific belongs
here. **Do not repeat:** do not build a second runner, label protocol, or brief/review system in
the archaeology project. Extend the harness upstream for deficiencies 1–4, each with its lesson.

---

## 2. `imperial_conquest_2` — where the process was learned

409 commits in 20 days, 113 task files, 98 merged tasks, 133 bugs. The harness is its distillate.

**Reuse (already captured by the harness) [V]:** main session plans/triages/merges and never lets
agents into the main checkout; task file per task; pasted contract in briefs (incident 14: a
pointer cost ~85k tokens to reach ~1.45k of contract); reviewer of another family re-runs every
Done-when (gate 1) after proving the tree (gate 0, incident 5); Done-when immutable to agents;
two rework rounds then escalate; fix lane; status only in labels (incident 10).

**Reuse (not yet captured by the harness) [V]:**

- **Two-machine protocol** (`docs/build-process.md §8`, adopted 2026-09-27): own main session and
  clone per machine, GitHub as the only shared state; identity = `IC2_MACHINE` env + `machine:<name>`
  label because both machines are the same GitHub account; claim = check no `machine:*` label → add
  yours → re-read → second claimer backs off; only the claimer resumes or merges; a cloud session is a
  third main session that claims nothing. Used: `machine:desktop` ×15, `machine:rogx` ×2.
- **Capability labels** `local-only` (needs originals via ignored `assets.local.ini`) and
  `single-instance` (Godot; never two processes per machine). "A machine claims only tasks whose
  labels it can satisfy."
- **Concurrency rule:** two machines may run tasks together only with disjoint Owns (implicit
  ownership included), no "never in flight with" line, and no seam redefinition.
- **Start-after (soft) vs Merge-after (hard)** dependencies; "never in flight with".
- **Recovery table** (`§5`): pushed branch, no PR → resume implementer; PR, no verdict → reviewer;
  `status:rework` → re-dispatch; no branch → back to `ready`.
- **Verification by location:** "CI is the authority on test results. A reviewer's local run adds
  the `local-only` subset CI cannot run." "A result seen only under Wine gets one confirmation on the
  desktop."
- **Research → implementation routes** (`docs/evidence-pipeline.md`): each new finding becomes a doc
  fix, a bug, a not-yet-dispatched task edit, or a user question; research never decides design.
- **Contract findings**: a reviewer may find a defect in the task entry itself (T66 C1), settled by
  the main session, not the implementer.

**Remain specific:** .NET/Godot/ruleset machinery, `[designed]` tag (it belongs to a *rebuild*, not
to archaeology), the playability gate, release plan.

**Do not repeat [V]:**
- **Process churn.** ~125 Plan/Process PRs vs ~139 task PRs; implementer model routing changed four
  times on 2026-10-01 alone; an orchestrator built and retired within a day (incident 13); worktrees
  dropped and reinstated within a day. Lesson: start from the distilled harness; add process only
  per incident.
- **Owns too tight**: 11 "grant T<nn> …" plan PRs mid-implementation (L5).
- **Machine-bound paths** (`C:\Users\diego\…` in CLAUDE.md and appendices) and `.claude/` ignored
  with skills reinstalled by hand from docs.
- **Unused ceremony**: `Plan (routine):` prefix used 0 times; 19-item release checklist run partially;
  frozen waves table; stale "(orchestrator-managed)" label descriptions.
- **Label race**: the IC2 claim is two non-atomic writes plus a re-read; "second" is undefined when
  both re-read after both writes. Never observed with 17 claims [I], but it is a race.

---

## 3. `ic2-conquest` — operating the original automatically

**How it works [V]:** Ubuntu 24.04 on WSL2; Wine 9.0 (32-bit prefix), Xvfb `:99`, no window manager,
`xdotool` input, ImageMagick screenshots, Tesseract OCR for message boxes; a 30-line mingw Win32
helper (`harness/win_controls.c`) run *inside* Wine to enumerate dialog controls; toolbar positions
read at runtime from Wine tooltip windows and cached. State: read-only `/proc/<pid>/mem` at known
Delphi globals; SAV parsed by `state/sav.py` (hand-written offsets from the research repo).
Determinism by **intervention**: `patches/seed_patch.py` reroutes `Randomize` to read `SEED.TXT` and
log every firing to `SEED.LOG`; the fixtures' `patch_exe.py` adds async sound, instant battles and an
autosave hook at StartTurn. Finding: *loading a save does not reseed* → each turn is
f(save, seed, orders), executed in a fresh process. Byte-identical repeat shown for a scripted turn
and new game; branching is serial (restart + load).

**Findings format [V]** (`findings/YYYY-MM-DD-<claim>.md`): title is the claim; `Status: draft
finding … awaiting promotion`; Answer; Method (build + SHA-256, environment, code addresses);
Observations; Inferences; *What this does not establish*; Reproduction. Handed to the research repo
by a **pasted prompt relayed by the user** ("never write to another repository").

**Reuse (as patterns, not code):**
- the Wine/Xvfb/xdotool stack and runtime UI discovery (generic to Win32 games under Wine — but only
  one game has used it; stays game-specific until a second Win32 target needs it);
- **seed-from-file + firing log** and **autosave hook**: turn an original into a controllable,
  observable simulator — the archetype of a *declared intervention*;
- verify every action against memory/save state, not screenshots;
- the findings template (converged independently with the research repo's dated template);
- pinned inputs (`setup/pins.txt`: repo commits + original exe SHA-256, checked by `setup.sh`).

**Remain specific:** every address, the SAV layout, window titles, the turn formula, the planner.

**Do not repeat [V]:**
- **Interventions not stamped on results.** `results.json` carries no build hash; the seed build
  (`354d8265…`) is identified only in prose and not asserted by `setup.sh`; `no_delay` (instant
  battles) is assumed behaviour-neutral and never tested.
- **Raw data overwritten / mis-recorded:** `results.json` holds 1 of the 4 seeds the README reports;
  a dict comprehension kept only the last unit per type; the battle-repeatability hash was never
  recorded.
- **Evidence only on one disk:** experiment artifacts live in a gitignored local folder; no release.
- **Global singletons** (`:99`, one prefix, one `SEED.TXT`, `wineserver -k`, first-pid `pgrep`)
  prevent parallel runs; the README's "4–8 displays in parallel" is not supported by the code.
- **Silent setup failure:** `pip install … 2>/dev/null || true` left capstone missing on 24.04
  (PEP 668), so cited disassembly cannot be re-run; `wineboot -u` as user is a manual step without
  which every load times out; `IC2_SRC` default is wrong on WSL.
- **Doc drift on load-bearing facts:** README, rules digest and opening prompt still say load
  reseeds, which the promoted finding refutes; HANDOVER says nothing is merged after 4 merges.
- **Hand relay** of findings between repos via pasted prompts.

---

## 4. `imperial-conquest-2-research` — recording RE evidence and uncertainty

**How it works [V]:** 75 reports in `docs/reports/`, no template file. Converged dated template:
Question / Answer / Method (build + SHA-256, environment, runs, code) / Observations / Inferences /
*What this does not establish* / Where the evidence is / Reproduction / Next checks. Inline claim
tags: `[confirmed]` (184), `[derived]` (72), `[confirmed: decompile]` (40), `[confirmed: code]`
(15), `[open]` (7), `[hypothesis]` (4), plus ad-hoc variants. `evidence-index.md` maps bare
filenames → release/path with "three things that will mislead you". `recording-ledger.md` tracks
how deeply each recording was mined (scanned/surveyed/read/exhausted). Intake: skill
`retrieve-findings` treats each draft as "a claim, not evidence", re-checks it, and records an outcome
(`promoted / promoted, corrected / merged into / rejected / deferred`) in `findings-intake.md`; a
daily workflow lists unledgered drafts. Static RE: Ghidra 12.1.3 + JDK 21 off-repo under
`%LOCALAPPDATA%\ReTools`; Delphi RTTI recovery was the key enabler.

**Reuse (generic method, formalize once):**
- the dated report template and the **"What this does not establish"** section;
- **claim tags with a basis suffix** (`confirmed: decompile|listing|saves|bytes|live`) — but with a
  legend in the same repo, and split into *status* vs *basis* (see 06-research);
- **quantified agreement** ("494 of 494", "10,693 of 10,980 city-turns exact") as the standard for
  a behavioural confirmation;
- **intake as review**: a draft is a claim; outcome vocabulary; a ledger;
- the evidence index, with digests added.

**Remain specific:** RTTI scanner, offsets/strides, VAs, recording naming conventions.

**Do not repeat [V]:**
- **No legend in the repo**; the definitions live in the build repo's `design-audit.md`; a sibling
  repo uses a different scheme (`[C]/[D]/[O]/[P]`).
- **Five different correction/supersession styles** across 39 files.
- **Implicit binary identity:** only ~4 reports state the analysed exe hash; the decompilation plan
  points at the *demo* hash file.
- **Unstable reproduction references:** line numbers into a regenerated local dump, uncommitted
  Ghidra scripts, "ad-hoc parser (not committed)".
- **Stale top-level docs:** "the executable is not run" while live Wine runs exist; the evidence
  store described as private in one file and public in another.
- **A second, unledgered intake path** (build-repo issues / evidence-pipeline agent pushing straight
  to `main`): research findings reached canonical reports without independent review.

---

## 5. `imp_conquest_fixtures` (+ `imp_conquest_original`, `ic2-test-fixtures`) — artifacts

**What is stored [V]:** `imp_conquest_fixtures` is **public, unlicensed**, and contains the original
v1.01 `Imperial Conquest 2.exe` (`9d753d5d…ba31`), `.dat`, `.hlp`, a `.cnt` matching neither hashed
original, resampled `WAVS/` (no provenance) beside the original `WAVS - Copy/`, four patched EXEs,
`patch_exe.py`, 64 saves (54 duplicated byte-for-byte in releases), screenshots, notes, and a Win98
VHD transfer tool. Releases: `run-1-ptolemy` (~805 MB incl. 22 mp4), `legacy-probes` (~181 MB),
`run-1-rome/cartago/thracia`. `scripts/fetch-release.sh` targets the *private*
`imp_conquest_original`, which has no releases, and verifies no checksum.

**The design that already exists, and was then bypassed [V]:**

| Repo | Visibility | Holds | Read by |
| --- | --- | --- | --- |
| `imp_conquest_original` | private | the whole corpus incl. exe, recordings | "no automated job touches" it |
| `ic2-test-fixtures` | private | exactly what CI tests read: DAT + 99 saves + `manifest.json` (path, bytes, sha256) | CI, via a read-only token scoped to this repo |
| `imperial_conquest_2` | public | code; tests resolve fixtures **by name** | everyone |
| `imp_conquest_fixtures` | **public** | a copy of the original corpus, patched builds, recordings | `ic2-conquest` (pinned), research docs, build-repo docs |

`ic2-test-fixtures/README.md` is the best artifact-policy document in the IC2 family: the *whole*
subset a test project needs (a named subset silently lost 42 CI cases), sha256 manifest, filenames
load-bearing, "synthetic for shape, real for reality", private + least-privilege token.

**Reuse:** the three-tier split (private originals / private minimal CI subset with manifest /
public code); `patch_exe.py`'s discipline — assert input bytes at every site, deterministic output
(re-running it on the committed original reproduced all four committed EXE hashes [V]); pinning
consumers by commit + original hash; GitHub release digests as free sha256.

**Remain specific:** VAs, the Win98 VHD tool (the *idea* of a VM transfer disk generalizes).

**Do not repeat [V]:**
- originals, patched binaries and ~1 GB of gameplay video in a **public** repository, contrary to the
  project's own stated policy (research README:7, roadmap:3, harness rule 17/L17);
- modified originals without provenance (`WAVS/`, `.cnt`);
- the same saves in git *and* releases; docs disagreeing on where evidence lives; a fetch script
  aimed at an empty store; no post-download checksum;
- no manifest mapping each patched EXE to its base hash, options and patcher commit.

> This package does **not** migrate or change any IC2 repository. The public fixtures repo is
> raised as open decision **U1** (README).

---

## 6. `malpaco` — the earlier, abandoned Isle Wars attempt

`C:\Users\diego\projects\malpaco` (`diegoami/malpaco`, 2026-09-15 → 09-24, ~30 commits). Started as
"Islesrisk POC": a Godot 4.7 re-take of the Isle Wars ruleset, **explicitly not** a port or
reconstruction. Iterations 0–3 shipped a hot-seat game; it adopted "harness release r4" (a third
process lineage: `PRINCIPLES.md`, AGREE/BLOCK markers, review records as files under `reviews/`,
a design stage before implementation).

**What it contributes [V, as claims it makes — none verified here]:**
- *Isle Wars* is by **Soleau Software (1994)**, a DOS game that "already runs in a browser tab …
  via DOSBox builds on playdosgames.com and the Internet Archive"; ***Isle Wars Pro*** is its
  **Win9x sequel** (`RULES.md:13`, `DECISIONS.md:26-29`).
- "*Isle Wars Pro* is **not abandonware** — Soleau has continued selling the registered version
  (about $12 by download, per the classic-games catalogues)"; "They have historically been relaxed
  about their catalogue being redistributed" (`DECISIONS.md:430-433, 461-464`).
- Features attributed to the original: the match rule, the failed-attack penalty, hazards, roaming
  production centres, the AI's collective surrender offer, a three-card idea, "46 countries divided
  between 9 continents" (`RULES.md:13-15`, `DECISIONS.md:208, 318`).
- Its own warning: "**The constants here are ours.** … nothing in this document was reverse-engineered
  … do not 'restore' them to something a wiki claims" (`RULES.md:19-25`).

**Reuse:** the provenance discipline of that warning; the feature list above as *unverified
secondary-source assertions* that seed Isle Wars research questions (never as specification).

**Remain specific / out of scope:** the engine, presets, art, the product case. Malpaco is a
possible *later consumer* of a reviewed Isle Wars specification, not an input to it.

**Do not repeat:**
- Designing from recalled/secondary descriptions of the original. Malpaco had to correct its board
  shape after shipping because "46 countries … 9 continents" was misread
  (`DECISIONS.md` 2026-09-18) — exactly the failure an evidence-backed specification prevents.
- A *third* process lineage. Malpaco, IC2 and harness_imperial each carry a different review
  protocol; this project adopts one.

**Consequences for this architecture:**
1. Isle Wars Pro is a **currently sold commercial product**, unlike IC2. The user's decision
   (**U2**, 2026-10-02): no licence, so it is explored but never replicated. Originals stay on the
   user's own machines, never in a repository, a store or the cloud. This makes artifact policy a
   per-game decision, not a global default.
2. There are **two reference artifacts**, both in scope (**U3**): DOS *Isle Wars* (DOSBox; DOSBox-X
   offers a debugger and save states) and Win9x *Isle Wars Pro* (Wine or Windows). The knowledge map
   scopes every claim to an artifact.

---

## 7. Cross-cutting conclusions

1. **Concern A is solved** well enough to adopt, and it is young. The archaeology project should
   contain *zero* generic orchestration code; it should file four bounded upstream changes against
   `harness_imperial`.
2. **The research method converged independently in two repos** (findings template, claim tags,
   "what this does not establish", promotion-as-review). That is a demonstrated repetition — it can
   be formalized as a *format* now.
3. **Every IC2 artifact failure is an identity/provenance failure**, not a storage failure: implicit
   binary identity, unstamped interventions, overwritten raw results, unexplained modified originals.
   The artifact architecture is mostly manifests and hashes, not infrastructure.
4. **Every IC2 environment failure was "installed ≠ usable"**: Go login listing nothing while
   `console orgs` exits 0; pip failing silently; Wine prefix without a user profile; the WSL
   OpenCode shim. Hence declared vs verified capability.
5. **Runtime code has had exactly one consumer.** Nothing in `ic2-conquest`'s driver is generic yet.
6. **Three review protocols already exist** (IC2, harness_imperial, malpaco's harness r4). Adopting one
   — harness_imperial, the most recent distillate with tested tooling — is itself a decision (ADR-002).
