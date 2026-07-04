import logging
import pandas as pd
from pathlib import Path

# ============================================================
# BASE CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

RECON_DIR = BASE_DIR / "reconciliation"
FRAUD_DIR = BASE_DIR / "fraud_reports"
RISK_DIR = BASE_DIR / "risk_reports"
OUTPUT_DIR = BASE_DIR / "outputs"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = OUTPUT_DIR / "security_ai_final_report.csv"

# ============================================================
# FILES
# ============================================================

PF_FILE = RECON_DIR / "pf_reconciliation_report.csv"
ESI_FILE = RECON_DIR / "esi_reconciliation_report.csv"
WAGE_FILE = RECON_DIR / "wage_anomaly_report.csv"
FRAUD_FILE = FRAUD_DIR / "fraud_detection_report.csv"
RISK_FILE = RISK_DIR / "compliance_risk_report.csv"
SITE_FILE = OUTPUT_DIR / "site_performance_scores.csv"

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
# REPORT GENERATOR
# ============================================================

def generate_report():

    pf_df = safe_load(PF_FILE)
    esi_df = safe_load(ESI_FILE)
    wage_df = safe_load(WAGE_FILE)
    fraud_df = safe_load(FRAUD_FILE)
    risk_df = safe_load(RISK_FILE)
    site_df = safe_load(SITE_FILE)

    total_employees = 0
    pf_mismatches = 0
    esi_mismatches = 0
    wage_anomalies = 0
    fraud_alerts = 0
    high_risk_cases = 0
    best_site = "N/A"
    worst_site = "N/A"

    # PF
    if not pf_df.empty:
        total_employees = max(
            total_employees,
            len(pf_df)
        )

        if "Mismatch_Flag" in pf_df.columns:
            pf_mismatches = (
                pf_df["Mismatch_Flag"]
                .astype(str)
                .str.lower()
                .eq("yes")
                .sum()
            )

    # ESI
    if not esi_df.empty:
        total_employees = max(
            total_employees,
            len(esi_df)
        )

        if "Mismatch_Flag" in esi_df.columns:
            esi_mismatches = (
                esi_df["Mismatch_Flag"]
                .astype(str)
                .str.lower()
                .eq("yes")
                .sum()
            )

    # Wage anomalies
    if not wage_df.empty:
        wage_anomalies = len(wage_df)

    # Fraud alerts
    if not fraud_df.empty:
        fraud_alerts = len(fraud_df)

    # Risk cases
    if not risk_df.empty:
        high_risk_cases = len(risk_df)

    # Site scores
    if not site_df.empty:
        if "Performance_Score" in site_df.columns:
            best_site_row = site_df.loc[
                site_df["Performance_Score"].idxmax()
            ]

            worst_site_row = site_df.loc[
                site_df["Performance_Score"].idxmin()
            ]

            best_site = best_site_row.get(
                "Site_ID",
                "N/A"
            )

            worst_site = worst_site_row.get(
                "Site_ID",
                "N/A"
            )

    final_report = {
        "Total_Employees": total_employees,
        "PF_Mismatches": pf_mismatches,
        "ESI_Mismatches": esi_mismatches,
        "Wage_Anomalies": wage_anomalies,
        "Fraud_Alerts": fraud_alerts,
        "High_Risk_Cases": high_risk_cases,
        "Best_Performing_Site": best_site,
        "Worst_Performing_Site": worst_site
    }

    return pd.DataFrame([final_report])

# ============================================================
# SAVE
# ============================================================

def save_report(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Final security report saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():

    logger.info(
        "Starting Final Security Report Generation"
    )

    report_df = generate_report()

    save_report(report_df)

    logger.info(
        "Final Security Report Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()

