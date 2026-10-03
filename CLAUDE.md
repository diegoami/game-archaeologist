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
7. Merge only with an approving review and green CI. Two rework rounds, then escalate.
8. Relay review findings in full, never a subset.
9. A test proves behaviour only if it fails when the behaviour is removed; a claim that nothing
   failed is re-taken before it is believed.
10. A comment asserting behaviour at an edge arrives with the test that visits that edge.
11. Until the first playable build, schedule only bugs that break play; label the rest
    `post-playable`.
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
    and Isle Wars originals never leave the user's own machines (ADR-006, U2).
20. Reviewers: `luna` (GPT-6 Luna) by default. A **guard task** is reviewed by `sol` (GPT-6 Sol), and
    its task file says why. A guard task is one whose failure would leak or corrupt evidence:
    blindness, the originals guard, sealed rules, record integrity. User decision of 2026-10-03,
    from the reviewer replay: Sol blocked every head that had a blocker, with no false findings.
    The roster, the routing and what each model has shown are in `docs/models.md`; the main session
    keeps it current.
