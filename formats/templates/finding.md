# F<nnn> <The claim, as one sentence>

- **Status**: proposed | merged, outcome: supported | supported, narrowed: <narrowing> | inconclusive | refuted
- **Question**: <the falsifiable question, as in the task>
- **Tests claims**: C-<AREA>-<nn>, R<nnn>, … (the spec rows this finding bears on)
- **Experiment and runs**: E<nnn>; runs E<nnn>-r0001 … (every run cited below exists in `runs/E<nnn>/`)
- **Artifact**: set `<set id>`, variant `<variant id>` | none
- **Max intervention**: I0 | I1 | I2 | I3
- **Tier reached**: V0 | V1 | V2 | V3 | V4
- **Confidence**: <outcome> — <basis>, <n runs / N of N agreement>, <alternatives excluded or not>

## Answer

<A few bullets. Each sentence cites the run ids it rests on. No sentence here that the Observations
do not support. `## Answer` and `## Inferences` hold only list items, `###` sub-headings, tables
whose data rows each cite a run, and blank lines; `check_citations.py` refuses anything else there
(U25).>

## Method

<Artifact and variant. Runtime: driver@commit, platform, versions. Start state (id, sha256, how
restored). Arms, n per arm, seeds. The action script and its hash. Static tools and the binary sha256
with addresses, when used.>

## Observations

<Raw only: what was read, from which source, in which run. A decoded value cites the R-claim that
licenses it. Tables of raw values and hashes. No interpretation.>

## Inferences

<What the observations mean, each inference naming the observations it rests on.>

## Alternatives considered

<At least two other explanations of the observations, each marked "excluded by <which arm/run>" or
"not excluded".>

## What this does not establish

<The scope limits: other artifact versions, settings, states, tiers not reached, questions left open.>

## Where the evidence is

<The evidence manifests (`evidence/E<nnn>/<run-id>.manifest.json`) and the release that holds the
bundles.>

## Reproduction

<Commands, from a clean clone on a machine whose preflight passes for the task's `Runs on`.>

<!-- Corrections, if any, go just under the title in the one allowed style:
> **Correction (YYYY-MM-DD, F0nn):** <what was wrong, and what is right> -->
