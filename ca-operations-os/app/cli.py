import argparse
from main import CAOperationsOS
from crm.leads import Lead


system = CAOperationsOS()


def add_lead(args):
    lead = Lead(
        name=args.name,
        profession=args.profession,
        mobile=args.mobile,
        email=args.email,
        city=args.city,
        state=args.state,
        status="ACTIVE"
    )

    leads = system.leads.load_leads()
    leads.append(lead)
    system.leads.save_leads(leads)

    print(f"Lead added: {args.name}")


def onboard_client(args):
    result = system.onboard_client(args.client)
    print(result)


def run_pipeline(args):
    result = system.run_pipeline(args.client)
    print(result)


parser = argparse.ArgumentParser(
    description="CA Operations OS CLI"
)

subparsers = parser.add_subparsers()

# add-lead
lead_parser = subparsers.add_parser("add-lead")
lead_parser.add_argument("--name", required=True)
lead_parser.add_argument("--profession", required=True)
lead_parser.add_argument("--mobile", required=True)
lead_parser.add_argument("--email", required=True)
lead_parser.add_argument("--city", required=True)
lead_parser.add_argument("--state", required=True)
lead_parser.set_defaults(func=add_lead)

# onboard-client
client_parser = subparsers.add_parser("onboard-client")
client_parser.add_argument("--client", required=True)
client_parser.set_defaults(func=onboard_client)

# run-pipeline
pipeline_parser = subparsers.add_parser("run-pipeline")
pipeline_parser.add_argument("--client", required=True)
pipeline_parser.set_defaults(func=run_pipeline)

args = parser.parse_args()

if hasattr(args, "func"):
    args.func(args)
else:
    parser.print_help()
