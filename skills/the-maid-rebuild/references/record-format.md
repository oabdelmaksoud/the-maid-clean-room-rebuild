# Version 1 record format

This is a bespoke JSON record contract, not JSON Schema. All listed fields are required; extra fields are rejected. Arrays can be empty unless stated otherwise. `text` means nonblank string; `string` permits empty text. IDs match `[a-z][a-z0-9-]{0,63}`. IDs are unique within each collection, and cross-reference lists cannot contain duplicates. Booleans are not integers. SHA256 is 64 lowercase hexadecimal characters.

## Common file and parser rules

`FileRef = {path, sha256}`. Paths are relative POSIX paths within the caller-selected project root. Absolute paths, backslashes, colons, NUL, empty components, `.` and `..` are rejected. Symlink components beneath the root and nonregular files are rejected. The selected root itself is resolved. All referenced files are read and hash-checked, including during discovery; a stale handoff hash is invalid even before handoff approval.

Project and run JSON are limited to 1 MiB each. Every JSON collection is limited to 1,000 entries and nesting to 40. Duplicate JSON keys, nonfinite numbers, invalid UTF-8 and unknown record versions are rejected. There are at most 256 unique referenced files, 16 MiB per file, and a 64 MiB total read budget (including project/run reads). Packet scans are bounded to 1,000 entries. Visual comparisons have a cumulative 16,000,000-pixel budget per validation invocation, including comparisons that reuse cached images. Files are never executed, fetched remotely, or mutated. Tools run without network or subprocess calls. Avoid concurrently changing the evidence directory during validation; recorded results describe the files read in that invocation.

## project.json

Exact root fields:

| Field | Type / rules |
| --- | --- |
| format_version | integer `1` |
| project_id | ID |
| title, scope, exclusion_note | text |
| target | `{name:text, version:text, mode:text}` |
| sources | Source array |
| commands | Command array |
| cases | Case array |
| exclusions | Exclusion array |
| handoff | Handoff |
| gaps | Gap array |

**Source** fields: `id:ID`, `kind:D|O|R|U`, `locator:text`, `captured_on:YYYY-MM-DD`, `description:text`, `permission`, `evidence:FileRef[]`. D means documented, O observed, R reported, U unknown. Observation sources require evidence. Remote locators are metadata and are never fetched.

`permission = {observe:allowed|denied|unknown, handoff:allowed|denied|unknown, publish:allowed|denied|unknown, basis:text, reviewer:string}`. Any allowed permission requires a nonblank reviewer. Unknown permissions and unknown source kinds remain visible warnings. Publication permission is separate from local handoff approval.

**Command** fields: `id:ID`, `description:text`, `parameters:text`, `preconditions:text[]`, `effects:text[]`, `errors:text[]`, `recovery:text`, `access:text`, `events:text[]`, `design_rationale:text`. Effects and errors must be nonempty. Commands are independently designed; behavior source references belong to cases.

**Case** fields: `id:ID`, `title:text`, `origin:documented|observed|reported|unknown|original_synthetic_design`, `source_ids:ID[]`, `authorship:string`, `command_ids:ID[]`, `preconditions:text[]`, `steps:text[]`, `expected:text`, `fixtures:FileRef[]`, `oracle`, `required:boolean`, `required_trials:integer 1..20`.

Steps and command references must be nonempty. Documented/observed/reported cases require source references, including a D/O/R source respectively, and cannot cite U sources as substantiation. Original synthetic designs require nonblank authorship; their source list may be empty. Unknown cases are recorded during discovery but cannot enter an active handoff.

`oracle = {kind:exact_json|manual_review|journey_trace|visual_pixels, description:text, expected:any JSON}`. Exact JSON requires a non-null expected value; comparisons use typed structural values and preserve type distinctions (including boolean versus integer and integer versus decimal representation). Decimal and exponent literals are parsed with exact decimal precision, avoiding binary floating-point rounding. Numerically equal decimal spellings such as `1.0` and `1.00` compare equal; integer `1` remains distinct. Exponents are never expanded into fixed-point strings for comparison. Object key order is ignored; array order matters. Manual review requires null oracle expected; the case's `expected` and oracle description state the human criteria.

