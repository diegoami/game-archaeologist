# game-archaeologist

The method for evidence-backed behavioural specifications of old games (decisions, record formats,
vocabularies), built from the Phase 0 analysis of the Imperial Conquest 2 projects. The process is
`docs/process.md`; read it before running a task. Tasks are `docs/tasks/T<nn>.md`, indexed in
`docs/tasks/README.md`.

## Rules
1. The main session plans, runs `/run-task`, triages and talks to the user. It delegates (`/delegate`):
   code to OpenCode, review to another model family, repeated decisions to Jev after a trial, and
   images and audio to OpenRouter or ElevenLabs models, whose ids come from live lists, never memory.
2. Nobody works in the main checkout but the main session: OpenCode runs in the worktree the script
   makes, Claude agents run with worktree isolation. Never `git stash`.
3. Status lives in GitHub labels. No document carries a status snapshot.
4. A question is not a request to edit files. Answer it; propose any fix and wait.
5. The Done-when is not negotiable by the implementer. It stops and reports; it never weakens an
   assertion, skips a test or edits its task file. The main session amends a Done-when on `main`
   with the reason in the commit message.
6. The reviewer is never the implementer's model family. It re-runs every Done-when line itself.
7. Merge only with an approving review and green CI. Two rework rounds, then escalate. After a heavy
   review, the next round's implementer moves one step up, never down (`/run-task`). (L38)
8. Relay review findings in full. Read a run's final message before you retry or re-route it (L55).
9. A test proves behaviour only if it fails without that behaviour; re-take a claim that nothing failed.
10. A comment asserting behaviour at an edge arrives with the test that visits that edge.
11. Until the first playable build, schedule only bugs that break play; the rest are `post-playable`.
12. A bug whose fix stays in the files it names and changes no outcome is a `fix`; a blocking
    one-file mechanical fix may ride the PR that found it, declared under Scope.
13. Design decisions go to the user; nothing else waits for the user.
14. At session start: `gh issue list --label triage:needed --state open`, and any task in flight.

## Token economy
15. A brief carries the task file pasted in full, never a pointer to it.
16. Keep every file an agent must read under ~20k tokens. Scope searches to the source and test
    directories; keep terminal output quiet; show diffs, not files.

## This project
17. The architecture is `docs/adr/` (ADR-001..009, accepted 2026-10-02). `docs/phase0/` is the record
    they cite, including the reviews and the user's decisions U1–U12. Change it only by a recorded
    decision.
18. No game code, game artifacts or orchestration code here (ADR-001, ADR-002). A process gap is a
    `harness_imperial` issue with its lesson. The copied harness is pinned in `harness.lock` and
    changes only by a harness bump. Rule 11 has no effect: this repository builds no playable game.
19. Generic only with two concrete uses (ADR-009). Original game files never enter any repository,
    and Isle Wars originals never leave the user's own machines (ADR-006, U2). The one exception is
    GOAL2, treated as abandonware: its files and extracts may sit in private `goal2-archaeology` (U17).
20. The model pair follows the task's difficulty (the owner's decision of 2026-10-03, as in
    isle-wars-archaeology). **Easy**, the default: GLM-5.3 Flash implements and GPT-5.6 Luna reviews,
    with Sonnet as both fallbacks. **Hard**: DeepSeek V4.1 Flash implements and GLM-5.3 reviews; GPT-6.1 Sol
    (effort `low`, `medium` if justified, never `high`; every heavy model runs at its lightest effort, `docs/models.md`) reviews guard tasks and a hard task's last rework round,
    and every complex task: guards, harness or driver changes, measurement integrity, research deliverables,
    plans with many acceptance lines (the owner, 2026-10-04). GPT-5.6 Luna (`luna`, its own weekly pool; harness_imperial L51) reviews only small, simple PRs. A task is hard if it is a **guard task** (its failure
    would leak or corrupt evidence: blindness, the originals guard, sealed rules, record integrity),
    if it adds a new mechanism across several files or a new external dependency, if it implements
    game rules, formulas or constants from evidence (the owner's decision of 2026-10-03), or if an earlier
    round found blocking bypasses. The main session decides; the task file's Implementer and
    Reviewer lines say `easy` or `hard` with the reason. Before choosing or delegating to any model, check its provider's quota
    with quota-tracker (`docs/environment.md`); an `exhausted` provider is skipped for the chain's next
    model, passed explicitly and named in the report (harness_imperial L50). The roster, the routing and what each model
    has shown are in `docs/models.md`; the main session keeps it current. After a review with three or more
    blocking findings, or a second round of the same class, the next round goes to a stronger
    implementer (`docs/models.md`, escalating the implementer).
21. **Read a delegated run's report before acting on it** (the owner, 2026-10-05). Before you retry a
    delegated run, re-route it to another model, or call it a failure, read what it returned. Never
    retry blind. An OpenCode run's final message lives in its session record, not in the log's tail
    (`docs/models.md`, "Reading a run's report"). For a Claude agent, read its hand-back in full. A
    run that stopped and reported gets an answer: amend the task, decide, or escalate. Its report is
    posted on the task's issue. An earlier "model X ends runs early" verdict stays unconfirmed until
    its runs' final messages have been read.
