import os
import logging
import pandas as pd
from pathlib import Path
import sys

# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")
sys.path.append(str(BASE_DIR))

from core.tax_rules import (
    calculate_tax,
    calculate_advance_tax,
    get_total_advance_tax
)

FINANCIAL_DIR = CLIENT_DIR / client_name / "output" / "financial"
LEDGER_DIR = CLIENT_DIR / client_name / "output" / "ledgers"

PL_FILE = FINANCIAL_DIR / "profit_and_loss.csv"
DEPRECIATION_FILE = FINANCIAL_DIR / "depreciation_chart.csv"

OUTPUT_FILE = FINANCIAL_DIR / "tax_computation.csv"

FINANCIAL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ============================================================
# SAFE LOAD
# ============================================================

def safe_load(file_path):
    if file_path.exists():
        return pd.read_csv(file_path)
    return pd.DataFrame()

# ============================================================
# GET PROFIT
# ============================================================

def get_profit():
    df = safe_load(PL_FILE)

    if df.empty:
        return 0.0

    numeric_cols = df.select_dtypes(include="number")

    if numeric_cols.empty:
        return 0.0

    return numeric_cols.sum().sum()

# ============================================================
# GET DEPRECIATION
# ============================================================

def get_depreciation():
    df = safe_load(DEPRECIATION_FILE)

    if df.empty:
        return 0.0

    if "Depreciation" not in df.columns:
        return 0.0

    return df["Depreciation"].sum()

# ============================================================
# GET DISALLOWANCES
# ============================================================

def get_disallowances():
    disallowance_files = [
        "bank_charges_expense.csv",
        "marketing_expense.csv",
        "professional_fees.csv"
    ]

    total = 0.0

    for file_name in disallowance_files:
        file_path = LEDGER_DIR / file_name
        df = safe_load(file_path)

        if df.empty:
            continue

        if "Amount" in df.columns:
            total += df["Amount"].sum()

    return total

# ============================================================
# COMPUTE TAX
# ============================================================

def compute_tax():
    book_profit = get_profit()
    depreciation = get_depreciation()
    disallowances = get_disallowances()

    taxable_income = (
        book_profit
        + disallowances
        - depreciation
    )

    taxable_income = max(
        taxable_income,
        0
    )

    tax_liability = calculate_tax(
        taxable_income
    )

    advance_tax_breakup = calculate_advance_tax(
        tax_liability
    )

    total_advance_tax = get_total_advance_tax(
        tax_liability
    )

    return {
        "Book_Profit": round(book_profit, 2),
        "Add_Back_Disallowances": round(disallowances, 2),
        "Less_Depreciation": round(depreciation, 2),
        "Taxable_Income": round(taxable_income, 2),
        "Tax_Liability": round(tax_liability, 2),
        "Advance_Tax_Required": round(total_advance_tax, 2),
        "Q1_15%": advance_tax_breakup["Q1_15%"],
        "Q2_45%": advance_tax_breakup["Q2_45%"],
        "Q3_75%": advance_tax_breakup["Q3_75%"],
        "Q4_100%": advance_tax_breakup["Q4_100%"]
    }

# ============================================================
# SAVE
# ============================================================

def save_tax_computation(data):
    df = pd.DataFrame([data])

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Tax computation saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Tax Computation Pipeline"
    )

    tax_data = compute_tax()
    save_tax_computation(tax_data)

    logger.info(
        "Tax Computation Pipeline Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()

