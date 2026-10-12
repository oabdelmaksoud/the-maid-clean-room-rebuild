# Outcomes, gaps, and recovery

Freeze fixture identities, assertions, oracles, trial count, and tolerances before execution. Record the corpus identity with every run. A changed corpus needs a new identity; do not rewrite historical results to match it.

Distinguish structural validation, feature breadth, recorded acceptance evidence, and independently verified real-work outcomes. A named command or test proves neither execution nor correctness. A screenshot of success does not establish that an exported file opens correctly in another reader.

For each run retain implementation revision, environment, individual trial outcomes, actual evidence artifacts and hashes, oracle results, limitations, and reviewer disposition. Record pass, failed, blocked, unknown, or justified skip. Required unavailable oracles block acceptance. Do not let a successful earlier run conceal a later failure.

Report denominators and exclusions. Evaluate correctness, usability, recovery, interoperability, latency, and cost as applicable; avoid combining them into a single readiness percentage. A synthetic example validates the method's mechanics only within its declared scope.

For gaps, record severity, workflow exposure, evidence confidence, estimated effort and uncertainty, owner, reproduction, and recovery acceptance condition. Rank user-harming blockers first, then exposure, then confidence, then effort. Explain any owner override. Weak evidence may call for a discovery task before a repair.

Exercise cancellation, partial output, process loss, and lost receipts where relevant. Name interrupted and persisted states, permitted retry effects, and artifact checks. Minimize failing inputs into original regression fixtures. Reopen accepted behavior after regression, preserve previous evidence, and close the gap only after its acceptance condition is rerun and independently evaluated.