`journey_trace` requires `expected = {steps:[{id:ID, action:text, state:object}]}`. Steps must be nonempty and IDs unique; every state must be a nonempty JSON object. The result uses that same exact shape. Comparison is ordered and typed with the same exact JSON rules above: a missing/reordered step, changed action, or different state fails. Define the expected trace before execution; collect actual state from the candidate's DOM, storage, or other observable outputs rather than copying the expectation into the result.

`visual_pixels` requires `expected = {baseline:FileRef, width:integer, height:integer, max_channel_delta:integer, max_changed_pixels:integer}`. Width/height are 1..4096 with at most 1,000,000 pixels total. `max_channel_delta` is 0..254; `max_changed_pixels` is 0..(width × height − 1). Booleans, decimals, negative and all-passing budgets are invalid. The baseline and result must be binary PPM P6: an ASCII header with width, height, and maximum value 255, no comments, followed by exactly width × height × 3 RGB bytes. Headers are bounded to 128 bytes. A pixel counts as changed if any channel differs by more than `max_channel_delta`; acceptance permits at most `max_changed_pixels` such pixels. Zero budgets mean exact RGB equality. Baseline dimensions must match the contract; a valid result with different dimensions fails comparison.

The baseline is hash-checked even during discovery. Keep it as evaluator evidence outside the implementation packet; PPM/PNG files are not permitted packet extensions. Baselines use the normal FileRef safety and read budgets. Keep original browser PNG captures as evaluation evidence; convert to RGB PPM before validation. See [visual and journey validation](visual-and-journey.md) for capture conditions and limits. Existing version 1 records remain valid; older validators cannot interpret the newly added oracle kinds.

**Exclusion** fields: `case_id:ID`, `reason:text`, `approved_by:text`. Each case may be excluded once. Excluded cases remain in the total denominator. Optional does not mean an approved skip. Excluding every required case cannot yield acceptance.

**Handoff** fields: `directory:relative path`, `files:HandoffFile[]`, `reviewer:string`, `approved:boolean`, `attestation:string`, `exposure_notes:text[]`.

`HandoffFile = {path, sha256, role:specification|fixture, provenance:text, source_ids:ID[]}`. Files must be under the declared directory with `.md`, `.txt`, `.json` or `.csv` extensions. The directory's exact file set, including hidden files, must match the manifest. Symlinks and nonregular entries are rejected. Directory may be absent only for an empty discovery handoff. No source file is automatically copied or included; the report indicates whether source evidence paths were explicitly included.

Handoff approval requires `approved:true`, a nonblank reviewer and attestation, nonempty exposure notes, and at least one specification. All active case fixtures must be handed off. Every referenced handoff source needs allowed handoff permission. Active source-backed cases require both allowed observation and handoff permission. Hashes and approval records cannot detect concealed copied content or prove the truth of provenance declarations.

**Gap** fields: `id:ID`, `case_ids:ID[]`, `severity:blocker|high|medium|low`, `impact:integer 1..5`, `recovery_action:text`, `status:open|closed`. Reports sort by severity, descending impact, then ID. Any open blocker prevents acceptance, even when associated cases are excluded.

## Explicit run record

Exact fields: `format_version:1`, `run_id:ID`, `manifest_sha256:SHA256`, `candidate_id:text`, `created_at:ISO8601 timestamp with timezone`, `runner:text`, `environment:text`, `evaluations:Evaluation[]`.

The digest binds the exact raw `project.json` bytes, including formatting. Acceptance requires both `--run relative/path.json` and `--candidate ID`. Candidate must match exactly. No historical or newest run is automatically selected. A changed manifest requires a newly bound run.

**Evaluation** fields: `case_id:ID`, `trial:integer 1..20`, `status:pass|failed|blocked|unknown|skip`, `oracle_status:available|missing`, `result:FileRef|null`, `evidence:FileRef[]`, `review`, `notes:string`.

