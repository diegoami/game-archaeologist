# E<nnn> <slug>

Copied from the research task's contract when the experiment is created. After the first run this
file is append-only. A changed design is a new experiment, or `v2/`.

- **Task**: T<nn> (#<issue>)
- **Question**: <one falsifiable question>
- **Hypotheses**:
  - H0: <null hypothesis> — distinguished by <the observation that would show it>
  - H1: <…> — distinguished by <…>
- **Artifact**: set `<set id>`, variant `<variant id>` | none
- **Runtime**: <driver@commit>, <platform>; maximum intervention level <I0–I3>, because <why>
- **Design**:
  - start state: `<id>` (sha256 `<…>`), restored by <everything reinstated>
  - control: <…>
  - arms: <arm>: <treatment> …
  - n per arm: <n>; stopping rule: <…>
- **Measurements**: <each raw quantity, how it is read, and its source: screen | save | memory | file | ui-text | log | process | static>
- **Outputs**:
  - run records: `runs/E<nnn>/`;
  - evidence manifests: `evidence/E<nnn>/`, bundles in release `E<nnn>`;
  - `findings/F<nnn>-*.md`, status `proposed`.

## Scripts

<The script(s) in this directory, and the arguments each arm uses.>
