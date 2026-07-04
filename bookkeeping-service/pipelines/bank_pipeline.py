import os
import logging
import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")
sys.path.append(str(BASE_DIR))

from core.utils import hybrid_bank_reconciliation
from config.paths import (
    ACCOUNTING_OUTPUT_DIR,
    PROCESSED_DIR,
    BANKING_OUTPUT_DIR
)

# PATHS
BOOK_FILE = Path(ACCOUNTING_OUTPUT_DIR) / "accounting_output.csv"
BANK_FILE = Path(PROCESSED_DIR) / "clean_bank_statement.csv"

OUTPUT_DIR = Path(BANKING_OUTPUT_DIR)
OUTPUT_FILE = OUTPUT_DIR / "bank_reconciliation_output.csv"
MANUAL_REVIEW_FILE = OUTPUT_DIR / "bank_manual_review.csv"

# LOGGING
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# LOAD DATA
def load_data():
    if not BOOK_FILE.exists():
        raise FileNotFoundError(f"Missing: {BOOK_FILE}")

    if not BANK_FILE.exists():
        raise FileNotFoundError(f"Missing: {BANK_FILE}")

    book_df = pd.read_csv(BOOK_FILE)
    bank_df = pd.read_csv(BANK_FILE)

    logger.info(f"Loaded book records: {len(book_df)}")
    logger.info(f"Loaded bank records: {len(bank_df)}")

    return book_df, bank_df

# RECONCILE
def reconcile(book_df, bank_df):
    results = []
    used_bank_rows = set()

    bank_df_records = []
    for idx, row in bank_df.iterrows():
        bank_df_records.append({
            "index": idx,
            "text": str(row["Transaction_Text"]).strip(),
            "amount": float(row["Amount"])
        })

    for _, book_row in book_df.iterrows():
        book_text = str(book_row["Transaction_Text"]).strip()
        book_amount = float(book_row["Amount"])
        matched = False

        ml_profile = hybrid_bank_reconciliation(
            book_text,
            book_amount,
            0.0
        )

        for bank_record in bank_df_records:
            bank_idx = bank_record["index"]

            if bank_idx in used_bank_rows:
                continue

            bank_text = bank_record["text"]
            bank_amount = bank_record["amount"]

            if abs(book_amount - bank_amount) < 0.01:
                results.append({
                    "Book_Transaction": book_text,
                    "Bank_Transaction": bank_text,
                    "Book_Amount": book_amount,
                    "Bank_Amount": bank_amount,
                    "Status": "Matched",
                    "Confidence": ml_profile.get("confidence", 1.0),
                    "Source": "RULE"
                })
                used_bank_rows.add(bank_idx)
                matched = True
                break

            elif ml_profile.get("status") == "Fuzzy Matched":
                results.append({
                    "Book_Transaction": book_text,
                    "Bank_Transaction": bank_text,
                    "Book_Amount": book_amount,
                    "Bank_Amount": bank_amount,
                    "Status": "Fuzzy Matched",
                    "Confidence": ml_profile.get("confidence", 0.7),
                    "Source": "ML"
                })
                used_bank_rows.add(bank_idx)
                matched = True
                break

        if not matched:
            results.append({
                "Book_Transaction": book_text,
                "Bank_Transaction": None,
                "Book_Amount": book_amount,
                "Bank_Amount": None,
                "Status": "Missing Entry",
                "Confidence": 0.0,
                "Source": "RULE"
            })

    for bank_record in bank_df_records:
        if bank_record["index"] not in used_bank_rows:
            results.append({
                "Book_Transaction": None,
                "Bank_Transaction": bank_record["text"],
                "Book_Amount": None,
                "Bank_Amount": bank_record["amount"],
                "Status": "Unrecorded Bank Entry",
                "Confidence": 0.0,
                "Source": "RULE"
            })

    return pd.DataFrame(results)

# SAVE OUTPUTS
def save_outputs(df):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_FILE, index=False)

    review_df = df[
        df["Status"].isin([
            "Missing Entry",
            "Unrecorded Bank Entry"
        ])
    ]

    review_df.to_csv(MANUAL_REVIEW_FILE, index=False)

    logger.info(f"Saved: {OUTPUT_FILE}")
    logger.info(f"Saved: {MANUAL_REVIEW_FILE}")

# MAIN
def run_pipeline():
    logger.info("Starting Bank Pipeline")

    book_df, bank_df = load_data()
    result_df = reconcile(book_df, bank_df)
    save_outputs(result_df)

    logger.info("Bank Pipeline Completed")

if __name__ == "__main__":
    run_pipeline()
