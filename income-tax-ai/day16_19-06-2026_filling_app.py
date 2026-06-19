import joblib
import pandas as pd

print("\nTDS Filing AI - Day 16")

# ============================================================
# LOAD MODEL
# ============================================================
print("\nLoading Model...")
model = joblib.load("tds-ai/models/tds_model.pkl")
vectorizer = joblib.load("tds-ai/models/tds_vectorizer.pkl")
print("Model Loaded Successfully!")

# ============================================================
# SAMPLE TRANSACTIONS
# ============================================================
transactions = [
    {
        "transaction": "Salary paid to employees",
        "amount": 120000,
        "deductee_type": "Employee"
    },
    {
        "transaction": "CA fees paid",
        "amount": 50000,
        "deductee_type": "Resident"
    },
    {
        "transaction": "Commission paid to broker",
        "amount": 35000,
        "deductee_type": "Resident"
    },
    {
        "transaction": "Office rent paid",
        "amount": 150000,
        "deductee_type": "Resident"
    },
    {
        "transaction": "Consultancy fees paid to UK firm",
        "amount": 200000,
        "deductee_type": "Non-Resident"
    },
    {
        "transaction": "TCS collected on sale",
        "amount": 100000,
        "deductee_type": "Buyer"
    }
]

# ============================================================
# RETURN TYPE LOGIC
# ============================================================
def detect_return_type(section, deductee_type, transaction):
    if "salary" in transaction.lower():
        return "24Q"
    elif deductee_type == "Non-Resident":
        return "27Q"
    elif "tcs" in transaction.lower():
        return "27EQ"
    else:
        return "26Q"

# ============================================================
# PROCESS
# ============================================================
results = []
print("\n" + "=" * 60)
print("TDS RETURN FILING DETECTION")
print("=" * 60)

for item in transactions:
    transaction = item["transaction"]
    amount = item["amount"]
    deductee_type = item["deductee_type"]

    # Special handling for metrics outside standard Naive Bayes boundaries
    if "salary" in transaction.lower():
        section = "192"
    elif "tcs" in transaction.lower():
        section = "TCS"
    else:
        vector = vectorizer.transform([transaction])
        section = model.predict(vector)[0]

    return_type = detect_return_type(section, deductee_type, transaction)

    # ========================================================
    # RETURN DESCRIPTION
    # ========================================================
    if return_type == "24Q":
        return_desc = "Salary TDS Return"
    elif return_type == "26Q":
        return_desc = "Non-Salary Domestic TDS Return"
    elif return_type == "27Q":
        return_desc = "Non-Resident TDS Return"
    elif return_type == "27EQ":
        return_desc = "TCS Return"
    else:
        return_desc = "Unknown"

    results.append({
        "Transaction": transaction,
        "Amount": amount,
        "Deductee_Type": deductee_type,
        "Section": section,
        "Return_Type": return_type,
        "Return_Description": return_desc
    })

# ============================================================
# RESULTS CSV GENERATION & PRESENTATION
# ============================================================
results_df = pd.DataFrame(results)
print("\nFinal Filing Data Dataframe View:")
print(results_df.to_string(index=False))

# SAVE TO OUTPUT DIR
results_df.to_csv("income-tax-ai/tds_filing_output.csv", index=False)
print("\nTDS Filing Output Saved Successfully to: income-tax-ai/tds_filing_output.csv")
print("\nDay 16 TDS Filing AI Completed!")
