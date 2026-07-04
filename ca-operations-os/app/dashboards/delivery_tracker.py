from datetime import datetime


class DeliveryTracker:
    def __init__(self):
        self.deliveries = []

    def mark_delivered(self, client_name, report_name):
        delivery = {
            "client": client_name,
            "report": report_name,
            "delivered_at": datetime.now().isoformat(),
            "status": "DELIVERED"
        }

        self.deliveries.append(delivery)
        return delivery

    def get_client_deliveries(self, client_name):
        return [
            d for d in self.deliveries
            if d["client"] == client_name
        ]
