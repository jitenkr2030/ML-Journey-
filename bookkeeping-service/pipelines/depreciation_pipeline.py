import os
import logging
import pandas as pd
from pathlib import Path
import sys

# ============================================================
# BASE PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")
sys.path.append(str(BASE_DIR))

from core.depreciation_rules import (
    get_depreciation_rate,
    classify_asset_type
)

INPUT_FILE = (
    BASE_DIR /
    "outputs" /
    "ledgers" /
    "fixed_asset.csv"
)

OUTPUT_DIR = (
    BASE_DIR /
    "outputs" /
    "financial"
)

OUTPUT_FILE = (
    OUTPUT_DIR /
    "depreciation_chart.csv"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Fixed asset file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    logger.info(
        f"Loaded {len(df)} fixed asset entries"
    )

    return df

# ============================================================
# CALCULATE DEPRECIATION
# ============================================================

def calculate_depreciation(df):
    results = []

    for _, row in df.iterrows():
        asset_name = row["Transaction_Text"]
        amount = float(row["Amount"])

        asset_type = classify_asset_type(
            asset_name
        )

        rate = get_depreciation_rate(
            asset_name
        )

        depreciation = round(
            amount * rate,
            2
        )

        closing_value = round(
            amount - depreciation,
            2
        )

        results.append({
            "Asset_Name": asset_name,
            "Asset_Type": asset_type,
            "Opening_Value": amount,
            "Rate": rate * 100,
            "Depreciation": depreciation,
            "Closing_Value": closing_value
        })

    return pd.DataFrame(results)

# ============================================================
# SAVE
# ============================================================

def save(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Depreciation chart saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Depreciation Pipeline"
    )

    df = load_data()
    dep_df = calculate_depreciation(df)
    save(dep_df)

    logger.info(
        "Depreciation Pipeline Completed"
    )

if __name__ == "__main__":
    run()
