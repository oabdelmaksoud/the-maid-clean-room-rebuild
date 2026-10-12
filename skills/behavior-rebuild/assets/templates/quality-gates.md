# Quality gate matrix

| Gate | Required evidence | Blocking conditions | Decision owner |
|---|---|---|---|
| Discovery | Bounded cases, provenance, independently designed commands | Empty scope, malformed records | [owner] |
| Handoff | Exact packet inventory/hashes, permission review, attestation | Unknown origins, unapproved sources, unlisted files | [owner] |
| Acceptance | Explicit run/candidate, current manifest hash, every required trial and oracle | Missing/failed outcomes, stale bindings, open blockers | [owner] |
| Publication | License/provenance review, secret/content review, installation and CI evidence | Unreviewed redistribution or untested supported claims | [owner] |

Record feature breadth separately from accepted real workflows. The validator checks recorded evidence and consistency; content review and truth of an observation remain reviewer responsibilities.
