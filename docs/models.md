# Models: who implements, who reviews, and how

This page is the main session's working strategy for routing work to models. It covers this
repository and the two toy repositories the same session runs:
[toy-target](https://github.com/diegoami/toy-target) (private) and
[toy-archaeology](https://github.com/diegoami/toy-archaeology) (private). isle-wars-archaeology and
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

| Name in `harness.json` | Model and route | Family | Where it is entered | Used for |
| --- | --- | --- | --- | --- |
| `deepseek-flash` | DeepSeek V4.1 Flash, `opencode-go/deepseek-v4.1-flash` | DeepSeek | all three | the default implementer |
| `glm-flash-zai` | GLM-5.3 Flash, `zai-coding-plan/glm-5.3-flash` | GLM | toy-archaeology | a trial implementer; viable (two fixes, below) |
| `luna` | GPT-6 Luna, `openai/gpt-6-luna`, the direct OpenAI route | OpenAI | all three | the default reviewer, and the research reviewer |
| `sol` | GPT-6 Sol, `openai/gpt-6-sol` | OpenAI | all three | the reviewer of guard tasks (rule 20) |
| (Claude) Opus | the main session | Claude | — | architecture tasks (A1–A6), the toy target (A4), the score (A6) |
| (Claude) Opus or Sonnet | a Claude session as the blind user | Claude | — | toy research (Y2); the contract says Sonnet, and Y2 ran on Opus |

Every model runs at effort `high` (`variant` in `harness.json`), never `max`.

**Probed, not entered:**
- GLM-5.3 on the Z.AI Coding Plan, and DeepSeek V4 Pro: they answer, but the reviewer replay
  below gave neither a role.
- `glm-5.3-highspeed`: refused by the plan.

## Routing: which pair for which work

| Work | Implementer | Reviewer | Why |
| --- | --- | --- | --- |
| Code, tools, tests, format examples | `deepseek-flash` (OpenCode) | `luna` | cheap; Luna proves findings by mutation |
| A **guard task**: blindness, the originals guard, sealed rules, record integrity (formats, the checker) | `deepseek-flash`, or the main session | **`sol`** | a miss here leaks or corrupts evidence; in the replay only Sol blocked every head that had a blocker (rule 20) |
| Architecture: ADRs, the method, the retrospective | the main session (Opus) | `luna`, or `sol` when it is a guard task | the decisions are recorded ones; the reviewer checks citations and scope |
| Toy research | a Claude session **as the local user `blind`** (method §6) | `luna`, also as `blind` | the researcher and its reviewer must not reach `toy-target` |
| A toy research contract, after A6 | a Claude session that never read `toy-target` | — | the main session has read the sealed rules and could lead the researcher (method §6) |

The reviewer is never the implementer's family. `review.mjs --exclude <implementer>` enforces it,
and `--reviewer sol` picks Sol.

## How a run is made

- **Implementer:** `node tools/harness/implement.mjs --task T<nn> --slug <slug> --issue <n> --brief <file> [--model <name>]`,
  with `run_in_background`, never a shell `&`. On rework the same command resumes the branch.
- **Reviewer:** `node tools/harness/review.mjs --pr <n> --brief <file> --exclude <implementer> --issue <n> --apply-label [--reviewer sol]`.
- **As `blind`:** `sudo -iu blind bash -lc '. ~/.nvm/nvm.sh && export TMPDIR=~/tmp && cd ~/toy-archaeology && …'`.
  `blind` cannot read the main session's scratchpad: pipe a brief in on stdin
  (`sudo -iu blind bash -lc 'cat > ~/brief.md' < brief.md`).
- **Briefs:** the implementer brief is the task file pasted in full, then process.md §4's block, then
  on rework the review's URL. The review brief is §5's block (research: method §3's) filled in,
  then the task file. Until harness_imperial#19 and #24 land, a review brief also asks for one
  `DW<k>:` evidence line per Done-when line.
- **The header** names the reviewer: `T<nn> review (sol)`. With `--reviewer`, a placeholder such as
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
