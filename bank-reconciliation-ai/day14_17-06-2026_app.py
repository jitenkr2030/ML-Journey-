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

print("\nBank Reconciliation AI - Day 14")

# ==================================================
# LOAD DATASET
# ==================================================

print("\nLoading Dataset...")

df = pd.read_csv(
    "bank-reconciliation-ai/datasets/bank_reconciliation_2000.csv"
)

print("\nDataset Preview:")
print(df.head())

print("\nTotal Records :", len(df))

print("\nMatch Distribution:")
print(df["Match_Status"].value_counts())

# ==================================================
# CREATE COMBINED FEATURE
# ==================================================

df["Combined_Text"] = (
    df["Book_Description"]
    + " "
    + df["Bank_Description"]
    + " Amount "
    + df["Amount"].astype(str)
)

# ==================================================
# FEATURES & LABELS
# ==================================================

X = df["Combined_Text"]

y = df["Match_Status"]

# ==================================================
# TRAIN TEST SPLIT
# ==================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining Records :", len(X_train))
print("Testing Records  :", len(X_test))

# ==================================================
# TF-IDF
# ==================================================

print("\nConverting Text To Features...")

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
    len(vectorizer.get_feature_names_out())
)

# ==================================================
# TRAIN MODEL
# ==================================================

print("\nTraining Model...")

model = MultinomialNB()

model.fit(
    X_train_vector,
    y_train
)

# ==================================================
# PREDICTIONS
# ==================================================

predictions = model.predict(
    X_test_vector
)

# ==================================================
# ACCURACY
# ==================================================

accuracy = accuracy_score(
    y_test,
    predictions
)

print(
    "\nModel Accuracy :",
    round(accuracy, 4)
)

# ==================================================
# CLASSIFICATION REPORT
# ==================================================

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

# ==================================================
# CONFUSION MATRIX
# ==================================================

print("\n" + "=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)

print(
    confusion_matrix(
        y_test,
        predictions
    )
)

# ==================================================
# WRONG PREDICTIONS
# ==================================================

results = pd.DataFrame({

    "Transaction": X_test.values,
    "Actual": y_test.values,
    "Predicted": predictions

})

wrong = results[
    results["Actual"] != results["Predicted"]
]

print("\nWrong Predictions :", len(wrong))

# ==================================================
# SAVE RESULTS
# ==================================================

results.to_csv(
    "bank-reconciliation-ai/results_day14.csv",
    index=False
)

print("\nResults Saved Successfully!")

# ==================================================
# SAVE MODEL
# ==================================================

joblib.dump(
    model,
    "bank-reconciliation-ai/models/reconciliation_model.pkl"
)

joblib.dump(
    vectorizer,
    "bank-reconciliation-ai/models/reconciliation_vectorizer.pkl"
)

print("Model Saved Successfully!")

# ==================================================
# LOAD MODEL
# ==================================================

loaded_model = joblib.load(
    "bank-reconciliation-ai/models/reconciliation_model.pkl"
)

loaded_vectorizer = joblib.load(
    "bank-reconciliation-ai/models/reconciliation_vectorizer.pkl"
)

# ==================================================
# TEST DATA
# ==================================================

sample_transactions = [

    "Salary Paid Salary Transfer Amount 25000",

    "Office Rent Rent Payment Amount 15000",

    "Laptop Purchase ATM Withdrawal Amount 45000",

    "Customer Receipt Customer Payment Amount 50000",

    "GST Payment GST Challan Amount 10000",

    "Travel Expense Credit Card Payment Amount 7000",

    "Electricity Bill Electricity Payment Amount 9000"

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
print("BANK RECONCILIATION TEST")
print("=" * 60)

for transaction, prediction, probs in zip(
    sample_transactions,
    sample_predictions,
    sample_probabilities
):

    confidence = max(probs) * 100

    print("\nTransaction:")
    print(transaction)

    print(
        "Prediction :",
        prediction
    )

    print(
        "Confidence :",
        round(confidence, 2),
        "%"
    )

print("\nDay 14 Completed Successfully!")
