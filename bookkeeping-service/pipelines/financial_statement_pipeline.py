import os
import logging
import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "core"))

from config.paths import (
    ACCOUNTING_OUTPUT_DIR,
    FINANCIAL_OUTPUT_DIR
)

from journal_rules import generate_journal_entry
from financial_rules import hybrid_financial_classification

ACCOUNTING_FILE = Path(ACCOUNTING_OUTPUT_DIR) / "accounting_output.csv"

JOURNAL_FILE = Path(FINANCIAL_OUTPUT_DIR) / "journal_entries.csv"
P_AND_L_FILE = Path(FINANCIAL_OUTPUT_DIR) / "profit_and_loss.csv"
BALANCE_SHEET_FILE = Path(FINANCIAL_OUTPUT_DIR) / "balance_sheet.csv"
TRIAL_BALANCE_FILE = Path(FINANCIAL_OUTPUT_DIR) / "trial_balance.csv"
CASHFLOW_FILE = Path(FINANCIAL_OUTPUT_DIR) / "cash_flow.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def load_data():
    return pd.read_csv(ACCOUNTING_FILE)


def run_pipeline():
    logger.info("Starting Financial Statement Pipeline")

    Path(FINANCIAL_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    df = load_data()

    df.to_csv(JOURNAL_FILE, index=False)

    pd.DataFrame([
        ["Revenue", df["Amount"].sum()]
    ], columns=["Particulars", "Amount"]).to_csv(P_AND_L_FILE, index=False)

    pd.DataFrame([
        ["Assets", df["Amount"].sum()]
    ], columns=["Particulars", "Amount"]).to_csv(BALANCE_SHEET_FILE, index=False)

    pd.DataFrame([
        ["Trial", df["Amount"].sum()]
    ], columns=["Particulars", "Amount"]).to_csv(TRIAL_BALANCE_FILE, index=False)

    pd.DataFrame([
        ["Cash Flow", df["Amount"].sum()]
    ], columns=["Particulars", "Amount"]).to_csv(CASHFLOW_FILE, index=False)

    logger.info("Financial Statement Pipeline Completed")


if __name__ == "__main__":
    run_pipeline()
