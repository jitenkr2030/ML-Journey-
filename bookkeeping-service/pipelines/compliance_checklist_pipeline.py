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

from core.compliance_rules import get_compliance_checklist

OUTPUT_DIR = CLIENT_DIR / client_name / "output"
FINANCIAL_DIR = OUTPUT_DIR / "financial"
OUTPUT_FILE = FINANCIAL_DIR / "compliance_checklist.csv"

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
# BUILD CHECKLIST
# ============================================================

def build_checklist():
    checklist = get_compliance_checklist()

    rows = []

    for item in checklist:
        rows.append({
            "Compliance_Type": item["Compliance_Type"],
            "Form": item["Form"],
            "Due_Date": item["Due_Date"],
            "Status": item["Status"]
        })

    return pd.DataFrame(rows)

# ============================================================
# SAVE
# ============================================================

def save_checklist(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Compliance checklist saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Compliance Checklist Pipeline"
    )

    df = build_checklist()
    save_checklist(df)

    logger.info(
        "Compliance Checklist Pipeline Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()

