Phase 0 package review (DeepSeek-V4-Pro)
approve after named fixes

ADR verdicts
ADR-001: accept with named changes (R1, R6)
ADR-002: accept with named changes (R5, R14)
ADR-003: accept with named changes (R8, R10)
ADR-004: accept with named changes (R9, R12)
ADR-005: accept
ADR-006: accept
ADR-007: accept with named changes (R11)
ADR-008: accept
ADR-009: accept with named changes (R13)

Confirmed claims
- 40-line CLAUDE.md, 150-line process.md: evidence/harness_imperial/template/CLAUDE.md (40 lines), evidence/harness_imperial/template/docs/process.md (150 lines).
- Lessons L1–L26, each tied to a real failure: evidence/harness_imperial/template/docs/lessons.md.
- ~1,100 lines of Node tooling (actual 1,104): evidence/harness_imperial/template/tools/**/*.mjs.
- Six commits: evidence/harness_imperial/GITLOG.txt.
- "A full run through implement.mjs has not happened yet": evidence/harness_imperial/README.md:138.
- implement.mjs resumes a pushed branch and hard-codes `--task` to `^T\d{2,3}$`: evidence/harness_imperial/template/tools/harness/implement.mjs:33,58.
- 409 commits, 2026-09-12 → 2026-10-01: evidence/imperial_conquest_2/GITLOG.txt.
- 113 task files T01–T113: evidence/imperial_conquest_2/docs/tasks/.
- Two-machine protocol §8 (IC2_MACHINE + `machine:<name>`, cloud session "claims no task", "A machine claims only tasks whose labels it can satisfy"): evidence/imperial_conquest_2/docs/build-process.md:393-399,416.
- "CI is the authority on test results" and "A result seen only under Wine gets one confirmation on the desktop": evidence/imperial_conquest_2/docs/build-process.md:448, evidence/imperial_conquest_2/docs/evidence-pipeline.md:42.
- 11 "grant T<nn> …" plan PRs: evidence/imperial_conquest_2/GITLOG.txt (11 `Plan: …grant…` commits).
- T66 C1 contract finding settled by the main session: evidence/imperial_conquest_2/docs/tasks/T66.md:13.
- `pip … 2>/dev/null || true` (setup.sh:27), plain-https clone (setup.sh:32), curl release downloads (opening-prompt.md:23): evidence/ic2-conquest/setup/setup.sh:27,32, evidence/ic2-conquest/docs/opening-prompt.md:23.
- `wineboot -u` as user is a manual step without which loads time out: evidence/ic2-conquest/HANDOVER.md:52.
- results.json holds 1 of the 4 seeds the README reports and carries no build hash; the lossy dict comprehension `{u["type"]: u["troops"] for u in …}`: evidence/ic2-conquest/runs/experiments/gallic-army/results.json, evidence/ic2-conquest/runs/experiments/gallic-army.py:66.
- Seed build `354d8265…` identified only in prose, not asserted by setup.sh: evidence/ic2-conquest/findings/2026-09-29-loading-a-save-does-not-reseed.md:12, evidence/ic2-conquest/setup/pins.txt.
- Autosave hook before StartTurn (0x45217A) plus async_sound/no_delay in patch_exe.py: evidence/imp_conquest_fixtures/patch_exe.py:51,287-289.
- 64 saves, four patched EXEs, `WAVS/` beside `WAVS - Copy/`, unexplained `.cnt`: evidence/imp_conquest_fixtures/ALL_TRACKED_FILES.txt.
- fetch-release.sh targets `diegoami/imp_conquest_original` and verifies no checksum: evidence/imp_conquest_fixtures/scripts/fetch-release.sh:11.
- 75 report files; intake outcomes `promoted / promoted, corrected / merged into / rejected / deferred`; "Three things that will mislead you"; correction at line 114; scanned/surveyed/read/exhausted ledger: evidence/imperial-conquest-2-research/docs/reports/ (75 .md), evidence/imperial-conquest-2-research/docs/findings-intake.md:13, evidence/imperial-conquest-2-research/docs/evidence-index.md:31,114, evidence/imperial-conquest-2-research/docs/recording-ledger.md:14-17.
- Decompilation plan points at the demo hash file and says "The executable is not run" while live Wine runs exist: evidence/imperial-conquest-2-research/docs/decompilation-plan.md:3, evidence/imperial-conquest-2-research/docs/reports/impconq2-sha256.txt vs impconq2-full-save-sha256.txt.
- malpaco quotes at the cited lines (Soleau 1994, $12, relaxed redistribution, 46-across-9 misread 2026-09-18, "The constants here are ours"): evidence/malpaco/RULES.md:13-15,19-25, evidence/malpaco/DECISIONS.md:431-432,462-463,166-173,318.
- `envWith()` copies the whole process.env into agent runs: evidence/harness_imperial/template/tools/harness/lib/common.mjs:52-53.
- checkReview requires the verdict on line 2 and repeated as the last line — compatible with the two-axis research verdict (line 2 record verdict, line 3 claim outcome): evidence/harness_imperial/template/tools/harness/lib/chain.mjs.
- Stale "(orchestrator-managed)" label descriptions: evidence/imperial_conquest_2/LABELS.txt.
- Atomic claim via `POST /git/refs` (201/422) is sound: ref creation is per-name compare-and-set; the H4 race test and lease-takeover rules cover the failure scenarios I tried.

