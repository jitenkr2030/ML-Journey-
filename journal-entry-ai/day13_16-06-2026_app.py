import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score

print("\nJournal Entry AI - Day 13")

# =====================================================
# LOAD DATASET
# =====================================================

print("\nLoading Dataset...")

df = pd.read_csv(
    "journal-entry-ai/datasets/journal_entries_2000.csv"
)

print("\nDataset Preview:")
print(df.head())

print("\nTotal Records :", len(df))

print("\nTransaction Types:")
print(df["Transaction_Type"].value_counts())

# =====================================================
# FEATURES
# =====================================================

X = df["Transaction_Text"]

# =====================================================
# LABELS
# =====================================================

y_debit = df["Debit_Account"]
y_credit = df["Credit_Account"]

# =====================================================
# SPLIT
# =====================================================

X_train, X_test, y_debit_train, y_debit_test = train_test_split(
    X,
    y_debit,
    test_size=0.20,
    random_state=42,
    stratify=y_debit
)

_, _, y_credit_train, y_credit_test = train_test_split(
    X,
    y_credit,
    test_size=0.20,
    random_state=42,
    stratify=y_credit
)

print("\nTraining Records :", len(X_train))
print("Testing Records  :", len(X_test))

# =====================================================
# TFIDF
# =====================================================

print("\nVectorizing Text...")

vectorizer = TfidfVectorizer(
    ngram_range=(1,2),
    max_features=5000
)

X_train_vector = vectorizer.fit_transform(X_train)
X_test_vector = vectorizer.transform(X_test)

print("Vectorization Completed!")

print(
    "Vocabulary Size :",
    len(vectorizer.get_feature_names_out())
)

# =====================================================
# DEBIT MODEL
# =====================================================

print("\nTraining Debit Model...")

debit_model = MultinomialNB()

debit_model.fit(
    X_train_vector,
    y_debit_train
)

# =====================================================
# CREDIT MODEL
# =====================================================

print("Training Credit Model...")

credit_model = MultinomialNB()

credit_model.fit(
    X_train_vector,
    y_credit_train
)

# =====================================================
# TEST
# =====================================================

debit_predictions = debit_model.predict(
    X_test_vector
)

credit_predictions = credit_model.predict(
    X_test_vector
)

debit_accuracy = accuracy_score(
    y_debit_test,
    debit_predictions
)

credit_accuracy = accuracy_score(
    y_credit_test,
    credit_predictions
)

print(
    "\nDebit Accuracy :",
    round(debit_accuracy,4)
)

print(
    "Credit Accuracy:",
    round(credit_accuracy,4)
)

# =====================================================
# SAVE MODELS
# =====================================================

joblib.dump(
    debit_model,
    "journal-entry-ai/models/debit_model.pkl"
)

joblib.dump(
    credit_model,
    "journal-entry-ai/models/credit_model.pkl"
)

joblib.dump(
    vectorizer,
    "journal-entry-ai/models/vectorizer.pkl"
)

print("\nModels Saved Successfully!")

# =====================================================
# LOAD MODELS
# =====================================================

debit_model = joblib.load(
    "journal-entry-ai/models/debit_model.pkl"
)

credit_model = joblib.load(
    "journal-entry-ai/models/credit_model.pkl"
)

vectorizer = joblib.load(
    "journal-entry-ai/models/vectorizer.pkl"
)

print("Models Loaded Successfully!")

# =====================================================
# TEST TRANSACTIONS
# =====================================================

sample_transactions = [

    "Salary paid to employees",

    "Monthly office rent paid",

    "GST payment deposited",

    "Purchased laptop for office",

    "Received payment from customer",

    "Electricity bill paid",

    "Facebook advertisement expense",

    "Professional consultancy fees",

    "Bank charges deducted",

    "Loan EMI paid"

]

sample_vector = vectorizer.transform(
    sample_transactions
)

debit_results = debit_model.predict(
    sample_vector
)

credit_results = credit_model.predict(
    sample_vector
)

print("\n" + "="*60)
print("JOURNAL ENTRY AI PREDICTIONS")
print("="*60)

for transaction, debit, credit in zip(
    sample_transactions,
    debit_results,
    credit_results
):

    print("\nTransaction : ", transaction)
    print("Debit  :", debit)
    print("Credit :", credit)

print("\nDay 13 Completed Successfully!")
