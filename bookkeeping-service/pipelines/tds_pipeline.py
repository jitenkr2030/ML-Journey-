import os
import re
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
    TDS_OUTPUT_DIR
)

from tds_rules import (
    predict_tds_section,
    predict_tds_confidence,
    calculate_tds
)

INPUT_FILE = Path(ACCOUNTING_OUTPUT_DIR) / "accounting_output.csv"
OUTPUT_FILE = Path(TDS_OUTPUT_DIR) / "tds_output.csv"
SUMMARY_FILE = Path(TDS_OUTPUT_DIR) / "tds_summary.csv"
MANUAL_REVIEW_FILE = Path(TDS_OUTPUT_DIR) / "tds_manual_review.csv"

CONFIDENCE_THRESHOLD = 0.70

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def validate_pan(text):
    pattern = r"[A-Z]{5}[0-9]{4}[A-Z]{1}"
    if re.search(pattern, str(text)):
        return "Valid"
    return "Missing"


def load_data():
    df = pd.read_csv(INPUT_FILE)
    return df


def process_tds(df):
    sections = []
    confidences = []
    tds_amounts = []
    pan_statuses = []
    compliance_flags = []

    for _, row in df.iterrows():
        text = str(row["Transaction_Text"])
        amount = float(row["Amount"])

        section = predict_tds_section(text)
        confidence = predict_tds_confidence(text)
        tds_amount = calculate_tds(amount)
        pan_status = validate_pan(text)

        compliance = "OK"

        if confidence < CONFIDENCE_THRESHOLD:
            compliance = "REVIEW"

        if pan_status == "Missing":
            compliance = "PAN Required"

        sections.append(section)
        confidences.append(confidence)
        tds_amounts.append(tds_amount)
        pan_statuses.append(pan_status)
        compliance_flags.append(compliance)

    df["TDS_Section"] = sections
    df["Confidence"] = confidences
    df["TDS_Amount"] = tds_amounts
    df["PAN_Status"] = pan_statuses
    df["Compliance_Status"] = compliance_flags

    return df


def generate_summary(df):
    return df.groupby("TDS_Section")["TDS_Amount"].sum().reset_index()


def save_outputs(df, summary):
    Path(TDS_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)

    review_df = df[df["Compliance_Status"].isin(["PAN Required", "REVIEW"])]
    review_df.to_csv(MANUAL_REVIEW_FILE, index=False)


def run_pipeline():
    logger.info("Starting TDS Pipeline")

    df = load_data()
    processed_df = process_tds(df)
    summary_df = generate_summary(processed_df)

    save_outputs(processed_df, summary_df)

    logger.info("TDS Pipeline Completed")


if __name__ == "__main__":
    run_pipeline()
