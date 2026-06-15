import pandas as pd
import joblib

from sklearn.model_selection import train_test_split

from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.naive_bayes import MultinomialNB

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

print("\nLedger Classification - Day 12")

# ============================================================
# LOAD DATASET
# ============================================================

print("\nLoading Ledger Dataset...")

df = pd.read_csv(
    "ledger-classifier/datasets/ledger_transactions_2250.csv"
)

print("\nDataset Preview:")
print(df.head())

print("\nTotal Records :", len(df))

print("\nLedger Distribution:")
print(
    df["Ledger"].value_counts()
)

# ============================================================
# FEATURES & LABELS
# ============================================================

X = df["Transaction_Text"]

y = df["Ledger"]

# ============================================================
# TRAIN TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining Records :", len(X_train))
print("Testing Records  :", len(X_test))

# ============================================================
# TF-IDF
# ============================================================

print("\nConverting Text To Numbers...")

vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=5000
)

X_train_vector = vectorizer.fit_transform(
    X_train
)

X_test_vector = vectorizer.transform(
    X_test
)

print("Vectorization Completed!")

print(
    "\nVocabulary Size :",
    len(
        vectorizer.get_feature_names_out()
    )
)

# ============================================================
# TRAIN MODEL
# ============================================================

print("\nTraining Ledger Classifier...")

model = MultinomialNB()

model.fit(
    X_train_vector,
    y_train
)

# ============================================================
# PREDICTIONS
# ============================================================

predictions = model.predict(
    X_test_vector
)

# ============================================================
# ACCURACY
# ============================================================

accuracy = accuracy_score(
    y_test,
    predictions
)

print(
    "\nModel Accuracy :",
    round(accuracy, 4)
)

# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n" + "=" * 60)
print("CLASSIFICATION REPORT")
print("=" * 60)

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)

# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\n" + "=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)

cm = confusion_matrix(
    y_test,
    predictions
)

print(cm)

# ============================================================
# WRONG PREDICTIONS
# ============================================================

print("\n" + "=" * 60)
print("WRONG PREDICTIONS")
print("=" * 60)

results = pd.DataFrame({
    "Transaction_Text": X_test.values,
    "Actual": y_test.values,
    "Predicted": predictions
})

wrong_predictions = results[
    results["Actual"] != results["Predicted"]
]

if len(wrong_predictions) > 0:

    print(
        wrong_predictions.head(10)
    )

else:

    print(
        "No Wrong Predictions Found!"
    )

# ============================================================
# SAVE RESULTS
# ============================================================

results.to_csv(
    "ledger-classifier/results_day12.csv",
    index=False
)

print(
    "\nResults Saved Successfully!"
)

# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(
    model,
    "ledger-classifier/models/ledger_classifier_day12.pkl"
)

joblib.dump(
    vectorizer,
    "ledger-classifier/models/ledger_vectorizer_day12.pkl"
)

print(
    "\nModel Saved Successfully!"
)

# ============================================================
# LOAD MODEL
# ============================================================

loaded_model = joblib.load(
    "ledger-classifier/models/ledger_classifier_day12.pkl"
)

loaded_vectorizer = joblib.load(
    "ledger-classifier/models/ledger_vectorizer_day12.pkl"
)

print(
    "Model Loaded Successfully!"
)

# ============================================================
# CUSTOM TESTING
# ============================================================

sample_transactions = [

    "Monthly employee salary payment",

    "Office rent for June",

    "Electricity bill paid",

    "SBI bank service charges",

    "CA consultation fees",

    "GST payment challan",

    "TDS deposited to government",

    "Customer invoice generated",

    "Purchase of office supplies",

    "Fixed deposit interest received",

    "Business loan EMI payment",

    "Vehicle insurance premium",

    "Flight ticket booking",

    "Facebook advertisement expense",

    "AWS cloud hosting charges"
]

sample_vector = loaded_vectorizer.transform(
    sample_transactions
)

sample_predictions = loaded_model.predict(
    sample_vector
)

sample_probabilities = loaded_model.predict_proba(
    sample_vector
)

print("\n" + "=" * 60)
print("LEDGER PREDICTIONS")
print("=" * 60)

for transaction, ledger, probs in zip(
    sample_transactions,
    sample_predictions,
    sample_probabilities
):

    confidence = max(probs) * 100

    print(transaction)

    print(
        "Prediction :",
        ledger
    )

    print(
        "Confidence :",
        round(confidence, 2),
        "%"
    )

    print("-" * 50)

print(
    "\nDay 12 Completed Successfully!"
)
