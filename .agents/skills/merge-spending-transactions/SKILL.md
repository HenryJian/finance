---
name: "merge-spending-transactions"
description: "Use when merging, regenerating, normalizing, or inspecting yearly spending transaction CSV files from raw Amex and CIBC card exports in this finance repository."
---

# Merge Spending Transactions

Use this skill when the user asks to merge, regenerate, normalize, or inspect
the yearly spending transaction CSV files from raw card exports in this finance
repository.

## What It Does

- Reads raw exports from `spending/raw-transactions/`.
- Preserves raw export files unchanged.
- Generates one normalized CSV per transaction year in `spending/transactions/`.
- Outputs exactly these columns:
  `transaction_date`, `card`, `merchant`, `amount_cad`.

## Command

Run from the repository root:

```bash
./.venv/bin/python spending/scripts/merge_transactions.py
```

## Amount Convention

- Amex `Amount` values are already CAD and are copied as signed values.
- CIBC debit values become positive `amount_cad` values.
- CIBC credit/payment values become negative `amount_cad` values.

## Verification

After running the script, check the generated files without printing full
private transaction rows:

```bash
./.venv/bin/python - <<'PY'
import csv
from pathlib import Path

for path in sorted(Path("spending/transactions").glob("transactions-*.csv")):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    print(path, reader.fieldnames, len(rows))
PY
```
