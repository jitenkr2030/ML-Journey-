import pandas as pd
import random

print("\nTDS AI Dataset Generator - Day 16")

records = []

tds_data = {
    "194C": {
        "rate": 1,
        "ledger": "Contractor Expense",
        "transactions": [
            "Contractor payment made",
            "Labour charges paid",
            "Construction work payment",
            "Transport charges paid",
            "Freight charges paid"
        ]
    },
    "194H": {
        "rate": 5,
        "ledger": "Commission Expense",
        "transactions": [
            "Commission paid to agent",
            "Brokerage charges paid",
            "Sales commission payment",
            "Referral commission paid",
            "Agent incentive paid"
        ]
    },
    "194I": {
        "rate": 10,
        "ledger": "Rent Expense",
        "transactions": [
            "Office rent paid",
            "Warehouse rent paid",
            "Building lease payment",
            "Shop rent transferred",
            "Property rent paid"
        ]
    },
    "194J": {
        "rate": 10,
        "ledger": "Professional Fees",
        "transactions": [
            "CA fees paid",
            "Legal consultancy fees paid",
            "Audit fees paid",
            "Professional consultancy charges",
            "Doctor consultation fees paid"
        ]
    },
    "194A": {
        "rate": 10,
        "ledger": "Interest Expense",
        "transactions": [
            "Interest paid on loan",
            "Bank interest paid",
            "Interest on unsecured loan",
            "Finance charges paid",
            "Interest payment booked"
        ]
    },
    "194Q": {
        "rate": 0.1,
        "ledger": "Purchase Expense",
        "transactions": [
            "Goods purchased from vendor",
            "Raw material purchase made",
            "Bulk inventory purchase",
            "Purchase of stock items",
            "Vendor supply payment"
        ]
    }
}

deductee_types = ["Individual", "Company", "Firm", "Contractor", "Professional"]

for i in range(5500):
    section = random.choice(list(tds_data.keys()))
    transaction = random.choice(tds_data[section]["transactions"])
    amount = random.randint(5000, 500000)
    deductee = random.choice(deductee_types)
    
    rate = tds_data[section]["rate"]
    ledger = tds_data[section]["ledger"]
    
    tds_amount = round((amount * rate) / 100, 2)
    net_payment = round(amount - tds_amount, 2)
    
    records.append({
        "Transaction_Text": transaction,
        "Amount": amount,
        "Deductee_Type": deductee,
        "TDS_Section": section,
        "TDS_Rate": str(rate) + "%",
        "TDS_Amount": tds_amount,
        "Net_Payment": net_payment,
        "Ledger": ledger
    })

df = pd.DataFrame(records)
print("\nDataset Preview:")
print(df.head())
print("\nTotal Records:", len(df))
print("\nTDS Section Distribution:")
print(df["TDS_Section"].value_counts())

df.to_csv("tds-ai/datasets/tds_dataset_5500.csv", index=False)
print("\nDataset Saved Successfully!")
