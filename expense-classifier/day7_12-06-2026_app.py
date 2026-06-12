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

print("\nFinancial Expense Classification - Day 7")

# ==================================
# LOAD DATASET
# ==================================

print("\nLoading CSV Dataset...")

df = pd.read_csv(
    "financial_expenses_1000.csv"
)

print("\nDataset Preview:")
print(df.head())

print("\nTotal Records :", len(df))

# ==================================
# FEATURES AND LABELS
# ==================================

X = df["Description"]

y = df["Category"]

# ==================================
# TRAIN / TEST SPLIT
# ==================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=20
)

print("\nTraining Records :", len(X_train))
print("Testing Records  :", len(X_test))

# ==================================
# TF-IDF VECTORIZATION
# ==================================

print("\nConverting text into numbers using TF-IDF...")

vectorizer = TfidfVectorizer()

X_train_vector = vectorizer.fit_transform(
    X_train
)

X_test_vector = vectorizer.transform(
    X_test
)

print("Vectorization Completed!")

# ==================================
# MODEL TRAINING
# ==================================

print("\nTraining Naive Bayes Model...")

model = MultinomialNB()

model.fit(
    X_train_vector,
    y_train
)

# ==================================
# PREDICTIONS
# ==================================

predictions = model.predict(
    X_test_vector
)

# ==================================
# ACCURACY
# ==================================

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\nModel Accuracy :", round(accuracy, 4))

# ==================================
# CLASSIFICATION REPORT
# ==================================

print("\n" + "=" * 60)
print("CLASSIFICATION REPORT")
print("=" * 60)

print(
    classification_report(
        y_test,
        predictions
    )
)

# ==================================
# CONFUSION MATRIX
# ==================================

print("\n" + "=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)

cm = confusion_matrix(
    y_test,
    predictions
)

print(cm)

# ==================================
# WRONG PREDICTIONS
# ==================================

print("\n" + "=" * 60)
print("WRONG PREDICTIONS")
print("=" * 60)

results = pd.DataFrame({
    "Description": X_test.values,
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

# ==================================
# SAVE MODEL
# ==================================

joblib.dump(
    model,
    "expense-classifier/expense_classifier_day7.pkl"
)

joblib.dump(
    vectorizer,
    "expense-classifier/tfidf_vectorizer_day7.pkl"
)

print("\nModel Saved Successfully!")

# ==================================
# LOAD MODEL
# ==================================

loaded_model = joblib.load(
    "expense-classifier/expense_classifier_day7.pkl"
)

loaded_vectorizer = joblib.load(
    "expense-classifier/tfidf_vectorizer_day7.pkl"
)

print("Model Loaded Successfully!")

# ==================================
# CUSTOM PREDICTIONS
# ==================================

sample_expenses = [

    "Uber Airport Ride",

    "Electricity Payment",

    "Salary Transfer",

    "Laptop Purchase",

    "Google Workspace Subscription",

    "Office Rent Payment",

    "Facebook Advertisement",

    "GST Payment",

    "Bank Service Charges",

    "AWS Cloud Hosting"
]

sample_vector = loaded_vectorizer.transform(
    sample_expenses
)

sample_predictions = loaded_model.predict(
    sample_vector
)

print("\n" + "=" * 60)
print("EXPENSE PREDICTIONS")
print("=" * 60)

for expense, category in zip(
    sample_expenses,
    sample_predictions
):

    print(
        f"{expense} --> {category}"
    )

print("\nDay 7 Completed Successfully!")
