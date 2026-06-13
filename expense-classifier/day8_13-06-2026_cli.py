import joblib

print("=" * 60)
print("FINANCIAL EXPENSE CLASSIFIER - DAY 8")
print("=" * 60)

# ==================================
# LOAD MODEL
# ==================================

print("\nLoading Trained Model...")

model = joblib.load(
    "expense-classifier/expense_classifier_day7.pkl"
)

vectorizer = joblib.load(
    "expense-classifier/tfidf_vectorizer_day7.pkl"
)

print("Model Loaded Successfully!")

# ==================================
# CLI LOOP
# ==================================

while True:

    print("\n" + "=" * 60)

    expense = input(
        "Enter Expense Description (or type exit): "
    )

    if expense.lower() == "exit":

        print("\nExiting Application...")
        break

    expense_vector = vectorizer.transform(
        [expense]
    )

    prediction = model.predict(
        expense_vector
    )[0]

    print(
        f"\nPredicted Category : {prediction}"
    )

print("\nDay 8 Completed Successfully!")
