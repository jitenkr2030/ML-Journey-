import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report

print("\nPSARA Compliance ML Engine - Day 17")

# ============================================================
# LOAD DATASET
# ============================================================
print("\nLoading PSARA Compliance Dataset...")
df = pd.read_csv("psara-ai/datasets/psara_dataset_5500.csv")

print("\nDataset Preview:")
print(df.head())
print("\nTotal Records:", len(df))

# ============================================================
# FEATURE ENGINEERING (Building Document Metadata String tokens)
# ============================================================
df["Features"] = (
    df["Document_Name"].astype(str) + " " +
    df["Document_Status"].astype(str) + " " +
    df["Training_Completed"].astype(str) + " " +
    df["Police_Verified"].astype(str) + " " +
    df["Medical_Fit"].astype(str) + " " +
    df["State"].astype(str)
)

X = df["Features"]
y = df["Risk_Level"]

# ============================================================
# SPLIT
# ============================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

# ============================================================
# TF-IDF VECTORIZATION
# ============================================================
print("\nVectorizing Text Features...")
vectorizer = TfidfVectorizer()
X_train_vector = vectorizer.fit_transform(X_train)
X_test_vector = vectorizer.transform(X_test)

# ============================================================
# MODEL TRAINING
# ============================================================
print("Training Naive Bayes PSARA Risk Classifier...")
model = MultinomialNB()
model.fit(X_train_vector, y_train)

# ============================================================
# EVALUATION
# ============================================================
predictions = model.predict(X_test_vector)
accuracy = accuracy_score(y_test, predictions)

print("\nModel Accuracy:", round(accuracy, 4))
print("\nClassification Report:")
print(classification_report(y_test, predictions))

# ============================================================
# SAVE MODEL
# ============================================================
joblib.dump(model, "psara-ai/psara_model.pkl")
joblib.dump(vectorizer, "psara-ai/psara_vectorizer.pkl")
print("\nModel Artifacts Saved Successfully!")

# ============================================================
# LOAD MODEL
# ============================================================
loaded_model = joblib.load("psara-ai/psara_model.pkl")
loaded_vectorizer = joblib.load("psara-ai/psara_vectorizer.pkl")
print("Model Artifacts Loaded & Verified Successfully!")

# ============================================================
# TEST PREDICTIONS
# ============================================================
test_cases = [
    "Police Verification Expired No No Delhi",
    "Training Certificate Verified Yes Yes Haryana",
    "ID Card Missing Yes No Punjab",
    "Medical Fitness Expired No Yes Delhi",
    "GST Certificate Verified Yes Yes Rajasthan"
]

test_vector = loaded_vectorizer.transform(test_cases)
results = loaded_model.predict(test_vector)

print("\n" + "=" * 60)
print("PSARA RISK PREDICTIONS")
print("=" * 60)

for case, result in zip(test_cases, results):
    print(f"\nInput          : {case}")
    print(f"Predicted Risk : {result}")
    print("-" * 60)

print("\nDay 17 PSARA ML Completed!")
