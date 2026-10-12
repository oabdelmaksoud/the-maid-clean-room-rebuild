# Pocket Tasks: does broader validation catch more?

An original tiny task-list app with three deliberately seeded regressions. The initial narrow `exact_json` case checks adding one valid task. Enhanced coverage adds ordered journey traces for blank input and save/reload, plus pixel checks at desktop and mobile sizes.

The real browser trial catches all three faults that the narrow baseline misses. Each isolated mutation fails exactly its corresponding enhanced case; the repaired variant passes all five. This measures the value of added coverage in this controlled example. Richer tests could also have been written using the previous JSON oracle; this does not establish automatic defect discovery, general quality improvement, or independent clean-room separation.

## Run it

From the repository root, install optional browser-runner dependencies outside the repository. The record validators remain standard-library-only.

```sh
python3 -m venv /tmp/maid-browser-python
/tmp/maid-browser-python/bin/pip install Pillow==12.1.1
npm install --prefix /tmp/maid-browser-node playwright@1.62.1
/tmp/maid-browser-node/node_modules/.bin/playwright install chromium
/tmp/maid-browser-python/bin/python examples/pocket-tasks/run_trial.py \
  --output /tmp/maid-pocket-trial \
  --playwright-module /tmp/maid-browser-node/node_modules/playwright
```

Use a new output directory for every run. `--node PATH` selects a Node executable; `--browser-executable PATH` optionally selects an already installed compatible Chromium executable. Linux may require Playwright's documented browser system dependencies. Dependency installation needs network access; the trial itself serves the original app on loopback and blocks browser requests to other origins.

The runner exits nonzero if actual detections differ from the controlled expectation or any portable acceptance gate disagrees. It saves all failed results as evidence. To inspect individual gates:

```sh
python3 skills/the-maid-rebuild/scripts/validate.py /tmp/maid-pocket-trial/baseline \
  --stage acceptance --run runs/buggy.json --candidate pocket-buggy
# Expected exit 0: the old narrow add-task check misses all three faults.
python3 skills/the-maid-rebuild/scripts/validate.py /tmp/maid-pocket-trial/enhanced \
  --stage acceptance --run runs/buggy.json --candidate pocket-buggy
# Expected exit 1: blank feedback, persistence and mobile layout fail.
python3 skills/the-maid-rebuild/scripts/validate.py /tmp/maid-pocket-trial/enhanced \
  --stage acceptance --run runs/fixed.json --candidate pocket-fixed
# Expected exit 0: all five cases pass.
```

## What is preserved

- `source/` and `source-hashes.json`: frozen original app, contract, harness and portable validator snapshot.
- `frozen-before-candidates.json`: both manifest hashes, source hashes, runtime metadata and freeze timestamp, written before candidate runs.
- `reference/`: original blank-state screenshots, frozen before all candidates.
- `baseline/` and `enhanced/`: manifests, packet, per-variant run records and evidence.
- `summary.json`: observed per-case outcomes; `gate-results.json`: actual validator outputs and exit codes.
- PNG screenshots for people, P6 RGB PPM files for the portable pixel oracle; journey JSON records read from actual browser DOM after actions.

The same original source selects explicit `buggy`, `mobile`, `persistence`, `feedback`, or `fixed` variants through a query parameter. Fresh browser contexts isolate storage. Zero pixel tolerance is reasonable here because reference and candidates run in the same browser environment; the reference is regenerated for each controlled trial, never from a candidate after failure. For an external project, approve and freeze a trustworthy baseline separately, including fonts, browser, operating system, scale and viewports.

This trial uses author-reviewed synthetic expectations and automated review labels. It does not establish human UX approval, accessibility conformance, pixel similarity across operating systems, full application parity, or a legal clean-room guarantee. Binary evidence remains in the selected output directory, outside the source distribution.
