import joblib

print("\nTDS AI CLI - Day 16")

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

ledger_mapping = {
    "194C": "Contractor Expense",
    "194H": "Commission Expense",
    "194I": "Rent Expense",
    "194J": "Professional Fees",
    "194A": "Interest Expense",
    "194Q": "Purchase Expense"
}

# ============================================================
# CLI LOOP
# ============================================================
while True:
    print("\n" + "=" * 60)
    
    transaction = input("\nEnter Transaction (or type exit): ")
    if transaction.lower() == "exit":
        print("\nExiting TDS AI...")
        break
        
    try:
        amount = float(input("Enter Amount: "))
    except ValueError:
        print("Invalid number format. Please enter a valid numerical amount.")
        continue

    # ========================================================
    # PREDICT SECTION
    # ========================================================
    vector = vectorizer.transform([transaction])
    section = model.predict(vector)[0]
    probability = model.predict_proba(vector)[0]
    confidence = round(max(probability) * 100, 2)

    # ========================================================
    # TDS CALCULATION
    # ========================================================
    rate = tds_rates[section]
    tds_amount = round((amount * rate) / 100, 2)
    net_payment = round(amount - tds_amount, 2)
    ledger = ledger_mapping[section]

    # ========================================================
    # OUTPUT
    # ========================================================
    print("\n" + "=" * 60)
    print("TDS AI RESULT")
    print("=" * 60)
    
    print("\nTransaction  :", transaction)
    print("Amount       :", amount)
    print("TDS Section  :", section)
    print("TDS Rate     :", str(rate) + "%")
    print("TDS Amount   :", tds_amount)
    print("Net Payment  :", net_payment)
    print("Ledger       :", ledger)
    print("Confidence   :", confidence, "%")
    
    print("\nJournal Entry:")
    print(f"{ledger} Dr  {amount}")
    print(f"    To TDS Payable  {tds_amount}")
    print(f"    To Bank         {net_payment}")
    print("\n" + "=" * 60)

print("\nDay 16 CLI Completed Successfully!")
