import logging
import sys
from pathlib import Path


# ============================================================
# FIX IMPORT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from core.ml_bank_engine import MLBankEngine


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# GLOBAL ML ENGINE
# ============================================================

bank_engine = MLBankEngine()


# ============================================================
# BANK STATUS PREDICTION
# ============================================================

def predict_bank_status(transaction_text):

    result = bank_engine.predict(
        transaction_text
    )

    return result["status"]


# ============================================================
# BANK CONFIDENCE
# ============================================================

def predict_bank_confidence(transaction_text):

    result = bank_engine.predict(
        transaction_text
    )

    return result["confidence"]


# ============================================================
# RULE FALLBACK
# ============================================================

def fallback_bank_status(amount_1, amount_2):

    if float(amount_1) == float(amount_2):
        return "Matched"

    return "Unmatched"


# ============================================================
# HYBRID BANK RECONCILIATION
# ============================================================

def hybrid_bank_reconciliation(
    transaction_text,
    amount_1,
    amount_2,
    threshold=0.70
):

    result = bank_engine.predict(
        transaction_text
    )

    if result["confidence"] >= threshold:

        return {
            "status": result["status"],
            "confidence": result["confidence"],
            "source": "ML"
        }

    fallback_status = fallback_bank_status(
        amount_1,
        amount_2
    )

    return {
        "status": fallback_status,
        "confidence": result["confidence"],
        "source": "RULE"
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    result = hybrid_bank_reconciliation(
        "Salary payment through SBI",
        50000,
        50000
    )

    print(result)
