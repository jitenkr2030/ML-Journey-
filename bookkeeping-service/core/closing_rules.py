import pandas as pd

# ============================================================
# YEAR-END CLOSING RULE DEFINITIONS
# ============================================================

CLOSING_CHECKLIST = [
    {
        "task": "Trial Balance Generated",
        "path": "outputs/financial/trial_balance.csv"
    },
    {
        "task": "GST Reconciled",
        "path": "outputs/gst/gst_summary.csv"
    },
    {
        "task": "TDS Reconciled",
        "path": "outputs/tds/tds_summary.csv"
    },
    {
        "task": "Bank Reconciled",
        "path": "outputs/banking/bank_reconciliation_output.csv"
    },
    {
        "task": "Depreciation Posted",
        "path": "outputs/financial/depreciation_chart.csv"
    },
    {
        "task": "Expenses Verified",
        "path": "outputs/financial/profit_and_loss.csv"
    },
    {
        "task": "Closing Stock Verified",
        "path": "outputs/financial/balance_sheet.csv"
    },
    {
        "task": "Working Notes Completed",
        "path": "outputs/financial/working_notes.csv"
    },
    {
        "task": "Risk Analysis Completed",
        "path": "outputs/financial/risk_analysis.csv"
    },
    {
        "task": "Tax Computation Completed",
        "path": "outputs/financial/tax_computation.csv"
    }
]

# ============================================================
# GET CLOSING CHECKLIST
# ============================================================

def get_closing_checklist():
    return CLOSING_CHECKLIST


# ============================================================
# SAVE CHECKLIST
# ============================================================

def save_closing_checklist(output_path, df):
    df.to_csv(output_path, index=False)
    return output_path
