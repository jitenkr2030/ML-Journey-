import pandas as pd
import random
import os

# =====================================
# JOURNAL ENTRY DATASET GENERATOR
# DAY 13
# =====================================

transactions = {

    "Salary Payment": (
        [
            "Salary paid to employees",
            "Monthly payroll processed",
            "Salary transfer through bank",
            "Employee wages paid",
            "Payroll expense booked"
        ],
        "Salary Expense",
        "Bank"
    ),

    "Office Rent": (
        [
            "Office rent paid",
            "Monthly building rent",
            "Commercial rent transfer",
            "Office premises rent paid",
            "Rent payment through bank"
        ],
        "Rent Expense",
        "Bank"
    ),

    "Electricity Bill": (
        [
            "Electricity bill paid",
            "Power bill payment",
            "Electric utility charges",
            "Electricity charges settled",
            "Monthly power expense"
        ],
        "Electricity Expense",
        "Bank"
    ),

    "Internet Expense": (
        [
            "Internet bill paid",
            "Broadband charges",
            "WiFi subscription payment",
            "Internet service charges",
            "Network expense paid"
        ],
        "Internet Expense",
        "Bank"
    ),

    "Laptop Purchase": (
        [
            "Laptop purchased",
            "Computer equipment acquired",
            "Office laptop bought",
            "New workstation purchased",
            "IT equipment purchased"
        ],
        "Computer Asset",
        "Bank"
    ),

    "GST Payment": (
        [
            "GST paid to government",
            "GST challan payment",
            "GST liability settled",
            "Tax payment made",
            "GST deposited"
        ],
        "GST Payable",
        "Bank"
    ),

    "Loan Repayment": (
        [
            "Loan EMI paid",
            "Loan installment paid",
            "Bank loan repayment",
            "Loan principal paid",
            "EMI transferred"
        ],
        "Loan Payable",
        "Bank"
    ),

    "Customer Receipt": (
        [
            "Customer payment received",
            "Invoice amount received",
            "Client payment credited",
            "Sales receipt received",
            "Payment collected from customer"
        ],
        "Bank",
        "Accounts Receivable"
    ),

    "Sales Invoice": (
        [
            "Product sold to customer",
            "Sales invoice generated",
            "Goods sold",
            "Customer billing completed",
            "Sales transaction recorded"
        ],
        "Accounts Receivable",
        "Sales Revenue"
    ),

    "Vendor Payment": (
        [
            "Vendor payment made",
            "Supplier invoice paid",
            "Outstanding payable cleared",
            "Vendor settlement completed",
            "Payment released to supplier"
        ],
        "Accounts Payable",
        "Bank"
    )
}

rows = []

records_per_category = 200

for category, values in transactions.items():

    descriptions = values[0]
    debit_account = values[1]
    credit_account = values[2]

    for _ in range(records_per_category):

        amount = random.randint(1000, 500000)

        rows.append({
            "Transaction_Text": random.choice(descriptions),
            "Amount": amount,
            "Debit_Account": debit_account,
            "Credit_Account": credit_account,
            "Transaction_Type": category
        })

df = pd.DataFrame(rows)

os.makedirs(
    "journal-entry-ai/datasets",
    exist_ok=True
)

file_path = (
    "journal-entry-ai/datasets/"
    "journal_entries_2000.csv"
)

df.to_csv(
    file_path,
    index=False
)

print("\nDataset Generated Successfully!")
print("Total Records :", len(df))
print("\nDataset Preview:")
print(df.head())

print("\nSaved To:")
print(file_path)
