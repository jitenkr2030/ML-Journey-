# ML Journey - Day 15

## Date

18-06-2026

## Project

Financial Statement AI + Accounting Assistant V1

---

# Goal

The goal of Day 15 was to move beyond individual accounting models and build a unified Accounting Assistant.

This day connected all previous projects into one workflow.

Instead of solving one accounting task at a time, we built a system that can process a transaction and generate:

* Category
* Ledger
* Journal Entry
* Financial Statement Group

This was the first complete Accounting AI workflow.

---

# Part 1: Financial Statement AI

We learned how accounting records are grouped into financial statement categories.

Main groups:

* Asset
* Liability
* Income
* Expense

Example:

Cash → Asset

Loan Payable → Liability

Sales Revenue → Income

Salary Expense → Expense

This helped us understand financial reporting structure.

---

# Financial Statement Dataset

Created:

```text
financial_statement_5200.csv
```

Dataset Size:

```text
5200 Records
```

Fields:

* Account_Name
* Account_Type
* Debit
* Credit

Purpose:

To train and understand how accounts affect financial statements.

---

# Part 2: Accounting Assistant V1

Today we combined all previous AI systems into one.

Architecture:

Transaction
↓
Classification
↓
Ledger
↓
Journal Entry
↓
Financial Statement

This is the foundation of a full AI Accounting Assistant.

---

# Accounting Assistant Dataset

Created:

```text
accounting_assistant_5200.csv
```

Dataset Size:

```text
5200 Records
```

Fields:

* Transaction_Text
* Amount
* Category
* Ledger
* Journal_Entry
* Financial_Statement

Categories included:

* Payroll
* Rent
* GST
* Asset
* Utilities
* Marketing
* Revenue
* Bank Charges
* Loan
* Insurance
* Professional Fees
* Travel

---

# Machine Learning Concepts Learned

## 1. Large Dataset Importance

Earlier:

16 records

Result:

0.0 Accuracy

After dataset expansion:

5200 records

Result:

Much better training quality

Lesson:

Small datasets cannot train good models.

Large structured datasets improve learning.

---

## 2. Multi-Level Accounting Prediction

One transaction can produce multiple outputs.

Example:

Input:

Salary paid to employees

Output:

Category → Payroll

Ledger → Salary Expense

Journal →

Salary Expense Dr
To Bank

Financial Statement → Expense

This is the first multi-output accounting workflow.

---

## 3. TF-IDF with N-Grams

Used:

```python
TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=5000
)
```

Benefits:

* Better word understanding
* Better phrase detection
* Better classification

Example:

salary paid

bank charges

loan emi

These are stronger than single words.

---

## 4. Stratified Train Test Split

Used:

```python
stratify=y
```

Why?

Keeps category distribution balanced.

Important for multi-class datasets.

---

## 5. Model Saving

Saved:

```text
accounting_assistant_model.pkl
accounting_assistant_vectorizer.pkl
```

Purpose:

Reusable trained model.

---

# Deployment Practiced

## CLI Application

Created:

```text
day15_18-06-2026_cli.py
```

Purpose:

User enters transaction.

System returns:

* Category
* Ledger
* Journal
* Statement

Example:

Input:

Salary paid through HDFC

Output:

Payroll
Salary Expense
Journal Entry
Expense

---

## FastAPI API

Created:

```text
day15_18-06-2026_api.py
```

API endpoint:

```text
POST /predict
```

Input:

```json
{
  "transaction": "Office rent paid"
}
```

Output:

```json
{
  "predicted_category": "Rent",
  "ledger": "Rent Expense",
  "journal_entry": "Rent Expense Dr | To Bank",
  "financial_statement_group": "Expense"
}
```

This is production-ready structure.

---

# What We Built So Far

Completed Projects:

## Stock Prediction

* Data Collection
* Model Training
* Next Day Prediction

## Expense Classification

* TF-IDF
* Naive Bayes
* API
* CLI

## GST Classification

* GST Record Classification

## Ledger Classification

* Ledger Prediction

## Journal Entry AI

* Journal Entry Prediction

## Bank Reconciliation AI

* Rule Based Matching
* ML Reconciliation

## Financial Statement AI

* Account Grouping

## Accounting Assistant V1

* End-to-End Accounting Workflow

---

# Major Understanding

Accounting itself is structured data.

That makes it highly suitable for AI.

We realized:

Transaction → Ledger → Journal → Financial Statement

is a predictable machine learning workflow.

This can automate major accounting tasks.

---

# Business Applications

Potential products:

* AI Bookkeeping Software
* AI GST Assistant
* AI Ledger Posting
* AI Journal Automation
* AI Reconciliation Software
* AI CFO Dashboard
* AI Tax Assistant

Strong accounting knowledge gives a big advantage in building these systems.

---

# Key Learning of the Day

Day 15 was the first day where all previous models connected into one unified AI system.

This is no longer a simple ML experiment.

This is the foundation of an AI Accounting Platform.

---

# Next Goal (Day 16)

Build:

TDS & INCOME TAX AI

Why
TDS/INCOME TAX is the missing core module.



# Day 15 Summary

Today we learned:

* Financial Statement Classification
* Multi-output AI workflows
* Large dataset training
* Better TF-IDF usage
* Stratified splitting
* CLI deployment
* FastAPI deployment
* End-to-end Accounting AI design

This is one of the most important days in the ML journey because it transformed separate projects into one integrated AI product.
