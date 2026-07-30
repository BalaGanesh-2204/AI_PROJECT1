"""
main.py

Entry point for the AI Expense Manager CLI application.

Responsibilities
----------------
- Validate project environment
- Ensure required directories/files exist
- Start the interactive chat agent
- Gracefully handle fatal errors

Author: Balaganesh
"""

from __future__ import annotations

import sys
from pathlib import Path

from config import (
    DATA_DIR,
    EXPENSE_FILE,
    CATEGORY_FILE,
    DEFAULT_CATEGORIES,
    logger,
)

from store import JSONStore
from chat import ExpenseChatAgent


# ----------------------------------------------------------
# Startup Banner
# ----------------------------------------------------------

def banner() -> None:
    print("=" * 70)
    print(" AI EXPENSE MANAGER")
    print(" Groq Powered CLI Agent")
    print("=" * 70)


# ----------------------------------------------------------
# Verify Project Files
# ----------------------------------------------------------

def verify_environment() -> None:
    """
    Ensure project folders and files exist.
    """

    DATA_DIR.mkdir(exist_ok=True)

    store = JSONStore()

    if not EXPENSE_FILE.exists():
        store.clear_database()

    if not CATEGORY_FILE.exists():
        import json

        with open(CATEGORY_FILE, "w") as f:
            json.dump(DEFAULT_CATEGORIES, f, indent=4)

    logger.info("Environment verification completed.")


# ----------------------------------------------------------
# Application
# ----------------------------------------------------------

class ExpenseManagerApplication:

    def __init__(self):

        verify_environment()

        self.agent = ExpenseChatAgent()

    def run(self):

        banner()

        print("\nType /help for available commands.\n")

        self.agent.run_cli()


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------

def main():

    try:

        app = ExpenseManagerApplication()

        app.run()

    except KeyboardInterrupt:

        print("\nApplication terminated.")

    except Exception as e:

        logger.exception(e)

        print(f"\nFatal Error: {e}")

        sys.exit(1)


if __name__ == "__main__":
    main()