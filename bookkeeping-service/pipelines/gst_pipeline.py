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
    GST_OUTPUT_DIR
)

from gst_rules import (
    predict_gst_type,
    predict_gst_confidence,
    calculate_gst
)

INPUT_FILE = Path(ACCOUNTING_OUTPUT_DIR) / "accounting_output.csv"
OUTPUT_FILE = Path(GST_OUTPUT_DIR) / "gst_output.csv"
SUMMARY_FILE = Path(GST_OUTPUT_DIR) / "gst_summary.csv"
MANUAL_REVIEW_FILE = Path(GST_OUTPUT_DIR) / "gst_manual_review.csv"

CONFIDENCE_THRESHOLD = 0.70

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def load_data():
    df = pd.read_csv(INPUT_FILE)
    return df


def classify_gst(df):
    gst_types = []
    confidences = []
    gst_amounts = []
    cgst_amounts = []
    sgst_amounts = []
    review_flags = []

    for _, row in df.iterrows():
        text = str(row["Transaction_Text"]).strip()
        amount = float(row["Amount"])

        gst_type = predict_gst_type(text)
        confidence = predict_gst_confidence(text)
        gst_amount = calculate_gst(amount)

        gst_types.append(gst_type)
        confidences.append(confidence)
        gst_amounts.append(round(gst_amount, 2))
        cgst_amounts.append(round(gst_amount / 2, 2))
        sgst_amounts.append(round(gst_amount / 2, 2))

        if confidence < CONFIDENCE_THRESHOLD:
            review_flags.append("REVIEW")
        else:
            review_flags.append("OK")

    df["GST_Type"] = gst_types
    df["Confidence"] = confidences
    df["GST_Amount"] = gst_amounts
    df["CGST"] = cgst_amounts
    df["SGST"] = sgst_amounts
    df["GST_Status"] = review_flags

    return df


def generate_summary(df):
    return df.groupby("GST_Type")["GST_Amount"].sum().reset_index()


def save_outputs(df, summary):
    Path(GST_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)

    review_df = df[df["GST_Status"] == "REVIEW"]
    review_df.to_csv(MANUAL_REVIEW_FILE, index=False)


def run_pipeline():
    logger.info("Starting GST Pipeline")

    df = load_data()
    gst_df = classify_gst(df)
    summary_df = generate_summary(gst_df)

    save_outputs(gst_df, summary_df)

    logger.info("GST Pipeline Completed")


if __name__ == "__main__":
    run_pipeline()
