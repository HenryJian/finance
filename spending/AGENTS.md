# Spending Tracking

This directory tracks the user's personal spending. Treat the files here as
private financial data and avoid unnecessary copying, printing, or broad
rewrites.

## Current layout

- `raw-transactions/`: canonical imported transaction exports, grouped by
  account/card. Keep these source CSVs intact unless the user explicitly asks to
  edit or replace an export.
- `raw-transactions/amex-1001/`: American Express exports for card/account
  ending `1001`. Files are named by statement period, such as `2026-5.csv`.
- `raw-transactions/cibc-2451/`: CIBC exports for card/account ending `2451`.
- `raw-transactions/cibc-8359/`: CIBC exports for card/account ending `8359`.
- `scripts/merge_transactions.py`: merges raw card exports into normalized
  yearly transaction CSVs.
- `transactions/`: generated normalized yearly CSVs. Recreate these with
  `./.venv/bin/python spending/scripts/merge_transactions.py` instead of
  editing them manually.
- Repo-local support: `../.agents/skills/merge-spending-transactions/` defines
  the Codex skill for regenerating and verifying the normalized yearly
  transaction CSVs.

## Data formats

- Amex CSVs have a header row with 14 columns:
  `Date`, `Date Processed`, `Description`, `Amount`, `Foreign Spend Amount`,
  `Commission`, `Exchange Rate`, `Additional Information`, `Merchant`,
  `Address`, `City / Province`, `Postal Code`, `Country`, `Reference`.
- Some Amex fields contain embedded newlines, so use a real CSV parser instead
  of line-oriented parsing.
- CIBC CSVs currently have no header row and use 5 columns:
  transaction date, description, debit amount, credit amount, masked card/account
  number.
- Dates appear as `DD Mon YYYY` in Amex exports and `YYYY-MM-DD` in CIBC
  exports.
- Generated yearly CSVs in `transactions/` have exactly 4 columns:
  `transaction_date`, `card`, `merchant`, `amount_cad`.
- In generated CSVs, `amount_cad` is Canadian dollars. Spending/charges are
  positive values. CIBC credits/payments are negative values.
- For generated CIBC rows, `merchant` is the second source CSV column.

## Working guidelines

- Preserve raw export filenames and contents when building derived summaries or
  reports.
- If adding normalized data, summaries, or generated reports, place them outside
  `raw-transactions/` and document the new location here.
- Use the `merge-spending-transactions` skill when regenerating or inspecting
  yearly merged spending CSVs.
- Be careful about logging full transaction contents; prefer row counts, date
  ranges, account suffixes, and aggregate totals when possible.