`review = {reviewer:string, decision:accepted|rejected|pending, notes:string}`. Case/trial pairs are unique and trials cannot exceed the case's required count. Failed, blocked, and unknown evaluations require nonblank notes. Missing oracle permits only blocked or unknown status. Skip requires explicit case exclusion.

Every pass needs an available oracle and recorded accepted review with nonblank reviewer and notes. An exact JSON or journey trace pass needs a strict JSON result file equal to expected; a visual pass needs a valid PPM result within its frozen pixel budgets; manual review needs null result and at least one evidence file. All supplied files are hash-checked regardless of status. Every claimed pass receives the same evidence checks, including optional and excluded cases: missing accepted review, missing results, mismatched JSON, or missing manual evidence blocks the gate with exit 1. Honest optional failed, blocked, or unknown statuses remain visible without blocking acceptance of required scope. Invalid file integrity or malformed records always invalidate the input with exit 2.

Acceptance requires at least one active required case and a passing record for every required trial. Missing, failed, blocked or unknown required trials prevent acceptance. A pass denotes a **recorded-evidence gate**, never product certification, legal assurance, or independently verified human judgment.

## Commands, output, and exit codes

```sh
python3 scripts/validate.py PROJECT --stage discover --json
python3 scripts/validate.py PROJECT --stage handoff --json
python3 scripts/validate.py PROJECT --stage acceptance --run runs/demo.json --candidate demo-v1 --json
python3 scripts/validate.py PROJECT --digest
python3 scripts/report.py PROJECT --run runs/demo.json --candidate demo-v1 --json
```

`--digest` checks bounded file access and strict JSON parsing, then prints raw SHA256. It does not approve the manifest shape or any gate. Without a stage, validate defaults to discovery. Report without a run evaluates discovery and explicitly marks acceptance unevaluated; with a run it evaluates acceptance.

Normal JSON gate output has exact top-level fields `format_version`, `stage`, `ok`, `exit_code`, `manifest_sha256`, `errors`, `warnings`, `summary`. Each issue has `{code,path,message}`. Summary provides total/active/required/optional denominators, excluded IDs, required trial count, recorded status counts, untested trials, per-evaluation required/excluded flags, ranked gaps, selected run/candidate when supplied, and evidence limitations. Counts describe recorded statuses and must be read alongside errors and warnings.

Exit **0** means the selected gate passed, **1** means well-formed records with blocked evidence/readiness, and **2** means invalid shape, paths, hashes or usage. Expected input errors produce no traceback. Argparse usage errors print ordinary CLI help to stderr. All output is stdout/stderr; the validator never writes to the project.

Stable issue categories include `SHAPE`, `ID`, `TEXT`, `ENUM`, `INTEGER`, `BOOLEAN`, `COLLECTION`, `DUPLICATE_ID`, `DUPLICATE_REFERENCE`, `UNKNOWN_REFERENCE`, `DUPLICATE_KEY`, `INVALID_JSON`, `NONFINITE_JSON`, `JSON_DEPTH`, `UNSAFE_PATH`, `SYMLINK`, `NOT_REGULAR`, `FILE_SIZE`, `TOTAL_SIZE`, `FILE_LIMIT`, `HASH_MISMATCH`, `PACKET_FILE_SET`, `MANIFEST_MISMATCH`, `CANDIDATE_MISMATCH`, `EMPTY_SCOPE`, `HANDOFF_APPROVAL`, `CASE_PERMISSION`, `PASS_REVIEW`, `ORACLE_MISMATCH`, `REQUIRED_TRIAL`, `NO_REQUIRED_CASES`, and `OPEN_BLOCKER`. Messages provide context; integrations should branch on code and exit status.

## Slice-readiness records

The additional two-file readiness contract has its own [exact format reference](readiness-record-format.md). It leaves the existing version 1 project/run shapes unchanged and is checked by `readiness.py`, separately from acceptance and fidelity.
