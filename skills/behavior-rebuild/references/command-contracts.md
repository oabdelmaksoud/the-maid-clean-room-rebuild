# Independently authored contracts

First describe observable behavior: actor, goal, preconditions, inputs, state transitions, expected outcome, failure/recovery behavior, constraints, and evidence references. Then choose an implementation contract with its own rationale while preserving the locked objective in [fidelity](fidelity.md). Original architecture is not permission to change observable behavior.

For each command, define availability, typed parameters and validation, state effects, outputs, errors, persistence, cancellation, retries, idempotency scope, and access requirements. Define event order where consumers depend on it. State explicitly when undo is unavailable or recovery cannot be guaranteed.

Choose an engine boundary that lets UI and automation exercise the same operation. This is a design option, not evidence about the target's architecture. Test the shared operation and the user-facing path; engine correctness alone cannot establish usable UI behavior.

Example design question for an original CSV export: what happens if the process stops after committing a file but before returning its receipt? Specify the visible retry outcome and evidence needed to recognize the committed file. An atomic rename is one possible implementation; it is not the behavior requirement itself.

Link each required behavior to a command and acceptance case. If the requested behavior remains unknown, resolve it through permitted discovery or record it as unknown/blocked. A scope reduction requires the user's actual decision and evidence, not an implementer-authored non-goal. An implementation guess must remain labeled original design.


For faithful reimplementation, map every inventoried menu/action, dialog, setting, persistence operation and failure/recovery path to a command and case. Include availability and keyboard behavior. Record target file format and actual open/save compatibility requirements separately from an independently chosen internal serialization. New JSON export may be useful additional behavior; it does not replace requested target interoperability.

Freeze assertions from permitted target evidence before candidate execution. Paired journeys must exercise comparable transitions in the target and candidate, including the requested native runtime. Label proposed behavior that lacks target evidence as a design choice or unknown; do not silently promote it to the target contract.
