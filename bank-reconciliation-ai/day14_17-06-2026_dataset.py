import pandas as pd
import random

print("\nGenerating Bank Reconciliation Dataset...")

matched_pairs = [

    ("Salary Paid", "Salary Transfer"),
    ("Office Rent", "Rent Payment"),
    ("Electricity Bill", "Electricity Payment"),
    ("Internet Expense", "Internet Bill Payment"),
    ("GST Payment", "GST Challan"),
    ("Customer Receipt", "Customer Payment"),
    ("Laptop Purchase", "Computer Purchase"),
    ("Software Subscription", "Software Payment"),
    ("Bank Charges", "Bank Service Charges"),
    ("Insurance Premium", "Insurance Payment")
]

unmatched_book = [

    "Salary Paid",
    "Office Rent",
    "Laptop Purchase",
    "GST Payment",
    "Travel Expense",
    "Fuel Expense",
    "Staff Welfare",
    "Advertising Expense",
    "Consultancy Fees",
    "Stationery Purchase"
]

unmatched_bank = [

    "ATM Withdrawal",
    "Cheque Bounce Charge",
    "Loan EMI",
    "Credit Card Payment",
    "Interest Debit",
    "Unknown Transaction",
    "Personal Transfer",
    "UPI Payment",
    "Cash Withdrawal",
    "Investment Transfer"
]

records = []

# ==================================================
# 1000 MATCHED
# ==================================================

for _ in range(1000):

    book_desc, bank_desc = random.choice(
        matched_pairs
    )

    amount = random.randint(
        1000,
        100000
    )

    records.append({

        "Book_Description": book_desc,
        "Bank_Description": bank_desc,
        "Amount": amount,
        "Match_Status": "Matched"

    })

# ==================================================
# 1000 NOT MATCHED
# ==================================================

for _ in range(1000):

    book_desc = random.choice(
        unmatched_book
    )

    bank_desc = random.choice(
        unmatched_bank
    )

    amount = random.randint(
        1000,
        100000
    )

    records.append({

        "Book_Description": book_desc,
        "Bank_Description": bank_desc,
        "Amount": amount,
        "Match_Status": "Not Matched"

    })

# ==================================================
# DATAFRAME
# ==================================================

df = pd.DataFrame(records)

df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

# ==================================================
# SAVE
# ==================================================

output_file = (
    "bank-reconciliation-ai/datasets/"
    "bank_reconciliation_2000.csv"
)

df.to_csv(
    output_file,
    index=False
)

print("\nDataset Generated Successfully!")

print("\nDataset Shape:")
print(df.shape)

print("\nPreview:")
print(df.head())

print("\nMatch Distribution:")
print(
    df["Match_Status"].value_counts()
)

print(
    "\nSaved:",
    output_file
)

print("\nDay 14 Dataset Completed!")
