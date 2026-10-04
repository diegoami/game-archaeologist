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
  seed build was known only by `354d8265…`).
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

`tools/validate_records.py` implements them, and `tests/formats/check_examples.py` checks them on the
examples. Game repositories call the validator rather than copying it (ADR-009).

1. **Artifact-set id.** `id` is `<label>-<h8>`, where `<h8>` is the first 8 hex of the sha256 of the
   *canonical manifest*:
   - the manifest without `id` and `acquired`;
   - `files` sorted by `path`;
   - serialised as JSON with sorted keys and separators `(",", ":")`, UTF-8, no ASCII escaping.

   Two copies are the same artifact iff their ids match. `acquired` is excluded, so the same bytes
   obtained differently stay one artifact.

   `runtime_writes` is part of the canonical manifest, so a set registered before it ever ran keeps
   its list as registered (U21). When a run later shows more writes, register a **successor set**:
   - the same files, except that a shipped file the game writes moves from `files` to a
     `runtime_writes` glob;
   - `runtime_writes` complete as observed, so the successor gets a new id;
   - its `notes` in `known.json` name the predecessor and the run and finding that showed the writes,
     and the predecessor's notes name the successor.

   The predecessor stays in `known.json`, and the records that name it stay true: the files that ran
   were the same. New runs name the successor. isle-wars-archaeology's `iwp-2.0-3694a782`, the
   successor of `iwp-2.0-996e86c5`, is the first case.
2. **Evidence asset names.** Each bundle file is uploaded as the release asset `<sha256[:16]>-<name>`.

## The validator

`tools/validate_records.py` (stdlib only, Python ≥ 3.11) validates a record document against the
schema its top-level `schema` field names, and applies the two rules above. It implements exactly
the JSON Schema keywords these schemas use:
- `type`, `required`, `properties`, `additionalProperties`, `items`;
- `enum`, `const`, `pattern`, `minItems`, `minimum`, `minLength`, `anyOf`;
- the annotations `$schema`, `$id`, `title`, `description`.

A schema that uses any other keyword fails, so no rule is ever silently unenforced. Any standard
JSON Schema 2020-12 validator accepts these schemas too.

Run it on files; it prints `ok: <path>`, or `<path>: <error>` for each error, and exits 0 only when
every file is valid: `python3 tools/validate_records.py <file.json>...`. Each of these is an error
for that file, never a crash, and the files after it are still checked:
- a path it cannot read, or bytes that are not UTF-8;
- text that is not JSON, including `NaN` or `Infinity`, an object with a duplicate key (which value
  counts would depend on the reader), and nesting too deep to parse;
- a document with no `schema`, or an unknown one;
- a string holding a lone surrogate (`"\ud800"`), which UTF-8 cannot encode, so the document has
  no canonical form;
- any other failure while checking a document, reported as `internal error on malformed input`.

`validate_document(doc)` does the same for a parsed document, returning the errors; only a schema
with a keyword it does not implement makes it raise.

**A game repository calls it, never copies it.** List `tools/validate_records.py` in the
repository's `archaeology.json` `uses`, and fetch it with `formats/*.schema.json` at the pinned
commit, keeping `tools/validate_records.py` beside `formats/`; the module finds the schemas relative
to its own path. Never copy or edit it, so every repository stays on the rules of the commit it
pins. `tests/formats/check_examples.py` (run in CI) uses the same module to check the examples
against `expected-errors.json` and the claim statuses against 06 §4.

### Registering a set

`tools/register_artifact.py` (stdlib only, Python ≥ 3.11) registers an artifact set and checks a
copy. Fetch it beside `tools/validate_records.py` and `formats/*.schema.json` at the pinned commit,
keeping that layout; it imports `canonical_set_hash`, `validate_document` and the schema loading
from the validator, so the identity rule is never re-implemented.

