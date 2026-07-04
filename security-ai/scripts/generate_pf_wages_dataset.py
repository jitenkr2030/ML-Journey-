import pandas as pd
import random
from pathlib import Path
from datetime import datetime, timedelta

print("\nGenerating PF/ESI Wage Reconciliation Dataset")

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "raw"

RAW_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = RAW_DIR / "pf_wages_reconciliation.xlsx"

NUM_EMPLOYEES = 500
NUM_SITES = 12

# ============================================================
# MASTER DATA
# ============================================================

names = [
    "Rahul Kumar",
    "Amit Singh",
    "Ramesh Yadav",
    "Suresh Sharma",
    "Vikas Gupta",
    "Anil Kumar",
    "Deepak Verma",
    "Jitender Kumar"
]

banks = [
    "SBI",
    "HDFC",
    "PNB",
    "ICICI"
]

leave_types = [
    "Sick Leave",
    "Casual Leave",
    "Emergency Leave"
]

site_ids = [f"S{i+1}" for i in range(NUM_SITES)]

# ============================================================
# STORAGE
# ============================================================

employee_master = []
wages_register = []
attendance = []
pf_ecr = []
esi_challan = []
overtime_register = []
leave_register = []

# ============================================================
# GENERATE DATA
# ============================================================

for i in range(NUM_EMPLOYEES):

    emp_id = f"E{i+1}"
    site_id = random.choice(site_ids)

    rate_of_wage = random.randint(
        15000,
        30000
    )

    days_worked = random.randint(
        20,
        31
    )

    overtime_hours = random.randint(
        0,
        50
    )

    basic_vda = round(
        (rate_of_wage / 26) * days_worked,
        2
    )

    special_basic = random.randint(
        0,
        2000
    )

    da = random.randint(
        0,
        1000
    )

    overtime_payment = overtime_hours * 80

    total_wages = (
        basic_vda
        + special_basic
        + da
        + overtime_payment
    )

    pf_wage = min(
        basic_vda,
        15000
    )

    pf_employee = round(
        pf_wage * 0.12,
        2
    )

    pf_employer = round(
        pf_wage * 0.12,
        2
    )

    esi_employee = round(
        basic_vda * 0.0075,
        2
    )

    esi_employer = round(
        basic_vda * 0.0325,
        2
    )

    deductions = (
        pf_employee
        + esi_employee
    )

    net_payment = total_wages - deductions

    uan = f"UAN{100000+i}"
    ip_number = f"IP{200000+i}"

    # Employee Master
    employee_master.append({
        "Employee_ID": emp_id,
        "Name": random.choice(names),
        "Site_ID": site_id,
        "UAN": uan,
        "IP_Number": ip_number,
        "Bank": random.choice(banks),
        "Joining_Date": (
            datetime(2024, 1, 1)
            + timedelta(days=random.randint(1, 500))
        ).strftime("%Y-%m-%d")
    })

    # Wage Register
    wages_register.append({
        "Employee_ID": emp_id,
        "Site_ID": site_id,
        "Rate_Of_Wage": rate_of_wage,
        "Days_Worked": days_worked,
        "Overtime_Hours": overtime_hours,
        "Basic_VDA": basic_vda,
        "Special_Basic": special_basic,
        "DA": da,
        "Overtime_Payment": overtime_payment,
        "Total_Wages": total_wages,
        "PF_Employee": pf_employee,
        "ESI_Employee": esi_employee,
        "Net_Payment": net_payment,
        "PF_Employer": pf_employer,
        "ESI_Employer": esi_employer
    })

    # Attendance
    attendance.append({
        "Employee_ID": emp_id,
        "Days_Present": days_worked,
        "Absent_Days": 31 - days_worked,
        "Overtime_Hours": overtime_hours
    })

    # PF ECR
    pf_ecr.append({
        "Employee_ID": emp_id,
        "UAN": uan,
        "PF_Wages": pf_wage,
        "Employee_PF": pf_employee,
        "Employer_PF": pf_employer
    })

    # ESI Challan
    esi_challan.append({
        "Employee_ID": emp_id,
        "IP_Number": ip_number,
        "ESI_Wages": basic_vda,
        "Employee_ESI": esi_employee,
        "Employer_ESI": esi_employer
    })

    # Overtime Register
    overtime_register.append({
        "Employee_ID": emp_id,
        "Overtime_Hours": overtime_hours,
        "Overtime_Amount": overtime_payment
    })

    # Leave Register
    leave_register.append({
        "Employee_ID": emp_id,
        "Leave_Type": random.choice(leave_types),
        "Leave_Days": random.randint(0, 5)
    })

# ============================================================
# SAVE EXCEL
# ============================================================

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    pd.DataFrame(employee_master).to_excel(
        writer,
        sheet_name="employee_master",
        index=False
    )

    pd.DataFrame(wages_register).to_excel(
        writer,
        sheet_name="wages_register",
        index=False
    )

    pd.DataFrame(attendance).to_excel(
        writer,
        sheet_name="attendance",
        index=False
    )

    pd.DataFrame(pf_ecr).to_excel(
        writer,
        sheet_name="pf_ecr",
        index=False
    )

    pd.DataFrame(esi_challan).to_excel(
        writer,
        sheet_name="esi_challan",
        index=False
    )

    pd.DataFrame(overtime_register).to_excel(
        writer,
        sheet_name="overtime_register",
        index=False
    )

    pd.DataFrame(leave_register).to_excel(
        writer,
        sheet_name="leave_register",
        index=False
    )

print(f"\nDataset saved: {OUTPUT_FILE}")

