# 06 · Research architecture

## 1. Objects and their lifecycle

```
question ─► experiment (design) ─► run(s) ─► evidence bundle ─► finding (proposed)
   ▲                                                               │ research review
   │                                                               ▼
   └──── inconclusive / new question ◄──── finding (merged, with claim outcome)
                                                                   │ promotion (main session)
                                                                   ▼
                                                         spec claim (status, scope, basis)
```

| Object | Where | Mutable? | Purpose |
| --- | --- | --- | --- |
| **Question** | GitHub issue (`kind:research`, `triage:needed` until shaped) → task file `Question` | yes, until dispatched | what we want to know |
| **Experiment** | `experiments/E<nnn>-<slug>/` — `README.md` (question, hypotheses, design, copied from the task), scripts | append-only after first run (new version = new E-number or `v2/`) | the procedure |
| **Run record** | `runs/E<nnn>/<run-id>.json` | **immutable** | one execution; raw only |
| **Evidence bundle** | evidence store, by hash; manifest at `evidence/E<nnn>/<run-id>.manifest.json` | immutable | saves, screenshots, dumps, logs |
| **Finding** | `findings/F<nnn>-<claim-as-title>.md` | corrected only by a marked correction or a superseding finding | the interpretation |
| **Spec claim** | row in `spec/<area>.md` | status changes only by promotion | the current best statement |

**Raw evidence is never edited to fit an interpretation; interpretations are corrected without
touching raw evidence.** That is the core invariant (principle 4).

## 2. Run record (schema `run/1`, provisional fields)

```json
{
  "schema": "run/1",
  "run_id": "E007-r0003",
  "experiment": "E007", "arm": "treatment-B", "rep": 3,
  "code_commit": "<game repo sha>", "machine": "desk",
  "artifact": { "set": "iwp-1.x-ab12cd34", "variant": "iwp-1.x-ab12cd34-seed" },
  "runtime": { "driver": "runtime@<sha>", "platform": "wine-9.0/ubuntu-24.04/xvfb", "fingerprint": { "…": "…" } },
  "interventions": [ { "level": "I3", "what": "seed 12345 via SEED.TXT", "variant": "…-seed" } ],
  "start_state": { "id": "S-newgame-default", "sha256": "…", "restore": "fresh process + load save" },
  "seed": 12345,
  "actions": { "script": "experiments/E007/run.py", "sha256": "…", "args": ["--arm", "B"] },
  "observations": [
    { "step": 0, "source": "save", "field": "raw:bytes[0x1A0:0x1A4]", "value": "04000000" },
    { "step": 1, "source": "screen", "ref": "sha256:…png" },
    { "step": 1, "source": "memory", "addr": "0x8123", "value": "05" }
  ],
  "outputs": [ { "name": "after.sav", "sha256": "…", "store": "release:E007" } ],
  "started": "…", "ended": "…", "status": "completed | aborted: <reason>"
}
```

No interpretation fields. A `decoded` view (e.g. `"robot_target": "factory B"`) may be added **only**
with `"via": "R014"` naming the representation claim that licenses the decoding (§5). IC2's
`results.json` failures — 1 of 4 seeds kept, a lossy dict, no build hash — are each prevented by a
field above plus "one immutable file per run".

## 3. Observation versus intervention

| Level | Name | Examples | Result means |
| --- | --- | --- | --- |
| **I0** | pure observation | normal play through the UI; parsing a save the game wrote; reading the manual | untouched-original behaviour |
| **I1** | passive instrumentation | screenshots; read-only memory (`/proc/pid/mem`); debugger watchpoints that do not alter flow; static analysis | untouched behaviour, but timing-sensitive games may differ under a debugger — say so |
| **I2** | harness-enabling modification, claimed neutral | autosave hook, async sound, no-delay battles, a save-state | original behaviour **if** the neutrality claim holds |
| **I3** | behaviour-altering intervention | forced RNG seed, memory write, crafted/modified save, ROM/EXE patch changing logic, altered timing | behaviour *of the modified system*; evidence about the original only by argument |

Rules: every run lists its interventions; a finding states its max level; a **spec claim built on
I2/I3 evidence carries either a corroboration at a lower level or a cited neutrality argument**
(e.g. "the seed patch replaces only the source of the seed; R003 shows Randomize's output feeds the
same generator" — and a control showing the measured property is unchanged without the patch where
practical). IC2's always-on `no_delay` instant battles were never tested for neutrality; under this
rule that would have been its own finding.

## 4. Claims: status, basis, scope

Evaluated against the proposed labels:
- `observed`, `reproduced` are properties **of evidence**, not states of a claim → they become
  *basis* and *count*.
