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
GST_DIR = CLIENT_DIR / client_name / "output" / "gst"
TDS_DIR = CLIENT_DIR / client_name / "output" / "tds"

OUTPUT_DIR = CLIENT_DIR / client_name / "output" / "financial"
OUTPUT_FILE = OUTPUT_DIR / "working_notes.csv"

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
# GENERATE WORKING NOTES
# ============================================================

def generate_working_notes():
    working_notes = []

    files = {
        "Salary Expense": LEDGER_DIR / "salary_expense.csv",
        "Rent Expense": LEDGER_DIR / "rent_expense.csv",
        "Utilities Expense": LEDGER_DIR / "utilities_expense.csv",
        "Marketing Expense": LEDGER_DIR / "marketing_expense.csv",
        "Fixed Assets": LEDGER_DIR / "fixed_asset.csv",
        "GST Summary": GST_DIR / "gst_summary.csv",
        "TDS Summary": TDS_DIR / "tds_summary.csv"
    }

    for note_name, file_path in files.items():
        df = load_csv(file_path)

        if df.empty:
            continue

        if "Amount" in df.columns:
            total = df["Amount"].sum()
        else:
            numeric_cols = df.select_dtypes(include="number")
            total = numeric_cols.sum().sum()

        working_notes.append({
            "Particular": note_name,
            "Entries": len(df),
            "Total_Amount": round(total, 2),
            "Remarks": f"{note_name} derived from source ledger"
        })

    return pd.DataFrame(working_notes)

# ============================================================
# SAVE FILE
# ============================================================

def save_notes(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Working notes saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Working Notes Pipeline"
    )

    df = generate_working_notes()

    save_notes(df)

    logger.info(
        "Working Notes Pipeline Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
