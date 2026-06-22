import pandas as pd
import random
from datetime import datetime, timedelta

print("\nSecurity Guard AI Dataset Generator V2")

# ============================================================
# STORAGE
# ============================================================

guard_records = []
attendance_records = []
payroll_records = []
compliance_records = []
incident_records = []
complaint_records = []
leave_records = []

# ============================================================
# MASTER VALUES
# ============================================================

guard_names = [
    "Rahul Kumar",
    "Amit Singh",
    "Ramesh Yadav",
    "Suresh Sharma",
    "Vikas Gupta",
    "Anil Kumar"
]

states = [
    "Delhi",
    "Haryana",
    "UP",
    "Punjab"
]

incident_types = [
    "Late Reporting",
    "Unauthorized Entry",
    "Theft Attempt",
    "Sleeping on Duty"
]

leave_types = [
    "Sick Leave",
    "Casual Leave",
    "Emergency Leave"
]

base_date = datetime(2026, 1, 1)

# ============================================================
# STEP 1 — GUARDS + COMPLIANCE
# ============================================================

guard_risk_map = {}

for i in range(500):

    guard_id = f"G{i+1}"

    joining_date = base_date - timedelta(
        days=random.randint(30, 1500)
    )

    police_verification = random.choice(
        ["Yes", "No"]
    )

    training_status = random.choice(
        ["Completed", "Pending"]
    )

    police_expiry = joining_date + timedelta(
        days=365
    )

    risk_score = 0

    if police_verification == "No":
        risk_score += 50

    if training_status == "Pending":
        risk_score += 30

    if police_expiry < datetime.now():
        risk_score += 20

    if risk_score >= 70:
        risk_level = "High"
    elif risk_score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    guard_risk_map[guard_id] = risk_level

    guard_records.append({
        "Guard_ID": guard_id,
        "Name": random.choice(guard_names),
        "Age": random.randint(21, 55),
        "State": random.choice(states),
        "Joining_Date": joining_date.strftime("%Y-%m-%d"),
        "Salary": random.randint(12000, 30000)
    })

    compliance_records.append({
        "Guard_ID": guard_id,
        "Police_Verification": police_verification,
        "Training_Status": training_status,
        "Police_Expiry": police_expiry.strftime("%Y-%m-%d"),
        "Risk_Level": risk_level
    })

# ============================================================
# STEP 2 — LEAVES
# ============================================================

leave_guard_ids = []

for i in range(300):

    guard_id = f"G{random.randint(1,500)}"

    approved = random.choice(
        ["Yes", "No"]
    )

    leave_records.append({
        "Leave_ID": f"L{i+1}",
        "Guard_ID": guard_id,
        "Leave_Type": random.choice(
            leave_types
        ),
        "Days": random.randint(1, 5),
        "Approved": approved
    })

    if approved == "Yes":
        leave_guard_ids.append(
            guard_id
        )

# ============================================================
# STEP 3 — ATTENDANCE (linked with leaves)
# ============================================================

guard_attendance_summary = {}

for i in range(5000):

    guard_id = f"G{random.randint(1,500)}"

    if guard_id in leave_guard_ids:
        status = "Absent"
    else:
        status = random.choice([
            "Present",
            "Late",
            "Absent",
            "Overtime"
        ])

    hours_worked = random.randint(6, 14)

    attendance_records.append({
        "Guard_ID": guard_id,
        "Date": (
            base_date + timedelta(
                days=random.randint(0,180)
            )
        ).strftime("%Y-%m-%d"),
        "Status": status,
        "Hours_Worked": hours_worked,
        "Late_Minutes": random.randint(0,60),
        "GPS_Match": random.choice(
            ["Yes", "No"]
        )
    })

    if guard_id not in guard_attendance_summary:
        guard_attendance_summary[guard_id] = {
            "absent": 0,
            "overtime": 0,
            "late": 0
        }

    if status == "Absent":
        guard_attendance_summary[guard_id]["absent"] += 1

    if status == "Overtime":
        guard_attendance_summary[guard_id]["overtime"] += hours_worked

    if status == "Late":
        guard_attendance_summary[guard_id]["late"] += 1

# ============================================================
# STEP 4 — PAYROLL (linked with attendance)
# ============================================================

for guard in guard_records:

    guard_id = guard["Guard_ID"]
    basic = guard["Salary"]

    summary = guard_attendance_summary.get(
        guard_id,
        {
            "absent": 0,
            "overtime": 0,
            "late": 0
        }
    )

    absence_deduction = summary["absent"] * 500
    overtime_amount = summary["overtime"] * 50
    late_penalty = summary["late"] * 100

    net_pay = (
        basic
        - absence_deduction
        + overtime_amount
        - late_penalty
    )

    payroll_records.append({
        "Guard_ID": guard_id,
        "Basic_Salary": basic,
        "Absence_Deduction": absence_deduction,
        "Overtime_Amount": overtime_amount,
        "Late_Penalty": late_penalty,
        "PF": round(basic * 0.12, 2),
        "ESI": round(basic * 0.0075, 2),
        "Net_Pay": net_pay
    })

# ============================================================
# STEP 5 — INCIDENTS
# ============================================================

for i in range(800):

    guard_id = f"G{random.randint(1,500)}"

    risk_level = guard_risk_map[
        guard_id
    ]

    if risk_level == "High":
        severity = random.choice(
            ["Medium", "High"]
        )
    else:
        severity = random.choice(
            ["Low", "Medium"]
        )

    incident_records.append({
        "Incident_ID": f"I{i+1}",
        "Guard_ID": guard_id,
        "Incident_Type": random.choice(
            incident_types
        ),
        "Severity": severity
    })

# ============================================================
# STEP 6 — COMPLAINTS (linked with incidents)
# ============================================================

for incident in incident_records:

    if incident["Severity"] in [
        "Medium",
        "High"
    ]:

        complaint_records.append({
            "Guard_ID": incident["Guard_ID"],
            "Complaint_Type": incident["Incident_Type"],
            "Satisfaction_Score": random.randint(1,3)
        })

# ============================================================
# SAVE CSV
# ============================================================

pd.DataFrame(guard_records).to_csv(
    "security-ai/datasets/guards_master.csv",
    index=False
)

pd.DataFrame(compliance_records).to_csv(
    "security-ai/datasets/compliance.csv",
    index=False
)

pd.DataFrame(leave_records).to_csv(
    "security-ai/datasets/leaves.csv",
    index=False
)

pd.DataFrame(attendance_records).to_csv(
    "security-ai/datasets/attendance.csv",
    index=False
)

pd.DataFrame(payroll_records).to_csv(
    "security-ai/datasets/payroll.csv",
    index=False
)

pd.DataFrame(incident_records).to_csv(
    "security-ai/datasets/incidents.csv",
    index=False
)

pd.DataFrame(complaint_records).to_csv(
    "security-ai/datasets/complaints.csv",
    index=False
)

print("\nRelational Security Dataset Generated Successfully!")

