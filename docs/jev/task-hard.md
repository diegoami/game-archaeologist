The state is one task file from a software project, before any work on it starts: its title,
kind, why, evidence, Owns (the files it may change), scope, Done-when lines and hazards. The
projects are game rebuilds, game archaeology (evidence-backed specifications of old games) and
their tooling.

Answer yes if the task is hard: if any of these holds.
- It is a guard: its failure would leak or corrupt evidence, or let something through that must
  be stopped. Examples: keeping sealed rules or original game files out of a repository; a checker
  or validator that decides which records, examples or inputs are valid; a gate or test whose
  purpose is to catch a forbidden state; the format of evidence records.
- It adds a new mechanism across several files or modules, or a new external dependency (a
  library, a service, a runtime, an emulator).
- It is a rework of a task whose review found blocking bypasses or evasions.

Answer no if the task is easy: a documentation or configuration fix, a change whose contract names
the exact lines, a correction confined to one or two files, a single-mechanism change with clear
tests, a task file or index update, or data entry from a given source.

Confusing cases:
- Many files changed mechanically (a rename, a link fix in many documents) is easy: no new mechanism.
- A small change to a guard or validator is hard: a guard's small changes are where bypasses live.
- A research or investigation task that only writes documents is easy unless its records are the
  evidence format itself or it must keep something hidden.
- "Correction" in the kind does not make a task easy or hard by itself; judge what it changes.
