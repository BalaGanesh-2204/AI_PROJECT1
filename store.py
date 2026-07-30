"""
store.py

Handles all JSON persistence.

This module acts as a tiny database layer.

Author : Balaganesh
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional

from config import (
    EXPENSE_FILE,
    CATEGORY_FILE,
    DEFAULT_CATEGORIES,
    logger,
)


class JSONStore:
    """
    Simple JSON database.
    """

    def __init__(self):

        self._initialize_database()

    # ---------------------------------------------------------

    def _initialize_database(self):

        if not EXPENSE_FILE.exists():
            with open(EXPENSE_FILE, "w") as f:
                json.dump([], f, indent=4)

        if not CATEGORY_FILE.exists():
            with open(CATEGORY_FILE, "w") as f:
                json.dump(DEFAULT_CATEGORIES, f, indent=4)

    # ---------------------------------------------------------

    def _read(self):

        with open(EXPENSE_FILE, "r") as f:
            return json.load(f)

    # ---------------------------------------------------------

    def _write(self, data):

        with open(EXPENSE_FILE, "w") as f:
            json.dump(
                data,
                f,
                indent=4
            )

    # ---------------------------------------------------------

    def next_id(self):

        data = self._read()

        if not data:
            return 1

        return max(i["id"] for i in data) + 1

    # ---------------------------------------------------------

    def add_expense(
        self,
        title: str,
        amount: float,
        category: str,
        date: str,
        notes: str = "",
    ):

        data = self._read()

        expense = {
            "id": self.next_id(),
            "title": title,
            "amount": amount,
            "category": category,
            "date": date,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
        }

        data.append(expense)

        self._write(data)

        logger.info("Expense Added")

        return expense

    # ---------------------------------------------------------

    def list_expenses(self):

        return self._read()

    # ---------------------------------------------------------

    def delete_expense(self, expense_id: int):

        data = self._read()

        updated = [
            x for x in data
            if x["id"] != expense_id
        ]

        self._write(updated)

        logger.info("Expense Deleted")

        return len(updated) != len(data)

    # ---------------------------------------------------------

    def update_expense(
        self,
        expense_id: int,
        **kwargs,
    ):

        data = self._read()

        updated = False

        for expense in data:

            if expense["id"] == expense_id:

                for key, value in kwargs.items():

                    if value is not None:
                        expense[key] = value

                updated = True

                break

        self._write(data)

        return updated

    # ---------------------------------------------------------

    def get_expense(
        self,
        expense_id: int,
    ) -> Optional[Dict]:

        data = self._read()

        for expense in data:

            if expense["id"] == expense_id:
                return expense

        return None

    # ---------------------------------------------------------

    def total_expense(self):

        return sum(
            x["amount"]
            for x in self._read()
        )

    # ---------------------------------------------------------

    def highest_expense(self):

        expenses = self._read()

        if not expenses:
            return None

        return max(
            expenses,
            key=lambda x: x["amount"]
        )

    # ---------------------------------------------------------

    def category_summary(self):

        result = {}

        for expense in self._read():

            category = expense["category"]

            result.setdefault(category, 0)

            result[category] += expense["amount"]

        return result

    # ---------------------------------------------------------

    def monthly_summary(self):

        result = {}

        for expense in self._read():

            month = expense["date"][:7]

            result.setdefault(month, 0)

            result[month] += expense["amount"]

        return result

    # ---------------------------------------------------------

    def search(
        self,
        keyword: str,
    ) -> List[Dict]:

        keyword = keyword.lower()

        results = []

        for expense in self._read():

            title = expense["title"].lower()

            notes = expense.get(
                "notes",
                ""
            ).lower()

            if keyword in title or keyword in notes:
                results.append(expense)

        return results

    # ---------------------------------------------------------

    def clear_database(self):

        self._write([])

        logger.warning("Database cleared.")