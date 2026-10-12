# Existing chess app fidelity trial

This example tests whether The Maid catches fidelity gaps in an **existing, unchanged candidate**. A successful trial means the gate correctly **blocks** Quiet Knight under `faithful_reimplementation`; it does not mean the app passes fidelity acceptance.

From the toolkit root:

```sh
python3 examples/chess-fidelity/run_trial.py --output /path/to/new-evidence-directory
```

The output directory must not exist. Python's standard library is sufficient. `--maid-script /path/to/fidelity.py` can select an installed gate. `--candidate-html /path/to/standalone.html` optionally verifies the recorded candidate hash without launching it. The fixture itself requires no Mac, browser, chess library, application source, or binary.

The runner retains `gate-recorded.json`, `gate-forged-pass.json`, and `summary.json`. It exits zero only when the gate identifies all seven recorded differences, preserves all four unknown families, rejects the original-design visual baselines and incomplete inventory, and reports seven `ORACLE_MISMATCH` errors after passing labels are forged. The mutation preserves frozen expected values and hashed actual outcomes; it changes only assessment labels and the claimed baseline origin. A generic inventory blocker alone cannot make this trial succeed.

## Assessment and evidence

Target: Apple Chess 3.18, build Chess-600.4, native macOS. Candidate: Quiet Knight, native macOS wrapper with a browser companion. Existing standalone HTML identity:

```text
6f012bd249b247b2cbe173d1b0b52771bf80ddffcb02869f74ff6d63b62df4e3
```

No app was rebuilt for this reassessment. The fixture combines sanitized prior synthetic-game observations, prior candidate results/source verification, and the parent evaluator's partial native menu inspection on October 11, 2026, approximately 22:04–22:07 America/Detroit. New dialogs were canceled; listed commands, variants, speech and style controls were inspected for presence, not executed. Private games, moves and window names are omitted. No application bundle, native binary, target image, target artwork, or chess implementation is included.

| Recorded status | Feature families |
| --- | --- |
| 4 matches | Four local player modes, native macOS execution, 64 labeled squares, observed opening squares/turn/log count |
| 7 differences | 3D board, style choices, variants, local Hint/Undo availability, Game Center option, speech controls, native document command inventory |
| 4 unknowns | Camera gestures, actual speech output, target save/PGN interoperability, computer strength equivalence |

Each required feature maps to a target surface and a frozen case. Known outcomes are JSON records bound to candidate and case IDs. The observed opening outcome is decoded from a prior runtime trace. Other outcomes are sanitized source/menu attestations, rather than a newly executed comprehensive runtime probe. Unknown cases have no invented outcomes. `fixture-identities.json` records original artifact identities; `fixture/evidence/` explains their provenance and limits.

The current evaluator request authorizes a faithful comparison. It does **not** retroactively reclassify the earlier original-design contract or assert user-authorized deviations. The target inventory is explicitly not exhaustive, so `completeness.reviewed` remains false.

## Why the earlier checks can pass

Quiet Knight's earlier contract intentionally specified an original 2D interface and excluded variants, speech, Game Center and target file compatibility. Its 476 rules, 21 browser journeys and original-design visual checkpoints support that bounded contract. They cannot establish near-complete Apple Chess fidelity.

The parent evaluator freshly reran that old five-case acceptance gate and the 476-rule suite successfully during this reassessment. It did **not** freshly replay all 21 browser journeys or recapture all prior screenshots. Those legacy results remain separate from this fidelity gate. Two approved Quiet Knight visual baselines demonstrate original-design regression stability; they are expressly rejected as target visual evidence here.

The gate validates recorded evidence and compares known outcomes to frozen expectations. It does not discover omitted features, execute the chess app, authenticate observer declarations, or certify that the target inventory is complete. Human review remains necessary. `evidence-summary.json` records this example's local diagnostic run; the reproducible runner produces fresh gate evidence elsewhere.
