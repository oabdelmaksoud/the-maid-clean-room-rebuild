---
name: the-maid-build
description: For The Maid clean-room product rebuilds, Independently implement authorized ready slices using the approved packet and permitted original assets.
---

# The Maid - Build

Invoke as `$the-maid-build` in Codex. This is a native skill command, not a shell binary.

First load the shared [The Maid - ReBuild core](../the-maid-rebuild/SKILL.md). If it or the command reference is missing, stop: install both `the-maid-build` and `the-maid-rebuild` as sibling folders in `${CODEX_HOME:-~/.codex}/skills` from the same release's skill archive, then retry. Do not invent a fallback workflow.

Then read only the `build` section of [command modes](../the-maid-rebuild/references/commands.md) and the core references required by that section. Execute mode `build` with the core's source restrictions, approved-packet boundary, context exposure disclosures, full requested scope, and authorization requirements intact. This explicit mode controls execution; do not advance to another mode unless its contract permits it or the user selects it.
