# Models: who implements, who reviews, and how

This page is the main session's working strategy for routing work to models. It covers this
repository and the two toy repositories the same session runs:
[toy-target](https://github.com/diegoami/toy-target) (private) and
[toy-archaeology](https://github.com/diegoami/toy-archaeology) (private), and
[goal2-archaeology](https://github.com/diegoami/goal2-archaeology) (private, U14–U20). isle-wars-archaeology and
malpaco keep their own page, also `docs/models.md`. The two pages share the harness, not their
roster names: this page's `sol` is their `gpt-6-sol`.

- **No status.** What is running lives in the labels; what each run did is in its PR's measurement
  comment (process.md §9).
- **The binding rules** are CLAUDE.md rules 1, 6 and 20. Where this page and those rules differ,
  the rules win, and this page gets fixed.
- **Who decides.** The owner chooses the models. The main session keeps a switch cheap:
  - every candidate stays probed, with a `harness.json` entry in each repository that uses it;
  - each task file names its implementer and its reviewer, and says why when it is not the default;
  - a switch is applied to tasks not yet started, with the owner's reason in the commit message.

## The roster

| Name in `harness.json` | Model and route | Family | Used for |
| --- | --- | --- | --- |
| `zai-glm-5.3-flash` | GLM-5.3 Flash, `zai-coding-plan/glm-5.3-flash` | GLM | **easy implementer**, the `harness.json` default; probed 2026-10-03, PONG in 5 s |
| `deepseek-flash` | DeepSeek V4.1 Flash, `opencode-go/deepseek-v4.1-flash` | DeepSeek | **hard implementer** (`--model deepseek-flash`) |
| `luna` | GPT-6 Luna, `openai/gpt-6-luna`, the direct OpenAI route | OpenAI | **easy reviewer**, the `harness.json` default, and the research reviewer |
| `gpt-6.1-sol` | GPT-6.1 Sol, `openai/gpt-6.1-sol` | OpenAI | **hard reviewer** (`--reviewer gpt-6.1-sol`); probed 2026-10-03, PONG in 6 s |
| `sol` | GPT-6 Sol, `openai/gpt-6-sol` | OpenAI | the hard reviewer before 6.1 (T05, T06) |
| `glm-flash-zai` | GLM-5.3 Flash (toy-archaeology only; the same model as `zai-glm-5.3-flash`) | GLM | the implementer trial (toy-archaeology #8, #9) |
| (Claude) Sonnet | `claudeFallback` | Claude | both fallback implementers; the easy fallback reviewer; toy research as `blind` |
| (Claude) Opus | the main session; the hard fallback reviewer | Claude | architecture tasks (A1–A6), the toy target (A4), the score (A6) |

Every model runs at effort `high` (`variant` in `harness.json`), never `max`.

**Probed, not entered:**
- GLM-5.3 on the Z.AI Coding Plan, and DeepSeek V4 Pro: they answer, but the reviewer replay
  below gave neither a role.
- `glm-5.3-highspeed`: refused by the plan.

## Routing: easy or hard

The owner decided on 2026-10-03 that the pair follows the task's difficulty, as in
isle-wars-archaeology (CLAUDE.md rule 20):

| Difficulty | Implementer | If it is unavailable | Reviewer | If it is unavailable |
| --- | --- | --- | --- | --- |
| Easy, the default | GLM-5.3 Flash | Sonnet | GPT-6 Luna | Sonnet |
| Hard | DeepSeek V4.1 Flash | Sonnet | GPT-6.1 Sol | Opus |

**When a task is hard.** Any of:
- a **guard task**: blindness, the originals guard, sealed rules, record integrity (the formats and
  their checker);
- a new mechanism across several files, or a new external dependency;
- game rules, formulas or constants implemented from evidence (the owner's decision of
  2026-10-03, from the Jev trial: these were most of the "easy" IC2 tasks that took two or more
  rework rounds);
- an earlier round found blocking bypasses.

Everything else is easy: doc and config fixes, exact-line contracts, single-mechanism code with
clear tests. The main session decides, until Jev is calibrated for it (below); the task file's
Implementer and Reviewer lines say `easy` or `hard` with the reason. A hard task passes
`--model deepseek-flash` and `--reviewer gpt-6.1-sol`, and names Opus as its Claude fallback
reviewer.

**Jev decides the clear hard cases** (decision `task-hard`, [docs/jev/task-hard.md](jev/task-hard.md)).
Route a new task file through `jev.mjs route --decision task-hard` (run with `bash -ic`, where the
OpenRouter key is set). At p ≥ 0.8 it is hard, and the task file says "hard (Jev, p = …)"; anything
else the main session decides, since no cutoff for easy passed the trial. Trial of 2026-10-03, on
132 task files labelled blind by Sonnet agents: held out, 46 of 46 hard calls agreed (100%),
covering 72% of items. Against IC2's review outcomes, the labels' hard tasks averaged 1.55 rework
rounds (43 of 84 took two or more) and their easy ones 0.93 (3 of 15). Counting game rules from
evidence as hard (the owner's decision, after the first trial) moved most of the reworked "easy"
tasks to hard.

**The exceptions:**

| Work | Implementer | Reviewer | Why |
| --- | --- | --- | --- |
| Architecture: ADRs, the method, the retrospective | the main session (Opus) | by difficulty | the decisions are recorded ones; the reviewer checks citations and scope |
| Research, spikes and static reading (judgment, not code) | Claude, with worktree isolation: **Opus when the task is hard**, Sonnet when it is easy | by difficulty | the owner's preference of 2026-10-03: hard judgment work goes to Opus (goal2 T02 and T04 started on Sonnet before it was stated) |
| Toy research | a Claude session **as the local user `blind`** (method §6) | `luna`, also as `blind` | the researcher and its reviewer must not reach `toy-target` |
| A toy research contract, after A6 | a Claude session that never read `toy-target` | — | the main session has read the sealed rules and could lead the researcher (method §6) |

The reviewer is never the implementer's family. `review.mjs --exclude <implementer>` enforces it.

**Watch:** L27 records GLM-5.3 Flash stalling and ending long implementer runs early in IC2. Its
two trial runs here were clean. Its first runs as the default are watched, and a stall is
diagnosed before any fallback.

## Escalating the implementer after a heavy review

Adopted on 2026-10-03 from isle-wars-archaeology's proposal, which the owner passed on ("adopt if
appropriate"). When a reviewer shows that the implementer is out of its depth, the next round goes
to a stronger implementer. A task does not spend its last rework round on the same model. T05 is
the case that would have triggered it: Sol found a new blocking code-span defect in each of three
rounds, and the task escalated to the owner.

**Trigger.** Either of these, judged from the review just posted:
- the review asks for rework with three or more blocking findings;
- a rework round brings new blocking findings of the same class as the previous round's (for
  example, the same kind of bypass found again in new code): the fix did not converge.

**Ladder.** The implementer moves up one step for the next round, and never steps down within a task:
- GLM-5.3 Flash (`zai-glm-5.3-flash`) → DeepSeek V4.1 Flash (`deepseek-flash`) → Claude Opus;
- Claude Sonnet → Claude Opus.

**Rules that still hold:**
- The rework-round limit (rule 7) does not reset. After the last round, a remaining blocking finding
  goes to the owner with options.
- The reviewer stays from another family than the implementer. If Opus implements and no OpenCode
  reviewer is available, a Claude fallback reviewer is not allowed: escalate to the owner.
- The Done-when is never weakened to make the stronger model's round pass.

**Hand-over.** The main session:
1. stops the current implementer if it is mid-round;
2. saves its unpushed work as a patch (`git add -N` new files, then `git diff > patch`);
3. starts the new implementer on the pushed branch with the task file pasted in full, every review so
   far (the current one in full), the patch path "to weigh, never to apply blindly", and an
   instruction to fix the class of the findings, not each instance, then to sweep its own code for
   the same class and list the sweep in the PR body;
4. records the change on the task file's Implementer line, with the finding counts as the reason, and
   commits that on `main`.

**Records.** After the round, the PR's measurement comment gives the models, the trigger, the
finding counts before and after, and whether the stronger model converged; "What each model has
shown" below gains a line. After several escalations, compare them before tuning the trigger.

## How a run is made

- **Implementer:** `node tools/harness/implement.mjs --task T<nn> --slug <slug> --issue <n> --brief <file> [--model <name>]`,
  with `run_in_background`, never a shell `&`. On rework the same command resumes the branch.
- **Reviewer:** `node tools/harness/review.mjs --pr <n> --brief <file> --exclude <implementer> --issue <n> --apply-label [--reviewer gpt-6.1-sol]`. A hard task passes `--model deepseek-flash` to the implementer and `--reviewer gpt-6.1-sol` here.
- **As `blind`:** `sudo -iu blind bash -lc '. ~/.nvm/nvm.sh && export TMPDIR=~/tmp && cd ~/toy-archaeology && …'`.
  `blind` cannot read the main session's scratchpad: pipe a brief in on stdin
  (`sudo -iu blind bash -lc 'cat > ~/brief.md' < brief.md`).
- **Briefs:** the implementer brief is the task file pasted in full, then process.md §4's block, then
  on rework the review's URL. The review brief is §5's block (research: method §3's) filled in,
  then the task file. Until harness_imperial#19 and #24 land, a review brief also asks for one
  `DW<k>:` evidence line per Done-when line.
- **The header** names the reviewer: `T<nn> review (gpt-6.1-sol)`. With `--reviewer`, a placeholder such as
  `(MODEL)` is printed as written.
- **Merging:** a squash, except a research PR, which merges with a merge commit (method §4).

## Adjustments that keep runs working

| Adjustment | Why | Learned |
| --- | --- | --- |
| `export PATH=$HOME/.nvm/versions/node/v24.21.0/bin:$PATH` before the scripts | node is not on the non-interactive shell's PATH | 2026-10-02 |
| Every Done-when line runnable by a read-only reviewer: stage instead of commit | a reviewer cannot commit, so a line that needs a commit cannot be re-run | W0, harness_imperial#24 |
| Every Done-when line finishes inside the reviewer's limits (600 s idle, 3,600 s total) | Y3's evidence check made 1,783 `gh` calls and outran both | Y3, toy-archaeology#11 |
| "Never cd, never `..`" in every brief | a tool call outside the worktree fails the run | A4's first attempt; harness_imperial#14 |
| The blind user: https git through `gh` (never an SSH key), its own `TMPDIR`, its own node and OpenCode login | an SSH key reaches every repository; the harness's `/tmp` folder is shared between users | Y2/Y3 setup; harness_imperial#30 |
| Dry-run every Done-when line before a task starts | a line nobody can meet reached a reviewer twice (T04's blindness check, fix #6's DW2) | 2026-10-02/03 |
| Scope added by the main session is scoped as tightly as the evidence | in T05, "skip code spans", which no item required, took three Sol rounds and an escalation | T05 |

## What each model has shown so far

- **DeepSeek V4.1 Flash** (implementer): sound on tools and formats. It stops on a Done-when it
  cannot meet. In T05 it fixed all eight format items first time, but the code-span parsing the
  main session had added needed three rounds against Sol.
- **GLM-5.3 Flash** (implementer, trial): two fixes in toy-archaeology (#8, #9), each exit 0 on the
  first attempt, inside Owns, in about 450 s and 264 s. Its briefs lacked process.md §4's block.
- **GPT-6 Luna** (reviewer): fast, and it proves findings by mutation. In the reviewer replay of
  2026-10-03 it caught 0 of 8 known defects. It ran Y3 (the research review) cleanly: it reran a
  control and a treatment field by field.
- **GPT-6 Sol** (guard reviewer): the adversary. In the replay it caught 2 of 8 known defects and
  gave the correct rework verdict on 3 of 3 heads, with no false findings. In T05 it found a real
  defect in each of three rounds, each reproduced with a scratch file. In T06 its two blocking
  findings were both correct (a literal Done-when, an amendment citing nothing).
- **GLM-5.3 on Z.AI** (replay reviewer): 2 of 8, but approved every head.
- **DeepSeek V4 Pro** (replay reviewer): 0 of 8, one run returned nothing.
- **Claude Opus** (main session, and Y2's researcher as `blind`): Y2's finding was scored correct
  against the sealed rules, with every limit declared (toy-target#5).

## Keeping this page current

The main session updates this page in the same commit as any of these: the owner switches a model;
a `harness.json` entry is added or removed; a run teaches a new adjustment; a run changes what a
model is known to do well or badly.
