# Lessons (archaeology)

Archaeology lessons that hold across games, numbered from L200
([02 §3](docs/phase0/02-project-architecture.md)). Process lessons are in
[docs/lessons.md](docs/lessons.md) and, upstream, in the harness. A game-only lesson stays in its
game's repository. Every rule here is in [method/](method/) or [vocabulary/](vocabulary/) with the
failure or result that produced it; never renumber.

## The walking skeleton (M2: Y1–Y3, A6)

The archaeology loop ran once end to end on a target whose truth was sealed: a question, a blind
researcher (Y2), 323 runs and their bundles pushed before the finding, a falsifying review that
reran runs it chose (Y3), a promotion, and a score against the sealed rules (A6).

**The score.** F001 made two claims that go beyond what 06 §10 discloses: one about behaviour,
one about representation. Both are **correct**, and none is **wrong**. Five parts of the sealed
truth that the question touched are **unclaimed**; the finding declared each one as a limit, and the
review's narrowing of the claim followed exactly those limits. The detailed score names sealed rules,
so it is in the private `toy-target` only.

**The formats.** Y1–Y3 met no friction in `run/1`, `evidence-manifest/1`, `artifact-set/1` or the
vocabularies that needed a format change. All 646 of Y2's records (323 runs, 323 manifests) are
valid. 1,460 bundle entries share 477 files, deduplicated by the `<sha256[:16]>-<name>` asset names.
Y2's A/B pairs are linked through `start_state.sha256` with no new field. Y1's one intervention
problem (every loaded save marked I3) was the driver's, not the vocabulary's. The eight defects the
reviewer replay found (#14, items 1–8) are fixed by T05, and `formats-v1` is tagged after A6.

## Lessons

| # | Rule | What happened |
| --- | --- | --- |
| L200 | A finding is scored against sealed truth only after its review verdict, and the score stays where researchers cannot read it | A6 read SEALED.md for the first time after Y3's verdict, with its sha256 equal to the one posted on #9 before Y2 began. The score names the rules, and this repository is public. |
| L201 | A research PR merges with a merge commit, never a squash | Y2's DW4 proves that runs and bundles were committed before the finding, by commit order. A squash, the harness default, would have left one commit on `main` and erased that proof. |
| L202 | Every Done-when finishes inside the reviewer's limits, or the task names a faster equivalent | Y3's DW3 (`verify_evidence.py E001`) made one `gh` call per bundle entry, 1,460 in all. It ran past the reviewer's 600 s idle limit and would have outrun its 3,600 s total. One release download, then the same check on the local copy, took about 40 s. |
| L203 | A review gives one outcome per claim the finding proposes | F001 proposed a behaviour claim and a representation claim (R001). Y3's line 3 covered only the first, so R001 entered `spec/` as `hypothesis`, with nothing to promote it. |
| L204 | A blind researcher's local user is isolated in everything it shares with the owner: GitHub token, git transport, temp directory, toolchain | Setting up Y2/Y3's user: a clone over SSH failed (and an SSH key would have reached every repository), the first review exited 127 (node is per user), and the second hit EACCES on the harness's shared `/tmp/harness-opencode` (harness_imperial#30). |
| L205 | Once a session has read the sealed rules, it no longer drafts toy research contracts | Y2's contract was written blind, with four hypotheses that each varied one factor. After A6 the main session knows which one holds, and a contract it wrote could steer a researcher toward it through the hypotheses or the states. |
| L206 | Two pieces of evidence from one process are not independent, however many they are | F001's printed and dumped counts agreed in 165 of 165 pairs. Both came from the same process, as the finding said itself, and one finding with I0 and I3 runs on one machine and one driver was promoted `supported`, not `corroborated`. |
