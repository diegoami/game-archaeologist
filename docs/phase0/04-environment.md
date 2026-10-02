# 04 · Environment architecture

## 1. Three things that are not the same

| Concept | Question | Where it lives | Who writes it |
| --- | --- | --- | --- |
| **Requirement** | What does this task need? | task file `Runs on` line (committed) | main session |
| **Declaration** | What does this machine say it has? | `~/.config/harness/machine.json` (local, never committed) | the machine's owner, once |
| **Verified capability** | What is usable **now**? | preflight output (ephemeral; summary posted in the claim comment) | `preflight.mjs` |

A declaration is a hint, never proof. A token is **verified** only by a check that ran now;
**declared** when the machine claims it but no check exists or it was skipped as expensive;
**unavailable** when the check failed or the token is undeclared. Evidence this distinction is
needed: OpenCode Go "logged in" while `opencode console orgs` exits 0 and lists no models; `pip …
|| true` leaving capstone missing; a Wine prefix lacking a user profile so every load times out;
the WSL `opencode` on PATH being the Windows shim (01 §7.4).

## 2. Capability vocabulary

Token grammar: `<category>:<name>[@<constraint>]`. Constraints only where compatibility matters.

| Category | Tokens (initial; added only when a task needs one) | Check (cheap, non-destructive) |
| --- | --- | --- |
| `os` / `arch` | `os:linux`, `os:windows`, `arch:x64` | `process.platform`, `process.arch` |
| `tool` | `tool:git`, `tool:gh`, `tool:node@>=20`, `tool:python@>=3.11`, `tool:opencode@1.18`, `tool:wine@9`, `tool:xvfb`, `tool:xdotool`, later `tool:dosbox-x@…`, `tool:mame@…`, `tool:vice@…`, `tool:ghidra@12` | `--version` parse; version only where the token has a constraint |
| `facility` | `facility:display` (any X/Win display), `facility:desktop` (interactive, a human can look), `facility:audio`, `facility:persistent-disk` | `xdpyinfo`/env; `desktop` is declaration-only (can't be proven by a script) |
| `exclusive` | `exclusive:wine-display`, `exclusive:godot` | no conflicting process running |
| `hw` | none initially; `hw:disk>=<n>G` when a task stores large evidence | `statfs` |
| `artifact` | `artifact:<set-id>` e.g. `artifact:iwp-1.x-<hash8>`, `artifact:toy-1.0-<hash8>` | locate via `machine.json` path → sha256 every file against the committed set manifest |
| `svc` | `svc:opencode-go`, `svc:openrouter`, `svc:claude` (the session itself) | `opencode models opencode-go` contains the configured ids; OpenRouter `/models` with key; optional `--deep` one-token prompt (costs tokens) |
| `gh` | `gh:read`, `gh:push`, `gh:pr`, `gh:issues`, `gh:labels`, `gh:release-read:<repo>`, `gh:release-write:<repo>`, `gh:fixtures-read:<repo>` | `gh auth status`; `gh api repos/<r>` succeeds (read); the claim ref creation is the first real write and happens before expensive work |
| `net` | `net:none`, `net:github`, `net:provider`, `net:packages`, `net:web`, `net:allow:<list>` | HEAD request to each host in the class with a 5 s timeout |

Generic tokens and their checks live in the harness **[H]**. Game repos add tokens in
`capabilities.json`: `{ "<token>": { "check": "<command>", "describes": "…", "cost": "cheap|slow" } }`,
exit 0 = verified. Example: `"facility:iwp-prefix": { "check": "python3 runtime/check_prefix.py" }`.

## 3. Machine declaration

`~/.config/harness/machine.json` (on Windows `%APPDATA%\harness\machine.json`; never in git):

```json
{
  "id": "desk",
  "declares": ["os:windows", "facility:desktop", "facility:audio", "artifact:iwp-1.x-ab12cd34"],
  "artifacts": { "iwp-1.x-ab12cd34": "D:/games/originals/isle-wars-pro" },
  "restrictions": { "noCloudSync": ["artifact:*"], "concurrency": 1 }
}
```

Paths and restrictions stay local. A committed `machine.example.json` documents the shape. Machines
come and go (U7): a new machine is a new `machine.json` plus its first preflight, and a retired
machine simply stops claiming. Its stale claims are taken over (03 §7.4). **No shared machine
inventory** is committed: discovery is local (03 §7.2), and the claim comment's
preflight summary is the visible record of what each machine could do when it claimed. Add a shared
inventory only if a real failure shows the user cannot tell which machine to provision.

## 4. Preflight / doctor [H]

```
node tools/harness/preflight.mjs --task T07            # can THIS machine run T07 NOW?
node tools/harness/preflight.mjs --tokens tool:wine@9 artifact:iwp-…   # ad hoc
node tools/harness/preflight.mjs --machine             # verify everything declared
  [--json] [--deep]
```

- Expands `Runs on: base`, merges generic and repo `capabilities.json` checks.
- Prints one line per token: `verified | declared-unchecked | unavailable: <reason>`; verdict
  `ready` only if every required token is `verified`, or `declared-unchecked` for one of the
  **declaration-only tokens**, which no script can prove: `facility:desktop` (a human can look) and
  `facility:audio` (a human can hear). The list is closed; adding to it is a harness change.
- `gh:pr` has no non-destructive probe: push access does not prove a fine-grained token may open PRs.
  So it is proved early instead of checked. H5 makes `/run-task` open a **draft PR** right after the
  claim and the first push, before any expensive work. A missing PR permission then fails in minutes,
  and the draft PR makes the work visible from the start.
- **Never prints** environment values, token strings, or local paths; reports `GH_TOKEN: set`, not
  its value (the session-start hook's existing rule).
- Cheap by default: no model prompts, no game launches, no downloads. `--deep` may spend (one
  model token, a 1-second emulator launch) and says so.
- Exit codes match the harness convention: 0 ready, 1 not ready (reasons printed), 3 preflight
  itself could not run.
- `/run-task` step 0 runs it before claiming **[H5]**; the summary goes in the claim comment and in
  the brief.

## 5. Bootstrap: clean machine → ready for a class of tasks

Profiles are **bundles of tokens with an idempotent setup script**, created only when a task needs
them. Each script ends by running `preflight --tokens <profile tokens>`; the script's own exit code
is not trusted (IC2 `|| true` lesson).

| Profile | Tokens | Where defined | Exists when |
| --- | --- | --- | --- |
| `base` | git, gh (logged in), node ≥20 | harness `docs/environment.md` | now |
| `agent-opencode` | `tool:opencode@1.18`, `svc:opencode-go` | harness (session-start hook does it in cloud) | now |
| `toy` | python ≥3.11, `artifact:toy-*` (downloaded by hash from the `toy-archaeology` release) | `toy-archaeology` | M2 |
| `iwp-runtime` / `iw-dos-runtime` | decided by W3a (Windows, or Wine+Xvfb) / W3b (DOSBox-X) | game repo `setup/iwp/`, `setup/iw-dos/` | W-M1 |
| `re-static` | `tool:ghidra@12`, JDK 21, committed scripts | game repo, local only | when the first static task is approved |

Pin where results can depend on the version (Wine, emulators, OpenCode CLI, Ghidra when citing
listings); do not pin where they cannot (Python minor, gh). A pinned version is *checked* by
preflight, not just installed. Manual steps that cannot be scripted (buying/registering an artifact,
`opencode console login`, a human looking at a screen) are listed in the profile's README with the
preflight token that proves each was done.

## 6. Cloud suitability — a property of the task

| Class | Meaning | Typical tasks |
| --- | --- | --- |
| **C0** | any cloud session: no artifacts, no GUI | harness/meta code, formats, toy target, toy experiments (non-copyrighted artifact), documentation research |
| **C1** | cloud + private CI fixture subset via a read-only token | real-save parser tests |
| **C2** | cloud + original artifact, headless | Wine/emulator experiment reruns — **only for games whose rights decision allows the artifact off the owner's machines. Not Isle Wars (U2): its artifact tasks are C3/C4.** |
| **C3** | local research machine | needs a declared-only facility, a large local corpus, Ghidra project, or an artifact not cleared for cloud |
| **C4** | human present | visual confirmation (V4), first-run installers, purchasing/registering |

Criteria, in order: artifact licence → OS/GUI → secrets needed → persistent disk → runtime length/cost.
A task is never "cloud-capable" because its *project* is; it says its class. **A class above C1 is
not marked cloud-capable until a task has demonstrated it** (prompt for Isle Wars, step 3).

## 7. Network policy

Classes describe what a **task** needs; the game runtime itself gets **N0** unless a finding shows
otherwise.

| Class | Allows | Needed by |
| --- | --- | --- |
| **N0** none | — | running an original under Wine/emulator; offline analysis |
| **N1** github | `github.com`, `api.github.com` (+ release-asset download hosts, to be discovered) | push, PR, labels, release download |
| **N2** github + provider | N1 + the provider hosts of the configured delegates | implementer/reviewer runs |
| **N3** packages | N1 + package registries a bootstrap uses | bootstrap only |
| **N4** web | open web (read) | historical/documentation research only |

**Endpoint source rule:** a host enters a class only with its source — authoritative documentation
or a logged, tested run. Hosts known now, from `harness_imperial/template/docs/environment.md`
(tested in its cloud session): `opencode.ai`, `openrouter.ai`, `api.elevenlabs.io`,
`registry.npmjs.org`, `api.github.com`, `github.com`, the Ubuntu archive, optional `models.dev`.
GitHub release-asset download hosts, PyPI, WineHQ and emulator download sites are **not yet
established** for this project: H3's and W3x's first runs log the hosts they reach and record them
with that evidence. IC2 also observed the cloud proxy refusing release access (`IC2_RELEASE_TOKEN`
403) — C2 tasks must test release download in their first run.

## 8. GitHub access by task kind (least privilege)

| Task kind | read | push branch | PR | comment | labels | releases | Actions | private fixtures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| implementation / environment | ✓ | ✓ | ✓ | ✓ (claim) | main session only | — | read logs | only if Runs on says so (read) |
| research | ✓ | ✓ | ✓ | ✓ | main session only | **write** to the evidence store | — | read |
| implementation review | ✓ | — | — | ✓ (via script) | `status:approved/rework` | — | read logs | read, if the tier needs it |
| research review | ✓ | — | — | ✓ | as above | **read** evidence store | — | read |
| main session | ✓ | ✓ | ✓ | ✓ | ✓ | as tasks need | ✓ | as tasks need |

The OpenCode agent files already deny label edits, merges and force-push to implementers and all
writes to reviewers. Tokens: fine-grained, per repository, contents/PRs/issues read-write for
working repos; **a separate read-only token scoped to each private fixture/evidence repo** (IC2
`FIXTURES_TOKEN`); release-write only on evidence stores.

## 9. Agent / model providers

Providers are execution services behind the harness's delegate model (`harness.json` chains,
families, `/delegate`). The architecture names **roles**, never models. A task may require
`svc:<provider>` only when it genuinely depends on it (e.g. image reading for screenshot
interpretation → a vision-capable model). Verification: CLI exists → authenticated → configured
model ids present in the live list (L25) → optional `--deep` one-token prompt. Input/output
capability (image, audio) is checked from the live list's modalities (`models.mjs` already filters
on them).

