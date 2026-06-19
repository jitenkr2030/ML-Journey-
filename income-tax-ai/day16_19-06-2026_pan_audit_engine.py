import joblib

print("\nTDS PAN Validation AI - Day 16")

# ============================================================
# LOAD MODEL
# ============================================================
print("\nLoading Model...")
model = joblib.load("tds-ai/models/tds_model.pkl")
vectorizer = joblib.load("tds-ai/models/tds_vectorizer.pkl")
print("Model Loaded Successfully!")

# ============================================================
# NORMAL TDS RATE
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
# NO PAN RATE (Section 206AA Statutory Penalty Rates)
# ============================================================
no_pan_rates = {
    "194C": 20,
    "194H": 20,
    "194I": 20,
    "194J": 20,
    "194A": 20,
    "194Q": 5
}

# ============================================================
# SAMPLE DATA
# ============================================================
transactions = [
    {
        "transaction": "CA fees paid",
        "amount": 50000,
        "pan_available": True
    },
    {
        "transaction": "CA fees paid",
        "amount": 50000,
        "pan_available": False
    },
    {
        "transaction": "Office rent paid",
        "amount": 100000,
        "pan_available": True
    },
    {
        "transaction": "Office rent paid",
        "amount": 100000,
        "pan_available": False
    }
]

# ============================================================
# PROCESS
# ============================================================
print("\n" + "=" * 60)
print("PAN VALIDATION RESULTS (SEC 206AA)")
print("=" * 60)

for item in transactions:
    transaction = item["transaction"]
    amount = item["amount"]
    pan_available = item["pan_available"]
    
    vector = vectorizer.transform([transaction])
    section = model.predict(vector)[0]
    
    # ========================================================
    # PAN VALIDATION LOGIC
    # ========================================================
    if pan_available:
        rate = tds_rates[section]
        pan_status = "PAN Available - Standard Deduction"
    else:
        rate = no_pan_rates[section]
        pan_status = "PAN Not Available - Higher TDS Applied (Sec 206AA)"
        
    tds_amount = round((amount * rate) / 100, 2)
    net_payment = round(amount - tds_amount, 2)
    
    # ========================================================
    # OUTPUT
    # ========================================================
    print(f"\nTransaction : {transaction}")
    print(f"Amount      : {amount}")
    print(f"Section     : {section}")
    print(f"PAN Status  : {pan_status}")
    print(f"TDS Rate    : {rate}%")
    print(f"TDS Amount  : {tds_amount}")
    print(f"Net Payment : {net_payment}")
    
    print("\nJournal Entry:")
    print(f"Expense Dr  {amount}")
    print(f"    To TDS Payable  {tds_amount}")
    print(f"    To Bank         {net_payment}")
    print("-" * 60)

print("\nDay 16 PAN Validation Completed!")
