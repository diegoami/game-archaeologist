# Basis

Source: [docs/phase0/06-research.md](../docs/phase0/06-research.md) §4, §8.

## Legend

A claim's **basis** says what kind of evidence stands behind it. Tags combine, separated by commas,
for example `observed, quantified: 30 of 30`.

| Tag | Meaning |
| --- | --- |
| `doc` | a manual, help file, readme or designer statement. It can only make a claim `documented`. |
| `observed` | behaviour of the original seen at I0 or I1 (play, screenshots, read-only memory) |
| `parsed` | a file format read by a parser (saves, data files, configuration) |
| `static:decompile` | decompiled code, naming the binary's sha256 and an address or symbol |
| `static:listing` | a disassembly listing, likewise |
| `static:bytes` | raw bytes of the binary or a data file at a stated offset |
| `intervened` | behaviour of a modified system (I2/I3). It needs a lower-level corroboration or a neutrality argument before it speaks for the original. |
| `quantified: N of N` | agreement counted over cases, e.g. `494 of 494` (IC2's standard for a behavioural confirmation) |

Two methods are **independent** when no step of one relies on the other's output. Behavioural plus
static is independent; two runs on one machine with one driver are not. `corroborated` needs
independence ([status.md](status.md)).

From IC2's tags, for reference:
- `[confirmed: decompile]` → `supported` + `static:decompile`;
- `[confirmed: saves]` → `supported` + `parsed, quantified`;
- `[derived]` → `hypothesis`;
- `[open]` → `unknown`.
