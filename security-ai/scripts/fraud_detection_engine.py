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

DATASET_DIR = BASE_DIR / "datasets"
RECON_DIR = BASE_DIR / "reconciliation"
OUTPUT_DIR = BASE_DIR / "fraud_reports"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

ATTENDANCE_FILE = DATASET_DIR / "attendance.csv"
PAYROLL_FILE = DATASET_DIR / "payroll.csv"
GUARD_FILE = DATASET_DIR / "guards_master.csv"
COMPLIANCE_FILE = DATASET_DIR / "compliance.csv"

PF_RECON_FILE = RECON_DIR / "pf_reconciliation_report.csv"
ESI_RECON_FILE = RECON_DIR / "esi_reconciliation_report.csv"

OUTPUT_FILE = OUTPUT_DIR / "fraud_detection_report.csv"

# ============================================================
# SAFE LOAD
# ============================================================

def safe_load(file_path):
    if not file_path.exists():
        logger.warning(f"Missing file: {file_path}")
        return pd.DataFrame()

    return pd.read_csv(file_path)

# ============================================================
# GHOST EMPLOYEE DETECTION
# Employee in payroll but no attendance
# ============================================================

def detect_ghost_employees():
    attendance_df = safe_load(ATTENDANCE_FILE)
    payroll_df = safe_load(PAYROLL_FILE)

    if attendance_df.empty or payroll_df.empty:
        return []

    attendance_guards = set(
        attendance_df["Guard_ID"].unique()
    )

    payroll_guards = set(
        payroll_df["Guard_ID"].unique()
    )

    ghost_guards = payroll_guards - attendance_guards

    return [
        {
            "Fraud_Type": "Ghost Employee",
            "Guard_ID": guard_id,
            "Risk_Level": "High"
        }
        for guard_id in ghost_guards
    ]

# ============================================================
# FAKE ATTENDANCE DETECTION
# Absent but worked hours present
# ============================================================

def detect_fake_attendance():
    attendance_df = safe_load(ATTENDANCE_FILE)

    if attendance_df.empty:
        return []

    suspicious = attendance_df[
        (attendance_df["Status"] == "Absent") &
        (attendance_df["Hours_Worked"] > 0)
    ]

    results = []

    for _, row in suspicious.iterrows():
        results.append({
            "Fraud_Type": "Fake Attendance",
            "Guard_ID": row["Guard_ID"],
            "Risk_Level": "High"
        })

    return results

# ============================================================
# OVERTIME FRAUD
# ============================================================

def detect_overtime_fraud():
    payroll_df = safe_load(PAYROLL_FILE)

    if payroll_df.empty:
        return []

    if "Overtime_Hours" not in payroll_df.columns:
        return []

    suspicious = payroll_df[
        payroll_df["Overtime_Hours"] > 100
    ]

    results = []

    for _, row in suspicious.iterrows():
        results.append({
            "Fraud_Type": "Excessive Overtime",
            "Guard_ID": row["Guard_ID"],
            "Risk_Level": "Medium"
        })

    return results

# ============================================================
# SALARY INFLATION
# ============================================================

def detect_salary_inflation():
    payroll_df = safe_load(PAYROLL_FILE)

    if payroll_df.empty:
        return []

    avg_salary = payroll_df["Basic_Salary"].mean()

    suspicious = payroll_df[
        payroll_df["Basic_Salary"] > (avg_salary * 2)
    ]

    results = []

    for _, row in suspicious.iterrows():
        results.append({
            "Fraud_Type": "Salary Inflation",
            "Guard_ID": row["Guard_ID"],
            "Risk_Level": "High"
        })

    return results

# ============================================================
# PF EVASION
# ============================================================

def detect_pf_evasion():
    pf_df = safe_load(PF_RECON_FILE)

    if pf_df.empty:
        return []

    suspicious = pf_df[
        pf_df["Match_Status"] != "Matched"
    ]

    results = []

    for _, row in suspicious.iterrows():
        results.append({
            "Fraud_Type": "PF Evasion",
            "Guard_ID": row["Guard_ID"],
            "Risk_Level": "High"
        })

    return results

# ============================================================
# ESI EVASION
# ============================================================

def detect_esi_evasion():
    esi_df = safe_load(ESI_RECON_FILE)

    if esi_df.empty:
        return []

    suspicious = esi_df[
        esi_df["Match_Status"] != "Matched"
    ]

    results = []

    for _, row in suspicious.iterrows():
        results.append({
            "Fraud_Type": "ESI Evasion",
            "Guard_ID": row["Guard_ID"],
            "Risk_Level": "High"
        })

    return results

# ============================================================
# DUPLICATE EMPLOYEE DETECTION
# ============================================================

def detect_duplicate_employees():
    guard_df = safe_load(GUARD_FILE)

    if guard_df.empty:
        return []

    duplicates = guard_df[
        guard_df.duplicated(
            subset=["Name"],
            keep=False
        )
    ]

    results = []

    for _, row in duplicates.iterrows():
        results.append({
            "Fraud_Type": "Duplicate Employee",
            "Guard_ID": row["Guard_ID"],
            "Risk_Level": "Medium"
        })

    return results

# ============================================================
# MASTER FRAUD ENGINE
# ============================================================

def run_fraud_detection():
    fraud_cases = []

    fraud_cases.extend(
        detect_ghost_employees()
    )

    fraud_cases.extend(
        detect_fake_attendance()
    )

    fraud_cases.extend(
        detect_overtime_fraud()
    )

    fraud_cases.extend(
        detect_salary_inflation()
    )

    fraud_cases.extend(
        detect_pf_evasion()
    )

    fraud_cases.extend(
        detect_esi_evasion()
    )

    fraud_cases.extend(
        detect_duplicate_employees()
    )

    if not fraud_cases:
        fraud_cases.append({
            "Fraud_Type": "No Fraud Detected",
            "Guard_ID": "N/A",
            "Risk_Level": "Safe"
        })

    return pd.DataFrame(
        fraud_cases
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
        f"Fraud report saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Fraud Detection Engine"
    )

    fraud_df = run_fraud_detection()

    save_report(
        fraud_df
    )

    logger.info(
        "Fraud Detection Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
