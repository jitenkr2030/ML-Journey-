from fastapi import FastAPI
from pydantic import BaseModel
import joblib

print("\nPSARA Compliance API - Day 17")

# ============================================================
# LOAD MODEL
# ============================================================

model = joblib.load(
    "psara-ai/psara_model.pkl"
)

vectorizer = joblib.load(
    "psara-ai/psara_vectorizer.pkl"
)

print("Model Loaded Successfully!")

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="PSARA Compliance AI API"
)

# ============================================================
# INPUT SCHEMA
# ============================================================

class PSARAInput(BaseModel):

    document_name: str
    document_status: str
    training_completed: str
    police_verified: str
    medical_fit: str
    state: str

# ============================================================
# HOME ROUTE
# ============================================================

@app.get("/")
def home():

    return {
        "message": "PSARA Compliance AI API Running"
    }

# ============================================================
# PREDICTION ROUTE
# ============================================================

@app.post("/predict")
def predict(data: PSARAInput):

    user_input = (

        data.document_name
        + " "
        + data.document_status
        + " "
        + data.training_completed
        + " "
        + data.police_verified
        + " "
        + data.medical_fit
        + " "
        + data.state

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

    # ACTIONS
    if prediction == "High Risk":

        action = [
            "Immediate Compliance Review",
            "Renew Expired Documents",
            "Complete Police Verification"
        ]

    elif prediction == "Medium Risk":

        action = [
            "Check Missing Documents",
            "Review Pending Compliance"
        ]

    else:

        action = [
            "Compliance Good",
            "Continue Monitoring"
        ]

    return {

        "risk_level": prediction,
        "confidence": str(confidence) + "%",
        "recommended_action": action

    }

