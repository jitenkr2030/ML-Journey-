import logging
import joblib
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class MLLedgerEngine:

    def __init__(self):

        BASE_DIR = Path(__file__).resolve().parent.parent.parent

        MODEL_DIR = BASE_DIR / "ledger-classifier" / "models"

        self.model_path = MODEL_DIR / "ledger_classifier_day12.pkl"
        self.vectorizer_path = MODEL_DIR / "ledger_vectorizer_day12.pkl"

        self.model = None
        self.vectorizer = None

    def load(self):

        self.model = joblib.load(
            self.model_path
        )

        self.vectorizer = joblib.load(
            self.vectorizer_path
        )

        logger.info(
            "Ledger ML model loaded successfully"
        )

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
            "ledger": prediction,
            "confidence": float(confidence)
        }


if __name__ == "__main__":

    engine = MLLedgerEngine()

    result = engine.predict(
        "Office electricity bill payment"
    )

    print(result)
