"""Create, migrate, exercise, and remove one owned disposable Jobs database."""
from __future__ import annotations
import json,os,subprocess,uuid
from pathlib import Path
import psycopg
from psycopg import sql
SOURCE=Path('/Users/pchordia/Downloads/swarm_codex/review/jobs-health-badge-source')
VENV=SOURCE.parent/'jobs-source/.venv/bin'
SOCKET='/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd'
EXPECTED=['1e54aafa61ef06ed2ef8a7a681c806ba89ef3268','8972a90de1f7aafd469fedde63926382c726319f']
identity=subprocess.check_output(['git','rev-parse','HEAD','HEAD^{tree}'],cwd=SOURCE,text=True).splitlines()
assert identity==EXPECTED
assert subprocess.check_output(['git','status','--porcelain'],cwd=SOURCE,text=True)==''
db='jobs_control_status_'+uuid.uuid4().hex[:12]
out=Path('/tmp/jobs-control-center-config-status-independent-20260922'); out.mkdir(exist_ok=True)
env={**os.environ,'DATABASE_URL':f'postgresql+psycopg:///{db}?host={SOCKET}&port=56422','PYTHONPATH':f'{SOURCE/"src"}:{SOURCE}'}
summary={'source_sha':identity[0],'source_tree':identity[1],'database':db}
with psycopg.connect(dbname='postgres',host=SOCKET,port=56422,autocommit=True) as admin:
 admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(db)))
 try:
  with (out/'migration.log').open('w') as log:
   p=subprocess.run([str(VENV/'alembic'),'upgrade','head'],cwd=SOURCE,env=env,stdout=log,stderr=subprocess.STDOUT)
  summary['migration_exit']=p.returncode; assert p.returncode==0
  with (out/'workflow.log').open('w') as log:
   p=subprocess.run([str(VENV/'python'),'/tmp/jobs-control-center-config-status-repro.py'],cwd=SOURCE,env=env,stdout=log,stderr=subprocess.STDOUT)
  summary['workflow_exit']=p.returncode; assert p.returncode==0
  raw=(out/'workflow.log').read_text(); report=json.JSONDecoder().raw_decode(raw[raw.index('{'):])[0]
  (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 finally:
  admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(db)))
  summary['remaining_database_count']=admin.execute('SELECT count(*) FROM pg_database WHERE datname=%s',(db,)).fetchone()[0]
  (out/'run.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
  print(json.dumps(summary,sort_keys=True))