R1 · package/06-research.md:191-206, package/02-project-architecture.md:60-63, package/07-delivery-plan.md:108 · blocking · unsound mechanism. Proof: the meta repo is public and holds the sealed rules — package/02-project-architecture.md:60-63 "Meta repo (exists empty, public: diegoami/games_revival_framework …) … `toy-target/` (source + sealed rules + build)"; package/06-research.md:191 "Hidden rules (in `toy-target/SEALED.md`, committed with its sha256 announced in the M2 tracking issue)". A toy researcher (Y2) runs with network N1 = GitHub (package/07-delivery-plan.md:108) and `gh` tooling, so `gh api repos/diegoami/games_revival_framework/contents/toy-target/SEALED.md` reveals every hidden rule; the only guard is a "Not in scope: reading anything outside this repository" line (package/08-example-contracts.md:213), and the package itself concedes agents web-search (06 §11). The M2 walking-skeleton score ("discover hidden behaviour") then proves nothing. Change: keep SEALED.md out of any researcher-reachable repo until A6 (private repo or a release-only artifact), and add "never read toy-target/SEALED.md" to Y2's Hazards.

R2 · package/01-existing-systems.md:14,109,92-93 · non-blocking · evidence error. Proof: "~1,100 lines of Node tooling with 56 tests" — the six fake-based test files define 63 named `test(` blocks (chain 11, implement 7, review 6, opencode 21, jev 12, models 6; 65 with opencode-real) per evidence/harness_imperial/test/*.test.mjs; "a 30-line mingw Win32 helper (`harness/win_controls.c`)" — the file is 42 lines, evidence/ic2-conquest/harness/win_controls.c; "implementer model routing changed four times on 2026-10-01 alone" — evidence/imperial_conquest_2/GITLOG.txt shows three chain changes on 2026-10-01 (#552, #556, #574). Change: correct the three numbers.

R3 · package/01-existing-systems.md:159-160,181 · non-blocking · evidence error. Proof: package claims "[confirmed] (184), [derived] (72), [confirmed: code] (15), [open] (7)"; plain grep over docs/reports/ yields 201, 86, 23, 12 (only [confirmed: decompile]=40 and [hypothesis]=4 match) — evidence/imperial-conquest-2-research/docs/reports/. And "a sibling repo uses a different scheme ([C]/[D]/[O]/[P])" — the actual scheme is `[C]/[D]/[?]/[P]`: evidence/ic2-conquest/docs/sav-layout-notes.md:14. Change: state the counting method or correct the counts and the scheme letter.

R4 · package/01-existing-systems.md:57,71,92,199-200; package/README.md:93; package/01-existing-systems.md:16,209 · non-blocking · evidence error. Proof: unverified. "98 merged tasks, 133 bugs", "machine:desktop ×15, machine:rogx ×2", "~125 Plan/Process PRs vs ~139 task PRs", "54 duplicated byte-for-byte in releases", "~805 MB / ~181 MB", "0 forks", issue #1's title, and ic2-test-fixtures' "99 saves / 42 CI cases" have no supporting data in evidence/ (no issue/PR/label-count/release-size/forks dump), and the catalogue explicitly refuses counts: evidence/imperial_conquest_2/docs/task-catalogue.md:9 "No counts are kept here". Change: either add the GitHub data to the package or mark these [I]/unverified.

R5 · package/01-existing-systems.md:285,51; package/README.md:22-23; package/02-project-architecture.md:54-57,125 · non-blocking · inconsistency. Proof: "it should file four bounded upstream changes against harness_imperial" (01:285) vs "Five bounded upstream harness changes" (README:22); "Extend the harness upstream for deficiencies 1–4" (01:51) includes deficiency 3 (research task kinds), but "Meta repo first; upstream to harness after toy + IWP use it" (02:125) and 03 mark the research blocks [M], while 02:55-56 says the harness holds "after M1 … the research task-kind brief/review blocks". Change: fix the count to five (H2–H6) everywhere and make research-kind upstreaming timing one value.

R6 · package/02-project-architecture.md:74,69; package/07-delivery-plan.md:62,106; package/README.md:102 · non-blocking · inconsistency. Proof: "isle-wars-archaeology (to be created at W-M1)" (02:74) vs "W0 isle-wars-archaeology repo" (07:62) and U10 "private isle-wars-archaeology (W0)" (README:102); also "user approval needed for repo creation" (02:69) and "repo creation needs user OK" (07:106) vs U10 "Both new repos approved". Change: make creation milestone W0 everywhere and drop the stale approval wording.

R7 · package/07-delivery-plan.md:33,27; package/08-example-contracts.md:166-167 · non-blocking · inconsistency. Proof: "W-M1 runs in parallel with M1–M3 because it depends on no generic code" (07:33), yet W-M1 is "demonstrated by … preflight verifies artifact:<set> and the runtime tokens" (07:27) — preflight is H3, merged at M3 — and W3a's Done-when requires "3 run records validating against run/1" (08:166-167), a schema from A2 with no A2→W1a/W3a edge in the dependency graph (A6 freezes it). Change: add A2→W-track edges (or an explicit "draft schema" note) and state that W-track claims/preflight apply only after M3.

R8 · package/07-delivery-plan.md:89; package/03-work-execution.md:29; package/08-example-contracts.md:11,50,92,137,187,234 · non-blocking · under-specification. Proof: the backlog names tasks H/A/Y/W (07:89) but the contract template and all six examples use per-repo T-numbers (T01–T15), with collisions inside 08 itself (two "T02"s, two "T03"s), and the harness enforces `^T\d{2,3}$`: evidence/harness_imperial/template/tools/harness/implement.mjs:33. The H3=T13 etc. mapping is never stated, so a cold agent cannot tell which task file H4's example is. Also 08:22 cites "truncated hashes" as an IC2 failure that 01 §3 never lists, and H3's Done-when 5 requires a "Linux and Windows matrix" CI whose workflow file is not in Owns (08:104-106). Change: state the ID convention (one sentence), fix the example numbering, and add the CI workflow to H3's Owns.

R9 · package/03-work-execution.md:256; package/04-environment.md:48 · non-blocking · inconsistency. Proof: "One primary … is designated by a repository variable, gh variable set HARNESS_PRIMARY" (03:256) vs the machine.json example carrying "primary": true (04:48). Change: remove "primary" from machine.json or state which mechanism wins.

R10 · package/07-delivery-plan.md:121; package/04-environment.md:144 · non-blocking · inconsistency. Proof: W8a/W8b (research reviewers) get "Runs on: as W7x", inheriting `gh:release-write:isle-wars-archaeology` (07:120-121), while the least-privilege table gives research review only "read evidence store" (04:144). Change: give W8x a reviewer Runs-on (release read only).

R11 · package/06-research.md:29-48,115-128 · non-blocking · mission gap. Proof: mission.md:944 requires "confidence;" in the minimum experiment representation; no package format (run/1, finding, experiment README) carries a confidence field. Also mission.md:995,999 lists "inconclusive" among labels to evaluate ("Do not adopt these labels without evaluating them"), but 06 §4 never states where inconclusive went (it silently became a review claim outcome in 03 §6.2). Change: add a confidence field to the finding schema (or explicitly reject it with a reason in 06 §4) and add one sentence evaluating "inconclusive".

R12 · package/04-environment.md:31,69-71,26 · non-blocking · unsound mechanism. Proof: the `gh` checks are "gh auth status; gh api repos/<r> succeeds (read); the claim ref creation is the first real write" — ref creation proves push, but `gh:pr` permission is never verified, so a task can run to completion and only then fail to open a PR; and "ready" admits "declared-unchecked for declaration-only tokens" (04:69-71) while only `facility:desktop` is ever marked declaration-only (04:26). Change: add a cheap PR-permission probe (e.g. `gh api repos/<r>/pulls?state=open&per_page=1` write-context check) and enumerate the declaration-only tokens.

R13 · package/07-delivery-plan.md:15; package/02-project-architecture.md:129; package/08-example-contracts.md:278; package/06-research.md:144 · non-blocking · inconsistency. Proof: ADR-009 says "generic only with two concrete uses" (07:15) and 06:144 extracts the driver interface "when two real games' drivers exist", but 02:129 defers code "until a third copy" and 08:278 says "the second copy is the trigger for moving them to the meta repo". Change: pick one trigger (two uses) and align all four statements.

R14 · package/01-existing-systems.md:284; package/07-delivery-plan.md:8,179 · non-blocking · mislabelled decision. Proof: "Concern A is solved well enough to adopt, and it is young" (01:284) and ADR-002 "Decided from evidence" (07:8) rest on "the harness is its tested distillate" (README:56), but the harness has never completed a real run — evidence/harness_imperial/README.md:138 — and the package's own risk table rates "Harness unproven in a real run" high/high (07:179). The reuse-vs-rebuild decision is evidence-backed; "solved" is not. Change: keep ADR-002 as Decided for "no second orchestration layer", but state in it that operational readiness is provisional pending H1.

approve after named fixes
