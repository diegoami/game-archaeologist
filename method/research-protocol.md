# Research protocol

How a research task is run, reviewed and promoted, on top of `harness_imperial` (copied here, pinned
in [harness.lock](../harness.lock)). It transcribes the accepted design
([docs/phase0/03-work-execution.md](../docs/phase0/03-work-execution.md) §1, §2.2, §6;
[06-research.md](../docs/phase0/06-research.md) §10; [ADR-007](../docs/adr/007-evidence-provenance.md),
[ADR-008](../docs/adr/008-claim-lifecycle.md)). It lives here, not in the harness, until the toy and
Isle Wars repositories have used it ([ADR-002](../docs/adr/002-harness-reuse.md)).

## 1. Who runs what

| Role | Who | How | Credentials |
| --- | --- | --- | --- |
| Researcher | a Claude agent (Sonnet). Research is judgment: choosing what not to conclude. OpenCode only for a mechanical sweep the contract names. | the task file pasted in full, then the researcher block (§2), in its own worktree on `task/T<nn>-<slug>` | **Isle Wars**: a Claude agent with worktree isolation, on a machine holding the artifact (C3). **Toy research**: §6, never the owner's own `gh` login. |
| Research reviewer | `luna` (GPT-6 Luna on OpenAI) via `tools/harness/review.mjs`: another family than a Claude researcher. Claude Opus only when the researcher was not Claude. | the review block (§3) with the research task file pasted, `review.mjs --pr <n> --brief <file> --exclude claude --issue <n> --apply-label` | read the repository and the evidence release; comment; the two status labels |
| Promotion | the main session, only | §4, after merge | push to `main` |

`review.mjs` needs no change. It reads line 1 as the header, line 2 as the verdict, and the last
line as the repeated verdict. The claim outcome travels on line 3, which the harness does not parse;
the main session reads it at promotion. A finding that proposes more than one claim (a representation
claim `R<nnn>` included) gets one outcome line per claim, right after line 3. Y3 gave F001's
behaviour claim an outcome and its representation claim none, which left R001 at `hypothesis`.

## 2. The researcher block

