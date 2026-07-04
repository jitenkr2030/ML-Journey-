import os
import logging
import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")
sys.path.append(str(BASE_DIR))

from core.risk_rules import (
    evaluate_cashflow_risk,
    evaluate_tax_risk,
    evaluate_ratio_risk,
    evaluate_gst_risk,
    evaluate_tds_risk
)

OUTPUT_DIR = CLIENT_DIR / client_name / "output"
FINANCIAL_DIR = OUTPUT_DIR / "financial"
GST_DIR = OUTPUT_DIR / "gst"
TDS_DIR = OUTPUT_DIR / "tds"
BANK_DIR = OUTPUT_DIR / "banking"

RATIO_FILE = FINANCIAL_DIR / "financial_ratios.csv"
CASHFLOW_FILE = FINANCIAL_DIR / "cash_flow.csv"
TAX_FILE = FINANCIAL_DIR / "tax_computation.csv"
GST_FILE = GST_DIR / "gst_summary.csv"
TDS_FILE = TDS_DIR / "tds_summary.csv"
BANK_FILE = BANK_DIR / "bank_reconciliation_output.csv"

OUTPUT_FILE = FINANCIAL_DIR / "risk_analysis.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def safe_load(file_path):
    if file_path.exists():
        return pd.read_csv(file_path)
    return pd.DataFrame()


def analyze_risks():
    risks = []

    cash_df = safe_load(CASHFLOW_FILE)
    if not cash_df.empty:
        cash_value = cash_df.select_dtypes(include="number").sum().sum()
        risk = evaluate_cashflow_risk(cash_value)
        if risk:
            risks.append(risk)

    gst_df = safe_load(GST_FILE)
    if not gst_df.empty:
        gst_value = gst_df.select_dtypes(include="number").sum().sum()
        risk = evaluate_gst_risk(gst_value)
        if risk:
            risks.append(risk)

    tds_df = safe_load(TDS_FILE)
    if not tds_df.empty:
        tds_value = tds_df.select_dtypes(include="number").sum().sum()
        risk = evaluate_tds_risk(tds_value)
        if risk:
            risks.append(risk)

    tax_df = safe_load(TAX_FILE)
    if not tax_df.empty and "Tax_Liability" in tax_df.columns:
        tax_value = tax_df["Tax_Liability"].sum()
        risk = evaluate_tax_risk(tax_value)
        if risk:
            risks.append(risk)

    ratio_df = safe_load(RATIO_FILE)
    if not ratio_df.empty:
        ratio_value = ratio_df.select_dtypes(include="number").mean().mean()
        risk = evaluate_ratio_risk(ratio_value)
        if risk:
            risks.append(risk)

    bank_df = safe_load(BANK_FILE)
    if not bank_df.empty and len(bank_df) > 100:
        risks.append("High Unreconciled Bank Transactions")

    if not risks:
        risks.append("No Major Risk Detected")

    return pd.DataFrame({"Risk_Flag": risks})


def save_risk_report(df):
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Risk analysis saved: {OUTPUT_FILE}")


def run():
    logger.info("Starting Risk Analysis Pipeline")
    risk_df = analyze_risks()
    save_risk_report(risk_df)
    logger.info("Risk Analysis Pipeline Completed")


if __name__ == "__main__":
    run()
