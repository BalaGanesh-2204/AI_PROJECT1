# 💰 AI Expense Manager

A production-ready AI-powered Expense Manager built using **Python**, **Groq**, and **Tool Calling**.

The assistant understands natural language and manages expenses through JSON storage.

---

# Features

- AI Agent powered by Groq
- Tool Calling
- JSON Database
- Streaming Responses
- Expense CRUD
- Monthly Reports
- Category Reports
- Search Expenses
- Running Token Usage
- Conversation Memory
- Production Ready Architecture

---

# Project Structure

expense-manager-ai/

```
config.py
chat.py
tools.py
store.py
main.py

data/
    expenses.json
    categories.json

requirements.txt
.env
README.md
```

---

# Installation

Clone repository

```bash
git clone https://github.com/yourusername/expense-manager-ai.git

cd expense-manager-ai
```

Create virtual environment

```bash
python -m venv .venv
```

Activate

Windows

```bash
.venv\Scripts\activate
```

Linux/Mac

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Configure API Key

Create

```
.env
```

Add

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxx
```

---

# Run

```bash
python main.py
```

---

# Example Commands

```
Add ₹250 Food expense today.

Show all expenses.

Delete expense 3.

Update expense 5 amount to 650.

Show monthly report.

Show category summary.

What is my highest expense?

Search coffee.

Clear database.
```

---

# Project Layers

```
main.py

↓

chat.py

↓

tools.py

↓

store.py

↓

JSON Database
```

---

# Tool Calling

The LLM never directly modifies data.

Instead it calls

- add_expense
- update_expense
- delete_expense
- list_expenses
- expense_summary
- monthly_report
- category_report
- search_expenses
- highest_expense

---

# Future Improvements

- SQLite Backend
- PostgreSQL
- User Authentication
- FastAPI REST API
- Voice Commands
- OCR Receipt Scanner
- Expense Prediction
- Budget Alerts
- CSV Export
- Charts
- Dashboard
- Multi-user Support

---

# License

MIT