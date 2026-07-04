# ============================================================
# COMPLIANCE RULE ENGINE
# Supports:
# - GST due dates
# - TDS due dates
# - ROC due dates
# - Compliance checklist generation
# ============================================================

from datetime import datetime

# ============================================================
# DUE DATES
# ============================================================

GST_DUE_DATES = {
    "GSTR1": "11",
    "GSTR3B": "20"
}

TDS_DUE_DATES = {
    "Q1": "31-07",
    "Q2": "31-10",
    "Q3": "31-01",
    "Q4": "31-05"
}

ROC_DUE_DATES = {
    "AOC4": "30-10",
    "MGT7": "30-11"
}

# ============================================================
# STATUS CHECK
# ============================================================

def check_due_status(due_date_str):
    today = datetime.today()

    try:
        due_date = datetime.strptime(
            f"{today.year}-{due_date_str}",
            "%Y-%d"
        )
    except:
        try:
            due_date = datetime.strptime(
                f"{today.year}-{due_date_str}",
                "%Y-%d-%m"
            )
        except:
            return "Unknown"

    if today <= due_date:
        return "Pending"
    return "Overdue"

# ============================================================
# MAIN CHECKLIST ENGINE
# ============================================================

def get_compliance_checklist():
    checklist = []

    for form, due in GST_DUE_DATES.items():
        checklist.append({
            "Compliance_Type": "GST",
            "Form": form,
            "Due_Date": due,
            "Status": "Check"
        })

    for form, due in TDS_DUE_DATES.items():
        checklist.append({
            "Compliance_Type": "TDS",
            "Form": form,
            "Due_Date": due,
            "Status": "Check"
        })

    for form, due in ROC_DUE_DATES.items():
        checklist.append({
            "Compliance_Type": "ROC",
            "Form": form,
            "Due_Date": due,
            "Status": "Check"
        })

    return checklist

