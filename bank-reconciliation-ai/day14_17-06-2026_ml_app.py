import pandas as pd
import joblib

from difflib import SequenceMatcher

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

print("\nBank Reconciliation ML AI - Day 14")

# ============================================================
# LOAD DATASET
# ============================================================

print("\nLoading Dataset...")

df = pd.read_csv(
    "bank-reconciliation-ai/datasets/bank_reconciliation_5000.csv"
)

print("\nDataset Shape :", df.shape)

# ============================================================
# SIMILARITY FUNCTION
# ============================================================

def similarity(text1, text2):

    return SequenceMatcher(
        None,
        str(text1).lower(),
        str(text2).lower()
    ).ratio()

# ============================================================
# FEATURE ENGINEERING
# ============================================================

print("\nCreating Features...")

df["Amount_Match"] = (
    df["Book_Amount"] == df["Bank_Amount"]
).astype(int)

df["Reference_Match"] = (
    df["Book_Reference"].astype(str)
    ==
    df["Bank_Reference"].astype(str)
).astype(int)

df["Cheque_Match"] = (
    df["Book_Cheque"].astype(str)
    ==
    df["Bank_Cheque"].astype(str)
).astype(int)

df["Date_Match"] = (
    df["Book_Date"].astype(str)
    ==
    df["Bank_Date"].astype(str)
).astype(int)

df["Amount_Difference"] = (
    abs(
        df["Book_Amount"]
        -
        df["Bank_Amount"]
    )
)

df["Description_Similarity"] = df.apply(
    lambda row: similarity(
        row["Book_Description"],
        row["Bank_Description"]
    ),
    axis=1
)

# ============================================================
# FEATURES
# ============================================================

feature_columns = [

    "Amount_Match",
    "Reference_Match",
    "Cheque_Match",
    "Date_Match",
    "Amount_Difference",
    "Description_Similarity"

]

X = df[feature_columns]

y = df["Status"]

# ============================================================
# LABEL ENCODER
# ============================================================

encoder = LabelEncoder()

y_encoded = encoder.fit_transform(y)

# ============================================================
# TRAIN TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y_encoded,

    test_size=0.20,
    random_state=42,
    stratify=y_encoded

)

print("\nTraining Records :", len(X_train))
print("Testing Records  :", len(X_test))

# ============================================================
# MODEL
# ============================================================

print("\nTraining Random Forest...")

model = RandomForestClassifier(

    n_estimators=200,
    max_depth=10,
    random_state=42

)

model.fit(
    X_train,
    y_train
)

# ============================================================
# PREDICTIONS
# ============================================================

predictions = model.predict(
    X_test
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

        target_names=encoder.classes_,
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
# FEATURE IMPORTANCE
# ============================================================

print("\n" + "=" * 60)
print("FEATURE IMPORTANCE")
print("=" * 60)

importance_df = pd.DataFrame({

    "Feature": feature_columns,
    "Importance": model.feature_importances_

})

importance_df = importance_df.sort_values(
    by="Importance",
    ascending=False
)

print(importance_df)

# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(

    model,

    "bank-reconciliation-ai/models/bank_reconciliation_ml.pkl"

)

joblib.dump(

    encoder,

    "bank-reconciliation-ai/models/bank_reconciliation_encoder.pkl"

)

print("\nModel Saved Successfully!")

# ============================================================
# SAMPLE PREDICTION
# ============================================================

print("\n" + "=" * 60)
print("SAMPLE PREDICTION")
print("=" * 60)

sample = pd.DataFrame([{

    "Amount_Match": 1,
    "Reference_Match": 1,
    "Cheque_Match": 1,
    "Date_Match": 1,
    "Amount_Difference": 0,
    "Description_Similarity": 0.95

}])

prediction = model.predict(sample)

probability = model.predict_proba(sample)

predicted_status = encoder.inverse_transform(
    prediction
)[0]

confidence = round(
    max(probability[0]) * 100,
    2
)

print(
    "Predicted Status :",
    predicted_status
)

print(
    "Confidence :",
    confidence,
    "%"
)

print("\nDay 14 ML Completed Successfully!")

