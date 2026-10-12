# Release verification records

## Version 0.3.0 — October 11, 2026

The local macOS suite passed **75 unit/CLI tests**, including 23 fidelity tests. The new tests cover objective changes, missing feature/case mappings, original-design visual baselines, unauthorized deviations, runtime substitution, typed actual outcomes, candidate identity, evidence integrity, unsafe paths and escaped terminal output. On systems without symlink privileges, the nonregular-evidence test exercises a directory-as-file rejection instead; that fallback does not establish symlink coverage.

The [chess fidelity trial](../examples/chess-fidelity/README.md) was run against the unchanged Quiet Knight HTML identity `6f012bd249b247b2cbe173d1b0b52771bf80ddffcb02869f74ff6d63b62df4e3`. The old five-case bounded evidence gate still passed, and a fresh rules run passed 476 tests. The new fidelity gate returned **BLOCKED**: 15 recorded feature groups, 4 matches, 7 mismatches, 4 unknowns and no deviations. It also rejected two original-design visual baselines and retained an incomplete-discovery blocker. All seven forged pass labels were rejected by comparing unchanged actual outcomes with frozen expectations.

Independent code review reran the 75-test suite, nine additional probes and the chess trial; a separate verifier also reran the suite and trial. This tests gap detection using partial fresh native menu/setup observations plus explicitly retrospective evidence. It does not constitute a fresh exhaustive target probe, repair the chess candidate, authenticate evidence authorship or measure a whole-product fidelity percentage.

The CI matrix now includes this expected-rejection chess trial on each of the six OS/Python combinations. A workflow definition or local pass does not establish remote success; inspect the run for the exact published revision. No tagged release is asserted.

## Version 0.2.0 — October 11, 2026

Local macOS verification passed all 52 unit/CLI tests. A separate code reviewer passed the same suite and 1,000 randomized pixel-comparison probes. New cases cover ordered journeys, exact state types, image dimensions and budgets, malformed images, forged passes, altered hashes, symlinks, optional pass claims, and bounded aggregate comparison work.

The [Pocket Tasks browser experiment](../examples/pocket-tasks/README.md) used actual Chromium 153.0.8010.12, Playwright 1.62.1, Pillow 12.1.1, and Python 3.14.6. The narrow add-task case passed for all five variants. The expanded suite rejected all three combined faults, and each isolated fault failed exactly its associated case. The repaired variant passed all five cases. All ten baseline/enhanced acceptance invocations returned their expected exit codes. The runner preserves source and validator snapshots, hashes, screenshots, traces, frozen manifests, and gate outputs outside the source distribution.

This is a controlled coverage experiment on an original app. Expected failures are deliberately seeded, the reference is an original design, and the author knew the faults. It does not establish independent clean-room authorship or general defect-discovery rates. Existing JSON assertions could also have expressed richer state checks; the extension supplies reusable visual and journey contracts with validation.

The workflow includes the existing six OS/Python combinations and a separate Ubuntu Chromium trial with retained evidence. A workflow definition alone is not a completed CI result; inspect the run for the exact revision under review. No tagged release is asserted.

## Historical version 0.1.0

Initial prepublication verification snapshot, October 11, 2026. At that checkpoint, the local candidate had no remote or initial commit. Those historical facts do not describe the repository’s current Git or publication state. Version 0.1.0 identifies the package; this document does not attest to a tagged GitHub release.

## Executed checks

| Check | Observed result |
|---|---|
| `python -m unittest discover -s tests -q` on macOS arm64, Python 3.11.15 | 36 tests passed |
| Same suite, Python 3.12.12 | 36 tests passed |
| Same suite, Python 3.13.13 | 36 tests passed |
| Same suite, Python 3.14.6 | 36 tests passed |
| Documented discovery, handoff and report commands | Passed; static example has no executed acceptance run |
| Fresh original demo, acceptance and report | Passed, two required trials, candidate `demo-v1` |
| Relocated standalone skill | Acceptance worked using only the copied skill directory |
| Skill metadata validation and relative Markdown links | Passed |
| Independent code and security reviews | Findings corrected; independent re-review approved |

Tests cover malformed and duplicate JSON, bounded inputs, unsafe paths and symlinks, stale hashes and revisions, missing trials/oracles, truthful scope denominators, exclusions, blockers, review declarations, read-only input handling, and deterministic archive construction. Regression cases cover unsupported optional/excluded pass claims, decimal rounding and underflow, Python 3.11 symlink-loop handling, and terminal control escaping.

The example executes a small original CSV transformation and separately inspects its output. Its automated oracle is explicit; it does not represent independent human approval or production parity.

## Host trials

Codex CLI 0.160.1 loaded the project-local skill and exercised discovery, handoff, and verify/recover instructions. It preserved an unsupported autosave claim as unknown, disregarded injected instructions in source text, disclosed exposure, and observed acceptance exit 0 for the matching revision and exit 2 for a mismatched revision. This bounded trial used the same skill instructions as the final candidate; the subsequent validator hardening was verified by the test suite and independent reproductions.

Claude Code 2.1.215 was attempted with a project-local copy, but authentication failed before inference. No Claude native compatibility claim is made. At the initial checkpoint, Linux and Windows CI jobs were configured but had not run. The initial host smoke trials did not change global installation or agent configuration. A subsequent complete global Codex installation was exercised through discovery, reviewed handoff, fresh implementation, and explicit acceptance in the [bounded project trial](project-trial.md). That trial passed 141 final comparisons and 80 independent review probes; its negative controls blocked acceptance as expected.

## Distribution boundary

`release-files.txt` is the explicit distribution inventory. The release builder rejects unlisted files, unsafe entries, and symlinks; it excludes Git metadata and Python caches. Full and standalone archives have deterministic ordering, timestamps, and modes. Both distributions include the original MIT license and source-exposure notice. `SHA256SUMS` identifies the produced archive bytes.

Validate and package trusted local copies with no concurrent writers. These tools are not an operating-system sandbox. Recorded permission and reviewer declarations cannot prove their own truth, legal clearance, or implementation independence.

The owner subsequently authorized publication to a private GitHub repository. The initial local snapshot does not establish remote CI completion or a tagged release; subsequent observed outcomes follow below.


## Private repository and remote verification — October 11, 2026

The initial revision `821c8568ce45d53dd0f3aa93138df68dfef3fa9b` was pushed to the private repository. Repository visibility was verified through the GitHub API. A fresh clone contained 45 byte-identical distributed files; the README installation command and 36-test suite passed from that clone.

[GitHub Actions run 38187814468](https://github.com/oabdelmaksoud/the-maid-clean-room-rebuild/actions/runs/38187814468) completed successfully for that revision. All six jobs passed: Linux, macOS, and Windows, each with Python 3.11 and 3.14. Each job passed the 36-test suite, generated the original demonstration, validated its explicit acceptance run and candidate, and built the release archives.

These results apply to the initial revision identified above. This documentation follow-up was authored after that run; the earlier CI result does not establish validation of a later commit. No tagged GitHub release is asserted.
