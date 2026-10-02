# 08 · Example task contracts

Six complete contracts in the proposed format (03 §2), each written as it would be pasted into a
brief. They exist to test the schema; §7 records what writing them showed.

Each contract carries its **own repository's** T-number (07 §4, "IDs"), so numbers repeat across
repositories. The plan label and the repository are in each section heading.

---

## 1. Architecture task — A2 Formats and vocabularies v1 (meta repo)

```markdown
# T02 Formats and vocabularies v1
- **Kind**: architecture
- **Issue**: #2 · **Branch**: `task/T02-formats-v1` · **Merge after**: T01
- **Implementer**: claude (opus) · **Reviewer**: opencode (glm), then claude (sonnet) `/code-review`
- **Why**: the toy research repo (T05) and every game repo record runs, artifacts and findings in
  these shapes; the walking skeleton tests them.
- **Evidence** (pasted):
  - docs/phase0/06-research.md §2 (run record fields), §3 (I0–I3 table), §4 (status/basis/scope
    tables), §5 (representation claims), §9 (spec claim table) — pasted in full below this contract.
  - docs/phase0/05-artifacts.md §2 (artifact-set and variant JSON) — pasted.
  - IC2 failures these formats must prevent (01 §3, §4): results.json kept 1 of 4 seeds; no build hash
    in results; the seed build identified only by a truncated hash in prose; interventions unstamped.
- **Owns**: `formats/**`, `vocabulary/**`, `tests/formats/**`
- **Scope**: JSON Schemas `run/1`, `artifact-set/1`, `variant/1`, `evidence-manifest/1`; Markdown
  templates `finding.md`, `spec-area.md`, `experiment-README.md`; legends `status.md`, `basis.md`,
  `interventions.md`, `tiers.md`; one valid and one invalid example per schema.
  **Not in scope**: a validator CLI (deferred, 02 §5); game-specific fields; a spec ontology.
- **Decisions**: field names and required/optional split for each schema; how a decoded value cites a
  representation claim (`via`).
- **Escalate**: any field whose need is not traceable to 06 §2–5 or an IC2 failure — propose, do not add.
- **Done when**:
  1. `python3 -m json.tool` succeeds on every file under `formats/` (all parse).
  2. `python3 tests/formats/check_examples.py` (stdlib-only, written in this task) reports every
     `valid/*.json` valid and every `invalid/*.json` invalid with the expected error, for each schema.
  3. Deleting `interventions` from `run/1`'s `required` makes `tests/formats/check_examples.py` fail
     (the invalid example `run-missing-interventions.json` exists).
  4. `grep -L "Legend" vocabulary/*.md` prints nothing; every status in `status.md` appears in
     06 §4's table and vice versa.
  5. CI green.
- **Hazards**: inventing fields "for later" (02 §5 says default specific); putting interpretation
  fields into `run/1` — the run record is raw only.
- **Runs on**: base
```

---

## 2. Generic implementation task — H4 Claim transaction (harness_imperial)

```markdown
# T14 Atomic task claims across machines
- **Kind**: infrastructure
- **Issue**: #14 · **Branch**: `task/T14-claim` · **Start after**: #1 (real run verified)
- **Implementer**: opencode (default chain) · **Claude fallback**: sonnet · **Reviewer**: claude (opus)
- **Why**: two machines (same GitHub account) must never both work a task; labels alone cannot
  guarantee it (two adds + two re-reads leave "second" undefined).
- **Evidence** (pasted):
  - IC2 build-process.md §8 (claim protocol, identity by `IC2_MACHINE` + `machine:<name>`,
    "only the claiming machine resumes") — pasted.
  - docs/phase0/03-work-execution.md §7.3–7.4 — pasted (the transaction and takeover).
  - GitHub REST "Create a reference": `POST /repos/{owner}/{repo}/git/refs` with `ref`, `sha`;
    an existing ref returns 422 — to be confirmed by Done-when 5, not assumed.
- **Owns**: `template/tools/harness/claim.mjs`, `template/tools/harness/lib/claim.mjs`,
  `test/claim.test.mjs`, `test/fake-gh.mjs`, `template/docs/process.md` §8 (claims paragraph only)
- **Scope**: `claim.mjs claim|release|status|takeover --task T<nn> --issue <n>`; machine id from
  `HARNESS_MACHINE`; claim = create `refs/heads/claim/T<nn>` at origin/main via `gh api`, then label
  `machine:<id>` + `status:in-progress`, then a claim comment `claim T<nn> machine=<id> at=<iso>
  lease=<h>h`; `status` prints holder, age, last activity (latest push to `task/T<nn>-*` or comment);
  `takeover` requires `--from <id>` and a stale lease (or `--force-user`), deletes then recreates the
  ref, swaps labels, comments. Exit codes: 0 won/done, 1 held/refused, 2 usage, 3 gh unavailable.
  **Not in scope**: preflight (T13), `/run-task` wiring (T15), any scheduler or polling loop.
- **Done when**:
  1. `npm test` green, including new `test/claim.test.mjs`.
  2. Fake gh returning 422 on ref creation → `claim` exits 1 and adds **no** label (test asserts the
     fake saw no label call).
  3. Two concurrent `claim` processes against the fake gh (which serializes ref creation) → exactly
     one exits 0 (test runs 20 iterations).
  4. `takeover` with a fresh lease exits 1 without `--force-user` (test).
  5. Against a real scratch repo (`diegoami/harness-scratch`), `node test/claim-real.mjs` run twice
     in parallel prints exactly one `won`; output pasted in the PR. Skips with an explicit SKIP line
     if `HARNESS_SCRATCH_REPO` is unset.
  6. Removing the 422 check from `lib/claim.mjs` makes test 2 fail (stated in the PR how checked).
- **Hazards**: adding the label before the ref (reintroduces the race); treating a network error as
  "held" (must exit 3, not 1); printing `GH_TOKEN`.
- **Runs on**: base · GitHub: push, issues, labels on the scratch repo for Done-when 5
```

---

## 3. Environment/preflight task — H3 Preflight (harness_imperial)

```markdown
# T13 Preflight: can this machine run this task now?
- **Kind**: infrastructure (environment)
- **Issue**: #13 · **Branch**: `task/T13-preflight` · **Start after**: #1
- **Implementer**: opencode · **Claude fallback**: sonnet · **Reviewer**: claude (sonnet)
- **Why**: claims must fail before expensive work on a machine that cannot run the task; "installed"
  has repeatedly not meant "usable".
- **Evidence** (pasted):
  - template/docs/environment.md: OpenCode Go "lists none, although `opencode console orgs` still
    exits 0" — pasted.
  - IC2 incidents: `pip install … || true` left capstone missing; WSL `opencode` on PATH is the
    Windows shim; prefix without `wineboot -u` makes every load time out — pasted from 01 §3.
  - docs/phase0/04-environment.md §1–4 (tokens, declaration file, output contract) — pasted.
- **Owns**: `template/tools/harness/preflight.mjs`, `template/tools/harness/lib/caps.mjs`,
  `test/preflight.test.mjs`, `test/fixtures/preflight/**`, `template/docs/environment.md`
  ("Preflight" section only), `template/machine.example.json`, `.github/workflows/ci.yml` (only to
  add the preflight smoke step for Done-when 5)
- **Scope**: parse a task file's `Runs on` line per the grammar in 03 §2.1 (`base` expansion, a single
  network class or a `<class> for <purpose>` list, `GitHub:` as `gh:*` tokens); load generic checks for
  `os`, `arch`, `tool` (with optional version constraint), `gh` (auth + repo read), `svc:opencode-go`
  (configured ids in `opencode models opencode-go`), `net:<class>` (HEAD each listed host, 5 s);
  merge `capabilities.json` from the repo root (token → check command, exit 0 = verified); read
  `machine.json` declarations; print `verified | declared-unchecked | unavailable: <reason>` per token
  and a verdict; `--json`; `--deep` gate for costly checks. Exit 0 ready, 1 not ready, 3 cannot run.
  **Not in scope**: claiming; installing anything; game-specific checks (they come via capabilities.json).
- **Done when**:
  1. `npm test` green, including `test/preflight.test.mjs`.
  2. With a fake `opencode` whose `models opencode-go` prints nothing but `console orgs` exits 0,
     `svc:opencode-go` is `unavailable` and the exit code is 1 (test).
  3. A `capabilities.json` check that exits 0 → `verified`; exits 1 → `unavailable` (test).
  4. Output for a run with `GH_TOKEN=secret-xyz` set contains neither `secret-xyz` nor any absolute
     path from `machine.json` (test greps captured stdout+stderr).
  5. `node template/tools/harness/preflight.mjs --tokens tool:node@>=20` exits 0 on CI (Linux and
     Windows matrix).
  6. Removing the version comparison from `lib/caps.mjs` makes the `tool:node@>=99` test fail.
- **Hazards**: trusting declarations as verification; slow default checks (no network beyond HEAD,
  no model prompts without `--deep`); Windows path handling for `machine.json`.
- **Runs on**: base · cloud: C0 · network: N1 (+ hosts under test for `net:*` checks; tests use a
  local stub server)
```

---

## 4. Game-specific runtime/integration task — W3a Isle Wars Pro runtime feasibility spike (isle-wars-archaeology)

(Its sibling W3b, for DOS Isle Wars under DOSBox-X, has the same shape and owns `runtime/iw-dos/**`.)

```markdown
# T03 Runtime feasibility: launch, act, observe, reset the reference artifact
- **Kind**: runtime (spike — produces a report and a profile draft, no driver)
- **Issue**: #3 · **Branch**: `task/T03-runtime-spike` · **Merge after**: T01 (artifact identity)
- **Implementer**: claude (sonnet) — judgment-heavy, not code-heavy · **Reviewer**: claude (opus),
  on a second machine that holds the artifact if one exists, else a fresh session on the same machine
  with that limitation stated
- **Why**: no driver, experiment or cloud decision can be made until we know what actually runs where.
- **Evidence** (pasted):
  - T01's merged finding F001: artifact set id, file list, platform statement, runtime-write list —
    pasted in full by the main session when T01 merges (this task stays `blocked` until then).
  - IC2 runtime facts as *hypotheses to test, not assumptions*: Wine 9.0 32-bit prefix + Xvfb +
    xdotool worked for a 1996 Delphi Win32 game; no window manager caused dropped clicks; `wineboot -u`
    as user was required; dialogs' controls are not X windows (01 §3) — pasted.
  - Security rule 04 §11: remove the prefix's `Z:` mapping — pasted.
- **Owns**: `runtime/iwp/spike/**`, `setup/iwp/**`, `findings/F002-*`, `capabilities.json` (the `iwp` tokens only)
- **Scope**: on this machine, try in order and record each outcome with exact versions:
  (a) native Windows, if the machine is Windows; (b) Wine (prefix arch per the binary's PE header)
  under Xvfb. For each: does it launch unattended;
  how to reach a known screen; does one keyboard/mouse input take effect (before/after observation);
  how to terminate and reset reliably; files written at runtime (diff of the install dir + prefix
  before/after); audio dependency; window/resolution behaviour. Draft `setup/iwp/iwp-runtime.sh` (or
  `.ps1`) ending in `preflight --tokens <profile tokens>`, and add those tokens' checks to
  `capabilities.json`.
  **Not in scope**: a reusable driver (T05); any game rule; decompilation; computer vision beyond a
  screenshot; network access for the game (N0).
- **Done when**:
  1. `findings/F002-*.md` has, per attempted path, a row: launch / known screen / input / observe /
     terminate / reset — each `works | fails: <evidence> | not tried: <why>`, with tool versions.
  2. For the best path, `runtime/iwp/spike/cycle.(py|ps1)` performs launch → one input → before/after
     screenshot → terminate, and running it 3× produces 3 run records validating against `run/1`
     whose `before` screenshot hashes are identical (or the finding states why they cannot be).
  3. `setup/iwp/iwp-runtime.*` exits only through `preflight --tokens …`; on this machine preflight
     prints `ready`; output pasted.
  4. `git ls-files | grep -iE '\.(exe|dll|dat|hlp|com|ovl)$'` prints nothing, and no tracked file is
     larger than 1 MB (`git ls-files -z | xargs -0 du -k | awk '$1>1024'` prints nothing).
  5. The finding's "What this does not establish" lists every untried path.
- **Hazards**: committing original files or a prefix; treating "it ran once" as unattended launch;
  fixed sleeps without recording them; generalizing Wine tricks into the meta repo (stays here);
  copying the user's install anywhere (U2: the bytes never leave this machine).
- **Runs on**: `artifact:iwp-*`, `facility:display`, `tool:python@>=3.11` (+ whichever runtime is
  tried) · cloud: **C3 only** (U2: no licence, the artifact never leaves the user's machines) ·
  network: **N0** for the game, N3 for bootstrap installs (hosts logged into the finding),
  N1 for push · GitHub: push, PR
```

---

## 5. Behavioural research task — Y2 Toy reinforcement rule (toy-archaeology)

```markdown
# T02 How many reinforcements does a player receive?
- **Kind**: research
- **Issue**: #2 · **Branch**: `task/T02-reinforcement` · **Merge after**: T01 (driver)
- **Implementer (researcher)**: claude (sonnet) · **Reviewer**: claude (opus) in a different session,
  ideally on a different machine (T03)
- **Why**: the walking skeleton's first discovery; proves question → evidence → reviewed finding.
- **Evidence** (pasted): driver capabilities from T01's `runtime/capabilities.json` (launch, act,
  observe screen text, save/restore, `--seed` = I3, `--dump` = I1) — pasted; formats `run/1`,
  finding template, status/basis/intervention legends — pasted from formats-v1.
- **Question**: At the start of a player's turn, how many reinforcement units are granted, as a
  function of the observable board state?
- **Hypotheses**: H0: a constant. H1: a function of provinces held. H2: also depends on holding whole
  islands. H3: depends on something else observable (turn number, units on board). Each is
  distinguished by varying one factor with the others fixed (Design).
- **Artifact**: `toy-1.0-<hash8>` (from `artifacts/known.json`); variant: none.
- **Runtime**: driver@T01-merge; max intervention **I3** (crafted saves to set ownership, `--seed`);
  justify each I3 use in the finding; at least one I0 confirmation run (normal play) required.
- **Design**: start states crafted to vary provinces held (1…8) with islands broken, then with each
  island completed; control = the same state reached by normal play where possible; n ≥ 3 per state
  (check stochasticity before concluding); stop when one hypothesis fits all states or none can.
- **Measurements**: reinforcement count read from screen text **and** from `--dump` delta; disagree
  → record both, do not choose.
- **Outputs**: `runs/E001/*.json`, evidence bundles uploaded as release `E001`, `findings/F001-*.md`
  status `proposed`.
- **Owns**: `experiments/E001-*/**`, `runs/E001/**`, `evidence/E001/**`, `findings/F001-*`
- **Scope**: answer the question for version 1.0 only. **Not in scope**: combat, AI, version 1.1,
  editing `spec/`, reading anything outside this repository.
- **Done when**:
  1. Every file in `runs/E001/` validates against `run/1` (`python3 tools/validate_runs.py runs/E001`).
  2. Every run record's `outputs[].sha256` matches the downloaded release asset
     (`python3 tools/verify_evidence.py E001` exits 0).
  3. Run records were pushed in commits **before** the commit that adds `findings/F001-*` (`git log
     --format=%H -- runs/E001 findings/F001*` order).
  4. Every sentence in the finding's Answer and Inferences cites ≥1 run id that exists in `runs/E001/`
     (`python3 tools/check_citations.py findings/F001-*.md`).
  5. The finding has non-empty "What this does not establish" and "Alternatives considered".
- **Hazards**: concluding from one run per state; reading the UI text as truth (the UI can be
  wrong); writing `supported` — the researcher writes `proposed`, only review + promotion change it;
  unpacking or reading the `.pyz` (static analysis is out of scope for this behavioural task); looking
  for the toy's source or rules anywhere (they are not reachable, and trying is a contract breach).
- **Runs on**: base, `tool:python@>=3.11`, `artifact:toy-1.0-*` · cloud: C0 · network: N1 (N2 if run
  via OpenCode) · GitHub: push, PR, release-write on **this repo only**. Run it in a cloud session
  scoped to `toy-archaeology`, or via OpenCode with a token for this repo alone; never with the owner's
  own `gh` login.
```

---

## 6. Independent research-review task — Y3 Review of F001 (toy-archaeology)

```markdown
# T03 Review F001 (reinforcement)
- **Kind**: research-review
- **Issue**: #3 · **Branch**: none — detached worktree at PR #<pr> head · **Merge after**: T02 PR open
- **Reviewer**: claude (opus), **not the session or machine that ran T02** (if impossible: a fresh
  session, stated in the review)
- **Why**: a finding does not reach the spec without an attempt to falsify it.
- **Finding under review**: `findings/F001-*.md` @ <sha>, with `runs/E001/` and release `E001`.
- **Evidence** (pasted): T02's contract in full; the research-review block (03 §6.2) in full;
  status/basis/intervention legends.
- **Reruns**: the reviewer chooses — at least 1 crafted-state run per hypothesis-discriminating state
  and the I0 confirmation run; rerun from the recorded start-state hash and seed; compare raw
  observations field by field.
- **Owns**: nothing (read-only); posts one PR comment; applies `status:approved` or `status:rework`.
- **Done when** (the review comment contains):
  1. Line 1 `T03 review (opus)`; line 2 record verdict (`approve | approve after named fixes | rework
     | user decision`); line 3 claim outcome (`supported | supported, narrowed: … | inconclusive |
     refuted`); verdict repeated as the last line.
  2. Gate 0–7 results (03 §6.2), each with the command run and its output tail.
  3. The rerun table: run id, reviewer's run record hash, fields compared, equal/different.
  4. ≥2 alternative explanations, each marked excluded/not excluded by the design.
  5. Findings R1..Rn classified implementation defect / contract defect (C) / architectural
     uncertainty / research uncertainty (03 §6.5).
  6. **After** posting: for the walking skeleton only, the main session (not the reviewer) scores
     the finding against SEALED.md in A6.
- **Hazards**: rerunning only the runs the researcher highlighted; reviewing prose instead of raw
  records; reading SEALED.md (it is not in this repository — do not look for it).
- **Runs on**: base, `tool:python@>=3.11`, `artifact:toy-1.0-*` · cloud: C0 · network: N1 ·
  GitHub: read, comment, labels `status:approved|rework`, release read
```

---

## 7. What writing these showed about the schema

1. **`Runs on: base` carried the two pure-code tasks** (A2 needs nothing else). The line is cheap
   for the common case and essential for W3a/Y2/Y3 — keep it mandatory, default `base`.
2. **Evidence must be pasted, and can be blocked on.** W3a cannot be `ready` until T01's finding is
   pasted into it; "Merge after" alone would have let a cold agent start without the artifact facts.
   Rule: a task whose Evidence says "pasted when X merges" stays `blocked`.
3. **Research Done-when lines test records, never truth.** Every attempt to write "H1 holds" as a
   Done-when line made the task unfalsifiable by the reviewer; the record checks (validation, hash
   match, push order, citations) are what a reviewer can re-run.
4. **The research tasks need four small tools** (`validate_runs`, `verify_evidence`,
   `check_citations`, `register_artifact`). They are written first in the toy repo (Y1) and copied
   into the IWP repo — the second copy is the trigger for moving them to the meta repo (02 §5).
5. **A review task has no branch.** The harness's T-id/branch assumption fits it badly; it is run
   by `/run-task`'s review step, not `implement.mjs`. Keep reviews as a *step* of the reviewed task
   in practice; the separate contract exists for the brief, and for cross-machine dispatch when the
   reviewer must be another machine.
6. **"Never in flight with" was not needed** in any example; disjoint Owns sufficed. Keep it
   optional.
