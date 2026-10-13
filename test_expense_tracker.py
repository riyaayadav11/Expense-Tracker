import csv
import os
import tempfile
import unittest

import expense_tracker as et


class TestAddAndDelete(unittest.TestCase):
    def test_add_assigns_incrementing_ids(self):
        expenses = []
        first = et.add_expense(expenses, 100, "Food", "Lunch", "2026-10-01")
        second = et.add_expense(expenses, "50.5", "travel", "", "2026-10-02")
        self.assertEqual((first["id"], second["id"]), (1, 2))
        self.assertEqual(first["category"], "food")  # normalised to lowercase
        self.assertEqual(second["amount"], 50.5)

    def test_add_defaults_to_today(self):
        expense = et.add_expense([], 10, "misc")
        self.assertEqual(len(expense["date"]), 10)

    def test_add_rejects_bad_input(self):
        bad_cases = [
            (0, "food", "2026-10-01"),
            (-5, "food", "2026-10-01"),
            ("abc", "food", "2026-10-01"),
            ("nan", "food", "2026-10-01"),
            ("inf", "food", "2026-10-01"),
            (10, "", "2026-10-01"),
            (10, "   ", "2026-10-01"),
            (10, "food", "01-10-2026"),
            (10, "food", "2026-13-40"),
        ]
        for amount, category, day in bad_cases:
            with self.subTest(amount=amount, category=category, day=day):
                with self.assertRaises(ValueError):
                    et.add_expense([], amount, category, "", day)

    def test_id_not_reused_after_delete_of_older_item(self):
        expenses = []
        et.add_expense(expenses, 1, "a", "", "2026-10-01")
        et.add_expense(expenses, 2, "b", "", "2026-10-01")
        et.delete_expense(expenses, 1)
        third = et.add_expense(expenses, 3, "c", "", "2026-10-01")
        self.assertEqual(third["id"], 3)

    def test_delete(self):
        expenses = []
        et.add_expense(expenses, 10, "food", "", "2026-10-01")
        removed = et.delete_expense(expenses, 1)
        self.assertEqual(removed["amount"], 10)
        self.assertEqual(expenses, [])
        with self.assertRaises(ValueError):
            et.delete_expense(expenses, 1)


class TestFilterAndSummary(unittest.TestCase):
    def setUp(self):
        self.expenses = []
        et.add_expense(self.expenses, 100, "food", "a", "2026-10-05")
        et.add_expense(self.expenses, 40, "travel", "b", "2026-10-02")
        et.add_expense(self.expenses, 60, "food", "c", "2026-09-28")

    def test_filter_by_category(self):
        result = et.filter_expenses(self.expenses, category="FOOD")
        self.assertEqual([e["description"] for e in result], ["c", "a"])

    def test_filter_by_month(self):
        result = et.filter_expenses(self.expenses, month="2026-10")
        self.assertEqual([e["description"] for e in result], ["b", "a"])

    def test_filter_bad_month(self):
        with self.assertRaises(ValueError):
            et.filter_expenses(self.expenses, month="October")

    def test_summary(self):
        summary = et.summarize(self.expenses)
        self.assertEqual(summary["total"], 200)
        self.assertEqual(summary["count"], 3)
        self.assertEqual(list(summary["by_category"].items()), [("food", 160), ("travel", 40)])

    def test_summary_avoids_float_noise(self):
        expenses = []
        for _ in range(3):
            et.add_expense(expenses, 0.1, "x", "", "2026-10-01")
        self.assertEqual(et.summarize(expenses)["total"], 0.3)

    def test_empty_summary(self):
        self.assertEqual(et.summarize([])["total"], 0)
        self.assertEqual(et.format_summary(et.summarize([])), "No expenses found.")


class TestStorageAndExport(unittest.TestCase):
    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.json")
            self.assertEqual(et.load_expenses(path), [])
            expenses = []
            et.add_expense(expenses, 25, "books", "Notebook", "2026-10-03")
            et.save_expenses(path, expenses)
            self.assertEqual(et.load_expenses(path), expenses)

    def test_corrupt_file_raises(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.json")
            with open(path, "w") as file:
                file.write("{not json")
            with self.assertRaises(ValueError):
                et.load_expenses(path)

    def test_export_csv(self):
        with tempfile.TemporaryDirectory() as folder:
            out = os.path.join(folder, "out.csv")
            expenses = []
            et.add_expense(expenses, 25, "books", "Notebook, ruled", "2026-10-03")
            et.export_csv(expenses, out)
            with open(out, newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(rows[0]["description"], "Notebook, ruled")
            self.assertEqual(rows[0]["amount"], "25.0")


class TestCli(unittest.TestCase):
    def test_full_session(self):
        with tempfile.TemporaryDirectory() as folder:
            data = os.path.join(folder, "data.json")
            base = ["--file", data]
            self.assertEqual(et.main(base + ["add", "250", "food", "Lunch", "--date", "2026-10-01"]), 0)
            self.assertEqual(et.main(base + ["add", "99.5", "travel", "--date", "2026-10-02"]), 0)
            self.assertEqual(et.main(base + ["list", "--month", "2026-10"]), 0)
            self.assertEqual(et.main(base + ["summary"]), 0)
            self.assertEqual(et.main(base + ["export", os.path.join(folder, "e.csv")]), 0)
            self.assertEqual(et.main(base + ["delete", "1"]), 0)
            self.assertEqual(len(et.load_expenses(data)), 1)

    def test_errors_return_1(self):
        with tempfile.TemporaryDirectory() as folder:
            base = ["--file", os.path.join(folder, "data.json")]
            self.assertEqual(et.main(base + ["add", "-5", "food"]), 1)
            self.assertEqual(et.main(base + ["delete", "7"]), 1)
            self.assertEqual(et.main(base + ["list", "--month", "bad"]), 1)


if __name__ == "__main__":
    unittest.main()
