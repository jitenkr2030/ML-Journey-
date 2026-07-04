import logging
import joblib
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class MLFinancialEngine:

    def __init__(self):

        BASE_DIR = Path(__file__).resolve().parent.parent.parent

        MODEL_DIR = (
            BASE_DIR /
            "financial-statement-ai" /
            "models"
        )

        self.model_path = (
            MODEL_DIR /
            "financial_statement_model.pkl"
        )

        self.vectorizer_path = (
            MODEL_DIR /
            "financial_statement_vectorizer.pkl"
        )

        self.model = None
        self.vectorizer = None


    # ============================================================
    # LOAD MODEL
    # ============================================================

    def load(self):

        self.model = joblib.load(
            self.model_path
        )

        self.vectorizer = joblib.load(
            self.vectorizer_path
        )

        logger.info(
            "Financial statement ML model loaded successfully"
        )


    # ============================================================
    # PREDICT
    # ============================================================

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
            self.model.predict_proba(
                vector
            )[0]
        )

        return {
            "statement_type": prediction,
            "confidence": float(confidence)
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    engine = MLFinancialEngine()

    result = engine.predict(
        "Office rent paid through bank"
    )

    print(result)