## 10. Secrets

1. No secret values in git, task files, briefs, evidence records, run records, logs, or PR/issue text.
2. Preflight and hooks report `set`/`MISSING`, never values; never print the environment.
3. **[H] Environment allowlist for agent runs.** Today `envWith()` copies the whole `process.env`
   into OpenCode's run, so an implementer can read every key on the machine. Change: pass only
   the variables the task's tokens need (`GH_TOKEN` for `gh:*`; nothing for `net:none` tasks).
   Separate *using* a service (the runner holds the credential) from *reading* it (the agent's env).
4. Short-lived/fine-grained tokens per repository; a read-only token per private store.
5. Research runs record the *names* of credentials used, never values; evidence bundles are scanned
   for the configured secret variable values before upload (cheap string match, by the uploader).

## 11. Runner and workstation security (proportionate)

Assets on a research workstation: private originals, private stores' tokens, GitHub write,
provider credentials, Ghidra projects, personal files. Threats that are real here: (a) an LLM agent
running arbitrary shell (it already does: `bash: "*": allow`); (b) prompt injection from web content
in N4 research; (c) an old, untrusted game binary; (d) public-PR code.

| Rule | Mitigates |
| --- | --- |
| **No self-hosted GitHub Actions runners on research workstations.** CI runs on GitHub-hosted runners; fork PRs never receive secrets (already IC2 CI's behaviour). | (d) |
| Agents run only on branches of the owner's repos, from the owner's own claim. Never check out and run a fork PR's code locally. | (d) |
| **N4 (web) research runs on C0 machines** with no private artifacts and only that repo's token. | (b) |
| Wine prefixes for originals: remove the `Z:` → `/` drive mapping and home-folder links; the game sees only its own `C:`. DOSBox mounts only the game directory. | (c) |
| Agent env allowlist (§10.3); worktree confinement (L26 — OpenCode rejects paths outside the worktree, the runner fails such runs). | (a) |
| Originals reach a cloud machine only via C2, only for a game whose rights decision allows it, through a read-only token to that game's private store. For Isle Wars, never (U2). | licensing + (a) |
| Machines differ in credentials: cloud sessions carry repo-scoped tokens only; release-write on an evidence store is held only by machines that run that game's experiments. | blast radius |
