import os
import logging
import pandas as pd
from pathlib import Path

# ============================================================
# PATH CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")

LEDGER_DIR = CLIENT_DIR / client_name / "output" / "ledgers"
OUTPUT_DIR = CLIENT_DIR / client_name / "output" / "financial"

OUTPUT_FILE = OUTPUT_DIR / "schedules.csv"

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
# SAFE LOAD
# ============================================================

def load_csv(file_path):
    if file_path.exists():
        return pd.read_csv(file_path)
    return pd.DataFrame()

# ============================================================
# BUILD SCHEDULES
# ============================================================

def build_schedules():
    schedule_rows = []

    schedule_files = {
        "Salary Schedule": LEDGER_DIR / "salary_expense.csv",
        "Rent Schedule": LEDGER_DIR / "rent_expense.csv",
        "Utilities Schedule": LEDGER_DIR / "utilities_expense.csv",
        "Marketing Schedule": LEDGER_DIR / "marketing_expense.csv",
        "Fixed Asset Schedule": LEDGER_DIR / "fixed_asset.csv",
        "GST Liability Schedule": LEDGER_DIR / "gst_payable.csv",
        "TDS Liability Schedule": LEDGER_DIR / "tds_payable.csv"
    }

    for schedule_name, file_path in schedule_files.items():
        df = load_csv(file_path)

        if df.empty:
            continue

        if "Amount" in df.columns:
            total = df["Amount"].sum()
        else:
            numeric_cols = df.select_dtypes(include="number")
            total = numeric_cols.sum().sum()

        schedule_rows.append({
            "Schedule_Name": schedule_name,
            "Entries": len(df),
            "Total_Amount": round(total, 2),
            "Source_File": file_path.name
        })

    return pd.DataFrame(schedule_rows)

# ============================================================
# SAVE
# ============================================================

def save_schedules(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Schedules saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Schedule Pipeline"
    )

    df = build_schedules()

    save_schedules(df)

    logger.info(
        "Schedule Pipeline Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
