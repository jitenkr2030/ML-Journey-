from fastapi import FastAPI
from pydantic import BaseModel
import joblib

print("Loading Ledger Classification Model...")

model = joblib.load(
    "ledger-classifier/models/ledger_classifier_day12.pkl"
)

vectorizer = joblib.load(
    "ledger-classifier/models/ledger_vectorizer_day12.pkl"
)

print("Model Loaded Successfully!")
print("Day 13 Ledger API Ready!")

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Ledger Classification API",
    version="1.0"
)

# ============================================================
# REQUEST MODEL
# ============================================================

class LedgerRequest(BaseModel):
    description: str

# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Ledger Classification API Running"
    }

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "success",
        "model": "loaded"
    }

# ============================================================
# PREDICT
# ============================================================

@app.post("/predict")
def predict(request: LedgerRequest):

    vector = vectorizer.transform(
        [request.description]
    )

    prediction = model.predict(
        vector
    )[0]

    probabilities = model.predict_proba(
        vector
    )[0]

    confidence = round(
        max(probabilities) * 100,
        2
    )

    return {
        "description": request.description,
        "ledger": prediction,
        "confidence": confidence
    }

# ============================================================
# MULTIPLE PREDICTIONS
# ============================================================

@app.post("/batch-predict")
def batch_predict(
    descriptions: list[str]
):

    results = []

    for text in descriptions:

        vector = vectorizer.transform(
            [text]
        )

        prediction = model.predict(
            vector
        )[0]

        probability = model.predict_proba(
            vector
        )[0]

        confidence = round(
            max(probability) * 100,
            2
        )

        results.append(
            {
                "description": text,
                "ledger": prediction,
                "confidence": confidence
            }
        )

    return {
        "results": results
    }
