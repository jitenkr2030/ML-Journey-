from ml_ledger_engine import MLLedgerEngine

ledger_engine = MLLedgerEngine()


def predict_ledger(text):
    result = ledger_engine.predict(text)
    return result["ledger"]


def predict_ledger_confidence(text):
    result = ledger_engine.predict(text)
    return result["confidence"]
