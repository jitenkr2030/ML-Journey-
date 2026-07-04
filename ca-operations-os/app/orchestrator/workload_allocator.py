class WorkloadAllocator:
    def __init__(self):
        self.assignments = {}

    def assign(self, freelancer_name: str, client_name: str):
        if freelancer_name not in self.assignments:
            self.assignments[freelancer_name] = []

        self.assignments[freelancer_name].append(client_name)

        return {
            "freelancer": freelancer_name,
            "assigned_client": client_name
        }

    def get_workload(self, freelancer_name: str):
        return self.assignments.get(freelancer_name, [])
