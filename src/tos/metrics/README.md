# src/tos/metrics — phase 2

Not part of the thin slice. When phase 2 is built this directory gets:

- `run.py` — the executor: runs a metric script over a snapshot under `raw/metrics/<connector>/` and returns a receipt `{ computation_sha256, snapshot_sha256, parameters, rows, fetched_at }`.
- `attest.py` — the attester: deterministic code that checks the receipt's hashes against the `Attested Computation` page and the snapshot file, and the parameters against the declared ones.
- one script per metric (e.g. `sprint_completion.py`).

Design: docs/design.html §3 "Numbers are attested, not remembered" and decision D9.
