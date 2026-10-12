# Independently authored command contract

- Command ID: [lowercase-hyphen ID]
- Purpose: [user outcome]
- Parameters and types: [name, type, required/default, limits]
- Preconditions: [state and permissions]
- Observable effects: [state transition and output]
- Errors: [invalid input, unavailable resource, failure output]
- Recovery: [what survives; what the caller can safely do next]
- Access: [UI/CLI/API entry points in your design]
- Events: [observable event names and ordering]
- Design rationale: [your reasoning; not an inferred proprietary architecture]
- Acceptance case IDs: [traceable cases]

Define retry/idempotency or crash guarantees only when an executable acceptance case proves each guarantee.