Appended after the research task file, which is pasted in full. A research repository ignores
`scratch/` in its `.gitignore`. The block checks it, since not every repository does (#14, item 15).

```text
You research <T<nn>>. The task file above is the contract: its Question, Hypotheses, Artifact,
Runtime, Design, Measurements and Outputs bind you.
- First tool call: print `git rev-parse --show-toplevel`, `git rev-parse HEAD` and the preflight
  summary the brief gives. Every path you pass to a tool or type is inside your worktree; scratch
  work goes in `scratch/`, deleted before you finish. If `git check-ignore -q scratch/x` fails,
  `scratch/` is not ignored here: stop and report. Never cd, never write `..`.
- Raw before interpretation. Write one run record per run (`runs/E<nnn>/<run-id>.json`, valid
  `run/1`) and its evidence manifest, upload the bundle to release `E<nnn>`, and commit and push
  them, **before** you write any finding. A run that aborts is recorded as aborted, never dropped.
- Record every intervention, including passive ones (`{"level": "I0", "what": "none"}` for pure
  observation). The start state's sha256 and how it was restored go in every record.
- Observations are raw: what was read, where, from which source. A decoded value goes only in
  `decoded`, with `via` naming the representation claim (R<nnn>) that licenses it. If none
  exists, propose one in the finding; do not decode.
- Then write `findings/F<nnn>-<claim>.md` from `formats/templates/finding.md`, with status
  `proposed`. Every sentence in Answer and Inferences cites run ids that exist in `runs/E<nnn>/`.
  Write at least two alternative explanations and say which your design excludes. "What this does
  not establish" names every artifact, version, setting and state you did not test.
- The claim is no wider than what you ran: the artifact set and variant, the settings, the states.
  A rate needs enough runs to support a rate; say n.
- Never edit `spec/`, never promote, never widen the question. A Done-when line you cannot meet:
  stop and report. A result that refutes or does not decide the hypothesis is a result: write it
  as such.
- PR body: Closes #<issue>; Outputs (runs, manifest, release, finding); a fenced block with each
  Done-when command and the tail of its output; Docs changed.
```

## 3. The research-review block

The review block for `review.mjs`, followed by the research task file (pasted in full) and the
finding's path.

```text
<T<nn>> research review (<model>)
You review PR #<n> at <sha>: a research finding. You did not write it, and your job is to try to
falsify it. The task file follows. Work through the gates, in order:
G0 Tree and records: the tree proof your agent file asks for; every run record validates against
   run/1; for at least one evidence file, download it from release E<nnn> and check its sha256
   against the manifest.
G1 Artifact identity: every run's artifact set and variant match artifacts/known.json and the
   task's Artifact line; a patched variant is named as such.
G2 Environment identity: the runtime fingerprint is recorded; state how your environment differs.
G3 Reproduction: YOU choose at least one control and one treatment run (not the ones the finding
   highlights) and rerun them from the recorded start state and seed; compare raw observations
   field by field. A claim about a rate or a distribution needs its statistic rerun, not one sample.
   If your machine cannot run the artifact, say so: that is a tier you did not reach, not a pass.
G4 Raw vs interpretation: every sentence in Answer and Inferences cites run ids that exist;
   observations carry no interpretation; every decoded value cites an R-claim.
G5 Alternatives: write at least two other explanations of the observations yourself, and say for
   each whether the design excludes it. Check that the arms differ ONLY in the treatment: start-state
   path, how the state was restored, seed control, settings, driver path.
G6 Intervention: the finding's "Max intervention" equals the highest level in its runs, and each
   I2/I3 use is declared and justified in the finding; an I2/I3 result is not stated as
   untouched-original behaviour without a neutrality argument.
G7 Scope: the claim is no wider than the artifact versions, settings and states actually run.
Every finding names a file from the diff, and is proven (run it, quote the record) or labelled
unverified. Classify each: implementation defect | contract defect (C) | architectural uncertainty |
research uncertainty.
Post one PR comment:
  line 1: the header above
  line 2: the record verdict, one of: approve | approve after named fixes | rework | user decision
          (is the record sound?)
  line 3: "Claim outcome: " and one of: supported | supported, narrowed: <narrowing> | inconclusive |
          refuted   (what does the sound record establish?)
  then, if the finding proposes other claims (a representation claim R<nnn> included), one line
          each: "Claim outcome <id>: " and one of the same four
  then one line per Done-when line: "DW<k>: ran <command> → <result>" or "DW<k>: not run — <reason>"
  then one line per gate: "G<k>: <what you did> → <result>"
  then "Tier reached: V<k>" (the highest verification tier your review reached, and why not higher)
  then the findings R1..Rn (file:line, blocking or not, class)
  last line: the record verdict again, exactly as on line 2.
A refuted or inconclusive claim with a sound record is approved: a negative result is a result.
Apply status:approved or status:rework to issue #<issue>.
```

Every Done-when line of a research task must be runnable by this read-only reviewer
(harness_imperial#24). Mutations are made in place and restored; nothing is committed.

Every Done-when line must also finish inside the reviewer's limits (`review` in `harness.json`:
600 s without output, 3,600 s in all). A check that cannot comes with a faster equivalent in the task
file or the brief, which the reviewer reports it used. Y3's DW3 checked 1,460 bundle files with one
`gh` call each and outran both limits; one download of the release, then the same check on the local
copy, took about 40 s.

Review findings are numbered R1..Rn, the form the harness reader recognises. Representation claims
have three digits (`R001`), so the two do not collide.

## 4. Promotion

A research PR is merged with a merge commit (`gh pr merge <pr> --merge`), never squashed. Its
branch's commit order is the evidence that runs and bundles came before the finding (the Y2 contract's
DW4), and a squash would erase it from `main`.

After a research PR is merged, and only then, the main session:

1. Reads line 3 of the approving review, and any per-claim outcome lines after it. A claim the
   review gave no outcome goes in no higher than `hypothesis`, with the finding linked.
2. Updates the claim's row in `spec/<area>.md`, creating the file from
   `formats/templates/spec-area.md` if it is the area's first claim. It sets:
   - the status, by `vocabulary/status.md` § Finding outcomes;
   - the scope, the basis and the finding link.

   A representation claim goes to `spec/representation.md`.
3. Rewrites the area's summary from its `supported` and `corroborated` rows only.
4. Commits on `main` as `Promote F<nnn>: <claim id> <old status> → <new status>`, with the reason and
   the review URL in the body. There is no PR: the review already happened, and the next research
   review that touches the row checks the transcription.
5. Where the repository has a knowledge map, updates its cell for that area and artifact to point
   at the spec row. (toy-archaeology has none: its areas come from its research tasks.)

`inconclusive` changes no status: the row keeps `unknown` or `hypothesis` and gains the finding link.
A finding that conflicts with an existing `supported` row makes it `contested`; the user is told.

## 5. Defect routing

| The review finds | Class | Route |
| --- | --- | --- |
| a record that does not meet a sound contract (e.g. an invalid run record, a missing manifest) | implementation defect | `rework` on the same branch, at most two rounds, then escalate |
| a contract that is wrong or under-specified (a Done-when the reviewer cannot run, a design that cannot answer the question) | contract defect (C) | the main session amends the task on `main` with the reason; if the change is to Done-when semantics, the user is told; then re-review |
| a decision no document makes (a new record field, a new capability class) | architectural uncertainty | verdict `user decision`; an issue in game-archaeologist; the task is blocked |
| a sound record that does not decide the question | research uncertainty | not a defect: `approve`, claim outcome `inconclusive`, plus a new research-question issue saying what would decide it |

