import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

print("\nAccounting Assistant ML Engine - Day 15")

# LOAD DATASET
print("\nLoading Dataset...")
df = pd.read_csv("accounting-assistant/datasets/accounting_assistant_5200.csv")

print("\nDataset Preview:")
print(df.head())
print("\nTotal Records :", len(df))
print("\nCategory Distribution:")
print(df["Category"].value_counts())

# FEATURES
X = df["Transaction_Text"]
y = df["Category"]

# TRAIN TEST SPLIT
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print("\nTraining Records :", len(X_train))
print("Testing Records :", len(X_test))

# TF-IDF
print("\nConverting Text To Numbers...")
vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
X_train_vector = vectorizer.fit_transform(X_train)
X_test_vector = vectorizer.transform(X_test)
print("Vectorization Completed!")
print("\nVocabulary Size :", len(vectorizer.get_feature_names_out()))

# TRAIN MODEL
print("\nTraining Model...")
model = MultinomialNB()
model.fit(X_train_vector, y_train)

# PREDICTION
predictions = model.predict(X_test_vector)

# EVALUATION METRICS
accuracy = accuracy_score(y_test, predictions)
print("\nModel Accuracy :", round(accuracy, 4))

print("\n" + "=" * 60)
print("CLASSIFICATION REPORT")
print("=" * 60)
print(classification_report(y_test, predictions, zero_division=0))

print("\n" + "=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)
cm = confusion_matrix(y_test, predictions)
print(cm)

# SAVE MODEL
joblib.dump(model, "accounting-assistant/models/accounting_assistant_model.pkl")
joblib.dump(vectorizer, "accounting-assistant/models/accounting_assistant_vectorizer.pkl")
print("\nModel Saved Successfully!")

# LOAD MODEL
loaded_model = joblib.load("accounting-assistant/models/accounting_assistant_model.pkl")
loaded_vectorizer = joblib.load("accounting-assistant/models/accounting_assistant_vectorizer.pkl")
print("Model Loaded Successfully!")

# SAMPLE TESTING VIA PIPELINE
transactions = [
    "Salary paid through HDFC",
    "Office rent transferred",
    "GST deposited online",
    "Laptop purchased for office",
    "Customer payment received",
    "Facebook advertisement expense",
    "Electricity bill paid",
    "Bank charges deducted",
    "Loan EMI paid",
    "Insurance premium paid",
    "Professional consultancy fees paid",
    "Flight ticket booked"
]

transaction_vector = loaded_vectorizer.transform(transactions)
sample_predictions = loaded_model.predict(transaction_vector)
sample_probabilities = loaded_model.predict_proba(transaction_vector)

print("\n" + "=" * 60)
print("ACCOUNTING ASSISTANT PREDICTIONS")
print("=" * 60)

for transaction, prediction, probs in zip(transactions, sample_predictions, sample_probabilities):
    confidence = max(probs) * 100
    
    # --------------------------------------------------------
    # ACCOUNTING LOGIC
    # --------------------------------------------------------
    if prediction == "Payroll":
        ledger = "Salary Expense"
        journal = "Salary Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Rent":
        ledger = "Rent Expense"
        journal = "Rent Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "GST":
        ledger = "GST Payable"
        journal = "GST Payable Dr | To Bank"
        statement = "Liability"
    elif prediction == "Asset":
        ledger = "Fixed Assets"
        journal = "Fixed Asset Dr | To Bank"
        statement = "Asset"
    elif prediction == "Utilities":
        ledger = "Utilities Expense"
        journal = "Utilities Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Marketing":
        ledger = "Advertisement Expense"
        journal = "Advertisement Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Revenue":
        ledger = "Sales Revenue"
        journal = "Bank Dr | To Sales Revenue"
        statement = "Income"
    elif prediction == "Bank Charges":
        ledger = "Bank Charges Expense"
        journal = "Bank Charges Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Loan":
        ledger = "Loan Payable"
        journal = "Loan Payable Dr | To Bank"
        statement = "Liability"
    elif prediction == "Insurance":
        ledger = "Insurance Expense"
        journal = "Insurance Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Professional Fees":
        ledger = "Professional Fees Expense"
        journal = "Professional Fees Expense Dr | To Bank"
        statement = "Expense"
    elif prediction == "Travel":
        ledger = "Travel Expense"
        journal = "Travel Expense Dr | To Bank"
        statement = "Expense"
    else:
        ledger = "Manual Review"
        journal = "Manual Journal Required"
        statement = "Unknown"
        
    print("\nTransaction:", transaction)
    print("Predicted Category:", prediction)
    print("Confidence :", round(confidence, 2), "%")
    print("Ledger:", ledger)
    print("Journal Entry:", journal)
    print("Financial Statement:", statement)
    print("-" * 60)

print("\nDay 15 Accounting Assistant ML Completed Successfully!")
