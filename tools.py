"""
tools.py

Business logic layer for the AI Expense Manager.

Responsibilities
----------------
- Validate user input
- Call the JSON store
- Format responses
- Provide tool registry
- Execute tools requested by the LLM

Author : Balaganesh
"""

from __future__ import annotations

import inspect
import json
from datetime import datetime, timedelta
from typing import Any, Callable, Dict

from config import DEFAULT_CATEGORIES, logger
from store import JSONStore

# -------------------------------------------------------
# Initialize Store
# -------------------------------------------------------

store = JSONStore()


# -------------------------------------------------------
# Validation Helpers
# -------------------------------------------------------

def validate_category(category: str) -> str:
    """
    Ensure category exists.
    """

    category = category.strip().title()

    if category not in DEFAULT_CATEGORIES:
        raise ValueError(
            f"Invalid category '{category}'. "
            f"Allowed categories: {', '.join(DEFAULT_CATEGORIES)}"
        )

    return category


def validate_amount(amount: float) -> float:
    """
    Validate amount.
    """

    amount = float(amount)

    if amount <= 0:
        raise ValueError(
            "Expense amount must be greater than zero."
        )

    return amount


def validate_date(date: str) -> str:
    """
    Validate ISO date or recognize simple natural language dates.
    """

    normalized = date.strip().lower()

    if normalized == "today":
        return datetime.now().strftime("%Y-%m-%d")

    if normalized == "yesterday":
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    if normalized == "tomorrow":
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    if "t" in date:
        date = date.split("t", 1)[0]

    try:
        parsed_date = datetime.strptime(date.strip(), "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            "Date must be in YYYY-MM-DD format or a supported keyword like 'today', 'yesterday', or 'tomorrow'."
        )

    return parsed_date.strftime("%Y-%m-%d")


# -------------------------------------------------------
# Expense Tools
# -------------------------------------------------------

def add_expense(
    title: str,
    amount: float,
    category: str,
    date: str,
    notes: str = "",
):
    """
    Add a new expense.
    """

    amount = validate_amount(amount)
    category = validate_category(category)
    date = validate_date(date)

    expense = store.add_expense(
        title=title,
        amount=amount,
        category=category,
        date=date,
        notes=notes,
    )

    logger.info("Added expense %s", expense["id"])

    return {
        "success": True,
        "message": "Expense added successfully.",
        "expense": expense,
    }


def list_expenses():
    """
    Return all expenses.
    """

    expenses = store.list_expenses()

    return {
        "count": len(expenses),
        "expenses": expenses,
    }


def delete_expense(expense_id: int):
    """
    Delete an expense.
    """

    deleted = store.delete_expense(expense_id)

    if deleted:
        return {
            "success": True,
            "message": f"Expense {expense_id} deleted."
        }

    return {
        "success": False,
        "message": "Expense not found."
    }


def update_expense(
    expense_id: int,
    title: str | None = None,
    amount: float | None = None,
    category: str | None = None,
    date: str | None = None,
    notes: str | None = None,
):
    """
    Update an expense.
    """

    updates = {}

    if title is not None:
        updates["title"] = title

    if amount is not None:
        updates["amount"] = validate_amount(amount)

    if category is not None:
        updates["category"] = validate_category(category)

    if date is not None:
        updates["date"] = validate_date(date)

    if notes is not None:
        updates["notes"] = notes

    updated = store.update_expense(
        expense_id,
        **updates,
    )

    return {
        "success": updated,
        "message": (
            "Expense updated."
            if updated
            else "Expense not found."
        ),
    }


def expense_summary():
    """
    Overall statistics.
    """

    expenses = store.list_expenses()

    if not expenses:
        return {
            "total": 0,
            "transactions": 0,
            "average": 0,
            "highest": 0,
        }

    total = sum(
        e["amount"]
        for e in expenses
    )

    highest = max(
        e["amount"]
        for e in expenses
    )

    average = total / len(expenses)

    return {
        "total": round(total, 2),
        "transactions": len(expenses),
        "average": round(average, 2),
        "highest": highest,
    }


def category_report():
    """
    Category wise report.
    """

    return store.category_summary()


def monthly_report():
    """
    Monthly report.
    """

    return store.monthly_summary()


def search_expenses(keyword: str):
    """
    Search expenses.
    """

    results = store.search(keyword)

    return {
        "count": len(results),
        "results": results,
    }


def highest_expense():
    """
    Highest expense.
    """

    highest = store.highest_expense()

    if highest is None:
        return {
            "message": "No expenses available."
        }

    return highest


def get_expense(expense_id: int):
    """
    Fetch single expense.
    """

    expense = store.get_expense(expense_id)

    if expense is None:
        return {
            "success": False,
            "message": "Expense not found."
        }

    return expense


def clear_database():
    """
    Delete all expenses.
    """

    store.clear_database()

    return {
        "success": True,
        "message": "Database cleared."
    }


# -------------------------------------------------------
# Tool Registry
# -------------------------------------------------------

TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {
    "add_expense": add_expense,
    "list_expenses": list_expenses,
    "delete_expense": delete_expense,
    "update_expense": update_expense,
    "expense_summary": expense_summary,
    "monthly_report": monthly_report,
    "category_report": category_report,
    "highest_expense": highest_expense,
    "search_expenses": search_expenses,
    "get_expense": get_expense,
    "clear_database": clear_database,
}


# -------------------------------------------------------
# Generic Tool Executor
# -------------------------------------------------------

def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
):
    """
    Execute any registered tool.

    Used by chat.py after the LLM
    selects a function call.
    """

    if tool_name not in TOOL_REGISTRY:
        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    if arguments is None:
        arguments = {}

    logger.info(
        "Executing tool: %s",
        tool_name,
    )

    tool_func = TOOL_REGISTRY[tool_name]

    try:
        signature = inspect.signature(tool_func)
    except (TypeError, ValueError):
        signature = None

    accepted_arguments: Dict[str, Any] = {}

    if signature is not None:
        accepts_var_kwargs = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        )

        for name, value in arguments.items():
            if name in signature.parameters or accepts_var_kwargs:
                accepted_arguments[name] = value
    else:
        accepted_arguments = arguments

    result = tool_func(
        **accepted_arguments
    )

    return result


# -------------------------------------------------------
# Helper for pretty printing
# -------------------------------------------------------

def pretty_json(data):
    """
    Nicely formatted JSON.
    """

    return json.dumps(
        data,
        indent=4,
        ensure_ascii=False,
    )


# -------------------------------------------------------
# Simple local test
# -------------------------------------------------------

if __name__ == "__main__":

    print(
        pretty_json(
            expense_summary()
        )
    )