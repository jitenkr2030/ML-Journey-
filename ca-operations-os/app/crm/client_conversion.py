import os


class ClientConversion:
    BASE_DIR = "../data/clients"

    def create_client_workspace(self, client_name: str):
        client_path = os.path.join(self.BASE_DIR, client_name.replace(" ", "_"))
        os.makedirs(os.path.join(client_path, "input"), exist_ok=True)
        os.makedirs(os.path.join(client_path, "output"), exist_ok=True)
        os.makedirs(os.path.join(client_path, "reports"), exist_ok=True)

        return {
            "client": client_name,
            "workspace": client_path
        }
