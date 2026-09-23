import re

content = open("src/jobs_automation/intelligence/opportunity_graph.py").read()
new_func = """
    def resolve_best_profile(self, job_id: str, role_family: str | None = None) -> list[tuple["OpportunityNode", float]]:
        # Gather application nodes for this job
        apps = [e.subject_id for e in self.edges_to(job_id, Predicate.FOR_JOB)]
        
        contact_scores: dict[str, float] = {}
        
        for app_id in apps:
            # Gather contact edges pointing to this application
            for e in self.edges_to(app_id, Predicate.CONTACT_TOUCHED_APPLICATION):
                # Temporary: we pass role_family down
                score = e.get_score(role_family)
                contact_scores[e.subject_id] = contact_scores.get(e.subject_id, 0.0) + score

        # Build list of (Node, score) and sort descending
        results = []
        for cid, score in contact_scores.items():
            node = self.get_node(cid)
            if node:
                results.append((node, score))
                
        results.sort(key=lambda x: x[1], reverse=True)
        return results

"""

if "def resolve_best_profile" not in content:
    # insert before class OpportunityGraphService
    content = content.replace("class OpportunityGraphService:", new_func + "\nclass OpportunityGraphService:")

with open("src/jobs_automation/intelligence/opportunity_graph.py", "w") as f:
    f.write(content)
