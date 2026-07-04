import os
import logging
import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "core"))

from config.paths import (
    ACCOUNTING_OUTPUT_DIR,
    LEDGER_OUTPUT_DIR
)

from ledger_rules import (
    predict_ledger,
    predict_ledger_confidence
)

INPUT_FILE = Path(ACCOUNTING_OUTPUT_DIR) / "accounting_output.csv"
MASTER_LEDGER_FILE = Path(LEDGER_OUTPUT_DIR) / "master_ledger.csv"
LEDGER_SUMMARY_FILE = Path(LEDGER_OUTPUT_DIR) / "ledger_summary.csv"

CONFIDENCE_THRESHOLD = 0.70

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def load_data():
    return pd.read_csv(INPUT_FILE)


def classify_ledgers(df):
    ledgers = []
    confidences = []
    statuses = []

    for _, row in df.iterrows():
        text = str(row["Transaction_Text"])

        ledger = predict_ledger(text)
        confidence = predict_ledger_confidence(text)

        status = "OK"
        if confidence < CONFIDENCE_THRESHOLD:
            status = "REVIEW"

        ledgers.append(ledger)
        confidences.append(confidence)
        statuses.append(status)

    df["ML_Ledger"] = ledgers
    df["Ledger_Confidence"] = confidences
    df["Ledger_Status"] = statuses

    return df


def generate_master_ledger(df):
    grouped = df.groupby("ML_Ledger", as_index=False)["Amount"].sum()
    grouped.to_csv(MASTER_LEDGER_FILE, index=False)
    return grouped


def generate_summary(df):
    summary = df.groupby("ML_Ledger")["Amount"].sum().reset_index()
    summary.to_csv(LEDGER_SUMMARY_FILE, index=False)


def generate_individual_ledgers(df):
    for ledger in df["ML_Ledger"].dropna().unique():
        ledger_df = df[df["ML_Ledger"] == ledger]

        safe_name = str(ledger).replace(" ", "_").lower()
        file_path = Path(LEDGER_OUTPUT_DIR) / f"{safe_name}.csv"

        ledger_df.to_csv(file_path, index=False)


def run_pipeline():
    logger.info("Starting Ledger Pipeline")

    Path(LEDGER_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    df = load_data()
    df = classify_ledgers(df)

    generate_master_ledger(df)
    generate_summary(df)
    generate_individual_ledgers(df)

    logger.info("Ledger Pipeline Completed")


if __name__ == "__main__":
    run_pipeline()
