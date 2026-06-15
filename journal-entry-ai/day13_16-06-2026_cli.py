import joblib

print("=" * 60)
print("JOURNAL ENTRY AI - DAY 13 CLI")
print("=" * 60)

# =====================================================
# LOAD MODELS
# =====================================================

print("\nLoading Models...")

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

# =====================================================
# CLI LOOP
# =====================================================

while True:

    print("\n" + "=" * 60)

    transaction = input(
        "Enter Transaction Description (or type exit): "
    )

    if transaction.lower() == "exit":

        print("\nExiting Application...")
        print("Day 13 Completed Successfully!")
        break

    transaction_vector = vectorizer.transform(
        [transaction]
    )

    debit_prediction = debit_model.predict(
        transaction_vector
    )[0]

    credit_prediction = credit_model.predict(
        transaction_vector
    )[0]

    debit_confidence = max(
        debit_model.predict_proba(
            transaction_vector
        )[0]
    ) * 100

    credit_confidence = max(
        credit_model.predict_proba(
            transaction_vector
        )[0]
    ) * 100

    print("\nSuggested Journal Entry")
    print("-" * 40)

    print(
        "Debit Account :",
        debit_prediction
    )

    print(
        "Credit Account:",
        credit_prediction
    )

    print(
        "\nDebit Confidence :",
        round(debit_confidence, 2),
        "%"
    )

    print(
        "Credit Confidence:",
        round(credit_confidence, 2),
        "%"
    )
