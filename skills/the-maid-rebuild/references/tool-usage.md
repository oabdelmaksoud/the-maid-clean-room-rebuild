# Local tool usage

The Python 3.11+ standard-library scripts consume a project directory containing `project.json`. The exact contract is in [record format](record-format.md). This is a bespoke versioned JSON format, not JSON Schema. The tools never fetch locators or run target code.

Run `scripts/validate.py` with the project directory and `--stage discover`, `--stage handoff`, or `--stage acceptance`. Acceptance also requires an explicit project-relative `--run` path and `--candidate` identity. The run must bind the exact project manifest bytes and that candidate; the tool never chooses a newest run. `--digest` prints the manifest's SHA-256 identity without approving a gate. Add `--json` for machine-readable gate output.

Run `scripts/report.py` with a project directory. Without a run/candidate pair it reports discovery and says acceptance was not evaluated. Supply both to inspect recorded acceptance evidence. The report uses the same gate results as validation.

| Exit | Meaning |
|---|---|
| 0 | The selected supported structural/recorded-evidence gate passed. |
| 1 | Records are well formed, but a gate is blocked or failed. |
| 2 | Input, path, integrity, or invocation is invalid. |

An empty starter project is intentionally blocked. A handoff needs the reviewed exact packet, exposure disclosures, allowed source use, and required fixture coverage. Acceptance needs all active required trials, available oracles, evidence integrity, recorded accepted review, and no open blocker gap. Optional failures and explicit exclusions remain visible.

`exact_json` compares recorded result JSON with the declared expectation, including type distinctions. `journey_trace` additionally validates a nonempty, ordered sequence of actions and observed states. `visual_pixels` compares bounded RGB PPM captures against a hashed baseline and frozen pixel budgets. `manual_review` requires evidence and a recorded review decision. Every automated pass claim is recomputed from its supplied result; declaring a pass does not bypass comparison. None of these modes establishes that the recorded experiment happened or that its reviewer is independent. Reviewers must inspect the actual evidence, source decisions, and authorship claims.

File paths are relative to the project; references to symlinks, non-regular files, and escaping paths are rejected. Unknown fields and format versions are rejected. Size/depth/file limits bound processing; see the format reference for precise limits. The validator does not scan arbitrary project files for secrets or certify publication safety.

## Browser capture is a separate step

The core tools need no browser, REA, Replica, Pillow, or network access. A browser runner produces evidence first; validation then reads that evidence offline. The optional Pocket Tasks example uses Playwright and Pillow for browser captures and PNG-to-PPM conversion. Those are example dependencies, not skill dependencies. See [visual and journey validation](visual-and-journey.md) for capture discipline and `examples/pocket-tasks/README.md` in the full repository for executable commands. The standalone skill archive does not include the example.
