# Research-to-implementation boundary

Use separate researcher, implementer, and reviewer contexts when the project requires separation. Contexts are information boundaries, not merely different task labels. An implementer who has seen source material cannot become unexposed by changing their role name.

1. Lock the exact original request, target/version/platform/runtime, target path or identity and objective. Record research scope, exposure disclosures, source decisions and unresolved issues.
2. Inventory every surface/feature within the requested scope, including settings, menus, files and recovery paths. Obtain a completeness review and a distinct intent review against the original request. Distill approved material into behavioral statements. Exclude target implementation code, copied assets, restricted captures, private endpoints, account material, and uncertain sources.
3. Choose original architecture independently and label it as design. Keep the reasoning separate from target observations.
4. Ask a separate reviewer to inspect the proposed packet and source-use decisions. Packet review is separate from intent review: a safe sanitized packet can still omit required surfaces or describe the wrong deliverable. Record their actual decision and limitations, never a fabricated approval.
5. Freeze the approved file list and hashes. Deliver only that packet and permitted original assets to the implementer context.
6. Reopen review when evidence, scope, permissions, or packet files change. Keep historical packets identifiable.

The source ledger can retain excluded entries for accountability without including their contents in the packet. A machine check can establish that references and hashes agree. A person must still assess whether the stated source-use basis is adequate and whether the disclosures are truthful.

This process is a project control. It provides no legal certification and cannot establish historical independence from public repository documents alone.


For faithful rebuilds, preserve abstract target behavior and appearance requirements in the packet without copying restricted implementation or assets. Evaluators may retain permitted target captures and files outside the authors' packet when required by the source boundary. Missing evidence is an explicit handoff gap; it is not authorization to redesign. A user decision changing scope must be linked to the locked request and frozen contract. See [fidelity](fidelity.md).

On resume, recover the same target path/identity, exact request, objective, contract/packet digests, candidate path/revision, open blockers and next action. Re-check filesystem/worktree state before edits. Never infer a new objective from a completion summary or accidentally treat candidate regression evidence as target evidence.

## Shared canonical requirements

Give authors and evaluators the same approved behavioral facts with stable requirement IDs. For each applicable state record surface, precondition, action, exact visible strings, enabled/disabled controls, navigation result, persisted effect, and error/recovery outcome; record explicit not-applicable dispositions rather than ambiguous blanks. Link evidence locator, confidence, source IDs and acceptance case IDs. Preserve evaluator-only captures outside the packet where required, while handing off approved measurements and facts. Resolve conflicting labels before readiness; do not silently choose the author's or evaluator's wording.

Map approved requirements to packet fields and acceptance cases, and map implemented controls back to requirements or explicitly proposed original design. Mechanical coverage checks cannot judge semantic equivalence: a separate reviewer must reconcile the packet against the canonical facts. Plan the service behind each capability before choosing a backend. A different service must demonstrate the required outcomes; a named model selector, placeholder or unavailable dialog does not demonstrate routing or capability.

Use [implementation readiness](implementation-readiness.md) for a selected slice. Full inventory completeness, provisional permission to develop, and readiness to implement that slice are separate claims. Only applicable slice requirements block that slice; remaining requested scope stays visible in the backlog.
