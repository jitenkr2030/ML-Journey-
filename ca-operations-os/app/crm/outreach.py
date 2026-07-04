from datetime import datetime


class OutreachManager:
    def __init__(self):
        self.logs = []

    def send_whatsapp(self, lead_name: str, mobile: str):
        log = {
            "type": "whatsapp",
            "lead": lead_name,
            "mobile": mobile,
            "time": datetime.now().isoformat()
        }
        self.logs.append(log)
        return log

    def send_email(self, lead_name: str, email: str):
        log = {
            "type": "email",
            "lead": lead_name,
            "email": email,
            "time": datetime.now().isoformat()
        }
        self.logs.append(log)
        return log
