from fastapi import FastAPI
from pydantic import BaseModel
import joblib

print("Loading GST Classification Model...")

model = joblib.load(
    "gst-classifier/models/gst_classifier_day11.pkl"
)

vectorizer = joblib.load(
    "gst-classifier/models/gst_vectorizer_day11.pkl"
)

print("Model Loaded Successfully!")

app = FastAPI(
    title="GST Classification API",
    version="1.0.0"
)


class InvoiceRequest(BaseModel):
    invoice_text: str


@app.get("/")
def home():

    return {
        "message": "GST Classification API Running",
        "status": "success"
    }


@app.post("/predict")
def predict(request: InvoiceRequest):

    invoice_text = request.invoice_text

    vector = vectorizer.transform(
        [invoice_text]
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
        "invoice_text": invoice_text,
        "category": prediction,
        "confidence": confidence
    }


print("Day 12 GST API Ready!")
