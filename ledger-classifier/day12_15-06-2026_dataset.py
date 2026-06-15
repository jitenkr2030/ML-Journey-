import pandas as pd
import random

print("\nGenerating Ledger Classification Dataset...")

ledger_templates = {

    "Salary Expense": [
        "Salary paid to employee",
        "Monthly staff salary",
        "Wages paid to workers",
        "Security guard salary",
        "Payroll payment",
        "Employee bonus payment"
    ],

    "Rent Expense": [
        "Office rent payment",
        "Warehouse rent",
        "Shop rent paid",
        "Building lease payment",
        "Monthly office rent"
    ],

    "Utilities Expense": [
        "Electricity bill payment",
        "Water bill payment",
        "Internet bill",
        "Telephone expense",
        "Utility charges"
    ],

    "Bank Charges": [
        "Bank service charges",
        "Cheque book charges",
        "RTGS charges",
        "NEFT charges",
        "Processing fee charged by bank"
    ],

    "Professional Fees": [
        "CA consultation fees",
        "Legal advisor fees",
        "Audit fees",
        "Tax filing charges",
        "Professional consultancy fees"
    ],

    "GST Payable": [
        "GST payment challan",
        "GST liability payment",
        "GST deposited",
        "GST monthly payment",
        "GST tax paid"
    ],

    "TDS Payable": [
        "TDS payment",
        "TDS deposited",
        "TDS government payment",
        "TDS challan",
        "Monthly TDS payment"
    ],

    "Sales Revenue": [
        "Customer invoice generated",
        "Product sale",
        "Service income received",
        "Sales receipt",
        "Revenue from client"
    ],

    "Purchase Expense": [
        "Raw material purchase",
        "Inventory purchase",
        "Office supplies purchase",
        "Goods purchased",
        "Purchase invoice received"
    ],

    "Interest Income": [
        "FD interest received",
        "Bank interest income",
        "Interest credited",
        "Savings account interest",
        "Investment interest"
    ],

    "Loan Liability": [
        "Loan EMI payment",
        "Bank loan installment",
        "Loan repayment",
        "Interest on loan",
        "Business loan payment"
    ],

    "Insurance Expense": [
        "Vehicle insurance premium",
        "Health insurance premium",
        "Business insurance payment",
        "Insurance renewal",
        "Insurance expense"
    ],

    "Travel Expense": [
        "Uber ride",
        "Flight ticket",
        "Hotel accommodation",
        "Train ticket",
        "Business travel expense"
    ],

    "Marketing Expense": [
        "Facebook advertisement",
        "Google Ads payment",
        "Marketing campaign expense",
        "Promotional expense",
        "Advertisement charges"
    ],

    "Software Expense": [
        "AWS hosting charges",
        "Google Workspace subscription",
        "Microsoft 365 subscription",
        "Software license renewal",
        "Cloud hosting payment"
    ]
}

records = []

records_per_category = 150

for ledger_name, templates in ledger_templates.items():

    for _ in range(records_per_category):

        description = random.choice(templates)

        amount = random.randint(
            500,
            500000
        )

        text = f"{description} Rs {amount}"

        records.append([
            text,
            ledger_name
        ])

df = pd.DataFrame(
    records,
    columns=[
        "Transaction_Text",
        "Ledger"
    ]
)

df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

output_file = (
    "ledger-classifier/datasets/"
    "ledger_transactions_2250.csv"
)

df.to_csv(
    output_file,
    index=False
)

print("\nDataset Generated Successfully!")

print("\nTotal Records :", len(df))

print("\nCategories:")
print(
    df["Ledger"].value_counts()
)

print("\nDataset Saved To:")
print(output_file)

print("\nDay 12 Dataset Generation Completed!")
