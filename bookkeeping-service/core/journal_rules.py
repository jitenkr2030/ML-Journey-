from ml_journal_engine import MLJournalEngine

journal_engine = MLJournalEngine()


def generate_journal_entry(text, amount):

    result = journal_engine.predict(
        text
    )

    return {
        "debit_account": result["debit"],
        "credit_account": result["credit"],
        "amount": amount
    }
