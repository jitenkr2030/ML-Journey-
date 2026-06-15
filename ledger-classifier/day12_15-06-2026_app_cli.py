import joblib

print("\n" + "=" * 60)
print("LEDGER CLASSIFICATION CLI - DAY 13")
print("=" * 60)

# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading Trained Model...")

model = joblib.load(
    "ledger-classifier/models/ledger_classifier_day12.pkl"
)

vectorizer = joblib.load(
    "ledger-classifier/models/ledger_vectorizer_day12.pkl"
)

print("Model Loaded Successfully!")

# ============================================================
# CLI LOOP
# ============================================================

while True:

    print("\n" + "=" * 60)

    transaction = input(
        "Enter Transaction Description (or type exit): "
    )

    if transaction.lower() == "exit":

        print("\nExiting Application...")
        break

    vector = vectorizer.transform(
        [transaction]
    )

    prediction = model.predict(
        vector
    )[0]

    probability = model.predict_proba(
        vector
    )[0]

    confidence = max(probability) * 100

    print("\nPredicted Ledger :",
          prediction)

    print(
        "Confidence :",
        round(confidence, 2),
        "%"
    )

print("\nDay 13 Completed Successfully!")
