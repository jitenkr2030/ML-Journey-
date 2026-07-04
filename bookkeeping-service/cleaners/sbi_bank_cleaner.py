import pandas as pd
from pathlib import Path
import logging
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from config.paths import (
    BANK_STATEMENT_FILE,
    CLEAN_BANK_FILE
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class SBIBankCleaner:
    def __init__(self, file_path):
        self.file_path = Path(file_path)

    def validate_input(self):
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Input file not found: {self.file_path}"
            )

        logging.info(
            f"Input file found: {self.file_path}"
        )

    def clean_amount(self, value):
        if pd.isna(value):
            return 0.0

        try:
            cleaned = (
                str(value)
                .replace(",", "")
                .replace('"', "")
                .replace("CR", "")
                .replace("DR", "")
                .strip()
            )

            if cleaned == "":
                return 0.0

            return float(cleaned)

        except Exception:
            return 0.0

    def load_raw_data(self):
        self.validate_input()

        df = pd.read_csv(
            self.file_path,
            header=None,
            on_bad_lines="skip",
            low_memory=False,
            dtype=str
        )

        logging.info(
            f"Raw rows loaded: {len(df)}"
        )

        return df

    def is_transaction_row(self, row):
        if len(row) < 8:
            return False

        value_date = str(row[0]).strip()

        if "-" in value_date:
            return True

        return False

    def extract_transactions(self, df):
        cleaned_rows = []

        for _, row in df.iterrows():
            row_values = row.fillna("").tolist()

            if not self.is_transaction_row(row_values):
                continue

            try:
                value_date = str(row_values[0]).strip()
                posting_date = str(row_values[1]).strip()
                narration = str(row_values[2]).strip()
                reference = str(row_values[3]).strip()
                description = str(row_values[4]).strip()

                debit = self.clean_amount(row_values[5])
                credit = self.clean_amount(row_values[6])
                balance = self.clean_amount(row_values[7])

                if debit > 0:
                    amount = debit
                    txn_type = "Debit"
                elif credit > 0:
                    amount = credit
                    txn_type = "Credit"
                else:
                    amount = 0.0
                    txn_type = "Unknown"

                transaction_text = (
                    f"{narration} {description}"
                ).strip()

                cleaned_rows.append({
                    "Date": value_date,
                    "Posting_Date": posting_date,
                    "Transaction_Text": transaction_text,
                    "Reference": reference,
                    "Debit": debit,
                    "Credit": credit,
                    "Amount": amount,
                    "Type": txn_type,
                    "Balance": balance
                })

            except Exception as e:
                logging.warning(
                    f"Skipped malformed row: {e}"
                )

        return pd.DataFrame(cleaned_rows)

    def remove_invalid_transactions(self, df):
        before = len(df)

        df = df[
            df["Amount"] > 0
        ].copy()

        df = df.reset_index(drop=True)

        after = len(df)

        logging.info(
            f"Removed invalid rows: {before - after}"
        )

        return df

    def save(self, df):
        Path(CLEAN_BANK_FILE).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_csv(
            CLEAN_BANK_FILE,
            index=False
        )

        logging.info(
            f"Clean bank statement saved: {CLEAN_BANK_FILE}"
        )


def run():
    logging.info(
        "Starting SBI Bank Cleaner"
    )

    cleaner = SBIBankCleaner(
        BANK_STATEMENT_FILE
    )

    raw_df = cleaner.load_raw_data()

    clean_df = cleaner.extract_transactions(
        raw_df
    )

    clean_df = cleaner.remove_invalid_transactions(
        clean_df
    )

    cleaner.save(clean_df)

    logging.info(
        f"Total cleaned transactions: {len(clean_df)}"
    )

    logging.info(
        "SBI Bank Cleaner Completed"
    )


if __name__ == "__main__":
    run()
