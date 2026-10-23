"""Expense Tracker.

A lightweight command-line tool for logging your daily spending and checking where your money goes.
Everything is saved in a local JSON file (`expenses.json` by default), so there's no database or setup.

Usage:
    python expense_tracker.py add 250 food "Lunch with friends"
    python expense_tracker.py list
    python expense_tracker.py list --category food --month 2026-10
    python expense_tracker.py summary --month 2026-10
    python expense_tracker.py delete 3
    python expense_tracker.py export my_expenses.csv
"""

import argparse
import csv
import json
import math
import os
import sys
from datetime import date, datetime

DEFAULT_FILE = "expenses.json"
DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"


# ---------- Storage ----------

def load_expenses(path: str) -> list:
    """Load expenses from a JSON file. Returns an empty list if it doesn't exist."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        raise ValueError(f"{path} is not valid JSON. Fix or delete the file.")
    if not isinstance(data, list):
        raise ValueError(f"{path} has an unexpected format.")
    return data


def save_expenses(path: str, expenses: list) -> None:
    """Save expenses to a JSON file."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(expenses, file, indent=2)


# ---------- Validation helpers ----------

def parse_amount(value) -> float:
    """Convert a value to a positive amount rounded to 2 decimals."""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"invalid amount: {value!r}")
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("amount must be a positive number")
    return round(amount, 2)


def parse_date(value: str) -> str:
    """Validate a YYYY-MM-DD date string and return it."""
    try:
        datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValueError(f"invalid date {value!r}, use YYYY-MM-DD")
    return value


def parse_month(value: str) -> str:
    """Validate a YYYY-MM month string and return it."""
    try:
        datetime.strptime(value, MONTH_FORMAT)
    except (TypeError, ValueError):
        raise ValueError(f"invalid month {value!r}, use YYYY-MM")
    return value


# ---------- Core operations ----------

def add_expense(expenses, amount, category, description="", on_date=None) -> dict:
    """Add a new expense to the list and return it."""
    category = (category or "").strip().lower()
    if not category:
        raise ValueError("category cannot be empty")

    expense = {
        "id": max((e["id"] for e in expenses), default=0) + 1,
        "date": parse_date(on_date) if on_date else date.today().strftime(DATE_FORMAT),
        "amount": parse_amount(amount),
        "category": category,
        "description": (description or "").strip(),
    }
    expenses.append(expense)
    return expense


def delete_expense(expenses, expense_id: int) -> dict:
    """Remove the expense with the given id and return it."""
    for index, expense in enumerate(expenses):
        if expense["id"] == expense_id:
            return expenses.pop(index)
    raise ValueError(f"no expense with id {expense_id}")


def filter_expenses(expenses, category=None, month=None) -> list:
    """Return expenses matching an optional category and/or YYYY-MM month."""
    result = expenses
    if category:
        result = [e for e in result if e["category"] == category.strip().lower()]
    if month:
        month = parse_month(month)
        result = [e for e in result if e["date"].startswith(month)]
    return sorted(result, key=lambda e: (e["date"], e["id"]))


def summarize(expenses) -> dict:
    """Return the total and per-category totals (largest first)."""
    by_category = {}
    for expense in expenses:
        by_category[expense["category"]] = (
            by_category.get(expense["category"], 0) + expense["amount"]
        )
    by_category = {
        name: round(total, 2)
        for name, total in sorted(by_category.items(), key=lambda item: -item[1])
    }
    return {
        "total": round(sum(by_category.values()), 2),
        "count": len(expenses),
        "by_category": by_category,
    }


def export_csv(expenses, path: str) -> None:
    """Write expenses to a CSV file."""
    fields = ["id", "date", "amount", "category", "description"]
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(expenses)


# ---------- Output formatting ----------

def format_table(expenses) -> str:
    """Format expenses as a plain-text table."""
    if not expenses:
        return "No expenses found."
    lines = [f"{'ID':<4} {'Date':<10} {'Amount':>10}  {'Category':<12} Description"]
    lines.append("-" * 60)
    for e in expenses:
        lines.append(
            f"{e['id']:<4} {e['date']:<10} {e['amount']:>10.2f}  "
            f"{e['category']:<12} {e['description']}"
        )
    return "\n".join(lines)


def format_summary(summary) -> str:
    """Format a summary dict as text."""
    if summary["count"] == 0:
        return "No expenses found."
    lines = [f"Total spent: {summary['total']:.2f} ({summary['count']} expenses)", ""]
    for name, total in summary["by_category"].items():
        share = total / summary["total"] * 100
        lines.append(f"  {name:<12} {total:>10.2f}  {share:5.1f}%")
    return "\n".join(lines)


# ---------- Command line ----------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track your daily expenses.")
    parser.add_argument(
        "--file", default=DEFAULT_FILE, help=f"data file (default: {DEFAULT_FILE})"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add an expense")
    add.add_argument("amount", help="amount spent, e.g. 250 or 99.50")
    add.add_argument("category", help="category, e.g. food, travel, books")
    add.add_argument("description", nargs="?", default="", help="optional note")
    add.add_argument("--date", help="date as YYYY-MM-DD (default: today)")

    lst = sub.add_parser("list", help="list expenses")
    lst.add_argument("--category", help="only this category")
    lst.add_argument("--month", help="only this month, as YYYY-MM")

    summary = sub.add_parser("summary", help="show totals by category")
    summary.add_argument("--month", help="only this month, as YYYY-MM")

    delete = sub.add_parser("delete", help="delete an expense by id")
    delete.add_argument("id", type=int, help="id shown in the list")

    export = sub.add_parser("export", help="export all expenses to a CSV file")
    export.add_argument("output", help="CSV file to write, e.g. expenses.csv")

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    try:
        expenses = load_expenses(args.file)

        if args.command == "add":
            expense = add_expense(
                expenses, args.amount, args.category, args.description, args.date
            )
            save_expenses(args.file, expenses)
            print(
                f"Added #{expense['id']}: {expense['amount']:.2f} "
                f"on {expense['category']} ({expense['date']})"
            )

        elif args.command == "list":
            print(format_table(filter_expenses(expenses, args.category, args.month)))

        elif args.command == "summary":
            print(format_summary(summarize(filter_expenses(expenses, month=args.month))))

        elif args.command == "delete":
            removed = delete_expense(expenses, args.id)
            save_expenses(args.file, expenses)
            print(f"Deleted #{removed['id']}: {removed['amount']:.2f} on {removed['category']}")

        elif args.command == "export":
            export_csv(filter_expenses(expenses), args.output)
            print(f"Exported {len(expenses)} expenses to {args.output}")

    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
