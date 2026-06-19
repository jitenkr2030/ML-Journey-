import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

print("\nTDS AI - Day 16")

# ============================================================
# LOAD DATASET
# ============================================================
print("\nLoading Dataset...")
df = pd.read_csv("tds-ai/datasets/tds_dataset_5500.csv")

print("\nDataset Preview:")
print(df.head())
print("\nTotal Records :", len(df))
print("\nTDS Sections:")
print(df["TDS_Section"].value_counts())

# ============================================================
# FEATURES & LABELS
# ============================================================
X = df["Transaction_Text"]
y = df["TDS_Section"]

# ============================================================
# TRAIN TEST SPLIT
# ============================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print("\nTraining Records :", len(X_train))
print("Testing Records  :", len(X_test))

# ============================================================
# TF-IDF
# ============================================================
print("\nConverting Text To Numbers...")
vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
X_train_vector = vectorizer.fit_transform(X_train)
X_test_vector = vectorizer.transform(X_test)
print("Vectorization Completed!")

# ============================================================
# MODEL TRAINING
# ============================================================
print("\nTraining TDS Model...")
model = MultinomialNB()
model.fit(X_train_vector, y_train)

# ============================================================
# PREDICTION
# ============================================================
predictions = model.predict(X_test_vector)

# ============================================================
# EVALUATION METRICS
# ============================================================
accuracy = accuracy_score(y_test, predictions)
print("\nModel Accuracy :", round(accuracy, 4))

print("\nClassification Report:")
print(classification_report(y_test, predictions))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))

# ============================================================
# SAVE MODEL
# ============================================================
joblib.dump(model, "tds-ai/models/tds_model.pkl")
joblib.dump(vectorizer, "tds-ai/models/tds_vectorizer.pkl")
print("\nModel Saved Successfully!")

# ============================================================
# LOAD MODEL
# ============================================================
loaded_model = joblib.load("tds-ai/models/tds_model.pkl")
loaded_vectorizer = joblib.load("tds-ai/models/tds_vectorizer.pkl")
print("Model Loaded Successfully!")

# ============================================================
# SAMPLE TESTING WITH DYNAMIC TAX MATHEMATICS
# ============================================================
sample_transactions = [
    "CA fees paid",
    "Office rent paid",
    "Commission paid to broker",
    "Interest paid on loan",
    "Goods purchased from vendor",
    "Contractor payment made"
]

sample_amounts = [50000, 80000, 25000, 60000, 150000, 90000]

sample_vector = loaded_vectorizer.transform(sample_transactions)
sample_predictions = loaded_model.predict(sample_vector)

print("\n" + "=" * 60)
print("TDS PREDICTIONS")
print("=" * 60)

tds_rates = {
    "194C": 1,
    "194H": 5,
    "194I": 10,
    "194J": 10,
    "194A": 10,
    "194Q": 0.1
}

for transaction, amount, section in zip(sample_transactions, sample_amounts, sample_predictions):
    rate = tds_rates[section]
    tds_amount = round((amount * rate) / 100, 2)
    net_payment = round(amount - tds_amount, 2)
    
    print("\nTransaction :", transaction)
    print("Amount       :", amount)
    print("Section      :", section)
    print("TDS Rate     :", str(rate) + "%")
    print("TDS Amount   :", tds_amount)
    print("Net Payment  :", net_payment)
    print("-" * 50)

print("\nDay 16 Completed Successfully!")
