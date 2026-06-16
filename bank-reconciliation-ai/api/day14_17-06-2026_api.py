from fastapi import FastAPI
from pydantic import BaseModel

import pandas as pd
import joblib

print("\nLoading Bank Reconciliation ML Model...")

# ============================================================
# LOAD MODEL
# ============================================================

model = joblib.load(
    "bank-reconciliation-ai/models/bank_reconciliation_ml.pkl"
)

encoder = joblib.load(
    "bank-reconciliation-ai/models/bank_reconciliation_encoder.pkl"
)

print("Model Loaded Successfully!")

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Bank Reconciliation AI API",
    version="1.0.0"
)

# ============================================================
# REQUEST MODEL
# ============================================================

class ReconciliationRequest(BaseModel):

    Amount_Match: int
    Reference_Match: int
    Cheque_Match: int
    Date_Match: int

    Amount_Difference: float

    Description_Similarity: float

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def home():

    return {
        "message":
        "Bank Reconciliation AI API Running"
    }

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }

# ============================================================
# PREDICT
# ============================================================

@app.post("/predict")
def predict(data: ReconciliationRequest):

    sample = pd.DataFrame([{

        "Amount_Match":
            data.Amount_Match,

        "Reference_Match":
            data.Reference_Match,

        "Cheque_Match":
            data.Cheque_Match,

        "Date_Match":
            data.Date_Match,

        "Amount_Difference":
            data.Amount_Difference,

        "Description_Similarity":
            data.Description_Similarity

    }])

    prediction = model.predict(
        sample
    )

    probabilities = model.predict_proba(
        sample
    )

    predicted_status = encoder.inverse_transform(
        prediction
    )[0]

    confidence = round(
        max(probabilities[0]) * 100,
        2
    )

    return {

        "predicted_status":
            predicted_status,

        "confidence":
            confidence,

        "input": {

            "Amount_Match":
                data.Amount_Match,

            "Reference_Match":
                data.Reference_Match,

            "Cheque_Match":
                data.Cheque_Match,

            "Date_Match":
                data.Date_Match,

            "Amount_Difference":
                data.Amount_Difference,

            "Description_Similarity":
                data.Description_Similarity

        }

    }

print("\nDay 14 Bank Reconciliation API Ready!")

