class FreelancerManager:
    def __init__(self):
        self.freelancers = []

    def add_freelancer(self, name: str, skill: str):
        freelancer = {
            "name": name,
            "skill": skill,
            "status": "AVAILABLE"
        }
        self.freelancers.append(freelancer)
        return freelancer

    def available_freelancers(self):
        return [
            f for f in self.freelancers
            if f["status"] == "AVAILABLE"
        ]

    def mark_busy(self, name: str):
        for freelancer in self.freelancers:
            if freelancer["name"] == name:
                freelancer["status"] = "BUSY"
                return freelancer
        return None
