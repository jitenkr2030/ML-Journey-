import joblib
from datetime import datetime

print("\nTDS Compliance AI - Day 16")

# ============================================================
# LOAD MODEL
# ============================================================
print("\nLoading Model...")
model = joblib.load("tds-ai/models/tds_model.pkl")
vectorizer = joblib.load("tds-ai/models/tds_vectorizer.pkl")
print("Model Loaded Successfully!")

# ============================================================
# TDS RATES
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
# SAMPLE COMPLIANCE DATA
# ============================================================
transactions = [
    {
        "transaction": "CA fees paid",
        "amount": 50000,
        "tds_deducted": True,
        "tds_deposited": True,
        "deduction_date": "2026-06-10",
        "deposit_date": "2026-06-15"
    },
    {
        "transaction": "Office rent paid",
        "amount": 100000,
        "tds_deducted": True,
        "tds_deposited": False,
        "deduction_date": "2026-06-01",
        "deposit_date": None
    },
    {
        "transaction": "Commission paid",
        "amount": 30000,
        "tds_deducted": False,
        "tds_deposited": False,
        "deduction_date": None,
        "deposit_date": None
    }
]

# ============================================================
# PROCESS
# ============================================================
print("\n" + "=" * 60)
print("TDS COMPLIANCE AUDIT CHECK")
print("=" * 60)

for item in transactions:
    transaction = item["transaction"]
    amount = item["amount"]
    tds_deducted = item["tds_deducted"]
    tds_deposited = item["tds_deposited"]
    
    vector = vectorizer.transform([transaction])
    section = model.predict(vector)[0]
    
    rate = tds_rates[section]
    expected_tds = round((amount * rate) / 100, 2)
    
    # ========================================================
    # COMPLIANCE RULES
    # ========================================================
    if not tds_deducted:
        compliance_status = "TDS Non-Deduction Violation"
        risk = "Section 201 Default Risk (1% p.m. interest penalty from date of applicability)"
    elif tds_deducted and not tds_deposited:
        compliance_status = "TDS Deducted But Short-Deposited/Un-Deposited"
        risk = "Interest Penalty u/s 201(1A) (1.5% p.m. interest charge from date of deduction)"
    else:
        compliance_status = "Fully Compliant"
        risk = "No Legal Risk Detected"
        
    # ========================================================
    # OUTPUT
    # ========================================================
    print(f"\nTransaction        : {transaction}")
    print(f"Amount             : {amount}")
    print(f"Predicted Section  : {section}")
    print(f"TDS Rate           : {rate}%")
    print(f"Expected TDS       : {expected_tds}")
    print(f"Compliance Status  : {compliance_status}")
    print(f"Compliance Risk    : {risk}")
    print("-" * 60)

print("\nDay 16 Compliance AI Completed!")
