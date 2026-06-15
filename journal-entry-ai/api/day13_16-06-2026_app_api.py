from fastapi import FastAPI
from pydantic import BaseModel
import joblib

print("Loading Journal Entry AI Models...")

debit_model = joblib.load(
    "journal-entry-ai/models/debit_model.pkl"
)

credit_model = joblib.load(
    "journal-entry-ai/models/credit_model.pkl"
)

vectorizer = joblib.load(
    "journal-entry-ai/models/vectorizer.pkl"
)

print("Models Loaded Successfully!")
print("Day 13 Journal Entry API Ready!")

# ====================================================
# FASTAPI APP
# ====================================================

app = FastAPI(
    title="Journal Entry AI API",
    version="1.0"
)

# ====================================================
# REQUEST MODEL
# ====================================================

class TransactionRequest(BaseModel):
    transaction_text: str

# ====================================================
# HOME
# ====================================================

@app.get("/")
def home():

    return {
        "message": "Journal Entry AI API Running",
        "version": "1.0"
    }

# ====================================================
# PREDICT
# ====================================================

@app.post("/predict")
def predict_journal_entry(
    request: TransactionRequest
):

    text = request.transaction_text

    vector = vectorizer.transform(
        [text]
    )

    debit_prediction = debit_model.predict(
        vector
    )[0]

    credit_prediction = credit_model.predict(
        vector
    )[0]

    debit_confidence = round(
        max(
            debit_model.predict_proba(
                vector
            )[0]
        ) * 100,
        2
    )

    credit_confidence = round(
        max(
            credit_model.predict_proba(
                vector
            )[0]
        ) * 100,
        2
    )

    return {

        "transaction_text": text,

        "debit_account": debit_prediction,

        "credit_account": credit_prediction,

        "debit_confidence": debit_confidence,

        "credit_confidence": credit_confidence
    }

# ====================================================
# HEALTH CHECK
# ====================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }
