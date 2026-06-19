from fastapi import FastAPI
from pydantic import BaseModel
import joblib

app = FastAPI(
    title="TDS AI API",
    version="1.0"
)

# ============================================================
# LOAD MODEL
# ============================================================
model = joblib.load("tds-ai/models/tds_model.pkl")
vectorizer = joblib.load("tds-ai/models/tds_vectorizer.pkl")

# ============================================================
# TDS RATE MAP
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
# INPUT MODEL
# ============================================================
class TransactionInput(BaseModel):
    transaction: str
    amount: float

# ============================================================
# HOME
# ============================================================
@app.get("/")
def home():
    return {
        "message": "TDS AI API Running"
    }

# ============================================================
# PREDICT
# ============================================================
@app.post("/predict")
def predict(data: TransactionInput):
    vector = vectorizer.transform([data.transaction])
    section = model.predict(vector)[0]
    probability = model.predict_proba(vector)[0]
    confidence = round(max(probability) * 100, 2)
    
    rate = tds_rates[section]
    tds_amount = round((data.amount * rate) / 100, 2)
    net_payment = round(data.amount - tds_amount, 2)
    ledger = ledger_mapping[section]
    
    journal_entry = {
        "Debit": f"{ledger} (Amount: {data.amount})",
        "Credit_1": f"TDS Payable (Amount: {tds_amount})",
        "Credit_2": f"Bank (Amount: {net_payment})"
    }
    
    return {
        "transaction": data.transaction,
        "amount": data.amount,
        "tds_section": section,
        "tds_rate": f"{rate}%",
        "tds_amount": tds_amount,
        "net_payment": net_payment,
        "ledger": ledger,
        "journal_entry": journal_entry,
        "confidence": f"{confidence}%"
    }
