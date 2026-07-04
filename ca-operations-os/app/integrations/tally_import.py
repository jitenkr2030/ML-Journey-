import shutil
from pathlib import Path


class TallyImporter:
    def __init__(self, source_file: str, target_dir: str):
        self.source_file = Path(source_file)
        self.target_dir = Path(target_dir)

    def import_file(self):
        if not self.source_file.exists():
            raise FileNotFoundError("Tally export file not found")

        self.target_dir.mkdir(parents=True, exist_ok=True)

        destination = self.target_dir / self.source_file.name
        shutil.copy(self.source_file, destination)

        return str(destination)
