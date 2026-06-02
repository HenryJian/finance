#!/usr/bin/env python3
"""Merge raw card transaction exports into one normalized CSV per year."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


SPENDING_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = SPENDING_DIR / "raw-transactions"
OUTPUT_DIR = SPENDING_DIR / "transactions"
OUTPUT_COLUMNS = ["transaction_date", "card", "merchant", "amount_cad"]


@dataclass(frozen=True)
class Transaction:
    transaction_date: str
    card: str
    merchant: str
    amount_cad: Decimal

    def as_csv_row(self) -> dict[str, str]:
        return {
            "transaction_date": self.transaction_date,
            "card": self.card,
            "merchant": self.merchant,
            "amount_cad": f"{self.amount_cad:.2f}",
        }


def parse_amount(value: str, *, path: Path, row_number: int) -> Decimal:
    normalized = value.strip().replace(",", "")
    try:
        return Decimal(normalized).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount in {path} row {row_number}: {value!r}") from exc


def parse_amex_date(value: str, *, path: Path, row_number: int) -> str:
    try:
        return datetime.strptime(value.strip(), "%d %b %Y").date().isoformat()
    except ValueError as exc:
        raise ValueError(f"Invalid Amex date in {path} row {row_number}: {value!r}") from exc


def parse_iso_date(value: str, *, path: Path, row_number: int) -> str:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date in {path} row {row_number}: {value!r}") from exc


def iter_amex_transactions(card_dir: Path) -> list[Transaction]:
    transactions: list[Transaction] = []
    card = card_dir.name

    for path in sorted(card_dir.glob("*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row_number, row in enumerate(reader, start=2):
                merchant = (row.get("Merchant") or row.get("Description") or "").strip()
                transactions.append(
                    Transaction(
                        transaction_date=parse_amex_date(
                            row["Date"], path=path, row_number=row_number
                        ),
                        card=card,
                        merchant=merchant,
                        amount_cad=parse_amount(
                            row["Amount"], path=path, row_number=row_number
                        ),
                    )
                )

    return transactions


def iter_cibc_transactions(card_dir: Path) -> list[Transaction]:
    transactions: list[Transaction] = []
    card = card_dir.name

    for path in sorted(card_dir.glob("*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            for row_number, row in enumerate(reader, start=1):
                if len(row) != 5:
                    raise ValueError(f"Expected 5 CIBC columns in {path} row {row_number}")

                date_text, merchant, debit, credit, _masked_card = row
                debit = debit.strip()
                credit = credit.strip()

                if bool(debit) == bool(credit):
                    raise ValueError(
                        f"Expected exactly one of debit/credit in {path} row {row_number}"
                    )

                amount = parse_amount(
                    debit or credit, path=path, row_number=row_number
                )
                if credit:
                    amount = -amount

                transactions.append(
                    Transaction(
                        transaction_date=parse_iso_date(
                            date_text, path=path, row_number=row_number
                        ),
                        card=card,
                        merchant=merchant.strip(),
                        amount_cad=amount,
                    )
                )

    return transactions


def load_transactions() -> list[Transaction]:
    transactions: list[Transaction] = []

    for card_dir in sorted(RAW_DIR.iterdir()):
        if not card_dir.is_dir():
            continue
        if card_dir.name.startswith("amex-"):
            transactions.extend(iter_amex_transactions(card_dir))
        elif card_dir.name.startswith("cibc-"):
            transactions.extend(iter_cibc_transactions(card_dir))
        else:
            raise ValueError(f"Unsupported card directory: {card_dir}")

    return transactions


def write_yearly_csvs(transactions: list[Transaction]) -> dict[str, int]:
    OUTPUT_DIR.mkdir(exist_ok=True)

    by_year: dict[str, list[Transaction]] = defaultdict(list)
    for transaction in transactions:
        by_year[transaction.transaction_date[:4]].append(transaction)

    row_counts: dict[str, int] = {}
    for year, rows in sorted(by_year.items()):
        rows.sort(
            key=lambda item: (
                item.transaction_date,
                item.card,
                item.merchant,
                item.amount_cad,
            )
        )
        output_path = OUTPUT_DIR / f"transactions-{year}.csv"
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(row.as_csv_row() for row in rows)
        row_counts[year] = len(rows)

    return row_counts


def main() -> None:
    row_counts = write_yearly_csvs(load_transactions())
    for year, count in sorted(row_counts.items()):
        print(f"wrote {OUTPUT_DIR / f'transactions-{year}.csv'} ({count} rows)")


if __name__ == "__main__":
    main()
