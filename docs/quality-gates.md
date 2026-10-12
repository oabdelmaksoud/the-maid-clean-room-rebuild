# Quality gate matrix

| Claim | Mechanism | Remaining evaluation |
|---|---|---|
| Records have the supported format | Strict versioned parser and reference checks | Whether the records are truthful and sufficiently scoped. |
| Evidence bytes match references | Local SHA-256 checks and safe path reads | Evidence provenance, permission, and semantic relevance. |
| Packet matches declared handoff | Exact file set, hashes, extensions, source references, exposure/reviewer fields | Reviewer must inspect content and the stated use basis. |
| Required outcomes have recorded support | Explicit run/candidate binding, trials, oracle/result and review checks | Reproduce the outcome and assess oracle independence. |
| Required uncertainty blocks acceptance | Missing/failed/blocked/unknown trial rules and open blockers | Whether the chosen required cases cover actual user needs. |
| Exclusions are visible | Explicit approved exclusions and denominator reporting | Whether scope reduction is justified. |
| Tools behave predictably | Unit/CLI negative tests and bounded read checks | Platform combinations actually executed. |
| Skill is portable | Isolated-folder link/tool smoke test | Native host discovery and behavior trials. |
| Repository is ready to publish | Content/provenance review and publication checklist | Owner authorization, actual GitHub CI, and release inspection. |

Do not substitute one row's evidence for another. Source policy text needs an implemented check where mechanical enforcement is possible; a configured check needs an observed result. Agent instruction-following requires a separate behavioral trial with realistic source material and unknowns.

The tools rank gaps by severity, impact, then stable identifier. Confidence and effort belong in the reusable task/recovery notes for human prioritization; they are not measured or inferred by this version's ranker.
