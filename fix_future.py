content = open("src/jobs_automation/preparation/packet_builder.py").read()

content = content.replace("from jobs_automation.core.job_search import JobSearchConfig\n", "")
content = content.replace("from __future__ import annotations", "from __future__ import annotations\n\nfrom typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from jobs_automation.core.job_search import JobSearchConfig")
with open("src/jobs_automation/preparation/packet_builder.py", "w") as f:
    f.write(content)
