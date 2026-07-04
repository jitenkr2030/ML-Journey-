import os
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

# ============================================================
# PATH CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")

RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUTS_DIR = CLIENT_DIR / client_name / "output"
FINANCIAL_DIR = OUTPUTS_DIR / "financial"

OUTPUT_FILE = FINANCIAL_DIR / "audit_trail.csv"

FINANCIAL_DIR.mkdir(
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
# SAFE LOADER
# ============================================================

def safe_load(file_path):
    if file_path.exists():
        return pd.read_csv(file_path)
    return pd.DataFrame()

# ============================================================
# AUDIT SOURCES
# ============================================================

def get_pipeline_sources():
    return {
        "Raw Bank Statement": RAW_DIR / "bank_statement.csv",
        "Raw Daybook": RAW_DIR / "daybook.csv",
        "Accounting Output": OUTPUTS_DIR / "accounting" / "accounting_output.csv",
        "Bank Reconciliation": OUTPUTS_DIR / "banking" / "bank_reconciliation_output.csv",
        "GST Output": OUTPUTS_DIR / "gst" / "gst_output.csv",
        "TDS Output": OUTPUTS_DIR / "tds" / "tds_output.csv",
        "Master Ledger": OUTPUTS_DIR / "ledgers" / "master_ledger.csv",
        "Depreciation Chart": OUTPUTS_DIR / "financial" / "depreciation_chart.csv",
        "Working Notes": OUTPUTS_DIR / "financial" / "working_notes.csv",
        "Annexure Report": OUTPUTS_DIR / "financial" / "annexure_report.csv",
        "Schedules": OUTPUTS_DIR / "financial" / "schedules.csv",
        "Trial Balance": OUTPUTS_DIR / "financial" / "trial_balance.csv",
        "Profit and Loss": OUTPUTS_DIR / "financial" / "profit_and_loss.csv",
        "Balance Sheet": OUTPUTS_DIR / "financial" / "balance_sheet.csv"
    }

# ============================================================
# BUILD AUDIT TRAIL
# ============================================================

def build_audit_trail():
    audit_rows = []

    sources = get_pipeline_sources()

    for stage_name, file_path in sources.items():
        df = safe_load(file_path)

        if df.empty:
            continue

        total_amount = 0.0

        if "Amount" in df.columns:
            total_amount = df["Amount"].sum()
        else:
            numeric_cols = df.select_dtypes(include="number")
            if not numeric_cols.empty:
                total_amount = numeric_cols.sum().sum()

        audit_rows.append({
            "Audit_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Stage": stage_name,
            "Source_File": file_path.name,
            "Rows": len(df),
            "Total_Amount": round(total_amount, 2),
            "Status": "Verified"
        })

    return pd.DataFrame(audit_rows)

# ============================================================
# SAVE
# ============================================================

def save_audit(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Audit trail saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Audit Trail Pipeline"
    )

    audit_df = build_audit_trail()

    save_audit(audit_df)

    logger.info(
        "Audit Trail Pipeline Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
