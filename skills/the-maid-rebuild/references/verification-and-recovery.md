# Outcomes, gaps, and recovery

Freeze fixture identities, assertions, oracles, trial count, and tolerances before execution. Record the corpus identity with every run. A changed corpus needs a new identity; do not rewrite historical results to match it.

Distinguish structural validation, feature breadth, recorded acceptance evidence, and independently verified real-work outcomes. A named command or test proves neither execution nor correctness. A screenshot of success does not establish that an exported file opens correctly in another reader.

For each run retain implementation revision, environment, individual trial outcomes, actual evidence artifacts and hashes, oracle results, limitations, and reviewer disposition. Record pass, failed, blocked, unknown, or justified skip. Required unavailable oracles block acceptance. Do not let a successful earlier run conceal a later failure.

Report denominators and exclusions, keeping all inventoried features and unknowns visible. A user-authorized deviation remains a deviation rather than a match. Evaluate correctness, usability, recovery, interoperability, latency, and cost as applicable; avoid combining them into a single readiness percentage. A synthetic example validates the method's mechanics only within its declared scope.

For gaps, record severity, workflow exposure, evidence confidence, estimated effort and uncertainty, owner, reproduction, and recovery acceptance condition. Rank user-harming blockers first, then exposure, then confidence, then effort. Explain any owner override. Weak evidence may call for a discovery task before a repair.

Exercise cancellation, partial output, process loss, and lost receipts where relevant. Name interrupted and persisted states, permitted retry effects, and artifact checks. Minimize failing inputs into original regression fixtures. Reopen accepted behavior after regression, preserve previous evidence, and close the gap only after its acceptance condition is rerun and independently evaluated.

## Visual and journey coverage

Use [visual and journey validation](visual-and-journey.md) for UI behavior. Freeze the viewport, browser environment, screenshot checkpoint, baseline, tolerances, and ordered state assertions before executing the candidate. Separate appearance from interaction, persisted state, and exported outcomes; a screenshot cannot replace a journey trace and a trace cannot establish visual fidelity.

Compare a baseline suite with the expanded suite against the same candidate and deliberately flawed variants. Record which defects the baseline misses and the added checks catch. A seeded defect demonstrates detection of that fault, not general coverage of all UI regressions. Preserve failing artifacts, make the repair, and rerun the unchanged checks. Never regenerate the expected screenshot or trace just to make the candidate pass.


## Fidelity and intent gates

Use [fidelity](fidelity.md) for the separate contract/evaluation records. Assess intent review, inventory completeness, source/packet review, executed behavior, paired target/candidate evidence, native platform behavior and actual interoperability as distinct gates. Packet acceptance and a passing bounded acceptance corpus cannot establish a faithful product rebuild.

For each dimension report counts of matched, mismatched, unknown and authorized-deviation features with explicit denominators. Keep criticality visible; removing optional or unobserved features from the denominator inflates coverage. Do not combine these dimensions into an unsupported “100%” score. A qualified user-authorized result with deviations is not a full match.

Changing scope or expected outcomes needs the recorded user decision or new target evidence, fresh review and a new frozen contract; retain historical runs. A repair closes a specific gap only after the unchanged target-derived assertion and affected native/file journeys are independently rerun.
