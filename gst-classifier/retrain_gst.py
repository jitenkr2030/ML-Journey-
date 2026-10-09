import pandas as pd
import joblib
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score

print(f"sklearn version: {sklearn.__version__}")

df = pd.read_csv("gst-classifier/datasets/gst_invoices_5000.csv")
print(f"Dataset: {len(df)} records")
print(df["Category"].value_counts())

X = df["Invoice_Text"]
y = df["Category"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

model = MultinomialNB()
model.fit(X_train_vec, y_train)

accuracy = accuracy_score(y_test, model.predict(X_test_vec))
print(f"Accuracy: {accuracy:.4f}")

import os
for d in ["gst-classifier/models", "backend/app/models", "deploy/backend/app/models"]:
    os.makedirs(d, exist_ok=True)

for d in ["gst-classifier/models", "backend/app/models", "deploy/backend/app/models"]:
    joblib.dump(model, f"{d}/gst_classifier_day11.pkl")
    joblib.dump(vectorizer, f"{d}/gst_vectorizer_day11.pkl")
    print(f"Saved to {d}/")

print("Done! All GST models retrained with sklearn", sklearn.__version__)
