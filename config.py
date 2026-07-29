"""
config.py

Central configuration for the AI Expense Manager.

Everything configurable in the project should live here.

Author : Balaganesh
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field

# ------------------------------------------------------------------
# Load Environment
# ------------------------------------------------------------------

load_dotenv()

# ------------------------------------------------------------------
# Project Paths
# ------------------------------------------------------------------

ROOT_DIR = Path(__file__).parent

DATA_DIR = ROOT_DIR / "data"

EXPENSE_FILE = DATA_DIR / "expenses.json"

CATEGORY_FILE = DATA_DIR / "categories.json"

LOG_DIR = ROOT_DIR / "logs"

LOG_FILE = LOG_DIR / "expense_manager.log"

DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ],
)

logger = logging.getLogger("ExpenseManager")

# ------------------------------------------------------------------
# Groq Configuration
# ------------------------------------------------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found in .env file."
    )

MODEL_NAME = "llama-3.3-70b-versatile"

TEMPERATURE = 0.2

MAX_TOKENS = 1024

SYSTEM_PROMPT = """
You are an AI Expense Manager.

Your responsibilities are:

1. Manage expenses.
2. Understand user requests.
3. Call tools whenever necessary.
4. Never make up expense information.
5. Always use the available tools.
6. Keep answers concise.
"""

client = Groq(
    api_key=GROQ_API_KEY
)

# ------------------------------------------------------------------
# Expense Categories
# ------------------------------------------------------------------

DEFAULT_CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Travel",
    "Entertainment",
    "Medical",
    "Education",
    "Investment",
    "Others",
]

# ------------------------------------------------------------------
# Pydantic Models
# ------------------------------------------------------------------

ExpenseCategory = Literal[
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Travel",
    "Entertainment",
    "Medical",
    "Education",
    "Investment",
    "Others",
]


class Expense(BaseModel):
    id: int

    title: str = Field(
        min_length=1,
        max_length=100
    )

    amount: float = Field(
        gt=0
    )

    category: ExpenseCategory

    date: str

    notes: str = ""


class ExpenseSummary(BaseModel):

    total_expense: float

    total_transactions: int

    highest_expense: float

    average_expense: float


class MonthlyReport(BaseModel):

    month: str

    total: float

    transactions: int


# ------------------------------------------------------------------
# Tool Definitions
# ------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_expense",
            "description": "Add a new expense.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string"
                    },
                    "amount": {
                        "type": "number"
                    },
                    "category": {
                        "type": "string"
                    },
                    "date": {
                        "type": "string"
                    },
                    "notes": {
                        "type": "string"
                    }
                },
                "required": [
                    "title",
                    "amount",
                    "category",
                    "date"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_expenses",
            "description": "List every stored expense.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_expense",
            "description": "Delete an expense.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_id": {
                        "type": "integer"
                    }
                },
                "required": [
                    "expense_id"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "expense_summary",
            "description": "Generate summary of expenses.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]