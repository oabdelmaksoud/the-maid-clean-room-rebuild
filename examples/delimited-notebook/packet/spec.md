# Delimited Notebook: original synthetic specification

This teaching design was authored for Behavior Rebuild Kit. It describes no competitor.
Accept UTF-8 CSV with the exact header item,amount. Require nonempty item text and finite nonnegative decimal amounts with at most two decimal places. Parse all rows before replacing in-memory records. Invalid input preserves the previous records and creates no export.
For valid input, calculate an exact decimal total and export the same header and ordered rows with two decimal places. The supplied three rows total 35.50.
The example checks import, total, export, and invalid-input state preservation in one process. It makes no durable crash recovery, concurrency, production readiness, or retry/idempotency claim.
The oracle independently parses the actual exported CSV, checks header/rows, and sums its amounts; the negative oracle compares state and checks absence of an output file.
