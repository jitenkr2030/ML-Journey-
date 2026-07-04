import logging
from ml_financial_engine import MLFinancialEngine


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# GLOBAL ML ENGINE
# ============================================================

financial_engine = MLFinancialEngine()


# ============================================================
# FINANCIAL STATEMENT TYPE
# ============================================================

def predict_financial_statement(
    transaction_text
):

    result = financial_engine.predict(
        transaction_text
    )

    return result["statement_type"]


# ============================================================
# CONFIDENCE
# ============================================================

def predict_financial_confidence(
    transaction_text
):

    result = financial_engine.predict(
        transaction_text
    )

    return result["confidence"]


# ============================================================
# FALLBACK RULES
# ============================================================

def fallback_financial_statement(
    category
):

    RULES = {
        "Payroll": "Expense",
        "Rent": "Expense",
        "Utilities": "Expense",
        "Marketing": "Expense",
        "Revenue": "Income",
        "GST": "Liability",
        "Asset": "Asset",
        "Bank Charges": "Expense",
        "Loan": "Liability"
    }

    return RULES.get(
        category,
        "Unknown"
    )


# ============================================================
# HYBRID ENGINE
# ============================================================

def hybrid_financial_classification(
    transaction_text,
    category,
    threshold=0.70
):

    result = financial_engine.predict(
        transaction_text
    )

    if result["confidence"] >= threshold:

        return {
            "statement_type": result["statement_type"],
            "confidence": result["confidence"],
            "source": "ML"
        }

    fallback_result = fallback_financial_statement(
        category
    )

    return {
        "statement_type": fallback_result,
        "confidence": result["confidence"],
        "source": "RULE"
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    result = hybrid_financial_classification(
        "Office rent payment",
        "Rent"
    )

    print(result)