## 6. Toy research blindness

From [06 §10](../docs/phase0/06-research.md). A toy researcher (Y2) and its research reviewer (Y3)
must not learn the sealed rules except by experiment.

- **Credentials.** The researcher never runs with the owner's own `gh` login, which can read the
  private `toy-target`. Two paths limit GitHub access to `toy-archaeology`:
  - a Claude Code cloud session on that repository alone, started by the user with the brief pasted;
  - **a separate local user**, the path Y2 and Y3 ran on (the user's choice). The user creates it
    with its home closed to others (750). Its `gh` is logged in with a fine-grained token for
    `toy-archaeology` alone, and git uses https through `gh` (`gh auth setup-git`, `git_protocol
    https`). It never gets an SSH key, which would reach every repository the owner's key reaches.
    Its OpenCode data dir and provider login are its own, and so is its temp directory (`TMPDIR`
    inside its home: the harness's transcript folder under `/tmp` is shared between users,
    harness_imperial#30). Commands run as `sudo -iu <user> bash -lc '…'`, which must load its own
    node. The token is revoked when the research tasks it served are merged.

  After H2 lands, an OpenCode run with a fine-grained token for that repository alone is a third
  path. The research reviewer runs on the same credentials as the researcher.
- **Proof of blindness, first command.** The researcher runs `gh repo view diegoami/toy-target`
  and `git ls-remote https://github.com/diegoami/toy-target.git`, and both must **fail**. The
  private `toy-target` is the only place the concrete rules and their parameters exist
  (`SEALED.md`, the source, the tests). If either succeeds, the task stops before any run: the
  session can see too much.
- **What is public, and so disclosed.** game-archaeologist is public, and its
  [06 §10](../docs/phase0/06-research.md) describes the seven hidden rules, some almost completely:
  - rule 3, "an attack never moves the last unit; the UI reports success anyway";
  - rule 5, "the RNG is **not** restored by loading a save";
  - rule 6, "1.0 and 1.1 differ in exactly one rule".
  
  The other four are described by shape: a step function with an island-group bonus, stochastic
  combat with a tie rule, a periodic event every k turns affecting the largest stack, and a
  deterministic AI. Anyone can read this without a credential. **Everything 06 §10 states counts as
  disclosed.**
- **What the procedure keeps blind, and A6 scores.** Only what 06 §10 does not state:
  - the concrete form and parameters of each rule (the steps and bonus, the combat odds and tie
    rule, k and the event's effect, the AI's policy);
  - which rule differs between 1.0 and 1.1, and how;
  - any way a rule departs from its public description.
  
  At A6, a finding that only restates 06 §10 scores **disclosed**, not correct. Only what goes beyond
  it scores correct, wrong or unclaimed.
- **Reading limits.** The researcher needs this repository's `formats/`, `vocabulary/` and `method/`,
  and reads nothing else of it (`docs/phase0/` and `docs/adr/` are out of bounds). This cannot be
  enforced, which is why disclosure is defined above instead of assumed away. The research reviewer
  also checks that the finding claims nothing its runs do not show.
- **Network**: N1 (N2 through OpenCode), never N4. No web search.
- **Method**: behavioural only. Unpacking or reading the `.pyz` is static analysis, which is out of
  scope for Y2. The run records and the Method section show only I0–I3 behavioural methods, and the
  research reviewer checks that.
- **Barred sessions**: the sessions recorded on diegoami/toy-target#1 and #3 never run toy research
  or its review. Since A6, neither does the main session that scored F001 (it read `SEALED.md` and
  the source), nor the session that reviewed A6.
- **Toy contracts after A6.** A session that has read the sealed rules can lead a researcher by the
  hypotheses it lists or the states it designs. A later toy research contract is therefore drafted
  by a session that has never read `toy-target`, from 06 §10 and the toy's `spec/` alone. A
  convenient one is a Claude session run as the researcher's local user. The main session edits only
  its form: the template, Owns, Done-when.
- **Scoring**: A6, by the main session, after the review verdict is posted. It reads `SEALED.md` for
  the first time, checks its sha256 against the M2 tracking issue
  ([#9](https://github.com/diegoami/game-archaeologist/issues/9)), and scores each claim **disclosed**
  (only restates 06 §10), **correct**, **wrong** or **unclaimed**. The score names sealed rules, so it
  lives only in `toy-target`, as an issue there. This repository gets only its counts and classes;
  `toy-archaeology`, which toy researchers read, gets nothing of it.

## 7. Reviewer calibration

[examples/planted/](examples/planted/README.md) is a **fabricated** experiment and finding about a
fictional game, with defects planted in it. A research-review block can be checked by having a reviewer
apply it to the planted case, without the answer key, and scoring the defects found. The key is never
committed. Its sha256 is in the task that introduced the case (T04), and the key is posted on that
task's PR after the review. The case is for calibration only; it is never evidence about any game.
