# Native command modes

Use `$the-maid-discover`, `$the-maid-rea`, `$the-maid-spec`, `$the-maid-ready`, `$the-maid-build`, `$the-maid-validate`, `$the-maid-repair`, `$the-maid-status`, or `$the-maid-all` in Codex. These are native skills, not installed shell commands. `$the-maid-rebuild` remains the shared compatibility entrypoint for natural-language mode selection. The sibling core is a required dependency; every release ships it with the wrappers. `commands.json` is the packaging catalog of these entrypoints.

Read the selected section and its named core references, not every mode's references. Explicit mode selection takes precedence over the core's default recovery behavior: `validate` reports failures without repair, and `repair` or `all` authorizes the repair stage within the user's existing scope. No mode grants account, source, setup, installation, publication, push, or message authorization. Preserve unknowns and the full requested inventory; report partial and blocked outcomes explicitly.

## discover

Read `fidelity.md` and `evidence-levels.md`. Lock the original request and target/version/platform/runtime; establish the permitted source set, permission basis, exposure disclosures, and complete requested surface inventory. Record evidence identities, confidence, exclusions, unknowns, and blockers. Use the discovery templates. REA is optional: enter its integration only when requested or connected and permitted. Stop after discovery; do not silently specify, build, install, or publish.

## rea

Read `rea-integration.md` and `evidence-levels.md`. Confirm the exact target and permitted capture scope before capture. Use REA only for scoped rendered UI evidence permitted by the core profile; do not inspect source, bundles, private endpoints, network internals, or decompile. Keep captures evaluator-only and validate the reviewed handoff with the core REA validator. If unavailable or not permitted, record the limitation and permitted manual observation alternative; do not install or configure it automatically. Stop after the requested integration/evidence work.

## spec

Read `fidelity.md`, `command-contracts.md`, `handoff-boundaries.md`, and applicable visual guidance in `visual-and-journey.md`. Reconcile atomic canonical requirements with approved evidence, exact states, and acceptance IDs. Preserve the full inventory and unknown surfaces. Freeze acceptance expectations, oracles, conditions, tolerances, packet files, and hashes before implementation. Obtain separate intent/completeness and packet/source-use reviews; record actual decisions. Keep restricted evidence outside the approved author packet. Stop at the specification/handoff outcome; approval alone does not run readiness or build.

## ready

Read `implementation-readiness.md`, `readiness-record-format.md`, and `tool-usage.md`. Prepare or assess the selected slice's canonical requirements, approved packet, actual capabilities/dependencies, target-specific task, and review evidence. Run the local readiness gate. Report requested slice IDs, nonready required slices, and concrete blockers. A passing recorded slice gate is neither full-scope readiness nor runtime proof. Stop after readiness; do not build silently.

## build

Read `handoff-boundaries.md`, `implementation-readiness.md`, and `tool-usage.md`. Confirm existing build authorization, the selected target/slice/ownership, reviewed frozen packet, and passing readiness gate before writing implementation. Give a fresh implementer context only the approved packet and permitted original assets when separation is required; disclose prior exposure and stop at the boundary if no valid context can be provided. Choose and write original architecture/code. Implement the ready slice within ownership while retaining unresolved requested scope. Do not substitute redesigned or reduced behavior for missing evidence. Report implementation and developer checks separately from independent acceptance; do not implicitly publish or install.

## validate

Read `verification-and-recovery.md`, applicable `visual-and-journey.md`, `fidelity.md`, and `tool-usage.md`. This mode is read-only toward candidate implementation, frozen requirements/oracles, and prior evidence; it may write new evaluation records and capture evidence for already authorized probes. Use an independent evaluator context where required. Evaluate the identified candidate against pre-frozen cases, preserve actual outcomes and paired target/candidate evidence, and run applicable local record validators. Never populate actuals from expected values or change expectations to match the candidate. Report quality, regression stability, fidelity, failures, unknowns, exclusions, and blockers separately. Stop with a repair recommendation; do not automatically repair.

## repair

Read `verification-and-recovery.md`, `implementation-readiness.md`, and applicable fidelity/visual guidance. Reproduce recorded accessible defects and prioritize their user impact within authorized ownership. Freeze the failed candidate/run and evidence; create a new candidate identity, then implement original corrections from the approved packet. New target facts require new contract review, not changed oracles to hide failures. Independently revalidate the repaired candidate against unchanged target-derived cases and affected regressions before closing gaps. Continue accessible specified repair work; if a concrete access or dependency blocker prevents progress, leave an explicit incomplete checkpoint with the next reproducible step.

## status

Read existing project status, session/task ownership, target identity, locked objective, packet/contract hashes, readiness, candidate revision, acceptance results, and open gaps. Report evidence-backed completed work, remaining full requested scope, concrete blockers, owners, and next action. This is read-only: do not edit records, execute probes, run builds, repair, install, or publish. If records are absent or inconsistent, report that uncertainty without manufacturing progress.

## all

Orchestrate `discover` → optional `rea` only when available and permitted → `spec` with reviewed packet and frozen expectations → `ready` for selected slices → `build` with original implementation → independent `validate` → `repair` and independent revalidation for accessible specified gaps. Load each stage's references only as it is reached. Preserve separate researcher/implementer/evaluator contexts and approved packet exposure boundaries wherever required; do not pretend a role label resets exposure. Delegate fresh contexts only through available authorized mechanisms; otherwise report the concrete blocked stage.

Track every requested feature and surface across the entire sequence. Ready independent slices can proceed while other slices remain blocked, but retain those slices and discovery obligations in the denominator. Never call a partial result full completion, silently reduce scope, replace fidelity with redesign, or claim local record checks establish runtime parity. A blocker affects its dependent stages; continue other permitted ready slices and discovery that can make meaningful progress. Return an incomplete checkpoint only when no further meaningful permitted work remains, or the user requests a checkpoint. At that concrete unresolved access/dependency/approval boundary, retain completed artifacts and failures and state the next step. Completion requires the applicable independent acceptance evidence and closed accessible gaps, not merely a packet or build. No implicit publication, global installation, provider setup, account action, push, or external message is part of this command.
