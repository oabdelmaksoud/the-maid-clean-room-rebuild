# Compatibility and verification scope

The canonical distribution is the complete `skills/the-maid-rebuild/` directory. It contains Markdown instructions, references, JSON/Markdown templates, and Python scripts. Root examples and documentation are optional repository resources. No plugin manifest, hooks, or MCP server is required.

## Observed coverage

| Surface | Observed result | Limit |
|---|---|---|
| Python on macOS arm64 | Initial full suite passed on 3.11.15, 3.12.12, 3.13.13, and 3.14.6 | Exact final test results belong in the release verification record. |
| Codex 0.160.1 | Loaded local `.agents/skills`; discovery preserved unknowns and handled source injection; handoff inspected packet/exposure; demo acceptance exited 0 and wrong revision exited 2 | Project-local and global installed trials; bounded behavior, not a guarantee for every future agent decision. |
| Claude Code 2.1.215 | Local `.claude/skills` trial attempted | “Not logged in” occurred before inference; native behavior remains unverified. |
| GitHub CI: Linux, macOS, Windows | Six jobs passed: each OS with Python 3.11 and 3.14; 36 tests, demo, explicit acceptance, and release build passed in each job | [Observed run](https://github.com/oabdelmaksoud/the-maid-clean-room-rebuild/actions/runs/38187814468) tested the initial published revision recorded in [release verification](release-verification.md); OS CI does not establish native agent behavior. |
| Other agents | Manual Markdown/template use is available | Native loading and behavior unverified. |

Follow the chosen host's current documented skill installation process and copy the entire folder, not only `SKILL.md`. Initial trials used project-local skill locations. A subsequent trial used a complete global Codex installation and exercised the method on a bounded real-command project; see [project trial](project-trial.md). The install command in the [README](../README.md) copies the skill only; it does not edit agent configuration. A plugin adapter remains deferred until trials demonstrate useful installation or update behavior.

The offline validators require Python 3.11+ and only the standard library, including the visual-pixel and journey-trace checks. The optional Pocket Tasks browser trial additionally uses Node.js, Playwright/Chromium, and Pillow to capture PNGs and convert them to the validator's bounded PPM format. These capture dependencies are not required to install or use the portable skill. REA is optional discovery tooling and is not a dependency of any acceptance gate.

Validate a trusted, quiescent local copy: no other process should replace files or path components during inspection. The validator is not a sandbox against concurrent hostile filesystem mutation.

A configured CI matrix states intended coverage. Only observed completed runs establish tested combinations. The [release verification record](release-verification.md) identifies the tested revision, commands, versions, results, and remaining limitations. Later documentation updates are not implicitly covered by an earlier CI run.
