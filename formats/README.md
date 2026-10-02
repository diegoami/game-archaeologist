# Record formats (v1, provisional until A6)

The shapes in which every archaeology repository records runs, artifacts, evidence, findings and
specification claims. Decided in [ADR-006](../docs/adr/006-artifact-identity.md),
[ADR-007](../docs/adr/007-evidence-provenance.md) and [ADR-008](../docs/adr/008-claim-lifecycle.md).
The field lists are provisional until the walking skeleton's retrospective (A6) freezes them as tag
`formats-v1`.

| Format | File | Lives in a game repo at |
| --- | --- | --- |
| Run record `run/1` | [run-1.schema.json](run-1.schema.json) | `runs/E<nnn>/<run-id>.json` |
| Artifact set `artifact-set/1` | [artifact-set-1.schema.json](artifact-set-1.schema.json) | entries in `artifacts/known.json` |
| Derived variant `variant/1` | [variant-1.schema.json](variant-1.schema.json) | `patches/<variant>.json` beside its recipe script |
| Evidence manifest `evidence-manifest/1` | [evidence-manifest-1.schema.json](evidence-manifest-1.schema.json) | `evidence/E<nnn>/<run-id>.manifest.json` |
| Finding | [templates/finding.md](templates/finding.md) | `findings/F<nnn>-<claim>.md` |
| Experiment | [templates/experiment-README.md](templates/experiment-README.md) | `experiments/E<nnn>-<slug>/README.md` |
| Spec area | [templates/spec-area.md](templates/spec-area.md) | `spec/<area>.md` |
| Representation | [templates/spec-representation.md](templates/spec-representation.md) | `spec/representation.md` |

The vocabularies these use are in [vocabulary/](../vocabulary/): [status](../vocabulary/status.md),
[basis](../vocabulary/basis.md), [interventions](../vocabulary/interventions.md),
[tiers](../vocabulary/tiers.md).

## Rules the schemas carry

- **Raw only.** `run/1` allows no field outside its list. An interpretation is not a field: it
  belongs in a finding. A decoded value is allowed only under `decoded`, with `via` naming the
  representation claim (`R<nnn>`) that licenses it.
- **Every observation is located.** A `value` comes with where it was read (`field` or `addr`); a
  `ref` points at a file in the evidence bundle.
- **Interventions are never omitted.** `interventions` is required, with at least one entry; a
  pure-observation run lists `{"level": "I0", "what": "none"}`.
- **Bundles live in the experiment's release.** Every evidence file, and every run output, is in
  `release:E<nnn>` (05 §4); only the run record and the manifest are in the repository. Each file's
  `class` is its artifact class from 05 §1: `save` (3); `screenshot`, `recording` (4); `memory-dump`,
  `trace`, `log`, `measurement` (6).
- **Hashes are full.** Every `sha256` is 64 hex characters; a truncated hash fails validation (IC2's
  seed build was known only by `354d8265…532f`).
- **Identity is named everywhere.** Run records and evidence manifests carry `artifact.set` and
  `artifact.variant` (`null` when the unmodified set ran).
- **No paths.** `machine` is an id (lower-case letters, digits, hyphens; it starts with a letter or
  digit). `runtime.fingerprint` holds versions that could change behaviour, as strings, and a value
  containing `/` or `\` fails validation.
- **No secrets, by a different mechanism.** A schema cannot recognise a credential. Records are clean
  by rule ([04 §10.1](../docs/phase0/04-environment.md)) and checked in review; evidence bundles are
  scanned by the uploader for the configured secret values before upload
  ([04 §10.5](../docs/phase0/04-environment.md)). Not this validator.

## Two rules no schema can express

`tests/formats/check_examples.py` checks them on the examples. Game repositories apply them with the
same code, copied, until a second consumer moves it here (ADR-009).

1. **Artifact-set id.** `id` is `<label>-<h8>`, where `<h8>` is the first 8 hex of the sha256 of the
   *canonical manifest*:
   - the manifest without `id` and `acquired`;
   - `files` sorted by `path`;
   - serialised as JSON with sorted keys and separators `(",", ":")`, UTF-8, no ASCII escaping.

   Two copies are the same artifact iff their ids match. `acquired` is excluded, so the same bytes
   obtained differently stay one artifact.
2. **Evidence asset names.** Each bundle file is uploaded as the release asset `<sha256[:16]>-<name>`.

## The validator

`python3 tests/formats/check_examples.py` (stdlib only, run in CI) implements exactly the JSON Schema
keywords these schemas use:
- `type`, `required`, `properties`, `additionalProperties`, `items`;
- `enum`, `const`, `pattern`, `minItems`, `minimum`, `minLength`, `anyOf`;
- the annotations `$schema`, `$id`, `title`, `description`.

A schema that uses any other keyword fails the check, so no rule is ever silently unenforced. Any
standard JSON Schema 2020-12 validator accepts these schemas too.

## Versioning

A schema id (`run/1`) never changes meaning. A breaking change is a new id (`run/2`) beside the old
one; records already written stay valid under their own id and are never rewritten.
