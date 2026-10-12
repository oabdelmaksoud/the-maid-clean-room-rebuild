# Delimited Notebook

This fictional CSV workflow is original synthetic material for The Maid - Clean Room Rebuild (formerly Behavior Rebuild Kit). It does not describe or compare a competitor. Its static `project.json` and `packet/` demonstrate a discovery/handoff record; executed acceptance evidence is generated separately.

The runner imports rows with the exact `item,amount` header, parses finite nonnegative amounts with at most two decimal places, calculates a decimal total, and exports the original rows with amounts formatted to two decimals. The valid fixture has three rows totaling **35.50**. The export preserves those three rows; it does not append a total row.

A separate output reader uses `csv.reader` and integer cents to recalculate the total and capture row names and amounts. The result is compared with the recorded expectation. This avoids reusing the transformation's decimal summation, but both paths are authored in the same demonstration script. It is not an external application or independently commissioned reviewer.

The invalid fixture checks rejection, preservation of the previous in-memory state, and absence of a new export. This limited demonstration does not implement cancellation, crash recovery, persisted transactions, idempotency tokens, or receipt recovery. Those need additional contracts, implementation, and cases before acceptance.

From the repository root:

```sh
python3 examples/delimited-notebook/run_demo.py --output ../behavior-rebuild-demo
python3 skills/behavior-rebuild/scripts/validate.py ../behavior-rebuild-demo --stage acceptance --run runs/demo.json --candidate demo-v1
```

Use Python 3.11+ and a new destination outside this canonical example. The runner copies the manifest and packet, writes result artifacts, and creates `runs/demo.json` bound to the manifest's exact bytes. It refuses an existing destination. Choose another path for another run.

The recorded reviewer `deterministic-demo-oracle` explicitly denotes automated synthetic fixture checks. A passing recorded-evidence gate validates the supplied format, hashes, assertions, and review fields. It does not prove human review, broad CSV compatibility, real-product readiness, or legal independence. Keep historical runs; do not edit their identities to match later manifest changes.
