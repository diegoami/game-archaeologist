# Claim status, finding outcomes, links and corrections

Source: [docs/phase0/06-research.md](../docs/phase0/06-research.md) §4; [ADR-008](../docs/adr/008-claim-lifecycle.md).
`tests/formats/check_examples.py` checks that the statuses below equal the package's.

## Legend

- A **claim** is a row in a specification table. It has exactly one **status**, a **basis**
  ([basis.md](basis.md)), and a **scope**: the artifact set and variant, the settings, and the state
  preconditions under which it holds.
- A **finding** is a reviewed interpretation of evidence. It has an **outcome**, which is not a claim
  status.
- **Promotion** (by the main session only) turns finding outcomes into claim statuses.

## Claim status

| Status | Meaning | Gets there by |
| --- | --- | --- |
| `unknown` | nothing established. It is the default, and it is written explicitly. | the knowledge map |
| `documented` | asserted by a manual, help file or designer, and not yet tested | documentation research (basis `doc`) |
| `hypothesis` | proposed, with a test design | a question |
| `supported` | a reviewed finding supports it, by one method | research review, then promotion |
| `corroborated` | supported by at least two independent methods: behavioural + static, two independent runtimes or machines, or I0 + I3 | a second reviewed finding |
| `refuted` | a reviewed finding contradicts it | research review |
| `contested` | reviewed findings disagree, unresolved | promotion, when a new finding conflicts |

The two methods of `corroborated` come from two reviewed findings. An I0 confirmation inside one
finding is what lets an `intervened` basis speak for the original ([basis.md](basis.md)); it does not
corroborate that finding, whose runs share one machine and one driver (F001 in toy-archaeology, I0
and I3 in one finding, was promoted `supported`).

A finding of the original game is never `designed`. That word belongs to a rebuild, not to
archaeology.

## Finding outcomes

The outcome is on line 3 of a research review (ADR-008, [research protocol](../method/research-protocol.md)
§3); line 2 is the record verdict. A finding that proposes more than one claim gets one outcome per claim. One
of:

| Outcome | Meaning | Effect on the claim at promotion |
| --- | --- | --- |
| `supported` | the record supports the claim as stated | `supported`, or `corroborated` if independent support already exists |
| `supported, narrowed: <narrowing>` | it supports a narrower claim | the claim's text or scope is narrowed, then as above |
| `inconclusive` | a sound record that does not decide the question | status unchanged (`unknown` or `hypothesis`), the finding linked: "we looked, and could not tell" stays visible |
| `refuted` | the record contradicts the claim | `refuted`, or `contested` if other findings support it |

Before review, a finding's status is `proposed`.

## Links and corrections

- `superseded-by: <claim id>` is a link, not a status. The old row keeps its status and points
  forward.
- Corrections use one style only, inside the corrected finding:
  `> **Correction (YYYY-MM-DD, F0nn):** <what was wrong, and what is right>`. Mistakes are stated,
  not quietly fixed.
- Claim ids:
  - `C-<AREA>-<nn>` for behaviour (e.g. `C-SET-01`). `<AREA>` is an upper-case abbreviation of a
    knowledge-map area.
  - `R<nnn>` for representation claims (e.g. `R014`).
  - Findings are `F<nnn>`, experiments `E<nnn>`.
