from datetime import datetime
from uuid import uuid4
import csv
from pathlib import Path


class JobDispatcher:
    def __init__(self):
        self.jobs = []

        self.jobs_file = Path(
            "ca-operations-os/data/jobs/jobs_master.csv"
        )

        self.jobs_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.jobs_file.exists():
            with open(self.jobs_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "job_id",
                    "client",
                    "pipeline",
                    "status",
                    "created_at"
                ])

    def create_job(self, client_name: str, pipeline: str):
        job = {
            "job_id": str(uuid4()),
            "client": client_name,
            "pipeline": pipeline,
            "status": "PENDING",
            "created_at": datetime.now().isoformat()
        }

        self.jobs.append(job)

        with open(self.jobs_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                job["job_id"],
                job["client"],
                job["pipeline"],
                job["status"],
                job["created_at"]
            ])

        return job

    def update_status(self, job_id: str, status: str):
        for job in self.jobs:
            if job["job_id"] == job_id:
                job["status"] = status
                return job

        return None
