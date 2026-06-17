from fastapi import FastAPI
from pydantic import BaseModel
import joblib

print("Loading Financial Statement AI Model...")
model = joblib.load(
    "financial-statement-ai/models/financial_statement_model.pkl"
)
vectorizer = joblib.load(
    "financial-statement-ai/models/financial_statement_vectorizer.pkl"
)
print("Model Loaded Successfully!")

app = FastAPI(
    title="Financial Statement AI API",
    description="Predict Financial Statement Group from Account Name",
    version="1.0"
)

class AccountRequest(BaseModel):
    account_name: str

@app.get("/")
def home():
    return {
        "message": "Financial Statement AI API Running"
    }

@app.post("/predict")
def predict_account(request: AccountRequest):
    vector = vectorizer.transform([request.account_name])
    prediction = model.predict(vector)[0]
    probabilities = model.predict_proba(vector)[0]
    confidence = round(max(probabilities) * 100, 2)
    
    interpretation = ""
    if prediction == "Asset":
        interpretation = "Appears in Balance Sheet under Assets"
    elif prediction == "Liability":
        interpretation = "Appears in Balance Sheet under Liabilities"
    elif prediction == "Income":
        interpretation = "Appears in Profit & Loss Statement as Income"
    elif prediction == "Expense":
        interpretation = "Appears in Profit & Loss Statement as Expense"
        
    return {
        "account_name": request.account_name,
        "prediction": prediction,
        "confidence": confidence,
        "interpretation": interpretation
    }

print("Day 15 Financial Statement API Ready!")
