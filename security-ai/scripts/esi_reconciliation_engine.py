import pandas as pd
import logging
from pathlib import Path
from difflib import SequenceMatcher

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

INPUT_DIR = BASE_DIR / "processed"
OUTPUT_DIR = BASE_DIR / "reconciliation"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

WAGES_FILE = INPUT_DIR / "wages.csv"
ESI_FILE = INPUT_DIR / "difference.csv"

OUTPUT_FILE = OUTPUT_DIR / "esi_reconciliation_report.csv"

# ============================================================
# ESI RULES
# ============================================================

ESI_WAGE_LIMIT = 21000
EMPLOYEE_ESI_RATE = 0.0075
EMPLOYER_ESI_RATE = 0.0325

# ============================================================
# LOAD FILES
# ============================================================

def load_csv(file_path):
    if not file_path.exists():
        logger.error(f"Missing file: {file_path}")
        return pd.DataFrame()

    return pd.read_csv(file_path)


# ============================================================
# NORMALIZE NAME
# ============================================================

def normalize_name(name):
    if pd.isna(name):
        return ""

    return (
        str(name)
        .upper()
        .strip()
        .replace("  ", " ")
    )


# ============================================================
# FUZZY MATCH
# ============================================================

def similarity(a, b):
    return SequenceMatcher(
        None,
        normalize_name(a),
        normalize_name(b)
    ).ratio()


# ============================================================
# ESI ELIGIBILITY CHECK
# ============================================================

def is_esi_applicable(gross_wage):
    return gross_wage <= ESI_WAGE_LIMIT


# ============================================================
# CALCULATE ESI
# ============================================================

def calculate_employee_esi(gross_wage):
    if not is_esi_applicable(gross_wage):
        return 0

    return round(
        gross_wage * EMPLOYEE_ESI_RATE
    )


def calculate_employer_esi(gross_wage):
    if not is_esi_applicable(gross_wage):
        return 0

    return round(
        gross_wage * EMPLOYER_ESI_RATE
    )


# ============================================================
# VALIDATE ESI
# ============================================================

def validate_esi(row):
    basic = row.get("BASIC + VDA", 0)
    actual_esi = row.get("ESIC 0.75% OF BASIC +VDA", 0)
    actual_employer_esi = row.get(
        "EMPLOYER SHARE OF ESIC 3.25% OF BASIC + VDA",
        0
    )

    expected_employee_esi = calculate_employee_esi(
        basic
    )

    expected_employer_esi = calculate_employer_esi(
        basic
    )

    employee_diff = round(
        actual_esi - expected_employee_esi,
        2
    )

    employer_diff = round(
        actual_employer_esi - expected_employer_esi,
        2
    )

    return (
        expected_employee_esi,
        expected_employer_esi,
        employee_diff,
        employer_diff
    )


# ============================================================
# RECONCILIATION ENGINE
# ============================================================

def reconcile_esi(wages_df):
    results = []

    for _, row in wages_df.iterrows():
        (
            expected_employee_esi,
            expected_employer_esi,
            employee_diff,
            employer_diff
        ) = validate_esi(row)

        status = "Matched"

        if employee_diff != 0 or employer_diff != 0:
            status = "Mismatch"

        eligibility = (
            "Applicable"
            if is_esi_applicable(
                row["BASIC + VDA"]
            )
            else "Not Applicable"
        )

        results.append({
            "Employee_Name": row["NAME"],
            "Basic_VDA": row["BASIC + VDA"],
            "ESI_Eligibility": eligibility,
            "Actual_Employee_ESI": row["ESIC 0.75% OF BASIC +VDA"],
            "Expected_Employee_ESI": expected_employee_esi,
            "Employee_ESI_Difference": employee_diff,
            "Actual_Employer_ESI": row["EMPLOYER SHARE OF ESIC 3.25% OF BASIC + VDA"],
            "Expected_Employer_ESI": expected_employer_esi,
            "Employer_ESI_Difference": employer_diff,
            "Status": status
        })

    return pd.DataFrame(results)


# ============================================================
# FRAUD CHECKS
# ============================================================

def fraud_flags(df):
    flags = []

    for _, row in df.iterrows():
        if (
            row["ESI_Eligibility"] == "Not Applicable"
            and row["Actual_Employee_ESI"] > 0
        ):
            flags.append({
                "Employee_Name": row["Employee_Name"],
                "Risk": "Wrong ESI deduction above threshold"
            })

        if (
            row["ESI_Eligibility"] == "Applicable"
            and row["Actual_Employee_ESI"] == 0
        ):
            flags.append({
                "Employee_Name": row["Employee_Name"],
                "Risk": "Missing ESI deduction"
            })

    return pd.DataFrame(flags)


# ============================================================
# SAVE REPORT
# ============================================================

def save_output(df, file_name):
    output_path = OUTPUT_DIR / file_name

    df.to_csv(
        output_path,
        index=False
    )

    logger.info(f"Saved: {output_path}")


# ============================================================
# MAIN
# ============================================================

def run():
    logger.info("Starting ESI Reconciliation Engine")

    wages_df = load_csv(WAGES_FILE)

    if wages_df.empty:
        logger.error("Wages file missing")
        return

    esi_report_df = reconcile_esi(
        wages_df
    )

    fraud_df = fraud_flags(
        esi_report_df
    )

    save_output(
        esi_report_df,
        "esi_reconciliation_report.csv"
    )

    save_output(
        fraud_df,
        "esi_risk_flags.csv"
    )

    logger.info("ESI Reconciliation Completed")


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
