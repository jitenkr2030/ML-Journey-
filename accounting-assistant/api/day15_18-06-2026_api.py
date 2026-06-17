from fastapi import FastAPI
from pydantic import BaseModel
import joblib

print("\nLoading Accounting Assistant Model...")
model = joblib.load(
    "accounting-assistant/models/accounting_assistant_model.pkl"
)
vectorizer = joblib.load(
    "accounting-assistant/models/accounting_assistant_vectorizer.pkl"
)
print("Model Loaded Successfully!")

app = FastAPI(
    title="Accounting Assistant AI API",
    version="1.0"
)

class TransactionRequest(BaseModel):
    transaction: str

@app.get("/")
def home():
    return {
        "message": "Accounting Assistant AI API Running"
    }

@app.post("/predict")
def predict(data: TransactionRequest):
    transaction = data.transaction
    
    vector = vectorizer.transform([transaction])
    prediction = model.predict(vector)[0]
    probability = model.predict_proba(vector)[0]
    confidence = round(max(probability) * 100, 2)
    
    # ========================================================
    # ACCOUNTING LOGIC
    # ========================================================
    if prediction == "Payroll":
        ledger = "Salary Expense"
        journal = "Salary Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Rent":
        ledger = "Rent Expense"
        journal = "Rent Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "GST":
        ledger = "GST Payable"
        journal = "GST Payable Dr | To Bank"
        statement = "Liability"
    elif prediction == "Asset":
        ledger = "Fixed Assets"
        journal = "Fixed Asset Dr | To Bank"
        statement = "Asset"
    elif prediction == "Utilities":
        ledger = "Utilities Expense"
        journal = "Utilities Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Marketing":
        ledger = "Advertisement Expense"
        journal = "Advertisement Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Revenue":
        ledger = "Sales Revenue"
        journal = "Bank Dr | To Sales Revenue"
        statement = "Income"
    elif prediction == "Bank Charges":
        ledger = "Bank Charges Expense"
        journal = "Bank Charges Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Loan":
        ledger = "Loan Payable"
        journal = "Loan Payable Dr | To Bank"
        statement = "Liability"
    elif prediction == "Insurance":
        ledger = "Insurance Expense"
        journal = "Insurance Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Professional Fees":
        ledger = "Professional Fees Expense"
        journal = "Professional Fees Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Travel":
        ledger = "Travel Expense"
        journal = "Travel Expense Dr | To Bank"
        statement = "Expense"
    else:
        ledger = "Manual Review"
        journal = "Manual Journal Required"
        statement = "Unknown"
        
    return {
        "transaction": transaction,
        "predicted_category": prediction,
        "confidence": confidence,
        "ledger": ledger,
        "journal_entry": journal,
        "financial_statement_group": statement
    }

print("\nDay 15 Accounting Assistant API Ready!")
