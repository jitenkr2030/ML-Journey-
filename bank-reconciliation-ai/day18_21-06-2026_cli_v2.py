import joblib

print("\nBank Reconciliation AI V2 - CLI")

# ============================================================
# LOAD MODEL
# ============================================================

model = joblib.load(
    "bank-reconciliation-ai/models/reconciliation_v2_model.pkl"
)

vectorizer = joblib.load(
    "bank-reconciliation-ai/models/reconciliation_v2_vectorizer.pkl"
)

print("\nModel Loaded Successfully!")

# ============================================================
# CLI LOOP
# ============================================================

while True:

    print("\n" + "=" * 60)
    print("BANK RECONCILIATION V2 INPUT")
    print("=" * 60)

    book_description = input(
        "\nEnter Book Description: "
    )

    bank_description = input(
        "Enter Bank Description: "
    )

    book_amount = input(
        "Enter Book Amount: "
    )

    bank_amount = input(
        "Enter Bank Amount: "
    )

    book_reference = input(
        "Enter Book Reference: "
    )

    bank_reference = input(
        "Enter Bank Reference: "
    )

    # ========================================================
    # BUILD INPUT
    # ========================================================

    user_input = (

        book_description
        + " "
        + bank_description
        + " "
        + book_amount
        + " "
        + bank_amount
        + " "
        + book_reference
        + " "
        + bank_reference

    )

    # ========================================================
    # VECTORIZE
    # ========================================================

    user_vector = vectorizer.transform(
        [user_input]
    )

    # ========================================================
    # PREDICT
    # ========================================================

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
    # OUTPUT
    # ========================================================

    print("\n" + "=" * 60)
    print("RECONCILIATION RESULT")
    print("=" * 60)

    print("Predicted Status :", prediction)
    print("Confidence       :", str(confidence) + "%")

    # ========================================================
    # ACTION SUGGESTION
    # ========================================================

    if prediction == "Matched":

        print("\nAction:")
        print("- Entry is fully matched")

    elif prediction == "Fuzzy Matched":

        print("\nAction:")
        print("- Verify amount/date tolerance")

    elif prediction == "Duplicate":

        print("\nAction:")
        print("- Check duplicate transaction")

    elif prediction == "Missing Entry":

        print("\nAction:")
        print("- Entry missing in bank/book")

    elif prediction == "Reversal Entry":

        print("\nAction:")
        print("- Check reversal or refund")

    elif prediction == "Suspicious":

        print("\nAction:")
        print("- Manual review required")

    # ========================================================
    # CONTINUE
    # ========================================================

    choice = input(
        "\nDo you want to continue? (yes/no): "
    )

    if choice.lower() != "yes":

        break

print("\nDay 18 Bank Reconciliation CLI V2 Completed!")

