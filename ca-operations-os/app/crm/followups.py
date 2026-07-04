from datetime import datetime, timedelta


class FollowupScheduler:
    def __init__(self):
        self.followups = []

    def schedule(self, lead_name: str, days: int = 3):
        next_date = datetime.now() + timedelta(days=days)
        followup = {
            "lead": lead_name,
            "next_followup": next_date.isoformat()
        }
        self.followups.append(followup)
        return followup
