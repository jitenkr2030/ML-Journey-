from fastapi import FastAPI
from pydantic import BaseModel

import joblib

print("\nLoading Expense Classification Model...")

model = joblib.load(
    "expense-classifier/expense_classifier_day7.pkl"
)

vectorizer = joblib.load(
    "expense-classifier/tfidf_vectorizer_day7.pkl"
)

print("Model Loaded Successfully!")

# ==================================
# FASTAPI APP
# ==================================

app = FastAPI(
    title="Financial Expense Classification API",
    version="1.0"
)

# ==================================
# REQUEST MODEL
# ==================================

class ExpenseRequest(BaseModel):
    description: str

# ==================================
# HOME PAGE
# ==================================

@app.get("/")
def home():

    return {
        "message": "Financial Expense Classification API Running Successfully"
    }

# ==================================
# PREDICTION API
# ==================================

@app.post("/predict")
def predict_expense(data: ExpenseRequest):

    expense_text = data.description

    expense_vector = vectorizer.transform(
        [expense_text]
    )

    prediction = model.predict(
        expense_vector
    )[0]

    return {
        "description": expense_text,
        "category": prediction
    }

# ==================================
# STARTUP MESSAGE
# ==================================

print("\nDay 9 API Ready!")
