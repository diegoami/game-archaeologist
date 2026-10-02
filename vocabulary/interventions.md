# Intervention levels

Source: [docs/phase0/06-research.md](../docs/phase0/06-research.md) §3; [ADR-007](../docs/adr/007-evidence-provenance.md).

## Legend

| Level | Name | Examples | A result means |
| --- | --- | --- | --- |
| `I0` | pure observation | normal play through the UI; parsing a save the game wrote; reading the manual | behaviour of the untouched original |
| `I1` | passive instrumentation | screenshots; read-only memory (`/proc/<pid>/mem`); debugger watchpoints that do not alter flow; static analysis | untouched behaviour, but a timing-sensitive game may differ under a debugger: say so |
| `I2` | harness-enabling modification, claimed neutral | an autosave hook, async sound, no-delay battles, a save-state | original behaviour, **if** the neutrality claim holds |
| `I3` | behaviour-altering intervention | a forced RNG seed, a memory write, a crafted or modified save, a patch changing logic, altered timing | behaviour of the modified system; evidence about the original only by argument |

## Rules

- **Every run lists its interventions** in `run/1`'s `interventions`, passive ones included. A
  pure-observation run lists `{"level": "I0", "what": "none"}`. The list is never empty, because an
  empty list could mean "none" or "not recorded".
- **A finding states its maximum level**: the highest level in any run it cites.
- **A spec claim built on I2/I3 evidence** carries either a corroboration at a lower level or a cited
  neutrality argument. Where practical, that argument includes a control showing the measured
  property is unchanged without the modification.
- **A derived variant** (`variant/1`) lists its own interventions, and they are I2 or I3 only. A run
  on that variant repeats them.
