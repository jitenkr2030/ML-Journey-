import joblib
import pandas as pd

print("\nBank Reconciliation AI CLI - Day 14")

# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading Model...")

model = joblib.load(
    "bank-reconciliation-ai/models/bank_reconciliation_ml.pkl"
)

encoder = joblib.load(
    "bank-reconciliation-ai/models/bank_reconciliation_encoder.pkl"
)

print("Model Loaded Successfully!")

# ============================================================
# CLI LOOP
# ============================================================

while True:

    print("\n" + "=" * 60)
    print("BANK RECONCILIATION PREDICTOR")
    print("=" * 60)

    user_input = input(
        "\nPress Enter to continue or type 'exit' : "
    )

    if user_input.lower() == "exit":

        print("\nGoodbye!")
        break

    # ========================================================
    # INPUTS
    # ========================================================

    amount_match = int(
        input(
            "\nAmount Match? (1=yes, 0=no): "
        )
    )

    reference_match = int(
        input(
            "Reference Match? (1=yes, 0=no): "
        )
    )

    cheque_match = int(
        input(
            "Cheque Match? (1=yes, 0=no): "
        )
    )

    date_match = int(
        input(
            "Date Match? (1=yes, 0=no): "
        )
    )

    amount_difference = float(
        input(
            "Amount Difference: "
        )
    )

    description_similarity = float(
        input(
            "Description Similarity (0-1): "
        )
    )

    # ========================================================
    # DATAFRAME
    # ========================================================

    sample = pd.DataFrame([{

        "Amount_Match":
            amount_match,

        "Reference_Match":
            reference_match,

        "Cheque_Match":
            cheque_match,

        "Date_Match":
            date_match,

        "Amount_Difference":
            amount_difference,

        "Description_Similarity":
            description_similarity

    }])

    # ========================================================
    # PREDICTION
    # ========================================================

    prediction = model.predict(
        sample
    )

    probabilities = model.predict_proba(
        sample
    )

    status = encoder.inverse_transform(
        prediction
    )[0]

    confidence = round(
        max(probabilities[0]) * 100,
        2
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    print("\n" + "=" * 60)
    print("RECONCILIATION RESULT")
    print("=" * 60)

    print(
        "Predicted Status :",
        status
    )

    print(
        "Confidence :",
        confidence,
        "%"
    )

    print("=" * 60)

print("\nDay 14 CLI Completed Successfully!")

