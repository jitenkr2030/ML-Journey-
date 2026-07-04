import pandas as pd
import logging
from pathlib import Path

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ============================================================
# PATH CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

RECON_DIR = BASE_DIR / "reconciliation"
DATASET_DIR = BASE_DIR / "datasets"

OUTPUT_DIR = BASE_DIR / "risk_reports"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PF_FILE = RECON_DIR / "pf_reconciliation_report.csv"
ESI_FILE = RECON_DIR / "esi_reconciliation_report.csv"
MATCH_FILE = RECON_DIR / "employee_matching_report.csv"
ATTENDANCE_FILE = DATASET_DIR / "attendance.csv"
PAYROLL_FILE = DATASET_DIR / "payroll.csv"
GUARD_FILE = DATASET_DIR / "guards_master.csv"

OUTPUT_FILE = OUTPUT_DIR / "compliance_risk_report.csv"

# ============================================================
# SAFE LOAD
# ============================================================

def safe_load(file_path):
    if not file_path.exists():
        logger.warning(f"Missing file: {file_path}")
        return pd.DataFrame()

    return pd.read_csv(file_path)

# ============================================================
# PF RISK
# ============================================================

def calculate_pf_risk():
    df = safe_load(PF_FILE)

    if df.empty:
        return 0

    mismatches = df[
        df["Match_Status"] != "Matched"
    ]

    return len(mismatches) * 5

# ============================================================
# ESI RISK
# ============================================================

def calculate_esi_risk():
    df = safe_load(ESI_FILE)

    if df.empty:
        return 0

    mismatches = df[
        df["Match_Status"] != "Matched"
    ]

    return len(mismatches) * 5

# ============================================================
# EMPLOYEE MATCH RISK
# ============================================================

def calculate_employee_match_risk():
    df = safe_load(MATCH_FILE)

    if df.empty:
        return 0

    risky = df[
        df["Match_Status"] != "Matched"
    ]

    return len(risky) * 3

# ============================================================
# ATTENDANCE FRAUD RISK
# ============================================================

def calculate_attendance_risk():
    df = safe_load(ATTENDANCE_FILE)

    if df.empty:
        return 0

    gps_mismatch = df[
        df["GPS_Match"] == "No"
    ]

    absent_but_hours = df[
        (df["Status"] == "Absent") &
        (df["Hours_Worked"] > 0)
    ]

    risk_score = (
        len(gps_mismatch) * 2
        + len(absent_but_hours) * 5
    )

    return risk_score

# ============================================================
# PAYROLL RISK
# ============================================================

def calculate_payroll_risk():
    df = safe_load(PAYROLL_FILE)

    if df.empty:
        return 0

    negative_net_pay = df[
        df["Net_Pay"] < 0
    ]

    excessive_ot = df[
        df["Overtime_Hours"] > 100
    ] if "Overtime_Hours" in df.columns else pd.DataFrame()

    risk_score = (
        len(negative_net_pay) * 10
        + len(excessive_ot) * 5
    )

    return risk_score

# ============================================================
# DUPLICATE EMPLOYEE RISK
# ============================================================

def calculate_duplicate_risk():
    df = safe_load(GUARD_FILE)

    if df.empty:
        return 0

    duplicates = df[
        df.duplicated(
            subset=["Name"],
            keep=False
        )
    ]

    return len(duplicates) * 4

# ============================================================
# TOTAL RISK SCORE
# ============================================================

def calculate_total_risk():
    pf_risk = calculate_pf_risk()
    esi_risk = calculate_esi_risk()
    employee_risk = calculate_employee_match_risk()
    attendance_risk = calculate_attendance_risk()
    payroll_risk = calculate_payroll_risk()
    duplicate_risk = calculate_duplicate_risk()

    total_score = (
        pf_risk
        + esi_risk
        + employee_risk
        + attendance_risk
        + payroll_risk
        + duplicate_risk
    )

    return {
        "PF_Risk": pf_risk,
        "ESI_Risk": esi_risk,
        "Employee_Match_Risk": employee_risk,
        "Attendance_Risk": attendance_risk,
        "Payroll_Risk": payroll_risk,
        "Duplicate_Risk": duplicate_risk,
        "Total_Risk_Score": total_score
    }

# ============================================================
# RISK LEVEL
# ============================================================

def classify_risk(total_score):
    if total_score <= 20:
        return "Low"

    if total_score <= 50:
        return "Medium"

    return "High"

# ============================================================
# BUILD REPORT
# ============================================================

def build_report():
    risk_data = calculate_total_risk()

    risk_data["Risk_Level"] = classify_risk(
        risk_data["Total_Risk_Score"]
    )

    return pd.DataFrame(
        [risk_data]
    )

# ============================================================
# SAVE REPORT
# ============================================================

def save_report(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Saved risk report: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Compliance Risk Scoring Engine"
    )

    report_df = build_report()

    save_report(
        report_df
    )

    logger.info(
        "Compliance Risk Scoring Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
