import subprocess
from pathlib import Path
import os


class GSTConnector:
    def __init__(self, client_name):
        self.client_name = client_name
        self.script = Path(
            "bookkeeping-service/pipelines/gst_pipeline.py"
        )

    def run(self):
        env = os.environ.copy()
        env["CLIENT_NAME"] = self.client_name

        result = subprocess.run(
            ["python", str(self.script)],
            capture_output=True,
            text=True,
            env=env
        )

        return {
            "service": "gst",
            "client": self.client_name,
            "status": result.returncode,
            "output": result.stdout,
            "error": result.stderr
        }
