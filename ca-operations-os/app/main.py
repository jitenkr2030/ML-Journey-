import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from crm.leads import LeadManager
from crm.outreach import OutreachManager
from crm.followups import FollowupScheduler
from crm.client_conversion import ClientConversion

from orchestrator.job_dispatcher import JobDispatcher
from orchestrator.pipeline_router import PipelineRouter
from orchestrator.freelancer_manager import FreelancerManager
from orchestrator.workload_allocator import WorkloadAllocator

from dashboards.client_dashboard import ClientDashboard
from dashboards.work_status import WorkStatusTracker
from dashboards.delivery_tracker import DeliveryTracker

from connectors.bookkeeping_connector import BookkeepingConnector
from connectors.gst_connector import GSTConnector
from connectors.tds_connector import TDSConnector
from connectors.bank_connector import BankConnector
from connectors.journal_connector import JournalConnector


class CAOperationsOS:
    def __init__(self):
        self.leads = LeadManager("../data/leads/leads.csv")
        self.outreach = OutreachManager()
        self.followups = FollowupScheduler()
        self.client_conversion = ClientConversion()

        self.job_dispatcher = JobDispatcher()
        self.pipeline_router = PipelineRouter()
        self.freelancer_manager = FreelancerManager()
        self.workload_allocator = WorkloadAllocator()

        self.client_dashboard = ClientDashboard()
        self.work_status = WorkStatusTracker()
        self.delivery_tracker = DeliveryTracker()

        self.bookkeeping = None
        self.gst = None
        self.tds = None
        self.bank = None
        self.journal = None

    def process_lead(self, lead):
        score = self.leads.score_lead(lead)
        priority = self.leads.prioritize(score)

        return {
            "lead": lead.name,
            "score": score,
            "priority": priority
        }

    def onboard_client(self, client_name):
        workspace = self.client_conversion.create_client_workspace(client_name)
        return workspace

    def run_pipeline(self, client_name):

        self.bookkeeping = BookkeepingConnector(client_name)
        self.gst = GSTConnector(client_name)
        self.tds = TDSConnector(client_name)
        self.bank = BankConnector(client_name)
        self.journal = JournalConnector(client_name)

        results = {}

        self.work_status.add_status(client_name, "bookkeeping", "RUNNING")
        results["bookkeeping"] = self.bookkeeping.run()

        self.work_status.add_status(client_name, "gst", "RUNNING")
        results["gst"] = self.gst.run()

        self.work_status.add_status(client_name, "tds", "RUNNING")
        results["tds"] = self.tds.run()

        self.work_status.add_status(client_name, "bank", "RUNNING")
        results["bank"] = self.bank.run()

        self.work_status.add_status(client_name, "journal", "RUNNING")
        results["journal"] = self.journal.run()

        self.delivery_tracker.mark_delivered(
            client_name,
            "final_report"
        )

        return results


if __name__ == "__main__":
    system = CAOperationsOS()

    print("=" * 60)
    print("CA OPERATIONS OS STARTED")
    print("=" * 60)

    clients = system.client_dashboard.list_clients()
    print("Active Clients:", clients)
