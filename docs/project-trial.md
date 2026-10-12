# Installed skill project trial

On October 11, 2026, a complete global Codex installation of Behavior Rebuild 0.1.0 was used to research, specify, implement, and evaluate a bounded subset of the installed `/usr/bin/sort` command. This summary is original documentation of the process and observed results. The repository does not include target captures, raw research, the implementation packet, local result files, or the trial implementation.

## Process

1. A fresh research context recorded permitted observations using original synthetic inputs and identified excluded behavior.
2. A separate reviewer inspected the original contract, fixture provenance, source-use decisions, and implementation packet. Handoff validation blocked missing approval before accepting the reviewed packet.
3. A fresh implementation agent, started without inherited conversation history, received only the approved packet and authored the candidate. Its exposure declaration excluded research, withheld cases, target source, and target execution.
4. A separate evaluator executed the target and candidate, bound the tested identities to an explicit run and candidate, and recorded exact output and exit-status comparisons.
5. Separate code and security reviewers evaluated the candidate and runner. Findings about supplemental failures, run overwrites, and tested-byte identity were corrected before the final evaluation.

All contexts shared a filesystem. Separation was logical and instruction-based, not operating-system isolation. Exposure declarations record claims about access; they cannot prove historical independence.

## Observed results

The final candidate passed **141/141 comparisons**: eight required cases, five withheld cases, and 128 deterministic seeded cases. The explicit acceptance gate exited 0. A separate code reviewer also executed **80/80 passing probes**. These are finite behavioral checks; source and branch coverage were not measured.

| Negative control | Observed gate result |
|---|---|
| Wrapper dropped reverse sorting | Exit 1; a required case failed. |
| Wrapper failed only wider cases while all eight original required cases passed | Exit 1; known supplemental failures blocked acceptance. |
| Failed actual output retained with forged pass declarations | Exit 1, `ORACLE_MISMATCH`. |
| Wrong explicit candidate | Exit 2, `CANDIDATE_MISMATCH`. |
| Tampered packet in a separate copy | Exit 2, `HASH_MISMATCH`. |

The trial runner also refused an existing run before execution and preserved its bytes. The runner was project-specific: these execution features do not imply that the kit’s record validator executes targets or candidates.

## Scope and limits

The contract covered UTF-8 records separated by LF, byte ordering, a bounded finite-decimal numeric grammar, stable ties, reverse ordering, and declared unsupported-token behavior under `LC_ALL=C`. It excluded locales, keys and fields, unique filtering, file input/output, other flags, binary or invalid UTF-8 input, unsupported numeric syntax, large-data performance, streaming latency, and interruption parity.

The result supports this bounded contract and evidence workflow. It makes no full sorting parity, legal-clearance, forensic-independence, production-readiness, or all-host compatibility claim. At the time of this trial, Linux and Windows CI runs had not been observed. Subsequently, all six Linux/macOS/Windows and Python 3.11/3.14 CI combinations passed; see the current [compatibility record](compatibility.md). Claude native behavior remains unverified because authentication blocked its initial trial. See [compatibility](compatibility.md) and the [initial verification snapshot](release-verification.md).
