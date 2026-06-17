import pandas as pd
import random

print("\nAccounting Assistant Dataset Generator - Day 15")

records = []

categories = {
    "Payroll": [
        "Salary paid to employees",
        "Monthly payroll payment",
        "Employee salary transfer",
        "Staff salary paid",
        "Payroll expense booked"
    ],
    "Rent": [
        "Office rent paid",
        "Monthly rent transferred",
        "Building rent payment",
        "Warehouse rent paid",
        "Rent expense booked"
    ],
    "GST": [
        "GST deposited",
        "GST payment made",
        "GST liability paid",
        "GST tax deposited",
        "GST challan payment"
    ],
    "Asset": [
        "Laptop purchased",
        "Computer equipment purchased",
        "Office furniture purchased",
        "Printer purchased",
        "Vehicle purchased"
    ],
    "Utilities": [
        "Electricity bill paid",
        "Internet bill paid",
        "Water bill paid",
        "Telephone bill paid",
        "Utility expense paid"
    ],
    "Marketing": [
        "Facebook advertisement expense",
        "Google advertisement expense",
        "Marketing campaign expense",
        "Promotional expense paid",
        "Advertising charges paid"
    ],
    "Revenue": [
        "Customer payment received",
        "Sales collection received",
        "Revenue received from client",
        "Customer receipt recorded",
        "Sales income received"
    ],
    "Bank Charges": [
        "Bank charges deducted",
        "Bank service fee charged",
        "Processing charges deducted",
        "Bank commission charged",
        "Transaction charges deducted"
    ],
    "Loan": [
        "Loan EMI paid",
        "Loan repayment made",
        "Bank loan installment paid",
        "Term loan payment made",
        "Loan principal paid"
    ],
    "Insurance": [
        "Insurance premium paid",
        "Vehicle insurance paid",
        "Health insurance premium",
        "Business insurance paid",
        "Insurance renewal paid"
    ],
    "Professional Fees": [
        "Consultancy fees paid",
        "CA fees paid",
        "Legal fees paid",
        "Audit fees paid",
        "Professional charges paid"
    ],
    "Travel": [
        "Flight ticket booked",
        "Taxi fare paid",
        "Hotel expense paid",
        "Travel reimbursement paid",
        "Business travel expense"
    ]
}

ledger_mapping = {
    "Payroll": "Salary Expense",
    "Rent": "Rent Expense",
    "GST": "GST Payable",
    "Asset": "Fixed Assets",
    "Utilities": "Utilities Expense",
    "Marketing": "Advertisement Expense",
    "Revenue": "Sales Revenue",
    "Bank Charges": "Bank Charges Expense",
    "Loan": "Loan Payable",
    "Insurance": "Insurance Expense",
    "Professional Fees": "Professional Fees Expense",
    "Travel": "Travel Expense"
}

statement_mapping = {
    "Payroll": "Expense",
    "Rent": "Expense",
    "GST": "Liability",
    "Asset": "Asset",
    "Utilities": "Expense",
    "Marketing": "Expense",
    "Revenue": "Income",
    "Bank Charges": "Expense",
    "Loan": "Liability",
    "Insurance": "Expense",
    "Professional Fees": "Expense",
    "Travel": "Expense"
}

journal_mapping = {
    "Payroll": "Salary Expense Dr | To Bank",
    "Rent": "Rent Expense Dr | To Bank",
    "GST": "GST Payable Dr | To Bank",
    "Asset": "Fixed Asset Dr | To Bank",
    "Utilities": "Utilities Expense Dr | To Bank",
    "Marketing": "Advertisement Expense Dr | To Bank",
    "Revenue": "Bank Dr | To Sales Revenue",
    "Bank Charges": "Bank Charges Expense Dr | To Bank",
    "Loan": "Loan Payable Dr | To Bank",
    "Insurance": "Insurance Expense Dr | To Bank",
    "Professional Fees": "Professional Fees Expense Dr | To Bank",
    "Travel": "Travel Expense Dr | To Bank"
}

for _ in range(5200):
    category = random.choice(list(categories.keys()))
    transaction = random.choice(categories[category])
    amount = random.randint(1000, 500000)
    
    records.append({
        "Transaction_Text": transaction,
        "Amount": amount,
        "Category": category,
        "Ledger": ledger_mapping[category],
        "Journal_Entry": journal_mapping[category],
        "Financial_Statement": statement_mapping[category]
    })

df = pd.DataFrame(records)
print("\nDataset Preview:")
print(df.head())
print("\nTotal Records:", len(df))

df.to_csv("accounting-assistant/datasets/accounting_assistant_5200.csv", index=False)
print("\nDataset Saved Successfully!")
