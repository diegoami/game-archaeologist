# ADR-005 Multi-machine claims: atomic ref, label, lease

- **Status**: Accepted 2026-10-02. §2 and §7 are amended on 2026-10-09 (T17) to match the
  claim-commit form that `claim.mjs` implements; the owner's decision of 2026-10-08 is the basis
  (harness_imperial#120, comment 2026-10-08 19:52 UTC, PR #131). T14, the two-machine race test in
  `method/drills/01-race-test/`, validates the implementation against this ADR.
- **Source:** [docs/phase0/03-work-execution.md](../phase0/03-work-execution.md) §5, §7

## Context

IC2 ran two machines under one GitHub account. Its claim was "check no `machine:*` label, add yours,
re-read, the second backs off". That is two non-atomic writes and a re-read: when both machines
re-read after both have written, "second" is undefined. Assignees cannot tell machines apart.

## Decision

1. **Preflight** passes for the task, including the claim's own tokens.
2. **Claim** by creating `refs/heads/claim/T<nn>` at a **claim commit** through the GitHub API.
   201 means won; 422 (`Reference already exists`) means the task is held, so stop. The claim
   commit's tree is `origin/main`'s tree; its parent is `origin/main` on the first claim, or the
   previous state commit after that. Its message is
   `claim T<nn> machine=<id> at=<iso> issue=<n> nonce=<hex>`, which is what dates the claim —
   GitHub records no creation time for a ref, so the commit is the only timestamp the stale rules
   can use (the owner's decision, 2026-10-08, harness_imperial#120). The four state kinds the
   commit may carry are `claim`, `renew`, `release` and `merged`; their message formats are
   listed in `tools/harness/lib/claim.mjs`'s header (the implementation is authoritative for the
   exact text).
3. Add `machine:<id>` and `status:in-progress`, and post the claim comment
   `claim T<nn> machine=<id> at=<iso> lease=24h preflight=<summary>`. The comment is part of the
   claim record, not the race: it is allowed to land up to 5 minutes after the ref's `at=`
   timestamp. A claimer whose comment arrives 5 or more minutes late gives the claim back
   automatically. A failed comment calls `giveBack()`, which moves the ref to a `release` commit
   (compare-and-set, not a delete); a failed label edit warns (L62).
4. **Every change after the first create is a non-forced PATCH** to a child of the commit that was
   read. The change is therefore compare-and-set: a stale or older state is refused. A renewal
   that reads an older state and PATCHes a fresh child beats a takeover that read the same older
   state, because the renewal's PATCH lands first.
5. **Release**: comment, remove the labels, PATCH the ref to a `release` commit. The pushed task
   branch stays as the resumable state. The release commit's parent is the current state commit;
   its message names the task, machine, time, issue, reason and nonce. A `release` commit is not
   deleted; it stays on the ref so a subsequent `claim` can re-take the task from it (line 244 in
   `lib/claim.mjs`).
6. **Merge**: the claiming machine PATCHes the ref to a `merged` commit
   (`merged T<nn> machine=<id> at=<iso> issue=<n> nonce=<hex>`) and then deletes the ref in the
   same call (`DELETE repos/.../git/refs/heads/claim/T<nn>`). A non-204 delete is logged as a
   warning and blocks nothing. Nothing ever claims, renews, releases or takes over a `merged` ref.
7. **Abandoned claims**:
   - A claim is stale when its lease expires with no push and no comment; once stale, it stays
     stale (a renewal is a PATCH, not a re-issue). Activity after expiry revives nothing.
   - A claim ref whose `at=` is more than 10 minutes old and that has no claim comment is stale at
     once; same for any subsequent state commit.
   - A task branch that can't be read leaves the lease **unknown**. Only the user's `--force`
     takeover acts on an unknown lease.
   - **Takeover** needs the primary or the user: comment, PATCH the ref to a fresh child of the
     current state commit (compare-and-set; a delete-and-recreate would let a slow taker delete the
     winner's ref), swap the labels, resume the pushed branch. If the PATCH is refused (another
     taker won first), the takeover stops.
8. **The primary** is the repository variable `HARNESS_PRIMARY`, moved only by the user. No document
   names a machine.
9. **Concurrency** follows IC2's rules:
   - one task per machine, unless the task has no `exclusive:` token and the machine declares
     `concurrency>1`;
   - disjoint Owns, implicit ownership included;
   - no "never in flight with" pairing;
   - no seam redefinition;
   - `exclusive:<resource>` tokens (e.g. `exclusive:wine-display`) replace `single-instance`, and
     preflight fails if a process holding that resource is running.

## Consequences

- No scheduler or service.
- GitHub stays the only shared state, and all state needed to resume is pushed: work on an
  abandoned machine is, by design, non-essential.
- Cloud sessions may claim C0/C1 tasks once H4 exists.
- The race is two PATCHes at the same parent commit; the only one that wins is the one whose
  PATCH lands first. The ref's `at=` is set when the claim commit is created, and the comment may
  follow by up to 5 minutes; the race and the comment are not the same clock.
- A holder re-runs `status` before it acts on the claim (a merge, a push): a forced takeover by the
  user may have moved the ref in between.
- T14's `replay.mjs` parses the tool's stdout, one line per ref write:
  `claim-api op=<create|claim|renew|release|merged|takeover|delete> status=<http> ref=refs/heads/claim/T<nn> machine=<id> at=<iso>`.
  Exit codes 0 won/done, 3 held/lost/refused, 1 GitHub error, 2 usage.

## Amendment history

- 2026-10-09 (T17): §2 and §7 replaced to match the claim-commit form. The owner's decision of
  2026-10-08 (harness_imperial#120) is the basis. §3's failed-comment branch is `giveBack()`, a
  release PATCH, not a delete. §5 makes explicit that a `release` commit is kept on the ref so a
  later `claim` can re-take the task. §6 describes the actual merge sequence: a `merged` PATCH
  carrying task, machine, time, issue and nonce, then a direct `DELETE` of the ref in the same
  call. T14 is the race test that validates this ADR.