- `verified` is ambiguous (verified by whom, how?) → replaced by explicit review + corroboration.
- `version-specific` is a **scope qualifier**, orthogonal to status.
- `superseded` is a link, not a truth value.

**Status** (claim truth state; one of):

| Status | Meaning | Gets there by |
| --- | --- | --- |
| `unknown` | nothing established — the default, written explicitly | knowledge map |
| `documented` | asserted by a manual/help/designer, not yet tested | doc research (basis `doc`) |
| `hypothesis` | proposed, with a test design | a question |
| `supported` | a reviewed finding supports it, by one method | research review → promotion |
| `corroborated` | supported by ≥2 independent methods (behavioural + static, or two independent runtimes/machines, or I0 + I3) | second reviewed finding |
| `refuted` | a reviewed finding contradicts it | research review |
| `contested` | reviewed findings disagree, unresolved | promotion when a new finding conflicts |

Plus `superseded-by: <claim id>` as a link. **Basis** tags (any combination), defined once in the
meta repo with a legend: `doc`, `observed` (I0/I1 behaviour), `parsed` (file format read),
`static:decompile|listing|bytes`, `intervened` (I2/I3), `quantified: N of N`. **Scope**: artifact set
(and variant), settings, state preconditions. IC2 mapping for reference: `[confirmed: decompile]` →
`supported` + `static:decompile`; `[confirmed: saves]` → `supported` + `parsed, quantified`;
`[derived]` → `hypothesis`; `[open]` → `unknown`; `[designed]` → not an archaeology status (it belongs
to a rebuild).

**Corrections:** one style only — `> **Correction (YYYY-MM-DD, F0nn):** …` in the corrected finding,
and the spec row changes status with the superseding finding linked. Mistakes are stated, not
quietly fixed (IC2 `evidence-index.md:114`).

## 5. Raw observation vs semantic interpretation

`memory[0x8123] changed 4 → 5` is an observation. "Robot target changed from factory A to B" needs a
**representation claim**: `R014: byte 0x8123 of the robot record holds the target factory index
(scope: artifact X)`. Representation claims live in `spec/representation.md` with the same status
lifecycle. Decoded values in records and findings cite them. If R014 is later refuted, every finding
citing it is mechanically discoverable (`grep R014`) and re-interpretable from unchanged raw evidence.
IC2 did this implicitly (SAV field tags in `sav-layout-notes.md`); here it is explicit and shared
by memory maps, save formats and screen readings alike.

## 6. Experiments

Minimum representation: the research task's extension fields (03 §2.2) copied into the experiment
README, one script, one run record per run. **No DSL**: actions are code in the game's language; the
run record hashes the script and its arguments. A DSL is justified only if two games' experiments
would share action vocabularies, which nothing indicates.

**Branching** (`state S → arms A, B, C`): expressed in the design as one `start_state` and several
`arms`. The runner restores S before each arm and **records the restored state's hash per arm** —
that is how identity of S is proven, not assumed. Restoration is a per-game capability
(`restore: savestate | fresh process + load + seed | emulator snapshot`); IC2 showed restoring a
save is not restoring RNG, so `restore` must name everything it reinstates. A game that cannot
restore states runs arms from a deterministic replay from new game, or cannot branch — and its
questions are designed as population comparisons instead.

## 7. Runtime capabilities

Capability-*specific* per game, with a **declared capability list** rather than a common adapter
interface:

```json
// runtime/capabilities.json in the game repo — documentation + preflight tokens, not an interface
{ "launch": true, "terminate": true, "reset": "fresh-process", "input": ["mouse", "keyboard"],
  "observe": ["screenshot", "save-file", "ui-text"], "save_state": "in-game save only",
  "restore": "fresh process + load", "seed_control": "I3 patch | none", "frame_step": false,
  "memory_read": "proc-mem (I1)", "memory_write": false, "breakpoints": false, "trace": false }
```

Experiments declare which capabilities they use; preflight checks those that are machine-dependent.
A shared Python interface (`launch() / act() / observe() / restore()`) is extracted only when two
real games' drivers exist and their call sites repeat. Test case for the decision: Gain Ground under
MAME (frame stepping, savestates, Lua memory access) and IC2 under Wine (no frame stepping, patch-
based seed) share almost nothing below "launch".

## 8. Static analysis integration

- Static work is a research task like any other, basis `static:*`, level I1.
- Every static claim names the **binary sha256** and an **address or symbol**, never a line number in
  a regenerated dump (IC2 lesson). Scripts (Ghidra, capstone, pefile) are **committed**; the Ghidra
  project itself is local (C3, `re-static` profile), reproducible from the binary + committed scripts.
