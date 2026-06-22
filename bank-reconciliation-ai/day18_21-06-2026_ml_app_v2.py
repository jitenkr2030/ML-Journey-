import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report

print("\nBank Reconciliation AI V2 - ML Engine")

# ============================================================
# LOAD DATASET
# ============================================================

df = pd.read_csv(
    "bank-reconciliation-ai/datasets/bank_reconciliation_v2_6000.csv"
)

print("\nDataset Preview:")
print(df.head())

print("\nTotal Records:", len(df))

# ============================================================
# FEATURE ENGINEERING
# ============================================================

df["Features"] = (

    df["Book_Description"].astype(str)
    + " "
    + df["Bank_Description"].astype(str)
    + " "
    + df["Book_Amount"].astype(str)
    + " "
    + df["Bank_Amount"].astype(str)
    + " "
    + df["Book_Reference"].astype(str)
    + " "
    + df["Bank_Reference"].astype(str)

)

X = df["Features"]
y = df["Status"]

# ============================================================
# SPLIT DATA
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y

)

# ============================================================
# TF-IDF
# ============================================================

vectorizer = TfidfVectorizer()

X_train_vector = vectorizer.fit_transform(
    X_train
)

X_test_vector = vectorizer.transform(
    X_test
)

# ============================================================
# MODEL TRAINING
# ============================================================

model = MultinomialNB()

model.fit(
    X_train_vector,
    y_train
)

# ============================================================
# EVALUATION
# ============================================================

predictions = model.predict(
    X_test_vector
)

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\nModel Accuracy:", round(
    accuracy,
    4
))

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions
    )
)

# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(

    model,
    "bank-reconciliation-ai/models/reconciliation_v2_model.pkl"

)

joblib.dump(

    vectorizer,
    "bank-reconciliation-ai/models/reconciliation_v2_vectorizer.pkl"

)

print("\nModel Saved Successfully!")

# ============================================================
# LOAD MODEL
# ============================================================

loaded_model = joblib.load(
    "bank-reconciliation-ai/models/reconciliation_v2_model.pkl"
)

loaded_vectorizer = joblib.load(
    "bank-reconciliation-ai/models/reconciliation_v2_vectorizer.pkl"
)

print("Model Loaded Successfully!")

# ============================================================
# TEST CASES
# ============================================================

test_cases = [

    "Salary Payment Salary Payment 50000 50000 REF12345 REF12345",
    "Vendor Payment Vendor Payment 20000 19995 REF56789 REF56789",
    "Customer Receipt Not Available 15000 0 REF11111 NA",
    "Bank Charges Bank Charges 5000 -5000 REF22222 REF22222",
    "Fuel Expense Unknown Transaction 7000 25000 REF33333 REF99999"

]

test_vector = loaded_vectorizer.transform(
    test_cases
)

results = loaded_model.predict(
    test_vector
)

probabilities = loaded_model.predict_proba(
    test_vector
)

print("\n" + "=" * 60)
print("BANK RECONCILIATION V2 TEST RESULTS")
print("=" * 60)

for case, result, prob in zip(
    test_cases,
    results,
    probabilities
):

    confidence = round(
        max(prob) * 100,
        2
    )

    print("\nInput :", case)
    print("Predicted Status :", result)
    print("Confidence :", str(confidence) + "%")
    print("-" * 60)

print("\nDay 18 Bank Reconciliation AI V2 Completed!")

