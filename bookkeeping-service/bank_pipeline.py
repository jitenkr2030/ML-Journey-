import os
import logging
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUTS_DIR = "bookkeeping-service/outputs"
UPLOADS_DIR = "bookkeeping-service/uploads"

BOOK_FILE = os.path.join(
    OUTPUTS_DIR,
    "accounting_output.csv"
)

BANK_FILE = os.path.join(
    UPLOADS_DIR,
    "bank_statement.csv"
)

OUTPUT_FILE = os.path.join(
    OUTPUTS_DIR,
    "bank_reconciliation_output.csv"
)

MANUAL_REVIEW_FILE = os.path.join(
    OUTPUTS_DIR,
    "bank_manual_review.csv"
)

AMOUNT_TOLERANCE = 5


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.exists(BOOK_FILE):
        raise FileNotFoundError(
            f"Missing book file: {BOOK_FILE}"
        )

    if not os.path.exists(BANK_FILE):
        raise FileNotFoundError(
            f"Missing bank file: {BANK_FILE}"
        )

    book_df = pd.read_csv(
        BOOK_FILE
    )

    bank_df = pd.read_csv(
        BANK_FILE
    )

    required_book_cols = [
        "Transaction_Text",
        "Amount"
    ]

    required_bank_cols = [
        "Transaction_Text",
        "Amount"
    ]

    for col in required_book_cols:
        if col not in book_df.columns:
            raise ValueError(
                f"Missing book column: {col}"
            )

    for col in required_bank_cols:
        if col not in bank_df.columns:
            raise ValueError(
                f"Missing bank column: {col}"
            )

    logging.info(
        f"Loaded book records: {len(book_df)}"
    )

    logging.info(
        f"Loaded bank records: {len(bank_df)}"
    )

    return book_df, bank_df


# ============================================================
# RECONCILIATION ENGINE
# ============================================================

def reconcile(book_df, bank_df):

    results = []
    used_bank_rows = set()

    for _, book_row in book_df.iterrows():

        book_text = str(
            book_row["Transaction_Text"]
        )

        book_amount = float(
            book_row["Amount"]
        )

        matched = False

        for bank_index, bank_row in bank_df.iterrows():

            if bank_index in used_bank_rows:
                continue

            bank_text = str(
                bank_row["Transaction_Text"]
            )

            bank_amount = float(
                bank_row["Amount"]
            )

            difference = abs(
                book_amount - bank_amount
            )

            # EXACT MATCH
            if (
                book_text.lower() == bank_text.lower()
                and difference == 0
            ):

                status = "Matched"
                matched = True
                used_bank_rows.add(bank_index)

            # FUZZY MATCH
            elif difference <= AMOUNT_TOLERANCE:

                status = "Fuzzy Matched"
                matched = True
                used_bank_rows.add(bank_index)

            # REVERSAL
            elif bank_amount < 0:

                status = "Reversal Entry"
                matched = True
                used_bank_rows.add(bank_index)

            else:
                continue

            results.append({

                "Book_Transaction": book_text,
                "Bank_Transaction": bank_text,
                "Book_Amount": book_amount,
                "Bank_Amount": bank_amount,
                "Difference": difference,
                "Status": status

            })

            break

        # IF NO MATCH
        if not matched:

            results.append({

                "Book_Transaction": book_text,
                "Bank_Transaction": None,
                "Book_Amount": book_amount,
                "Bank_Amount": None,
                "Difference": None,
                "Status": "Missing Entry"

            })

    # DUPLICATE CHECK
    duplicate_counts = book_df[
        "Transaction_Text"
    ].value_counts()

    for transaction, count in duplicate_counts.items():

        if count > 1:

            results.append({

                "Book_Transaction": transaction,
                "Bank_Transaction": None,
                "Book_Amount": None,
                "Bank_Amount": None,
                "Difference": None,
                "Status": "Duplicate"

            })

    return pd.DataFrame(results)


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(df):

    os.makedirs(
        OUTPUTS_DIR,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    review_df = df[
        df["Status"].isin(
            ["Missing Entry", "Duplicate"]
        )
    ]

    review_df.to_csv(
        MANUAL_REVIEW_FILE,
        index=False
    )

    logging.info(
        f"Reconciliation output saved: {OUTPUT_FILE}"
    )

    logging.info(
        f"Manual review saved: {MANUAL_REVIEW_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def run_pipeline():

    logging.info(
        "Starting Bank Reconciliation Pipeline"
    )

    book_df, bank_df = load_data()

    result_df = reconcile(
        book_df,
        bank_df
    )

    save_outputs(
        result_df
    )

    logging.info(
        "Bank Reconciliation Completed"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_pipeline()

