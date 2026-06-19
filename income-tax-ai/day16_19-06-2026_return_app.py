import joblib
from datetime import datetime

print("\nTDS Return Filing & Form 26Q Engine - Day 16")

# ============================================================
# LOAD MODEL
# ============================================================
print("\nLoading Model...")
model = joblib.load("tds-ai/models/tds_model.pkl")
vectorizer = joblib.load("tds-ai/models/tds_vectorizer.pkl")
print("Model Loaded Successfully!")

# ============================================================
# TDS COMPLIANCE DICTIONARIES
# ============================================================
tds_rates = {
    "194C": 1, "194H": 5, "194I": 10, "194J": 10, "194A": 10, "194Q": 0.1
}

no_pan_rates = {
    "194C": 20, "194H": 20, "194I": 20, "194J": 20, "194A": 20, "194Q": 5
}

# ============================================================
# BATCH TRANSACTION DATA (Quarterly Bookings)
# ============================================================
quarterly_ledger = [
    {"challan_no": "CH-801", "transaction": "CA fees paid to auditor", "amount": 45000, "pan_available": True, "status": "Deposited"},
    {"challan_no": "CH-802", "transaction": "Office rent paid to landlord", "amount": 120000, "pan_available": True, "status": "Deposited"},
    {"challan_no": "CH-803", "transaction": "Contractor payment for office fit-out", "amount": 85000, "pan_available": False, "status": "Deposited"},
    {"challan_no": "CH-804", "transaction": "Commission paid to real estate broker", "amount": 25000, "pan_available": True, "status": "Deposited"},
    {"challan_no": "CH-805", "transaction": "Legal consultancy fees paid", "amount": 60000, "pan_available": True, "status": "Deposited"},
    {"challan_no": "CH-806", "transaction": "Interest paid on corporate loan", "amount": 15000, "pan_available": True, "status": "Deducted But Not Deposited"}
]

# ============================================================
# INITIALIZE COMPILATION MATRIX
# ============================================================
form_26q_records = []
total_quarterly_booking = 0.0
total_tds_deducted = 0.0
total_tds_deposited = 0.0
non_compliance_flags = 0

print("\n" + "=" * 75)
print("PROCESSING QUARTERLY TRANSACTIONS FOR FORM 26Q COMPILATION")
print("=" * 75)

for record in quarterly_ledger:
    transaction = record["transaction"]
    amount = record["amount"]
    pan_available = record["pan_available"]
    status = record["status"]
    challan = record["challan_no"]
    
    # Infer TDS classification section via ML model
    vector = vectorizer.transform([transaction])
    section = model.predict(vector)[0]
    
    # Apply standard rate or Sec 206AA penalty fallback rate
    if pan_available:
        rate = tds_rates[section]
        pan_flag = "VALID"
    else:
        rate = no_pan_rates[section]
        pan_flag = "MISSING (Sec 206AA Higher Rate applied)"
        
    # Run core calculations
    calculated_tds = round((amount * rate) / 100, 2)
    net_payout = round(amount - calculated_tds, 2)
    
    # Update financial totals
    total_quarterly_booking += amount
    total_tds_deducted += calculated_tds
    
    if status == "Deposited":
        deposited_amt = calculated_tds
        total_tds_deposited += calculated_tds
        compliance_notes = "Ready for Return Filing"
    else:
        deposited_amt = 0.0
        non_compliance_flags += 1
        compliance_notes = "CRITICAL: Clear outstanding challan balance before filing!"
        
    # Append structured record to Form 26Q layout
    form_26q_records.append({
        "Challan": challan,
        "Section": section,
        "Gross_Amount": amount,
        "TDS_Rate": f"{rate}%",
        "TDS_Deducted": calculated_tds,
        "TDS_Deposited": deposited_amt,
        "PAN_Status": pan_flag,
        "Filing_Status": compliance_notes
    })

# ============================================================
# OUTPUT STRUCTURAL FORM 26Q REPORT
# ============================================================
print("\n" + "=" * 75)
print("                      FORM 26Q - QUARTERLY STATEMENT                      ")
print(f"                      Generated On: {datetime.now().strftime('%Y-%m-%d')}                     ")
print("=" * 75)

print(f"{'Challan':<10} | {'Sec':<5} | {'Gross Amt':<10} | {'Rate':<6} | {'Deducted':<9} | {'Deposited':<9} | {'Filing Suitability'}")
print("-" * 75)
for row in form_26q_records:
    print(f"{row['Challan']:<10} | {row['Section']:<5} | {row['Gross_Amount']:<10} | {row['TDS_Rate']:<6} | {row['TDS_Deducted']:<9} | {row['TDS_Deposited']:<9} | {row['Filing_Status']}")

print("=" * 75)
print("                        COMPLIANCE SUMMARY DASHBOARD                       ")
print("=" * 75)
print(f"Total Gross Payments Booked : INR {total_quarterly_booking:,.2f}")
print(f"Total TDS Liability Charged : INR {total_tds_deducted:,.2f}")
print(f"Total TDS Funds Deposited   : INR {total_tds_deposited:,.2f}")

# Final validation audit step
print("-" * 75)
if non_compliance_flags == 0:
    print("AUDIT SUCCESS: All quarterly matching challans have been fully cleared.")
    print("STATUS: Form 26Q validation pass token generated. Ready to upload FVU to TRACES.")
else:
    print(f"AUDIT WARNING: Found ({non_compliance_flags}) un-deposited transaction entries.")
    print("STATUS: Return file generation BLOCKED. Balance sheets show outstanding liabilities.")
print("=" * 75)

print("\nDay 16 Return App Compilation Completed Successfully!")
