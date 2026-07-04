import logging
import joblib
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_DIR = BASE_DIR / "accounting-assistant" / "models"

MODEL_PATH = MODEL_DIR / "accounting_assistant_model.pkl"
VECTORIZER_PATH = MODEL_DIR / "accounting_assistant_vectorizer.pkl"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# ML ENGINE
# ============================================================

class MLAccountingEngine:

    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.load()

    # ========================================================
    # LOAD MODEL
    # ========================================================

    def load(self):

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file missing: {MODEL_PATH}"
            )

        if not VECTORIZER_PATH.exists():
            raise FileNotFoundError(
                f"Vectorizer file missing: {VECTORIZER_PATH}"
            )

        self.model = joblib.load(
            MODEL_PATH
        )

        self.vectorizer = joblib.load(
            VECTORIZER_PATH
        )

        logger.info(
            "Accounting ML model loaded successfully"
        )

    # ========================================================
    # PREDICT CATEGORY
    # ========================================================

    def predict(self, text):

        vector = self.vectorizer.transform(
            [text]
        )

        prediction = self.model.predict(
            vector
        )[0]

        confidence = self.model.predict_proba(
            vector
        ).max()

        return {
            "category": prediction,
            "confidence": float(confidence)
        }

    # ========================================================
    # BATCH PREDICT
    # ========================================================

    def batch_predict(self, texts):

        vectors = self.vectorizer.transform(
            texts
        )

        predictions = self.model.predict(
            vectors
        )

        probabilities = self.model.predict_proba(
            vectors
        )

        results = []

        for i in range(len(texts)):
            results.append({
                "text": texts[i],
                "category": predictions[i],
                "confidence": float(
                    probabilities[i].max()
                )
            })

        return results


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    engine = MLAccountingEngine()

    result = engine.predict(
        "Salary Paid to Employees"
    )

    print(result)
