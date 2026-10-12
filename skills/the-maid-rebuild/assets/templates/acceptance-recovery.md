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
