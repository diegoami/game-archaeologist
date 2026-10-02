# ADR-005 Multi-machine claims: atomic ref, label, lease

- **Status**: Accepted 2026-10-02. The mechanism is provisional until H4's two-machine race test.
- **Source:** [docs/phase0/03-work-execution.md](../phase0/03-work-execution.md) §5, §7

## Context

IC2 ran two machines under one GitHub account. Its claim was "check no `machine:*` label, add yours,
re-read, the second backs off". That is two non-atomic writes and a re-read: when both machines
re-read after both have written, "second" is undefined. Assignees cannot tell machines apart.

## Decision

1. **Preflight** passes for the task, including the claim's own tokens.
2. **Claim** by creating `refs/heads/claim/T<nn>` at `origin/main`'s SHA through the GitHub API.
   201 means won; 422 means the task is held, so stop.
3. Add `machine:<id>` and `status:in-progress`, and post the claim comment
   `claim T<nn> machine=<id> at=<iso> lease=24h preflight=<summary>`.
4. A push to the task branch, or a comment on the issue, renews the lease.
5. **Release**: comment, remove the label, delete the claim ref. The pushed task branch stays as the
   resumable state.
6. **Merge**: the claiming machine merges and deletes the claim ref.
7. **Abandoned claims**:
   - A claim is stale when its lease expires with no push and no comment.
   - A claim ref with no claim comment after 10 minutes is stale at once.
   - Takeover needs the primary or the user: comment, delete the ref, recreate it (if another taker
     won, stop), swap the labels, resume the pushed branch.
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
