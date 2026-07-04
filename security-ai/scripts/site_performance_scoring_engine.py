# ============================================================
# SITE PERFORMANCE SCORING ENGINE
# Production Grade Version
#
# Purpose:
# - Measure site-level operational performance
# - Attendance discipline scoring
# - Incident severity scoring
# - Complaint frequency scoring
# - Compliance scoring
# - Risk weighted site scoring
# - Final performance grading
# ============================================================

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
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "datasets"

SITE_ASSIGNMENTS_FILE = DATASET_DIR / "site_assignments.csv"
ATTENDANCE_FILE = DATASET_DIR / "attendance.csv"
INCIDENTS_FILE = DATASET_DIR / "incidents.csv"
COMPLAINTS_FILE = DATASET_DIR / "complaints.csv"
COMPLIANCE_FILE = DATASET_DIR / "compliance.csv"

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "site_performance_scores.csv"

# ============================================================
# SAFE CSV LOADER
# ============================================================

def safe_read_csv(file_path):
    if not file_path.exists():
        logger.error(f"Missing file: {file_path}")
        return pd.DataFrame()

    try:
        return pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return pd.DataFrame()

# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    return {
        "assignments": safe_read_csv(SITE_ASSIGNMENTS_FILE),
        "attendance": safe_read_csv(ATTENDANCE_FILE),
        "incidents": safe_read_csv(INCIDENTS_FILE),
        "complaints": safe_read_csv(COMPLAINTS_FILE),
        "compliance": safe_read_csv(COMPLIANCE_FILE),
    }

# ============================================================
# ATTENDANCE SCORE
# ============================================================

def calculate_attendance_score(site_guards, attendance_df):
    site_attendance = attendance_df[
        attendance_df["Guard_ID"].isin(site_guards)
    ]

    if site_attendance.empty:
        return 0

    total_records = len(site_attendance)

    present_count = len(
        site_attendance[
            site_attendance["Status"] == "Present"
        ]
    )

    score = (present_count / total_records) * 100
    return round(score, 2)

# ============================================================
# INCIDENT SCORE
# ============================================================

def calculate_incident_score(site_guards, incidents_df):
    site_incidents = incidents_df[
        incidents_df["Guard_ID"].isin(site_guards)
    ]

    if site_incidents.empty:
        return 100

    severity_weights = {
        "Low": 5,
        "Medium": 15,
        "High": 30
    }

    total_penalty = 0

    for _, row in site_incidents.iterrows():
        total_penalty += severity_weights.get(
            row["Severity"], 10
        )

    score = max(100 - total_penalty, 0)

    return round(score, 2)

# ============================================================
# COMPLAINT SCORE
# ============================================================

def calculate_complaint_score(site_guards, complaints_df):
    site_complaints = complaints_df[
        complaints_df["Guard_ID"].isin(site_guards)
    ]

    complaint_count = len(site_complaints)

    penalty = complaint_count * 5

    score = max(100 - penalty, 0)

    return round(score, 2)

# ============================================================
# COMPLIANCE SCORE
# ============================================================

def calculate_compliance_score(site_guards, compliance_df):
    site_compliance = compliance_df[
        compliance_df["Guard_ID"].isin(site_guards)
    ]

    if site_compliance.empty:
        return 0

    compliant_count = len(
        site_compliance[
            site_compliance["Risk_Level"] == "Low"
        ]
    )

    total = len(site_compliance)

    score = (compliant_count / total) * 100

    return round(score, 2)

# ============================================================
# FINAL SITE SCORE
# ============================================================

def calculate_final_score(
    attendance_score,
    incident_score,
    complaint_score,
    compliance_score
):
    final_score = (
        (attendance_score * 0.35)
        + (incident_score * 0.25)
        + (complaint_score * 0.20)
        + (compliance_score * 0.20)
    )

    return round(final_score, 2)

# ============================================================
# PERFORMANCE GRADE
# ============================================================

def assign_grade(score):
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Average"
    elif score >= 40:
        return "Poor"
    else:
        return "Critical"

# ============================================================
# BUILD SITE PERFORMANCE REPORT
# ============================================================

def build_site_performance():
    data = load_data()

    assignments = data["assignments"]
    attendance = data["attendance"]
    incidents = data["incidents"]
    complaints = data["complaints"]
    compliance = data["compliance"]

    if assignments.empty:
        logger.error("Site assignments missing.")
        return pd.DataFrame()

    site_records = []

    grouped_sites = assignments.groupby("Site_ID")

    for site_id, group in grouped_sites:
        site_guards = group["Guard_ID"].tolist()

        attendance_score = calculate_attendance_score(
            site_guards, attendance
        )

        incident_score = calculate_incident_score(
            site_guards, incidents
        )

        complaint_score = calculate_complaint_score(
            site_guards, complaints
        )

        compliance_score = calculate_compliance_score(
            site_guards, compliance
        )

        final_score = calculate_final_score(
            attendance_score,
            incident_score,
            complaint_score,
            compliance_score
        )

        grade = assign_grade(final_score)

        site_records.append({
            "Site_ID": site_id,
            "Guard_Count": len(site_guards),
            "Attendance_Score": attendance_score,
            "Incident_Score": incident_score,
            "Complaint_Score": complaint_score,
            "Compliance_Score": compliance_score,
            "Final_Score": final_score,
            "Grade": grade
        })

    return pd.DataFrame(site_records)

# ============================================================
# SAVE REPORT
# ============================================================

def save_report(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(f"Saved: {OUTPUT_FILE}")

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Site Performance Scoring Engine"
    )

    df = build_site_performance()

    if df.empty:
        logger.warning(
            "No site performance data generated."
        )
        return

    save_report(df)

    logger.info(
        "Site Performance Scoring Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()

