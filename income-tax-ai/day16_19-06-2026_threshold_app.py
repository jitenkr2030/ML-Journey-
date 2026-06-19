import joblib

print("\nTDS Threshold Detection AI - Day 16")

# ============================================================
# LOAD MODEL
# ============================================================
print("\nLoading Model...")
model = joblib.load("tds-ai/models/tds_model.pkl")
vectorizer = joblib.load("tds-ai/models/tds_vectorizer.pkl")
print("Model Loaded Successfully!")

# ============================================================
# TDS RATE MAPPING
# ============================================================
tds_rates = {
    "194C": 1,
    "194H": 5,
    "194I": 10,
    "194J": 10,
    "194A": 10,
    "194Q": 0.1
}

# ============================================================
# THRESHOLD RULES (Indian Tax Compliance Limits)
# ============================================================
thresholds = {
    "194C": 30000,
    "194H": 15000,
    "194I": 240000,
    "194J": 30000,
    "194A": 5000,
    "194Q": 5000000
}

# ============================================================
# LEDGER MAP
# ============================================================
ledger_mapping = {
    "194C": "Contractor Expense",
    "194H": "Commission Expense",
    "194I": "Rent Expense",
    "194J": "Professional Fees",
    "194A": "Interest Expense",
    "194Q": "Purchase Expense"
}

# ============================================================
# SAMPLE TEST DATA (Below vs Above Thresholds)
# ============================================================
transactions = [
    ("CA fees paid", 20000),
    ("CA fees paid", 80000),
    ("Office rent paid", 100000),
    ("Office rent paid", 300000),
    ("Commission paid to broker", 10000),
    ("Commission paid to broker", 50000),
    ("Contractor payment made", 20000),
    ("Contractor payment made", 90000)
]

# ============================================================
# PROCESS
# ============================================================
print("\n" + "=" * 60)
print("TDS THRESHOLD CHECK RESULTS")
print("=" * 60)

for transaction, amount in transactions:
    vector = vectorizer.transform([transaction])
    section = model.predict(vector)[0]
    
    rate = tds_rates[section]
    threshold = thresholds[section]
    ledger = ledger_mapping[section]
    
    # ========================================================
    # THRESHOLD CHECK
    # ========================================================
    if amount <= threshold:
        tds_amount = 0.0
        net_payment = amount
        tds_status = "No TDS Applicable"
    else:
        tds_amount = round((amount * rate) / 100, 2)
        net_payment = round(amount - tds_amount, 2)
        tds_status = "TDS Applicable"
        
    # ========================================================
    # OUTPUT
    # ========================================================
    print(f"\nTransaction : {transaction}")
    print(f"Amount      : {amount}")
    print(f"Section     : {section}")
    print(f"Threshold   : {threshold}")
    print(f"TDS Status  : {tds_status}")
    print(f"TDS Rate    : {rate}%")
    print(f"TDS Amount  : {tds_amount}")
    print(f"Net Payment : {net_payment}")
    print(f"Ledger      : {ledger}")
    
    print("\nJournal Entry:")
    if tds_amount > 0:
        print(f"{ledger} Dr  {amount}")
        print(f"    To TDS Payable  {tds_amount}")
        print(f"    To Bank         {net_payment}")
    else:
        print(f"{ledger} Dr  {amount}")
        print(f"    To Bank         {net_payment}")
    print("-" * 60)

print("\nDay 16 Threshold Detection Completed!")
