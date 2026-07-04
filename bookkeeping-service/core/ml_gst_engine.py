import logging
import joblib
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class MLGSTEngine:

    def __init__(self):

        BASE_DIR = Path(__file__).resolve().parent.parent.parent

        MODEL_DIR = BASE_DIR / "gst-classifier" / "models"

        self.model_path = MODEL_DIR / "gst_classifier_day11.pkl"
        self.vectorizer_path = MODEL_DIR / "gst_vectorizer_day11.pkl"

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
            "GST ML model loaded successfully"
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
            "gst_type": prediction,
            "confidence": float(confidence)
        }


if __name__ == "__main__":

    engine = MLGSTEngine()

    result = engine.predict(
        "GST payment for office rent"
    )

    print(result)
