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
OUTPUT_FILE = OUTPUT_DIR / "annexure_report.csv"

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
# BUILD ANNEXURE
# ============================================================

def build_annexure():
    annexure_rows = []

    annexure_files = {
        "Debtors Annexure": LEDGER_DIR / "master_ledger.csv",
        "Creditors Annexure": LEDGER_DIR / "master_ledger.csv",
        "Expense Annexure": LEDGER_DIR / "ledger_summary.csv",
        "Fixed Asset Annexure": LEDGER_DIR / "fixed_asset.csv",
        "GST Payable Annexure": LEDGER_DIR / "gst_payable.csv",
        "TDS Payable Annexure": LEDGER_DIR / "tds_payable.csv"
    }

    for annexure_name, file_path in annexure_files.items():
        df = load_csv(file_path)

        if df.empty:
            continue

        if "Amount" in df.columns:
            total = df["Amount"].sum()
        else:
            numeric_cols = df.select_dtypes(include="number")
            total = numeric_cols.sum().sum()

        annexure_rows.append({
            "Annexure_Name": annexure_name,
            "Rows": len(df),
            "Total_Amount": round(total, 2),
            "Source_File": file_path.name
        })

    return pd.DataFrame(annexure_rows)

# ============================================================
# SAVE
# ============================================================

def save_annexure(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Annexure report saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Annexure Pipeline"
    )

    df = build_annexure()

    save_annexure(df)

    logger.info(
        "Annexure Pipeline Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
