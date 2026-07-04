from pathlib import Path
import os


class ClientDashboard:
    BASE_DIR = Path("../data/clients")

    def list_clients(self):
        if not self.BASE_DIR.exists():
            return []

        return [
            client.name
            for client in self.BASE_DIR.iterdir()
            if client.is_dir()
        ]

    def client_summary(self, client_name: str):
        client_path = self.BASE_DIR / client_name

        if not client_path.exists():
            return {"error": "Client not found"}

        return {
            "client": client_name,
            "input_files": len(os.listdir(client_path / "input")),
            "output_files": len(os.listdir(client_path / "output")),
            "reports": len(os.listdir(client_path / "reports"))
        }
