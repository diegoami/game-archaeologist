# Representation

What raw values mean: file formats, memory layout, screen elements. A decoded value in a run record
(`decoded[].via`) or a finding cites a row here. Rows follow the same lifecycle as any claim
(`vocabulary/status.md`) and change only by promotion. If a row is refuted,
`grep -rn R<nnn> findings runs` finds everything that relied on it, and the raw evidence is still
there to reinterpret.

| ID | Representation | Status | Scope | Basis | Findings |
| --- | --- | --- | --- | --- | --- |
| R001 | <e.g. bytes 0x1A0–0x1A3 of a save hold the player's province count, little-endian u32> | hypothesis | <set id> | — | — |
