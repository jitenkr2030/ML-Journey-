import logging
import joblib
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class MLJournalEngine:

    def __init__(self):

        BASE_DIR = Path(__file__).resolve().parent.parent.parent

        MODEL_DIR = BASE_DIR / "journal-entry-ai" / "models"

        self.debit_model_path = MODEL_DIR / "debit_model.pkl"
        self.credit_model_path = MODEL_DIR / "credit_model.pkl"
        self.vectorizer_path = MODEL_DIR / "vectorizer.pkl"

        self.debit_model = None
        self.credit_model = None
        self.vectorizer = None

    def load(self):

        self.debit_model = joblib.load(
            self.debit_model_path
        )

        self.credit_model = joblib.load(
            self.credit_model_path
        )

        self.vectorizer = joblib.load(
            self.vectorizer_path
        )

        logger.info(
            "Journal AI models loaded successfully"
        )

    def predict(self, text):

        if self.debit_model is None:
            self.load()

        vector = self.vectorizer.transform(
            [text]
        )

        debit = self.debit_model.predict(
            vector
        )[0]

        credit = self.credit_model.predict(
            vector
        )[0]

        return {
            "debit": debit,
            "credit": credit
        }


if __name__ == "__main__":

    engine = MLJournalEngine()

    result = engine.predict(
        "Office rent paid by bank"
    )

    print(result)
