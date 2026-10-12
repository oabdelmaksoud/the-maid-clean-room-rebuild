# Requested fidelity and measurable coverage

Use this reference when scoping a reimplementation or assessing its completeness. Fidelity records supplement the existing `project.json` gates; existing bounded projects do not require migration merely to retain their earlier bounded claims.

## Lock intent before selecting a contract

Retain the exact original user request in a hashed local evidence file. Record the intended target/version, target path or identity, platform/runtime, deliverable and authorized source boundary. Select an objective supported by that request:

- `faithful_reimplementation`: preserve the requested product's observable appearance, behavior, journeys, platform experience and interoperability. Independently authored code and permitted original artwork do not authorize a redesign.
- `original_redesign`: the user explicitly requested or accepted changed appearance/behavior. Record the decision and what it changes.
- `bounded_workflow`: the user explicitly requested a limited workflow. State the boundary and keep findings within it.

Do not treat the builder's preference, a sanitized packet's omissions, unavailable observations or a passing finite test suite as authorization to reduce scope. When a required observation is unavailable, record unknown/blocked evidence and continue independent work that does not depend on it. Seek a user decision only for a concrete unresolved change of objective or scope; previously granted authorization remains applicable.

## Inventory the requested surface

Before handoff, map all surfaces within the requested scope: windows/views, menus and actions, dialogs, options, settings, navigation, status/errors, keyboard/accessibility paths, saved/opened/exported files, persistence/relaunch and recovery. Enumerate features per surface with evidence and acceptance case IDs. Mark critical features explicitly, but retain noncritical features in the denominator.

Observe both nominal and relevant failure paths with permitted synthetic data. Inventory entries distinguish observed, documented and unknown behavior. An unobserved surface remains an explicit gap. Have a reviewer evaluate inventory completeness against the original request and observed surface map before the implementer receives the packet.

The intent review answers whether the proposed objective and scope satisfy the user's original request. The packet review answers whether the implementation input is permitted, accurate and sufficiently specified. Keep separate records and dispositions; neither review substitutes for the other or supplies its own authenticity.

## Paired target and candidate evidence

For each feature retain the target observation, candidate observation, matching case IDs, exact candidate identity, runtime and review disposition. Dimensions are `behavior`, `visual`, `journey`, `interoperability` and `platform`. Record features in all requested dimensions; omitting an entire dimension is a completeness issue, not perfect coverage.

For visual fidelity use permitted target captures and comparable candidate captures. Identify target version, viewport/window size, state, platform, scale factor and assets/fonts. If source restrictions prevent giving target captures to authors, the evaluator can retain them outside the approved packet. Do not copy prohibited target assets or implementation code.

An independently approved original-design baseline checks regression of that candidate design. It cannot establish target visual fidelity. A native deliverable requires actual native launch, controls, menus, file panels and relaunch evidence; browser screenshots and engine tests alone cannot support it. Interoperability requires actual target-produced files reopened by the candidate and candidate-produced files reopened by the target when compatibility is requested and permitted. Similar button names or a new proprietary JSON format do not establish compatibility.

## Report coverage without inventing certainty

Use `match`, `mismatch`, `unknown` or user-authorized `deviation` per feature. Each match links executed passing cases and actual candidate evidence to target evidence. State which dimensions and surfaces were assessed, their denominators, critical failures, unknowns and authorized deviations. Do not convert task completion, packet approval, a selected subset of passing tests or an original-design regression result into “100% fidelity.”

A deviation requires the exact user instruction and its hashed evidence. It stays visible in coverage; approval does not turn changed behavior into a match. An unknown has no inferred pass. Frozen hashes identify files but do not authenticate observation, user instructions or runtime execution.

## Local fidelity records

Copy `assets/templates/fidelity-contract.json` and `fidelity.json` into the project, fill them from actual evidence, and replace the intentionally unresolved template fields. File references use `{"path":"relative/path","sha256":"64 lowercase hex characters"}`. Paths resolve inside the project directory. The contract freezes the request, objective, target, inventory and reviews; the evaluation binds that contract, candidate and executed evidence. The templates are intentionally unresolved: zero digests and missing evidence do not pass. Define every requested surface/feature and dimension from real observations before freezing.

`intent_review` has reviewer, approved and evidence fields; `completeness` separately records reviewer, reviewed and evidence. Contract `cases` bind IDs and feature IDs to a non-null typed `expected` value. Evaluation cases bind the same IDs to candidate ID, status, evidence and a `result` file reference (or null when unavailable). A result file is exactly `{"case_id":"case-id","candidate_id":"candidate-id","actual":<observed JSON>}`; the checker compares actual and frozen expected values with their JSON types. Read actual state after actions rather than copying expected values into the result.

Each evaluated feature records its status, candidate ID/evidence, case IDs, baseline origin (`target`, `original_design` or `not_applicable`) and deviation. A deviation is null or `{"instruction":"exact user decision","evidence":{"path":"evidence/decision.txt","sha256":"..."}}`; the instruction must occur in the hashed text. A faithful objective requires the requested target/candidate runtime and platform to agree. Explicit redesign/bounded objectives may use the runtime permitted by their request.

```sh
python3 skills/the-maid-rebuild/scripts/fidelity.py PROJECT_DIR --json
```

The CLI reads the explicit `fidelity-contract.json` and `fidelity.json` in that project directory without requiring `project.json`. Exit `0` means the recorded fidelity gate passed, `1` means well-formed evidence is blocked or fails, and `2` means invalid records or integrity/invocation errors. These remain local record checks; they do not observe the target, launch the candidate, prove authenticity or grant publication permission.

## Normalize requirement units

Keep URLs and documents in a source ledger, then derive atomic observable features. Map many sources to one behavior and one behavior to multiple state/dimension cases. A new documentation URL is not automatically a new critical feature. Keep broad unknown surfaces as discovery obligations, separate from executable acceptance cases; assign criticality by workflow impact. Have the inventory reviewed for overlaps and omissions. When normalizing an earlier contract, preserve its results and an old-to-new requirement mapping; do not remove historical failures to improve counts.

Report observed coverage, capability availability, behavioral agreement, visual agreement, output quality and unresolved evidence separately. Plan identity/session, orchestration/cancellation, browser/computer execution, context/uploads, artifact viewers/editing/export, automation, connectors, sharing and generation services when the requested target needs them. Record dependencies, authorized access, infrastructure, cost and source constraints. Independently chosen architecture must demonstrate target-relative behavior rather than substitute an easier product. No workflow tool supplies unobserved service behavior or promises near-100-percent whole-product equivalence.
