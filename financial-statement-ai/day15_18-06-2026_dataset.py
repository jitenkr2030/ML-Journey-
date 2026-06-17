import pandas as pd
import random

print("Financial Statement AI Dataset Generator")

records = []

assets = [
    "Cash",
    "Bank Account",
    "Accounts Receivable",
    "Inventory",
    "Furniture",
    "Vehicle"
]

liabilities = [
    "Accounts Payable",
    "Bank Loan",
    "GST Payable",
    "TDS Payable"
]

income = [
    "Sales Revenue",
    "Service Revenue",
    "Consulting Income",
    "Interest Income"
]

expenses = [
    "Salary Expense",
    "Rent Expense",
    "Electricity Expense",
    "Travel Expense",
    "Office Expense",
    "Software Expense"
]

equity = [
    "Capital Account",
    "Retained Earnings"
]

for i in range(1500):
    records.append({
        "Account_Name": random.choice(assets),
        "Account_Type": "Asset",
        "Debit": random.randint(5000, 500000),
        "Credit": 0
    })

for i in range(1000):
    records.append({
        "Account_Name": random.choice(liabilities),
        "Account_Type": "Liability",
        "Debit": 0,
        "Credit": random.randint(5000, 500000)
    })

for i in range(1000):
    records.append({
        "Account_Name": random.choice(income),
        "Account_Type": "Income",
        "Debit": 0,
        "Credit": random.randint(10000, 1000000)
    })

for i in range(1200):
    records.append({
        "Account_Name": random.choice(expenses),
        "Account_Type": "Expense",
        "Debit": random.randint(1000, 300000),
        "Credit": 0
    })

for i in range(500):
    records.append({
        "Account_Name": random.choice(equity),
        "Account_Type": "Equity",
        "Debit": 0,
        "Credit": random.randint(10000, 2000000)
    })

df = pd.DataFrame(records)

print(df.head())
print("Total Records:", len(df))

df.to_csv(
    "financial-statement-ai/datasets/financial_statements_5200.csv",
    index=False
)

print("Dataset Saved Successfully!")
