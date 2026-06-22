import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report

print("\nBank Reconciliation AI V3 - Feature Engineering")

# ============================================================
# LOAD DATASET
# ============================================================

df = pd.read_csv(
    "bank-reconciliation-ai/datasets/bank_reconciliation_v2_6000.csv"
)

print("\nDataset Preview:")
print(df.head())

print("\nTotal Records:", len(df))

# ============================================================
# CONVERT DATE
# ============================================================

df["Book_Date"] = pd.to_datetime(
    df["Book_Date"]
)

df["Bank_Date"] = pd.to_datetime(
    df["Bank_Date"]
)

# ============================================================
# FEATURE ENGINEERING
# ============================================================

# 1 Amount Difference
df["Amount_Difference"] = abs(

    df["Book_Amount"] -
    df["Bank_Amount"]

)

# 2 Percentage Difference
df["Percentage_Difference"] = abs(

    (
        df["Book_Amount"] -
        df["Bank_Amount"]
    ) / df["Book_Amount"]

) * 100

# 3 Date Difference
df["Date_Difference"] = abs(

    (
        df["Book_Date"] -
        df["Bank_Date"]
    ).dt.days

)

# 4 Reference Match
df["Reference_Match"] = (

    df["Book_Reference"] ==
    df["Bank_Reference"]

).astype(int)

# 5 Cheque Match
df["Cheque_Match"] = (

    df["Book_Cheque"] ==
    df["Bank_Cheque"]

).astype(int)

print("\nEngineered Features Preview:")
print(

    df[
        [
            "Amount_Difference",
            "Percentage_Difference",
            "Date_Difference",
            "Reference_Match",
            "Cheque_Match"
        ]
    ].head()

)

# ============================================================
# FEATURES
# ============================================================

X = df[
    [
        "Amount_Difference",
        "Percentage_Difference",
        "Date_Difference",
        "Reference_Match",
        "Cheque_Match"
    ]
]

y = df["Status"]

# ============================================================
# SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y

)

# ============================================================
# MODEL
# ============================================================

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(
    X_train,
    y_train
)

# ============================================================
# EVALUATION
# ============================================================

predictions = model.predict(
    X_test
)

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\nModel Accuracy:", round(
    accuracy,
    4
))

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions
    )
)

# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame({

    "Feature": X.columns,
    "Importance": model.feature_importances_

})

print("\nFeature Importance:")
print(
    importance.sort_values(
        by="Importance",
        ascending=False
    )
)

# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(

    model,
    "bank-reconciliation-ai/models/reconciliation_v3_feature_model.pkl"

)

print("\nModel Saved Successfully!")

# ============================================================
# TEST CASES
# ============================================================

test_data = pd.DataFrame([

    [0, 0.00, 0, 1, 1],
    [5, 0.05, 2, 1, 1],
    [0, 0.00, 0, 1, 1],
    [15000, 100.00, 0, 0, 0],
    [30000, 300.00, 5, 0, 0]

], columns=[

    "Amount_Difference",
    "Percentage_Difference",
    "Date_Difference",
    "Reference_Match",
    "Cheque_Match"

])

results = model.predict(
    test_data
)

print("\n" + "=" * 60)
print("FEATURE ENGINEERING TEST RESULTS")
print("=" * 60)

for i, result in enumerate(results):

    print("\nCase", i + 1)
    print(test_data.iloc[i].to_dict())
    print("Predicted Status:", result)
    print("-" * 60)

print("\nDay 19 Feature Engineering Completed!")

