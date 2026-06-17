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

print("\nFinancial Statement AI (ML Version) - Day 15")

# ============================================================
# LOAD DATASET
# ============================================================

print("\nLoading Dataset...")

df = pd.read_csv(
    "financial-statement-ai/datasets/financial_statements_5200.csv"
)

print("\nDataset Preview:")
print(df.head())

print("\nTotal Records :", len(df))

# ============================================================
# ACCOUNT GROUP MAPPING
# ============================================================

asset_accounts = [
    "Cash",
    "Bank Account",
    "Accounts Receivable",
    "Inventory",
    "Furniture",
    "Computer Equipment",
    "Vehicle"
]

liability_accounts = [
    "Accounts Payable",
    "GST Payable",
    "Loan Payable"
]

income_accounts = [
    "Sales Revenue",
    "Service Revenue",
    "Commission Income"
]

expense_accounts = [
    "Salary Expense",
    "Rent Expense",
    "Electricity Expense",
    "Internet Expense",
    "Marketing Expense"
]

def get_group(account):

    if account in asset_accounts:
        return "Asset"

    elif account in liability_accounts:
        return "Liability"

    elif account in income_accounts:
        return "Income"

    elif account in expense_accounts:
        return "Expense"

    return "Other"

df["Financial_Group"] = df["Account_Name"].apply(
    get_group
)

print("\nFinancial Groups:")
print(df["Financial_Group"].value_counts())

# ============================================================
# FEATURES & LABELS
# ============================================================

X = df["Account_Name"]

y = df["Financial_Group"]

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
    max_features=2000
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

print("\nTraining Financial Statement Model...")

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
# REPORT
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
# SAVE MODEL
# ============================================================

joblib.dump(
    model,
    "financial-statement-ai/models/financial_statement_model.pkl"
)

joblib.dump(
    vectorizer,
    "financial-statement-ai/models/financial_statement_vectorizer.pkl"
)

print("\nModel Saved Successfully!")

# ============================================================
# LOAD MODEL
# ============================================================

loaded_model = joblib.load(
    "financial-statement-ai/models/financial_statement_model.pkl"
)

loaded_vectorizer = joblib.load(
    "financial-statement-ai/models/financial_statement_vectorizer.pkl"
)

print("Model Loaded Successfully!")

# ============================================================
# CUSTOM TESTING
# ============================================================

sample_accounts = [

    "Cash",
    "Bank Account",
    "Inventory",
    "Vehicle",

    "Loan Payable",
    "GST Payable",

    "Sales Revenue",
    "Commission Income",

    "Salary Expense",
    "Marketing Expense",

    "Internet Expense",
    "Rent Expense"
]

sample_vector = loaded_vectorizer.transform(
    sample_accounts
)

sample_predictions = loaded_model.predict(
    sample_vector
)

sample_probabilities = loaded_model.predict_proba(
    sample_vector
)

print("\n" + "=" * 60)
print("ACCOUNT GROUP PREDICTIONS")
print("=" * 60)

for account, prediction, probs in zip(
    sample_accounts,
    sample_predictions,
    sample_probabilities
):

    confidence = max(probs) * 100

    print(account)
    print("Prediction :", prediction)
    print(
        "Confidence :",
        round(confidence, 2),
        "%"
    )
    print("-" * 50)

# ============================================================
# FINANCIAL SUMMARY
# ============================================================

total_assets = df[
    df["Financial_Group"] == "Asset"
]["Debit"].sum()

total_liabilities = df[
    df["Financial_Group"] == "Liability"
]["Credit"].sum()

total_income = df[
    df["Financial_Group"] == "Income"
]["Credit"].sum()

total_expenses = df[
    df["Financial_Group"] == "Expense"
]["Debit"].sum()

net_profit = total_income - total_expenses

print("\n" + "=" * 60)
print("FINANCIAL STATEMENT SUMMARY")
print("=" * 60)

print("Total Assets      :", round(total_assets, 2))
print("Total Liabilities :", round(total_liabilities, 2))
print("Total Income      :", round(total_income, 2))
print("Total Expenses    :", round(total_expenses, 2))
print("Net Profit        :", round(net_profit, 2))

print("\nDay 15 ML Completed Successfully!")
