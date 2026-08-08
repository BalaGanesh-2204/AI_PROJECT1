<div align="center">

# 🔍 PEER REVIEW REPORT

## Week 2 Assignment

### AI Expense Manager

---

# 👨‍💻 Review of BalaGanesh's Week 2 Assignment

### Reviewed By: **Prasanth**

📅 **Review Date:** 07 August 2026

🧪 **Testing Performed:** Functional Testing • Edge Case Testing • Input Validation • Error Handling

---

<img src="https://img.shields.io/badge/Repository-Cloned-success?style=for-the-badge">
<img src="https://img.shields.io/badge/Application-Tested-success?style=for-the-badge">
<img src="https://img.shields.io/badge/Issues-10-red?style=for-the-badge">

</div>

---

# 📑 Executive Summary

I cloned the repository, installed all required dependencies, configured the environment, executed the application, and tested various scenarios including normal usage, invalid inputs, edge cases, and error handling.

---

| Test Category | Status |
|---------------|--------|
| Repository Cloned | ✅ Completed |
| Dependencies Installed | ✅ Completed |
| Application Executed | ✅ Completed |
| Functional Testing | ✅ Completed |
| Edge Case Testing | ✅ Completed |
| Error Handling Testing | ✅ Completed |
| Issues Identified | **10** |

---

# 🧪 Testing Workflow

```text
Clone Repository
        │
        ▼
Install Dependencies
        │
        ▼
Configure .env
        │
        ▼
Run Application
        │
        ▼
Functional Testing
        │
        ▼
Edge Case Testing
        │
        ▼
Error Handling Testing
        │
        ▼
Review Documentation
```

---

# 🚨 ISSUE 1

## 📌 Monthly Report Includes Expenses from Multiple Months

| Property | Details |
|----------|---------|
| 🔥 Severity | Medium |
| 📂 Module | Reporting |

### 🧪 Steps to Reproduce

```text
Show monthly report
```

### ❌ Actual Result

The monthly report includes expenses from multiple months instead of only the selected/current month.

### ✅ Expected Result

The report should display only expenses from the selected/current month.

### 🎯 Impact

Users may receive incorrect monthly financial summaries.

---

# 🚨 ISSUE 2

## 📌 Invalid Amount Input Is Not Handled Gracefully

| Property | Details |
|----------|---------|
| 🔥 Severity | High |
| 📂 Module | Input Validation |

### 🧪 Steps to Reproduce

```text
Add an expense of abc for food
```

### ❌ Actual Result

The application produces a tool validation error and internal logs.

### ✅ Expected Result

```text
Please enter a valid numeric amount.
```

### 🎯 Impact

Poor user experience and confusing error messages.

---

# 🚨 ISSUE 3

## 📌 Update Operation Does Not Handle Non-Existent Expenses Correctly

| Property | Details |
|----------|---------|
| 🔥 Severity | High |
| 📂 Module | Update Expense |

### 🧪 Steps to Reproduce

```text
Update expense 999 amount to 500
```

### ❌ Actual Result

The application attempts an incorrect update workflow instead of reporting that the expense does not exist.

### ✅ Expected Result

```text
Expense ID 999 not found.
```

### 🎯 Impact

Can lead to unexpected behavior and confusion.

---

# 🚨 ISSUE 4

## 📌 Update Recreates the Expense Instead of Modifying It

| Property | Details |
|----------|---------|
| 🔥 Severity | High |
| 📂 Module | Update Expense |

### 🧪 Steps to Reproduce

```text
Update expense 1 amount to 500
```

### ❌ Actual Result

The application deletes the existing expense and creates a new record.

### ✅ Expected Result

Modify the existing expense while preserving its original ID and metadata.

### 🎯 Impact

May lose important metadata and affect data consistency.

---

# 🚨 ISSUE 5

## 📌 Clear Database Deletes All Records Without Confirmation

