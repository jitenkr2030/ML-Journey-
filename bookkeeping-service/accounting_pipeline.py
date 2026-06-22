import os
import logging
import joblib
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

UPLOADS_DIR = "bookkeeping-service/uploads"
OUTPUTS_DIR = "bookkeeping-service/outputs"

MODEL_PATH = "accounting-assistant/models/accounting_assistant_model.pkl"
VECTORIZER_PATH = "accounting-assistant/models/accounting_assistant_vectorizer.pkl"

INPUT_FILE = os.path.join(
    UPLOADS_DIR,
    "transactions.csv"
)

OUTPUT_FILE = os.path.join(
    OUTPUTS_DIR,
    "accounting_output.csv"
)

MANUAL_REVIEW_FILE = os.path.join(
    OUTPUTS_DIR,
    "manual_review.csv"
)

CONFIDENCE_THRESHOLD = 0.60


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# ACCOUNTING RULES
# ============================================================

ACCOUNTING_RULES = {

    "Payroll": {
        "ledger": "Salary Expense",
        "journal": "Salary Expense Dr | To Bank",
        "statement": "Expense"
    },

    "Rent": {
        "ledger": "Rent Expense",
        "journal": "Rent Expense Dr | To Bank",
        "statement": "Expense"
    },

    "GST": {
        "ledger": "GST Payable",
        "journal": "GST Payable Dr | To Bank",
        "statement": "Liability"
    },

    "Asset": {
        "ledger": "Fixed Asset",
        "journal": "Fixed Asset Dr | To Bank",
        "statement": "Asset"
    },

    "Utilities": {
        "ledger": "Utilities Expense",
        "journal": "Utilities Expense Dr | To Bank",
        "statement": "Expense"
    },

    "Marketing": {
        "ledger": "Marketing Expense",
        "journal": "Marketing Expense Dr | To Bank",
        "statement": "Expense"
    },

    "Revenue": {
        "ledger": "Sales Revenue",
        "journal": "Bank Dr | To Sales Revenue",
        "statement": "Income"
    },

    "Bank Charges": {
        "ledger": "Bank Charges Expense",
        "journal": "Bank Charges Expense Dr | To Bank",
        "statement": "Expense"
    }

}


# ============================================================
# LOAD MODELS
# ============================================================

def load_models():

    model = joblib.load(
        MODEL_PATH
    )

    vectorizer = joblib.load(
        VECTORIZER_PATH
    )

    logging.info(
        "Models loaded successfully"
    )

    return model, vectorizer


# ============================================================
# LOAD TRANSACTIONS
# ============================================================

def load_transactions():

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    required_columns = [
        "Transaction_Text",
        "Amount"
    ]

    for col in required_columns:

        if col not in df.columns:

            raise ValueError(
                f"Missing required column: {col}"
            )

    logging.info(
        f"Loaded {len(df)} transactions"
    )

    return df


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_transactions(
    df,
    model,
    vectorizer
):

    vectors = vectorizer.transform(
        df["Transaction_Text"]
    )

    predictions = model.predict(
        vectors
    )

    probabilities = model.predict_proba(
        vectors
    )

    df["Predicted_Category"] = predictions
    df["Confidence"] = probabilities.max(
        axis=1
    )

    ledgers = []
    journals = []
    statements = []
    review_flags = []

    for category, confidence in zip(
        df["Predicted_Category"],
        df["Confidence"]
    ):

        if category in ACCOUNTING_RULES:

            rule = ACCOUNTING_RULES[
                category
            ]

            ledgers.append(
                rule["ledger"]
            )

            journals.append(
                rule["journal"]
            )

            statements.append(
                rule["statement"]
            )

        else:

            ledgers.append(
                "Manual Review"
            )

            journals.append(
                "Manual Journal Required"
            )

            statements.append(
                "Unknown"
            )

        if confidence < CONFIDENCE_THRESHOLD:

            review_flags.append(
                "REVIEW"
            )

        else:

            review_flags.append(
                "OK"
            )

    df["Ledger"] = ledgers
    df["Journal"] = journals
    df["Financial_Statement"] = statements
    df["Status"] = review_flags

    return df


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(df):

    os.makedirs(
        OUTPUTS_DIR,
        exist_ok=True
    )

    final_columns = [

        "Transaction_Text",
        "Amount",
        "Predicted_Category",
        "Confidence",
        "Ledger",
        "Journal",
        "Financial_Statement",
        "Status"

    ]

    df = df[final_columns]

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    review_df = df[
        df["Status"] == "REVIEW"
    ]

    review_df.to_csv(
        MANUAL_REVIEW_FILE,
        index=False
    )

    logging.info(
        f"Output saved: {OUTPUT_FILE}"
    )

    logging.info(
        f"Manual review saved: {MANUAL_REVIEW_FILE}"
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline():

    logging.info(
        "Starting Accounting Pipeline"
    )

    model, vectorizer = load_models()

    df = load_transactions()

    processed_df = classify_transactions(
        df,
        model,
        vectorizer
    )

    save_outputs(
        processed_df
    )

    logging.info(
        "Accounting Pipeline Completed"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_pipeline()

