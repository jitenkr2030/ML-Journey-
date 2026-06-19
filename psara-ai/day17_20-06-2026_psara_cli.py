import joblib

print("\nPSARA Compliance CLI - Day 17")

# ============================================================
# LOAD MODEL
# ============================================================

model = joblib.load(
    "psara-ai/psara_model.pkl"
)

vectorizer = joblib.load(
    "psara-ai/psara_vectorizer.pkl"
)

print("\nModel Loaded Successfully!")

# ============================================================
# CLI LOOP
# ============================================================

while True:

    print("\n" + "=" * 60)
    print("ENTER PSARA COMPLIANCE DETAILS")
    print("=" * 60)

    document_name = input(
        "\nDocument Name: "
    )

    document_status = input(
        "Document Status (Submitted/Missing/Expired/Verified): "
    )

    training_completed = input(
        "Training Completed (Yes/No): "
    )

    police_verified = input(
        "Police Verified (Yes/No): "
    )

    medical_fit = input(
        "Medical Fit (Yes/No): "
    )

    state = input(
        "State: "
    )

    # ========================================================
    # BUILD INPUT STRING
    # ========================================================

    user_input = (

        document_name
        + " "
        + document_status
        + " "
        + training_completed
        + " "
        + police_verified
        + " "
        + medical_fit
        + " "
        + state

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
    # RESULT
    # ========================================================

    print("\n" + "=" * 60)
    print("PSARA COMPLIANCE RESULT")
    print("=" * 60)

    print("Predicted Risk :", prediction)
    print("Confidence      :", str(confidence) + "%")

    # ========================================================
    # ACTION SUGGESTION
    # ========================================================

    if prediction == "High Risk":

        print("\nAction Required:")
        print("- Immediate Compliance Review")
        print("- Renew Expired Documents")
        print("- Complete Police Verification")

    elif prediction == "Medium Risk":

        print("\nAction Required:")
        print("- Check Missing Documents")
        print("- Review Pending Compliance")

    else:

        print("\nAction Required:")
        print("- Compliance Good")
        print("- Continue Monitoring")

    # ========================================================
    # EXIT OPTION
    # ========================================================

    choice = input(
        "\nDo you want to check another? (yes/no): "
    )

    if choice.lower() != "yes":

        break

print("\nDay 17 PSARA CLI Completed!")
