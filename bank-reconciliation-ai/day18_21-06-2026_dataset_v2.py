import pandas as pd
import random
from datetime import datetime, timedelta

print("\nBank Reconciliation AI V2 Dataset Generator - Day 18")

records = []

descriptions = [

    "Salary Payment",
    "Vendor Payment",
    "Customer Receipt",
    "Bank Charges",
    "GST Payment",
    "Office Rent",
    "Fuel Expense",
    "Professional Fees",
    "Electricity Bill",
    "Software Subscription"

]

statuses = [

    "Matched",
    "Fuzzy Matched",
    "Duplicate",
    "Missing Entry",
    "Reversal Entry",
    "Suspicious"

]

# ============================================================
# DATE GENERATOR
# ============================================================

base_date = datetime(
    2026,
    6,
    1
)

# ============================================================
# GENERATE RECORDS
# ============================================================

for i in range(6000):

    book_desc = random.choice(
        descriptions
    )

    bank_desc = book_desc

    amount = random.randint(
        1000,
        100000
    )

    bank_amount = amount

    book_date = base_date + timedelta(
        days=random.randint(0, 30)
    )

    bank_date = book_date

    reference = "REF" + str(
        random.randint(10000, 99999)
    )

    bank_reference = reference

    cheque = "CHQ" + str(
        random.randint(1000, 9999)
    )

    bank_cheque = cheque

    status = random.choice(
        statuses
    )

    # ========================================================
    # STATUS LOGIC
    # ========================================================

    if status == "Fuzzy Matched":

        bank_amount = amount + random.randint(
            -10,
            10
        )

        bank_date = book_date + timedelta(
            days=random.randint(1, 3)
        )

    elif status == "Duplicate":

        bank_reference = reference
        bank_amount = amount

    elif status == "Missing Entry":

        bank_desc = "Not Available"
        bank_amount = 0
        bank_reference = "NA"
        bank_cheque = "NA"

    elif status == "Reversal Entry":

        bank_amount = -amount

    elif status == "Suspicious":

        bank_desc = "Unknown Transaction"
        bank_amount = amount * random.randint(
            2,
            5
        )

    records.append({

        "Book_Description": book_desc,
        "Bank_Description": bank_desc,
        "Book_Amount": amount,
        "Bank_Amount": bank_amount,
        "Book_Date": book_date.strftime(
            "%Y-%m-%d"
        ),
        "Bank_Date": bank_date.strftime(
            "%Y-%m-%d"
        ),
        "Book_Reference": reference,
        "Bank_Reference": bank_reference,
        "Book_Cheque": cheque,
        "Bank_Cheque": bank_cheque,
        "Status": status

    })

# ============================================================
# SAVE DATASET
# ============================================================

df = pd.DataFrame(records)

print("\nDataset Preview:")
print(df.head())

print("\nTotal Records:", len(df))

print("\nStatus Distribution:")
print(
    df["Status"].value_counts()
)

df.to_csv(
    "bank-reconciliation-ai/datasets/bank_reconciliation_v2_6000.csv",
    index=False
)

print("\nDataset Saved Successfully!")