| Property | Details |
|----------|---------|
| 🔥 Severity | Medium |
| 📂 Module | Database |

### 🧪 Steps to Reproduce

```text
Clear database
```

### ❌ Actual Result

All expenses are deleted immediately.

### ✅ Expected Result

Ask the user for confirmation before deleting all records.

### 🎯 Impact

Accidental data loss is possible.

---

# 🚨 ISSUE 6

## 📌 Application Crashes During Rate-Limit Recovery

| Property | Details |
|----------|---------|
| 🔥 Severity | Critical |
| 📂 Module | API Handling |

### 🧪 Steps to Reproduce

Send multiple requests until the Groq API returns **429 (Rate Limit)**.

### ❌ Actual Result

The application terminates unexpectedly.

### ✅ Expected Result

Gracefully handle the rate limit and allow the application to continue running.

### 🎯 Impact

Reduces application reliability.

---

# 🚨 ISSUE 7

## 📌 Missing Method Causes Runtime Error

| Property | Details |
|----------|---------|
| 🔥 Severity | Critical |
| 📂 Module | Exception Handling |

### 🧪 Steps to Reproduce

Trigger the rate-limit recovery flow.

### ❌ Actual Result

```text
AttributeError:
_build_rate_limit_after_tools_message
```

### ✅ Expected Result

The method should exist or the exception should be handled properly.

### 🎯 Impact

Causes the application to crash.

---

# 🚨 ISSUE 8

## 📌 Duplicate Expenses Can Be Added

| Property | Details |
|----------|---------|
| 🔥 Severity | Medium |
| 📂 Module | Expense Management |

### 🧪 Steps to Reproduce

```text
Add an expense of 250 for food

Add an expense of 250 for food
```

### ❌ Actual Result

Multiple identical expense records are created.

### ✅ Expected Result

The application should detect possible duplicates and ask the user whether they want to continue.

### 🎯 Impact

May lead to duplicate records and inaccurate reports.

---

# 🚨 ISSUE 9

## 📌 Internal Debug Logs Are Visible to End Users

| Property | Details |
|----------|---------|
| 🔥 Severity | Low |
| 📂 Module | User Interface |

### 🧪 Steps to Reproduce

```text
Show monthly report
```

### ❌ Actual Result

The application displays HTTP requests, retry messages, tool execution logs, and other internal debugging information.

### ✅ Expected Result

Only user-friendly messages should be displayed. Internal logs should be available only in debug mode.

### 🎯 Impact

Reduces usability and exposes implementation details.

---

# 🚨 ISSUE 10

## 📌 No Confirmation Before Deleting an Expense

| Property | Details |
|----------|---------|
| 🔥 Severity | Medium |
| 📂 Module | Delete Expense |

### 🧪 Steps to Reproduce

```text
Delete expense 2
```

### ❌ Actual Result

The expense is deleted immediately.

### ✅ Expected Result

Ask the user to confirm before permanently deleting the expense.

### 🎯 Impact

Accidental deletions cannot be prevented.

---

<div align="center">

# 📊 Review Summary

| Category | Status |
|----------|--------|
| Total Issues Found | **10** |
| Critical Issues | **2** |
| High Severity | **3** |
| Medium Severity | **4** |
| Low Severity | **1** |

---

# ⭐ Strengths Observed

✅ Well-organized project structure

✅ Good separation of responsibilities

✅ Clean Tool Calling implementation

✅ Conversation memory works correctly

✅ Modular and readable code

✅ Core expense management functionality works as expected

---

# 📝 Final Verdict

The project is well structured and demonstrates a good implementation of an AI-powered Expense Manager. The core features work correctly under normal usage. The issues identified mainly relate to input validation, error handling, user experience, and data management. Addressing these issues would improve the application's robustness, reliability, and overall usability.

---

### 👨‍💻 Reviewed By

# **Prasanth**

**Week 3 Peer Review Assignment**

</div>