from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "bookkeeping-service"))

from core.ml_gst_engine import MLGSTEngine


gst_engine = MLGSTEngine()


def predict_gst_type(transaction_text):

    result = gst_engine.predict(
        transaction_text
    )

    return result["gst_type"]


def predict_gst_confidence(transaction_text):

    result = gst_engine.predict(
        transaction_text
    )

    return result["confidence"]


def calculate_gst(amount, rate=18):

    return (amount * rate) / 100
