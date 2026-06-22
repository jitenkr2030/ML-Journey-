from fastapi import FastAPI
from pydantic import BaseModel
import joblib

print("\nBank Reconciliation AI V2 API")

# ============================================================
# LOAD MODEL
# ============================================================

model = joblib.load(
    "bank-reconciliation-ai/models/reconciliation_v2_model.pkl"
)

vectorizer = joblib.load(
    "bank-reconciliation-ai/models/reconciliation_v2_vectorizer.pkl"
)

print("Model Loaded Successfully!")

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Bank Reconciliation AI V2 API"
)

# ============================================================
# INPUT MODEL
# ============================================================

class ReconciliationInput(BaseModel):

    book_description: str
    bank_description: str
    book_amount: float
    bank_amount: float
    book_reference: str
    bank_reference: str

# ============================================================
# HOME ROUTE
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Bank Reconciliation AI V2 Running"
    }

# ============================================================
# PREDICTION ROUTE
# ============================================================

@app.post("/predict")
def predict(data: ReconciliationInput):

    user_input = (

        data.book_description
        + " "
        + data.bank_description
        + " "
        + str(data.book_amount)
        + " "
        + str(data.bank_amount)
        + " "
        + data.book_reference
        + " "
        + data.bank_reference

    )

    # VECTORIZE
    user_vector = vectorizer.transform(
        [user_input]
    )

    # PREDICT
    prediction = model.predict(
        user_vector
    )[0]

    probability = model.predict_proba(
        user_vector
    )[0]

    confidence = round(
        max(probability) * 100,
        2
    )

    # ========================================================
    # ACTIONS
    # ========================================================

    if prediction == "Matched":

        action = [
            "Entry fully matched"
        ]

    elif prediction == "Fuzzy Matched":

        action = [
            "Verify amount tolerance",
            "Check date difference"
        ]

    elif prediction == "Duplicate":

        action = [
            "Check duplicate transaction"
        ]

    elif prediction == "Missing Entry":

        action = [
            "Missing in book or bank"
        ]

    elif prediction == "Reversal Entry":

        action = [
            "Check reversal/refund"
        ]

    else:

        action = [
            "Manual review required"
        ]

    return {

        "predicted_status": prediction,
        "confidence": str(confidence) + "%",
        "recommended_action": action

    }

