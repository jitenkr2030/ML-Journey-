import pandas as pd
import joblib
import os
import logging
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "upi_reconciliation_5000.csv")
MODEL_DIR = os.path.join(os.path.dirname(BASE_DIR), "app", "models")

logger.info("Loading UPI dataset...")
df = pd.read_csv(DATASET_PATH)
logger.info(f"Total records: {len(df)}")
logger.info(f"\n{df['Status'].value_counts()}")

# ============================================================
# FEATURE ENGINEERING
# ============================================================

def build_features(row):
    features = (
        f"{row['Book_Description']} "
        f"{row['Bank_Description']} "
        f"{row['Book_Amount']} "
        f"{row['Bank_Amount']} "
        f"{row['Book_Reference']} "
        f"{row['Bank_Reference']} "
        f"{row['UPI_ID']} "
        f"{row['UPI_Type']} "
        f"{row['UPI_App']}"
    )
    return features

df["Features"] = df.apply(build_features, axis=1)

# Also build numeric features
df["AmountDiff"] = abs(df["Book_Amount"] - df["Bank_Amount"])
df["AmountDiffPct"] = df["AmountDiff"] / df["Book_Amount"].abs().clip(lower=1) * 100
df["HasBankDesc"] = (df["Bank_Description"].notna() & (df["Bank_Description"] != "")).astype(int)
df["RefMatch"] = (df["Book_Reference"] == df["Bank_Reference"]).astype(int)
df["AmountMatch"] = (df["AmountDiff"] < 0.01).astype(int)

X_text = df["Features"]
y = df["Status"]

X_train, X_test, y_train, y_test = train_test_split(
    X_text, y, test_size=0.20, random_state=42, stratify=y
)

# ============================================================
# TF-IDF VECTORIZER
# ============================================================
logger.info("Training TF-IDF vectorizer...")
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# ============================================================
# MODEL COMPARISON
# ============================================================
models = {
    "MultinomialNB": MultinomialNB(alpha=0.1),
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
    "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
}

best_model = None
best_accuracy = 0
best_name = ""

for name, model in models.items():
    logger.info(f"\nTraining {name}...")
    model.fit(X_train_vec, y_train)
    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"{name} Accuracy: {accuracy:.4f}")
    logger.info(f"\n{classification_report(y_test, y_pred)}")

    if accuracy > best_accuracy:
        best_accuracy = accuracy
        best_model = model
        best_name = name

logger.info(f"\n{'='*50}")
logger.info(f"Best model: {best_name} (Accuracy: {best_accuracy:.4f})")

# ============================================================
# SAVE MODEL
# ============================================================
os.makedirs(MODEL_DIR, exist_ok=True)

# Save as v3 UPI model
joblib.dump(best_model, os.path.join(MODEL_DIR, "upi_reconciliation_v3_model.pkl"))
joblib.dump(vectorizer, os.path.join(MODEL_DIR, "upi_reconciliation_v3_vectorizer.pkl"))

# Also save as main model (backup old first)
import shutil
old_model = os.path.join(MODEL_DIR, "reconciliation_v2_model.pkl")
if os.path.exists(old_model):
    shutil.copy2(old_model, os.path.join(MODEL_DIR, "reconciliation_v2_model_backup.pkl"))
    logger.info("Backed up old v2 model")

joblib.dump(best_model, os.path.join(MODEL_DIR, "reconciliation_v2_model.pkl"))
joblib.dump(vectorizer, os.path.join(MODEL_DIR, "reconciliation_v2_vectorizer.pkl"))

logger.info(f"\nModels saved to: {MODEL_DIR}")
logger.info(f"  - upi_reconciliation_v3_model.pkl")
logger.info(f"  - upi_reconciliation_v3_vectorizer.pkl")
logger.info(f"  - reconciliation_v2_model.pkl (updated)")
logger.info(f"  - reconciliation_v2_vectorizer.pkl (updated)")
logger.info("Training complete!")
