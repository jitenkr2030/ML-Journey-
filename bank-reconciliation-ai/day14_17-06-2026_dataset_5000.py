import pandas as pd
import random
from datetime import datetime, timedelta

print("Generating 5000 Bank Reconciliation Records...")

book_descriptions = [
    "Salary Payment",
    "Office Rent",
    "Electricity Bill",
    "Internet Expense",
    "GST Payment",
    "Vendor Payment",
    "Customer Receipt",
    "Bank Charges",
    "Loan EMI",
    "Insurance Premium",
    "Fuel Expense",
    "Travel Expense",
    "Software Subscription",
    "Professional Fees",
    "Advertising Expense"
]

bank_descriptions = [
    "NEFT Salary Transfer",
    "Rent Transfer",
    "Electricity Payment",
    "Internet Payment",
    "GST Challan",
    "Vendor Transfer",
    "Customer Credit",
    "Bank Service Charge",
    "EMI Debit",
    "Insurance Debit",
    "Fuel Card Payment",
    "Travel Reimbursement",
    "Software Auto Debit",
    "Consultancy Payment",
    "Marketing Expense"
]

statuses = [
    "Matched",
    "Probable Match",
    "Date Difference",
    "Reference Mismatch",
    "Cheque Mismatch",
    "Amount Mismatch",
    "Unmatched"
]

records = []

base_date = datetime(2026, 1, 1)

for i in range(5000):

    idx = random.randint(0, len(book_descriptions) - 1)

    book_desc = book_descriptions[idx]
    bank_desc = bank_descriptions[idx]

    amount = random.randint(1000, 500000)

    txn_date = (
        base_date +
        timedelta(days=random.randint(0, 180))
    )

    reference_number = (
        "REF" +
        str(random.randint(100000, 999999))
    )

    cheque_number = random.choice([
        "NA",
        f"CHQ{random.randint(1000,9999)}"
    ])

    status = random.choices(
        statuses,
        weights=[70, 10, 5, 5, 3, 4, 3],
        k=1
    )[0]

    bank_amount = amount
    bank_reference = reference_number
    bank_cheque = cheque_number
    bank_date = txn_date

    if status == "Amount Mismatch":
        bank_amount += random.randint(
            100,
            5000
        )

    elif status == "Reference Mismatch":
        bank_reference = (
            "REF" +
            str(
                random.randint(
                    100000,
                    999999
                )
            )
        )

    elif status == "Cheque Mismatch":
        bank_cheque = (
            "CHQ" +
            str(
                random.randint(
                    1000,
                    9999
                )
            )
        )

    elif status == "Date Difference":
        bank_date = (
            txn_date +
            timedelta(
                days=random.randint(
                    5,
                    20
                )
            )
        )

    records.append({

        "Book_Description":
        book_desc,

        "Bank_Description":
        bank_desc,

        "Book_Amount":
        amount,

        "Bank_Amount":
        bank_amount,

        "Book_Date":
        txn_date.strftime(
            "%Y-%m-%d"
        ),

        "Bank_Date":
        bank_date.strftime(
            "%Y-%m-%d"
        ),

        "Book_Reference":
        reference_number,

        "Bank_Reference":
        bank_reference,

        "Book_Cheque":
        cheque_number,

        "Bank_Cheque":
        bank_cheque,

        "Status":
        status
    })

df = pd.DataFrame(records)

output_file = (
    "bank-reconciliation-ai/datasets/"
    "bank_reconciliation_5000.csv"
)

df.to_csv(
    output_file,
    index=False
)

print("\nDataset Created Successfully!")
print("Total Records :", len(df))
print("File :", output_file)

print("\nStatus Distribution:")
print(
    df["Status"].value_counts()
)

print("\nSample Records:")
print(df.head())
