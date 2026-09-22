import json, os, subprocess, sys, uuid
from pathlib import Path
import psycopg
from psycopg import sql

source = Path('/Users/pchordia/Downloads/swarm_codex/review/jobs-fixture-source')
venv = source.parent / 'jobs-source/.venv/bin'
socket = '/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd'
database = 'jobs_golden_root_' + uuid.uuid4().hex[:12]
out = Path('/tmp/jobs-golden-root-result-20260922')
out.mkdir(exist_ok=True)
identity = subprocess.check_output(['git', 'rev-parse', 'HEAD', 'HEAD^{tree}'], cwd=source, text=True).splitlines()
assert identity == ['832d85f5177ca82564c9d0b6c168790f26ea1dc3', '047eb8501e562cbbca450e946e260a1b8454f74b']
assert subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True) == ''
env = dict(os.environ, JOBS_DB=database, JOBS_PG_SOCKET=socket, JOBS_PG_PORT='56422',
           SOURCE_SHA=identity[0], PYTHONPATH=str(source/'src')+':'+str(source),
           DATABASE_URL=f'postgresql+psycopg:///{database}?host={socket}&port=56422')
result = {'source_sha': identity[0], 'tree': identity[1], 'database': database}
with psycopg.connect(dbname='postgres', host=socket, port=56422, autocommit=True) as admin:
    admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
    try:
        with (out/'migration.log').open('w') as log:
            p = subprocess.run([str(venv/'alembic'),'upgrade','head'],cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT)
        result['migration_exit'] = p.returncode
        assert p.returncode == 0
        with (out/'workflow.log').open('w') as log:
            p = subprocess.run([str(venv/'python'),'/tmp/jobs-v20-golden-steps9-17.py'],cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT)
        result['workflow_exit'] = p.returncode
        assert p.returncode == 0
        raw = (out/'workflow.log').read_text()
        start = raw.index('{\n  "result": "PASS_STEPS_1_17"')
        report = json.JSONDecoder().raw_decode(raw[start:])[0]
        (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    finally:
        admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))
        result['remaining_database_count'] = admin.execute('SELECT count(*) FROM pg_database WHERE datname=%s',(database,)).fetchone()[0]
        (out/'run.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,sort_keys=True))
