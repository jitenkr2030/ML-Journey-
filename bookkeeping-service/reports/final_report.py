import os
import logging
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

OUTPUTS_DIR = "bookkeeping-service/outputs"
REPORTS_DIR = "bookkeeping-service/reports"

ACCOUNTING_FILE = os.path.join(
    OUTPUTS_DIR,
    "accounting_output.csv"
)

BANK_FILE = os.path.join(
    OUTPUTS_DIR,
    "bank_reconciliation_output.csv"
)

GST_FILE = os.path.join(
    OUTPUTS_DIR,
    "gst_output.csv"
)

TDS_FILE = os.path.join(
    OUTPUTS_DIR,
    "tds_output.csv"
)

FINAL_REPORT_FILE = os.path.join(
    REPORTS_DIR,
    "final_client_report.csv"
)

COMPLIANCE_FILE = os.path.join(
    REPORTS_DIR,
    "compliance_summary.csv"
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# LOAD FILES
# ============================================================

def load_files():

    files = {
        "accounting": ACCOUNTING_FILE,
        "bank": BANK_FILE,
        "gst": GST_FILE,
        "tds": TDS_FILE
    }

    for name, path in files.items():
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Missing file: {path}"
            )

    accounting_df = pd.read_csv(ACCOUNTING_FILE)
    bank_df = pd.read_csv(BANK_FILE)
    gst_df = pd.read_csv(GST_FILE)
    tds_df = pd.read_csv(TDS_FILE)

    return accounting_df, bank_df, gst_df, tds_df


# ============================================================
# BUILD FINAL REPORT
# ============================================================

def build_final_report(
    accounting_df,
    bank_df,
    gst_df,
    tds_df
):

    report = accounting_df.copy()

    report["Bank_Status"] = bank_df["Status"]
    report["GST_Type"] = gst_df["GST_Type"]
    report["GST_Amount"] = gst_df["GST_Amount"]
    report["TDS_Section"] = tds_df["TDS_Section"]
    report["TDS_Amount"] = tds_df["TDS_Amount"]
    report["TDS_Compliance"] = tds_df["Compliance_Status"]

    return report


# ============================================================
# COMPLIANCE SUMMARY
# ============================================================

def build_compliance_summary(
    bank_df,
    gst_df,
    tds_df
):

    summary = {
        "Missing_Bank_Entries": len(
            bank_df[bank_df["Status"] == "Missing Entry"]
        ),

        "GST_Review_Items": len(
            gst_df[gst_df["GST_Status"] == "REVIEW"]
        ),

        "TDS_PAN_Issues": len(
            tds_df[
                tds_df["Compliance_Status"] == "PAN Required"
            ]
        ),

        "Total_TDS_Deducted": tds_df[
            "TDS_Amount"
        ].sum(),

        "Total_GST": gst_df[
            "GST_Amount"
        ].sum()
    }

    return pd.DataFrame(
        [summary]
    )


# ============================================================
# SAVE REPORTS
# ============================================================

def save_reports(
    final_report,
    compliance_summary
):

    os.makedirs(
        REPORTS_DIR,
        exist_ok=True
    )

    final_report.to_csv(
        FINAL_REPORT_FILE,
        index=False
    )

    compliance_summary.to_csv(
        COMPLIANCE_FILE,
        index=False
    )

    logging.info(
        f"Final report saved: {FINAL_REPORT_FILE}"
    )

    logging.info(
        f"Compliance summary saved: {COMPLIANCE_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def run():

    logging.info(
        "Starting Final Reporting Engine"
    )

    accounting_df, bank_df, gst_df, tds_df = load_files()

    final_report = build_final_report(
        accounting_df,
        bank_df,
        gst_df,
        tds_df
    )

    compliance_summary = build_compliance_summary(
        bank_df,
        gst_df,
        tds_df
    )

    save_reports(
        final_report,
        compliance_summary
    )

    logging.info(
        "Final Reporting Completed"
    )


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    run()

