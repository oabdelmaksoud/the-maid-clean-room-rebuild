# Version 1 slice-readiness records

These exact JSON shapes supplement the existing project/run format; they are not JSON Schema. Unknown fields are rejected. IDs, strict JSON parsing, safe paths, hash references and read limits follow [record format](record-format.md). `FileRef` is `{path, sha256}` relative to the selected project. `evidence` arrays contain hash-checked FileRefs; required evidence cannot be empty. The checker does not authenticate their contents.

## readiness-contract.json

Root fields: `format_version:1`, `target_id:ID`, `target_version:text`, `sources`, `requirements`, `acceptance_cases`, `slices`, `capabilities`, `inventory_review`.

- Source: `{id:ID, evidence:FileRef[]}`. Keep source and requirement IDs distinct. This supplemental ledger does not replace source permission records.
- Requirement: `{id, kind, surface, state, precondition, action, controls, expected, source_ids, evidence, confidence, acceptance_ids, slice_ids, packet_id}`. `kind` is behavior/visual/capability; surface/state/precondition/action are nonblank text. Confidence is observed/documented/unknown. Source, acceptance and slice IDs are nonempty unique ID lists; source/slice references must exist. Packet ID designates exactly one author packet. Controls is a unique text array naming every applicable control; backend requirements may use an empty array. Visual requirements may only belong to visual slices.
- Expected: `{visible_strings:string[], control_states:object, navigation:string, persisted_effect:object, error_recovery:object}`. Control states must exactly cover the controls array, with nonblank control names and enabled/disabled/hidden/readonly values; an empty controls array permits an empty object. Visible strings may be empty; navigation permits an empty string; persisted/error objects may be empty. Use reviewed explicit not-applicable descriptions where meaningful, but do not add fields to this exact shape. The gate cannot judge whether empty values omit important behavior.
- Acceptance case: `{id, requirement_ids, expected, steps, evidence}`. Requirement IDs must exactly match requirements naming this acceptance ID. Expected maps exactly those IDs to canonical expected objects. Steps is a nonempty text array; evidence is required. These define assertions, not executed results.
- Slice: `{id, kind, required, requirement_ids, capability_ids, capture}`. Kind is behavior/visual/backend; required is boolean. Requirement IDs must exactly match requirements naming this slice. Capability IDs name contract capabilities. Capture is null for nonvisual slices; visual slices require Capture below.
- Capability: `{id:ID, description:text}`.
- Review: `{approved:boolean, reviewer:string, evidence:FileRef[]}`. The inventory review must be approved with a nonblank reviewer and evidence. Recorded approval is not authenticated independence.

Capture is exactly `{browser, browser_version, os, css_viewport, dpr, fonts, theme, locale, state}`. Browser/version/OS/theme/locale/state are nonblank text. CSS viewport is `{width:integer 1..100000, height:integer 1..100000}`; DPR is a JSON number greater than 0 and at most 16. Fonts is a nonempty text array. Capture equality is typed exact JSON agreement; measure actual rendering conditions separately. The record does not include measured element geometry or tolerance budgets.

## readiness.json

Root fields: `format_version:1`, `contract:FileRef`, `target_id`, `target_version`, `candidate_id:ID`, `requested_slice_ids:ID[]`, `status:ready|provisional|blocked`, `full_scope_readiness_claim:boolean`, `packets`, `slices`, `capabilities`, `task`, `resume`, `gaps`. Contract path must be `readiness-contract.json`; its hash binds exact bytes. Requested slice IDs are nonempty and must exist.

- Packet: `{id, target_id, approved, reviewer, requirement_ids, expected, evidence, artifact}`. Expected maps exactly each declared requirement ID to its canonical expected object. Artifact is a FileRef to JSON with exactly `{target_id, requirement_ids, expected}` matching the inline declaration. Every canonical requirement must appear only in its designated packet. Packets need approved true, nonblank reviewer and evidence; reviewer must differ from task owner. Target IDs must agree. Other approved prose/assets remain governed by the existing packet boundary.
- Slice: `{id, status, requirements, capture, blocker, review}`. Status is ready/provisional/blocked. Requirement records are `{id, status:ready|blocked, reason:string, evidence:FileRef[]}` and cover exactly this slice's requirements. Blocked requirements need a reason. Ready requires known, ready requirements, available required capabilities, approved Review with reviewer distinct from task owner, and null blocker. A visual ready slice must have Capture exactly equal to the contract. Nonvisual ready capture is null. Nonready slices have a blocker; capture may be null or a complete Capture.
- Blocker: `{owner:text, reason:text, next_action:text, evidence:FileRef[]}`.
- Capability: `{id, availability:available|unavailable|blocked, disposition:string, evidence:FileRef[]}`. All contract capability IDs must have one record. Unavailable/blocked needs a disposition. Available needs evidence; this is not an execution test.
- Task and resume: `{target_id:ID, name:text, owner:text, evidence:FileRef[]}`. Both must match the contract target; lowercase name must contain the target ID. This compares declarations, not live orchestration state.

Run slices and capabilities must cover the entire declared contract, including nonrequested scope. Requested slices must be ready. Overall status ready rejects nonready required slices; provisional permits ready requested slices alongside blocked required scope. A full-scope readiness claim requires overall ready, all required scope ready and no open gaps; it is not product acceptance.

## Recovery gap and closure

Gap fields: `{id, cause, status, fixable, owner, reproduction, requirement_ids, acceptance, next_action, candidate_id, closure}`. Cause is specification/implementation/oracle/capture/access/dependency; status is open/closed; fixable is boolean. Owner/reproduction/acceptance/next_action are nonblank text. Requirements are a nonempty list of canonical IDs. Candidate ID identifies the failed candidate. Open closure must be null.

Closed closure is `{candidate_id, independent_reviewer, rerun:FileRef, evidence:FileRef[]}`. The repaired candidate must equal the current record candidate and differ from the failed candidate; reviewer must differ from owner. Rerun JSON is exactly `{candidate_id, requirement_ids, expected, actual}`. IDs must retain gap order; expected and actual must equal a map of those IDs to frozen canonical expected values. The checker validates supplied rerun bytes; independent execution and preserved historical candidate files remain external responsibilities.

## Results and limits

CLI: `python3 scripts/readiness.py PROJECT_DIR --json`. Output includes format_version, stage, ok, exit_code, contract_sha256, errors, warnings and summary. Summary names target/candidate, overall status, ready/nonready/required-nonready slices, open gaps and counts. Its declared_scope_ready field means only that declared required scope is ready with no open gaps or record errors.

Exit 0 is a selected recorded readiness pass, 1 a well-formed blocked gate, 2 invalid shape/path/hash/input. No target observation, network, capability execution, publication or account authorization occurs. Semantic inventory normalization, measured visual specifications and variable-output quality rubrics require separate review and real trials.
