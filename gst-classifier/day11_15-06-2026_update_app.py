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

print("\nGST Invoice Classification - Day 11")

# ============================================================
# LOAD DATASET
# ============================================================

print("\nLoading GST Dataset...")

df = pd.read_csv(
    "gst-classifier/datasets/gst_invoices_5000.csv"
)

print("\nDataset Preview:")
print(df.head())

print("\nTotal Records :", len(df))

print("\nCategory Distribution:")
print(df["Category"].value_counts())

# ============================================================
# FEATURES & LABELS
# ============================================================

X = df["Invoice_Text"]
y = df["Category"]

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
    len(vectorizer.get_feature_names_out())
)

# ============================================================
# TRAIN MODEL
# ============================================================

print("\nTraining GST Classifier...")

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
    "Invoice_Text": X_test.values,
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
    "gst-classifier/results_day11.csv",
    index=False
)

print("\nResults Saved Successfully!")

# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(
    model,
    "gst-classifier/models/gst_classifier_day11.pkl"
)

joblib.dump(
    vectorizer,
    "gst-classifier/models/gst_vectorizer_day11.pkl"
)

print("\nModel Saved Successfully!")

# ============================================================
# LOAD MODEL
# ============================================================

loaded_model = joblib.load(
    "gst-classifier/models/gst_classifier_day11.pkl"
)

loaded_vectorizer = joblib.load(
    "gst-classifier/models/gst_vectorizer_day11.pkl"
)

print("Model Loaded Successfully!")

# ============================================================
# CUSTOM TESTING
# ============================================================

sample_invoices = [

    "Invoice to ABC Pvt Ltd Delhi",
    "Retail customer purchase bill",
    "Export software service to USA",
    "Import machinery from China",
    "Credit note issued against sales return",
    "Debit note raised for freight charges",
    "GST payment challan",
    "GST refund received from department",
    "Reverse charge advocate service",
    "Healthcare exempt supply",
    "Wholesale supply to corporate client",
    "Amazon customer invoice",
    "Interstate sale to Maharashtra",
    "Export software service to UK",
    "Import electronics from Singapore"

]

sample_vector = loaded_vectorizer.transform(
    sample_invoices
)

sample_predictions = loaded_model.predict(
    sample_vector
)

sample_probabilities = loaded_model.predict_proba(
    sample_vector
)

print("\n" + "=" * 60)
print("GST INVOICE PREDICTIONS")
print("=" * 60)

for invoice, category, probs in zip(
    sample_invoices,
    sample_predictions,
    sample_probabilities
):

    confidence = max(probs) * 100

    print(invoice)
    print("Prediction :", category)
    print(
        "Confidence :",
        round(confidence, 2),
        "%"
    )
    print("-" * 50)

print("\nDay 11 Completed Successfully!")
