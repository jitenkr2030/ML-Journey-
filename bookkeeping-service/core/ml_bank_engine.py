import sys
import logging
import joblib
from pathlib import Path


# ============================================================
# FIX IMPORT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# BANK ML ENGINE
# ============================================================

class MLBankEngine:

    def __init__(self):

        MODEL_DIR = BASE_DIR / "bank-reconciliation-ai" / "models"

        self.model_path = MODEL_DIR / "reconciliation_model.pkl"
        self.vectorizer_path = MODEL_DIR / "reconciliation_vectorizer.pkl"

        self.model = None
        self.vectorizer = None


    # ========================================================
    # LOAD MODEL
    # ========================================================

    def load(self):

        self.model = joblib.load(
            self.model_path
        )

        self.vectorizer = joblib.load(
            self.vectorizer_path
        )

        logger.info(
            "Bank reconciliation ML model loaded successfully"
        )


    # ========================================================
    # PREDICT
    # ========================================================

    def predict(self, text):

        if self.model is None:
            self.load()

        vector = self.vectorizer.transform(
            [text]
        )

        prediction = self.model.predict(
            vector
        )[0]

        confidence = max(
            self.model.predict_proba(vector)[0]
        )

        return {
            "status": str(prediction),
            "confidence": float(confidence)
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    engine = MLBankEngine()

    result = engine.predict(
        "Salary payment through SBI"
    )

    print(result)

