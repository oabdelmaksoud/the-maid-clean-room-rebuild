# Evidence boundary

For each project, record the authorized sources and uses before gathering evidence. Permissions attach to a specific source, version, action, and handoff use; they are not inferred from confidence or public access. Retain versioned decisions and review changed permissions before reusing a packet.

Exclude competitor proprietary source, disassembled bundles, private endpoints, credentials, account material, copied product assets, and uncertain sources from this toolkit and its implementation packets. Existing private observation collections must not be copied into the repository. A permitted source may support a distilled behavior claim without permitting redistribution of the original artifact.

Disclose what each participant/context has already seen. A fresh implementation context can restrict future inputs, but it cannot undo an author's prior exposure. An independent reviewer checks the packet and disclosures; neither a role label nor the validator establishes independence.

File hashes identify exact bytes and detect changes. They do not establish source permission, truth, legal clearance, authorship, semantic correctness, or target equivalence. The machine gate checks the supported record rules; source-use and outcome judgments remain explicit review work.

Storytold inspired this method, with repository-specific policies. See [NOTICE](../NOTICE.md) for pinned attribution and the limits of that inference.

## Local filesystem assumption

Use a trusted, quiescent local copy for validation. Keep other writers from replacing files or path components while checks run. Path and hash validation reduce accidental or recorded-input escapes; they do not provide an operating-system sandbox against concurrent hostile filesystem mutation.
