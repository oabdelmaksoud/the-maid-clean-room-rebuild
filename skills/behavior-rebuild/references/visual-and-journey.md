# Visual and user-journey validation

A UI contract has at least two distinct questions: does the checkpoint look right, and does the sequence of actions leave the right observable state? Record separate cases for each. Keep outcome checks such as export contents or persistence after reload alongside them.

## Freeze before execution

Use the [UI validation template](../assets/templates/ui-validation.md). Record permitted evidence, baseline provenance, original synthetic inputs, expected states, screenshot checkpoints, and explicit exclusions. Have the packet reviewed before implementation. Keep raw research and evaluator baselines outside the implementer's packet unless specifically permitted; the current packet format accepts only Markdown, text, JSON, and CSV.

Freeze expected journeys and visual baselines before running the candidate. A permitted target capture supplies the baseline for faithful visual comparison. An independently approved original design supplies a candidate regression baseline only; it cannot establish target fidelity. Identify the baseline origin in every result. Do not derive expectations from the candidate under test. Hash each baseline and bind the exact project manifest in the explicit run. Changing a baseline or tolerance creates a new contract and run; retain the previous evidence and rationale. Never automatically rebaseline after a failure.

## Capture repeatably

Record browser/version, operating system, viewport, device scale factor, color scheme, locale, timezone, fonts, and data seed. Use local, stable assets where permitted. Wait for the declared ready state and fonts; disable transitions/animations and hide the caret. Freeze clocks or exclude dynamic regions explicitly. Record storage initialization and whether reloads reuse the same browser context.

Use the same conditions for reference and candidate. Font rasterization and browser/OS differences can change pixels despite equivalent behavior. A changed environment requires investigation, not a quietly enlarged tolerance. The tools compare RGB pixels, not perceptual similarity or accessibility.

If only one region matters, crop both captures with a predeclared rectangle before freezing the baseline. Store the rectangle and full captures as evidence. The validator has no implicit masking, cropping, scaling, or image normalization. Region selection must not conceal required behavior.

## Visual oracle

`visual_pixels` compares a hashed binary PPM P6 baseline with a PPM result. The exact fields, limits, and changed-pixel rule are in [record format](record-format.md). Use zero budgets for exact comparison when capture conditions support it. Any nonzero budgets need a written rationale established before execution. Budgets that allow every possible image to pass are rejected, but a permissive valid budget can still miss important small defects.

Browser screenshots commonly arrive as PNG. Retain the PNG as evaluation evidence and convert a copy into 8-bit RGB PPM before validation. Optional capture tools such as Pillow can perform this conversion; the core validator needs only the Python standard library and never launches a browser. The full repository's `examples/pocket-tasks` supplies a runnable browser example. The standalone skill includes the validator and guidance, not browser dependencies.

A visual result proves only the recorded image comparison. It cannot prove the image came from a particular runtime, that a button works, or that the page is accessible.

## Journey oracle

`journey_trace` requires an ordered, nonempty `steps` array. Each step has a unique `id`, a nonblank `action`, and a nonempty `state` object. Freeze both the actions and assertions before execution. The recorded result must match exactly, including JSON types and array order.

Capture state from actual observations: visible DOM values, selected controls, storage reads, navigation state, or produced files. A runner should perform each action and read state afterward. Do not copy expected state into the trace or use a supplied `passed: true` value as the outcome. Keep enough independent evidence to inspect the runner's claims.

Choose states that distinguish failures. For a persisted task, check visible completion, read storage, reload, and check the restored state. Merely recording that a click was attempted cannot distinguish a working button from an ignored event. Use complementary accessibility and usability review when needed; exact traces cover only the selected paths.

## Demonstrate added value

Run the old baseline checks and the expanded checks on the same candidate. Include deliberate visual and journey faults whose expected outcomes were fixed first. Report baseline passes, additional failures, and repair reruns separately. Retain failing images and traces and have a separate reviewer inspect the capture method and evidence.

Every automated pass claim is independently recomputed by the validator from its supplied result. Accepted-review records are still attestations. Candidate IDs and manifest/file hashes bind records and bytes; they do not authenticate runtime execution or enforce context/filesystem isolation.

## Optional discovery tools

REA can assist permitted observations when useful. It is neither installed nor required by this skill. Do not put proprietary source, extracted bundles, private endpoint material, credentials, or copied assets into the handoff. A discovery tool's output is evidence requiring review, not permission to broaden access. Replica is also not a dependency. Keep the default workflow portable and use the same evidence boundaries whichever capture tool you choose.


## Target fidelity versus candidate regression

Apply the locked objective in [fidelity](fidelity.md). Approval of an attractive original design does not authorize replacing a faithful rebuild. Keep paired target/candidate captures and ordered observations for every requested surface, under comparable state and capture conditions. Unavailable target evidence remains unknown or blocked; a candidate-only screenshot cannot close it.

Run native deliverables in their actual native runtime, including launch/relaunch, complete board or content visibility, menus, focus, keyboard actions, dialogs and file panels. Browser testing can complement this evidence but cannot substitute for it. If file compatibility is requested, exchange actual files in both directions and inspect reopened state and failure behavior. Freeze the target-derived expected outcomes before those candidate trials.

Report regression results separately from target matches, dimension coverage and unresolved surfaces. A negative visual control proves detection of that particular fault within the declared budgets. It does not prove exhaustive fidelity.
