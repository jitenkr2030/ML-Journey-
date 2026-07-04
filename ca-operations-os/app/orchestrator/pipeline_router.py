import subprocess
from pathlib import Path


class PipelineRouter:
    def __init__(self):
        self.base_pipeline = Path("bookkeeping-service/pipelines")

    def route(self, pipeline_name: str):
        pipeline_map = {
            "bookkeeping": "run_all.py",
            "gst": "gst_summary.py",
            "tds": "tds_summary.py",
            "trial_balance": "trial_balance.py",
            "journal_entries": "journal_entries.py"
        }

        if pipeline_name not in pipeline_map:
            raise ValueError(f"Unknown pipeline: {pipeline_name}")

        script = self.base_pipeline / pipeline_map[pipeline_name]

        result = subprocess.run(
            ["python", str(script)],
            capture_output=True,
            text=True
        )

        return {
            "pipeline": pipeline_name,
            "status": "success" if result.returncode == 0 else "failed",
            "stdout": result.stdout,
            "stderr": result.stderr
        }
