from dataclasses import dataclass, asdict
from typing import List, Optional
import csv
import os


@dataclass
class Lead:
    name: str
    profession: str
    mobile: str
    email: str
    city: str
    state: str
    status: str
    priority: Optional[str] = None
    score: Optional[int] = 0


class LeadManager:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_leads(self) -> List[Lead]:
        leads = []
        if not os.path.exists(self.file_path):
            return leads

        with open(self.file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                leads.append(Lead(**row))
        return leads

    def save_leads(self, leads: List[Lead]):
        if not leads:
            return

        with open(self.file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=asdict(leads[0]).keys())
            writer.writeheader()
            for lead in leads:
                writer.writerow(asdict(lead))

    def classify_lead(self, profession: str) -> str:
        if "Chartered Accountant" in profession:
            return "CLIENT"
        elif "Commerce" in profession:
            return "FREELANCER"
        return "PARTNER"

    def score_lead(self, lead: Lead) -> int:
        score = 0
        if "Chartered Accountant" in lead.profession:
            score += 90
        if lead.mobile:
            score += 5
        if lead.email:
            score += 5
        return score

    def prioritize(self, score: int) -> str:
        if score >= 95:
            return "A"
        elif score >= 70:
            return "B"
        return "C"
