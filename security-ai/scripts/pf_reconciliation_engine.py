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
ECR_FILE = INPUT_DIR / "ecr.csv"
MATCHING_FILE = INPUT_DIR / "matching.csv"

OUTPUT_FILE = OUTPUT_DIR / "pf_reconciliation_report.csv"

# ============================================================
# LOAD FILES
# ============================================================

def load_csv(file_path):
    if not file_path.exists():
        logger.error(f"Missing file: {file_path}")
        return pd.DataFrame()

    return pd.read_csv(file_path)


# ============================================================
# NORMALIZE NAMES
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
# FUZZY MATCH SCORE
# ============================================================

def similarity(a, b):
    return SequenceMatcher(
        None,
        normalize_name(a),
        normalize_name(b)
    ).ratio()


# ============================================================
# MAP EMPLOYEES
# ============================================================

def build_employee_map(wages_df, ecr_df):
    mappings = []

    wage_names = wages_df["NAME"].tolist()
    ecr_names = ecr_df["Employee Name"].tolist()

    for wage_name in wage_names:
        best_match = None
        best_score = 0

        for ecr_name in ecr_names:
            score = similarity(
                wage_name,
                ecr_name
            )

            if score > best_score:
                best_score = score
                best_match = ecr_name

        mappings.append({
            "Wage_Name": wage_name,
            "ECR_Name": best_match,
            "Match_Score": round(best_score, 4)
        })

    return pd.DataFrame(mappings)


# ============================================================
# PF VALIDATION
# ============================================================

def validate_pf(row):
    basic = row.get("BASIC + VDA", 0)
    actual_pf = row.get("EPF 12% of15000 if BASIC + VDA IS ABOVE 15000", 0)

    pf_wage = min(basic, 15000)
    expected_pf = round(
        pf_wage * 0.12
    )

    mismatch = actual_pf - expected_pf

    return expected_pf, mismatch


# ============================================================
# RECONCILIATION
# ============================================================

def reconcile_pf(wages_df):
    results = []

    for _, row in wages_df.iterrows():
        expected_pf, mismatch = validate_pf(row)

        status = "Matched"

        if mismatch != 0:
            status = "Mismatch"

        results.append({
            "Employee_Name": row["NAME"],
            "Basic_VDA": row["BASIC + VDA"],
            "Actual_PF": row["EPF 12% of15000 if BASIC + VDA IS ABOVE 15000"],
            "Expected_PF": expected_pf,
            "PF_Difference": mismatch,
            "Status": status
        })

    return pd.DataFrame(results)


# ============================================================
# SAVE REPORTS
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
    logger.info("Starting PF Reconciliation Engine")

    wages_df = load_csv(WAGES_FILE)
    ecr_df = load_csv(ECR_FILE)

    if wages_df.empty or ecr_df.empty:
        logger.error("Required files missing")
        return

    employee_map_df = build_employee_map(
        wages_df,
        ecr_df
    )

    pf_report_df = reconcile_pf(
        wages_df
    )

    save_output(
        employee_map_df,
        "employee_matching_report.csv"
    )

    save_output(
        pf_report_df,
        "pf_reconciliation_report.csv"
    )

    logger.info("PF Reconciliation Completed")


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
