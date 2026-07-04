import logging
import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from config.paths import (
    DAYBOOK_FILE,
    TRANSACTIONS_FILE
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def clean_amount(value):
    if pd.isna(value):
        return 0.0

    value = str(value).replace(",", "").strip()

    if value == "":
        return 0.0

    try:
        return float(value)
    except Exception:
        return 0.0


def find_header(df):
    for idx, row in df.iterrows():
        row_values = [
            str(x).strip()
            for x in row.tolist()
        ]

        if "Particulars" in row_values:
            return idx

    return None


def load_raw():
    input_file = Path(DAYBOOK_FILE)

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}"
        )

    logger.info(
        f"Input file found: {input_file}"
    )

    raw_df = pd.read_csv(
        input_file,
        header=None,
        dtype=str,
        low_memory=False
    )

    logger.info(
        f"Raw rows loaded: {len(raw_df)}"
    )

    return raw_df


def standardize():
    raw_df = load_raw()

    header_index = find_header(raw_df)

    if header_index is None:
        raise ValueError(
            "Could not detect Tally header row"
        )

    logger.info(
        f"Header row detected at: {header_index}"
    )

    df = pd.read_csv(
        DAYBOOK_FILE,
        skiprows=header_index
    )

    df.columns = df.columns.str.strip()

    required_columns = [
        "Date",
        "Particulars",
        "Debit Amount",
        "Credit Amount"
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(
                f"Missing required column: {col}"
            )

    df["Debit Amount"] = df[
        "Debit Amount"
    ].apply(clean_amount)

    df["Credit Amount"] = df[
        "Credit Amount"
    ].apply(clean_amount)

    df["Amount"] = (
        df["Debit Amount"] +
        df["Credit Amount"]
    )

    df["Transaction_Text"] = df[
        "Particulars"
    ].astype(str).str.strip()

    df["Type"] = df.apply(
        lambda row:
        "Debit"
        if row["Debit Amount"] > 0
        else "Credit",
        axis=1
    )

    clean_df = df[
        [
            "Date",
            "Transaction_Text",
            "Debit Amount",
            "Credit Amount",
            "Amount",
            "Type"
        ]
    ]

    clean_df = clean_df[
        clean_df["Transaction_Text"].notna()
    ]

    clean_df = clean_df[
        clean_df["Amount"] > 0
    ]

    clean_df = clean_df.reset_index(
        drop=True
    )

    logger.info(
        f"Valid cleaned rows: {len(clean_df)}"
    )

    return clean_df


def save(df):
    output_file = Path(TRANSACTIONS_FILE)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        output_file,
        index=False
    )

    logger.info(
        f"Cleaned transactions saved: {output_file}"
    )


def clean_daybook():
    logger.info(
        "Starting Tally DayBook Cleaner"
    )

    df = standardize()

    save(df)

    logger.info(
        "Tally DayBook Cleaner Completed"
    )


if __name__ == "__main__":
    clean_daybook()