- Exported annotations (symbol names, struct layouts) live in `static/` as text with the binary hash.
- The productive loop seen in IC2 — disassembly says Randomize is not called on load; SEED.LOG
  counts confirm behaviourally — is exactly **corroboration**: the spec rewards combining methods.
- Static analysis is never started "because it is possible" (Isle Wars prompt, step 6); it answers a
  named question or recovers a representation claim a behavioural question needs.

## 9. Specification (minimal)

```
spec/
  README.md            areas, status legend, how to read
  representation.md    R-claims: file formats, memory layout, screen elements
  <area>.md            one per area the knowledge map names (setup, turn, combat, …)
```

Each area: a short prose summary of *supported/corroborated* claims only, then the claim table:

| ID | Claim | Status | Scope | Basis | Findings |
| --- | --- | --- | --- | --- | --- |
| C-SET-01 | A new game with identical settings produces an identical initial position | unknown | — | — | — |

No ontology, no entity schema. Areas are the knowledge map's areas; the prose is regenerated by the
main session at promotion. A reconstructed implementation, if ever built, consumes this table and its
tests cite claim ids — that is the IC2 "corpus with provenance" (L15) at specification level.

## 10. The toy target (walking-skeleton subject)

**Purpose:** prove the loop can *discover* hidden behaviour, in C0/V0, with no copyrighted artifact.
Lives in the meta repo (`toy-target/`); distributed to the toy research repo only as a built,
hashed artifact (a Python zipapp `toy-isles-<ver>.pyz` on a meta-repo release).

**Shape (deliberately Isle-Wars-like, ~300–400 lines, stdlib only):** a 2-player territorial
game on a fixed 8-province, 3-island map, text UI over stdin/stdout, binary save files with an
undocumented layout, `--seed` flag (an I3 "patch" analogue), `--dump` (raw bytes of internal state:
the memory-read analogue), `--poke addr=val` (memory write, I3).

**Hidden rules** (in `toy-target/SEALED.md`, committed with its sha256 announced in the M2 tracking
issue; the toy research repo never contains it):
1. Reinforcement is a step function of provinces held with an island-group bonus (discoverable by
   designed experiments).
2. Combat is stochastic with a tie rule (needs repeated runs and statistics).
3. A silent clamp: an attack never moves the last unit; the UI reports success anyway (observation
   vs UI text disagree).
4. A periodic event every k turns affecting the largest stack (timing; needs long runs).
5. The RNG is **not** restored by loading a save (IC2's trap, so the method must detect it).
6. Two artifact versions, 1.0 and 1.1, differ in exactly one rule (scope/version discipline).
7. A deterministic AI policy (behavioural inference of AI).

**Blindness:** the researcher works only in the toy research repo (worktree confinement + a task
token scoped to that repo). Blindness is a methodological aid, not a security boundary; the research
reviewer checks findings against SEALED.md **after** the review verdict is posted, and records the
score (claims correct / wrong / unclaimed) as the walking-skeleton's outcome measure.

**Not built:** graphics, a second map, networking, more than one AI policy.

## 11. Future targets as architecture tests (not built)

| Target | Stresses | Does the architecture hold? |
| --- | --- | --- |
| Nether Earth (ZX Spectrum) | emulator state + memory inspection + annotated disassembly | yes: savestate restore, I1 memory reads, representation claims, `static:*` basis; needs `tool:fuse` or similar — a profile, not a framework change |
| Gain Ground (MAME) | frame stepping, arcade input, big experiment matrices | yes: per-game capabilities (`frame_step`), branching from savestates; matrices = many runs → evidence volume makes the content-addressed store matter; possible pressure for a shared runner (extract then, not now) |
| Shadowfire | inferring multi-agent order semantics | yes: hypotheses with competing models, I0 observation; stresses the *representation* claims for queued orders |
| Omega | semantics of a programmable in-game machine | spec areas become "a language" — a spec area may need a grammar, still a claim table per instruction; no ontology needed in advance |
| Exile / The Sentinel | blind benchmarks vs known RE | the toy-target method scaled up: sealed reference = public RE; blindness enforcement matters more (agents can web-search) → run as N0/N1 tasks |
| Bagman, Paradroid, Gain Ground | arcade timing, AI pursuit | timing claims need frame-accurate observation (V2 only with a frame-stepping emulator) |

Nothing in the list requires a component now. Gain Ground is the likeliest first forcing case for a
shared experiment runner; Exile/Sentinel for blindness enforcement.
