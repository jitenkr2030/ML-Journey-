import pandas as pd
from pathlib import Path


class BankImporter:
    REQUIRED_COLUMNS = ["date", "description", "amount"]

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load(self):
        df = pd.read_csv(self.file_path)

        missing = [
            col for col in self.REQUIRED_COLUMNS
            if col not in df.columns
        ]

        if missing:
            raise ValueError(f"Missing columns: {missing}")

        return df
