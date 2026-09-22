from pathlib import Path
import contextlib,io,json,subprocess,sys
source=Path('/Users/pchordia/Downloads/swarm_codex/review/jobs-config-status-source')
assert subprocess.check_output(['git','rev-parse','HEAD','HEAD^{tree}'],cwd=source,text=True).splitlines()==['413a18ee13ee049f57651ddd7060fd98fafad5f9','f40e443a084e4a2e5c6a4ac7cbc4f6dcf791cfa6']
assert not subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True).strip()
sys.path[:0]=[str(source/'src'),str(source)]
from tests.test_dashboard import DummyRequestHandler
class NoDB:
 def __call__(self):raise AssertionError('config_route_opened_database')
h=DummyRequestHandler('GET','/api/config-status',session_factory=NoDB())
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):h.do_GET()
body=json.loads(h.mock_wfile.getvalue())
assert h.status_code==200
assert set(body)=={'state','error_count','warning_count','loaded_config_count','loaded_config_names','unresolved_fact_counts'}
assert body['state'] in {'VALID','INVALID'}
assert body['loaded_config_count']==len(body['loaded_config_names'])
assert body['loaded_config_names']==sorted(set(body['loaded_config_names']))
print(json.dumps({'source_sha':'413a18ee13ee049f57651ddd7060fd98fafad5f9','source_tree':'f40e443a084e4a2e5c6a4ac7cbc4f6dcf791cfa6','http_status':h.status_code,'database_entries':0,'sanitized_projection':body},indent=2,sort_keys=True))
