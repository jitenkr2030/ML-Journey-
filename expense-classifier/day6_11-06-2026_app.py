import pandas as pd
import joblib

from sklearn.model_selection import train_test_split

from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.naive_bayes import MultinomialNB

from sklearn.metrics import accuracy_score

print("\nFinancial Expense Classification - Day 6")

# ==================================
# LOAD DATASET
# ==================================

print("\nLoading CSV Dataset...")

df = pd.read_csv(
    "expense-classifier/financial_expenses.csv"
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
    random_state=42
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
# EVALUATION
# ==================================

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\nModel Accuracy :", round(accuracy, 4))

# ==================================
# SAVE MODEL
# ==================================

joblib.dump(
    model,
    "expense-classifier/expense_classifier.pkl"
)

joblib.dump(
    vectorizer,
    "expense-classifier/tfidf_vectorizer.pkl"
)

print("\nModel Saved Successfully!")

# ==================================
# LOAD MODEL
# ==================================

loaded_model = joblib.load(
    "expense-classifier/expense_classifier.pkl"
)

loaded_vectorizer = joblib.load(
    "expense-classifier/tfidf_vectorizer.pkl"
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

    "GST Payment"

]

sample_vector = loaded_vectorizer.transform(
    sample_expenses
)

sample_predictions = loaded_model.predict(
    sample_vector
)

print("\nExpense Predictions")

for expense, category in zip(
    sample_expenses,
    sample_predictions
):

    print(
        f"{expense} --> {category}"
    )

print("\nDay 6 Completed Successfully!")
