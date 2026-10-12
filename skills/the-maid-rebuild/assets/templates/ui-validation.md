# UI validation contract

Complete this record before candidate execution. Unresolved fields remain blockers, not acceptance evidence.

## Scope and provenance

- Product/version and permitted observation scope:
- Frozen fidelity contract digest, objective, feature IDs and requested runtime:
- Original synthetic data and initialization:
- Baseline origin (permitted reference or approved original design):
- For faithful rebuilds: target capture identity and paired candidate checkpoint; original-design baselines establish regression only:
- Reviewer and exposure record:
- Required workflows and explicit exclusions:
- User instruction authorizing each deviation, with evidence reference (keep deviations in the inventory):

## Capture conditions

- Browser/version, operating system, fonts:
- Viewport, device scale factor, color scheme:
- Locale, timezone, clock handling:
- Ready-state rule, font wait, animation/caret handling:
- Storage initialization and reload behavior:
- Full capture paths and hashes:
- Predeclared crop rectangle, if any, and rationale:

## Approved measured specification

| Requirement / state ID | Element | Rectangle / spacing | Typography | Color / border / radius | Responsive / overflow rule | Evidence locator / review |
|---|---|---|---|---|---|---|

Provide approved measurements and original wireframes to authors. Keep restricted captures in evaluator evidence. Compare layout, typography and imagery separately; original assets do not become exact asset matches. Unknown CSS viewport, DPR or ready state blocks comparable visual claims.

## Visual cases

| Case ID | Checkpoint | Baseline path / SHA-256 | Width × height | Channel delta budget | Changed-pixel budget | Rationale |
|---|---|---|---|---|---|---|

Retain original PNG evidence and RGB PPM comparison files. Freeze the baseline and budgets before execution. Do not automatically rebaseline failures.

## Journey cases

| Case ID | Step ID | Action | Expected observable state | Actual-state collection method |
|---|---|---|---|---|

Use nonempty ordered steps and nonempty state objects. Include persistence/reload or error/recovery steps where required. Read actual candidate state; never copy expectations into results.

For faithful rebuilds, run paired target/candidate actions and compare enabled/disabled controls, visible outcomes, persisted state and produced files. Record actual runtime for each side. Mark unobserved paths unknown; a browser run does not discharge a native-runtime obligation.

## Comparison and recovery

- Baseline suite and unchanged candidate identity:
- Added visual and journey cases:
- Deliberate faults and expected detection:
- Observed baseline versus expanded results:
- Retained failing evidence:
- Repair identity and unchanged-contract rerun:
- Independent review and remaining limitations:

Bind the explicit run to the exact manifest bytes and candidate ID. These identities establish record consistency, not runtime authenticity or isolation.
