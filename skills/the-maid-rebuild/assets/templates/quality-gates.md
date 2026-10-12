# Quality gate matrix

| Gate | Required evidence | Blocking conditions | Decision owner |
|---|---|---|---|
| Intent | Original request and evidence, target/version/path/platform/runtime, locked objective, distinct review | Redesign or reduced scope without user decision; wrong deliverable | [owner] |
| Discovery completeness | Every requested surface/feature, observed/documented/unknown distinctions, target evidence and case mapping | Missing menus/settings/files/recovery surfaces; unreported unknowns | [owner] |
| Handoff | Exact packet inventory/hashes, source-use review and exposure attestation | Unknown origins, unapproved sources, unlisted files; intent review replaced by packet review | [owner] |
| Acceptance | Explicit run/candidate, current manifest hash, every required trial and oracle | Missing/failed outcomes, stale bindings, open blockers | [owner] |
| Fidelity | Paired target/candidate evidence by requested dimension, actual required runtime and file compatibility | Candidate-only regression called fidelity; unknown/mismatched required features; unsupported coverage claims | [owner] |
| Publication | License/provenance review, secret/content review, installation and CI evidence | Unreviewed redistribution or untested supported claims | [owner] |

Keep matched, mismatched, unknown and user-authorized deviations in the inventory denominator. Report behavior, visual, journey, interoperability and platform dimensions separately; no single completion or fidelity percentage is implied. An approved deviation is a qualified outcome, not an unchanged feature.

Existing explicitly bounded projects retain bounded acceptance gates. The fidelity supplement is required when making fidelity claims; it does not retroactively broaden those projects. Validators check local recorded evidence and consistency; content review and observation truth remain reviewer responsibilities.
