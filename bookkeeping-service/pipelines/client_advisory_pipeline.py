import os
import logging
import pandas as pd
from pathlib import Path

# ============================================================
# PATH CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")
FINANCIAL_DIR = CLIENT_DIR / client_name / "output" / "financial"

RISK_FILE = FINANCIAL_DIR / "risk_analysis.csv"
TAX_FILE = FINANCIAL_DIR / "tax_computation.csv"
RATIO_FILE = FINANCIAL_DIR / "financial_ratios.csv"
COMPLIANCE_FILE = FINANCIAL_DIR / "compliance_checklist.csv"
CLOSING_FILE = FINANCIAL_DIR / "closing_checklist.csv"

OUTPUT_FILE = FINANCIAL_DIR / "client_advisory.csv"

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
# GENERATE ADVISORY
# ============================================================

def generate_advisory():
    advisory = []

    # Risk based advice
    risk_df = safe_load(RISK_FILE)

    if not risk_df.empty:
        risks = risk_df["Risk_Flag"].astype(str).tolist()

        for risk in risks:
            if "GST" in risk:
                advisory.append("Review GST planning and optimize input credits")

            if "TDS" in risk:
                advisory.append("Clear pending TDS liabilities immediately")

            if "Cash Flow" in risk:
                advisory.append("Improve receivable collection for better cash flow")

            if "Tax" in risk:
                advisory.append("Plan advance tax properly to avoid interest")

            if "Financial Ratios" in risk:
                advisory.append("Control expenses and improve profitability")

            if "Bank" in risk:
                advisory.append("Complete pending bank reconciliations")

    # Tax advice
    tax_df = safe_load(TAX_FILE)

    if not tax_df.empty:
        if "Tax_Liability" in tax_df.columns:
            tax_amount = tax_df["Tax_Liability"].sum()

            if tax_amount > 500000:
                advisory.append("Consider tax-saving investments before year-end")

    # Compliance advice
    compliance_df = safe_load(COMPLIANCE_FILE)

    if not compliance_df.empty:
        pending = compliance_df[
            compliance_df["Status"] == "Pending"
        ]

        if len(pending) > 0:
            advisory.append("Complete pending compliance tasks immediately")

    # Closing advice
    closing_df = safe_load(CLOSING_FILE)

    if not closing_df.empty:
        pending = closing_df[
            closing_df["Status"] == "Pending"
        ]

        if len(pending) > 0:
            advisory.append("Finalize year-end closing tasks before audit")

    if len(advisory) == 0:
        advisory.append("Books look healthy. Maintain compliance discipline")

    return pd.DataFrame({
        "Advisory_Notes": advisory
    })

# ============================================================
# SAVE
# ============================================================

def save_advisory(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Client advisory saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Client Advisory Pipeline"
    )

    advisory_df = generate_advisory()

    save_advisory(advisory_df)

    logger.info(
        "Client Advisory Pipeline Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
