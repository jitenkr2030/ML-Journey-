import os
import sys
from pathlib import Path
import logging
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")
sys.path.append(str(BASE_DIR))

from core.ml_accounting_engine import MLAccountingEngine
from core.accounting_rules import get_accounting_rule
from config.paths import (
    TRANSACTIONS_FILE,
    ACCOUNTING_OUTPUT_DIR
)

INPUT_FILE = TRANSACTIONS_FILE
OUTPUT_FILE = ACCOUNTING_OUTPUT_DIR + "/accounting_output.csv"
MANUAL_REVIEW_FILE = ACCOUNTING_OUTPUT_DIR + "/manual_review.csv"

CONFIDENCE_THRESHOLD = 0.60

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def load_transactions():
    df = pd.read_csv(INPUT_FILE)
    logger.info(f"Loaded {len(df)} transactions")
    return df


def classify_transactions(df):
    engine = MLAccountingEngine()
    results = engine.batch_predict(
        df["Transaction_Text"].tolist()
    )

    categories = []
    confidences = []
    ledgers = []
    journals = []
    statements = []
    statuses = []

    for result in results:
        category = result["category"]
        confidence = result["confidence"]

        rule = get_accounting_rule(category)

        categories.append(category)
        confidences.append(confidence)
        ledgers.append(rule["ledger"])
        journals.append(rule["journal"])
        statements.append(rule["statement"])

        if confidence < CONFIDENCE_THRESHOLD:
            statuses.append("REVIEW")
        else:
            statuses.append("OK")

    df["Predicted_Category"] = categories
    df["Confidence"] = confidences
    df["Ledger"] = ledgers
    df["Journal"] = journals
    df["Financial_Statement"] = statements
    df["Status"] = statuses

    return df


def save_outputs(df):
    df.to_csv(OUTPUT_FILE, index=False)

    review_df = df[df["Status"] == "REVIEW"]
    review_df.to_csv(MANUAL_REVIEW_FILE, index=False)

    logger.info("Accounting Pipeline Completed")


def run_pipeline():
    df = load_transactions()
    processed_df = classify_transactions(df)
    save_outputs(processed_df)


if __name__ == "__main__":
    run_pipeline()
