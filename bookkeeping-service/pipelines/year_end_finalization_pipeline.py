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
FINANCIAL_DIR = CLIENT_DIR / client_name / "output" / "financial"

CHECKLIST_FILE = FINANCIAL_DIR / "closing_checklist.csv"
ADVISORY_FILE = FINANCIAL_DIR / "client_advisory.csv"
RISK_FILE = FINANCIAL_DIR / "risk_analysis.csv"
TAX_FILE = FINANCIAL_DIR / "tax_computation.csv"
BALANCE_SHEET_FILE = FINANCIAL_DIR / "balance_sheet.csv"
PNL_FILE = FINANCIAL_DIR / "profit_and_loss.csv"

OUTPUT_FILE = FINANCIAL_DIR / "year_end_finalization.csv"

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

def safe_load(file_path):
    if file_path.exists():
        return pd.read_csv(file_path)
    return pd.DataFrame()

# ============================================================
# FINALIZATION CHECK
# ============================================================

def build_finalization():
    checklist_df = safe_load(CHECKLIST_FILE)

    pending_items = 0

    if not checklist_df.empty:
        pending_items = len(
            checklist_df[
                checklist_df["Status"] == "Pending"
            ]
        )

    final_status = (
        "Finalized"
        if pending_items == 0
        else "Pending Review"
    )

    summary = {
        "Finalization_Date": datetime.now().strftime("%Y-%m-%d"),
        "Pending_Items": pending_items,
        "Final_Status": final_status,
        "Balance_Sheet_Ready": BALANCE_SHEET_FILE.exists(),
        "Profit_Loss_Ready": PNL_FILE.exists(),
        "Tax_Computation_Ready": TAX_FILE.exists(),
        "Risk_Report_Ready": RISK_FILE.exists(),
        "Client_Advisory_Ready": ADVISORY_FILE.exists()
    }

    return pd.DataFrame([summary])

# ============================================================
# SAVE
# ============================================================

def save_finalization(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Year-end finalization saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Year-End Finalization Pipeline"
    )

    final_df = build_finalization()

    save_finalization(final_df)

    logger.info(
        "Year-End Finalization Pipeline Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
