from ml_tds_engine import MLTDSEngine

tds_engine = MLTDSEngine()


def predict_tds_section(text):
    result = tds_engine.predict(text)
    return result["tds_section"]


def predict_tds_confidence(text):
    result = tds_engine.predict(text)
    return result["confidence"]


def calculate_tds(amount, rate=10):
    return round(
        amount * rate / 100,
        2
    )
