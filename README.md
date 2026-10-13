# Expense Tracker

A simple command-line app to record and review your daily expenses. Written in plain Python with no external packages. Your data is saved in a local JSON file.

## Features

- Add expenses with an amount, category, optional note and date
- List expenses, filtered by category and/or month
- Summary with totals per category and percentage share
- Delete a wrong entry by its ID
- Export everything to a CSV file (opens in Excel / Google Sheets)
- Input validation (rejects negative amounts, bad dates, empty categories)
- Unit tests

## Requirements

Python 3.8 or newer.

## Usage

```bash
# Add expenses (date defaults to today)
python expense_tracker.py add 250 food "Lunch with friends"
python expense_tracker.py add 1200 books "DSA textbook" --date 2026-10-05

# List expenses
python expense_tracker.py list
python expense_tracker.py list --category food
python expense_tracker.py list --month 2026-10

# See where your money goes
python expense_tracker.py summary
python expense_tracker.py summary --month 2026-10

# Delete by ID (shown in the list)
python expense_tracker.py delete 2

# Export to CSV
python expense_tracker.py export expenses.csv
```

Example output:

```
$ python expense_tracker.py summary
Total spent: 1450.00 (2 expenses)

  books           1200.00   82.8%
  food             250.00   17.2%
```

By default data is stored in `expenses.json` in the current folder. Use `--file` to pick another file:

```bash
python expense_tracker.py --file college.json add 80 travel "Bus pass"
```

## Running the tests

```bash
python -m unittest -v
```

## Project structure

```
.
├── expense_tracker.py       # app logic + CLI
├── test_expense_tracker.py  # unit tests
├── README.md
├── LICENSE
└── .gitignore
```

## Ideas for improvement

- Monthly budget limits with warnings
- Edit an existing expense
- Charts of spending over time
- A simple GUI or web version

## License

MIT. See [LICENSE](LICENSE).
