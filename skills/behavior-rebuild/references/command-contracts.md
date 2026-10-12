# Independently authored contracts

First describe observable behavior: actor, goal, preconditions, inputs, state transitions, expected outcome, failure/recovery behavior, constraints, and evidence references. Then choose an implementation contract with its own rationale.

For each command, define availability, typed parameters and validation, state effects, outputs, errors, persistence, cancellation, retries, idempotency scope, and access requirements. Define event order where consumers depend on it. State explicitly when undo is unavailable or recovery cannot be guaranteed.

Choose an engine boundary that lets UI and automation exercise the same operation. This is a design option, not evidence about the target's architecture. Test the shared operation and the user-facing path; engine correctness alone cannot establish usable UI behavior.

Example design question for an original CSV export: what happens if the process stops after committing a file but before returning its receipt? Specify the visible retry outcome and evidence needed to recognize the committed file. An atomic rename is one possible implementation; it is not the behavior requirement itself.

Link each required behavior to a command and acceptance case. If the requested behavior remains unknown, resolve it through permitted discovery or record an explicit scope reduction. An implementation guess must remain labeled original design.
