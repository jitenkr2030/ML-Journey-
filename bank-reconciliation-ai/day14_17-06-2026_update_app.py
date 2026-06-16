import pandas as pd
from difflib import SequenceMatcher

print("\nBank Reconciliation AI - Day 14")

# ============================================================
# LOAD DATASET
# ============================================================

print("\nLoading Dataset...")

df = pd.read_csv(
    "bank-reconciliation-ai/datasets/bank_reconciliation_5000.csv"
)

print("\nDataset Preview:")
print(df.head())

print("\nTotal Records :", len(df))

print("\nDataset Columns:")
print(df.columns.tolist())

print("\nActual Dataset Status Distribution:")
print(df["Status"].value_counts())

# ============================================================
# DESCRIPTION SIMILARITY
# ============================================================

def text_similarity(text1, text2):

    return SequenceMatcher(
        None,
        str(text1).lower(),
        str(text2).lower()
    ).ratio()

# ============================================================
# RECONCILIATION ENGINE
# ============================================================

results = []

for _, row in df.iterrows():

    score = 0

    # ========================================================
    # AMOUNT MATCH
    # ========================================================

    if row["Book_Amount"] == row["Bank_Amount"]:
        score += 40

    # ========================================================
    # REFERENCE MATCH
    # ========================================================

    if (
        str(row["Book_Reference"])
        ==
        str(row["Bank_Reference"])
    ):
        score += 25

    # ========================================================
    # CHEQUE MATCH
    # ========================================================

    if (
        str(row["Book_Cheque"])
        ==
        str(row["Bank_Cheque"])
    ):
        score += 20

    # ========================================================
    # DATE MATCH
    # ========================================================

    if row["Book_Date"] == row["Bank_Date"]:
        score += 10

    # ========================================================
    # DESCRIPTION MATCH
    # ========================================================

    similarity = text_similarity(
        row["Book_Description"],
        row["Bank_Description"]
    )

    if similarity >= 0.70:
        score += 5

    # ========================================================
    # FINAL STATUS
    # ========================================================

    if score >= 90:
        status = "Matched"

    elif score >= 60:
        status = "Possible Match"

    else:
        status = "Unmatched"

    # ========================================================
    # STORE RESULT
    # ========================================================

    results.append({

        "Book_Description":
            row["Book_Description"],

        "Bank_Description":
            row["Bank_Description"],

        "Book_Amount":
            row["Book_Amount"],

        "Bank_Amount":
            row["Bank_Amount"],

        "Book_Date":
            row["Book_Date"],

        "Bank_Date":
            row["Bank_Date"],

        "Book_Reference":
            row["Book_Reference"],

        "Bank_Reference":
            row["Bank_Reference"],

        "Book_Cheque":
            row["Book_Cheque"],

        "Bank_Cheque":
            row["Bank_Cheque"],

        "Description_Similarity":
            round(similarity, 2),

        "Match_Score":
            score,

        "Predicted_Status":
            status,

        "Actual_Status":
            row["Status"]
    })

# ============================================================
# RESULTS DATAFRAME
# ============================================================

results_df = pd.DataFrame(results)

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("RECONCILIATION SUMMARY")
print("=" * 60)

print(
    results_df["Predicted_Status"].value_counts()
)

matched_count = len(
    results_df[
        results_df["Predicted_Status"] == "Matched"
    ]
)

possible_count = len(
    results_df[
        results_df["Predicted_Status"] == "Possible Match"
    ]
)

unmatched_count = len(
    results_df[
        results_df["Predicted_Status"] == "Unmatched"
    ]
)

print("\nMatched Records :", matched_count)
print("Possible Matches :", possible_count)
print("Unmatched Records :", unmatched_count)

# ============================================================
# MATCH PERCENTAGE
# ============================================================

match_percentage = round(
    (
        matched_count /
        len(results_df)
    ) * 100,
    2
)

print(
    "\nMatch Percentage :",
    match_percentage,
    "%"
)

# ============================================================
# SAMPLE RESULTS
# ============================================================

print("\n" + "=" * 60)
print("SAMPLE RESULTS")
print("=" * 60)

print(results_df.head(20))

# ============================================================
# TOP UNMATCHED
# ============================================================

print("\n" + "=" * 60)
print("TOP UNMATCHED RECORDS")
print("=" * 60)

print(
    results_df[
        results_df["Predicted_Status"] == "Unmatched"
    ].head(10)
)

# ============================================================
# SAVE RESULTS
# ============================================================

results_df.to_csv(
    "bank-reconciliation-ai/results_day14.csv",
    index=False
)

print("\nResults Saved Successfully!")

print("\nDay 14 Completed Successfully!")
