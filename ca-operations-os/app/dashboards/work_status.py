from datetime import datetime


class WorkStatusTracker:
    def __init__(self):
        self.status_log = []

    def add_status(self, client, task, status):
        entry = {
            "client": client,
            "task": task,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }

        self.status_log.append(entry)
        return entry

    def get_status(self, client):
        return [
            log for log in self.status_log
            if log["client"] == client
        ]