- `python3 tools/register_artifact.py manifest <dir> --label … --title … --version … --how …
  [--when <date>] [--note …] [--runtime-write GLOB]… [--exclude GLOB]…` prints the
  `artifact-set/1` manifest, `id` included, that `artifacts/known.json` holds. `--when` defaults to
  today. A file matching a `runtime_writes` glob or an `--exclude` glob leaves `files`; `--exclude`
  is not recorded. `--writes` is an alias of `--runtime-write`.
- `python3 tools/register_artifact.py check (<dir> | --list <file>) <set-id> [--strict]
  [--known artifacts/known.json]` re-hashes a copy, or reads `<sha256>  <bytes>  <path>` listing
  lines, and compares them with the `known.json` entry. A listed file whose bytes or sha256 differ,
  or that is missing, is a failure; a file outside the manifest prints `unlisted: <path>` and fails
  only with `--strict`.
- `python3 tools/register_artifact.py validate [--known artifacts/known.json]` checks every entry
  against the schema and recomputes its id.

`--known` is relative to the working directory, never to the script. Errors are named lines and exit
1; usage errors exit 2.

Nothing is accepted unvalidated. `check` and `validate` accept a manifest only when it matches the
schema, its id is the canonical one, and no path is named twice; a `known.json` names each id once.
Every path, in a manifest or a listing, is relative and POSIX, with no `..`, `.` or empty segment, no
backslash and no drive letter. A listing line is a 64-hex sha256 (upper case is read as the same
digest), a byte count of digits only, and such a path. A symbolic link that leaves the checked
directory, a broken link and a special file are reported and never read, so `check` fails and
`manifest` refuses the directory.

A successor set is registered with the same `manifest` command: a shipped file the game writes moves
from `files` to a `runtime_writes` glob, `runtime_writes` is completed as observed, and the new id's
entry in `known.json` names the predecessor (U21, above).

### Verifying a bundle and checking citations

Two more tools move here once a second repository copies them (ADR-009): `tools/verify_evidence.py`
and `tools/check_citations.py`. Fetch them beside `tools/validate_records.py` and
`formats/*.schema.json` at the pinned commit, keeping that layout: the evidence tool imports the
validator, so the evidence-manifest rules (schema and the asset name) are never re-implemented. Both
run from the game repository's working directory, never from the cache folder that holds them, so
they serve the repository they are run in.

- `python3 tools/verify_evidence.py E<nnn>` reads `evidence/E<nnn>/*.manifest.json`, validates every
  manifest with `validate_records.validate_document`, downloads release `E<nnn>` in **one**
  `gh release download E<nnn> -D <dir>` call into a fresh directory under `.cache/evidence/`, and
  checks every listed asset there by sha256. An asset the bulk call left out is retried once, by
  name; whatever is still missing is reported by name. A stale cached file never stands in for this
  run's download. `--local DIR` checks an already-downloaded bundle instead of the release,
  `--evidence-dir DIR` overrides `evidence/` under the working directory, and `--repo OWNER/NAME`
  overrides the working directory's repository (`gh repo view`). Exit 0 prints
  `ok: <n> manifest(s) verified`; any problem is a named line and exit 1.
- `python3 tools/check_citations.py findings/F<nnn>-*.md` fails (exit 1) when a run id anywhere in
  the finding has no record under `runs/E<nnn>/`, or when a bullet in `## Answer` or `## Inferences`
  cites no run id on any of its lines. A bullet is any Markdown list item, however it is written:
  `-`, `*`, `+` or a numbered `1.`/`1)` marker, plain, tab-separated, alone on its line, or inside
  a blockquote (`> - claim`); an indented continuation line belongs to its bullet
  (toy-archaeology#12), and a thematic break (`- - -`) is not a bullet. **Every** occurrence of the
  two sections is checked, so repeating a heading cannot move a claim out of the guard, and fenced
  code is neither heading nor bullet. `--runs DIR` overrides `runs/` under the working directory.

Neither tool ever copies or edits the validator: they call it. Their tests run in
`tests/tools/` and in CI (`formats/README.md`).

## Versioning

A schema id (`run/1`) never changes meaning. A breaking change is a new id (`run/2`) beside the old
one; records already written stay valid under their own id and are never rewritten.
