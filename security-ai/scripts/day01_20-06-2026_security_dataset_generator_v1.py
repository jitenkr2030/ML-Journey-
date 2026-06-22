import pandas as pd
import random
from datetime import datetime, timedelta

print("\nSecurity Guard AI Dataset Generator V1")

# ============================================================
# MASTER DATA
# ============================================================

guard_records = []
client_records = []
assignment_records = []
attendance_records = []
payroll_records = []
compliance_records = []
incident_records = []
complaint_records = []
leave_records = []

guard_names = [
    "Rahul Kumar",
    "Amit Singh",
    "Ramesh Yadav",
    "Suresh Sharma",
    "Vikas Gupta",
    "Anil Kumar",
    "Deepak Verma"
]

client_names = [
    "ABC Factory",
    "XYZ School",
    "Metro Hospital",
    "Prime Warehouse",
    "Royal Society"
]

states = ["Delhi", "Haryana", "UP", "Punjab"]

incident_types = [
    "Late Reporting",
    "Unauthorized Entry",
    "Theft Attempt",
    "Visitor Misconduct"
]

complaint_types = [
    "Late Arrival",
    "Misbehavior",
    "Sleeping on Duty"
]

leave_types = [
    "Sick Leave",
    "Casual Leave",
    "Emergency Leave"
]

base_date = datetime(2026, 1, 1)

# ============================================================
# CLIENTS
# ============================================================

for i in range(20):
    client_records.append({
        "Client_ID": f"C{i+1}",
        "Client_Name": random.choice(client_names),
        "Industry": random.choice(
            ["Factory", "School", "Hospital", "Warehouse"]
        ),
        "Contract_Value": random.randint(50000, 500000),
        "Risk_Level": random.choice(
            ["Low", "Medium", "High"]
        )
    })

# ============================================================
# GUARDS
# ============================================================

for i in range(500):

    joining_date = base_date - timedelta(
        days=random.randint(30, 1500)
    )

    police_expiry = joining_date + timedelta(days=365)

    salary = random.randint(
        12000,
        30000
    )

    guard_records.append({
        "Guard_ID": f"G{i+1}",
        "Name": random.choice(guard_names),
        "Age": random.randint(21, 55),
        "State": random.choice(states),
        "Joining_Date": joining_date.strftime("%Y-%m-%d"),
        "Experience_Years": random.randint(0, 15),
        "Salary": salary
    })

    compliance_records.append({
        "Guard_ID": f"G{i+1}",
        "Police_Verification": random.choice(
            ["Yes", "No"]
        ),
        "Training_Status": random.choice(
            ["Completed", "Pending"]
        ),
        "Police_Expiry": police_expiry.strftime("%Y-%m-%d"),
        "Compliance_Status": random.choice(
            ["Compliant", "Non-Compliant"]
        )
    })

# ============================================================
# ASSIGNMENTS
# ============================================================

for i in range(800):
    assignment_records.append({
        "Assignment_ID": f"A{i+1}",
        "Guard_ID": f"G{random.randint(1,500)}",
        "Client_ID": f"C{random.randint(1,20)}",
        "Shift": random.choice(
            ["Morning", "Evening", "Night"]
        ),
        "Site_ID": f"S{random.randint(1,100)}"
    })

# ============================================================
# ATTENDANCE
# ============================================================

for i in range(5000):

    hours = random.randint(6, 14)

    attendance_records.append({
        "Guard_ID": f"G{random.randint(1,500)}",
        "Date": (
            base_date + timedelta(
                days=random.randint(0,180)
            )
        ).strftime("%Y-%m-%d"),
        "Hours_Worked": hours,
        "Late_Minutes": random.randint(0, 60),
        "GPS_Match": random.choice(
            ["Yes", "No"]
        ),
        "Status": random.choice(
            ["Present", "Absent", "Late", "Overtime"]
        )
    })

# ============================================================
# PAYROLL
# ============================================================

for i in range(500):

    basic = random.randint(
        12000,
        30000
    )

    overtime = random.randint(0, 50)

    payroll_records.append({
        "Guard_ID": f"G{i+1}",
        "Basic_Salary": basic,
        "Overtime_Hours": overtime,
        "Overtime_Amount": overtime * 100,
        "PF": round(basic * 0.12, 2),
        "ESI": round(basic * 0.0075, 2),
        "Net_Pay": basic + (overtime * 100)
    })

# ============================================================
# INCIDENTS
# ============================================================

for i in range(1000):
    incident_records.append({
        "Incident_ID": f"I{i+1}",
        "Guard_ID": f"G{random.randint(1,500)}",
        "Incident_Type": random.choice(
            incident_types
        ),
        "Severity": random.choice(
            ["Low", "Medium", "High"]
        ),
        "Resolved": random.choice(
            ["Yes", "No"]
        )
    })

# ============================================================
# COMPLAINTS
# ============================================================

for i in range(800):
    complaint_records.append({
        "Complaint_ID": f"CP{i+1}",
        "Client_ID": f"C{random.randint(1,20)}",
        "Guard_ID": f"G{random.randint(1,500)}",
        "Complaint_Type": random.choice(
            complaint_types
        ),
        "Satisfaction_Score": random.randint(1, 5)
    })

# ============================================================
# LEAVES
# ============================================================

for i in range(600):
    leave_records.append({
        "Leave_ID": f"L{i+1}",
        "Guard_ID": f"G{random.randint(1,500)}",
        "Leave_Type": random.choice(
            leave_types
        ),
        "Days": random.randint(1, 7),
        "Approved": random.choice(
            ["Yes", "No"]
        )
    })

# ============================================================
# SAVE CSV FILES
# ============================================================

pd.DataFrame(guard_records).to_csv(
    "security-ai/datasets/guards_master.csv",
    index=False
)

pd.DataFrame(client_records).to_csv(
    "security-ai/datasets/clients.csv",
    index=False
)

pd.DataFrame(assignment_records).to_csv(
    "security-ai/datasets/site_assignments.csv",
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

pd.DataFrame(compliance_records).to_csv(
    "security-ai/datasets/compliance.csv",
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

pd.DataFrame(leave_records).to_csv(
    "security-ai/datasets/leaves.csv",
    index=False
)

print("\nAll security datasets generated successfully!")

