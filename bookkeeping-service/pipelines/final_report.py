import os
import logging
import pandas as pd
from pathlib import Path
import sys

# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")
sys.path.append(str(BASE_DIR))

from config.paths import (
    ACCOUNTING_OUTPUT_DIR,
    BANKING_OUTPUT_DIR,
    GST_OUTPUT_DIR,
    TDS_OUTPUT_DIR,
    FINANCIAL_OUTPUT_DIR,
    REPORTS_DIR
)

# ============================================================
# FILES
# ============================================================

FILES = {
    "Accounting": Path(ACCOUNTING_OUTPUT_DIR) / "accounting_output.csv",
    "Bank_Reconciliation": Path(BANKING_OUTPUT_DIR) / "bank_reconciliation_output.csv",
    "GST": Path(GST_OUTPUT_DIR) / "gst_output.csv",
    "TDS": Path(TDS_OUTPUT_DIR) / "tds_output.csv",
    "Profit_Loss": Path(FINANCIAL_OUTPUT_DIR) / "profit_and_loss.csv",
    "Balance_Sheet": Path(FINANCIAL_OUTPUT_DIR) / "balance_sheet.csv",
    "Depreciation": Path(FINANCIAL_OUTPUT_DIR) / "depreciation_chart.csv",
    "Working_Notes": Path(FINANCIAL_OUTPUT_DIR) / "working_notes.csv",
    "Annexure": Path(FINANCIAL_OUTPUT_DIR) / "annexure_report.csv",
    "Schedules": Path(FINANCIAL_OUTPUT_DIR) / "schedules.csv",
    "Audit_Trail": Path(FINANCIAL_OUTPUT_DIR) / "audit_trail.csv",
    "Compliance_Checklist": Path(FINANCIAL_OUTPUT_DIR) / "compliance_checklist.csv",
    "Tax_Computation": Path(FINANCIAL_OUTPUT_DIR) / "tax_computation.csv",
    "Risk_Analysis": Path(FINANCIAL_OUTPUT_DIR) / "risk_analysis.csv",
    "Closing_Checklist": Path(FINANCIAL_OUTPUT_DIR) / "closing_checklist.csv",
    "Client_Advisory": Path(FINANCIAL_OUTPUT_DIR) / "client_advisory.csv",
    "Year_End_Finalization": Path(FINANCIAL_OUTPUT_DIR) / "year_end_finalization.csv"
}

FINAL_REPORT_FILE = Path(REPORTS_DIR) / "final_client_report.csv"
COMPLIANCE_FILE = Path(REPORTS_DIR) / "compliance_summary.csv"
MANAGEMENT_REPORT_FILE = Path(REPORTS_DIR) / "management_summary.csv"

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
# FINAL REPORT
# ============================================================

def build_final_report():
    report_rows = []

    for report_name, file_path in FILES.items():
        df = safe_load(file_path)

        report_rows.append({
            "Report_Name": report_name,
            "File_Name": file_path.name,
            "Status": "Available" if not df.empty else "Missing",
            "Rows": len(df)
        })

    return pd.DataFrame(report_rows)

# ============================================================
# COMPLIANCE SUMMARY
# ============================================================

def build_compliance_summary():
    gst_df = safe_load(FILES["GST"])
    tds_df = safe_load(FILES["TDS"])

    gst_total = 0
    tds_total = 0

    if not gst_df.empty:
        gst_total = gst_df.select_dtypes(include="number").sum().sum()

    if not tds_df.empty:
        tds_total = tds_df.select_dtypes(include="number").sum().sum()

    return pd.DataFrame([{
        "GST_Total": gst_total,
        "TDS_Total": tds_total
    }])

# ============================================================
# MANAGEMENT SUMMARY
# ============================================================

def build_management_summary():
    accounting_df = safe_load(FILES["Accounting"])
    bank_df = safe_load(FILES["Bank_Reconciliation"])
    risk_df = safe_load(FILES["Risk_Analysis"])

    return pd.DataFrame([{
        "Total_Transactions": len(accounting_df),
        "Bank_Entries": len(bank_df),
        "Risk_Flags": len(risk_df)
    }])

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Final Reporting Started"
    )

    final_df = build_final_report()
    compliance_df = build_compliance_summary()
    management_df = build_management_summary()

    final_df.to_csv(
        FINAL_REPORT_FILE,
        index=False
    )

    compliance_df.to_csv(
        COMPLIANCE_FILE,
        index=False
    )

    management_df.to_csv(
        MANAGEMENT_REPORT_FILE,
        index=False
    )

    logger.info(
        "Final Reporting Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
