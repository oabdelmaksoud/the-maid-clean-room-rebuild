# Acceptance and recovery design

- Case ID / command IDs: [traceability]
- Origin / source IDs / original authorship: [exact provenance]
- Fixture paths and SHA256: [synthetic or permitted files]
- Preconditions and ordered steps: [reproducible procedure]
- Expected outcome: [values, state, files, absence of side effects]
- Oracle: [exact JSON or manual review; independently evaluate output]
- Required trials: [1–20 with reason]
- Failure injection: [invalid input or interrupted operation within scope]
- Recovery expectation: [state preserved and next safe action]
- Evidence per trial: [result, file hashes, reviewer, decision, notes]
- Exclusions: [case ID, explicit reason, approver; retain denominator]

A missing oracle is blocked or unknown. A command listing or test name is not output evidence. Durable crash recovery requires a separate real-process failure experiment.

## Repair queue and candidate history

- Gap ID, cause (specification / implementation / oracle / capture / access / dependency):
- Owner, minimal reproduction and affected canonical requirement IDs:
- Old frozen candidate/run and retained failed evidence:
- Acceptance condition and next action:
- New repaired candidate identity:
- Unchanged target-derived cases and affected regressions rerun:
- Independent reviewer, evidence and closure decision:
- Concrete blocker and incomplete checkpoint, if further repair is prevented:

## Variable-output paired task rubric

- Frozen task constraints and identical target/candidate synthetic input:
- Required output structure/content and quality criteria:
- Source/factual checks, navigation, reopened exports and file validity:
- Follow-up edits, attachments/context, cancellation/retry and relaunch:
- Actual target/candidate output identities and separate rubric decisions:

Do not use exact prose equality for variable generation or infer other capabilities from a text-only task. Preserve historical contracts when new target evidence changes expectations.
