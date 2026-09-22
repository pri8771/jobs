"""Production-handler proof that J20-01 has no safe config/status read surface."""
from __future__ import annotations

import io
import json
import os
import subprocess
from pathlib import Path
from typing import Any, cast

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from jobs_automation.dashboard.server import DashboardRequestHandler

SOURCE = Path('/Users/pchordia/Downloads/swarm_codex/review/jobs-health-badge-source')
EXPECTED = ['1e54aafa61ef06ed2ef8a7a681c806ba89ef3268','8972a90de1f7aafd469fedde63926382c726319f']
identity = subprocess.check_output(['git','rev-parse','HEAD','HEAD^{tree}'],cwd=SOURCE,text=True).splitlines()
assert identity == EXPECTED
assert subprocess.check_output(['git','status','--porcelain'],cwd=SOURCE,text=True) == ''

class Handler(DashboardRequestHandler):
    def __init__(self, path: str, factory: Any):
        self.command='GET'; self.path=path; self.request_version='HTTP/1.1'
        self.headers=cast(Any,{})
        self.rfile=io.BytesIO(); self.mock_wfile=io.BytesIO(); self.wfile=cast(Any,self.mock_wfile)
        self.session_factory=factory; self.client_address=('127.0.0.1',12345)
        self.status_code=200; self.response_headers={}; self.error_message=None
    def send_response(self, code:int, message:str|None=None)->None: self.status_code=code
    def send_header(self, keyword:str, value:str)->None: self.response_headers[keyword]=value
    def end_headers(self)->None: pass
    def send_error(self, code:int, message:str|None=None, explain:str|None=None)->None:
        self.status_code=code; self.error_message=message

def request(path: str, factory: Any) -> dict[str, Any]:
    h=Handler(path,factory); h.do_GET(); raw=h.mock_wfile.getvalue()
    return {'path':path,'status':h.status_code,'error':h.error_message,
            'json':json.loads(raw) if raw else None}

engine=create_engine(os.environ['DATABASE_URL'])
factory=sessionmaker(bind=engine)
controls=[request('/api/jobs',factory),request('/api/policies',factory)]
probes=[request(p,factory) for p in ('/api/status','/api/config','/api/system-status')]
assert all(x['status']==200 for x in controls), controls
assert all(x['status']==404 for x in probes), probes
print(json.dumps({'source_sha':identity[0],'source_tree':identity[1],
 'result':'REPRO_SAFE_CONFIG_STATUS_READ_SURFACE_ABSENT',
 'working_read_controls':controls,'missing_read_surfaces':probes},indent=2,sort_keys=True))
