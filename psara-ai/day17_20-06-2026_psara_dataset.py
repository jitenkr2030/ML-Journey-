import pandas as pd
import random

print("\nPSARA AI Dataset Generator - Day 17")

records = []

documents = [
    "PAN Card",
    "GST Certificate",
    "Shop Act License",
    "Police Verification",
    "Training Certificate",
    "Aadhaar Card",
    "ESIC Registration",
    "EPF Registration",
    "Medical Fitness",
    "Character Certificate",
    "Address Proof",
    "Affidavit",
    "Bank Passbook",
    "Employment Contract"
]

states = [
    "Delhi",
    "Uttar Pradesh",
    "Haryana",
    "Punjab",
    "Rajasthan"
]

statuses = [
    "Submitted",
    "Missing",
    "Expired",
    "Verified"
]

risk_levels = [
    "Low Risk",
    "Medium Risk",
    "High Risk"
]

for i in range(5500):
    agency_id = f"AGENCY_{random.randint(1000, 9999)}"
    guard_id = f"GUARD_{random.randint(10000, 99999)}"
    state = random.choice(states)
    document_name = random.choice(documents)
    document_status = random.choice(statuses)
    training_completed = random.choice(["Yes", "No"])
    police_verified = random.choice(["Yes", "No"])
    medical_fit = random.choice(["Yes", "No"])
    expiry_days = random.randint(0, 365)
    
    # ========================================================
    # PSARA RISK COMPLIANCE MATRIX LOGIC
    # ========================================================
    if (
        document_status == "Expired"
        or police_verified == "No"
        or training_completed == "No"
    ):
        risk = "High Risk"
    elif document_status == "Missing":
        risk = "Medium Risk"
    else:
        risk = "Low Risk"
        
    records.append({
        "Agency_ID": agency_id,
        "Guard_ID": guard_id,
        "State": state,
        "Document_Name": document_name,
        "Document_Status": document_status,
        "Training_Completed": training_completed,
        "Police_Verified": police_verified,
        "Medical_Fit": medical_fit,
        "Expiry_Days_Left": expiry_days,
        "Risk_Level": risk
    })

df = pd.DataFrame(records)

print("\nDataset Preview:")
print(df.head())
print("\nTotal Records:", len(df))
print("\nRisk Distribution:")
print(df["Risk_Level"].value_counts())

df.to_csv("psara-ai/datasets/psara_dataset_5500.csv", index=False)
print("\nDataset Saved Successfully!")
