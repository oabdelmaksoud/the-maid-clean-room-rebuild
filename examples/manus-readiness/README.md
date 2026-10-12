# Synthetic Manus-inspired slice-readiness trial

Run from the repository root with a **new output directory**:

```sh
python3 examples/manus-readiness/run_trial.py --output ../manus-readiness-trial
```

The runner retains the four fixture directories and `results.json` in that new directory. Omitting `--output` uses temporary records. It creates original synthetic records and exercises four cases: a conflicting author packet (exit 1), a reviewed corrected visual slice (exit 0), independent backend work while required visual scope stays blocked (exit 0 with provisional status), and a false full-scope readiness claim (exit 1). It exits 0 only when all four outcomes match those expectations.

This tests local gate mechanics inspired by the Manus trial findings. It performs no target access, product observation, generation task, browser capture or real service execution. Synthetic approvals are fixtures, not evidence of independent human review. No Manus screenshot, code or asset is included.

The blocked starter in `skills/the-maid-rebuild/assets/templates/readiness-starter` must be completed with real permitted evidence and separate reviews before use. See the readiness reference for exact shapes and remaining semantic responsibilities.
