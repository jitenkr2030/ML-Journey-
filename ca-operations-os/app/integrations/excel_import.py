import pandas as pd
from pathlib import Path


class ExcelImporter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load(self):
        if not self.file_path.exists():
            raise FileNotFoundError(f"{self.file_path} not found")

        if self.file_path.suffix == ".csv":
            df = pd.read_csv(self.file_path)
        elif self.file_path.suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(self.file_path)
        else:
            raise ValueError("Unsupported file type")

        return df

    def export_csv(self, output_path: str):
        df = self.load()
        df.to_csv(output_path, index=False)
        return output_path
