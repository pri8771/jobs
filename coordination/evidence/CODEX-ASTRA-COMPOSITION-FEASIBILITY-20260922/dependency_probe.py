import importlib.util
from pathlib import Path
import jobs_automation.ingestion.engine as e
print('base engine:',e.__file__,flush=True)
p=Path('/tmp/jobs-astra-composition-feasibility-20260922/accepted_canary_bounded.py')
s=importlib.util.spec_from_file_location('accepted_canary_bounded_probe',p)
m=importlib.util.module_from_spec(s)
s.loader.exec_module(m)
